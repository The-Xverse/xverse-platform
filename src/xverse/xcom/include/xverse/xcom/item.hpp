/**
 * @file item.hpp
 * @brief Immutable bounded communication-item metadata and payload.
 * @ownership Items own all metadata and payload bytes.
 * @lifetime Accessor references and views remain valid while the item lives.
 * @thread_safety Valid items are immutable and support concurrent const access.
 * @failure create() returns stable diagnostics and never exposes a partial item.
 */

#ifndef XVERSE_XCOM_ITEM_HPP
#define XVERSE_XCOM_ITEM_HPP

#include "xverse/xcom/contract.hpp"

#include <cstddef>
#include <span>
#include <string_view>

namespace xverse::xcom {

/** Domain-neutral origin classifications preserved by an item. */
enum class OriginKind {
  /** Item originated from a logical component. */
  component,
  /** Item originated from an explicit validation tool. */
  validation_tool,
  /** Item originated from replayed data. */
  replay,
  /** Item originated at a provider boundary. */
  provider_generated,
};

/**
 * @brief Convert an origin kind to stable external text.
 * @param origin Origin classification.
 * @return Static-lifetime external text.
 */
[[nodiscard]] std::string_view to_string(OriginKind origin) noexcept;

/**
 * @brief Raw, call-scoped input for communication-item validation.
 * @ownership The factory copies all views and payload bytes; this input owns nothing.
 * @lifetime Views need only remain valid for the create() call.
 * @thread_safety Distinct inputs may be used concurrently.
 * @failure Missing, over-bound, or contract-inconsistent fields produce diagnostics.
 */
struct CommunicationItemInput final {
  /** Logical contract identity. */
  std::string_view contract_id;
  /** Canonical contract version. */
  std::string_view contract_version;
  /** Logical interface identity. */
  std::string_view interface_id;
  /** Logical endpoint identity. */
  std::string_view endpoint_id;
  /** Payload schema identity. */
  std::string_view schema_id;
  /** Canonical payload schema version. */
  std::string_view schema_version;
  /** Item interaction semantics. */
  InteractionKind interaction_kind;
  /** Explicit origin classification. */
  OriginKind origin;
  /** Signed timestamp magnitude. */
  Timestamp timestamp;
  /** Timestamp clock-domain identity. */
  std::string_view clock_domain;
  /** Correlation identity. */
  std::string_view correlation_id;
  /** Causation identity. */
  std::string_view causation_id;
  /** Route provenance identity without lifecycle semantics. */
  std::string_view route_id;
  /** Provider provenance identity without provider behavior. */
  std::string_view provider_id;
  /** Call-scoped payload bytes. */
  std::span<const std::byte> payload;
};

/**
 * @brief A validated immutable communication item with explicit bounded metadata.
 * @ownership Owns every identity, version, timestamp, origin, and payload byte.
 * @lifetime Accessor references and spans are valid while the item lives.
 * @thread_safety Concurrent const access is safe; no mutation is exposed.
 * @failure Only create() constructs a value; failure returns sorted diagnostics.
 */
class CommunicationItem final {
 public:
  /**
   * @brief Validate and own an item against an immutable communication contract.
   * @param input Complete item metadata and payload.
   * @param contract Contract whose logical/schema fields and kind must match.
   * @return A valid item or a deterministic non-empty diagnostic set.
   */
  [[nodiscard]] static Result<CommunicationItem> create(
      const CommunicationItemInput& input, const CommunicationContract& contract) noexcept;

  /**
   * @brief Copy a valid item without changing the source.
   * @param other Valid source item.
   * @failure This operation cannot fail.
   */
  CommunicationItem(const CommunicationItem& other) noexcept = default;

  /** Assignment is disabled so accessor references and spans cannot be invalidated. */
  CommunicationItem& operator=(const CommunicationItem&) = delete;

  /** @return The exact logical contract identity. */
  [[nodiscard]] const Identity& contract_id() const noexcept { return contract_id_; }
  /** @return The exact logical contract version. */
  [[nodiscard]] const SemanticVersion& contract_version() const noexcept { return contract_version_; }
  /** @return The exact logical interface identity. */
  [[nodiscard]] const Identity& interface_id() const noexcept { return interface_id_; }
  /** @return The logical endpoint identity, independent of realization. */
  [[nodiscard]] const Identity& endpoint_id() const noexcept { return endpoint_id_; }
  /** @return The exact schema identity. */
  [[nodiscard]] const Identity& schema_id() const noexcept { return schema_id_; }
  /** @return The exact schema version. */
  [[nodiscard]] const SemanticVersion& schema_version() const noexcept { return schema_version_; }
  /** @return The contract-compatible interaction kind. */
  [[nodiscard]] InteractionKind interaction_kind() const noexcept { return interaction_kind_; }
  /** @return The explicit item origin classification. */
  [[nodiscard]] OriginKind origin() const noexcept { return origin_; }
  /** @return The timestamp value without cross-clock inference. */
  [[nodiscard]] Timestamp timestamp() const noexcept { return timestamp_; }
  /** @return The explicit timestamp clock-domain identity. */
  [[nodiscard]] const Identity& clock_domain() const noexcept { return clock_domain_; }
  /** @return The item correlation identity. */
  [[nodiscard]] const Identity& correlation_id() const noexcept { return correlation_id_; }
  /** @return The item causation identity. */
  [[nodiscard]] const Identity& causation_id() const noexcept { return causation_id_; }
  /** @return The route provenance identity without lifecycle behavior. */
  [[nodiscard]] const Identity& route_id() const noexcept { return route_id_; }
  /** @return The provider provenance identity without provider behavior. */
  [[nodiscard]] const Identity& provider_id() const noexcept { return provider_id_; }
  /** @return The immutable value-owned bounded payload. */
  [[nodiscard]] const Payload& payload() const noexcept { return payload_; }

  /**
   * @brief Compare every immutable communication-item field.
   * @param left First item.
   * @param right Second item.
   * @return true when every field and payload byte is equal.
   */
  friend bool operator==(const CommunicationItem& left, const CommunicationItem& right) = default;

 private:
  /**
   * @brief Own all already validated item fields.
   * @param contract_id Logical contract identity.
   * @param contract_version Canonical contract version.
   * @param interface_id Logical interface identity.
   * @param endpoint_id Logical endpoint identity.
   * @param schema_id Payload schema identity.
   * @param schema_version Canonical schema version.
   * @param interaction_kind Validated interaction semantics.
   * @param origin Explicit origin classification.
   * @param timestamp Signed timestamp magnitude.
   * @param clock_domain Explicit clock-domain identity.
   * @param correlation_id Correlation identity.
   * @param causation_id Causation identity.
   * @param route_id Route provenance identity.
   * @param provider_id Provider provenance identity.
   * @param payload Owned bounded payload.
   * @failure This operation cannot fail.
   */
  CommunicationItem(const Identity& contract_id, const SemanticVersion& contract_version,
                    const Identity& interface_id, const Identity& endpoint_id,
                    const Identity& schema_id, const SemanticVersion& schema_version,
                    InteractionKind interaction_kind, OriginKind origin, Timestamp timestamp,
                    const Identity& clock_domain, const Identity& correlation_id,
                    const Identity& causation_id, const Identity& route_id,
                    const Identity& provider_id, const Payload& payload) noexcept
      : contract_id_(contract_id),
        contract_version_(contract_version),
        interface_id_(interface_id),
        endpoint_id_(endpoint_id),
        schema_id_(schema_id),
        schema_version_(schema_version),
        interaction_kind_(interaction_kind),
        origin_(origin),
        timestamp_(timestamp),
        clock_domain_(clock_domain),
        correlation_id_(correlation_id),
        causation_id_(causation_id),
        route_id_(route_id),
        provider_id_(provider_id),
        payload_(payload) {}

  Identity contract_id_;              /**< Owned logical contract identity. */
  SemanticVersion contract_version_;  /**< Owned canonical contract version. */
  Identity interface_id_;             /**< Owned logical interface identity. */
  Identity endpoint_id_;              /**< Owned logical endpoint identity. */
  Identity schema_id_;                /**< Owned payload schema identity. */
  SemanticVersion schema_version_;    /**< Owned canonical schema version. */
  InteractionKind interaction_kind_;  /**< Validated interaction semantics. */
  OriginKind origin_;                 /**< Explicit origin classification. */
  Timestamp timestamp_;               /**< Signed timestamp magnitude. */
  Identity clock_domain_;             /**< Owned clock-domain identity. */
  Identity correlation_id_;           /**< Owned correlation identity. */
  Identity causation_id_;             /**< Owned causation identity. */
  Identity route_id_;                 /**< Owned route provenance identity. */
  Identity provider_id_;              /**< Owned provider provenance identity. */
  Payload payload_;                   /**< Owned bounded payload bytes. */
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_ITEM_HPP
