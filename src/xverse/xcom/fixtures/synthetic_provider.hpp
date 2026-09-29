/**
 * @file synthetic_provider.hpp
 * @brief T034 second owned in-process synthetic provider used only for provider-replaceability
 *        evidence, validated by the unchanged accepted T033 provider contract suite.
 * @details This fixture is the second minimal synthetic provider of capability 007. It implements the
 *          accepted `CommunicationProvider` source-level interface with independently written fixed
 *          route slots and a fixed reject-new queue prefix, a nonzero per-instance identity, and a
 *          storage-bounded `descriptor_compatible()` predicate. It models no network, transport
 *          protocol, clock, retry, timing, reliability, discovery, or compatibility behavior and
 *          defines no competing provider interface, RPC, or configuration language. It is an owned
 *          in-process fixture; it never opens a socket, listener, resolver, TLS session, legacy
 *          binary, or production workload.
 * @ingroup xcom_gw
 * @par Traceability
 * Realizes accepted `XCOM-DU-007`/`XCOM-DU-008` (provider boundary and composition, owned synthetic
 * provider) over the accepted `XCOM-CMP-006`/`XCOM-CMP-007` architecture and `XCOM-SW-CORE-003`/
 * `-004`/`-005`/`-007`/`-009`. Verified by the T034 `t034-` suites and the unchanged T033
 * `ProviderContractSuite`.
 * @ownership The provider owns every prepared route binding and every accepted `CommunicationItem`
 *            copy in its own fixed storage. Returned tokens and values own no borrowed storage.
 * @lifetime Returned handles, items, and state values are independent owned copies and remain valid
 *           after later provider operations; the provider must outlive `ProviderComposition` and
 *           every issued provider-route handle.
 * @thread_safety One mutex serializes every route, queue, and counter mutation. No callback,
 *                registry, filesystem, environment, process, socket, or network operation occurs.
 * @failure Invalid or foreign tokens return a stable outcome without mutation; a full reject-new
 *          queue rejects the new item while preserving every earlier item; a configured forced
 *          failure returns its exact stable outcome without mutating route state.
 */

#ifndef XVERSE_XCOM_FIXTURES_SYNTHETIC_PROVIDER_HPP_
#define XVERSE_XCOM_FIXTURES_SYNTHETIC_PROVIDER_HPP_

#include "xverse/xcom/provider.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>

namespace xverse::xcom {

/**
 * @brief Second owned in-process synthetic provider for provider-replaceability evidence only.
 * @details The provider declares the caller-supplied descriptor and, when compatible, admits route
 *          resources within its compile-time finite storage. `descriptor_compatible()` checks only
 *          nonzero capability masks and finite storage; it deliberately does not check the contract
 *          version, so a version misreport surfaces as the composition registration gate's
 *          `unsupported_contract_version` rather than as `invalid_descriptor`.
 */
class SyntheticProvider final : public CommunicationProvider {
 public:
  /** Compile-time maximum route resources for this fixture. */
  static constexpr std::size_t kMaximumRoutes = 2U;
  /** Compile-time maximum items retained in each route queue for this fixture. */
  static constexpr std::size_t kMaximumQueueItems = 8U;
  /**
   * Compile-time base for this fixture's opaque instance identity.
   *
   * The accepted loopback provider draws its identities from an independent low-sequence counter.
   * Starting this fixture's counter from a disjoint high base guarantees that a live
   * `SyntheticProvider` identity cannot equal a live loopback identity in the same process, so the
   * replaceability proof's distinct-identity check is deterministic and not an artifact of
   * construction order.
   */
  static constexpr std::uint64_t kInstanceIdentityBase = 0x1'0000'0000ULL;

  /**
   * @brief Construct an empty provider from a descriptor within this fixture's hard limits.
   * @param descriptor Valid descriptor whose limits do not exceed the compile-time storage.
   * @pre descriptor.maximum_routes() <= kMaximumRoutes and
   * descriptor.maximum_queue_items() <= kMaximumQueueItems for full compatibility.
   */
  explicit SyntheticProvider(const ProviderDescriptor& descriptor) noexcept;
  SyntheticProvider(const SyntheticProvider&) = delete;
  SyntheticProvider& operator=(const SyntheticProvider&) = delete;

  /** @return Immutable retained descriptor. */
  [[nodiscard]] const ProviderDescriptor& descriptor() const noexcept override {
    return descriptor_;
  }
  /**
   * @return true only for nonzero interaction, delivery, and ordering masks within this fixture's
   * finite route and queue storage; the contract version is intentionally not checked here.
   */
  [[nodiscard]] bool descriptor_compatible() const noexcept override;
  /** @return Opaque nonzero provider object identity distinct from the loopback provider. */
  [[nodiscard]] std::uint64_t instance_id() const noexcept override { return instance_id_; }

  /**
   * @brief Configure one forced stable failure outcome for `prepare` and `submit`.
   * @param outcome Stable outcome returned instead of a normal result.
   * @failure No outcome is substituted when unset; a configured outcome mutates no route state.
   */
  void configure_forced_failure(ProviderOutcome outcome) noexcept;

  /** @return Number of `prepare` virtual dispatches observed by this fixture. */
  [[nodiscard]] std::size_t prepare_dispatch_count() const noexcept;
  /** @return Number of `submit` virtual dispatches observed by this fixture. */
  [[nodiscard]] std::size_t submit_dispatch_count() const noexcept;
  /** @return Number of items copied into a route queue by this fixture. */
  [[nodiscard]] std::size_t accepted_item_count() const noexcept;

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

  /** One fixed reject-new FIFO queue written independently of the loopback provider storage. */
  struct Queue final {
    /** @param configured_capacity Nonzero prefix of item slots used by this queue. */
    explicit Queue(std::size_t configured_capacity) noexcept : capacity(configured_capacity) {}
    /** Fixed item slots; only the configured prefix is addressable. */
    std::array<std::optional<CommunicationItem>, kMaximumQueueItems> slots{};
    /** Configured slot prefix. */
    std::size_t capacity;
    /** Index of the oldest retained item. */
    std::size_t read_index{0U};
    /** Number of retained items. */
    std::size_t count{0U};
  };

  /** One exact provider-owned route resource. */
  struct RouteRecord final {
    /**
     * @param route_binding Exact owned lifecycle and requirements binding.
     * @param issued_token Exact provider-local route token.
     */
    RouteRecord(const ProviderRouteBinding& route_binding,
                const ProviderRouteToken& issued_token) noexcept
        : binding(route_binding), token(issued_token),
          queue(route_binding.queue_capacity()) {}
    /** Exact route and lifecycle binding. */
    ProviderRouteBinding binding;
    /** Exact provider-local route token. */
    ProviderRouteToken token;
    /** Current provider-owned route state. */
    ProviderRouteState state{ProviderRouteState::prepared};
    /** Fixed reject-new queue. */
    Queue queue;
  };

  /** @param token Candidate provider-local token. @return Authenticated route or null. */
  [[nodiscard]] RouteRecord* route_for(const ProviderRouteToken& token) noexcept;
  /** @param token Candidate provider-local token. @return Authenticated route or null. */
  [[nodiscard]] const RouteRecord* route_for(const ProviderRouteToken& token) const noexcept;
  /**
   * @param record Authenticated route.
   * @param lifecycle Expected lifecycle owner.
   * @param allow_draining Whether the draining provider state is accepted.
   * @return true only when every exact lifecycle binding is current and state-compatible.
   */
  [[nodiscard]] static bool lifecycle_matches(const RouteRecord& record,
                                              const LifecycleController& lifecycle,
                                              bool allow_draining) noexcept;
  /** @param record Authenticated route. @return Owned bounded internal state, if consistent. */
  [[nodiscard]] static std::optional<ProviderRouteStateValue> state_value(
      const RouteRecord& record) noexcept;

  ProviderDescriptor descriptor_; /**< Immutable provider claims and hard limits. */
  std::uint64_t instance_id_; /**< Opaque nonzero live object identity. */
  std::uint64_t next_route_generation_{1U}; /**< Next nonzero provider route generation. */
  mutable std::mutex mutex_; /**< Serializes route, queue, and counter mutation. */
  std::array<std::optional<RouteRecord>, kMaximumRoutes> routes_{}; /**< Fixed route slots. */
  std::optional<ProviderOutcome> forced_failure_; /**< Optional forced stable failure outcome. */
  std::size_t prepare_dispatches_{0U}; /**< Observed prepare dispatches. */
  std::size_t submit_dispatches_{0U}; /**< Observed submit dispatches. */
  std::size_t accepted_items_{0U}; /**< Observed accepted (emitted) items. */
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_FIXTURES_SYNTHETIC_PROVIDER_HPP_
