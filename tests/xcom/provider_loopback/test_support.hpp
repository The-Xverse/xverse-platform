/**
 * @file test_support.hpp
 * @brief Owned provider-loopback test fixture helpers.
 */

#ifndef XVERSE_XCOM_PROVIDER_LOOPBACK_TEST_SUPPORT_HPP
#define XVERSE_XCOM_PROVIDER_LOOPBACK_TEST_SUPPORT_HPP

#include "xverse/xcom/loopback_provider.hpp"

#include <array>
#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace xverse::xcom::test {

/** Return compatible source direction for one interaction family. */
[[nodiscard]] inline EndpointDirection source_direction(const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::request
             : kind == InteractionKind::service_response ? EndpointDirection::respond
                                                         : EndpointDirection::produce;
}

/** Return compatible destination direction for one interaction family. */
[[nodiscard]] inline EndpointDirection destination_direction(
    const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::respond
             : kind == InteractionKind::service_response ? EndpointDirection::request
                                                         : EndpointDirection::consume;
}

/** Return a valid loopback descriptor with caller-selected identity. */
[[nodiscard]] inline ProviderDescriptor descriptor(const std::string_view provider_id) {
  constexpr std::uint8_t all_interactions = 0x0FU;
  const auto result = ProviderDescriptor::create(
      {provider_id, "1.0.0", "source.xverse.xcom.loopback", all_interactions,
       delivery_capability_bit(DeliveryCapability::best_effort),
       ordering_capability_bit(OrderingCapability::per_route_fifo),
       kMaximumPayloadBytes, LoopbackProvider::kMaximumRoutes,
       LoopbackProvider::kMaximumQueueItems});
  return *result.value();
}

/**
 * @brief One exact lifecycle/provider route fixture with optional activation.
 * @ownership Owns every contract, lifecycle resource, provider, registry, and handle.
 */
class Scenario final {
 public:
  /**
   * @param kind Interaction family for the route.
   * @param queue_capacity Fixed reject-new queue capacity.
   * @param maximum_payload_bytes Per-route payload bound.
   * @param suffix Identity suffix used to keep fixtures independent.
   * @param activate_now Whether to activate the prepared provider route.
   */
  Scenario(const InteractionKind kind, const std::size_t queue_capacity,
           const std::size_t maximum_payload_bytes, const std::string_view suffix,
           const bool activate_now = true) {
    const std::string contract_id = "contract." + std::string(suffix);
    const std::string interface_id = "interface." + std::string(suffix);
    const std::string schema_id = "schema." + std::string(suffix);
    const std::string source_id = "source." + std::string(suffix);
    const std::string destination_id = "destination." + std::string(suffix);
    const std::string route_id = "route." + std::string(suffix);
    constexpr std::string_view digest =
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

    const auto contract = CommunicationContract::create(
        {contract_id, "1.0.0", interface_id, schema_id, "1.0.0", kind,
         source_direction(kind), destination_direction(kind)});
    if (!contract.has_value()) {
      return;
    }
    contract_.emplace(*contract.value());
    const auto source = EndpointSpec::create(
        {source_id, digest, "provider.loopback", source_direction(kind)}, *contract_);
    const auto destination = EndpointSpec::create(
        {destination_id, digest, "provider.loopback", destination_direction(kind)}, *contract_);
    if (!source.has_value() || !destination.has_value()) {
      return;
    }
    source_spec_.emplace(*source.value());
    destination_spec_.emplace(*destination.value());
    const auto route = RouteSpec::create(
        {route_id, digest, "provider.loopback"}, *source_spec_, *destination_spec_);
    if (!route.has_value()) {
      return;
    }
    route_spec_.emplace(*route.value());
    const auto lifecycle_configuration = LifecycleConfiguration::create({2U, 2U});
    if (!lifecycle_configuration.has_value()) {
      return;
    }
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
        !lifecycle_->validate_route(*route_handle_, *source_handle_,
                                    *destination_handle_).has_value() ||
        !lifecycle_->activate_endpoint(*source_handle_).has_value() ||
        !lifecycle_->activate_endpoint(*destination_handle_).has_value()) {
      return;
    }

    descriptor_.emplace(descriptor("provider.loopback"));
    provider_.emplace(*descriptor_);
    const auto registry_configuration = ProviderRegistryConfiguration::create(1U);
    if (!registry_configuration.has_value()) {
      return;
    }
    composition_.emplace(*registry_configuration.value());
    if (composition_->register_provider(*provider_).outcome() != ProviderOutcome::registered) {
      return;
    }
    requirements_ = {"1.0.0", kind, DeliveryCapability::best_effort,
                     OrderingCapability::per_route_fifo, maximum_payload_bytes,
                     queue_capacity};
    const auto prepared = composition_->prepare_route(
        *lifecycle_, *route_spec_, *route_handle_, *source_handle_, *destination_handle_,
        requirements_);
    if (!prepared.has_value()) {
      return;
    }
    provider_handle_.emplace(*prepared.value());
    if (activate_now &&
        composition_->activate_route(*provider_handle_, *lifecycle_).outcome() !=
            ProviderOutcome::activated) {
      return;
    }
    ready_ = true;
  }

  /** @return true when every fixture resource was created. */
  [[nodiscard]] bool ready() const noexcept { return ready_; }
  /** @return Owned contract. */
  [[nodiscard]] const CommunicationContract& contract() const noexcept { return *contract_; }
  /** @return Owned route declaration. */
  [[nodiscard]] const RouteSpec& route_spec() const noexcept { return *route_spec_; }
  /** @return Owned source endpoint declaration. */
  [[nodiscard]] const EndpointSpec& source_spec() const noexcept { return *source_spec_; }
  /** @return Owned destination endpoint declaration. */
  [[nodiscard]] const EndpointSpec& destination_spec() const noexcept {
    return *destination_spec_;
  }
  /** @return Exact source endpoint handle. */
  [[nodiscard]] const EndpointHandle& source_handle() const noexcept { return *source_handle_; }
  /** @return Exact destination endpoint handle. */
  [[nodiscard]] const EndpointHandle& destination_handle() const noexcept {
    return *destination_handle_;
  }
  /** @return Exact lifecycle route handle. */
  [[nodiscard]] const RouteHandle& route_handle() const noexcept { return *route_handle_; }
  /** @return Exact provider route handle. */
  [[nodiscard]] const ProviderRouteHandle& provider_handle() const noexcept {
    return *provider_handle_;
  }
  /** @return Mutable lifecycle controller for transition tests. */
  [[nodiscard]] LifecycleController& lifecycle() noexcept { return *lifecycle_; }
  /** @return Lifecycle controller for observations. */
  [[nodiscard]] const LifecycleController& lifecycle() const noexcept { return *lifecycle_; }
  /** @return Mutable composition dispatcher. */
  [[nodiscard]] ProviderComposition& composition() noexcept { return *composition_; }
  /** @return Mutable provider for explicit multi-composition ownership tests. */
  [[nodiscard]] LoopbackProvider& provider() noexcept { return *provider_; }
  /** @return Immutable requirements used for preparation. */
  [[nodiscard]] const ProviderRouteRequirements& requirements() const noexcept {
    return requirements_;
  }

  /**
   * @brief Create a valid route-bound item with one caller-selected payload byte.
   * @param sequence Byte used for payload, timestamp, and correlation identity.
   * @return Owned item or core validation diagnostics.
   */
  [[nodiscard]] Result<CommunicationItem> item(const unsigned int sequence) const noexcept {
    const std::array<std::byte, 1U> payload{std::byte(sequence & 0xFFU)};
    const std::string correlation = "correlation." + std::to_string(sequence);
    const std::string causation = "causation." + std::to_string(sequence);
    return CommunicationItem::create(
        {contract_->contract_id().value(), contract_->contract_version().value(),
         contract_->interface_id().value(), route_spec_->source_endpoint_id().value(),
         contract_->schema_id().value(), contract_->schema_version().value(),
         contract_->interaction_kind(), OriginKind::component,
         Timestamp(static_cast<std::int64_t>(sequence)), "clock.fixture", correlation,
         causation, route_spec_->route_id().value(), route_spec_->provider_id().value(),
         payload},
        *contract_);
  }

  /**
   * @brief Create contract-valid item metadata with caller-selected route binding fields.
   * @param endpoint_id Logical source metadata.
   * @param route_id Route provenance metadata.
   * @param provider_id Provider provenance metadata.
   * @param payload Payload bytes.
   * @return Owned core item or validation diagnostics.
   */
  [[nodiscard]] Result<CommunicationItem> item_with_binding(
      const std::string_view endpoint_id, const std::string_view route_id,
      const std::string_view provider_id, const std::span<const std::byte> payload) const noexcept {
    return CommunicationItem::create(
        {contract_->contract_id().value(), contract_->contract_version().value(),
         contract_->interface_id().value(), endpoint_id, contract_->schema_id().value(),
         contract_->schema_version().value(), contract_->interaction_kind(), OriginKind::component,
         Timestamp(1), "clock.fixture", "correlation.custom", "causation.custom", route_id,
         provider_id, payload},
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
  ProviderRouteRequirements requirements_{"1.0.0", InteractionKind::message_event,
                                           DeliveryCapability::best_effort,
                                           OrderingCapability::per_route_fifo, 1U, 1U};
  std::optional<ProviderRouteHandle> provider_handle_;
};

}  // namespace xverse::xcom::test

#endif  // XVERSE_XCOM_PROVIDER_LOOPBACK_TEST_SUPPORT_HPP
