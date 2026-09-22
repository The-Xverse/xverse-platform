/**
 * @file test_support.hpp
 * @brief Owned loopback fixture for provider/observation integration checks.
 * @ownership Each Scenario owns its lifecycle, provider, composition, and exact handles. An optional
 * ObservationHub is caller-owned and must outlive the scenario.
 * @lifetime Returned references remain valid for the Scenario lifetime.
 * @thread_safety Construction is single-threaded; the composed provider and observation hub serialize
 * their own operations for concurrent fixture calls.
 * @failure ready() remains false when any bounded fixture resource cannot be created.
 * @par Traceability
 * Supports XCOM-OBS-001, XCOM-OBS-002, XCOM-OBS-004, XCOM-OBS-005, XCOM-OBS-007, and XCOM-OBS-008.
 */

#ifndef XVERSE_XCOM_OBSERVATION_INTEGRATION_TEST_SUPPORT_HPP
#define XVERSE_XCOM_OBSERVATION_INTEGRATION_TEST_SUPPORT_HPP

#include "xverse/xcom/loopback_provider.hpp"

#include <array>
#include <cstddef>
#include <optional>
#include <span>
#include <string>
#include <string_view>

namespace xverse::xcom::observation_test {

/** @param kind Interaction family. @return Its compatible source direction. */
[[nodiscard]] inline EndpointDirection source_direction(const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::request
             : kind == InteractionKind::service_response ? EndpointDirection::respond
                                                         : EndpointDirection::produce;
}

/** @param kind Interaction family. @return Its compatible destination direction. */
[[nodiscard]] inline EndpointDirection destination_direction(const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::respond
             : kind == InteractionKind::service_response ? EndpointDirection::request
                                                         : EndpointDirection::consume;
}

/**
 * @brief One active fixed-capacity loopback route, optionally linked to observation.
 * @ownership Owns all normal-route resources. It never owns observation_hub.
 */
class Scenario final {
 public:
  /**
   * @param suffix Stable suffix used to isolate fixture identities.
   * @param kind Route interaction family.
   * @param queue_capacity Fixed loopback queue capacity.
   * @param observation_hub Optional caller-owned observation boundary.
   */
  Scenario(const std::string_view suffix, const InteractionKind kind,
           const std::size_t queue_capacity, ObservationHub* const observation_hub = nullptr) {
    constexpr std::string_view digest =
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
    const std::string contract_id = "contract." + std::string(suffix);
    const std::string interface_id = "interface." + std::string(suffix);
    const std::string schema_id = "schema." + std::string(suffix);
    const std::string source_id = "source." + std::string(suffix);
    const std::string destination_id = "destination." + std::string(suffix);
    const std::string route_id = "route." + std::string(suffix);
    const std::string provider_id = "provider." + std::string(suffix);

    const auto contract = CommunicationContract::create(
        {contract_id, "1.0.0", interface_id, schema_id, "1.0.0", kind,
         source_direction(kind), destination_direction(kind)});
    if (!contract.has_value()) {
      return;
    }
    contract_.emplace(*contract.value());
    const auto source = EndpointSpec::create(
        {source_id, digest, provider_id, source_direction(kind)}, *contract_);
    const auto destination = EndpointSpec::create(
        {destination_id, digest, provider_id, destination_direction(kind)}, *contract_);
    if (!source.has_value() || !destination.has_value()) {
      return;
    }
    source_spec_.emplace(*source.value());
    destination_spec_.emplace(*destination.value());
    const auto route = RouteSpec::create(
        {route_id, digest, provider_id}, *source_spec_, *destination_spec_);
    const auto lifecycle_configuration = LifecycleConfiguration::create({2U, 1U});
    if (!route.has_value() || !lifecycle_configuration.has_value()) {
      return;
    }
    route_spec_.emplace(*route.value());
    lifecycle_.emplace(*lifecycle_configuration.value());
    const auto source_handle = lifecycle_->declare_endpoint(*source_spec_);
    const auto destination_handle = lifecycle_->declare_endpoint(*destination_spec_);
    const auto route_handle = lifecycle_->declare_route(*route_spec_);
    if (!source_handle.has_value() || !destination_handle.has_value() ||
        !route_handle.has_value()) {
      return;
    }
    source_handle_.emplace(*source_handle.value());
    destination_handle_.emplace(*destination_handle.value());
    route_handle_.emplace(*route_handle.value());
    if (!lifecycle_->validate_endpoint(*source_handle_).has_value() ||
        !lifecycle_->validate_endpoint(*destination_handle_).has_value() ||
        !lifecycle_->validate_route(*route_handle_, *source_handle_, *destination_handle_)
             .has_value() ||
        !lifecycle_->activate_endpoint(*source_handle_).has_value() ||
        !lifecycle_->activate_endpoint(*destination_handle_).has_value()) {
      return;
    }

    constexpr std::uint8_t all_interactions = 0x0FU;
    const auto descriptor = ProviderDescriptor::create(
        {provider_id, "1.0.0", "source.fixture.observation", all_interactions,
         delivery_capability_bit(DeliveryCapability::best_effort),
         ordering_capability_bit(OrderingCapability::per_route_fifo), kMaximumPayloadBytes,
         LoopbackProvider::kMaximumRoutes, LoopbackProvider::kMaximumQueueItems});
    const auto registry_configuration = ProviderRegistryConfiguration::create(1U);
    if (!descriptor.has_value() || !registry_configuration.has_value()) {
      return;
    }
    descriptor_.emplace(*descriptor.value());
    provider_.emplace(*descriptor_);
    if (observation_hub == nullptr) {
      composition_.emplace(*registry_configuration.value());
    } else {
      composition_.emplace(*registry_configuration.value(), *observation_hub);
    }
    if (composition_->register_provider(*provider_).outcome() != ProviderOutcome::registered) {
      return;
    }
    const ProviderRouteRequirements requirements{
        "1.0.0", kind, DeliveryCapability::best_effort,
        OrderingCapability::per_route_fifo, 16U, queue_capacity};
    const auto prepared = composition_->prepare_route(
        *lifecycle_, *route_spec_, *route_handle_, *source_handle_, *destination_handle_,
        requirements);
    if (!prepared.has_value()) {
      return;
    }
    provider_handle_.emplace(*prepared.value());
    if (composition_->activate_route(*provider_handle_, *lifecycle_).outcome() !=
        ProviderOutcome::activated) {
      return;
    }
    ready_ = true;
  }

  /** @return true only when every owned resource is active. */
  [[nodiscard]] bool ready() const noexcept { return ready_; }
  /** @return Mutable provider composition. */
  [[nodiscard]] ProviderComposition& composition() noexcept { return *composition_; }
  /** @return Bound lifecycle owner. */
  [[nodiscard]] const LifecycleController& lifecycle() const noexcept { return *lifecycle_; }
  /** @return Exact active provider-route authority. */
  [[nodiscard]] const ProviderRouteHandle& provider_handle() const noexcept {
    return *provider_handle_;
  }
  /** @return Exact logical route identity. */
  [[nodiscard]] std::string_view route_id() const noexcept {
    return route_spec_->route_id().value();
  }
  /** @return Exact logical provider identity. */
  [[nodiscard]] std::string_view provider_id() const noexcept {
    return route_spec_->provider_id().value();
  }

  /**
   * @brief Make one valid route-bound item.
   * @param sequence Value used in timestamp, identities, and the first payload byte.
   * @param payload_size Requested payload size from one through four.
   * @return Owned validated item or diagnostics.
   */
  [[nodiscard]] Result<CommunicationItem> item(
      const unsigned int sequence, const std::size_t payload_size = 4U) const noexcept {
    const std::array<std::byte, 4U> bytes{
        std::byte(sequence & 0xFFU), std::byte{0x22U}, std::byte{0x33U}, std::byte{0x44U}};
    const std::string correlation = "correlation." + std::to_string(sequence);
    const std::string causation = "causation." + std::to_string(sequence);
    const std::span<const std::byte> payload(bytes.data(), payload_size);
    return CommunicationItem::create(
        {contract_->contract_id().value(), contract_->contract_version().value(),
         contract_->interface_id().value(), route_spec_->source_endpoint_id().value(),
         contract_->schema_id().value(), contract_->schema_version().value(),
         contract_->interaction_kind(), OriginKind::component,
         Timestamp(static_cast<std::int64_t>(sequence)), "clock.fixture", correlation, causation,
         route_spec_->route_id().value(), route_spec_->provider_id().value(), payload},
        *contract_);
  }

 private:
  bool ready_{false};
  std::optional<CommunicationContract> contract_;
  std::optional<EndpointSpec> source_spec_;
  std::optional<EndpointSpec> destination_spec_;
  std::optional<RouteSpec> route_spec_;
  std::optional<LifecycleController> lifecycle_;
  std::optional<EndpointHandle> source_handle_;
  std::optional<EndpointHandle> destination_handle_;
  std::optional<RouteHandle> route_handle_;
  std::optional<ProviderDescriptor> descriptor_;
  std::optional<LoopbackProvider> provider_;
  std::optional<ProviderComposition> composition_;
  std::optional<ProviderRouteHandle> provider_handle_;
};

/**
 * @brief Create one observation policy.
 * @param filter Provider-neutral logical constraints.
 * @param payload_mode Payload visibility policy.
 * @param maximum_payload_bytes Explicit prefix bound, or zero.
 * @param record_capacity Fixed record slots.
 * @param overflow_policy Saturation behavior.
 * @return Valid owned policy.
 */
[[nodiscard]] inline ObservationTapSpec make_tap_spec(
    const ObservationFilterInput& filter, const ObservationPayloadMode payload_mode,
    const std::size_t maximum_payload_bytes, const std::size_t record_capacity,
    const ObservationOverflowPolicy overflow_policy) {
  const auto spec = ObservationTapSpec::create(
      {kObservationContractVersion, filter, payload_mode, maximum_payload_bytes,
       record_capacity, overflow_policy});
  return *spec;
}

}  // namespace xverse::xcom::observation_test

#endif  // XVERSE_XCOM_OBSERVATION_INTEGRATION_TEST_SUPPORT_HPP
