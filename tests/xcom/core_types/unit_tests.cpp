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
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
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

/** @return true when every declared policy value round-trips with its exact external text. */
[[nodiscard]] bool test_flow_policy_table() {
  constexpr std::array<OrderingPolicy, 3U> orderings{OrderingPolicy::fifo, OrderingPolicy::priority,
                                                     OrderingPolicy::unordered};
  constexpr std::array<std::string_view, 3U> ordering_text{"fifo", "priority", "unordered"};
  constexpr std::array<ReliabilityPolicy, 4U> reliabilities{
      ReliabilityPolicy::at_most_once, ReliabilityPolicy::at_least_once,
      ReliabilityPolicy::exactly_once, ReliabilityPolicy::best_effort};
  constexpr std::array<std::string_view, 4U> reliability_text{"at-most-once", "at-least-once",
                                                               "exactly-once", "best-effort"};
  constexpr std::array<OverflowPolicy, 6U> overflows{
      OverflowPolicy::drop_oldest, OverflowPolicy::drop_newest, OverflowPolicy::coalesce,
      OverflowPolicy::lossless_backpressure, OverflowPolicy::reject, OverflowPolicy::fail_closed};
  constexpr std::array<std::string_view, 6U> overflow_text{"drop-oldest",  "drop-newest",
                                                           "coalesce",     "lossless-backpressure",
                                                           "reject",       "fail-closed"};

  for (std::size_t ordering_index = 0U; ordering_index < orderings.size(); ++ordering_index) {
    for (std::size_t reliability_index = 0U; reliability_index < reliabilities.size();
         ++reliability_index) {
      for (std::size_t overflow_index = 0U; overflow_index < overflows.size(); ++overflow_index) {
        const FlowPolicyInput input{orderings[ordering_index], reliabilities[reliability_index],
                                    overflows[overflow_index], 1000, 3, 8};
        const auto result = FlowPolicy::create(input);
        if (!expect(result.has_value() && result.value() != nullptr &&
                        result.diagnostics() == nullptr,
                    "declared policy combination was rejected")) {
          return false;
        }
        const FlowPolicy& policy = *result.value();
        if (!expect(policy.ordering() == orderings[ordering_index] &&
                        policy.reliability() == reliabilities[reliability_index] &&
                        policy.overflow() == overflows[overflow_index] &&
                        policy.deadline_ms() == 1000 && policy.retry() == 3 &&
                        policy.queue_depth() == 8,
                    "declared policy did not round-trip exactly")) {
          return false;
        }
        if (!expect(to_string(policy.ordering()) == ordering_text[ordering_index] &&
                        to_string(policy.reliability()) == reliability_text[reliability_index] &&
                        to_string(policy.overflow()) == overflow_text[overflow_index],
                    "policy external text differs from the declared vocabulary")) {
          return false;
        }
      }
    }
  }
  return true;
}

/** @return true when each numeric policy bound is accepted and its neighbour is rejected. */
[[nodiscard]] bool test_flow_policy_boundaries() {
  const auto accepted = [](const std::int64_t deadline, const std::int64_t retry,
                           const std::int64_t depth) {
    const auto result = FlowPolicy::create({OrderingPolicy::unordered,
                                            ReliabilityPolicy::best_effort, OverflowPolicy::reject,
                                            deadline, retry, depth});
    return result.has_value() && result.value() != nullptr && result.diagnostics() == nullptr;
  };
  if (!expect(accepted(0, 0, 1), "minimum policy bounds were rejected") ||
      !expect(accepted(FlowPolicy::kMaximumDeadlineMs, FlowPolicy::kMaximumRetry,
                       FlowPolicy::kMaximumQueueDepth),
              "maximum policy bounds were rejected")) {
    return false;
  }

  struct BoundCase final {
    std::int64_t deadline;   /**< Candidate deadline in milliseconds. */
    std::int64_t retry;      /**< Candidate retry count. */
    std::int64_t depth;      /**< Candidate queue depth. */
    std::string_view field;  /**< Expected affected field name. */
  };
  constexpr std::array<BoundCase, 6U> rejected{{
      {-1, 0, 1, "deadline_ms"},
      {FlowPolicy::kMaximumDeadlineMs + 1, 0, 1, "deadline_ms"},
      {0, -1, 1, "retry"},
      {0, FlowPolicy::kMaximumRetry + 1, 1, "retry"},
      {0, 0, 0, "queue_depth"},
      {0, 0, FlowPolicy::kMaximumQueueDepth + 1, "queue_depth"},
  }};
  for (const BoundCase& entry : rejected) {
    const auto result = FlowPolicy::create(
        {OrderingPolicy::fifo, ReliabilityPolicy::at_most_once, OverflowPolicy::drop_oldest,
         entry.deadline, entry.retry, entry.depth});
    if (!expect(!result.has_value() && result.value() == nullptr &&
                    result.diagnostics() != nullptr,
                "out-of-range policy bound was accepted") ||
        !expect(result.diagnostics()->size() == 1U, "policy bound failure count differs")) {
      return false;
    }
    const Diagnostic& diagnostic = result.diagnostics()->values().front();
    if (!expect(diagnostic.code() == DiagnosticCode::invalid_policy &&
                    diagnostic.phase() == ValidationPhase::policy &&
                    diagnostic.affected_identity() == entry.field,
                "policy bound diagnostic differs")) {
      return false;
    }
  }
  return true;
}

/** @return true when policy copies are stable and equivalent invalid inputs serialize identically. */
[[nodiscard]] bool test_flow_policy_immutability_and_determinism() {
  static_assert(std::is_copy_constructible_v<FlowPolicy>);
  static_assert(!std::is_copy_assignable_v<FlowPolicy>);
  static_assert(std::is_nothrow_copy_constructible_v<FlowPolicy>);
  static_assert(noexcept(FlowPolicy::create(FlowPolicyInput{})));

  const auto result = FlowPolicy::create(
      {OrderingPolicy::priority, ReliabilityPolicy::exactly_once, OverflowPolicy::coalesce, 250, 4,
       16});
  if (!expect(result.has_value(), "policy immutability fixture was rejected")) {
    return false;
  }
  const FlowPolicy source = *result.value();
  const FlowPolicy copied(source);
  if (!expect(source == copied && source.deadline_ms() == 250 && copied.queue_depth() == 16,
              "policy copy changed the source or its declared fields")) {
    return false;
  }

  const auto weaker = FlowPolicy::create(
      {OrderingPolicy::priority, ReliabilityPolicy::at_least_once, OverflowPolicy::coalesce, 250, 4,
       16});
  const auto stronger = FlowPolicy::create(
      {OrderingPolicy::priority, ReliabilityPolicy::exactly_once, OverflowPolicy::coalesce, 250, 4,
       16});
  if (!expect(weaker.has_value() && stronger.has_value(), "no-upgrade fixtures were rejected") ||
      !expect(*weaker.value() != *stronger.value(),
              "distinct reliability declarations compared equal")) {
    return false;
  }

  constexpr std::array<DiagnosticInput, 5U> forward{{
      {DiagnosticCode::invalid_policy, DiagnosticSeverity::error, ValidationPhase::policy,
       "ordering", "ordering policy is outside the declared vocabulary",
       "use one declared ordering policy"},
      {DiagnosticCode::invalid_policy, DiagnosticSeverity::error, ValidationPhase::policy,
       "overflow", "overflow policy is outside the declared vocabulary",
       "use one declared overflow policy"},
      {DiagnosticCode::invalid_policy, DiagnosticSeverity::error, ValidationPhase::policy,
       "deadline_ms", "deadline is outside the declared range",
       "use a deadline between 0 and 600000 milliseconds"},
      {DiagnosticCode::invalid_policy, DiagnosticSeverity::error, ValidationPhase::policy, "retry",
       "retry is outside the declared range", "use a retry count between 0 and 64"},
      {DiagnosticCode::invalid_policy, DiagnosticSeverity::error, ValidationPhase::policy,
       "queue_depth", "queue depth is outside the declared range",
       "use a finite queue depth between 1 and 65536"},
  }};
  std::array<DiagnosticInput, forward.size()> reverse{};
  for (std::size_t index = 0U; index < forward.size(); ++index) {
    reverse[index] = forward[forward.size() - 1U - index];
  }
  const auto forward_set = DiagnosticSet::create_from_inputs(forward);
  const auto reverse_set = DiagnosticSet::create_from_inputs(reverse);
  const auto rejected = FlowPolicy::create(
      {static_cast<OrderingPolicy>(255), ReliabilityPolicy::best_effort,
       static_cast<OverflowPolicy>(255), -1, 65, 0});
  return expect(forward_set.has_value() && reverse_set.has_value(),
                "policy diagnostic set was rejected") &&
         expect(forward_set->serialize() == reverse_set->serialize(),
                "reordered policy diagnostics serialized differently") &&
         expect(rejected.diagnostics() != nullptr &&
                    forward_set->serialize() == rejected.diagnostics()->serialize(),
                "policy diagnostic sequence is not order independent");
}

}  // namespace

/** @return Zero when every unit fixture passes, otherwise one. */
int main() {
  const bool passed = test_interaction_table() && test_complete_item_after_source_destruction() &&
                      test_exact_diagnostic_set() && test_rvalue_source_invariants() &&
                      test_concurrent_const_reads() && test_flow_policy_table() &&
                      test_flow_policy_boundaries() &&
                      test_flow_policy_immutability_and_determinism();
  return passed ? 0 : 1;
}
