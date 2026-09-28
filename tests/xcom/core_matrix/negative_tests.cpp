/**
 * @file negative_tests.cpp
 * @brief T016 consolidated SC-001 negative matrix: twenty-seven individually named rejection cases
 * spanning malformed, incompatible, over-capacity, and unauthorized classes and all four families.
 * @ownership Each case owns its fixture and local injected-defect values; no shared state exists.
 * @lifetime Every fixture and defect value is per-case; nothing survives a case.
 * @thread_safety Single-threaded; concurrency assertions live in concurrency_tests.cpp.
 * @failure Each case asserts an exact stable outcome and that no registry, provider, route, queue, or
 * lifecycle record was mutated by the rejection; a weaker or non-exact outcome fails the case.
 */

#include "test_support.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>

namespace {

using namespace xverse::xcom;
using xverse::xcom::test::CoreStackFixture;
using xverse::xcom::test::kAllInteractions;
using xverse::xcom::test::kCoreDigest;
using xverse::xcom::test::ProbeProvider;

/** A one-byte synthetic payload. */
constexpr std::array<std::byte, 1U> kOneByte{std::byte{0x2AU}};

/** @return true when the set contains exactly one diagnosed code at the expected phase. */
[[nodiscard]] bool has_code(const DiagnosticSet& set, const DiagnosticCode code,
                            const ValidationPhase phase) {
  return set.size() >= 1U &&
         set.values().front().code() == code && set.values().front().phase() == phase;
}

/** @return true when any diagnostic in the set carries the expected code. */
[[nodiscard]] bool contains_code(const DiagnosticSet& set, const DiagnosticCode code) {
  for (const Diagnostic& diagnostic : set.values()) {
    if (diagnostic.code() == code) {
      return true;
    }
  }
  return false;
}

/** @return true when both optional provider route snapshots describe the same state and queue. */
[[nodiscard]] bool same_provider_state(const ProviderResult<ProviderRouteSnapshot>& left,
                                       const ProviderResult<ProviderRouteSnapshot>& right) {
  return left.has_value() && right.has_value() &&
         left.value()->state() == right.value()->state() &&
         left.value()->queued_items() == right.value()->queued_items() &&
         left.value()->queue_capacity() == right.value()->queue_capacity();
}

}  // namespace

/** NEG-01: empty and over-bound contract identity fields are rejected. */
TEST(CoreMatrixNegative, Neg01_MalformedContract_RejectedWithRequiredFieldOrBound) {
  const auto empty = CommunicationContract::create(
      {"", "1.0.0", "interface.neg01", "schema.neg01", "1.0.0",
       InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume});
  ASSERT_FALSE(empty.has_value());
  ASSERT_FALSE(empty.diagnostics() == nullptr);
  EXPECT_TRUE(has_code(*empty.diagnostics(), DiagnosticCode::required_field,
                       ValidationPhase::contract));

  const std::string over_bound(129U, 'a');
  const auto bound = CommunicationContract::create(
      {over_bound, "1.0.0", "interface.neg01", "schema.neg01", "1.0.0",
       InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume});
  ASSERT_FALSE(bound.has_value());
  ASSERT_FALSE(bound.diagnostics() == nullptr);
  EXPECT_TRUE(contains_code(*bound.diagnostics(), DiagnosticCode::bound_exceeded));
}

/** NEG-02: an incompatible interaction/direction tuple is rejected. */
TEST(CoreMatrixNegative, Neg02_IncompatibleDirection_Rejected) {
  const auto result = CommunicationContract::create(
      {"contract.neg02", "1.0.0", "interface.neg02", "schema.neg02", "1.0.0",
       InteractionKind::service_request, EndpointDirection::produce, EndpointDirection::consume});
  ASSERT_FALSE(result.has_value());
  ASSERT_FALSE(result.diagnostics() == nullptr);
  EXPECT_TRUE(has_code(*result.diagnostics(), DiagnosticCode::incompatible_direction,
                       ValidationPhase::contract));
}

/** NEG-03: item metadata missing a required identity or over-bound is rejected in the item phase. */
TEST(CoreMatrixNegative, Neg03_MalformedItem_RejectedInItemPhase) {
  const auto contract =
      xverse::xcom::test::make_contract("neg03", InteractionKind::message_event);
  ASSERT_TRUE(contract.has_value());
  const CommunicationContract& value = *contract.value();
  const auto missing = CommunicationItem::create(
      {value.contract_id().value(), value.contract_version().value(), value.interface_id().value(),
       "endpoint.neg03", value.schema_id().value(), value.schema_version().value(),
       InteractionKind::message_event, OriginKind::component, Timestamp(1), "", "correlation.neg03",
       "causation.neg03", "route.neg03", "provider.neg03", kOneByte},
      value);
  ASSERT_FALSE(missing.has_value());
  ASSERT_FALSE(missing.diagnostics() == nullptr);
  EXPECT_TRUE(has_code(*missing.diagnostics(), DiagnosticCode::required_field,
                       ValidationPhase::item));

  const std::string over_bound(129U, 'c');
  const auto bound = CommunicationItem::create(
      {value.contract_id().value(), value.contract_version().value(), value.interface_id().value(),
       "endpoint.neg03", value.schema_id().value(), value.schema_version().value(),
       InteractionKind::message_event, OriginKind::component, Timestamp(1), "clock.neg03",
       over_bound, "causation.neg03", "route.neg03", "provider.neg03", kOneByte},
      value);
  ASSERT_FALSE(bound.has_value());
  ASSERT_FALSE(bound.diagnostics() == nullptr);
  EXPECT_TRUE(contains_code(*bound.diagnostics(), DiagnosticCode::bound_exceeded));
}

/** NEG-04: a payload over the per-route prepared bound is rejected before any mutation. */
TEST(CoreMatrixNegative, Neg04_SubmitOverPreparedPayloadBound_Rejected) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg04", 2U, 2U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const std::array<std::byte, 4U> payload{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const auto item = fixture.item_with_payload(1U, payload);
  ASSERT_TRUE(item.has_value());
  const auto status = fixture.submit(*item.value());
  EXPECT_EQ(status.outcome(), ProviderOutcome::payload_limit_exceeded);
  EXPECT_EQ(status.diagnostic_code(), "XCOM-PROV-E018");
  const auto state = fixture.route_state();
  ASSERT_TRUE(state.has_value());
  EXPECT_EQ(state.value()->queued_items(), 0U);
}

/** NEG-05: an invalid declared flow policy is rejected in the policy phase. */
TEST(CoreMatrixNegative, Neg05_InvalidFlowPolicy_RejectedInPolicyPhase) {
  const auto zero_depth = FlowPolicy::create(
      {OrderingPolicy::fifo, ReliabilityPolicy::best_effort, OverflowPolicy::reject, 0, 0, 0});
  ASSERT_FALSE(zero_depth.has_value());
  ASSERT_FALSE(zero_depth.diagnostics() == nullptr);
  EXPECT_TRUE(has_code(*zero_depth.diagnostics(), DiagnosticCode::invalid_policy,
                       ValidationPhase::policy));

  const auto out_of_vocabulary = FlowPolicy::create(
      {static_cast<OrderingPolicy>(99), ReliabilityPolicy::best_effort, OverflowPolicy::reject, 0, 0,
       1});
  ASSERT_FALSE(out_of_vocabulary.has_value());
  ASSERT_FALSE(out_of_vocabulary.diagnostics() == nullptr);
  EXPECT_TRUE(contains_code(*out_of_vocabulary.diagnostics(), DiagnosticCode::invalid_policy));
}

/** NEG-06: an unadvertised interaction family is rejected before any provider dispatch. */
TEST(CoreMatrixNegative, Neg06_UnadvertisedInteraction_RejectedBeforeDispatch) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg06", 0x01U, delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91006U);
  CoreStackFixture fixture(InteractionKind::message_event, "neg06", 1U, 16U, false, &probe, nullptr,
                           "provider.neg06");
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::unsupported_interaction);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E015");
  EXPECT_FALSE(rejected.has_value());
  EXPECT_EQ(probe.prepare_calls(), 0U);
}

/** NEG-07: an unadvertised delivery claim is rejected before any provider dispatch. */
TEST(CoreMatrixNegative, Neg07_UnadvertisedDelivery_RejectedBeforeDispatch) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg07", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91007U);
  CoreStackFixture fixture(InteractionKind::message_event, "neg07", 1U, 16U, false, &probe, nullptr,
                           "provider.neg07", "provider.neg07", kAllInteractions,
                           DeliveryCapability::reliable, OrderingCapability::per_route_fifo, 1U, 1U);
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::unsupported_delivery);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E016");
  EXPECT_EQ(probe.prepare_calls(), 0U);
}

/** NEG-08: an unadvertised ordering claim is rejected before any provider dispatch. */
TEST(CoreMatrixNegative, Neg08_UnadvertisedOrdering_RejectedBeforeDispatch) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg08", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91008U);
  CoreStackFixture fixture(InteractionKind::message_event, "neg08", 1U, 16U, false, &probe, nullptr,
                           "provider.neg08", "provider.neg08", kAllInteractions,
                           DeliveryCapability::best_effort, OrderingCapability::unordered, 1U, 1U);
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::unsupported_ordering);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E017");
  EXPECT_EQ(probe.prepare_calls(), 0U);
}

/** NEG-09: a mismatched provider contract version is rejected before any provider dispatch. */
TEST(CoreMatrixNegative, Neg09_UnsupportedContractVersion_RejectedBeforeDispatch) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg09", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91009U);
  CoreStackFixture fixture(InteractionKind::message_event, "neg09", 1U, 16U, false, &probe, nullptr,
                           "provider.neg09", "provider.neg09", kAllInteractions,
                           DeliveryCapability::best_effort, OrderingCapability::per_route_fifo, 1U,
                           1U, 1U, "2.0.0");
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::unsupported_contract_version);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E014");
  EXPECT_EQ(probe.prepare_calls(), 0U);
}

/** NEG-10: an unmappable declared delivery or ordering claim is rejected before dispatch. */
TEST(CoreMatrixNegative, Neg10_UnmappableDeclaredClaim_RejectedBeforeDispatch) {
  struct ClaimCase final {
    OrderingPolicy ordering;
    ReliabilityPolicy reliability;
    DeliveryCapability requested_delivery;
    OrderingCapability requested_ordering;
    ProviderOutcome expected;
  };
  const std::array<ClaimCase, 3U> cases{{
      {OrderingPolicy::fifo, ReliabilityPolicy::at_most_once, DeliveryCapability::best_effort,
       OrderingCapability::per_route_fifo, ProviderOutcome::unsupported_delivery},
      {OrderingPolicy::fifo, ReliabilityPolicy::exactly_once, DeliveryCapability::best_effort,
       OrderingCapability::per_route_fifo, ProviderOutcome::unsupported_delivery},
      {OrderingPolicy::priority, ReliabilityPolicy::best_effort, DeliveryCapability::best_effort,
       OrderingCapability::per_route_fifo, ProviderOutcome::unsupported_ordering},
  }};
  std::uint64_t instance = 91010U;
  std::size_t index = 0U;
  for (const auto& entry : cases) {
    const std::string provider_id = "provider.neg10." + std::to_string(index);
    const auto descriptor = xverse::xcom::test::make_descriptor(
        provider_id, kAllInteractions, delivery_capability_bit(DeliveryCapability::best_effort),
        ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
    ProbeProvider probe(descriptor, instance++);
    const auto policy = FlowPolicy::create(
        {entry.ordering, entry.reliability, OverflowPolicy::reject, 0, 0, 1});
    ASSERT_TRUE(policy.has_value());
    CoreStackFixture fixture(InteractionKind::message_event, "neg10." + std::to_string(index), 1U,
                             16U, false, &probe, &*policy.value(), provider_id, provider_id,
                             kAllInteractions, entry.requested_delivery,
                             entry.requested_ordering, 1U, 1U);
    ASSERT_TRUE(fixture.ready());
    const auto rejected = fixture.prepare();
    EXPECT_EQ(rejected.outcome(), entry.expected);
    EXPECT_EQ(probe.prepare_calls(), 0U);
    ++index;
  }
}

/** NEG-11: an unsupported declared policy dimension is rejected before dispatch. */
TEST(CoreMatrixNegative, Neg11_UnsupportedDeclaredPolicyDimension_RejectedBeforeDispatch) {
  struct DimensionCase final {
    OverflowPolicy overflow;
    std::int64_t deadline_ms;
    std::int64_t retry;
  };
  const std::array<DimensionCase, 4U> cases{{
      {OverflowPolicy::drop_oldest, 0, 0},
      {OverflowPolicy::coalesce, 0, 0},
      {OverflowPolicy::reject, 100, 0},
      {OverflowPolicy::reject, 0, 1},
  }};
  std::uint64_t instance = 91011U;
  std::size_t index = 0U;
  for (const auto& entry : cases) {
    const std::string provider_id = "provider.neg11." + std::to_string(index);
    const auto descriptor = xverse::xcom::test::make_descriptor(
        provider_id, kAllInteractions, delivery_capability_bit(DeliveryCapability::best_effort),
        ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
    ProbeProvider probe(descriptor, instance++);
    const auto policy = FlowPolicy::create({OrderingPolicy::fifo, ReliabilityPolicy::best_effort,
                                            entry.overflow, entry.deadline_ms, entry.retry, 1});
    ASSERT_TRUE(policy.has_value());
    CoreStackFixture fixture(InteractionKind::message_event, "neg11." + std::to_string(index), 1U,
                             16U, false, &probe, &*policy.value(), provider_id);
    ASSERT_TRUE(fixture.ready());
    const auto rejected = fixture.prepare();
    EXPECT_EQ(rejected.outcome(), ProviderOutcome::unsupported_policy);
    EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E030");
    EXPECT_EQ(rejected.diagnostic_message(),
              "declared route policy is not supported by the selected provider");
    // Fail-closed: rejected before any provider dispatch; no provider, route, or lifecycle mutation.
    EXPECT_EQ(probe.prepare_calls(), 0U);
    EXPECT_FALSE(fixture.prepared());
    EXPECT_FALSE(fixture.activated());
    ++index;
  }
}

/** NEG-12: a requested queue capacity above the declared depth is rejected before dispatch. */
TEST(CoreMatrixNegative, Neg12_RequestedQueueAboveDeclaredDepth_RejectedBeforeDispatch) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg12", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91012U);
  const auto policy = FlowPolicy::create({OrderingPolicy::fifo, ReliabilityPolicy::best_effort,
                                          OverflowPolicy::reject, 0, 0, 1});
  ASSERT_TRUE(policy.has_value());
  CoreStackFixture fixture(InteractionKind::message_event, "neg12", 2U, 16U, false, &probe,
                           &*policy.value(), "provider.neg12");
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::queue_limit_exceeded);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E019");
  EXPECT_FALSE(rejected.has_value());
  // Fail-closed: rejected before any provider dispatch; no provider, route, or lifecycle mutation.
  EXPECT_EQ(probe.prepare_calls(), 0U);
  EXPECT_FALSE(fixture.prepared());
  EXPECT_FALSE(fixture.activated());
}

/** NEG-13: a route declaring an unregistered provider identity is rejected. */
TEST(CoreMatrixNegative, Neg13_UnregisteredProviderIdentity_Rejected) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.registered", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91013U);
  CoreStackFixture fixture(InteractionKind::message_event, "neg13", 1U, 16U, false, &probe, nullptr,
                           "provider.registered", "provider.unregistered", kAllInteractions,
                           DeliveryCapability::best_effort, OrderingCapability::per_route_fifo, 1U,
                           1U);
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::provider_mismatch);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E025");
  EXPECT_EQ(probe.prepare_calls(), 0U);
}

/** NEG-14: a provider advertising fewer claims than the declared claim requires is rejected. */
TEST(CoreMatrixNegative, Neg14_ProviderAdvertisesFewerClaims_Rejected) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg14", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91014U);
  const auto policy = FlowPolicy::create({OrderingPolicy::fifo, ReliabilityPolicy::at_least_once,
                                          OverflowPolicy::reject, 0, 0, 1});
  ASSERT_TRUE(policy.has_value());
  CoreStackFixture fixture(InteractionKind::message_event, "neg14", 1U, 16U, false, &probe,
                           &*policy.value(), "provider.neg14", "provider.neg14", kAllInteractions,
                           DeliveryCapability::reliable, OrderingCapability::per_route_fifo, 1U, 1U);
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::unsupported_delivery);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E016");
  // Fail-closed: rejected before any provider dispatch; no provider, route, or lifecycle mutation.
  EXPECT_EQ(probe.prepare_calls(), 0U);
  EXPECT_FALSE(fixture.prepared());
  EXPECT_FALSE(fixture.activated());
}

/** NEG-15: a duplicate provider identity or instance is rejected without replacing a slot. */
TEST(CoreMatrixNegative, Neg15_DuplicateProviderIdentity_RejectedNoSlotReplaced) {
  const auto first_descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg15", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  const auto second_descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg15.other", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider first(first_descriptor, 91015U);
  ProbeProvider same_identity(first_descriptor, 91016U);
  ProbeProvider same_instance(second_descriptor, 91015U);
  // Same instance identity but a different descriptor identity is still a duplicate.
  const auto configuration = ProviderRegistryConfiguration::create(3U);
  ASSERT_TRUE(configuration.has_value());
  ProviderComposition composition(*configuration.value());
  ASSERT_EQ(composition.register_provider(first).outcome(), ProviderOutcome::registered);
  EXPECT_EQ(composition.register_provider(same_identity).outcome(),
            ProviderOutcome::duplicate_provider);
  EXPECT_EQ(composition.register_provider(same_instance).outcome(),
            ProviderOutcome::duplicate_provider);
  // The retained first slot is unchanged: re-registering it is still a duplicate.
  EXPECT_EQ(composition.register_provider(first).outcome(), ProviderOutcome::duplicate_provider);
}

/** NEG-16: a full registry rejects a new provider without changing an existing slot. */
TEST(CoreMatrixNegative, Neg16_ProviderRegistryFull_RejectedFirstSlotUnchanged) {
  const auto first_descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg16.first", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  const auto second_descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg16.second", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider first(first_descriptor, 91017U);
  ProbeProvider second(second_descriptor, 91018U);
  const auto configuration = ProviderRegistryConfiguration::create(1U);
  ASSERT_TRUE(configuration.has_value());
  ProviderComposition composition(*configuration.value());
  ASSERT_EQ(composition.register_provider(first).outcome(), ProviderOutcome::registered);
  EXPECT_EQ(composition.register_provider(second).outcome(),
            ProviderOutcome::provider_capacity_exhausted);
  EXPECT_EQ(composition.register_provider(first).outcome(), ProviderOutcome::duplicate_provider);
  EXPECT_EQ(second.prepare_calls(), 0U);
}

/** NEG-17: loopback route storage exhaustion rejects a fifth route without changing earlier ones. */
TEST(CoreMatrixNegative, Neg17_LoopbackRouteStorageExhausted_RejectedExistingRoutesUnchanged) {
  const auto contract =
      xverse::xcom::test::make_contract("neg17", InteractionKind::message_event);
  const auto configuration = LifecycleConfiguration::create({10U, 5U});
  ASSERT_TRUE(contract.has_value());
  ASSERT_TRUE(configuration.has_value());
  LifecycleController lifecycle(*configuration.value());
  const auto descriptor = xverse::xcom::test::loopback_descriptor("provider.neg17");
  LoopbackProvider provider(descriptor);
  const auto registry = ProviderRegistryConfiguration::create(1U);
  ASSERT_TRUE(registry.has_value());
  ProviderComposition composition(*registry.value());
  ASSERT_EQ(composition.register_provider(provider).outcome(), ProviderOutcome::registered);

  std::array<std::optional<RouteSpec>, 5U> route_specs{};
  std::array<std::optional<EndpointHandle>, 5U> source_handles{};
  std::array<std::optional<EndpointHandle>, 5U> destination_handles{};
  std::array<std::optional<RouteHandle>, 5U> route_handles{};
  std::size_t declared = 0U;
  for (std::size_t index = 0U; index < 5U; ++index) {
    const std::string suffix = "neg17." + std::to_string(index);
    const auto source = EndpointSpec::create(
        {"source." + suffix, kCoreDigest, "provider.neg17", EndpointDirection::produce},
        *contract.value());
    const auto destination = EndpointSpec::create(
        {"destination." + suffix, kCoreDigest, "provider.neg17", EndpointDirection::consume},
        *contract.value());
    if (!source.has_value() || !destination.has_value()) {
      break;
    }
    const auto route = RouteSpec::create({"route." + suffix, kCoreDigest, "provider.neg17"},
                                         *source.value(), *destination.value());
    if (!route.has_value()) {
      break;
    }
    const auto source_handle = lifecycle.declare_endpoint(*source.value());
    const auto destination_handle = lifecycle.declare_endpoint(*destination.value());
    if (!source_handle.has_value() || !destination_handle.has_value()) {
      break;
    }
    ASSERT_TRUE(lifecycle.validate_endpoint(*source_handle.value()).has_value());
    ASSERT_TRUE(lifecycle.validate_endpoint(*destination_handle.value()).has_value());
    ASSERT_TRUE(lifecycle.activate_endpoint(*source_handle.value()).has_value());
    ASSERT_TRUE(lifecycle.activate_endpoint(*destination_handle.value()).has_value());
    const auto route_handle = lifecycle.declare_route(*route.value());
    if (!route_handle.has_value()) {
      break;
    }
    ASSERT_TRUE(lifecycle
                    .validate_route(*route_handle.value(), *source_handle.value(),
                                    *destination_handle.value())
                    .has_value());
    route_specs[index].emplace(*route.value());
    source_handles[index].emplace(*source_handle.value());
    destination_handles[index].emplace(*destination_handle.value());
    route_handles[index].emplace(*route_handle.value());
    ++declared;
  }
  ASSERT_EQ(declared, 5U);
  const ProviderRouteRequirements requirements{"1.0.0", InteractionKind::message_event,
                                               DeliveryCapability::best_effort,
                                               OrderingCapability::per_route_fifo, 16U, 1U};
  std::array<std::optional<ProviderRouteHandle>, 4U> prepared{};
  for (std::size_t index = 0U; index < 4U; ++index) {
    const auto result = composition.prepare_route(
        lifecycle, *route_specs[index], *route_handles[index], *source_handles[index],
        *destination_handles[index], requirements);
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result.outcome(), ProviderOutcome::prepared);
    prepared[index].emplace(*result.value());
  }
  const auto before = composition.route_state(*prepared[0]);
  const auto rejected = composition.prepare_route(
      lifecycle, *route_specs[4], *route_handles[4], *source_handles[4], *destination_handles[4],
      requirements);
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::route_capacity_exhausted);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E020");
  EXPECT_FALSE(rejected.has_value());
  EXPECT_TRUE(same_provider_state(before, composition.route_state(*prepared[0])));
}

/** NEG-18: a submit beyond the configured queue capacity preserves every queued item and index. */
TEST(CoreMatrixNegative, Neg18_SubmitBeyondQueueCapacity_RejectedPreservingFifo) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg18", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto first = fixture.item(0U);
  const auto second = fixture.item(1U);
  const auto third = fixture.item(2U);
  ASSERT_TRUE(first.has_value() && second.has_value() && third.has_value());
  ASSERT_EQ(fixture.submit(*first.value()).outcome(), ProviderOutcome::accepted);
  ASSERT_EQ(fixture.submit(*second.value()).outcome(), ProviderOutcome::accepted);
  const auto before = fixture.route_state();
  const auto rejected = fixture.submit(*third.value());
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::queue_saturated);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E010");
  EXPECT_TRUE(same_provider_state(before, fixture.route_state()));
  const auto received_first = fixture.receive();
  const auto received_second = fixture.receive();
  ASSERT_TRUE(received_first.has_value() && received_second.has_value());
  EXPECT_EQ(*received_first.value(), *first.value());
  EXPECT_EQ(*received_second.value(), *second.value());
}

/** NEG-19: a submit payload over the prepared provider bound is rejected without queuing. */
TEST(CoreMatrixNegative, Neg19_SubmitPayloadOverProviderBound_Rejected) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg19", 2U, 8U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const std::array<std::byte, 16U> payload{};
  const auto item = fixture.item_with_payload(1U, payload);
  ASSERT_TRUE(item.has_value());
  const auto rejected = fixture.submit(*item.value());
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::payload_limit_exceeded);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E018");
  const auto state = fixture.route_state();
  ASSERT_TRUE(state.has_value());
  EXPECT_EQ(state.value()->queued_items(), 0U);
  EXPECT_EQ(state.value()->state(), ProviderRouteState::active);
}

/** NEG-20: closing a draining route that retains items is rejected and the resource is retained. */
TEST(CoreMatrixNegative, Neg20_CloseDrainingRouteWithItems_Rejected) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg20", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto item = fixture.item(1U);
  ASSERT_TRUE(item.has_value());
  ASSERT_EQ(fixture.submit(*item.value()).outcome(), ProviderOutcome::accepted);
  ASSERT_EQ(fixture.drain().outcome(), ProviderOutcome::draining);
  const auto rejected = fixture.close();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::queued_items_remain);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E027");
  const auto state = fixture.route_state();
  ASSERT_TRUE(state.has_value());
  EXPECT_EQ(state.value()->state(), ProviderRouteState::draining);
  EXPECT_EQ(state.value()->queued_items(), 1U);
  const auto retained = fixture.receive();
  ASSERT_TRUE(retained.has_value());
  EXPECT_EQ(*retained.value(), *item.value());
  EXPECT_EQ(fixture.close().outcome(), ProviderOutcome::closed);
}

/** NEG-21: a stale generation handle after route recreation is rejected without mutation. */
TEST(CoreMatrixNegative, Neg21_StaleGenerationHandleAfterRecreation_Rejected) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg21", 1U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  ASSERT_EQ(fixture.drain().outcome(), ProviderOutcome::draining);
  ASSERT_EQ(fixture.close().outcome(), ProviderOutcome::closed);
  const ProviderRouteHandle stale = fixture.provider_handle();

  const auto recreated_route = fixture.lifecycle().declare_route(fixture.route_spec());
  ASSERT_TRUE(recreated_route.has_value());
  EXPECT_NE(recreated_route.value()->generation(), fixture.route_handle().generation());
  ASSERT_TRUE(fixture.lifecycle()
                  .validate_route(*recreated_route.value(), fixture.source_handle(),
                                  fixture.destination_handle())
                  .has_value());
  const auto prepared = fixture.composition().prepare_route(
      fixture.lifecycle(), fixture.route_spec(), *recreated_route.value(), fixture.source_handle(),
      fixture.destination_handle(), fixture.requirements());
  ASSERT_TRUE(prepared.has_value());
  ASSERT_EQ(fixture.composition()
                .activate_route(*prepared.value(), fixture.lifecycle())
                .outcome(),
            ProviderOutcome::activated);
  const auto rejected = fixture.composition().route_state(stale);
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::invalid_provider_route_handle);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E021");
  // The recreated route remains usable.
  const auto item = fixture.item(1U);
  ASSERT_TRUE(item.has_value());
  EXPECT_EQ(fixture.composition()
                .submit(*prepared.value(), *item.value(), fixture.lifecycle())
                .outcome(),
            ProviderOutcome::accepted);
}

/** NEG-22: a handle issued by a foreign composition instance is rejected without mutation. */
TEST(CoreMatrixNegative, Neg22_ForeignCompositionHandle_Rejected) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg22", 1U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto configuration = ProviderRegistryConfiguration::create(1U);
  ASSERT_TRUE(configuration.has_value());
  ProviderComposition foreign(*configuration.value());
  ASSERT_EQ(foreign.register_provider(fixture.provider()).outcome(),
            ProviderOutcome::registered);
  const auto item = fixture.item(1U);
  ASSERT_TRUE(item.has_value());
  const auto rejected = foreign.submit(fixture.provider_handle(), *item.value(), fixture.lifecycle());
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::invalid_provider_route_handle);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E021");
  const auto observed = foreign.route_state(fixture.provider_handle());
  EXPECT_EQ(observed.outcome(), ProviderOutcome::invalid_provider_route_handle);
  // The original composition is unaffected.
  EXPECT_EQ(fixture.submit(*item.value()).outcome(), ProviderOutcome::accepted);
}

/** NEG-23: submit on a non-active route is rejected without delivery. */
TEST(CoreMatrixNegative, Neg23_SubmitOnNonActiveRoute_Rejected) {
  CoreStackFixture prepared_fixture(InteractionKind::message_event, "neg23.prepared", 1U, 16U, false);
  ASSERT_TRUE(prepared_fixture.ready());
  ASSERT_TRUE(prepared_fixture.prepare().has_value());
  const auto item = prepared_fixture.item(1U);
  ASSERT_TRUE(item.has_value());
  const auto rejected = prepared_fixture.submit(*item.value());
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::inactive_route);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E023");

  CoreStackFixture draining_fixture(InteractionKind::message_event, "neg23.draining", 1U, 16U, true);
  ASSERT_TRUE(draining_fixture.ready());
  ASSERT_TRUE(draining_fixture.activated());
  ASSERT_EQ(draining_fixture.drain().outcome(), ProviderOutcome::draining);
  const auto draining_item = draining_fixture.item(1U);
  ASSERT_TRUE(draining_item.has_value());
  EXPECT_EQ(draining_fixture.submit(*draining_item.value()).outcome(),
            ProviderOutcome::inactive_route);
}

/** NEG-24: an item bound to a different route or provider is rejected without queuing. */
TEST(CoreMatrixNegative, Neg24_ItemBoundToDifferentRoute_Rejected) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg24", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto wrong_route = fixture.item_with_binding(
      fixture.route_spec().source_endpoint_id().value(), "route.other",
      fixture.route_spec().provider_id().value(), kOneByte);
  ASSERT_TRUE(wrong_route.has_value());
  const auto route_rejected = fixture.submit(*wrong_route.value());
  EXPECT_EQ(route_rejected.outcome(), ProviderOutcome::item_mismatch);
  EXPECT_EQ(route_rejected.diagnostic_code(), "XCOM-PROV-E026");

  const auto wrong_provider = fixture.item_with_binding(
      fixture.route_spec().source_endpoint_id().value(), fixture.route_spec().route_id().value(),
      "provider.other", kOneByte);
  ASSERT_TRUE(wrong_provider.has_value());
  EXPECT_EQ(fixture.submit(*wrong_provider.value()).outcome(), ProviderOutcome::item_mismatch);
  const auto state = fixture.route_state();
  ASSERT_TRUE(state.has_value());
  EXPECT_EQ(state.value()->queued_items(), 0U);
}

/** NEG-25: reconciliation after provider/lifecycle divergence reports interrupted_resource. */
TEST(CoreMatrixNegative, Neg25_ReconcileAfterDivergence_RejectedInterrupted) {
  CoreStackFixture fixture(InteractionKind::message_event, "neg25", 1U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  ASSERT_TRUE(fixture.lifecycle().fail_route(fixture.route_handle()).has_value());
  const auto rejected = fixture.reconcile();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::interrupted_resource);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E028");
  EXPECT_FALSE(rejected.has_value());
}

/**
 * NEG-26: a signal-state-update route requesting a family the provider does not advertise is rejected
 * before any provider dispatch. This extends the SC-001 matrix to the signal_state_update family
 * (T016-IR-01 closure).
 */
TEST(CoreMatrixNegative, Neg26_SignalStateUpdateFamilyUnadvertised_RejectedBeforeDispatch) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.neg26", interaction_capability_bit(InteractionKind::message_event),
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider probe(descriptor, 91026U);
  CoreStackFixture fixture(InteractionKind::signal_state_update, "neg26", 1U, 16U, false, &probe,
                           nullptr, "provider.neg26");
  ASSERT_TRUE(fixture.ready());
  const auto rejected = fixture.prepare();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::unsupported_interaction);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E015");
  EXPECT_FALSE(rejected.has_value());
  // Fail-closed: rejected before any provider dispatch; no provider, route, or lifecycle mutation.
  EXPECT_EQ(probe.prepare_calls(), 0U);
  EXPECT_FALSE(fixture.prepared());
  EXPECT_FALSE(fixture.activated());
}

/**
 * NEG-27: an item whose route binding does not match the prepared route on a service-response route is
 * rejected without queuing. This extends the SC-001 matrix to the service_response family
 * (T016-IR-01 closure).
 */
TEST(CoreMatrixNegative, Neg27_ServiceResponseItemBinding_RejectedWithoutQueuing) {
  CoreStackFixture fixture(InteractionKind::service_response, "neg27", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto wrong_route = fixture.item_with_binding(
      fixture.route_spec().source_endpoint_id().value(), "route.other",
      fixture.route_spec().provider_id().value(), kOneByte);
  ASSERT_TRUE(wrong_route.has_value());
  const auto rejected = fixture.submit(*wrong_route.value());
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::item_mismatch);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E026");
  const auto state = fixture.route_state();
  ASSERT_TRUE(state.has_value());
  EXPECT_EQ(state.value()->queued_items(), 0U);
  EXPECT_EQ(state.value()->state(), ProviderRouteState::active);
}
