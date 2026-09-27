// Bounded, immutable C++ decoder for the canonical X-COM activation-plan v1 artifact.
//
// The decoder is a pure function over caller-supplied plan bytes: it performs no filesystem,
// network, or subprocess access, retains no global state, and fails closed on malformed,
// out-of-shape, or over-bound input. It independently reproduces the T017 canonical
// serialization rule and the domain-separated SHA-256 digest and verifies the plan version and
// the capability/cross-reference closure before returning an immutable value.

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
  std::size_t max_bytes = 5u * 1024u * 1024u;
  std::size_t max_depth = 100u;
  std::size_t max_nodes = 100'000u;
  std::size_t max_string_length = 4096u;
  std::size_t max_contracts = 4096u;
  std::size_t max_endpoints = 4096u;
  std::size_t max_routes = 4096u;
  std::size_t max_providers = 256u;
  std::size_t max_observation_points = 1024u;
  std::size_t max_clock_domains = 256u;
  std::size_t max_diagnostics = 4096u;
  std::size_t max_activation_order = 8192u;
  std::size_t max_provenance_resources = 1000u;
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
  std::string code;
  std::string target_id;
  std::string message;
};

/// @brief Recorded or recomputed SHA-256 digest.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct PlanDigest {
  std::string algorithm;
  std::string value;
};

/// @brief Declared XDL resource reference.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct ResourceRef {
  std::string api_version;
  std::string kind;
  std::string ns;
  std::string name;
  std::optional<std::string> version;
  PlanDigest source_digest;
};

/// @brief Plan generation provenance.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Provenance {
  std::string generated_at;
  PlanDigest graph_digest;
  std::vector<ResourceRef> resources;
};

/// @brief Declared communication contract reference.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Contract {
  std::string contract_id;
  std::string schema_id;
  std::string schema_version;
};

/// @brief Declared logical endpoint and role.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Endpoint {
  std::string endpoint_id;
  std::string role;
};

/// @brief Declared logical route.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Route {
  std::string route_id;
  std::string from;
  std::string to;
  std::string contract_id;
};

/// @brief Selected provider and its declared capability set.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Provider {
  std::string provider_id;
  std::vector<std::string> capabilities;
  std::vector<std::string> required_capabilities;
};

/// @brief Declared bounded queue/ordering/reliability policy set.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Policies {
  std::string ordering;
  std::string reliability;
  std::string overflow;
  std::string backpressure;
  std::int64_t deadline_ms = 0;
  std::int64_t retry = 0;
  std::int64_t queue_depth = 0;
};

/// @brief Declared observation point.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct ObservationPoint {
  std::string tap_id;
  std::string route_id;
  std::string payload_access;
  std::string validity_effect;
};

/// @brief Declared stimulation actions and permit-policy references.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Stimulation {
  std::vector<std::string> actions;
  std::vector<std::string> permit_policy_refs;
};

/// @brief Declared clock domain.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct ClockDomain {
  std::string clock_domain_id;
  std::string source;
};

/// @brief Declared deterministic diagnostic entry.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
struct Diagnostic {
  std::string code;
  std::string severity;
  std::string target_id;
};

/// @brief Declared input-resolution states.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
/// Failure semantics: a plan declaring `activatable` with any state other than `resolved` is
/// rejected with `XCOM-DECODE-UNRESOLVED`.
struct InputResolution {
  std::string identity;
  std::string schema;
  std::string capability;
  std::string time;
  std::string ownership;
  std::string policy;
};

/// @brief Bounded, immutable decoded activation-plan value.
/// @details Ownership: caller-owns-value (the caller owns the returned value). Lifetime:
/// plan-scoped (valid for the activation-plan scope and immutable after decode). Thread-safety:
/// immutable-value (shareable read-only without synchronization; no internal lock, no global
/// state). Failure semantics: produced only on `accepted`; every string is bounded and every
/// collection capped by `DecodeLimits`.
struct ActivationPlan {
  std::string plan_version;
  PlanDigest digest;
  std::string generator_task;
  std::string generator_version;
  Provenance provenance;
  std::vector<Contract> contracts;
  std::vector<Endpoint> endpoints;
  std::vector<Route> routes;
  std::vector<Provider> providers;
  Policies policies;
  std::vector<ObservationPoint> observation_points;
  Stimulation stimulation;
  std::vector<ClockDomain> clock_domains;
  std::vector<std::string> activation_order;
  std::vector<Diagnostic> diagnostics;
  std::string status;
  InputResolution input_resolution;
};

/// @brief Result of a bounded decode: an outcome, an optional plan, and an optional error.
/// @details Ownership: caller-owns-value. Lifetime: plan-scoped. Thread-safety: immutable-value.
/// Failure semantics: `plan` is engaged if and only if `outcome == accepted`; `error` is
/// populated if and only if `outcome != accepted`.
struct DecodeResult {
  DecodeOutcome outcome = DecodeOutcome::rejected;
  std::optional<ActivationPlan> plan;
  DecodeError error;
};

/// @brief Byte-producing result used by the canonicalization/digest helpers.
/// @details Ownership: caller-owns-value. Lifetime: process-scoped. Thread-safety:
/// offline-single-threaded. Failure semantics: `value` is empty and `error` populated unless
/// `outcome == accepted`.
struct BytesResult {
  DecodeOutcome outcome = DecodeOutcome::rejected;
  std::string value;
  DecodeError error;
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
