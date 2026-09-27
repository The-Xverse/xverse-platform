// T020 ordering-equivalence and determinism suite (T20-ORD-01..08, T20-DET-01..04).
//
// Proves that equivalent normalized plan representations produce one canonical plan body and one
// domain-separated digest, that the declared per-collection ordering and duplicate-free
// activationOrder rules hold, that diagnostics are ordered deterministically, and that repeated
// decodes and integral-number/whitespace variants are identical. The committed T017 fixtures are
// read read-only.

#include "t020_support.hpp"

#include <algorithm>
#include <string>
#include <vector>

namespace {

using t20::DecodeOutcome;
using t20::json;
using xverse::xcom::plan::ActivationPlan;
using xverse::xcom::plan::DecodeResult;
using xverse::xcom::plan::decode_activation_plan;
using xverse::xcom::plan::sha256_hex;

}  // namespace

TEST(T20OrderingEquivalence, EquivalentSyntheticPlansShareCanonicalBytes) {
  // T20-ORD-01, CHK-20-01: member-reordered and whitespace-varied representations of one plan
  // yield one canonical byte string and one recomputed digest.
  const std::string original = t20::activatable();
  const json value = json::parse(original);
  const std::string reversed = t20::reverse_key_order_text(value);
  const std::string pretty = t20::with_whitespace(original);
  EXPECT_NE(reversed, original);
  EXPECT_NE(pretty, original);

  const std::string canonical = t20::canonical_body(original);
  EXPECT_EQ(t20::canonical_body(reversed), canonical);
  EXPECT_EQ(t20::canonical_body(pretty), canonical);
  EXPECT_EQ(t20::recompute_digest(reversed), t20::recompute_digest(original));
  EXPECT_EQ(t20::recompute_digest(pretty), t20::recompute_digest(original));
}

TEST(T20OrderingEquivalence, ReorderedFixtureSharesCanonicalBytesAndDigest) {
  // T20-ORD-02, CHK-20-01: a pretty re-serialization of a committed fixture yields the same
  // canonical bytes and digest as the original committed bytes.
  const std::string original = t20::activatable();
  const json fixture = json::parse(original);
  const std::string reserialized = fixture.dump(3);
  EXPECT_NE(reserialized, original);

  EXPECT_EQ(t20::canonical_body(reserialized), t20::canonical_body(original));
  EXPECT_EQ(t20::recompute_digest(reserialized), t20::recompute_digest(original));
  EXPECT_EQ(t20::recompute_digest(reserialized),
            fixture.at("digest").at("value").get<std::string>());
}

TEST(T20OrderingEquivalence, DeclaredCollectionOrderingIsEnforced) {
  // T20-ORD-03, CHK-20-02: each identity-bearing collection is asserted in declared key order; a
  // reversed or descending collection is rejected with the collection target and no decoded plan.
  const json fixture = json::parse(t20::activatable());
  ASSERT_EQ(fixture.at("endpoints").size(), 2u);
  EXPECT_LT(fixture.at("endpoints")[0].at("endpointId").get<std::string>(),
            fixture.at("endpoints")[1].at("endpointId").get<std::string>());
  ASSERT_EQ(fixture.at("provenance").at("resources").size(), 2u);
  EXPECT_LT(fixture.at("provenance").at("resources")[0].at("name").get<std::string>(),
            fixture.at("provenance").at("resources")[1].at("name").get<std::string>());

  json reversed_endpoints = fixture;
  std::reverse(reversed_endpoints["endpoints"].begin(), reversed_endpoints["endpoints"].end());
  t20::expect_error(decode_activation_plan(reversed_endpoints.dump()), t20::kCodeShape, "endpoints");

  json reversed_resources = fixture;
  std::reverse(reversed_resources["provenance"]["resources"].begin(),
               reversed_resources["provenance"]["resources"].end());
  t20::expect_error(decode_activation_plan(reversed_resources.dump()), t20::kCodeShape,
                    "provenance");

  json descending_contracts = fixture;
  json ahead = {{"contractId", "z-contract"}, {"schemaId", "xcom.control.v1"},
                {"schemaVersion", "1.0.0"}};
  json contracts = json::array();
  contracts.push_back(ahead);
  contracts.push_back(fixture.at("contracts")[0]);
  descending_contracts["contracts"] = contracts;
  t20::expect_error(decode_activation_plan(descending_contracts.dump()), t20::kCodeShape,
                    "contracts");
}

TEST(T20OrderingEquivalence, ActivationOrderIsDuplicateFree) {
  // T20-ORD-04, CHK-20-02: activationOrder is duplicate-free and non-empty, and its declared order
  // is preserved verbatim (it is an explicit order, not a sorted collection).
  json duplicate = json::parse(t20::activatable());
  duplicate["activationOrder"] = json::array({"controller-a", "controller-a"});
  t20::expect_error(decode_activation_plan(duplicate.dump()), t20::kCodeShape, "activationOrder");

  json empty = json::parse(t20::activatable());
  empty["activationOrder"] = json::array();
  t20::expect_error(decode_activation_plan(empty.dump()), t20::kCodeShape, "activationOrder");

  json reordered = json::parse(t20::activatable());
  reordered["activationOrder"] = json::array({"plant-a", "controller-a"});
  const ActivationPlan plan = t20::expect_accepted(decode_activation_plan(t20::seal(reordered)));
  const std::vector<std::string> expected{"plant-a", "controller-a"};
  EXPECT_EQ(plan.activation_order, expected);
}

TEST(T20OrderingEquivalence, DecodedDiagnosticsAreOrderedDeterministically) {
  // T20-ORD-05, CHK-20-02: the decoded diagnostics sequence equals the declared (code, targetId)
  // order and is identical across equivalent input representations.
  json plan = json::parse(t20::activatable());
  plan["diagnostics"] = json::array();
  plan["diagnostics"].push_back(
      {{"code", "XCOM-PLAN-AA"}, {"severity", "info"}, {"targetId", "route-ctrl"}});
  plan["diagnostics"].push_back(
      {{"code", "XCOM-PLAN-OK"}, {"severity", "info"}, {"targetId", "route-ctrl"}});
  const ActivationPlan decoded = t20::expect_accepted(decode_activation_plan(t20::seal(plan)));
  ASSERT_EQ(decoded.diagnostics.size(), 2u);
  EXPECT_EQ(decoded.diagnostics[0].code, "XCOM-PLAN-AA");
  EXPECT_EQ(decoded.diagnostics[1].code, "XCOM-PLAN-OK");

  json reversed = plan;
  std::reverse(reversed["diagnostics"].begin(), reversed["diagnostics"].end());
  t20::expect_error(decode_activation_plan(reversed.dump()), t20::kCodeShape, "diagnostics");

  const std::string equivalent = t20::reverse_key_order_text(json::parse(t20::seal(plan)));
  const ActivationPlan again = t20::expect_accepted(decode_activation_plan(equivalent));
  ASSERT_EQ(again.diagnostics.size(), 2u);
  EXPECT_EQ(again.diagnostics[0].code, decoded.diagnostics[0].code);
  EXPECT_EQ(again.diagnostics[0].target_id, decoded.diagnostics[0].target_id);
  EXPECT_EQ(again.diagnostics[1].code, decoded.diagnostics[1].code);
}

TEST(T20OrderingEquivalence, ReorderedDocumentSameOutcomeAndDecodedValue) {
  // T20-ORD-06, T20-DET-01, T20-DET-02: a reordered-but-equivalent document yields the identical
  // outcome, code, digest, and decoded fields, and a repeated decode is identical.
  const std::string original = t20::activatable();
  const std::string reordered = t20::reverse_key_order_text(json::parse(original));
  const ActivationPlan first = t20::expect_accepted(decode_activation_plan(original));
  const ActivationPlan second = t20::expect_accepted(decode_activation_plan(reordered));

  EXPECT_EQ(second.digest.value, first.digest.value);
  EXPECT_EQ(second.digest.algorithm, first.digest.algorithm);
  EXPECT_EQ(second.plan_version, first.plan_version);
  EXPECT_EQ(second.status, first.status);
  EXPECT_EQ(second.activation_order, first.activation_order);
  ASSERT_EQ(second.endpoints.size(), first.endpoints.size());
  ASSERT_EQ(second.provenance.resources.size(), first.provenance.resources.size());
  EXPECT_EQ(second.input_resolution.time, first.input_resolution.time);
  EXPECT_EQ(second.policies.deadline_ms, first.policies.deadline_ms);

  const DecodeResult repeat = decode_activation_plan(original);
  ASSERT_EQ(repeat.outcome, DecodeOutcome::accepted);
  ASSERT_TRUE(repeat.plan.has_value());
  EXPECT_EQ(repeat.plan->digest.value, first.digest.value);
}

TEST(T20OrderingEquivalence, IntegralNumberVariantSharesCanonicalBody) {
  // T20-ORD-07, T20-DET-03: replacing an integral token (100) with 100.0 yields the same canonical
  // body and digest and still decodes to the single integer value.
  const std::string from = "\"deadlineMs\": 100";
  std::string variant = t20::activatable();
  const std::size_t position = variant.find(from);
  ASSERT_NE(position, std::string::npos);
  variant.replace(position, from.size(), "\"deadlineMs\": 100.0");

  EXPECT_EQ(t20::canonical_body(variant), t20::canonical_body(t20::activatable()));
  EXPECT_EQ(t20::recompute_digest(variant), t20::recompute_digest(t20::activatable()));
  const ActivationPlan plan = t20::expect_accepted(decode_activation_plan(variant));
  EXPECT_EQ(plan.policies.deadline_ms, 100);
}

TEST(T20OrderingEquivalence, RepeatedDecodeAndWhitespaceVariantsAreIdentical) {
  // T20-ORD-08, T20-DET-01, T20-DET-04: repeated decodes and whitespace variants are identical, and
  // the domain-separated SHA-256 over the canonical body is deterministic and equals the reference.
  const std::string original = t20::activatable();
  const ActivationPlan first = t20::expect_accepted(decode_activation_plan(original));
  const ActivationPlan second = t20::expect_accepted(decode_activation_plan(original));
  EXPECT_EQ(second.digest.value, first.digest.value);
  EXPECT_EQ(second.status, first.status);

  const ActivationPlan whitespace =
      t20::expect_accepted(decode_activation_plan(t20::with_whitespace(original)));
  EXPECT_EQ(whitespace.digest.value, first.digest.value);
  EXPECT_EQ(whitespace.status, first.status);

  std::string separator = "xverse.xcom.activation-plan.v1";
  separator.push_back('\0');
  const std::string body = t20::canonical_body(original);
  EXPECT_EQ(sha256_hex(separator + body), t20::recompute_digest(original));
  EXPECT_EQ(sha256_hex(separator + body), sha256_hex(separator + body));
}
