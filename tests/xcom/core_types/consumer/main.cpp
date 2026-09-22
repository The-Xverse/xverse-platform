/**
 * @file main.cpp
 * @brief External consumer fixture for public success and diagnostic contracts.
 * @ownership The fixture owns every contract, item, result, and source payload.
 * @lifetime Public accessor views are consumed only while their owners live.
 * @thread_safety The fixture is single-threaded and uses immutable values.
 * @failure Any public construction or exact-diagnostic mismatch returns nonzero.
 */

#include <xverse/xcom/core_types.hpp>

#include <array>
#include <cstddef>

/** @return Zero when public success and failure APIs behave exactly as declared. */
int main() {
  using namespace xverse::xcom;
  const auto contract = CommunicationContract::create(
      {"consumer.contract", "1.0.0", "consumer.interface", "consumer.schema", "1.0.0",
       InteractionKind::service_request, EndpointDirection::request, EndpointDirection::respond});
  if (!contract.has_value()) {
    return 1;
  }
  const std::array<std::byte, 2U> payload{std::byte{0x01}, std::byte{0x02}};
  const auto item = CommunicationItem::create(
      {"consumer.contract", "1.0.0", "consumer.interface", "consumer.endpoint",
       "consumer.schema", "1.0.0", InteractionKind::service_request,
       OriginKind::validation_tool, Timestamp(100), "consumer.clock", "consumer.correlation",
       "consumer.causation", "consumer.route", "consumer.provider", payload},
      *contract.value());
  if (!item.has_value() || item.value()->payload().size() != payload.size() ||
      item.value()->origin() != OriginKind::validation_tool) {
    return 2;
  }

  const auto rejected = CommunicationContract::create(
      {"", "1.0.0", "consumer.interface", "consumer.schema", "1.0.0",
       InteractionKind::service_request, EndpointDirection::request, EndpointDirection::respond});
  if (rejected.has_value() || rejected.value() != nullptr || rejected.diagnostics() == nullptr ||
      rejected.diagnostics()->size() != 1U) {
    return 3;
  }
  const Diagnostic& diagnostic = rejected.diagnostics()->values().front();
  return diagnostic.code() == DiagnosticCode::required_field &&
                 diagnostic.severity() == DiagnosticSeverity::error &&
                 diagnostic.phase() == ValidationPhase::contract &&
                 diagnostic.affected_identity() == "contract_id"
             ? 0
             : 4;
}
