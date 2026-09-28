// T019 bounded activation-plan decoder: declared negative set NEG-D01..NEG-D20 and the bound
// checks BND-01..BND-03/BND-05. Each case injects one controlled defect into a bounded,
// repository-owned, public-safe synthetic document or a mutation of a committed T017 fixture and
// asserts the declared outcome, code, target, and the absence of a decoded plan.

#include "xverse/xcom/activation_plan.hpp"

#include <algorithm>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <string>

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

namespace {

using nlohmann::json;
using xverse::xcom::plan::DecodeLimits;
using xverse::xcom::plan::DecodeOutcome;
using xverse::xcom::plan::DecodeResult;
using xverse::xcom::plan::canonical_plan_body_bytes;
using xverse::xcom::plan::decode_activation_plan;
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

json activatable() { return json::parse(plan_fixture("plan-activatable.json")); }
json inspectable() { return json::parse(plan_fixture("plan-inspectable.json")); }

/// Recompute and record the canonical digest so a mutation isolates a later check.
std::string seal(json plan) {
  const auto digest = recompute_plan_digest(plan.dump());
  plan["digest"]["value"] = digest.value;
  return plan.dump();
}

void expect_error(const DecodeResult& result, const std::string& code, const std::string& target) {
  EXPECT_FALSE(result.plan.has_value());
  EXPECT_NE(result.outcome, DecodeOutcome::accepted);
  EXPECT_EQ(result.error.code, code);
  if (target.empty()) {
    // The affected identifier is implementation-defined for a nested shape defect; it must be
    // a bounded, non-empty identifier or the fixed plan target.
    EXPECT_FALSE(result.error.target_id.empty());
  } else {
    EXPECT_EQ(result.error.target_id, target);
  }
  if (code == "XCOM-DECODE-BOUND" || code == "XCOM-DECODE-UNKNOWN") {
    EXPECT_EQ(result.outcome, DecodeOutcome::failed);
  } else {
    EXPECT_EQ(result.outcome, DecodeOutcome::rejected);
  }
}

}  // namespace

TEST(DecodeNegative, NegD01MalformedJson) {
  expect_error(decode_activation_plan("{\"planVersion\": \"1\""), "XCOM-DECODE-INPUT", "xcom-plan");
  expect_error(decode_activation_plan(""), "XCOM-DECODE-INPUT", "xcom-plan");
  expect_error(decode_activation_plan("{} trailing"), "XCOM-DECODE-INPUT", "xcom-plan");
}

TEST(DecodeNegative, NegD02DuplicateMember) {
  expect_error(decode_activation_plan("{\"planVersion\":\"1\",\"planVersion\":\"1\"}"),
               "XCOM-DECODE-INPUT", "xcom-plan");
}

TEST(DecodeNegative, NegD03NonObjectRoot) {
  expect_error(decode_activation_plan("[]"), "XCOM-DECODE-INPUT", "xcom-plan");
  expect_error(decode_activation_plan("42"), "XCOM-DECODE-INPUT", "xcom-plan");
  expect_error(decode_activation_plan("\"plan\""), "XCOM-DECODE-INPUT", "xcom-plan");
}

TEST(DecodeNegative, NegD04MissingRequiredMember) {
  json plan = activatable();
  plan.erase("clockDomains");
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-SHAPE", "xcom-plan");
}

TEST(DecodeNegative, NegD05UnknownTopLevelMember) {
  json plan = activatable();
  plan["unknownField"] = 1;
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-SHAPE", "xcom-plan");
}

TEST(DecodeNegative, NegD06UnknownNestedMember) {
  json plan = activatable();
  plan["policies"]["unknownMember"] = 1;
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-SHAPE", "policies");
}

TEST(DecodeNegative, NegD07VocabularyViolation) {
  json status = activatable();
  status["status"] = "pending";
  expect_error(decode_activation_plan(status.dump()), "XCOM-DECODE-SHAPE", "xcom-plan");

  json role = activatable();
  role["endpoints"][0]["role"] = "admin";
  expect_error(decode_activation_plan(role.dump()), "XCOM-DECODE-SHAPE", "endpoints");

  json severity = activatable();
  severity["diagnostics"][0]["severity"] = "critical";
  expect_error(decode_activation_plan(severity.dump()), "XCOM-DECODE-SHAPE", "diagnostics");
}

TEST(DecodeNegative, NegD08PatternViolation) {
  json plan = activatable();
  plan["contracts"][0]["contractId"] = "Contract-Upper";
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-SHAPE", "contracts");
}

TEST(DecodeNegative, NegD08DigestPattern) {
  // NEG-D08: the closed digest sub-schema (algorithm == "sha256", value =~ ^[0-9a-f]{64}$) applies
  // to every embedded digest, not only the top-level recorded `digest`. The closed-shape pass
  // precedes the digest check, so each mutation fails closed with `XCOM-DECODE-SHAPE` at target
  // `provenance` (and no engaged plan) regardless of the now-stale recorded digest; a digest check
  // reaching these inputs instead would indicate the declared pipeline order regressed.
  json graph_algorithm = activatable();
  graph_algorithm["provenance"]["graphDigest"]["algorithm"] = "md5";
  expect_error(decode_activation_plan(graph_algorithm.dump()), "XCOM-DECODE-SHAPE", "provenance");

  json graph_value = activatable();
  graph_value["provenance"]["graphDigest"]["value"] = "abc";
  expect_error(decode_activation_plan(graph_value.dump()), "XCOM-DECODE-SHAPE", "provenance");

  json graph_upper = activatable();
  graph_upper["provenance"]["graphDigest"]["value"] = std::string(64, 'A');
  expect_error(decode_activation_plan(graph_upper.dump()), "XCOM-DECODE-SHAPE", "provenance");

  json source_algorithm = activatable();
  source_algorithm["provenance"]["resources"][0]["sourceDigest"]["algorithm"] = "md5";
  expect_error(decode_activation_plan(source_algorithm.dump()), "XCOM-DECODE-SHAPE", "provenance");

  json source_value = activatable();
  source_value["provenance"]["resources"][0]["sourceDigest"]["value"] = "zzz";
  expect_error(decode_activation_plan(source_value.dump()), "XCOM-DECODE-SHAPE", "provenance");

  json source_short = activatable();
  source_short["provenance"]["resources"][0]["sourceDigest"]["value"] = std::string(63, 'a');
  expect_error(decode_activation_plan(source_short.dump()), "XCOM-DECODE-SHAPE", "provenance");
}

TEST(DecodeNegative, GeneratedAtDateTime) {
  for (const char* timestamp : {"2026-02-30T12:00:00Z", "2026-09-27T25:61:61Z",
                                "2026-09-27T12:00:60Z", "2026-09-27T12:00:00+24:00"}) {
    json plan = activatable();
    plan["provenance"]["generatedAt"] = timestamp;
    expect_error(decode_activation_plan(seal(plan)), "XCOM-DECODE-SHAPE", "provenance");
  }
  json valid = activatable();
  valid["provenance"]["generatedAt"] = "2024-02-29T23:59:59.123+01:30";
  const auto decoded = decode_activation_plan(seal(valid));
  EXPECT_EQ(decoded.outcome, DecodeOutcome::accepted);
  EXPECT_TRUE(decoded.plan.has_value());
}

TEST(DecodeNegative, NegD17CollectionOutOfOrder) {
  json plan = activatable();
  std::reverse(plan["endpoints"].begin(), plan["endpoints"].end());
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-SHAPE", "endpoints");
}

TEST(DecodeNegative, NegD18DuplicateOrEmptyOrNonInteger) {
  json duplicate = activatable();
  json extra_endpoint = duplicate["endpoints"][0];
  duplicate["endpoints"].push_back(extra_endpoint);
  expect_error(decode_activation_plan(duplicate.dump()), "XCOM-DECODE-SHAPE", "endpoints");

  json empty_order = activatable();
  empty_order["activationOrder"] = json::array();
  expect_error(decode_activation_plan(empty_order.dump()), "XCOM-DECODE-SHAPE", "activationOrder");

  json empty_caps = activatable();
  empty_caps["providers"][0]["capabilities"] = json::array();
  expect_error(decode_activation_plan(empty_caps.dump()), "XCOM-DECODE-SHAPE", "providers");

  json non_integer = activatable();
  non_integer["policies"]["deadlineMs"] = 100.5;
  expect_error(decode_activation_plan(non_integer.dump()), "XCOM-DECODE-SHAPE", "policies");
}

TEST(DecodeNegative, NegD09VersionMismatch) {
  json plan = activatable();
  plan["planVersion"] = "2";
  expect_error(decode_activation_plan(seal(plan)), "XCOM-DECODE-VERSION", "xcom-plan");
}

TEST(DecodeNegative, NegD10DigestFormInvalid) {
  json algorithm = activatable();
  algorithm["digest"]["algorithm"] = "sha512";
  expect_error(decode_activation_plan(algorithm.dump()), "XCOM-DECODE-DIGEST", "xcom-plan");

  json value = activatable();
  value["digest"]["value"] = "NOT-HEX";
  expect_error(decode_activation_plan(value.dump()), "XCOM-DECODE-DIGEST", "xcom-plan");
}

TEST(DecodeNegative, NegD11BodyChangedDigestUnchanged) {
  json plan = activatable();
  plan["generator"]["version"] = "0.2.0";
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-DIGEST", "xcom-plan");
}

TEST(DecodeNegative, NegD12DigestOverNonCanonicalSerialization) {
  json plan = activatable();
  json body = plan;
  body.erase("digest");
  // The recorded digest is computed over a non-canonical serialization of the digested region: the
  // same body with insignificant whitespace inserted, so the encoding differs from the canonical
  // form the decoder recomputes even though the member set is unchanged.
  const std::string noncanonical = body.dump(2);
  std::string separator = "xverse.xcom.activation-plan.v1";
  separator.push_back('\0');
  plan["digest"]["value"] = sha256_hex(separator + noncanonical);
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-DIGEST", "xcom-plan");
}

TEST(DecodeNegative, NegD13CapabilityDefect) {
  json no_provider = activatable();
  no_provider["providers"] = json::array();
  expect_error(decode_activation_plan(seal(no_provider)), "XCOM-DECODE-CAPABILITY", "xcom-plan");

  // A plan that declares capability resolved while selecting no provider is rejected even when its
  // status is inspectable, because it claims closure it does not have.
  json resolved_no_provider = inspectable();
  resolved_no_provider["providers"] = json::array();
  resolved_no_provider["inputResolution"]["capability"] = "resolved";
  expect_error(decode_activation_plan(seal(resolved_no_provider)), "XCOM-DECODE-CAPABILITY",
               "xcom-plan");

  json insufficient = activatable();
  insufficient["providers"][0]["requiredCapabilities"] = json::array({"telemetry"});
  expect_error(decode_activation_plan(seal(insufficient)), "XCOM-DECODE-CAPABILITY",
               "loopback-provider");

  json inspectable_insufficient = inspectable();
  inspectable_insufficient["providers"][0]["requiredCapabilities"] = json::array({"telemetry"});
  inspectable_insufficient["inputResolution"]["capability"] = "resolved";
  expect_error(decode_activation_plan(seal(inspectable_insufficient)), "XCOM-DECODE-CAPABILITY",
               "loopback-provider");
}

TEST(DecodeNegative, NegD14RouteReferenceDefect) {
  json unknown_contract = activatable();
  unknown_contract["routes"][0]["contractId"] = "contract-missing";
  expect_error(decode_activation_plan(seal(unknown_contract)), "XCOM-DECODE-REFERENCE", "route-ctrl");

  json unknown_endpoint = activatable();
  unknown_endpoint["routes"][0]["to"] = "endpoint-missing";
  expect_error(decode_activation_plan(seal(unknown_endpoint)), "XCOM-DECODE-REFERENCE", "route-ctrl");
}

TEST(DecodeNegative, NegD15ObservationAndOrderReferenceDefect) {
  json unknown_route = activatable();
  unknown_route["observationPoints"][0]["routeId"] = "route-missing";
  expect_error(decode_activation_plan(seal(unknown_route)), "XCOM-DECODE-REFERENCE", "tap-ctrl");

  json unknown_order = activatable();
  unknown_order["activationOrder"] = json::array({"controller-a", "route-undeclared"});
  expect_error(decode_activation_plan(seal(unknown_order)), "XCOM-DECODE-REFERENCE", "xcom-plan");
}

TEST(DecodeNegative, NegD16ActivatableWithUnresolvedInput) {
  json plan = inspectable();  // time is unresolved
  plan["status"] = "activatable";
  expect_error(decode_activation_plan(seal(plan)), "XCOM-DECODE-UNRESOLVED", "xcom-plan");
}

TEST(DecodeNegative, NegD19ByteDepthNodeBound) {
  DecodeLimits byte_limits;
  byte_limits.max_bytes = 8u;
  expect_error(decode_activation_plan(plan_fixture("plan-activatable.json"), byte_limits),
               "XCOM-DECODE-BOUND", "xcom-plan");

  DecodeLimits depth_limits;
  depth_limits.max_depth = 3u;
  expect_error(decode_activation_plan("{\"n\":{\"n\":{\"n\":{\"n\":1}}}}", depth_limits),
               "XCOM-DECODE-BOUND", "xcom-plan");

  DecodeLimits node_limits;
  node_limits.max_nodes = 2u;
  expect_error(decode_activation_plan("{\"a\":1,\"b\":2,\"c\":3}", node_limits),
               "XCOM-DECODE-BOUND", "xcom-plan");
}

TEST(DecodeNegative, NegD20EntityCapBound) {
  DecodeLimits limits;
  limits.max_provenance_resources = 1u;
  expect_error(decode_activation_plan(plan_fixture("plan-activatable.json"), limits),
               "XCOM-DECODE-BOUND", "xcom-plan");

  DecodeLimits endpoint_limits;
  endpoint_limits.max_endpoints = 1u;
  expect_error(decode_activation_plan(plan_fixture("plan-activatable.json"), endpoint_limits),
               "XCOM-DECODE-BOUND", "xcom-plan");
}

TEST(DecodeNegative, BoundLimitsInvalid) {
  // BND-05: a DecodeLimits member below the minimum fails closed with no plan.
  DecodeLimits limits;
  limits.max_nodes = 0u;
  expect_error(decode_activation_plan(plan_fixture("plan-activatable.json"), limits),
               "XCOM-DECODE-UNKNOWN", "xcom-plan");
}

TEST(DecodeNegative, NegD21NonFiniteOrOutOfRangeNumber) {
  // A non-finite or out-of-range integral numeric token is an input defect, not a value silently
  // retained as a double (detailed-design.md §4 step 3, §12).
  expect_error(decode_activation_plan("{\"n\":1e999}"), "XCOM-DECODE-INPUT", "xcom-plan");
  expect_error(decode_activation_plan("{\"n\":1e30}"), "XCOM-DECODE-INPUT", "xcom-plan");
  expect_error(decode_activation_plan("{\"n\":-1e30}"), "XCOM-DECODE-INPUT", "xcom-plan");
}

TEST(DecodeNegative, NegD22DigestMissingDomainSeparator) {
  // The recorded digest is computed over the canonical body but without the declared domain
  // separator, so it is not the domain-separated digest the decoder recomputes.
  json plan = activatable();
  const auto body = canonical_plan_body_bytes(plan.dump());
  ASSERT_EQ(body.outcome, DecodeOutcome::accepted);
  plan["digest"]["value"] = sha256_hex(body.value);
  expect_error(decode_activation_plan(plan.dump()), "XCOM-DECODE-DIGEST", "xcom-plan");
}
