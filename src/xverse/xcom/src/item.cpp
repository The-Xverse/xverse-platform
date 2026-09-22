/**
 * @file item.cpp
 * @brief Allocation-free communication-item validation and contract consistency.
 * @ownership Successful items own copied metadata and payload; failures own diagnostics.
 * @lifetime No caller-provided view or span is retained after construction.
 * @thread_safety Validation uses call-local state and supports concurrent calls.
 * @failure Invalid fields return a deterministic non-empty set without exceptions.
 */

#include "xverse/xcom/item.hpp"

#include <array>
#include <span>

namespace xverse::xcom {
namespace {

/**
 * @brief Fixed-capacity call-local item diagnostic accumulator.
 * @ownership Stores call-scoped views until create() copies them into a DiagnosticSet.
 * @lifetime Inputs and accumulator live only for one item factory call.
 * @thread_safety Each instance is call-local.
 * @failure The item validation matrix cannot exceed its declared capacity.
 */
class DiagnosticAccumulator final {
 public:
  /**
   * @brief Append one deterministic item diagnostic input.
   * @param code Stable diagnostic code.
   * @param field Affected field name.
   * @param reason Deterministic failure reason.
   * @param correction Deterministic corrective action.
   */
  void add(const DiagnosticCode code, const std::string_view field,
           const std::string_view reason, const std::string_view correction) noexcept {
    inputs_[size_++] = {code, DiagnosticSeverity::error, ValidationPhase::item,
                        field, reason, correction};
  }

  /** @return The initialized diagnostic-input prefix. */
  [[nodiscard]] std::span<const DiagnosticInput> inputs() const noexcept {
    return {inputs_.data(), size_};
  }

  /** @return true when no validation error was appended. */
  [[nodiscard]] bool empty() const noexcept { return size_ == 0U; }

 private:
  /** Item validation has at most nineteen independent diagnostics. */
  std::array<DiagnosticInput, 19U> inputs_{};
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
 * @brief Append a contract-mismatch diagnostic for differing non-empty metadata.
 * @param diagnostics Call-local accumulator.
 * @param field Stable field name.
 * @param actual Candidate item metadata.
 * @param expected Validated contract metadata.
 */
void validate_match(DiagnosticAccumulator& diagnostics, const std::string_view field,
                    const std::string_view actual, const std::string_view expected) noexcept {
  if (!actual.empty() && actual != expected) {
    diagnostics.add(DiagnosticCode::contract_mismatch, field,
                    "item metadata differs from its communication contract",
                    "use the exact immutable contract value");
  }
}

/**
 * @brief Validate an origin enumeration.
 * @param origin Candidate origin.
 * @return true only for a declared domain-neutral origin.
 */
[[nodiscard]] bool known_origin(const OriginKind origin) noexcept {
  switch (origin) {
    case OriginKind::component:
    case OriginKind::validation_tool:
    case OriginKind::replay:
    case OriginKind::provider_generated:
      return true;
  }
  return false;
}

}  // namespace

std::string_view to_string(const OriginKind origin) noexcept {
  switch (origin) {
    case OriginKind::component:
      return "component";
    case OriginKind::validation_tool:
      return "validation-tool";
    case OriginKind::replay:
      return "replay";
    case OriginKind::provider_generated:
      return "provider-generated";
  }
  return "unknown";
}

Result<CommunicationItem> CommunicationItem::create(
    const CommunicationItemInput& input, const CommunicationContract& contract) noexcept {
  DiagnosticAccumulator diagnostics;
  validate_identity(diagnostics, "contract_id", input.contract_id);
  validate_version(diagnostics, "contract_version", input.contract_version);
  validate_identity(diagnostics, "interface_id", input.interface_id);
  validate_identity(diagnostics, "endpoint_id", input.endpoint_id);
  validate_identity(diagnostics, "schema_id", input.schema_id);
  validate_version(diagnostics, "schema_version", input.schema_version);
  validate_identity(diagnostics, "clock_domain", input.clock_domain);
  validate_identity(diagnostics, "correlation_id", input.correlation_id);
  validate_identity(diagnostics, "causation_id", input.causation_id);
  validate_identity(diagnostics, "route_id", input.route_id);
  validate_identity(diagnostics, "provider_id", input.provider_id);
  if (!known_origin(input.origin)) {
    diagnostics.add(DiagnosticCode::bound_exceeded, "origin",
                    "origin is outside the declared enumeration",
                    "use one declared domain-neutral origin kind");
  }
  if (input.payload.size() > kMaximumPayloadBytes) {
    diagnostics.add(DiagnosticCode::bound_exceeded, "payload",
                    "payload exceeds the explicit item bound", "use at most 65536 bytes");
  }

  validate_match(diagnostics, "contract_id", input.contract_id, contract.contract_id().value());
  validate_match(diagnostics, "contract_version", input.contract_version,
                 contract.contract_version().value());
  validate_match(diagnostics, "interface_id", input.interface_id, contract.interface_id().value());
  validate_match(diagnostics, "schema_id", input.schema_id, contract.schema_id().value());
  validate_match(diagnostics, "schema_version", input.schema_version,
                 contract.schema_version().value());
  if (input.interaction_kind != contract.interaction_kind()) {
    diagnostics.add(DiagnosticCode::contract_mismatch, "interaction_kind",
                    "item interaction kind differs from its communication contract",
                    "use the exact immutable contract interaction kind");
  }

  if (!diagnostics.empty()) {
    const auto set = DiagnosticSet::create_from_inputs(diagnostics.inputs());
    return Result<CommunicationItem>::failure(*set);
  }

  const auto contract_id = Identity::create(input.contract_id);
  const auto contract_version = SemanticVersion::create(input.contract_version);
  const auto interface_id = Identity::create(input.interface_id);
  const auto endpoint_id = Identity::create(input.endpoint_id);
  const auto schema_id = Identity::create(input.schema_id);
  const auto schema_version = SemanticVersion::create(input.schema_version);
  const auto clock_domain = Identity::create(input.clock_domain);
  const auto correlation_id = Identity::create(input.correlation_id);
  const auto causation_id = Identity::create(input.causation_id);
  const auto route_id = Identity::create(input.route_id);
  const auto provider_id = Identity::create(input.provider_id);
  const auto payload = Payload::create(input.payload);
  const CommunicationItem item(*contract_id, *contract_version, *interface_id, *endpoint_id,
                               *schema_id, *schema_version, input.interaction_kind, input.origin,
                               input.timestamp, *clock_domain, *correlation_id, *causation_id,
                               *route_id, *provider_id, *payload);
  return Result<CommunicationItem>::success(item);
}

}  // namespace xverse::xcom
