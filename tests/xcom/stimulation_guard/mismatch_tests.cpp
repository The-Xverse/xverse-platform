/**
 * @file mismatch_tests.cpp
 * @brief T027 permit/identity/plan, lifecycle, schema/target, action/direction,
 *        service-ownership, quota, and loop matrices.
 * @ownership Each case owns the permit, policy, guard, requests, and snapshot copies it builds.
 * @lifetime One guard per case; requests and snapshots are values.
 * @thread_safety Single-threaded.
 * @bounds Finite declared tables, ≤ 8 evaluations per case.
 * @failure A declared mismatch that is authorized, a matching request that is rejected, or a
 *          rejection that mutates operational state fails the case.
 */

#include "xverse/xcom/stimulation_guard.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr val::Timestamp kFrom = 0;
constexpr val::Timestamp kUntil = 100;

[[nodiscard]] val::SessionId session_a() {
  val::SessionId value{};
  value[0] = 1U;
  value[15] = 0x11U;
  return value;
}
[[nodiscard]] val::PlanDigest digest_a() {
  val::PlanDigest value{};
  value[0] = 2U;
  value[31] = 0x22U;
  return value;
}
[[nodiscard]] val::Tag tag(std::string_view text) { return val::Tag::make(text).value(); }

[[nodiscard]] val::Permit make_permit() {
  val::PermitBuilder builder;
  builder.set_session_id(session_a());
  builder.set_plan_digest(digest_a());
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
  policy.allowed_schemas = {val::SchemaKey{tag("sig.v1"), tag("1")},
                            val::SchemaKey{tag("msg.v1"), tag("1")}};
  policy.max_actions_per_session = 8U;
  policy.max_actions_per_window = 8U;
  policy.action_window = 8U;
  policy.loop_window = 4U;
  policy.allow_service_emulation = true;
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

[[nodiscard]] val::ResolvedTime in_window() {
  return val::ResolvedTime{kDomain, 50, val::Result::Ok};
}

[[nodiscard]] bool operational_equal(const val::GuardSnapshot &lhs,
                                     const val::GuardSnapshot &rhs) {
  return lhs.open == rhs.open && lhs.actions_authorized == rhs.actions_authorized &&
         lhs.actions_remaining == rhs.actions_remaining && lhs.window_actions == rhs.window_actions &&
         lhs.window_remaining == rhs.window_remaining && lhs.loop_entries == rhs.loop_entries;
}

void after_rejection(val::StimulationGuard &guard, const val::StimulationRequest &request) {
  const val::GuardSnapshot before = guard.snapshot();
  val::GuardDiagnostic diagnostic;
  const val::GuardOutcome outcome =
      guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic);
  EXPECT_NE(outcome, val::GuardOutcome::Authorized);
  EXPECT_TRUE(operational_equal(before, guard.snapshot()));
}

} // namespace

/** T27-TS-006 (CHK-16): every identity/plan row of detailed-design §5.6. */
TEST(XcomStimulationGuardMismatch, GuardIdentityAndPlanMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  val::StimulationGuard guard;
  ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
  val::GuardDiagnostic diagnostic;

  EXPECT_EQ(guard.authorize(make_request(permit, 31U), val::LifecycleState::active, in_window(),
                            diagnostic),
            val::GuardOutcome::Authorized);

  val::StimulationRequest foreign_session = make_request(permit, 32U);
  foreign_session.session_id[0] = 0xEEU;
  ASSERT_EQ(guard.authorize(foreign_session, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::PermitMismatch);

  val::StimulationRequest foreign_permit = make_request(permit, 33U);
  foreign_permit.permit_id[0] ^= 0xFFU;
  ASSERT_EQ(guard.authorize(foreign_permit, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::PermitMismatch);

  val::StimulationRequest foreign_plan = make_request(permit, 34U);
  foreign_plan.plan_digest[1] ^= 0xFFU;
  ASSERT_EQ(guard.authorize(foreign_plan, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::PermitMismatch);

  val::StimulationPolicy inconsistent = policy;
  inconsistent.plan_digest[0] ^= 0xFFU;
  val::StimulationGuard other;
  EXPECT_EQ(other.open(permit, inconsistent), val::GuardStatus::RejectedConfiguration);
}

/** T27-TS-007 (CHK-07): every lifecycle row of detailed-design §5.2. */
TEST(XcomStimulationGuardMismatch, GuardLifecycleMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  constexpr std::array<std::pair<val::LifecycleState, val::GuardReason>, 8U> rows{{
      {val::LifecycleState::active, val::GuardReason::None},
      {val::LifecycleState::revoked, val::GuardReason::Revoked},
      {val::LifecycleState::expired, val::GuardReason::Expired},
      {val::LifecycleState::declared, val::GuardReason::NotActive},
      {val::LifecycleState::armed, val::GuardReason::NotActive},
      {val::LifecycleState::closing, val::GuardReason::NotActive},
      {val::LifecycleState::closed, val::GuardReason::NotActive},
      {val::LifecycleState::evidence_incomplete, val::GuardReason::NotActive},
  }};
  for (std::size_t index = 0; index < rows.size(); ++index) {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    const val::GuardSnapshot before = guard.snapshot();
    val::GuardDiagnostic diagnostic;
    const val::GuardOutcome outcome =
        guard.authorize(make_request(permit, 40U + index), rows[index].first, in_window(), diagnostic);
    EXPECT_EQ(diagnostic.reason, rows[index].second);
    EXPECT_EQ(outcome, rows[index].second == val::GuardReason::None ? val::GuardOutcome::Authorized
                                                                    : val::GuardOutcome::Rejected);
    if (rows[index].second != val::GuardReason::None) {
      EXPECT_TRUE(operational_equal(before, guard.snapshot()));
    }
  }
}

/** T27-TS-008 (CHK-08): declared/undeclared schema, invalid schema tags, target/interface. */
TEST(XcomStimulationGuardMismatch, GuardSchemaAndTargetMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  val::StimulationGuard guard;
  ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
  val::GuardDiagnostic diagnostic;

  EXPECT_EQ(guard.authorize(make_request(permit, 51U), val::LifecycleState::active, in_window(),
                            diagnostic),
            val::GuardOutcome::Authorized);

  val::StimulationRequest undeclared = make_request(permit, 52U);
  undeclared.schema = val::SchemaKey{tag("other.v1"), tag("1")};
  after_rejection(guard, undeclared);
  ASSERT_EQ(guard.authorize(undeclared, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::SchemaMismatch);

  val::StimulationRequest empty_id = make_request(permit, 53U);
  empty_id.schema = val::SchemaKey{val::Tag{}, tag("1")};
  ASSERT_EQ(guard.authorize(empty_id, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::SchemaMismatch);

  val::StimulationRequest over_long = make_request(permit, 54U);
  over_long.schema = val::SchemaKey{val::Tag(std::string(64U, 'x')), tag("1")};
  ASSERT_EQ(guard.authorize(over_long, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::SchemaMismatch);

  val::StimulationRequest bad_target = make_request(permit, 55U);
  bad_target.target = tag("target.beta");
  after_rejection(guard, bad_target);
  ASSERT_EQ(guard.authorize(bad_target, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::TargetMismatch);

  val::StimulationRequest bad_interface = make_request(permit, 56U);
  bad_interface.interface_tag = tag("iface.other");
  ASSERT_EQ(guard.authorize(bad_interface, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::TargetMismatch);
}

/** T27-TS-009 (CHK-09): defined-action-not-allowed and policy-exclusion rows. */
TEST(XcomStimulationGuardMismatch, GuardActionDirectionMatrix) {
  const val::Permit permit = make_permit();
  val::StimulationPolicy policy = make_policy(permit);
  policy.allowed_actions = val::to_stimulation_mask(val::StimulationAction::InjectSignal);
  policy.allowed_interactions = 0x03U;
  policy.allowed_directions = 0x01U;
  val::StimulationGuard guard;
  ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
  val::GuardDiagnostic diagnostic;

  EXPECT_EQ(guard.authorize(make_request(permit, 61U), val::LifecycleState::active, in_window(),
                            diagnostic),
            val::GuardOutcome::Authorized);

  val::StimulationRequest disallowed = make_request(permit, 62U);
  disallowed.action = val::StimulationAction::InjectMessage;
  disallowed.interaction = InteractionKind::message_event;
  disallowed.direction = EndpointDirection::produce;
  ASSERT_EQ(guard.authorize(disallowed, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::ActionMismatch);

  val::StimulationRequest excluded_interaction = make_request(permit, 63U);
  excluded_interaction.interaction = InteractionKind::message_event;
  ASSERT_EQ(guard.authorize(excluded_interaction, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::InteractionMismatch);

  val::StimulationRequest excluded_direction = make_request(permit, 64U);
  excluded_direction.direction = EndpointDirection::consume;
  ASSERT_EQ(guard.authorize(excluded_direction, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::DirectionMismatch);

  val::StimulationRequest zero_action = make_request(permit, 65U);
  zero_action.action = static_cast<val::StimulationAction>(0U);
  ASSERT_EQ(guard.authorize(zero_action, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::RejectedConfiguration);

  val::StimulationRequest composite_action = make_request(permit, 66U);
  composite_action.action = static_cast<val::StimulationAction>(0x05U);
  ASSERT_EQ(guard.authorize(composite_action, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::RejectedConfiguration);

  // A single undefined action bit is out-of-vocabulary and must be classified as malformed at
  // rank 1 (`RejectedConfiguration`), not fall through to the rank-7 direction check.
  val::StimulationRequest undefined_action = make_request(permit, 67U);
  undefined_action.action = static_cast<val::StimulationAction>(0x10U);
  const val::GuardSnapshot before_undefined = guard.snapshot();
  ASSERT_EQ(guard.authorize(undefined_action, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::RejectedConfiguration);
  EXPECT_TRUE(operational_equal(before_undefined, guard.snapshot()));
}

/** T27-TS-010 (CHK-11): declared/missing/mismatched owner and generation. */
TEST(XcomStimulationGuardMismatch, GuardServiceOwnershipMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  const auto service_request = [&](std::uint64_t id, val::StimulationAction action) {
    val::StimulationRequest request = make_request(permit, id);
    request.action = action;
    if (action == val::StimulationAction::InvokeService) {
      request.interaction = InteractionKind::service_request;
      request.direction = EndpointDirection::request;
    } else {
      request.interaction = InteractionKind::service_response;
      request.direction = EndpointDirection::respond;
    }
    request.service_owner = policy.service_owner;
    return request;
  };

  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    EXPECT_EQ(guard.authorize(service_request(71U, val::StimulationAction::InvokeService),
                              val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.authorize(service_request(72U, val::StimulationAction::EmulateService),
                              val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Authorized);
    val::StimulationRequest inject = make_request(permit, 73U);
    EXPECT_EQ(guard.authorize(inject, val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Authorized);
  }

  const auto rejects_ownership = [&](std::uint64_t id, val::StimulationAction action,
                                     const val::StimulationPolicy &bound_policy,
                                     const val::ServiceOwner &owner) {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, bound_policy), val::GuardStatus::Ok);
    val::StimulationRequest request = service_request(id, action);
    request.service_owner = owner;
    val::GuardDiagnostic diagnostic;
    ASSERT_EQ(guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::OwnershipConflict);
  };

  rejects_ownership(74U, val::StimulationAction::InvokeService, policy, val::ServiceOwner{});
  rejects_ownership(75U, val::StimulationAction::InvokeService, policy,
                    val::ServiceOwner{tag("svc.alpha"), 4U, true});
  rejects_ownership(76U, val::StimulationAction::InvokeService, policy,
                    val::ServiceOwner{tag("svc.beta"), 3U, true});
  {
    val::StimulationPolicy no_owner = make_policy(permit);
    no_owner.service_owner.declared = false;
    no_owner.allow_service_emulation = false;
    no_owner.allowed_actions = val::to_stimulation_mask(val::StimulationAction::InjectSignal) |
                               val::to_stimulation_mask(val::StimulationAction::InjectMessage) |
                               val::to_stimulation_mask(val::StimulationAction::InvokeService);
    rejects_ownership(77U, val::StimulationAction::InvokeService, no_owner, policy.service_owner);
  }
  {
    val::StimulationPolicy no_emulation = make_policy(permit);
    no_emulation.allow_service_emulation = false;
    rejects_ownership(78U, val::StimulationAction::EmulateService, no_emulation, no_emulation.service_owner);
  }
}

/** T27-TS-011 (CHK-10): per-session and per-window quota rows of detailed-design §5.4. */
TEST(XcomStimulationGuardMismatch, GuardQuotaMatrix) {
  const val::Permit permit = make_permit();

  // Per-session budget isolates: the window resets every action, so only the session budget binds.
  {
    val::StimulationPolicy policy = make_policy(permit);
    policy.max_actions_per_session = 2U;
    policy.max_actions_per_window = 2U;
    policy.action_window = 1U;
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    EXPECT_EQ(guard.authorize(make_request(permit, 81U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.authorize(make_request(permit, 82U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    const val::GuardSnapshot before = guard.snapshot();
    ASSERT_EQ(guard.authorize(make_request(permit, 83U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::QuotaExhausted);
    EXPECT_TRUE(operational_equal(before, guard.snapshot()));
  }

  // Per-window budget isolates: the window never resets within the tested count.
  {
    val::StimulationPolicy policy = make_policy(permit);
    policy.max_actions_per_session = 4U;
    policy.max_actions_per_window = 2U;
    policy.action_window = 4U;
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    EXPECT_EQ(guard.authorize(make_request(permit, 84U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.authorize(make_request(permit, 85U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    ASSERT_EQ(guard.authorize(make_request(permit, 86U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::QuotaExhausted);
  }

  // The window tally resets at `action_window`, and only `Authorized` advances it.
  {
    val::StimulationPolicy policy = make_policy(permit);
    policy.max_actions_per_session = 4U;
    policy.max_actions_per_window = 2U;
    policy.action_window = 2U;
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    EXPECT_EQ(guard.authorize(make_request(permit, 87U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.snapshot().window_actions, 1U);
    EXPECT_EQ(guard.authorize(make_request(permit, 88U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.snapshot().window_actions, 0U);
    EXPECT_EQ(guard.authorize(make_request(permit, 89U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.snapshot().window_actions, 1U);
  }
}

/** T27-TS-012 (CHK-12): prohibited reinjection, zero causation, and window depth/eviction. */
TEST(XcomStimulationGuardMismatch, GuardLoopBoundMatrix) {
  const val::Permit permit = make_permit();
  val::StimulationPolicy policy = make_policy(permit);
  policy.loop_window = 2U;
  val::StimulationGuard guard;
  ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
  val::GuardDiagnostic diagnostic;

  EXPECT_EQ(guard.authorize(make_request(permit, 101U), val::LifecycleState::active, in_window(),
                            diagnostic),
            val::GuardOutcome::Authorized);

  val::StimulationRequest reinjection = make_request(permit, 102U);
  reinjection.causation_id = 101U;
  const val::GuardSnapshot before = guard.snapshot();
  ASSERT_EQ(guard.authorize(reinjection, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::LoopBound);
  EXPECT_TRUE(operational_equal(before, guard.snapshot()));
  EXPECT_EQ(guard.snapshot().loop_entries, 1U);

  val::StimulationRequest zero_causation = make_request(permit, 103U);
  zero_causation.causation_id = 0U;
  EXPECT_EQ(guard.authorize(zero_causation, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Authorized);
  EXPECT_EQ(guard.snapshot().loop_entries, 2U);

  val::StimulationRequest third = make_request(permit, 104U);
  EXPECT_EQ(guard.authorize(third, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Authorized);
  EXPECT_EQ(guard.snapshot().loop_entries, 2U);

  val::StimulationRequest evicted_parent = make_request(permit, 105U);
  evicted_parent.causation_id = 101U;
  EXPECT_EQ(guard.authorize(evicted_parent, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Authorized);

  val::StimulationRequest recent_parent = make_request(permit, 106U);
  recent_parent.causation_id = 104U;
  ASSERT_EQ(guard.authorize(recent_parent, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::LoopBound);
}
