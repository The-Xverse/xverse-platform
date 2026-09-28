/**
 * @file main.cpp
 * @brief T016 external consumer: a separate translation unit over the accepted public core include
 * surface that performs one minimal end-to-end round trip.
 * @ownership Owns its local values and declarations; no shared state exists.
 * @lifetime Process of the test executable.
 * @thread_safety Single-threaded.
 * @bounds One contract, one route, one item, and one bounded payload.
 * @failure Returns nonzero on any expectation failure, proving the public surface is usable from
 * outside the package without any package-internal test-support header.
 */

#include "xverse/xcom/activation_plan.hpp"
#include "xverse/xcom/core_types.hpp"
#include "xverse/xcom/endpoint_route_lifecycle.hpp"
#include "xverse/xcom/loopback_provider.hpp"
#include "xverse/xcom/provider.hpp"
#include "xverse/xcom/validation_session.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <optional>
#include <string>

namespace {

using namespace xverse::xcom;

constexpr std::string_view kDigest =
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

/** @return true when the external consumer completed its minimal round trip. */
[[nodiscard]] bool run_round_trip() {
  const auto contract = CommunicationContract::create(
      {"contract.consumer", "1.0.0", "interface.consumer", "schema.consumer", "1.0.0",
       InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume});
  if (!contract.has_value()) {
    return false;
  }
  const auto source = EndpointSpec::create(
      {"source.consumer", kDigest, "provider.consumer", EndpointDirection::produce},
      *contract.value());
  const auto destination = EndpointSpec::create(
      {"destination.consumer", kDigest, "provider.consumer", EndpointDirection::consume},
      *contract.value());
  if (!source.has_value() || !destination.has_value()) {
    return false;
  }
  const auto route = RouteSpec::create({"route.consumer", kDigest, "provider.consumer"},
                                       *source.value(), *destination.value());
  const auto configuration = LifecycleConfiguration::create({2U, 2U});
  if (!route.has_value() || !configuration.has_value()) {
    return false;
  }
  LifecycleController lifecycle(*configuration.value());
  const auto source_handle = lifecycle.declare_endpoint(*source.value());
  const auto destination_handle = lifecycle.declare_endpoint(*destination.value());
  const auto route_handle = lifecycle.declare_route(*route.value());
  if (!source_handle.has_value() || !destination_handle.has_value() ||
      !route_handle.has_value()) {
    return false;
  }
  if (!lifecycle.validate_endpoint(*source_handle.value()).has_value() ||
      !lifecycle.validate_endpoint(*destination_handle.value()).has_value() ||
      !lifecycle
           .validate_route(*route_handle.value(), *source_handle.value(),
                           *destination_handle.value())
           .has_value() ||
      !lifecycle.activate_endpoint(*source_handle.value()).has_value() ||
      !lifecycle.activate_endpoint(*destination_handle.value()).has_value()) {
    return false;
  }

  const auto provider_descriptor = *ProviderDescriptor::create(
                                        {"provider.consumer", "1.0.0", "source.consumer.fixture",
                                         static_cast<std::uint8_t>(0x0FU),
                                         delivery_capability_bit(DeliveryCapability::best_effort),
                                         ordering_capability_bit(OrderingCapability::per_route_fifo),
                                         65'536U, 4U, 8U})
                                        .value();
  LoopbackProvider provider(provider_descriptor);
  const auto registry = ProviderRegistryConfiguration::create(1U);
  if (!registry.has_value()) {
    return false;
  }
  ProviderComposition composition(*registry.value());
  if (composition.register_provider(provider).outcome() != ProviderOutcome::registered) {
    return false;
  }
  const ProviderRouteRequirements requirements{"1.0.0", InteractionKind::message_event,
                                               DeliveryCapability::best_effort,
                                               OrderingCapability::per_route_fifo, 16U, 2U};
  const auto prepared = composition.prepare_route(lifecycle, *route.value(), *route_handle.value(),
                                                  *source_handle.value(),
                                                  *destination_handle.value(), requirements);
  if (!prepared.has_value() ||
      composition.activate_route(*prepared.value(), lifecycle).outcome() !=
          ProviderOutcome::activated) {
    return false;
  }
  const std::array<std::byte, 3U> payload{std::byte{0x01}, std::byte{0x02}, std::byte{0x03}};
  const auto item = CommunicationItem::create(
      {contract.value()->contract_id().value(), contract.value()->contract_version().value(),
       contract.value()->interface_id().value(), route.value()->source_endpoint_id().value(),
       contract.value()->schema_id().value(), contract.value()->schema_version().value(),
       InteractionKind::message_event, OriginKind::component, Timestamp(1), "clock.consumer",
       "correlation.consumer", "causation.consumer", route.value()->route_id().value(),
       route.value()->provider_id().value(), payload},
      *contract.value());
  if (!item.has_value()) {
    return false;
  }
  if (composition.submit(*prepared.value(), *item.value(), lifecycle).outcome() !=
      ProviderOutcome::accepted) {
    return false;
  }
  const auto received = composition.receive(*prepared.value(), lifecycle);
  return received.has_value() && received.outcome() == ProviderOutcome::received &&
         *received.value() == *item.value();
}

}  // namespace

/** @return Zero when the external consumer round trip succeeds. */
int main() {
  const bool passed = run_round_trip();
  if (!passed) {
    std::cerr << "core_matrix external consumer failed\n";
    return 1;
  }
  std::cout << "core_matrix external consumer round trip succeeded\n";
  return 0;
}
