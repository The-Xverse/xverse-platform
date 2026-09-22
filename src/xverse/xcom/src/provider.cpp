/**
 * @file provider.cpp
 * @brief Allocation-free descriptor validation and explicit provider dispatch.
 * @ownership Accepted descriptors, registrations, bindings, and results are copied by value.
 * @lifetime The registry retains caller-owned provider addresses until registry destruction.
 * @thread_safety Registry access is serialized; virtual provider calls occur after mutex release.
 * @failure Compatibility and lifecycle rejection occurs before provider preparation.
 */

#include "xverse/xcom/provider.hpp"

#include <array>
#include <atomic>
#include <limits>
#include <span>

namespace xverse::xcom {
namespace {

constexpr std::uint8_t kKnownInteractionMask = 0x0FU;
constexpr std::uint8_t kKnownDeliveryMask = 0x03U;
constexpr std::uint8_t kKnownOrderingMask = 0x03U;
constexpr std::size_t kMaximumDeclaredRoutes = 32U;
constexpr std::size_t kMaximumDeclaredQueueItems = 32U;
constexpr std::string_view kProviderContractVersion = "1.0.0";
std::atomic<std::uint64_t> next_composition_instance{1U};

/** Create one deterministic descriptor failure. */
[[nodiscard]] Result<ProviderDescriptor> descriptor_failure(
    const DiagnosticCode code, const std::string_view field, const std::string_view reason,
    const std::string_view correction) noexcept {
  const std::array<DiagnosticInput, 1U> inputs{{
      {code, DiagnosticSeverity::error, ValidationPhase::contract, field, reason, correction},
  }};
  const auto diagnostics = DiagnosticSet::create_from_inputs(inputs);
  return Result<ProviderDescriptor>::failure(*diagnostics);
}

/** Return true only for a declared delivery enumeration. */
[[nodiscard]] bool known_delivery(const DeliveryCapability capability) noexcept {
  return capability == DeliveryCapability::best_effort ||
         capability == DeliveryCapability::reliable;
}

/** Return true only for a declared ordering enumeration. */
[[nodiscard]] bool known_ordering(const OrderingCapability capability) noexcept {
  return capability == OrderingCapability::unordered ||
         capability == OrderingCapability::per_route_fifo;
}

/** Return true only for endpoint states permitted during route preparation. */
[[nodiscard]] bool preparable_endpoint_state(const LifecycleState state) noexcept {
  return state == LifecycleState::validated || state == LifecycleState::active;
}

}  // namespace

std::string_view to_string(const ProviderOutcome outcome) noexcept {
  switch (outcome) {
    case ProviderOutcome::registered: return "registered";
    case ProviderOutcome::prepared: return "prepared";
    case ProviderOutcome::activated: return "activated";
    case ProviderOutcome::accepted: return "accepted";
    case ProviderOutcome::received: return "received";
    case ProviderOutcome::draining: return "draining";
    case ProviderOutcome::closed: return "closed";
    case ProviderOutcome::reconciled: return "reconciled";
    case ProviderOutcome::queue_empty: return "queue-empty";
    case ProviderOutcome::queue_saturated: return "queue-saturated";
    case ProviderOutcome::invalid_descriptor: return "invalid-descriptor";
    case ProviderOutcome::duplicate_provider: return "duplicate-provider";
    case ProviderOutcome::provider_capacity_exhausted: return "provider-capacity-exhausted";
    case ProviderOutcome::unsupported_contract_version: return "unsupported-contract-version";
    case ProviderOutcome::unsupported_interaction: return "unsupported-interaction";
    case ProviderOutcome::unsupported_delivery: return "unsupported-delivery";
    case ProviderOutcome::unsupported_ordering: return "unsupported-ordering";
    case ProviderOutcome::payload_limit_exceeded: return "payload-limit-exceeded";
    case ProviderOutcome::queue_limit_exceeded: return "queue-limit-exceeded";
    case ProviderOutcome::route_capacity_exhausted: return "route-capacity-exhausted";
    case ProviderOutcome::invalid_provider_route_handle: return "invalid-provider-route-handle";
    case ProviderOutcome::lifecycle_mismatch: return "lifecycle-mismatch";
    case ProviderOutcome::inactive_route: return "inactive-route";
    case ProviderOutcome::route_mismatch: return "route-mismatch";
    case ProviderOutcome::provider_mismatch: return "provider-mismatch";
    case ProviderOutcome::item_mismatch: return "item-mismatch";
    case ProviderOutcome::queued_items_remain: return "queued-items-remain";
    case ProviderOutcome::interrupted_resource: return "interrupted-resource";
  }
  return "unknown";
}

std::string_view provider_diagnostic_code(const ProviderOutcome outcome) noexcept {
  switch (outcome) {
    case ProviderOutcome::registered: return "XCOM-PROV-S001";
    case ProviderOutcome::prepared: return "XCOM-PROV-S002";
    case ProviderOutcome::activated: return "XCOM-PROV-S003";
    case ProviderOutcome::accepted: return "XCOM-PROV-S004";
    case ProviderOutcome::received: return "XCOM-PROV-S005";
    case ProviderOutcome::draining: return "XCOM-PROV-S006";
    case ProviderOutcome::closed: return "XCOM-PROV-S007";
    case ProviderOutcome::reconciled: return "XCOM-PROV-S008";
    case ProviderOutcome::queue_empty: return "XCOM-PROV-I009";
    case ProviderOutcome::queue_saturated: return "XCOM-PROV-E010";
    case ProviderOutcome::invalid_descriptor: return "XCOM-PROV-E011";
    case ProviderOutcome::duplicate_provider: return "XCOM-PROV-E012";
    case ProviderOutcome::provider_capacity_exhausted: return "XCOM-PROV-E013";
    case ProviderOutcome::unsupported_contract_version: return "XCOM-PROV-E014";
    case ProviderOutcome::unsupported_interaction: return "XCOM-PROV-E015";
    case ProviderOutcome::unsupported_delivery: return "XCOM-PROV-E016";
    case ProviderOutcome::unsupported_ordering: return "XCOM-PROV-E017";
    case ProviderOutcome::payload_limit_exceeded: return "XCOM-PROV-E018";
    case ProviderOutcome::queue_limit_exceeded: return "XCOM-PROV-E019";
    case ProviderOutcome::route_capacity_exhausted: return "XCOM-PROV-E020";
    case ProviderOutcome::invalid_provider_route_handle: return "XCOM-PROV-E021";
    case ProviderOutcome::lifecycle_mismatch: return "XCOM-PROV-E022";
    case ProviderOutcome::inactive_route: return "XCOM-PROV-E023";
    case ProviderOutcome::route_mismatch: return "XCOM-PROV-E024";
    case ProviderOutcome::provider_mismatch: return "XCOM-PROV-E025";
    case ProviderOutcome::item_mismatch: return "XCOM-PROV-E026";
    case ProviderOutcome::queued_items_remain: return "XCOM-PROV-E027";
    case ProviderOutcome::interrupted_resource: return "XCOM-PROV-E028";
  }
  return "XCOM-PROV-E000";
}

std::string_view provider_diagnostic_message(const ProviderOutcome outcome) noexcept {
  switch (outcome) {
    case ProviderOutcome::registered: return "explicit source-linked provider registered";
    case ProviderOutcome::prepared: return "exact provider route prepared without traffic";
    case ProviderOutcome::activated: return "exact provider route activated";
    case ProviderOutcome::accepted: return "item copied into bounded provider queue";
    case ProviderOutcome::received: return "oldest queued item returned by value";
    case ProviderOutcome::draining: return "new submissions stopped; queued items retained";
    case ProviderOutcome::closed: return "empty provider route resource released";
    case ProviderOutcome::reconciled: return "provider and lifecycle state match exactly";
    case ProviderOutcome::queue_empty: return "route queue contains no accepted item";
    case ProviderOutcome::queue_saturated: return "route queue is full; new item rejected";
    case ProviderOutcome::invalid_descriptor: return "provider descriptor is invalid";
    case ProviderOutcome::duplicate_provider: return "provider identity is already registered";
    case ProviderOutcome::provider_capacity_exhausted: return "provider registry is full";
    case ProviderOutcome::unsupported_contract_version: return "provider contract version unsupported";
    case ProviderOutcome::unsupported_interaction: return "interaction family unsupported";
    case ProviderOutcome::unsupported_delivery: return "delivery capability unsupported";
    case ProviderOutcome::unsupported_ordering: return "ordering capability unsupported";
    case ProviderOutcome::payload_limit_exceeded: return "payload limit exceeded";
    case ProviderOutcome::queue_limit_exceeded: return "queue limit invalid or exceeded";
    case ProviderOutcome::route_capacity_exhausted: return "provider route storage is full";
    case ProviderOutcome::invalid_provider_route_handle: return "provider route handle is inauthentic";
    case ProviderOutcome::lifecycle_mismatch: return "exact lifecycle binding or state differs";
    case ProviderOutcome::inactive_route: return "provider route is not active";
    case ProviderOutcome::route_mismatch: return "route identity, digest, or generation differs";
    case ProviderOutcome::provider_mismatch: return "provider identity or instance differs";
    case ProviderOutcome::item_mismatch: return "item metadata differs from prepared route";
    case ProviderOutcome::queued_items_remain: return "route retains accepted queued items";
    case ProviderOutcome::interrupted_resource: return "provider and lifecycle state cannot reconcile";
  }
  return "unknown provider outcome";
}

std::string_view to_string(const ProviderRouteState state) noexcept {
  switch (state) {
    case ProviderRouteState::prepared: return "prepared";
    case ProviderRouteState::active: return "active";
    case ProviderRouteState::draining: return "draining";
    case ProviderRouteState::closed: return "closed";
  }
  return "unknown";
}

ProviderDescriptor::ProviderDescriptor(
    const Identity& provider_id, const SemanticVersion& contract_version,
    const Identity& source_link, const std::uint8_t interaction_mask,
    const std::uint8_t delivery_mask, const std::uint8_t ordering_mask,
    const std::size_t maximum_payload_bytes, const std::size_t maximum_routes,
    const std::size_t maximum_queue_items) noexcept
    : provider_id_(provider_id), contract_version_(contract_version), source_link_(source_link),
      interaction_mask_(interaction_mask), delivery_mask_(delivery_mask),
      ordering_mask_(ordering_mask), maximum_payload_bytes_(maximum_payload_bytes),
      maximum_routes_(maximum_routes), maximum_queue_items_(maximum_queue_items) {}

Result<ProviderDescriptor> ProviderDescriptor::create(
    const ProviderDescriptorInput& input) noexcept {
  const auto provider_id = Identity::create(input.provider_id);
  if (!provider_id.has_value()) {
    return descriptor_failure(DiagnosticCode::required_field, "provider_id",
                              "provider identity is empty, malformed, or over-bound",
                              "provide a bounded logical provider identity");
  }
  const auto version = SemanticVersion::create(input.contract_version);
  if (!version.has_value()) {
    return descriptor_failure(DiagnosticCode::invalid_version, "contract_version",
                              "provider contract version is not canonical",
                              "provide canonical major.minor.patch text");
  }
  const auto source_link = Identity::create(input.source_link);
  if (!source_link.has_value()) {
    return descriptor_failure(DiagnosticCode::required_field, "source_link",
                              "source link is empty, malformed, or over-bound",
                              "provide a stable bounded source identity");
  }
  if (input.interaction_mask == 0U ||
      (input.interaction_mask & static_cast<std::uint8_t>(~kKnownInteractionMask)) != 0U ||
      input.delivery_mask == 0U ||
      (input.delivery_mask & static_cast<std::uint8_t>(~kKnownDeliveryMask)) != 0U ||
      input.ordering_mask == 0U ||
      (input.ordering_mask & static_cast<std::uint8_t>(~kKnownOrderingMask)) != 0U) {
    return descriptor_failure(DiagnosticCode::bound_exceeded, "capability_mask",
                              "capability mask is empty or contains an unknown bit",
                              "use only declared interaction, delivery, and ordering bits");
  }
  if (input.maximum_payload_bytes == 0U ||
      input.maximum_payload_bytes > kMaximumPayloadBytes || input.maximum_routes == 0U ||
      input.maximum_routes > kMaximumDeclaredRoutes || input.maximum_queue_items == 0U ||
      input.maximum_queue_items > kMaximumDeclaredQueueItems) {
    return descriptor_failure(DiagnosticCode::bound_exceeded, "provider_limits",
                              "provider limits are zero or exceed compile-time bounds",
                              "use nonzero payload, route, and queue limits within declared maxima");
  }
  return Result<ProviderDescriptor>::success(
      ProviderDescriptor(*provider_id, *version, *source_link, input.interaction_mask,
                         input.delivery_mask, input.ordering_mask,
                         input.maximum_payload_bytes, input.maximum_routes,
                         input.maximum_queue_items));
}

ProviderRouteHandle::ProviderRouteHandle(
    const std::uint64_t composition_instance_id, const std::uint64_t provider_instance_id,
    const std::uint64_t registration_generation, const Identity& provider_id,
    const RouteHandle& route_handle, const EndpointHandle& source_handle,
    const EndpointHandle& destination_handle,
    const std::uint64_t provider_route_generation,
    const std::size_t maximum_payload_bytes,
    const std::size_t queue_capacity) noexcept
    : composition_instance_id_(composition_instance_id),
      provider_instance_id_(provider_instance_id),
      registration_generation_(registration_generation), provider_id_(provider_id),
      route_id_(route_handle.identity()),
      provider_route_generation_(provider_route_generation),
      lifecycle_route_generation_(route_handle.generation()),
      source_endpoint_generation_(source_handle.generation()),
      destination_endpoint_generation_(destination_handle.generation()),
      route_handle_(route_handle), source_handle_(source_handle),
      destination_handle_(destination_handle),
      maximum_payload_bytes_(maximum_payload_bytes), queue_capacity_(queue_capacity) {
  static_cast<void>(plan_digest_.assign(route_handle.plan_digest()));
}

ProviderRouteSnapshot::ProviderRouteSnapshot(
    const ProviderRouteHandle& handle, const ProviderRouteState state,
    const std::size_t queued_items, const std::size_t queue_capacity) noexcept
    : handle_(handle), state_(state), queued_items_(queued_items),
      queue_capacity_(queue_capacity) {}

ProviderRegistration::ProviderRegistration(
    const std::uint64_t provider_instance_id, const std::uint64_t generation,
    const ProviderDescriptor& descriptor) noexcept
    : provider_instance_id_(provider_instance_id), generation_(generation),
      descriptor_(descriptor) {}

std::optional<ProviderRouteToken> ProviderRouteToken::create(
    const std::uint64_t generation) noexcept {
  if (generation == 0U) {
    return std::nullopt;
  }
  return ProviderRouteToken(generation);
}

ProviderRouteStateValue::ProviderRouteStateValue(
    const ProviderRouteToken& token, const ProviderRouteState state,
    const std::size_t queued_items, const std::size_t queue_capacity) noexcept
    : token_(token), state_(state), queued_items_(queued_items),
      queue_capacity_(queue_capacity) {}

std::optional<ProviderRouteStateValue> ProviderRouteStateValue::create(
    const ProviderRouteToken& token, const ProviderRouteState state,
    const std::size_t queued_items, const std::size_t queue_capacity) noexcept {
  const bool known_state = state == ProviderRouteState::prepared ||
                           state == ProviderRouteState::active ||
                           state == ProviderRouteState::draining ||
                           state == ProviderRouteState::closed;
  if (!known_state || queue_capacity == 0U || queued_items > queue_capacity) {
    return std::nullopt;
  }
  return ProviderRouteStateValue(token, state, queued_items, queue_capacity);
}

ProviderRouteBinding::ProviderRouteBinding(
    const RouteSpec& route_spec, const RouteHandle& route_handle,
    const EndpointHandle& source_handle, const EndpointHandle& destination_handle,
    const std::uint64_t composition_instance_id,
    const std::uint64_t registration_generation,
    const ProviderRouteRequirements& requirements) noexcept
    : route_spec_(route_spec), route_handle_(route_handle), source_handle_(source_handle),
      destination_handle_(destination_handle),
      composition_instance_id_(composition_instance_id),
      registration_generation_(registration_generation),
      provider_contract_version_(*SemanticVersion::create(requirements.provider_contract_version)),
      interaction_kind_(requirements.interaction_kind), delivery_(requirements.delivery),
      ordering_(requirements.ordering),
      maximum_payload_bytes_(requirements.maximum_payload_bytes),
      queue_capacity_(requirements.queue_capacity) {}

Result<ProviderRegistryConfiguration> ProviderRegistryConfiguration::create(
    const std::size_t capacity) noexcept {
  if (capacity == 0U || capacity > ProviderComposition::kMaximumProviders) {
    const std::array<DiagnosticInput, 1U> inputs{{
        {DiagnosticCode::bound_exceeded, DiagnosticSeverity::error,
         ValidationPhase::lifecycle_configuration, "provider_capacity",
         "provider registry capacity is zero or exceeds its fixed maximum",
         "use a capacity from one through eight"},
    }};
    const auto diagnostics = DiagnosticSet::create_from_inputs(inputs);
    return Result<ProviderRegistryConfiguration>::failure(*diagnostics);
  }
  return Result<ProviderRegistryConfiguration>::success(
      ProviderRegistryConfiguration(capacity));
}

ProviderComposition::ProviderComposition(
    const ProviderRegistryConfiguration& configuration) noexcept
    : instance_id_(next_composition_instance.fetch_add(1U)),
      capacity_(configuration.capacity()) {
  if (instance_id_ == 0U) {
    instance_id_ = next_composition_instance.fetch_add(1U);
  }
}

ProviderResult<ProviderRegistration> ProviderComposition::register_provider(
    CommunicationProvider& provider) noexcept {
  const ProviderDescriptor descriptor(provider.descriptor());
  const bool descriptor_compatible = provider.descriptor_compatible();
  const std::uint64_t provider_instance_id = provider.instance_id();
  if (!descriptor_compatible || provider_instance_id == 0U) {
    return ProviderResult<ProviderRegistration>::without_value(
        ProviderOutcome::invalid_descriptor);
  }
  if (descriptor.contract_version().value() != kProviderContractVersion) {
    return ProviderResult<ProviderRegistration>::without_value(
        ProviderOutcome::unsupported_contract_version);
  }
  const std::lock_guard lock(mutex_);
  std::size_t free_slot = capacity_;
  for (std::size_t index = 0U; index < capacity_; ++index) {
    if (!providers_[index].has_value()) {
      if (free_slot == capacity_) {
        free_slot = index;
      }
      continue;
    }
    if (providers_[index]->descriptor.provider_id() == descriptor.provider_id() ||
        providers_[index]->instance_id == provider_instance_id) {
      return ProviderResult<ProviderRegistration>::without_value(
          ProviderOutcome::duplicate_provider);
    }
  }
  if (free_slot == capacity_ || next_generation_ == std::numeric_limits<std::uint64_t>::max()) {
    return ProviderResult<ProviderRegistration>::without_value(
        ProviderOutcome::provider_capacity_exhausted);
  }
  const std::uint64_t generation = next_generation_++;
  providers_[free_slot].emplace(provider, descriptor, generation, provider_instance_id);
  const ProviderRegistration registration(provider_instance_id, generation, descriptor);
  return ProviderResult<ProviderRegistration>::with_value(ProviderOutcome::registered,
                                                           registration);
}

ProviderResult<ProviderRouteHandle> ProviderComposition::prepare_route(
    const LifecycleController& lifecycle, const RouteSpec& route_spec,
    const RouteHandle& route_handle, const EndpointHandle& source_handle,
    const EndpointHandle& destination_handle,
    const ProviderRouteRequirements& requirements) noexcept {
  if (route_handle.identity() != route_spec.route_id() ||
      route_handle.plan_digest() != route_spec.plan_digest() ||
      source_handle.identity() != route_spec.source_endpoint_id() ||
      destination_handle.identity() != route_spec.destination_endpoint_id() ||
      source_handle.plan_digest() != route_spec.plan_digest() ||
      destination_handle.plan_digest() != route_spec.plan_digest()) {
    return ProviderResult<ProviderRouteHandle>::without_value(ProviderOutcome::route_mismatch);
  }
  const auto route_state = lifecycle.route_snapshot(route_handle);
  const auto source_state = lifecycle.endpoint_snapshot(source_handle);
  const auto destination_state = lifecycle.endpoint_snapshot(destination_handle);
  const auto retained_route = lifecycle.route_declaration(route_handle);
  const auto retained_source = lifecycle.endpoint_declaration(source_handle);
  const auto retained_destination = lifecycle.endpoint_declaration(destination_handle);
  if (!route_state.has_value() || !source_state.has_value() || !destination_state.has_value() ||
      !retained_route.has_value() || !retained_source.has_value() ||
      !retained_destination.has_value()) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::lifecycle_mismatch);
  }
  if (*retained_route.value() != route_spec ||
      retained_source.value()->endpoint_id() != route_spec.source_endpoint_id() ||
      retained_destination.value()->endpoint_id() != route_spec.destination_endpoint_id() ||
      retained_source.value()->plan_digest() != route_spec.plan_digest() ||
      retained_destination.value()->plan_digest() != route_spec.plan_digest() ||
      retained_source.value()->provider_id() != route_spec.provider_id() ||
      retained_destination.value()->provider_id() != route_spec.provider_id() ||
      retained_source.value()->contract() != route_spec.contract() ||
      retained_destination.value()->contract() != route_spec.contract() ||
      retained_source.value()->direction() != route_spec.contract().source_direction() ||
      retained_destination.value()->direction() != route_spec.contract().target_direction()) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::route_mismatch);
  }
  if (route_state.value()->state() != LifecycleState::validated ||
      !preparable_endpoint_state(source_state.value()->state()) ||
      !preparable_endpoint_state(destination_state.value()->state())) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::lifecycle_mismatch);
  }
  CommunicationProvider* selected = nullptr;
  std::uint64_t registration_generation = 0U;
  std::uint64_t provider_instance_id = 0U;
  std::optional<ProviderDescriptor> descriptor;
  {
    const std::lock_guard lock(mutex_);
    for (std::size_t index = 0U; index < capacity_; ++index) {
      if (providers_[index].has_value() &&
          providers_[index]->descriptor.provider_id() == retained_route.value()->provider_id()) {
        selected = providers_[index]->provider;
        registration_generation = providers_[index]->generation;
        provider_instance_id = providers_[index]->instance_id;
        descriptor.emplace(providers_[index]->descriptor);
        break;
      }
    }
  }
  if (selected == nullptr || !descriptor.has_value()) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::provider_mismatch);
  }
  if (requirements.provider_contract_version != descriptor->contract_version().value()) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::unsupported_contract_version);
  }
  if (requirements.interaction_kind != retained_route.value()->contract().interaction_kind() ||
      (descriptor->interaction_mask() &
       interaction_capability_bit(requirements.interaction_kind)) == 0U) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::unsupported_interaction);
  }
  if (!known_delivery(requirements.delivery) ||
      (descriptor->delivery_mask() & delivery_capability_bit(requirements.delivery)) == 0U) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::unsupported_delivery);
  }
  if (!known_ordering(requirements.ordering) ||
      (descriptor->ordering_mask() & ordering_capability_bit(requirements.ordering)) == 0U) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::unsupported_ordering);
  }
  if (requirements.maximum_payload_bytes == 0U ||
      requirements.maximum_payload_bytes > descriptor->maximum_payload_bytes()) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::payload_limit_exceeded);
  }
  if (requirements.queue_capacity == 0U ||
      requirements.queue_capacity > descriptor->maximum_queue_items()) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::queue_limit_exceeded);
  }
  const ProviderRouteBinding binding(route_spec, route_handle, source_handle,
                                     destination_handle, instance_id_,
                                     registration_generation, requirements);
  const auto prepared = selected->prepare(binding);
  if (!prepared.has_value()) {
    return ProviderResult<ProviderRouteHandle>::without_value(prepared.outcome());
  }
  if (prepared.outcome() != ProviderOutcome::prepared) {
    return ProviderResult<ProviderRouteHandle>::without_value(
        ProviderOutcome::interrupted_resource);
  }
  const ProviderRouteHandle handle(
      instance_id_, provider_instance_id, registration_generation,
      descriptor->provider_id(), route_handle, source_handle, destination_handle,
      prepared.value()->generation(), requirements.maximum_payload_bytes,
      requirements.queue_capacity);
  return ProviderResult<ProviderRouteHandle>::with_value(ProviderOutcome::prepared, handle);
}

CommunicationProvider* ProviderComposition::provider_for(
    const ProviderRouteHandle& handle) const noexcept {
  const std::lock_guard lock(mutex_);
  for (std::size_t index = 0U; index < capacity_; ++index) {
    if (providers_[index].has_value() &&
        handle.composition_instance_id() == instance_id_ &&
        providers_[index]->instance_id == handle.provider_instance_id() &&
        providers_[index]->generation == handle.registration_generation() &&
        providers_[index]->descriptor.provider_id() == handle.provider_id()) {
      return providers_[index]->provider;
    }
  }
  return nullptr;
}

bool ProviderComposition::lifecycle_matches(
    const ProviderRouteHandle& handle, const LifecycleController& lifecycle,
    const LifecycleState route_state, const bool endpoints_must_be_active) noexcept {
  const auto route = lifecycle.route_snapshot(handle.route_handle_);
  const auto source = lifecycle.endpoint_snapshot(handle.source_handle_);
  const auto destination = lifecycle.endpoint_snapshot(handle.destination_handle_);
  const bool source_state_matches = source.has_value() &&
      (endpoints_must_be_active
           ? source.value()->state() == LifecycleState::active
           : route_state == LifecycleState::validated
                 ? preparable_endpoint_state(source.value()->state())
                 : true);
  const bool destination_state_matches = destination.has_value() &&
      (endpoints_must_be_active
           ? destination.value()->state() == LifecycleState::active
           : route_state == LifecycleState::validated
                 ? preparable_endpoint_state(destination.value()->state())
                 : true);
  return route.has_value() && source.has_value() && destination.has_value() &&
         route.value()->identity() == handle.route_id_ &&
         route.value()->plan_digest() == handle.plan_digest_.view() &&
         route.value()->generation() == handle.lifecycle_route_generation_ &&
         route.value()->state() == route_state &&
         source.value()->plan_digest() == handle.plan_digest_.view() &&
         source.value()->generation() == handle.source_endpoint_generation_ &&
         source_state_matches &&
         destination.value()->plan_digest() == handle.plan_digest_.view() &&
         destination.value()->generation() == handle.destination_endpoint_generation_ &&
         destination_state_matches;
}

ProviderStatus ProviderComposition::activate_route(const ProviderRouteHandle& handle,
                                                   LifecycleController& lifecycle) noexcept {
  CommunicationProvider* provider = provider_for(handle);
  const auto token = ProviderRouteToken::create(handle.provider_route_generation());
  if (provider == nullptr || !token.has_value()) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  const auto route = lifecycle.route_snapshot(handle.route_handle_);
  if (!route.has_value() ||
      (route.value()->state() != LifecycleState::validated &&
       route.value()->state() != LifecycleState::active) ||
      !lifecycle_matches(handle, lifecycle, route.value()->state(), true)) {
    return ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  const ProviderStatus activated = provider->activate(*token, lifecycle);
  if (activated.outcome() != ProviderOutcome::activated ||
      route.value()->state() == LifecycleState::active) {
    return activated;
  }
  const auto lifecycle_activated = lifecycle.activate_route(
      handle.route_handle_, handle.source_handle_, handle.destination_handle_);
  return lifecycle_activated.has_value() &&
                 lifecycle_activated.value()->state() == LifecycleState::active
             ? ProviderStatus(ProviderOutcome::activated)
             : ProviderStatus(ProviderOutcome::lifecycle_mismatch);
}

ProviderStatus ProviderComposition::submit(const ProviderRouteHandle& handle,
                                           const CommunicationItem& item,
                                           const LifecycleController& lifecycle) noexcept {
  CommunicationProvider* provider = provider_for(handle);
  const auto token = ProviderRouteToken::create(handle.provider_route_generation());
  if (provider == nullptr || !token.has_value()) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  const auto lifecycle_route = lifecycle.route_snapshot(handle.route_handle_);
  if (!lifecycle_route.has_value()) {
    return ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  if (lifecycle_route.value()->state() == LifecycleState::validated ||
      lifecycle_route.value()->state() == LifecycleState::draining ||
      lifecycle_route.value()->state() == LifecycleState::closed) {
    return ProviderStatus(ProviderOutcome::inactive_route);
  }
  if (!lifecycle_matches(handle, lifecycle, LifecycleState::active, true)) {
    return ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  const auto route = lifecycle.route_declaration(handle.route_handle_);
  if (!route.has_value()) {
    return ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  const CommunicationContract& contract = route.value()->contract();
  if (route.value()->provider_id() != handle.provider_id() ||
      item.contract_id() != contract.contract_id() ||
      item.contract_version() != contract.contract_version() ||
      item.interface_id() != contract.interface_id() ||
      item.schema_id() != contract.schema_id() ||
      item.schema_version() != contract.schema_version() ||
      item.interaction_kind() != contract.interaction_kind() ||
      item.endpoint_id() != route.value()->source_endpoint_id() ||
      item.route_id() != route.value()->route_id() ||
      item.provider_id() != route.value()->provider_id()) {
    return ProviderStatus(ProviderOutcome::item_mismatch);
  }
  if (item.payload().size() > handle.maximum_payload_bytes_) {
    return ProviderStatus(ProviderOutcome::payload_limit_exceeded);
  }
  return provider->submit(*token, item, lifecycle);
}

ProviderResult<CommunicationItem> ProviderComposition::receive(
    const ProviderRouteHandle& handle, const LifecycleController& lifecycle) noexcept {
  CommunicationProvider* provider = provider_for(handle);
  const auto token = ProviderRouteToken::create(handle.provider_route_generation());
  if (provider == nullptr || !token.has_value()) {
    return ProviderResult<CommunicationItem>::without_value(
        ProviderOutcome::invalid_provider_route_handle);
  }
  const auto route = lifecycle.route_snapshot(handle.route_handle_);
  if (!route.has_value() ||
      (route.value()->state() != LifecycleState::active &&
       route.value()->state() != LifecycleState::draining) ||
      !lifecycle_matches(handle, lifecycle, route.value()->state(), true)) {
    return ProviderResult<CommunicationItem>::without_value(
        ProviderOutcome::lifecycle_mismatch);
  }
  return provider->receive(*token, lifecycle);
}

ProviderStatus ProviderComposition::drain_route(const ProviderRouteHandle& handle,
                                                LifecycleController& lifecycle) noexcept {
  CommunicationProvider* provider = provider_for(handle);
  const auto token = ProviderRouteToken::create(handle.provider_route_generation());
  if (provider == nullptr || !token.has_value()) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  const auto route = lifecycle.route_snapshot(handle.route_handle_);
  if (!route.has_value() ||
      (route.value()->state() != LifecycleState::active &&
       route.value()->state() != LifecycleState::draining) ||
      !lifecycle_matches(handle, lifecycle, route.value()->state(), true)) {
    return ProviderStatus(ProviderOutcome::inactive_route);
  }
  const ProviderStatus draining = provider->drain(*token, lifecycle);
  if (draining.outcome() != ProviderOutcome::draining ||
      route.value()->state() == LifecycleState::draining) {
    return draining;
  }
  const auto lifecycle_draining = lifecycle.drain_route(handle.route_handle_);
  return lifecycle_draining.has_value() &&
                 lifecycle_draining.value()->state() == LifecycleState::draining
             ? ProviderStatus(ProviderOutcome::draining)
             : ProviderStatus(ProviderOutcome::lifecycle_mismatch);
}

ProviderStatus ProviderComposition::close_route(const ProviderRouteHandle& handle,
                                                LifecycleController& lifecycle) noexcept {
  CommunicationProvider* provider = provider_for(handle);
  const auto token = ProviderRouteToken::create(handle.provider_route_generation());
  if (provider == nullptr || !token.has_value()) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  const auto route = lifecycle.route_snapshot(handle.route_handle_);
  if (!route.has_value() ||
      (route.value()->state() != LifecycleState::draining &&
       route.value()->state() != LifecycleState::closed) ||
      !lifecycle_matches(handle, lifecycle, route.value()->state(),
                         route.value()->state() != LifecycleState::closed)) {
    return ProviderStatus(ProviderOutcome::inactive_route);
  }
  const ProviderStatus closed = provider->close(*token, lifecycle);
  if (closed.outcome() != ProviderOutcome::closed ||
      route.value()->state() == LifecycleState::closed) {
    return closed;
  }
  const auto lifecycle_closed = lifecycle.close_route(handle.route_handle_);
  return lifecycle_closed.has_value() &&
                 lifecycle_closed.value()->state() == LifecycleState::closed
             ? ProviderStatus(ProviderOutcome::closed)
             : ProviderStatus(ProviderOutcome::lifecycle_mismatch);
}

ProviderResult<ProviderRouteSnapshot> ProviderComposition::route_state(
    const ProviderRouteHandle& handle) const noexcept {
  CommunicationProvider* provider = provider_for(handle);
  const auto token = ProviderRouteToken::create(handle.provider_route_generation());
  if (provider == nullptr || !token.has_value()) {
    return ProviderResult<ProviderRouteSnapshot>::without_value(
        ProviderOutcome::invalid_provider_route_handle);
  }
  const auto internal = provider->state(*token);
  if (!internal.has_value() || internal.outcome() != ProviderOutcome::reconciled ||
      internal.value()->token() != *token ||
      internal.value()->queue_capacity() != handle.queue_capacity_) {
    return ProviderResult<ProviderRouteSnapshot>::without_value(
        internal.has_value() ? ProviderOutcome::interrupted_resource : internal.outcome());
  }
  const ProviderRouteSnapshot snapshot(handle, internal.value()->state(),
                                       internal.value()->queued_items(),
                                       internal.value()->queue_capacity());
  return ProviderResult<ProviderRouteSnapshot>::with_value(internal.outcome(), snapshot);
}

ProviderResult<ProviderRouteSnapshot> ProviderComposition::reconcile_route(
    const ProviderRouteHandle& handle, const LifecycleController& lifecycle) const noexcept {
  CommunicationProvider* provider = provider_for(handle);
  const auto token = ProviderRouteToken::create(handle.provider_route_generation());
  if (provider == nullptr || !token.has_value()) {
    return ProviderResult<ProviderRouteSnapshot>::without_value(
        ProviderOutcome::invalid_provider_route_handle);
  }
  const auto current = provider->state(*token);
  if (!current.has_value() || current.outcome() != ProviderOutcome::reconciled ||
      current.value()->token() != *token ||
      current.value()->queue_capacity() != handle.queue_capacity_) {
    return ProviderResult<ProviderRouteSnapshot>::without_value(
        current.has_value() ? ProviderOutcome::interrupted_resource : current.outcome());
  }
  LifecycleState expected = LifecycleState::validated;
  switch (current.value()->state()) {
    case ProviderRouteState::prepared: expected = LifecycleState::validated; break;
    case ProviderRouteState::active: expected = LifecycleState::active; break;
    case ProviderRouteState::draining: expected = LifecycleState::draining; break;
    case ProviderRouteState::closed: expected = LifecycleState::closed; break;
  }
  const bool endpoints_must_be_active = expected == LifecycleState::active ||
                                        expected == LifecycleState::draining;
  if (!lifecycle_matches(handle, lifecycle, expected, endpoints_must_be_active)) {
    return ProviderResult<ProviderRouteSnapshot>::without_value(
        ProviderOutcome::interrupted_resource);
  }
  const auto internal = provider->reconcile(*token, lifecycle);
  if (!internal.has_value() || internal.outcome() != ProviderOutcome::reconciled ||
      internal.value()->token() != *token ||
      internal.value()->queue_capacity() != handle.queue_capacity_) {
    return ProviderResult<ProviderRouteSnapshot>::without_value(
        internal.has_value() ? ProviderOutcome::interrupted_resource : internal.outcome());
  }
  const ProviderRouteSnapshot snapshot(handle, internal.value()->state(),
                                       internal.value()->queued_items(),
                                       internal.value()->queue_capacity());
  return ProviderResult<ProviderRouteSnapshot>::with_value(internal.outcome(), snapshot);
}

}  // namespace xverse::xcom
