/**
 * @file loopback_provider.hpp
 * @ingroup xcom_core
 * @brief Owned fixed-capacity in-process FIFO loopback provider.
 * @ownership The provider owns every prepared route and every accepted CommunicationItem copy.
 * @lifetime Returned handles do not retain resources; items returned by receive() are independent
 * copies and remain valid after later provider operations.
 * @thread_safety Every operation serializes shared mutation with one mutex. No callback, registry,
 * filesystem, environment, process, socket, or network operation occurs while locked or unlocked.
 * @failure Saturation rejects the new item, preserves every queued item and FIFO index, and reports
 * ProviderOutcome::queue_saturated without allocating additional storage.
 */

#ifndef XVERSE_XCOM_LOOPBACK_PROVIDER_HPP
#define XVERSE_XCOM_LOOPBACK_PROVIDER_HPP

#include "xverse/xcom/provider.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>

namespace xverse::xcom {

/**
 * @brief In-process provider for deterministic bounded capability evidence only.
 *
 * The provider declares best-effort delivery and per-route FIFO ordering. It does not model a
 * network, transport protocol, clock, retry, timing, reliability, or compatibility behavior.
 * ProviderComposition alone may invoke its private route operations; consumers retain public
 * read-only access to the source-linked descriptor, compatibility claim, and instance identity.
 */
class LoopbackProvider final : public CommunicationProvider {
 public:
  /** Compile-time maximum route resources. */
  static constexpr std::size_t kMaximumRoutes = 4U;
  /** Compile-time maximum items retained in each route queue. */
  static constexpr std::size_t kMaximumQueueItems = 8U;

  /**
   * @brief Construct an empty provider from a descriptor within loopback hard limits.
   * @param descriptor Valid descriptor whose limits do not exceed compile-time storage.
   * @pre descriptor.maximum_routes() <= kMaximumRoutes and
   * descriptor.maximum_queue_items() <= kMaximumQueueItems.
   */
  explicit LoopbackProvider(const ProviderDescriptor& descriptor) noexcept;
  LoopbackProvider(const LoopbackProvider&) = delete;
  LoopbackProvider& operator=(const LoopbackProvider&) = delete;

  /** @return Immutable source-linked descriptor. */
  [[nodiscard]] const ProviderDescriptor& descriptor() const noexcept override {
    return descriptor_;
  }
  /**
   * @return true only for all-four-interaction, best-effort, FIFO claims within fixed storage.
   */
  [[nodiscard]] bool descriptor_compatible() const noexcept override;
  /** @return Opaque nonzero provider object identity. */
  [[nodiscard]] std::uint64_t instance_id() const noexcept override { return instance_id_; }

 private:
  friend class ProviderComposition;

  /** @brief Prepares one exact route binding; see the base private route contract.
   * @param binding Exact validated route binding.
   * @return Prepared token or stable outcome. */
  [[nodiscard]] ProviderResult<ProviderRouteToken> prepare(
      const ProviderRouteBinding& binding) noexcept override;
  /** @brief Activates one prepared route token; see the base private route contract.
   * @param token Exact prepared provider-local token.
   * @param lifecycle Bound lifecycle owner.
   * @return Status without changing lifecycle-controller state. */
  [[nodiscard]] ProviderStatus activate(const ProviderRouteToken& token,
                                        const LifecycleController& lifecycle) noexcept override;
  /** @brief Submits one item on an active route; see the base private route contract.
   * @param token Exact active provider-local token.
   * @param item Owned item copied on acceptance.
   * @param lifecycle Bound lifecycle owner.
   * @return Submission status. */
  [[nodiscard]] ProviderStatus submit(const ProviderRouteToken& token,
                                      const CommunicationItem& item,
                                      const LifecycleController& lifecycle) noexcept override;
  /** @brief Receives the oldest item on an active route; see the base private route contract.
   * @param token Exact active or draining provider-local token.
   * @param lifecycle Bound lifecycle owner.
   * @return Oldest owned item or an explicit empty/failure outcome. */
  [[nodiscard]] ProviderResult<CommunicationItem> receive(
      const ProviderRouteToken& token,
      const LifecycleController& lifecycle) noexcept override;
  /** @brief Drains an active route; see the base private route contract.
   * @param token Exact active provider-local token.
   * @param lifecycle Bound lifecycle owner.
   * @return Status without changing lifecycle-controller state. */
  [[nodiscard]] ProviderStatus drain(const ProviderRouteToken& token,
                                     const LifecycleController& lifecycle) noexcept override;
  /** @brief Closes an empty draining route; see the base private route contract.
   * @param token Exact empty draining provider-local token.
   * @param lifecycle Bound lifecycle owner.
   * @return Resource-release status without changing lifecycle-controller state. */
  [[nodiscard]] ProviderStatus close(const ProviderRouteToken& token,
                                     const LifecycleController& lifecycle) noexcept override;
  /** @brief Reports bounded provider state; see the base private route contract.
   * @param token Exact current provider-local token.
   * @return Owned bounded provider state. */
  [[nodiscard]] ProviderResult<ProviderRouteStateValue> state(
      const ProviderRouteToken& token) const noexcept override;
  /** @brief Reconciles bounded provider state; see the base private route contract.
   * @param token Exact current provider-local token.
   * @param lifecycle Bound lifecycle owner.
   * @return Reconciled bounded state or interrupted-resource outcome. */
  [[nodiscard]] ProviderResult<ProviderRouteStateValue> reconcile(
      const ProviderRouteToken& token,
      const LifecycleController& lifecycle) const noexcept override;

  /** One fixed reject-new FIFO queue. */
  struct Queue final {
    /** @param configured_capacity Nonzero prefix of items used by this queue. */
    explicit Queue(std::size_t configured_capacity) noexcept
        : capacity(configured_capacity) {}
    std::array<std::optional<CommunicationItem>, kMaximumQueueItems> items{}; /**< Item slots. */
    std::size_t capacity; /**< Configured slot prefix. */
    std::size_t head{0U}; /**< Oldest item index. */
    std::size_t size{0U}; /**< Retained item count. */
  };

  /** One exact provider-owned route resource. */
  struct RouteRecord final {
    /** @param route_binding Exact owned lifecycle and requirements binding.
     * @param issued_token Exact provider-local route token. */
    RouteRecord(const ProviderRouteBinding& route_binding,
                const ProviderRouteToken& issued_token) noexcept
        : binding(route_binding), token(issued_token),
          queue(route_binding.queue_capacity()) {}
    ProviderRouteBinding binding; /**< Exact route and lifecycle binding. */
    ProviderRouteToken token; /**< Exact provider-local route token. */
    ProviderRouteState state{ProviderRouteState::prepared}; /**< Provider resource state. */
    Queue queue; /**< Fixed reject-new FIFO. */
  };

  /** @param token Candidate provider-local token. @return Authenticated route or null. */
  [[nodiscard]] RouteRecord* authenticate(const ProviderRouteToken& token) noexcept;
  /** @param token Candidate provider-local token. @return Authenticated route or null. */
  [[nodiscard]] const RouteRecord* authenticate(
      const ProviderRouteToken& token) const noexcept;
  /** @param record Authenticated route. @param lifecycle Lifecycle owner.
   * @param allow_draining Whether draining route state is accepted.
   * @return true only when every exact lifecycle binding is current and state-compatible. */
  [[nodiscard]] static bool lifecycle_matches(const RouteRecord& record,
                                              const LifecycleController& lifecycle,
                                              bool allow_draining) noexcept;
  /** @param record Authenticated route. @return Owned bounded internal state, if consistent. */
  [[nodiscard]] static std::optional<ProviderRouteStateValue> state_value(
      const RouteRecord& record) noexcept;

  ProviderDescriptor descriptor_; /**< Immutable provider claims and hard limits. */
  std::uint64_t instance_id_; /**< Opaque nonzero live object identity. */
  std::uint64_t next_route_generation_{1U}; /**< Next nonzero provider route generation. */
  mutable std::mutex mutex_; /**< Serializes route and queue mutation. */
  std::array<std::optional<RouteRecord>, kMaximumRoutes> routes_{}; /**< Fixed route slots. */
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_LOOPBACK_PROVIDER_HPP
