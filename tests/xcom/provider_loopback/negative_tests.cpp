/**
 * @file negative_tests.cpp
 * @brief Provider descriptor, compatibility, identity, state, and stale-handle rejection tests.
 */

#include "test_support.hpp"
#include "independent_provider.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <string_view>

namespace {

using namespace xverse::xcom;
using xverse::xcom::test::Scenario;
constexpr std::string_view kDigest =
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
constexpr std::string_view kOtherDigest =
    "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";

/** Report one failed expectation. */
[[nodiscard]] bool expect(const bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << "provider negative failure: " << message << '\n';
  }
  return condition;
}

/** Fresh registered provider and lifecycle declarations with no prepared provider resource. */
class FreshPreparationFixture final {
 public:
  /**
   * @param suffix Stable identity suffix for this isolated fixture.
   * @param bind_registered_provider Whether the route names the registered provider.
   */
  explicit FreshPreparationFixture(const std::string_view suffix,
                                   const bool bind_registered_provider = true) {
    const std::string contract_id = "contract." + std::string(suffix);
    const std::string interface_id = "interface." + std::string(suffix);
    const std::string schema_id = "schema." + std::string(suffix);
    const std::string source_id = "source." + std::string(suffix);
    const std::string destination_id = "destination." + std::string(suffix);
    const std::string route_id = "route." + std::string(suffix);
    const std::string_view route_provider =
        bind_registered_provider ? "provider.fresh" : "provider.unregistered";
    const auto contract = CommunicationContract::create(
        {contract_id, "1.0.0", interface_id, schema_id, "1.0.0",
         InteractionKind::message_event, EndpointDirection::produce,
         EndpointDirection::consume});
    if (!contract.has_value()) return;
    contract_.emplace(*contract.value());
    const auto source = EndpointSpec::create(
        {source_id, kDigest, route_provider, EndpointDirection::produce}, *contract_);
    const auto destination = EndpointSpec::create(
        {destination_id, kDigest, route_provider, EndpointDirection::consume}, *contract_);
    if (!source.has_value() || !destination.has_value()) return;
    source_spec_.emplace(*source.value());
    destination_spec_.emplace(*destination.value());
    const auto route = RouteSpec::create(
        {route_id, kDigest, route_provider}, *source_spec_, *destination_spec_);
    const auto lifecycle_configuration = LifecycleConfiguration::create({2U, 2U});
    if (!route.has_value() || !lifecycle_configuration.has_value()) return;
    route_spec_.emplace(*route.value());
    lifecycle_.emplace(*lifecycle_configuration.value());
    const auto source_handle = lifecycle_->declare_endpoint(*source_spec_);
    const auto destination_handle = lifecycle_->declare_endpoint(*destination_spec_);
    const auto route_handle = lifecycle_->declare_route(*route_spec_);
    if (!source_handle.has_value() || !destination_handle.has_value() ||
        !route_handle.has_value()) return;
    source_handle_.emplace(*source_handle.value());
    destination_handle_.emplace(*destination_handle.value());
    route_handle_.emplace(*route_handle.value());
    if (!lifecycle_->validate_endpoint(*source_handle_).has_value() ||
        !lifecycle_->validate_endpoint(*destination_handle_).has_value() ||
        !lifecycle_->validate_route(*route_handle_, *source_handle_,
                                    *destination_handle_).has_value()) return;

    const auto descriptor = ProviderDescriptor::create(
        {"provider.fresh", "1.0.0", "source.fixture.fresh", 0x0FU,
         delivery_capability_bit(DeliveryCapability::best_effort),
         ordering_capability_bit(OrderingCapability::per_route_fifo), 16U, 1U, 1U});
    const auto registry_configuration = ProviderRegistryConfiguration::create(1U);
    if (!descriptor.has_value() || !registry_configuration.has_value()) return;
    descriptor_.emplace(*descriptor.value());
    provider_.emplace(*descriptor_, 10000U + next_instance_++);
    composition_.emplace(*registry_configuration.value());
    if (composition_->register_provider(*provider_).outcome() !=
        ProviderOutcome::registered) return;
    ready_ = true;
  }

  /** @return true when declarations and explicit registration completed. */
  [[nodiscard]] bool ready() const noexcept { return ready_; }
  /** @return Exact retained contract. */
  [[nodiscard]] const CommunicationContract& contract() const noexcept { return *contract_; }
  /** @return Exact retained source declaration. */
  [[nodiscard]] const EndpointSpec& source_spec() const noexcept { return *source_spec_; }
  /** @return Exact retained destination declaration. */
  [[nodiscard]] const EndpointSpec& destination_spec() const noexcept {
    return *destination_spec_;
  }
  /** @return Exact retained route declaration. */
  [[nodiscard]] const RouteSpec& route_spec() const noexcept { return *route_spec_; }
  /** @return Exact source lifecycle handle. */
  [[nodiscard]] const EndpointHandle& source_handle() const noexcept { return *source_handle_; }
  /** @return Exact destination lifecycle handle. */
  [[nodiscard]] const EndpointHandle& destination_handle() const noexcept {
    return *destination_handle_;
  }
  /** @return Exact route lifecycle handle. */
  [[nodiscard]] const RouteHandle& route_handle() const noexcept { return *route_handle_; }
  /** @return Mutable lifecycle owner. */
  [[nodiscard]] LifecycleController& lifecycle() noexcept { return *lifecycle_; }
  /** @return Mutable composition dispatcher. */
  [[nodiscard]] ProviderComposition& composition() noexcept { return *composition_; }
  /** @return Dispatch-counted independent provider. */
  [[nodiscard]] test::IndependentProvider& provider() noexcept { return *provider_; }
  /** @return Exact valid preparation requirements. */
  [[nodiscard]] ProviderRouteRequirements requirements() const noexcept {
    return {"1.0.0", InteractionKind::message_event,
            DeliveryCapability::best_effort, OrderingCapability::per_route_fifo,
            16U, 1U};
  }
  /** @return Prepared handle or stable failure for the exact retained declarations. */
  [[nodiscard]] ProviderResult<ProviderRouteHandle> prepare() noexcept {
    return composition_->prepare_route(*lifecycle_, *route_spec_, *route_handle_,
                                       *source_handle_, *destination_handle_,
                                       requirements());
  }
  /** @return true when both exact endpoints transition to active. */
  [[nodiscard]] bool activate_endpoints() noexcept {
    return lifecycle_->activate_endpoint(*source_handle_).has_value() &&
           lifecycle_->activate_endpoint(*destination_handle_).has_value();
  }
  /** @return Contract-valid item with caller-selected binding fields and payload. */
  [[nodiscard]] Result<CommunicationItem> item_with_binding(
      const std::string_view endpoint_id, const std::string_view route_id,
      const std::string_view provider_id,
      const std::span<const std::byte> payload) const noexcept {
    return CommunicationItem::create(
        {contract_->contract_id().value(), contract_->contract_version().value(),
         contract_->interface_id().value(), endpoint_id, contract_->schema_id().value(),
         contract_->schema_version().value(), contract_->interaction_kind(),
         OriginKind::component, Timestamp(1), "clock.fresh", "correlation.fresh",
         "causation.fresh", route_id, provider_id, payload},
        *contract_);
  }

 private:
  inline static std::uint64_t next_instance_{1U};
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
  std::optional<test::IndependentProvider> provider_;
  std::optional<ProviderComposition> composition_;
};

/** Compare provider snapshots without relying on object identity. */
[[nodiscard]] bool same_snapshot(
    const ProviderResult<ProviderRouteSnapshot>& left,
    const ProviderResult<ProviderRouteSnapshot>& right) {
  return left.has_value() && right.has_value() &&
         left.outcome() == right.outcome() &&
         left.value()->state() == right.value()->state() &&
         left.value()->queued_items() == right.value()->queued_items() &&
         left.value()->queue_capacity() == right.value()->queue_capacity() &&
         left.value()->handle().provider_route_generation() ==
             right.value()->handle().provider_route_generation() &&
         left.value()->handle().lifecycle_route_generation() ==
             right.value()->handle().lifecycle_route_generation();
}

/** Compare lifecycle observations, including stable absence for stale handles. */
[[nodiscard]] bool same_lifecycle_observation(
    const Result<LifecycleSnapshot>& left,
    const Result<LifecycleSnapshot>& right) {
  return left.has_value() == right.has_value() &&
         (!left.has_value() || *left.value() == *right.value());
}

/** Compare optional observations used only when a replacement handle exists. */
[[nodiscard]] bool same_optional_lifecycle_observation(
    const std::optional<Result<LifecycleSnapshot>>& left,
    const std::optional<Result<LifecycleSnapshot>>& right) {
  return left.has_value() == right.has_value() &&
         (!left.has_value() || same_lifecycle_observation(*left, *right));
}

/** Verify malformed, zero-bound, unsupported-version, duplicate, and capacity rejection. */
[[nodiscard]] bool test_descriptor_and_registration_rejection() {
  constexpr ProviderDescriptorInput valid{
      "provider.valid", "1.0.0", "source.valid", 0x0FU,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U};
  const std::array invalid{
      ProviderDescriptorInput{"", "1.0.0", "source.valid", 0x0FU, 1U, 2U, 64U, 1U, 1U},
      ProviderDescriptorInput{"provider.valid", "bad", "source.valid", 0x0FU, 1U, 2U, 64U,
                              1U, 1U},
      ProviderDescriptorInput{"provider.valid", "1.0.0", "", 0x0FU, 1U, 2U, 64U, 1U, 1U},
      ProviderDescriptorInput{"provider.valid", "1.0.0", "source.valid", 0U, 1U, 2U, 64U,
                              1U, 1U},
      ProviderDescriptorInput{"provider.valid", "1.0.0", "source.valid", 0x0FU, 1U, 2U, 0U,
                              1U, 1U},
      ProviderDescriptorInput{"provider.valid", "1.0.0", "source.valid", 0x0FU, 1U, 2U, 64U,
                              0U, 1U},
      ProviderDescriptorInput{"provider.valid", "1.0.0", "source.valid", 0x0FU, 1U, 2U, 64U,
                              1U, 0U},
  };
  for (const auto& input : invalid) {
    if (!expect(!ProviderDescriptor::create(input).has_value(),
                "invalid descriptor was accepted")) {
      return false;
    }
  }
  const auto descriptor = ProviderDescriptor::create(valid);
  const auto unsupported = ProviderDescriptor::create(
      {"provider.unsupported", "2.0.0", "source.unsupported", 0x0FU, 1U, 2U, 64U, 1U,
       1U});
  const auto registry = ProviderRegistryConfiguration::create(1U);
  if (!descriptor.has_value() || !unsupported.has_value() || !registry.has_value()) {
    return expect(false, "registration fixtures were invalid");
  }
  auto first = std::make_unique<LoopbackProvider>(*descriptor.value());
  auto duplicate = std::make_unique<LoopbackProvider>(*descriptor.value());
  auto wrong_version = std::make_unique<LoopbackProvider>(*unsupported.value());
  ProviderComposition composition(*registry.value());
  if (!expect(composition.register_provider(*wrong_version).outcome() ==
                  ProviderOutcome::unsupported_contract_version,
              "unsupported source contract version was registered") ||
      !expect(composition.register_provider(*first).outcome() == ProviderOutcome::registered,
              "valid provider was rejected") ||
      !expect(composition.register_provider(*duplicate).outcome() ==
                  ProviderOutcome::duplicate_provider,
              "duplicate identity was registered")) {
    return false;
  }
  const auto second_descriptor = test::descriptor("provider.second");
  auto second = std::make_unique<LoopbackProvider>(second_descriptor);
  if (!expect(composition.register_provider(*second).outcome() ==
                  ProviderOutcome::provider_capacity_exhausted,
              "full provider registry accepted a new provider")) {
    return false;
  }

  const auto over_queue = ProviderDescriptor::create(
      {"provider.over-queue", "1.0.0", "source.over-queue", 0x0FU,
       delivery_capability_bit(DeliveryCapability::best_effort),
       ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U,
       LoopbackProvider::kMaximumQueueItems + 1U});
  const auto reliable = ProviderDescriptor::create(
      {"provider.reliable", "1.0.0", "source.reliable", 0x0FU,
       delivery_capability_bit(DeliveryCapability::reliable),
       ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U});
  const auto wider_registry = ProviderRegistryConfiguration::create(2U);
  if (!over_queue.has_value() || !reliable.has_value() || !wider_registry.has_value()) {
    return expect(false, "incompatible loopback descriptor fixtures were invalid");
  }
  LoopbackProvider over_queue_provider(*over_queue.value());
  LoopbackProvider reliable_provider(*reliable.value());
  ProviderComposition incompatible(*wider_registry.value());
  return expect(incompatible.register_provider(over_queue_provider).outcome() ==
                    ProviderOutcome::invalid_descriptor,
                "loopback accepted queue capacity beyond fixed storage") &&
         expect(incompatible.register_provider(reliable_provider).outcome() ==
                    ProviderOutcome::invalid_descriptor,
                "loopback accepted an unsupported reliability claim");
}

/** Verify one composition cannot dispatch a handle issued through another registry. */
[[nodiscard]] bool test_foreign_composition_rejection() {
  Scenario scenario(InteractionKind::message_event, 1U, 8U, "composition");
  const auto configuration = ProviderRegistryConfiguration::create(1U);
  if (!scenario.ready() || !configuration.has_value()) {
    return expect(false, "foreign composition fixture setup failed");
  }
  ProviderComposition foreign(*configuration.value());
  if (foreign.register_provider(scenario.provider()).outcome() != ProviderOutcome::registered) {
    return expect(false, "same provider could not be explicitly registered in second registry");
  }
  const auto item = scenario.item(1U);
  if (!item.has_value()) {
    return expect(false, "foreign composition item construction failed");
  }
  return expect(foreign.submit(scenario.provider_handle(), *item.value(), scenario.lifecycle())
                    .outcome() == ProviderOutcome::invalid_provider_route_handle,
                "foreign composition accepted another registry's exact handle") &&
         expect(foreign.route_state(scenario.provider_handle()).outcome() ==
                    ProviderOutcome::invalid_provider_route_handle,
                "foreign composition observed another registry's route");
}

/** Verify every route compatibility boundary rejects without provider mutation. */
[[nodiscard]] bool test_prepare_compatibility_rejection() {
  Scenario scenario(InteractionKind::message_event, 2U, 16U, "prepare", false);
  if (!expect(scenario.ready(), "prepare rejection scenario setup failed")) {
    return false;
  }
  const auto check = [&scenario](const ProviderRouteRequirements& requirements,
                                 const ProviderOutcome expected) {
    const auto provider_before = scenario.composition().route_state(scenario.provider_handle());
    const auto route_before = scenario.lifecycle().route_snapshot(scenario.route_handle());
    const auto source_before = scenario.lifecycle().endpoint_snapshot(scenario.source_handle());
    const auto destination_before =
        scenario.lifecycle().endpoint_snapshot(scenario.destination_handle());
    const auto result = scenario.composition().prepare_route(
        scenario.lifecycle(), scenario.route_spec(), scenario.route_handle(),
        scenario.source_handle(), scenario.destination_handle(), requirements);
    const auto provider_after = scenario.composition().route_state(scenario.provider_handle());
    const auto route_after = scenario.lifecycle().route_snapshot(scenario.route_handle());
    const auto source_after = scenario.lifecycle().endpoint_snapshot(scenario.source_handle());
    const auto destination_after =
        scenario.lifecycle().endpoint_snapshot(scenario.destination_handle());
    return expect(result.outcome() == expected && !result.has_value(),
                  "prepare compatibility outcome differs") &&
           expect(provider_before.has_value() && provider_after.has_value() &&
                      provider_before.value()->state() == provider_after.value()->state() &&
                      provider_before.value()->queued_items() ==
                          provider_after.value()->queued_items() &&
                      route_before.has_value() && route_after.has_value() &&
                      *route_before.value() == *route_after.value() &&
                      source_before.has_value() && source_after.has_value() &&
                      *source_before.value() == *source_after.value() &&
                      destination_before.has_value() && destination_after.has_value() &&
                      *destination_before.value() == *destination_after.value(),
                  "prepare compatibility rejection mutated provider or lifecycle state");
  };
  auto requirements = scenario.requirements();
  requirements.provider_contract_version = "2.0.0";
  if (!check(requirements, ProviderOutcome::unsupported_contract_version)) return false;
  requirements = scenario.requirements();
  requirements.interaction_kind = InteractionKind::service_request;
  if (!check(requirements, ProviderOutcome::unsupported_interaction)) return false;
  requirements = scenario.requirements();
  requirements.delivery = DeliveryCapability::reliable;
  if (!check(requirements, ProviderOutcome::unsupported_delivery)) return false;
  requirements = scenario.requirements();
  requirements.ordering = OrderingCapability::unordered;
  if (!check(requirements, ProviderOutcome::unsupported_ordering)) return false;
  requirements = scenario.requirements();
  requirements.maximum_payload_bytes = kMaximumPayloadBytes + 1U;
  if (!check(requirements, ProviderOutcome::payload_limit_exceeded)) return false;
  requirements = scenario.requirements();
  requirements.queue_capacity = LoopbackProvider::kMaximumQueueItems + 1U;
  if (!check(requirements, ProviderOutcome::queue_limit_exceeded)) return false;

  const auto other_contract = CommunicationContract::create(
      {"contract.prepare.other", "2.0.0", "interface.prepare.other",
       "schema.prepare.other", "2.0.0", InteractionKind::message_event,
       EndpointDirection::produce, EndpointDirection::consume});
  if (!other_contract.has_value()) return expect(false, "alternate prepare contract failed");
  const auto make_route = [](const std::string_view route_id,
                             const std::string_view source_id,
                             const std::string_view destination_id,
                             const std::string_view digest,
                             const std::string_view provider_id,
                             const CommunicationContract& contract) {
    const auto source = EndpointSpec::create(
        {source_id, digest, provider_id, EndpointDirection::produce}, contract);
    const auto destination = EndpointSpec::create(
        {destination_id, digest, provider_id, EndpointDirection::consume}, contract);
    if (!source.has_value() || !destination.has_value()) {
      return std::optional<RouteSpec>{};
    }
    const auto route = RouteSpec::create({route_id, digest, provider_id},
                                         *source.value(), *destination.value());
    return route.has_value() ? std::optional<RouteSpec>(*route.value())
                             : std::optional<RouteSpec>{};
  };
  const std::array mismatched_routes{
      make_route("route.prepare.other", "source.prepare", "destination.prepare", kDigest,
                 "provider.loopback", scenario.contract()),
      make_route("route.prepare", "source.prepare.other", "destination.prepare", kDigest,
                 "provider.loopback", scenario.contract()),
      make_route("route.prepare", "source.prepare", "destination.prepare.other", kDigest,
                 "provider.loopback", scenario.contract()),
      make_route("route.prepare", "source.prepare", "destination.prepare", kOtherDigest,
                 "provider.loopback", scenario.contract()),
      make_route("route.prepare", "source.prepare", "destination.prepare", kDigest,
                 "provider.other", scenario.contract()),
      make_route("route.prepare", "source.prepare", "destination.prepare", kDigest,
                 "provider.loopback", *other_contract.value()),
  };
  for (const auto& route : mismatched_routes) {
    if (!route.has_value()) return expect(false, "prepare mismatch declaration failed");
    const auto before = scenario.composition().route_state(scenario.provider_handle());
    const auto route_before = scenario.lifecycle().route_snapshot(scenario.route_handle());
    const auto source_before = scenario.lifecycle().endpoint_snapshot(scenario.source_handle());
    const auto destination_before =
        scenario.lifecycle().endpoint_snapshot(scenario.destination_handle());
    const auto rejected = scenario.composition().prepare_route(
        scenario.lifecycle(), *route, scenario.route_handle(),
        scenario.source_handle(), scenario.destination_handle(), scenario.requirements());
    const auto after = scenario.composition().route_state(scenario.provider_handle());
    const auto route_after = scenario.lifecycle().route_snapshot(scenario.route_handle());
    const auto source_after = scenario.lifecycle().endpoint_snapshot(scenario.source_handle());
    const auto destination_after =
        scenario.lifecycle().endpoint_snapshot(scenario.destination_handle());
    if (!expect(rejected.outcome() == ProviderOutcome::route_mismatch &&
                    !rejected.has_value(),
                "retained declaration mismatch was prepared") ||
        !expect(before.has_value() && after.has_value() &&
                    before.value()->state() == after.value()->state() &&
                    before.value()->queued_items() == after.value()->queued_items() &&
                    before.value()->queue_capacity() == after.value()->queue_capacity(),
                "retained declaration rejection mutated provider state") ||
        !expect(route_before.has_value() && route_after.has_value() &&
                    *route_before.value() == *route_after.value() &&
                    source_before.has_value() && source_after.has_value() &&
                    *source_before.value() == *source_after.value() &&
                    destination_before.has_value() && destination_after.has_value() &&
                    *destination_before.value() == *destination_after.value(),
                "retained declaration rejection mutated lifecycle state")) {
      return false;
    }
  }
  const auto duplicate = scenario.composition().prepare_route(
      scenario.lifecycle(), scenario.route_spec(), scenario.route_handle(),
      scenario.source_handle(), scenario.destination_handle(), scenario.requirements());
  if (!expect(duplicate.outcome() == ProviderOutcome::route_mismatch,
              "duplicate provider route resource was prepared")) {
    return false;
  }
  const auto state = scenario.composition().route_state(scenario.provider_handle());
  return expect(state.has_value() && state.value()->state() == ProviderRouteState::prepared &&
                    state.value()->queued_items() == 0U,
                "rejected preparation mutated existing provider resource");
}

/** Compatibility dimensions exercised with a fresh, never-prepared provider fixture. */
enum class PrepareMismatch {
  contract_version,
  interaction,
  delivery,
  ordering,
  zero_payload,
  excessive_payload,
  zero_queue,
  excessive_queue,
  route_identity,
  source_identity,
  destination_identity,
  plan_digest,
  provider_identity,
  contract,
  unregistered_provider,
};

/** Verify every composition mismatch rejects before first provider dispatch or mutation. */
[[nodiscard]] bool test_fresh_prepare_rejection_matrix() {
  const std::array cases{
      PrepareMismatch::contract_version,
      PrepareMismatch::interaction,
      PrepareMismatch::delivery,
      PrepareMismatch::ordering,
      PrepareMismatch::zero_payload,
      PrepareMismatch::excessive_payload,
      PrepareMismatch::zero_queue,
      PrepareMismatch::excessive_queue,
      PrepareMismatch::route_identity,
      PrepareMismatch::source_identity,
      PrepareMismatch::destination_identity,
      PrepareMismatch::plan_digest,
      PrepareMismatch::provider_identity,
      PrepareMismatch::contract,
      PrepareMismatch::unregistered_provider,
  };
  for (const PrepareMismatch mismatch : cases) {
    const bool registered_binding = mismatch != PrepareMismatch::unregistered_provider;
    FreshPreparationFixture fixture("fresh.prepare", registered_binding);
    if (!fixture.ready()) return expect(false, "fresh preparation fixture setup failed");
    ProviderRouteRequirements requirements = fixture.requirements();
    ProviderOutcome expected = ProviderOutcome::route_mismatch;
    std::optional<RouteSpec> attempted_route(fixture.route_spec());
    std::optional<CommunicationContract> alternate_contract;
    std::optional<EndpointSpec> alternate_source;
    std::optional<EndpointSpec> alternate_destination;
    const auto replace_route = [&](const std::string_view route_id,
                                   const std::string_view source_id,
                                   const std::string_view destination_id,
                                   const std::string_view digest,
                                   const std::string_view provider_id,
                                   const CommunicationContract& contract) {
      const auto source = EndpointSpec::create(
          {source_id, digest, provider_id, EndpointDirection::produce}, contract);
      const auto destination = EndpointSpec::create(
          {destination_id, digest, provider_id, EndpointDirection::consume}, contract);
      if (!source.has_value() || !destination.has_value()) return false;
      alternate_source.reset();
      alternate_source.emplace(*source.value());
      alternate_destination.reset();
      alternate_destination.emplace(*destination.value());
      const auto route = RouteSpec::create(
          {route_id, digest, provider_id}, *alternate_source, *alternate_destination);
      if (!route.has_value()) return false;
      attempted_route.reset();
      attempted_route.emplace(*route.value());
      return true;
    };
    bool alternate_ready = true;
    switch (mismatch) {
      case PrepareMismatch::contract_version:
        requirements.provider_contract_version = "2.0.0";
        expected = ProviderOutcome::unsupported_contract_version;
        break;
      case PrepareMismatch::interaction:
        requirements.interaction_kind = InteractionKind::service_request;
        expected = ProviderOutcome::unsupported_interaction;
        break;
      case PrepareMismatch::delivery:
        requirements.delivery = DeliveryCapability::reliable;
        expected = ProviderOutcome::unsupported_delivery;
        break;
      case PrepareMismatch::ordering:
        requirements.ordering = OrderingCapability::unordered;
        expected = ProviderOutcome::unsupported_ordering;
        break;
      case PrepareMismatch::zero_payload:
        requirements.maximum_payload_bytes = 0U;
        expected = ProviderOutcome::payload_limit_exceeded;
        break;
      case PrepareMismatch::excessive_payload:
        requirements.maximum_payload_bytes = 17U;
        expected = ProviderOutcome::payload_limit_exceeded;
        break;
      case PrepareMismatch::zero_queue:
        requirements.queue_capacity = 0U;
        expected = ProviderOutcome::queue_limit_exceeded;
        break;
      case PrepareMismatch::excessive_queue:
        requirements.queue_capacity = 2U;
        expected = ProviderOutcome::queue_limit_exceeded;
        break;
      case PrepareMismatch::route_identity:
        alternate_ready = replace_route(
            "route.other", fixture.source_spec().endpoint_id().value(),
            fixture.destination_spec().endpoint_id().value(), kDigest,
            fixture.route_spec().provider_id().value(), fixture.contract());
        break;
      case PrepareMismatch::source_identity:
        alternate_ready = replace_route(
            fixture.route_spec().route_id().value(), "source.other",
            fixture.destination_spec().endpoint_id().value(), kDigest,
            fixture.route_spec().provider_id().value(), fixture.contract());
        break;
      case PrepareMismatch::destination_identity:
        alternate_ready = replace_route(
            fixture.route_spec().route_id().value(),
            fixture.source_spec().endpoint_id().value(), "destination.other", kDigest,
            fixture.route_spec().provider_id().value(), fixture.contract());
        break;
      case PrepareMismatch::plan_digest:
        alternate_ready = replace_route(
            fixture.route_spec().route_id().value(),
            fixture.source_spec().endpoint_id().value(),
            fixture.destination_spec().endpoint_id().value(), kOtherDigest,
            fixture.route_spec().provider_id().value(), fixture.contract());
        break;
      case PrepareMismatch::provider_identity:
        alternate_ready = replace_route(
            fixture.route_spec().route_id().value(),
            fixture.source_spec().endpoint_id().value(),
            fixture.destination_spec().endpoint_id().value(), kDigest,
            "provider.other", fixture.contract());
        break;
      case PrepareMismatch::contract: {
        const auto contract = CommunicationContract::create(
            {"contract.other", "1.0.0", "interface.other", "schema.other", "1.0.0",
             InteractionKind::message_event, EndpointDirection::produce,
             EndpointDirection::consume});
        if (!contract.has_value()) {
          alternate_ready = false;
          break;
        }
        alternate_contract.emplace(*contract.value());
        alternate_ready = replace_route(
            fixture.route_spec().route_id().value(),
            fixture.source_spec().endpoint_id().value(),
            fixture.destination_spec().endpoint_id().value(), kDigest,
            fixture.route_spec().provider_id().value(), *alternate_contract);
        break;
      }
      case PrepareMismatch::unregistered_provider:
        expected = ProviderOutcome::provider_mismatch;
        break;
    }
    if (!alternate_ready || !attempted_route.has_value()) {
      return expect(false, "fresh preparation alternate declaration failed");
    }
    const auto route_before = fixture.lifecycle().route_snapshot(fixture.route_handle());
    const auto source_before = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
    const auto destination_before =
        fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
    const auto rejected = fixture.composition().prepare_route(
        fixture.lifecycle(), *attempted_route, fixture.route_handle(),
        fixture.source_handle(), fixture.destination_handle(), requirements);
    const auto route_after = fixture.lifecycle().route_snapshot(fixture.route_handle());
    const auto source_after = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
    const auto destination_after =
        fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
    if (!expect(rejected.outcome() == expected && !rejected.has_value(),
                "fresh preparation mismatch outcome differs") ||
        !expect(fixture.provider().prepare_calls() == 0U &&
                    fixture.provider().activate_calls() == 0U &&
                    fixture.provider().submit_calls() == 0U,
                "fresh preparation mismatch reached provider dispatch") ||
        !expect(route_before.has_value() && route_after.has_value() &&
                    *route_before.value() == *route_after.value() &&
                    source_before.has_value() && source_after.has_value() &&
                    *source_before.value() == *source_after.value() &&
                    destination_before.has_value() && destination_after.has_value() &&
                    *destination_before.value() == *destination_after.value(),
                "fresh preparation mismatch mutated lifecycle state")) {
      return false;
    }
  }
  return true;
}

/** Verify stale route and endpoint generations reject before provider preparation. */
[[nodiscard]] bool test_prepare_generation_rejection() {
  const auto run = [](const int stale_resource) {
    const auto contract = CommunicationContract::create(
        {"contract.generation", "1.0.0", "interface.generation", "schema.generation",
         "1.0.0", InteractionKind::message_event, EndpointDirection::produce,
         EndpointDirection::consume});
    if (!contract.has_value()) return false;
    const auto source = EndpointSpec::create(
        {"source.generation", kDigest, "provider.generation", EndpointDirection::produce},
        *contract.value());
    const auto destination = EndpointSpec::create(
        {"destination.generation", kDigest, "provider.generation", EndpointDirection::consume},
        *contract.value());
    if (!source.has_value() || !destination.has_value()) return false;
    const auto route = RouteSpec::create(
        {"route.generation", kDigest, "provider.generation"}, *source.value(),
        *destination.value());
    const auto lifecycle_configuration = LifecycleConfiguration::create({2U, 1U});
    const auto registry_configuration = ProviderRegistryConfiguration::create(1U);
    if (!route.has_value() || !lifecycle_configuration.has_value() ||
        !registry_configuration.has_value()) return false;
    LifecycleController lifecycle(*lifecycle_configuration.value());
    const auto source_old = lifecycle.declare_endpoint(*source.value());
    const auto destination_old = lifecycle.declare_endpoint(*destination.value());
    if (!source_old.has_value() || !destination_old.has_value() ||
        !lifecycle.validate_endpoint(*source_old.value()).has_value() ||
        !lifecycle.validate_endpoint(*destination_old.value()).has_value()) return false;
    std::optional<EndpointHandle> source_current(*source_old.value());
    std::optional<EndpointHandle> destination_current(*destination_old.value());
    if (stale_resource == 1) {
      if (!lifecycle.fail_endpoint(*source_old.value()).has_value() ||
          !lifecycle.close_endpoint(*source_old.value()).has_value()) return false;
      const auto recreated = lifecycle.declare_endpoint(*source.value());
      if (!recreated.has_value()) return false;
      source_current.reset();
      source_current.emplace(*recreated.value());
      if (
          !lifecycle.validate_endpoint(*source_current).has_value()) return false;
    } else if (stale_resource == 2) {
      if (!lifecycle.fail_endpoint(*destination_old.value()).has_value() ||
          !lifecycle.close_endpoint(*destination_old.value()).has_value()) return false;
      const auto recreated = lifecycle.declare_endpoint(*destination.value());
      if (!recreated.has_value()) return false;
      destination_current.reset();
      destination_current.emplace(*recreated.value());
      if (
          !lifecycle.validate_endpoint(*destination_current).has_value()) return false;
    }
    if (!lifecycle.activate_endpoint(*source_current).has_value() ||
        !lifecycle.activate_endpoint(*destination_current).has_value()) return false;
    const auto route_old = lifecycle.declare_route(*route.value());
    if (!route_old.has_value() ||
        !lifecycle.validate_route(*route_old.value(), *source_current,
                                  *destination_current).has_value()) return false;
    std::optional<RouteHandle> route_current(*route_old.value());
    if (stale_resource == 0) {
      if (!lifecycle.fail_route(*route_old.value()).has_value() ||
          !lifecycle.close_route(*route_old.value()).has_value()) return false;
      const auto recreated = lifecycle.declare_route(*route.value());
      if (!recreated.has_value()) return false;
      route_current.reset();
      route_current.emplace(*recreated.value());
      if (
          !lifecycle.validate_route(*route_current, *source_current,
                                    *destination_current).has_value()) return false;
    }
    const auto provider_descriptor = ProviderDescriptor::create(
        {"provider.generation", "1.0.0", "source.fixture.generation", 0x0FU,
         delivery_capability_bit(DeliveryCapability::best_effort),
         ordering_capability_bit(OrderingCapability::per_route_fifo), 16U, 1U, 1U});
    if (!provider_descriptor.has_value()) return false;
    test::IndependentProvider provider(*provider_descriptor.value(),
                                       9200U + static_cast<std::uint64_t>(stale_resource));
    ProviderComposition composition(*registry_configuration.value());
    if (composition.register_provider(provider).outcome() != ProviderOutcome::registered) {
      return false;
    }
    const ProviderRouteRequirements requirements{
        "1.0.0", InteractionKind::message_event, DeliveryCapability::best_effort,
        OrderingCapability::per_route_fifo, 16U, 1U};
    const RouteHandle& attempted_route =
        stale_resource == 0 ? *route_old.value() : *route_current;
    const EndpointHandle& attempted_source =
        stale_resource == 1 ? *source_old.value() : *source_current;
    const EndpointHandle& attempted_destination =
        stale_resource == 2 ? *destination_old.value() : *destination_current;
    const auto rejected = composition.prepare_route(
        lifecycle, *route.value(), attempted_route, attempted_source,
        attempted_destination, requirements);
    if (provider.prepare_calls() != 0U) return false;
    const auto accepted = composition.prepare_route(
        lifecycle, *route.value(), *route_current, *source_current,
        *destination_current, requirements);
    return rejected.outcome() == ProviderOutcome::lifecycle_mismatch &&
           !rejected.has_value() && accepted.outcome() == ProviderOutcome::prepared &&
           accepted.has_value() && provider.prepare_calls() == 1U;
  };
  return expect(run(0), "stale route generation mutated or reached the provider") &&
         expect(run(1), "stale source generation mutated or reached the provider") &&
         expect(run(2), "stale destination generation mutated or reached the provider");
}

/** Lifecycle mutations covered before any provider activation dispatch. */
enum class ActivationMismatch {
  foreign_owner,
  route_failed,
  route_closed,
  route_recreated,
  source_failed,
  source_closed,
  source_recreated,
  destination_failed,
  destination_closed,
  destination_recreated,
};

/** Verify the complete failed, closed, recreated, stale, and foreign activation matrix. */
[[nodiscard]] bool test_activation_rejection_matrix() {
  const std::array cases{
      ActivationMismatch::foreign_owner,
      ActivationMismatch::route_failed,
      ActivationMismatch::route_closed,
      ActivationMismatch::route_recreated,
      ActivationMismatch::source_failed,
      ActivationMismatch::source_closed,
      ActivationMismatch::source_recreated,
      ActivationMismatch::destination_failed,
      ActivationMismatch::destination_closed,
      ActivationMismatch::destination_recreated,
  };
  for (const ActivationMismatch mismatch : cases) {
    FreshPreparationFixture fixture("activation.matrix");
    if (!fixture.ready()) return expect(false, "activation matrix fixture setup failed");
    const auto prepared = fixture.prepare();
    if (!prepared.has_value() || !fixture.activate_endpoints()) {
      return expect(false, "activation matrix preparation failed");
    }
    std::optional<RouteHandle> recreated_route;
    std::optional<EndpointHandle> recreated_source;
    std::optional<EndpointHandle> recreated_destination;
    std::optional<LifecycleController> foreign_lifecycle;
    LifecycleController* attempted_lifecycle = &fixture.lifecycle();
    bool mutation_ready = true;
    switch (mismatch) {
      case ActivationMismatch::foreign_owner: {
        const auto configuration = LifecycleConfiguration::create({2U, 2U});
        if (!configuration.has_value()) {
          mutation_ready = false;
          break;
        }
        foreign_lifecycle.emplace(*configuration.value());
        attempted_lifecycle = &*foreign_lifecycle;
        break;
      }
      case ActivationMismatch::route_failed:
        mutation_ready = fixture.lifecycle().fail_route(fixture.route_handle()).has_value();
        break;
      case ActivationMismatch::route_closed:
      case ActivationMismatch::route_recreated:
        mutation_ready = fixture.lifecycle().fail_route(fixture.route_handle()).has_value() &&
                         fixture.lifecycle().close_route(fixture.route_handle()).has_value();
        if (mutation_ready && mismatch == ActivationMismatch::route_recreated) {
          const auto recreated = fixture.lifecycle().declare_route(fixture.route_spec());
          mutation_ready = recreated.has_value();
          if (mutation_ready) {
            recreated_route.emplace(*recreated.value());
            mutation_ready = fixture.lifecycle()
                                 .validate_route(*recreated_route, fixture.source_handle(),
                                                 fixture.destination_handle())
                                 .has_value();
          }
        }
        break;
      case ActivationMismatch::source_failed:
        mutation_ready = fixture.lifecycle().fail_endpoint(fixture.source_handle()).has_value();
        break;
      case ActivationMismatch::source_closed:
      case ActivationMismatch::source_recreated:
        mutation_ready = fixture.lifecycle().fail_route(fixture.route_handle()).has_value() &&
                         fixture.lifecycle().close_route(fixture.route_handle()).has_value() &&
                         fixture.lifecycle().fail_endpoint(fixture.source_handle()).has_value() &&
                         fixture.lifecycle().close_endpoint(fixture.source_handle()).has_value();
        if (mutation_ready && mismatch == ActivationMismatch::source_recreated) {
          const auto recreated = fixture.lifecycle().declare_endpoint(fixture.source_spec());
          mutation_ready = recreated.has_value();
          if (mutation_ready) {
            recreated_source.emplace(*recreated.value());
            mutation_ready =
                fixture.lifecycle().validate_endpoint(*recreated_source).has_value() &&
                fixture.lifecycle().activate_endpoint(*recreated_source).has_value();
          }
          if (mutation_ready) {
            const auto route = fixture.lifecycle().declare_route(fixture.route_spec());
            mutation_ready = route.has_value();
            if (mutation_ready) {
              recreated_route.emplace(*route.value());
              mutation_ready = fixture.lifecycle()
                                   .validate_route(*recreated_route, *recreated_source,
                                                   fixture.destination_handle())
                                   .has_value();
            }
          }
        }
        break;
      case ActivationMismatch::destination_failed:
        mutation_ready =
            fixture.lifecycle().fail_endpoint(fixture.destination_handle()).has_value();
        break;
      case ActivationMismatch::destination_closed:
      case ActivationMismatch::destination_recreated:
        mutation_ready =
            fixture.lifecycle().fail_route(fixture.route_handle()).has_value() &&
            fixture.lifecycle().close_route(fixture.route_handle()).has_value() &&
            fixture.lifecycle().fail_endpoint(fixture.destination_handle()).has_value() &&
            fixture.lifecycle().close_endpoint(fixture.destination_handle()).has_value();
        if (mutation_ready && mismatch == ActivationMismatch::destination_recreated) {
          const auto recreated =
              fixture.lifecycle().declare_endpoint(fixture.destination_spec());
          mutation_ready = recreated.has_value();
          if (mutation_ready) {
            recreated_destination.emplace(*recreated.value());
            mutation_ready =
                fixture.lifecycle().validate_endpoint(*recreated_destination).has_value() &&
                fixture.lifecycle().activate_endpoint(*recreated_destination).has_value();
          }
          if (mutation_ready) {
            const auto route = fixture.lifecycle().declare_route(fixture.route_spec());
            mutation_ready = route.has_value();
            if (mutation_ready) {
              recreated_route.emplace(*route.value());
              mutation_ready = fixture.lifecycle()
                                   .validate_route(*recreated_route, fixture.source_handle(),
                                                   *recreated_destination)
                                   .has_value();
            }
          }
        }
        break;
    }
    if (!mutation_ready) {
      return expect(false, "activation matrix mutation setup failed at case " +
                               std::to_string(static_cast<int>(mismatch)));
    }

    const auto provider_before = fixture.composition().route_state(*prepared.value());
    const auto route_before = fixture.lifecycle().route_snapshot(fixture.route_handle());
    const auto source_before = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
    const auto destination_before =
        fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
    std::optional<Result<LifecycleSnapshot>> recreated_route_before;
    std::optional<Result<LifecycleSnapshot>> recreated_source_before;
    std::optional<Result<LifecycleSnapshot>> recreated_destination_before;
    if (recreated_route.has_value()) {
      recreated_route_before.emplace(fixture.lifecycle().route_snapshot(*recreated_route));
    }
    if (recreated_source.has_value()) {
      recreated_source_before.emplace(
          fixture.lifecycle().endpoint_snapshot(*recreated_source));
    }
    if (recreated_destination.has_value()) {
      recreated_destination_before.emplace(
          fixture.lifecycle().endpoint_snapshot(*recreated_destination));
    }
    const auto rejected =
        fixture.composition().activate_route(*prepared.value(), *attempted_lifecycle);
    const auto provider_after = fixture.composition().route_state(*prepared.value());
    const auto route_after = fixture.lifecycle().route_snapshot(fixture.route_handle());
    const auto source_after = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
    const auto destination_after =
        fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
    std::optional<Result<LifecycleSnapshot>> recreated_route_after;
    std::optional<Result<LifecycleSnapshot>> recreated_source_after;
    std::optional<Result<LifecycleSnapshot>> recreated_destination_after;
    if (recreated_route.has_value()) {
      recreated_route_after.emplace(fixture.lifecycle().route_snapshot(*recreated_route));
    }
    if (recreated_source.has_value()) {
      recreated_source_after.emplace(
          fixture.lifecycle().endpoint_snapshot(*recreated_source));
    }
    if (recreated_destination.has_value()) {
      recreated_destination_after.emplace(
          fixture.lifecycle().endpoint_snapshot(*recreated_destination));
    }
    if (!expect(rejected.outcome() == ProviderOutcome::lifecycle_mismatch &&
                    rejected.diagnostic_code() == "XCOM-PROV-E022" &&
                    rejected.diagnostic_message() ==
                        "exact lifecycle binding or state differs",
                "activation matrix outcome or diagnostic bytes differ") ||
        !expect(fixture.provider().activate_calls() == 0U,
                "activation mismatch reached provider dispatch") ||
        !expect(same_snapshot(provider_before, provider_after),
                "activation mismatch mutated prepared provider state") ||
        !expect(same_lifecycle_observation(route_before, route_after) &&
                    same_lifecycle_observation(source_before, source_after) &&
                    same_lifecycle_observation(destination_before, destination_after) &&
                    same_optional_lifecycle_observation(recreated_route_before,
                                                        recreated_route_after) &&
                    same_optional_lifecycle_observation(recreated_source_before,
                                                        recreated_source_after) &&
                    same_optional_lifecycle_observation(recreated_destination_before,
                                                        recreated_destination_after),
                "activation mismatch mutated lifecycle state")) {
      return false;
    }
  }
  return true;
}

/** Verify active first-route state survives exact fixed provider route-capacity rejection. */
[[nodiscard]] bool test_route_capacity_after_activation() {
  FreshPreparationFixture fixture("capacity.activation");
  if (!fixture.ready()) return expect(false, "route capacity fixture setup failed");
  const auto first = fixture.prepare();
  if (!first.has_value() || !fixture.activate_endpoints() ||
      fixture.composition().activate_route(*first.value(), fixture.lifecycle()).outcome() !=
          ProviderOutcome::activated) {
    return expect(false, "first route activation failed");
  }
  const auto second_spec = RouteSpec::create(
      {"route.capacity.second", kDigest, fixture.route_spec().provider_id().value()},
      fixture.source_spec(), fixture.destination_spec());
  if (!second_spec.has_value()) return expect(false, "second route declaration failed");
  const auto second_handle = fixture.lifecycle().declare_route(*second_spec.value());
  if (!second_handle.has_value() ||
      !fixture.lifecycle()
           .validate_route(*second_handle.value(), fixture.source_handle(),
                           fixture.destination_handle())
           .has_value()) {
    return expect(false, "second lifecycle route setup failed");
  }
  const auto provider_before = fixture.composition().route_state(*first.value());
  const auto first_route_before = fixture.lifecycle().route_snapshot(fixture.route_handle());
  const auto second_route_before =
      fixture.lifecycle().route_snapshot(*second_handle.value());
  const auto source_before = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
  const auto destination_before =
      fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
  const auto rejected = fixture.composition().prepare_route(
      fixture.lifecycle(), *second_spec.value(), *second_handle.value(),
      fixture.source_handle(), fixture.destination_handle(), fixture.requirements());
  const auto provider_after = fixture.composition().route_state(*first.value());
  const auto first_route_after = fixture.lifecycle().route_snapshot(fixture.route_handle());
  const auto second_route_after =
      fixture.lifecycle().route_snapshot(*second_handle.value());
  const auto source_after = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
  const auto destination_after =
      fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
  return expect(rejected.outcome() == ProviderOutcome::route_capacity_exhausted &&
                    !rejected.has_value() &&
                    rejected.diagnostic_code() == "XCOM-PROV-E020" &&
                    rejected.diagnostic_message() == "provider route storage is full",
                "route capacity outcome or diagnostic bytes differ") &&
         expect(fixture.provider().prepare_calls() == 2U &&
                    fixture.provider().activate_calls() == 1U,
                "route capacity dispatch counts differ") &&
         expect(same_snapshot(provider_before, provider_after),
                "route capacity rejection mutated active provider route") &&
         expect(same_lifecycle_observation(first_route_before, first_route_after) &&
                    same_lifecycle_observation(second_route_before, second_route_after) &&
                    same_lifecycle_observation(source_before, source_after) &&
                    same_lifecycle_observation(destination_before, destination_after),
                "route capacity rejection mutated lifecycle state");
}

/** Verify every item/payload mismatch rejects before provider dispatch with no mutation. */
[[nodiscard]] bool test_fresh_submit_rejection_matrix() {
  FreshPreparationFixture fixture("submit.matrix");
  if (!fixture.ready()) return expect(false, "submit matrix fixture setup failed");
  const auto prepared = fixture.prepare();
  if (!prepared.has_value() || !fixture.activate_endpoints() ||
      fixture.composition().activate_route(*prepared.value(), fixture.lifecycle()).outcome() !=
          ProviderOutcome::activated) {
    return expect(false, "submit matrix route activation failed");
  }
  const std::array<std::byte, 1U> one{std::byte{1U}};
  const std::array<std::byte, 17U> oversized{};
  const auto check = [&](const Result<CommunicationItem>& item,
                         const ProviderOutcome expected) {
    if (!item.has_value()) return false;
    const auto provider_before = fixture.composition().route_state(*prepared.value());
    const auto route_before = fixture.lifecycle().route_snapshot(fixture.route_handle());
    const auto source_before = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
    const auto destination_before =
        fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
    const std::size_t dispatches_before = fixture.provider().submit_calls();
    const auto rejected = fixture.composition().submit(
        *prepared.value(), *item.value(), fixture.lifecycle());
    const auto provider_after = fixture.composition().route_state(*prepared.value());
    const auto route_after = fixture.lifecycle().route_snapshot(fixture.route_handle());
    const auto source_after = fixture.lifecycle().endpoint_snapshot(fixture.source_handle());
    const auto destination_after =
        fixture.lifecycle().endpoint_snapshot(fixture.destination_handle());
    const std::string_view code = expected == ProviderOutcome::item_mismatch
        ? "XCOM-PROV-E026"
        : "XCOM-PROV-E018";
    const std::string_view message = expected == ProviderOutcome::item_mismatch
        ? "item metadata differs from prepared route"
        : "payload limit exceeded";
    return rejected.outcome() == expected && rejected.diagnostic_code() == code &&
           rejected.diagnostic_message() == message &&
           fixture.provider().submit_calls() == dispatches_before &&
           same_snapshot(provider_before, provider_after) &&
           same_lifecycle_observation(route_before, route_after) &&
           same_lifecycle_observation(source_before, source_after) &&
           same_lifecycle_observation(destination_before, destination_after);
  };
  const std::array binding_mismatches{
      fixture.item_with_binding(
          "source.other", fixture.route_spec().route_id().value(),
          fixture.route_spec().provider_id().value(), one),
      fixture.item_with_binding(
          fixture.source_spec().endpoint_id().value(), "route.other",
          fixture.route_spec().provider_id().value(), one),
      fixture.item_with_binding(
          fixture.source_spec().endpoint_id().value(),
          fixture.route_spec().route_id().value(), "provider.other", one),
  };
  for (const auto& item : binding_mismatches) {
    if (!expect(check(item, ProviderOutcome::item_mismatch),
                "binding mismatch dispatched or mutated state")) {
      return false;
    }
  }
  const auto make_contract_item = [&](const CommunicationContractInput& input) {
    const auto contract = CommunicationContract::create(input);
    if (!contract.has_value()) {
      return Result<CommunicationItem>::failure(*contract.diagnostics());
    }
    return CommunicationItem::create(
        {contract.value()->contract_id().value(), contract.value()->contract_version().value(),
         contract.value()->interface_id().value(),
         fixture.source_spec().endpoint_id().value(), contract.value()->schema_id().value(),
         contract.value()->schema_version().value(), contract.value()->interaction_kind(),
         OriginKind::component, Timestamp(1), "clock.submit", "correlation.submit",
         "causation.submit", fixture.route_spec().route_id().value(),
         fixture.route_spec().provider_id().value(), one},
        *contract.value());
  };
  const std::array contract_mismatches{
      make_contract_item({"contract.other", "1.0.0", "interface.submit.matrix",
                          "schema.submit.matrix", "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit.matrix", "2.0.0", "interface.submit.matrix",
                          "schema.submit.matrix", "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit.matrix", "1.0.0", "interface.other",
                          "schema.submit.matrix", "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit.matrix", "1.0.0", "interface.submit.matrix",
                          "schema.other", "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit.matrix", "1.0.0", "interface.submit.matrix",
                          "schema.submit.matrix", "2.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit.matrix", "1.0.0", "interface.submit.matrix",
                          "schema.submit.matrix", "1.0.0", InteractionKind::service_request,
                          EndpointDirection::request, EndpointDirection::respond}),
  };
  for (const auto& item : contract_mismatches) {
    if (!expect(check(item, ProviderOutcome::item_mismatch),
                "contract mismatch dispatched or mutated state")) {
      return false;
    }
  }
  const auto oversized_item = fixture.item_with_binding(
      fixture.source_spec().endpoint_id().value(),
      fixture.route_spec().route_id().value(), fixture.route_spec().provider_id().value(),
      oversized);
  return expect(check(oversized_item, ProviderOutcome::payload_limit_exceeded),
                "payload mismatch dispatched or mutated state");
}

/** Verify item, payload, provider, lifecycle, and inactive-state rejection with zero delivery. */
[[nodiscard]] bool test_submit_rejection() {
  auto scenario = std::make_unique<Scenario>(InteractionKind::message_event, 2U, 1U,
                                             "submit");
  auto foreign = std::make_unique<Scenario>(InteractionKind::message_event, 2U, 1U,
                                            "foreign");
  auto inactive = std::make_unique<Scenario>(InteractionKind::message_event, 2U, 1U,
                                             "inactive", false);
  if (!scenario->ready() || !foreign->ready() || !inactive->ready()) {
    return expect(false, "submit rejection fixture setup failed");
  }
  const std::array<std::byte, 1U> one{std::byte{1U}};
  const std::array<std::byte, 2U> two{std::byte{1U}, std::byte{2U}};
  const auto wrong_endpoint = scenario->item_with_binding(
      "source.other", scenario->route_spec().route_id().value(), "provider.loopback", one);
  const auto wrong_route = scenario->item_with_binding(
      scenario->source_spec().endpoint_id().value(), "route.other", "provider.loopback", one);
  const auto wrong_provider = scenario->item_with_binding(
      scenario->source_spec().endpoint_id().value(), scenario->route_spec().route_id().value(),
      "provider.other", one);
  const auto oversized = scenario->item_with_binding(
      scenario->source_spec().endpoint_id().value(), scenario->route_spec().route_id().value(),
      "provider.loopback", two);
  const auto valid = scenario->item(1U);
  if (!wrong_endpoint.has_value() || !wrong_route.has_value() || !wrong_provider.has_value() ||
      !oversized.has_value() || !valid.has_value()) {
    return expect(false, "submit rejection item construction failed");
  }
  for (const CommunicationItem* item :
       {wrong_endpoint.value(), wrong_route.value(), wrong_provider.value()}) {
    if (!expect(scenario->composition()
                    .submit(scenario->provider_handle(), *item, scenario->lifecycle())
                    .outcome() == ProviderOutcome::item_mismatch,
                "mismatched item was accepted")) {
      return false;
    }
  }
  const auto make_contract_item = [&scenario, &one](
                                      const CommunicationContractInput& contract_input) {
    const auto contract = CommunicationContract::create(contract_input);
    if (!contract.has_value()) return Result<CommunicationItem>::failure(*contract.diagnostics());
    return CommunicationItem::create(
        {contract.value()->contract_id().value(), contract.value()->contract_version().value(),
         contract.value()->interface_id().value(), scenario->source_spec().endpoint_id().value(),
         contract.value()->schema_id().value(), contract.value()->schema_version().value(),
         contract.value()->interaction_kind(), OriginKind::component, Timestamp(1),
         "clock.fixture", "correlation.mismatch", "causation.mismatch",
         scenario->route_spec().route_id().value(), "provider.loopback", one},
        *contract.value());
  };
  const std::array mismatched_contract_items{
      make_contract_item({"contract.other", "1.0.0", "interface.submit", "schema.submit",
                          "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit", "2.0.0", "interface.submit", "schema.submit",
                          "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit", "1.0.0", "interface.other", "schema.submit",
                          "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit", "1.0.0", "interface.submit", "schema.other",
                          "1.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit", "1.0.0", "interface.submit", "schema.submit",
                          "2.0.0", InteractionKind::message_event,
                          EndpointDirection::produce, EndpointDirection::consume}),
      make_contract_item({"contract.submit", "1.0.0", "interface.submit", "schema.submit",
                          "1.0.0", InteractionKind::service_request,
                          EndpointDirection::request, EndpointDirection::respond}),
  };
  for (const auto& item : mismatched_contract_items) {
    if (!item.has_value() ||
        !expect(scenario->composition()
                    .submit(scenario->provider_handle(), *item.value(), scenario->lifecycle())
                    .outcome() == ProviderOutcome::item_mismatch,
                "contract/schema/version/kind mismatch was accepted")) {
      return false;
    }
    const auto unchanged = scenario->composition().route_state(scenario->provider_handle());
    if (!expect(unchanged.has_value() && unchanged.value()->queued_items() == 0U,
                "item mismatch mutated the destination queue")) {
      return false;
    }
  }
  if (!expect(scenario->composition()
                  .submit(scenario->provider_handle(), *oversized.value(), scenario->lifecycle())
                  .outcome() == ProviderOutcome::payload_limit_exceeded,
              "over-route payload was accepted") ||
      !expect(foreign->composition()
                  .submit(scenario->provider_handle(), *valid.value(), foreign->lifecycle())
                  .outcome() == ProviderOutcome::invalid_provider_route_handle,
              "foreign composition accepted a route handle") ||
      !expect(scenario->composition()
                  .submit(scenario->provider_handle(), *valid.value(), foreign->lifecycle())
                  .outcome() == ProviderOutcome::lifecycle_mismatch,
              "foreign lifecycle owner was accepted")) {
    return false;
  }
  const auto inactive_item = inactive->item(1U);
  if (!inactive_item.has_value() ||
      !expect(inactive->composition()
                  .submit(inactive->provider_handle(), *inactive_item.value(), inactive->lifecycle())
                  .outcome() == ProviderOutcome::inactive_route,
              "prepared route accepted an item")) {
    return false;
  }
  const auto state = scenario->composition().route_state(scenario->provider_handle());
  return expect(state.has_value() && state.value()->queued_items() == 0U,
                "rejected submissions delivered an item");
}

/** Verify closed-resource recreation invalidates the prior provider-route generation. */
[[nodiscard]] bool test_stale_handle_after_recreation() {
  Scenario scenario(InteractionKind::signal_state_update, 1U, 8U, "recreate");
  if (!scenario.ready()) {
    return expect(false, "recreation scenario setup failed");
  }
  const ProviderRouteHandle old_handle(scenario.provider_handle());
  if (scenario.composition().drain_route(old_handle, scenario.lifecycle()).outcome() !=
          ProviderOutcome::draining ||
      scenario.composition().close_route(old_handle, scenario.lifecycle()).outcome() !=
          ProviderOutcome::closed) {
    return expect(false, "old route could not close");
  }
  const auto recreated_lifecycle = scenario.lifecycle().declare_route(scenario.route_spec());
  if (!recreated_lifecycle.has_value() ||
      !scenario.lifecycle()
           .validate_route(*recreated_lifecycle.value(), scenario.source_handle(),
                           scenario.destination_handle())
           .has_value()) {
    return expect(false, "lifecycle route recreation failed");
  }
  const auto recreated = scenario.composition().prepare_route(
      scenario.lifecycle(), scenario.route_spec(), *recreated_lifecycle.value(),
      scenario.source_handle(), scenario.destination_handle(), scenario.requirements());
  if (!recreated.has_value() ||
      scenario.composition().activate_route(*recreated.value(), scenario.lifecycle()).outcome() !=
          ProviderOutcome::activated) {
    return expect(false, "provider route recreation failed");
  }
  return expect(scenario.composition().route_state(old_handle).outcome() ==
                    ProviderOutcome::invalid_provider_route_handle,
                "stale provider route handle remained usable") &&
         expect(recreated.value()->provider_route_generation() !=
                    old_handle.provider_route_generation() &&
                    recreated.value()->lifecycle_route_generation() !=
                        old_handle.lifecycle_route_generation(),
                "recreated route did not advance both generations");
}

/** Verify failed lifecycle resources reconcile only as interrupted. */
[[nodiscard]] bool test_interrupted_reconciliation() {
  Scenario scenario(InteractionKind::service_response, 1U, 8U, "interrupt");
  if (!scenario.ready()) {
    return expect(false, "interruption scenario setup failed");
  }
  if (!scenario.lifecycle().fail_route(scenario.route_handle()).has_value()) {
    return expect(false, "lifecycle interruption fixture failed");
  }
  return expect(scenario.composition()
                    .reconcile_route(scenario.provider_handle(), scenario.lifecycle())
                    .outcome() == ProviderOutcome::interrupted_resource,
                "failed lifecycle resource was inferred healthy");
}

/** Verify every public outcome, diagnostic code, and message byte sequence exactly. */
[[nodiscard]] bool test_exact_provider_diagnostics() {
  struct ExpectedDiagnostic final {
    ProviderOutcome outcome;
    std::string_view text;
    std::string_view code;
    std::string_view message;
  };
  const std::array expected{
      ExpectedDiagnostic{ProviderOutcome::registered, "registered", "XCOM-PROV-S001",
                         "explicit source-linked provider registered"},
      ExpectedDiagnostic{ProviderOutcome::prepared, "prepared", "XCOM-PROV-S002",
                         "exact provider route prepared without traffic"},
      ExpectedDiagnostic{ProviderOutcome::activated, "activated", "XCOM-PROV-S003",
                         "exact provider route activated"},
      ExpectedDiagnostic{ProviderOutcome::accepted, "accepted", "XCOM-PROV-S004",
                         "item copied into bounded provider queue"},
      ExpectedDiagnostic{ProviderOutcome::received, "received", "XCOM-PROV-S005",
                         "oldest queued item returned by value"},
      ExpectedDiagnostic{ProviderOutcome::draining, "draining", "XCOM-PROV-S006",
                         "new submissions stopped; queued items retained"},
      ExpectedDiagnostic{ProviderOutcome::closed, "closed", "XCOM-PROV-S007",
                         "empty provider route resource released"},
      ExpectedDiagnostic{ProviderOutcome::reconciled, "reconciled", "XCOM-PROV-S008",
                         "provider and lifecycle state match exactly"},
      ExpectedDiagnostic{ProviderOutcome::queue_empty, "queue-empty", "XCOM-PROV-I009",
                         "route queue contains no accepted item"},
      ExpectedDiagnostic{ProviderOutcome::queue_saturated, "queue-saturated",
                         "XCOM-PROV-E010", "route queue is full; new item rejected"},
      ExpectedDiagnostic{ProviderOutcome::invalid_descriptor, "invalid-descriptor",
                         "XCOM-PROV-E011", "provider descriptor is invalid"},
      ExpectedDiagnostic{ProviderOutcome::duplicate_provider, "duplicate-provider",
                         "XCOM-PROV-E012", "provider identity is already registered"},
      ExpectedDiagnostic{ProviderOutcome::provider_capacity_exhausted,
                         "provider-capacity-exhausted", "XCOM-PROV-E013",
                         "provider registry is full"},
      ExpectedDiagnostic{ProviderOutcome::unsupported_contract_version,
                         "unsupported-contract-version", "XCOM-PROV-E014",
                         "provider contract version unsupported"},
      ExpectedDiagnostic{ProviderOutcome::unsupported_interaction,
                         "unsupported-interaction", "XCOM-PROV-E015",
                         "interaction family unsupported"},
      ExpectedDiagnostic{ProviderOutcome::unsupported_delivery, "unsupported-delivery",
                         "XCOM-PROV-E016", "delivery capability unsupported"},
      ExpectedDiagnostic{ProviderOutcome::unsupported_ordering, "unsupported-ordering",
                         "XCOM-PROV-E017", "ordering capability unsupported"},
      ExpectedDiagnostic{ProviderOutcome::payload_limit_exceeded,
                         "payload-limit-exceeded", "XCOM-PROV-E018",
                         "payload limit exceeded"},
      ExpectedDiagnostic{ProviderOutcome::queue_limit_exceeded, "queue-limit-exceeded",
                         "XCOM-PROV-E019", "queue limit invalid or exceeded"},
      ExpectedDiagnostic{ProviderOutcome::route_capacity_exhausted,
                         "route-capacity-exhausted", "XCOM-PROV-E020",
                         "provider route storage is full"},
      ExpectedDiagnostic{ProviderOutcome::invalid_provider_route_handle,
                         "invalid-provider-route-handle", "XCOM-PROV-E021",
                         "provider route handle is inauthentic"},
      ExpectedDiagnostic{ProviderOutcome::lifecycle_mismatch, "lifecycle-mismatch",
                         "XCOM-PROV-E022", "exact lifecycle binding or state differs"},
      ExpectedDiagnostic{ProviderOutcome::inactive_route, "inactive-route",
                         "XCOM-PROV-E023", "provider route is not active"},
      ExpectedDiagnostic{ProviderOutcome::route_mismatch, "route-mismatch",
                         "XCOM-PROV-E024",
                         "route identity, digest, or generation differs"},
      ExpectedDiagnostic{ProviderOutcome::provider_mismatch, "provider-mismatch",
                         "XCOM-PROV-E025", "provider identity or instance differs"},
      ExpectedDiagnostic{ProviderOutcome::item_mismatch, "item-mismatch",
                         "XCOM-PROV-E026",
                         "item metadata differs from prepared route"},
      ExpectedDiagnostic{ProviderOutcome::queued_items_remain, "queued-items-remain",
                         "XCOM-PROV-E027", "route retains accepted queued items"},
      ExpectedDiagnostic{ProviderOutcome::interrupted_resource, "interrupted-resource",
                         "XCOM-PROV-E028",
                         "provider and lifecycle state cannot reconcile"},
  };
  for (const auto& item : expected) {
    if (!expect(to_string(item.outcome) == item.text &&
                    provider_diagnostic_code(item.outcome) == item.code &&
                    provider_diagnostic_message(item.outcome) == item.message,
                "provider diagnostic bytes differ")) {
      return false;
    }
  }
  return true;
}

}  // namespace

/** @return Zero when all provider-loopback negative checks pass. */
int main() {
  const bool passed =
      test_descriptor_and_registration_rejection() &&
      test_prepare_compatibility_rejection() && test_fresh_prepare_rejection_matrix() &&
      test_prepare_generation_rejection() &&
      test_activation_rejection_matrix() && test_route_capacity_after_activation() &&
      test_fresh_submit_rejection_matrix() && test_submit_rejection() &&
      test_stale_handle_after_recreation() && test_interrupted_reconciliation() &&
      test_foreign_composition_rejection() && test_exact_provider_diagnostics();
  return passed ? 0 : 1;
}
