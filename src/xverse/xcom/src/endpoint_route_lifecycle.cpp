/**
 * @file endpoint_route_lifecycle.cpp
 * @brief Allocation-free declarations and serialized fixed-record lifecycle operations.
 * @ownership Accepted inputs are copied into values or controller-owned fixed records.
 * @lifetime No caller view or reference is retained after an operation returns.
 * @thread_safety Factories use local state; controller calls serialize on one mutex.
 * @failure Every rejection produces one stable diagnostic before any record mutation.
 */

#include "xverse/xcom/endpoint_route_lifecycle.hpp"

#include <atomic>
#include <limits>

namespace xverse::xcom {
namespace {

std::atomic<std::uint64_t> next_controller_id{1U};

/**
 * @brief Validate one exact lowercase hexadecimal plan digest.
 * @param digest Candidate digest bytes.
 * @return true only for the exact canonical digest form.
 */
[[nodiscard]] bool valid_digest(const std::string_view digest) noexcept {
  if (digest.size() != EndpointSpec::kPlanDigestBytes) {
    return false;
  }
  for (const char character : digest) {
    if (!((character >= '0' && character <= '9') ||
          (character >= 'a' && character <= 'f'))) {
      return false;
    }
  }
  return true;
}

/**
 * @brief Test whether an endpoint direction occurs in an exact contract.
 * @param direction Candidate endpoint direction.
 * @param contract Exact communication contract.
 * @return true for the declared source or target direction.
 */
[[nodiscard]] bool is_contract_direction(const EndpointDirection direction,
                                         const CommunicationContract& contract) noexcept {
  return direction == contract.source_direction() || direction == contract.target_direction();
}

/**
 * @brief Create one stable single-diagnostic failed result.
 * @tparam T Successful result type.
 * @param code Stable diagnostic code.
 * @param phase Stable validation phase.
 * @param affected Affected logical identity or field.
 * @param reason Deterministic rejection reason.
 * @param correction Deterministic correction.
 * @return Failed result containing exactly one diagnostic.
 */
template <typename T>
[[nodiscard]] Result<T> failure(const DiagnosticCode code, const ValidationPhase phase,
                                const std::string_view affected, const std::string_view reason,
                                const std::string_view correction) noexcept {
  const DiagnosticInput input{code, DiagnosticSeverity::error, phase, affected, reason, correction};
  const auto diagnostics = DiagnosticSet::create_from_inputs({&input, 1U});
  return Result<T>::failure(*diagnostics);
}

/**
 * @brief Return a stable invalid-handle failure for an affected handle.
 * @tparam ResultValue Successful result type.
 * @tparam Handle EndpointHandle or RouteHandle.
 * @param handle Rejected ownership handle.
 * @return Failed result containing one ownership diagnostic.
 */
template <typename ResultValue, typename Handle>
[[nodiscard]] Result<ResultValue> invalid_handle(const Handle& handle) noexcept {
  return failure<ResultValue>(
      DiagnosticCode::invalid_handle, ValidationPhase::ownership, handle.identity().value(),
      "handle does not identify the current resource owned by this controller",
      "use the exact handle issued for the current controller and generation");
}

/**
 * @brief Issue one process-local nonzero controller instance identity.
 * @return Nonzero identity monotonically issued until integer exhaustion.
 */
[[nodiscard]] std::uint64_t issue_controller_id() noexcept {
  std::uint64_t identifier = next_controller_id.fetch_add(1U, std::memory_order_relaxed);
  while (identifier == 0U) {
    identifier = next_controller_id.fetch_add(1U, std::memory_order_relaxed);
  }
  return identifier;
}

}  // namespace

std::string_view to_string(const ResourceKind kind) noexcept {
  switch (kind) {
    case ResourceKind::endpoint:
      return "endpoint";
    case ResourceKind::route:
      return "route";
  }
  return "unknown";
}

std::string_view to_string(const LifecycleState state) noexcept {
  switch (state) {
    case LifecycleState::declared:
      return "declared";
    case LifecycleState::validated:
      return "validated";
    case LifecycleState::active:
      return "active";
    case LifecycleState::draining:
      return "draining";
    case LifecycleState::failed:
      return "failed";
    case LifecycleState::closed:
      return "closed";
  }
  return "unknown";
}

EndpointSpec::EndpointSpec(const Identity& endpoint_id,
                           const detail::FixedText<kPlanDigestBytes>& plan_digest,
                           const Identity& provider_id, const EndpointDirection direction,
                           const CommunicationContract& contract) noexcept
    : endpoint_id_(endpoint_id),
      plan_digest_(plan_digest),
      provider_id_(provider_id),
      direction_(direction),
      contract_(contract) {}

Result<EndpointSpec> EndpointSpec::create(const EndpointSpecInput& input,
                                          const CommunicationContract& contract) noexcept {
  const auto endpoint_id = Identity::create(input.endpoint_id);
  if (!endpoint_id.has_value()) {
    return failure<EndpointSpec>(DiagnosticCode::required_field,
                                 ValidationPhase::endpoint_declaration, "endpoint_id",
                                 "endpoint identity is empty, malformed, or over bound",
                                 "provide a non-empty bounded logical endpoint identity");
  }
  if (!valid_digest(input.plan_digest)) {
    return failure<EndpointSpec>(DiagnosticCode::invalid_digest,
                                 ValidationPhase::endpoint_declaration, input.endpoint_id,
                                 "plan digest is not exactly 64 lowercase hexadecimal characters",
                                 "provide the exact canonical activation-plan digest");
  }
  const auto provider_id = Identity::create(input.provider_id);
  if (!provider_id.has_value()) {
    return failure<EndpointSpec>(DiagnosticCode::required_field,
                                 ValidationPhase::endpoint_declaration, "provider_id",
                                 "provider identity is empty, malformed, or over bound",
                                 "provide a non-empty bounded logical provider identity");
  }
  if (!is_contract_direction(input.direction, contract)) {
    return failure<EndpointSpec>(DiagnosticCode::incompatible_direction,
                                 ValidationPhase::endpoint_declaration, input.endpoint_id,
                                 "endpoint direction is not declared by the communication contract",
                                 "use the exact source or target direction from the contract");
  }
  detail::FixedText<kPlanDigestBytes> digest;
  static_cast<void>(digest.assign(input.plan_digest));
  return Result<EndpointSpec>::success(
      EndpointSpec(*endpoint_id, digest, *provider_id, input.direction, contract));
}

RouteSpec::RouteSpec(const Identity& route_id,
                     const detail::FixedText<EndpointSpec::kPlanDigestBytes>& digest,
                     const Identity& provider_id, const EndpointSpec& source,
                     const EndpointSpec& destination) noexcept
    : route_id_(route_id),
      plan_digest_(digest),
      provider_id_(provider_id),
      source_endpoint_id_(source.endpoint_id()),
      destination_endpoint_id_(destination.endpoint_id()),
      contract_(source.contract()) {}

Result<RouteSpec> RouteSpec::create(const RouteSpecInput& input, const EndpointSpec& source,
                                    const EndpointSpec& destination) noexcept {
  const auto route_id = Identity::create(input.route_id);
  if (!route_id.has_value()) {
    return failure<RouteSpec>(DiagnosticCode::required_field,
                              ValidationPhase::route_declaration, "route_id",
                              "route identity is empty, malformed, or over bound",
                              "provide a non-empty bounded logical route identity");
  }
  if (!valid_digest(input.plan_digest)) {
    return failure<RouteSpec>(DiagnosticCode::invalid_digest,
                              ValidationPhase::route_declaration, input.route_id,
                              "plan digest is not exactly 64 lowercase hexadecimal characters",
                              "provide the exact canonical activation-plan digest");
  }
  const auto provider_id = Identity::create(input.provider_id);
  if (!provider_id.has_value()) {
    return failure<RouteSpec>(DiagnosticCode::required_field,
                              ValidationPhase::route_declaration, "provider_id",
                              "provider identity is empty, malformed, or over bound",
                              "provide a non-empty bounded logical provider identity");
  }
  const bool compatible = source.endpoint_id() != destination.endpoint_id() &&
                          source.plan_digest() == input.plan_digest &&
                          destination.plan_digest() == input.plan_digest &&
                          source.provider_id() == *provider_id &&
                          destination.provider_id() == *provider_id &&
                          source.contract() == destination.contract() &&
                          source.direction() == source.contract().source_direction() &&
                          destination.direction() == source.contract().target_direction();
  if (!compatible) {
    return failure<RouteSpec>(DiagnosticCode::route_incompatible,
                              ValidationPhase::route_declaration, input.route_id,
                              "route endpoints differ in identity, plan, provider, contract, or direction",
                              "use distinct compatible endpoints from one exact plan and contract");
  }
  detail::FixedText<EndpointSpec::kPlanDigestBytes> digest;
  static_cast<void>(digest.assign(input.plan_digest));
  return Result<RouteSpec>::success(
      RouteSpec(*route_id, digest, *provider_id, source, destination));
}

Result<LifecycleConfiguration> LifecycleConfiguration::create(
    const LifecycleConfigurationInput& input) noexcept {
  if (input.endpoint_capacity == 0U ||
      input.endpoint_capacity > LifecycleController::kMaximumEndpoints) {
    return failure<LifecycleConfiguration>(
        DiagnosticCode::bound_exceeded, ValidationPhase::lifecycle_configuration,
        "endpoint_capacity", "endpoint capacity is zero or exceeds the compile-time maximum",
        "configure a finite endpoint capacity within the published maximum");
  }
  if (input.route_capacity == 0U || input.route_capacity > LifecycleController::kMaximumRoutes) {
    return failure<LifecycleConfiguration>(
        DiagnosticCode::bound_exceeded, ValidationPhase::lifecycle_configuration,
        "route_capacity", "route capacity is zero or exceeds the compile-time maximum",
        "configure a finite route capacity within the published maximum");
  }
  return Result<LifecycleConfiguration>::success(
      LifecycleConfiguration(input.endpoint_capacity, input.route_capacity));
}

EndpointHandle::EndpointHandle(const std::uint64_t controller_id, const Identity& identity,
                               const std::string_view plan_digest,
                               const std::uint64_t generation) noexcept
    : controller_id_(controller_id), identity_(identity), generation_(generation) {
  static_cast<void>(plan_digest_.assign(plan_digest));
}

RouteHandle::RouteHandle(const std::uint64_t controller_id, const Identity& identity,
                         const std::string_view plan_digest,
                         const std::uint64_t generation) noexcept
    : controller_id_(controller_id), identity_(identity), generation_(generation) {
  static_cast<void>(plan_digest_.assign(plan_digest));
}

LifecycleSnapshot::LifecycleSnapshot(const ResourceKind kind, const Identity& identity,
                                     const std::string_view digest,
                                     const std::uint64_t generation,
                                     const LifecycleState state) noexcept
    : kind_(kind), identity_(identity), generation_(generation), state_(state) {
  static_cast<void>(plan_digest_.assign(digest));
}

LifecycleController::LifecycleController(const LifecycleConfiguration& configuration) noexcept
    : controller_id_(issue_controller_id()),
      endpoint_capacity_(configuration.endpoint_capacity()),
      route_capacity_(configuration.route_capacity()) {}

Result<EndpointHandle> LifecycleController::declare_endpoint(const EndpointSpec& spec) noexcept {
  const std::lock_guard lock(mutex_);
  std::size_t reusable = endpoint_capacity_;
  for (std::size_t index = 0U; index < endpoint_capacity_; ++index) {
    if (!endpoints_[index].has_value()) {
      if (reusable == endpoint_capacity_) {
        reusable = index;
      }
      continue;
    }
    if (endpoints_[index]->state != LifecycleState::closed &&
        endpoints_[index]->spec.endpoint_id() == spec.endpoint_id()) {
      return failure<EndpointHandle>(DiagnosticCode::duplicate_identity,
                                     ValidationPhase::endpoint_declaration,
                                     spec.endpoint_id().value(),
                                     "a nonclosed endpoint already owns this logical identity",
                                     "close the current endpoint before recreating its identity");
    }
    if (endpoints_[index]->state == LifecycleState::closed &&
        (reusable == endpoint_capacity_ ||
         endpoints_[index]->spec.endpoint_id() == spec.endpoint_id())) {
      reusable = index;
      if (endpoints_[index]->spec.endpoint_id() == spec.endpoint_id()) {
        break;
      }
    }
  }
  if (reusable == endpoint_capacity_) {
    return failure<EndpointHandle>(DiagnosticCode::capacity_exhausted,
                                   ValidationPhase::endpoint_declaration,
                                   spec.endpoint_id().value(),
                                   "configured endpoint capacity is exhausted",
                                   "close an endpoint before declaring another resource");
  }
  if (next_generation_ == std::numeric_limits<std::uint64_t>::max()) {
    return failure<EndpointHandle>(DiagnosticCode::generation_exhausted,
                                   ValidationPhase::endpoint_declaration,
                                   spec.endpoint_id().value(),
                                   "controller generation space is exhausted",
                                   "replace the controller before declaring another resource");
  }
  const std::uint64_t generation = next_generation_;
  endpoints_[reusable].reset();
  endpoints_[reusable].emplace(spec, generation);
  ++next_generation_;
  return Result<EndpointHandle>::success(
      EndpointHandle(controller_id_, spec.endpoint_id(), spec.plan_digest(), generation));
}

Result<RouteHandle> LifecycleController::declare_route(const RouteSpec& spec) noexcept {
  const std::lock_guard lock(mutex_);
  std::size_t reusable = route_capacity_;
  for (std::size_t index = 0U; index < route_capacity_; ++index) {
    if (!routes_[index].has_value()) {
      if (reusable == route_capacity_) {
        reusable = index;
      }
      continue;
    }
    if (routes_[index]->state != LifecycleState::closed &&
        routes_[index]->spec.route_id() == spec.route_id()) {
      return failure<RouteHandle>(DiagnosticCode::duplicate_identity,
                                  ValidationPhase::route_declaration, spec.route_id().value(),
                                  "a nonclosed route already owns this logical identity",
                                  "close the current route before recreating its identity");
    }
    if (routes_[index]->state == LifecycleState::closed &&
        (reusable == route_capacity_ || routes_[index]->spec.route_id() == spec.route_id())) {
      reusable = index;
      if (routes_[index]->spec.route_id() == spec.route_id()) {
        break;
      }
    }
  }
  if (reusable == route_capacity_) {
    return failure<RouteHandle>(DiagnosticCode::capacity_exhausted,
                                ValidationPhase::route_declaration, spec.route_id().value(),
                                "configured route capacity is exhausted",
                                "close a route before declaring another resource");
  }
  if (next_generation_ == std::numeric_limits<std::uint64_t>::max()) {
    return failure<RouteHandle>(DiagnosticCode::generation_exhausted,
                                ValidationPhase::route_declaration, spec.route_id().value(),
                                "controller generation space is exhausted",
                                "replace the controller before declaring another resource");
  }
  const std::uint64_t generation = next_generation_;
  routes_[reusable].reset();
  routes_[reusable].emplace(spec, generation);
  ++next_generation_;
  return Result<RouteHandle>::success(
      RouteHandle(controller_id_, spec.route_id(), spec.plan_digest(), generation));
}

LifecycleController::EndpointRecord* LifecycleController::authenticate_endpoint(
    const EndpointHandle& handle) noexcept {
  if (handle.controller_id() != controller_id_ || handle.kind() != ResourceKind::endpoint) {
    return nullptr;
  }
  for (std::size_t index = 0U; index < endpoint_capacity_; ++index) {
    if (endpoints_[index].has_value() &&
        endpoints_[index]->spec.endpoint_id() == handle.identity() &&
        endpoints_[index]->spec.plan_digest() == handle.plan_digest() &&
        endpoints_[index]->generation == handle.generation()) {
      return &*endpoints_[index];
    }
  }
  return nullptr;
}

const LifecycleController::EndpointRecord* LifecycleController::authenticate_endpoint(
    const EndpointHandle& handle) const noexcept {
  return const_cast<LifecycleController*>(this)->authenticate_endpoint(handle);
}

LifecycleController::RouteRecord* LifecycleController::authenticate_route(
    const RouteHandle& handle) noexcept {
  if (handle.controller_id() != controller_id_ || handle.kind() != ResourceKind::route) {
    return nullptr;
  }
  for (std::size_t index = 0U; index < route_capacity_; ++index) {
    if (routes_[index].has_value() && routes_[index]->spec.route_id() == handle.identity() &&
        routes_[index]->spec.plan_digest() == handle.plan_digest() &&
        routes_[index]->generation == handle.generation()) {
      return &*routes_[index];
    }
  }
  return nullptr;
}

const LifecycleController::RouteRecord* LifecycleController::authenticate_route(
    const RouteHandle& handle) const noexcept {
  return const_cast<LifecycleController*>(this)->authenticate_route(handle);
}

bool LifecycleController::endpoint_in_use(const std::string_view endpoint_id) const noexcept {
  for (std::size_t index = 0U; index < route_capacity_; ++index) {
    if (routes_[index].has_value() && routes_[index]->state != LifecycleState::closed &&
        (routes_[index]->spec.source_endpoint_id().value() == endpoint_id ||
         routes_[index]->spec.destination_endpoint_id().value() == endpoint_id)) {
      return true;
    }
  }
  return false;
}

Result<LifecycleSnapshot> LifecycleController::endpoint_snapshot(
    const EndpointHandle& handle) const noexcept {
  const std::lock_guard lock(mutex_);
  const EndpointRecord* record = authenticate_endpoint(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  return Result<LifecycleSnapshot>::success(LifecycleSnapshot(
      ResourceKind::endpoint, record->spec.endpoint_id(), record->spec.plan_digest(),
      record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::route_snapshot(
    const RouteHandle& handle) const noexcept {
  const std::lock_guard lock(mutex_);
  const RouteRecord* record = authenticate_route(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  return Result<LifecycleSnapshot>::success(
      LifecycleSnapshot(ResourceKind::route, record->spec.route_id(), record->spec.plan_digest(),
                        record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::validate_endpoint(
    const EndpointHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  EndpointRecord* record = authenticate_endpoint(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::declared) {
    record->state = LifecycleState::validated;
  } else if (record->state != LifecycleState::validated) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.endpoint_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(LifecycleSnapshot(
      ResourceKind::endpoint, record->spec.endpoint_id(), record->spec.plan_digest(),
      record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::activate_endpoint(
    const EndpointHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  EndpointRecord* record = authenticate_endpoint(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::validated) {
    record->state = LifecycleState::active;
  } else if (record->state != LifecycleState::active) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.endpoint_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(LifecycleSnapshot(
      ResourceKind::endpoint, record->spec.endpoint_id(), record->spec.plan_digest(),
      record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::drain_endpoint(
    const EndpointHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  EndpointRecord* record = authenticate_endpoint(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::active) {
    if (endpoint_in_use(record->spec.endpoint_id().value())) {
      return failure<LifecycleSnapshot>(DiagnosticCode::endpoint_in_use,
                                        ValidationPhase::lifecycle,
                                        record->spec.endpoint_id().value(),
                                        "a nonclosed route still uses this endpoint generation",
                                        "close every using route before draining the endpoint");
    }
    record->state = LifecycleState::draining;
  } else if (record->state != LifecycleState::draining) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.endpoint_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(LifecycleSnapshot(
      ResourceKind::endpoint, record->spec.endpoint_id(), record->spec.plan_digest(),
      record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::fail_endpoint(
    const EndpointHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  EndpointRecord* record = authenticate_endpoint(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::declared || record->state == LifecycleState::validated ||
      record->state == LifecycleState::active || record->state == LifecycleState::draining) {
    record->state = LifecycleState::failed;
  } else if (record->state != LifecycleState::failed) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.endpoint_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(LifecycleSnapshot(
      ResourceKind::endpoint, record->spec.endpoint_id(), record->spec.plan_digest(),
      record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::close_endpoint(
    const EndpointHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  EndpointRecord* record = authenticate_endpoint(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::draining || record->state == LifecycleState::failed) {
    if (endpoint_in_use(record->spec.endpoint_id().value())) {
      return failure<LifecycleSnapshot>(DiagnosticCode::endpoint_in_use,
                                        ValidationPhase::lifecycle,
                                        record->spec.endpoint_id().value(),
                                        "a nonclosed route still uses this endpoint generation",
                                        "close every using route before closing the endpoint");
    }
    record->state = LifecycleState::closed;
  } else if (record->state != LifecycleState::closed) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.endpoint_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(LifecycleSnapshot(
      ResourceKind::endpoint, record->spec.endpoint_id(), record->spec.plan_digest(),
      record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::validate_route(
    const RouteHandle& handle, const EndpointHandle& source,
    const EndpointHandle& destination) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* route = authenticate_route(handle);
  EndpointRecord* source_record = authenticate_endpoint(source);
  EndpointRecord* destination_record = authenticate_endpoint(destination);
  if (route == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (source_record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(source);
  }
  if (destination_record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(destination);
  }
  const bool compatible =
      route->spec.source_endpoint_id() == source_record->spec.endpoint_id() &&
      route->spec.destination_endpoint_id() == destination_record->spec.endpoint_id() &&
      route->spec.plan_digest() == source_record->spec.plan_digest() &&
      route->spec.plan_digest() == destination_record->spec.plan_digest() &&
      route->spec.provider_id() == source_record->spec.provider_id() &&
      route->spec.provider_id() == destination_record->spec.provider_id() &&
      route->spec.contract() == source_record->spec.contract() &&
      route->spec.contract() == destination_record->spec.contract() &&
      source_record->spec.direction() == route->spec.contract().source_direction() &&
      destination_record->spec.direction() == route->spec.contract().target_direction() &&
      (source_record->state == LifecycleState::validated ||
       source_record->state == LifecycleState::active) &&
      (destination_record->state == LifecycleState::validated ||
       destination_record->state == LifecycleState::active);
  if (!compatible) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::route_incompatible, ValidationPhase::route_compatibility,
        route->spec.route_id().value(),
        "route endpoints, contract, plan, provider, directions, or lifecycle states differ",
        "supply the exact current compatible validated endpoint handles");
  }
  if (route->state == LifecycleState::declared) {
    route->state = LifecycleState::validated;
  } else if (route->state != LifecycleState::validated) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        route->spec.route_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(
      LifecycleSnapshot(ResourceKind::route, route->spec.route_id(), route->spec.plan_digest(),
                        route->generation, route->state));
}

Result<LifecycleSnapshot> LifecycleController::activate_route(
    const RouteHandle& handle, const EndpointHandle& source,
    const EndpointHandle& destination) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* route = authenticate_route(handle);
  EndpointRecord* source_record = authenticate_endpoint(source);
  EndpointRecord* destination_record = authenticate_endpoint(destination);
  if (route == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (source_record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(source);
  }
  if (destination_record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(destination);
  }
  const bool compatible =
      route->spec.source_endpoint_id() == source_record->spec.endpoint_id() &&
      route->spec.destination_endpoint_id() == destination_record->spec.endpoint_id() &&
      route->spec.plan_digest() == source_record->spec.plan_digest() &&
      route->spec.plan_digest() == destination_record->spec.plan_digest() &&
      route->spec.provider_id() == source_record->spec.provider_id() &&
      route->spec.provider_id() == destination_record->spec.provider_id() &&
      route->spec.contract() == source_record->spec.contract() &&
      route->spec.contract() == destination_record->spec.contract() &&
      source_record->spec.direction() == route->spec.contract().source_direction() &&
      destination_record->spec.direction() == route->spec.contract().target_direction() &&
      source_record->state == LifecycleState::active &&
      destination_record->state == LifecycleState::active;
  if (!compatible) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::route_incompatible, ValidationPhase::route_compatibility,
        route->spec.route_id().value(),
        "route activation requires both exact compatible endpoints to be active",
        "activate the exact current source and destination endpoint handles");
  }
  if (route->state == LifecycleState::validated) {
    route->state = LifecycleState::active;
  } else if (route->state != LifecycleState::active) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        route->spec.route_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(
      LifecycleSnapshot(ResourceKind::route, route->spec.route_id(), route->spec.plan_digest(),
                        route->generation, route->state));
}

Result<LifecycleSnapshot> LifecycleController::drain_route(const RouteHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate_route(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::active) {
    record->state = LifecycleState::draining;
  } else if (record->state != LifecycleState::draining) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.route_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(
      LifecycleSnapshot(ResourceKind::route, record->spec.route_id(), record->spec.plan_digest(),
                        record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::fail_route(const RouteHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate_route(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::declared || record->state == LifecycleState::validated ||
      record->state == LifecycleState::active || record->state == LifecycleState::draining) {
    record->state = LifecycleState::failed;
  } else if (record->state != LifecycleState::failed) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.route_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(
      LifecycleSnapshot(ResourceKind::route, record->spec.route_id(), record->spec.plan_digest(),
                        record->generation, record->state));
}

Result<LifecycleSnapshot> LifecycleController::close_route(const RouteHandle& handle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate_route(handle);
  if (record == nullptr) {
    return invalid_handle<LifecycleSnapshot>(handle);
  }
  if (record->state == LifecycleState::draining || record->state == LifecycleState::failed) {
    record->state = LifecycleState::closed;
  } else if (record->state != LifecycleState::closed) {
    return failure<LifecycleSnapshot>(
        DiagnosticCode::invalid_transition, ValidationPhase::lifecycle,
        record->spec.route_id().value(),
        "requested lifecycle transition is not permitted from the current state",
        "follow the declared lifecycle transition sequence");
  }
  return Result<LifecycleSnapshot>::success(
      LifecycleSnapshot(ResourceKind::route, record->spec.route_id(), record->spec.plan_digest(),
                        record->generation, record->state));
}

}  // namespace xverse::xcom
