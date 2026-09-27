/**
 * @file contract.cpp
 * @brief Allocation-free contract and flow-policy validation with interaction compatibility.
 * @ownership Successful contracts own copied values; failures own fixed diagnostics.
 * @lifetime No caller-provided view is retained after construction.
 * @thread_safety Validation uses call-local state and supports concurrent calls.
 * @failure Every invalid field is accumulated deterministically without exceptions.
 */

#include "xverse/xcom/contract.hpp"

#include <array>
#include <cstdint>
#include <span>

namespace xverse::xcom {
namespace {

/**
 * @brief Fixed-capacity call-local contract diagnostic accumulator.
 * @ownership Stores call-scoped views until create() copies them into a DiagnosticSet.
 * @lifetime Inputs and accumulator live only for one contract factory call.
 * @thread_safety Each instance is call-local.
 * @failure The contract validation matrix cannot exceed its declared capacity.
 */
class DiagnosticAccumulator final {
 public:
  /**
   * @brief Append one deterministic contract or policy diagnostic input.
   * @param code Stable diagnostic code.
   * @param field Affected field name.
   * @param reason Deterministic failure reason.
   * @param correction Deterministic corrective action.
   * @param phase Validation phase that produced the diagnostic.
   */
  void add(const DiagnosticCode code, const std::string_view field,
           const std::string_view reason, const std::string_view correction,
           const ValidationPhase phase = ValidationPhase::contract) noexcept {
    inputs_[size_++] = {code, DiagnosticSeverity::error, phase, field, reason, correction};
  }

  /** @return The initialized diagnostic-input prefix. */
  [[nodiscard]] std::span<const DiagnosticInput> inputs() const noexcept {
    return {inputs_.data(), size_};
  }

  /** @return true when no validation error was appended. */
  [[nodiscard]] bool empty() const noexcept { return size_ == 0U; }

 private:
  /** Contract and policy validation each have at most six independent diagnostics. */
  std::array<DiagnosticInput, 6U> inputs_{};
  /** Initialized input count. */
  std::size_t size_{0U};
};

/**
 * @brief Append an identity rejection when required.
 * @param diagnostics Call-local accumulator.
 * @param field Stable field name.
 * @param value Candidate identity.
 */
void validate_identity(DiagnosticAccumulator& diagnostics, const std::string_view field,
                       const std::string_view value) noexcept {
  if (value.empty()) {
    diagnostics.add(DiagnosticCode::required_field, field, "required identity is empty",
                    "provide a non-empty bounded identity");
  } else if (!Identity::create(value).has_value()) {
    diagnostics.add(DiagnosticCode::bound_exceeded, field,
                    "identity is malformed or exceeds its bound",
                    "use at most 128 bytes without control or edge whitespace");
  }
}

/**
 * @brief Append a semantic-version rejection when required.
 * @param diagnostics Call-local accumulator.
 * @param field Stable field name.
 * @param value Candidate semantic version.
 */
void validate_version(DiagnosticAccumulator& diagnostics, const std::string_view field,
                      const std::string_view value) noexcept {
  if (value.empty()) {
    diagnostics.add(DiagnosticCode::required_field, field, "required version is empty",
                    "provide a canonical semantic version");
  } else if (!SemanticVersion::create(value).has_value()) {
    diagnostics.add(DiagnosticCode::invalid_version, field,
                    "version is not bounded canonical major.minor.patch",
                    "provide three decimal components without leading zeroes");
  }
}

/**
 * @brief Validate explicit source and target directions for one interaction kind.
 * @param kind Interaction semantics.
 * @param source Source endpoint direction.
 * @param target Target endpoint direction.
 * @return true only for one declared compatible tuple.
 */
[[nodiscard]] bool directions_are_compatible(const InteractionKind kind,
                                             const EndpointDirection source,
                                             const EndpointDirection target) noexcept {
  switch (kind) {
    case InteractionKind::signal_state_update:
    case InteractionKind::message_event:
      return source == EndpointDirection::produce && target == EndpointDirection::consume;
    case InteractionKind::service_request:
      return source == EndpointDirection::request && target == EndpointDirection::respond;
    case InteractionKind::service_response:
      return source == EndpointDirection::respond && target == EndpointDirection::request;
  }
  return false;
}

/** @brief Return whether ordering is a declared value. */
[[nodiscard]] bool known_ordering(const OrderingPolicy ordering) noexcept {
  switch (ordering) {
    case OrderingPolicy::fifo:
    case OrderingPolicy::priority:
    case OrderingPolicy::unordered:
      return true;
  }
  return false;
}

/** @brief Return whether reliability is a declared value. */
[[nodiscard]] bool known_reliability(const ReliabilityPolicy reliability) noexcept {
  switch (reliability) {
    case ReliabilityPolicy::at_most_once:
    case ReliabilityPolicy::at_least_once:
    case ReliabilityPolicy::exactly_once:
    case ReliabilityPolicy::best_effort:
      return true;
  }
  return false;
}

/** @brief Return whether overflow is a declared value. */
[[nodiscard]] bool known_overflow(const OverflowPolicy overflow) noexcept {
  switch (overflow) {
    case OverflowPolicy::drop_oldest:
    case OverflowPolicy::drop_newest:
    case OverflowPolicy::coalesce:
    case OverflowPolicy::lossless_backpressure:
    case OverflowPolicy::reject:
    case OverflowPolicy::fail_closed:
      return true;
  }
  return false;
}

/**
 * @brief Append one policy rejection when a declared number is out of range.
 * @param diagnostics Call-local accumulator.
 * @param field Stable field name.
 * @param value Candidate declared number.
 * @param minimum Inclusive lower bound.
 * @param maximum Inclusive upper bound.
 * @param reason Deterministic failure reason.
 * @param correction Deterministic corrective action.
 */
void validate_policy_range(DiagnosticAccumulator& diagnostics, const std::string_view field,
                           const std::int64_t value, const std::int64_t minimum,
                           const std::int64_t maximum, const std::string_view reason,
                           const std::string_view correction) noexcept {
  if (value < minimum || value > maximum) {
    diagnostics.add(DiagnosticCode::invalid_policy, field, reason, correction,
                    ValidationPhase::policy);
  }
}

}  // namespace

std::string_view to_string(const InteractionKind kind) noexcept {
  switch (kind) {
    case InteractionKind::signal_state_update:
      return "signal-state-update";
    case InteractionKind::message_event:
      return "message-event";
    case InteractionKind::service_request:
      return "service-request";
    case InteractionKind::service_response:
      return "service-response";
  }
  return "unknown";
}

std::string_view to_string(const EndpointDirection direction) noexcept {
  switch (direction) {
    case EndpointDirection::produce:
      return "produce";
    case EndpointDirection::consume:
      return "consume";
    case EndpointDirection::request:
      return "request";
    case EndpointDirection::respond:
      return "respond";
  }
  return "unknown";
}

std::string_view to_string(const OrderingPolicy policy) noexcept {
  switch (policy) {
    case OrderingPolicy::fifo:
      return "fifo";
    case OrderingPolicy::priority:
      return "priority";
    case OrderingPolicy::unordered:
      return "unordered";
  }
  return "unknown";
}

std::string_view to_string(const ReliabilityPolicy policy) noexcept {
  switch (policy) {
    case ReliabilityPolicy::at_most_once:
      return "at-most-once";
    case ReliabilityPolicy::at_least_once:
      return "at-least-once";
    case ReliabilityPolicy::exactly_once:
      return "exactly-once";
    case ReliabilityPolicy::best_effort:
      return "best-effort";
  }
  return "unknown";
}

std::string_view to_string(const OverflowPolicy policy) noexcept {
  switch (policy) {
    case OverflowPolicy::drop_oldest:
      return "drop-oldest";
    case OverflowPolicy::drop_newest:
      return "drop-newest";
    case OverflowPolicy::coalesce:
      return "coalesce";
    case OverflowPolicy::lossless_backpressure:
      return "lossless-backpressure";
    case OverflowPolicy::reject:
      return "reject";
    case OverflowPolicy::fail_closed:
      return "fail-closed";
  }
  return "unknown";
}

Result<CommunicationContract> CommunicationContract::create(
    const CommunicationContractInput& input) noexcept {
  DiagnosticAccumulator diagnostics;
  validate_identity(diagnostics, "contract_id", input.contract_id);
  validate_version(diagnostics, "contract_version", input.contract_version);
  validate_identity(diagnostics, "interface_id", input.interface_id);
  validate_identity(diagnostics, "schema_id", input.schema_id);
  validate_version(diagnostics, "schema_version", input.schema_version);
  if (!directions_are_compatible(input.interaction_kind, input.source_direction,
                                 input.target_direction)) {
    diagnostics.add(DiagnosticCode::incompatible_direction, "directions",
                    "directions are incompatible with the interaction kind",
                    "use the interaction kind's explicit source and target directions");
  }

  if (!diagnostics.empty()) {
    const auto set = DiagnosticSet::create_from_inputs(diagnostics.inputs());
    return Result<CommunicationContract>::failure(*set);
  }

  const auto contract_id = Identity::create(input.contract_id);
  const auto contract_version = SemanticVersion::create(input.contract_version);
  const auto interface_id = Identity::create(input.interface_id);
  const auto schema_id = Identity::create(input.schema_id);
  const auto schema_version = SemanticVersion::create(input.schema_version);
  const CommunicationContract contract(*contract_id, *contract_version, *interface_id, *schema_id,
                                       *schema_version, input.interaction_kind,
                                       input.source_direction, input.target_direction);
  return Result<CommunicationContract>::success(contract);
}

Result<FlowPolicy> FlowPolicy::create(const FlowPolicyInput& input) noexcept {
  DiagnosticAccumulator diagnostics;
  if (!known_ordering(input.ordering)) {
    diagnostics.add(DiagnosticCode::invalid_policy, "ordering",
                    "ordering policy is outside the declared vocabulary",
                    "use one declared ordering policy", ValidationPhase::policy);
  }
  if (!known_reliability(input.reliability)) {
    diagnostics.add(DiagnosticCode::invalid_policy, "reliability",
                    "reliability policy is outside the declared vocabulary",
                    "use one declared reliability policy", ValidationPhase::policy);
  }
  if (!known_overflow(input.overflow)) {
    diagnostics.add(DiagnosticCode::invalid_policy, "overflow",
                    "overflow policy is outside the declared vocabulary",
                    "use one declared overflow policy", ValidationPhase::policy);
  }
  validate_policy_range(diagnostics, "deadline_ms", input.deadline_ms, 0,
                        kMaximumDeadlineMs, "deadline is outside the declared range",
                        "use a deadline between 0 and 600000 milliseconds");
  validate_policy_range(diagnostics, "retry", input.retry, 0, kMaximumRetry,
                        "retry is outside the declared range",
                        "use a retry count between 0 and 64");
  validate_policy_range(diagnostics, "queue_depth", input.queue_depth, 1,
                        kMaximumQueueDepth, "queue depth is outside the declared range",
                        "use a finite queue depth between 1 and 65536");

  if (!diagnostics.empty()) {
    const auto set = DiagnosticSet::create_from_inputs(diagnostics.inputs());
    return Result<FlowPolicy>::failure(*set);
  }

  return Result<FlowPolicy>::success(FlowPolicy(input));
}

}  // namespace xverse::xcom
