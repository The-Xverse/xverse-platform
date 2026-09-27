/**
 * @file unit_tests.cpp
 * @brief Table-driven lifecycle, capacity, and concurrency unit tests.
 * @ownership Fixtures own every declaration, handle, result, and thread.
 * @lifetime Accessor views are used only while their owners remain alive.
 * @thread_safety Concurrency cases share only the serialized controller.
 * @failure A failed expectation returns a nonzero process status.
 */

#include <xverse/xcom/endpoint_route_lifecycle.hpp>

#include <array>
#include <atomic>
#include <cstdint>
#include <iostream>
#include <string>
#include <thread>

namespace {

using namespace xverse::xcom;

enum class Operation { validate, activate, drain, fail, close };

constexpr std::array kStates{LifecycleState::declared, LifecycleState::validated,
                             LifecycleState::active, LifecycleState::draining,
                             LifecycleState::failed, LifecycleState::closed};
constexpr std::array kOperations{Operation::validate, Operation::activate, Operation::drain,
                                 Operation::fail, Operation::close};

[[nodiscard]] bool expect(const bool condition, const char* message) {
  if (!condition) {
    std::cerr << message << '\n';
  }
  return condition;
}

[[nodiscard]] CommunicationContract contract(const InteractionKind kind) {
  EndpointDirection source = EndpointDirection::produce;
  EndpointDirection destination = EndpointDirection::consume;
  if (kind == InteractionKind::service_request) {
    source = EndpointDirection::request;
    destination = EndpointDirection::respond;
  } else if (kind == InteractionKind::service_response) {
    source = EndpointDirection::respond;
    destination = EndpointDirection::request;
  }
  return *CommunicationContract::create({"contract.main", "1.0.0", "interface.main",
                                         "schema.main", "1.0.0", kind, source,
                                         destination})
              .value();
}

[[nodiscard]] EndpointSpec endpoint(const char* identity, const EndpointDirection direction,
                                    const CommunicationContract& value) {
  return *EndpointSpec::create(
              {identity,
               "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
               "provider.main", direction},
              value)
              .value();
}

[[nodiscard]] RouteSpec route(const char* identity, const EndpointSpec& source,
                              const EndpointSpec& destination) {
  return *RouteSpec::create(
              {identity,
               "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
               "provider.main"},
              source, destination)
              .value();
}

[[nodiscard]] FlowPolicy flow_policy(const OrderingPolicy ordering = OrderingPolicy::fifo,
                                     const ReliabilityPolicy reliability =
                                         ReliabilityPolicy::at_least_once,
                                     const OverflowPolicy overflow = OverflowPolicy::reject,
                                     const std::int64_t deadline = 100,
                                     const std::int64_t retry = 2,
                                     const std::int64_t queue_depth = 8) {
  return *FlowPolicy::create({ordering, reliability, overflow, deadline, retry, queue_depth})
              .value();
}

[[nodiscard]] RouteSpec policy_route(const char* identity, const EndpointSpec& source,
                                     const EndpointSpec& destination, const FlowPolicy& policy) {
  return *RouteSpec::create(
              {identity,
               "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
               "provider.main"},
              source, destination, policy)
              .value();
}

[[nodiscard]] LifecycleConfiguration configuration(const std::size_t endpoints = 4U,
                                                   const std::size_t routes = 2U) {
  return *LifecycleConfiguration::create({endpoints, routes}).value();
}

[[nodiscard]] bool operation_succeeds(const LifecycleState initial,
                                      const Operation operation) noexcept {
  switch (operation) {
    case Operation::validate:
      return initial == LifecycleState::declared || initial == LifecycleState::validated;
    case Operation::activate:
      return initial == LifecycleState::validated || initial == LifecycleState::active;
    case Operation::drain:
      return initial == LifecycleState::active || initial == LifecycleState::draining;
    case Operation::fail:
      return initial != LifecycleState::closed;
    case Operation::close:
      return initial == LifecycleState::draining || initial == LifecycleState::failed ||
             initial == LifecycleState::closed;
  }
  return false;
}

[[nodiscard]] LifecycleState resulting_state(const LifecycleState initial,
                                             const Operation operation) noexcept {
  switch (operation) {
    case Operation::validate:
      return LifecycleState::validated;
    case Operation::activate:
      return LifecycleState::active;
    case Operation::drain:
      return LifecycleState::draining;
    case Operation::fail:
      return LifecycleState::failed;
    case Operation::close:
      return LifecycleState::closed;
  }
  return initial;
}

[[nodiscard]] bool prepare_endpoint_state(LifecycleController& controller,
                                          const EndpointHandle& handle,
                                          const LifecycleState state) {
  if (state == LifecycleState::declared) {
    return true;
  }
  if (state == LifecycleState::failed || state == LifecycleState::closed) {
    if (!controller.fail_endpoint(handle).has_value()) {
      return false;
    }
    return state == LifecycleState::failed || controller.close_endpoint(handle).has_value();
  }
  if (!controller.validate_endpoint(handle).has_value()) {
    return false;
  }
  if (state == LifecycleState::validated) {
    return true;
  }
  if (!controller.activate_endpoint(handle).has_value()) {
    return false;
  }
  return state == LifecycleState::active || controller.drain_endpoint(handle).has_value();
}

[[nodiscard]] Result<LifecycleSnapshot> invoke_endpoint_operation(
    LifecycleController& controller, const EndpointHandle& handle, const Operation operation) {
  switch (operation) {
    case Operation::validate:
      return controller.validate_endpoint(handle);
    case Operation::activate:
      return controller.activate_endpoint(handle);
    case Operation::drain:
      return controller.drain_endpoint(handle);
    case Operation::fail:
      return controller.fail_endpoint(handle);
    case Operation::close:
      return controller.close_endpoint(handle);
  }
  return controller.endpoint_snapshot(handle);
}

[[nodiscard]] bool prepare_route_state(LifecycleController& controller,
                                       const RouteHandle& route_handle,
                                       const EndpointHandle& source_handle,
                                       const EndpointHandle& destination_handle,
                                       const LifecycleState state) {
  if (state == LifecycleState::declared) {
    return true;
  }
  if (state == LifecycleState::failed || state == LifecycleState::closed) {
    if (!controller.fail_route(route_handle).has_value()) {
      return false;
    }
    return state == LifecycleState::failed || controller.close_route(route_handle).has_value();
  }
  if (!controller
           .validate_route(route_handle, source_handle, destination_handle)
           .has_value()) {
    return false;
  }
  if (state == LifecycleState::validated) {
    return true;
  }
  if (!controller
           .activate_route(route_handle, source_handle, destination_handle)
           .has_value()) {
    return false;
  }
  return state == LifecycleState::active || controller.drain_route(route_handle).has_value();
}

[[nodiscard]] Result<LifecycleSnapshot> invoke_route_operation(
    LifecycleController& controller, const RouteHandle& route_handle,
    const EndpointHandle& source_handle, const EndpointHandle& destination_handle,
    const Operation operation) {
  switch (operation) {
    case Operation::validate:
      return controller.validate_route(route_handle, source_handle, destination_handle);
    case Operation::activate:
      return controller.activate_route(route_handle, source_handle, destination_handle);
    case Operation::drain:
      return controller.drain_route(route_handle);
    case Operation::fail:
      return controller.fail_route(route_handle);
    case Operation::close:
      return controller.close_route(route_handle);
  }
  return controller.route_snapshot(route_handle);
}

[[nodiscard]] bool test_interaction_tables() {
  constexpr std::array kinds{InteractionKind::signal_state_update,
                             InteractionKind::message_event,
                             InteractionKind::service_request,
                             InteractionKind::service_response};
  for (const InteractionKind kind : kinds) {
    const auto communication = contract(kind);
    const auto source = endpoint("endpoint.source", communication.source_direction(), communication);
    const auto destination =
        endpoint("endpoint.destination", communication.target_direction(), communication);
    const auto route_spec = route("route.main", source, destination);
    LifecycleController controller(configuration());
    const auto source_handle = controller.declare_endpoint(source);
    const auto destination_handle = controller.declare_endpoint(destination);
    const auto route_handle = controller.declare_route(route_spec);
    if (!expect(source_handle.has_value() && destination_handle.has_value() &&
                    route_handle.has_value(),
                "valid declarations failed") ||
        !expect(controller.validate_endpoint(*source_handle.value()).has_value() &&
                    controller.validate_endpoint(*destination_handle.value()).has_value(),
                "endpoint validation failed") ||
        !expect(controller.validate_route(*route_handle.value(), *source_handle.value(),
                                          *destination_handle.value())
                    .has_value(),
                "route validation failed") ||
        !expect(controller.activate_endpoint(*source_handle.value()).has_value() &&
                    controller.activate_endpoint(*destination_handle.value()).has_value(),
                "endpoint activation failed") ||
        !expect(controller.activate_route(*route_handle.value(), *source_handle.value(),
                                          *destination_handle.value())
                    .has_value(),
                "route activation failed")) {
      return false;
    }
  }
  return true;
}

[[nodiscard]] bool test_state_table_and_idempotence() {
  const auto communication = contract(InteractionKind::message_event);
  const auto spec = endpoint("endpoint.single", EndpointDirection::produce, communication);
  LifecycleController controller(configuration(1U, 1U));
  const auto handle = controller.declare_endpoint(spec);
  if (!handle.has_value() || handle.value()->generation() == 0U ||
      handle.value()->kind() != ResourceKind::endpoint) {
    return expect(false, "endpoint handle binding differs");
  }
  const auto declared = controller.endpoint_snapshot(*handle.value());
  const auto validated = controller.validate_endpoint(*handle.value());
  const auto validated_repeat = controller.validate_endpoint(*handle.value());
  const auto active = controller.activate_endpoint(*handle.value());
  const auto active_repeat = controller.activate_endpoint(*handle.value());
  const auto draining = controller.drain_endpoint(*handle.value());
  const auto draining_repeat = controller.drain_endpoint(*handle.value());
  const auto closed = controller.close_endpoint(*handle.value());
  const auto closed_repeat = controller.close_endpoint(*handle.value());
  return expect(declared.has_value() && declared.value()->state() == LifecycleState::declared,
                "declared snapshot differs") &&
         expect(validated.has_value() && validated_repeat.has_value() &&
                    validated.value()->state() == LifecycleState::validated &&
                    validated.value()->generation() == validated_repeat.value()->generation(),
                "validate idempotence differs") &&
         expect(active.has_value() && active_repeat.has_value() &&
                    active.value()->state() == LifecycleState::active,
                "activate idempotence differs") &&
         expect(draining.has_value() && draining_repeat.has_value() &&
                    draining.value()->state() == LifecycleState::draining,
                "drain idempotence differs") &&
         expect(closed.has_value() && closed_repeat.has_value() &&
                    closed.value()->state() == LifecycleState::closed,
                "close idempotence differs");
}

[[nodiscard]] bool test_complete_endpoint_transition_table() {
  const auto communication = contract(InteractionKind::message_event);
  const auto spec = endpoint("endpoint.matrix", EndpointDirection::produce, communication);
  for (const LifecycleState initial : kStates) {
    for (const Operation operation : kOperations) {
      LifecycleController controller(configuration(1U, 1U));
      const auto handle = controller.declare_endpoint(spec);
      if (!handle.has_value() ||
          !prepare_endpoint_state(controller, *handle.value(), initial)) {
        return expect(false, "endpoint transition matrix setup failed");
      }
      const auto before = controller.endpoint_snapshot(*handle.value());
      const auto result =
          invoke_endpoint_operation(controller, *handle.value(), operation);
      const auto after = controller.endpoint_snapshot(*handle.value());
      if (operation_succeeds(initial, operation)) {
        if (!expect(result.has_value() && after.has_value() &&
                        result.value()->state() == resulting_state(initial, operation) &&
                        result.value()->generation() == before.value()->generation(),
                    "permitted endpoint transition or idempotent repeat failed")) {
          return false;
        }
      } else if (!expect(!result.has_value() && result.diagnostics() != nullptr &&
                             result.diagnostics()->values().front().code() ==
                                 DiagnosticCode::invalid_transition &&
                             before.has_value() && after.has_value() &&
                             *before.value() == *after.value(),
                         "rejected endpoint transition changed state or diagnostics")) {
        return false;
      }
    }
  }
  return true;
}

[[nodiscard]] bool test_complete_route_transition_table() {
  const auto communication = contract(InteractionKind::message_event);
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto route_spec = route("route.matrix", source, destination);
  for (const LifecycleState initial : kStates) {
    for (const Operation operation : kOperations) {
      LifecycleController controller(configuration(2U, 1U));
      const auto source_handle = controller.declare_endpoint(source);
      const auto destination_handle = controller.declare_endpoint(destination);
      const auto route_handle = controller.declare_route(route_spec);
      if (!source_handle.has_value() || !destination_handle.has_value() ||
          !route_handle.has_value() ||
          !controller.validate_endpoint(*source_handle.value()).has_value() ||
          !controller.validate_endpoint(*destination_handle.value()).has_value() ||
          !controller.activate_endpoint(*source_handle.value()).has_value() ||
          !controller.activate_endpoint(*destination_handle.value()).has_value() ||
          !prepare_route_state(controller, *route_handle.value(), *source_handle.value(),
                               *destination_handle.value(), initial)) {
        return expect(false, "route transition matrix setup failed");
      }
      const auto before = controller.route_snapshot(*route_handle.value());
      const auto result = invoke_route_operation(
          controller, *route_handle.value(), *source_handle.value(),
          *destination_handle.value(), operation);
      const auto after = controller.route_snapshot(*route_handle.value());
      if (operation_succeeds(initial, operation)) {
        if (!expect(result.has_value() && after.has_value() &&
                        result.value()->state() == resulting_state(initial, operation) &&
                        result.value()->generation() == before.value()->generation(),
                    "permitted route transition or idempotent repeat failed")) {
          return false;
        }
      } else if (!expect(!result.has_value() && result.diagnostics() != nullptr &&
                             result.diagnostics()->values().front().code() ==
                                 DiagnosticCode::invalid_transition &&
                             before.has_value() && after.has_value() &&
                             *before.value() == *after.value(),
                         "rejected route transition changed state or diagnostics")) {
        return false;
      }
    }
  }
  return true;
}

[[nodiscard]] bool test_failure_and_recreation() {
  const auto communication = contract(InteractionKind::signal_state_update);
  const auto spec = endpoint("endpoint.reused", EndpointDirection::produce, communication);
  LifecycleController controller(configuration(1U, 1U));
  const auto first = controller.declare_endpoint(spec);
  if (!first.has_value() || !controller.fail_endpoint(*first.value()).has_value() ||
      !controller.fail_endpoint(*first.value()).has_value() ||
      !controller.close_endpoint(*first.value()).has_value()) {
    return expect(false, "failure cleanup failed");
  }
  const auto second = controller.declare_endpoint(spec);
  if (!expect(second.has_value() &&
                  second.value()->generation() > first.value()->generation(),
              "recreation did not advance generation")) {
    return false;
  }
  const auto stale = controller.endpoint_snapshot(*first.value());
  return expect(!stale.has_value() && stale.diagnostics() != nullptr &&
                    stale.diagnostics()->values().front().code() ==
                        DiagnosticCode::invalid_handle,
                "old generation was not rejected");
}

[[nodiscard]] bool test_fixed_capacity_and_isolation() {
  const auto communication = contract(InteractionKind::message_event);
  const auto first_spec = endpoint("endpoint.one", EndpointDirection::produce, communication);
  const auto second_spec = endpoint("endpoint.two", EndpointDirection::consume, communication);
  LifecycleController controller(configuration(1U, 1U));
  const auto first = controller.declare_endpoint(first_spec);
  const auto before = controller.endpoint_snapshot(*first.value());
  const auto overflow = controller.declare_endpoint(second_spec);
  const auto duplicate = controller.declare_endpoint(first_spec);
  const auto after = controller.endpoint_snapshot(*first.value());
  return expect(controller.endpoint_capacity() == 1U && first.has_value(),
                "configured endpoint capacity differs") &&
         expect(!overflow.has_value() && overflow.diagnostics()->values().front().code() ==
                                             DiagnosticCode::capacity_exhausted,
                "capacity exhaustion differs") &&
         expect(!duplicate.has_value() && duplicate.diagnostics()->values().front().code() ==
                                              DiagnosticCode::duplicate_identity,
                "duplicate live identity differs") &&
         expect(before.has_value() && after.has_value() && *before.value() == *after.value(),
                "rejected declaration mutated an unrelated resource");
}

[[nodiscard]] bool test_serialized_safe_repeat() {
  const auto communication = contract(InteractionKind::message_event);
  const auto spec = endpoint("endpoint.concurrent", EndpointDirection::produce, communication);
  LifecycleController controller(configuration(1U, 1U));
  const auto handle = controller.declare_endpoint(spec);
  if (!handle.has_value() || !controller.validate_endpoint(*handle.value()).has_value()) {
    return expect(false, "concurrency precondition failed");
  }
  std::atomic<unsigned int> failures{0U};
  std::array<std::thread, 8U> workers;
  for (std::thread& worker : workers) {
    worker = std::thread([&controller, &handle, &failures]() {
      for (std::size_t repeat = 0U; repeat < 100U; ++repeat) {
        if (!controller.activate_endpoint(*handle.value()).has_value()) {
          ++failures;
        }
      }
    });
  }
  for (std::thread& worker : workers) {
    worker.join();
  }
  const auto snapshot = controller.endpoint_snapshot(*handle.value());
  return expect(failures.load() == 0U && snapshot.has_value() &&
                    snapshot.value()->state() == LifecycleState::active,
                "serialized idempotent contention differs");
}

[[nodiscard]] bool test_maximum_escaped_diagnostic_ordering_keys() {
  for (const char escaped : std::array{'|', '\\'}) {
    const std::string affected(kMaximumIdentityBytes, escaped);
    const std::string reason(Diagnostic::kMaximumTextBytes, escaped);
    const std::string correction(Diagnostic::kMaximumTextBytes, escaped);
    const DiagnosticInput input{DiagnosticCode::generation_exhausted,
                                DiagnosticSeverity::information,
                                ValidationPhase::lifecycle_configuration,
                                affected, reason, correction};
    const auto diagnostic = Diagnostic::create(input);
    if (!expect(diagnostic.has_value(), "maximum escaped diagnostic was rejected")) {
      return false;
    }

    std::string expected;
    const auto append_escaped = [&expected](const std::string_view value) {
      for (const char character : value) {
        if (character == '\\' || character == '|') {
          expected.push_back('\\');
        }
        expected.push_back(character);
      }
    };
    append_escaped(to_string(input.phase));
    expected.push_back('|');
    append_escaped(to_string(input.severity));
    expected.push_back('|');
    append_escaped(to_string(input.code));
    expected.push_back('|');
    append_escaped(input.affected_identity);
    expected.push_back('|');
    append_escaped(input.reason);
    expected.push_back('|');
    append_escaped(input.correction);

    if (!expect(diagnostic->ordering_key() == expected,
                "maximum diagnostic escaping or serialization differs") ||
        !expect(diagnostic->ordering_key().size() <= Diagnostic::kMaximumOrderingKeyBytes,
                "maximum escaped diagnostic exceeds derived storage")) {
      return false;
    }
  }
  return true;
}

[[nodiscard]] bool test_route_declared_policy_binding() {
  const auto communication = contract(InteractionKind::message_event);
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto declared = flow_policy(OrderingPolicy::priority, ReliabilityPolicy::exactly_once,
                                    OverflowPolicy::lossless_backpressure, 1500, 5, 64);
  const auto bound = policy_route("route.bound", source, destination, declared);
  const auto unbound = route("route.unbound", source, destination);
  if (!expect(bound.has_policy() && bound.policy() != nullptr && *bound.policy() == declared,
              "declared route policy binding differs") ||
      !expect(!unbound.has_policy() && unbound.policy() == nullptr,
              "unbound route policy state differs")) {
    return false;
  }
  LifecycleController controller(configuration());
  const auto source_handle = controller.declare_endpoint(source);
  const auto destination_handle = controller.declare_endpoint(destination);
  const auto bound_handle = controller.declare_route(bound);
  const auto unbound_handle = controller.declare_route(unbound);
  if (!expect(source_handle.has_value() && destination_handle.has_value() &&
                  bound_handle.has_value() && unbound_handle.has_value(),
              "declared-policy route declarations failed")) {
    return false;
  }
  const auto bound_snapshot = controller.route_snapshot(*bound_handle.value());
  const auto unbound_snapshot = controller.route_snapshot(*unbound_handle.value());
  const auto bound_read = controller.route_policy(*bound_handle.value());
  const auto unbound_read = controller.route_policy(*unbound_handle.value());
  const auto bound_declaration = controller.route_declaration(*bound_handle.value());
  return expect(bound_snapshot.has_value() && bound_snapshot.value()->policy_bound(),
                "bound route snapshot policy flag differs") &&
         expect(unbound_snapshot.has_value() && !unbound_snapshot.value()->policy_bound(),
                "unbound route snapshot policy flag differs") &&
         expect(bound_read.has_value() && *bound_read.value() == declared &&
                    bound_read.value()->ordering() == OrderingPolicy::priority &&
                    bound_read.value()->reliability() == ReliabilityPolicy::exactly_once &&
                    bound_read.value()->overflow() == OverflowPolicy::lossless_backpressure &&
                    bound_read.value()->deadline_ms() == 1500 &&
                    bound_read.value()->retry() == 5 &&
                    bound_read.value()->queue_depth() == 64,
                "route_policy did not return the exact declared policy") &&
         expect(bound_declaration.has_value() && bound_declaration.value()->has_policy() &&
                    bound_declaration.value()->policy() != nullptr &&
                    *bound_declaration.value()->policy() == declared,
                "route declaration lost the declared policy") &&
         expect(!unbound_read.has_value() && unbound_read.diagnostics() != nullptr &&
                    unbound_read.diagnostics()->values().front().code() ==
                        DiagnosticCode::required_field,
                "unbound route_policy did not fail closed");
}

[[nodiscard]] bool test_route_policy_generation_binding() {
  const auto communication = contract(InteractionKind::message_event);
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto first_policy = flow_policy(OrderingPolicy::fifo, ReliabilityPolicy::at_least_once,
                                        OverflowPolicy::reject, 100, 2, 8);
  const auto second_policy =
      flow_policy(OrderingPolicy::unordered, ReliabilityPolicy::best_effort,
                  OverflowPolicy::drop_oldest, 0, 0, 1);
  LifecycleController controller(configuration());
  const auto source_handle = controller.declare_endpoint(source);
  const auto destination_handle = controller.declare_endpoint(destination);
  const auto first =
      controller.declare_route(policy_route("route.main", source, destination, first_policy));
  if (!expect(source_handle.has_value() && destination_handle.has_value() && first.has_value(),
              "first declared-policy route generation failed") ||
      !controller.fail_route(*first.value()).has_value() ||
      !controller.close_route(*first.value()).has_value()) {
    return false;
  }
  const auto second =
      controller.declare_route(policy_route("route.main", source, destination, second_policy));
  if (!expect(second.has_value() && second.value()->generation() > first.value()->generation(),
              "recreated policy route did not advance generation")) {
    return false;
  }
  const auto second_read = controller.route_policy(*second.value());
  const auto stale_read = controller.route_policy(*first.value());
  return expect(second_read.has_value() && *second_read.value() == second_policy,
                "new generation route_policy returned the wrong policy") &&
         expect(!stale_read.has_value() && stale_read.diagnostics() != nullptr &&
                    stale_read.diagnostics()->values().front().code() ==
                        DiagnosticCode::invalid_handle,
                "superseded generation route_policy was not rejected");
}

[[nodiscard]] bool test_route_policy_immutability() {
  const auto communication = contract(InteractionKind::message_event);
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto weaker = flow_policy(OrderingPolicy::fifo, ReliabilityPolicy::best_effort,
                                  OverflowPolicy::reject, 100, 0, 4);
  const auto stronger = flow_policy(OrderingPolicy::fifo, ReliabilityPolicy::exactly_once,
                                    OverflowPolicy::reject, 100, 8, 64);
  const auto route_a = policy_route("route.a", source, destination, weaker);
  const auto route_b = policy_route("route.b", source, destination, stronger);
  const RouteSpec copied = route_a;
  const auto unbound = route("route.c", source, destination);
  return expect(route_a != route_b, "routes differing only by declared policy compared equal") &&
         expect(copied == route_a && copied.has_policy() && copied.policy() != nullptr &&
                    *copied.policy() == weaker,
                "copied route did not preserve its declared policy") &&
         expect(!unbound.has_policy() && unbound.policy() == nullptr,
                "unbound route substituted a default policy");
}

[[nodiscard]] bool test_route_policy_concurrent_read() {
  const auto communication = contract(InteractionKind::message_event);
  const auto source = endpoint("endpoint.source", EndpointDirection::produce, communication);
  const auto destination =
      endpoint("endpoint.destination", EndpointDirection::consume, communication);
  const auto declared = flow_policy(OrderingPolicy::priority, ReliabilityPolicy::at_least_once,
                                    OverflowPolicy::coalesce, 250, 3, 16);
  LifecycleController controller(configuration());
  const auto source_handle = controller.declare_endpoint(source);
  const auto destination_handle = controller.declare_endpoint(destination);
  const auto handle = controller.declare_route(
      policy_route("route.concurrent", source, destination, declared));
  if (!expect(source_handle.has_value() && destination_handle.has_value() && handle.has_value(),
              "concurrent declared-policy fixture failed")) {
    return false;
  }
  std::atomic<unsigned int> failures{0U};
  std::array<std::thread, 8U> workers;
  for (std::thread& worker : workers) {
    worker = std::thread([&controller, &handle, &declared, &failures]() {
      for (std::size_t repeat = 0U; repeat < 100U; ++repeat) {
        const auto read = controller.route_policy(*handle.value());
        const auto snapshot = controller.route_snapshot(*handle.value());
        if (!read.has_value() || *read.value() != declared || !snapshot.has_value() ||
            !snapshot.value()->policy_bound()) {
          ++failures;
        }
      }
    });
  }
  for (std::thread& worker : workers) {
    worker.join();
  }
  return expect(failures.load() == 0U, "concurrent declared-policy read differs");
}

}  // namespace

/** @return Zero only when all lifecycle unit tests pass. */
int main() {
  return test_interaction_tables() && test_state_table_and_idempotence() &&
                 test_complete_endpoint_transition_table() &&
                 test_complete_route_transition_table() &&
                 test_failure_and_recreation() && test_fixed_capacity_and_isolation() &&
                 test_serialized_safe_repeat() &&
                 test_maximum_escaped_diagnostic_ordering_keys() &&
                 test_route_declared_policy_binding() && test_route_policy_generation_binding() &&
                 test_route_policy_immutability() && test_route_policy_concurrent_read()
             ? 0
             : 1;
}
