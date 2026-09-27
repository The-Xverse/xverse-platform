// T020 bounded, header-only test support for the XDL-derived activation-plan suites.
//
// The helpers read the committed T017 plan fixtures and schemas read-only, build bounded
// synthetic representations, and assert the decoder's declared outcome/code. They perform no
// network, subprocess, clock, or filesystem *write* access and hold no global mutable state.
// Only the C++20 standard library, the already-admitted nlohmann/json header, the already-required
// GTest prefix, and the T019 decoder header are used.

#ifndef XVERSE_XCOM_T020_SUPPORT_HPP
#define XVERSE_XCOM_T020_SUPPORT_HPP

#include "xverse/xcom/activation_plan.hpp"

#include <algorithm>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

namespace t20 {

using nlohmann::json;
using xverse::xcom::plan::ActivationPlan;
using xverse::xcom::plan::DecodeError;
using xverse::xcom::plan::DecodeLimits;
using xverse::xcom::plan::DecodeOutcome;
using xverse::xcom::plan::DecodeResult;

inline constexpr std::string_view kCodeInput = "XCOM-DECODE-INPUT";
inline constexpr std::string_view kCodeShape = "XCOM-DECODE-SHAPE";
inline constexpr std::string_view kCodeVersion = "XCOM-DECODE-VERSION";
inline constexpr std::string_view kCodeDigest = "XCOM-DECODE-DIGEST";
inline constexpr std::string_view kCodeCapability = "XCOM-DECODE-CAPABILITY";
inline constexpr std::string_view kCodeReference = "XCOM-DECODE-REFERENCE";
inline constexpr std::string_view kCodeUnresolved = "XCOM-DECODE-UNRESOLVED";
inline constexpr std::string_view kCodeBound = "XCOM-DECODE-BOUND";
inline constexpr std::string_view kCodeUnknown = "XCOM-DECODE-UNKNOWN";
inline constexpr std::string_view kPlanTarget = "xcom-plan";

/// The closed required top-level member set (drift-guarded against the committed plan schema).
inline const std::vector<std::string>& required_members() {
  static const std::vector<std::string> members = {
      "planVersion",     "digest",         "generator",       "provenance",
      "contracts",       "endpoints",      "routes",          "providers",
      "policies",        "observationPoints", "stimulation",  "clockDomains",
      "activationOrder", "diagnostics",    "status",          "inputResolution"};
  return members;
}

/// Pinned golden values captured from the accepted, unchanged T017 artifacts.
inline constexpr std::string_view kFixtureActivatableFileSha256 =
    "8f32193b5fe9ad3546cbc291eaa276ffae6e41297fa8d990e26997f5c8bc0790";
inline constexpr std::string_view kFixtureActivatableBodySha256 =
    "03dde94859fde2503ee905930b0a75a653898a21b30fd508b4bb0322930762e5";
inline constexpr std::string_view kFixtureActivatableDigest =
    "7aaf63173194330d2debe9faaba2f5ed2125a611ce9f9accc124a9d215a5e4ce";
inline constexpr std::string_view kFixtureInspectableFileSha256 =
    "48be9d195ed0f324ad497437faeef6f34f6cc6a083989bf7ce3a800e4ec84cd1";
inline constexpr std::string_view kFixtureInspectableBodySha256 =
    "a97a0a6ae524373b789db5cb3b195233d7e46a6536435160c8a6c96b6836ba99";
inline constexpr std::string_view kFixtureInspectableDigest =
    "98c13f81e6945485e5ac74bbd0f44b271ca05b68c47a2ac5cc55c964c3030d3f";
inline constexpr std::string_view kT019NegativeFileSha256 =
    "14cb56ec5cac23826735350d5db302fbf1ae0cba0514923882ca14bae3017ab5";

/// Read a file as bounded binary text; aborts the calling case when it cannot be read.
inline std::string read_text(const std::string& path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    ADD_FAILURE() << "unreadable test input: " << path;
    return {};
  }
  std::ostringstream buffer;
  buffer << stream.rdbuf();
  return buffer.str();
}

inline std::string plan_fixture(const std::string& name) {
  return read_text(std::string(XCOM_ACTIVATION_PLAN_FIXTURE_DIR) + "/plan/valid/" + name);
}

inline std::string activatable() { return plan_fixture("plan-activatable.json"); }
inline std::string inspectable() { return plan_fixture("plan-inspectable.json"); }

/// The committed T017 plan schema, and the Profile schema, read read-only via the build-time paths.
inline json plan_schema() { return json::parse(read_text(XCOM_ACTIVATION_PLAN_SCHEMA_PATH)); }
inline json profile_schema() { return json::parse(read_text(XCOM_T020_PROFILE_SCHEMA_PATH)); }

/// Recompute and record the canonical digest so a mutation isolates exactly one later check.
inline std::string seal(json plan) {
  const auto digest = xverse::xcom::plan::recompute_plan_digest(plan.dump());
  if (digest.outcome == DecodeOutcome::accepted) {
    plan["digest"]["value"] = digest.value;
  }
  return plan.dump();
}

/// Canonical digested bytes of a document, asserting the document is accepted first.
inline std::string canonical_body(const std::string& text) {
  const auto body = xverse::xcom::plan::canonical_plan_body_bytes(text);
  EXPECT_EQ(body.outcome, DecodeOutcome::accepted);
  return body.value;
}

/// Recomputed domain-separated digest, asserting the document is accepted first.
inline std::string recompute_digest(const std::string& text) {
  const auto digest = xverse::xcom::plan::recompute_plan_digest(text);
  EXPECT_EQ(digest.outcome, DecodeOutcome::accepted);
  return digest.value;
}

/// Assert the declared outcome, stable code, target, and the absence of a decoded plan.
inline void expect_error(const DecodeResult& result, std::string_view code,
                         std::string_view target) {
  EXPECT_FALSE(result.plan.has_value());
  EXPECT_NE(result.outcome, DecodeOutcome::accepted);
  EXPECT_EQ(result.error.code, code);
  if (target.empty()) {
    EXPECT_FALSE(result.error.target_id.empty());
  } else {
    EXPECT_EQ(result.error.target_id, target);
  }
  if (code == kCodeBound || code == kCodeUnknown) {
    EXPECT_EQ(result.outcome, DecodeOutcome::failed);
  } else {
    EXPECT_EQ(result.outcome, DecodeOutcome::rejected);
  }
}

/// Assert acceptance with an engaged, error-free value and return a copy of it.
inline ActivationPlan expect_accepted(const DecodeResult& result) {
  EXPECT_EQ(result.outcome, DecodeOutcome::accepted);
  EXPECT_TRUE(result.plan.has_value());
  EXPECT_TRUE(result.error.code.empty());
  return result.plan ? *result.plan : ActivationPlan{};
}

/// Append a JSON string value in the canonical minimal escaping the decoder accepts.
inline void append_string(const std::string& value, std::string& out) { out += json(value).dump(); }

/// Emit a JSON value with every object's members in reverse key order (a non-canonical but
/// semantically equivalent representation), used to prove member-order equivalence.
inline void emit_reversed(const json& value, std::string& out) {
  if (value.is_object()) {
    std::vector<std::string> keys;
    keys.reserve(value.size());
    for (auto& item : value.items()) {
      keys.push_back(item.key());
    }
    std::reverse(keys.begin(), keys.end());
    out.push_back('{');
    bool first = true;
    for (const std::string& key : keys) {
      if (!first) {
        out.push_back(',');
      }
      first = false;
      append_string(key, out);
      out.push_back(':');
      emit_reversed(value.at(key), out);
    }
    out.push_back('}');
    return;
  }
  if (value.is_array()) {
    out.push_back('[');
    bool first = true;
    for (const json& element : value) {
      if (!first) {
        out.push_back(',');
      }
      first = false;
      emit_reversed(element, out);
    }
    out.push_back(']');
    return;
  }
  out += value.dump();
}

inline std::string reverse_key_order_text(const json& value) {
  std::string out;
  emit_reversed(value, out);
  return out;
}

/// A whitespace-bearing, member-sorted serialization of a parsed value.
inline std::string with_whitespace(const std::string& text) { return json::parse(text).dump(3); }

/// Enumerate each of the 13 declared DecodeLimits members, setting it to zero in turn.
template <typename Fn>
inline void for_each_limit(Fn&& visit) {
  const std::vector<std::pair<std::string, std::size_t DecodeLimits::*>> members = {
      {"max_bytes", &DecodeLimits::max_bytes},
      {"max_depth", &DecodeLimits::max_depth},
      {"max_nodes", &DecodeLimits::max_nodes},
      {"max_string_length", &DecodeLimits::max_string_length},
      {"max_contracts", &DecodeLimits::max_contracts},
      {"max_endpoints", &DecodeLimits::max_endpoints},
      {"max_routes", &DecodeLimits::max_routes},
      {"max_providers", &DecodeLimits::max_providers},
      {"max_observation_points", &DecodeLimits::max_observation_points},
      {"max_clock_domains", &DecodeLimits::max_clock_domains},
      {"max_diagnostics", &DecodeLimits::max_diagnostics},
      {"max_activation_order", &DecodeLimits::max_activation_order},
      {"max_provenance_resources", &DecodeLimits::max_provenance_resources}};
  for (const auto& [name, pointer] : members) {
    DecodeLimits probe;
    probe.*pointer = 0u;
    visit(name, probe);
  }
}

/// The count of distinct declared DecodeLimits members (a bounded, fixed capacity).
inline constexpr std::size_t kDecodeLimitCount = 13u;

}  // namespace t20

#endif  // XVERSE_XCOM_T020_SUPPORT_HPP
