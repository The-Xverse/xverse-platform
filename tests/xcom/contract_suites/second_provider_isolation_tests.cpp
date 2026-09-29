/**
 * @file second_provider_isolation_tests.cpp
 * @brief T034 `t034-isolation` driver: proves that a second-provider failure or rejected adapter
 *        registration yields a stable non-success outcome with zero emission and leaves an unrelated
 *        active route active, bounded, and observable with its exact retained items.
 * @ownership Each case owns its providers, compositions, and fixtures; returned items are
 *            independent owned copies.
 * @lifetime Providers, compositions, and fixtures are per-case values.
 * @thread_safety Single-threaded; the accepted composition and providers serialize their own state.
 * @bounds At most two providers and two routes per case; every queue is finite.
 * @failure A failing or missing assertion fails the owning case closed with a bounded message; a
 *          failure is never reported as success.
 * @par Traceability
 * Supports T034-SR-008 and T034-SR-009 over the accepted `XCOM-SW-CORE-005` explicit registration
 * and exact-handle ownership and the accepted `ProviderComposition` boundary.
 */

#include <gtest/gtest.h>

#include "core_matrix/test_support.hpp"
#include "synthetic_provider.hpp"

#include <cstddef>
#include <string_view>

namespace {

using xverse::xcom::DeliveryCapability;
using xverse::xcom::InteractionKind;
using xverse::xcom::LoopbackProvider;
using xverse::xcom::OrderingCapability;
using xverse::xcom::ProviderDescriptor;
using xverse::xcom::ProviderOutcome;
using xverse::xcom::ProviderRouteState;
using xverse::xcom::SyntheticProvider;
using xverse::xcom::delivery_capability_bit;
using xverse::xcom::ordering_capability_bit;
using xverse::xcom::test::CoreStackFixture;
using xverse::xcom::test::kAllInteractions;
using xverse::xcom::test::make_descriptor;

/// @brief Build one second-provider descriptor with a caller-selected version and finite storage.
/// @param version Canonical provider-contract version text.
/// @param maximum_routes Finite route bound.
/// @param maximum_queue_items Finite per-route queue bound.
/// @return Owned descriptor over the admitted vocabulary.
[[nodiscard]] ProviderDescriptor synthetic_descriptor_with_version(
    const std::string_view version, const std::size_t maximum_routes = 1U,
    const std::size_t maximum_queue_items = 2U) {
  return *ProviderDescriptor::create(
              {"provider.t034.synthetic.isolation", version, "source.xverse.xcom.t034",
               kAllInteractions, delivery_capability_bit(DeliveryCapability::best_effort),
               ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, maximum_routes,
               maximum_queue_items})
              .value();
}

}  // namespace

TEST(T034FailureIsolation, ProviderFailureYieldsStableOutcomeNoEmission) {
  // A configured forced failure is reported exactly from prepare and mutates no route state.
  const ProviderDescriptor descriptor = synthetic_descriptor_with_version("1.0.0");
  SyntheticProvider prepare_provider(descriptor);
  CoreStackFixture prepare_fixture(
      InteractionKind::message_event, "t034.isolation.fail.prepare",
      /*queue_capacity=*/2U, /*maximum_payload_bytes=*/4U, /*activate_now=*/false,
      /*external_provider=*/&prepare_provider, /*policy=*/nullptr,
      /*provider_id=*/"provider.t034.synthetic.isolation", /*route_provider_id=*/"",
      /*interaction_mask=*/kAllInteractions, /*delivery=*/DeliveryCapability::best_effort,
      /*ordering=*/OrderingCapability::per_route_fifo, /*maximum_routes=*/1U,
      /*maximum_queue_items=*/2U, /*registry_capacity=*/1U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(prepare_fixture.ready());
  prepare_provider.configure_forced_failure(ProviderOutcome::unsupported_policy);
  const auto failed_prepare = prepare_fixture.prepare();
  EXPECT_EQ(failed_prepare.outcome(), ProviderOutcome::unsupported_policy);
  EXPECT_FALSE(prepare_fixture.prepared());
  EXPECT_FALSE(prepare_fixture.activated());
  EXPECT_EQ(prepare_provider.accepted_item_count(), 0U);

  // A forced failure on submit returns its exact outcome and emits no item.
  SyntheticProvider submit_provider(descriptor);
  CoreStackFixture submit_fixture(
      InteractionKind::message_event, "t034.isolation.fail.submit",
      /*queue_capacity=*/2U, /*maximum_payload_bytes=*/4U, /*activate_now=*/false,
      /*external_provider=*/&submit_provider, /*policy=*/nullptr,
      /*provider_id=*/"provider.t034.synthetic.isolation", /*route_provider_id=*/"",
      /*interaction_mask=*/kAllInteractions, /*delivery=*/DeliveryCapability::best_effort,
      /*ordering=*/OrderingCapability::per_route_fifo, /*maximum_routes=*/1U,
      /*maximum_queue_items=*/2U, /*registry_capacity=*/1U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(submit_fixture.ready());
  const auto activated = submit_fixture.prepare_and_activate();
  ASSERT_TRUE(activated.has_value());
  ASSERT_TRUE(submit_fixture.activated());
  submit_provider.configure_forced_failure(ProviderOutcome::interrupted_resource);
  const auto item = submit_fixture.item(1U);
  ASSERT_TRUE(item.has_value());
  EXPECT_EQ(submit_fixture.submit(*item.value()).outcome(),
            ProviderOutcome::interrupted_resource);
  EXPECT_EQ(submit_fixture.receive().outcome(), ProviderOutcome::queue_empty);
  EXPECT_EQ(submit_provider.accepted_item_count(), 0U);
  EXPECT_GE(submit_provider.submit_dispatch_count(), 1U);
}

TEST(T034FailureIsolation, UnrelatedRouteRemainsActiveAndBounded) {
  // An unrelated loopback route is prepared and activated before the second provider fails.
  CoreStackFixture unrelated(InteractionKind::message_event, "t034.isolation.unrelated",
                             /*queue_capacity=*/2U, /*maximum_payload_bytes=*/4U,
                             /*activate_now=*/true, /*external_provider=*/nullptr,
                             /*policy=*/nullptr, /*provider_id=*/"provider.t034.unrelated",
                             /*route_provider_id=*/"", /*interaction_mask=*/kAllInteractions,
                             /*delivery=*/DeliveryCapability::best_effort,
                             /*ordering=*/OrderingCapability::per_route_fifo,
                             /*maximum_routes=*/LoopbackProvider::kMaximumRoutes,
                             /*maximum_queue_items=*/LoopbackProvider::kMaximumQueueItems,
                             /*registry_capacity=*/1U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(unrelated.ready());
  ASSERT_TRUE(unrelated.activated());
  const auto first = unrelated.item(1U);
  ASSERT_TRUE(first.has_value());
  ASSERT_EQ(unrelated.submit(*first.value()).outcome(), ProviderOutcome::accepted);
  const auto before = unrelated.route_state();
  ASSERT_TRUE(before.has_value());
  ASSERT_EQ(before.value()->state(), ProviderRouteState::active);
  ASSERT_EQ(before.value()->queued_items(), 1U);
  ASSERT_EQ(before.value()->queue_capacity(), 2U);

  // A second provider on an independently composed route fails to prepare.
  const ProviderDescriptor descriptor = synthetic_descriptor_with_version("1.0.0");
  SyntheticProvider failing(descriptor);
  CoreStackFixture failing_fixture(
      InteractionKind::message_event, "t034.isolation.failing", /*queue_capacity=*/2U,
      /*maximum_payload_bytes=*/4U, /*activate_now=*/false, /*external_provider=*/&failing,
      /*policy=*/nullptr, /*provider_id=*/"provider.t034.synthetic.isolation",
      /*route_provider_id=*/"", /*interaction_mask=*/kAllInteractions,
      /*delivery=*/DeliveryCapability::best_effort,
      /*ordering=*/OrderingCapability::per_route_fifo, /*maximum_routes=*/1U,
      /*maximum_queue_items=*/2U, /*registry_capacity=*/1U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(failing_fixture.ready());
  failing.configure_forced_failure(ProviderOutcome::unsupported_policy);
  EXPECT_EQ(failing_fixture.prepare().outcome(), ProviderOutcome::unsupported_policy);

  // The unrelated route stays active, bounded, accepts a further item, and returns its exact item.
  const auto after = unrelated.route_state();
  ASSERT_TRUE(after.has_value());
  EXPECT_EQ(after.value()->state(), ProviderRouteState::active);
  EXPECT_EQ(after.value()->queued_items(), 1U);
  EXPECT_EQ(after.value()->queue_capacity(), 2U);
  const auto second = unrelated.item(2U);
  ASSERT_TRUE(second.has_value());
  EXPECT_EQ(unrelated.submit(*second.value()).outcome(), ProviderOutcome::accepted);
  const auto received = unrelated.receive();
  ASSERT_TRUE(received.has_value());
  EXPECT_EQ(received.outcome(), ProviderOutcome::received);
  EXPECT_TRUE(*received.value() == *first.value());
}

TEST(T034FailureIsolation, UnrelatedRouteStateStaysObservable) {
  CoreStackFixture unrelated(InteractionKind::message_event, "t034.isolation.observable",
                             /*queue_capacity=*/2U, /*maximum_payload_bytes=*/4U,
                             /*activate_now=*/true, /*external_provider=*/nullptr,
                             /*policy=*/nullptr, /*provider_id=*/"provider.t034.observable",
                             /*route_provider_id=*/"", /*interaction_mask=*/kAllInteractions,
                             /*delivery=*/DeliveryCapability::best_effort,
                             /*ordering=*/OrderingCapability::per_route_fifo,
                             /*maximum_routes=*/LoopbackProvider::kMaximumRoutes,
                             /*maximum_queue_items=*/LoopbackProvider::kMaximumQueueItems,
                             /*registry_capacity=*/1U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(unrelated.ready());
  ASSERT_TRUE(unrelated.activated());
  const auto item = unrelated.item(5U);
  ASSERT_TRUE(item.has_value());
  ASSERT_EQ(unrelated.submit(*item.value()).outcome(), ProviderOutcome::accepted);

  const ProviderDescriptor descriptor = synthetic_descriptor_with_version("1.0.0");
  SyntheticProvider failing(descriptor);
  CoreStackFixture failing_fixture(
      InteractionKind::message_event, "t034.isolation.observable.failing",
      /*queue_capacity=*/2U, /*maximum_payload_bytes=*/4U, /*activate_now=*/false,
      /*external_provider=*/&failing, /*policy=*/nullptr,
      /*provider_id=*/"provider.t034.synthetic.isolation", /*route_provider_id=*/"",
      /*interaction_mask=*/kAllInteractions, /*delivery=*/DeliveryCapability::best_effort,
      /*ordering=*/OrderingCapability::per_route_fifo, /*maximum_routes=*/1U,
      /*maximum_queue_items=*/2U, /*registry_capacity=*/1U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(failing_fixture.ready());
  failing.configure_forced_failure(ProviderOutcome::unsupported_policy);
  EXPECT_EQ(failing_fixture.prepare().outcome(), ProviderOutcome::unsupported_policy);

  const auto snapshot = unrelated.route_state();
  const auto reconciled = unrelated.reconcile();
  ASSERT_TRUE(snapshot.has_value());
  ASSERT_TRUE(reconciled.has_value());
  EXPECT_EQ(snapshot.outcome(), ProviderOutcome::reconciled);
  EXPECT_EQ(reconciled.outcome(), ProviderOutcome::reconciled);
  EXPECT_EQ(snapshot.value()->state(), ProviderRouteState::active);
  EXPECT_EQ(snapshot.value()->queued_items(), reconciled.value()->queued_items());
  EXPECT_EQ(snapshot.value()->queue_capacity(), reconciled.value()->queue_capacity());
  EXPECT_EQ(snapshot.value()->queue_capacity(), 2U);
  EXPECT_EQ(snapshot.value()->queued_items(), 1U);
}

TEST(T034FailureIsolation, RejectedAdapterLeavesUnrelatedRouteIntact) {
  // One composition owns an active loopback route and has capacity for one more provider.
  CoreStackFixture shared(InteractionKind::message_event, "t034.isolation.shared",
                          /*queue_capacity=*/2U, /*maximum_payload_bytes=*/4U,
                          /*activate_now=*/true, /*external_provider=*/nullptr,
                          /*policy=*/nullptr, /*provider_id=*/"provider.t034.shared",
                          /*route_provider_id=*/"", /*interaction_mask=*/kAllInteractions,
                          /*delivery=*/DeliveryCapability::best_effort,
                          /*ordering=*/OrderingCapability::per_route_fifo,
                          /*maximum_routes=*/LoopbackProvider::kMaximumRoutes,
                          /*maximum_queue_items=*/LoopbackProvider::kMaximumQueueItems,
                          /*registry_capacity=*/2U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(shared.ready());
  ASSERT_TRUE(shared.activated());
  const auto queued = shared.item(3U);
  ASSERT_TRUE(queued.has_value());
  ASSERT_EQ(shared.submit(*queued.value()).outcome(), ProviderOutcome::accepted);

  // A misreporting adapter registered into the same composition is rejected fail-closed.
  const ProviderDescriptor misreported = synthetic_descriptor_with_version("2.0.0");
  SyntheticProvider rejected(misreported);
  EXPECT_EQ(shared.composition().register_provider(rejected).outcome(),
            ProviderOutcome::unsupported_contract_version);

  // The unrelated route is still active, bounded, and returns its exact retained item.
  const auto snapshot = shared.route_state();
  ASSERT_TRUE(snapshot.has_value());
  EXPECT_EQ(snapshot.value()->state(), ProviderRouteState::active);
  EXPECT_EQ(snapshot.value()->queued_items(), 1U);
  EXPECT_EQ(snapshot.value()->queue_capacity(), 2U);
  const auto received = shared.receive();
  ASSERT_TRUE(received.has_value());
  EXPECT_TRUE(*received.value() == *queued.value());
}
