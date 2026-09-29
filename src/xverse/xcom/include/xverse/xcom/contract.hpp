/**
 * @file contract.hpp
 * @ingroup xcom_core
 * @brief Immutable domain-neutral communication contract and flow-policy values.
 * @ownership Contracts copy and own every identifier and version.
 * @lifetime Accessor views remain valid while the contract lives.
 * @thread_safety Valid contracts are immutable and support concurrent const access.
 * @failure create() returns stable diagnostics and never exposes a partial contract.
 */

#ifndef XVERSE_XCOM_CONTRACT_HPP
#define XVERSE_XCOM_CONTRACT_HPP

#include "xverse/xcom/result.hpp"
#include "xverse/xcom/value.hpp"

#include <cstdint>
#include <string_view>

namespace xverse::xcom {

/** Distinct interaction semantics retained by the core value model. */
enum class InteractionKind {
  /** Signal or state update produced for a consumer. */
  signal_state_update,
  /** Message or event produced for a consumer. */
  message_event,
  /** Service request sent from requester to responder. */
  service_request,
  /** Service response sent from responder to requester. */
  service_response,
};

/** Explicit endpoint direction used to validate each interaction kind. */
enum class EndpointDirection {
  /** Produce signal, state, message, or event data. */
  produce,
  /** Consume signal, state, message, or event data. */
  consume,
  /** Request a service operation. */
  request,
  /** Respond to a service operation. */
  respond,
};

/**
 * @brief Declared ordering guarantee for a bounded flow.
 * @ownership Value enumeration; copies trivially and owns no resource.
 * @lifetime Static-lifetime vocabulary.
 * @thread_safety Immutable and safe to read concurrently.
 * @failure An out-of-vocabulary value is rejected by FlowPolicy::create().
 */
enum class OrderingPolicy {
  /** First-in-first-out delivery order. */
  fifo,
  /** Caller-declared priority delivery order. */
  priority,
  /** No ordering guarantee is declared. */
  unordered,
};

/**
 * @brief Declared reliability guarantee for a bounded flow.
 * @ownership Value enumeration; copies trivially and owns no resource.
 * @lifetime Static-lifetime vocabulary.
 * @thread_safety Immutable and safe to read concurrently.
 * @failure An out-of-vocabulary value is rejected by FlowPolicy::create().
 */
enum class ReliabilityPolicy {
  /** At most one delivery attempt is made. */
  at_most_once,
  /** At least one delivery attempt is guaranteed. */
  at_least_once,
  /** Exactly one observable delivery is guaranteed. */
  exactly_once,
  /** No delivery guarantee is declared. */
  best_effort,
};

/**
 * @brief Declared bounded-overflow behaviour for a bounded flow.
 * @ownership Value enumeration; copies trivially and owns no resource.
 * @lifetime Static-lifetime vocabulary.
 * @thread_safety Immutable and safe to read concurrently.
 * @failure An out-of-vocabulary value is rejected by FlowPolicy::create().
 */
enum class OverflowPolicy {
  /** Discard the oldest queued element. */
  drop_oldest,
  /** Discard the newest queued element. */
  drop_newest,
  /** Coalesce queued elements into one. */
  coalesce,
  /** Apply lossless backpressure instead of discarding. */
  lossless_backpressure,
  /** Reject the overflowing element. */
  reject,
  /** Fail closed and reject the whole operation. */
  fail_closed,
};

/**
 * @brief Convert an interaction kind to stable external text.
 * @param kind Interaction kind enumeration.
 * @return Static-lifetime external text.
 */
[[nodiscard]] std::string_view to_string(InteractionKind kind) noexcept;
/**
 * @brief Convert an endpoint direction to stable external text.
 * @param direction Endpoint direction enumeration.
 * @return Static-lifetime external text.
 */
[[nodiscard]] std::string_view to_string(EndpointDirection direction) noexcept;
/**
 * @brief Convert a declared ordering policy to stable external text.
 * @param policy Ordering policy enumeration.
 * @return Static-lifetime external text matching the accepted X-COM Profile vocabulary.
 */
[[nodiscard]] std::string_view to_string(OrderingPolicy policy) noexcept;
/**
 * @brief Convert a declared reliability policy to stable external text.
 * @param policy Reliability policy enumeration.
 * @return Static-lifetime external text matching the accepted X-COM Profile vocabulary.
 */
[[nodiscard]] std::string_view to_string(ReliabilityPolicy policy) noexcept;
/**
 * @brief Convert a declared overflow policy to stable external text.
 * @param policy Overflow policy enumeration.
 * @return Static-lifetime external text matching the accepted X-COM Profile vocabulary.
 */
[[nodiscard]] std::string_view to_string(OverflowPolicy policy) noexcept;

/**
 * @brief Raw, call-scoped input for communication-contract validation.
 * @ownership The factory copies every view; this input owns nothing.
 * @lifetime Views need only remain valid for the create() call.
 * @thread_safety Distinct inputs may be used concurrently.
 * @failure Missing, malformed, over-bound, or incompatible fields produce diagnostics.
 */
struct CommunicationContractInput final {
  /** Logical contract identity. */
  std::string_view contract_id;
  /** Canonical logical contract version. */
  std::string_view contract_version;
  /** Logical interface identity. */
  std::string_view interface_id;
  /** Payload schema identity. */
  std::string_view schema_id;
  /** Canonical payload schema version. */
  std::string_view schema_version;
  /** Interaction semantics. */
  InteractionKind interaction_kind;
  /** Logical source direction. */
  EndpointDirection source_direction;
  /** Logical target direction. */
  EndpointDirection target_direction;
};

/**
 * @brief An immutable logical communication contract independent of realization.
 * @ownership Owns all identities and versions by value.
 * @lifetime Accessor references are valid while the contract lives.
 * @thread_safety Concurrent const access is safe; no mutating operation exists.
 * @failure Only create() can construct a value; validation failure returns sorted diagnostics.
 */
class CommunicationContract final {
 public:
  /**
   * @brief Validate and own a logical communication contract.
   * @param input Candidate logical and schema metadata.
   * @return A valid contract or a deterministic non-empty diagnostic set.
   */
  [[nodiscard]] static Result<CommunicationContract> create(
      const CommunicationContractInput& input) noexcept;

  /**
   * @brief Copy a valid contract without changing the source.
   * @param other Valid source contract.
   * @failure This operation cannot fail.
   */
  CommunicationContract(const CommunicationContract& other) noexcept = default;

  /** Assignment is disabled so accessor references cannot be invalidated. */
  CommunicationContract& operator=(const CommunicationContract&) = delete;

  /** @return The logical contract identity. */
  [[nodiscard]] const Identity& contract_id() const noexcept { return contract_id_; }
  /** @return The logical contract version. */
  [[nodiscard]] const SemanticVersion& contract_version() const noexcept { return contract_version_; }
  /** @return The logical interface identity. */
  [[nodiscard]] const Identity& interface_id() const noexcept { return interface_id_; }
  /** @return The payload schema identity. */
  [[nodiscard]] const Identity& schema_id() const noexcept { return schema_id_; }
  /** @return The payload schema version. */
  [[nodiscard]] const SemanticVersion& schema_version() const noexcept { return schema_version_; }
  /** @return The interaction semantics retained by this contract. */
  [[nodiscard]] InteractionKind interaction_kind() const noexcept { return interaction_kind_; }
  /** @return The validated logical source direction. */
  [[nodiscard]] EndpointDirection source_direction() const noexcept { return source_direction_; }
  /** @return The validated logical target direction. */
  [[nodiscard]] EndpointDirection target_direction() const noexcept { return target_direction_; }

  /**
   * @brief Compare every immutable contract field.
   * @param left First contract.
   * @param right Second contract.
   * @return true when every field is equal.
   */
  friend bool operator==(const CommunicationContract& left,
                         const CommunicationContract& right) = default;

 private:
  /**
   * @brief Own already validated contract fields.
   * @param contract_id Logical contract identity.
   * @param contract_version Canonical contract version.
   * @param interface_id Logical interface identity.
   * @param schema_id Payload schema identity.
   * @param schema_version Canonical schema version.
   * @param interaction_kind Interaction semantics.
   * @param source_direction Validated source direction.
   * @param target_direction Validated target direction.
   * @failure This operation cannot fail.
   */
  CommunicationContract(const Identity& contract_id, const SemanticVersion& contract_version,
                        const Identity& interface_id, const Identity& schema_id,
                        const SemanticVersion& schema_version, InteractionKind interaction_kind,
                        EndpointDirection source_direction,
                        EndpointDirection target_direction) noexcept
      : contract_id_(contract_id),
        contract_version_(contract_version),
        interface_id_(interface_id),
        schema_id_(schema_id),
        schema_version_(schema_version),
        interaction_kind_(interaction_kind),
        source_direction_(source_direction),
        target_direction_(target_direction) {}

  Identity contract_id_;                 /**< Owned logical contract identity. */
  SemanticVersion contract_version_;     /**< Owned canonical contract version. */
  Identity interface_id_;                /**< Owned logical interface identity. */
  Identity schema_id_;                   /**< Owned payload schema identity. */
  SemanticVersion schema_version_;       /**< Owned canonical schema version. */
  InteractionKind interaction_kind_;     /**< Validated interaction semantics. */
  EndpointDirection source_direction_;   /**< Validated source direction. */
  EndpointDirection target_direction_;   /**< Validated target direction. */
};

/**
 * @brief Raw, call-scoped declaration input for flow-policy validation.
 * @ownership The aggregate owns nothing; the factory copies every field by value.
 * @lifetime All fields need only be valid for the FlowPolicy::create() call.
 * @thread_safety Distinct inputs may be used concurrently.
 * @failure An out-of-vocabulary enumeration or out-of-range number produces diagnostics.
 */
struct FlowPolicyInput final {
  /** Declared ordering guarantee. */
  OrderingPolicy ordering;
  /** Declared reliability guarantee. */
  ReliabilityPolicy reliability;
  /** Declared bounded-overflow behaviour. */
  OverflowPolicy overflow;
  /** Declared delivery deadline in milliseconds, 0 to 600000. */
  std::int64_t deadline_ms;
  /** Declared maximum retry count, 0 to 64. */
  std::int64_t retry;
  /** Declared finite queue depth, 1 to 65536. */
  std::int64_t queue_depth;
};

/**
 * @brief An immutable, bounded declared flow policy independent of any provider.
 * @ownership Owns every declared field by value; copies trivially and owns no resource.
 * @lifetime Invocation-scoped; accessors are valid while the policy lives.
 * @thread_safety Concurrent const access is safe; no mutating operation exists.
 * @failure Only create() can construct a value; an invalid declaration yields sorted
 * diagnostics and never a partial or default-substituted policy.
 */
class FlowPolicy final {
 public:
  /** Maximum accepted delivery deadline in milliseconds. */
  static constexpr std::int64_t kMaximumDeadlineMs = 600000;
  /** Maximum accepted retry count. */
  static constexpr std::int64_t kMaximumRetry = 64;
  /** Maximum accepted finite queue depth. */
  static constexpr std::int64_t kMaximumQueueDepth = 65536;

  /**
   * @brief Validate and own a declared flow policy.
   * @param input Candidate policy declaration.
   * @return A valid policy, or a deterministic non-empty diagnostic set.
   */
  [[nodiscard]] static Result<FlowPolicy> create(const FlowPolicyInput& input) noexcept;

  /**
   * @brief Copy a valid policy without changing the source.
   * @param other Valid source policy.
   * @failure This operation cannot fail.
   */
  FlowPolicy(const FlowPolicy& other) noexcept = default;

  /** Assignment is disabled so accessor values cannot be silently replaced. */
  FlowPolicy& operator=(const FlowPolicy&) = delete;

  /** @return The declared ordering guarantee. */
  [[nodiscard]] OrderingPolicy ordering() const noexcept { return ordering_; }
  /** @return The declared reliability guarantee. */
  [[nodiscard]] ReliabilityPolicy reliability() const noexcept { return reliability_; }
  /** @return The declared bounded-overflow behaviour. */
  [[nodiscard]] OverflowPolicy overflow() const noexcept { return overflow_; }
  /** @return The declared delivery deadline in milliseconds. */
  [[nodiscard]] std::int64_t deadline_ms() const noexcept { return deadline_ms_; }
  /** @return The declared maximum retry count. */
  [[nodiscard]] std::int64_t retry() const noexcept { return retry_; }
  /** @return The declared finite queue depth. */
  [[nodiscard]] std::int64_t queue_depth() const noexcept { return queue_depth_; }

  /**
   * @brief Compare every declared policy field.
   * @param left First policy.
   * @param right Second policy.
   * @return true only when every declared field is equal.
   */
  friend bool operator==(const FlowPolicy& left, const FlowPolicy& right) = default;

 private:
  /**
   * @brief Own already validated policy fields.
   * @param input Input validated by create().
   * @failure This operation cannot fail.
   */
  explicit FlowPolicy(const FlowPolicyInput& input) noexcept
      : ordering_(input.ordering),
        reliability_(input.reliability),
        overflow_(input.overflow),
        deadline_ms_(input.deadline_ms),
        retry_(input.retry),
        queue_depth_(input.queue_depth) {}

  OrderingPolicy ordering_;        /**< Declared ordering guarantee. */
  ReliabilityPolicy reliability_;  /**< Declared reliability guarantee. */
  OverflowPolicy overflow_;        /**< Declared bounded-overflow behaviour. */
  std::int64_t deadline_ms_;       /**< Declared delivery deadline in milliseconds. */
  std::int64_t retry_;             /**< Declared maximum retry count. */
  std::int64_t queue_depth_;       /**< Declared finite queue depth. */
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_CONTRACT_HPP
