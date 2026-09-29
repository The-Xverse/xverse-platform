/**
 * \file stimulation_actions.hpp
 * \brief T028 guarded stimulation action path: execute the four declared stimulation actions
 *        only on an authorized pre-emission decision, hold an exclusive generation-bound
 *        service-emulation lease, carry synthetic provenance, and complete the session
 *        lifecycle with zero mutation and zero emission on every decline.
 * \ingroup xcom_stim
 *
 * \details
 * This header is the additive T028 production surface of `xverse::xcom::validation`. It
 * consumes the accepted T025 `validation_session.hpp`, the accepted T026
 * `stimulation_journal.hpp`, the accepted T027 `stimulation_guard.hpp`, and the accepted
 * T-CORE `item.hpp` origin vocabulary read-only, and redefines no identity, digest,
 * diagnostic, interaction, origin, or action type.
 *
 * The action path owns a bounded pending queue, a bounded emission-time lineage window,
 * bounded counters, and a bounded set of held leases. It emits a payload-free synthetic
 * descriptor through a host-supplied `ActionEmitter` seam only after the accepted journal has
 * made the intent durable, and it never retains, journals, or logs a payload byte. Every
 * precondition, guard, lease, late-item, or completion decline emits nothing, journals
 * nothing, and mutates no accepted guard, lease, queue, lineage, or durable journal record in
 * the declined dimension.
 *
 * \note This is an internal prototype candidate. It is not a runtime, transport, gateway,
 *       provider, route, compatibility, live-readiness, or production interface, and it is
 *       not user-accepted or externally reviewed.
 */

#ifndef XVERSE_XCOM_STIMULATION_ACTIONS_HPP_
#define XVERSE_XCOM_STIMULATION_ACTIONS_HPP_

#include "xverse/xcom/item.hpp"
#include "xverse/xcom/stimulation_guard.hpp"
#include "xverse/xcom/stimulation_journal.hpp"
#include "xverse/xcom/validation_session.hpp"

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <span>
#include <string_view>
#include <type_traits>
#include <vector>

namespace xverse::xcom::validation {

/// \brief Maximum declared pending scheduled actions.
/// \ownership Static-lifetime constant.
/// \lifetime Program lifetime.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure A declared depth above this bound is rejected at open.
inline constexpr std::size_t kActionPathMaxPendingActions = 64U;
/// \brief Maximum declared emission-time lineage depth.
/// \ownership Static-lifetime constant.
/// \lifetime Program lifetime.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure A declared depth above this bound is rejected at open.
inline constexpr std::size_t kActionPathMaxLineage = 64U;
/// \brief Maximum pending actions completed by one drain or completion call.
/// \ownership Static-lifetime constant.
/// \lifetime Program lifetime.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure A declared budget above this bound is rejected at open.
inline constexpr std::size_t kActionPathMaxDrainSteps = 64U;
/// \brief Maximum call-scoped payload view forwarded to the emitter.
/// \ownership Static-lifetime constant.
/// \lifetime Program lifetime.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure A declared payload bound above this is rejected at open.
inline constexpr std::size_t kActionPathMaxPayloadBytes = 4096U;
/// \brief Maximum active service-emulation leases in one registry.
/// \ownership Static-lifetime constant.
/// \lifetime Program lifetime.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure A capacity above this bound is rejected at registry construction.
inline constexpr std::size_t kActionPathMaxActiveLeases = 64U;

/// \brief Closed action-path outcome vocabulary; declaration order is the stable reporting order.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure Every enumerator names one bounded outcome; only `Emitted` reports success.
enum class ActionStatus : std::uint8_t {
  /// \brief Authorized, intent durable, emitted exactly once, outcome durable.
  Emitted,
  /// \brief The guard declined with a definite declared mismatch; no emission, no journal.
  Rejected,
  /// \brief The guard could not complete deterministically; no emission, no journal.
  Failed,
  /// \brief Emulation requested but the exclusive lease could not be acquired or validated.
  LeaseConflict,
  /// \brief An authorized scheduled action entered the bounded pending queue.
  Queued,
  /// \brief A pending action was cancelled by completion; no emission.
  Cancelled,
  /// \brief A pending action lapsed under the declared late-item policy; no emission.
  Expired,
  /// \brief The intent is durable but no durable outcome exists; never success.
  EvidenceIncomplete,
  /// \brief The intent append or sync failed; no emission.
  JournalFailed,
  /// \brief A declared queue or lease bound would be exceeded; fail closed.
  CapacityExhausted,
  /// \brief The addressed session is not active for the requested operation.
  NotActive,
  /// \brief The action path is closed and evaluates nothing.
  NotOpen,
  /// \brief A malformed request or an invalid declared configuration.
  RejectedConfiguration,
  /// \brief The intent and host outcome are durable but the host rejected the descriptor; the
  ///        action is not delivered and is never reported as success.
  EmissionRejected,
  /// \brief The intent is durable but the host emission outcome is explicitly unknown; the action
  ///        is not delivered and is never reported as success.
  EmissionUnavailable,
};

/// \brief Returns the stable, non-empty name of an action status.
/// \param status An action status.
/// \return A stable, non-empty view; the same input always yields the same name.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view action_status_name(ActionStatus status) noexcept {
  switch (status) {
  case ActionStatus::Emitted:
    return "Emitted";
  case ActionStatus::Rejected:
    return "Rejected";
  case ActionStatus::Failed:
    return "Failed";
  case ActionStatus::LeaseConflict:
    return "LeaseConflict";
  case ActionStatus::Queued:
    return "Queued";
  case ActionStatus::Cancelled:
    return "Cancelled";
  case ActionStatus::Expired:
    return "Expired";
  case ActionStatus::EvidenceIncomplete:
    return "EvidenceIncomplete";
  case ActionStatus::JournalFailed:
    return "JournalFailed";
  case ActionStatus::CapacityExhausted:
    return "CapacityExhausted";
  case ActionStatus::NotActive:
    return "NotActive";
  case ActionStatus::NotOpen:
    return "NotOpen";
  case ActionStatus::RejectedConfiguration:
    return "RejectedConfiguration";
  case ActionStatus::EmissionRejected:
    return "EmissionRejected";
  case ActionStatus::EmissionUnavailable:
    return "EmissionUnavailable";
  default:
    return {};
  }
}

/// \brief Returns the zero-based precedence rank of an action status.
/// \param status An action status.
/// \return The zero-based rank; declaration order is the stable reporting order.
/// \ownership Pure function; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails.
[[nodiscard]] constexpr std::uint8_t precedence_rank(ActionStatus status) noexcept {
  return static_cast<std::uint8_t>(status);
}

/// \brief Closed lease-operation outcome vocabulary.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure Only `Ok` reports a successful lease operation.
enum class LeaseStatus : std::uint8_t {
  /// \brief The operation completed.
  Ok,
  /// \brief An active lease already owns the endpoint generation.
  Conflict,
  /// \brief No lease matches the supplied key.
  NotFound,
  /// \brief The lease exists but is not held by the caller.
  NotHeld,
  /// \brief The lease was already released.
  AlreadyReleased,
  /// \brief An active lease with the same endpoint belongs to another session.
  SessionMismatch,
  /// \brief An active lease with the same endpoint belongs to another generation.
  GenerationMismatch,
  /// \brief An active lease with the same endpoint generation carries another plan digest.
  PlanMismatch,
  /// \brief The lease validity elapsed.
  Expired,
  /// \brief The lease was quarantined.
  Quarantined,
  /// \brief The active-lease capacity was reached.
  CapacityExhausted,
  /// \brief A malformed key or inconsistent declared lease value.
  RejectedConfiguration,
};

/// \brief Returns the stable, non-empty name of a lease status.
/// \param status A lease status.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view lease_status_name(LeaseStatus status) noexcept {
  switch (status) {
  case LeaseStatus::Ok:
    return "Ok";
  case LeaseStatus::Conflict:
    return "Conflict";
  case LeaseStatus::NotFound:
    return "NotFound";
  case LeaseStatus::NotHeld:
    return "NotHeld";
  case LeaseStatus::AlreadyReleased:
    return "AlreadyReleased";
  case LeaseStatus::SessionMismatch:
    return "SessionMismatch";
  case LeaseStatus::GenerationMismatch:
    return "GenerationMismatch";
  case LeaseStatus::PlanMismatch:
    return "PlanMismatch";
  case LeaseStatus::Expired:
    return "Expired";
  case LeaseStatus::Quarantined:
    return "Quarantined";
  case LeaseStatus::CapacityExhausted:
    return "CapacityExhausted";
  case LeaseStatus::RejectedConfiguration:
    return "RejectedConfiguration";
  default:
    return {};
  }
}

/// \brief Returns the zero-based precedence rank of a lease status.
/// \param status A lease status.
/// \return The zero-based rank; declaration order is the stable reporting order.
/// \ownership Pure function; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails.
[[nodiscard]] constexpr std::uint8_t precedence_rank(LeaseStatus status) noexcept {
  return static_cast<std::uint8_t>(status);
}

/// \brief Closed lease-state vocabulary.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure Only `Active` conflict-blocks a later acquisition for one endpoint generation.
enum class LeaseState : std::uint8_t {
  /// \brief No lease exists for the key.
  None,
  /// \brief The lease is active and exclusively owned.
  Active,
  /// \brief The lease was released by its owner.
  Released,
  /// \brief The lease was quarantined.
  Quarantined,
  /// \brief The lease validity elapsed.
  Expired,
};

/// \brief Returns the stable, non-empty name of a lease state.
/// \param state A lease state.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view lease_state_name(LeaseState state) noexcept {
  switch (state) {
  case LeaseState::None:
    return "None";
  case LeaseState::Active:
    return "Active";
  case LeaseState::Released:
    return "Released";
  case LeaseState::Quarantined:
    return "Quarantined";
  case LeaseState::Expired:
    return "Expired";
  default:
    return {};
  }
}

/// \brief Closed scheduled-ordering vocabulary.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure The declared rule is the only ordering applied; no raw clock is compared.
enum class OrderingRule : std::uint8_t {
  /// \brief Order by `(scheduled_at, request_id)`.
  ScheduledThenArrival,
  /// \brief Order by `request_id` only.
  Arrival,
};

/// \brief Returns the stable, non-empty name of an ordering rule.
/// \param rule An ordering rule.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view ordering_rule_name(OrderingRule rule) noexcept {
  switch (rule) {
  case OrderingRule::ScheduledThenArrival:
    return "ScheduledThenArrival";
  case OrderingRule::Arrival:
    return "Arrival";
  default:
    return {};
  }
}

/// \brief Closed late-item policy vocabulary.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure Both policies cancel a late action with zero emission.
enum class LateItemPolicy : std::uint8_t {
  /// \brief A late action is cancelled and counted as late-rejected.
  RejectLate,
  /// \brief A late action is cancelled and counted as discarded.
  DiscardLate,
};

/// \brief Returns the stable, non-empty name of a late-item policy.
/// \param policy A late-item policy.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view late_item_policy_name(LateItemPolicy policy) noexcept {
  switch (policy) {
  case LateItemPolicy::RejectLate:
    return "RejectLate";
  case LateItemPolicy::DiscardLate:
    return "DiscardLate";
  default:
    return {};
  }
}

/// \brief Closed drain-state vocabulary.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure A terminal completion leaves `Cancelled`; a drained queue leaves `Drained`.
enum class DrainState : std::uint8_t {
  /// \brief Nothing is pending or due.
  Idle,
  /// \brief A drain is in progress with work remaining.
  Draining,
  /// \brief The pending queue is empty.
  Drained,
  /// \brief A terminal completion cancelled the bounded work.
  Cancelled,
};

/// \brief Returns the stable, non-empty name of a drain state.
/// \param state A drain state.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view drain_state_name(DrainState state) noexcept {
  switch (state) {
  case DrainState::Idle:
    return "Idle";
  case DrainState::Draining:
    return "Draining";
  case DrainState::Drained:
    return "Drained";
  case DrainState::Cancelled:
    return "Cancelled";
  default:
    return {};
  }
}

/// \brief Closed emitter-seam outcome vocabulary.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure Only `Delivered` maps to a delivered outcome; the others never report success.
enum class EmissionStatus : std::uint8_t {
  /// \brief The host seam delivered the descriptor.
  Delivered,
  /// \brief The host seam rejected the descriptor.
  Rejected,
  /// \brief The host seam is unavailable; the outcome is explicitly unknown.
  Unavailable,
};

/// \brief Returns the stable, non-empty name of an emission status.
/// \param status An emission status.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view emission_status_name(EmissionStatus status) noexcept {
  switch (status) {
  case EmissionStatus::Delivered:
    return "Delivered";
  case EmissionStatus::Rejected:
    return "Rejected";
  case EmissionStatus::Unavailable:
    return "Unavailable";
  default:
    return {};
  }
}

/// \brief Closed completion-outcome vocabulary.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure `EvidenceIncomplete` is never converted to `Closed`.
enum class CompletionOutcome : std::uint8_t {
  /// \brief No completion was applied.
  None,
  /// \brief The pending queue drained.
  Drained,
  /// \brief The session was closed after draining and releasing every lease.
  Closed,
  /// \brief The session was revoked; pending work cancelled and leases released.
  Revoked,
  /// \brief The session expired; pending work cancelled and leases expired.
  Expired,
  /// \brief A durable intent has no durable outcome; never success.
  EvidenceIncomplete,
};

/// \brief Returns the stable, non-empty name of a completion outcome.
/// \param outcome A completion outcome.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view completion_outcome_name(CompletionOutcome outcome) noexcept {
  switch (outcome) {
  case CompletionOutcome::None:
    return "None";
  case CompletionOutcome::Drained:
    return "Drained";
  case CompletionOutcome::Closed:
    return "Closed";
  case CompletionOutcome::Revoked:
    return "Revoked";
  case CompletionOutcome::Expired:
    return "Expired";
  case CompletionOutcome::EvidenceIncomplete:
    return "EvidenceIncomplete";
  default:
    return {};
  }
}

/// \brief Closed reason for quarantining an exclusive lease.
/// \ownership Value enumeration; owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable; safe to read concurrently.
/// \failure A quarantined lease is no longer active and no longer conflict-blocks.
enum class QuarantineReason : std::uint8_t {
  /// \brief A conflicting ownership.
  Conflict,
  /// \brief A session revocation.
  Revocation,
  /// \brief A session disconnect.
  Disconnect,
  /// \brief A lease validity expiry.
  Expiry,
};

/// \brief Returns the stable, non-empty name of a quarantine reason.
/// \param reason A quarantine reason.
/// \return A stable, non-empty view.
/// \ownership Returns a static-lifetime view; owns nothing.
/// \lifetime Static.
/// \thread_safety Safe to call concurrently.
/// \failure Never fails; an out-of-vocabulary value yields an empty view.
[[nodiscard]] constexpr std::string_view quarantine_reason_name(QuarantineReason reason) noexcept {
  switch (reason) {
  case QuarantineReason::Conflict:
    return "Conflict";
  case QuarantineReason::Revocation:
    return "Revocation";
  case QuarantineReason::Disconnect:
    return "Disconnect";
  case QuarantineReason::Expiry:
    return "Expiry";
  default:
    return {};
  }
}

/// \brief Bounded, payload-free declared action-path configuration.
/// \ownership Copyable caller-owned value; copied into the action path at construction.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure A zero, over-maximum, or inconsistent bound is `RejectedConfiguration` at open.
struct ActionPathConfig {
  /// \brief Maximum pending scheduled actions; `1 … kActionPathMaxPendingActions`.
  std::size_t max_pending_actions{kActionPathMaxPendingActions};
  /// \brief Maximum emission-time lineage entries; `1 … kActionPathMaxLineage`.
  std::size_t max_lineage_entries{kActionPathMaxLineage};
  /// \brief Maximum pending actions completed by one call; `1 … kActionPathMaxDrainSteps`.
  std::size_t max_drain_steps{kActionPathMaxDrainSteps};
  /// \brief Maximum call-scoped payload view; `1 … kActionPathMaxPayloadBytes`.
  std::size_t max_payload_bytes{kActionPathMaxPayloadBytes};
  /// \brief Declared scheduled ordering rule.
  OrderingRule ordering{OrderingRule::ScheduledThenArrival};
  /// \brief Declared late-item policy.
  LateItemPolicy late_policy{LateItemPolicy::RejectLate};
  /// \brief Non-negative bounded late tolerance in the validity domain.
  Timestamp late_tolerance{0};
  /// \brief Valid tool tag bound into every intent.
  Tag tool{};

  /// \brief Value equality over every field.
  friend bool operator==(const ActionPathConfig &, const ActionPathConfig &) noexcept = default;
};

/// \brief Bounded, payload-free exclusive lease key.
/// \ownership Copyable value; owns no resource.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure A different session, endpoint, generation, or plan digest never matches the key.
struct EndpointGeneration {
  /// \brief Bound session identity.
  SessionId session{};
  /// \brief Declared service endpoint tag.
  Tag endpoint{};
  /// \brief Declared endpoint generation.
  Generation generation{0};
  /// \brief Bound plan digest.
  PlanDigest plan_digest{};

  /// \brief Value equality over every field.
  friend bool operator==(const EndpointGeneration &, const EndpointGeneration &) noexcept = default;
};

/// \brief Bounded, payload-free exclusive lease value.
/// \ownership Copyable value; owns no resource.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure `expires_at >= acquired_at` always holds; a released/quarantined lease is inactive.
struct EmulationLease {
  /// \brief Exclusive lease key.
  EndpointGeneration key{};
  /// \brief Request identity of the owning action.
  std::uint64_t request_id{0};
  /// \brief Declared clock domain of the acquisition and expiry values.
  ClockDomainId domain{kInvalidClockDomain};
  /// \brief Acquisition time in `domain`.
  Timestamp acquired_at{0};
  /// \brief Expiry time in `domain`.
  Timestamp expires_at{0};
  /// \brief Current lease state.
  LeaseState state{LeaseState::None};

  /// \brief Value equality over every field.
  friend bool operator==(const EmulationLease &, const EmulationLease &) noexcept = default;
};

/// \brief Bounded, payload-free pending scheduled action.
/// \ownership Copyable value retained by the action path.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure A non-due pending action stays queued; a cancelled action emits nothing.
struct PendingAction {
  /// \brief Request identity.
  std::uint64_t request_id{0};
  /// \brief Exact guard authorization to release if journal admission later fails.
  std::uint64_t authorization_token{0};
  /// \brief Declared stimulation action.
  StimulationAction action{StimulationAction::InjectSignal};
  /// \brief Declared clock domain of `scheduled_at`.
  ClockDomainId domain{kInvalidClockDomain};
  /// \brief Declared schedule in `domain`.
  Timestamp scheduled_at{0};
  /// \brief Explicit immediate/scheduled label; always `false` for a queued action.
  bool immediate{false};
  /// \brief Retained bounded payload-free declaration, for exact intent and lease reconstruction.
  StimulationRequest request{};

  /// \brief Value equality over every field.
  friend bool operator==(const PendingAction &, const PendingAction &) noexcept = default;
};

/// \brief Bounded, payload-free synthetic descriptor forwarded to the host emitter.
/// \ownership Copyable value; owns no payload.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure `origin` is always `OriginKind::validation_tool`; no path emits another origin.
struct SyntheticStimulationItem {
  /// \brief Synthetic origin classification; always `OriginKind::validation_tool`.
  OriginKind origin{OriginKind::validation_tool};
  /// \brief Exact bounded intent identity and metadata.
  StimulationIntent intent{};

  /// \brief Value equality over every field.
  friend bool operator==(const SyntheticStimulationItem &,
                         const SyntheticStimulationItem &) noexcept = default;
};

/// \brief Bounded, payload-free action diagnostic.
/// \ownership Copyable value; owns no resource.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure Names the explicit bounded status and reason of one action evaluation.
struct ActionDiagnostic {
  /// \brief Closed action-path status.
  ActionStatus status{ActionStatus::NotOpen};
  /// \brief Guard reason for a guard decision.
  GuardReason guard_reason{GuardReason::None};
  /// \brief Lease status for a lease decline.
  LeaseStatus lease_status{LeaseStatus::Ok};
  /// \brief Journal status for an emission attempt.
  JournalStatus journal_status{JournalStatus::Ok};
  /// \brief Host emission status of an attempt; meaningful only when a callback ran.
  EmissionStatus emission_status{EmissionStatus::Delivered};
  /// \brief Request identity.
  std::uint64_t request_id{0};
  /// \brief Bounded accepted T025 diagnostic detail.
  Diagnostic detail{};

  /// \brief Value equality over every field.
  friend bool operator==(const ActionDiagnostic &, const ActionDiagnostic &) noexcept = default;
};

/// \brief Bounded, payload-free observable action-path snapshot.
/// \ownership Copyable value produced by `StimulationActionPath::snapshot()`.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure A snapshot taken after a decline equals the pre-decline snapshot apart from the
///          declared counters.
struct ActionPathSnapshot {
  /// \brief Whether the action path is open.
  bool open{false};
  /// \brief Pending scheduled actions.
  std::size_t pending{0};
  /// \brief Retained lineage entries.
  std::size_t lineage_entries{0};
  /// \brief Actions emitted.
  std::uint64_t emitted{0};
  /// \brief Authorized actions whose durable host outcome was a rejection.
  std::uint64_t emission_rejected{0};
  /// \brief Authorized actions whose durable host outcome is explicitly unknown.
  std::uint64_t emission_unavailable{0};
  /// \brief Actions rejected.
  std::uint64_t rejected{0};
  /// \brief Actions that failed.
  std::uint64_t failed{0};
  /// \brief Pending actions cancelled.
  std::uint64_t cancelled{0};
  /// \brief Pending actions expired as late-rejected.
  std::uint64_t expired{0};
  /// \brief Pending actions discarded as late.
  std::uint64_t discarded{0};
  /// \brief Intents without a durable outcome.
  std::uint64_t evidence_incomplete{0};
  /// \brief Lease conflicts observed.
  std::uint64_t lease_conflicts{0};
  /// \brief Current drain state.
  DrainState drain_state{DrainState::Idle};

  /// \brief Value equality over every field.
  friend bool operator==(const ActionPathSnapshot &, const ActionPathSnapshot &) noexcept = default;
};

/// \brief Bounded, payload-free observable lease-registry snapshot.
/// \ownership Copyable value produced by `ServiceEmulationRegistry::snapshot()`.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure Reflects the bounded lease table; never mutates it.
struct LeaseSnapshot {
  /// \brief Active leases.
  std::size_t active{0};
  /// \brief Released tombstones.
  std::size_t released{0};
  /// \brief Quarantined tombstones.
  std::size_t quarantined{0};
  /// \brief Expired tombstones.
  std::size_t expired{0};
  /// \brief Successful acquisitions.
  std::uint64_t acquisitions{0};
  /// \brief Conflicting acquisitions.
  std::uint64_t conflicts{0};

  /// \brief Value equality over every field.
  friend bool operator==(const LeaseSnapshot &, const LeaseSnapshot &) noexcept = default;
};

/// \brief Bounded, payload-free completion input.
/// \ownership Copyable value; owns no resource.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure A domain differing from the permit validity domain yields `CompletionOutcome::None`.
struct CompletionRequest {
  /// \brief Caller-supplied current time in `domain`.
  Timestamp now{0};
  /// \brief Declared clock domain of `now`.
  ClockDomainId domain{kInvalidClockDomain};
  /// \brief Caller-supplied lifecycle state of the session.
  LifecycleState session_state{LifecycleState::active};

  /// \brief Value equality over every field.
  friend bool operator==(const CompletionRequest &, const CompletionRequest &) noexcept = default;
};

/// \brief Bounded, payload-free completion report.
/// \ownership Copyable value; owns no resource.
/// \lifetime Value lifetime.
/// \thread_safety Immutable; safe to copy and read concurrently.
/// \failure Reports the exact bounded outcome and per-action counts of one completion.
struct CompletionReport {
  /// \brief Closed completion outcome.
  CompletionOutcome outcome{CompletionOutcome::None};
  /// \brief Pending actions emitted or completed.
  std::size_t drained{0};
  /// \brief Pending actions cancelled.
  std::size_t cancelled{0};
  /// \brief Held leases released.
  std::size_t released_leases{0};
  /// \brief Held leases quarantined.
  std::size_t quarantined_leases{0};
  /// \brief Held leases expired.
  std::size_t expired_leases{0};
  /// \brief Durable intents without a durable outcome surfaced by this completion.
  std::size_t evidence_incomplete{0};
  /// \brief Due pending actions this completion could not complete; a non-zero value is never
  ///        reported as `Drained` or `Closed`.
  std::size_t failed{0};

  /// \brief Value equality over every field.
  friend bool operator==(const CompletionReport &, const CompletionReport &) noexcept = default;
};

/**
 * \brief Host emission seam: the only realization boundary of the action path.
 *
 * The action path invokes `emit` exactly once per authorized emission, outside every lock,
 * with the bounded synthetic descriptor and the call-scoped payload view. The seam owns
 * realization; the accepted T-CORE provider boundary owns transport and T030–T034 owns the
 * gateway. T028 retains, journals, and logs no payload byte.
 *
 * \ownership Host-owned; the action path holds a non-owning reference that must outlive it.
 * \lifetime Must outlive every action path that references it.
 * \thread_safety A seam may be invoked concurrently; an implementation that shares mutable
 *                state must synchronize it.
 * \failure `Rejected` and `Unavailable` never map to a delivered outcome.
 */
class ActionEmitter {
public:
  /// \brief Destructor.
  virtual ~ActionEmitter() = default;

  /// \brief Delivers one bounded synthetic descriptor exactly once.
  /// \param item Bounded payload-free synthetic descriptor.
  /// \param payload Call-scoped payload view; never retained or logged.
  /// \return The closed bounded emission status.
  [[nodiscard]] virtual EmissionStatus emit(const SyntheticStimulationItem &item,
                                            std::span<const std::byte> payload) = 0;
};

/**
 * \brief Bounded exclusive service-emulation lease registry.
 *
 * The registry owns a bounded table of `(session, endpoint, generation, plan)` leases and
 * atomically checks and inserts under one mutex, so a concurrently racing second owner
 * observes exactly one winner and one conflicted loser for one endpoint generation. An active
 * lease is valid only for the endpoint generation under which it was acquired; a released,
 * quarantined, or expired lease is retained as a bounded tombstone for accounting and no
 * longer conflict-blocks. A comparison is performed only between values in one declared clock
 * domain; two raw mismatched domains are never compared or ordered.
 *
 * \ownership Shared, caller-owned; a lease is valid only for its endpoint generation.
 * \lifetime `endpoint-generation`: active from acquisition to release, quarantine, or expiry.
 * \thread_safety `internally-synchronized`; one mutex serializes every operation; no callback.
 * \failure Every operation returns an explicit `LeaseStatus`; a conflict, identity mismatch,
 *          unknown key, capacity exhaustion, or expiry comparison mutates no entry.
 */
class ServiceEmulationRegistry {
public:
  /// \brief Constructs a registry with a bounded active-lease capacity.
  /// \param max_active_leases Active-lease capacity; `1 … kActionPathMaxActiveLeases`.
  /// \throws std::invalid_argument when the capacity is zero or above the declared maximum.
  explicit ServiceEmulationRegistry(
      std::size_t max_active_leases = kActionPathMaxActiveLeases);

  /// \brief Destructor.
  ~ServiceEmulationRegistry() = default;

  /// \brief Copy construction is deleted; the registry is non-copyable.
  ServiceEmulationRegistry(const ServiceEmulationRegistry &) = delete;
  /// \brief Copy assignment is deleted; the registry is non-copyable.
  ServiceEmulationRegistry &operator=(const ServiceEmulationRegistry &) = delete;
  /// \brief Move construction is deleted; the registry is non-movable.
  ServiceEmulationRegistry(ServiceEmulationRegistry &&) = delete;
  /// \brief Move assignment is deleted; the registry is non-movable.
  ServiceEmulationRegistry &operator=(ServiceEmulationRegistry &&) = delete;

  /// \brief Atomically acquires an exclusive lease for one endpoint generation.
  /// \param key Exact lease key.
  /// \param request_id Owning request identity.
  /// \param domain Clock domain of the times.
  /// \param acquired_at Acquisition time.
  /// \param expires_at Expiry time; must be at least `acquired_at`.
  /// \return `LeaseStatus::Ok` on success; `Conflict` when an active lease already owns the
  ///         endpoint generation; `SessionMismatch`, `GenerationMismatch`, or `PlanMismatch`
  ///         when an active lease with the same endpoint differs in that identity field;
  ///         `CapacityExhausted` at capacity; `RejectedConfiguration` for a malformed key.
  ///         No entry is mutated on a decline.
  [[nodiscard]] LeaseStatus acquire(const EndpointGeneration &key, std::uint64_t request_id,
                                    ClockDomainId domain, Timestamp acquired_at,
                                    Timestamp expires_at);

  /// \brief Classifies a would-be acquisition without mutating any entry.
  /// \param key Exact lease key.
  /// \param domain Clock domain of the times.
  /// \param acquired_at Acquisition time.
  /// \param expires_at Expiry time; must be at least `acquired_at`.
  /// \return The exact `LeaseStatus` that `acquire` would return for the same arguments at the
  ///         observed table state; `Ok` when an acquisition would succeed. It mutates no entry,
  ///         increments no counter, and invokes no callback, so a caller can classify a
  ///         precondition before a guard evaluation and still acquire atomically afterwards.
  [[nodiscard]] LeaseStatus precheck(const EndpointGeneration &key, ClockDomainId domain,
                                     Timestamp acquired_at, Timestamp expires_at) const;

  /// \brief Releases a held lease for its exact owner.
  /// \param key Exact lease key.
  /// \param request_id Owning request identity.
  /// \return `LeaseStatus::Ok` on success; `NotFound` when no lease matches the key;
  ///         `AlreadyReleased` when the lease was already released; `NotHeld` when the lease
  ///         is quarantined, expired, or owned by another request. No mutation on failure.
  [[nodiscard]] LeaseStatus release(const EndpointGeneration &key, std::uint64_t request_id);

  /// \brief Quarantines a held lease.
  /// \param key Exact lease key.
  /// \param reason Bounded quarantine reason.
  /// \return `LeaseStatus::Ok` on success; `NotFound` when no lease matches; `NotHeld` when the
  ///         lease is not active. No mutation on failure.
  [[nodiscard]] LeaseStatus quarantine(const EndpointGeneration &key, QuarantineReason reason);

  /// \brief Expires every active lease in a domain whose validity elapsed.
  /// \param domain Declared clock domain to compare in.
  /// \param now Caller-supplied time in `domain`.
  /// \return The number of leases transitioned to `Expired`. A lease in another domain is
  ///         never compared or ordered.
  [[nodiscard]] std::size_t expire_elapsed(ClockDomainId domain, Timestamp now);

  /// \brief Expires one active lease regardless of time.
  /// \param key Exact lease key.
  /// \return `LeaseStatus::Ok` on success; `NotFound` when no lease matches; `NotHeld` when the
  ///         lease is not active. No mutation on failure.
  [[nodiscard]] LeaseStatus expire_key(const EndpointGeneration &key);

  /// \brief Reports whether an exact active lease is held.
  /// \param key Exact lease key.
  /// \return `true` when an active entry with the exact key exists.
  [[nodiscard]] bool holds(const EndpointGeneration &key) const;

  /// \brief Atomically reserves emission for the exact owning request.
  /// A reserved slot cannot be reused until finish_emission, even if released meanwhile.
  /// \param key Session, endpoint generation, and plan bound to the lease.
  /// \param request_id Owning request identity.
  /// \return `true` when the reservation was created; `false` when no matching lease/owner exists.
  [[nodiscard]] bool reserve_emission(const EndpointGeneration &key, std::uint64_t request_id);
  /// \brief Ends the exact request's emission reservation under the lease mutex.
  /// \param key Session, endpoint generation, and plan bound to the lease.
  /// \param request_id Owning request; another owner's reservation is unchanged.
  void finish_emission(const EndpointGeneration &key, std::uint64_t request_id) noexcept;

  /// \brief Returns the state of the lease with the exact key.
  /// \param key Exact lease key.
  /// \return The lease state, or `LeaseState::None` when no entry matches.
  [[nodiscard]] LeaseState state_of(const EndpointGeneration &key) const;

  /// \brief Returns an immutable snapshot without mutating state.
  /// \return The bounded lease-registry snapshot.
  [[nodiscard]] LeaseSnapshot snapshot() const;

  /// \brief Returns the configured active-lease capacity.
  /// \return The configured active-lease capacity.
  [[nodiscard]] std::size_t capacity() const noexcept;

private:
  /// \brief One bounded lease-table entry; released/quarantined entries are tombstones.
  struct LeaseEntry {
    /// \brief Exact lease key.
    EndpointGeneration key{};
    /// \brief Owning request identity.
    std::uint64_t request_id{0};
    /// \brief Clock domain of the times.
    ClockDomainId domain{kInvalidClockDomain};
    /// \brief Acquisition time.
    Timestamp acquired_at{0};
    /// \brief Expiry time.
    Timestamp expires_at{0};
    /// \brief Current lease state.
    LeaseState state{LeaseState::None};
    bool emission_reserved{false};
    /// \brief Recorded quarantine reason; meaningful only for a quarantined entry.
    QuarantineReason quarantine_reason{QuarantineReason::Conflict};
  };

  /// \brief Finds an entry with the exact key; call only while holding the mutex.
  /// \param key Exact lease key.
  /// \return Pointer to the entry, or `nullptr` when absent.
  [[nodiscard]] LeaseEntry *find_locked(const EndpointGeneration &key) noexcept;
  /// \brief Finds an entry with the exact key; call only while holding the mutex.
  /// \param key Exact lease key.
  /// \return Pointer to the entry, or `nullptr` when absent.
  [[nodiscard]] const LeaseEntry *find_locked(const EndpointGeneration &key) const noexcept;
  /// \brief Counts active entries; call only while holding the mutex.
  /// \return The number of active leases.
  [[nodiscard]] std::size_t active_count_locked() const noexcept;
  /// \brief Finds a reusable table slot; call only while holding the mutex.
  /// \return Pointer to a reusable slot, or `nullptr` when none is available.
  [[nodiscard]] LeaseEntry *reusable_slot_locked() noexcept;
  /// \brief Reports whether a lease key is well formed.
  /// \param key Candidate lease key.
  /// \return `true` when the session is non-zero and the endpoint tag is valid.
  [[nodiscard]] static bool key_is_valid(const EndpointGeneration &key) noexcept;

  /// \brief Serializes every registry operation.
  mutable std::mutex mutex_;
  /// \brief Configured active-lease capacity.
  std::size_t capacity_{kActionPathMaxActiveLeases};
  /// \brief Bounded lease table.
  std::vector<LeaseEntry> entries_{};
  /// \brief Successful acquisitions.
  std::uint64_t acquisitions_{0};
  /// \brief Conflicting or mismatched acquisitions.
  std::uint64_t conflicts_{0};
};

/**
 * \brief Bounded guarded action path for one validation-session scope.
 *
 * The action path evaluates one declared `StimulationRequest` against the accepted T027 guard,
 * acquires the exclusive service-emulation lease for an emulation action, journals the
 * payload-free intent durably through the accepted T026 journal before invoking the host
 * emitter exactly once, and records an explicit bounded outcome. It bounds its own
 * emission-time reinjection lineage, schedules authorized work in a bounded ordered pending
 * queue, and completes the session lifecycle with `drain`, `close`, `revoke`, `expire`, and
 * `mark_evidence_incomplete`. Every decline emits nothing, journals nothing, and mutates no
 * accepted guard, lease, queue, lineage, or journal record in the declined dimension.
 *
 * \ownership `session-issued-handle`; only a path opened from the session's immutable permit
 *            may execute. The journal, registry, and emitter references are non-owning and
 *            must outlive the action path.
 * \lifetime `session-scoped`; the path retains at most `config.max_pending_actions` pending
 *           descriptors and `config.max_lineage_entries` lineage entries.
 * \thread_safety `internally-synchronized`; one mutex serializes state; the host emitter is
 *                invoked outside the lock, so no callback runs under a lock.
 * \failure Every decline returns the closed `ActionStatus`; only a durable intent, a single
 *          successful emission, and a durable outcome report `Emitted`.
 */
class StimulationActionPath {
public:
  /// \brief Constructs a closed action path over non-owning references.
  /// \param config Bounded declared configuration; copied.
  /// \param journal Accepted T026 journal; must outlive the path.
  /// \param registry Exclusive lease registry; must outlive the path.
  /// \param emitter Host emission seam; must outlive the path.
  /// \pre `journal`, `registry`, and `emitter` outlive the action path.
  /// \post The path is closed and evaluates nothing.
  StimulationActionPath(const ActionPathConfig &config, StimulationJournal &journal,
                        ServiceEmulationRegistry &registry, ActionEmitter &emitter) noexcept;

  /// \brief Destructor.
  ~StimulationActionPath() = default;

  /// \brief Copy construction is deleted; the path is non-copyable.
  StimulationActionPath(const StimulationActionPath &) = delete;
  /// \brief Copy assignment is deleted; the path is non-copyable.
  StimulationActionPath &operator=(const StimulationActionPath &) = delete;
  /// \brief Move construction is deleted; the path is non-movable.
  StimulationActionPath(StimulationActionPath &&) = delete;
  /// \brief Move assignment is deleted; the path is non-movable.
  StimulationActionPath &operator=(StimulationActionPath &&) = delete;

  /// \brief Validates a declared configuration and permit/policy pair and binds the guard.
  /// \param permit Immutable session permit the path is opened from; copied.
  /// \param policy Bounded declared stimulation policy for this session.
  /// \return `GuardStatus::Ok` when the configuration and permit/policy pair are valid;
  ///         otherwise `GuardStatus::RejectedConfiguration`, leaving the path closed with zero
  ///         counters and authorizing nothing.
  [[nodiscard]] GuardStatus open(const Permit &permit, const StimulationPolicy &policy);

  /// \brief Evaluates and, when authorized, performs one declared action.
  /// \param request Declared stimulation request.
  /// \param session_state Current session lifecycle state read from the accepted T025 session.
  /// \param resolved_time Caller-resolved time in the permit validity domain.
  /// \param payload Call-scoped payload view; forwarded to the emitter only and retained by
  ///                nothing.
  /// \param out Receives the bounded action diagnostic.
  /// \return `Emitted`, `Queued`, or an explicit bounded non-emitting status. No decline
  ///         mutates accepted guard state, a lease, a queue entry, a lineage entry, or a
  ///         durable journal record, and no decline emits.
  [[nodiscard]] ActionStatus execute(const StimulationRequest &request, LifecycleState session_state,
                                     const ResolvedTime &resolved_time,
                                     std::span<const std::byte> payload, ActionDiagnostic &out);

  /// \brief Completes every due pending action within the bounded step budget.
  /// \param request Caller-supplied completion input.
  /// \return A bounded deterministic completion report.
  [[nodiscard]] CompletionReport drain(const CompletionRequest &request);

  /// \brief Drains every due pending action, cancels the rest, and releases every held lease.
  /// \param request Caller-supplied completion input.
  /// \return A bounded deterministic completion report; `EvidenceIncomplete` when a durable
  ///         intent has no durable outcome, never `Closed`.
  [[nodiscard]] CompletionReport close(const CompletionRequest &request);

  /// \brief Cancels every pending action and releases every held lease.
  /// \param request Caller-supplied completion input.
  /// \return A bounded deterministic completion report with outcome `Revoked`.
  [[nodiscard]] CompletionReport revoke(const CompletionRequest &request);

  /// \brief Cancels every pending action and expires every held lease.
  /// \param request Caller-supplied completion input.
  /// \return A bounded deterministic completion report with outcome `Expired`.
  [[nodiscard]] CompletionReport expire(const CompletionRequest &request);

  /// \brief Cancels every pending action, releases every held lease, and counts incomplete intents.
  /// \param request Caller-supplied completion input.
  /// \return A bounded deterministic completion report with outcome `EvidenceIncomplete`.
  [[nodiscard]] CompletionReport mark_evidence_incomplete(const CompletionRequest &request);

  /// \brief Returns an immutable snapshot without mutating state.
  /// \return The bounded action-path snapshot.
  [[nodiscard]] ActionPathSnapshot snapshot() const;

  /// \brief Reports whether the action path is open.
  /// \return `true` when the path was successfully opened.
  [[nodiscard]] bool is_open() const;

private:
  /// \brief One held lease advanced for completion by the owning request identity.
  struct HeldLease {
    /// \brief Exact lease key.
    EndpointGeneration key{};
    /// \brief Owning request identity.
    std::uint64_t request_id{0};
  };

  /// \brief Result of one journal-then-emit attempt.
  struct EmissionAttempt {
    /// \brief Journal status of the durable intent/outcome pair.
    JournalStatus journal{JournalStatus::Ok};
    /// \brief Host emission status observed exactly once; only set when the callback ran.
    EmissionStatus emission{EmissionStatus::Delivered};
    bool emission_started{false};
  };

  /// \brief Reports whether a declared configuration is legal.
  /// \param config Candidate configuration.
  /// \return `true` when every declared bound is legal and the tool tag is valid.
  [[nodiscard]] static bool config_is_legal(const ActionPathConfig &config) noexcept;

  /// \brief Builds the exact lease key from a request and the bound permit.
  /// \param request Declared stimulation request.
  /// \return The exact lease key.
  [[nodiscard]] EndpointGeneration lease_key_for(const StimulationRequest &request) const;

  /// \brief Builds the payload-free intent from a request and the bound permit.
  /// \param request Declared stimulation request.
  /// \return The bounded intent.
  [[nodiscard]] StimulationIntent intent_for(const StimulationRequest &request) const;

  /// \brief Reports whether a lineage identity is already retained.
  /// \param identity Candidate causal identity.
  /// \return `true` when the identity is present in the bounded lineage window.
  [[nodiscard]] bool lineage_contains(std::uint64_t identity) const noexcept;

  /// \brief Advances the bounded lineage window with an emitted request identity.
  /// \param request_id Emitted request identity.
  void advance_lineage_locked(std::uint64_t request_id);

  /// \brief Inserts a pending action in the declared order; call only while holding the mutex.
  /// \param pending Pending action to insert.
  void queue_locked(const PendingAction &pending);

  /// \brief Finds the first due pending action in declared order; call only holding the mutex.
  /// \param domain Declared completion clock domain to compare in.
  /// \param now Caller-supplied time.
  /// \param index Receives the index only when a due action exists.
  /// \return `true` when a due action exists.
  [[nodiscard]] bool first_due_locked(ClockDomainId domain, Timestamp now,
                                      std::size_t &index) const;

  /// \brief Journals the intent durably and emits once; called with the mutex released.
  /// \param lock Held action-path lock, released around the host emission.
  /// \param intent Bounded intent.
  /// \param payload Call-scoped payload view.
  /// \param observed_domain Domain containing the observed completion timestamp.
  /// \param observed_at Observed time recorded with the outcome.
  /// \return The journal status of the durable intent/outcome pair and the host emission status.
  [[nodiscard]] EmissionAttempt journal_and_emit(std::unique_lock<std::mutex> &lock,
                                                 const StimulationIntent &intent,
                                                 std::span<const std::byte> payload,
                                                 ClockDomainId observed_domain,
                                                 Timestamp observed_at);

  /// \brief Classifies a journal/emission result into a bounded status and updates the counters.
  /// \param attempt Journal and host emission result of one attempt.
  /// \param request_id Request identity.
  /// \return The bounded action status; `Emitted` only for a durable `Delivered` outcome.
  ActionStatus classify_locked(const EmissionAttempt &attempt, std::uint64_t request_id);

  /// \brief Emits one due pending action; call only while holding the mutex.
  /// \param lock Held action-path lock, released around the host emission.
  /// \param index Index of the pending action in the bounded queue.
  /// \param now Caller-supplied completion time.
  /// \return The bounded status of the emission or cancellation.
  ActionStatus emit_pending_locked(std::unique_lock<std::mutex> &lock, std::size_t index,
                                   Timestamp now);

  /// \brief Cancels every pending action; call only while holding the mutex.
  /// \return The number of cancelled actions.
  std::size_t cancel_all_locked();

  /// \brief Releases every held lease; call only while holding the mutex.
  /// \return The number of released leases.
  std::size_t release_all_locked();

  /// \brief Releases this request's held lease without touching another owner's lease.
  void release_held_lease_locked(const EndpointGeneration &key, std::uint64_t request_id);

  /// \brief Expires every held lease; call only while holding the mutex.
  /// \return The number of expired leases.
  std::size_t expire_all_locked();

  /// \brief Counts durable intents without a durable outcome.
  /// \return The number of orphan intents reported by the accepted journal.
  [[nodiscard]] std::size_t incomplete_count() const;

  /// \brief Reports whether a completion request's domain matches the permit validity domain.
  /// \param request Candidate completion request.
  /// \return `true` when the domains match and the path is open.
  [[nodiscard]] bool completion_domain_ok(const CompletionRequest &request) const noexcept;

  /// \brief Serializes every action-path operation.
  mutable std::mutex mutex_;
  /// \brief Bound configuration.
  ActionPathConfig config_{};
  /// \brief Non-owning accepted journal reference.
  StimulationJournal &journal_;
  /// \brief Non-owning exclusive lease registry reference.
  ServiceEmulationRegistry &registry_;
  /// \brief Non-owning host emission seam reference.
  ActionEmitter &emitter_;
  /// \brief Bound accepted guard.
  StimulationGuard guard_{};
  /// \brief Bound immutable permit copy.
  Permit permit_{};
  /// \brief Whether the path is open.
  bool open_{false};
  /// \brief Bounded pending queue in declared order.
  std::vector<PendingAction> pending_{};
  /// \brief Bounded emission-time lineage window.
  std::vector<std::uint64_t> lineage_{};
  /// \brief Bounded set of leases held by this path.
  std::vector<HeldLease> held_leases_{};
  /// \brief Emitted actions.
  std::uint64_t emitted_{0};
  /// \brief Authorized actions whose durable host outcome was a rejection.
  std::uint64_t emission_rejected_{0};
  /// \brief Authorized actions whose durable host outcome is explicitly unknown.
  std::uint64_t emission_unavailable_{0};
  /// \brief Rejected actions.
  std::uint64_t rejected_{0};
  /// \brief Failed actions.
  std::uint64_t failed_{0};
  /// \brief Cancelled pending actions.
  std::uint64_t cancelled_{0};
  /// \brief Late-rejected pending actions.
  std::uint64_t expired_{0};
  /// \brief Discarded pending actions.
  std::uint64_t discarded_{0};
  /// \brief Intents without a durable outcome.
  std::uint64_t evidence_incomplete_{0};
  /// \brief Lease conflicts observed.
  std::uint64_t lease_conflicts_{0};
  /// \brief Current drain state.
  DrainState drain_state_{DrainState::Idle};
};

static_assert(!std::is_copy_constructible_v<ServiceEmulationRegistry>,
              "ServiceEmulationRegistry must not be copyable");
static_assert(!std::is_move_constructible_v<ServiceEmulationRegistry>,
              "ServiceEmulationRegistry must not be movable");
static_assert(!std::is_copy_constructible_v<StimulationActionPath>,
              "StimulationActionPath must not be copyable");
static_assert(!std::is_move_constructible_v<StimulationActionPath>,
              "StimulationActionPath must not be movable");
static_assert(!std::is_constructible_v<ActionPathConfig, std::string_view>,
              "ActionPathConfig must be payload-free");
static_assert(!std::is_constructible_v<ActionPathConfig, std::vector<std::uint8_t>>,
              "ActionPathConfig must not accept a payload byte container");
static_assert(!std::is_constructible_v<EndpointGeneration, std::string_view>,
              "EndpointGeneration must be payload-free");
static_assert(!std::is_constructible_v<EmulationLease, std::string_view>,
              "EmulationLease must be payload-free");
static_assert(!std::is_constructible_v<EmulationLease, std::vector<std::uint8_t>>,
              "EmulationLease must not accept a payload byte container");
static_assert(!std::is_constructible_v<PendingAction, std::vector<std::uint8_t>>,
              "PendingAction must not accept a payload byte container");
static_assert(!std::is_constructible_v<SyntheticStimulationItem, std::span<const std::byte>>,
              "SyntheticStimulationItem must not retain a payload view");
static_assert(sizeof(ActionPathConfig) <= 512U, "ActionPathConfig must stay bounded");
static_assert(sizeof(EndpointGeneration) <= 128U, "EndpointGeneration must stay bounded");
static_assert(sizeof(EmulationLease) <= 128U, "EmulationLease must stay bounded");
static_assert(sizeof(PendingAction) <= 768U, "PendingAction must stay bounded");
static_assert(sizeof(SyntheticStimulationItem) <= 320U,
              "SyntheticStimulationItem must stay bounded");
static_assert(sizeof(ActionDiagnostic) <= 256U, "ActionDiagnostic must stay bounded");
static_assert(sizeof(ActionPathSnapshot) <= 128U, "ActionPathSnapshot must stay bounded");
static_assert(sizeof(LeaseSnapshot) <= 128U, "LeaseSnapshot must stay bounded");
static_assert(sizeof(CompletionRequest) <= 64U, "CompletionRequest must stay bounded");
static_assert(sizeof(CompletionReport) <= 64U, "CompletionReport must stay bounded");

} // namespace xverse::xcom::validation

#endif // XVERSE_XCOM_STIMULATION_ACTIONS_HPP_
