/**
 * @file concurrency_tests.cpp
 * @brief T027 bounded deterministic concurrency: independent guards reproduce the single-threaded
 *        golden decision sequence, concurrent rejections of one guard mutate no state, and
 *        concurrent authorizations against one guard never exceed the declared quota.
 * @ownership Each case owns its permit, policy, guards, joined threads, and recorded sequences.
 * @lifetime Every thread is joined before its guard is destroyed.
 * @thread_safety ≤ 4 threads; one logical writer per guard; each thread writes only its own slot.
 * @bounds `max_actions_per_session` 16 (7 for the quota case); ≤ 4 threads; ≤ 16 evaluations per
 *         thread; 3 repeated runs.
 * @failure A guard sequence or final snapshot that differs from the golden one, an outcome that is
 *          not `Rejected`/`Failed`, a mutating concurrent rejection, or a committed over-quota
 *          authorization fails the case.
 */

#include "xverse/xcom/stimulation_guard.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <thread>
#include <utility>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr std::size_t kThreads = 4U;
constexpr std::size_t kSteps = 16U;

using Decision = std::pair<val::GuardOutcome, val::GuardReason>;

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
  builder.set_validity(kDomain, 0, 100);
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
  policy.max_actions_per_session = 16U;
  policy.max_actions_per_window = 16U;
  policy.action_window = 16U;
  policy.loop_window = 8U;
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

/** Runs the fixed golden sequence of `kSteps` evaluations against one guard. */
[[nodiscard]] std::vector<Decision> run_sequence(val::StimulationGuard &guard, const val::Permit &permit) {
  std::vector<Decision> decisions;
  decisions.reserve(kSteps);
  val::GuardDiagnostic diagnostic;
  for (std::size_t step = 0; step < kSteps; ++step) {
    val::StimulationRequest request = make_request(permit, 400U + step);
    if (step % 4U == 3U) {
      request.schema = val::SchemaKey{tag("sig.v1"), tag("9")};
    }
    const val::GuardOutcome outcome =
        guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic);
    decisions.emplace_back(outcome, diagnostic.reason);
  }
  return decisions;
}

} // namespace

/** T27-TS-019 (CHK-18): four independent guards reproduce the single-threaded golden sequence. */
TEST(XcomStimulationGuardConcurrency, GuardBoundedDeterministicConcurrency) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  std::vector<Decision> golden;
  val::GuardSnapshot golden_snapshot;
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    golden = run_sequence(guard, permit);
    golden_snapshot = guard.snapshot();
  }
  ASSERT_EQ(golden.size(), kSteps);
  EXPECT_EQ(golden_snapshot.evaluations, static_cast<std::uint64_t>(kSteps));
  EXPECT_EQ(golden_snapshot.actions_authorized, 12U);
  EXPECT_EQ(golden_snapshot.loop_entries, 8U);

  for (std::size_t run = 0; run < 3U; ++run) {
    std::array<std::vector<Decision>, kThreads> decisions;
    std::array<val::GuardSnapshot, kThreads> snapshots{};
    std::array<std::thread, kThreads> workers;
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
      workers[worker] = std::thread([&, worker]() {
        val::StimulationGuard guard;
        const val::GuardStatus opened = guard.open(permit, policy);
        EXPECT_EQ(opened, val::GuardStatus::Ok);
        decisions[worker] = run_sequence(guard, permit);
        snapshots[worker] = guard.snapshot();
      });
    }
    for (std::thread &worker : workers) {
      worker.join();
    }
    for (std::size_t worker = 0; worker < kThreads; ++worker) {
      EXPECT_EQ(decisions[worker], golden);
      EXPECT_EQ(snapshots[worker], golden_snapshot);
    }
  }
}

/** T27-TS-020 (CHK-18): concurrent rejections of one guard mutate no operational state. */
TEST(XcomStimulationGuardConcurrency, GuardConcurrentRejectionNoMutation) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  val::StimulationGuard guard;
  ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
  const val::GuardSnapshot before = guard.snapshot();

  std::array<std::vector<val::GuardOutcome>, kThreads> outcomes;
  std::array<std::thread, kThreads> workers;
  for (std::size_t worker = 0; worker < kThreads; ++worker) {
    workers[worker] = std::thread([&, worker]() {
      val::GuardDiagnostic diagnostic;
      for (std::size_t step = 0; step < kSteps; ++step) {
        val::StimulationRequest request = make_request(permit, 500U + worker * kSteps + step);
        request.schema = val::SchemaKey{tag("other.v1"), tag("1")};
        const val::GuardOutcome outcome =
            guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic);
        outcomes[worker].push_back(outcome);
      }
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }

  const val::GuardSnapshot after = guard.snapshot();
  EXPECT_TRUE(operational_equal(before, after));
  EXPECT_EQ(after.actions_authorized, 0U);
  EXPECT_EQ(after.loop_entries, 0U);
  EXPECT_EQ(after.evaluations, static_cast<std::uint64_t>(kThreads * kSteps));
  EXPECT_EQ(after.rejections, static_cast<std::uint64_t>(kThreads * kSteps));
  for (const std::vector<val::GuardOutcome> &worker_outcomes : outcomes) {
    ASSERT_EQ(worker_outcomes.size(), kSteps);
    for (const val::GuardOutcome outcome : worker_outcomes) {
      EXPECT_NE(outcome, val::GuardOutcome::Authorized);
    }
  }
}

/**
 * T27-TS-019 (CHK-18, OBS-03): concurrent authorizations against one guard never exceed the declared
 * per-session quota, and the guard records exactly the quota of committed actions.
 */
TEST(XcomStimulationGuardConcurrency, GuardConcurrentAuthorizationWithinQuota) {
  const val::Permit permit = make_permit();
  val::StimulationPolicy policy = make_policy(permit);
  constexpr std::size_t kQuota = 7U;
  constexpr std::size_t kAttempts = kThreads * kSteps;
  policy.max_actions_per_session = kQuota;
  policy.max_actions_per_window = kQuota;
  policy.action_window = kQuota;
  policy.loop_window = 8U;
  val::StimulationGuard guard;
  ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);

  std::array<std::vector<val::GuardOutcome>, kThreads> outcomes;
  std::array<std::thread, kThreads> workers;
  for (std::size_t worker = 0; worker < kThreads; ++worker) {
    workers[worker] = std::thread([&, worker]() {
      val::GuardDiagnostic diagnostic;
      for (std::size_t step = 0; step < kSteps; ++step) {
        const val::StimulationRequest request = make_request(permit, 600U + worker * kSteps + step);
        const val::GuardOutcome outcome =
            guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic);
        outcomes[worker].push_back(outcome);
      }
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }

  std::size_t authorized = 0U;
  std::size_t rejected = 0U;
  for (const std::vector<val::GuardOutcome> &worker_outcomes : outcomes) {
    ASSERT_EQ(worker_outcomes.size(), kSteps);
    for (const val::GuardOutcome outcome : worker_outcomes) {
      ASSERT_TRUE(outcome == val::GuardOutcome::Authorized || outcome == val::GuardOutcome::Rejected);
      if (outcome == val::GuardOutcome::Authorized) {
        ++authorized;
      } else {
        ++rejected;
      }
    }
  }
  EXPECT_EQ(authorized, kQuota);
  EXPECT_EQ(rejected, kAttempts - kQuota);

  const val::GuardSnapshot after = guard.snapshot();
  EXPECT_EQ(after.actions_authorized, kQuota);
  EXPECT_EQ(after.actions_remaining, 0U);
  EXPECT_EQ(after.evaluations, static_cast<std::uint64_t>(kAttempts));
  EXPECT_EQ(after.rejections, static_cast<std::uint64_t>(kAttempts - kQuota));
  EXPECT_LE(after.loop_entries, policy.loop_window);
}
