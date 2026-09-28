/**
 * @file time_tests.cpp
 * @brief T027 pre-emission time-policy checks: scheduled window, unmapped-clock fail-closed, and
 *        immediate labeling. The guard performs no time-authority call and no raw-clock compare.
 * @ownership Each case owns the permit, policy, guard, requests, and resolved-time values.
 * @lifetime One guard per case; resolved-time values are supplied per evaluation.
 * @thread_safety Single-threaded.
 * @bounds Validity interval [0, 100); ≤ 6 rows per case; finite declared tables.
 * @failure An in-window request that is rejected, an out-of-window request that is authorized, a
 *          non-`Ok` resolution that is not `Failed`/`TimeUnmapped`, or a rejection that mutates
 *          state fails the case.
 */

#include "xverse/xcom/stimulation_guard.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <utility>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr val::Timestamp kFrom = 0;
constexpr val::Timestamp kUntil = 100;

[[nodiscard]] val::Tag tag(std::string_view text) { return val::Tag::make(text).value(); }

[[nodiscard]] val::Permit make_permit() {
  val::PermitBuilder builder;
  val::SessionId session{};
  session[0] = 1U;
  val::PlanDigest digest{};
  digest[0] = 2U;
  builder.set_session_id(session);
  builder.set_plan_digest(digest);
  builder.set_scenario("scenario");
  builder.set_deployment("deployment");
  builder.set_environment("environment");
  builder.set_tool("tool");
  builder.set_interface("iface.v1");
  builder.set_target("target.alpha");
  builder.set_nonce(1U);
  builder.set_validity(kDomain, kFrom, kUntil);
  builder.add_allowed_action(val::to_mask(val::Action::Activate));
  builder.add_quota(val::Quota{val::QuotaKind::Operations, 16U});
  val::Permit permit;
  const val::Result result = builder.build(permit);
  EXPECT_EQ(result, val::Result::Ok);
  return permit;
}

[[nodiscard]] val::StimulationPolicy make_policy(const val::Permit &permit) {
  val::StimulationPolicy policy;
  policy.plan_digest = permit.plan_digest();
  policy.interface_tag = tag("iface.v1");
  policy.target = tag("target.alpha");
  policy.validity_domain = permit.validity_domain();
  policy.allowed_actions = val::kDefinedStimulationActions;
  policy.allowed_interactions = 0x0FU;
  policy.allowed_directions = 0x0FU;
  policy.allowed_schemas = {val::SchemaKey{tag("sig.v1"), tag("1")}};
  policy.max_actions_per_session = 8U;
  policy.max_actions_per_window = 8U;
  policy.action_window = 8U;
  policy.loop_window = 4U;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return policy;
}

[[nodiscard]] val::StimulationRequest make_request(const val::Permit &permit, std::uint64_t id) {
  val::StimulationRequest request;
  request.permit_id = permit.permit_id();
  request.session_id = permit.session_id();
  request.plan_digest = permit.plan_digest();
  request.action = val::StimulationAction::InjectSignal;
  request.interaction = InteractionKind::signal_state_update;
  request.direction = EndpointDirection::produce;
  request.schema = val::SchemaKey{tag("sig.v1"), tag("1")};
  request.target = tag("target.alpha");
  request.interface_tag = tag("iface.v1");
  request.clock_domain = kDomain;
  request.immediate = false;
  request.request_id = id;
  return request;
}

[[nodiscard]] bool operational_equal(const val::GuardSnapshot &lhs,
                                     const val::GuardSnapshot &rhs) {
  return lhs.open == rhs.open && lhs.actions_authorized == rhs.actions_authorized &&
         lhs.actions_remaining == rhs.actions_remaining && lhs.window_actions == rhs.window_actions &&
         lhs.window_remaining == rhs.window_remaining && lhs.loop_entries == rhs.loop_entries;
}

} // namespace

/** T27-TS-013 (CHK-13): scheduled in-window and out-of-window rows of detailed-design §5.5. */
TEST(XcomStimulationGuardTime, GuardScheduledTimeWindowMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  constexpr std::array<std::pair<val::Timestamp, val::GuardOutcome>, 4U> rows{{
      {0, val::GuardOutcome::Authorized},
      {99, val::GuardOutcome::Authorized},
      {100, val::GuardOutcome::Rejected},
      {-1, val::GuardOutcome::Rejected},
  }};
  for (std::size_t index = 0; index < rows.size(); ++index) {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    const val::ResolvedTime resolved{kDomain, rows[index].first, val::Result::Ok};
    const val::GuardOutcome outcome =
        guard.authorize(make_request(permit, 201U + index), val::LifecycleState::active, resolved, diagnostic);
    EXPECT_EQ(outcome, rows[index].second);
    if (outcome == val::GuardOutcome::Rejected) {
      EXPECT_EQ(diagnostic.reason, val::GuardReason::TimeOutOfWindow);
    }
  }
}

/** T27-TS-014 (CHK-13): every non-`Ok` resolution and a domain mismatch fail closed. */
TEST(XcomStimulationGuardTime, GuardUnmappedClockFailsClosed) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  constexpr std::array<std::pair<val::ClockDomainId, val::Result>, 6U> rows{{
      {kDomain, val::Result::UnknownClock},
      {kDomain, val::Result::MissingMapping},
      {kDomain, val::Result::ToleranceExceeded},
      {kDomain, val::Result::ClockSourceFailure},
      {kDomain, val::Result::ClockRegression},
      {kDomain + 9U, val::Result::Ok},
  }};
  for (std::size_t index = 0; index < rows.size(); ++index) {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    const val::GuardSnapshot before = guard.snapshot();
    val::GuardDiagnostic diagnostic;
    const val::ResolvedTime resolved{rows[index].first, 50, rows[index].second};
    ASSERT_EQ(guard.authorize(make_request(permit, 210U + index), val::LifecycleState::active, resolved,
                              diagnostic),
              val::GuardOutcome::Failed);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::TimeUnmapped);
    EXPECT_TRUE(operational_equal(before, guard.snapshot()));
    EXPECT_EQ(guard.snapshot().failures, before.failures + 1U);
  }
}

/** T27-TS-015 (CHK-13): the immediate-labeling rows of detailed-design §5.5. */
TEST(XcomStimulationGuardTime, GuardImmediateLabelingMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::StimulationRequest request = make_request(permit, 221U);
    request.immediate = true;
    request.clock_domain = kDomain;
    val::GuardDiagnostic diagnostic;
    EXPECT_EQ(guard.authorize(request, val::LifecycleState::active,
                              val::ResolvedTime{kDomain, 50, val::Result::Ok}, diagnostic),
              val::GuardOutcome::Authorized);
  }
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::StimulationRequest request = make_request(permit, 222U);
    request.immediate = true;
    request.clock_domain = kDomain + 5U;
    val::GuardDiagnostic diagnostic;
    ASSERT_EQ(guard.authorize(request, val::LifecycleState::active,
                              val::ResolvedTime{kDomain, 50, val::Result::Ok}, diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::RejectedConfiguration);
  }
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::StimulationRequest request = make_request(permit, 223U);
    request.immediate = false;
    request.clock_domain = val::kInvalidClockDomain;
    val::GuardDiagnostic diagnostic;
    ASSERT_EQ(guard.authorize(request, val::LifecycleState::active,
                              val::ResolvedTime{kDomain, 50, val::Result::Ok}, diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::RejectedConfiguration);
  }
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::StimulationRequest request = make_request(permit, 224U);
    request.immediate = true;
    request.clock_domain = kDomain;
    val::GuardDiagnostic diagnostic;
    ASSERT_EQ(guard.authorize(request, val::LifecycleState::active,
                              val::ResolvedTime{kDomain, 100, val::Result::Ok}, diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::TimeOutOfWindow);
  }
}
