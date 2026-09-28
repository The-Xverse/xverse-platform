/**
 * \file stimulation_guard.hpp
 * \brief T027 fail-closed pre-emission guard: decide, fail closed, whether one declared
 *        stimulation request may enter a route, with zero mutation and zero emission on
 *        every rejection or failure.
 * \ingroup xcom_stim
 *
 * \details
 * This header is the additive T027 production surface of `xverse::xcom::validation`. It
 * consumes the accepted T025 in-process contract (`validation_session.hpp`) and the accepted
 * T-CORE interaction vocabulary (`contract.hpp`, `result.hpp`) read-only and redefines no
 * identity, digest, diagnostic, interaction, or direction type. It defines no emission,
 * injection, invocation, service-emulation, lease, route, provider, endpoint, tap, journal,
 * gateway, transport, filesystem, or network surface: the guard produces a bounded decision
 * only, and a non-`Authorized` decision proceeds to no emission.
 *
 * \ownership session-issued-handle — only a guard opened from a session's immutable permit
 *            may authorize; the guard copies the permit and the declared policy and owns its
 *            bounded tallies and loop window.
 * \lifetime session-scoped — the guard is valid for one validation-session scope and retains
 *           at most `policy.loop_window` lineage entries and bounded counters.
 * \thread_safety internally-synchronized — one per-guard mutex serializes `open`, the checks,
 *                the tallies, and the loop window; there is exactly one declared logical writer
 *                and no callback.
 * \failure Every decline is `Rejected` (a definite declared mismatch) or `Failed` (an
 *          indeterminate evaluation, including a closed guard or an unmapped time); both
 *          mutate no tally, loop entry, permit, or policy byte and emit nothing. Only
 *          `Authorized` commits.
 */

#ifndef XVERSE_XCOM_STIMULATION_GUARD_HPP_
#define XVERSE_XCOM_STIMULATION_GUARD_HPP_

#include "xverse/xcom/contract.hpp"
#include "xverse/xcom/result.hpp"
#include "xverse/xcom/validation_session.hpp"

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <string_view>
#include <type_traits>
#include <vector>

namespace xverse::xcom::validation {

/// \brief Maximum declared allowed-schema entries in one policy.
inline constexpr std::size_t kGuardMaxSchemas = 16U;
/// \brief Maximum declared loop-detection window depth.
inline constexpr std::size_t kGuardMaxLoopWindow = 64U;
/// \brief Maximum declared per-session authorized-action budget.
inline constexpr std::size_t kGuardMaxActionsPerSession = 4096U;
/// \brief Maximum declared per-window authorized-action budget.
inline constexpr std::size_t kGuardMaxActionsPerWindow = 4096U;

/// \brief Closed stimulation-action vocabulary; each enumerator is one atomic bit.
/// \ownership Value enumeration; copies trivially and owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable and safe to read concurrently.
/// \failure An out-of-vocabulary value is rejected by the guard as `RejectedConfiguration`.
enum class StimulationAction : std::uint32_t {
  /// \brief Inject one declared signal or state update.
  InjectSignal = 1U << 0U,
  /// \brief Inject one declared message or event.
  InjectMessage = 1U << 1U,
  /// \brief Invoke one declared service operation.
  InvokeService = 1U << 2U,
  /// \brief Emulate one explicitly allowed service endpoint.
  EmulateService = 1U << 3U,
};

/// \brief Bitmask of one or more `StimulationAction` bits.
using StimulationActionMask = std::uint32_t;

/// \brief Mask of every defined stimulation-action bit.
inline constexpr StimulationActionMask kDefinedStimulationActions = 0x0FU;

/// \brief Converts a stimulation action into its single-bit mask.
/// \param action A stimulation action.
/// \return The single-bit mask of `action`.
[[nodiscard]] constexpr StimulationActionMask
to_stimulation_mask(StimulationAction action) noexcept {
  return static_cast<StimulationActionMask>(action);
}

/// \brief Reports whether a candidate mask contains at least one defined bit and no undefined bit.
/// \param mask Candidate stimulation-action mask.
/// \return `true` when `mask` is non-zero and contains no undefined stimulation-action bit.
[[nodiscard]] constexpr bool is_defined_stimulation_action(StimulationActionMask mask) noexcept {
  return mask != 0U && (mask & ~kDefinedStimulationActions) == 0U;
}

/// \brief Reports whether a candidate mask holds exactly one bit.
/// \param mask Candidate stimulation-action mask.
/// \return `true` when `mask` contains exactly one bit.
[[nodiscard]] constexpr bool is_single_stimulation_action(StimulationActionMask mask) noexcept {
  return mask != 0U && (mask & (mask - 1U)) == 0U;
}

/// \brief Returns the stable name of a single defined stimulation-action mask.
/// \param mask Candidate stimulation-action mask.
/// \return The stable, non-empty name for a single defined action bit, or an empty view for a
///         zero, composite, or undefined-bit mask.
[[nodiscard]] constexpr std::string_view
stimulation_action_name(StimulationActionMask mask) noexcept {
  switch (mask) {
  case 1U << 0U:
    return "InjectSignal";
  case 1U << 1U:
    return "InjectMessage";
  case 1U << 2U:
    return "InvokeService";
  case 1U << 3U:
    return "EmulateService";
  default:
    return {};
  }
}

/// \brief Closed decision vocabulary of the guard.
/// \ownership Value enumeration; copies trivially and owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable and safe to read concurrently.
/// \failure Only `Authorized` may proceed to emission.
enum class GuardOutcome : std::uint8_t {
  /// \brief Every check passed and the bounded tallies were committed.
  Authorized,
  /// \brief A definite declared mismatch; no mutation and no emission.
  Rejected,
  /// \brief The evaluation could not complete deterministically; no mutation and no emission.
  Failed,
};

/// \brief Closed failing-check vocabulary; declaration order is evaluation and precedence order.
/// \ownership Value enumeration; copies trivially and owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable and safe to read concurrently.
/// \failure A lower rank is evaluated earlier and binds; `None` is the only success reason.
enum class GuardReason : std::uint8_t {
  /// \brief The guard is closed; no request is evaluated.
  NotOpen,
  /// \brief A malformed request or an invalid/zero/inconsistent declared bound.
  RejectedConfiguration,
  /// \brief Session, permit, or plan identity differs from the bound permit.
  PermitMismatch,
  /// \brief The session is revoked.
  Revoked,
  /// \brief The session is expired.
  Expired,
  /// \brief The session is in a non-`active`, non-revoked, non-expired state.
  NotActive,
  /// \brief The schema is undeclared or not admissible.
  SchemaMismatch,
  /// \brief The direction is inconsistent or not admissible.
  DirectionMismatch,
  /// \brief The interaction kind is inconsistent or not admissible.
  InteractionMismatch,
  /// \brief The target or interface tag differs from the permit.
  TargetMismatch,
  /// \brief The action is defined but not declared allowed.
  ActionMismatch,
  /// \brief A service owner or generation is missing, mismatched, or ambiguous.
  OwnershipConflict,
  /// \brief The per-session or per-window action budget is exhausted.
  QuotaExhausted,
  /// \brief A prohibited reinjection or a loop-window bound.
  LoopBound,
  /// \brief The resolved time is outside the permit validity interval.
  TimeOutOfWindow,
  /// \brief The time resolution is absent, unmapped, or outside tolerance.
  TimeUnmapped,
  /// \brief Every check passed; the tallies were committed.
  None,
};

/// \brief Closed open/precondition status vocabulary of the guard.
/// \ownership Value enumeration; copies trivially and owns no resource.
/// \lifetime Static-lifetime vocabulary.
/// \thread_safety Immutable and safe to read concurrently.
/// \failure A guard that is not `Ok` authorizes nothing.
enum class GuardStatus : std::uint8_t {
  /// \brief The guard is open and validated.
  Ok,
  /// \brief The supplied permit/policy pair was invalid or inconsistent; the guard stays closed.
  RejectedConfiguration,
  /// \brief The guard has not been opened.
  NotOpen,
};

/// \brief Returns the zero-based precedence rank of a guard reason.
/// \param reason A guard reason.
/// \return The zero-based rank (lower binds earlier).
[[nodiscard]] constexpr std::uint8_t precedence_rank(GuardReason reason) noexcept {
  return static_cast<std::uint8_t>(reason);
}

/// \brief Maps a guard reason to its closed decision outcome.
/// \param reason A guard reason.
/// \return `Authorized` for `None`, `Failed` for `NotOpen`/`TimeUnmapped`, else `Rejected`.
[[nodiscard]] constexpr GuardOutcome outcome_of(GuardReason reason) noexcept {
  switch (reason) {
  case GuardReason::None:
    return GuardOutcome::Authorized;
  case GuardReason::NotOpen:
  case GuardReason::TimeUnmapped:
    return GuardOutcome::Failed;
  default:
    return GuardOutcome::Rejected;
  }
}

/// \brief Returns the stable name of a guard reason.
/// \param reason A guard reason.
/// \return The stable, non-empty name.
[[nodiscard]] constexpr std::string_view reason_name(GuardReason reason) noexcept {
  switch (reason) {
  case GuardReason::NotOpen:
    return "NotOpen";
  case GuardReason::RejectedConfiguration:
    return "RejectedConfiguration";
  case GuardReason::PermitMismatch:
    return "PermitMismatch";
  case GuardReason::Revoked:
    return "Revoked";
  case GuardReason::Expired:
    return "Expired";
  case GuardReason::NotActive:
    return "NotActive";
  case GuardReason::SchemaMismatch:
    return "SchemaMismatch";
  case GuardReason::DirectionMismatch:
    return "DirectionMismatch";
  case GuardReason::InteractionMismatch:
    return "InteractionMismatch";
  case GuardReason::TargetMismatch:
    return "TargetMismatch";
  case GuardReason::ActionMismatch:
    return "ActionMismatch";
  case GuardReason::OwnershipConflict:
    return "OwnershipConflict";
  case GuardReason::QuotaExhausted:
    return "QuotaExhausted";
  case GuardReason::LoopBound:
    return "LoopBound";
  case GuardReason::TimeOutOfWindow:
    return "TimeOutOfWindow";
  case GuardReason::TimeUnmapped:
    return "TimeUnmapped";
  case GuardReason::None:
    return "None";
  default:
    return {};
  }
}

/// \brief Returns the stable name of a guard outcome.
/// \param outcome A guard outcome.
/// \return The stable, non-empty name.
[[nodiscard]] constexpr std::string_view outcome_name(GuardOutcome outcome) noexcept {
  switch (outcome) {
  case GuardOutcome::Authorized:
    return "Authorized";
  case GuardOutcome::Rejected:
    return "Rejected";
  case GuardOutcome::Failed:
    return "Failed";
  default:
    return {};
  }
}

/// \brief Returns the stable name of a guard status.
/// \param status A guard status.
/// \return The stable, non-empty name.
[[nodiscard]] constexpr std::string_view guard_status_name(GuardStatus status) noexcept {
  switch (status) {
  case GuardStatus::Ok:
    return "Ok";
  case GuardStatus::RejectedConfiguration:
    return "RejectedConfiguration";
  case GuardStatus::NotOpen:
    return "NotOpen";
  default:
    return {};
  }
}

/// \brief Interaction-kind bit for the closed action/interaction/direction table.
/// \param kind An interaction kind.
/// \return The single-bit value for a defined kind, or `0` for an out-of-vocabulary value.
[[nodiscard]] constexpr std::uint8_t interaction_bit(InteractionKind kind) noexcept {
  switch (kind) {
  case InteractionKind::signal_state_update:
    return 1U << 0U;
  case InteractionKind::message_event:
    return 1U << 1U;
  case InteractionKind::service_request:
    return 1U << 2U;
  case InteractionKind::service_response:
    return 1U << 3U;
  default:
    return 0U;
  }
}

/// \brief Endpoint-direction bit for the closed action/interaction/direction table.
/// \param direction An endpoint direction.
/// \return The single-bit value for a defined direction, or `0` for an out-of-vocabulary value.
[[nodiscard]] constexpr std::uint8_t direction_bit(EndpointDirection direction) noexcept {
  switch (direction) {
  case EndpointDirection::produce:
    return 1U << 0U;
  case EndpointDirection::consume:
    return 1U << 1U;
  case EndpointDirection::request:
    return 1U << 2U;
  case EndpointDirection::respond:
    return 1U << 3U;
  default:
    return 0U;
  }
}

/// \brief Interaction-kind bit paired with a defined stimulation action.
/// \param action A defined single-bit stimulation action.
/// \return The paired interaction bit, or `0` for an undefined action.
[[nodiscard]] constexpr std::uint8_t paired_interaction_bit(StimulationAction action) noexcept {
  switch (action) {
  case StimulationAction::InjectSignal:
    return interaction_bit(InteractionKind::signal_state_update);
  case StimulationAction::InjectMessage:
    return interaction_bit(InteractionKind::message_event);
  case StimulationAction::InvokeService:
    return interaction_bit(InteractionKind::service_request);
  case StimulationAction::EmulateService:
    return interaction_bit(InteractionKind::service_response);
  default:
    return 0U;
  }
}

/// \brief Endpoint-direction bit paired with a defined stimulation action.
/// \param action A defined single-bit stimulation action.
/// \return The paired direction bit, or `0` for an undefined action.
[[nodiscard]] constexpr std::uint8_t paired_direction_bit(StimulationAction action) noexcept {
  switch (action) {
  case StimulationAction::InjectSignal:
    return direction_bit(EndpointDirection::produce);
  case StimulationAction::InjectMessage:
    return direction_bit(EndpointDirection::produce);
  case StimulationAction::InvokeService:
    return direction_bit(EndpointDirection::request);
  case StimulationAction::EmulateService:
    return direction_bit(EndpointDirection::respond);
  default:
    return 0U;
  }
}

/// \brief Bounded, payload-free schema identity and version pair.
/// \ownership Copyable value; owns no payload, address, or free-form member.
/// \lifetime Value lifetime.
/// \thread_safety Safe to copy and read concurrently.
/// \failure The guard rejects an invalid or undeclared schema as `SchemaMismatch`.
struct SchemaKey {
  /// \brief Declared schema identity tag.
  Tag id{};
  /// \brief Declared schema version tag.
  Tag version{};

  /// \brief Value equality over both tags.
  friend bool operator==(const SchemaKey &, const SchemaKey &) noexcept = default;
};

/// \brief Bounded, payload-free declared service-owner identity.
/// \ownership Copyable value; owns no payload, address, or free-form member.
/// \lifetime Value lifetime.
/// \thread_safety Safe to copy and read concurrently.
/// \failure A missing, mismatched, or ambiguous declaration is `OwnershipConflict`.
struct ServiceOwner {
  /// \brief Declared service endpoint tag.
  Tag endpoint{};
  /// \brief Declared monotonic endpoint generation.
  std::uint64_t generation{0};
  /// \brief Whether an owner was explicitly declared.
  bool declared{false};

  /// \brief Value equality over every field.
  friend bool operator==(const ServiceOwner &, const ServiceOwner &) noexcept = default;
};

/// \brief Bounded, payload-free declared stimulation policy for one session scope.
/// \ownership Copyable, caller-owned value; copied into the guard at open.
/// \lifetime Value lifetime; the guard retains one copy for its session scope.
/// \thread_safety Safe to copy and read concurrently; the guard never mutates it.
/// \failure Every invalid, zero, over-maximum, or permit-inconsistent bound fails closed at open.
struct StimulationPolicy {
  /// \brief Plan digest; must equal the bound permit.
  PlanDigest plan_digest{};
  /// \brief Interface tag; must be valid and equal the bound permit.
  Tag interface_tag{};
  /// \brief Target tag; must be valid and equal the bound permit.
  Tag target{};
  /// \brief Validity clock domain; must be valid and equal the bound permit.
  ClockDomainId validity_domain{kInvalidClockDomain};
  /// \brief Allowed stimulation-action mask; non-zero and defined bits only.
  StimulationActionMask allowed_actions{0};
  /// \brief Allowed interaction-kind bits; non-zero and only bits `0x0F`.
  std::uint8_t allowed_interactions{0};
  /// \brief Allowed endpoint-direction bits; non-zero and only bits `0x0F`.
  std::uint8_t allowed_directions{0};
  /// \brief Declared allowed-schema table; non-empty and at most `kGuardMaxSchemas`.
  std::vector<SchemaKey> allowed_schemas{};
  /// \brief Finite per-session authorized-action budget, `1 … kGuardMaxActionsPerSession`.
  std::size_t max_actions_per_session{0};
  /// \brief Finite per-window authorized-action budget, `1 … max_actions_per_session`.
  std::size_t max_actions_per_window{0};
  /// \brief Ordinal window width, `1 … kGuardMaxActionsPerWindow`.
  std::size_t action_window{0};
  /// \brief Loop-detection window depth, `1 … kGuardMaxLoopWindow`.
  std::size_t loop_window{0};
  /// \brief Whether `EmulateService` is permitted for this session.
  bool allow_service_emulation{false};
  /// \brief Declared service-owner identity for service actions.
  ServiceOwner service_owner{};
};

/// \brief Bounded, payload-free declared stimulation request.
/// \ownership Copyable value; owns no payload, address, or free-form member.
/// \lifetime Value lifetime.
/// \thread_safety Safe to copy and read concurrently; the guard never mutates it.
/// \failure A malformed or mismatched request is rejected with the matching guard reason.
struct StimulationRequest {
  /// \brief Permit identity; must equal the bound permit.
  PermitId permit_id{};
  /// \brief Session identity; must equal the bound permit.
  SessionId session_id{};
  /// \brief Plan digest; must equal the bound permit.
  PlanDigest plan_digest{};
  /// \brief Declared stimulation action.
  StimulationAction action{StimulationAction::InjectSignal};
  /// \brief Declared interaction kind.
  InteractionKind interaction{InteractionKind::signal_state_update};
  /// \brief Declared endpoint direction.
  EndpointDirection direction{EndpointDirection::produce};
  /// \brief Declared schema identity and version.
  SchemaKey schema{};
  /// \brief Declared target tag; must equal the bound permit.
  Tag target{};
  /// \brief Declared interface tag; must equal the bound permit.
  Tag interface_tag{};
  /// \brief Declared service-owner identity, validated only for service actions.
  ServiceOwner service_owner{};
  /// \brief Declared request clock domain.
  ClockDomainId clock_domain{kInvalidClockDomain};
  /// \brief Declared schedule in `clock_domain` (informational).
  Timestamp scheduled_at{0};
  /// \brief Explicit immediate/scheduled label.
  bool immediate{false};
  /// \brief Non-zero request identity.
  std::uint64_t request_id{0};
  /// \brief Correlation identity.
  std::uint64_t correlation_id{0};
  /// \brief Causal parent identity; a non-zero value already in the loop window is prohibited.
  std::uint64_t causation_id{0};
  /// \brief Informational quota cost; the guard budgets one action per authorization.
  std::uint32_t quota_cost{0};
};

/// \brief Bounded, payload-free caller-resolved time value.
/// \ownership Copyable value; owns no payload, address, or free-form member.
/// \lifetime Value lifetime.
/// \thread_safety Safe to copy and read concurrently; the guard never mutates a time authority.
/// \failure A non-`Ok`, unmapped, or out-of-tolerance resolution fails closed as `TimeUnmapped`.
struct ResolvedTime {
  /// \brief Domain the caller resolved the value into.
  ClockDomainId domain{kInvalidClockDomain};
  /// \brief Resolved time value.
  Timestamp value{0};
  /// \brief Resolution result; only `Result::Ok` is admissible.
  Result resolution{Result::UnknownClock};

  /// \brief Value equality over every field.
  friend bool operator==(const ResolvedTime &, const ResolvedTime &) noexcept = default;
};

/// \brief Bounded, payload-free guard diagnostic.
/// \ownership Copyable value; owns a bounded reason and a bounded T025 diagnostic.
/// \lifetime Value lifetime.
/// \thread_safety Safe to copy and read concurrently.
/// \failure The bound reason is explicit for every non-`Authorized` decision.
struct GuardDiagnostic {
  /// \brief Closed guard reason.
  GuardReason reason{GuardReason::None};
  /// \brief Bounded T025 diagnostic detail.
  Diagnostic detail{};

  /// \brief Value equality over both fields.
  friend bool operator==(const GuardDiagnostic &, const GuardDiagnostic &) noexcept = default;
};

/// \brief Bounded, payload-free observable snapshot of the guard's own bookkeeping.
/// \ownership Copyable value produced by `StimulationGuard::snapshot()`.
/// \lifetime Value lifetime; an independent copy.
/// \thread_safety Safe to copy and read concurrently.
/// \failure A snapshot taken after a rejection equals the pre-rejection snapshot for every
///          operational field (the declared evaluation/rejection counters may advance).
struct GuardSnapshot {
  /// \brief Whether the guard is open.
  bool open{false};
  /// \brief Authorized actions since open.
  std::size_t actions_authorized{0};
  /// \brief Remaining per-session authorized actions.
  std::size_t actions_remaining{0};
  /// \brief Authorized actions in the current ordinal window.
  std::size_t window_actions{0};
  /// \brief Remaining per-window authorized actions.
  std::size_t window_remaining{0};
  /// \brief Lineage entries currently retained in the loop window.
  std::size_t loop_entries{0};
  /// \brief Total `authorize` calls performed while open.
  std::uint64_t evaluations{0};
  /// \brief `Rejected` outcomes.
  std::uint64_t rejections{0};
  /// \brief `Failed` outcomes.
  std::uint64_t failures{0};

  /// \brief Value equality over every field.
  friend bool operator==(const GuardSnapshot &, const GuardSnapshot &) noexcept = default;
};

/**
 * \brief Bounded, fail-closed pre-emission guard for one validation-session scope.
 *
 * The guard evaluates one declared `StimulationRequest` against the immutable `Permit` it was
 * opened from and a bounded declared `StimulationPolicy`. It returns exactly one of
 * `Authorized`, `Rejected`, or `Failed`. Only `Authorized` advances the bounded per-session and
 * per-window tallies and records the request lineage in the bounded loop window; `Rejected` and
 * `Failed` return an explicit `GuardReason` and mutate no tally, window entry, permit, or policy
 * byte. The guard exposes no emission, callback, route, injection, invocation, service-emulation,
 * or lease entry point: a non-`Authorized` decision proceeds to no emission.
 *
 * \ownership session-issued-handle — only a guard opened from the session's immutable permit
 *            may authorize.
 * \lifetime session-scoped — valid for one validation session; retains bounded state only.
 * \thread_safety internally-synchronized — one per-guard mutex serializes `open`, the checks,
 *                the tallies, and the loop window; no callback is invoked. Non-copyable and
 *                non-movable.
 * \failure A closed guard is `Failed`/`NotOpen`; an absent/unmapped/out-of-tolerance time is
 *          `Failed`/`TimeUnmapped`; every declared mismatch is `Rejected` with its reason. No
 *          decline mutates operational state or emits.
 */
class StimulationGuard {
  friend class StimulationActionPath;
public:
  /// \brief Bound snapshot type, also usable as `StimulationGuard::GuardSnapshot`.
  using GuardSnapshot = ::xverse::xcom::validation::GuardSnapshot;

  /// \brief Constructs a closed guard with zero tallies.
  StimulationGuard() noexcept = default;
  /// \brief Destructor.
  ~StimulationGuard() = default;

  /// \brief Copy construction is deleted; the guard is non-copyable.
  StimulationGuard(const StimulationGuard &) = delete;
  /// \brief Copy assignment is deleted; the guard is non-copyable.
  StimulationGuard &operator=(const StimulationGuard &) = delete;
  /// \brief Move construction is deleted; the guard is non-movable.
  StimulationGuard(StimulationGuard &&) = delete;
  /// \brief Move assignment is deleted; the guard is non-movable.
  StimulationGuard &operator=(StimulationGuard &&) = delete;

  /// \brief Validates a permit/policy pair and binds it, resetting the bounded tallies.
  /// \param permit Immutable session permit the guard is opened from.
  /// \param policy Bounded declared stimulation policy for this session.
  /// \return `GuardStatus::Ok` when the pair is valid and consistent; otherwise
  ///         `GuardStatus::RejectedConfiguration`, which leaves the guard closed with zero tallies
  ///         and authorizes no request. No external state is mutated on rejection.
  /// \pre `permit` is the session's immutable permit.
  /// \post On `Ok` the guard is open with zero tallies and a cleared loop window; on
  ///       `RejectedConfiguration` the guard is closed and `is_open()` is `false`.
  [[nodiscard]] GuardStatus open(const Permit &permit, const StimulationPolicy &policy);

  /// \brief Fail-closed evaluates one declared request and writes its diagnostic.
  /// \param request Declared stimulation request.
  /// \param session_state Current session lifecycle state read from the accepted T025 session.
  /// \param resolved_time Caller-resolved time in the permit validity domain.
  /// \param out Receives the bounded guard diagnostic; the reason is always set.
  /// \return `Authorized` only when every check passes (then the tallies are committed); otherwise
  ///         `Rejected` or `Failed`. A non-`Authorized` result mutates no tally, loop entry,
  ///         permit, or policy byte and emits nothing.
  [[nodiscard]] GuardOutcome authorize(const StimulationRequest &request, LifecycleState session_state,
                                       const ResolvedTime &resolved_time, GuardDiagnostic &out);

  /// \brief Returns an immutable snapshot of the guard's own bookkeeping.
  /// \return A value copy taken under the guard mutex; never mutates state.
  [[nodiscard]] GuardSnapshot snapshot() const;

  /// \brief Reports whether the guard is open.
  /// \return `true` when the guard was successfully opened.
  [[nodiscard]] bool is_open() const;

  /// \brief Returns the current open/precondition status.
  /// \return `GuardStatus::Ok` when open, otherwise `GuardStatus::NotOpen`.
  [[nodiscard]] GuardStatus status() const;

private:
  struct AuthorizationCheckpoint {
    std::size_t actions_authorized{0};
    std::size_t window_actions{0};
    std::uint64_t evaluations{0};
    std::vector<std::uint64_t> loop_window{};
  };
  [[nodiscard]] AuthorizationCheckpoint checkpoint() const;
  void restore_authorization(const AuthorizationCheckpoint &checkpoint);
  /// \brief Serializes `open`, the checks, the tallies, and the loop window.
  mutable std::mutex mutex_{};
  /// \brief Whether a valid permit/policy pair is bound.
  bool open_{false};
  /// \brief Bound immutable permit copy.
  Permit permit_{};
  /// \brief Bound declared policy copy.
  StimulationPolicy policy_{};
  /// \brief Authorized actions since open.
  std::size_t actions_authorized_{0};
  /// \brief Authorized actions in the current ordinal window.
  std::size_t window_actions_{0};
  /// \brief Bounded loop-detection window of authorized request identities.
  std::vector<std::uint64_t> loop_window_{};
  /// \brief Total `authorize` calls performed while open.
  std::uint64_t evaluations_{0};
  /// \brief `Rejected` outcomes.
  std::uint64_t rejections_{0};
  /// \brief `Failed` outcomes.
  std::uint64_t failures_{0};
};

static_assert(!std::is_copy_constructible_v<StimulationGuard>,
              "StimulationGuard must not be copyable");
static_assert(!std::is_move_constructible_v<StimulationGuard>,
              "StimulationGuard must not be movable");
static_assert(!std::is_constructible_v<SchemaKey, std::string_view>,
              "SchemaKey must be payload-free");
static_assert(!std::is_constructible_v<ServiceOwner, std::string_view>,
              "ServiceOwner must be payload-free");
static_assert(!std::is_constructible_v<StimulationRequest, std::string_view>,
              "StimulationRequest must be payload-free");
static_assert(!std::is_constructible_v<StimulationRequest, std::vector<std::uint8_t>>,
              "StimulationRequest must not accept a payload byte container");
static_assert(!std::is_constructible_v<StimulationPolicy, std::string_view>,
              "StimulationPolicy must be payload-free");
static_assert(sizeof(SchemaKey) <= 128U, "SchemaKey must stay bounded");
static_assert(sizeof(ServiceOwner) <= 128U, "ServiceOwner must stay bounded");
static_assert(sizeof(StimulationRequest) <= 512U, "StimulationRequest must stay bounded");
static_assert(sizeof(ResolvedTime) <= 64U, "ResolvedTime must stay bounded");
static_assert(sizeof(GuardDiagnostic) <= 256U, "GuardDiagnostic must stay bounded");
static_assert(sizeof(GuardSnapshot) <= 128U, "GuardSnapshot must stay bounded");

} // namespace xverse::xcom::validation

#endif // XVERSE_XCOM_STIMULATION_GUARD_HPP_
