/**
 * @file activation_plan.hpp
 * @brief Bounded, immutable C++ decoder for the canonical X-COM activation-plan v1 artifact.
 * @ingroup xcom_xdl
 * @ownership Caller-owns-value for every decoded value; the decoder retains no global state and no
 * input buffer after return.
 * @lifetime Decoded values are valid for the activation-plan scope and immutable after decode.
 * @thread_safety The decoder is offline-single-threaded and reentrant over distinct inputs; decoded
 * values are immutable and may be shared read-only.
 * @failure The decoder performs no filesystem, network, or subprocess access, retains no global
 * state, and fails closed on malformed, out-of-shape, or over-bound input with a stable
 * `XCOM-DECODE-*` code and no decoded plan.
 *
 * The decoder is a pure function over caller-supplied plan bytes: it independently reproduces the
 * T017 canonical serialization rule and the domain-separated SHA-256 digest and verifies the plan
 * version and the capability/cross-reference closure before returning an immutable value.
 */

#ifndef XVERSE_XCOM_ACTIVATION_PLAN_HPP
#define XVERSE_XCOM_ACTIVATION_PLAN_HPP

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xverse::xcom::plan {

/// Bounded decode limits. Every member is finite and must be >= 1.
///
/// @brief Resource bounds applied to one decode call.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: read-only-static
/// (a value may be shared read-only). Failure semantics: a member < 1 makes the decode `failed`
/// with `XCOM-DECODE-UNKNOWN` before any parse; overflow policy is `fail-closed`.
struct DecodeLimits {
  std::size_t max_bytes = 5u * 1024u * 1024u;  ///< Maximum accepted document byte length.
  std::size_t max_depth = 100u;                ///< Maximum JSON nesting depth.
  std::size_t max_nodes = 100'000u;            ///< Maximum parsed JSON nodes.
  std::size_t max_string_length = 4096u;       ///< Maximum single string length.
  std::size_t max_contracts = 4096u;           ///< Maximum declared contracts.
  std::size_t max_endpoints = 4096u;           ///< Maximum declared endpoints.
  std::size_t max_routes = 4096u;              ///< Maximum declared routes.
  std::size_t max_providers = 256u;            ///< Maximum declared providers.
  std::size_t max_observation_points = 1024u;  ///< Maximum declared observation points.
  std::size_t max_clock_domains = 256u;        ///< Maximum declared clock domains.
  std::size_t max_diagnostics = 4096u;         ///< Maximum declared diagnostics.
  std::size_t max_activation_order = 8192u;    ///< Maximum declared activation-order entries.
  std::size_t max_provenance_resources = 1000u;  ///< Maximum declared provenance resources.
};

/// @brief Closed decode outcome vocabulary.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: read-only-static.
/// Failure semantics: every input is classified as exactly one of these values; an `accepted`
/// result alone carries a decoded plan.
enum class DecodeOutcome { accepted, rejected, failed };

/// @brief Stable decode diagnostic: code, affected target, bounded message.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
/// Failure semantics: `code` is from the closed `XCOM-DECODE-*` vocabulary and `target_id` is the
/// affected plan identifier or the fixed `xcom-plan` target; `message` never carries payload
/// content, credentials, private addresses, or an absolute host path.
struct DecodeError {
  std::string code;       ///< Closed `XCOM-DECODE-*` diagnostic code.
  std::string target_id;  ///< Affected plan identifier or the fixed `xcom-plan` target.
  std::string message;    ///< Bounded public-safe message; never carries payload or host data.
};

/// @brief Recorded or recomputed SHA-256 digest.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct PlanDigest {
  std::string algorithm;  ///< Digest algorithm identifier (`sha256`).
  std::string value;      ///< Lowercase-hex digest value.
};

/// @brief Declared XDL resource reference.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct ResourceRef {
  std::string api_version;             ///< Declared XDL API version.
  std::string kind;                    ///< Declared XDL resource kind.
  std::string ns;                      ///< Declared resource namespace.
  std::string name;                    ///< Declared resource name.
  std::optional<std::string> version;  ///< Optional declared resource version.
  PlanDigest source_digest;            ///< Recorded source digest of the resource.
};

/// @brief Plan generation provenance.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Provenance {
  std::string generated_at;          ///< Declared generation timestamp.
  PlanDigest graph_digest;           ///< Recorded graph digest.
  std::vector<ResourceRef> resources;  ///< Declared bounded resource set.
};

/// @brief Declared communication contract reference.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Contract {
  std::string contract_id;     ///< Declared contract identifier.
  std::string schema_id;       ///< Declared schema identifier.
  std::string schema_version;  ///< Declared schema version.
};

/// @brief Declared logical endpoint and role.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Endpoint {
  std::string endpoint_id;  ///< Declared endpoint identity.
  std::string role;         ///< Declared endpoint role.
};

/// @brief Declared logical route.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Route {
  std::string route_id;     ///< Declared route identity.
  std::string from;         ///< Declared source endpoint identity.
  std::string to;           ///< Declared destination endpoint identity.
  std::string contract_id;  ///< Declared bound contract identity.
};

/// @brief Selected provider and its declared capability set.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Provider {
  std::string provider_id;                  ///< Declared provider identity.
  std::vector<std::string> capabilities;    ///< Declared provided capability set.
  std::vector<std::string> required_capabilities;  ///< Declared required capability set.
};

/// @brief Declared bounded queue/ordering/reliability policy set.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Policies {
  std::string ordering;      ///< Declared ordering policy.
  std::string reliability;   ///< Declared reliability policy.
  std::string overflow;      ///< Declared overflow policy.
  std::string backpressure;  ///< Declared backpressure policy.
  std::int64_t deadline_ms = 0;  ///< Declared deadline in milliseconds.
  std::int64_t retry = 0;        ///< Declared retry count.
  std::int64_t queue_depth = 0;  ///< Declared bounded queue depth.
};

/// @brief Declared observation point.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct ObservationPoint {
  std::string tap_id;           ///< Declared observation tap identity.
  std::string route_id;         ///< Declared observed route identity.
  std::string payload_access;   ///< Declared payload-access policy.
  std::string validity_effect;  ///< Declared validity effect of observation.
};

/// @brief Declared stimulation actions and permit-policy references.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Stimulation {
  std::vector<std::string> actions;             ///< Declared allowed actions.
  std::vector<std::string> permit_policy_refs;  ///< Declared permit-policy references.
};

/// @brief Declared clock domain.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct ClockDomain {
  std::string clock_domain_id;  ///< Declared clock-domain identity.
  std::string source;           ///< Declared clock source.
};

/// @brief Declared deterministic diagnostic entry.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Diagnostic {
  std::string code;       ///< Declared diagnostic code.
  std::string severity;   ///< Declared diagnostic severity.
  std::string target_id;  ///< Affected plan identifier.
};

/// @brief Declared input-resolution states.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
/// Failure semantics: a plan declaring `activatable` with any state other than `resolved` is
/// rejected with `XCOM-DECODE-UNRESOLVED`.
struct InputResolution {
  std::string identity;    ///< Declared identity resolution state.
  std::string schema;      ///< Declared schema resolution state.
  std::string capability;  ///< Declared capability resolution state.
  std::string time;        ///< Declared time resolution state.
  std::string ownership;   ///< Declared ownership resolution state.
  std::string policy;      ///< Declared policy resolution state.
};

/// @brief Bounded, immutable decoded activation-plan value.
/// @details Ownership: caller-owns-value (the caller owns the returned value). Lifetime:
/// plan-scoped (valid for the activation-plan scope and immutable after decode). Thread-safety:
/// immutable-value (shareable read-only without synchronization; no internal lock, no global
/// state). Failure semantics: produced only on `accepted`; every string is bounded and every
/// collection capped by `DecodeLimits`.
struct ActivationPlan {
  std::string plan_version;                      ///< Declared plan schema version.
  PlanDigest digest;                             ///< Recorded canonical plan digest.
  std::string generator_task;                    ///< Task that generated the plan.
  std::string generator_version;                 ///< Generator version identity.
  Provenance provenance;                         ///< Plan generation provenance.
  std::vector<Contract> contracts;               ///< Declared bounded contracts.
  std::vector<Endpoint> endpoints;               ///< Declared bounded endpoints.
  std::vector<Route> routes;                     ///< Declared bounded routes.
  std::vector<Provider> providers;               ///< Declared bounded providers.
  Policies policies;                             ///< Declared bounded policy set.
  std::vector<ObservationPoint> observation_points;  ///< Declared bounded observation points.
  Stimulation stimulation;                       ///< Declared bounded stimulation set.
  std::vector<ClockDomain> clock_domains;        ///< Declared bounded clock domains.
  std::vector<std::string> activation_order;     ///< Declared bounded activation order.
  std::vector<Diagnostic> diagnostics;           ///< Declared bounded diagnostics.
  std::string status;                            ///< Declared plan status.
  InputResolution input_resolution;              ///< Declared input-resolution states.
};

/// @brief Result of a bounded decode: an outcome, an optional plan, and an optional error.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
/// Failure semantics: `plan` is engaged if and only if `outcome == accepted`; `error` is
/// populated if and only if `outcome != accepted`.
struct DecodeResult {
  DecodeOutcome outcome = DecodeOutcome::rejected;  ///< Closed decode outcome.
  std::optional<ActivationPlan> plan;               ///< Decoded plan when `accepted`.
  DecodeError error;                                ///< Bounded error when not `accepted`.
};

/// @brief Byte-producing result used by the canonicalization/digest helpers.
/// @details Ownership: caller-owns-value. Lifetime: process-scoped. Thread-safety:
/// offline-single-threaded. Failure semantics: `value` is empty and `error` populated unless
/// `outcome == accepted`.
struct BytesResult {
  DecodeOutcome outcome = DecodeOutcome::rejected;  ///< Closed producing outcome.
  std::string value;                                ///< Produced bytes when `accepted`.
  DecodeError error;                                ///< Bounded error when not `accepted`.
};

/// @brief True iff every `DecodeLimits` member is >= 1.
/// @details Ownership: caller-owns-value. Lifetime: process-scoped. Thread-safety:
/// offline-single-threaded. Failure semantics: never throws.
bool is_valid(const DecodeLimits& limits) noexcept;

/// @brief Lowercase-hex SHA-256 of the given bytes.
/// @details Ownership: caller-owns-value. Lifetime: process-scoped. Thread-safety:
/// offline-single-threaded. Failure semantics: never throws; the digest is deterministic.
std::string sha256_hex(std::string_view bytes);

/// @brief Canonical bytes of the digested region (the plan value minus the top-level `digest`).
/// @details Ownership: caller-owns-value. Lifetime: process-scoped. Thread-safety:
/// offline-single-threaded. Failure semantics: a malformed, shape-invalid, or over-bound document
/// returns a `rejected`/`failed` result with an empty value.
BytesResult canonical_plan_body_bytes(std::string_view document_json,
                                      const DecodeLimits& limits = {});

/// @brief Recomputed domain-separated SHA-256 hex of the plan body.
/// @details Ownership: caller-owns-value. Lifetime: process-scoped. Thread-safety:
/// offline-single-threaded. Failure semantics: a malformed, shape-invalid, or over-bound document
/// returns a `rejected`/`failed` result with an empty value.
BytesResult recompute_plan_digest(std::string_view document_json,
                                  const DecodeLimits& limits = {});

/// @brief Bounded decode with independent version/digest/capability verification.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety:
/// offline-single-threaded. Failure semantics: on any defect the result is `rejected` or `failed`
/// with a stable code and **no** decoded plan; a fully valid plan is `accepted`.
DecodeResult decode_activation_plan(std::string_view document_json,
                                    const DecodeLimits& limits = {});

}  // namespace xverse::xcom::plan

#endif  // XVERSE_XCOM_ACTIVATION_PLAN_HPP
