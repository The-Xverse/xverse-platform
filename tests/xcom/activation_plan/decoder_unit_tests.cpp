// T019 bounded activation-plan decoder: positive, digest, canonicalization, determinism, value,
// bound, and schema-drift tests. The committed T017 plan fixtures are read read-only.

#include "xverse/xcom/activation_plan.hpp"

#include <algorithm>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

namespace {

using nlohmann::json;
using xverse::xcom::plan::ActivationPlan;
using xverse::xcom::plan::DecodeLimits;
using xverse::xcom::plan::DecodeOutcome;
using xverse::xcom::plan::DecodeResult;
using xverse::xcom::plan::canonical_plan_body_bytes;
using xverse::xcom::plan::decode_activation_plan;
using xverse::xcom::plan::is_valid;
using xverse::xcom::plan::recompute_plan_digest;
using xverse::xcom::plan::sha256_hex;

std::string read_text(const std::string& path) {
  std::ifstream stream(path, std::ios::binary);
  std::ostringstream buffer;
  buffer << stream.rdbuf();
  return buffer.str();
}

std::string plan_fixture(const std::string& name) {
  return read_text(std::string(XCOM_ACTIVATION_PLAN_FIXTURE_DIR) + "/plan/valid/" + name);
}

std::string activatable() { return plan_fixture("plan-activatable.json"); }
std::string inspectable() { return plan_fixture("plan-inspectable.json"); }

/// Recompute and record the canonical digest so a synthetic mutation is digest-valid.
std::string seal(json plan) {
  const auto digest = recompute_plan_digest(plan.dump());
  plan["digest"]["value"] = digest.value;
  return plan.dump();
}

}  // namespace

TEST(Decode, PublicApiAndConstants) {
  // CHK-01, CHK-10: the bounded public API and its declared defaults are present.
  static_assert(std::is_same_v<decltype(DecodeOutcome::accepted), DecodeOutcome>);
  const DecodeLimits limits;
  EXPECT_EQ(limits.max_bytes, 5u * 1024u * 1024u);
  EXPECT_EQ(limits.max_depth, 100u);
  EXPECT_EQ(limits.max_nodes, 100'000u);
  EXPECT_EQ(limits.max_string_length, 4096u);
  EXPECT_EQ(limits.max_providers, 256u);
  EXPECT_TRUE(is_valid(limits));

  // The public API is reachable and returns a classified result for an empty document.
  const DecodeResult empty = decode_activation_plan("");
  EXPECT_NE(empty.outcome, DecodeOutcome::accepted);
  EXPECT_FALSE(empty.plan.has_value());
}

TEST(Decode, Sha256KnownAnswers) {
  // CHK-04, DET-04: FIPS 180-4 known answers, independent of the compiler's Python hashlib.
  EXPECT_EQ(sha256_hex(""), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  EXPECT_EQ(sha256_hex("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  EXPECT_EQ(sha256_hex(std::string_view("\x00\x01\x02", 3)),
            "ae4b3280e56e2faf83f414a6e3dabe9d5fbe18976544c05fed121accb85b53fc");
}

TEST(Decode, PositiveActivatableFixture) {
  // CHK-02, CHK-05: the committed activatable fixture decodes to an immutable value.
  const DecodeResult result = decode_activation_plan(activatable());
  ASSERT_EQ(result.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(result.plan.has_value());
  EXPECT_EQ(result.plan->plan_version, "1");
  EXPECT_EQ(result.plan->status, "activatable");
  EXPECT_EQ(result.plan->input_resolution.time, "resolved");
  EXPECT_TRUE(result.error.code.empty());
}

TEST(Decode, PositiveInspectableFixture) {
  // CHK-02, CHK-05: an inspectable plan with an explicit unresolved member is accepted.
  const DecodeResult result = decode_activation_plan(inspectable());
  ASSERT_EQ(result.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(result.plan.has_value());
  EXPECT_EQ(result.plan->status, "inspectable");
  EXPECT_EQ(result.plan->input_resolution.time, "unresolved");
}

TEST(Decode, InspectableUnresolvedCapabilityIsAccepted) {
  // CHK-05: a schema-valid, digest-sealed inspectable plan that declares a route with no selected
  // provider and `inputResolution.capability = "unresolved"` is accepted as a non-activatable value.
  // This is the artifact the accepted T018 producer emits when a graph has routes but no selected
  // provider (`_resolve`: routes and not providers -> capability unresolved, status inspectable).
  json plan = json::parse(inspectable());
  plan["providers"] = json::array();
  plan["inputResolution"]["capability"] = "unresolved";
  plan["status"] = "inspectable";

  const DecodeResult result = decode_activation_plan(seal(plan));
  ASSERT_EQ(result.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(result.plan.has_value());
  EXPECT_EQ(result.plan->status, "inspectable");
  EXPECT_EQ(result.plan->input_resolution.capability, "unresolved");
  EXPECT_TRUE(result.plan->providers.empty());
  EXPECT_TRUE(result.error.code.empty());
}

TEST(Decode, InspectableUnresolvedReferenceIsAccepted) {
  // CHK-05: an inspectable plan that honestly records an unresolved schema or identity reference
  // is accepted as a non-activatable value; only a plan claiming the state resolved is rejected.
  json schema_plan = json::parse(inspectable());
  schema_plan["routes"][0]["contractId"] = "contract-missing";
  schema_plan["inputResolution"]["schema"] = "unresolved";
  const DecodeResult schema_result = decode_activation_plan(seal(schema_plan));
  ASSERT_EQ(schema_result.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(schema_result.plan.has_value());
  EXPECT_EQ(schema_result.plan->input_resolution.schema, "unresolved");

  json identity_plan = json::parse(inspectable());
  identity_plan["routes"][0]["to"] = "endpoint-missing";
  identity_plan["inputResolution"]["identity"] = "unresolved";
  const DecodeResult identity_result = decode_activation_plan(seal(identity_plan));
  ASSERT_EQ(identity_result.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(identity_result.plan.has_value());
  EXPECT_EQ(identity_result.plan->input_resolution.identity, "unresolved");
}

TEST(Decode, DigestAgreesWithT017Fixture) {
  // CHK-03: the decoder's recomputed digest equals the value recorded by the T017 compiler.
  for (const std::string& document : {activatable(), inspectable()}) {
    const json fixture = json::parse(document);
    const std::string recorded = fixture.at("digest").at("value").get<std::string>();
    const auto recomputed = recompute_plan_digest(document);
    ASSERT_EQ(recomputed.outcome, DecodeOutcome::accepted);
    EXPECT_EQ(recomputed.value, recorded);
  }
}

TEST(Decode, DecodedFieldsMatchFixture) {
  // CHK-03: every decoded member equals the fixture.
  const json fixture = json::parse(activatable());
  const DecodeResult result = decode_activation_plan(activatable());
  ASSERT_TRUE(result.plan.has_value());
  const ActivationPlan& plan = *result.plan;

  ASSERT_EQ(plan.contracts.size(), fixture.at("contracts").size());
  EXPECT_EQ(plan.contracts[0].contract_id, "contract-ctrl");
  EXPECT_EQ(plan.contracts[0].schema_id, "xcom.control.v1");
  EXPECT_EQ(plan.contracts[0].schema_version, "1.0.0");

  ASSERT_EQ(plan.endpoints.size(), 2u);
  EXPECT_EQ(plan.endpoints[0].endpoint_id, "controller-a");
  EXPECT_EQ(plan.endpoints[0].role, "initiator");
  EXPECT_EQ(plan.endpoints[1].endpoint_id, "plant-a");
  EXPECT_EQ(plan.endpoints[1].role, "responder");

  ASSERT_EQ(plan.routes.size(), 1u);
  EXPECT_EQ(plan.routes[0].route_id, "route-ctrl");
  EXPECT_EQ(plan.routes[0].from, "controller-a");
  EXPECT_EQ(plan.routes[0].to, "plant-a");
  EXPECT_EQ(plan.routes[0].contract_id, "contract-ctrl");

  ASSERT_EQ(plan.providers.size(), 1u);
  EXPECT_EQ(plan.providers[0].provider_id, "loopback-provider");
  EXPECT_EQ(plan.providers[0].capabilities, std::vector<std::string>({"message"}));
  EXPECT_EQ(plan.providers[0].required_capabilities, std::vector<std::string>({"message"}));

  EXPECT_EQ(plan.policies.ordering, "fifo");
  EXPECT_EQ(plan.policies.reliability, "at-most-once");
  EXPECT_EQ(plan.policies.overflow, "reject");
  EXPECT_EQ(plan.policies.backpressure, "fail-closed");
  EXPECT_EQ(plan.policies.deadline_ms, 100);
  EXPECT_EQ(plan.policies.retry, 0);
  EXPECT_EQ(plan.policies.queue_depth, 64);

  ASSERT_EQ(plan.observation_points.size(), 1u);
  EXPECT_EQ(plan.observation_points[0].tap_id, "tap-ctrl");
  EXPECT_EQ(plan.observation_points[0].route_id, "route-ctrl");
  EXPECT_EQ(plan.observation_points[0].payload_access, "metadata-only");
  EXPECT_EQ(plan.observation_points[0].validity_effect, "none");

  EXPECT_EQ(plan.stimulation.actions, std::vector<std::string>({"inject-message"}));
  EXPECT_EQ(plan.stimulation.permit_policy_refs, std::vector<std::string>({"local-permit"}));

  ASSERT_EQ(plan.clock_domains.size(), 1u);
  EXPECT_EQ(plan.clock_domains[0].clock_domain_id, "clock-monotonic");
  EXPECT_EQ(plan.clock_domains[0].source, "monotonic");

  EXPECT_EQ(plan.activation_order, std::vector<std::string>({"controller-a", "plant-a"}));
  ASSERT_EQ(plan.diagnostics.size(), 1u);
  EXPECT_EQ(plan.diagnostics[0].code, "XCOM-PLAN-OK");
  EXPECT_EQ(plan.diagnostics[0].severity, "info");
  EXPECT_EQ(plan.diagnostics[0].target_id, "route-ctrl");

  EXPECT_EQ(plan.generator_task, "T018");
  EXPECT_EQ(plan.generator_version, "0.1.0");
  EXPECT_EQ(plan.provenance.generated_at, "1970-01-01T00:00:00Z");
  ASSERT_EQ(plan.provenance.resources.size(), 2u);
  EXPECT_EQ(plan.provenance.resources[0].name, "controller-a");
  EXPECT_EQ(plan.provenance.resources[1].name, "plant-a");
}

TEST(Decode, CanonicalBodyIsMemberSortedWhitespaceFree) {
  // CHK-08, DET-03: the canonical digested region is member-name ordered and whitespace-free.
  const auto body = canonical_plan_body_bytes(activatable());
  ASSERT_EQ(body.outcome, DecodeOutcome::accepted);
  // Lexicographically the first top-level member is activationOrder.
  ASSERT_GE(body.value.size(), 20u);
  EXPECT_EQ(body.value.rfind("{\"activationOrder\":", 0), 0u);
  EXPECT_EQ(body.value.back(), '}');
  for (char c : body.value) {
    EXPECT_NE(c, ' ');
    EXPECT_NE(c, '\n');
    EXPECT_NE(c, '\t');
  }
  EXPECT_EQ(body.value.find("\"digest\""), std::string::npos);
}

TEST(Decode, ReorderedDocumentSameDigestAndResult) {
  // DET-01, DET-02: a reordered/whitespace-varied but equivalent document yields one result.
  const std::string document = activatable();
  const json parsed = json::parse(document);
  const std::string reordered = parsed.dump(3);  // whitespace + sorted member order
  EXPECT_NE(reordered, document);

  const auto first = recompute_plan_digest(document);
  const auto second = recompute_plan_digest(reordered);
  ASSERT_EQ(first.outcome, DecodeOutcome::accepted);
  ASSERT_EQ(second.outcome, DecodeOutcome::accepted);
  EXPECT_EQ(first.value, second.value);

  const DecodeResult a = decode_activation_plan(document);
  const DecodeResult b = decode_activation_plan(reordered);
  ASSERT_EQ(a.outcome, DecodeOutcome::accepted);
  ASSERT_EQ(b.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(a.plan.has_value());
  ASSERT_TRUE(b.plan.has_value());
  EXPECT_EQ(a.plan->digest.value, b.plan->digest.value);
  EXPECT_EQ(a.plan->status, b.plan->status);

  // Repeated decodes of the same bytes are identical.
  const DecodeResult again = decode_activation_plan(document);
  EXPECT_EQ(again.outcome, a.outcome);
  EXPECT_EQ(again.plan->digest.value, a.plan->digest.value);
}

TEST(Decode, IntegralNumberVariantSharesCanonicalBytes) {
  // DET-03: an integral-number variant (100.0) canonicalizes to the single integer form.
  std::string variant = activatable();
  const std::string from = "\"deadlineMs\": 100";
  const std::size_t position = variant.find(from);
  ASSERT_NE(position, std::string::npos);
  variant.replace(position, from.size(), "\"deadlineMs\": 100.0");

  const auto original = canonical_plan_body_bytes(activatable());
  const auto mutated = canonical_plan_body_bytes(variant);
  ASSERT_EQ(mutated.outcome, DecodeOutcome::accepted);
  EXPECT_EQ(mutated.value, original.value);

  // The integral variant still decodes against the unchanged recorded digest.
  const DecodeResult result = decode_activation_plan(variant);
  ASSERT_EQ(result.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(result.plan.has_value());
  EXPECT_EQ(result.plan->policies.deadline_ms, 100);
}

TEST(Decode, ValueIsImmutableAndCopyable) {
  // CHK-10: the decoded value exposes no mutation surface and is copyable/movable.
  static_assert(std::is_copy_constructible_v<ActivationPlan>);
  static_assert(std::is_move_constructible_v<ActivationPlan>);
  static_assert(std::is_copy_assignable_v<ActivationPlan>);
  static_assert(std::is_move_assignable_v<ActivationPlan>);
  static_assert(!std::is_polymorphic_v<ActivationPlan>);
  static_assert(std::is_trivially_copyable_v<DecodeLimits>);

  const DecodeResult result = decode_activation_plan(activatable());
  ASSERT_TRUE(result.plan.has_value());
  ActivationPlan copy = *result.plan;
  ActivationPlan moved = std::move(copy);
  EXPECT_EQ(moved.status, "activatable");
  EXPECT_EQ(moved.contracts.size(), 1u);
}

TEST(Decode, LimitsValidationBounds) {
  // CHK-07, BND-05: an invalid limit fails closed before any parse.
  DecodeLimits limits;
  limits.max_depth = 0;
  EXPECT_FALSE(is_valid(limits));
  const DecodeResult result = decode_activation_plan(activatable(), limits);
  EXPECT_EQ(result.outcome, DecodeOutcome::failed);
  EXPECT_EQ(result.error.code, "XCOM-DECODE-UNKNOWN");
  EXPECT_FALSE(result.plan.has_value());
}

TEST(Decode, SchemaDriftGuard) {
  // CHK-06: the decoder's member/vocabulary table agrees with the committed plan schema.
  const json schema = json::parse(read_text(XCOM_ACTIVATION_PLAN_SCHEMA_PATH));

  std::vector<std::string> required;
  for (auto& name : schema.at("required")) {
    required.push_back(name.get<std::string>());
  }
  std::vector<std::string> expected = {"planVersion",        "digest",        "generator",
                                       "provenance",         "contracts",     "endpoints",
                                       "routes",             "providers",     "policies",
                                       "observationPoints",  "stimulation",   "clockDomains",
                                       "activationOrder",    "diagnostics",   "status",
                                       "inputResolution"};
  std::sort(required.begin(), required.end());
  std::sort(expected.begin(), expected.end());
  EXPECT_EQ(required, expected);
  EXPECT_EQ(schema.at("additionalProperties").get<bool>(), false);

  std::vector<std::string> status;
  for (auto& token : schema.at("properties").at("status").at("enum")) {
    status.push_back(token.get<std::string>());
  }
  EXPECT_EQ(status, std::vector<std::string>({"inspectable", "activatable"}));

  EXPECT_EQ(schema.at("$defs").at("provider").at("properties").at("capabilities").at("minItems").get<int>(), 1);
  EXPECT_EQ(schema.at("$defs").at("provenance").at("properties").at("resources").at("minItems").get<int>(), 1);
  EXPECT_EQ(schema.at("properties").at("activationOrder").at("minItems").get<int>(), 1);
  EXPECT_EQ(schema.at("$defs").at("inputResolution").at("required").size(), 6u);
  EXPECT_EQ(schema.at("$defs").at("policies").at("properties").at("deadlineMs").at("maximum").get<int>(),
            600000);

  // The closed digest sub-schema (`$defs/digest`) must agree with the decoder's digest table:
  // algorithm enum {sha256} and value pattern ^[0-9a-f]{64}$. The decoder enforces this for every
  // embedded digest, so a nested digest violation is bound to `XCOM-DECODE-SHAPE`.
  const json& digest_def = schema.at("$defs").at("digest");
  EXPECT_EQ(digest_def.at("additionalProperties").get<bool>(), false);
  std::vector<std::string> digest_algorithms;
  for (auto& token : digest_def.at("properties").at("algorithm").at("enum")) {
    digest_algorithms.push_back(token.get<std::string>());
  }
  EXPECT_EQ(digest_algorithms, std::vector<std::string>({"sha256"}));
  EXPECT_EQ(digest_def.at("properties").at("value").at("pattern").get<std::string>(),
            "^[0-9a-f]{64}$");

  json bad_graph_digest = json::parse(activatable());
  bad_graph_digest["provenance"]["graphDigest"]["algorithm"] = "md5";
  EXPECT_EQ(decode_activation_plan(bad_graph_digest.dump()).error.code, "XCOM-DECODE-SHAPE");
  json bad_source_digest = json::parse(activatable());
  bad_source_digest["provenance"]["resources"][0]["sourceDigest"]["value"] = "zzz";
  EXPECT_EQ(decode_activation_plan(bad_source_digest.dump()).error.code, "XCOM-DECODE-SHAPE");

  // The decoder rejects a missing required member and an unknown member, binding behaviour to the
  // same closed member set.
  json dropped = json::parse(activatable());
  dropped.erase("clockDomains");
  EXPECT_EQ(decode_activation_plan(dropped.dump()).error.code, "XCOM-DECODE-SHAPE");
  json unknown = json::parse(activatable());
  unknown["unknownField"] = 1;
  EXPECT_EQ(decode_activation_plan(unknown.dump()).error.code, "XCOM-DECODE-SHAPE");
}
