/**
 * @file second_provider_version_tests.cpp
 * @brief T034 `t034-version` driver: proves fail-closed rejection of a misreported provider contract
 *        version or capability at explicit registration and of an unsupported requested version or
 *        capability before activation, with zero item emission on every rejection path.
 * @ownership Each case owns its provider, composition, and fixture; the accepted composition owns
 *            its own registry and route state.
 * @lifetime Provider, composition, and fixture are per-case values.
 * @thread_safety Single-threaded; the accepted composition and provider serialize their own state.
 * @bounds One provider, one route, and at most one rejected registration or preparation per case.
 * @failure Every assertion fails the owning case closed with a bounded message; no rejection is
 *          reported as success.
 * @par Traceability
 * Supports T034-SR-005 through T034-SR-007 over the accepted `XCOM-SW-CORE-003` registration and
 * preparation gates and the accepted `ProviderComposition` boundary.
 */

#include <gtest/gtest.h>

#include "core_matrix/test_support.hpp"
#include "synthetic_provider.hpp"

#include <cstddef>
#include <string_view>

namespace {

using xverse::xcom::DeliveryCapability;
using xverse::xcom::InteractionKind;
using xverse::xcom::OrderingCapability;
using xverse::xcom::ProviderComposition;
using xverse::xcom::ProviderDescriptor;
using xverse::xcom::ProviderOutcome;
using xverse::xcom::ProviderRegistryConfiguration;
using xverse::xcom::ProviderResult;
using xverse::xcom::ProviderRouteHandle;
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
    const std::size_t maximum_queue_items = 1U) {
  return *ProviderDescriptor::create(
              {"provider.t034.synthetic.version", version, "source.xverse.xcom.t034",
               kAllInteractions, delivery_capability_bit(DeliveryCapability::best_effort),
               ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, maximum_routes,
               maximum_queue_items})
              .value();
}

/// @brief Build one non-copyable composition with caller-selected finite registry capacity.
/// @param capacity Finite registry slot count.
/// @return The constructed composition.
[[nodiscard]] ProviderComposition make_composition(const std::size_t capacity) {
  const ProviderRegistryConfiguration configuration =
      *ProviderRegistryConfiguration::create(capacity).value();
  return ProviderComposition(configuration);
}

}  // namespace

TEST(T034VersionRejection, MisreportedContractVersionRejectedAtRegistration) {
  const ProviderDescriptor descriptor = synthetic_descriptor_with_version("2.0.0");
  SyntheticProvider provider(descriptor);
  EXPECT_TRUE(provider.descriptor_compatible());

  ProviderComposition composition = make_composition(1U);
  const ProviderResult<xverse::xcom::ProviderRegistration> registration =
      composition.register_provider(provider);
  EXPECT_EQ(registration.outcome(), ProviderOutcome::unsupported_contract_version);
  EXPECT_FALSE(registration.has_value());
  EXPECT_EQ(provider.prepare_dispatch_count(), 0U);
}

TEST(T034VersionRejection, UnsupportedRequestedVersionRejectedBeforeActivation) {
  const ProviderDescriptor descriptor =
      make_descriptor("provider.t034.synthetic.request", kAllInteractions,
                      delivery_capability_bit(DeliveryCapability::best_effort),
                      ordering_capability_bit(OrderingCapability::per_route_fifo), 1U, 1U, 1U);
  SyntheticProvider provider(descriptor);
  CoreStackFixture fixture(InteractionKind::message_event, "t034.version.request",
                           /*queue_capacity=*/1U, /*maximum_payload_bytes=*/1U,
                           /*activate_now=*/false, /*external_provider=*/&provider,
                           /*policy=*/nullptr, /*provider_id=*/"provider.t034.synthetic.request",
                           /*route_provider_id=*/"", /*interaction_mask=*/kAllInteractions,
                           /*delivery=*/DeliveryCapability::best_effort,
                           /*ordering=*/OrderingCapability::per_route_fifo,
                           /*maximum_routes=*/1U, /*maximum_queue_items=*/1U,
                           /*registry_capacity=*/1U, /*requirements_version=*/"9.9.9");
  ASSERT_TRUE(fixture.ready());

  const ProviderResult<ProviderRouteHandle> prepared = fixture.prepare();
  EXPECT_EQ(prepared.outcome(), ProviderOutcome::unsupported_contract_version);
  EXPECT_FALSE(fixture.prepared());
  EXPECT_FALSE(fixture.activated());
  EXPECT_EQ(provider.accepted_item_count(), 0U);
}

TEST(T034VersionRejection, MisreportedCapabilityRejectedAtRegistration) {
  const ProviderDescriptor route_misreport = synthetic_descriptor_with_version(
      "1.0.0", /*maximum_routes=*/SyntheticProvider::kMaximumRoutes + 1U,
      /*maximum_queue_items=*/1U);
  SyntheticProvider route_provider(route_misreport);
  EXPECT_FALSE(route_provider.descriptor_compatible());
  ProviderComposition route_composition = make_composition(1U);
  EXPECT_EQ(route_composition.register_provider(route_provider).outcome(),
            ProviderOutcome::invalid_descriptor);

  const ProviderDescriptor queue_misreport = synthetic_descriptor_with_version(
      "1.0.0", /*maximum_routes=*/1U,
      /*maximum_queue_items=*/SyntheticProvider::kMaximumQueueItems + 1U);
  SyntheticProvider queue_provider(queue_misreport);
  EXPECT_FALSE(queue_provider.descriptor_compatible());
  ProviderComposition queue_composition = make_composition(1U);
  EXPECT_EQ(queue_composition.register_provider(queue_provider).outcome(),
            ProviderOutcome::invalid_descriptor);
}

TEST(T034VersionRejection, UnsupportedRequestedCapabilityRejectedBeforeActivation) {
  const ProviderDescriptor descriptor =
      make_descriptor("provider.t034.synthetic.capability", kAllInteractions,
                      delivery_capability_bit(DeliveryCapability::best_effort),
                      ordering_capability_bit(OrderingCapability::per_route_fifo), 1U, 1U, 1U);
  SyntheticProvider provider(descriptor);
  CoreStackFixture fixture(InteractionKind::message_event, "t034.version.capability",
                           /*queue_capacity=*/1U, /*maximum_payload_bytes=*/1U,
                           /*activate_now=*/false, /*external_provider=*/&provider,
                           /*policy=*/nullptr,
                           /*provider_id=*/"provider.t034.synthetic.capability",
                           /*route_provider_id=*/"", /*interaction_mask=*/kAllInteractions,
                           /*delivery=*/DeliveryCapability::reliable,
                           /*ordering=*/OrderingCapability::per_route_fifo,
                           /*maximum_routes=*/1U, /*maximum_queue_items=*/1U,
                           /*registry_capacity=*/1U, /*requirements_version=*/"1.0.0");
  ASSERT_TRUE(fixture.ready());

  const ProviderResult<ProviderRouteHandle> prepared = fixture.prepare();
  EXPECT_EQ(prepared.outcome(), ProviderOutcome::unsupported_delivery);
  EXPECT_FALSE(fixture.prepared());
  EXPECT_FALSE(fixture.activated());
  EXPECT_EQ(provider.submit_dispatch_count(), 0U);
  EXPECT_EQ(provider.accepted_item_count(), 0U);
}

TEST(T034VersionRejection, RejectionEmitsNothing) {
  // Registration rejection mutates no operational state and dispatches no provider operation.
  const ProviderDescriptor misreported = synthetic_descriptor_with_version("2.0.0");
  SyntheticProvider rejected(misreported);
  ProviderComposition composition = make_composition(1U);
  EXPECT_EQ(composition.register_provider(rejected).outcome(),
            ProviderOutcome::unsupported_contract_version);
  EXPECT_EQ(rejected.prepare_dispatch_count(), 0U);
  EXPECT_EQ(rejected.submit_dispatch_count(), 0U);
  EXPECT_EQ(rejected.accepted_item_count(), 0U);

  // Preparation rejection issues no handle and emits no item on a registered provider.
  const ProviderDescriptor registered = synthetic_descriptor_with_version("1.0.0");
  SyntheticProvider provider(registered);
  CoreStackFixture fixture(InteractionKind::message_event, "t034.version.emits",
                           /*queue_capacity=*/1U, /*maximum_payload_bytes=*/1U,
                           /*activate_now=*/false, /*external_provider=*/&provider,
                           /*policy=*/nullptr, /*provider_id=*/"provider.t034.synthetic.version",
                           /*route_provider_id=*/"", /*interaction_mask=*/kAllInteractions,
                           /*delivery=*/DeliveryCapability::best_effort,
                           /*ordering=*/OrderingCapability::per_route_fifo,
                           /*maximum_routes=*/1U, /*maximum_queue_items=*/1U,
                           /*registry_capacity=*/1U, /*requirements_version=*/"9.9.9");
  ASSERT_TRUE(fixture.ready());
  const ProviderResult<ProviderRouteHandle> prepared = fixture.prepare();
  EXPECT_EQ(prepared.outcome(), ProviderOutcome::unsupported_contract_version);
  EXPECT_FALSE(fixture.prepared());
  EXPECT_EQ(provider.submit_dispatch_count(), 0U);
  EXPECT_EQ(provider.accepted_item_count(), 0U);
}
