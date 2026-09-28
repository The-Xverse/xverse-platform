/**
 * @file lease_drain_tests.cpp
 * @brief T029 lease-conflict and drain/terminal lifecycle matrix: exclusive generation-bound
 *        lease identity and conflict, release/quarantine/expiry, declared-domain expiry, ordered
 *        bounded drain, both late-item policies, dropped-due-action surfacing, immediate
 *        labelling, and every terminal completion outcome.
 * @ownership Each case owns its registry, fixture, pending queue, and completion reports.
 * @lifetime The registry and fixture outlive every caller.
 * @thread_safety Single-threaded.
 * @bounds registry capacity 1-4, pending 4, max_drain_steps 4, no wall-clock verdict.
 * @failure A second owner that acquires or emits, a foreign identity that acquires, a completion
 *          that leaves work unresolved, or an orphan reported `Closed` fails the case.
 */

#include "test_support.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace val = xverse::xcom::validation;
using xverse::xcom::stimulation_matrix_test::digest_a;
using xverse::xcom::stimulation_matrix_test::digest_b;
using xverse::xcom::stimulation_matrix_test::in_window;
using xverse::xcom::stimulation_matrix_test::kDomain;
using xverse::xcom::stimulation_matrix_test::kForeignDomain;
using xverse::xcom::stimulation_matrix_test::kUntil;
using xverse::xcom::stimulation_matrix_test::make_config;
using xverse::xcom::stimulation_matrix_test::make_permit;
using xverse::xcom::stimulation_matrix_test::make_policy;
using xverse::xcom::stimulation_matrix_test::make_request;
using xverse::xcom::stimulation_matrix_test::MatrixFixture;
using xverse::xcom::stimulation_matrix_test::session_a;
using xverse::xcom::stimulation_matrix_test::session_b;
using xverse::xcom::stimulation_matrix_test::StorageFault;
using xverse::xcom::stimulation_matrix_test::tag;

namespace {

/// @brief Builds one declared exclusive lease key.
/// @param session Bound session identity.
/// @param endpoint Declared endpoint tag.
/// @param generation Declared endpoint generation.
/// @param digest Bound plan digest.
/// @return The lease key.
[[nodiscard]] val::EndpointGeneration make_key(val::SessionId session, std::string_view endpoint,
                                               val::Generation generation,
                                               val::PlanDigest digest) {
  val::EndpointGeneration value;
  value.session = session;
  value.endpoint = tag(endpoint);
  value.generation = generation;
  value.plan_digest = digest;
  return value;
}

/// @brief Builds one bounded completion request.
/// @param now Caller-supplied time.
/// @param domain Declared completion domain.
/// @param state Caller-supplied session state.
/// @return The completion request.
[[nodiscard]] val::CompletionRequest completion(val::Timestamp now,
                                                val::ClockDomainId domain = kDomain,
                                                val::LifecycleState state =
                                                    val::LifecycleState::active) {
  return val::CompletionRequest{now, domain, state};
}

} // namespace

/** T29-TS-016 (CHK-08, CHK-17, NEG-24, NEG-25): the exclusive lease conflict, identity,
 *  supersession, release, quarantine, expiry, capacity, and generation matrix. */
TEST(XcomStimulationMatrixLeaseDrain, LeaseConflictMatrixEndToEnd) {
  const val::EndpointGeneration base = make_key(session_a(), "svc.alpha", 3U, digest_a());
  const val::EndpointGeneration other = make_key(session_a(), "svc.beta", 3U, digest_a());

  // Direct registry matrix with two active-lease slots.
  {
    val::ServiceEmulationRegistry registry{2U};
    ASSERT_EQ(registry.acquire(base, 900U, kDomain, 0, 50), val::LeaseStatus::Ok);
    const auto declines = [&](const val::EndpointGeneration &key, std::uint64_t request_id,
                              val::LeaseStatus expected) {
      const val::LeaseSnapshot before = registry.snapshot();
      EXPECT_EQ(registry.acquire(key, request_id, kDomain, 0, 50), expected);
      const val::LeaseSnapshot after = registry.snapshot();
      // No lease entry is mutated: the active set and the acquisition count are unchanged. A
      // conflict-family decline advances only the declared conflict counter.
      EXPECT_EQ(after.active, before.active);
      EXPECT_EQ(after.acquisitions, before.acquisitions);
      const bool conflict_family = expected == val::LeaseStatus::Conflict ||
                                   expected == val::LeaseStatus::PlanMismatch ||
                                   expected == val::LeaseStatus::SessionMismatch ||
                                   expected == val::LeaseStatus::GenerationMismatch;
      EXPECT_EQ(after.conflicts, before.conflicts + (conflict_family ? 1U : 0U));
      EXPECT_EQ(registry.state_of(base), val::LeaseState::Active);
    };
    declines(base, 901U, val::LeaseStatus::Conflict);
    declines(make_key(session_a(), "svc.alpha", 3U, digest_b()), 902U,
             val::LeaseStatus::PlanMismatch);
    declines(make_key(session_b(), "svc.alpha", 3U, digest_a()), 903U,
             val::LeaseStatus::SessionMismatch);
    declines(make_key(session_a(), "svc.alpha", 4U, digest_a()), 904U,
             val::LeaseStatus::GenerationMismatch);
    ASSERT_EQ(registry.acquire(other, 905U, kDomain, 0, 50), val::LeaseStatus::Ok);
    declines(make_key(session_a(), "svc.gamma", 3U, digest_a()), 906U,
             val::LeaseStatus::CapacityExhausted);
    val::EndpointGeneration malformed = make_key(session_a(), "svc.alpha", 9U, digest_a());
    malformed.session.fill(0U);
    declines(malformed, 907U, val::LeaseStatus::RejectedConfiguration);
    EXPECT_EQ(registry.snapshot().active, 2U);

    // Exact-owner release, wrong owner, already-released, and unknown.
    EXPECT_EQ(registry.release(base, 999U), val::LeaseStatus::NotHeld);
    EXPECT_EQ(registry.release(base, 900U), val::LeaseStatus::Ok);
    EXPECT_EQ(registry.state_of(base), val::LeaseState::Released);
    EXPECT_EQ(registry.release(base, 900U), val::LeaseStatus::AlreadyReleased);
    EXPECT_EQ(registry.release(make_key(session_a(), "svc.unknown", 3U, digest_a()), 900U),
              val::LeaseStatus::NotFound);

    // Quarantine relinquishes ownership and no longer conflict-blocks.
    EXPECT_EQ(registry.quarantine(other, val::QuarantineReason::Conflict), val::LeaseStatus::Ok);
    EXPECT_EQ(registry.state_of(other), val::LeaseState::Quarantined);
    EXPECT_FALSE(registry.holds(other));
    EXPECT_EQ(registry.quarantine(other, val::QuarantineReason::Disconnect),
              val::LeaseStatus::NotHeld);
    EXPECT_EQ(registry.quarantine(make_key(session_a(), "svc.unknown", 3U, digest_a()),
                                  val::QuarantineReason::Conflict),
              val::LeaseStatus::NotFound);
    EXPECT_EQ(registry.acquire(other, 908U, kDomain, 60, 90), val::LeaseStatus::Ok);

    // Expiry in the declared domain relinquishes ownership; a foreign domain is untouched.
    EXPECT_EQ(registry.expire_elapsed(kForeignDomain, 1000), 0U);
    EXPECT_TRUE(registry.holds(other));
    EXPECT_EQ(registry.expire_elapsed(kDomain, 1000), 1U);
    EXPECT_EQ(registry.state_of(other), val::LeaseState::Expired);
    EXPECT_FALSE(registry.holds(other));
  }

  // End-to-end through the accepted action path: a second emulation owner is rejected with zero
  // emission and no lease mutation.
  {
    const val::Permit permit = make_permit();
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, make_policy(permit), make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(
                  make_request(permit, 910U, val::StimulationAction::EmulateService),
                  val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    EXPECT_TRUE(fixture.registry.holds(base));
    const std::size_t calls = fixture.emitter.calls.load();
    const val::LeaseSnapshot leases = fixture.registry.snapshot();
    EXPECT_EQ(fixture.path->execute(
                  make_request(permit, 911U, val::StimulationAction::EmulateService),
                  val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::LeaseConflict);
    EXPECT_EQ(diagnostic.lease_status, val::LeaseStatus::Conflict);
    EXPECT_EQ(fixture.emitter.calls.load(), calls);
    EXPECT_EQ(fixture.registry.snapshot(), leases);
    EXPECT_EQ(fixture.registry.snapshot().acquisitions, 1U);

    // Releasing the exact owner makes the generation acquirable again.
    ASSERT_EQ(fixture.registry.release(base, 910U), val::LeaseStatus::Ok);
    EXPECT_EQ(fixture.registry.acquire(base, 912U, kDomain, 50, 90), val::LeaseStatus::Ok);
    EXPECT_TRUE(fixture.registry.holds(base));
  }
}

/** T29-TS-017 (CHK-14, NEG-17, NEG-29, NEG-30): drain, close, revoke, expire, and
 *  evidence-incomplete completion. */
TEST(XcomStimulationMatrixLeaseDrain, DrainTerminalLifecycleMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  // D-01: an active drain empties the due queue and reports `Drained`.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1000U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = fixture.path->drain(completion(kUntil - 1));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Drained);
    EXPECT_EQ(report.drained, 1U);
    EXPECT_EQ(fixture.path->snapshot().drain_state, val::DrainState::Drained);
  }
  // D-02: a declared/armed drain cancels every pending action with zero emission.
  for (const val::LifecycleState state :
       {val::LifecycleState::declared, val::LifecycleState::armed}) {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1010U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = fixture.path->drain(completion(50, kDomain, state));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::None);
    EXPECT_EQ(report.cancelled, 1U);
    EXPECT_EQ(fixture.emitter.calls.load(), 0U);
    EXPECT_EQ(fixture.path->snapshot().pending, 0U);
  }
  // D-03: an active close drains due work and releases every held lease.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(
                  make_request(permit, 1020U, val::StimulationAction::EmulateService),
                  val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1021U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = fixture.path->close(completion(kUntil - 1));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Closed);
    EXPECT_EQ(report.drained, 1U);
    EXPECT_EQ(report.released_leases, 1U);
    EXPECT_EQ(fixture.registry.state_of(make_key(session_a(), "svc.alpha", 3U, digest_a())),
              val::LeaseState::Released);
  }
  // D-05: revoke cancels every pending action and releases every held lease.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(
                  make_request(permit, 1030U, val::StimulationAction::EmulateService),
                  val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1031U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = fixture.path->revoke(completion(50));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Revoked);
    EXPECT_EQ(report.cancelled, 1U);
    EXPECT_EQ(report.released_leases, 1U);
    EXPECT_EQ(fixture.emitter.calls.load(), 1U);
  }
  // D-06: expire cancels every pending action and expires every held lease.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(
                  make_request(permit, 1040U, val::StimulationAction::EmulateService),
                  val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    const val::CompletionReport report = fixture.path->expire(completion(kUntil));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Expired);
    EXPECT_EQ(report.expired_leases, 1U);
    EXPECT_EQ(fixture.registry.state_of(make_key(session_a(), "svc.alpha", 3U, digest_a())),
              val::LeaseState::Expired);
  }
  // D-07: mark_evidence_incomplete always reports `EvidenceIncomplete`.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    const val::CompletionReport report = fixture.path->mark_evidence_incomplete(completion(kUntil));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::EvidenceIncomplete);
  }
  // D-04: an orphan intent forces `EvidenceIncomplete` and is never `Closed`.
  {
    MatrixFixture fixture;
    fixture.storage.append_fault = StorageFault::WriteFailed;
    fixture.storage.append_fault_on = 2U;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1050U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::EvidenceIncomplete);
    ASSERT_EQ(fixture.journal.snapshot().orphan_intents, 1U);
    const val::CompletionReport report =
        fixture.path->close(completion(kUntil, kDomain, val::LifecycleState::closed));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::EvidenceIncomplete);
    EXPECT_NE(report.outcome, val::CompletionOutcome::Closed);
    EXPECT_GE(report.evidence_incomplete, 1U);
  }
  // A terminal close with no orphan is `Closed`.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1060U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    EXPECT_EQ(fixture.path->close(completion(kUntil, kDomain, val::LifecycleState::closed)).outcome,
              val::CompletionOutcome::Closed);
    EXPECT_EQ(fixture.emitter.calls.load(), 0U);
  }
}

/** T29-TS-018 (CHK-18, NEG-27, NEG-28, NEG-30): ordered bounded drain, both late policies, a
 *  surfaced dropped due action, and explicit immediate labelling. */
TEST(XcomStimulationMatrixLeaseDrain, DrainOrderingLatePolicyAndImmediateLabel) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  // Declared ordering by `(scheduled_at, request_id)` within the declared domain.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config(4U, 4U, 4U)), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    for (const auto &spec : {std::pair<std::uint64_t, val::Timestamp>{30U, 60},
                             std::pair<std::uint64_t, val::Timestamp>{10U, 20},
                             std::pair<std::uint64_t, val::Timestamp>{20U, 20}}) {
      ASSERT_EQ(fixture.path->execute(make_request(permit, spec.first,
                                                   val::StimulationAction::InjectSignal, false,
                                                   spec.second),
                                      val::LifecycleState::active, in_window(), {}, diagnostic),
                val::ActionStatus::Queued);
    }
    const val::CompletionReport partial = fixture.path->drain(completion(50));
    EXPECT_EQ(partial.drained, 2U);
    EXPECT_EQ(fixture.emitter.emission_order(),
              (std::vector<std::uint64_t>{10U, 20U}));
    const val::CompletionReport final_report = fixture.path->drain(completion(kUntil - 1));
    EXPECT_EQ(final_report.outcome, val::CompletionOutcome::Drained);
    EXPECT_EQ(fixture.emitter.emission_order(),
              (std::vector<std::uint64_t>{10U, 20U, 30U}));
  }
  // The drain budget bounds each call.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config(4U, 4U, 1U)), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    for (std::uint64_t id : {1100U, 1101U}) {
      ASSERT_EQ(fixture.path->execute(make_request(permit, id, val::StimulationAction::InjectSignal,
                                                   false, 10),
                                      val::LifecycleState::active, in_window(), {}, diagnostic),
                val::ActionStatus::Queued);
    }
    EXPECT_EQ(fixture.path->drain(completion(50)).drained, 1U);
    EXPECT_EQ(fixture.path->snapshot().pending, 1U);
  }
  // Both late-item policies emit nothing.
  for (const val::LateItemPolicy late_policy :
       {val::LateItemPolicy::RejectLate, val::LateItemPolicy::DiscardLate}) {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    val::ActionPathConfig config = make_config(4U, 4U, 4U, 0);
    config.late_policy = late_policy;
    ASSERT_EQ(fixture.open_path(permit, policy, config), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1110U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    EXPECT_EQ(fixture.path->drain(completion(50)).drained, 0U);
    EXPECT_EQ(fixture.emitter.calls.load(), 0U);
    if (late_policy == val::LateItemPolicy::RejectLate) {
      EXPECT_EQ(fixture.path->snapshot().expired, 1U);
    } else {
      EXPECT_EQ(fixture.path->snapshot().discarded, 1U);
    }
  }
  // A due action whose drain-time intent append fails is surfaced, never a clean `Drained`.
  {
    MatrixFixture fixture;
    fixture.storage.append_fault = StorageFault::WriteFailed;
    fixture.storage.append_fault_on = 1U; // the drain-time intent append.
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config(4U, 4U, 4U)), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1120U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = fixture.path->drain(completion(kUntil - 1));
    EXPECT_EQ(report.failed, 1U);
    EXPECT_EQ(report.drained, 0U);
    EXPECT_EQ(report.outcome, val::CompletionOutcome::EvidenceIncomplete);
    EXPECT_EQ(fixture.emitter.calls.load(), 0U);
  }
  // Immediate labelling: an immediate request is labelled, a scheduled request is not.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config(4U, 4U, 4U)), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1130U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    EXPECT_TRUE(fixture.emitter.last_item().intent.immediate);
    ASSERT_EQ(fixture.path->execute(make_request(permit, 1131U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    ASSERT_EQ(fixture.path->drain(completion(kUntil - 1)).drained, 1U);
    EXPECT_FALSE(fixture.emitter.last_item().intent.immediate);
  }
}
