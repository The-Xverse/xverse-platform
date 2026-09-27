// T020 drift suite (T20-DRF-01..09, CHK-20-04).
//
// Guards the decoder's declared member, vocabulary, pattern, ordering-key, minimum, and
// numeric-range tables against the committed normative plan schema; guards the closed
// `$defs/digest` sub-schema, the plan-version const, the domain separator, and the committed
// fixtures' canonical-body/digest goldens; and pins the accepted five Profile forms. Anchored
// schemas and fixtures are read read-only.

#include "t020_support.hpp"

#include <algorithm>
#include <functional>
#include <string>
#include <utility>
#include <vector>

namespace {

using t20::DecodeOutcome;
using t20::json;
using xverse::xcom::plan::decode_activation_plan;
using xverse::xcom::plan::recompute_plan_digest;
using xverse::xcom::plan::sha256_hex;

std::vector<std::string> tokens(const json& array) {
  std::vector<std::string> out;
  for (const json& item : array) {
    out.push_back(item.get<std::string>());
  }
  return out;
}

/// Assert one closed enum against the schema, accept every declared token, and reject one
/// out-of-vocabulary token with the declared code/target.
void probe_enum(const json& enum_values, const std::vector<std::string>& expected,
                const std::function<void(json&, const std::string&)>& set, bool inspectable_base,
                const std::string& bad, std::string_view code, std::string_view target) {
  EXPECT_EQ(tokens(enum_values), expected);
  for (const std::string& value : tokens(enum_values)) {
    json plan = json::parse(inspectable_base ? t20::inspectable() : t20::activatable());
    set(plan, value);
    t20::expect_accepted(decode_activation_plan(t20::seal(plan)));
  }
  json plan = json::parse(inspectable_base ? t20::inspectable() : t20::activatable());
  set(plan, bad);
  t20::expect_error(decode_activation_plan(plan.dump()), code, target);
}

}  // namespace

TEST(T20Drift, RequiredMemberTableMatchesSchema) {
  // T20-DRF-01: the sorted 16-member set equals the schema `required`; the root and every object
  // definition are closed; the decoder binds to the same closed member set.
  const json schema = t20::plan_schema();
  std::vector<std::string> required = tokens(schema.at("required"));
  std::vector<std::string> expected = t20::required_members();
  ASSERT_EQ(required.size(), 16u);
  std::sort(required.begin(), required.end());
  std::sort(expected.begin(), expected.end());
  EXPECT_EQ(required, expected);
  EXPECT_EQ(schema.at("additionalProperties").get<bool>(), false);

  for (auto& item : schema.at("$defs").items()) {
    const json& def = item.value();
    if (def.is_object() && def.contains("type") && def.at("type") == "object") {
      ASSERT_TRUE(def.contains("additionalProperties")) << item.key();
      EXPECT_EQ(def.at("additionalProperties").get<bool>(), false) << item.key();
    }
  }

  json dropped = json::parse(t20::activatable());
  dropped.erase("digest");
  t20::expect_error(decode_activation_plan(dropped.dump()), t20::kCodeShape, t20::kPlanTarget);
  json unknown = json::parse(t20::activatable());
  unknown["unexpectedTopLevel"] = 1;
  t20::expect_error(decode_activation_plan(unknown.dump()), t20::kCodeShape, t20::kPlanTarget);
}

TEST(T20Drift, ClosedEnumTablesMatchSchema) {
  // T20-DRF-02: every closed enum of the schema is accepted token-by-token and one
  // out-of-vocabulary token is rejected with the declared code/target.
  const json schema = t20::plan_schema();
  const json& defs = schema.at("$defs");

  probe_enum(schema.at("properties").at("status").at("enum"), {"inspectable", "activatable"},
             [](json& p, const std::string& v) { p["status"] = v; }, false, "pending",
             t20::kCodeShape, t20::kPlanTarget);
  probe_enum(defs.at("endpoint").at("properties").at("role").at("enum"),
             {"initiator", "responder", "observer", "tool"},
             [](json& p, const std::string& v) { p["endpoints"][0]["role"] = v; }, false, "admin",
             t20::kCodeShape, "endpoints");
  probe_enum(defs.at("policies").at("properties").at("ordering").at("enum"),
             {"fifo", "priority", "unordered"},
             [](json& p, const std::string& v) { p["policies"]["ordering"] = v; }, false, "lifo",
             t20::kCodeShape, "policies");
  probe_enum(defs.at("policies").at("properties").at("reliability").at("enum"),
             {"at-most-once", "at-least-once", "exactly-once", "best-effort"},
             [](json& p, const std::string& v) { p["policies"]["reliability"] = v; }, false,
             "maybe", t20::kCodeShape, "policies");
  probe_enum(defs.at("policies").at("properties").at("overflow").at("enum"),
             {"drop-oldest", "drop-newest", "coalesce", "lossless-backpressure", "reject",
              "fail-closed"},
             [](json& p, const std::string& v) { p["policies"]["overflow"] = v; }, false,
             "explode", t20::kCodeShape, "policies");
  probe_enum(defs.at("policies").at("properties").at("backpressure").at("enum"),
             {"fail-closed", "reject", "lossless-backpressure"},
             [](json& p, const std::string& v) { p["policies"]["backpressure"] = v; }, false,
             "ignore", t20::kCodeShape, "policies");
  probe_enum(defs.at("observationPoint").at("properties").at("payloadAccess").at("enum"),
             {"metadata-only", "allow-listed"},
             [](json& p, const std::string& v) { p["observationPoints"][0]["payloadAccess"] = v; },
             false, "all", t20::kCodeShape, "observationPoints");
  probe_enum(defs.at("observationPoint").at("properties").at("validityEffect").at("enum"),
             {"none", "degrade-on-loss", "invalidate-on-loss"},
             [](json& p, const std::string& v) { p["observationPoints"][0]["validityEffect"] = v; },
             false, "expire", t20::kCodeShape, "observationPoints");
  probe_enum(defs.at("clockDomain").at("properties").at("source").at("enum"),
             {"monotonic", "local-validation-clock", "unmapped"},
             [](json& p, const std::string& v) { p["clockDomains"][0]["source"] = v; }, false,
             "wall", t20::kCodeShape, "clockDomains");
  probe_enum(defs.at("diagnostic").at("properties").at("severity").at("enum"),
             {"error", "warning", "info"},
             [](json& p, const std::string& v) { p["diagnostics"][0]["severity"] = v; }, false,
             "critical", t20::kCodeShape, "diagnostics");
  probe_enum(defs.at("resourceRef").at("properties").at("kind").at("enum"),
             {"Component", "Deployment", "Scenario"},
             [](json& p, const std::string& v) {
               p["provenance"]["resources"] = json::array({p["provenance"]["resources"][0]});
               p["provenance"]["resources"][0]["kind"] = v;
             },
             false, "Profile", t20::kCodeShape, "provenance");
  probe_enum(defs.at("digest").at("properties").at("algorithm").at("enum"), {"sha256"},
             [](json& p, const std::string& v) { p["digest"]["algorithm"] = v; }, false, "md5",
             t20::kCodeDigest, t20::kPlanTarget);

  for (const char* member : {"identity", "schema", "capability", "time", "ownership", "policy"}) {
    probe_enum(defs.at("inputResolution").at("properties").at(member).at("enum"),
               {"resolved", "unresolved"},
               [member](json& p, const std::string& v) { p["inputResolution"][member] = v; }, true,
               "maybe", t20::kCodeShape, "inputResolution");
  }
}

TEST(T20Drift, PatternTablesMatchSchema) {
  // T20-DRF-03: the identifier, version, digest, generator-task, diagnostic-code, and apiVersion
  // patterns equal the schema, evidenced by an accepted conforming value and a rejected
  // non-conforming value per pattern.
  const json schema = t20::plan_schema();
  const json& defs = schema.at("$defs");
  EXPECT_EQ(defs.at("identifier").at("pattern").get<std::string>(),
            "^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$");
  EXPECT_EQ(defs.at("version").at("pattern").get<std::string>(),
            "^[0-9]+\\.[0-9]+(?:\\.[0-9]+)?$");
  EXPECT_EQ(defs.at("digest").at("properties").at("value").at("pattern").get<std::string>(),
            "^[0-9a-f]{64}$");
  EXPECT_EQ(defs.at("generator").at("properties").at("task").at("pattern").get<std::string>(),
            "^T[0-9]{3}$");
  EXPECT_EQ(defs.at("diagnostic").at("properties").at("code").at("pattern").get<std::string>(),
            "^XCOM-[A-Z0-9-]{3,64}$");
  EXPECT_EQ(defs.at("apiVersion").at("const").get<std::string>(), "xverse.io/xdl/v1alpha1");

  // Identifier: the fixture's conforming value decodes; upper case and a leading digit are rejected.
  t20::expect_accepted(decode_activation_plan(t20::activatable()));
  json upper_identifier = json::parse(t20::activatable());
  upper_identifier["contracts"][0]["contractId"] = "Contract-Upper";
  t20::expect_error(decode_activation_plan(upper_identifier.dump()), t20::kCodeShape, "contracts");
  json digit_identifier = json::parse(t20::activatable());
  digit_identifier["contracts"][0]["contractId"] = "1contract";
  t20::expect_error(decode_activation_plan(digit_identifier.dump()), t20::kCodeShape, "contracts");

  // Version: `1.0.0` conforms; `1` does not.
  json missing_minor = json::parse(t20::activatable());
  missing_minor["contracts"][0]["schemaVersion"] = "1";
  t20::expect_error(decode_activation_plan(missing_minor.dump()), t20::kCodeShape, "contracts");

  // Generator task: `T018` conforms; `T18` does not.
  json short_task = json::parse(t20::activatable());
  short_task["generator"]["task"] = "T18";
  t20::expect_error(decode_activation_plan(short_task.dump()), t20::kCodeShape, "generator");

  // Diagnostic code: `XCOM-PLAN-OK` conforms; a too-short token does not.
  json short_code = json::parse(t20::activatable());
  short_code["diagnostics"][0]["code"] = "XCOM-OK";
  t20::expect_error(decode_activation_plan(short_code.dump()), t20::kCodeShape, "diagnostics");

  // Embedded digest pattern: a nested algorithm/value violation is rejected at `provenance`.
  json bad_algorithm = json::parse(t20::activatable());
  bad_algorithm["provenance"]["graphDigest"]["algorithm"] = "md5";
  t20::expect_error(decode_activation_plan(bad_algorithm.dump()), t20::kCodeShape, "provenance");
  json upper_value = json::parse(t20::activatable());
  upper_value["provenance"]["resources"][0]["sourceDigest"]["value"] = std::string(64, 'A');
  t20::expect_error(decode_activation_plan(upper_value.dump()), t20::kCodeShape, "provenance");

  // apiVersion const: a different api version is rejected at `provenance`.
  json bad_api = json::parse(t20::activatable());
  bad_api["provenance"]["resources"][0]["apiVersion"] = "xverse.io/xdl/v2";
  t20::expect_error(decode_activation_plan(bad_api.dump()), t20::kCodeShape, "provenance");
}

TEST(T20Drift, CollectionKeysAndMinimumsMatchSchema) {
  // T20-DRF-04: ordering keys, uniqueItems, minimums (`capabilities`=1, `resources`=1,
  // `activationOrder`=1), and the top-level collection set equal the schema, and the decoder
  // enforces order/uniqueness/minimum.
  const json schema = t20::plan_schema();
  const json& defs = schema.at("$defs");
  EXPECT_EQ(defs.at("provider").at("properties").at("capabilities").at("minItems").get<int>(), 1);
  EXPECT_EQ(defs.at("provenance").at("properties").at("resources").at("minItems").get<int>(), 1);
  EXPECT_EQ(schema.at("properties").at("activationOrder").at("minItems").get<int>(), 1);
  for (const char* collection : {"contracts", "endpoints", "routes", "providers",
                                 "observationPoints", "clockDomains", "diagnostics"}) {
    EXPECT_EQ(schema.at("properties").at(collection).at("uniqueItems").get<bool>(), true)
        << collection;
  }

  json empty_capabilities = json::parse(t20::activatable());
  empty_capabilities["providers"][0]["capabilities"] = json::array();
  t20::expect_error(decode_activation_plan(empty_capabilities.dump()), t20::kCodeShape,
                    "providers");

  json empty_resources = json::parse(t20::activatable());
  empty_resources["provenance"]["resources"] = json::array();
  t20::expect_error(decode_activation_plan(empty_resources.dump()), t20::kCodeShape, "provenance");

  json empty_order = json::parse(t20::activatable());
  empty_order["activationOrder"] = json::array();
  t20::expect_error(decode_activation_plan(empty_order.dump()), t20::kCodeShape, "activationOrder");

  json duplicate_key = json::parse(t20::activatable());
  duplicate_key["contracts"].push_back(duplicate_key["contracts"][0]);
  t20::expect_error(decode_activation_plan(duplicate_key.dump()), t20::kCodeShape, "contracts");

  json reversed = json::parse(t20::activatable());
  std::reverse(reversed["endpoints"].begin(), reversed["endpoints"].end());
  t20::expect_error(decode_activation_plan(reversed.dump()), t20::kCodeShape, "endpoints");
}

TEST(T20Drift, NumericRangesMatchSchema) {
  // T20-DRF-05: deadlineMs 0..600000, retry 0..64, queueDepth 1..65536 equal the schema; an
  // out-of-range or non-integer value is rejected `XCOM-DECODE-SHAPE`.
  const json schema = t20::plan_schema();
  const json& policies = schema.at("$defs").at("policies").at("properties");
  EXPECT_EQ(policies.at("deadlineMs").at("minimum").get<int>(), 0);
  EXPECT_EQ(policies.at("deadlineMs").at("maximum").get<int>(), 600000);
  EXPECT_EQ(policies.at("retry").at("minimum").get<int>(), 0);
  EXPECT_EQ(policies.at("retry").at("maximum").get<int>(), 64);
  EXPECT_EQ(policies.at("queueDepth").at("minimum").get<int>(), 1);
  EXPECT_EQ(policies.at("queueDepth").at("maximum").get<int>(), 65536);

  const auto set = [](const std::string& member, const json& value) {
    json plan = json::parse(t20::activatable());
    plan["policies"][member] = value;
    return t20::seal(plan);
  };
  t20::expect_accepted(decode_activation_plan(set("deadlineMs", 600000)));
  t20::expect_accepted(decode_activation_plan(set("retry", 64)));
  t20::expect_accepted(decode_activation_plan(set("queueDepth", 1)));

  for (const std::pair<const char*, json>& probe : {std::pair<const char*, json>{"deadlineMs", 600001},
                                                   {"deadlineMs", -1}, {"retry", 65},
                                                   {"queueDepth", 0}, {"deadlineMs", 100.5}}) {
    json plan = json::parse(t20::activatable());
    plan["policies"][probe.first] = probe.second;
    t20::expect_error(decode_activation_plan(plan.dump()), t20::kCodeShape, "policies");
  }
}

TEST(T20Drift, EmbeddedDigestSubSchemaMatchesDecoder) {
  // T20-DRF-06: the closed `$defs/digest` sub-schema equals the decoder's embedded-digest rule for
  // `provenance.graphDigest` and each `provenance.resources[].sourceDigest`; a violation is
  // rejected `XCOM-DECODE-SHAPE`.
  const json schema = t20::plan_schema();
  const json& digest = schema.at("$defs").at("digest");
  EXPECT_EQ(digest.at("additionalProperties").get<bool>(), false);
  EXPECT_EQ(tokens(digest.at("required")),
            std::vector<std::string>({"algorithm", "value"}));
  EXPECT_EQ(tokens(digest.at("properties").at("algorithm").at("enum")),
            std::vector<std::string>({"sha256"}));
  EXPECT_EQ(digest.at("properties").at("value").at("pattern").get<std::string>(),
            "^[0-9a-f]{64}$");

  json graph_algorithm = json::parse(t20::activatable());
  graph_algorithm["provenance"]["graphDigest"]["algorithm"] = "md5";
  t20::expect_error(decode_activation_plan(graph_algorithm.dump()), t20::kCodeShape, "provenance");
  json graph_value = json::parse(t20::activatable());
  graph_value["provenance"]["graphDigest"]["value"] = "abc";
  t20::expect_error(decode_activation_plan(graph_value.dump()), t20::kCodeShape, "provenance");
  json source_value = json::parse(t20::activatable());
  source_value["provenance"]["resources"][0]["sourceDigest"]["value"] = std::string(63, 'a');
  t20::expect_error(decode_activation_plan(source_value.dump()), t20::kCodeShape, "provenance");

  // The top-level recorded digest's algorithm/hex form is classified at the version/digest step.
  json top_algorithm = json::parse(t20::activatable());
  top_algorithm["digest"]["algorithm"] = "sha512";
  t20::expect_error(decode_activation_plan(top_algorithm.dump()), t20::kCodeDigest,
                    t20::kPlanTarget);
}

TEST(T20Drift, PlanVersionConstMatchesDecoder) {
  // T20-DRF-07: the schema planVersion const equals "1" and a mismatched version is rejected
  // `XCOM-DECODE-VERSION` before any digest/body comparison.
  const json schema = t20::plan_schema();
  EXPECT_EQ(schema.at("properties").at("planVersion").at("const").get<std::string>(), "1");
  t20::expect_accepted(decode_activation_plan(t20::activatable()));
  json version = json::parse(t20::activatable());
  version["planVersion"] = "2";
  t20::expect_error(decode_activation_plan(version.dump()), t20::kCodeVersion, t20::kPlanTarget);
}

TEST(T20Drift, DomainSeparatorAndGoldenDigestsAreStable) {
  // T20-DRF-08, CHK-20-04: each committed fixture's recorded digest equals its golden value, the
  // decoder's recomputation, and the canonical body hash; a digest without the declared domain
  // separator or over a non-canonical body is rejected `XCOM-DECODE-DIGEST`.
  struct Case {
    const char* name;
    std::string (*document)();
    const char* digest;
    const char* body_hash;
  };
  const Case cases[] = {{"plan-activatable.json", &t20::activatable, t20::kFixtureActivatableDigest.data(),
                         t20::kFixtureActivatableBodySha256.data()},
                        {"plan-inspectable.json", &t20::inspectable, t20::kFixtureInspectableDigest.data(),
                         t20::kFixtureInspectableBodySha256.data()}};

  std::string separator = "xverse.xcom.activation-plan.v1";
  separator.push_back('\0');

  for (const Case& item : cases) {
    const std::string document = item.document();
    const json parsed = json::parse(document);
    const std::string recorded = parsed.at("digest").at("value").get<std::string>();
    EXPECT_EQ(recorded, item.digest) << item.name;
    EXPECT_EQ(t20::recompute_digest(document), item.digest) << item.name;
    const std::string body = t20::canonical_body(document);
    EXPECT_EQ(sha256_hex(body), item.body_hash) << item.name;

    json without_separator = parsed;
    without_separator["digest"]["value"] = sha256_hex(body);
    t20::expect_error(decode_activation_plan(without_separator.dump()), t20::kCodeDigest,
                      t20::kPlanTarget);

    json non_canonical = parsed;
    non_canonical["digest"]["value"] = sha256_hex(separator + json::parse(body).dump(2));
    t20::expect_error(decode_activation_plan(non_canonical.dump()), t20::kCodeDigest,
                      t20::kPlanTarget);
  }
}

TEST(T20Drift, ProfileFormVocabularyIsTheAcceptedFiveForms) {
  // T20-DRF-09: the Profile schema declares exactly the accepted five form kinds and each form is a
  // closed object with required members; no sixth form is introduced.
  const json profile = t20::profile_schema();
  const json& kinds = profile.at("$defs").at("kind").at("enum");
  EXPECT_EQ(tokens(kinds), std::vector<std::string>({"interface-policy", "flow-policy",
                                                     "network-provider", "observation-policy",
                                                     "validation-policy"}));
  EXPECT_EQ(kinds.size(), 5u);

  const std::pair<const char*, const char*> forms[] = {
      {"interface-policy", "interfacePolicy"},   {"flow-policy", "flowPolicy"},
      {"network-provider", "networkProviderPolicy"}, {"observation-policy", "observationPolicy"},
      {"validation-policy", "validationPolicy"}};
  for (const auto& [kind, def] : forms) {
    const json& form = profile.at("$defs").at(def);
    ASSERT_TRUE(form.is_object()) << kind;
    EXPECT_EQ(form.at("additionalProperties").get<bool>(), false) << kind;
    EXPECT_FALSE(form.at("required").empty()) << kind;
  }
}
