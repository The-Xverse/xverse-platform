// T020 cross-language regression suite (T20-REG-01..10, CHK-20-06/07).
//
// Pins the accepted behaviour of the derived-plan chain: the committed T017 fixtures decode, their
// recorded and recomputed digests equal the pinned golden values, the canonical digested bytes, the
// 16 required members, the DecodeLimits defaults, the closed decode-code vocabulary, and the
// SHA-256 known answers are unchanged. Anchored artifacts are read read-only.

#include "t020_support.hpp"

#include <algorithm>
#include <string>
#include <vector>

namespace {

using t20::DecodeOutcome;
using t20::json;
using xverse::xcom::plan::ActivationPlan;
using xverse::xcom::plan::DecodeLimits;
using xverse::xcom::plan::DecodeResult;
using xverse::xcom::plan::decode_activation_plan;
using xverse::xcom::plan::is_valid;
using xverse::xcom::plan::sha256_hex;

}  // namespace

TEST(T20Regression, ActivatableFixtureDecodesWithPinnedFields) {
  // T20-REG-01: the activatable fixture decodes `accepted` with every pinned field/count.
  const ActivationPlan plan = t20::expect_accepted(decode_activation_plan(t20::activatable()));
  EXPECT_EQ(plan.plan_version, "1");
  EXPECT_EQ(plan.status, "activatable");
  EXPECT_EQ(plan.input_resolution.time, "resolved");
  EXPECT_EQ(plan.generator_task, "T018");
  EXPECT_EQ(plan.generator_version, "0.1.0");
  EXPECT_EQ(plan.provenance.generated_at, "1970-01-01T00:00:00Z");

  EXPECT_EQ(plan.contracts.size(), 1u);
  EXPECT_EQ(plan.contracts[0].contract_id, "contract-ctrl");
  EXPECT_EQ(plan.contracts[0].schema_id, "xcom.control.v1");
  EXPECT_EQ(plan.contracts[0].schema_version, "1.0.0");
  EXPECT_EQ(plan.endpoints.size(), 2u);
  EXPECT_EQ(plan.endpoints[0].endpoint_id, "controller-a");
  EXPECT_EQ(plan.endpoints[0].role, "initiator");
  EXPECT_EQ(plan.endpoints[1].endpoint_id, "plant-a");
  EXPECT_EQ(plan.endpoints[1].role, "responder");
  EXPECT_EQ(plan.routes.size(), 1u);
  EXPECT_EQ(plan.routes[0].route_id, "route-ctrl");
  EXPECT_EQ(plan.routes[0].from, "controller-a");
  EXPECT_EQ(plan.routes[0].to, "plant-a");
  EXPECT_EQ(plan.routes[0].contract_id, "contract-ctrl");
  EXPECT_EQ(plan.providers.size(), 1u);
  EXPECT_EQ(plan.providers[0].provider_id, "loopback-provider");
  EXPECT_EQ(plan.policies.ordering, "fifo");
  EXPECT_EQ(plan.policies.reliability, "at-most-once");
  EXPECT_EQ(plan.policies.overflow, "reject");
  EXPECT_EQ(plan.policies.backpressure, "fail-closed");
  EXPECT_EQ(plan.policies.deadline_ms, 100);
  EXPECT_EQ(plan.policies.retry, 0);
  EXPECT_EQ(plan.policies.queue_depth, 64);
  EXPECT_EQ(plan.observation_points.size(), 1u);
  EXPECT_EQ(plan.observation_points[0].tap_id, "tap-ctrl");
  EXPECT_EQ(plan.observation_points[0].payload_access, "metadata-only");
  EXPECT_EQ(plan.clock_domains.size(), 1u);
  EXPECT_EQ(plan.clock_domains[0].clock_domain_id, "clock-monotonic");
  EXPECT_EQ(plan.activation_order.size(), 2u);
  EXPECT_EQ(plan.diagnostics.size(), 1u);
  EXPECT_EQ(plan.diagnostics[0].code, "XCOM-PLAN-OK");
  EXPECT_EQ(plan.diagnostics[0].severity, "info");
  EXPECT_EQ(plan.diagnostics[0].target_id, "route-ctrl");
  EXPECT_EQ(plan.provenance.resources.size(), 2u);
  EXPECT_EQ(plan.provenance.resources[0].name, "controller-a");
  EXPECT_EQ(plan.provenance.resources[1].name, "plant-a");
}

TEST(T20Regression, InspectableFixtureDecodesWithPinnedFields) {
  // T20-REG-02: the inspectable fixture decodes `accepted` with status inspectable and its pinned
  // unresolved member.
  const ActivationPlan plan = t20::expect_accepted(decode_activation_plan(t20::inspectable()));
  EXPECT_EQ(plan.plan_version, "1");
  EXPECT_EQ(plan.status, "inspectable");
  EXPECT_EQ(plan.input_resolution.time, "unresolved");
  EXPECT_EQ(plan.input_resolution.identity, "resolved");
  EXPECT_EQ(plan.contracts.size(), 1u);
  EXPECT_EQ(plan.endpoints.size(), 2u);
  EXPECT_EQ(plan.diagnostics.size(), 1u);
}

TEST(T20Regression, GoldenRecordedAndRecomputedDigests) {
  // T20-REG-03, CHK-20-06: each fixture's recorded digest equals the golden value and the decoder's
  // recomputation.
  const std::pair<std::string, std::string> cases[] = {
      {t20::activatable(), std::string(t20::kFixtureActivatableDigest)},
      {t20::inspectable(), std::string(t20::kFixtureInspectableDigest)}};
  for (const auto& [document, golden] : cases) {
    const json parsed = json::parse(document);
    EXPECT_EQ(parsed.at("digest").at("value").get<std::string>(), golden);
    EXPECT_EQ(t20::recompute_digest(document), golden);
  }
}

TEST(T20Regression, Sha256KnownAnswersUnchanged) {
  // T20-REG-04: FIPS 180-4 known answers are unchanged (independent of any Python hashlib).
  EXPECT_EQ(sha256_hex(""), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  EXPECT_EQ(sha256_hex("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  EXPECT_EQ(sha256_hex(std::string_view("\x00\x01\x02", 3)),
            "ae4b3280e56e2faf83f414a6e3dabe9d5fbe18976544c05fed121accb85b53fc");
}

TEST(T20Regression, DomainSeparatorRegression) {
  // T20-REG-05: a digest computed over the canonical body with the declared domain separator
  // matches; without the separator, or over a non-canonical body, it is rejected `XCOM-DECODE-DIGEST`.
  const std::string document = t20::activatable();
  const json parsed = json::parse(document);
  const std::string body = t20::canonical_body(document);
  std::string separator = "xverse.xcom.activation-plan.v1";
  separator.push_back('\0');
  EXPECT_EQ(sha256_hex(separator + body), parsed.at("digest").at("value").get<std::string>());

  json without_separator = parsed;
  without_separator["digest"]["value"] = sha256_hex(body);
  t20::expect_error(decode_activation_plan(without_separator.dump()), t20::kCodeDigest,
                    t20::kPlanTarget);

  json non_canonical = parsed;
  non_canonical["digest"]["value"] = sha256_hex(separator + json::parse(body).dump(2));
  t20::expect_error(decode_activation_plan(non_canonical.dump()), t20::kCodeDigest,
                    t20::kPlanTarget);
}

TEST(T20Regression, RequiredMemberSetAndClosedSchemaUnchanged) {
  // T20-REG-06: the 16 required members, `additionalProperties == false`, and the closed `$defs`
  // object set are unchanged, and the decoder binds to them.
  const json schema = t20::plan_schema();
  ASSERT_EQ(schema.at("required").size(), 16u);
  EXPECT_EQ(schema.at("additionalProperties").get<bool>(), false);
  for (auto& item : schema.at("$defs").items()) {
    const json& def = item.value();
    if (def.is_object() && def.contains("type") && def.at("type") == "object") {
      EXPECT_EQ(def.at("additionalProperties").get<bool>(), false) << item.key();
    }
  }

  json dropped = json::parse(t20::activatable());
  dropped.erase("status");
  t20::expect_error(decode_activation_plan(dropped.dump()), t20::kCodeShape, t20::kPlanTarget);
  json unknown = json::parse(t20::activatable());
  unknown["extraMember"] = 1;
  t20::expect_error(decode_activation_plan(unknown.dump()), t20::kCodeShape, t20::kPlanTarget);
}

TEST(T20Regression, FixtureBytesAreUnchanged) {
  // T20-REG-07: each committed fixture's file SHA-256 equals its golden value, proving the anchored
  // T017 fixtures were not mutated.
  EXPECT_EQ(sha256_hex(t20::activatable()), t20::kFixtureActivatableFileSha256);
  EXPECT_EQ(sha256_hex(t20::inspectable()), t20::kFixtureInspectableFileSha256);
}

TEST(T20Regression, GoldenCanonicalBodyHashIsStable) {
  // T20-REG-08: the canonical digested bytes hash equals the pinned golden value.
  EXPECT_EQ(sha256_hex(t20::canonical_body(t20::activatable())), t20::kFixtureActivatableBodySha256);
  EXPECT_EQ(sha256_hex(t20::canonical_body(t20::inspectable())), t20::kFixtureInspectableBodySha256);
}

TEST(T20Regression, DecodeLimitsDefaultsUnchanged) {
  // T20-REG-09: all 13 DecodeLimits defaults equal their declared values and `is_valid` is true.
  const DecodeLimits limits;
  EXPECT_EQ(limits.max_bytes, 5u * 1024u * 1024u);
  EXPECT_EQ(limits.max_depth, 100u);
  EXPECT_EQ(limits.max_nodes, 100'000u);
  EXPECT_EQ(limits.max_string_length, 4096u);
  EXPECT_EQ(limits.max_contracts, 4096u);
  EXPECT_EQ(limits.max_endpoints, 4096u);
  EXPECT_EQ(limits.max_routes, 4096u);
  EXPECT_EQ(limits.max_providers, 256u);
  EXPECT_EQ(limits.max_observation_points, 1024u);
  EXPECT_EQ(limits.max_clock_domains, 256u);
  EXPECT_EQ(limits.max_diagnostics, 4096u);
  EXPECT_EQ(limits.max_activation_order, 8192u);
  EXPECT_EQ(limits.max_provenance_resources, 1000u);
  EXPECT_TRUE(is_valid(limits));
}

TEST(T20Regression, DecodeCodeVocabularyIsClosed) {
  // T20-REG-10, CHK-20-07: a representative defect per code produces exactly the nine declared
  // codes; BOUND/UNKNOWN map to `failed` and every other code maps to `rejected`.
  std::vector<DecodeResult> results;

  results.push_back(decode_activation_plan("{"));

  json dropped = json::parse(t20::activatable());
  dropped.erase("clockDomains");
  results.push_back(decode_activation_plan(dropped.dump()));

  json version = json::parse(t20::activatable());
  version["planVersion"] = "2";
  results.push_back(decode_activation_plan(version.dump()));

  json digest = json::parse(t20::activatable());
  digest["digest"]["value"] = "NOT-HEX";
  results.push_back(decode_activation_plan(digest.dump()));

  json capability = json::parse(t20::activatable());
  capability["providers"] = json::array();
  results.push_back(decode_activation_plan(t20::seal(capability)));

  json reference = json::parse(t20::activatable());
  reference["routes"][0]["contractId"] = "contract-missing";
  results.push_back(decode_activation_plan(t20::seal(reference)));

  json unresolved = json::parse(t20::inspectable());
  unresolved["status"] = "activatable";
  results.push_back(decode_activation_plan(t20::seal(unresolved)));

  DecodeLimits bound;
  bound.max_bytes = 1u;
  results.push_back(decode_activation_plan(t20::activatable(), bound));

  DecodeLimits unknown;
  unknown.max_nodes = 0u;
  results.push_back(decode_activation_plan(t20::activatable(), unknown));

  std::vector<std::string> codes;
  for (const DecodeResult& result : results) {
    EXPECT_FALSE(result.plan.has_value());
    codes.push_back(result.error.code);
    if (result.error.code == t20::kCodeBound || result.error.code == t20::kCodeUnknown) {
      EXPECT_EQ(result.outcome, DecodeOutcome::failed) << result.error.code;
    } else {
      EXPECT_EQ(result.outcome, DecodeOutcome::rejected) << result.error.code;
    }
  }
  std::sort(codes.begin(), codes.end());
  std::vector<std::string> expected = {std::string(t20::kCodeBound),      std::string(t20::kCodeCapability),
                                       std::string(t20::kCodeDigest),     std::string(t20::kCodeInput),
                                       std::string(t20::kCodeReference),  std::string(t20::kCodeShape),
                                       std::string(t20::kCodeUnknown),    std::string(t20::kCodeUnresolved),
                                       std::string(t20::kCodeVersion)};
  std::sort(expected.begin(), expected.end());
  EXPECT_EQ(codes, expected);
}
