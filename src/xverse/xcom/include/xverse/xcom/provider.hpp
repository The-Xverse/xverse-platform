/**
 * @file provider.hpp
 * @brief Explicit source-linked X-COM provider composition contracts.
 * @ownership Public values own their data. ProviderComposition retains non-owning provider pointers;
 * registered providers must outlive it and every handle it issued.
 * @lifetime Handles are usable only with their issuing provider instance, registration generation,
 * and the exact current lifecycle generations copied into the handle.
 * @thread_safety ProviderComposition serializes registry mutation and never calls a provider while
 * holding its registry mutex. Concrete providers define operation serialization.
 * @failure Every operation returns a stable ProviderOutcome and never infers ownership from names.
 */

#ifndef XVERSE_XCOM_PROVIDER_HPP
#define XVERSE_XCOM_PROVIDER_HPP

#include "xverse/xcom/endpoint_route_lifecycle.hpp"
#include "xverse/xcom/item.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include <string_view>

namespace xverse::xcom {

/** Delivery claims that an explicitly linked provider may advertise. */
enum class DeliveryCapability : std::uint8_t {
  /** No delivery guarantee beyond an explicit accepted/rejected outcome. */
  best_effort = 1U,
  /** Delivery reliability is explicitly claimed by the provider. */
  reliable = 2U,
};

/** Ordering claims that an explicitly linked provider may advertise. */
enum class OrderingCapability : std::uint8_t {
  /** No ordering guarantee is claimed. */
  unordered = 1U,
  /** Accepted items retain FIFO submission order independently for each route. */
  per_route_fifo = 2U,
};

/** Stable outcomes shared by composition and provider operations. */
enum class ProviderOutcome {
  /** An explicitly supplied provider was retained by the registry. */
  registered,
  /** A route resource was prepared without traffic emission. */
  prepared,
  /** A prepared route and its exact lifecycle resource became active. */
  activated,
  /** An item was copied into the bounded destination queue. */
  accepted,
  /** The oldest accepted item was removed and returned by value. */
  received,
  /** A route stopped accepting new items and retained its queued items. */
  draining,
  /** An empty drained route released its provider-owned resource. */
  closed,
  /** Exact provider and lifecycle state were reconciled without mutation. */
  reconciled,
  /** No accepted item is currently queued. */
  queue_empty,
  /** The configured queue is full; all earlier items remain unchanged. */
  queue_saturated,
  /** A descriptor field or capability mask is malformed. */
  invalid_descriptor,
  /** The provider identity is already registered. */
  duplicate_provider,
  /** The configured fixed provider registry is full. */
  provider_capacity_exhausted,
  /** The requested source contract version is unsupported. */
  unsupported_contract_version,
  /** The requested interaction family is unsupported. */
  unsupported_interaction,
  /** The requested delivery claim is unsupported. */
  unsupported_delivery,
  /** The requested ordering claim is unsupported. */
  unsupported_ordering,
  /** The requested or submitted payload exceeds the prepared limit. */
  payload_limit_exceeded,
  /** The requested queue capacity is zero or exceeds the provider limit. */
  queue_limit_exceeded,
  /** The provider has no free fixed route slot. */
  route_capacity_exhausted,
  /** A provider-route handle is stale, foreign, or otherwise inauthentic. */
  invalid_provider_route_handle,
  /** An exact endpoint or route lifecycle binding is stale, foreign, or in the wrong state. */
  lifecycle_mismatch,
  /** The provider route is not active for submission or receipt. */
  inactive_route,
  /** Route identity, digest, or generation differs from the prepared binding. */
  route_mismatch,
  /** Provider identity or instance differs from the prepared binding. */
  provider_mismatch,
  /** Item contract, kind, source endpoint, route, or provider metadata differs. */
  item_mismatch,
  /** A route still retains accepted items and cannot release its resource. */
  queued_items_remain,
  /** Provider and lifecycle state cannot be reconciled safely. */
  interrupted_resource,
};

/**
 * @param kind Interaction family.
 * @return One stable mask bit for the interaction family, or zero for an unknown value.
 */
[[nodiscard]] constexpr std::uint8_t interaction_capability_bit(
    const InteractionKind kind) noexcept {
  switch (kind) {
    case InteractionKind::signal_state_update:
      return 1U;
    case InteractionKind::message_event:
      return 2U;
    case InteractionKind::service_request:
      return 4U;
    case InteractionKind::service_response:
      return 8U;
  }
  return 0U;
}

/** @param capability Delivery capability. @return Its stable mask bit. */
[[nodiscard]] constexpr std::uint8_t delivery_capability_bit(
    const DeliveryCapability capability) noexcept {
  return static_cast<std::uint8_t>(capability);
}

/** @param capability Ordering capability. @return Its stable mask bit. */
[[nodiscard]] constexpr std::uint8_t ordering_capability_bit(
    const OrderingCapability capability) noexcept {
  return static_cast<std::uint8_t>(capability);
}

/** @param outcome Stable operation outcome. @return Stable external outcome text. */
[[nodiscard]] std::string_view to_string(ProviderOutcome outcome) noexcept;
/** @param outcome Stable operation outcome. @return Stable diagnostic code. */
[[nodiscard]] std::string_view provider_diagnostic_code(ProviderOutcome outcome) noexcept;
/** @param outcome Stable operation outcome. @return Stable diagnostic explanation. */
[[nodiscard]] std::string_view provider_diagnostic_message(ProviderOutcome outcome) noexcept;

/** Call-scoped input for a validated source-linked provider descriptor. */
struct ProviderDescriptorInput final {
  /** Stable logical provider identity, never an address. */
  std::string_view provider_id;
  /** Exact source-level provider contract version. */
  std::string_view contract_version;
  /** Stable source-link identity for this explicitly supplied implementation. */
  std::string_view source_link;
  /** Nonzero mask of supported InteractionKind values. */
  std::uint8_t interaction_mask;
  /** Nonzero mask of DeliveryCapability values. */
  std::uint8_t delivery_mask;
  /** Nonzero mask of OrderingCapability values. */
  std::uint8_t ordering_mask;
  /** Maximum accepted payload bytes per item. */
  std::size_t maximum_payload_bytes;
  /** Maximum simultaneously retained route resources. */
  std::size_t maximum_routes;
  /** Maximum configured items per route queue. */
  std::size_t maximum_queue_items;
};

/** Immutable validated provider identity, capabilities, and hard limits. */
class ProviderDescriptor final {
 public:
  /**
   * @brief Validate and own an explicit provider descriptor.
   * @param input Candidate identity, version, capabilities, and finite limits.
   * @return A descriptor or deterministic validation diagnostics.
   */
  [[nodiscard]] static Result<ProviderDescriptor> create(
      const ProviderDescriptorInput& input) noexcept;

  /** @brief Copy a descriptor. @param other Valid source descriptor. */
  ProviderDescriptor(const ProviderDescriptor& other) noexcept = default;
  /** Assignment is disabled to keep returned views stable. */
  ProviderDescriptor& operator=(const ProviderDescriptor&) = delete;

  /** @return Stable logical provider identity. */
  [[nodiscard]] const Identity& provider_id() const noexcept { return provider_id_; }
  /** @return Exact source provider-contract version. */
  [[nodiscard]] const SemanticVersion& contract_version() const noexcept {
    return contract_version_;
  }
  /** @return Explicit source-link identity. */
  [[nodiscard]] const Identity& source_link() const noexcept { return source_link_; }
  /** @return Supported interaction mask. */
  [[nodiscard]] std::uint8_t interaction_mask() const noexcept { return interaction_mask_; }
  /** @return Supported delivery mask. */
  [[nodiscard]] std::uint8_t delivery_mask() const noexcept { return delivery_mask_; }
  /** @return Supported ordering mask. */
  [[nodiscard]] std::uint8_t ordering_mask() const noexcept { return ordering_mask_; }
  /** @return Maximum accepted payload bytes. */
  [[nodiscard]] std::size_t maximum_payload_bytes() const noexcept {
    return maximum_payload_bytes_;
  }
  /** @return Maximum provider-owned route resources. */
  [[nodiscard]] std::size_t maximum_routes() const noexcept { return maximum_routes_; }
  /** @return Maximum items in each route queue. */
  [[nodiscard]] std::size_t maximum_queue_items() const noexcept {
    return maximum_queue_items_;
  }

 private:
  ProviderDescriptor(const Identity& provider_id, const SemanticVersion& contract_version,
                     const Identity& source_link, std::uint8_t interaction_mask,
                     std::uint8_t delivery_mask, std::uint8_t ordering_mask,
                     std::size_t maximum_payload_bytes, std::size_t maximum_routes,
                     std::size_t maximum_queue_items) noexcept;

  Identity provider_id_; /**< Owned logical provider identity. */
  SemanticVersion contract_version_; /**< Owned provider-contract version. */
  Identity source_link_; /**< Owned explicit source link. */
  std::uint8_t interaction_mask_; /**< Supported interaction bits. */
  std::uint8_t delivery_mask_; /**< Supported delivery bits. */
  std::uint8_t ordering_mask_; /**< Supported ordering bits. */
  std::size_t maximum_payload_bytes_; /**< Hard payload bound. */
  std::size_t maximum_routes_; /**< Hard route bound. */
  std::size_t maximum_queue_items_; /**< Hard per-route queue bound. */
};

/** Requested route semantics checked before any provider resource is prepared. */
struct ProviderRouteRequirements final {
  /** Required exact source provider-contract version. */
  std::string_view provider_contract_version;
  /** Required communication interaction family. */
  InteractionKind interaction_kind;
  /** Required delivery capability without claim strengthening. */
  DeliveryCapability delivery;
  /** Required ordering capability without claim strengthening. */
  OrderingCapability ordering;
  /** Maximum payload bytes accepted on this route. */
  std::size_t maximum_payload_bytes;
  /** Finite reject-new destination queue capacity. */
  std::size_t queue_capacity;
};

/** Provider-owned route lifecycle state. */
enum class ProviderRouteState {
  /** Resource is allocated and bound but emits no traffic. */
  prepared,
  /** Exact route is active for submit and receive. */
  active,
  /** New submissions are rejected while retained items may be received. */
  draining,
  /** Provider-owned resource was released after an empty drain. */
  closed,
};

/** @param state Provider-owned route state. @return Stable external text. */
[[nodiscard]] std::string_view to_string(ProviderRouteState state) noexcept;

/** Opaque exact provider-route handle, including lifecycle generations. */
class ProviderRouteHandle final {
 public:
  /** @brief Copy an issued handle. @param other Valid source handle. */
  ProviderRouteHandle(const ProviderRouteHandle& other) noexcept = default;
  /** Assignment is disabled to preserve exact binding. */
  ProviderRouteHandle& operator=(const ProviderRouteHandle&) = delete;
  /** @return Opaque issuing composition identity. */
  [[nodiscard]] std::uint64_t composition_instance_id() const noexcept {
    return composition_instance_id_;
  }
  /** @return Opaque issuing provider instance identity. */
  [[nodiscard]] std::uint64_t provider_instance_id() const noexcept {
    return provider_instance_id_;
  }
  /** @return Exact registry generation for this provider. */
  [[nodiscard]] std::uint64_t registration_generation() const noexcept {
    return registration_generation_;
  }
  /** @return Logical provider identity. */
  [[nodiscard]] const Identity& provider_id() const noexcept { return provider_id_; }
  /** @return Logical route identity. */
  [[nodiscard]] const Identity& route_id() const noexcept { return route_id_; }
  /** @return Exact plan digest. */
  [[nodiscard]] std::string_view plan_digest() const noexcept { return plan_digest_.view(); }
  /** @return Provider-owned route generation. */
  [[nodiscard]] std::uint64_t provider_route_generation() const noexcept {
    return provider_route_generation_;
  }
  /** @return Exact lifecycle route generation. */
  [[nodiscard]] std::uint64_t lifecycle_route_generation() const noexcept {
    return lifecycle_route_generation_;
  }
  /** @return Exact source endpoint generation. */
  [[nodiscard]] std::uint64_t source_endpoint_generation() const noexcept {
    return source_endpoint_generation_;
  }
  /** @return Exact destination endpoint generation. */
  [[nodiscard]] std::uint64_t destination_endpoint_generation() const noexcept {
    return destination_endpoint_generation_;
  }

 private:
  friend class ProviderComposition;
  ProviderRouteHandle(std::uint64_t composition_instance_id,
                      std::uint64_t provider_instance_id,
                      std::uint64_t registration_generation, const Identity& provider_id,
                      const RouteHandle& route_handle, const EndpointHandle& source_handle,
                      const EndpointHandle& destination_handle,
                      std::uint64_t provider_route_generation,
                      std::size_t maximum_payload_bytes,
                      std::size_t queue_capacity) noexcept;

  std::uint64_t composition_instance_id_; /**< Issuing composition instance. */
  std::uint64_t provider_instance_id_; /**< Issuing provider instance. */
  std::uint64_t registration_generation_; /**< Exact registry generation. */
  Identity provider_id_; /**< Owned provider identity. */
  Identity route_id_; /**< Owned route identity. */
  detail::FixedText<EndpointSpec::kPlanDigestBytes> plan_digest_; /**< Exact digest. */
  std::uint64_t provider_route_generation_; /**< Provider route generation. */
  std::uint64_t lifecycle_route_generation_; /**< Lifecycle route generation. */
  std::uint64_t source_endpoint_generation_; /**< Source endpoint generation. */
  std::uint64_t destination_endpoint_generation_; /**< Destination endpoint generation. */
  RouteHandle route_handle_; /**< Exact lifecycle route authority retained by composition. */
  EndpointHandle source_handle_; /**< Exact lifecycle source authority retained by composition. */
  EndpointHandle destination_handle_; /**< Exact destination authority retained by composition. */
  std::size_t maximum_payload_bytes_; /**< Validated per-route item payload bound. */
  std::size_t queue_capacity_; /**< Validated fixed provider queue capacity. */
};

/** Immutable point-in-time provider route state and queue disposition. */
class ProviderRouteSnapshot final {
 public:
  /** @brief Copy an owned snapshot. @param other Valid source snapshot. */
  ProviderRouteSnapshot(const ProviderRouteSnapshot& other) noexcept = default;
  /** Assignment is disabled to preserve point-in-time semantics. */
  ProviderRouteSnapshot& operator=(const ProviderRouteSnapshot&) = delete;
  /** @return Exact route handle observed. */
  [[nodiscard]] const ProviderRouteHandle& handle() const noexcept { return handle_; }
  /** @return Provider-owned route state. */
  [[nodiscard]] ProviderRouteState state() const noexcept { return state_; }
  /** @return Number of accepted items currently retained. */
  [[nodiscard]] std::size_t queued_items() const noexcept { return queued_items_; }
  /** @return Fixed configured queue capacity. */
  [[nodiscard]] std::size_t queue_capacity() const noexcept { return queue_capacity_; }

 private:
  friend class ProviderComposition;
  ProviderRouteSnapshot(const ProviderRouteHandle& handle, ProviderRouteState state,
                        std::size_t queued_items, std::size_t queue_capacity) noexcept;
  ProviderRouteHandle handle_; /**< Exact observed handle. */
  ProviderRouteState state_; /**< Provider route state. */
  std::size_t queued_items_; /**< Retained item count. */
  std::size_t queue_capacity_; /**< Fixed route queue capacity. */
};

/** Immutable explicit provider registration returned by composition. */
class ProviderRegistration final {
 public:
  /** @brief Copy a registration. @param other Valid source registration. */
  ProviderRegistration(const ProviderRegistration& other) noexcept = default;
  /** Assignment is disabled to preserve exact binding. */
  ProviderRegistration& operator=(const ProviderRegistration&) = delete;
  /** @return Opaque provider object instance identity. */
  [[nodiscard]] std::uint64_t provider_instance_id() const noexcept {
    return provider_instance_id_;
  }
  /** @return Exact nonzero registry generation. */
  [[nodiscard]] std::uint64_t generation() const noexcept { return generation_; }
  /** @return Retained validated descriptor. */
  [[nodiscard]] const ProviderDescriptor& descriptor() const noexcept { return descriptor_; }

 private:
  friend class ProviderComposition;
  ProviderRegistration(std::uint64_t provider_instance_id, std::uint64_t generation,
                       const ProviderDescriptor& descriptor) noexcept;
  std::uint64_t provider_instance_id_; /**< Registered provider object identity. */
  std::uint64_t generation_; /**< Registry generation. */
  ProviderDescriptor descriptor_; /**< Owned registered descriptor. */
};

/**
 * @brief Owned operation result with a stable outcome and optional immutable value.
 * @tparam T Value type returned for successful outcomes.
 * @ownership Copies and owns any returned value; no provider storage is exposed.
 * @lifetime value() remains valid while this result lives.
 * @thread_safety Concurrent const reads follow T's const-read contract.
 * @failure A non-value outcome carries stable code and message mappings.
 */
template <typename T>
class ProviderResult final {
 public:
  /** @brief Create a value result. @param outcome Stable outcome. @param value Value to copy.
   * @return Owned result containing the copied value. */
  [[nodiscard]] static ProviderResult with_value(ProviderOutcome outcome,
                                                 const T& value) noexcept {
    return ProviderResult(outcome, value);
  }
  /** @brief Create an outcome-only result. @param outcome Stable outcome.
   * @return Owned result without a value. */
  [[nodiscard]] static ProviderResult without_value(ProviderOutcome outcome) noexcept {
    return ProviderResult(outcome);
  }
  /** @brief Copy a complete result. @param other Source result. */
  ProviderResult(const ProviderResult& other) noexcept = default;
  /** Assignment is disabled to preserve returned views. */
  ProviderResult& operator=(const ProviderResult&) = delete;
  /** @return Stable operation outcome. */
  [[nodiscard]] ProviderOutcome outcome() const noexcept { return outcome_; }
  /** @return Owned value pointer, or nullptr when no value was returned. */
  [[nodiscard]] const T* value() const noexcept { return value_ ? &*value_ : nullptr; }
  /** @return true when an owned value is present. */
  [[nodiscard]] bool has_value() const noexcept { return value_.has_value(); }
  /** @return Stable diagnostic code associated with outcome(). */
  [[nodiscard]] std::string_view diagnostic_code() const noexcept {
    return provider_diagnostic_code(outcome_);
  }
  /** @return Stable diagnostic explanation associated with outcome(). */
  [[nodiscard]] std::string_view diagnostic_message() const noexcept {
    return provider_diagnostic_message(outcome_);
  }

 private:
  explicit ProviderResult(ProviderOutcome outcome) noexcept : outcome_(outcome) {}
  ProviderResult(ProviderOutcome outcome, const T& value) noexcept
      : outcome_(outcome), value_(value) {}
  ProviderOutcome outcome_; /**< Stable outcome. */
  std::optional<T> value_; /**< Optional owned value. */
};

/** Outcome-only provider operation result. */
class ProviderStatus final {
 public:
  /** @brief Construct an outcome status. @param outcome Stable outcome. */
  explicit constexpr ProviderStatus(ProviderOutcome outcome) noexcept : outcome_(outcome) {}
  /** @return Stable outcome. */
  [[nodiscard]] constexpr ProviderOutcome outcome() const noexcept { return outcome_; }
  /** @return Stable diagnostic code. */
  [[nodiscard]] std::string_view diagnostic_code() const noexcept {
    return provider_diagnostic_code(outcome_);
  }
  /** @return Stable diagnostic explanation. */
  [[nodiscard]] std::string_view diagnostic_message() const noexcept {
    return provider_diagnostic_message(outcome_);
  }

 private:
  ProviderOutcome outcome_; /**< Stable operation outcome. */
};

/**
 * @brief Non-authoritative provider-owned route token returned to composition.
 * @ownership Stores only one bounded provider-local generation value.
 * @lifetime The token is an owned value and retains no provider resource.
 * @thread_safety Concurrent const reads are safe.
 * @failure create() rejects zero, so providers cannot report an invalid prepared generation.
 *
 * A token is not a public route handle and conveys no composition or lifecycle authority.
 */
class ProviderRouteToken final {
 public:
  /** @param generation Nonzero provider-local route generation.
   * @return A valid token, or no value when generation is zero. */
  [[nodiscard]] static std::optional<ProviderRouteToken> create(
      std::uint64_t generation) noexcept;
  /** @return Nonzero provider-local route generation. */
  [[nodiscard]] std::uint64_t generation() const noexcept { return generation_; }
  /** @return true only when both provider-local generations are equal. */
  friend bool operator==(const ProviderRouteToken& left,
                         const ProviderRouteToken& right) = default;

 private:
  explicit ProviderRouteToken(std::uint64_t generation) noexcept : generation_(generation) {}
  std::uint64_t generation_; /**< Nonzero provider-local route generation. */
};

/**
 * @brief Bounded non-authoritative provider state returned to composition.
 * @ownership Owns its provider-local token, state, and finite queue counters.
 * @lifetime The value exposes no provider storage and survives later provider operations.
 * @thread_safety Concurrent const reads are safe.
 * @failure create() rejects zero capacity and queued counts greater than capacity.
 */
class ProviderRouteStateValue final {
 public:
  /**
   * @param token Exact provider-local route token.
   * @param state Provider-owned route lifecycle state.
   * @param queued_items Number of currently retained items.
   * @param queue_capacity Fixed configured queue capacity.
   * @return Valid bounded state, or no value for inconsistent queue bounds.
   */
  [[nodiscard]] static std::optional<ProviderRouteStateValue> create(
      const ProviderRouteToken& token, ProviderRouteState state,
      std::size_t queued_items, std::size_t queue_capacity) noexcept;
  /** @return Exact provider-local route token. */
  [[nodiscard]] const ProviderRouteToken& token() const noexcept { return token_; }
  /** @return Provider-owned route state. */
  [[nodiscard]] ProviderRouteState state() const noexcept { return state_; }
  /** @return Number of retained items. */
  [[nodiscard]] std::size_t queued_items() const noexcept { return queued_items_; }
  /** @return Fixed configured queue capacity. */
  [[nodiscard]] std::size_t queue_capacity() const noexcept { return queue_capacity_; }

 private:
  ProviderRouteStateValue(const ProviderRouteToken& token, ProviderRouteState state,
                          std::size_t queued_items,
                          std::size_t queue_capacity) noexcept;
  ProviderRouteToken token_; /**< Exact provider-local route token. */
  ProviderRouteState state_; /**< Provider-owned lifecycle state. */
  std::size_t queued_items_; /**< Retained item count. */
  std::size_t queue_capacity_; /**< Fixed queue capacity. */
};

/** Internal owned binding passed only to an explicitly registered provider. */
class ProviderRouteBinding final {
 public:
  /** @brief Copy an exact route binding. @param other Valid source binding. */
  ProviderRouteBinding(const ProviderRouteBinding& other) noexcept = default;
  /** Assignment is disabled to preserve exact binding. */
  ProviderRouteBinding& operator=(const ProviderRouteBinding&) = delete;
  /** @return Exact validated logical route declaration. */
  [[nodiscard]] const RouteSpec& route_spec() const noexcept { return route_spec_; }
  /** @return Exact current lifecycle route handle. */
  [[nodiscard]] const RouteHandle& route_handle() const noexcept { return route_handle_; }
  /** @return Exact current source endpoint handle. */
  [[nodiscard]] const EndpointHandle& source_handle() const noexcept { return source_handle_; }
  /** @return Exact current destination endpoint handle. */
  [[nodiscard]] const EndpointHandle& destination_handle() const noexcept {
    return destination_handle_;
  }
  /** @return Exact issuing composition identity. */
  [[nodiscard]] std::uint64_t composition_instance_id() const noexcept {
    return composition_instance_id_;
  }
  /** @return Exact provider registry generation. */
  [[nodiscard]] std::uint64_t registration_generation() const noexcept {
    return registration_generation_;
  }
  /** @return Owned exact provider contract version. */
  [[nodiscard]] const SemanticVersion& provider_contract_version() const noexcept {
    return provider_contract_version_;
  }
  /** @return Bound interaction family. */
  [[nodiscard]] InteractionKind interaction_kind() const noexcept { return interaction_kind_; }
  /** @return Bound delivery capability. */
  [[nodiscard]] DeliveryCapability delivery() const noexcept { return delivery_; }
  /** @return Bound ordering capability. */
  [[nodiscard]] OrderingCapability ordering() const noexcept { return ordering_; }
  /** @return Bound per-route payload limit. */
  [[nodiscard]] std::size_t maximum_payload_bytes() const noexcept {
    return maximum_payload_bytes_;
  }
  /** @return Bound finite queue capacity. */
  [[nodiscard]] std::size_t queue_capacity() const noexcept { return queue_capacity_; }

 private:
  friend class ProviderComposition;
  ProviderRouteBinding(const RouteSpec& route_spec, const RouteHandle& route_handle,
                       const EndpointHandle& source_handle,
                       const EndpointHandle& destination_handle,
                       std::uint64_t composition_instance_id,
                       std::uint64_t registration_generation,
                       const ProviderRouteRequirements& requirements) noexcept;
  RouteSpec route_spec_; /**< Owned route and contract declaration. */
  RouteHandle route_handle_; /**< Exact lifecycle route handle. */
  EndpointHandle source_handle_; /**< Exact source endpoint handle. */
  EndpointHandle destination_handle_; /**< Exact destination endpoint handle. */
  std::uint64_t composition_instance_id_; /**< Issuing composition identity. */
  std::uint64_t registration_generation_; /**< Registry generation. */
  SemanticVersion provider_contract_version_; /**< Owned provider contract version. */
  InteractionKind interaction_kind_; /**< Bound interaction family. */
  DeliveryCapability delivery_; /**< Bound delivery claim. */
  OrderingCapability ordering_; /**< Bound ordering claim. */
  std::size_t maximum_payload_bytes_; /**< Bound item payload limit. */
  std::size_t queue_capacity_; /**< Bound reject-new queue capacity. */
};

/**
 * @brief Source-level interface for an explicitly linked provider instance.
 * @ownership Implementations own route resources; composition owns none of them.
 * @lifetime Implementations must outlive ProviderComposition and issued handles.
 * @thread_safety Every virtual operation must serialize shared mutation and return owned results.
 * @failure Operations must reject before mutation when exact binding validation fails.
 * Only ProviderComposition may invoke the private route-operation virtuals. Independent provider
 * implementations may override them, but external consumers cannot dispatch raw tokens.
 *
 * This interface is not a stable binary plugin ABI and performs no discovery or dynamic loading.
 */
class CommunicationProvider {
 public:
  /** Virtual destruction through the source-level interface. */
  virtual ~CommunicationProvider() = default;
  /** @return Immutable provider descriptor retained by the implementation. */
  [[nodiscard]] virtual const ProviderDescriptor& descriptor() const noexcept = 0;
  /**
   * @return true only when descriptor claims fit this implementation's hard storage and semantics.
   * @failure false makes explicit registration fail with invalid-descriptor before retention.
   */
  [[nodiscard]] virtual bool descriptor_compatible() const noexcept = 0;
  /** @return Opaque nonzero identity unique to this live provider object. */
  [[nodiscard]] virtual std::uint64_t instance_id() const noexcept = 0;

 private:
  friend class ProviderComposition;

  /** @param binding Exact validated route binding. @return Prepared token or stable outcome. */
  [[nodiscard]] virtual ProviderResult<ProviderRouteToken> prepare(
      const ProviderRouteBinding& binding) noexcept = 0;
  /** @param token Exact prepared provider-local token. @param lifecycle Bound lifecycle owner.
   * @return Status without changing lifecycle-controller state. */
  [[nodiscard]] virtual ProviderStatus activate(const ProviderRouteToken& token,
                                                const LifecycleController& lifecycle) noexcept = 0;
  /** @param token Exact active provider-local token. @param item Owned item copied on acceptance.
   * @param lifecycle Bound lifecycle owner. @return Submission status. */
  [[nodiscard]] virtual ProviderStatus submit(const ProviderRouteToken& token,
                                              const CommunicationItem& item,
                                              const LifecycleController& lifecycle) noexcept = 0;
  /** @param token Exact active or draining provider-local token.
   * @param lifecycle Bound lifecycle owner.
   * @return Oldest owned item or an explicit empty/failure outcome. */
  [[nodiscard]] virtual ProviderResult<CommunicationItem> receive(
      const ProviderRouteToken& token, const LifecycleController& lifecycle) noexcept = 0;
  /** @param token Exact active provider-local token. @param lifecycle Bound lifecycle owner.
   * @return Status without changing lifecycle-controller state. */
  [[nodiscard]] virtual ProviderStatus drain(const ProviderRouteToken& token,
                                             const LifecycleController& lifecycle) noexcept = 0;
  /** @param token Exact empty draining provider-local token.
   * @param lifecycle Bound lifecycle owner.
   * @return Resource-release status without changing lifecycle-controller state. */
  [[nodiscard]] virtual ProviderStatus close(const ProviderRouteToken& token,
                                             const LifecycleController& lifecycle) noexcept = 0;
  /** @param token Exact current provider-local token. @return Owned bounded provider state. */
  [[nodiscard]] virtual ProviderResult<ProviderRouteStateValue> state(
      const ProviderRouteToken& token) const noexcept = 0;
  /** @param token Exact current provider-local token. @param lifecycle Bound lifecycle owner.
   * @return Reconciled bounded state or interrupted-resource outcome. */
  [[nodiscard]] virtual ProviderResult<ProviderRouteStateValue> reconcile(
      const ProviderRouteToken& token, const LifecycleController& lifecycle) const noexcept = 0;
};

/** Validated fixed registry configuration. */
class ProviderRegistryConfiguration final {
 public:
  /** @brief Validate a nonzero registry capacity. @param capacity Requested slots.
   * @return Configuration or stable diagnostics. */
  [[nodiscard]] static Result<ProviderRegistryConfiguration> create(
      std::size_t capacity) noexcept;
  /** @brief Copy a configuration. @param other Source configuration. */
  ProviderRegistryConfiguration(const ProviderRegistryConfiguration& other) noexcept = default;
  /** Assignment is disabled. */
  ProviderRegistryConfiguration& operator=(const ProviderRegistryConfiguration&) = delete;
  /** @return Configured provider slots. */
  [[nodiscard]] std::size_t capacity() const noexcept { return capacity_; }

 private:
  friend class ProviderComposition;
  explicit ProviderRegistryConfiguration(std::size_t capacity) noexcept : capacity_(capacity) {}
  std::size_t capacity_; /**< Validated slot count. */
};

/**
 * @brief Fixed-capacity registry and explicit provider operation dispatcher.
 * @ownership Retains non-owning pointers to caller-owned source-linked providers.
 * @lifetime A provider and lifecycle controller must outlive their issued route handles.
 * @thread_safety Registration and lookup are serialized; provider calls occur after unlock.
 * @failure Rejected registration/preparation leaves registry, provider, lifecycle, and queues intact.
 */
class ProviderComposition final {
 public:
  /** Compile-time provider registry maximum. */
  static constexpr std::size_t kMaximumProviders = 8U;
  /** @brief Construct an empty registry. @param configuration Validated finite capacity. */
  explicit ProviderComposition(const ProviderRegistryConfiguration& configuration) noexcept;
  ProviderComposition(const ProviderComposition&) = delete;
  ProviderComposition& operator=(const ProviderComposition&) = delete;

  /** @return Opaque nonzero identity used to bind every issued provider-route handle. */
  [[nodiscard]] std::uint64_t instance_id() const noexcept { return instance_id_; }

  /** @param provider Explicit source-linked provider object. @return Owned registration or outcome. */
  [[nodiscard]] ProviderResult<ProviderRegistration> register_provider(
      CommunicationProvider& provider) noexcept;
  /**
   * @brief Validate all compatibility and lifecycle bounds before provider preparation.
   * @param lifecycle Exact lifecycle owner for all supplied handles.
   * @param route_spec Exact validated route and contract declaration.
   * @param route_handle Exact current validated route handle.
   * @param source_handle Exact current validated or active source endpoint handle.
   * @param destination_handle Exact current validated or active destination endpoint handle.
   * @param requirements Requested capabilities and finite limits.
   * @return Prepared provider-route handle or a stable outcome with no partial preparation.
   */
  [[nodiscard]] ProviderResult<ProviderRouteHandle> prepare_route(
      const LifecycleController& lifecycle, const RouteSpec& route_spec,
      const RouteHandle& route_handle, const EndpointHandle& source_handle,
      const EndpointHandle& destination_handle,
      const ProviderRouteRequirements& requirements) noexcept;
  /** @param handle Exact prepared handle. @param lifecycle Bound lifecycle owner. @return Status. */
  [[nodiscard]] ProviderStatus activate_route(const ProviderRouteHandle& handle,
                                              LifecycleController& lifecycle) noexcept;
  /** @param handle Exact active handle. @param item Item copied on acceptance.
   * @param lifecycle Bound lifecycle owner. @return Status. */
  [[nodiscard]] ProviderStatus submit(const ProviderRouteHandle& handle,
                                      const CommunicationItem& item,
                                      const LifecycleController& lifecycle) noexcept;
  /** @param handle Exact active or draining handle. @param lifecycle Bound lifecycle owner.
   * @return Oldest item or explicit empty/failure outcome. */
  [[nodiscard]] ProviderResult<CommunicationItem> receive(
      const ProviderRouteHandle& handle, const LifecycleController& lifecycle) noexcept;
  /** @param handle Exact active handle. @param lifecycle Bound lifecycle owner. @return Status. */
  [[nodiscard]] ProviderStatus drain_route(const ProviderRouteHandle& handle,
                                           LifecycleController& lifecycle) noexcept;
  /** @param handle Exact empty draining handle. @param lifecycle Bound lifecycle owner.
   * @return Close status. */
  [[nodiscard]] ProviderStatus close_route(const ProviderRouteHandle& handle,
                                           LifecycleController& lifecycle) noexcept;
  /** @param handle Exact current handle. @return Owned state snapshot. */
  [[nodiscard]] ProviderResult<ProviderRouteSnapshot> route_state(
      const ProviderRouteHandle& handle) const noexcept;
  /** @param handle Exact current handle. @param lifecycle Bound lifecycle owner.
   * @return Reconciled snapshot or interrupted-resource outcome. */
  [[nodiscard]] ProviderResult<ProviderRouteSnapshot> reconcile_route(
      const ProviderRouteHandle& handle, const LifecycleController& lifecycle) const noexcept;

 private:
  /** Registry slot for one caller-owned provider. */
  struct ProviderSlot final {
    /** @brief Bind one provider from values captured before locking.
     * @param provider_ref Caller-owned provider.
     * @param descriptor_value Retained descriptor copy.
     * @param generation_value Registry generation.
     * @param instance_id_value Captured provider object identity. */
    ProviderSlot(CommunicationProvider& provider_ref,
                 const ProviderDescriptor& descriptor_value,
                 std::uint64_t generation_value,
                 std::uint64_t instance_id_value) noexcept
        : provider(&provider_ref), descriptor(descriptor_value),
          generation(generation_value), instance_id(instance_id_value) {}
    CommunicationProvider* provider; /**< Non-owning provider pointer. */
    ProviderDescriptor descriptor; /**< Retained validated descriptor. */
    std::uint64_t generation; /**< Exact registry generation. */
    std::uint64_t instance_id; /**< Exact provider object identity. */
  };

  /** @brief Resolve exact provider under the registry lock. @param handle Route handle.
   * @return Provider pointer or null. */
  [[nodiscard]] CommunicationProvider* provider_for(
      const ProviderRouteHandle& handle) const noexcept;
  /** @brief Authenticate exact embedded lifecycle handles and states.
   * @param handle Composition-issued provider-route handle.
   * @param lifecycle Expected lifecycle owner.
   * @param route_state Required exact lifecycle route state.
   * @param endpoints_must_be_active Whether both authenticated endpoints must be active.
   * @return true only when route and both endpoints are exact and state-compatible. */
  [[nodiscard]] static bool lifecycle_matches(
      const ProviderRouteHandle& handle, const LifecycleController& lifecycle,
      LifecycleState route_state, bool endpoints_must_be_active) noexcept;

  std::uint64_t instance_id_; /**< Opaque composition identity. */
  std::size_t capacity_; /**< Configured provider slot prefix. */
  std::uint64_t next_generation_{1U}; /**< Next registry generation. */
  mutable std::mutex mutex_; /**< Serializes registry inspection/mutation. */
  std::array<std::optional<ProviderSlot>, kMaximumProviders> providers_{}; /**< Fixed slots. */
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_PROVIDER_HPP
