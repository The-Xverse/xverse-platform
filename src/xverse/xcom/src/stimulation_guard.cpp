/**
 * \file stimulation_guard.cpp
 * \brief T027 fail-closed pre-emission guard implementation: bounded check order, commit on
 *        authorisation only, and non-mutating rejection.
 * \ingroup xcom_stim
 *
 * \details
 * This is the additive T027 production implementation. It consumes the accepted T025
 * `validation_session.hpp` contract and the accepted T-CORE interaction vocabulary read-only,
 * performs no I/O and no time-authority call, and exposes no emission path.
 */

#include "xverse/xcom/stimulation_guard.hpp"

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <utility>

namespace xverse::xcom::validation {
namespace {

/// \brief Bounded T025 diagnostic detail for one guard reason.
/// \param reason A guard reason.
/// \return A single-code bounded diagnostic; `None` yields the default `Ok` diagnostic.
[[nodiscard]] Diagnostic detail_for(GuardReason reason) noexcept {
  switch (reason) {
  case GuardReason::None:
    return Diagnostic{};
  case GuardReason::NotOpen:
    return Diagnostic::from_first({Result::InvalidHandle});
  case GuardReason::RejectedConfiguration:
    return Diagnostic::from_first({Result::InvalidPermit});
  case GuardReason::PermitMismatch:
    return Diagnostic::from_first({Result::PermitMismatch});
  case GuardReason::Revoked:
    return Diagnostic::from_first({Result::TerminalState});
  case GuardReason::Expired:
    return Diagnostic::from_first({Result::PermitExpired});
  case GuardReason::NotActive:
    return Diagnostic::from_first({Result::TerminalState});
  case GuardReason::SchemaMismatch:
    return Diagnostic::from_first({Result::PermitMismatch});
  case GuardReason::DirectionMismatch:
    return Diagnostic::from_first({Result::PermitMismatch});
  case GuardReason::InteractionMismatch:
    return Diagnostic::from_first({Result::PermitMismatch});
  case GuardReason::TargetMismatch:
    return Diagnostic::from_first({Result::PermitMismatch});
  case GuardReason::ActionMismatch:
    return Diagnostic::from_first({Result::ActionNotAllowed});
  case GuardReason::OwnershipConflict:
    return Diagnostic::from_first({Result::PermitMismatch});
  case GuardReason::QuotaExhausted:
    return Diagnostic::from_first({Result::QuotaExhausted});
  case GuardReason::LoopBound:
    return Diagnostic::from_first({Result::CapacityExhausted});
  case GuardReason::TimeOutOfWindow:
    return Diagnostic::from_first({Result::PermitExpired});
  case GuardReason::TimeUnmapped:
    return Diagnostic::from_first({Result::MissingMapping});
  default:
    return Diagnostic{};
  }
}

/// \brief Validates every declared policy bound and its consistency with the immutable permit.
/// \param permit The immutable permit the guard is opened from.
/// \param policy The declared stimulation policy.
/// \return `true` when every bound is legal and the policy is permit-consistent.
[[nodiscard]] bool guard_policy_is_valid(const Permit &permit,
                                         const StimulationPolicy &policy) noexcept {
  if (policy.plan_digest != permit.plan_digest()) {
    return false;
  }
  if (!Tag::is_valid(policy.interface_tag.value()) ||
      policy.interface_tag.value() != permit.interface_name()) {
    return false;
  }
  if (!Tag::is_valid(policy.target.value()) || policy.target.value() != permit.target()) {
    return false;
  }
  if (policy.validity_domain == kInvalidClockDomain ||
      policy.validity_domain != permit.validity_domain()) {
    return false;
  }
  if (!is_defined_stimulation_action(policy.allowed_actions)) {
    return false;
  }
  if (policy.allowed_interactions == 0U || (policy.allowed_interactions & 0xF0U) != 0U) {
    return false;
  }
  if (policy.allowed_directions == 0U || (policy.allowed_directions & 0xF0U) != 0U) {
    return false;
  }
  if (policy.allowed_schemas.empty() || policy.allowed_schemas.size() > kGuardMaxSchemas) {
    return false;
  }
  for (const SchemaKey &key : policy.allowed_schemas) {
    if (!Tag::is_valid(key.id.value()) || !Tag::is_valid(key.version.value())) {
      return false;
    }
  }
  if (policy.max_actions_per_session < 1U ||
      policy.max_actions_per_session > kGuardMaxActionsPerSession) {
    return false;
  }
  if (policy.max_actions_per_window < 1U ||
      policy.max_actions_per_window > policy.max_actions_per_session) {
    return false;
  }
  if (policy.action_window < 1U || policy.action_window > kGuardMaxActionsPerWindow) {
    return false;
  }
  if (policy.loop_window < 1U || policy.loop_window > kGuardMaxLoopWindow) {
    return false;
  }
  if (policy.allow_service_emulation &&
      (policy.allowed_actions & to_stimulation_mask(StimulationAction::EmulateService)) != 0U &&
      !policy.service_owner.declared) {
    return false;
  }
  if (policy.service_owner.declared &&
      !Tag::is_valid(policy.service_owner.endpoint.value())) {
    return false;
  }
  return true;
}

/// \brief Reports whether a schema key is a member of the declared allowed-schema table.
/// \param policy The declared policy.
/// \param key The candidate schema key.
/// \return `true` when `key` equals a declared entry.
[[nodiscard]] bool schema_is_allowed(const StimulationPolicy &policy,
                                     const SchemaKey &key) noexcept {
  for (const SchemaKey &allowed : policy.allowed_schemas) {
    if (allowed == key) {
      return true;
    }
  }
  return false;
}

/// \brief Reports whether a value is present in the bounded loop-detection window.
/// \param window The bounded loop window.
/// \param value The candidate lineage identity.
/// \return `true` when `value` is present.
[[nodiscard]] bool loop_contains(const std::vector<std::uint64_t> &window,
                                 std::uint64_t value) noexcept {
  for (const std::uint64_t entry : window) {
    if (entry == value) {
      return true;
    }
  }
  return false;
}

} // namespace

GuardStatus StimulationGuard::open(const Permit &permit, const StimulationPolicy &policy) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (!guard_policy_is_valid(permit, policy)) {
    // Fail closed: a rejected open leaves no authorizable configuration, so no request may pass.
    open_ = false;
    actions_authorized_ = 0U;
    window_actions_ = 0U;
    loop_window_.clear();
    evaluations_ = 0U;
    rejections_ = 0U;
    failures_ = 0U;
    return GuardStatus::RejectedConfiguration;
  }
  permit_ = permit;
  policy_ = policy;
  actions_authorized_ = 0U;
  window_actions_ = 0U;
  loop_window_.clear();
  loop_window_.reserve(policy.loop_window);
  evaluations_ = 0U;
  rejections_ = 0U;
  failures_ = 0U;
  open_ = true;
  return GuardStatus::Ok;
}

GuardOutcome StimulationGuard::authorize(const StimulationRequest &request,
                                         LifecycleState session_state,
                                         const ResolvedTime &resolved_time, GuardDiagnostic &out) {
  std::lock_guard<std::mutex> lock(mutex_);

  if (!open_) {
    out.reason = GuardReason::NotOpen;
    out.detail = detail_for(GuardReason::NotOpen);
    return GuardOutcome::Failed;
  }

  const auto reject = [this, &out](GuardReason reason) noexcept {
    ++evaluations_;
    ++rejections_;
    out.reason = reason;
    out.detail = detail_for(reason);
    return GuardOutcome::Rejected;
  };
  const auto fail = [this, &out](GuardReason reason) noexcept {
    ++evaluations_;
    ++failures_;
    out.reason = reason;
    out.detail = detail_for(reason);
    return GuardOutcome::Failed;
  };

  // Rank 1: a malformed request fails closed before any identity or state work.
  const StimulationActionMask action_mask = to_stimulation_mask(request.action);
  // The action must be a defined single bit: a zero, composite, or out-of-vocabulary action (for
  // example a single undefined bit such as `0x10`) is malformed and is `RejectedConfiguration`,
  // never a later direction/interaction/action-table mismatch.
  if (!is_defined_stimulation_action(action_mask) || !is_single_stimulation_action(action_mask)) {
    return reject(GuardReason::RejectedConfiguration);
  }
  if (request.request_id == 0U) {
    return reject(GuardReason::RejectedConfiguration);
  }
  if (request.immediate) {
    if (request.clock_domain != policy_.validity_domain) {
      return reject(GuardReason::RejectedConfiguration);
    }
  } else if (request.clock_domain == kInvalidClockDomain) {
    return reject(GuardReason::RejectedConfiguration);
  }

  // Rank 2: exact identity and plan-digest binding (`XCOM-INV-07`).
  if (request.session_id != permit_.session_id() || request.permit_id != permit_.permit_id() ||
      request.plan_digest != permit_.plan_digest() || policy_.plan_digest != request.plan_digest) {
    return reject(GuardReason::PermitMismatch);
  }

  // Ranks 3-5: only an `active` session authorizes.
  if (session_state == LifecycleState::revoked) {
    return reject(GuardReason::Revoked);
  }
  if (session_state == LifecycleState::expired) {
    return reject(GuardReason::Expired);
  }
  if (session_state != LifecycleState::active) {
    return reject(GuardReason::NotActive);
  }

  // Rank 6: schema identity/version must be valid and declared.
  if (!Tag::is_valid(request.schema.id.value()) ||
      !Tag::is_valid(request.schema.version.value()) ||
      !schema_is_allowed(policy_, request.schema)) {
    return reject(GuardReason::SchemaMismatch);
  }

  // Rank 7: the direction must match the closed action table and the policy mask.
  const std::uint8_t requested_direction = direction_bit(request.direction);
  if (requested_direction == 0U ||
      requested_direction != paired_direction_bit(request.action) ||
      (requested_direction & policy_.allowed_directions) == 0U) {
    return reject(GuardReason::DirectionMismatch);
  }

  // Rank 8: the interaction kind must match the closed action table and the policy mask.
  const std::uint8_t requested_interaction = interaction_bit(request.interaction);
  if (requested_interaction == 0U ||
      requested_interaction != paired_interaction_bit(request.action) ||
      (requested_interaction & policy_.allowed_interactions) == 0U) {
    return reject(GuardReason::InteractionMismatch);
  }

  // Rank 9: the target and interface tags must equal the bound permit.
  if (request.target.value() != permit_.target() ||
      request.interface_tag.value() != permit_.interface_name()) {
    return reject(GuardReason::TargetMismatch);
  }

  // Rank 10: the action must be declared allowed by the policy.
  if ((action_mask & policy_.allowed_actions) != action_mask) {
    return reject(GuardReason::ActionMismatch);
  }

  // Rank 11: declaration-level service ownership only; no lease is acquired (`XCOM-DU-018`).
  if (request.action == StimulationAction::InvokeService ||
      request.action == StimulationAction::EmulateService) {
    if (request.action == StimulationAction::EmulateService &&
        !policy_.allow_service_emulation) {
      return reject(GuardReason::OwnershipConflict);
    }
    if (!policy_.service_owner.declared || !request.service_owner.declared) {
      return reject(GuardReason::OwnershipConflict);
    }
    if (request.service_owner.endpoint.value() != policy_.service_owner.endpoint.value() ||
        request.service_owner.generation != policy_.service_owner.generation) {
      return reject(GuardReason::OwnershipConflict);
    }
  }

  // Rank 12: finite per-session and per-window budgets.
  if (actions_authorized_ + 1U > policy_.max_actions_per_session ||
      window_actions_ + 1U > policy_.max_actions_per_window) {
    return reject(GuardReason::QuotaExhausted);
  }

  // Rank 13: bounded declaration-level reinjection loop detection.
  if (request.causation_id != 0U && loop_contains(loop_window_, request.causation_id)) {
    return reject(GuardReason::LoopBound);
  }

  // Ranks 14-15: pre-emission time policy; no raw-clock comparison, no authority call.
  if (resolved_time.resolution != Result::Ok ||
      resolved_time.domain != policy_.validity_domain) {
    return fail(GuardReason::TimeUnmapped);
  }
  if (resolved_time.value < permit_.valid_from() ||
      resolved_time.value >= permit_.valid_until()) {
    return reject(GuardReason::TimeOutOfWindow);
  }

  // Authorize and commit once, atomically with the checks under the guard mutex.
  ++evaluations_;
  ++actions_authorized_;
  ++window_actions_;
  if (window_actions_ >= policy_.action_window) {
    window_actions_ = 0U;
  }
  if (loop_window_.size() >= policy_.loop_window) {
    loop_window_.erase(loop_window_.begin());
  }
  loop_window_.push_back(request.request_id);
  out.reason = GuardReason::None;
  out.detail = Diagnostic{};
  return GuardOutcome::Authorized;
}

GuardSnapshot StimulationGuard::snapshot() const {
  std::lock_guard<std::mutex> lock(mutex_);
  GuardSnapshot result{};
  if (!open_) {
    return result;
  }
  result.open = true;
  result.actions_authorized = actions_authorized_;
  result.actions_remaining = policy_.max_actions_per_session - actions_authorized_;
  result.window_actions = window_actions_;
  result.window_remaining = policy_.max_actions_per_window - window_actions_;
  result.loop_entries = loop_window_.size();
  result.evaluations = evaluations_;
  result.rejections = rejections_;
  result.failures = failures_;
  return result;
}

StimulationGuard::AuthorizationCheckpoint StimulationGuard::checkpoint() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return {actions_authorized_, window_actions_, evaluations_, loop_window_};
}

void StimulationGuard::restore_authorization(const AuthorizationCheckpoint &checkpoint) {
  std::lock_guard<std::mutex> lock(mutex_);
  actions_authorized_ = checkpoint.actions_authorized;
  window_actions_ = checkpoint.window_actions;
  evaluations_ = checkpoint.evaluations;
  // The checkpoint was copied before authorization, and the vector already has bounded capacity.
  loop_window_ = checkpoint.loop_window;
}

bool StimulationGuard::is_open() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return open_;
}

GuardStatus StimulationGuard::status() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return open_ ? GuardStatus::Ok : GuardStatus::NotOpen;
}

} // namespace xverse::xcom::validation
