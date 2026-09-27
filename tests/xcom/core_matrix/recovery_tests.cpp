/**
 * @file recovery_tests.cpp
 * @brief T016 recovery matrix: saturation recovery, rejected-operation reusability, generation
 * recreation, reconciliation mismatch, and empty-queue reporting.
 * @ownership Each case owns its fixture and provider; closed or recreated routes use a new exact
 * generation inside the same case.
 * @lifetime Every fixture and handle is per-case; the earlier generation's handles are asserted stale.
 * @thread_safety Single-threaded.
 * @failure A non-FIFO, lost, or duplicated item, a stale handle accepted as valid, or a mismatch
 * reported as success fails the case.
 */

#include "test_support.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <string>

namespace {

using namespace xverse::xcom;
using xverse::xcom::test::CoreStackFixture;

}  // namespace

/** CHK-14: saturation then drain recovers FIFO and accepts new submissions again. */
TEST(CoreMatrixRecovery, Saturation_ThenDrainRecoversFifo) {
  CoreStackFixture fixture(InteractionKind::message_event, "recover.saturation", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto first = fixture.item(0U);
  const auto second = fixture.item(1U);
  const auto third = fixture.item(2U);
  ASSERT_TRUE(first.has_value() && second.has_value() && third.has_value());
  ASSERT_EQ(fixture.submit(*first.value()).outcome(), ProviderOutcome::accepted);
  ASSERT_EQ(fixture.submit(*second.value()).outcome(), ProviderOutcome::accepted);
  ASSERT_EQ(fixture.submit(*third.value()).outcome(), ProviderOutcome::queue_saturated);
  const auto received_first = fixture.receive();
  const auto received_second = fixture.receive();
  ASSERT_TRUE(received_first.has_value() && received_second.has_value());
  EXPECT_EQ(*received_first.value(), *first.value());
  EXPECT_EQ(*received_second.value(), *second.value());
  ASSERT_EQ(fixture.receive().outcome(), ProviderOutcome::queue_empty);
  // After the queue drains, the route accepts new submissions again without loss or duplication.
  EXPECT_EQ(fixture.submit(*third.value()).outcome(), ProviderOutcome::accepted);
  const auto recovered = fixture.receive();
  ASSERT_TRUE(recovered.has_value());
  EXPECT_EQ(*recovered.value(), *third.value());
  EXPECT_EQ(fixture.receive().outcome(), ProviderOutcome::queue_empty);
}

/** CHK-14: a rejected operation leaves the route unchanged and immediately reusable. */
TEST(CoreMatrixRecovery, RejectedOperationLeavesStateReusable) {
  CoreStackFixture fixture(InteractionKind::message_event, "recover.rejected", 2U, 4U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const std::array<std::byte, 8U> oversized{};
  const auto rejected = fixture.item_with_payload(1U, oversized);
  ASSERT_TRUE(rejected.has_value());
  EXPECT_EQ(fixture.submit(*rejected.value()).outcome(), ProviderOutcome::payload_limit_exceeded);
  const auto state = fixture.route_state();
  ASSERT_TRUE(state.has_value());
  EXPECT_EQ(state.value()->queued_items(), 0U);
  // The exact same route accepts a valid item unchanged.
  const auto valid = fixture.item(2U);
  ASSERT_TRUE(valid.has_value());
  EXPECT_EQ(fixture.submit(*valid.value()).outcome(), ProviderOutcome::accepted);
  const auto received = fixture.receive();
  ASSERT_TRUE(received.has_value());
  EXPECT_EQ(*received.value(), *valid.value());
}

/** CHK-14: a closed route recreated as a new generation rejects the earlier generation's handles. */
TEST(CoreMatrixRecovery, ClosedRouteRecreatedAsNewGenerationRejectsStaleHandles) {
  CoreStackFixture fixture(InteractionKind::message_event, "recover.generation", 1U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  ASSERT_EQ(fixture.drain().outcome(), ProviderOutcome::draining);
  ASSERT_EQ(fixture.close().outcome(), ProviderOutcome::closed);
  const ProviderRouteHandle stale = fixture.provider_handle();
  const std::uint64_t stale_generation = fixture.route_handle().generation();

  const auto recreated_route = fixture.lifecycle().declare_route(fixture.route_spec());
  ASSERT_TRUE(recreated_route.has_value());
  EXPECT_NE(recreated_route.value()->generation(), stale_generation);
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
  EXPECT_NE(prepared.value()->provider_route_generation(), stale.provider_route_generation());
  EXPECT_NE(prepared.value()->lifecycle_route_generation(), stale.lifecycle_route_generation());
  const auto rejected = fixture.composition().route_state(stale);
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::invalid_provider_route_handle);
  const auto item = fixture.item(1U);
  ASSERT_TRUE(item.has_value());
  EXPECT_EQ(fixture.composition()
                .submit(*prepared.value(), *item.value(), fixture.lifecycle())
                .outcome(),
            ProviderOutcome::accepted);
  const auto received = fixture.composition().receive(*prepared.value(), fixture.lifecycle());
  ASSERT_TRUE(received.has_value());
  EXPECT_EQ(*received.value(), *item.value());
}

/** CHK-14: reconciliation after divergence reports interrupted_resource, never success. */
TEST(CoreMatrixRecovery, Reconcile_MismatchReportsInterruptedResource) {
  CoreStackFixture fixture(InteractionKind::service_response, "recover.reconcile", 1U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto healthy = fixture.reconcile();
  ASSERT_TRUE(healthy.has_value());
  EXPECT_EQ(healthy.outcome(), ProviderOutcome::reconciled);
  ASSERT_TRUE(fixture.lifecycle().fail_route(fixture.route_handle()).has_value());
  const auto rejected = fixture.reconcile();
  EXPECT_EQ(rejected.outcome(), ProviderOutcome::interrupted_resource);
  EXPECT_EQ(rejected.diagnostic_code(), "XCOM-PROV-E028");
  EXPECT_FALSE(rejected.has_value());
}

/** CHK-14: receiving on an empty active route reports queue_empty. */
TEST(CoreMatrixRecovery, ReceiveAfterEmptyReportsQueueEmpty) {
  CoreStackFixture fixture(InteractionKind::signal_state_update, "recover.empty", 2U, 16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  const auto empty = fixture.receive();
  EXPECT_EQ(empty.outcome(), ProviderOutcome::queue_empty);
  EXPECT_EQ(empty.diagnostic_code(), "XCOM-PROV-I009");
  EXPECT_FALSE(empty.has_value());
}
