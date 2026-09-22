/**
 * @file negative_tests.cpp
 * @brief No-mutation lifecycle declaration, ownership, and route rejection tests.
 * @ownership Fixtures own all compared snapshots and diagnostics.
 * @lifetime Public views remain within the owning fixture lifetime.
 * @thread_safety This negative suite is intentionally single-threaded.
 * @failure Any accepted invalid case or state mutation returns nonzero.
 */

#include <xverse/xcom/endpoint_route_lifecycle.hpp>

#include <array>
#include <iostream>
#include <string>
#include <type_traits>

namespace {

using namespace xverse::xcom;
static_assert(!std::is_invocable_v<decltype(&LifecycleController::validate_endpoint),
                                   LifecycleController&, const RouteHandle&>);
static_assert(!std::is_invocable_v<decltype(&LifecycleController::validate_route),
                                   LifecycleController&, const EndpointHandle&,
                                   const EndpointHandle&, const EndpointHandle&>);
constexpr std::string_view kDigest =
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
constexpr std::string_view kOtherDigest =
    "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";

[[nodiscard]] bool expect(const bool condition, const char* message) {
  if (!condition) {
    std::cerr << message << '\n';
  }
  return condition;
}

[[nodiscard]] CommunicationContract message_contract(const char* id = "contract.main") {
  return *CommunicationContract::create(
              {id, "1.0.0", "interface.main", "schema.main", "1.0.0",
               InteractionKind::message_event, EndpointDirection::produce,
               EndpointDirection::consume})
              .value();
}

[[nodiscard]] EndpointSpec endpoint(const std::string_view id, const EndpointDirection direction,
                                    const CommunicationContract& contract,
                                    const std::string_view provider = "provider.main",
                                    const std::string_view digest = kDigest) {
  return *EndpointSpec::create({id, digest, provider, direction}, contract).value();
}

[[nodiscard]] LifecycleConfiguration configuration() {
  return *LifecycleConfiguration::create({4U, 2U}).value();
}

[[nodiscard]] std::string invalid_handle_diagnostic(const std::string_view identity) {
  return "ownership|error|XCOM-LIFE-E009|" + std::string(identity) +
         "|handle does not identify the current resource owned by this controller|use the exact "
         "handle issued for the current controller and generation";
}

[[nodiscard]] std::string route_validation_diagnostic(const std::string_view route_id) {
  return "route_compatibility|error|XCOM-LIFE-E012|" + std::string(route_id) +
         "|route endpoints, contract, plan, provider, directions, or lifecycle states differ|"
         "supply the exact current compatible validated endpoint handles";
}

[[nodiscard]] std::string route_activation_diagnostic(const std::string_view route_id) {
  return "route_compatibility|error|XCOM-LIFE-E012|" + std::string(route_id) +
         "|route activation requires both exact compatible endpoints to be active|activate the "
         "exact current source and destination endpoint handles";
}

[[nodiscard]] bool exact_diagnostic(const Result<LifecycleSnapshot>& rejected,
                                    const std::string& expected, const char* message) {
  return expect(!rejected.has_value() && rejected.diagnostics() != nullptr &&
                    rejected.diagnostics()->serialize() == expected,
                message);
}

[[nodiscard]] bool resources_unchanged(
    LifecycleController& controller, const RouteHandle& route_handle,
    const EndpointHandle& source_handle, const EndpointHandle& destination_handle,
    const LifecycleSnapshot& route_before, const LifecycleSnapshot& source_before,
    const LifecycleSnapshot& destination_before, const char* message) {
  const auto route_after = controller.route_snapshot(route_handle);
  const auto source_after = controller.endpoint_snapshot(source_handle);
  const auto destination_after = controller.endpoint_snapshot(destination_handle);
  return expect(route_after.has_value() && source_after.has_value() &&
                    destination_after.has_value() && *route_after.value() == route_before &&
                    *source_after.value() == source_before &&
                    *destination_after.value() == destination_before,
                message);
}

[[nodiscard]] bool test_declaration_rejections() {
  const auto communication = message_contract();
  const std::string over_identity(kMaximumIdentityBytes + 1U, 'x');
  const std::array invalid_inputs{
      EndpointSpecInput{"", kDigest, "provider.main", EndpointDirection::produce},
      EndpointSpecInput{over_identity, kDigest, "provider.main", EndpointDirection::produce},
      EndpointSpecInput{"endpoint", "abc", "provider.main", EndpointDirection::produce},
      EndpointSpecInput{"endpoint", kDigest, "", EndpointDirection::produce},
      EndpointSpecInput{"endpoint", kDigest, "provider.main", EndpointDirection::request},
  };
  for (const auto& input : invalid_inputs) {
    if (!expect(!EndpointSpec::create(input, communication).has_value(),
                "invalid endpoint declaration was accepted")) {
      return false;
    }
  }
  const auto source = endpoint("same", EndpointDirection::produce, communication);
  const auto destination = endpoint("same", EndpointDirection::consume, communication);
  const auto normal_source =
      endpoint("source", EndpointDirection::produce, communication);
  const auto normal_destination =
      endpoint("destination", EndpointDirection::consume, communication);
  const auto other_plan_source = endpoint("source", EndpointDirection::produce, communication,
                                          "provider.main", kOtherDigest);
  const auto other_provider_source =
      endpoint("source", EndpointDirection::produce, communication, "provider.other");
  const auto other_contract = message_contract("contract.other");
  const auto other_contract_destination =
      endpoint("destination", EndpointDirection::consume, other_contract);
  const auto reversed_source =
      endpoint("source", EndpointDirection::consume, communication);
  const auto reversed_destination =
      endpoint("destination", EndpointDirection::produce, communication);
  const std::array invalid_routes{
      RouteSpec::create({"", kDigest, "provider.main"}, normal_source, normal_destination),
      RouteSpec::create({"route", "abc", "provider.main"}, normal_source, normal_destination),
      RouteSpec::create({"route", kDigest, ""}, normal_source, normal_destination),
      RouteSpec::create({"route", kDigest, "provider.main"}, source, destination),
      RouteSpec::create({"route", kDigest, "provider.main"}, other_plan_source,
                        normal_destination),
      RouteSpec::create({"route", kDigest, "provider.main"}, other_provider_source,
                        normal_destination),
      RouteSpec::create({"route", kDigest, "provider.main"}, normal_source,
                        other_contract_destination),
      RouteSpec::create({"route", kDigest, "provider.main"}, reversed_source,
                        reversed_destination),
  };
  for (const auto& result : invalid_routes) {
    if (!expect(!result.has_value(), "invalid route declaration was accepted")) {
      return false;
    }
  }
  return expect(!RouteSpec::create({"route", kDigest, "provider.main"}, source, destination)
                     .has_value(),
                "self route was accepted") &&
         expect(!LifecycleConfiguration::create({0U, 1U}).has_value(),
                "zero endpoint capacity was accepted") &&
         expect(!LifecycleConfiguration::create({1U, 0U}).has_value(),
                "zero route capacity was accepted") &&
         expect(!LifecycleConfiguration::create(
                     {LifecycleController::kMaximumEndpoints + 1U, 1U})
                     .has_value(),
                "over-maximum endpoint capacity was accepted") &&
         expect(!LifecycleConfiguration::create(
                     {1U, LifecycleController::kMaximumRoutes + 1U})
                     .has_value(),
                "over-maximum route capacity was accepted");
}

[[nodiscard]] bool rejects_route_compatibility(const RouteSpec& route_spec,
                                               const EndpointSpec& source,
                                               const EndpointSpec& destination,
                                               const bool activation) {
  LifecycleController controller(configuration());
  const auto source_handle = controller.declare_endpoint(source);
  const auto destination_handle = controller.declare_endpoint(destination);
  const auto route_handle = controller.declare_route(route_spec);
  if (!source_handle.has_value() || !destination_handle.has_value() ||
      !route_handle.has_value() ||
      !controller.validate_endpoint(*source_handle.value()).has_value() ||
      !controller.validate_endpoint(*destination_handle.value()).has_value()) {
    return expect(false, "route compatibility fixture setup failed");
  }
  if (activation &&
      (!controller.activate_endpoint(*source_handle.value()).has_value() ||
       !controller.activate_endpoint(*destination_handle.value()).has_value())) {
    return expect(false, "route activation compatibility fixture setup failed");
  }
  const auto before = controller.route_snapshot(*route_handle.value());
  const auto source_before = controller.endpoint_snapshot(*source_handle.value());
  const auto destination_before = controller.endpoint_snapshot(*destination_handle.value());
  const auto rejected =
      activation ? controller.activate_route(*route_handle.value(), *source_handle.value(),
                                             *destination_handle.value())
                 : controller.validate_route(*route_handle.value(), *source_handle.value(),
                                             *destination_handle.value());
  const std::string expected = activation ? route_activation_diagnostic("route.main")
                                          : route_validation_diagnostic("route.main");
  return exact_diagnostic(rejected, expected, "exact route compatibility diagnostic differs") &&
         expect(before.has_value() && source_before.has_value() && destination_before.has_value(),
                "route compatibility snapshots are missing") &&
         resources_unchanged(controller, *route_handle.value(), *source_handle.value(),
                             *destination_handle.value(), *before.value(),
                             *source_before.value(), *destination_before.value(),
                             "route compatibility rejection mutated a resource");
}

[[nodiscard]] bool test_route_compatibility_matrix() {
  const auto communication = message_contract();
  const auto other_contract = message_contract("contract.other");
  const auto planned_source =
      endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto planned_destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec =
      *RouteSpec::create({"route.main", kDigest, "provider.main"}, planned_source,
                         planned_destination)
           .value();
  const std::array incompatible_sources{
      endpoint("endpoint.other", EndpointDirection::produce, communication),
      endpoint("endpoint.source", EndpointDirection::produce, communication,
               "provider.main", kOtherDigest),
      endpoint("endpoint.source", EndpointDirection::produce, communication,
               "provider.other"),
      endpoint("endpoint.source", EndpointDirection::produce, other_contract),
      endpoint("endpoint.source", EndpointDirection::consume, communication),
  };
  const std::array incompatible_destinations{
      endpoint("endpoint.other", EndpointDirection::consume, communication),
      endpoint("endpoint.destination", EndpointDirection::consume, communication,
               "provider.main", kOtherDigest),
      endpoint("endpoint.destination", EndpointDirection::consume, communication,
               "provider.other"),
      endpoint("endpoint.destination", EndpointDirection::consume, other_contract),
      endpoint("endpoint.destination", EndpointDirection::produce, communication),
  };
  for (const bool activation : std::array{false, true}) {
    for (std::size_t index = 0U; index < incompatible_sources.size(); ++index) {
      if (!rejects_route_compatibility(route_spec, incompatible_sources[index],
                                       planned_destination, activation) ||
          !rejects_route_compatibility(route_spec, planned_source,
                                       incompatible_destinations[index], activation)) {
        return false;
      }
    }
  }
  return true;
}

[[nodiscard]] bool prepare_route_stage(
    LifecycleController& controller, const RouteHandle& route_handle,
    const EndpointHandle& source_handle, const EndpointHandle& destination_handle,
    const bool activation) {
  if (!controller.validate_endpoint(source_handle).has_value() ||
      !controller.validate_endpoint(destination_handle).has_value()) {
    return false;
  }
  if (!activation) {
    return true;
  }
  return controller.validate_route(route_handle, source_handle, destination_handle).has_value() &&
         controller.activate_endpoint(source_handle).has_value() &&
         controller.activate_endpoint(destination_handle).has_value();
}

[[nodiscard]] bool test_stale_endpoint_handle_boundary(const bool activation,
                                                       const bool destination_boundary) {
  const auto communication = message_contract();
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec =
      *RouteSpec::create({"route.main", kDigest, "provider.main"}, source, destination).value();
  LifecycleController controller(configuration());
  const EndpointSpec& target_spec = destination_boundary ? destination : source;
  const EndpointSpec& other_spec = destination_boundary ? source : destination;
  const auto stale = controller.declare_endpoint(target_spec);
  if (!stale.has_value() || !controller.fail_endpoint(*stale.value()).has_value() ||
      !controller.close_endpoint(*stale.value()).has_value()) {
    return expect(false, "stale endpoint fixture setup failed");
  }
  const auto current_target = controller.declare_endpoint(target_spec);
  const auto other = controller.declare_endpoint(other_spec);
  const auto route_handle = controller.declare_route(route_spec);
  if (!current_target.has_value() || !other.has_value() || !route_handle.has_value()) {
    return expect(false, "stale endpoint fixture declarations failed");
  }
  const EndpointHandle& source_handle =
      destination_boundary ? *other.value() : *current_target.value();
  const EndpointHandle& destination_handle =
      destination_boundary ? *current_target.value() : *other.value();
  if (!prepare_route_stage(controller, *route_handle.value(), source_handle,
                           destination_handle, activation)) {
    return expect(false, "stale endpoint fixture stage setup failed");
  }
  const auto route_before = controller.route_snapshot(*route_handle.value());
  const auto source_before = controller.endpoint_snapshot(source_handle);
  const auto destination_before = controller.endpoint_snapshot(destination_handle);
  const auto rejected = destination_boundary
                            ? (activation
                                   ? controller.activate_route(*route_handle.value(), source_handle,
                                                               *stale.value())
                                   : controller.validate_route(*route_handle.value(), source_handle,
                                                               *stale.value()))
                            : (activation
                                   ? controller.activate_route(*route_handle.value(), *stale.value(),
                                                               destination_handle)
                                   : controller.validate_route(*route_handle.value(), *stale.value(),
                                                               destination_handle));
  return exact_diagnostic(rejected,
                          invalid_handle_diagnostic(target_spec.endpoint_id().value()),
                          "exact stale endpoint diagnostic differs") &&
         expect(route_before.has_value() && source_before.has_value() &&
                    destination_before.has_value(),
                "stale endpoint snapshots are missing") &&
         resources_unchanged(controller, *route_handle.value(), source_handle,
                             destination_handle, *route_before.value(), *source_before.value(),
                             *destination_before.value(),
                             "stale endpoint rejection mutated a resource");
}

[[nodiscard]] bool test_foreign_endpoint_handle_boundary(const bool activation,
                                                         const bool destination_boundary) {
  const auto communication = message_contract();
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec =
      *RouteSpec::create({"route.main", kDigest, "provider.main"}, source, destination).value();
  LifecycleController owner(configuration());
  LifecycleController foreign(configuration());
  const auto source_handle = owner.declare_endpoint(source);
  const auto destination_handle = owner.declare_endpoint(destination);
  const auto route_handle = owner.declare_route(route_spec);
  const auto foreign_handle =
      foreign.declare_endpoint(destination_boundary ? destination : source);
  if (!source_handle.has_value() || !destination_handle.has_value() ||
      !route_handle.has_value() || !foreign_handle.has_value() ||
      !prepare_route_stage(owner, *route_handle.value(), *source_handle.value(),
                           *destination_handle.value(), activation)) {
    return expect(false, "foreign endpoint fixture setup failed");
  }
  const auto route_before = owner.route_snapshot(*route_handle.value());
  const auto source_before = owner.endpoint_snapshot(*source_handle.value());
  const auto destination_before = owner.endpoint_snapshot(*destination_handle.value());
  const auto rejected = destination_boundary
                            ? (activation
                                   ? owner.activate_route(*route_handle.value(),
                                                          *source_handle.value(),
                                                          *foreign_handle.value())
                                   : owner.validate_route(*route_handle.value(),
                                                          *source_handle.value(),
                                                          *foreign_handle.value()))
                            : (activation
                                   ? owner.activate_route(*route_handle.value(),
                                                          *foreign_handle.value(),
                                                          *destination_handle.value())
                                   : owner.validate_route(*route_handle.value(),
                                                          *foreign_handle.value(),
                                                          *destination_handle.value()));
  return exact_diagnostic(
             rejected,
             invalid_handle_diagnostic(
                 destination_boundary ? destination.endpoint_id().value()
                                      : source.endpoint_id().value()),
             "exact foreign endpoint diagnostic differs") &&
         expect(route_before.has_value() && source_before.has_value() &&
                    destination_before.has_value(),
                "foreign endpoint snapshots are missing") &&
         resources_unchanged(owner, *route_handle.value(), *source_handle.value(),
                             *destination_handle.value(), *route_before.value(),
                             *source_before.value(), *destination_before.value(),
                             "foreign endpoint rejection mutated a resource");
}

[[nodiscard]] bool test_route_handle_boundary(const bool activation, const bool foreign_boundary) {
  const auto communication = message_contract();
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec =
      *RouteSpec::create({"route.main", kDigest, "provider.main"}, source, destination).value();
  LifecycleController owner(configuration());
  LifecycleController foreign(configuration());
  const auto source_handle = owner.declare_endpoint(source);
  const auto destination_handle = owner.declare_endpoint(destination);
  if (!source_handle.has_value() || !destination_handle.has_value()) {
    return expect(false, "route handle fixture declarations failed");
  }
  const auto verify = [&](const RouteHandle& current, const RouteHandle& rejected_handle) {
    if (!prepare_route_stage(owner, current, *source_handle.value(),
                             *destination_handle.value(), activation)) {
      return expect(false, "route handle fixture stage setup failed");
    }
    const auto route_before = owner.route_snapshot(current);
    const auto source_before = owner.endpoint_snapshot(*source_handle.value());
    const auto destination_before = owner.endpoint_snapshot(*destination_handle.value());
    const auto rejected =
        activation ? owner.activate_route(rejected_handle, *source_handle.value(),
                                          *destination_handle.value())
                   : owner.validate_route(rejected_handle, *source_handle.value(),
                                          *destination_handle.value());
    return exact_diagnostic(rejected, invalid_handle_diagnostic("route.main"),
                            "exact stale or foreign route diagnostic differs") &&
           expect(route_before.has_value() && source_before.has_value() &&
                      destination_before.has_value(),
                  "route handle snapshots are missing") &&
           resources_unchanged(owner, current, *source_handle.value(),
                               *destination_handle.value(), *route_before.value(),
                               *source_before.value(), *destination_before.value(),
                               "route handle rejection mutated a resource");
  };
  if (foreign_boundary) {
    const auto current = owner.declare_route(route_spec);
    const auto foreign_route = foreign.declare_route(route_spec);
    return expect(current.has_value() && foreign_route.has_value(),
                  "foreign route fixture declaration failed") &&
           verify(*current.value(), *foreign_route.value());
  }
  const auto stale = owner.declare_route(route_spec);
  if (!stale.has_value() || !owner.fail_route(*stale.value()).has_value() ||
      !owner.close_route(*stale.value()).has_value()) {
    return expect(false, "stale route fixture setup failed");
  }
  const auto current = owner.declare_route(route_spec);
  return expect(current.has_value(), "stale route recreation failed") &&
         verify(*current.value(), *stale.value());
}

[[nodiscard]] bool test_exact_route_handle_boundaries() {
  for (const bool activation : std::array{false, true}) {
    for (const bool destination_boundary : std::array{false, true}) {
      if (!test_stale_endpoint_handle_boundary(activation, destination_boundary) ||
          !test_foreign_endpoint_handle_boundary(activation, destination_boundary)) {
        return false;
      }
    }
    if (!test_route_handle_boundary(activation, false) ||
        !test_route_handle_boundary(activation, true)) {
      return false;
    }
  }
  return true;
}

[[nodiscard]] bool test_validation_and_activation_state_boundaries() {
  const auto communication = message_contract();
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec =
      *RouteSpec::create({"route.main", kDigest, "provider.main"}, source, destination).value();
  for (const bool activation : std::array{false, true}) {
    for (const bool destination_boundary : std::array{false, true}) {
      LifecycleController controller(configuration());
      const auto source_handle = controller.declare_endpoint(source);
      const auto destination_handle = controller.declare_endpoint(destination);
      const auto route_handle = controller.declare_route(route_spec);
      if (!source_handle.has_value() || !destination_handle.has_value() ||
          !route_handle.has_value()) {
        return expect(false, "route state-boundary declarations failed");
      }
      if (activation) {
        if (!controller.validate_endpoint(*source_handle.value()).has_value() ||
            !controller.validate_endpoint(*destination_handle.value()).has_value() ||
            !controller
                 .validate_route(*route_handle.value(), *source_handle.value(),
                                 *destination_handle.value())
                 .has_value() ||
            !(destination_boundary
                  ? controller.activate_endpoint(*source_handle.value()).has_value()
                  : controller.activate_endpoint(*destination_handle.value()).has_value())) {
          return expect(false, "route activation-state fixture setup failed");
        }
      } else if (!(destination_boundary
                       ? controller.validate_endpoint(*source_handle.value()).has_value()
                       : controller.validate_endpoint(*destination_handle.value()).has_value())) {
        return expect(false, "route validation-state fixture setup failed");
      }
      const auto route_before = controller.route_snapshot(*route_handle.value());
      const auto source_before = controller.endpoint_snapshot(*source_handle.value());
      const auto destination_before = controller.endpoint_snapshot(*destination_handle.value());
      const auto rejected =
          activation ? controller.activate_route(*route_handle.value(), *source_handle.value(),
                                                 *destination_handle.value())
                     : controller.validate_route(*route_handle.value(), *source_handle.value(),
                                                 *destination_handle.value());
      const std::string expected = activation ? route_activation_diagnostic("route.main")
                                              : route_validation_diagnostic("route.main");
      if (!exact_diagnostic(rejected, expected, "exact route endpoint-state diagnostic differs") ||
          !expect(route_before.has_value() && source_before.has_value() &&
                      destination_before.has_value(),
                  "route endpoint-state snapshots are missing") ||
          !resources_unchanged(controller, *route_handle.value(), *source_handle.value(),
                               *destination_handle.value(), *route_before.value(),
                               *source_before.value(), *destination_before.value(),
                               "route endpoint-state rejection mutated a resource")) {
        return false;
      }
    }
  }
  return true;
}

[[nodiscard]] bool test_retained_endpoint_closure_boundary() {
  const auto communication = message_contract();
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec =
      *RouteSpec::create({"route.main", kDigest, "provider.main"}, source, destination).value();
  for (const bool destination_boundary : std::array{false, true}) {
    LifecycleController controller(configuration());
    const auto source_handle = controller.declare_endpoint(source);
    const auto destination_handle = controller.declare_endpoint(destination);
    const auto route_handle = controller.declare_route(route_spec);
    if (!source_handle.has_value() || !destination_handle.has_value() ||
        !route_handle.has_value()) {
      return expect(false, "retained endpoint fixture setup failed");
    }
    const EndpointHandle& target = destination_boundary ? *destination_handle.value()
                                                        : *source_handle.value();
    if (!controller.fail_endpoint(target).has_value()) {
      return expect(false, "retained endpoint failure setup failed");
    }
    const auto route_before = controller.route_snapshot(*route_handle.value());
    const auto source_before = controller.endpoint_snapshot(*source_handle.value());
    const auto destination_before = controller.endpoint_snapshot(*destination_handle.value());
    const auto rejected = controller.close_endpoint(target);
    const std::string identity = destination_boundary ? "endpoint.destination" : "endpoint.source";
    const std::string expected =
        "lifecycle|error|XCOM-LIFE-E011|" + identity +
        "|a nonclosed route still uses this endpoint generation|close every using route before "
        "closing the endpoint";
    if (!exact_diagnostic(rejected, expected, "exact retained-endpoint diagnostic differs") ||
        !expect(route_before.has_value() && source_before.has_value() &&
                    destination_before.has_value(),
                "retained endpoint snapshots are missing") ||
        !resources_unchanged(controller, *route_handle.value(), *source_handle.value(),
                             *destination_handle.value(), *route_before.value(),
                             *source_before.value(), *destination_before.value(),
                             "retained endpoint rejection mutated a resource")) {
      return false;
    }
  }
  return true;
}

[[nodiscard]] bool test_ownership_and_transition_rejections() {
  const auto communication = message_contract();
  const auto spec = endpoint("endpoint.main", EndpointDirection::produce, communication);
  LifecycleController owner(configuration());
  LifecycleController foreign(configuration());
  const auto handle = owner.declare_endpoint(spec);
  const EndpointHandle copied(*handle.value());
  const auto before = owner.endpoint_snapshot(copied);
  const auto skipped = owner.activate_endpoint(*handle.value());
  const auto cross_controller = foreign.validate_endpoint(copied);
  const auto after = owner.endpoint_snapshot(*handle.value());
  const std::string expected =
      "lifecycle|error|XCOM-LIFE-E010|endpoint.main|requested lifecycle transition is not "
      "permitted from the current state|follow the declared lifecycle transition sequence";
  return expect(!skipped.has_value() && skipped.diagnostics()->serialize() == expected,
                "exact invalid-transition diagnostic differs") &&
         expect(!cross_controller.has_value() &&
                    cross_controller.diagnostics()->values().front().code() ==
                        DiagnosticCode::invalid_handle &&
                    cross_controller.diagnostics()->values().front().phase() ==
                        ValidationPhase::ownership,
                "foreign handle rejection differs") &&
         expect(before.has_value() && after.has_value() && *before.value() == *after.value(),
                "rejected ownership/transition operation mutated owner state");
}

[[nodiscard]] bool test_route_boundaries_and_endpoint_use() {
  const auto communication = message_contract();
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination = endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec =
      *RouteSpec::create({"route.main", kDigest, "provider.main"}, source, destination).value();
  LifecycleController controller(configuration());
  const auto source_handle = controller.declare_endpoint(source);
  const auto destination_handle = controller.declare_endpoint(destination);
  const auto route_handle = controller.declare_route(route_spec);
  const auto route_before = controller.route_snapshot(*route_handle.value());
  const auto premature = controller.validate_route(*route_handle.value(), *source_handle.value(),
                                                   *destination_handle.value());
  if (!expect(!premature.has_value(), "route validated against declared endpoints") ||
      !controller.validate_endpoint(*source_handle.value()).has_value() ||
      !controller.validate_endpoint(*destination_handle.value()).has_value() ||
      !controller.validate_route(*route_handle.value(), *source_handle.value(),
                                 *destination_handle.value())
           .has_value() ||
      !controller.activate_endpoint(*source_handle.value()).has_value() ||
      !controller.activate_endpoint(*destination_handle.value()).has_value() ||
      !controller.activate_route(*route_handle.value(), *source_handle.value(),
                                 *destination_handle.value())
           .has_value()) {
    return expect(false, "route boundary preconditions failed");
  }
  const auto source_before = controller.endpoint_snapshot(*source_handle.value());
  const auto in_use = controller.drain_endpoint(*source_handle.value());
  const auto source_after = controller.endpoint_snapshot(*source_handle.value());
  return expect(route_before.has_value() && route_before.value()->state() == LifecycleState::declared,
                "rejected route validation mutated route") &&
         expect(!in_use.has_value() && in_use.diagnostics()->values().front().code() ==
                                           DiagnosticCode::endpoint_in_use,
                "endpoint-use rejection differs") &&
         expect(source_before.has_value() && source_after.has_value() &&
                    *source_before.value() == *source_after.value(),
                "endpoint-use rejection mutated endpoint");
}

[[nodiscard]] bool test_route_capacity_and_stale_handle() {
  const auto communication = message_contract();
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto first_spec =
      *RouteSpec::create({"route.first", kDigest, "provider.main"}, source, destination).value();
  const auto second_spec =
      *RouteSpec::create({"route.second", kDigest, "provider.main"}, source, destination).value();
  LifecycleController controller(*LifecycleConfiguration::create({2U, 1U}).value());
  const auto first = controller.declare_route(first_spec);
  if (!first.has_value()) {
    return expect(false, "first route declaration failed");
  }
  const RouteHandle copied(*first.value());
  const auto before = controller.route_snapshot(copied);
  const auto duplicate = controller.declare_route(first_spec);
  const auto overflow = controller.declare_route(second_spec);
  const auto after = controller.route_snapshot(copied);
  if (!expect(!duplicate.has_value() && duplicate.diagnostics()->values().front().code() ==
                                             DiagnosticCode::duplicate_identity,
              "duplicate route identity was not rejected") ||
      !expect(!overflow.has_value() && overflow.diagnostics()->values().front().code() ==
                                            DiagnosticCode::capacity_exhausted,
              "route capacity exhaustion was not rejected") ||
      !expect(before.has_value() && after.has_value() && *before.value() == *after.value(),
              "route declaration rejection mutated the live route") ||
      !controller.fail_route(copied).has_value() || !controller.close_route(copied).has_value()) {
    return false;
  }
  const auto recreated = controller.declare_route(second_spec);
  const auto stale = controller.route_snapshot(copied);
  return expect(recreated.has_value() &&
                    recreated.value()->generation() > copied.generation(),
                "route recreation did not advance generation") &&
         expect(!stale.has_value() && stale.diagnostics()->values().front().code() ==
                                          DiagnosticCode::invalid_handle,
                "stale route handle was not rejected");
}

}  // namespace

/** @return Zero only when every invalid input is rejected without mutation. */
int main() {
  return test_declaration_rejections() && test_route_compatibility_matrix() &&
                 test_exact_route_handle_boundaries() &&
                 test_validation_and_activation_state_boundaries() &&
                 test_retained_endpoint_closure_boundary() &&
                 test_ownership_and_transition_rejections() &&
                 test_route_boundaries_and_endpoint_use() &&
                 test_route_capacity_and_stale_handle()
             ? 0
             : 1;
}
