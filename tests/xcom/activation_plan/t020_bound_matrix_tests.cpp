// T020 bound-matrix suite (T20-BND-01..11, CHK-20-05).
//
// Exercises every declared DecodeLimits member at, below, and above its declared value, proving the
// declared failed/rejected classification with no decoded value on a breach and that a limit below
// one fails closed with XCOM-DECODE-UNKNOWN. All vectors are small and bounded; the true default
// byte bound is exercised by lowering the limit against the committed fixture rather than
// allocating an over-limit document. No production numeric value is fixed.

#include "t020_support.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace {

using t20::DecodeOutcome;
using t20::json;
using xverse::xcom::plan::DecodeLimits;
using xverse::xcom::plan::DecodeResult;
using xverse::xcom::plan::decode_activation_plan;

/// Find the smallest value of one limit at which the committed fixture is accepted.
template <typename Setter>
std::size_t minimal_limit(const std::string& document, Setter set, std::size_t ceiling) {
  for (std::size_t value = 1; value <= ceiling; ++value) {
    DecodeLimits limits;
    set(limits, value);
    if (decode_activation_plan(document, limits).outcome == DecodeOutcome::accepted) {
      return value;
    }
  }
  return 0u;
}

}  // namespace

TEST(T20BoundMatrix, ByteBoundAtAndOver) {
  // T20-BND-01: the fixture accepted at exactly its byte length and rejected one byte below.
  const std::string document = t20::activatable();
  DecodeLimits exact;
  exact.max_bytes = document.size();
  t20::expect_accepted(decode_activation_plan(document, exact));

  DecodeLimits under;
  under.max_bytes = document.size() - 1u;
  t20::expect_error(decode_activation_plan(document, under), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20BoundMatrix, DepthBoundAtAndOver) {
  // T20-BND-02: the document accepted at exactly the minimum depth and failed one level deeper.
  const std::string document = t20::activatable();
  const std::size_t depth =
      minimal_limit(document, [](DecodeLimits& limits, std::size_t value) { limits.max_depth = value; }, 64u);
  ASSERT_GE(depth, 2u);

  DecodeLimits exact;
  exact.max_depth = depth;
  t20::expect_accepted(decode_activation_plan(document, exact));

  DecodeLimits over;
  over.max_depth = depth - 1u;
  t20::expect_error(decode_activation_plan(document, over), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20BoundMatrix, NodeBoundAtAndOver) {
  // T20-BND-03: the document accepted at exactly the minimum node count and failed one node more.
  const std::string document = t20::activatable();
  const std::size_t nodes =
      minimal_limit(document, [](DecodeLimits& limits, std::size_t value) { limits.max_nodes = value; }, 4096u);
  ASSERT_GE(nodes, 17u);

  DecodeLimits exact;
  exact.max_nodes = nodes;
  t20::expect_accepted(decode_activation_plan(document, exact));

  DecodeLimits over;
  over.max_nodes = nodes - 1u;
  t20::expect_error(decode_activation_plan(document, over), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20BoundMatrix, StringLengthOverIsRejected) {
  // T20-BND-04: a decoded string one byte over max_string_length is rejected `XCOM-DECODE-SHAPE`
  // with no decoded value (per the T019 unit contract), not a bound failure.
  const std::string document = t20::activatable();
  const std::size_t length = minimal_limit(
      document, [](DecodeLimits& limits, std::size_t value) { limits.max_string_length = value; },
      256u);
  ASSERT_GE(length, 2u);

  DecodeLimits exact;
  exact.max_string_length = length;
  t20::expect_accepted(decode_activation_plan(document, exact));

  DecodeLimits over;
  over.max_string_length = length - 1u;
  t20::expect_error(decode_activation_plan(document, over), t20::kCodeShape, t20::kPlanTarget);
}

TEST(T20BoundMatrix, ContractCapAtAndOver) {
  // T20-BND-05: a valid two-contract plan accepted at max_contracts = 2 and failed at 1.
  json plan = json::parse(t20::activatable());
  json second = {{"contractId", "contract-b"}, {"schemaId", "xcom.control.v1"},
                 {"schemaVersion", "1.0.0"}};
  plan["contracts"] = json::array({second, plan["contracts"][0]});
  const std::string document = t20::seal(plan);
  t20::expect_accepted(decode_activation_plan(document));

  DecodeLimits exact;
  exact.max_contracts = 2u;
  t20::expect_accepted(decode_activation_plan(document, exact));
  DecodeLimits over;
  over.max_contracts = 1u;
  t20::expect_error(decode_activation_plan(document, over), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20BoundMatrix, EndpointCapAtAndOver) {
  // T20-BND-06: the two-endpoint fixture accepted at max_endpoints = 2 and failed at 1.
  const std::string document = t20::activatable();
  DecodeLimits exact;
  exact.max_endpoints = 2u;
  t20::expect_accepted(decode_activation_plan(document, exact));
  DecodeLimits over;
  over.max_endpoints = 1u;
  t20::expect_error(decode_activation_plan(document, over), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20BoundMatrix, RouteCapAtAndOver) {
  // T20-BND-07: a valid two-route plan accepted at max_routes = 2 and failed at 1.
  json plan = json::parse(t20::activatable());
  json second = {{"routeId", "route-b"}, {"from", "controller-a"}, {"to", "plant-a"},
                 {"contractId", "contract-ctrl"}};
  plan["routes"] = json::array({second, plan["routes"][0]});
  const std::string document = t20::seal(plan);
  t20::expect_accepted(decode_activation_plan(document));

  DecodeLimits exact;
  exact.max_routes = 2u;
  t20::expect_accepted(decode_activation_plan(document, exact));
  DecodeLimits over;
  over.max_routes = 1u;
  t20::expect_error(decode_activation_plan(document, over), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20BoundMatrix, ProviderCapAtAndOver) {
  // T20-BND-08: a valid two-provider plan accepted at max_providers = 2 and failed at 1.
  json plan = json::parse(t20::activatable());
  json second = {{"providerId", "provider-b"}, {"capabilities", json::array({"message"})},
                 {"requiredCapabilities", json::array({"message"})}};
  plan["providers"] = json::array({plan["providers"][0], second});
  const std::string document = t20::seal(plan);
  t20::expect_accepted(decode_activation_plan(document));

  DecodeLimits exact;
  exact.max_providers = 2u;
  t20::expect_accepted(decode_activation_plan(document, exact));
  DecodeLimits over;
  over.max_providers = 1u;
  t20::expect_error(decode_activation_plan(document, over), t20::kCodeBound, t20::kPlanTarget);
}

TEST(T20BoundMatrix, ObservationPointAndClockDomainCapsAtAndOver) {
  // T20-BND-09: a valid two-observation-point and two-clock-domain plan accepted at each cap and
  // failed one below.
  json observations = json::parse(t20::activatable());
  json tap = {{"tapId", "tap-a"}, {"routeId", "route-ctrl"}, {"payloadAccess", "metadata-only"},
              {"validityEffect", "none"}};
  observations["observationPoints"] = json::array({tap, observations["observationPoints"][0]});
  const std::string observation_document = t20::seal(observations);
  DecodeLimits observation_exact;
  observation_exact.max_observation_points = 2u;
  t20::expect_accepted(decode_activation_plan(observation_document, observation_exact));
  DecodeLimits observation_over;
  observation_over.max_observation_points = 1u;
  t20::expect_error(decode_activation_plan(observation_document, observation_over),
                    t20::kCodeBound, t20::kPlanTarget);

  json clocks = json::parse(t20::activatable());
  json domain = {{"clockDomainId", "clock-a"}, {"source", "monotonic"}};
  clocks["clockDomains"] = json::array({domain, clocks["clockDomains"][0]});
  const std::string clock_document = t20::seal(clocks);
  DecodeLimits clock_exact;
  clock_exact.max_clock_domains = 2u;
  t20::expect_accepted(decode_activation_plan(clock_document, clock_exact));
  DecodeLimits clock_over;
  clock_over.max_clock_domains = 1u;
  t20::expect_error(decode_activation_plan(clock_document, clock_over), t20::kCodeBound,
                    t20::kPlanTarget);
}

TEST(T20BoundMatrix, DiagnosticActivationOrderAndResourceCapsAtAndOver) {
  // T20-BND-10: diagnostics, activation order, and provenance resources each accepted at the plan's
  // count and failed one below.
  json diagnostics = json::parse(t20::activatable());
  json entry = {{"code", "XCOM-PLAN-AA"}, {"severity", "info"}, {"targetId", "route-ctrl"}};
  diagnostics["diagnostics"] = json::array({entry, diagnostics["diagnostics"][0]});
  const std::string diagnostic_document = t20::seal(diagnostics);
  DecodeLimits diagnostic_exact;
  diagnostic_exact.max_diagnostics = 2u;
  t20::expect_accepted(decode_activation_plan(diagnostic_document, diagnostic_exact));
  DecodeLimits diagnostic_over;
  diagnostic_over.max_diagnostics = 1u;
  t20::expect_error(decode_activation_plan(diagnostic_document, diagnostic_over), t20::kCodeBound,
                    t20::kPlanTarget);

  const std::string document = t20::activatable();
  DecodeLimits order_exact;
  order_exact.max_activation_order = 2u;
  t20::expect_accepted(decode_activation_plan(document, order_exact));
  DecodeLimits order_over;
  order_over.max_activation_order = 1u;
  t20::expect_error(decode_activation_plan(document, order_over), t20::kCodeBound,
                    t20::kPlanTarget);

  DecodeLimits resource_exact;
  resource_exact.max_provenance_resources = 2u;
  t20::expect_accepted(decode_activation_plan(document, resource_exact));
  DecodeLimits resource_over;
  resource_over.max_provenance_resources = 1u;
  t20::expect_error(decode_activation_plan(document, resource_over), t20::kCodeBound,
                    t20::kPlanTarget);
}

TEST(T20BoundMatrix, EveryLimitBelowOneFailsClosed) {
  // T20-BND-11, CHK-20-05: each of the 13 declared DecodeLimits members set to zero fails closed
  // with XCOM-DECODE-UNKNOWN and returns no decoded plan.
  EXPECT_EQ(t20::kDecodeLimitCount, 13u);
  const std::string document = t20::activatable();
  t20::for_each_limit([&document](const std::string& name, const DecodeLimits& limits) {
    const DecodeResult result = decode_activation_plan(document, limits);
    EXPECT_FALSE(result.plan.has_value()) << name;
    EXPECT_EQ(result.outcome, DecodeOutcome::failed) << name;
    EXPECT_EQ(result.error.code, t20::kCodeUnknown) << name;
    EXPECT_EQ(result.error.target_id, t20::kPlanTarget) << name;
  });
}
