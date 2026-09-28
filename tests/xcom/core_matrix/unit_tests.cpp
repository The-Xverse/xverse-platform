/**
 * @file unit_tests.cpp
 * @brief T016 nominal consolidated core matrix: interaction kinds, capabilities, policy, ownership,
 * lifecycle, queue bounds, and deterministic diagnostics as individually named GTest cases.
 * @ownership Each case owns its fixture and local values; no shared mutable fixture exists.
 * @lifetime Every fixture is per-case; nothing survives a case.
 * @thread_safety Cases are single-threaded except the concurrent const-read case.
 * @failure A failed expectation fails the case; no case is skipped, disabled, or conditionally run.
 */

#include "test_support.hpp"

#include <gtest/gtest.h>

#include <array>
#include <clocale>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace {

using namespace xverse::xcom;
using xverse::xcom::test::CoreStackFixture;
using xverse::xcom::test::DeclarationFixture;

/** Assert a full-stack round trip for one interaction family. */
void expect_round_trip(const InteractionKind kind, const std::string_view suffix) {
  CoreStackFixture fixture(kind, suffix, 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto item = fixture.item(7U);
  ASSERT_TRUE(item.has_value());
  EXPECT_EQ(fixture.submit(*item.value()).outcome(), ProviderOutcome::accepted);
  const auto received = fixture.receive();
  ASSERT_TRUE(received.has_value());
  EXPECT_EQ(received.outcome(), ProviderOutcome::received);
  EXPECT_EQ(*received.value(), *item.value());
  EXPECT_TRUE(received.value()->payload() == item.value()->payload());
  EXPECT_EQ(received.value()->interaction_kind(), kind);
  EXPECT_EQ(received.value()->endpoint_id().value(),
            fixture.route_spec().source_endpoint_id().value());
  EXPECT_EQ(received.value()->route_id().value(), fixture.route_spec().route_id().value());
  EXPECT_EQ(received.value()->provider_id().value(),
            fixture.route_spec().provider_id().value());
}

}  // namespace

/** CHK-05: signal-state-update family round trips end to end. */
TEST(CoreMatrix, InteractionKind_SignalStateUpdate_RoundTripsExactly) {
  expect_round_trip(InteractionKind::signal_state_update, "kind.signal");
}

/** CHK-05: message-event family round trips end to end. */
TEST(CoreMatrix, InteractionKind_MessageEvent_RoundTripsExactly) {
  expect_round_trip(InteractionKind::message_event, "kind.message");
}

/** CHK-05: service-request family preserves request/respond directions. */
TEST(CoreMatrix, InteractionKind_ServiceRequest_RoundTripsExactly) {
  expect_round_trip(InteractionKind::service_request, "kind.request");
}

/** CHK-05: service-response family preserves respond/request directions. */
TEST(CoreMatrix, InteractionKind_ServiceResponse_RoundTripsExactly) {
  expect_round_trip(InteractionKind::service_response, "kind.response");
}

/** CHK-06: stable capability bits and descriptor mask validation. */
TEST(CoreMatrix, CapabilityMask_StableBitsAndDescriptorValidation) {
  EXPECT_EQ(interaction_capability_bit(InteractionKind::signal_state_update), 1U);
  EXPECT_EQ(interaction_capability_bit(InteractionKind::message_event), 2U);
  EXPECT_EQ(interaction_capability_bit(InteractionKind::service_request), 4U);
  EXPECT_EQ(interaction_capability_bit(InteractionKind::service_response), 8U);
  EXPECT_EQ(delivery_capability_bit(DeliveryCapability::best_effort), 1U);
  EXPECT_EQ(delivery_capability_bit(DeliveryCapability::reliable), 2U);
  EXPECT_EQ(ordering_capability_bit(OrderingCapability::unordered), 1U);
  EXPECT_EQ(ordering_capability_bit(OrderingCapability::per_route_fifo), 2U);

  const ProviderDescriptorInput valid{"provider.mask", "1.0.0", "source.mask", 0x0FU, 1U, 2U,
                                      64U, 1U, 1U};
  EXPECT_TRUE(ProviderDescriptor::create(valid).has_value());
  EXPECT_FALSE(ProviderDescriptor::create({"provider.mask", "1.0.0", "source.mask", 0U, 1U, 2U,
                                           64U, 1U, 1U})
                   .has_value());
  EXPECT_FALSE(ProviderDescriptor::create({"provider.mask", "1.0.0", "source.mask", 0x10U, 1U,
                                           2U, 64U, 1U, 1U})
                   .has_value());
  EXPECT_FALSE(ProviderDescriptor::create({"provider.mask", "1.0.0", "source.mask", 0x0FU, 0U,
                                           2U, 64U, 1U, 1U})
                   .has_value());
  EXPECT_FALSE(ProviderDescriptor::create({"provider.mask", "1.0.0", "source.mask", 0x0FU, 1U,
                                           0U, 64U, 1U, 1U})
                   .has_value());
}

/** CHK-06: requested family/delivery/ordering contained in advertised masks prepares. */
TEST(CoreMatrix, CapabilityContainment_RequestMustBeAdvertised) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.containment", xverse::xcom::test::kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  xverse::xcom::test::ProbeProvider probe(descriptor, 90001U);
  CoreStackFixture fixture(InteractionKind::message_event, "containment", 1U, 16U, false, &probe,
                           nullptr, "provider.containment");
  ASSERT_TRUE(fixture.ready());
  const auto prepared = fixture.prepare();
  EXPECT_EQ(prepared.outcome(), ProviderOutcome::prepared);
  EXPECT_TRUE(prepared.has_value());
}

/** CHK-06: positive declared at_least_once mapping to the reliable claim. */
TEST(CoreMatrix, DeclaredPolicy_AtLeastOnceMapsToReliable_Positive) {
  const auto descriptor = xverse::xcom::test::make_descriptor(
      "provider.reliable", xverse::xcom::test::kAllInteractions,
      delivery_capability_bit(DeliveryCapability::reliable),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  xverse::xcom::test::ProbeProvider probe(descriptor, 90002U);
  const auto policy =
      FlowPolicy::create({OrderingPolicy::fifo, ReliabilityPolicy::at_least_once,
                          OverflowPolicy::reject, 0, 0, 1});
  ASSERT_TRUE(policy.has_value());
  CoreStackFixture fixture(InteractionKind::message_event, "policy.reliable", 1U, 16U, true, &probe,
                           policy.value() ? &*policy.value() : nullptr, "provider.reliable",
                           "provider.reliable", xverse::xcom::test::kAllInteractions,
                           DeliveryCapability::reliable, OrderingCapability::per_route_fifo, 1U, 1U);
  ASSERT_TRUE(fixture.ready());
  EXPECT_TRUE(fixture.activated());
  EXPECT_TRUE(probe.prepare_calls() == 1U);
  EXPECT_TRUE(probe.activate_calls() == 1U);
}

/** CHK-07: a supported declared claim prepares and activates. */
TEST(CoreMatrix, DeclaredPolicy_SupportedClaimPreparesAndActivates) {
  const auto policy =
      FlowPolicy::create({OrderingPolicy::fifo, ReliabilityPolicy::best_effort,
                          OverflowPolicy::reject, 0, 0, 1});
  ASSERT_TRUE(policy.has_value());
  CoreStackFixture fixture(InteractionKind::message_event, "policy.supported", 1U, 16U, true, nullptr,
                           &*policy.value());
  ASSERT_TRUE(fixture.ready());
  EXPECT_TRUE(fixture.activated());
  EXPECT_TRUE(fixture.route_spec().has_policy());
}

/** CHK-07: an unbound three-argument route prepares and activates unchanged. */
TEST(CoreMatrix, DeclaredPolicy_UnboundRouteIsUnaffected) {
  CoreStackFixture fixture(InteractionKind::message_event, "policy.unbound", 1U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  EXPECT_TRUE(fixture.activated());
  EXPECT_FALSE(fixture.route_spec().has_policy());
  EXPECT_TRUE(fixture.route_spec().policy() == nullptr);
}

/** CHK-08: same-identity routes differing only by declared policy compare unequal. */
TEST(CoreMatrix, DeclaredPolicy_SameIdentityDifferentPolicyCompareUnequal) {
  const auto contract = xverse::xcom::test::make_contract("policy.identity",
                                                          InteractionKind::message_event);
  ASSERT_TRUE(contract.has_value());
  const auto source = EndpointSpec::create(
      {"source.policy.identity", xverse::xcom::test::kCoreDigest, "provider.policy.identity",
       EndpointDirection::produce},
      *contract.value());
  const auto destination = EndpointSpec::create(
      {"destination.policy.identity", xverse::xcom::test::kCoreDigest,
       "provider.policy.identity", EndpointDirection::consume},
      *contract.value());
  ASSERT_TRUE(source.has_value());
  ASSERT_TRUE(destination.has_value());
  const auto first_policy = FlowPolicy::create({OrderingPolicy::fifo, ReliabilityPolicy::best_effort,
                                                OverflowPolicy::reject, 0, 0, 1});
  const auto second_policy = FlowPolicy::create(
      {OrderingPolicy::fifo, ReliabilityPolicy::at_least_once, OverflowPolicy::reject, 0, 0, 1});
  ASSERT_TRUE(first_policy.has_value());
  ASSERT_TRUE(second_policy.has_value());
  const RouteSpecInput input{"route.policy.identity", xverse::xcom::test::kCoreDigest,
                             "provider.policy.identity"};
  const auto first = RouteSpec::create(input, *source.value(), *destination.value(),
                                       *first_policy.value());
  const auto second = RouteSpec::create(input, *source.value(), *destination.value(),
                                        *second_policy.value());
  ASSERT_TRUE(first.has_value());
  ASSERT_TRUE(second.has_value());
  EXPECT_EQ(first.value()->route_id().value(), second.value()->route_id().value());
  EXPECT_EQ(first.value()->source_endpoint_id().value(),
            second.value()->source_endpoint_id().value());
  EXPECT_FALSE(*first.value() == *second.value());
  ASSERT_TRUE(first.value()->has_policy());
  ASSERT_TRUE(second.value()->has_policy());
  EXPECT_FALSE(*first.value()->policy() == *second.value()->policy());
}

/** CHK-09: issued handles, snapshots, and values are copyable and readable. */
TEST(CoreMatrix, Ownership_ExactHandlesAreCopyableAndReadable) {
  CoreStackFixture fixture(InteractionKind::message_event, "ownership", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const EndpointHandle endpoint_copy = fixture.source_handle();
  EXPECT_EQ(endpoint_copy.kind(), ResourceKind::endpoint);
  EXPECT_EQ(endpoint_copy.controller_id(), fixture.source_handle().controller_id());
  EXPECT_EQ(endpoint_copy.identity(), fixture.source_handle().identity());
  EXPECT_EQ(endpoint_copy.generation(), fixture.source_handle().generation());
  const RouteHandle route_copy = fixture.route_handle();
  EXPECT_EQ(route_copy.kind(), ResourceKind::route);
  EXPECT_EQ(route_copy.generation(), fixture.route_handle().generation());
  const ProviderRouteHandle provider_copy = fixture.provider_handle();
  EXPECT_EQ(provider_copy.provider_route_generation(),
            fixture.provider_handle().provider_route_generation());
  EXPECT_EQ(provider_copy.lifecycle_route_generation(),
            fixture.provider_handle().lifecycle_route_generation());

  const auto first_endpoint = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
  const auto second_endpoint = fixture.lifecycle().endpoint_snapshot(endpoint_copy);
  ASSERT_TRUE(first_endpoint.has_value());
  ASSERT_TRUE(second_endpoint.has_value());
  EXPECT_EQ(*first_endpoint.value(), *second_endpoint.value());

  // A snapshot constructed from an rvalue handle copy remains independently readable.
  const auto snapshot = fixture.lifecycle().route_snapshot(RouteHandle(fixture.route_handle()));
  ASSERT_TRUE(snapshot.has_value());
  EXPECT_EQ(snapshot.value()->kind(), ResourceKind::route);
  EXPECT_EQ(snapshot.value()->state(), LifecycleState::active);
}

/** CHK-10: accepted endpoint and route state transitions and idempotence. */
TEST(CoreMatrix, Lifecycle_EndpointAndRouteStateTable) {
  DeclarationFixture fixture(InteractionKind::message_event, "lifecycle.table");
  ASSERT_TRUE(fixture.ready());

  EXPECT_FALSE(fixture.lifecycle().activate_endpoint(fixture.source_handle()).has_value());
  const auto validated = fixture.lifecycle().validate_endpoint(fixture.source_handle());
  ASSERT_TRUE(validated.has_value());
  EXPECT_EQ(validated.value()->state(), LifecycleState::validated);
  EXPECT_TRUE(fixture.lifecycle().validate_endpoint(fixture.source_handle()).has_value());
  const auto active = fixture.lifecycle().activate_endpoint(fixture.source_handle());
  ASSERT_TRUE(active.has_value());
  EXPECT_EQ(active.value()->state(), LifecycleState::active);
  EXPECT_TRUE(fixture.lifecycle().activate_endpoint(fixture.source_handle()).has_value());
  const auto revalidated = fixture.lifecycle().validate_endpoint(fixture.source_handle());
  ASSERT_FALSE(revalidated.has_value());

  ASSERT_TRUE(fixture.lifecycle().validate_endpoint(fixture.destination_handle()).has_value());
  ASSERT_TRUE(fixture.lifecycle().activate_endpoint(fixture.destination_handle()).has_value());

  // A route cannot activate before it is validated.
  EXPECT_FALSE(fixture.lifecycle()
                   .activate_route(fixture.route_handle(), fixture.source_handle(),
                                   fixture.destination_handle())
                   .has_value());
  const auto route_validated = fixture.lifecycle().validate_route(
      fixture.route_handle(), fixture.source_handle(), fixture.destination_handle());
  ASSERT_TRUE(route_validated.has_value());
  EXPECT_EQ(route_validated.value()->state(), LifecycleState::validated);
  const auto route_active = fixture.lifecycle().activate_route(
      fixture.route_handle(), fixture.source_handle(), fixture.destination_handle());
  ASSERT_TRUE(route_active.has_value());
  EXPECT_EQ(route_active.value()->state(), LifecycleState::active);

  // An in-use endpoint cannot drain while its nonclosed route exists.
  const auto endpoint_in_use = fixture.lifecycle().drain_endpoint(fixture.source_handle());
  ASSERT_FALSE(endpoint_in_use.has_value());
  EXPECT_EQ(endpoint_in_use.diagnostics()->values().front().code(),
            DiagnosticCode::endpoint_in_use);

  ASSERT_TRUE(fixture.lifecycle().drain_route(fixture.route_handle()).has_value());
  ASSERT_TRUE(fixture.lifecycle().close_route(fixture.route_handle()).has_value());
  const auto drained_endpoint = fixture.lifecycle().drain_endpoint(fixture.source_handle());
  ASSERT_TRUE(drained_endpoint.has_value());
  EXPECT_EQ(drained_endpoint.value()->state(), LifecycleState::draining);
  const auto closed_endpoint = fixture.lifecycle().close_endpoint(fixture.source_handle());
  ASSERT_TRUE(closed_endpoint.has_value());
  EXPECT_EQ(closed_endpoint.value()->state(), LifecycleState::closed);
}

/** CHK-11: provider route prepared -> active -> draining -> closed. */
TEST(CoreMatrix, Lifecycle_ProviderRoutePreparedActiveDrainingClosed) {
  CoreStackFixture fixture(InteractionKind::message_event, "provider.lifecycle", 2U, 16U, false);
  ASSERT_TRUE(fixture.ready());
  ASSERT_FALSE(fixture.prepared());
  const auto prepared = fixture.prepare();
  ASSERT_TRUE(prepared.has_value());
  EXPECT_EQ(prepared.outcome(), ProviderOutcome::prepared);
  ASSERT_TRUE(fixture.prepared());
  ASSERT_FALSE(fixture.activated());

  const auto prepared_state = fixture.route_state();
  ASSERT_TRUE(prepared_state.has_value());
  EXPECT_EQ(prepared_state.value()->state(), ProviderRouteState::prepared);
  EXPECT_EQ(prepared_state.value()->queued_items(), 0U);

  EXPECT_EQ(fixture.composition().activate_route(fixture.provider_handle(), fixture.lifecycle())
                .outcome(),
            ProviderOutcome::activated);
  const auto active_state = fixture.route_state();
  ASSERT_TRUE(active_state.has_value());
  EXPECT_EQ(active_state.value()->state(), ProviderRouteState::active);

  const auto item = fixture.item(1U);
  ASSERT_TRUE(item.has_value());
  EXPECT_EQ(fixture.submit(*item.value()).outcome(), ProviderOutcome::accepted);
  EXPECT_EQ(fixture.drain().outcome(), ProviderOutcome::draining);
  const auto draining_state = fixture.route_state();
  ASSERT_TRUE(draining_state.has_value());
  EXPECT_EQ(draining_state.value()->state(), ProviderRouteState::draining);
  EXPECT_EQ(draining_state.value()->queued_items(), 1U);
  const auto retained = fixture.receive();
  ASSERT_TRUE(retained.has_value());
  EXPECT_EQ(*retained.value(), *item.value());
  EXPECT_EQ(fixture.close().outcome(), ProviderOutcome::closed);
  const auto closed_state = fixture.route_state();
  ASSERT_TRUE(closed_state.has_value());
  EXPECT_EQ(closed_state.value()->state(), ProviderRouteState::closed);
  EXPECT_EQ(closed_state.value()->queued_items(), 0U);
}

/** CHK-12: fixed queue and payload bounds are exact. */
TEST(CoreMatrix, QueueBounds_FixedLimitsAreExact) {
  EXPECT_EQ(LoopbackProvider::kMaximumRoutes, 4U);
  EXPECT_EQ(LoopbackProvider::kMaximumQueueItems, 8U);
  EXPECT_EQ(ProviderComposition::kMaximumProviders, 8U);
  EXPECT_EQ(LifecycleController::kMaximumRoutes, 32U);
  EXPECT_EQ(LifecycleController::kMaximumEndpoints, 32U);
  EXPECT_EQ(kMaximumPayloadBytes, 65'536U);
  EXPECT_TRUE(ProviderDescriptor::create({"provider.bounds", "1.0.0", "source.bounds", 0x0FU, 1U,
                                          2U, 65'536U, 32U, 32U})
                  .has_value());
  EXPECT_FALSE(ProviderDescriptor::create({"provider.bounds", "1.0.0", "source.bounds", 0x0FU, 1U,
                                           2U, 65'537U, 32U, 32U})
                   .has_value());
  EXPECT_FALSE(ProviderDescriptor::create({"provider.bounds", "1.0.0", "source.bounds", 0x0FU, 1U,
                                           2U, 65'536U, 33U, 32U})
                   .has_value());
  EXPECT_FALSE(ProviderDescriptor::create({"provider.bounds", "1.0.0", "source.bounds", 0x0FU, 1U,
                                           2U, 65'536U, 32U, 33U})
                   .has_value());
  EXPECT_TRUE(ProviderRegistryConfiguration::create(8U).has_value());
  EXPECT_FALSE(ProviderRegistryConfiguration::create(9U).has_value());
  EXPECT_FALSE(ProviderRegistryConfiguration::create(0U).has_value());
}

/** CHK-12: reject-new saturation preserves every queued item and FIFO index. */
TEST(CoreMatrix, QueueBounds_SaturationPreservesFifoAndItems) {
  CoreStackFixture fixture(InteractionKind::message_event, "bounds.saturation", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto first = fixture.item(0U);
  const auto second = fixture.item(1U);
  const auto third = fixture.item(2U);
  ASSERT_TRUE(first.has_value() && second.has_value() && third.has_value());
  EXPECT_EQ(fixture.submit(*first.value()).outcome(), ProviderOutcome::accepted);
  EXPECT_EQ(fixture.submit(*second.value()).outcome(), ProviderOutcome::accepted);
  EXPECT_EQ(fixture.submit(*third.value()).outcome(), ProviderOutcome::queue_saturated);
  const auto saturated = fixture.route_state();
  ASSERT_TRUE(saturated.has_value());
  EXPECT_EQ(saturated.value()->queued_items(), 2U);
  const auto received_first = fixture.receive();
  const auto received_second = fixture.receive();
  ASSERT_TRUE(received_first.has_value() && received_second.has_value());
  EXPECT_EQ(*received_first.value(), *first.value());
  EXPECT_EQ(*received_second.value(), *second.value());
  EXPECT_EQ(fixture.receive().outcome(), ProviderOutcome::queue_empty);
}

/** CHK-13: exact provider outcome, code, and message mapping. */
TEST(CoreMatrix, Diagnostics_ExactProviderOutcomeMapping) {
  struct Expected final {
    ProviderOutcome outcome;
    std::string_view text;
    std::string_view code;
    std::string_view message;
  };
  const std::array<Expected, 29U> expected{{
      {ProviderOutcome::registered, "registered", "XCOM-PROV-S001",
       "explicit source-linked provider registered"},
      {ProviderOutcome::prepared, "prepared", "XCOM-PROV-S002",
       "exact provider route prepared without traffic"},
      {ProviderOutcome::activated, "activated", "XCOM-PROV-S003", "exact provider route activated"},
      {ProviderOutcome::accepted, "accepted", "XCOM-PROV-S004",
       "item copied into bounded provider queue"},
      {ProviderOutcome::received, "received", "XCOM-PROV-S005",
       "oldest queued item returned by value"},
      {ProviderOutcome::draining, "draining", "XCOM-PROV-S006",
       "new submissions stopped; queued items retained"},
      {ProviderOutcome::closed, "closed", "XCOM-PROV-S007",
       "empty provider route resource released"},
      {ProviderOutcome::reconciled, "reconciled", "XCOM-PROV-S008",
       "provider and lifecycle state match exactly"},
      {ProviderOutcome::queue_empty, "queue-empty", "XCOM-PROV-I009",
       "route queue contains no accepted item"},
      {ProviderOutcome::queue_saturated, "queue-saturated", "XCOM-PROV-E010",
       "route queue is full; new item rejected"},
      {ProviderOutcome::observation_backpressure, "observation-backpressure", "XCOM-PROV-E029",
       "lossless observation capacity unavailable; provider not invoked"},
      {ProviderOutcome::invalid_descriptor, "invalid-descriptor", "XCOM-PROV-E011",
       "provider descriptor is invalid"},
      {ProviderOutcome::duplicate_provider, "duplicate-provider", "XCOM-PROV-E012",
       "provider identity is already registered"},
      {ProviderOutcome::provider_capacity_exhausted, "provider-capacity-exhausted",
       "XCOM-PROV-E013", "provider registry is full"},
      {ProviderOutcome::unsupported_contract_version, "unsupported-contract-version",
       "XCOM-PROV-E014", "provider contract version unsupported"},
      {ProviderOutcome::unsupported_interaction, "unsupported-interaction", "XCOM-PROV-E015",
       "interaction family unsupported"},
      {ProviderOutcome::unsupported_delivery, "unsupported-delivery", "XCOM-PROV-E016",
       "delivery capability unsupported"},
      {ProviderOutcome::unsupported_ordering, "unsupported-ordering", "XCOM-PROV-E017",
       "ordering capability unsupported"},
      {ProviderOutcome::unsupported_policy, "unsupported-policy", "XCOM-PROV-E030",
       "declared route policy is not supported by the selected provider"},
      {ProviderOutcome::payload_limit_exceeded, "payload-limit-exceeded", "XCOM-PROV-E018",
       "payload limit exceeded"},
      {ProviderOutcome::queue_limit_exceeded, "queue-limit-exceeded", "XCOM-PROV-E019",
       "queue limit invalid or exceeded"},
      {ProviderOutcome::route_capacity_exhausted, "route-capacity-exhausted", "XCOM-PROV-E020",
       "provider route storage is full"},
      {ProviderOutcome::invalid_provider_route_handle, "invalid-provider-route-handle",
       "XCOM-PROV-E021", "provider route handle is inauthentic"},
      {ProviderOutcome::lifecycle_mismatch, "lifecycle-mismatch", "XCOM-PROV-E022",
       "exact lifecycle binding or state differs"},
      {ProviderOutcome::inactive_route, "inactive-route", "XCOM-PROV-E023",
       "provider route is not active"},
      {ProviderOutcome::route_mismatch, "route-mismatch", "XCOM-PROV-E024",
       "route identity, digest, or generation differs"},
      {ProviderOutcome::provider_mismatch, "provider-mismatch", "XCOM-PROV-E025",
       "provider identity or instance differs"},
      {ProviderOutcome::item_mismatch, "item-mismatch", "XCOM-PROV-E026",
       "item metadata differs from prepared route"},
      {ProviderOutcome::queued_items_remain, "queued-items-remain", "XCOM-PROV-E027",
       "route retains accepted queued items"},
  }};
  for (const auto& entry : expected) {
    EXPECT_EQ(to_string(entry.outcome), entry.text);
    EXPECT_EQ(provider_diagnostic_code(entry.outcome), entry.code);
    EXPECT_EQ(provider_diagnostic_message(entry.outcome), entry.message);
  }
  EXPECT_EQ(provider_diagnostic_code(ProviderOutcome::interrupted_resource), "XCOM-PROV-E028");
  EXPECT_EQ(provider_diagnostic_message(ProviderOutcome::interrupted_resource),
            "provider and lifecycle state cannot reconcile");

  // Core diagnostic codes and phases remain byte-stable.
  EXPECT_EQ(to_string(DiagnosticCode::required_field), "XCOM-TYPE-E001");
  EXPECT_EQ(to_string(DiagnosticCode::bound_exceeded), "XCOM-TYPE-E002");
  EXPECT_EQ(to_string(DiagnosticCode::invalid_policy), "XCOM-TYPE-E006");
  EXPECT_EQ(to_string(ValidationPhase::contract), "contract");
  EXPECT_EQ(to_string(ValidationPhase::policy), "policy");
  EXPECT_EQ(to_string(DiagnosticSeverity::error), "error");
}

/** CHK-13: equivalent diagnostics serialize byte-identically in any construction order. */
TEST(CoreMatrix, Diagnostics_ByteStableOrderingAcrossConstructionOrder) {
  const std::array<DiagnosticInput, 3U> forward{{
      {DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::contract,
       "contract_id", "required identity is empty", "provide a non-empty bounded identity"},
      {DiagnosticCode::bound_exceeded, DiagnosticSeverity::error, ValidationPhase::policy,
       "queue_depth", "queue depth is outside the declared range",
       "use a finite queue depth between 1 and 65536"},
      {DiagnosticCode::invalid_version, DiagnosticSeverity::error, ValidationPhase::item,
       "schema_version", "version is not bounded canonical major.minor.patch",
       "provide three decimal components without leading zeroes"},
  }};
  const std::array<DiagnosticInput, 3U> reversed{{forward[2], forward[1], forward[0]}};
  const auto first = DiagnosticSet::create_from_inputs(forward);
  const auto second = DiagnosticSet::create_from_inputs(reversed);
  ASSERT_TRUE(first.has_value());
  ASSERT_TRUE(second.has_value());
  EXPECT_EQ(first.value().serialize(), second.value().serialize());
  EXPECT_TRUE(first.value() == second.value());
  EXPECT_EQ(first.value().values().front().code(), DiagnosticCode::required_field);
}

/** CHK-13: diagnostic bytes are independent of the process locale. */
TEST(CoreMatrix, Diagnostics_LocaleIndependent) {
  const auto set = CommunicationContract::create({"", "1.0.0", "interface.locale",
                                                   "schema.locale", "1.0.0",
                                                   InteractionKind::message_event,
                                                   EndpointDirection::produce,
                                                   EndpointDirection::consume});
  ASSERT_FALSE(set.has_value());
  ASSERT_FALSE(set.diagnostics() == nullptr);
  const std::string baseline = set.diagnostics()->serialize();
  const char* const original = std::setlocale(LC_ALL, nullptr);
  const std::string saved = original != nullptr ? original : "C";
  for (const char* const candidate : {"C", "POSIX", "C.UTF-8", "en_US.UTF-8"}) {
    if (std::setlocale(LC_ALL, candidate) != nullptr) {
      EXPECT_EQ(set.diagnostics()->serialize(), baseline);
    }
  }
  static_cast<void>(std::setlocale(LC_ALL, saved.c_str()));
}

/** CHK-15 (supporting): concurrent const reads of one immutable value are safe. */
TEST(CoreMatrix, Ownership_ConcurrentConstReadsAreStable) {
  CoreStackFixture fixture(InteractionKind::service_request, "ownership.const", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  const auto item = fixture.item(3U);
  ASSERT_TRUE(item.has_value());
  const CommunicationItem shared = *item.value();
  const std::string expected = "correlation.3";
  std::array<bool, 2U> observed{false, false};
  std::array<std::thread, 2U> readers{
      std::thread([&shared, &expected, &observed]() {
        observed[0] = shared.correlation_id().value() == expected &&
                      shared.interaction_kind() == InteractionKind::service_request;
      }),
      std::thread([&shared, &expected, &observed]() {
        observed[1] = shared.correlation_id().value() == expected &&
                      shared.payload().size() == 1U;
      }),
  };
  for (auto& reader : readers) {
    reader.join();
  }
  EXPECT_TRUE(observed[0]);
  EXPECT_TRUE(observed[1]);
}
