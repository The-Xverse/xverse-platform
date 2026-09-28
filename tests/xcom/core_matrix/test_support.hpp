/**
 * @file test_support.hpp
 * @brief Self-contained T016 consolidated core test fixture and probe provider.
 * @ownership The fixture owns every contract, declaration, lifecycle resource, provider, registry,
 * and handle it builds; returned items are independent owned copies. The probe provider owns its
 * descriptor, binding, token, queue slot, and counters. No borrowed internal storage is exposed.
 * @lifetime Every fixture value and handle is bounded to the test case that constructs it; nothing is
 * process-scoped or static except the probe provider instance-identity counter.
 * @thread_safety Construction is single-threaded. Immutable values and snapshots support concurrent
 * const reads; mutating provider operations serialize through the accepted provider/composition mutex.
 * @failure A failed construction leaves ready() false and exposes nothing usable; no partial or
 * default value is substituted. No network, filesystem, process, or ambient access occurs here.
 */

#ifndef XVERSE_XCOM_CORE_MATRIX_TEST_SUPPORT_HPP
#define XVERSE_XCOM_CORE_MATRIX_TEST_SUPPORT_HPP

#include "xverse/xcom/loopback_provider.hpp"
#include "xverse/xcom/provider.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include <span>
#include <string>
#include <string_view>

namespace xverse::xcom::test {

/** One fixed, synthetic, non-sensitive 64-character lowercase hexadecimal plan digest. */
inline constexpr std::string_view kCoreDigest =
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

/** A second synthetic 64-character digest used only to prove exact-binding rejection. */
inline constexpr std::string_view kOtherCoreDigest =
    "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";

/** Declared interaction capability mask covering all four accepted families. */
inline constexpr std::uint8_t kAllInteractions = 0x0FU;

/**
 * @brief Return the accepted compatible source direction for one interaction family.
 * @param kind Interaction family.
 * @return The contract source direction for that family.
 * @failure This pure operation cannot fail.
 */
[[nodiscard]] inline EndpointDirection source_direction(const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::request
             : kind == InteractionKind::service_response ? EndpointDirection::respond
                                                         : EndpointDirection::produce;
}

/**
 * @brief Return the accepted compatible destination direction for one interaction family.
 * @param kind Interaction family.
 * @return The contract target direction for that family.
 * @failure This pure operation cannot fail.
 */
[[nodiscard]] inline EndpointDirection destination_direction(const InteractionKind kind) noexcept {
  return kind == InteractionKind::service_request
             ? EndpointDirection::respond
             : kind == InteractionKind::service_response ? EndpointDirection::request
                                                         : EndpointDirection::consume;
}

/**
 * @brief Build one valid contract for a caller-selected interaction family.
 * @param suffix Stable identity suffix keeping fixtures independent.
 * @param kind Interaction family.
 * @return Owned contract or core validation diagnostics.
 * @failure Invalid constructed input yields a non-empty diagnostic result.
 */
[[nodiscard]] inline Result<CommunicationContract> make_contract(const std::string_view suffix,
                                                                 const InteractionKind kind) {
  const std::string contract_id = "contract." + std::string(suffix);
  const std::string interface_id = "interface." + std::string(suffix);
  const std::string schema_id = "schema." + std::string(suffix);
  return CommunicationContract::create({contract_id, "1.0.0", interface_id, schema_id, "1.0.0",
                                        kind, source_direction(kind),
                                        destination_direction(kind)});
}

/**
 * @brief Build one valid descriptor with caller-selected claims and finite limits.
 * @param provider_id Stable logical provider identity.
 * @param interaction_mask Nonzero admitted interaction mask.
 * @param delivery_mask Nonzero admitted delivery mask.
 * @param ordering_mask Nonzero admitted ordering mask.
 * @param maximum_payload_bytes Finite per-item payload bound.
 * @param maximum_routes Finite route bound.
 * @param maximum_queue_items Finite per-route queue bound.
 * @return Owned descriptor assumed within the admitted vocabulary.
 * @failure Invalid boundaries would return a diagnostic result dereferenced by the caller.
 */
[[nodiscard]] inline ProviderDescriptor make_descriptor(
    const std::string_view provider_id, const std::uint8_t interaction_mask,
    const std::uint8_t delivery_mask, const std::uint8_t ordering_mask,
    const std::size_t maximum_payload_bytes, const std::size_t maximum_routes,
    const std::size_t maximum_queue_items) {
  return *ProviderDescriptor::create({provider_id, "1.0.0", "source.xverse.xcom.core-matrix",
                                      interaction_mask, delivery_mask, ordering_mask,
                                      maximum_payload_bytes, maximum_routes,
                                      maximum_queue_items})
              .value();
}

/**
 * @brief Build one valid loopback descriptor within the fixed loopback storage.
 * @param provider_id Stable logical provider identity.
 * @param maximum_routes Finite route bound (defaults to the loopback maximum).
 * @param maximum_queue_items Finite per-route queue bound (defaults to the loopback maximum).
 * @return Owned best-effort, per-route-FIFO descriptor.
 * @failure The defaults are always within the admitted vocabulary.
 */
[[nodiscard]] inline ProviderDescriptor loopback_descriptor(
    const std::string_view provider_id,
    const std::size_t maximum_routes = LoopbackProvider::kMaximumRoutes,
    const std::size_t maximum_queue_items = LoopbackProvider::kMaximumQueueItems) {
  return make_descriptor(provider_id, kAllInteractions,
                         delivery_capability_bit(DeliveryCapability::best_effort),
                         ordering_capability_bit(OrderingCapability::per_route_fifo),
                         kMaximumPayloadBytes, maximum_routes, maximum_queue_items);
}

/**
 * @brief Independently implemented provider with one fixed route and one queue slot.
 * @ownership Owns its retained descriptor, binding, token, queue slot, counters, and mutex. A
 * registered instance must outlive its composition use; the composition retains it non-owning.
 * @lifetime Bounded to the test case; counter state is per-instance and never static.
 * @thread_safety One mutex serializes every route, queue, and counter operation; the optional
 * descriptor-compatibility re-entry callback runs before the composition registry lock is taken.
 * @failure Invalid tokens and states return a stable outcome without mutating retained state; a
 * configured forced-failure outcome is reported on prepare/submit while incrementing the counter and
 * never reports success.
 */
class ProbeProvider final : public CommunicationProvider {
 public:
  /**
   * @brief Construct one probe provider.
   * @param descriptor Retained immutable descriptor.
   * @param instance_id Nonzero caller-selected instance identity.
   */
  ProbeProvider(const ProviderDescriptor& descriptor, const std::uint64_t instance_id) noexcept
      : descriptor_(descriptor), instance_id_(instance_id) {}

  /**
   * @brief Configure one forced stable failure outcome for prepare and submit.
   * @param outcome Stable outcome returned instead of a normal prepare/submit result.
   * @failure No outcome is substituted when unset.
   */
  void configure_forced_failure(const ProviderOutcome outcome) noexcept {
    const std::lock_guard lock(mutex_);
    forced_failure_ = outcome;
  }

  /**
   * @brief Configure one descriptor-compatibility re-entry that registers a nested provider.
   * @param composition Registry to call while compatibility is evaluated.
   * @param nested_provider Distinct provider registered during that call.
   * @failure Null pointers are retained as a disabled probe and perform no callback.
   */
  void configure_registration_reentry(ProviderComposition* const composition,
                                      CommunicationProvider* const nested_provider) noexcept {
    const std::lock_guard lock(mutex_);
    reentry_composition_ = composition;
    reentry_provider_ = nested_provider;
    reentry_outcome_.reset();
  }

  /** @return One-shot re-entry registration outcome, if invoked. */
  [[nodiscard]] std::optional<ProviderOutcome> reentry_outcome() const noexcept {
    const std::lock_guard lock(mutex_);
    return reentry_outcome_;
  }
  /** @return Number of prepare virtual calls observed. */
  [[nodiscard]] std::size_t prepare_calls() const noexcept {
    const std::lock_guard lock(mutex_);
    return prepare_calls_;
  }
  /** @return Number of activate virtual calls observed. */
  [[nodiscard]] std::size_t activate_calls() const noexcept {
    const std::lock_guard lock(mutex_);
    return activate_calls_;
  }
  /** @return Number of submit virtual calls observed. */
  [[nodiscard]] std::size_t submit_calls() const noexcept {
    const std::lock_guard lock(mutex_);
    return submit_calls_;
  }

  /** @return Immutable retained descriptor. */
  [[nodiscard]] const ProviderDescriptor& descriptor() const noexcept override {
    return descriptor_;
  }
  /** @return true when the descriptor fits the one-route, one-item fixture storage. */
  [[nodiscard]] bool descriptor_compatible() const noexcept override {
    ProviderComposition* composition = nullptr;
    CommunicationProvider* nested_provider = nullptr;
    {
      const std::lock_guard lock(mutex_);
      composition = reentry_composition_;
      nested_provider = reentry_provider_;
      reentry_composition_ = nullptr;
      reentry_provider_ = nullptr;
    }
    if (composition != nullptr && nested_provider != nullptr) {
      const ProviderOutcome outcome = composition->register_provider(*nested_provider).outcome();
      const std::lock_guard lock(mutex_);
      reentry_outcome_.emplace(outcome);
    }
    return descriptor_.maximum_routes() == 1U && descriptor_.maximum_queue_items() == 1U;
  }
  /** @return Caller-selected nonzero instance identity. */
  [[nodiscard]] std::uint64_t instance_id() const noexcept override { return instance_id_; }

 private:
  /** @copydoc CommunicationProvider::prepare */
  [[nodiscard]] ProviderResult<ProviderRouteToken> prepare(
      const ProviderRouteBinding& binding) noexcept override {
    const std::lock_guard lock(mutex_);
    ++prepare_calls_;
    if (forced_failure_.has_value()) {
      return ProviderResult<ProviderRouteToken>::without_value(*forced_failure_);
    }
    if (binding_.has_value() && state_ != ProviderRouteState::closed) {
      return ProviderResult<ProviderRouteToken>::without_value(
          ProviderOutcome::route_capacity_exhausted);
    }
    const auto token = ProviderRouteToken::create(next_generation_++);
    if (!token.has_value() || binding.queue_capacity() != 1U) {
      return ProviderResult<ProviderRouteToken>::without_value(
          ProviderOutcome::queue_limit_exceeded);
    }
    binding_.reset();
    binding_.emplace(binding);
    token_.reset();
    token_.emplace(*token);
    item_.reset();
    state_ = ProviderRouteState::prepared;
    return ProviderResult<ProviderRouteToken>::with_value(ProviderOutcome::prepared, *token);
  }

  /** @copydoc CommunicationProvider::activate */
  [[nodiscard]] ProviderStatus activate(
      const ProviderRouteToken& token,
      [[maybe_unused]] const LifecycleController& lifecycle) noexcept override {
    const std::lock_guard lock(mutex_);
    ++activate_calls_;
    if (!authenticates(token) || state_ != ProviderRouteState::prepared) {
      return ProviderStatus(ProviderOutcome::inactive_route);
    }
    state_ = ProviderRouteState::active;
    return ProviderStatus(ProviderOutcome::activated);
  }

  /** @copydoc CommunicationProvider::submit */
  [[nodiscard]] ProviderStatus submit(
      const ProviderRouteToken& token, const CommunicationItem& item,
      [[maybe_unused]] const LifecycleController& lifecycle) noexcept override {
    const std::lock_guard lock(mutex_);
    ++submit_calls_;
    if (forced_failure_.has_value()) {
      return ProviderStatus(*forced_failure_);
    }
    if (!authenticates(token) || state_ != ProviderRouteState::active) {
      return ProviderStatus(ProviderOutcome::inactive_route);
    }
    if (item_.has_value()) {
      return ProviderStatus(ProviderOutcome::queue_saturated);
    }
    item_.emplace(item);
    return ProviderStatus(ProviderOutcome::accepted);
  }

  /** @copydoc CommunicationProvider::receive */
  [[nodiscard]] ProviderResult<CommunicationItem> receive(
      const ProviderRouteToken& token,
      [[maybe_unused]] const LifecycleController& lifecycle) noexcept override {
    const std::lock_guard lock(mutex_);
    if (!authenticates(token) || (state_ != ProviderRouteState::active &&
                                  state_ != ProviderRouteState::draining)) {
      return ProviderResult<CommunicationItem>::without_value(ProviderOutcome::inactive_route);
    }
    if (!item_.has_value()) {
      return ProviderResult<CommunicationItem>::without_value(ProviderOutcome::queue_empty);
    }
    const CommunicationItem returned(*item_);
    item_.reset();
    return ProviderResult<CommunicationItem>::with_value(ProviderOutcome::received, returned);
  }

  /** @copydoc CommunicationProvider::drain */
  [[nodiscard]] ProviderStatus drain(
      const ProviderRouteToken& token,
      [[maybe_unused]] const LifecycleController& lifecycle) noexcept override {
    const std::lock_guard lock(mutex_);
    if (!authenticates(token) || state_ != ProviderRouteState::active) {
      return ProviderStatus(ProviderOutcome::inactive_route);
    }
    state_ = ProviderRouteState::draining;
    return ProviderStatus(ProviderOutcome::draining);
  }

  /** @copydoc CommunicationProvider::close */
  [[nodiscard]] ProviderStatus close(
      const ProviderRouteToken& token,
      [[maybe_unused]] const LifecycleController& lifecycle) noexcept override {
    const std::lock_guard lock(mutex_);
    if (!authenticates(token) || state_ != ProviderRouteState::draining) {
      return ProviderStatus(ProviderOutcome::inactive_route);
    }
    if (item_.has_value()) {
      return ProviderStatus(ProviderOutcome::queued_items_remain);
    }
    state_ = ProviderRouteState::closed;
    return ProviderStatus(ProviderOutcome::closed);
  }

  /** @copydoc CommunicationProvider::state */
  [[nodiscard]] ProviderResult<ProviderRouteStateValue> state(
      const ProviderRouteToken& token) const noexcept override {
    const std::lock_guard lock(mutex_);
    return state_result(token);
  }

  /** @copydoc CommunicationProvider::reconcile */
  [[nodiscard]] ProviderResult<ProviderRouteStateValue> reconcile(
      const ProviderRouteToken& token,
      [[maybe_unused]] const LifecycleController& lifecycle) const noexcept override {
    const std::lock_guard lock(mutex_);
    return state_result(token);
  }

  /** @param token Candidate token. @return true only for the retained token. */
  [[nodiscard]] bool authenticates(const ProviderRouteToken& token) const noexcept {
    return token_.has_value() && *token_ == token;
  }

  /** @param token Candidate token. @return Owned bounded state or invalid-handle outcome. */
  [[nodiscard]] ProviderResult<ProviderRouteStateValue> state_result(
      const ProviderRouteToken& token) const noexcept {
    if (!authenticates(token) || !binding_.has_value()) {
      return ProviderResult<ProviderRouteStateValue>::without_value(
          ProviderOutcome::invalid_provider_route_handle);
    }
    const auto value =
        ProviderRouteStateValue::create(token, state_, item_.has_value() ? 1U : 0U, 1U);
    return value.has_value()
               ? ProviderResult<ProviderRouteStateValue>::with_value(ProviderOutcome::reconciled,
                                                                      *value)
               : ProviderResult<ProviderRouteStateValue>::without_value(
                     ProviderOutcome::interrupted_resource);
  }

  /** Retained immutable descriptor. */
  ProviderDescriptor descriptor_;
  /** Nonzero caller-selected instance identity. */
  std::uint64_t instance_id_;
  /** Next nonzero provider-local token generation. */
  std::uint64_t next_generation_{1U};
  /** Serializes every probe operation. */
  mutable std::mutex mutex_;
  /** One fixed route binding. */
  std::optional<ProviderRouteBinding> binding_;
  /** Current provider-local token. */
  std::optional<ProviderRouteToken> token_;
  /** Current provider-owned route state. */
  ProviderRouteState state_{ProviderRouteState::closed};
  /** One fixed queue slot. */
  std::optional<CommunicationItem> item_;
  /** Optional forced stable failure outcome. */
  std::optional<ProviderOutcome> forced_failure_;
  /** Observed prepare dispatches. */
  std::size_t prepare_calls_{0U};
  /** Observed activate dispatches. */
  std::size_t activate_calls_{0U};
  /** Observed submit dispatches. */
  std::size_t submit_calls_{0U};
  /** Optional one-shot re-entry registry. */
  mutable ProviderComposition* reentry_composition_{nullptr};
  /** Optional nested provider registered by the re-entry probe. */
  mutable CommunicationProvider* reentry_provider_{nullptr};
  /** One-shot re-entry outcome. */
  mutable std::optional<ProviderOutcome> reentry_outcome_;
};

/**
 * @brief One full accepted core stack for a caller-selected family and declared-policy option.
 * @ownership Owns one contract, endpoint/route declarations, one lifecycle controller, one provider
 * (a loopback when none is supplied), one composition, and the issued handles. Returned items are
 * independent owned copies.
 * @lifetime Bounded to the test case; a prepared or active route must not outlive the fixture.
 * @thread_safety Construction and mutation are single-threaded; immutable values and snapshots
 * support concurrent const reads; provider mutations serialize through the composition mutex.
 * @failure A failed declaration or registration leaves ready() false and exposes nothing usable.
 */
class CoreStackFixture final {
 public:
  /**
   * @brief Build the accepted core stack.
   * @param kind Interaction family bound into the contract and route.
   * @param suffix Stable identity suffix keeping fixtures independent.
   * @param queue_capacity Finite reject-new queue capacity.
   * @param maximum_payload_bytes Per-route requested payload bound.
   * @param activate_now Whether to prepare and activate the provider route at construction.
   * @param external_provider Caller-owned provider, or nullptr to own a loopback provider.
   * @param policy Optional declared flow policy bound into the route.
   * @param provider_id Registered provider identity and descriptor identity.
   * @param route_provider_id Provider identity declared by endpoints and route.
   * @param interaction_mask Advertised interaction mask (owned-loopback descriptor only).
   * @param delivery Advertised/requested delivery claim.
   * @param ordering Advertised/requested ordering claim.
   * @param maximum_routes Advertised finite route bound (owned descriptor only).
   * @param maximum_queue_items Advertised finite queue bound (owned descriptor only).
   * @param registry_capacity Finite provider registry capacity.
   * @param requirements_version Requested provider-contract version.
   */
  CoreStackFixture(const InteractionKind kind, const std::string_view suffix,
                   const std::size_t queue_capacity, const std::size_t maximum_payload_bytes,
                   const bool activate_now = true,
                   CommunicationProvider* const external_provider = nullptr,
                   const FlowPolicy* const policy = nullptr,
                   const std::string_view provider_id = "provider.core-matrix",
                   const std::string_view route_provider_id = "",
                   const std::uint8_t interaction_mask = kAllInteractions,
                   const DeliveryCapability delivery = DeliveryCapability::best_effort,
                   const OrderingCapability ordering = OrderingCapability::per_route_fifo,
                   const std::size_t maximum_routes = LoopbackProvider::kMaximumRoutes,
                   const std::size_t maximum_queue_items = LoopbackProvider::kMaximumQueueItems,
                   const std::size_t registry_capacity = 1U,
                   const std::string_view requirements_version = "1.0.0") {
    // An empty route provider identity defaults to the registered provider identity; an explicit
    // different value is used to prove unregistered-provider rejection.
    const std::string_view effective_route_provider =
        route_provider_id.empty() ? provider_id : route_provider_id;
    const auto contract = make_contract(suffix, kind);
    if (!contract.has_value()) {
      return;
    }
    contract_.emplace(*contract.value());
    const auto source = EndpointSpec::create(
        {std::string("source.") + std::string(suffix), kCoreDigest, effective_route_provider,
         source_direction(kind)},
        *contract_);
    const auto destination = EndpointSpec::create(
        {std::string("destination.") + std::string(suffix), kCoreDigest, effective_route_provider,
         destination_direction(kind)},
        *contract_);
    if (!source.has_value() || !destination.has_value()) {
      return;
    }
    source_spec_.emplace(*source.value());
    destination_spec_.emplace(*destination.value());
    const std::string route_id = "route." + std::string(suffix);
    const RouteSpecInput route_input{route_id, kCoreDigest, effective_route_provider};
    const auto route = policy != nullptr
                           ? RouteSpec::create(route_input, *source_spec_, *destination_spec_,
                                               *policy)
                           : RouteSpec::create(route_input, *source_spec_, *destination_spec_);
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
        !lifecycle_->validate_route(*route_handle_, *source_handle_, *destination_handle_)
             .has_value() ||
        !lifecycle_->activate_endpoint(*source_handle_).has_value() ||
        !lifecycle_->activate_endpoint(*destination_handle_).has_value()) {
      return;
    }

    if (external_provider == nullptr) {
      owned_descriptor_.emplace(make_descriptor(provider_id, interaction_mask,
                                                delivery_capability_bit(delivery),
                                                ordering_capability_bit(ordering),
                                                kMaximumPayloadBytes, maximum_routes,
                                                maximum_queue_items));
      owned_provider_.emplace(*owned_descriptor_);
      provider_ = &*owned_provider_;
    } else {
      provider_ = external_provider;
    }
    const auto registry_configuration = ProviderRegistryConfiguration::create(registry_capacity);
    if (!registry_configuration.has_value()) {
      return;
    }
    composition_.emplace(*registry_configuration.value());
    if (composition_->register_provider(*provider_).outcome() != ProviderOutcome::registered) {
      return;
    }
    requirements_ = {requirements_version, kind, delivery, ordering, maximum_payload_bytes,
                     queue_capacity};
    ready_ = true;
    if (activate_now) {
      static_cast<void>(prepare_and_activate());
    }
  }

  /** @return true when declaration and explicit registration completed. */
  [[nodiscard]] bool ready() const noexcept { return ready_; }
  /** @return true when the provider route is prepared. */
  [[nodiscard]] bool prepared() const noexcept { return provider_handle_.has_value(); }
  /** @return true when the provider route is active. */
  [[nodiscard]] bool activated() const noexcept { return active_; }
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
  /** @return Exact prepared provider-route handle (requires prepared()). */
  [[nodiscard]] const ProviderRouteHandle& provider_handle() const noexcept {
    return *provider_handle_;
  }
  /** @return Mutable lifecycle controller. */
  [[nodiscard]] LifecycleController& lifecycle() noexcept { return *lifecycle_; }
  /** @return Lifecycle controller for observations. */
  [[nodiscard]] const LifecycleController& lifecycle() const noexcept { return *lifecycle_; }
  /** @return Mutable composition dispatcher. */
  [[nodiscard]] ProviderComposition& composition() noexcept { return *composition_; }
  /** @return Immutable composition dispatcher. */
  [[nodiscard]] const ProviderComposition& composition() const noexcept { return *composition_; }
  /** @return Registered provider for explicit multi-composition tests. */
  [[nodiscard]] CommunicationProvider& provider() noexcept { return *provider_; }
  /** @return Exact requested semantics used by prepare(). */
  [[nodiscard]] const ProviderRouteRequirements& requirements() const noexcept {
    return requirements_;
  }

  /** @return Prepared-and-activated handle, or a stable failure without partial preparation. */
  [[nodiscard]] ProviderResult<ProviderRouteHandle> prepare_and_activate() noexcept {
    auto prepared = prepare();
    if (!prepared.has_value()) {
      return prepared;
    }
    const ProviderStatus status = composition_->activate_route(*provider_handle_, *lifecycle_);
    active_ = status.outcome() == ProviderOutcome::activated;
    return active_ ? std::move(prepared)
                   : ProviderResult<ProviderRouteHandle>::without_value(status.outcome());
  }

  /** @return Prepared provider-route handle for the fixture's requested semantics. */
  [[nodiscard]] ProviderResult<ProviderRouteHandle> prepare() noexcept {
    return prepare(requirements_);
  }

  /**
   * @brief Attempt preparation with caller-selected requirements.
   * @param requirements Requested capabilities and limits.
   * @return Prepared handle or a stable no-dispatch failure.
   */
  [[nodiscard]] ProviderResult<ProviderRouteHandle> prepare(
      const ProviderRouteRequirements& requirements) noexcept {
    const auto result = composition_->prepare_route(*lifecycle_, *route_spec_, *route_handle_,
                                                    *source_handle_, *destination_handle_,
                                                    requirements);
    if (result.has_value()) {
      provider_handle_.emplace(*result.value());
    }
    return result;
  }

  /** @return Submission status for an exact active route. */
  [[nodiscard]] ProviderStatus submit(const CommunicationItem& item) noexcept {
    return composition_->submit(*provider_handle_, item, *lifecycle_);
  }
  /** @return Oldest queued item or a stable empty/failure outcome. */
  [[nodiscard]] ProviderResult<CommunicationItem> receive() noexcept {
    return composition_->receive(*provider_handle_, *lifecycle_);
  }
  /** @return Draining status. */
  [[nodiscard]] ProviderStatus drain() noexcept {
    return composition_->drain_route(*provider_handle_, *lifecycle_);
  }
  /** @return Close status. */
  [[nodiscard]] ProviderStatus close() noexcept {
    return composition_->close_route(*provider_handle_, *lifecycle_);
  }
  /** @return Owned provider route snapshot. */
  [[nodiscard]] ProviderResult<ProviderRouteSnapshot> route_state() const noexcept {
    return composition_->route_state(*provider_handle_);
  }
  /** @return Reconciled provider route snapshot or a stable failure. */
  [[nodiscard]] ProviderResult<ProviderRouteSnapshot> reconcile() const noexcept {
    return composition_->reconcile_route(*provider_handle_, *lifecycle_);
  }

  /**
   * @brief Create one valid route-bound item with a one-byte synthetic payload.
   * @param sequence Byte used for payload, timestamp, and correlation identity.
   * @return Owned item or core validation diagnostics.
   */
  [[nodiscard]] Result<CommunicationItem> item(const unsigned int sequence) const noexcept {
    const std::array<std::byte, 1U> payload{std::byte(sequence & 0xFFU)};
    return item_with_payload(sequence, payload);
  }

  /**
   * @brief Create one valid route-bound item with a caller-selected payload.
   * @param sequence Timestamp and correlation sequence.
   * @param payload Synthetic payload bytes.
   * @return Owned item or core validation diagnostics.
   */
  [[nodiscard]] Result<CommunicationItem> item_with_payload(
      const unsigned int sequence, const std::span<const std::byte> payload) const noexcept {
    const std::string correlation = "correlation." + std::to_string(sequence);
    const std::string causation = "causation." + std::to_string(sequence);
    return CommunicationItem::create(
        {contract_->contract_id().value(), contract_->contract_version().value(),
         contract_->interface_id().value(), route_spec_->source_endpoint_id().value(),
         contract_->schema_id().value(), contract_->schema_version().value(),
         contract_->interaction_kind(), OriginKind::component,
         Timestamp(static_cast<std::int64_t>(sequence)), "clock.core-matrix", correlation,
         causation, route_spec_->route_id().value(), route_spec_->provider_id().value(), payload},
        *contract_);
  }

  /**
   * @brief Create contract-valid item metadata with caller-selected binding fields.
   * @param endpoint_id Logical source metadata.
   * @param route_id Route provenance metadata.
   * @param provider_id Provider provenance metadata.
   * @param payload Synthetic payload bytes.
   * @return Owned item or core validation diagnostics.
   */
  [[nodiscard]] Result<CommunicationItem> item_with_binding(
      const std::string_view endpoint_id, const std::string_view route_id,
      const std::string_view provider_id,
      const std::span<const std::byte> payload) const noexcept {
    return CommunicationItem::create(
        {contract_->contract_id().value(), contract_->contract_version().value(),
         contract_->interface_id().value(), endpoint_id, contract_->schema_id().value(),
         contract_->schema_version().value(), contract_->interaction_kind(),
         OriginKind::component, Timestamp(1), "clock.core-matrix", "correlation.custom",
         "causation.custom", route_id, provider_id, payload},
        *contract_);
  }

 private:
  bool ready_{false};
  bool active_{false};
  std::optional<CommunicationContract> contract_;
  std::optional<EndpointSpec> source_spec_;
  std::optional<EndpointSpec> destination_spec_;
  std::optional<RouteSpec> route_spec_;
  std::optional<LifecycleController> lifecycle_;
  std::optional<EndpointHandle> source_handle_;
  std::optional<EndpointHandle> destination_handle_;
  std::optional<RouteHandle> route_handle_;
  std::optional<ProviderDescriptor> owned_descriptor_;
  std::optional<LoopbackProvider> owned_provider_;
  CommunicationProvider* provider_{nullptr};
  std::optional<ProviderComposition> composition_;
  std::optional<ProviderRouteHandle> provider_handle_;
  ProviderRouteRequirements requirements_{"1.0.0", InteractionKind::message_event,
                                           DeliveryCapability::best_effort,
                                           OrderingCapability::per_route_fifo, 1U, 1U};
};

/**
 * @brief One declaration-only lifecycle stack without an activated provider route.
 * @ownership Owns one contract, endpoint/route declarations, one lifecycle controller, and handles.
 * @lifetime Bounded to the test case; no provider or composition is created.
 * @thread_safety Construction is single-threaded; immutable values support concurrent const reads.
 * @failure A failed declaration leaves ready() false and exposes nothing usable.
 */
class DeclarationFixture final {
 public:
  /**
   * @param kind Interaction family bound into the contract and route.
   * @param suffix Stable identity suffix.
   * @param policy Optional declared flow policy bound into the route.
   */
  DeclarationFixture(const InteractionKind kind, const std::string_view suffix,
                     const FlowPolicy* const policy = nullptr) {
    const auto contract = make_contract(suffix, kind);
    if (!contract.has_value()) {
      return;
    }
    contract_.emplace(*contract.value());
    const auto source = EndpointSpec::create(
        {std::string("source.") + std::string(suffix), kCoreDigest, "provider.declaration",
         source_direction(kind)},
        *contract_);
    const auto destination = EndpointSpec::create(
        {std::string("destination.") + std::string(suffix), kCoreDigest, "provider.declaration",
         destination_direction(kind)},
        *contract_);
    if (!source.has_value() || !destination.has_value()) {
      return;
    }
    source_spec_.emplace(*source.value());
    destination_spec_.emplace(*destination.value());
    const std::string route_id = "route." + std::string(suffix);
    const RouteSpecInput route_input{route_id, kCoreDigest, "provider.declaration"};
    const auto route = policy != nullptr
                           ? RouteSpec::create(route_input, *source_spec_, *destination_spec_,
                                               *policy)
                           : RouteSpec::create(route_input, *source_spec_, *destination_spec_);
    if (!route.has_value()) {
      return;
    }
    route_spec_.emplace(*route.value());
    const auto configuration = LifecycleConfiguration::create({2U, 2U});
    if (!configuration.has_value()) {
      return;
    }
    lifecycle_.emplace(*configuration.value());
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
    ready_ = true;
  }

  /** @return true when every declaration was retained. */
  [[nodiscard]] bool ready() const noexcept { return ready_; }
  /** @return Owned contract. */
  [[nodiscard]] const CommunicationContract& contract() const noexcept { return *contract_; }
  /** @return Owned source endpoint declaration. */
  [[nodiscard]] const EndpointSpec& source_spec() const noexcept { return *source_spec_; }
  /** @return Owned destination endpoint declaration. */
  [[nodiscard]] const EndpointSpec& destination_spec() const noexcept {
    return *destination_spec_;
  }
  /** @return Owned route declaration. */
  [[nodiscard]] const RouteSpec& route_spec() const noexcept { return *route_spec_; }
  /** @return Exact source endpoint handle. */
  [[nodiscard]] const EndpointHandle& source_handle() const noexcept { return *source_handle_; }
  /** @return Exact destination endpoint handle. */
  [[nodiscard]] const EndpointHandle& destination_handle() const noexcept {
    return *destination_handle_;
  }
  /** @return Exact lifecycle route handle. */
  [[nodiscard]] const RouteHandle& route_handle() const noexcept { return *route_handle_; }
  /** @return Mutable lifecycle controller. */
  [[nodiscard]] LifecycleController& lifecycle() noexcept { return *lifecycle_; }
  /** @return Lifecycle controller for observations. */
  [[nodiscard]] const LifecycleController& lifecycle() const noexcept { return *lifecycle_; }

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
};

}  // namespace xverse::xcom::test

#endif  // XVERSE_XCOM_CORE_MATRIX_TEST_SUPPORT_HPP
