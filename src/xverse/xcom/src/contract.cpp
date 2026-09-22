/**
 * @file contract.cpp
 * @brief Allocation-free contract validation and interaction compatibility.
 * @ownership Successful contracts own copied values; failures own fixed diagnostics.
 * @lifetime No caller-provided view is retained after construction.
 * @thread_safety Validation uses call-local state and supports concurrent calls.
 * @failure Every invalid field is accumulated deterministically without exceptions.
 */

#include "xverse/xcom/contract.hpp"

#include <array>
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
   * @brief Append one deterministic contract diagnostic input.
   * @param code Stable diagnostic code.
   * @param field Affected field name.
   * @param reason Deterministic failure reason.
   * @param correction Deterministic corrective action.
   */
  void add(const DiagnosticCode code, const std::string_view field,
           const std::string_view reason, const std::string_view correction) noexcept {
    inputs_[size_++] = {code, DiagnosticSeverity::error, ValidationPhase::contract,
                        field, reason, correction};
  }

  /** @return The initialized diagnostic-input prefix. */
  [[nodiscard]] std::span<const DiagnosticInput> inputs() const noexcept {
    return {inputs_.data(), size_};
  }

  /** @return true when no validation error was appended. */
  [[nodiscard]] bool empty() const noexcept { return size_ == 0U; }

 private:
  /** Contract validation has at most six independent diagnostics. */
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

}  // namespace xverse::xcom
