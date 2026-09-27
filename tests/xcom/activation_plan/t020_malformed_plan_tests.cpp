// T020 malformed-plan suite (T20-MAL-01..14, CHK-20-03).
//
// Systematically injects structural and closed-shape defects and asserts the declared fail-closed
// outcome, stable code, affected target, and the absence of a decoded plan, as a family distinct
// from the T019 `NEG-D*` set (which is read read-only and never edited). The committed T017
// fixtures are read read-only.

#include "t020_support.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace {

using t20::DecodeOutcome;
using t20::json;
using xverse::xcom::plan::DecodeResult;
using xverse::xcom::plan::decode_activation_plan;
using xverse::xcom::plan::sha256_hex;

}  // namespace

TEST(T20MalformedPlan, TruncatedDocumentsAreRejected) {
  // T20-MAL-01: truncation at several byte offsets is an input defect with no decoded plan.
  const std::string document = t20::activatable();
  ASSERT_GT(document.size(), 16u);
  for (const std::size_t cut : {std::size_t{1}, document.size() / 2u, document.size() - 2u}) {
    t20::expect_error(decode_activation_plan(document.substr(0, cut)), t20::kCodeInput,
                      t20::kPlanTarget);
  }
}

TEST(T20MalformedPlan, UnbalancedDelimitersAreRejected) {
  // T20-MAL-02: an unbalanced or duplicated closing delimiter is an input defect.
  std::string mismatched = t20::activatable();
  const std::size_t root_close = mismatched.rfind('}');
  ASSERT_NE(root_close, std::string::npos);
  mismatched.replace(root_close, 1, "]");
  t20::expect_error(decode_activation_plan(mismatched), t20::kCodeInput, t20::kPlanTarget);

  std::string duplicated = t20::activatable();
  duplicated.insert(duplicated.rfind('}'), 1, '}');
  t20::expect_error(decode_activation_plan(duplicated), t20::kCodeInput, t20::kPlanTarget);

  std::string bracket = t20::activatable();
  const std::string endpoints = "\"endpoints\": [";
  const std::size_t position = bracket.find(endpoints);
  ASSERT_NE(position, std::string::npos);
  bracket.replace(position + endpoints.size() - 1u, 1u, "{");
  t20::expect_error(decode_activation_plan(bracket), t20::kCodeInput, t20::kPlanTarget);
}

TEST(T20MalformedPlan, TrailingContentIsRejected) {
  // T20-MAL-03: content after, or a second document beside, the single root object is rejected.
  const std::string document = t20::activatable();
  for (const std::string suffix : {"{}", " trailing", "{\"planVersion\": \"1\"}"}) {
    t20::expect_error(decode_activation_plan(document + suffix), t20::kCodeInput, t20::kPlanTarget);
  }
}

TEST(T20MalformedPlan, DuplicateMembersAtEachLevelAreRejected) {
  // T20-MAL-04: a repeated member at the top level, in provenance, in policies, and in an
  // endpoints[] object is an input defect (duplicate members are never collapsed).
  const auto duplicate = [](const std::string& needle, const std::string& replacement) {
    std::string document = t20::activatable();
    const std::size_t position = document.find(needle);
    EXPECT_NE(position, std::string::npos);
    document.replace(position, needle.size(), replacement);
    return document;
  };

  t20::expect_error(
      decode_activation_plan(duplicate("\"planVersion\": \"1\",",
                                       "\"planVersion\": \"1\", \"planVersion\": \"1\",")),
      t20::kCodeInput, t20::kPlanTarget);
  t20::expect_error(
      decode_activation_plan(duplicate("\"generatedAt\": \"1970-01-01T00:00:00Z\",",
                                       "\"generatedAt\": \"1970-01-01T00:00:00Z\", "
                                       "\"generatedAt\": \"1970-01-01T00:00:00Z\",")),
      t20::kCodeInput, t20::kPlanTarget);
  t20::expect_error(
      decode_activation_plan(duplicate("\"ordering\": \"fifo\",",
                                       "\"ordering\": \"fifo\", \"ordering\": \"fifo\",")),
      t20::kCodeInput, t20::kPlanTarget);
  t20::expect_error(
      decode_activation_plan(duplicate(
          "{\"endpointId\": \"controller-a\", \"role\": \"initiator\"}",
          "{\"endpointId\": \"controller-a\", \"endpointId\": \"controller-a\", "
          "\"role\": \"initiator\"}")),
      t20::kCodeInput, t20::kPlanTarget);
}

TEST(T20MalformedPlan, NonObjectRootsAreRejected) {
  // T20-MAL-05: only an object root is a plan; array, numeric, boolean, null, and string roots are
  // input defects.
  for (const std::string root : {"[]", "42", "true", "null", "\"plan\""}) {
    t20::expect_error(decode_activation_plan(root), t20::kCodeInput, t20::kPlanTarget);
  }
}

TEST(T20MalformedPlan, WrongJsonTypesAreRejected) {
  // T20-MAL-06: a collection given as an object, or an object given as an array, is a shape defect
  // at the affected object.
  const auto mutate = [](const std::string& member, const json& value) {
    json plan = json::parse(t20::activatable());
    plan[member] = value;
    return plan.dump();
  };
  t20::expect_error(decode_activation_plan(mutate("contracts", json::object())), t20::kCodeShape,
                    "contracts");
  t20::expect_error(decode_activation_plan(mutate("endpoints", json::object())), t20::kCodeShape,
                    "endpoints");
  t20::expect_error(decode_activation_plan(mutate("policies", json::array())), t20::kCodeShape,
                    "policies");
  t20::expect_error(decode_activation_plan(mutate("stimulation", json::array())), t20::kCodeShape,
                    "stimulation");
}

TEST(T20MalformedPlan, NullWhereObjectOrArrayRequiredIsRejected) {
  // T20-MAL-07: null where an object or array is required is a shape defect at the affected object.
  for (const std::string member : {"policies", "provenance", "contracts", "inputResolution"}) {
    json plan = json::parse(t20::activatable());
    plan[member] = nullptr;
    t20::expect_error(decode_activation_plan(plan.dump()), t20::kCodeShape, member);
  }
}

TEST(T20MalformedPlan, MissingRequiredMembersAreRejected) {
  // T20-MAL-08: each of the sixteen required members dropped in turn is a shape defect at the plan
  // target with no decoded plan.
  ASSERT_EQ(t20::required_members().size(), 16u);
  for (const std::string& member : t20::required_members()) {
    json plan = json::parse(t20::activatable());
    plan.erase(member);
    t20::expect_error(decode_activation_plan(plan.dump()), t20::kCodeShape, t20::kPlanTarget);
  }
}

TEST(T20MalformedPlan, UnknownNestedMembersAreRejected) {
  // T20-MAL-09: one unknown member in each nested object is a shape defect at that object.
  const json probe = {{"unknownT20Member", 1}};

  // Object-valued nested members.
  for (const char* member : {"provenance", "policies", "generator", "stimulation",
                             "inputResolution"}) {
    json plan = json::parse(t20::activatable());
    ASSERT_TRUE(plan[member].is_object()) << member;
    plan[member].update(probe);
    t20::expect_error(decode_activation_plan(plan.dump()), t20::kCodeShape, member);
  }

  // One unknown member in a collection element object is likewise a shape defect.
  for (const char* member : {"contracts", "endpoints", "routes", "providers",
                             "observationPoints", "clockDomains", "diagnostics"}) {
    json plan = json::parse(t20::activatable());
    ASSERT_TRUE(plan[member].is_array()) << member;
    ASSERT_FALSE(plan[member].empty()) << member;
    plan[member][0].update(probe);
    t20::expect_error(decode_activation_plan(plan.dump()), t20::kCodeShape, member);
  }
}

TEST(T20MalformedPlan, InvalidUtf8IsRejected) {
  // T20-MAL-10: a lone 0xFF byte inside a string value is not valid UTF-8 and is an input defect.
  std::string document = t20::activatable();
  const std::string needle = "\"fifo\"";
  const std::size_t position = document.find(needle);
  ASSERT_NE(position, std::string::npos);
  std::string replacement = "\"fi";
  replacement.push_back(static_cast<char>(0xFF));
  replacement += "fo\"";
  document.replace(position, needle.size(), replacement);
  t20::expect_error(decode_activation_plan(document), t20::kCodeInput, t20::kPlanTarget);
}

TEST(T20MalformedPlan, EmptyAndWhitespaceOnlyDocumentsAreRejected) {
  // T20-MAL-11: an empty or whitespace-only document has no root and is an input defect.
  for (const std::string& document : {std::string(), std::string("   \n\t "), std::string("\n")}) {
    t20::expect_error(decode_activation_plan(document), t20::kCodeInput, t20::kPlanTarget);
  }
}

TEST(T20MalformedPlan, OverNestedDocumentsFailClosed) {
  // T20-MAL-12: nesting above the default max_depth fails closed as a bound, not a shape, defect.
  std::string document;
  constexpr int kDepth = 105;
  for (int index = 0; index < kDepth; ++index) {
    document += "{\"n\":";
  }
  document += "1";
  for (int index = 0; index < kDepth; ++index) {
    document += "}";
  }
  t20::expect_error(decode_activation_plan(document), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20MalformedPlan, MalformedPlansNeverReturnADecodedValue) {
  // T20-MAL-13, CHK-20-03: aggregate guard - every malformed vector is rejected/failed with no
  // decoded value and never accepted.
  std::string nested;
  for (int index = 0; index < 105; ++index) {
    nested += "{\"n\":";
  }
  nested += "1";
  for (int index = 0; index < 105; ++index) {
    nested += "}";
  }

  json missing = json::parse(t20::activatable());
  missing.erase("clockDomains");
  json unknown = json::parse(t20::activatable());
  unknown["unknownTopLevel"] = 1;

  const std::vector<std::string> documents = {
      std::string(),           "   \n",              t20::activatable().substr(0, 7),
      "[]",                    "42",                 "true",
      "null",                  "\"plan\"",           t20::activatable() + "{}",
      t20::activatable() + " trailing",               nested,
      missing.dump(),          unknown.dump()};
  for (const std::string& document : documents) {
    const DecodeResult result = decode_activation_plan(document);
    EXPECT_FALSE(result.plan.has_value());
    EXPECT_NE(result.outcome, DecodeOutcome::accepted);
    EXPECT_FALSE(result.error.code.empty());
  }
}

TEST(T20MalformedPlan, MalformedMutationsRemainDistinctFromT019Cases) {
  // T20-MAL-14: source-inspection guard over the T019 negative test file (read read-only). The T019
  // file is byte-identical to its accepted revision, carries the T019 `DecodeNegative`/`NegD*`
  // identifiers, and carries no T020 `T20-MAL` identifier; no T019 test is edited or weakened.
  const std::string path =
      std::string(XCOM_ACTIVATION_PLAN_FIXTURE_DIR) + "/../decoder_negative_tests.cpp";
  const std::string t019 = t20::read_text(path);
  ASSERT_FALSE(t019.empty());
  EXPECT_EQ(sha256_hex(t019), t20::kT019NegativeFileSha256);
  EXPECT_NE(t019.find("DecodeNegative"), std::string::npos);
  EXPECT_NE(t019.find("NegD01"), std::string::npos);
  EXPECT_EQ(t019.find("T20-MAL"), std::string::npos);
  EXPECT_EQ(t019.find("test_xcom_plan_ordering_equivalence"), std::string::npos);
}
