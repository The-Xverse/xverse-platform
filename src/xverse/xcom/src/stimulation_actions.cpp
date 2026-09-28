/**
 * \file stimulation_actions.cpp
 * \brief T028 guarded action-path and exclusive service-emulation lease implementation: bounded
 *        preconditions, one guard decision per request, journal-before-emission ordering, a
 *        bounded ordered pending queue, bounded lineage, and non-mutating completion.
 * \ingroup xcom_stim
 *
 * \details
 * This is the additive T028 production implementation. It consumes the accepted T025, T026, and
 * T027 in-process contracts and the accepted T-CORE origin vocabulary read-only. It performs no
 * file, network, socket, ambient, secret, dynamic-load, or subprocess access, calls no time
 * authority, and retains no payload byte.
 */

#include "xverse/xcom/stimulation_actions.hpp"

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <limits>
#include <span>
#include <stdexcept>
#include <utility>
#include <vector>

namespace xverse::xcom::validation {
namespace {

/// \brief Reports whether a session identity is all zero.
/// \param session Candidate session identity.
/// \return `true` when every byte is zero.
[[nodiscard]] bool session_is_zero(const SessionId &session) noexcept {
  for (const std::uint8_t byte : session) {
    if (byte != 0U) {
      return false;
    }
  }
  return true;
}

/// \brief Maps an emission status into a closed outcome kind; only `Delivered` reports delivery.
/// \param status Host emission status.
/// \return The bounded outcome kind.
[[nodiscard]] OutcomeKind outcome_kind_for(EmissionStatus status) noexcept {
  switch (status) {
  case EmissionStatus::Delivered:
    return OutcomeKind::Delivered;
  case EmissionStatus::Rejected:
    return OutcomeKind::Rejected;
  case EmissionStatus::Unavailable:
  default:
    return OutcomeKind::Unknown;
  }
}

/// \brief Orders two pending actions by the declared rule without comparing raw mismatched clocks.
/// \param ordering Declared ordering rule.
/// \param lhs First pending action.
/// \param rhs Second pending action.
/// \return `true` when `lhs` precedes `rhs`.
[[nodiscard]] bool pending_precedes(OrderingRule ordering, const PendingAction &lhs,
                                    const PendingAction &rhs) noexcept {
  if (ordering == OrderingRule::ScheduledThenArrival && lhs.domain == rhs.domain &&
      lhs.scheduled_at != rhs.scheduled_at) {
    return lhs.scheduled_at < rhs.scheduled_at;
  }
  return lhs.request_id < rhs.request_id;
}

[[nodiscard]] bool is_late(Timestamp now, Timestamp scheduled, Timestamp tolerance) noexcept {
  // Tolerance is nonnegative. Avoid signed overflow when the legal deadline exceeds Timestamp.
  return scheduled <= std::numeric_limits<Timestamp>::max() - tolerance &&
         now > scheduled + tolerance;
}

} // namespace

// ---------------------------------------------------------------------------------------------
// ServiceEmulationRegistry
// ---------------------------------------------------------------------------------------------

ServiceEmulationRegistry::ServiceEmulationRegistry(std::size_t max_active_leases) {
  if (max_active_leases < 1U || max_active_leases > kActionPathMaxActiveLeases) {
    throw std::invalid_argument("active-lease capacity out of declared range");
  }
  capacity_ = max_active_leases;
  entries_.reserve(capacity_);
}

bool ServiceEmulationRegistry::key_is_valid(const EndpointGeneration &key) noexcept {
  return !session_is_zero(key.session) && Tag::is_valid(key.endpoint.value());
}

ServiceEmulationRegistry::LeaseEntry *
ServiceEmulationRegistry::find_locked(const EndpointGeneration &key) noexcept {
  LeaseEntry *inactive = nullptr;
  for (LeaseEntry &entry : entries_) {
    if (entry.key == key) {
      if (entry.state == LeaseState::Active || entry.emission_reserved) {
        return &entry;
      }
      inactive = &entry;
    }
  }
  return inactive;
}

const ServiceEmulationRegistry::LeaseEntry *
ServiceEmulationRegistry::find_locked(const EndpointGeneration &key) const noexcept {
  const LeaseEntry *inactive = nullptr;
  for (const LeaseEntry &entry : entries_) {
    if (entry.key == key) {
      if (entry.state == LeaseState::Active || entry.emission_reserved) {
        return &entry;
      }
      inactive = &entry;
    }
  }
  return inactive;
}

std::size_t ServiceEmulationRegistry::active_count_locked() const noexcept {
  std::size_t count = 0U;
  for (const LeaseEntry &entry : entries_) {
    if (entry.state == LeaseState::Active || entry.emission_reserved) {
      ++count;
    }
  }
  return count;
}

ServiceEmulationRegistry::LeaseEntry *ServiceEmulationRegistry::reusable_slot_locked() noexcept {
  for (LeaseEntry &entry : entries_) {
    if (entry.state != LeaseState::Active && !entry.emission_reserved) {
      return &entry;
    }
  }
  if (entries_.size() < capacity_) {
    entries_.emplace_back();
    return &entries_.back();
  }
  return nullptr;
}

LeaseStatus ServiceEmulationRegistry::acquire(const EndpointGeneration &key,
                                              std::uint64_t request_id, ClockDomainId domain,
                                              Timestamp acquired_at, Timestamp expires_at) {
  if (!key_is_valid(key) || acquired_at > expires_at || domain == kInvalidClockDomain) {
    return LeaseStatus::RejectedConfiguration;
  }
  std::lock_guard<std::mutex> lock(mutex_);
  // A foreign identity is classified before the capacity check so a superseded generation or a
  // foreign session or plan never appears as a capacity failure.
  for (const LeaseEntry &entry : entries_) {
    if ((entry.state != LeaseState::Active && !entry.emission_reserved) ||
        entry.key.endpoint != key.endpoint) {
      continue;
    }
    ++conflicts_;
    if (entry.key == key) {
      return LeaseStatus::Conflict;
    }
    if (entry.key.plan_digest != key.plan_digest) {
      return LeaseStatus::PlanMismatch;
    }
    if (entry.key.session != key.session) {
      return LeaseStatus::SessionMismatch;
    }
    if (entry.key.generation != key.generation) {
      return LeaseStatus::GenerationMismatch;
    }
    return LeaseStatus::Conflict;
  }
  if (active_count_locked() >= capacity_) {
    return LeaseStatus::CapacityExhausted;
  }
  // Reuse a tombstone for the same key before a different slot; otherwise two inactive
  // generations with the same key would make state_of ambiguous after the new lease ends.
  LeaseEntry *slot = nullptr;
  for (LeaseEntry &entry : entries_) {
    if (entry.key == key && entry.state != LeaseState::Active && !entry.emission_reserved) {
      slot = &entry;
      break;
    }
  }
  if (slot == nullptr) {
    slot = reusable_slot_locked();
  }
  if (slot == nullptr) {
    return LeaseStatus::CapacityExhausted;
  }
  slot->key = key;
  slot->request_id = request_id;
  slot->domain = domain;
  slot->acquired_at = acquired_at;
  slot->expires_at = expires_at;
  slot->state = LeaseState::Active;
  slot->emission_reserved = false;
  ++acquisitions_;
  return LeaseStatus::Ok;
}

LeaseStatus ServiceEmulationRegistry::precheck(const EndpointGeneration &key, ClockDomainId domain,
                                               Timestamp acquired_at,
                                               Timestamp expires_at) const {
  if (!key_is_valid(key) || acquired_at > expires_at || domain == kInvalidClockDomain) {
    return LeaseStatus::RejectedConfiguration;
  }
  std::lock_guard<std::mutex> lock(mutex_);
  // A non-mutating copy of the acquire classification: a foreign identity is classified before the
  // capacity check so a superseded generation or a foreign session or plan never appears as a
  // capacity failure, and no entry or counter is touched.
  for (const LeaseEntry &entry : entries_) {
    if ((entry.state != LeaseState::Active && !entry.emission_reserved) ||
        entry.key.endpoint != key.endpoint) {
      continue;
    }
    if (entry.key == key) {
      return LeaseStatus::Conflict;
    }
    if (entry.key.plan_digest != key.plan_digest) {
      return LeaseStatus::PlanMismatch;
    }
    if (entry.key.session != key.session) {
      return LeaseStatus::SessionMismatch;
    }
    if (entry.key.generation != key.generation) {
      return LeaseStatus::GenerationMismatch;
    }
    return LeaseStatus::Conflict;
  }
  if (active_count_locked() >= capacity_) {
    return LeaseStatus::CapacityExhausted;
  }
  return LeaseStatus::Ok;
}

LeaseStatus ServiceEmulationRegistry::release(const EndpointGeneration &key,
                                              std::uint64_t request_id) {
  std::lock_guard<std::mutex> lock(mutex_);
  LeaseEntry *entry = find_locked(key);
  if (entry == nullptr) {
    return LeaseStatus::NotFound;
  }
  if (entry->state == LeaseState::Released) {
    return LeaseStatus::AlreadyReleased;
  }
  if (entry->state != LeaseState::Active) {
    return LeaseStatus::NotHeld;
  }
  if (entry->request_id != request_id) {
    return LeaseStatus::NotHeld;
  }
  entry->state = LeaseState::Released;
  return LeaseStatus::Ok;
}

LeaseStatus ServiceEmulationRegistry::quarantine(const EndpointGeneration &key,
                                                 QuarantineReason reason) {
  std::lock_guard<std::mutex> lock(mutex_);
  LeaseEntry *entry = find_locked(key);
  if (entry == nullptr) {
    return LeaseStatus::NotFound;
  }
  if (entry->state != LeaseState::Active) {
    return LeaseStatus::NotHeld;
  }
  entry->state = LeaseState::Quarantined;
  entry->quarantine_reason = reason;
  return LeaseStatus::Ok;
}

LeaseStatus ServiceEmulationRegistry::expire_key(const EndpointGeneration &key) {
  std::lock_guard<std::mutex> lock(mutex_);
  LeaseEntry *entry = find_locked(key);
  if (entry == nullptr) {
    return LeaseStatus::NotFound;
  }
  if (entry->state != LeaseState::Active) {
    return LeaseStatus::NotHeld;
  }
  entry->state = LeaseState::Expired;
  return LeaseStatus::Ok;
}

std::size_t ServiceEmulationRegistry::expire_elapsed(ClockDomainId domain, Timestamp now) {
  std::lock_guard<std::mutex> lock(mutex_);
  std::size_t count = 0U;
  for (LeaseEntry &entry : entries_) {
    // Only a value in the declared domain is compared; a foreign-domain entry is never ordered.
    if (entry.state != LeaseState::Active || entry.domain != domain) {
      continue;
    }
    if (entry.expires_at <= now) {
      entry.state = LeaseState::Expired;
      ++count;
    }
  }
  return count;
}

bool ServiceEmulationRegistry::holds(const EndpointGeneration &key) const {
  std::lock_guard<std::mutex> lock(mutex_);
  const LeaseEntry *entry = find_locked(key);
  return entry != nullptr && entry->state == LeaseState::Active;
}

bool ServiceEmulationRegistry::reserve_emission(const EndpointGeneration &key,
                                                 std::uint64_t request_id) {
  std::lock_guard<std::mutex> lock(mutex_);
  LeaseEntry *entry = find_locked(key);
  if (entry == nullptr || entry->state != LeaseState::Active ||
      entry->request_id != request_id || entry->emission_reserved) {
    return false;
  }
  entry->emission_reserved = true;
  return true;
}

void ServiceEmulationRegistry::finish_emission(const EndpointGeneration &key,
                                                std::uint64_t request_id) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  LeaseEntry *entry = find_locked(key);
  if (entry != nullptr && entry->request_id == request_id) {
    entry->emission_reserved = false;
  }
}

LeaseState ServiceEmulationRegistry::state_of(const EndpointGeneration &key) const {
  std::lock_guard<std::mutex> lock(mutex_);
  const LeaseEntry *entry = find_locked(key);
  return entry == nullptr ? LeaseState::None : entry->state;
}

LeaseSnapshot ServiceEmulationRegistry::snapshot() const {
  std::lock_guard<std::mutex> lock(mutex_);
  LeaseSnapshot result{};
  for (const LeaseEntry &entry : entries_) {
    switch (entry.state) {
    case LeaseState::Active:
      ++result.active;
      break;
    case LeaseState::Released:
      ++result.released;
      break;
    case LeaseState::Quarantined:
      ++result.quarantined;
      break;
    case LeaseState::Expired:
      ++result.expired;
      break;
    case LeaseState::None:
    default:
      break;
    }
  }
  result.acquisitions = acquisitions_;
  result.conflicts = conflicts_;
  return result;
}

std::size_t ServiceEmulationRegistry::capacity() const noexcept { return capacity_; }

// ---------------------------------------------------------------------------------------------
// StimulationActionPath
// ---------------------------------------------------------------------------------------------

StimulationActionPath::StimulationActionPath(const ActionPathConfig &config,
                                             StimulationJournal &journal,
                                             ServiceEmulationRegistry &registry,
                                             ActionEmitter &emitter) noexcept
    : config_(config), journal_(journal), registry_(registry), emitter_(emitter) {}

bool StimulationActionPath::config_is_legal(const ActionPathConfig &config) noexcept {
  if (config.max_pending_actions < 1U ||
      config.max_pending_actions > kActionPathMaxPendingActions) {
    return false;
  }
  if (config.max_lineage_entries < 1U ||
      config.max_lineage_entries > kActionPathMaxLineage) {
    return false;
  }
  if (config.max_drain_steps < 1U || config.max_drain_steps > kActionPathMaxDrainSteps) {
    return false;
  }
  if (config.max_payload_bytes < 1U || config.max_payload_bytes > kActionPathMaxPayloadBytes) {
    return false;
  }
  if (config.late_tolerance < 0) {
    return false;
  }
  return Tag::is_valid(config.tool.value());
}

GuardStatus StimulationActionPath::open(const Permit &permit, const StimulationPolicy &policy) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (!config_is_legal(config_)) {
    open_ = false;
    return GuardStatus::RejectedConfiguration;
  }
  try {
    pending_.reserve(config_.max_pending_actions);
    lineage_.reserve(config_.max_lineage_entries);
    held_leases_.reserve(kActionPathMaxActiveLeases);
  } catch (const std::exception &) {
    open_ = false;
    return GuardStatus::RejectedConfiguration;
  }
  const GuardStatus status = guard_.open(permit, policy);
  if (status != GuardStatus::Ok) {
    open_ = false;
    return status;
  }
  permit_ = permit;
  pending_.clear();
  lineage_.clear();
  held_leases_.clear();
  emitted_ = 0U;
  emission_rejected_ = 0U;
  emission_unavailable_ = 0U;
  rejected_ = 0U;
  failed_ = 0U;
  cancelled_ = 0U;
  expired_ = 0U;
  discarded_ = 0U;
  evidence_incomplete_ = 0U;
  lease_conflicts_ = 0U;
  drain_state_ = DrainState::Idle;
  open_ = true;
  return GuardStatus::Ok;
}

EndpointGeneration
StimulationActionPath::lease_key_for(const StimulationRequest &request) const {
  EndpointGeneration key;
  key.session = permit_.session_id();
  key.endpoint = request.service_owner.endpoint;
  key.generation = request.service_owner.generation;
  key.plan_digest = permit_.plan_digest();
  return key;
}

StimulationIntent StimulationActionPath::intent_for(const StimulationRequest &request) const {
  StimulationIntent intent;
  intent.permit_id = permit_.permit_id();
  intent.session_id = permit_.session_id();
  intent.plan_digest = permit_.plan_digest();
  intent.request_id = request.request_id;
  intent.correlation_id = request.correlation_id;
  intent.causation_id = request.causation_id;
  intent.action_mask = to_stimulation_mask(request.action);
  intent.target = request.target;
  intent.tool = config_.tool;
  intent.quota_cost = request.quota_cost;
  intent.clock_domain = request.clock_domain;
  intent.scheduled_at = request.scheduled_at;
  intent.immediate = request.immediate;
  return intent;
}

bool StimulationActionPath::lineage_contains(std::uint64_t identity) const noexcept {
  for (const std::uint64_t entry : lineage_) {
    if (entry == identity) {
      return true;
    }
  }
  return false;
}

void StimulationActionPath::advance_lineage_locked(std::uint64_t request_id) {
  if (lineage_.size() >= config_.max_lineage_entries) {
    lineage_.erase(lineage_.begin());
  }
  lineage_.push_back(request_id);
}

void StimulationActionPath::queue_locked(const PendingAction &pending) {
  std::size_t index = 0U;
  while (index < pending_.size() &&
         pending_precedes(config_.ordering, pending_[index], pending)) {
    ++index;
  }
  pending_.insert(pending_.begin() + static_cast<std::ptrdiff_t>(index), pending);
}

StimulationActionPath::EmissionAttempt
StimulationActionPath::journal_and_emit(std::unique_lock<std::mutex> &lock,
                                        const StimulationIntent &intent,
                                        std::span<const std::byte> payload,
                                        ClockDomainId observed_domain, Timestamp observed_at) {
  EmissionAttempt attempt;
  const auto seam = [this, &lock, payload, observed_domain, observed_at, &attempt](
                        const StimulationIntent &emitted) -> StimulationOutcome {
    attempt.emission_started = true;
    lock.unlock();
    SyntheticStimulationItem item;
    item.origin = OriginKind::validation_tool;
    item.intent = emitted;
    attempt.emission = emitter_.emit(item, payload);
    StimulationOutcome outcome;
    outcome.request_id = emitted.request_id;
    outcome.kind = outcome_kind_for(attempt.emission);
    outcome.reason = Result::Ok;
    outcome.clock_domain = observed_domain;
    outcome.observed_at = observed_at;
    return outcome;
  };
  StimulationOutcome outcome;
  attempt.journal = journal_.journal_then_emit(intent, seam, outcome);
  return attempt;
}

ActionStatus StimulationActionPath::classify_locked(const EmissionAttempt &attempt,
                                                    std::uint64_t request_id) {
  switch (attempt.journal) {
  case JournalStatus::Ok:
    advance_lineage_locked(request_id);
    // A durable intent whose host outcome is durable too is not success unless it was delivered.
    if (attempt.emission == EmissionStatus::Delivered) {
      ++emitted_;
      return ActionStatus::Emitted;
    }
    if (attempt.emission == EmissionStatus::Rejected) {
      ++emission_rejected_;
      return ActionStatus::EmissionRejected;
    }
    ++emission_unavailable_;
    return ActionStatus::EmissionUnavailable;
  case JournalStatus::EvidenceIncomplete:
    ++evidence_incomplete_;
    return ActionStatus::EvidenceIncomplete;
  case JournalStatus::CapacityExhausted:
    return ActionStatus::CapacityExhausted;
  case JournalStatus::RecordTooLarge:
  case JournalStatus::RejectedConfiguration:
  case JournalStatus::AlreadyResolved:
  case JournalStatus::NotFound:
    return ActionStatus::RejectedConfiguration;
  case JournalStatus::WriteFailed:
  case JournalStatus::PartialWrite:
  case JournalStatus::CorruptRecord:
    return ActionStatus::JournalFailed;
  default:
    return ActionStatus::JournalFailed;
  }
}

ActionStatus
StimulationActionPath::execute(const StimulationRequest &request, LifecycleState session_state,
                               const ResolvedTime &resolved_time,
                               std::span<const std::byte> payload, ActionDiagnostic &out) {
  std::unique_lock<std::mutex> lock(mutex_);
  out = ActionDiagnostic{};
  out.request_id = request.request_id;

  // Step 1: a closed path evaluates nothing.
  if (!open_) {
    out.status = ActionStatus::NotOpen;
    return ActionStatus::NotOpen;
  }
  // Step 2: a malformed request or over-bound payload before any state work.
  if (request.request_id == 0U || payload.size() > config_.max_payload_bytes) {
    out.status = ActionStatus::RejectedConfiguration;
    return ActionStatus::RejectedConfiguration;
  }
  // Step 3: bounded emission-time reinjection lineage; no guard quota is consumed.
  if (request.causation_id != 0U && lineage_contains(request.causation_id)) {
    out.guard_reason = GuardReason::LoopBound;
    out.status = ActionStatus::Rejected;
    ++rejected_;
    return ActionStatus::Rejected;
  }
  // Step 4: capacity and lease identity before the guard so a decline consumes no guard quota and
  // journals nothing. The lease check is a non-mutating `precheck`; the exclusive lease is acquired
  // only after an authorized guard decision (step 7), so a guard decline mutates no lease entry.
  if (!request.immediate && pending_.size() >= config_.max_pending_actions) {
    out.status = ActionStatus::CapacityExhausted;
    return ActionStatus::CapacityExhausted;
  }
  // Retained request identities are durable keys. Reject a known duplicate before it can
  // consume a guard reservation or enter the pending queue.
  for (const PendingAction &pending : pending_) {
    if (pending.request_id == request.request_id) {
      out.status = ActionStatus::RejectedConfiguration;
      return out.status;
    }
  }
  for (const StimulationIntent &retained : journal_.recovered_intents()) {
    if (retained.request_id == request.request_id) {
      out.status = ActionStatus::RejectedConfiguration;
      return out.status;
    }
  }
  EndpointGeneration key{};
  if (request.action == StimulationAction::EmulateService) {
    key = lease_key_for(request);
    const LeaseStatus lease_pre = registry_.precheck(key, resolved_time.domain,
                                                     resolved_time.value, permit_.valid_until());
    if (lease_pre != LeaseStatus::Ok) {
      out.lease_status = lease_pre;
      out.status = ActionStatus::LeaseConflict;
      ++lease_conflicts_;
      return ActionStatus::LeaseConflict;
    }
  }
  // Step 5: only an active session authorizes; no guard call and no emission otherwise.
  if (session_state != LifecycleState::active) {
    out.status = ActionStatus::NotActive;
    return ActionStatus::NotActive;
  }
  // Step 6: evaluate the accepted guard exactly once, before any lease is acquired.
  GuardDiagnostic guard_out;
  const GuardOutcome decision = guard_.authorize(request, session_state, resolved_time, guard_out);
  if (decision != GuardOutcome::Authorized) {
    out.guard_reason = guard_out.reason;
    if (decision == GuardOutcome::Rejected) {
      out.status = ActionStatus::Rejected;
      ++rejected_;
      return ActionStatus::Rejected;
    }
    out.status = ActionStatus::Failed;
    ++failed_;
    return ActionStatus::Failed;
  }
  const std::uint64_t authorization_token = guard_.authorization_token();
  // Step 7: atomically acquire the exclusive lease for an authorized emulation action. Acquisition
  // is unconditional: a concurrently held generation is rejected by the registry's own conflict
  // classification, so a second owner never emits under a lease it does not own.
  if (request.action == StimulationAction::EmulateService) {
    const LeaseStatus lease = registry_.acquire(key, request.request_id, resolved_time.domain,
                                                resolved_time.value, permit_.valid_until());
    if (lease != LeaseStatus::Ok) {
      guard_.rollback_authorization(authorization_token);
      out.lease_status = lease;
      out.status = ActionStatus::LeaseConflict;
      ++lease_conflicts_;
      return ActionStatus::LeaseConflict;
    }
    held_leases_.push_back(HeldLease{key, request.request_id});
  }
  // Step 8: an authorized scheduled action enters the bounded queue; nothing is emitted yet.
  if (!request.immediate) {
    PendingAction pending;
    pending.request_id = request.request_id;
    pending.authorization_token = authorization_token;
    pending.action = request.action;
    pending.domain = resolved_time.domain;
    // A foreign clock cannot be ordered against permit-domain completion. The supplied
    // resolution is the only trusted execution deadline in that case.
    pending.scheduled_at = request.clock_domain == resolved_time.domain
                               ? request.scheduled_at : resolved_time.value;
    pending.immediate = false;
    pending.request = request;
    queue_locked(pending);
    out.status = ActionStatus::Queued;
    return ActionStatus::Queued;
  }
  // Step 9: journal the intent durably, then emit once outside every lock.
  const StimulationIntent intent = intent_for(request);
  const bool emulation = request.action == StimulationAction::EmulateService;
  if (emulation && !registry_.reserve_emission(key, request.request_id)) {
    guard_.rollback_authorization(authorization_token);
    (void)registry_.release(key, request.request_id);
    held_leases_.pop_back();
    out.status = ActionStatus::LeaseConflict;
    ++lease_conflicts_;
    return out.status;
  }
  EmissionAttempt attempt;
  try {
    attempt = journal_and_emit(lock, intent, payload, resolved_time.domain,
                               resolved_time.value);
  } catch (...) {
    if (emulation) {
      registry_.finish_emission(key, request.request_id);
    }
    if (!lock.owns_lock()) {
      lock.lock();
    }
    throw;
  }
  if (emulation) {
    registry_.finish_emission(key, request.request_id);
  }
  if (!lock.owns_lock()) {
    lock.lock();
  } else {
    guard_.rollback_authorization(authorization_token);
    if (request.action == StimulationAction::EmulateService) {
      (void)registry_.release(key, request.request_id);
      held_leases_.pop_back();
    }
  }
  out.journal_status = attempt.journal;
  out.emission_status = attempt.emission;
  out.status = classify_locked(attempt, request.request_id);
  return out.status;
}

bool StimulationActionPath::first_due_locked(ClockDomainId domain, Timestamp now,
                                             std::size_t &index) const {
  for (std::size_t position = 0U; position < pending_.size(); ++position) {
    // A pending action in another domain is never compared or ordered.
    if (pending_[position].domain != domain) {
      continue;
    }
    if (pending_[position].scheduled_at <= now) {
      index = position;
      return true;
    }
  }
  return false;
}

ActionStatus StimulationActionPath::emit_pending_locked(std::unique_lock<std::mutex> &lock,
                                                        std::size_t index, Timestamp now) {
  const PendingAction pending = pending_[index];
  pending_.erase(pending_.begin() + static_cast<std::ptrdiff_t>(index));
  const bool emulation = pending.request.action == StimulationAction::EmulateService;
  const EndpointGeneration key = emulation ? lease_key_for(pending.request) : EndpointGeneration{};
  if (emulation) {
    if (!registry_.reserve_emission(key, pending.request_id)) {
      guard_.rollback_authorization(pending.authorization_token);
      release_held_lease_locked(key, pending.request_id);
      ++cancelled_;
      return ActionStatus::Cancelled;
    }
  }
  const StimulationIntent intent = intent_for(pending.request);
  EmissionAttempt attempt;
  try {
    attempt = journal_and_emit(lock, intent, {}, pending.domain, now);
  } catch (...) {
    if (emulation) {
      registry_.finish_emission(key, pending.request_id);
    }
    if (!lock.owns_lock()) {
      lock.lock();
    }
    throw;
  }
  if (emulation) {
    registry_.finish_emission(key, pending.request_id);
  }
  if (!lock.owns_lock()) {
    lock.lock();
  }
  if (!attempt.emission_started) {
    guard_.rollback_authorization(pending.authorization_token);
    if (emulation) {
      release_held_lease_locked(key, pending.request_id);
    }
  }
  return classify_locked(attempt, pending.request_id);
}

std::size_t StimulationActionPath::cancel_all_locked() {
  const std::size_t count = pending_.size();
  pending_.clear();
  cancelled_ += count;
  return count;
}

void StimulationActionPath::release_held_lease_locked(const EndpointGeneration &key,
                                                       std::uint64_t request_id) {
  for (auto entry = held_leases_.begin(); entry != held_leases_.end(); ++entry) {
    if (entry->key == key && entry->request_id == request_id) {
      (void)registry_.release(key, request_id);
      held_leases_.erase(entry);
      return;
    }
  }
}

std::size_t StimulationActionPath::release_all_locked() {
  std::size_t count = 0U;
  for (const HeldLease &held : held_leases_) {
    if (registry_.release(held.key, held.request_id) == LeaseStatus::Ok) {
      ++count;
    }
  }
  held_leases_.clear();
  return count;
}

std::size_t StimulationActionPath::expire_all_locked() {
  std::size_t count = 0U;
  for (const HeldLease &held : held_leases_) {
    if (registry_.expire_key(held.key) == LeaseStatus::Ok) {
      ++count;
    }
  }
  held_leases_.clear();
  return count;
}

std::size_t StimulationActionPath::incomplete_count() const {
  return journal_.snapshot().orphan_intents;
}

bool StimulationActionPath::completion_domain_ok(const CompletionRequest &request) const noexcept {
  return open_ && request.domain == permit_.validity_domain();
}

CompletionReport StimulationActionPath::drain(const CompletionRequest &request) {
  std::unique_lock<std::mutex> lock(mutex_);
  CompletionReport report;
  if (!completion_domain_ok(request)) {
    report.outcome = CompletionOutcome::None;
    return report;
  }
  if (is_terminal(request.session_state)) {
    report.cancelled = cancel_all_locked();
    report.released_leases = release_all_locked();
    report.evidence_incomplete = incomplete_count();
    drain_state_ = DrainState::Cancelled;
    switch (request.session_state) {
    case LifecycleState::expired:
      report.outcome = CompletionOutcome::Expired;
      break;
    case LifecycleState::revoked:
      report.outcome = CompletionOutcome::Revoked;
      break;
    case LifecycleState::evidence_incomplete:
      report.outcome = CompletionOutcome::EvidenceIncomplete;
      break;
    case LifecycleState::closed:
    default:
      // A durable intent without a durable outcome is never masked by a clean `Closed` outcome.
      report.outcome = report.evidence_incomplete > 0U ? CompletionOutcome::EvidenceIncomplete
                                                       : CompletionOutcome::Closed;
      break;
    }
    return report;
  }
  // A non-active, non-terminal caller state (`declared`/`armed`) authorizes no pending action.
  // Fail closed: cancel every pending action with zero emission and apply no drain outcome.
  if (request.session_state != LifecycleState::active &&
      request.session_state != LifecycleState::closing) {
    report.cancelled = cancel_all_locked();
    report.evidence_incomplete = incomplete_count();
    drain_state_ = DrainState::Cancelled;
    report.outcome = report.evidence_incomplete > 0U ? CompletionOutcome::EvidenceIncomplete
                                                     : CompletionOutcome::None;
    return report;
  }
  if (request.now < permit_.valid_from() || request.now >= permit_.valid_until()) {
    report.cancelled = cancel_all_locked();
    report.released_leases = release_all_locked();
    report.evidence_incomplete = incomplete_count();
    drain_state_ = DrainState::Cancelled;
    report.outcome = request.now >= permit_.valid_until() ? CompletionOutcome::Expired
                                                           : CompletionOutcome::None;
    return report;
  }
  std::size_t steps = 0U;
  while (steps < config_.max_drain_steps) {
    std::size_t index = 0U;
    if (!first_due_locked(request.domain, request.now, index)) {
      break;
    }
    ++steps;
    if (is_late(request.now, pending_[index].scheduled_at, config_.late_tolerance)) {
      if (config_.late_policy == LateItemPolicy::RejectLate) {
        ++expired_;
      } else {
        ++discarded_;
      }
      pending_.erase(pending_.begin() + static_cast<std::ptrdiff_t>(index));
      continue;
    }
    const ActionStatus status = emit_pending_locked(lock, index, request.now);
    if (status == ActionStatus::Emitted) {
      ++report.drained;
    } else if (status == ActionStatus::Cancelled) {
      ++report.cancelled;
    } else if (status == ActionStatus::EvidenceIncomplete) {
      ++report.evidence_incomplete;
    } else {
      // A due, previously authorized action whose durable intent could not be recorded (a journal
      // failure) or whose host outcome was not delivered is surfaced, never silently dropped.
      ++report.failed;
    }
  }
  if (pending_.empty()) {
    drain_state_ = DrainState::Drained;
    // A durable intent without a durable outcome is never masked by a clean `Drained` outcome; the
    // authoritative orphan count already includes a drain-time outcome-append failure, so assign it
    // rather than adding the per-action loop count.
    report.evidence_incomplete = incomplete_count();
    // A dropped or evidence-incomplete action is never reported as a clean drain.
    report.outcome = (report.evidence_incomplete > 0U || report.failed > 0U)
                         ? CompletionOutcome::EvidenceIncomplete
                         : CompletionOutcome::Drained;
  } else {
    drain_state_ = DrainState::Idle;
    report.outcome = CompletionOutcome::None;
  }
  return report;
}

CompletionReport StimulationActionPath::close(const CompletionRequest &request) {
  std::unique_lock<std::mutex> lock(mutex_);
  CompletionReport report;
  if (!completion_domain_ok(request)) {
    report.outcome = CompletionOutcome::None;
    return report;
  }
  if (is_terminal(request.session_state)) {
    report.cancelled = cancel_all_locked();
    report.released_leases = release_all_locked();
    report.evidence_incomplete = incomplete_count();
    drain_state_ = DrainState::Cancelled;
    switch (request.session_state) {
    case LifecycleState::expired:
      report.outcome = CompletionOutcome::Expired;
      break;
    case LifecycleState::revoked:
      report.outcome = CompletionOutcome::Revoked;
      break;
    case LifecycleState::evidence_incomplete:
      report.outcome = CompletionOutcome::EvidenceIncomplete;
      break;
    case LifecycleState::closed:
    default:
      // A durable intent without a durable outcome is never masked by a clean `Closed` outcome.
      report.outcome = report.evidence_incomplete > 0U ? CompletionOutcome::EvidenceIncomplete
                                                       : CompletionOutcome::Closed;
      break;
    }
    return report;
  }
  // A non-active, non-terminal caller state (`declared`/`armed`) authorizes no pending action.
  // Fail closed: cancel every pending action with zero emission and apply no close outcome.
  if (request.session_state != LifecycleState::active &&
      request.session_state != LifecycleState::closing) {
    report.cancelled = cancel_all_locked();
    report.evidence_incomplete = incomplete_count();
    drain_state_ = DrainState::Cancelled;
    report.outcome = report.evidence_incomplete > 0U ? CompletionOutcome::EvidenceIncomplete
                                                     : CompletionOutcome::None;
    return report;
  }
  if (request.now < permit_.valid_from() || request.now >= permit_.valid_until()) {
    report.cancelled = cancel_all_locked();
    report.released_leases = release_all_locked();
    report.evidence_incomplete = incomplete_count();
    drain_state_ = DrainState::Cancelled;
    report.outcome = request.now >= permit_.valid_until() ? CompletionOutcome::Expired
                                                           : CompletionOutcome::None;
    return report;
  }
  std::size_t steps = 0U;
  while (steps < config_.max_drain_steps) {
    std::size_t index = 0U;
    if (!first_due_locked(request.domain, request.now, index)) {
      break;
    }
    ++steps;
    if (is_late(request.now, pending_[index].scheduled_at, config_.late_tolerance)) {
      if (config_.late_policy == LateItemPolicy::RejectLate) {
        ++expired_;
      } else {
        ++discarded_;
      }
      pending_.erase(pending_.begin() + static_cast<std::ptrdiff_t>(index));
      continue;
    }
    const ActionStatus status = emit_pending_locked(lock, index, request.now);
    if (status == ActionStatus::Emitted) {
      ++report.drained;
    } else if (status == ActionStatus::Cancelled) {
      ++report.cancelled;
    } else if (status == ActionStatus::EvidenceIncomplete) {
      ++report.evidence_incomplete;
    } else {
      // A dropped due action is surfaced explicitly rather than reported as a clean close.
      ++report.failed;
    }
  }
  report.cancelled += cancel_all_locked();
  report.released_leases = release_all_locked();
  // Count each distinct durable intent without a durable outcome once: the authoritative journal
  // orphan count supersedes the per-action loop increment (which the same intent also produced).
  report.evidence_incomplete = incomplete_count();
  drain_state_ = DrainState::Drained;
  report.outcome = (report.evidence_incomplete > 0U || report.failed > 0U)
                       ? CompletionOutcome::EvidenceIncomplete
                       : CompletionOutcome::Closed;
  return report;
}

CompletionReport StimulationActionPath::revoke(const CompletionRequest &request) {
  std::lock_guard<std::mutex> lock(mutex_);
  CompletionReport report;
  if (!completion_domain_ok(request)) {
    report.outcome = CompletionOutcome::None;
    return report;
  }
  report.cancelled = cancel_all_locked();
  report.released_leases = release_all_locked();
  report.evidence_incomplete = incomplete_count();
  drain_state_ = DrainState::Cancelled;
  report.outcome = CompletionOutcome::Revoked;
  return report;
}

CompletionReport StimulationActionPath::expire(const CompletionRequest &request) {
  std::lock_guard<std::mutex> lock(mutex_);
  CompletionReport report;
  if (!completion_domain_ok(request)) {
    report.outcome = CompletionOutcome::None;
    return report;
  }
  report.cancelled = cancel_all_locked();
  report.expired_leases = expire_all_locked();
  report.evidence_incomplete = incomplete_count();
  drain_state_ = DrainState::Cancelled;
  report.outcome = CompletionOutcome::Expired;
  return report;
}

CompletionReport StimulationActionPath::mark_evidence_incomplete(const CompletionRequest &request) {
  std::lock_guard<std::mutex> lock(mutex_);
  CompletionReport report;
  if (!completion_domain_ok(request)) {
    report.outcome = CompletionOutcome::None;
    return report;
  }
  report.cancelled = cancel_all_locked();
  report.released_leases = release_all_locked();
  report.evidence_incomplete = incomplete_count();
  drain_state_ = DrainState::Cancelled;
  report.outcome = CompletionOutcome::EvidenceIncomplete;
  return report;
}

ActionPathSnapshot StimulationActionPath::snapshot() const {
  std::lock_guard<std::mutex> lock(mutex_);
  ActionPathSnapshot result;
  result.open = open_;
  result.pending = pending_.size();
  result.lineage_entries = lineage_.size();
  result.emitted = emitted_;
  result.emission_rejected = emission_rejected_;
  result.emission_unavailable = emission_unavailable_;
  result.rejected = rejected_;
  result.failed = failed_;
  result.cancelled = cancelled_;
  result.expired = expired_;
  result.discarded = discarded_;
  result.evidence_incomplete = evidence_incomplete_;
  result.lease_conflicts = lease_conflicts_;
  result.drain_state = drain_state_;
  return result;
}

bool StimulationActionPath::is_open() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return open_;
}

} // namespace xverse::xcom::validation
