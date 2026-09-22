/**
 * @file main.cpp
 * @brief Separate public-API consumer for endpoint and route lifecycle.
 * @ownership The consumer owns all specifications, handles, snapshots, and controller state.
 * @lifetime Returned views are consumed only while their owners remain alive.
 * @thread_safety This integration fixture is single-threaded.
 * @failure A public contract mismatch returns a distinct nonzero status.
 */

#include <xverse/xcom/endpoint_route_lifecycle.hpp>

/** @return Zero after a complete item-free endpoint and route lifecycle. */
int main() {
  using namespace xverse::xcom;
  constexpr std::string_view digest =
      "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
  const auto contract = CommunicationContract::create(
      {"consumer.contract", "1.0.0", "consumer.interface", "consumer.schema", "1.0.0",
       InteractionKind::service_request, EndpointDirection::request,
       EndpointDirection::respond});
  const auto source = EndpointSpec::create(
      {"consumer.requester", digest, "consumer.provider", EndpointDirection::request},
      *contract.value());
  const auto destination = EndpointSpec::create(
      {"consumer.responder", digest, "consumer.provider", EndpointDirection::respond},
      *contract.value());
  const auto route = RouteSpec::create({"consumer.route", digest, "consumer.provider"},
                                       *source.value(), *destination.value());
  const auto configuration = LifecycleConfiguration::create({2U, 1U});
  if (!contract.has_value() || !source.has_value() || !destination.has_value() ||
      !route.has_value() || !configuration.has_value()) {
    return 1;
  }
  LifecycleController controller(*configuration.value());
  const auto source_handle = controller.declare_endpoint(*source.value());
  const auto destination_handle = controller.declare_endpoint(*destination.value());
  const auto route_handle = controller.declare_route(*route.value());
  if (!source_handle.has_value() || !destination_handle.has_value() ||
      !route_handle.has_value()) {
    return 2;
  }
  if (!controller.validate_endpoint(*source_handle.value()).has_value() ||
      !controller.validate_endpoint(*source_handle.value()).has_value() ||
      !controller.validate_endpoint(*destination_handle.value()).has_value() ||
      !controller.validate_endpoint(*destination_handle.value()).has_value() ||
      !controller.activate_endpoint(*source_handle.value()).has_value() ||
      !controller.activate_endpoint(*source_handle.value()).has_value() ||
      !controller.activate_endpoint(*destination_handle.value()).has_value() ||
      !controller.activate_endpoint(*destination_handle.value()).has_value()) {
    return 3;
  }
  const auto route_before_invalid = controller.route_snapshot(*route_handle.value());
  const auto source_before_invalid = controller.endpoint_snapshot(*source_handle.value());
  const auto destination_before_invalid =
      controller.endpoint_snapshot(*destination_handle.value());
  const auto invalid_activation = controller.activate_route(
      *route_handle.value(), *source_handle.value(), *destination_handle.value());
  const auto route_after_invalid = controller.route_snapshot(*route_handle.value());
  const auto source_after_invalid = controller.endpoint_snapshot(*source_handle.value());
  const auto destination_after_invalid =
      controller.endpoint_snapshot(*destination_handle.value());
  constexpr std::string_view invalid_transition =
      "lifecycle|error|XCOM-LIFE-E010|consumer.route|requested lifecycle transition is not "
      "permitted from the current state|follow the declared lifecycle transition sequence";
  if (invalid_activation.has_value() || invalid_activation.diagnostics() == nullptr ||
      invalid_activation.diagnostics()->serialize() != invalid_transition ||
      !route_before_invalid.has_value() || !source_before_invalid.has_value() ||
      !destination_before_invalid.has_value() || !route_after_invalid.has_value() ||
      !source_after_invalid.has_value() || !destination_after_invalid.has_value() ||
      *route_before_invalid.value() != *route_after_invalid.value() ||
      *source_before_invalid.value() != *source_after_invalid.value() ||
      *destination_before_invalid.value() != *destination_after_invalid.value()) {
    return 4;
  }
  if (!controller.validate_route(*route_handle.value(), *source_handle.value(),
                                 *destination_handle.value())
           .has_value() ||
      !controller.validate_route(*route_handle.value(), *source_handle.value(),
                                 *destination_handle.value())
           .has_value() ||
      !controller.activate_route(*route_handle.value(), *source_handle.value(),
                                 *destination_handle.value())
           .has_value() ||
      !controller.activate_route(*route_handle.value(), *source_handle.value(),
                                 *destination_handle.value())
           .has_value()) {
    return 5;
  }
  if (controller.drain_endpoint(*source_handle.value()).has_value()) {
    return 6;
  }
  if (!controller.drain_route(*route_handle.value()).has_value() ||
      !controller.drain_route(*route_handle.value()).has_value() ||
      !controller.close_route(*route_handle.value()).has_value() ||
      !controller.close_route(*route_handle.value()).has_value() ||
      !controller.drain_endpoint(*source_handle.value()).has_value() ||
      !controller.drain_endpoint(*source_handle.value()).has_value() ||
      !controller.drain_endpoint(*destination_handle.value()).has_value() ||
      !controller.drain_endpoint(*destination_handle.value()).has_value() ||
      !controller.close_endpoint(*source_handle.value()).has_value() ||
      !controller.close_endpoint(*source_handle.value()).has_value() ||
      !controller.close_endpoint(*destination_handle.value()).has_value() ||
      !controller.close_endpoint(*destination_handle.value()).has_value()) {
    return 7;
  }
  const auto recreated_source = controller.declare_endpoint(*source.value());
  const auto recreated_destination = controller.declare_endpoint(*destination.value());
  const auto recreated_route = controller.declare_route(*route.value());
  if (!recreated_source.has_value() || !recreated_destination.has_value() ||
      !recreated_route.has_value() ||
      recreated_source.value()->generation() <= source_handle.value()->generation() ||
      recreated_destination.value()->generation() <= destination_handle.value()->generation() ||
      recreated_route.value()->generation() <= route_handle.value()->generation() ||
      controller.endpoint_snapshot(*source_handle.value()).has_value() ||
      controller.endpoint_snapshot(*destination_handle.value()).has_value() ||
      controller.route_snapshot(*route_handle.value()).has_value()) {
    return 8;
  }
  return controller.validate_endpoint(*recreated_source.value()).has_value() &&
                 controller.validate_endpoint(*recreated_destination.value()).has_value() &&
                 controller
                     .validate_route(*recreated_route.value(), *recreated_source.value(),
                                     *recreated_destination.value())
                     .has_value()
             ? 0
             : 9;
}
