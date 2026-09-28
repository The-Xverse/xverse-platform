/**
 * @file unit_tests.cpp
 * @brief T027 nominal authorisation, action/interaction/direction table, closed vocabulary,
 *        determinism, and policy/open validation matrix.
 * @ownership Each case owns the permit, policy, guard, requests, and snapshots it constructs.
 * @lifetime Permit and policy outlive the guard; snapshots are value copies.
 * @thread_safety Single-threaded.
 * @bounds Finite declared tables, ≤ 9 policy rows, ≤ 12 action rows, ≤ 8 evaluations per run.
 * @failure A nominal request that is not `Authorized`/`None`, an unstable vocabulary entry, a run
 *          that is not byte-identical to its predecessor, or an accepted invalid policy fails.
 */

#include "xverse/xcom/stimulation_guard.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <utility>
#include <vector>

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
[[nodiscard]] val::Tag tag(std::string_view text) {
  return val::Tag::make(text).value();
}

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
  policy.max_actions_per_window = 4U;
  policy.action_window = 4U;
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

void open_ok(val::StimulationGuard &guard, const val::Permit &permit,
             const val::StimulationPolicy &policy) {
  EXPECT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
}

} // namespace

/** T27-TS-001 (CHK-04, CHK-14): a consistent guard authorizes each action kind and commits. */
TEST(XcomStimulationGuardUnit, GuardAuthorizesNominalRequestAndSnapshot) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  val::StimulationGuard guard;
  open_ok(guard, permit, policy);
  EXPECT_TRUE(guard.is_open());
  EXPECT_EQ(guard.snapshot(), (val::GuardSnapshot{true, 0U, 8U, 0U, 4U, 0U, 0U, 0U, 0U}));

  val::GuardDiagnostic diagnostic;
  EXPECT_EQ(guard.authorize(make_request(permit, 11U), val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Authorized);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::None);
  EXPECT_EQ(guard.snapshot(), (val::GuardSnapshot{true, 1U, 7U, 1U, 3U, 1U, 1U, 0U, 0U}));

  for (std::uint64_t id = 12U; id <= 13U; ++id) {
    EXPECT_EQ(guard.authorize(make_request(permit, id), val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Authorized);
  }
  EXPECT_EQ(guard.snapshot(), (val::GuardSnapshot{true, 3U, 5U, 3U, 1U, 3U, 3U, 0U, 0U}));
}

/** T27-TS-002 (CHK-09): every row of detailed-design §5.3. */
TEST(XcomStimulationGuardUnit, GuardActionInteractionDirectionTable) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  val::StimulationGuard guard;
  open_ok(guard, permit, policy);
  val::GuardDiagnostic diagnostic;

  const auto decide = [&](val::StimulationRequest request) {
    return guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic);
  };

  EXPECT_EQ(decide(make_request(permit, 21U)), val::GuardOutcome::Authorized);

  val::StimulationRequest message = make_request(permit, 22U);
  message.action = val::StimulationAction::InjectMessage;
  message.interaction = InteractionKind::message_event;
  message.direction = EndpointDirection::produce;
  EXPECT_EQ(decide(message), val::GuardOutcome::Authorized);

  val::StimulationRequest invoke = make_request(permit, 23U);
  invoke.action = val::StimulationAction::InvokeService;
  invoke.interaction = InteractionKind::service_request;
  invoke.direction = EndpointDirection::request;
  invoke.service_owner = policy.service_owner;
  EXPECT_EQ(decide(invoke), val::GuardOutcome::Authorized);

  val::StimulationRequest emulate = make_request(permit, 24U);
  emulate.action = val::StimulationAction::EmulateService;
  emulate.interaction = InteractionKind::service_response;
  emulate.direction = EndpointDirection::respond;
  emulate.service_owner = policy.service_owner;
  EXPECT_EQ(decide(emulate), val::GuardOutcome::Authorized);

  val::StimulationRequest bad_interaction = make_request(permit, 25U);
  bad_interaction.interaction = InteractionKind::message_event;
  EXPECT_EQ(decide(bad_interaction), val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::InteractionMismatch);

  val::StimulationRequest bad_direction = make_request(permit, 26U);
  bad_direction.direction = EndpointDirection::consume;
  EXPECT_EQ(decide(bad_direction), val::GuardOutcome::Rejected);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::DirectionMismatch);
}

/** T27-TS-003 (CHK-17): closed vocabularies, stable names, ranks, and total `outcome_of`. */
TEST(XcomStimulationGuardUnit, GuardClosedVocabularyAndPrecedence) {
  constexpr std::array<val::GuardReason, 17U> reasons{
      val::GuardReason::NotOpen,          val::GuardReason::RejectedConfiguration,
      val::GuardReason::PermitMismatch,   val::GuardReason::Revoked,
      val::GuardReason::Expired,          val::GuardReason::NotActive,
      val::GuardReason::SchemaMismatch,   val::GuardReason::DirectionMismatch,
      val::GuardReason::InteractionMismatch, val::GuardReason::TargetMismatch,
      val::GuardReason::ActionMismatch,   val::GuardReason::OwnershipConflict,
      val::GuardReason::QuotaExhausted,   val::GuardReason::LoopBound,
      val::GuardReason::TimeOutOfWindow,  val::GuardReason::TimeUnmapped,
      val::GuardReason::None};
  constexpr std::array<std::string_view, 17U> reason_names{
      "NotOpen", "RejectedConfiguration", "PermitMismatch", "Revoked", "Expired", "NotActive",
      "SchemaMismatch", "DirectionMismatch", "InteractionMismatch", "TargetMismatch",
      "ActionMismatch", "OwnershipConflict", "QuotaExhausted", "LoopBound", "TimeOutOfWindow",
      "TimeUnmapped", "None"};
  constexpr std::array<val::GuardOutcome, 17U> outcomes{
      val::GuardOutcome::Failed,    val::GuardOutcome::Rejected, val::GuardOutcome::Rejected,
      val::GuardOutcome::Rejected,  val::GuardOutcome::Rejected, val::GuardOutcome::Rejected,
      val::GuardOutcome::Rejected,  val::GuardOutcome::Rejected, val::GuardOutcome::Rejected,
      val::GuardOutcome::Rejected,  val::GuardOutcome::Rejected, val::GuardOutcome::Rejected,
      val::GuardOutcome::Rejected,  val::GuardOutcome::Rejected, val::GuardOutcome::Rejected,
      val::GuardOutcome::Failed,    val::GuardOutcome::Authorized};

  for (std::size_t index = 0; index < reasons.size(); ++index) {
    EXPECT_EQ(val::precedence_rank(reasons[index]), static_cast<std::uint8_t>(index));
    EXPECT_EQ(val::reason_name(reasons[index]), reason_names[index]);
    EXPECT_EQ(val::outcome_of(reasons[index]), outcomes[index]);
  }
  EXPECT_EQ(val::reason_name(static_cast<val::GuardReason>(200U)), std::string_view{});
  EXPECT_EQ(val::precedence_rank(val::GuardReason::NotOpen), std::uint8_t{0});
  EXPECT_EQ(val::precedence_rank(val::GuardReason::None), std::uint8_t{16});

  EXPECT_EQ(val::outcome_name(val::GuardOutcome::Authorized), "Authorized");
  EXPECT_EQ(val::outcome_name(val::GuardOutcome::Rejected), "Rejected");
  EXPECT_EQ(val::outcome_name(val::GuardOutcome::Failed), "Failed");
  EXPECT_EQ(val::guard_status_name(val::GuardStatus::Ok), "Ok");
  EXPECT_EQ(val::guard_status_name(val::GuardStatus::RejectedConfiguration), "RejectedConfiguration");
  EXPECT_EQ(val::guard_status_name(val::GuardStatus::NotOpen), "NotOpen");

  EXPECT_EQ(val::stimulation_action_name(val::to_stimulation_mask(val::StimulationAction::InjectSignal)),
            "InjectSignal");
  EXPECT_EQ(val::stimulation_action_name(val::to_stimulation_mask(val::StimulationAction::InjectMessage)),
            "InjectMessage");
  EXPECT_EQ(val::stimulation_action_name(val::to_stimulation_mask(val::StimulationAction::InvokeService)),
            "InvokeService");
  EXPECT_EQ(val::stimulation_action_name(val::to_stimulation_mask(val::StimulationAction::EmulateService)),
            "EmulateService");
  EXPECT_EQ(val::stimulation_action_name(0U), std::string_view{});
  EXPECT_EQ(val::stimulation_action_name(0x0FU), std::string_view{});
  EXPECT_TRUE(val::is_defined_stimulation_action(0x0FU));
  EXPECT_FALSE(val::is_defined_stimulation_action(0U));
  EXPECT_FALSE(val::is_defined_stimulation_action(0x10U));
  EXPECT_TRUE(val::is_single_stimulation_action(0x04U));
  EXPECT_FALSE(val::is_single_stimulation_action(0x05U));
}

/** T27-TS-004 (CHK-17): three repeated runs are identical; a rejection mutates nothing. */
TEST(XcomStimulationGuardUnit, GuardStatusDeterminismAndNoMutation) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  std::vector<std::pair<val::GuardOutcome, val::GuardReason>> golden;
  val::GuardSnapshot golden_snapshot;
  for (std::size_t run = 0; run < 3U; ++run) {
    val::StimulationGuard guard;
    open_ok(guard, permit, policy);
    std::vector<std::pair<val::GuardOutcome, val::GuardReason>> sequence;
    val::GuardDiagnostic diagnostic;
    for (std::uint64_t step = 0; step < 8U; ++step) {
      val::StimulationRequest request = make_request(permit, 100U + step);
      if (step == 3U) {
        request.schema = val::SchemaKey{tag("sig.v1"), tag("9")};
      }
      const val::GuardOutcome outcome =
          guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic);
      sequence.emplace_back(outcome, diagnostic.reason);
    }
    if (run == 0U) {
      golden = sequence;
      golden_snapshot = guard.snapshot();
    } else {
      EXPECT_EQ(sequence, golden);
      EXPECT_EQ(guard.snapshot(), golden_snapshot);
    }
  }

  val::StimulationGuard guard;
  open_ok(guard, permit, policy);
  val::GuardDiagnostic diagnostic;
  ASSERT_EQ(guard.authorize(make_request(permit, 7U), val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Authorized);
  const val::GuardSnapshot before = guard.snapshot();
  val::StimulationRequest rejected = make_request(permit, 8U);
  rejected.target = tag("target.beta");
  ASSERT_EQ(guard.authorize(rejected, val::LifecycleState::active, in_window(), diagnostic),
            val::GuardOutcome::Rejected);
  const val::GuardSnapshot after = guard.snapshot();
  EXPECT_TRUE(operational_equal(before, after));
  EXPECT_EQ(after.evaluations, before.evaluations + 1U);
  EXPECT_EQ(after.rejections, before.rejections + 1U);
}

/** T27-TS-005 (CHK-06): every policy/open row of detailed-design §5.1. */
TEST(XcomStimulationGuardUnit, GuardPolicyValidationMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy base = make_policy(permit);

  const auto rejects = [&](const val::StimulationPolicy &policy) {
    val::StimulationGuard guard;
    EXPECT_EQ(guard.open(permit, policy), val::GuardStatus::RejectedConfiguration);
    EXPECT_FALSE(guard.is_open());
    EXPECT_EQ(guard.status(), val::GuardStatus::NotOpen);
    EXPECT_EQ(guard.snapshot(), (val::GuardSnapshot{}));
  };

  {
    val::StimulationGuard guard;
    EXPECT_EQ(guard.open(permit, base), val::GuardStatus::Ok);
  }
  { auto policy = base; policy.allowed_actions = 0U; rejects(policy); }
  { auto policy = base; policy.loop_window = 0U; rejects(policy); }
  { auto policy = base; policy.loop_window = val::kGuardMaxLoopWindow + 1U; rejects(policy); }
  { auto policy = base; policy.max_actions_per_session = 0U; rejects(policy); }
  { auto policy = base; policy.max_actions_per_session = val::kGuardMaxActionsPerSession + 1U; rejects(policy); }
  { auto policy = base; policy.max_actions_per_window = base.max_actions_per_session + 1U; rejects(policy); }
  { auto policy = base; policy.action_window = 0U; rejects(policy); }
  { auto policy = base; policy.action_window = val::kGuardMaxActionsPerWindow + 1U; rejects(policy); }
  { auto policy = base; policy.allowed_schemas.clear(); rejects(policy); }
  {
    auto policy = base;
    policy.allowed_schemas.assign(val::kGuardMaxSchemas + 1U, val::SchemaKey{tag("s.v1"), tag("1")});
    rejects(policy);
  }
  {
    auto policy = base;
    policy.allowed_schemas = {val::SchemaKey{val::Tag{}, tag("1")}};
    rejects(policy);
  }
  { auto policy = base; policy.plan_digest[0] ^= 0xFFU; rejects(policy); }
  { auto policy = base; policy.interface_tag = tag("iface.other"); rejects(policy); }
  { auto policy = base; policy.target = tag("target.other"); rejects(policy); }
  { auto policy = base; policy.validity_domain = kDomain + 1U; rejects(policy); }
  {
    auto policy = base;
    policy.service_owner.declared = false;
    rejects(policy);
  }
}
