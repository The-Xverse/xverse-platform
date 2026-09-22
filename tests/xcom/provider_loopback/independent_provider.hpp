/**
 * @file independent_provider.hpp
 * @brief Independent source-level provider fixture with one fixed route and queue slot.
 * @ownership The fixture owns its descriptor, binding, token, state, and optional item.
 * @lifetime Returned values are owned copies; a registered fixture must outlive composition use.
 * @thread_safety One mutex serializes every provider-owned route and queue operation.
 * @failure Invalid tokens and states return stable outcomes without mutating retained state.
 */

#ifndef XVERSE_XCOM_PROVIDER_LOOPBACK_INDEPENDENT_PROVIDER_HPP
#define XVERSE_XCOM_PROVIDER_LOOPBACK_INDEPENDENT_PROVIDER_HPP

#include "xverse/xcom/provider.hpp"

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>

namespace xverse::xcom::test {

/** Minimal independently implemented provider used to prove the public source contract. */
class IndependentProvider final : public CommunicationProvider {
 public:
  /** @brief Construct one provider fixture. @param descriptor Retained descriptor.
   * @param instance_id Nonzero caller-selected instance identity. */
  IndependentProvider(const ProviderDescriptor& descriptor,
                      const std::uint64_t instance_id) noexcept
      : descriptor_(descriptor), instance_id_(instance_id) {}

  /**
   * @brief Configure one registration callback that re-enters the supplied composition.
   * @param composition Registry to call while descriptor compatibility is evaluated.
   * @param nested_provider Distinct provider to register during that call.
   * @failure Null pointers are retained as a disabled probe and perform no callback.
   */
  void configure_registration_reentry(
      ProviderComposition* const composition,
      CommunicationProvider* const nested_provider) noexcept {
    const std::lock_guard lock(mutex_);
    reentry_composition_ = composition;
    reentry_provider_ = nested_provider;
    reentry_outcome_.reset();
  }

  /** @return Registration outcome produced by the one-shot re-entry probe, if invoked. */
  [[nodiscard]] std::optional<ProviderOutcome> reentry_outcome() const noexcept {
    const std::lock_guard lock(mutex_);
    return reentry_outcome_;
  }
  /** @return Number of prepare virtual calls observed by this fixture. */
  [[nodiscard]] std::size_t prepare_calls() const noexcept {
    const std::lock_guard lock(mutex_);
    return prepare_calls_;
  }
  /** @return Number of activate virtual calls observed by this fixture. */
  [[nodiscard]] std::size_t activate_calls() const noexcept {
    const std::lock_guard lock(mutex_);
    return activate_calls_;
  }
  /** @return Number of submit virtual calls observed by this fixture. */
  [[nodiscard]] std::size_t submit_calls() const noexcept {
    const std::lock_guard lock(mutex_);
    return submit_calls_;
  }

  /** @return Immutable retained descriptor. */
  [[nodiscard]] const ProviderDescriptor& descriptor() const noexcept override {
    return descriptor_;
  }
  /** @return true when the descriptor fits the one-route, one-item fixture. */
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
      const ProviderOutcome outcome =
          composition->register_provider(*nested_provider).outcome();
      const std::lock_guard lock(mutex_);
      reentry_outcome_.emplace(outcome);
    }
    return descriptor_.maximum_routes() == 1U &&
           descriptor_.maximum_queue_items() == 1U;
  }
  /** @return Caller-selected instance identity. */
  [[nodiscard]] std::uint64_t instance_id() const noexcept override {
    return instance_id_;
  }

 private:
  /** @copydoc CommunicationProvider::prepare */
  [[nodiscard]] ProviderResult<ProviderRouteToken> prepare(
      const ProviderRouteBinding& binding) noexcept override {
    const std::lock_guard lock(mutex_);
    ++prepare_calls_;
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
    return ProviderResult<ProviderRouteToken>::with_value(ProviderOutcome::prepared,
                                                          *token);
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
    if (!authenticates(token) ||
        (state_ != ProviderRouteState::active &&
         state_ != ProviderRouteState::draining)) {
      return ProviderResult<CommunicationItem>::without_value(
          ProviderOutcome::inactive_route);
    }
    if (!item_.has_value()) {
      return ProviderResult<CommunicationItem>::without_value(
          ProviderOutcome::queue_empty);
    }
    const CommunicationItem returned(*item_);
    item_.reset();
    return ProviderResult<CommunicationItem>::with_value(ProviderOutcome::received,
                                                         returned);
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
    const auto value = ProviderRouteStateValue::create(
        token, state_, item_.has_value() ? 1U : 0U, 1U);
    return value.has_value()
               ? ProviderResult<ProviderRouteStateValue>::with_value(
                     ProviderOutcome::reconciled, *value)
               : ProviderResult<ProviderRouteStateValue>::without_value(
                     ProviderOutcome::interrupted_resource);
  }

  ProviderDescriptor descriptor_; /**< Retained explicit descriptor. */
  std::uint64_t instance_id_; /**< Nonzero fixture identity. */
  std::uint64_t next_generation_{1U}; /**< Next provider-local token generation. */
  mutable std::mutex mutex_; /**< Serializes fixture state. */
  std::optional<ProviderRouteBinding> binding_; /**< One fixed route binding. */
  std::optional<ProviderRouteToken> token_; /**< Current provider-local token. */
  ProviderRouteState state_{ProviderRouteState::closed}; /**< Current route state. */
  std::optional<CommunicationItem> item_; /**< One fixed queue slot. */
  std::size_t prepare_calls_{0U}; /**< Observed prepare dispatches. */
  std::size_t activate_calls_{0U}; /**< Observed activate dispatches. */
  std::size_t submit_calls_{0U}; /**< Observed submit dispatches. */
  mutable ProviderComposition* reentry_composition_{nullptr}; /**< Optional callback registry. */
  mutable CommunicationProvider* reentry_provider_{nullptr}; /**< Optional nested provider. */
  mutable std::optional<ProviderOutcome> reentry_outcome_; /**< One-shot callback result. */
};

}  // namespace xverse::xcom::test

#endif  // XVERSE_XCOM_PROVIDER_LOOPBACK_INDEPENDENT_PROVIDER_HPP
