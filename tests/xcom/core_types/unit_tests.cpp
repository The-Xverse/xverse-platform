/**
 * @file unit_tests.cpp
 * @brief Positive, lifetime, invariant, exact-diagnostic, and concurrency unit checks.
 * @ownership Fixtures own every contract, item, result, diagnostic, and source buffer.
 * @lifetime Tests explicitly verify values after source destruction and rvalue construction.
 * @thread_safety The concurrency check performs const reads of one shared immutable item.
 * @failure The executable reports each failed expectation and returns nonzero.
 */

#include "xverse/xcom/core_types.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <iostream>
#include <string>
#include <thread>
#include <type_traits>
#include <utility>
#include <vector>

namespace {

using namespace xverse::xcom;

/**
 * @brief Report one failed unit expectation.
 * @param condition Expected boolean condition.
 * @param message Failure detail.
 * @return The original condition.
 */
[[nodiscard]] bool expect(const bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << "unit failure: " << message << '\n';
  }
  return condition;
}

/**
 * @brief Construct a required valid contract fixture.
 * @param kind Interaction semantics.
 * @param source Compatible source direction.
 * @param target Compatible target direction.
 * @return Valid value-owned contract.
 */
[[nodiscard]] CommunicationContract make_contract(const InteractionKind kind,
                                                  const EndpointDirection source,
                                                  const EndpointDirection target) {
  const auto result = CommunicationContract::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "schema.alpha", "2.0.1", kind, source,
       target});
  return *result.value();
}

/** @return true when every compatible interaction tuple is accepted. */
[[nodiscard]] bool test_interaction_table() {
  struct InteractionCase final {
    InteractionKind kind;       /**< Interaction semantics. */
    EndpointDirection source;   /**< Compatible source direction. */
    EndpointDirection target;   /**< Compatible target direction. */
  };
  constexpr std::array<InteractionCase, 4U> cases{{
      {InteractionKind::signal_state_update, EndpointDirection::produce,
       EndpointDirection::consume},
      {InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume},
      {InteractionKind::service_request, EndpointDirection::request, EndpointDirection::respond},
      {InteractionKind::service_response, EndpointDirection::respond, EndpointDirection::request},
  }};
  for (const auto& entry : cases) {
    const auto result = CommunicationContract::create(
        {"contract.alpha", "1.2.3", "interface.alpha", "schema.alpha", "2.0.1", entry.kind,
         entry.source, entry.target});
    if (!expect(result.has_value() && result.value() != nullptr && result.diagnostics() == nullptr,
                "compatible interaction did not produce exclusive success")) {
      return false;
    }
  }
  return true;
}

/** @return true when every item metadata field survives source destruction exactly. */
[[nodiscard]] bool test_complete_item_after_source_destruction() {
  const auto result = []() {
    const auto contract = make_contract(InteractionKind::message_event,
                                        EndpointDirection::produce, EndpointDirection::consume);
    std::string contract_id = "contract.alpha";
    std::string contract_version = "1.2.3";
    std::string interface_id = "interface.alpha";
    std::string endpoint_id = "endpoint.alpha";
    std::string schema_id = "schema.alpha";
    std::string schema_version = "2.0.1";
    std::string clock_domain = "clock.monotonic";
    std::string correlation_id = "correlation.1";
    std::string causation_id = "causation.1";
    std::string route_id = "route.alpha";
    std::string provider_id = "provider.alpha";
    std::vector<std::byte> payload{std::byte{0x11}, std::byte{0x22}};
    return CommunicationItem::create(
        {contract_id, contract_version, interface_id, endpoint_id, schema_id, schema_version,
         InteractionKind::message_event, OriginKind::component, Timestamp(42), clock_domain,
         correlation_id, causation_id, route_id, provider_id, payload},
        contract);
  }();

  if (!expect(result.has_value(), "complete item was rejected")) {
    return false;
  }
  const CommunicationItem& item = *result.value();
  return expect(item.contract_id().value() == "contract.alpha", "contract identity differs") &&
         expect(item.contract_version().value() == "1.2.3", "contract version differs") &&
         expect(item.interface_id().value() == "interface.alpha", "interface identity differs") &&
         expect(item.endpoint_id().value() == "endpoint.alpha", "endpoint identity differs") &&
         expect(item.schema_id().value() == "schema.alpha", "schema identity differs") &&
         expect(item.schema_version().value() == "2.0.1", "schema version differs") &&
         expect(item.interaction_kind() == InteractionKind::message_event, "kind differs") &&
         expect(item.origin() == OriginKind::component, "origin differs") &&
         expect(item.timestamp().nanoseconds() == 42, "timestamp differs") &&
         expect(item.clock_domain().value() == "clock.monotonic", "clock domain differs") &&
         expect(item.correlation_id().value() == "correlation.1", "correlation differs") &&
         expect(item.causation_id().value() == "causation.1", "causation differs") &&
         expect(item.route_id().value() == "route.alpha", "route identity differs") &&
         expect(item.provider_id().value() == "provider.alpha", "provider identity differs") &&
         expect(item.payload().size() == 2U, "payload size differs") &&
         expect(item.payload().bytes()[0] == std::byte{0x11}, "payload byte zero differs") &&
         expect(item.payload().bytes()[1] == std::byte{0x22}, "payload byte one differs");
}

/** @return true when exact diagnostic fields and sorted bytes are stable. */
[[nodiscard]] bool test_exact_diagnostic_set() {
  const auto first = Diagnostic::create(
      {DiagnosticCode::bound_exceeded, DiagnosticSeverity::error, ValidationPhase::item,
       "zeta", "bounded reason", "bounded correction"});
  const auto second = Diagnostic::create(
      {DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::contract,
       "alpha", "required reason", "required correction"});
  if (!expect(first.has_value() && second.has_value(), "valid diagnostic was rejected")) {
    return false;
  }
  const std::array<Diagnostic, 2U> forward_inputs{*first, *second};
  const std::array<Diagnostic, 2U> reverse_inputs{*second, *first};
  const auto forward = DiagnosticSet::create(forward_inputs);
  const auto reverse = DiagnosticSet::create(reverse_inputs);
  const std::string expected =
      "contract|error|XCOM-TYPE-E001|alpha|required reason|required correction\n"
      "item|error|XCOM-TYPE-E002|zeta|bounded reason|bounded correction";
  if (!expect(forward.has_value() && reverse.has_value(), "non-empty set was rejected") ||
      !expect(forward->serialize() == expected, "serialized diagnostic sequence differs") ||
      !expect(reverse->serialize() == expected, "reordered diagnostic sequence differs")) {
    return false;
  }
  const Diagnostic& diagnostic = forward->values().front();
  return expect(diagnostic.code() == DiagnosticCode::required_field, "exact code differs") &&
         expect(diagnostic.severity() == DiagnosticSeverity::error, "severity differs") &&
         expect(diagnostic.phase() == ValidationPhase::contract, "phase differs") &&
         expect(diagnostic.affected_identity() == "alpha", "affected identity differs") &&
         expect(diagnostic.reason() == "required reason", "reason differs") &&
         expect(diagnostic.correction() == "required correction", "correction differs") &&
         expect(diagnostic.ordering_key() == expected.substr(0U, expected.find('\n')),
                "ordering key differs");
}

/** @return true when rvalue construction preserves every source invariant. */
[[nodiscard]] bool test_rvalue_source_invariants() {
  static_assert(std::is_move_constructible_v<Identity>);
  static_assert(!std::is_move_assignable_v<Identity>);
  static_assert(std::is_nothrow_move_constructible_v<DiagnosticSet>);
  static_assert(!std::is_move_assignable_v<DiagnosticSet>);
  static_assert(noexcept(CommunicationContract::create(
      CommunicationContractInput{"a", "1.0.0", "b", "c", "1.0.0",
                                 InteractionKind::message_event, EndpointDirection::produce,
                                 EndpointDirection::consume})));

  auto identity = Identity::create("identity.alpha");
  const Identity copied_from_rvalue(std::move(*identity));
  if (!expect(identity->value() == "identity.alpha", "rvalue identity source changed") ||
      !expect(copied_from_rvalue.value() == "identity.alpha", "rvalue identity copy differs")) {
    return false;
  }

  const auto diagnostic = Diagnostic::create(
      {DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::contract,
       "field", "reason", "correction"});
  const std::array<Diagnostic, 1U> inputs{*diagnostic};
  auto set = DiagnosticSet::create(inputs);
  const auto failure = Result<CommunicationContract>::failure(std::move(*set));
  if (!expect(set->size() == 1U, "rvalue diagnostic-set source became empty") ||
      !expect(!failure.has_value() && failure.value() == nullptr && failure.diagnostics() != nullptr,
              "failure result is not exclusive") ||
      !expect(failure.diagnostics()->size() == 1U, "failure result lost diagnostics")) {
    return false;
  }

  auto success = CommunicationContract::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "schema.alpha", "2.0.1",
       InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume});
  const auto copied_result(std::move(success));
  return expect(success.has_value(), "rvalue result source lost its value") &&
         expect(copied_result.has_value(), "rvalue result copy lost its value");
}

/** @return true when concurrent const reads observe identical immutable state. */
[[nodiscard]] bool test_concurrent_const_reads() {
  const auto contract = make_contract(InteractionKind::signal_state_update,
                                      EndpointDirection::produce, EndpointDirection::consume);
  const std::array<std::byte, 1U> payload{std::byte{0x01}};
  const auto result = CommunicationItem::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "endpoint.alpha", "schema.alpha", "2.0.1",
       InteractionKind::signal_state_update, OriginKind::replay, Timestamp(-1), "clock.virtual",
       "correlation.2", "causation.2", "route.alpha", "provider.alpha", payload},
      contract);
  if (!expect(result.has_value(), "concurrency fixture item was rejected")) {
    return false;
  }
  const CommunicationItem& item = *result.value();
  std::atomic<bool> valid{true};
  std::vector<std::thread> readers;
  for (std::size_t index = 0U; index < 8U; ++index) {
    readers.emplace_back([&item, &valid]() {
      for (std::size_t iteration = 0U; iteration < 2'000U; ++iteration) {
        if (item.interface_id().value() != "interface.alpha" || item.payload().size() != 1U) {
          valid.store(false);
        }
      }
    });
  }
  for (auto& reader : readers) {
    reader.join();
  }
  return expect(valid.load(), "concurrent immutable reads differed");
}

}  // namespace

/** @return Zero when every unit fixture passes, otherwise one. */
int main() {
  const bool passed = test_interaction_table() && test_complete_item_after_source_destruction() &&
                      test_exact_diagnostic_set() && test_rvalue_source_invariants() &&
                      test_concurrent_const_reads();
  return passed ? 0 : 1;
}
