/**
 * @file main.cpp
 * @brief Separate consumer translation unit for the public provider-loopback API.
 * @ownership Owns all declarations, lifecycle resources, provider resources, and returned items.
 * @lifetime Every registered provider outlives its composition and every operation in the scenario.
 * @thread_safety The consumer is single-threaded; public providers retain their documented locking.
 * @failure Any unexpected result terminates the consumer with a nonzero status.
 */

#include "xverse/xcom/loopback_provider.hpp"

#include <array>
#include <cstddef>
#include <string>
#include <string_view>

namespace {

using namespace xverse::xcom;

/** Return the required logical source direction for one interaction family. */
[[nodiscard]] EndpointDirection source_direction(const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::request
             : kind == InteractionKind::service_response ? EndpointDirection::respond
                                                         : EndpointDirection::produce;
}

/** Return the required logical destination direction for one interaction family. */
[[nodiscard]] EndpointDirection destination_direction(const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::respond
             : kind == InteractionKind::service_response ? EndpointDirection::request
                                                         : EndpointDirection::consume;
}

/** Exercise public preparation, delivery, saturation, cleanup, and recreation for one family. */
[[nodiscard]] bool exercise(const InteractionKind kind, const std::string_view suffix) {
  constexpr std::string_view digest =
      "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
  const std::string contract_id = "contract.consumer." + std::string(suffix);
  const std::string interface_id = "interface.consumer." + std::string(suffix);
  const std::string schema_id = "schema.consumer." + std::string(suffix);
  const std::string source_id = "source.consumer." + std::string(suffix);
  const std::string destination_id = "destination.consumer." + std::string(suffix);
  const std::string route_id = "route.consumer." + std::string(suffix);

  const auto contract = CommunicationContract::create(
      {contract_id, "1.0.0", interface_id, schema_id, "1.0.0", kind,
       source_direction(kind), destination_direction(kind)});
  if (!contract.has_value()) return false;
  const auto source = EndpointSpec::create(
      {source_id, digest, "provider.consumer", source_direction(kind)}, *contract.value());
  const auto destination = EndpointSpec::create(
      {destination_id, digest, "provider.consumer", destination_direction(kind)},
      *contract.value());
  if (!source.has_value() || !destination.has_value()) return false;
  const auto route = RouteSpec::create(
      {route_id, digest, "provider.consumer"}, *source.value(), *destination.value());
  const auto lifecycle_configuration = LifecycleConfiguration::create({2U, 1U});
  if (!route.has_value() || !lifecycle_configuration.has_value()) return false;
  LifecycleController lifecycle(*lifecycle_configuration.value());
  const auto source_handle = lifecycle.declare_endpoint(*source.value());
  const auto destination_handle = lifecycle.declare_endpoint(*destination.value());
  const auto route_handle = lifecycle.declare_route(*route.value());
  if (!source_handle.has_value() || !destination_handle.has_value() ||
      !route_handle.has_value() ||
      !lifecycle.validate_endpoint(*source_handle.value()).has_value() ||
      !lifecycle.validate_endpoint(*destination_handle.value()).has_value() ||
      !lifecycle.validate_route(*route_handle.value(), *source_handle.value(),
                                *destination_handle.value()).has_value() ||
      !lifecycle.activate_endpoint(*source_handle.value()).has_value() ||
      !lifecycle.activate_endpoint(*destination_handle.value()).has_value()) {
    return false;
  }

  const auto descriptor = ProviderDescriptor::create(
      {"provider.consumer", "1.0.0", "source.xverse.xcom.loopback", 0x0FU,
       delivery_capability_bit(DeliveryCapability::best_effort),
       ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 2U});
  const auto registry_configuration = ProviderRegistryConfiguration::create(1U);
  if (!descriptor.has_value() || !registry_configuration.has_value()) return false;
  LoopbackProvider provider(*descriptor.value());
  ProviderComposition composition(*registry_configuration.value());
  if (composition.register_provider(provider).outcome() != ProviderOutcome::registered) {
    return false;
  }
  const ProviderRouteRequirements requirements{
      "1.0.0", kind, DeliveryCapability::best_effort,
      OrderingCapability::per_route_fifo, 16U, 2U};
  const auto prepared = composition.prepare_route(
      lifecycle, *route.value(), *route_handle.value(), *source_handle.value(),
      *destination_handle.value(), requirements);
  if (!prepared.has_value() ||
      composition.activate_route(*prepared.value(), lifecycle).outcome() !=
          ProviderOutcome::activated) {
    return false;
  }

  const std::array<std::byte, 1U> payload1{std::byte{1U}};
  const std::array<std::byte, 1U> payload2{std::byte{2U}};
  const std::array<std::byte, 1U> payload3{std::byte{3U}};
  const auto make_item = [&](const std::span<const std::byte> payload,
                             const std::string_view correlation) {
    return CommunicationItem::create(
        {contract.value()->contract_id().value(), contract.value()->contract_version().value(),
         contract.value()->interface_id().value(), source.value()->endpoint_id().value(),
         contract.value()->schema_id().value(), contract.value()->schema_version().value(), kind,
         OriginKind::component, Timestamp(1), "clock.consumer", correlation,
         "cause.consumer", route.value()->route_id().value(),
         route.value()->provider_id().value(), payload},
        *contract.value());
  };
  const auto first = make_item(payload1, "correlation.consumer.1");
  const auto second = make_item(payload2, "correlation.consumer.2");
  const auto third = make_item(payload3, "correlation.consumer.3");
  if (!first.has_value() || !second.has_value() || !third.has_value()) return false;
  if (composition.submit(*prepared.value(), *first.value(), lifecycle).outcome() !=
          ProviderOutcome::accepted ||
      composition.submit(*prepared.value(), *second.value(), lifecycle).outcome() !=
          ProviderOutcome::accepted ||
      composition.submit(*prepared.value(), *third.value(), lifecycle).outcome() !=
          ProviderOutcome::queue_saturated) {
    return false;
  }
  const auto received_first = composition.receive(*prepared.value(), lifecycle);
  if (!received_first.has_value() || *received_first.value() != *first.value() ||
      composition.submit(*prepared.value(), *third.value(), lifecycle).outcome() !=
          ProviderOutcome::accepted) {
    return false;
  }
  const auto received_second = composition.receive(*prepared.value(), lifecycle);
  const auto received_third = composition.receive(*prepared.value(), lifecycle);
  if (!received_second.has_value() || !received_third.has_value() ||
      *received_second.value() != *second.value() ||
      *received_third.value() != *third.value() ||
      composition.drain_route(*prepared.value(), lifecycle).outcome() !=
          ProviderOutcome::draining ||
      composition.close_route(*prepared.value(), lifecycle).outcome() !=
          ProviderOutcome::closed) {
    return false;
  }

  const auto recreated_route = lifecycle.declare_route(*route.value());
  if (!recreated_route.has_value() ||
      !lifecycle.validate_route(*recreated_route.value(), *source_handle.value(),
                                *destination_handle.value()).has_value()) {
    return false;
  }
  const auto recreated = composition.prepare_route(
      lifecycle, *route.value(), *recreated_route.value(), *source_handle.value(),
      *destination_handle.value(), requirements);
  return recreated.has_value() &&
         recreated.value()->provider_route_generation() !=
             prepared.value()->provider_route_generation() &&
         recreated.value()->lifecycle_route_generation() !=
             prepared.value()->lifecycle_route_generation() &&
         composition.activate_route(*recreated.value(), lifecycle).outcome() ==
             ProviderOutcome::activated &&
         composition.drain_route(*recreated.value(), lifecycle).outcome() ==
             ProviderOutcome::draining &&
         composition.close_route(*recreated.value(), lifecycle).outcome() ==
             ProviderOutcome::closed;
}

}  // namespace

/** @return Zero when the separately linked public API consumer passes every scenario. */
int main() {
  return exercise(InteractionKind::signal_state_update, "signal") &&
                 exercise(InteractionKind::message_event, "message") &&
                 exercise(InteractionKind::service_request, "request") &&
                 exercise(InteractionKind::service_response, "response")
             ? 0
             : 1;
}
