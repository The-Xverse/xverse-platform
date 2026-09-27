/**
 * @file endpoint_route_lifecycle.hpp
 * @brief Fixed-capacity endpoint and route lifecycle control plane.
 * @ownership Public values own all data; the controller exclusively owns its fixed records.
 * @lifetime Value accessor views live with their owner; handles are usable only with their issuing
 * controller and exact current generation.
 * @thread_safety Immutable values permit concurrent reads. Every controller operation is serialized.
 * @failure Factories and controller operations return stable diagnostics without partial mutation.
 */

#ifndef XVERSE_XCOM_ENDPOINT_ROUTE_LIFECYCLE_HPP
#define XVERSE_XCOM_ENDPOINT_ROUTE_LIFECYCLE_HPP

#include "xverse/xcom/contract.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include <string_view>

namespace xverse::xcom {

/** Exact lifecycle resource category bound into every issued handle and snapshot. */
enum class ResourceKind { endpoint, route };

/** Deterministic endpoint and route lifecycle states. */
enum class LifecycleState { declared, validated, active, draining, failed, closed };

/**
 * @param kind Resource kind enumeration.
 * @return Stable external text for one resource kind.
 */
[[nodiscard]] std::string_view to_string(ResourceKind kind) noexcept;

/**
 * @param state Lifecycle state enumeration.
 * @return Stable external text for one lifecycle state.
 */
[[nodiscard]] std::string_view to_string(LifecycleState state) noexcept;

/**
 * @brief Call-scoped endpoint declaration input.
 * @ownership Owns no referenced text; EndpointSpec::create copies accepted fields.
 * @lifetime Views need remain valid only for the factory call.
 * @thread_safety Distinct inputs may be used concurrently.
 * @failure The factory rejects incomplete, malformed, or contract-incompatible input.
 */
struct EndpointSpecInput final {
  /** Logical endpoint identity. */
  std::string_view endpoint_id;
  /** Exact 64-character lowercase hexadecimal activation-plan digest. */
  std::string_view plan_digest;
  /** Explicit logical provider identity, never an address or protocol. */
  std::string_view provider_id;
  /** Endpoint's exact contract direction. */
  EndpointDirection direction;
};

/**
 * @brief Immutable validated logical endpoint declaration.
 * @ownership Owns endpoint, digest, provider, and complete communication-contract values.
 * @lifetime Accessor views and references remain valid while this value lives.
 * @thread_safety Concurrent const access is safe; no mutation is exposed.
 * @failure create() returns deterministic diagnostics and no partial declaration.
 */
class EndpointSpec final {
 public:
  /** Maximum canonical plan-digest byte count. */
  static constexpr std::size_t kPlanDigestBytes = 64U;

  /**
   * @brief Validate and own an endpoint declaration against an exact contract.
   * @param input Logical endpoint, plan, provider, and direction input.
   * @param contract Immutable communication contract to bind.
   * @return Valid declaration or stable diagnostics.
   */
  [[nodiscard]] static Result<EndpointSpec> create(const EndpointSpecInput& input,
                                                   const CommunicationContract& contract) noexcept;

  /** @brief Copy an immutable declaration. @param other Valid source declaration. */
  EndpointSpec(const EndpointSpec& other) noexcept = default;
  /** Assignment is disabled so previously returned views cannot be invalidated. */
  EndpointSpec& operator=(const EndpointSpec&) = delete;

  /** @return Logical endpoint identity independent of realization. */
  [[nodiscard]] const Identity& endpoint_id() const noexcept { return endpoint_id_; }
  /** @return Exact canonical plan digest. */
  [[nodiscard]] std::string_view plan_digest() const noexcept { return plan_digest_.view(); }
  /** @return Explicit logical provider identity. */
  [[nodiscard]] const Identity& provider_id() const noexcept { return provider_id_; }
  /** @return Endpoint direction validated against the contract. */
  [[nodiscard]] EndpointDirection direction() const noexcept { return direction_; }
  /** @return Complete exact communication contract. */
  [[nodiscard]] const CommunicationContract& contract() const noexcept { return contract_; }

  /**
   * @param left First endpoint declaration.
   * @param right Second endpoint declaration.
   * @return true only when every immutable endpoint field is equal.
   */
  friend bool operator==(const EndpointSpec& left, const EndpointSpec& right) = default;

 private:
  /**
   * @brief Own already validated endpoint fields.
   * @param endpoint_id Logical endpoint identity.
   * @param plan_digest Exact canonical plan digest.
   * @param provider_id Logical provider identity.
   * @param direction Contract-compatible direction.
   * @param contract Exact immutable communication contract.
   */
  EndpointSpec(const Identity& endpoint_id,
               const detail::FixedText<kPlanDigestBytes>& plan_digest,
               const Identity& provider_id, EndpointDirection direction,
               const CommunicationContract& contract) noexcept;

  Identity endpoint_id_; /**< Owned logical endpoint identity. */
  detail::FixedText<kPlanDigestBytes> plan_digest_; /**< Owned exact plan digest. */
  Identity provider_id_; /**< Owned logical provider identity. */
  EndpointDirection direction_; /**< Contract-compatible endpoint direction. */
  CommunicationContract contract_; /**< Owned exact communication contract. */
};

/**
 * @brief Call-scoped route declaration input.
 * @ownership Owns no text; RouteSpec::create copies accepted fields.
 * @lifetime Views need remain valid only for the factory call.
 * @thread_safety Distinct inputs may be used concurrently.
 * @failure The factory rejects incomplete, malformed, or endpoint-incompatible input.
 */
struct RouteSpecInput final {
  /** Logical route identity. */
  std::string_view route_id;
  /** Exact activation-plan digest shared by route and endpoints. */
  std::string_view plan_digest;
  /** Explicit provider identity shared by route and endpoints. */
  std::string_view provider_id;
};

/**
 * @brief Immutable validated route declaration between two logical endpoints.
 * @ownership Owns all route, endpoint, plan, provider, and contract identities.
 * @lifetime Accessor views and references remain valid while this value lives.
 * @thread_safety Concurrent const access is safe; no mutation is exposed.
 * @failure create() returns stable diagnostics and retains no endpoint reference.
 */
class RouteSpec final {
 public:
  /**
   * @brief Validate a route against exact source and destination declarations.
   * @param input Logical route, plan digest, and provider identity.
   * @param source Exact logical source endpoint declaration.
   * @param destination Exact logical destination endpoint declaration.
   * @return Valid route declaration or stable diagnostics.
   */
  [[nodiscard]] static Result<RouteSpec> create(const RouteSpecInput& input,
                                                const EndpointSpec& source,
                                                const EndpointSpec& destination) noexcept;

  /**
   * @brief Validate a route and bind exactly one already-validated declared flow policy.
   * @param input Logical route, plan digest, and provider identity.
   * @param source Exact logical source endpoint declaration.
   * @param destination Exact logical destination endpoint declaration.
   * @param policy Already-validated immutable declared bounded delivery policy to bind.
   * @return Valid policy-bound route declaration or stable diagnostics.
   * @ownership The factory copies the policy into the returned route; the caller keeps its own value.
   * @lifetime The bound policy is reachable only through this route value and the exact generation
   * that declared it.
   * @thread_safety The caller's policy and the returned route support concurrent const reads.
   * @failure Rejects exactly as the three-argument factory does and never substitutes, defaults, or
   * weakens the declared policy.
   */
  [[nodiscard]] static Result<RouteSpec> create(const RouteSpecInput& input,
                                                const EndpointSpec& source,
                                                const EndpointSpec& destination,
                                                const FlowPolicy& policy) noexcept;

  /** @brief Copy an immutable route declaration. @param other Valid source declaration. */
  RouteSpec(const RouteSpec& other) noexcept = default;
  /** Assignment is disabled so returned views remain stable. */
  RouteSpec& operator=(const RouteSpec&) = delete;

  /** @return Logical route identity. */
  [[nodiscard]] const Identity& route_id() const noexcept { return route_id_; }
  /** @return Exact plan digest. */
  [[nodiscard]] std::string_view plan_digest() const noexcept { return plan_digest_.view(); }
  /** @return Explicit provider identity. */
  [[nodiscard]] const Identity& provider_id() const noexcept { return provider_id_; }
  /** @return Logical source endpoint identity. */
  [[nodiscard]] const Identity& source_endpoint_id() const noexcept { return source_endpoint_id_; }
  /** @return Logical destination endpoint identity. */
  [[nodiscard]] const Identity& destination_endpoint_id() const noexcept {
    return destination_endpoint_id_;
  }
  /** @return Exact communication contract shared by both endpoints. */
  [[nodiscard]] const CommunicationContract& contract() const noexcept { return contract_; }

  /**
   * @brief Report whether this route generation declared exactly one bounded flow policy.
   * @return true only when the declared policy is present.
   * @ownership The answer describes storage owned by this RouteSpec.
   * @lifetime Reflects the declaration for the whole lifetime of this value.
   * @thread_safety Concurrent const access is safe; no mutation is exposed.
   * @failure Never fails; an unbound route reports false rather than a substituted default.
   */
  [[nodiscard]] bool has_policy() const noexcept { return policy_.has_value(); }

  /**
   * @brief View the owned declared bounded delivery policy, if any.
   * @return Pointer to the owned declared policy, or nullptr when this route declared none.
   * @ownership The returned pointer views storage owned by this RouteSpec.
   * @lifetime Valid only while this RouteSpec lives; it is never a temporary or default value.
   * @thread_safety Concurrent const access is safe; no mutation is exposed.
   * @failure Returns nullptr rather than substituting, defaulting, or inferring a policy.
   */
  [[nodiscard]] const FlowPolicy* policy() const noexcept {
    return policy_.has_value() ? &*policy_ : nullptr;
  }

  /**
   * @param left First route declaration.
   * @param right Second route declaration.
   * @return true only when every immutable route field, including the declared policy, is equal.
   */
  friend bool operator==(const RouteSpec& left, const RouteSpec& right) = default;

 private:
  /**
   * @brief Shared validation path for the three- and four-argument route factories.
   * @param input Logical route, plan digest, and provider identity.
   * @param source Exact logical source endpoint declaration.
   * @param destination Exact logical destination endpoint declaration.
   * @param policy Declared policy to copy, or nullptr when the route declares none.
   * @return Valid route declaration or stable diagnostics.
   */
  [[nodiscard]] static Result<RouteSpec> create_impl(const RouteSpecInput& input,
                                                     const EndpointSpec& source,
                                                     const EndpointSpec& destination,
                                                     const FlowPolicy* policy) noexcept;

  /**
   * @brief Own already validated route, endpoint, and optional declared-policy fields.
   * @param route_id Logical route identity.
   * @param digest Exact plan digest.
   * @param provider_id Logical provider identity.
   * @param source Compatible source declaration.
   * @param destination Compatible destination declaration.
   * @param policy Already-validated declared policy copied when non-null, or nullptr for none.
   */
  RouteSpec(const Identity& route_id, const detail::FixedText<EndpointSpec::kPlanDigestBytes>& digest,
            const Identity& provider_id, const EndpointSpec& source,
            const EndpointSpec& destination, const FlowPolicy* policy) noexcept;

  Identity route_id_; /**< Owned logical route identity. */
  detail::FixedText<EndpointSpec::kPlanDigestBytes> plan_digest_; /**< Exact plan digest. */
  Identity provider_id_; /**< Owned logical provider identity. */
  Identity source_endpoint_id_; /**< Owned logical source endpoint identity. */
  Identity destination_endpoint_id_; /**< Owned logical destination endpoint identity. */
  CommunicationContract contract_; /**< Owned exact endpoint contract. */
  std::optional<FlowPolicy> policy_; /**< Owned declared policy, empty when this route declared none. */
};

/**
 * @brief Validated finite controller capacities.
 * @ownership Stores counts by value.
 * @lifetime Ordinary value lifetime with no references.
 * @thread_safety Concurrent const reads are safe.
 * @failure create() rejects zero or over-maximum capacities.
 */
struct LifecycleConfigurationInput final {
  /** Configured endpoint record capacity. */
  std::size_t endpoint_capacity;
  /** Configured route record capacity. */
  std::size_t route_capacity;
};

/** Immutable validated lifecycle storage configuration. */
class LifecycleConfiguration final {
 public:
  /**
   * @brief Validate finite nonzero capacities against compile-time maxima.
   * @param input Caller-requested endpoint and route capacities.
   * @return Validated configuration or stable bounds diagnostics.
   */
  [[nodiscard]] static Result<LifecycleConfiguration> create(
      const LifecycleConfigurationInput& input) noexcept;
  /** @brief Copy a validated configuration. @param other Valid source configuration. */
  LifecycleConfiguration(const LifecycleConfiguration& other) noexcept = default;
  /** Assignment is disabled to preserve immutability. */
  LifecycleConfiguration& operator=(const LifecycleConfiguration&) = delete;
  /** @return Configured endpoint capacity. */
  [[nodiscard]] std::size_t endpoint_capacity() const noexcept { return endpoint_capacity_; }
  /** @return Configured route capacity. */
  [[nodiscard]] std::size_t route_capacity() const noexcept { return route_capacity_; }

 private:
  friend class LifecycleController;
  /**
   * @brief Store capacities already validated by create().
   * @param endpoint_capacity Valid endpoint capacity.
   * @param route_capacity Valid route capacity.
   */
  LifecycleConfiguration(std::size_t endpoint_capacity, std::size_t route_capacity) noexcept
      : endpoint_capacity_(endpoint_capacity), route_capacity_(route_capacity) {}
  std::size_t endpoint_capacity_; /**< Valid configured endpoint capacity. */
  std::size_t route_capacity_; /**< Valid configured route capacity. */
};

/**
 * @brief Opaque exact ownership handle for one endpoint generation.
 * @ownership Owns its complete binding; it owns no controller resource.
 * @lifetime The value may outlive the controller but is usable only with the issuing live controller.
 * @thread_safety Copies and concurrent const access are safe.
 * @failure Only LifecycleController can issue a handle after successful declaration.
 */
class EndpointHandle final {
 public:
  /** @brief Copy an issued immutable handle. @param other Valid source handle. */
  EndpointHandle(const EndpointHandle& other) noexcept = default;
  /** Assignment is disabled to preserve an exact binding. */
  EndpointHandle& operator=(const EndpointHandle&) = delete;
  /** @return Opaque issuing-controller identity. */
  [[nodiscard]] std::uint64_t controller_id() const noexcept { return controller_id_; }
  /** @return Endpoint resource kind. */
  [[nodiscard]] ResourceKind kind() const noexcept { return ResourceKind::endpoint; }
  /** @return Logical endpoint identity. */
  [[nodiscard]] const Identity& identity() const noexcept { return identity_; }
  /** @return Exact plan digest binding. */
  [[nodiscard]] std::string_view plan_digest() const noexcept { return plan_digest_.view(); }
  /** @return Nonzero endpoint generation. */
  [[nodiscard]] std::uint64_t generation() const noexcept { return generation_; }

 private:
  friend class LifecycleController;
  /**
   * @brief Construct an issued endpoint handle.
   * @param controller_id Nonzero issuing-controller identity.
   * @param identity Logical endpoint identity.
   * @param plan_digest Exact plan digest.
   * @param generation Nonzero issued generation.
   */
  EndpointHandle(std::uint64_t controller_id, const Identity& identity,
                 std::string_view plan_digest, std::uint64_t generation) noexcept;
  std::uint64_t controller_id_; /**< Nonzero issuing-controller identity. */
  Identity identity_; /**< Owned logical endpoint identity. */
  detail::FixedText<EndpointSpec::kPlanDigestBytes> plan_digest_; /**< Exact plan digest. */
  std::uint64_t generation_; /**< Nonzero endpoint generation. */
};

/** Opaque exact ownership handle for one route generation. */
class RouteHandle final {
 public:
  /** @brief Copy an issued immutable handle. @param other Valid source handle. */
  RouteHandle(const RouteHandle& other) noexcept = default;
  /** Assignment is disabled to preserve an exact binding. */
  RouteHandle& operator=(const RouteHandle&) = delete;
  /** @return Opaque issuing-controller identity. */
  [[nodiscard]] std::uint64_t controller_id() const noexcept { return controller_id_; }
  /** @return Route resource kind. */
  [[nodiscard]] ResourceKind kind() const noexcept { return ResourceKind::route; }
  /** @return Logical route identity. */
  [[nodiscard]] const Identity& identity() const noexcept { return identity_; }
  /** @return Exact plan digest binding. */
  [[nodiscard]] std::string_view plan_digest() const noexcept { return plan_digest_.view(); }
  /** @return Nonzero route generation. */
  [[nodiscard]] std::uint64_t generation() const noexcept { return generation_; }

 private:
  friend class LifecycleController;
  /**
   * @brief Construct an issued route handle.
   * @param controller_id Nonzero issuing-controller identity.
   * @param identity Logical route identity.
   * @param plan_digest Exact plan digest.
   * @param generation Nonzero issued generation.
   */
  RouteHandle(std::uint64_t controller_id, const Identity& identity,
              std::string_view plan_digest, std::uint64_t generation) noexcept;
  std::uint64_t controller_id_; /**< Nonzero issuing-controller identity. */
  Identity identity_; /**< Owned logical route identity. */
  detail::FixedText<EndpointSpec::kPlanDigestBytes> plan_digest_; /**< Exact plan digest. */
  std::uint64_t generation_; /**< Nonzero route generation. */
};

/**
 * @brief Immutable owned lifecycle observation for one exact resource generation.
 * @ownership Owns identity, plan digest, kind, generation, and state.
 * @lifetime Accessor views remain valid while this snapshot lives.
 * @thread_safety Concurrent const reads are safe.
 * @failure Snapshots are created only after exact handle authentication.
 */
class LifecycleSnapshot final {
 public:
  /** @brief Copy an immutable snapshot. @param other Valid source snapshot. */
  LifecycleSnapshot(const LifecycleSnapshot& other) noexcept = default;
  /** Assignment is disabled to preserve observation immutability. */
  LifecycleSnapshot& operator=(const LifecycleSnapshot&) = delete;
  /** @return Resource kind. */
  [[nodiscard]] ResourceKind kind() const noexcept { return kind_; }
  /** @return Logical resource identity. */
  [[nodiscard]] const Identity& identity() const noexcept { return identity_; }
  /** @return Exact plan digest. */
  [[nodiscard]] std::string_view plan_digest() const noexcept { return plan_digest_.view(); }
  /** @return Nonzero resource generation. */
  [[nodiscard]] std::uint64_t generation() const noexcept { return generation_; }
  /** @return Observed lifecycle state. */
  [[nodiscard]] LifecycleState state() const noexcept { return state_; }
  /**
   * @brief Report whether the observed generation declared a bounded flow policy.
   * @return true only for a route generation that declared exactly one policy; false for endpoints
   * and for routes that declared none.
   * @ownership The answer describes the snapshot's own immutable state.
   * @lifetime Valid while this snapshot lives.
   * @thread_safety Concurrent const access is safe.
   * @failure Never fails; an unbound observation reports false without inference.
   */
  [[nodiscard]] bool policy_bound() const noexcept { return policy_bound_; }
  /**
   * @param left First snapshot.
   * @param right Second snapshot.
   * @return true only when all snapshot fields are equal.
   */
  friend bool operator==(const LifecycleSnapshot& left, const LifecycleSnapshot& right) = default;

 private:
  friend class LifecycleController;
  /**
   * @brief Construct one authenticated point-in-time observation.
   * @param kind Resource kind.
   * @param identity Logical resource identity.
   * @param digest Exact plan digest.
   * @param generation Current nonzero generation.
   * @param state Current lifecycle state.
   * @param policy_bound Whether the observed route generation declared a bounded flow policy.
   */
  LifecycleSnapshot(ResourceKind kind, const Identity& identity, std::string_view digest,
                    std::uint64_t generation, LifecycleState state, bool policy_bound) noexcept;
  ResourceKind kind_; /**< Exact resource kind. */
  Identity identity_; /**< Owned logical resource identity. */
  detail::FixedText<EndpointSpec::kPlanDigestBytes> plan_digest_; /**< Exact plan digest. */
  std::uint64_t generation_; /**< Nonzero observed generation. */
  LifecycleState state_; /**< Observed lifecycle state. */
  bool policy_bound_; /**< Whether the observed generation declared a bounded flow policy. */
};

/**
 * @brief Serialized fixed-capacity owner of endpoint and route lifecycle records.
 * @ownership Owns all records in compile-time arrays; handles never own or extend records.
 * @lifetime Handles become unusable when the controller dies or their identity is recreated.
 * Snapshots are independent owned values and remain readable after later transitions.
 * @thread_safety Every public operation locks one internal mutex; callbacks are never invoked.
 * @failure Rejections return stable diagnostics and leave all records and generations unchanged.
 */
class LifecycleController final {
 public:
  /** Compile-time endpoint storage maximum. */
  static constexpr std::size_t kMaximumEndpoints = 32U;
  /** Compile-time route storage maximum. */
  static constexpr std::size_t kMaximumRoutes = 32U;

  /**
   * @brief Construct empty fixed storage from a validated finite configuration.
   * @param configuration Valid finite capacities copied by value.
   */
  explicit LifecycleController(const LifecycleConfiguration& configuration) noexcept;
  LifecycleController(const LifecycleController&) = delete;
  LifecycleController& operator=(const LifecycleController&) = delete;

  /** @return Opaque nonzero controller identity used for handle authentication. */
  [[nodiscard]] std::uint64_t controller_id() const noexcept { return controller_id_; }
  /** @return Configured endpoint capacity within the compile-time array. */
  [[nodiscard]] std::size_t endpoint_capacity() const noexcept { return endpoint_capacity_; }
  /** @return Configured route capacity within the compile-time array. */
  [[nodiscard]] std::size_t route_capacity() const noexcept { return route_capacity_; }

  /**
   * @brief Declare one endpoint or reject capacity/duplicate failure without mutation.
   * @param spec Valid immutable endpoint declaration.
   * @return Newly issued exact endpoint handle or stable diagnostics.
   */
  [[nodiscard]] Result<EndpointHandle> declare_endpoint(const EndpointSpec& spec) noexcept;
  /**
   * @brief Declare one route or reject capacity/duplicate failure without mutation.
   * @param spec Valid immutable route declaration.
   * @return Newly issued exact route handle or stable diagnostics.
   */
  [[nodiscard]] Result<RouteHandle> declare_route(const RouteSpec& spec) noexcept;

  /**
   * @brief Return a snapshot after exact endpoint-handle authentication.
   * @param handle Exact current endpoint handle.
   * @return Immutable snapshot or stable ownership diagnostics.
   */
  [[nodiscard]] Result<LifecycleSnapshot> endpoint_snapshot(const EndpointHandle& handle) const noexcept;
  /**
   * @brief Return a snapshot after exact route-handle authentication.
   * @param handle Exact current route handle.
   * @return Immutable snapshot or stable ownership diagnostics.
   */
  [[nodiscard]] Result<LifecycleSnapshot> route_snapshot(const RouteHandle& handle) const noexcept;

  /**
   * @brief Copy the retained declaration after exact endpoint-handle authentication.
   * @param handle Exact current endpoint handle.
   * @return Independent owned endpoint declaration or stable ownership diagnostics.
   *
   * The returned value exposes no controller storage and remains valid after later lifecycle
   * transitions. A stale, foreign, recreated, or otherwise inauthentic handle returns failure.
   */
  [[nodiscard]] Result<EndpointSpec> endpoint_declaration(
      const EndpointHandle& handle) const noexcept;
  /**
   * @brief Copy the retained declaration after exact route-handle authentication.
   * @param handle Exact current route handle.
   * @return Independent owned route declaration or stable ownership diagnostics.
   *
   * The returned value exposes no controller storage and remains valid after later lifecycle
   * transitions. A stale, foreign, recreated, or otherwise inauthentic handle returns failure.
   */
  [[nodiscard]] Result<RouteSpec> route_declaration(const RouteHandle& handle) const noexcept;

  /**
   * @brief Return the exact declared bounded delivery policy after route-handle authentication.
   * @param handle Exact current route handle.
   * @return The exact declared policy copied from the route generation, or stable diagnostics.
   * @ownership The returned policy is an independent owned copy of the generation's declaration.
   * @lifetime The returned value remains valid independently of the controller; the binding stays
   * reachable only through the exact generation that declared it.
   * @thread_safety Serialized with every controller operation; concurrent const reads are safe.
   * @failure Returns an ownership diagnostic for a stale, foreign, or mismatched handle, and a
   * route-declaration diagnostic when the generation declared no policy; it never substitutes,
   * defaults, or infers a policy.
   */
  [[nodiscard]] Result<FlowPolicy> route_policy(const RouteHandle& handle) const noexcept;

  /**
   * @brief Transition an endpoint from declared to validated; validated repeats are safe.
   * @param handle Exact current endpoint handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> validate_endpoint(const EndpointHandle& handle) noexcept;
  /**
   * @brief Transition an endpoint from validated to active; active repeats are safe.
   * @param handle Exact current endpoint handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> activate_endpoint(const EndpointHandle& handle) noexcept;
  /**
   * @brief Transition an unused active endpoint to draining; draining repeats are safe.
   * @param handle Exact current endpoint handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> drain_endpoint(const EndpointHandle& handle) noexcept;
  /**
   * @brief Transition any nonterminal operational endpoint to failed; failed repeats are safe.
   * @param handle Exact current endpoint handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> fail_endpoint(const EndpointHandle& handle) noexcept;
  /**
   * @brief Close a draining or failed endpoint; closed repeats are safe until recreation.
   * @param handle Exact current endpoint handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> close_endpoint(const EndpointHandle& handle) noexcept;

  /**
   * @brief Validate a route against exact current validated-or-active endpoint handles.
   * @param handle Exact current route handle.
   * @param source Exact current logical source endpoint handle.
   * @param destination Exact current logical destination endpoint handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> validate_route(
      const RouteHandle& handle, const EndpointHandle& source,
      const EndpointHandle& destination) noexcept;
  /**
   * @brief Activate a validated route only while both exact endpoints are active.
   * @param handle Exact current route handle.
   * @param source Exact current active source endpoint handle.
   * @param destination Exact current active destination endpoint handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> activate_route(
      const RouteHandle& handle, const EndpointHandle& source,
      const EndpointHandle& destination) noexcept;
  /**
   * @brief Transition an active route to draining; draining repeats are safe.
   * @param handle Exact current route handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> drain_route(const RouteHandle& handle) noexcept;
  /**
   * @brief Transition any nonterminal operational route to failed; failed repeats are safe.
   * @param handle Exact current route handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> fail_route(const RouteHandle& handle) noexcept;
  /**
   * @brief Close a draining or failed route; closed repeats are safe until recreation.
   * @param handle Exact current route handle.
   * @return Resulting snapshot or stable diagnostics without mutation.
   */
  [[nodiscard]] Result<LifecycleSnapshot> close_route(const RouteHandle& handle) noexcept;

 private:
  /** Controller-owned endpoint declaration, generation, and mutable lifecycle state. */
  struct EndpointRecord final {
    /**
     * @brief Copy one declaration into a newly issued generation.
     * @param declaration Valid endpoint declaration.
     * @param issued_generation New nonzero generation.
     */
    EndpointRecord(const EndpointSpec& declaration, std::uint64_t issued_generation) noexcept
        : spec(declaration), generation(issued_generation) {}
    /** Immutable endpoint declaration. */
    EndpointSpec spec;
    /** Exact nonzero issued generation. */
    std::uint64_t generation;
    /** Serialized lifecycle state. */
    LifecycleState state{LifecycleState::declared};
  };
  /** Controller-owned route declaration, generation, and mutable lifecycle state. */
  struct RouteRecord final {
    /**
     * @brief Copy one declaration into a newly issued generation.
     * @param declaration Valid route declaration.
     * @param issued_generation New nonzero generation.
     */
    RouteRecord(const RouteSpec& declaration, std::uint64_t issued_generation) noexcept
        : spec(declaration), generation(issued_generation) {}
    /** Immutable route declaration. */
    RouteSpec spec;
    /** Exact nonzero issued generation. */
    std::uint64_t generation;
    /** Serialized lifecycle state. */
    LifecycleState state{LifecycleState::declared};
  };

  /** @brief Authenticate an endpoint handle; @param handle Candidate handle. @return Record or null. */
  [[nodiscard]] EndpointRecord* authenticate_endpoint(const EndpointHandle& handle) noexcept;
  /** @brief Authenticate an endpoint handle; @param handle Candidate handle. @return Record or null. */
  [[nodiscard]] const EndpointRecord* authenticate_endpoint(
      const EndpointHandle& handle) const noexcept;
  /** @brief Authenticate a route handle; @param handle Candidate handle. @return Record or null. */
  [[nodiscard]] RouteRecord* authenticate_route(const RouteHandle& handle) noexcept;
  /** @brief Authenticate a route handle; @param handle Candidate handle. @return Record or null. */
  [[nodiscard]] const RouteRecord* authenticate_route(const RouteHandle& handle) const noexcept;
  /**
   * @brief Inspect whether a nonclosed route uses an endpoint identity.
   * @param endpoint_id Logical endpoint identity.
   * @return true when a nonclosed route refers to the endpoint.
   */
  [[nodiscard]] bool endpoint_in_use(std::string_view endpoint_id) const noexcept;

  /** Opaque nonzero controller instance identity. */
  std::uint64_t controller_id_;
  /** Next nonzero generation; advanced only after successful declaration. */
  std::uint64_t next_generation_{1U};
  /** Caller-configured endpoint prefix length. */
  std::size_t endpoint_capacity_;
  /** Caller-configured route prefix length. */
  std::size_t route_capacity_;
  /** Serializes every controller operation. */
  mutable std::mutex mutex_;
  /** Compile-time-bounded endpoint record slots. */
  std::array<std::optional<EndpointRecord>, kMaximumEndpoints> endpoints_{};
  /** Compile-time-bounded route record slots. */
  std::array<std::optional<RouteRecord>, kMaximumRoutes> routes_{};
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_ENDPOINT_ROUTE_LIFECYCLE_HPP
