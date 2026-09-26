/**
 * \file validation_session.cpp
 * \brief Implementation of the standalone T025 time-authority, permit, and
 *        validation-session foundation.
 *
 * This translation unit uses only the C++20 standard library and the candidate public
 * header. It performs no file, socket, environment, logging, telemetry, or network I/O.
 */

#include <xverse/xcom/validation_session.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <span>
#include <utility>

namespace xverse::xcom::validation {
/// \brief File-local helpers for permit content serialization and field comparison.
/// \unitspec{T025-U-PERMIT}
namespace {

/// \brief Returns the exact full-range unsigned distance between two signed timestamps.
/// \param left First timestamp.
/// \param right Second timestamp.
/// \return The absolute difference as an unsigned 64-bit value, exact over the entire signed
///         64-bit domain (maximum `UINT64_MAX`). The magnitude is computed from the ordering
///         of the original signed values, so it never wraps modulo 2^64 and never treats the
///         top bit as a sign bit.
/// \unitspec{T025-U-TIME}
[[nodiscard]] std::uint64_t unsigned_distance(Timestamp left, Timestamp right) noexcept {
  return left >= right ? static_cast<std::uint64_t>(left) - static_cast<std::uint64_t>(right)
                       : static_cast<std::uint64_t>(right) - static_cast<std::uint64_t>(left);
}

/// \brief Appends a 64-bit value to a byte vector in little-endian order.
/// \param out Destination byte vector.
/// \param value Value to append.
/// \unitspec{T025-U-PERMIT}
void append_u64(std::vector<std::uint8_t> &out, std::uint64_t value) {
  for (std::size_t index = 0; index < 8; ++index) {
    out.push_back(static_cast<std::uint8_t>((value >> (index * 8U)) & 0xFFU));
  }
}

/// \brief Appends raw bytes to a byte vector.
/// \param out Destination byte vector.
/// \param bytes Bytes to append.
/// \unitspec{T025-U-PERMIT}
void append_bytes(std::vector<std::uint8_t> &out, std::span<const std::uint8_t> bytes) {
  out.insert(out.end(), bytes.begin(), bytes.end());
}

/// \brief Appends a length-prefixed tag text to a byte vector.
/// \param out Destination byte vector.
/// \param text Tag text to append.
/// \unitspec{T025-U-PERMIT}
void append_tag(std::vector<std::uint8_t> &out, const std::string &text) {
  append_u64(out, static_cast<std::uint64_t>(text.size()));
  append_bytes(out, std::span<const std::uint8_t>(
                        reinterpret_cast<const std::uint8_t *>(text.data()), text.size()));
}

/// \brief Reports whether a fixed-size byte array is all zero.
/// \tparam N Array length.
/// \param value Array to test.
/// \return `true` when every byte is zero.
/// \unitspec{T025-U-PERMIT}
template <std::size_t N>
[[nodiscard]] bool is_zero_bytes(const std::array<std::uint8_t, N> &value) noexcept {
  for (const std::uint8_t byte : value) {
    if (byte != 0U) {
      return false;
    }
  }
  return true;
}

/// \brief Reports whether a quota kind is one of the two defined kinds.
/// \param kind Quota kind to test.
/// \return `true` for `Operations` and `Evidence`.
/// \unitspec{T025-U-PERMIT}
[[nodiscard]] bool is_known_quota_kind(QuotaKind kind) noexcept {
  return kind == QuotaKind::Operations || kind == QuotaKind::Evidence;
}

/// \brief Orders two quota entries for set comparison.
/// \param left First quota entry.
/// \param right Second quota entry.
/// \return `true` when `left` sorts before `right`.
/// \unitspec{T025-U-PERMIT}
[[nodiscard]] bool quota_less(const Quota &left, const Quota &right) noexcept {
  if (left.kind != right.kind) {
    return static_cast<std::uint8_t>(left.kind) < static_cast<std::uint8_t>(right.kind);
  }
  return left.limit < right.limit;
}

/// \brief Reports whether two action-mask lists hold the same set of masks.
/// \param left First mask list.
/// \param right Second mask list.
/// \return `true` when both lists contain the same masks regardless of order.
/// \unitspec{T025-U-PERMIT}
[[nodiscard]] bool same_action_set(const std::vector<ActionMask> &left,
                                   const std::vector<ActionMask> &right) {
  std::vector<ActionMask> left_sorted = left;
  std::vector<ActionMask> right_sorted = right;
  std::sort(left_sorted.begin(), left_sorted.end());
  std::sort(right_sorted.begin(), right_sorted.end());
  return left_sorted == right_sorted;
}

/// \brief Reports whether two quota lists hold the same set of entries.
/// \param left First quota list.
/// \param right Second quota list.
/// \return `true` when both lists contain the same entries regardless of order.
/// \unitspec{T025-U-PERMIT}
[[nodiscard]] bool same_quota_set(const std::vector<Quota> &left, const std::vector<Quota> &right) {
  std::vector<Quota> left_sorted = left;
  std::vector<Quota> right_sorted = right;
  std::sort(left_sorted.begin(), left_sorted.end(), quota_less);
  std::sort(right_sorted.begin(), right_sorted.end(), quota_less);
  return left_sorted == right_sorted;
}

/// \brief Serializes a permit envelope (excluding the session identity) into bytes.
/// \param permit Permit to serialize.
/// \return The deterministic byte image used for the permit content digest.
/// \unitspec{T025-U-PERMIT}
[[nodiscard]] std::vector<std::uint8_t> permit_envelope_bytes(const Permit &permit) {
  std::vector<std::uint8_t> bytes;
  append_bytes(bytes, permit.plan_digest());
  append_tag(bytes, permit.scenario());
  append_tag(bytes, permit.deployment());
  append_tag(bytes, permit.environment());
  append_tag(bytes, permit.tool());
  append_tag(bytes, permit.interface_name());
  append_tag(bytes, permit.target());
  append_u64(bytes, permit.nonce());
  append_u64(bytes, static_cast<std::uint64_t>(permit.validity_domain()));
  append_u64(bytes, static_cast<std::uint64_t>(permit.valid_from()));
  append_u64(bytes, static_cast<std::uint64_t>(permit.valid_until()));
  std::vector<ActionMask> actions = permit.allowed_actions();
  std::sort(actions.begin(), actions.end());
  append_u64(bytes, static_cast<std::uint64_t>(actions.size()));
  for (const ActionMask mask : actions) {
    append_u64(bytes, static_cast<std::uint64_t>(mask));
  }
  std::vector<Quota> quotas = permit.quotas();
  std::sort(quotas.begin(), quotas.end(), quota_less);
  append_u64(bytes, static_cast<std::uint64_t>(quotas.size()));
  for (const Quota &quota : quotas) {
    append_u64(bytes, static_cast<std::uint64_t>(quota.kind));
    append_u64(bytes, static_cast<std::uint64_t>(quota.limit));
  }
  return bytes;
}

/// \brief Returns the locator of the first field where the context differs from the permit.
/// \param permit Immutable permit.
/// \param context Asserted runtime envelope.
/// \return The first mismatching field locator, or `std::nullopt` when all fields match.
/// \unitspec{T025-U-PERMIT}
[[nodiscard]] std::optional<FieldLocator> first_mismatch(const Permit &permit,
                                                         const SessionContext &context) {
  if (permit.session_id() != context.session_id) {
    return FieldLocator::SessionId;
  }
  if (permit.plan_digest() != context.plan_digest) {
    return FieldLocator::PlanDigest;
  }
  if (permit.scenario() != context.scenario) {
    return FieldLocator::Scenario;
  }
  if (permit.deployment() != context.deployment) {
    return FieldLocator::Deployment;
  }
  if (permit.environment() != context.environment) {
    return FieldLocator::Environment;
  }
  if (permit.tool() != context.tool) {
    return FieldLocator::Tool;
  }
  if (permit.interface_name() != context.interface_name) {
    return FieldLocator::Interface;
  }
  if (permit.target() != context.target) {
    return FieldLocator::Target;
  }
  if (permit.nonce() != context.nonce) {
    return FieldLocator::Nonce;
  }
  if (!same_action_set(permit.allowed_actions(), context.allowed_actions)) {
    return FieldLocator::AllowedActions;
  }
  if (permit.validity_domain() != context.validity_domain ||
      permit.valid_from() != context.valid_from || permit.valid_until() != context.valid_until) {
    return FieldLocator::Validity;
  }
  if (!same_quota_set(permit.quotas(), context.quotas)) {
    return FieldLocator::Quota;
  }
  return std::nullopt;
}

} // namespace

Diagnostic Diagnostic::from_first(std::initializer_list<Result> applicable,
                                  std::optional<std::uint32_t> locator) noexcept {
  Diagnostic diagnostic;
  diagnostic.size_ = 1;
  Result best = Result::Ok;
  bool assigned = false;
  for (const Result candidate : applicable) {
    if (!assigned || precedence_rank(candidate) < precedence_rank(best)) {
      best = candidate;
      assigned = true;
    }
  }
  diagnostic.codes_[0] = best;
  diagnostic.locator_ = locator;
  return diagnostic;
}

Diagnostic Diagnostic::accumulate(std::initializer_list<Result> codes,
                                  std::optional<std::uint32_t> locator) noexcept {
  Diagnostic diagnostic;
  diagnostic.locator_ = locator;
  for (const Result code : codes) {
    if (diagnostic.size_ >= capacity) {
      break;
    }
    diagnostic.codes_[diagnostic.size_] = code;
    ++diagnostic.size_;
  }
  std::sort(
      diagnostic.codes_.begin(),
      diagnostic.codes_.begin() + static_cast<std::ptrdiff_t>(diagnostic.size_),
      [](Result left, Result right) { return precedence_rank(left) < precedence_rank(right); });
  return diagnostic;
}

std::span<const Result> Diagnostic::codes() const noexcept {
  return std::span<const Result>(codes_.data(), size_);
}

Result Diagnostic::primary() const noexcept { return size_ == 0 ? Result::Ok : codes_.front(); }

std::size_t Diagnostic::size() const noexcept { return size_; }

bool Diagnostic::empty() const noexcept { return size_ == 0; }

std::optional<std::uint32_t> Diagnostic::locator() const noexcept { return locator_; }

Tag::Tag(std::string value) : value_(std::move(value)) {}

std::optional<Tag> Tag::make(std::string_view candidate) {
  if (!is_valid(candidate)) {
    return std::nullopt;
  }
  return Tag(std::string(candidate));
}

bool Tag::is_valid(std::string_view candidate) noexcept {
  if (candidate.empty() || candidate.size() > max_length) {
    return false;
  }
  for (const char character : candidate) {
    const auto code = static_cast<unsigned char>(character);
    if (code == 0U || code < 0x20U || code > 0x7EU) {
      return false;
    }
  }
  return true;
}

const std::string &Tag::value() const noexcept { return value_; }

bool Tag::empty() const noexcept { return value_.empty(); }

const SessionId &Permit::session_id() const noexcept { return session_id_; }
const PlanDigest &Permit::plan_digest() const noexcept { return plan_digest_; }
const std::string &Permit::scenario() const noexcept { return scenario_; }
const std::string &Permit::deployment() const noexcept { return deployment_; }
const std::string &Permit::environment() const noexcept { return environment_; }
const std::string &Permit::tool() const noexcept { return tool_; }
const std::string &Permit::interface_name() const noexcept { return interface_name_; }
const std::string &Permit::target() const noexcept { return target_; }
Nonce Permit::nonce() const noexcept { return nonce_; }
ClockDomainId Permit::validity_domain() const noexcept { return validity_domain_; }
Timestamp Permit::valid_from() const noexcept { return valid_from_; }
Timestamp Permit::valid_until() const noexcept { return valid_until_; }
const std::vector<ActionMask> &Permit::allowed_actions() const noexcept { return allowed_actions_; }
const std::vector<Quota> &Permit::quotas() const noexcept { return quotas_; }
const PermitId &Permit::permit_id() const noexcept { return permit_id_; }

bool Permit::allows(ActionMask mask) const noexcept {
  for (const ActionMask allowed : allowed_actions_) {
    if (allowed == mask) {
      return true;
    }
  }
  return false;
}

Result PermitBuilder::set_session_id(const SessionId &value) noexcept {
  session_id_ = value;
  return Result::Ok;
}

Result PermitBuilder::set_plan_digest(const PlanDigest &value) noexcept {
  plan_digest_ = value;
  return Result::Ok;
}

Result PermitBuilder::set_scenario(std::string value) {
  scenario_ = std::move(value);
  return Result::Ok;
}

Result PermitBuilder::set_deployment(std::string value) {
  deployment_ = std::move(value);
  return Result::Ok;
}

Result PermitBuilder::set_environment(std::string value) {
  environment_ = std::move(value);
  return Result::Ok;
}

Result PermitBuilder::set_tool(std::string value) {
  tool_ = std::move(value);
  return Result::Ok;
}

Result PermitBuilder::set_interface(std::string value) {
  interface_name_ = std::move(value);
  return Result::Ok;
}

Result PermitBuilder::set_target(std::string value) {
  target_ = std::move(value);
  return Result::Ok;
}

Result PermitBuilder::set_nonce(Nonce value) noexcept {
  nonce_ = value;
  return Result::Ok;
}

Result PermitBuilder::set_validity(ClockDomainId domain, Timestamp from, Timestamp until) noexcept {
  validity_domain_ = domain;
  valid_from_ = from;
  valid_until_ = until;
  return Result::Ok;
}

Result PermitBuilder::add_allowed_action(ActionMask mask) noexcept {
  allowed_actions_.push_back(mask);
  return Result::Ok;
}

Result PermitBuilder::add_quota(Quota quota) noexcept {
  quotas_.push_back(quota);
  return Result::Ok;
}

Result PermitBuilder::build(Permit &out) const {
  last_locator_.reset();
  const auto fail = [this](FieldLocator locator) -> Result {
    last_locator_ = locator;
    return Result::InvalidPermit;
  };
  if (is_zero_bytes(session_id_)) {
    return fail(FieldLocator::SessionId);
  }
  if (is_zero_bytes(plan_digest_)) {
    return fail(FieldLocator::PlanDigest);
  }
  if (!Tag::is_valid(scenario_)) {
    return fail(FieldLocator::Scenario);
  }
  if (!Tag::is_valid(deployment_)) {
    return fail(FieldLocator::Deployment);
  }
  if (!Tag::is_valid(environment_)) {
    return fail(FieldLocator::Environment);
  }
  if (!Tag::is_valid(tool_)) {
    return fail(FieldLocator::Tool);
  }
  if (!Tag::is_valid(interface_name_)) {
    return fail(FieldLocator::Interface);
  }
  if (!Tag::is_valid(target_)) {
    return fail(FieldLocator::Target);
  }
  if (allowed_actions_.empty() || allowed_actions_.size() > max_allowed_actions) {
    return fail(FieldLocator::AllowedActions);
  }
  for (const ActionMask mask : allowed_actions_) {
    if (!is_single_action(mask) || !is_defined_action(mask)) {
      return fail(FieldLocator::AllowedActions);
    }
  }
  if (validity_domain_ == kInvalidClockDomain || valid_from_ > valid_until_) {
    return fail(FieldLocator::Validity);
  }
  if (quotas_.size() > max_quotas) {
    return fail(FieldLocator::Quota);
  }
  for (const Quota &quota : quotas_) {
    if (!is_known_quota_kind(quota.kind) || quota.limit == 0U) {
      return fail(FieldLocator::Quota);
    }
  }
  Permit built;
  built.session_id_ = session_id_;
  built.plan_digest_ = plan_digest_;
  built.scenario_ = scenario_;
  built.deployment_ = deployment_;
  built.environment_ = environment_;
  built.tool_ = tool_;
  built.interface_name_ = interface_name_;
  built.target_ = target_;
  built.nonce_ = nonce_;
  built.validity_domain_ = validity_domain_;
  built.valid_from_ = valid_from_;
  built.valid_until_ = valid_until_;
  built.allowed_actions_ = allowed_actions_;
  built.quotas_ = quotas_;
  built.permit_id_ = canonical_digest(permit_envelope_bytes(built));
  out = built;
  return Result::Ok;
}

std::optional<FieldLocator> PermitBuilder::last_locator() const noexcept { return last_locator_; }

TimeAuthority::TimeAuthority(std::size_t max_domains, std::size_t max_mappings)
    : clocks_(max_domains), mappings_(max_mappings) {}

TimeAuthority::ClockEntry *TimeAuthority::find_clock_locked(ClockDomainId id) noexcept {
  for (ClockEntry &entry : clocks_) {
    if (entry.occupied && entry.id == id) {
      return &entry;
    }
  }
  return nullptr;
}

const TimeAuthority::ClockEntry *TimeAuthority::find_clock_locked(ClockDomainId id) const noexcept {
  for (const ClockEntry &entry : clocks_) {
    if (entry.occupied && entry.id == id) {
      return &entry;
    }
  }
  return nullptr;
}

const TimeAuthority::MappingEntry *
TimeAuthority::find_mapping_locked(ClockDomainId src, ClockDomainId dst) const noexcept {
  for (const MappingEntry &entry : mappings_) {
    if (entry.occupied && entry.src == src && entry.dst == dst) {
      return &entry;
    }
  }
  return nullptr;
}

Result TimeAuthority::declare_clock(ClockDomainId id, ClockSource source, ClockKind kind,
                                    Timestamp min_value, Timestamp max_value) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (id == kInvalidClockDomain || min_value > max_value) {
    return Result::UnknownClock;
  }
  ClockEntry *target = find_clock_locked(id);
  if (target == nullptr) {
    for (ClockEntry &entry : clocks_) {
      if (!entry.occupied) {
        target = &entry;
        break;
      }
    }
  }
  if (target == nullptr) {
    return Result::CapacityExhausted;
  }
  target->id = id;
  target->kind = kind;
  target->min_value = min_value;
  target->max_value = max_value;
  target->source = std::move(source);
  target->baseline.reset();
  // Every successful (re-)declaration receives a fresh generation, so a deferred commit of an
  // observation captured under a previous declaration can never be attributed to this one.
  target->declaration = ++declaration_counter_;
  target->occupied = true;
  return Result::Ok;
}

Result TimeAuthority::declare_mapping(ClockDomainId src, ClockDomainId dst, SignedOffset offset,
                                      Tolerance tolerance) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (src == kInvalidClockDomain || dst == kInvalidClockDomain) {
    return Result::UnknownClock;
  }
  if (find_clock_locked(src) == nullptr || find_clock_locked(dst) == nullptr) {
    return Result::UnknownClock;
  }
  MappingEntry *target = nullptr;
  for (MappingEntry &entry : mappings_) {
    if (entry.occupied && entry.src == src && entry.dst == dst) {
      target = &entry;
      break;
    }
  }
  if (target == nullptr) {
    for (MappingEntry &entry : mappings_) {
      if (!entry.occupied) {
        target = &entry;
        break;
      }
    }
  }
  if (target == nullptr) {
    return Result::CapacityExhausted;
  }
  target->src = src;
  target->dst = dst;
  target->offset = offset;
  target->tolerance = tolerance;
  target->occupied = true;
  return Result::Ok;
}

Result TimeAuthority::read_clock_locked(ClockEntry &entry, Timestamp &out, bool commit_baseline) {
  if (!entry.source) {
    return Result::ClockSourceFailure;
  }
  const std::optional<Timestamp> reading = entry.source();
  if (!reading.has_value()) {
    return Result::ClockSourceFailure;
  }
  const Timestamp value = reading.value();
  if (value < entry.min_value || value > entry.max_value) {
    return Result::ClockOutOfBounds;
  }
  if (entry.kind == ClockKind::Monotonic && entry.baseline.has_value() &&
      value < entry.baseline.value()) {
    return Result::ClockRegression;
  }
  if (commit_baseline) {
    entry.baseline = value;
  }
  out = value;
  return Result::Ok;
}

Result TimeAuthority::now_impl(ClockDomainId id, Timestamp &out, bool commit_baseline,
                               std::uint64_t *declaration) {
  std::lock_guard<std::mutex> lock(mutex_);
  ClockEntry *entry = find_clock_locked(id);
  if (entry == nullptr) {
    return Result::UnknownClock;
  }
  const Result result = read_clock_locked(*entry, out, commit_baseline);
  if (result == Result::Ok && declaration != nullptr) {
    *declaration = entry->declaration;
  }
  return result;
}

Result TimeAuthority::now(ClockDomainId id, Timestamp &out) {
  return now_impl(id, out, /*commit_baseline=*/true);
}

Result TimeAuthority::convert_impl(ClockDomainId src, ClockDomainId dst, Timestamp value,
                                   Timestamp &out, bool commit_baseline,
                                   Timestamp *destination_reading,
                                   std::uint64_t *destination_declaration) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (find_clock_locked(src) == nullptr) {
    return Result::UnknownClock;
  }
  const MappingEntry *mapping = find_mapping_locked(src, dst);
  if (mapping == nullptr) {
    return Result::MissingMapping;
  }
  ClockEntry *destination = find_clock_locked(dst);
  if (destination == nullptr) {
    return Result::UnknownClock;
  }
  Timestamp candidate = 0;
  if (__builtin_add_overflow(value, mapping->offset, &candidate)) {
    return Result::ClockOverflow;
  }
  if (candidate < destination->min_value || candidate > destination->max_value) {
    return Result::ClockOutOfBounds;
  }
  Timestamp destination_now = 0;
  const Result read = read_clock_locked(*destination, destination_now, /*commit_baseline=*/false);
  if (read != Result::Ok) {
    return read;
  }
  if (destination_reading != nullptr) {
    *destination_reading = destination_now;
  }
  if (destination_declaration != nullptr) {
    *destination_declaration = destination->declaration;
  }
  const std::uint64_t distance = unsigned_distance(candidate, destination_now);
  if (distance > mapping->tolerance) {
    return Result::ToleranceExceeded;
  }
  if (commit_baseline) {
    destination->baseline = destination_now;
  }
  out = candidate;
  return Result::Ok;
}

Result TimeAuthority::convert(ClockDomainId src, ClockDomainId dst, Timestamp value,
                              Timestamp &out) {
  return convert_impl(src, dst, value, out, /*commit_baseline=*/true);
}

void TimeAuthority::advance_baseline(ClockDomainId id, Timestamp reading,
                                     std::uint64_t declaration) {
  std::lock_guard<std::mutex> lock(mutex_);
  ClockEntry *entry = find_clock_locked(id);
  if (entry == nullptr || entry->declaration != declaration) {
    // Undeclared, or re-declared after the observation was captured: the reading belongs to a
    // different clock declaration and must never seed this one's retained baseline.
    return;
  }
  if (!entry->baseline.has_value() || reading >= entry->baseline.value()) {
    entry->baseline = reading;
  }
}

std::optional<Timestamp> TimeAuthority::baseline(ClockDomainId id) const {
  std::lock_guard<std::mutex> lock(mutex_);
  const ClockEntry *entry = find_clock_locked(id);
  if (entry == nullptr) {
    return std::nullopt;
  }
  return entry->baseline;
}

std::size_t TimeAuthority::domain_count() const {
  std::lock_guard<std::mutex> lock(mutex_);
  std::size_t count = 0;
  for (const ClockEntry &entry : clocks_) {
    if (entry.occupied) {
      ++count;
    }
  }
  return count;
}

std::size_t TimeAuthority::mapping_count() const {
  std::lock_guard<std::mutex> lock(mutex_);
  std::size_t count = 0;
  for (const MappingEntry &entry : mappings_) {
    if (entry.occupied) {
      ++count;
    }
  }
  return count;
}

std::size_t ValidationSession::quota_index(QuotaKind kind) noexcept {
  if (kind == QuotaKind::Operations) {
    return 0;
  }
  if (kind == QuotaKind::Evidence) {
    return 1;
  }
  return kQuotaKindCount;
}

ValidationSession::ValidationSession(const PermitId &permit_id, const SessionId &session_id,
                                     const ControllerId &controller, Generation generation,
                                     const std::vector<Quota> &quotas, LifecycleState initial_state)
    : state_(initial_state), permit_id_(permit_id), session_id_(session_id),
      controller_(controller), generation_(generation) {
  for (const Quota &quota : quotas) {
    const std::size_t index = quota_index(quota.kind);
    if (index < kQuotaKindCount && quota.limit != 0U && quotas_[index] == 0U) {
      quotas_[index] = quota.limit;
    }
  }
}

Result ValidationSession::apply(Action action, Timestamp now) noexcept {
  static_cast<void>(now);
  const ActionMask mask = to_mask(action);
  if (!is_single_action(mask) || !is_defined_action(mask)) {
    return Result::UndefinedAction;
  }
  const TransitionOutcome outcome = transition_outcome(state_, action);
  if (outcome == TransitionOutcome::InvalidTransition) {
    return Result::InvalidTransition;
  }
  if (outcome == TransitionOutcome::TerminalState) {
    return Result::TerminalState;
  }
  if (quotas_[quota_index(QuotaKind::Operations)] == 0U) {
    return Result::QuotaExhausted;
  }
  if (outcome == TransitionOutcome::AlreadyApplied) {
    return Result::AlreadyApplied;
  }
  state_ = successor_state(state_, action);
  --quotas_[quota_index(QuotaKind::Operations)];
  return Result::Ok;
}

LifecycleState ValidationSession::state() const noexcept { return state_; }

bool ValidationSession::is_terminal() const noexcept { return validation::is_terminal(state_); }

std::uint32_t ValidationSession::remaining_quota(QuotaKind kind) const noexcept {
  const std::size_t index = quota_index(kind);
  return index < kQuotaKindCount ? quotas_[index] : 0U;
}

SessionSnapshot ValidationSession::snapshot() const noexcept {
  SessionSnapshot result;
  result.state = state_;
  result.permit_id = permit_id_;
  result.session_id = session_id_;
  result.controller = controller_;
  result.generation = generation_;
  result.operations_remaining = remaining_quota(QuotaKind::Operations);
  result.evidence_remaining = remaining_quota(QuotaKind::Evidence);
  return result;
}

const PermitId &ValidationSession::permit_id() const noexcept { return permit_id_; }

const SessionId &ValidationSession::session_id() const noexcept { return session_id_; }

const ControllerId &ValidationSession::controller() const noexcept { return controller_; }

Generation ValidationSession::generation() const noexcept { return generation_; }

PermitRegistry::PermitRegistry(std::size_t max_consumed_permits, std::size_t max_consumed_sessions)
    : max_permits_(max_consumed_permits), max_sessions_(max_consumed_sessions) {}

Result PermitRegistry::try_consume(const ControllerId &controller, const PermitId &permit_id,
                                   const SessionId &session_id) {
  std::lock_guard<std::mutex> lock(mutex_);
  for (const SessionKey &key : sessions_) {
    if (key.controller == controller && key.session == session_id) {
      return Result::SessionAlreadyConsumed;
    }
  }
  for (const PermitKey &key : permits_) {
    if (key.controller == controller && key.permit == permit_id) {
      return Result::PermitAlreadyConsumed;
    }
  }
  if (permits_.size() >= max_permits_ || sessions_.size() >= max_sessions_) {
    return Result::CapacityExhausted;
  }
  permits_.push_back(PermitKey{controller, permit_id});
  sessions_.push_back(SessionKey{controller, session_id});
  return Result::Ok;
}

bool PermitRegistry::is_consumed_permit(const ControllerId &controller,
                                        const PermitId &permit_id) const {
  std::lock_guard<std::mutex> lock(mutex_);
  for (const PermitKey &key : permits_) {
    if (key.controller == controller && key.permit == permit_id) {
      return true;
    }
  }
  return false;
}

bool PermitRegistry::is_consumed_session(const ControllerId &controller,
                                         const SessionId &session_id) const {
  std::lock_guard<std::mutex> lock(mutex_);
  for (const SessionKey &key : sessions_) {
    if (key.controller == controller && key.session == session_id) {
      return true;
    }
  }
  return false;
}

std::size_t PermitRegistry::capacity() const noexcept { return max_permits_; }

std::size_t PermitRegistry::size() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return permits_.size();
}

std::size_t PermitRegistry::session_size() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return sessions_.size();
}

SessionManager::SessionManager(ManagerConfig config)
    : config_(config), authority_(config.max_domains, config.max_mappings),
      registry_(config.max_consumed_permits, config.max_consumed_sessions),
      sessions_(config.max_sessions) {
  if (is_zero_bytes(config_.scope)) {
    throw std::invalid_argument("SessionManager requires a non-zero uniqueness scope");
  }
}

TimeAuthority &SessionManager::time_authority() noexcept { return authority_; }

const TimeAuthority &SessionManager::time_authority() const noexcept { return authority_; }

SessionManager::ControllerEntry *
SessionManager::find_controller_locked(const ControllerId &id) noexcept {
  for (ControllerEntry &entry : controllers_) {
    if (entry.id == id) {
      return &entry;
    }
  }
  return nullptr;
}

const SessionManager::ControllerEntry *
SessionManager::find_controller_locked(const ControllerId &id) const noexcept {
  for (const ControllerEntry &entry : controllers_) {
    if (entry.id == id) {
      return &entry;
    }
  }
  return nullptr;
}

bool SessionManager::any_session_with_id_locked(const SessionId &id) const noexcept {
  for (const SessionEntry &entry : sessions_) {
    if (entry.occupied && entry.session == id) {
      return true;
    }
  }
  return false;
}

Result SessionManager::locate_locked(const SessionHandle &handle,
                                     std::size_t &index) const noexcept {
  index = kNoIndex;
  if (handle.scope != config_.scope) {
    return Result::ForeignHandle;
  }
  const ControllerEntry *controller = find_controller_locked(handle.controller);
  if (controller == nullptr) {
    return any_session_with_id_locked(handle.session) ? Result::ForeignHandle
                                                      : Result::InvalidHandle;
  }
  if (controller->superseded) {
    return Result::RecreatedController;
  }
  if (handle.generation < controller->generation) {
    return Result::StaleHandle;
  }
  if (handle.generation > controller->generation) {
    return Result::InvalidHandle;
  }
  for (std::size_t position = 0; position < sessions_.size(); ++position) {
    const SessionEntry &entry = sessions_[position];
    if (entry.occupied && entry.controller == handle.controller &&
        entry.session == handle.session && entry.generation == handle.generation) {
      index = position;
      return Result::Ok;
    }
  }
  return Result::SessionNotFound;
}

SessionManager::SessionEntry *SessionManager::allocate_slot_locked() noexcept {
  for (SessionEntry &entry : sessions_) {
    if (!entry.occupied) {
      return &entry;
    }
  }
  for (SessionEntry &entry : sessions_) {
    if (entry.terminal) {
      return &entry;
    }
  }
  return nullptr;
}

std::size_t SessionManager::live_session_count_locked() const noexcept {
  std::size_t count = 0;
  for (const SessionEntry &entry : sessions_) {
    if (entry.occupied && !entry.terminal) {
      ++count;
    }
  }
  return count;
}

bool SessionManager::evict_one_superseded_locked() {
  if (superseded_order_.empty()) {
    return false;
  }
  const ControllerId oldest = superseded_order_.front();
  superseded_order_.erase(superseded_order_.begin());
  const auto removed = std::remove_if(
      controllers_.begin(), controllers_.end(),
      [&oldest](const ControllerEntry &entry) { return entry.superseded && entry.id == oldest; });
  controllers_.erase(removed, controllers_.end());
  return true;
}

Result SessionManager::register_controller(const ControllerId &id, std::string_view name) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (is_zero_bytes(id)) {
    last_diagnostic_ = Diagnostic::from_first({Result::InvalidController});
    return Result::InvalidController;
  }
  if (find_controller_locked(id) != nullptr) {
    last_diagnostic_ = Diagnostic::from_first({Result::InvalidController});
    return Result::InvalidController;
  }
  if (controllers_.size() >= config_.max_controllers && !evict_one_superseded_locked()) {
    last_diagnostic_ = Diagnostic::from_first({Result::CapacityExhausted});
    return Result::CapacityExhausted;
  }
  for (ControllerEntry &entry : controllers_) {
    if (!entry.superseded && entry.name == name) {
      entry.superseded = true;
      superseded_order_.push_back(entry.id);
    }
  }
  while (superseded_order_.size() > config_.max_superseded) {
    const ControllerId oldest = superseded_order_.front();
    superseded_order_.erase(superseded_order_.begin());
    const auto removed = std::remove_if(
        controllers_.begin(), controllers_.end(),
        [&oldest](const ControllerEntry &entry) { return entry.superseded && entry.id == oldest; });
    controllers_.erase(removed, controllers_.end());
  }
  controllers_.push_back(ControllerEntry{id, std::string(name), Generation{1}, false});
  last_diagnostic_ = Diagnostic::from_first({Result::Ok});
  return Result::Ok;
}

Generation SessionManager::advance_generation(const ControllerId &controller) {
  std::lock_guard<std::mutex> lock(mutex_);
  ControllerEntry *entry = find_controller_locked(controller);
  if (entry == nullptr || entry->superseded) {
    return 0;
  }
  ++entry->generation;
  return entry->generation;
}

Result SessionManager::consume(const ControllerId &controller, const Permit &permit,
                               const SessionContext &context, SessionHandle &out) {
  std::lock_guard<std::mutex> lock(mutex_);
  const ControllerEntry *owner = find_controller_locked(controller);
  if (owner == nullptr) {
    last_diagnostic_ = Diagnostic::from_first({Result::ForeignHandle});
    return Result::ForeignHandle;
  }
  if (owner->superseded) {
    last_diagnostic_ = Diagnostic::from_first({Result::RecreatedController});
    return Result::RecreatedController;
  }
  const std::optional<FieldLocator> mismatch = first_mismatch(permit, context);
  if (mismatch.has_value()) {
    last_diagnostic_ = Diagnostic::from_first({Result::PermitMismatch},
                                              static_cast<std::uint32_t>(mismatch.value()));
    return Result::PermitMismatch;
  }
  // Replay precedes live-session capacity (design §7.3). These probes are read-only, so a
  // replayed identity is reported before a full session table can mask it as CapacityExhausted.
  if (registry_.is_consumed_session(controller, permit.session_id())) {
    last_diagnostic_ = Diagnostic::from_first({Result::SessionAlreadyConsumed});
    return Result::SessionAlreadyConsumed;
  }
  if (registry_.is_consumed_permit(controller, permit.permit_id())) {
    last_diagnostic_ = Diagnostic::from_first({Result::PermitAlreadyConsumed});
    return Result::PermitAlreadyConsumed;
  }
  SessionEntry *slot = allocate_slot_locked();
  if (slot == nullptr) {
    last_diagnostic_ = Diagnostic::from_first({Result::CapacityExhausted});
    return Result::CapacityExhausted;
  }
  // The atomic check-then-insert runs only after a session slot is available, so an unconsumed
  // permit is never persisted when no slot can be bound (transactional capacity rejection).
  const Result consumed =
      registry_.try_consume(controller, permit.permit_id(), permit.session_id());
  if (consumed != Result::Ok) {
    last_diagnostic_ = Diagnostic::from_first({consumed});
    return consumed;
  }
  slot->occupied = true;
  slot->terminal = false;
  slot->controller = controller;
  slot->generation = owner->generation;
  slot->session = permit.session_id();
  slot->permit = permit;
  slot->validation = ValidationSession(permit.permit_id(), permit.session_id(), controller,
                                       owner->generation, permit.quotas());
  out = SessionHandle{config_.scope, controller, owner->generation, permit.session_id()};
  last_diagnostic_ = Diagnostic::from_first({Result::Ok});
  return Result::Ok;
}

Result SessionManager::transition(const SessionHandle &handle, Action action,
                                  ClockDomainId now_domain, Timestamp now_value, Diagnostic &out) {
  std::lock_guard<std::mutex> lock(mutex_);
  std::size_t index = kNoIndex;
  const Result located = locate_locked(handle, index);
  if (located != Result::Ok) {
    out = Diagnostic::from_first({located});
    last_diagnostic_ = out;
    return located;
  }
  SessionEntry &entry = sessions_[index];
  const Permit &permit = entry.permit.value();
  Timestamp auth_now = 0;
  std::uint64_t now_declaration = 0;
  const Result now_result =
      authority_.now_impl(now_domain, auth_now, /*commit_baseline=*/false, &now_declaration);
  if (now_result != Result::Ok) {
    out = Diagnostic::from_first({now_result});
    last_diagnostic_ = out;
    return now_result;
  }
  if (unsigned_distance(now_value, auth_now) != 0U) {
    out = Diagnostic::from_first({Result::ToleranceExceeded});
    last_diagnostic_ = out;
    return Result::ToleranceExceeded;
  }
  Timestamp resolved = auth_now;
  ClockDomainId mapped_domain = kInvalidClockDomain;
  Timestamp mapped_reading = 0;
  std::uint64_t mapped_declaration = 0;
  if (now_domain != permit.validity_domain()) {
    Timestamp mapped = 0;
    const Result converted =
        authority_.convert_impl(now_domain, permit.validity_domain(), auth_now, mapped,
                                /*commit_baseline=*/false, &mapped_reading, &mapped_declaration);
    if (converted != Result::Ok) {
      out = Diagnostic::from_first({converted});
      last_diagnostic_ = out;
      return converted;
    }
    resolved = mapped;
    mapped_domain = permit.validity_domain();
  }
  if (resolved < permit.valid_from()) {
    out = Diagnostic::from_first({Result::PermitNotYetValid});
    last_diagnostic_ = out;
    return Result::PermitNotYetValid;
  }
  if (resolved >= permit.valid_until()) {
    out = Diagnostic::from_first({Result::PermitExpired});
    last_diagnostic_ = out;
    return Result::PermitExpired;
  }
  const ActionMask mask = to_mask(action);
  if (!is_single_action(mask) || !is_defined_action(mask)) {
    out = Diagnostic::from_first({Result::UndefinedAction});
    last_diagnostic_ = out;
    return Result::UndefinedAction;
  }
  if (!permit.allows(mask)) {
    out = Diagnostic::from_first({Result::ActionNotAllowed});
    last_diagnostic_ = out;
    return Result::ActionNotAllowed;
  }
  const Result applied = entry.validation.apply(action, resolved);
  if (applied == Result::Ok) {
    // Test-only deterministic interleaving point: a production manager leaves the probe empty, so
    // no external code runs here.
    if (before_commit_probe_) {
      before_commit_probe_();
    }
    // A successful transition commits the authority observations it relied on, so a later
    // backward monotonic reading is rejected with ClockRegression. Each commit is bound to the
    // declaration generation that produced the observation: a domain re-declared after the peek
    // no longer matches and is left untouched. Every rejection returns before this point, so a
    // rejected transition leaves baselines unchanged.
    authority_.advance_baseline(now_domain, auth_now, now_declaration);
    if (mapped_domain != kInvalidClockDomain) {
      authority_.advance_baseline(mapped_domain, mapped_reading, mapped_declaration);
    }
    if (entry.validation.is_terminal()) {
      entry.terminal = true;
    }
  }
  out = Diagnostic::from_first({applied});
  last_diagnostic_ = out;
  return applied;
}

Result SessionManager::state(const SessionHandle &handle, LifecycleState &out) const {
  std::lock_guard<std::mutex> lock(mutex_);
  std::size_t index = kNoIndex;
  const Result located = locate_locked(handle, index);
  if (located != Result::Ok) {
    return located;
  }
  out = sessions_[index].validation.state();
  return Result::Ok;
}

Result SessionManager::session_snapshot(const SessionHandle &handle, SessionSnapshot &out) const {
  std::lock_guard<std::mutex> lock(mutex_);
  std::size_t index = kNoIndex;
  const Result located = locate_locked(handle, index);
  if (located != Result::Ok) {
    return located;
  }
  out = sessions_[index].validation.snapshot();
  return Result::Ok;
}

Diagnostic SessionManager::last_diagnostic() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return last_diagnostic_;
}

ManagerSnapshot SessionManager::manager_snapshot() const {
  std::lock_guard<std::mutex> lock(mutex_);
  ManagerSnapshot snapshot;
  snapshot.live_sessions = live_session_count_locked();
  snapshot.consumed_permits = registry_.size();
  snapshot.consumed_sessions = registry_.session_size();
  snapshot.registered_controllers = controllers_.size();
  snapshot.emission_count = 0;
  return snapshot;
}

std::size_t SessionManager::capacity() const noexcept { return config_.max_sessions; }

std::uint64_t SessionManager::emission_count() const noexcept { return 0; }

} // namespace xverse::xcom::validation
