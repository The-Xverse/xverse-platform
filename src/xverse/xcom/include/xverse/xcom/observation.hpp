/**
 * @file observation.hpp
 * @brief Bounded provider-neutral X-COM observation values and pull-based taps.
 * @ownership Records, filters, policies, handles, and snapshots own their values. ObservationHub
 * exclusively owns fixed tap and record slots; reservations own bounded item and tap claims;
 * SyntheticObservationSink retains no record storage.
 * @lifetime Returned records and snapshots are value copies. A tap handle is valid only for its
 * issuing hub, tap identifier, and current generation; it grants no provider or route authority.
 * @thread_safety Hub mutation and pull operations are serialized. No consumer callback exists or is
 * invoked under an X-COM lock. Immutable values support concurrent const access.
 * @failure Invalid, stale, foreign, closed, and capacity-exhausted operations return stable outcomes
 * without unrelated mutation. This boundary performs no I/O, process, environment, or network work.
 * @par Traceability
 * Implements XCOM-OBS-001 through XCOM-OBS-006, XCOM-OBS-008, and XCOM-OBS-009 (historical SESN-era
 * identifiers retained as evidence). T021 refines XCOM-SW-OBS-001 with the declared observation point,
 * declared route point, declared validity effect, and self-describing record; see
 * docs/engineering/xcom/t021/{requirements,detailed-design,unit-specifications,verification-plan}.md.
 * T022 refines XCOM-SW-OBS-003 with the bounded best-effort drop and coalesce modes, the explicit
 * lossless-validation mode, the applied declared validity effect, and the observable realized
 * validity status exposed by ObservationSnapshot::validity_state; see
 * docs/engineering/xcom/t022/{requirements,detailed-design,unit-specifications,verification-plan}.md.
 * Focused behavioral fixtures reside in tests/xcom/observation/core/unit_tests.cpp
 * (XCOM-OBS-002 through XCOM-OBS-006).
 */

#ifndef XVERSE_XCOM_OBSERVATION_HPP
#define XVERSE_XCOM_OBSERVATION_HPP

#include "xverse/xcom/item.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include <span>
#include <string_view>

namespace xverse::xcom {

/** Version implemented by this provider-neutral observation boundary. */
inline constexpr std::string_view kObservationContractVersion{"1.0.0"};
/** Maximum simultaneously attached taps owned by one observation hub. */
inline constexpr std::size_t kMaximumObservationTaps{8U};
/** Maximum pull records retained by each tap. */
inline constexpr std::size_t kMaximumObservationRecordsPerTap{16U};
/** Maximum payload prefix copied into one normalized observation record. */
inline constexpr std::size_t kMaximumObservedPayloadBytes{1024U};

/** Declared payload exposure mode; metadata-only is the safe default. */
enum class ObservationPayloadMode : std::uint8_t {
  /** Expose no payload bytes. */
  metadata_only,
  /** Expose at most the explicitly configured prefix length. */
  bounded_prefix,
  /** Expose no bytes and explicitly label the content as redacted. */
  redacted,
};

/** Declared finite-queue behavior for one tap. */
enum class ObservationOverflowPolicy : std::uint8_t {
  /** Retain earlier records and drop the new matching record. */
  drop_newest,
  /**
   * Replace the newest retained record having the same contract/version, interface, endpoint,
   * schema/version, interaction, origin, route, and provider key; otherwise drop the new record.
   */
  coalesce_latest,
  /** Reject matching normal submission before provider mutation when capacity is unavailable. */
  lossless_validation,
};

/**
 * @brief Declared validity effect for observations lost by bounded saturation.
 * @ownership Owns no resource; it is an immutable enumeration value.
 * @lifetime It is a value copied with the policy that declares it.
 * @thread_safety Concurrent const access is safe.
 * @failure Unknown values are rejected by ObservationTapSpec::create; the declaration selects the
 * realized ObservationValidityState raised on a matching loss and is never inferred or strengthened.
 */
enum class ObservationValidityEffect : std::uint8_t {
  /** Declared loss does not change experiment validity. */
  none,
  /** Declared loss degrades experiment validity. */
  degrade_on_loss,
  /** Declared loss invalidates experiment validity. */
  invalidate_on_loss,
};

/**
 * @brief Realized observation-validity status of one tap interval.
 * @ownership Owns no resource; it is an immutable enumeration value owned by the hub slot and copied
 * into an ObservationSnapshot.
 * @lifetime It persists for the current tap interval and is discarded by detach or slot recreation;
 * acknowledgement closes a `degraded` interval while `invalid` persists until detach.
 * @thread_safety Concurrent const access is safe; the hub raises it only under its mutex.
 * @failure It is raised only by a matching declared loss, is monotonic within an interval, and is
 * never lowered except by acknowledgement or detach/recreation.
 */
enum class ObservationValidityState : std::uint8_t {
  /** No declared loss has affected the current observation interval. */
  valid = 0U,
  /** A declared loss degraded experiment validity. */
  degraded = 1U,
  /** A declared loss invalidated experiment validity. */
  invalid = 2U,
};

/** Visibility and completeness of the payload view returned in one record. */
enum class PayloadViewState : std::uint8_t {
  /** No content was requested by the policy. */
  omitted,
  /** The complete source content fitted inside the declared prefix bound. */
  complete,
  /** Only a declared prefix of the source content is present. */
  truncated,
  /** Content was deliberately withheld by an explicit redaction policy. */
  redacted,
};

/** Schema interpretation status; this slice never claims decoder success. */
enum class PayloadSchemaState : std::uint8_t {
  /** Bytes were not schema decoded by this provider-neutral slice. */
  undecoded,
};

/** Provider outcome normalized without coupling the observation boundary to a provider implementation. */
enum class ObservationProviderOutcome : std::uint8_t {
  /** The route was not submitted because observation backpressure rejected it. */
  not_attempted,
  /** The provider reported normal acceptance. */
  accepted,
  /** The provider reported an explicit non-acceptance outcome. */
  rejected,
};

/** Stable result codes for every observation-boundary operation. */
enum class ObservationOutcome : std::uint8_t {
  /** The requested operation completed. */
  accepted,
  /** A required policy or event field was malformed or out of the fixed bound. */
  invalid_argument,
  /** All fixed tap slots are occupied. */
  tap_capacity_exhausted,
  /** A tap's finite record capacity is invalid or unavailable. */
  record_capacity_exhausted,
  /** A handle names a different hub, tap, generation, or a closed slot. */
  invalid_tap_handle,
  /** A reservation names another hub, has already completed, or no longer owns its exact claims. */
  invalid_reservation,
  /** The operation is a duplicate close against an already closed exact handle. */
  tap_closed,
  /** The exact tap has an in-flight publication claim and cannot yet be detached. */
  tap_busy,
  /** Lossless-validation capacity is unavailable; normal submission must not mutate a provider. */
  observation_backpressure,
  /** A valid pull found no retained record. */
  no_record,
  /** A synthetic pull sink was explicitly disconnected. */
  sink_disconnected,
};

/** @param outcome Observation outcome. @return Stable external outcome text. */
[[nodiscard]] std::string_view to_string(ObservationOutcome outcome) noexcept;

/**
 * @brief Report the accepted io.xverse.xcom validity-effect text for one declaration.
 * @param effect Declared validity effect.
 * @return Stable external text: "none", "degrade-on-loss", or "invalidate-on-loss".
 */
[[nodiscard]] std::string_view to_string(ObservationValidityEffect effect) noexcept;

/**
 * @brief Report the stable external text for one realized observation-validity status.
 * @param state Realized validity status.
 * @return Stable external text: "valid", "degraded", or "invalid".
 * @ownership Owns no resource; it returns a static-lifetime view.
 * @lifetime The returned view remains valid for the program lifetime.
 * @thread_safety It is pure, `noexcept`, and introduces no shared mutable state.
 * @failure An unknown value returns stable fallback text and never raises or mutates a tap.
 */
[[nodiscard]] std::string_view to_string(ObservationValidityState state) noexcept;

/** Immutable operation status without dynamically allocated diagnostic text. */
struct ObservationStatus final {
  /** Stable operation result. */
  ObservationOutcome outcome{ObservationOutcome::invalid_argument};
  /** @return true only for successful completion. */
  [[nodiscard]] bool succeeded() const noexcept { return outcome == ObservationOutcome::accepted; }
};

/**
 * @brief Exact opaque authority for one current observation tap generation.
 * @ownership Owns the opaque hub, tap, and generation values.
 * @lifetime It remains usable only until the exact tap is detached or its slot is recreated.
 * @thread_safety Concurrent const access is safe.
 * @failure Possession does not confer route, provider, name, filter, or address mutation authority.
 */
class ObservationTapHandle final {
 public:
  /** @brief Copy an exact opaque handle. @param other Issued source handle. */
  ObservationTapHandle(const ObservationTapHandle& other) noexcept = default;
  /** Assignment is disabled so a copied handle cannot be rebound. */
  ObservationTapHandle& operator=(const ObservationTapHandle&) = delete;
  /** @return Opaque issuing hub identity. */
  [[nodiscard]] std::uint64_t hub_instance_id() const noexcept { return hub_instance_id_; }
  /** @return Opaque fixed tap slot identity. */
  [[nodiscard]] std::uint64_t tap_id() const noexcept { return tap_id_; }
  /** @return Exact current slot generation. */
  [[nodiscard]] std::uint64_t generation() const noexcept { return generation_; }

 private:
  friend class ObservationHub;
  /** Construct a handle known to originate at this hub. */
  ObservationTapHandle(std::uint64_t hub_instance_id, std::uint64_t tap_id,
                       std::uint64_t generation) noexcept
      : hub_instance_id_(hub_instance_id), tap_id_(tap_id), generation_(generation) {}
  std::uint64_t hub_instance_id_;
  std::uint64_t tap_id_;
  std::uint64_t generation_;
};

/** Call-scoped, provider-neutral filter input. Empty fields mean no constraint. */
struct ObservationFilterInput final {
  /** Exact logical contract identity, if constrained. */
  std::string_view contract_id;
  /** Exact logical interface identity, if constrained. */
  std::string_view interface_id;
  /** Exact logical endpoint identity, if constrained. */
  std::string_view endpoint_id;
  /** Exact logical route identity, if constrained. */
  std::string_view route_id;
  /** Exact logical provider identity, if constrained. */
  std::string_view provider_id;
  /** Optional interaction-family constraint. */
  std::optional<InteractionKind> interaction_kind;
  /** Optional explicit origin constraint. */
  std::optional<OriginKind> origin{std::nullopt};
};

/**
 * @brief Immutable exact-field filter for normalized logical observation points.
 * @ownership Owns every nonempty identity constraint.
 * @lifetime Accessor views remain valid with this value.
 * @thread_safety Concurrent const calls are safe.
 * @failure create() rejects malformed nonempty identity constraints without retaining caller text.
 */
class ObservationFilter final {
 public:
  /** @brief Validate and own a filter. @param input Call-scoped constraints. @return Filter or empty. */
  [[nodiscard]] static std::optional<ObservationFilter> create(
      const ObservationFilterInput& input) noexcept;
  /** @brief Copy a filter. @param other Valid source filter. */
  ObservationFilter(const ObservationFilter& other) noexcept = default;
  /** Assignment is disabled to keep owned accessor views stable. */
  ObservationFilter& operator=(const ObservationFilter&) = delete;
  /** @brief Test an item against every declared constraint.
   * @param item Candidate item.
   * @return true when the item satisfies every declared constraint.
   */
  [[nodiscard]] bool matches(const CommunicationItem& item) const noexcept;
  /** @brief Return the declared contract constraint. @return Owned constraint, or no value. */
  [[nodiscard]] const std::optional<Identity>& contract_id() const noexcept { return contract_id_; }
  /** @brief Return the declared interface constraint. @return Owned constraint, or no value. */
  [[nodiscard]] const std::optional<Identity>& interface_id() const noexcept { return interface_id_; }
  /** @brief Return the declared endpoint constraint. @return Owned constraint, or no value. */
  [[nodiscard]] const std::optional<Identity>& endpoint_id() const noexcept { return endpoint_id_; }
  /**
   * @brief Return the declared logical route point.
   * @return Owned route constraint, or no value when the tap observes every route.
   */
  [[nodiscard]] const std::optional<Identity>& route_id() const noexcept { return route_id_; }
  /** @brief Return the declared provider constraint. @return Owned constraint, or no value. */
  [[nodiscard]] const std::optional<Identity>& provider_id() const noexcept { return provider_id_; }
  /** @brief Return the declared interaction-family constraint. @return Constraint, or no value. */
  [[nodiscard]] std::optional<InteractionKind> interaction_kind() const noexcept {
    return interaction_kind_;
  }
  /** @brief Return the declared origin constraint. @return Constraint, or no value. */
  [[nodiscard]] std::optional<OriginKind> origin() const noexcept { return origin_; }

 private:
  ObservationFilter(std::optional<Identity> contract_id, std::optional<Identity> interface_id,
                    std::optional<Identity> endpoint_id, std::optional<Identity> route_id,
                    std::optional<Identity> provider_id,
                    std::optional<InteractionKind> interaction_kind,
                    std::optional<OriginKind> origin) noexcept;
  std::optional<Identity> contract_id_;
  std::optional<Identity> interface_id_;
  std::optional<Identity> endpoint_id_;
  std::optional<Identity> route_id_;
  std::optional<Identity> provider_id_;
  std::optional<InteractionKind> interaction_kind_;
  std::optional<OriginKind> origin_;
};

/** Call-scoped policy used to attach one fixed-capacity observation tap. */
struct ObservationTapSpecInput final {
  /** Version of this declared observation contract. */
  std::string_view contract_version;
  /** Mandatory declared observation-point identity realized by this tap (1-128 bytes). */
  std::string_view tap_id;
  /** Provider-neutral logical filter. */
  ObservationFilterInput filter;
  /** Payload exposure policy. */
  ObservationPayloadMode payload_mode{ObservationPayloadMode::metadata_only};
  /** Maximum visible bytes for bounded_prefix; zero for metadata/redacted. */
  std::size_t maximum_payload_bytes{0U};
  /** Fixed retention capacity, from one through kMaximumObservationRecordsPerTap. */
  std::size_t record_capacity{0U};
  /** Declared saturation behavior. */
  ObservationOverflowPolicy overflow_policy{ObservationOverflowPolicy::drop_newest};
  /** Declared validity effect applied to the realized status on a matching loss. */
  ObservationValidityEffect validity_effect{ObservationValidityEffect::none};
};

/** Immutable validated policy for one attach operation. */
class ObservationTapSpec final {
 public:
  /**
   * @brief Validate and own a bounded tap policy.
   * @param input Call-scoped policy.
   * @return A validated immutable policy, or no value when the input is invalid or out of bounds.
   */
  [[nodiscard]] static std::optional<ObservationTapSpec> create(
      const ObservationTapSpecInput& input) noexcept;
  /** @brief Copy a policy. @param other Valid source policy. */
  ObservationTapSpec(const ObservationTapSpec& other) noexcept = default;
  /** Assignment is disabled to preserve accessor lifetimes. */
  ObservationTapSpec& operator=(const ObservationTapSpec&) = delete;
  /** @return Exact implemented observation-contract version. */
  [[nodiscard]] const SemanticVersion& contract_version() const noexcept { return contract_version_; }
  /**
   * @brief Return the declared observation point realized by this tap.
   * @return Owned declared observation-point identity.
   * @ownership The identity is owned by this policy.
   * @lifetime The returned reference is valid while this policy lives.
   * @thread_safety Concurrent const access is safe.
   * @failure It is correlation metadata only; it confers no tap or route authority.
   */
  [[nodiscard]] const Identity& declared_tap_id() const noexcept { return declared_tap_id_; }
  /**
   * @brief Return the declared logical route point this tap attaches to.
   * @return The filter's declared route constraint, or no value when every route is observed.
   * @ownership The identity is owned by this policy's filter.
   * @lifetime The returned reference is valid while this policy lives.
   * @thread_safety Concurrent const access is safe.
   * @failure The filter is the single source of truth, so a contradictory attachment is impossible.
   */
  [[nodiscard]] const std::optional<Identity>& declared_route_point() const noexcept {
    return filter_.route_id();
  }
  /**
   * @brief Return the declared validity effect.
   * @return Declared effect applied to the realized ObservationValidityState on a matching loss.
   * @ownership Owned by this policy.
   * @lifetime The returned value is valid while this policy lives.
   * @thread_safety Concurrent const access is safe.
   * @failure It selects the realized status and is never inferred, defaulted, or strengthened.
   */
  [[nodiscard]] ObservationValidityEffect validity_effect() const noexcept { return validity_effect_; }
  /** @return Provider-neutral logical filter. */
  [[nodiscard]] const ObservationFilter& filter() const noexcept { return filter_; }
  /** @return Declared payload exposure mode. */
  [[nodiscard]] ObservationPayloadMode payload_mode() const noexcept { return payload_mode_; }
  /** @return Declared bounded-prefix byte limit. */
  [[nodiscard]] std::size_t maximum_payload_bytes() const noexcept { return maximum_payload_bytes_; }
  /** @return Fixed pull-record capacity. */
  [[nodiscard]] std::size_t record_capacity() const noexcept { return record_capacity_; }
  /** @return Declared saturation behavior. */
  [[nodiscard]] ObservationOverflowPolicy overflow_policy() const noexcept { return overflow_policy_; }

 private:
  ObservationTapSpec(const SemanticVersion& contract_version, const Identity& declared_tap_id,
                     const ObservationFilter& filter, ObservationPayloadMode payload_mode,
                     std::size_t maximum_payload_bytes, std::size_t record_capacity,
                     ObservationOverflowPolicy overflow_policy,
                     ObservationValidityEffect validity_effect) noexcept;
  SemanticVersion contract_version_;
  Identity declared_tap_id_;
  ObservationFilter filter_;
  ObservationPayloadMode payload_mode_;
  std::size_t maximum_payload_bytes_;
  std::size_t record_capacity_;
  ObservationOverflowPolicy overflow_policy_;
  ObservationValidityEffect validity_effect_;
};

/** Input metadata for normalizing one already-attempted logical observation event. */
struct ObservationEvent final {
  /** Immutable item whose metadata is normalized and whose payload is filtered by policy. */
  const CommunicationItem& item;
  /** Explicit observation timestamp, not compared with source time. */
  Timestamp observation_timestamp;
  /** Explicit observation clock-domain identity. */
  std::string_view observation_clock_domain;
  /** Sequence when the producer declares one; absent otherwise. */
  std::optional<std::uint64_t> sequence;
  /** Explicit provider result, never inferred by this boundary. */
  ObservationProviderOutcome provider_outcome;
};

/**
 * @brief Immutable retention-time queue-counter projection stamped into one record.
 * @ownership Owns only fixed counter values.
 * @lifetime It is copied with the record that carries it.
 * @thread_safety Concurrent const access is safe.
 * @failure It is a projection at the moment of retention; it is not a durable log.
 */
struct ObservationRecordCounters final {
  /** Records retained in the fixed queue when this record was retained. */
  std::size_t queued{0U};
  /** Records accepted into the tap queue when this record was retained. */
  std::uint64_t accepted{0U};
  /** Records dropped by drop-newest when this record was retained. */
  std::uint64_t dropped{0U};
  /** Records coalesced when this record was retained. */
  std::uint64_t coalesced{0U};
};

/**
 * @brief Immutable normalized, owned pull record with policy-bounded payload visibility.
 * @ownership Owns every copied item identity, source/observation timestamp, outcome, and visible byte.
 * @lifetime Accessors remain valid while this owned record lives.
 * @thread_safety Concurrent const access is safe.
 * @failure Records are made only by ObservationHub after a validated event and matching policy.
 */
class ObservationRecord final {
 public:
  /** @return Exact logical contract identity. */
  [[nodiscard]] const Identity& contract_id() const noexcept { return contract_id_; }
  /** @return Exact logical contract version. */
  [[nodiscard]] const SemanticVersion& contract_version() const noexcept { return contract_version_; }
  /** @return Exact logical interface identity. */
  [[nodiscard]] const Identity& interface_id() const noexcept { return interface_id_; }
  /** @return Exact logical endpoint identity. */
  [[nodiscard]] const Identity& endpoint_id() const noexcept { return endpoint_id_; }
  /** @return Exact payload schema identity. */
  [[nodiscard]] const Identity& schema_id() const noexcept { return schema_id_; }
  /** @return Exact payload schema version. */
  [[nodiscard]] const SemanticVersion& schema_version() const noexcept { return schema_version_; }
  /** @return Preserved interaction semantics. */
  [[nodiscard]] InteractionKind interaction_kind() const noexcept { return interaction_kind_; }
  /** @return Preserved explicit origin. */
  [[nodiscard]] OriginKind origin() const noexcept { return origin_; }
  /** @return Source timestamp, without cross-clock comparison. */
  [[nodiscard]] Timestamp source_timestamp() const noexcept { return source_timestamp_; }
  /** @return Source clock-domain identity. */
  [[nodiscard]] const Identity& source_clock_domain() const noexcept { return source_clock_domain_; }
  /** @return Observation timestamp, without cross-clock comparison. */
  [[nodiscard]] Timestamp observation_timestamp() const noexcept { return observation_timestamp_; }
  /** @return Observation clock-domain identity. */
  [[nodiscard]] const Identity& observation_clock_domain() const noexcept { return observation_clock_domain_; }
  /** @return Optional producer sequence. */
  [[nodiscard]] const std::optional<std::uint64_t>& sequence() const noexcept { return sequence_; }
  /** @return Correlation identity. */
  [[nodiscard]] const Identity& correlation_id() const noexcept { return correlation_id_; }
  /** @return Causation identity. */
  [[nodiscard]] const Identity& causation_id() const noexcept { return causation_id_; }
  /** @return Logical route identity. */
  [[nodiscard]] const Identity& route_id() const noexcept { return route_id_; }
  /** @return Logical provider identity. */
  [[nodiscard]] const Identity& provider_id() const noexcept { return provider_id_; }
  /** @return Complete source payload byte count, even when content is withheld. */
  [[nodiscard]] std::size_t source_payload_size() const noexcept { return source_payload_size_; }
  /** @return Explicit provider outcome. */
  [[nodiscard]] ObservationProviderOutcome provider_outcome() const noexcept { return provider_outcome_; }
  /** @return Visible payload state. */
  [[nodiscard]] PayloadViewState payload_view_state() const noexcept { return payload_view_state_; }
  /** @return Schema interpretation state, always undecoded in this slice. */
  [[nodiscard]] PayloadSchemaState payload_schema_state() const noexcept { return payload_schema_state_; }
  /** @return Bounded visible bytes; empty for metadata-only or redacted policy. */
  [[nodiscard]] std::span<const std::byte> payload_bytes() const noexcept {
    return {payload_bytes_.data(), payload_size_};
  }
  /**
   * @brief Return the declared observation point that produced this record.
   * @return Owned declared identity of the producing tap.
   * @ownership Owned by this record.
   * @lifetime The returned reference is valid while this record lives.
   * @thread_safety Concurrent const access is safe.
   * @failure It is stamped from the authenticated producing tap and cannot be forged.
   */
  [[nodiscard]] const Identity& tap_id() const noexcept { return tap_id_; }
  /**
   * @brief Return the retention-time queue-counter projection.
   * @return Owned counter values captured after the retention rule updated them.
   * @ownership Owned by this record.
   * @lifetime The returned reference is valid while this record lives.
   * @thread_safety Concurrent const access is safe.
   * @failure It is a snapshot projection, not a durable loss log.
   */
  [[nodiscard]] const ObservationRecordCounters& counters() const noexcept { return counters_; }

 private:
  friend class ObservationHub;
  ObservationRecord(const ObservationEvent& event, const Identity& observation_clock_domain,
                    ObservationPayloadMode mode, std::size_t maximum_payload_bytes,
                    const Identity& tap_id, const ObservationRecordCounters& counters) noexcept;
  Identity contract_id_;
  SemanticVersion contract_version_;
  Identity interface_id_;
  Identity endpoint_id_;
  Identity schema_id_;
  SemanticVersion schema_version_;
  InteractionKind interaction_kind_;
  OriginKind origin_;
  Timestamp source_timestamp_;
  Identity source_clock_domain_;
  Timestamp observation_timestamp_;
  Identity observation_clock_domain_;
  std::optional<std::uint64_t> sequence_;
  Identity correlation_id_;
  Identity causation_id_;
  Identity route_id_;
  Identity provider_id_;
  std::size_t source_payload_size_;
  ObservationProviderOutcome provider_outcome_;
  PayloadViewState payload_view_state_;
  PayloadSchemaState payload_schema_state_{PayloadSchemaState::undecoded};
  std::array<std::byte, kMaximumObservedPayloadBytes> payload_bytes_{};
  std::size_t payload_size_{0U};
  Identity tap_id_;
  ObservationRecordCounters counters_;
};

/** Immutable exact counter snapshot returned by a tap inspection. */
struct ObservationSnapshot final {
  /** Exact current handle authority. */
  ObservationTapHandle handle;
  /** Records retained in the fixed queue. */
  std::size_t queued{0U};
  /** Records accepted into the tap queue. */
  std::uint64_t accepted{0U};
  /** New matching records dropped by drop-newest. */
  std::uint64_t dropped{0U};
  /** New records that replaced the newest retained record with the same logical key. */
  std::uint64_t coalesced{0U};
  /** Number of lossless reservation rejections since acknowledgement. */
  std::uint64_t backpressure_rejections{0U};
  /**
   * Compatibility projection of the realized validity status: true while
   * validity_state is not valid, and false otherwise. It is set by a declared loss (always for a
   * lossless backpressure) and cleared by an exact acknowledgement of a `degraded` interval.
   */
  bool experiment_validity_degraded{false};
  /** Declared observation point realized by the authenticated tap. */
  Identity declared_tap_id;
  /** Declared validity effect of the authenticated tap. */
  ObservationValidityEffect validity_effect{ObservationValidityEffect::none};
  /** Realized validity status raised by the declared effect on a matching loss. */
  ObservationValidityState validity_state{ObservationValidityState::valid};
};

/** Result of attach, carrying an exact handle only on success. */
struct ObservationAttachResult final {
  /** Stable attach outcome. */
  ObservationStatus status;
  /** Exact authority for the new tap when attach succeeded. */
  std::optional<ObservationTapHandle> handle;
};

/** Result of an exact pull, carrying an owned record only when available. */
struct ObservationPollResult final {
  /** Stable pull outcome. */
  ObservationStatus status;
  /** Value-owned normalized record when one was retained. */
  std::optional<ObservationRecord> record;
};

class ObservationHub;

/**
 * @brief Move-only exact authority for one in-flight provider publication.
 * @ownership Owns a bounded item copy and the exact tap generations claimed by reserve().
 * @lifetime The issuing hub must outlive the reservation. Destruction safely cancels an active claim.
 * @thread_safety A reservation is single-owner state and must not be accessed concurrently. Distinct
 * reservations may be committed or cancelled concurrently through their issuing hub.
 * @failure A moved-from or already completed reservation grants no authority.
 */
class ObservationReservation final {
 public:
  /** @brief Transfer exact reservation authority. @param other Active or inactive source. */
  ObservationReservation(ObservationReservation&& other) noexcept;
  /** Copying is prohibited because a reservation is single-use authority. */
  ObservationReservation(const ObservationReservation&) = delete;
  /** Assignment is prohibited so an outstanding claim cannot be overwritten. */
  ObservationReservation& operator=(ObservationReservation&&) = delete;
  /** Assignment from a copy is prohibited. */
  ObservationReservation& operator=(const ObservationReservation&) = delete;
  /** Cancel an active claim; the issuing hub must still be alive. */
  ~ObservationReservation();
  /** @return Opaque issuing hub identity. */
  [[nodiscard]] std::uint64_t hub_instance_id() const noexcept { return hub_instance_id_; }
  /** @return Opaque single-use reservation identity. */
  [[nodiscard]] std::uint64_t reservation_id() const noexcept { return reservation_id_; }
  /** @return true while this value still owns an unconsumed exact claim. */
  [[nodiscard]] bool active() const noexcept { return active_; }

 private:
  friend class ObservationHub;
  ObservationReservation(ObservationHub& hub, std::uint64_t hub_instance_id,
                         std::uint64_t reservation_id, const CommunicationItem& item,
                         const std::array<std::uint64_t, kMaximumObservationTaps>& tap_generations)
      noexcept;
  ObservationHub* hub_;
  std::uint64_t hub_instance_id_;
  std::uint64_t reservation_id_;
  CommunicationItem item_;
  std::array<std::uint64_t, kMaximumObservationTaps> tap_generations_;
  bool active_{true};
};

/** Result of an atomic pre-provider reservation attempt. */
struct ObservationReserveResult final {
  /** Stable reservation outcome. */
  ObservationStatus status;
  /** Exact single-use authority, present only when reserve() succeeded. */
  std::optional<ObservationReservation> reservation;
};

/**
 * @brief Fixed-capacity, pull-only observation owner for a local X-COM composition.
 * @ownership Exclusively owns fixed tap slots and fixed optional record slots; no allocation occurs.
 * @lifetime The hub must outlive all handles, reservations, and synthetic sinks constructed from it.
 * @thread_safety Every operation serializes shared slot mutation. Callers receive copies after unlock.
 * @failure Best-effort loss is counted without blocking. reserve() atomically claims lossless capacity
 * before provider mutation; provider code executes after reserve() returns and before commit()/cancel().
 */
class ObservationHub final {
 public:
  /** @brief Create an empty fixed-capacity observation hub. */
  ObservationHub() noexcept;
  /** Observation hubs are non-copyable because identity and mutex ownership are unique. */
  ObservationHub(const ObservationHub&) = delete;
  /** Observation hubs are non-assignable. */
  ObservationHub& operator=(const ObservationHub&) = delete;

  /**
   * @brief Attach one validated policy to a free fixed slot.
   * @param spec Valid immutable policy.
   * @return An exact current handle on success, or a stable failure status without mutation.
   */
  [[nodiscard]] ObservationAttachResult attach(const ObservationTapSpec& spec) noexcept;
  /**
   * @brief Atomically claim every currently matching tap before normal provider mutation.
   * @param item Candidate normal-route item copied into the returned bounded reservation.
   * @return Exact single-use authority, or observation_backpressure without a provider-visible change.
   * @note The caller must commit or cancel the returned reservation. Destruction cancels it safely.
   */
  [[nodiscard]] ObservationReserveResult reserve(const CommunicationItem& item) noexcept;
  /**
   * @brief Commit one exact reservation after provider dispatch and retain its normalized event.
   * @param reservation Exact active authority returned by this hub for event.item.
   * @param event Complete provider-outcome event for the exactly reserved item.
   * @return accepted after consuming the claim, or a stable error without consuming a valid claim.
   */
  [[nodiscard]] ObservationStatus commit(ObservationReservation&& reservation,
                                         const ObservationEvent& event) noexcept;
  /**
   * @brief Cancel one exact reservation when provider dispatch did not occur.
   * @param reservation Exact active authority returned by this hub.
   * @return accepted after releasing the claim, or invalid_reservation without unrelated mutation.
   */
  [[nodiscard]] ObservationStatus cancel(ObservationReservation&& reservation) noexcept;
  /**
   * @brief Pull one owned record using exact authority.
   * @param handle Exact current handle.
   * @return A value-owned record when queued, or the corresponding stable status otherwise.
   */
  [[nodiscard]] ObservationPollResult poll(const ObservationTapHandle& handle) noexcept;
  /**
   * @brief Inspect counters using exact authority.
   * @param handle Exact current handle.
   * @return A value snapshot for an authenticated handle, or no value for an invalid handle.
   */
  [[nodiscard]] std::optional<ObservationSnapshot> snapshot(
      const ObservationTapHandle& handle) const noexcept;
  /**
   * @brief Acknowledge and close the current observation-validity interval of one exact tap.
   * @param handle Exact current handle.
   * @return A stable status indicating whether the exact handle was acknowledged.
   * @note Acknowledgement resets backpressure_rejections to zero and returns a `degraded` realized
   * status to `valid`; an `invalid` status persists until detach or slot recreation. A foreign,
   * stale, or closed handle returns invalid_tap_handle and performs no interval reset.
   */
  [[nodiscard]] ObservationStatus acknowledge(const ObservationTapHandle& handle) noexcept;
  /**
   * @brief Close one exact current handle and discard only its retained records.
   * @param handle Exact current handle.
   * @return A stable status indicating whether the exact handle was closed.
   */
  [[nodiscard]] ObservationStatus detach(const ObservationTapHandle& handle) noexcept;

 private:
  friend class ObservationReservation;
  struct TapSlot final {
    std::optional<ObservationTapSpec> spec;
    std::uint64_t generation{0U};
    std::array<std::optional<ObservationRecord>, kMaximumObservationRecordsPerTap> records{};
    std::size_t head{0U};
    std::size_t size{0U};
    std::uint64_t accepted{0U};
    std::uint64_t dropped{0U};
    std::uint64_t coalesced{0U};
    std::uint64_t backpressure_rejections{0U};
    std::size_t reserved_lossless{0U};
    std::size_t active_claims{0U};
    ObservationValidityState realized_validity{ObservationValidityState::valid};
  };
  /**
   * @brief Resolve an exact current handle to its mutable tap slot.
   * @param handle Candidate authority.
   */
  [[nodiscard]] TapSlot* authenticate(const ObservationTapHandle& handle) noexcept;
  /**
   * @brief Resolve an exact current handle to its immutable tap slot.
   * @param handle Candidate authority.
   */
  [[nodiscard]] const TapSlot* authenticate(const ObservationTapHandle& handle) const noexcept;
  /** @brief Release claims owned by an active reservation while mutex_ is held. */
  void release_claims(ObservationReservation& reservation) noexcept;
  /** @brief Cancel from a reservation destructor; the hub lifetime precondition still applies. */
  void cancel_from_destructor(ObservationReservation& reservation) noexcept;
  /**
   * @brief Retain one normalized event in a validated tap slot.
   * @param slot Destination slot.
   * @param event Event.
   */
  [[nodiscard]] ObservationStatus retain(TapSlot& slot, const ObservationEvent& event) noexcept;
  /**
   * @brief Raise one tap slot's realized validity status for a matching declared loss.
   * @param slot Authenticated slot whose declared effect selects the target status.
   * @param required_loss true when the loss removes a required (lossless-validation) observation,
   * which realizes at least `degraded`.
   * @note It is called only while mutex_ is held; it is monotonic within the interval and never
   * lowers the realized status.
   */
  void raise_realized_validity(TapSlot& slot, bool required_loss) noexcept;
  /**
   * @brief Create an authority-bearing handle for one tap slot.
   * @param index Slot index.
   * @param generation Current generation.
   */
  [[nodiscard]] ObservationTapHandle make_handle(std::size_t index, std::uint64_t generation) const noexcept;
  static std::atomic<std::uint64_t> next_hub_instance_id_;
  const std::uint64_t hub_instance_id_;
  std::uint64_t next_reservation_id_{1U};
  mutable std::mutex mutex_;
  std::array<TapSlot, kMaximumObservationTaps> taps_{};
};

/**
 * @brief A pull-only synthetic consumer for focused tests and isolated local validation fixtures.
 * @ownership Retains only a non-owning hub pointer and a copied exact handle; pulled records remain owned
 * by their return value.
 * @lifetime The referenced hub must outlive this sink. disconnect() only disables this sink, never a tap.
 * @thread_safety Individual sink calls are serialized by the hub; concurrent connect/disconnect on one
 * sink is not supported.
 * @failure Disconnection produces sink_disconnected and does not block, mutate, or callback into a route.
 */
class SyntheticObservationSink final {
 public:
  /**
   * @brief Bind a synthetic sink to one exact tap authority.
   * @param hub Hub that owns the tap; it must outlive this sink.
   * @param handle Exact current tap authority copied by the sink.
   */
  SyntheticObservationSink(ObservationHub& hub, const ObservationTapHandle& handle) noexcept;
  /**
   * @brief Copy a synthetic sink without taking hub ownership.
   * @param other Valid sink whose hub reference and exact handle are copied.
   */
  SyntheticObservationSink(const SyntheticObservationSink& other) noexcept = default;
  /** Assignment is disabled to prevent accidental hub rebinding. */
  SyntheticObservationSink& operator=(const SyntheticObservationSink&) = delete;
  /** @brief Enable pulling after a local disconnect. @return Exact-handle status. */
  [[nodiscard]] ObservationStatus connect() noexcept;
  /** @brief Disable this consumer without detaching or mutating its tap. */
  void disconnect() noexcept { connected_ = false; }
  /**
   * @brief Pull one value-owned record when connected.
   * @return A pulled record or the stable disconnected/underlying hub status.
   */
  [[nodiscard]] ObservationPollResult pull() noexcept;
  /** @return true only when this local consumer is enabled. */
  [[nodiscard]] bool connected() const noexcept { return connected_; }

 private:
  ObservationHub* hub_;
  ObservationTapHandle handle_;
  bool connected_{true};
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_OBSERVATION_HPP
