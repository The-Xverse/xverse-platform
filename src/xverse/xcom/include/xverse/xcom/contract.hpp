/**
 * @file contract.hpp
 * @brief Immutable domain-neutral communication contract values.
 * @ownership Contracts copy and own every identifier and version.
 * @lifetime Accessor views remain valid while the contract lives.
 * @thread_safety Valid contracts are immutable and support concurrent const access.
 * @failure create() returns stable diagnostics and never exposes a partial contract.
 */

#ifndef XVERSE_XCOM_CONTRACT_HPP
#define XVERSE_XCOM_CONTRACT_HPP

#include "xverse/xcom/result.hpp"
#include "xverse/xcom/value.hpp"

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

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_CONTRACT_HPP
