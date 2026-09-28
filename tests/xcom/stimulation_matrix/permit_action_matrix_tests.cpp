/**
 * @file permit_action_matrix_tests.cpp
 * @brief T029 complete permit/action mismatch matrix: every request-evaluation guard reason, the
 *        lifecycle-state preconditions and closed guard, quota commitment, loop/lineage bounds,
 *        and unmapped/out-of-tolerance clocks.
 * @ownership Each case owns the fixture, its requests, its direct guard, and its snapshots.
 * @lifetime The fixture outlives each request; snapshots are value copies.
 * @thread_safety Single-threaded.
 * @bounds <= 16 mismatch rows, <= 16 evaluations, no wall-clock verdict.
 * @failure Any row that emits, journals, or returns a different status/reason fails the case.
 */

#include "test_support.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;
using xverse::xcom::stimulation_matrix_test::digest_a;
using xverse::xcom::stimulation_matrix_test::in_window;
using xverse::xcom::stimulation_matrix_test::kDomain;
using xverse::xcom::stimulation_matrix_test::kForeignDomain;
using xverse::xcom::stimulation_matrix_test::kUntil;
using xverse::xcom::stimulation_matrix_test::make_config;
using xverse::xcom::stimulation_matrix_test::make_permit;
using xverse::xcom::stimulation_matrix_test::make_policy;
using xverse::xcom::stimulation_matrix_test::make_request;
using xverse::xcom::stimulation_matrix_test::MatrixFixture;
using xverse::xcom::stimulation_matrix_test::out_of_window;
using xverse::xcom::stimulation_matrix_test::session_a;
using xverse::xcom::stimulation_matrix_test::tag;
using xverse::xcom::stimulation_matrix_test::unmapped;

namespace {

/// @brief Asserts one declined execution with zero emission, zero journal append, and no lease
///        mutation, preserving the declared status and guard reason.
/// @param fixture The owned fixture.
/// @param request The declared request.
/// @param state Caller-supplied session state.
/// @param time Caller-resolved time.
/// @param status Declared action status.
/// @param reason Declared guard reason.
/// @param payload Optional call-scoped payload view.
void expect_decline(MatrixFixture &fixture, const val::StimulationRequest &request,
                    val::LifecycleState state, const val::ResolvedTime &time,
                    val::ActionStatus status, val::GuardReason reason,
                    std::span<const std::byte> payload = {}) {
  const std::size_t before_calls = fixture.emitter.calls.load();
  const val::JournalSnapshot before_journal = fixture.journal.snapshot();
  const val::LeaseSnapshot before_leases = fixture.registry.snapshot();
  val::ActionDiagnostic diagnostic;
  EXPECT_EQ(fixture.path->execute(request, state, time, payload, diagnostic), status);
  EXPECT_EQ(diagnostic.guard_reason, reason);
  EXPECT_EQ(fixture.emitter.calls.load(), before_calls);
  EXPECT_EQ(fixture.journal.snapshot(), before_journal);
  EXPECT_EQ(fixture.registry.snapshot(), before_leases);
}

} // namespace

/** T29-TS-001 (CHK-06, CHK-15, NEG-04, NEG-05): every request-evaluation guard reason. */
TEST(XcomStimulationMatrixPermitAction, MismatchMatrixEveryGuardReason) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  MatrixFixture fixture;
  ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);

  // M-01: action-path preconditions (zero request id, over-bound payload) fail closed with no
  // guard evaluation, no emission, and no journal append.
  {
    val::StimulationRequest malformed = make_request(permit, 100U);
    malformed.request_id = 0U;
    expect_decline(fixture, malformed, val::LifecycleState::active, in_window(),
                   val::ActionStatus::RejectedConfiguration, val::GuardReason::None);
    const std::vector<std::byte> over_bound(make_config().max_payload_bytes + 1U);
    expect_decline(fixture, make_request(permit, 101U), val::LifecycleState::active, in_window(),
                   val::ActionStatus::RejectedConfiguration, val::GuardReason::None, over_bound);
    val::StimulationRequest undefined = make_request(permit, 102U);
    undefined.action = static_cast<val::StimulationAction>(0x10U);
    expect_decline(fixture, undefined, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::RejectedConfiguration);
  }
  // M-02: foreign permit identity.
  {
    val::StimulationRequest request = make_request(permit, 110U);
    request.permit_id[0] ^= 0xFFU;
    expect_decline(fixture, request, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::PermitMismatch);
  }
  // M-03: undeclared schema.
  {
    val::StimulationRequest request = make_request(permit, 111U);
    request.schema = val::SchemaKey{tag("sig.v1"), tag("9")};
    expect_decline(fixture, request, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::SchemaMismatch);
  }
  // M-04: inconsistent direction.
  {
    val::StimulationRequest request = make_request(permit, 112U);
    request.direction = EndpointDirection::consume;
    expect_decline(fixture, request, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::DirectionMismatch);
  }
  // M-05: inconsistent interaction.
  {
    val::StimulationRequest request = make_request(permit, 113U);
    request.interaction = InteractionKind::message_event;
    expect_decline(fixture, request, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::InteractionMismatch);
  }
  // M-06: foreign target tag.
  {
    val::StimulationRequest request = make_request(permit, 114U);
    request.target = tag("target.beta");
    expect_decline(fixture, request, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::TargetMismatch);
  }
  // M-07: action not allowed by a narrower policy.
  {
    val::StimulationPolicy signal_only = policy;
    signal_only.allowed_actions = val::to_stimulation_mask(val::StimulationAction::InjectSignal);
    MatrixFixture narrow;
    ASSERT_EQ(narrow.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(narrow.open_path(permit, signal_only, make_config()), val::GuardStatus::Ok);
    expect_decline(narrow, make_request(permit, 115U, val::StimulationAction::InjectMessage),
                   val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
                   val::GuardReason::ActionMismatch);
  }
  // M-08: missing service owner.
  {
    val::StimulationRequest request =
        make_request(permit, 116U, val::StimulationAction::InvokeService);
    request.service_owner.declared = false;
    expect_decline(fixture, request, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::OwnershipConflict);
  }
  // M-09: declared quota exhausted.
  {
    MatrixFixture quota;
    ASSERT_EQ(quota.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(quota.open_path(permit, make_policy(permit, 1U), make_config()),
              val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(quota.path->execute(make_request(permit, 117U), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    expect_decline(quota, make_request(permit, 118U), val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::QuotaExhausted);
  }
  // M-10: causal parent retained in the action-path lineage window.
  {
    MatrixFixture lineage;
    ASSERT_EQ(lineage.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(lineage.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(lineage.path->execute(make_request(permit, 120U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    val::StimulationRequest loop = make_request(permit, 121U);
    loop.causation_id = 120U;
    expect_decline(lineage, loop, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::LoopBound);
  }
  // M-11: resolution outside the validity window.
  expect_decline(fixture, make_request(permit, 130U), val::LifecycleState::active, out_of_window(),
                 val::ActionStatus::Rejected, val::GuardReason::TimeOutOfWindow);
  // M-12: absent/unmapped/out-of-tolerance resolution.
  expect_decline(fixture, make_request(permit, 131U), val::LifecycleState::active,
                 unmapped(val::Result::MissingMapping), val::ActionStatus::Failed,
                 val::GuardReason::TimeUnmapped);

  // The accepted guard is evaluated exactly once per `authorize` call (source-inspected: the
  // action path calls it once per request; the private guard is exercised directly here).
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    ASSERT_EQ(guard.authorize(make_request(permit, 140U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.snapshot().evaluations, 1U);
    val::StimulationRequest mismatch = make_request(permit, 141U);
    mismatch.target = tag("target.beta");
    EXPECT_EQ(guard.authorize(mismatch, val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::TargetMismatch);
    EXPECT_EQ(guard.snapshot().evaluations, 2U);
    EXPECT_EQ(guard.snapshot().rejections, 1U);
  }
}

/** T29-TS-002 (CHK-06, NEG-06): lifecycle preconditions and the directly evaluated closed guard. */
TEST(XcomStimulationMatrixPermitAction, MismatchMatrixLifecycleAndClosedGuard) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  MatrixFixture fixture;
  ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);

  const std::array<val::LifecycleState, 5U> non_active{val::LifecycleState::revoked,
                                                       val::LifecycleState::expired,
                                                       val::LifecycleState::declared,
                                                       val::LifecycleState::armed,
                                                       val::LifecycleState::closing};
  std::uint64_t id = 200U;
  for (const val::LifecycleState state : non_active) {
    expect_decline(fixture, make_request(permit, id), state, in_window(),
                   val::ActionStatus::NotActive, val::GuardReason::None);
    ++id;
  }

  // A closed accepted guard fails closed with `NotOpen` and authorizes nothing.
  val::StimulationGuard closed;
  val::GuardDiagnostic diagnostic;
  EXPECT_FALSE(closed.is_open());
  EXPECT_EQ(closed.authorize(make_request(permit, 220U), val::LifecycleState::active, in_window(),
                             diagnostic),
            val::GuardOutcome::Failed);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::NotOpen);
  EXPECT_EQ(closed.status(), val::GuardStatus::NotOpen);

  // An opened guard with an inconsistent permit/policy pair stays closed and authorizes nothing.
  val::StimulationGuard inconsistent;
  val::StimulationPolicy foreign = policy;
  foreign.plan_digest[0] ^= 0xFFU;
  EXPECT_EQ(inconsistent.open(permit, foreign), val::GuardStatus::RejectedConfiguration);
  EXPECT_FALSE(inconsistent.is_open());
  EXPECT_EQ(inconsistent.authorize(make_request(permit, 221U), val::LifecycleState::active,
                                   in_window(), diagnostic),
            val::GuardOutcome::Failed);
  EXPECT_EQ(diagnostic.reason, val::GuardReason::NotOpen);
}

/** T29-TS-003 (CHK-07, NEG-07): quota commitment, exhaustion, and the per-window bound. */
TEST(XcomStimulationMatrixPermitAction, MismatchMatrixQuotaExhaustion) {
  const val::Permit permit = make_permit();

  // Q-01: the first `n` authorized actions are emitted; the `n+1`-th is rejected with zero
  // emission and zero journal append.
  {
    constexpr std::size_t kBudget = 3U;
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, make_policy(permit, kBudget), make_config()),
              val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    for (std::size_t index = 0U; index < kBudget; ++index) {
      ASSERT_EQ(fixture.path->execute(make_request(permit, 300U + index),
                                      val::LifecycleState::active, in_window(), {}, diagnostic),
                val::ActionStatus::Emitted);
    }
    EXPECT_EQ(fixture.path->snapshot().emitted, kBudget);
    expect_decline(fixture, make_request(permit, 310U), val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::QuotaExhausted);
  }

  // Exact commit accounting: the accepted guard commits exactly one action per authorization.
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, make_policy(permit, 2U)), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    ASSERT_EQ(guard.authorize(make_request(permit, 320U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    ASSERT_EQ(guard.authorize(make_request(permit, 321U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    EXPECT_EQ(guard.snapshot().actions_authorized, 2U);
    EXPECT_EQ(guard.snapshot().evaluations, 2U);
    EXPECT_EQ(guard.snapshot().actions_remaining, 0U);
    EXPECT_EQ(guard.authorize(make_request(permit, 322U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::QuotaExhausted);
    EXPECT_EQ(guard.snapshot().actions_authorized, 2U);
  }

  // Q-02: a per-window budget binds before the per-session budget.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, make_policy(permit, 5U, 4U, 2U, 5U), make_config()),
              val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    for (std::size_t index = 0U; index < 2U; ++index) {
      ASSERT_EQ(fixture.path->execute(make_request(permit, 330U + index),
                                      val::LifecycleState::active, in_window(), {}, diagnostic),
                val::ActionStatus::Emitted);
    }
    expect_decline(fixture, make_request(permit, 340U), val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::QuotaExhausted);
    EXPECT_EQ(fixture.path->snapshot().emitted, 2U);
  }
}

/** T29-TS-004 (CHK-08, NEG-09, NEG-10, NEG-20): loop bounds, zero causation, and the lineage
 *  window, including the directly exercised guard loop window. */
TEST(XcomStimulationMatrixPermitAction, MismatchMatrixLoopBoundAndLineage) {
  const val::Permit permit = make_permit();

  // L-01/L-02: a retained causal parent is a prohibited reinjection; `causation_id == 0` never is.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, make_policy(permit), make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 400U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    val::StimulationRequest loop = make_request(permit, 401U);
    loop.causation_id = 400U;
    expect_decline(fixture, loop, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::LoopBound);
    val::StimulationRequest zero = make_request(permit, 402U);
    zero.causation_id = 0U;
    ASSERT_EQ(fixture.path->execute(zero, val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
  }

  // L-03: the lineage window never exceeds its declared depth and evicts the oldest identity.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, make_policy(permit, 5U, 2U), make_config(4U, 2U, 4U)),
              val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    for (std::uint64_t identity : {410U, 411U, 412U}) {
      ASSERT_EQ(fixture.path->execute(make_request(permit, identity), val::LifecycleState::active,
                                      in_window(), {}, diagnostic),
                val::ActionStatus::Emitted);
    }
    EXPECT_EQ(fixture.path->snapshot().lineage_entries, 2U);
    val::StimulationRequest evicted = make_request(permit, 413U);
    evicted.causation_id = 410U;
    ASSERT_EQ(fixture.path->execute(evicted, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::Emitted);
    EXPECT_EQ(fixture.path->snapshot().lineage_entries, 2U);
    val::StimulationRequest retained = make_request(permit, 414U);
    retained.causation_id = 413U;
    expect_decline(fixture, retained, val::LifecycleState::active, in_window(),
                   val::ActionStatus::Rejected, val::GuardReason::LoopBound);
  }

  // L-04: the accepted guard loop window bounds a prohibited reinjection and evicts the oldest.
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, make_policy(permit, 8U, 2U)), val::GuardStatus::Ok);
    val::GuardDiagnostic diagnostic;
    for (std::uint64_t identity : {420U, 421U, 422U}) {
      ASSERT_EQ(guard.authorize(make_request(permit, identity), val::LifecycleState::active,
                                in_window(), diagnostic),
                val::GuardOutcome::Authorized);
    }
    EXPECT_EQ(guard.snapshot().loop_entries, 2U);
    val::StimulationRequest loop = make_request(permit, 423U);
    loop.causation_id = 422U;
    EXPECT_EQ(guard.authorize(loop, val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::LoopBound);
    val::StimulationRequest evicted = make_request(permit, 424U);
    evicted.causation_id = 420U;
    EXPECT_EQ(guard.authorize(evicted, val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Authorized);
  }
}

/** T29-TS-005 (CHK-09, NEG-11, NEG-12, NEG-26): unmapped/out-of-tolerance clocks and the
 *  declared lease clock domain. */
TEST(XcomStimulationMatrixPermitAction, MismatchMatrixUnmappedAndOutOfToleranceClock) {
  const val::Permit permit = make_permit();
  MatrixFixture fixture;
  ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, make_policy(permit), make_config()), val::GuardStatus::Ok);

  // C-01 positive control: an in-window `Ok` resolution proceeds.
  {
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 500U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
  }
  // C-02/C-03/C-04: every non-`Ok` resolution fails closed before emission and journaling.
  const std::array<val::Result, 3U> unresolved{val::Result::UnknownClock,
                                               val::Result::MissingMapping,
                                               val::Result::ToleranceExceeded};
  std::uint64_t id = 501U;
  for (const val::Result resolution : unresolved) {
    expect_decline(fixture, make_request(permit, id), val::LifecycleState::active,
                   unmapped(resolution), val::ActionStatus::Failed, val::GuardReason::TimeUnmapped);
    ++id;
  }
  // C-05: a value at or after the exclusive validity end is rejected before emission.
  expect_decline(fixture, make_request(permit, 510U), val::LifecycleState::active, out_of_window(),
                 val::ActionStatus::Rejected, val::GuardReason::TimeOutOfWindow);

  // C-06: an elapsed lease is compared only in its declared domain; a foreign domain is untouched.
  {
    val::ServiceEmulationRegistry registry{4U};
    val::EndpointGeneration key;
    key.session = session_a();
    key.endpoint = tag("svc.alpha");
    key.generation = 3U;
    key.plan_digest = digest_a();
    ASSERT_EQ(registry.acquire(key, 520U, kDomain, 0, 50), val::LeaseStatus::Ok);
    EXPECT_EQ(registry.expire_elapsed(kForeignDomain, 100), 0U);
    EXPECT_EQ(registry.state_of(key), val::LeaseState::Active);
    EXPECT_EQ(registry.expire_elapsed(kDomain, 50), 1U);
    EXPECT_EQ(registry.state_of(key), val::LeaseState::Expired);
    EXPECT_FALSE(registry.holds(key));
  }
  // C-07: no time authority is called or mutated; the accepted action path consumes only the
  // caller-resolved value. This is proven by source inspection (no `TimeAuthority` reference in
  // `stimulation_actions.hpp`/`.cpp`) and by every unmapped row failing closed above.
}
