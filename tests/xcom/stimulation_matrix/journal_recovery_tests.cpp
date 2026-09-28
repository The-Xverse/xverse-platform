/**
 * @file journal_recovery_tests.cpp
 * @brief T029 journal-before-emission ordering and journal failure/recovery matrix: the durable
 *        intent precedes the single emitter call for every action kind, an intent append/sync
 *        failure emits nothing, an outcome failure is `EvidenceIncomplete`, a restart recovers
 *        the exact intent identity, and over-capacity fails closed.
 * @ownership Each case owns its fixture, fault-injecting storage, recording emitter, byte view,
 *            and captured descriptor.
 * @lifetime The storage outlives every journal generation it backs.
 * @thread_safety Single-threaded.
 * @bounds <= 4 action kinds, <= 4 declared fault points, <= 16 KiB durable bytes.
 * @failure Any non-delivered outcome reported as `Emitted`, any fault that emits, or any lost
 *          restart identity fails the case.
 */

#include "test_support.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::stimulation_matrix_test::default_journal_config;
using xverse::xcom::stimulation_matrix_test::in_window;
using xverse::xcom::stimulation_matrix_test::make_config;
using xverse::xcom::stimulation_matrix_test::make_permit;
using xverse::xcom::stimulation_matrix_test::make_policy;
using xverse::xcom::stimulation_matrix_test::make_request;
using xverse::xcom::stimulation_matrix_test::MatrixFixture;
using xverse::xcom::stimulation_matrix_test::StorageFault;

namespace {

/// @brief One declared action kind and its request identity.
struct ActionRow {
  /// @brief Declared stimulation action.
  val::StimulationAction action;
  /// @brief Request identity.
  std::uint64_t request_id;
};

/// @brief The four declared action kinds with bounded, distinct request identities.
constexpr std::array<ActionRow, 4U> kActionKinds{{
    {val::StimulationAction::InjectSignal, 600U},
    {val::StimulationAction::InjectMessage, 601U},
    {val::StimulationAction::InvokeService, 602U},
    {val::StimulationAction::EmulateService, 603U},
}};

} // namespace

/** T29-TS-006 (CHK-10, NEG-13): the durable intent precedes the single emitter call for each
 *  action kind, and a durable non-delivery is never reported as `Emitted`. */
TEST(XcomStimulationMatrixJournalRecovery, JournalIntentPrecedesSingleEmission) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  for (const ActionRow &row : kActionKinds) {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(make_request(permit, row.request_id, row.action),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    EXPECT_EQ(fixture.emitter.calls.load(), 1U);
    EXPECT_TRUE(fixture.emitter.intent_durable_before_emit());
    EXPECT_GE(fixture.emitter.durable_size_at_call(), val::kJournalMinRecordBytes);
    const val::JournalSnapshot snapshot = fixture.journal.snapshot();
    EXPECT_EQ(snapshot.complete_intents, 1U);
    EXPECT_EQ(snapshot.outcomes, 1U);
    EXPECT_EQ(snapshot.orphan_intents, 0U);
  }

  // J-02/J-03: the host outcome is durable but is a bounded non-delivery, never success.
  for (const val::EmissionStatus non_delivery :
       {val::EmissionStatus::Rejected, val::EmissionStatus::Unavailable}) {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    fixture.emitter.status.store(non_delivery);
    val::ActionDiagnostic diagnostic;
    const val::ActionStatus status =
        fixture.path->execute(make_request(permit, 610U), val::LifecycleState::active, in_window(),
                              {}, diagnostic);
    EXPECT_EQ(fixture.emitter.calls.load(), 1U);
    EXPECT_EQ(fixture.journal.snapshot().outcomes, 1U);
    EXPECT_NE(status, val::ActionStatus::Emitted);
    if (non_delivery == val::EmissionStatus::Rejected) {
      EXPECT_EQ(status, val::ActionStatus::EmissionRejected);
    } else {
      EXPECT_EQ(status, val::ActionStatus::EmissionUnavailable);
    }
  }
}

/** T29-TS-007 (CHK-11, NEG-14, NEG-15): an intent append or sync failure emits nothing and
 *  commits no durable record. */
TEST(XcomStimulationMatrixJournalRecovery, JournalIntentAppendFailureEmitsNothing) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  const std::array<StorageFault, 2U> intent_faults{StorageFault::WriteFailed,
                                                   StorageFault::PartialWrite};
  std::uint64_t id = 620U;
  for (const StorageFault fault : intent_faults) {
    MatrixFixture fixture;
    fixture.storage.append_fault = fault;
    fixture.storage.append_fault_on = 1U;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(fixture.path->execute(make_request(permit, id), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::JournalFailed);
    EXPECT_EQ(diagnostic.journal_status,
              fault == StorageFault::PartialWrite ? val::JournalStatus::PartialWrite
                                                  : val::JournalStatus::WriteFailed);
    EXPECT_EQ(fixture.emitter.calls.load(), 0U);
    EXPECT_EQ(fixture.journal.snapshot().retained_records, 0U);
    EXPECT_EQ(fixture.storage.size(), 0U);
    ++id;
  }

  // A durable sync failure on the intent frame also emits nothing and commits no record.
  MatrixFixture sync_fixture;
  sync_fixture.storage.sync_fault = StorageFault::WriteFailed;
  sync_fixture.storage.sync_fault_on = 1U;
  ASSERT_EQ(sync_fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(sync_fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
  val::ActionDiagnostic diagnostic;
  EXPECT_EQ(sync_fixture.path->execute(make_request(permit, id), val::LifecycleState::active,
                                       in_window(), {}, diagnostic),
            val::ActionStatus::JournalFailed);
  EXPECT_EQ(diagnostic.journal_status, val::JournalStatus::WriteFailed);
  EXPECT_EQ(sync_fixture.emitter.calls.load(), 0U);
  EXPECT_EQ(sync_fixture.journal.snapshot().retained_records, 0U);
  EXPECT_EQ(sync_fixture.storage.size(), 0U);
}

/** T29-TS-008 (CHK-11, NEG-16): an outcome failure is `EvidenceIncomplete`, never `Emitted`. */
TEST(XcomStimulationMatrixJournalRecovery, JournalOutcomeFailureIsEvidenceIncomplete) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  // The intent append succeeds; the outcome append fails, short-writes, or fails to sync.
  struct FaultPlan {
    StorageFault append_fault;
    std::size_t append_on;
    StorageFault sync_fault;
    std::size_t sync_on;
  };
  const std::array<FaultPlan, 3U> plans{{
      {StorageFault::WriteFailed, 2U, StorageFault::None, 0U},
      {StorageFault::PartialWrite, 2U, StorageFault::None, 0U},
      {StorageFault::None, 0U, StorageFault::WriteFailed, 2U},
  }};
  std::uint64_t id = 640U;
  for (const FaultPlan &plan : plans) {
    MatrixFixture fixture;
    fixture.storage.append_fault = plan.append_fault;
    fixture.storage.append_fault_on = plan.append_on;
    fixture.storage.sync_fault = plan.sync_fault;
    fixture.storage.sync_fault_on = plan.sync_on;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    const val::ActionStatus status =
        fixture.path->execute(make_request(permit, id), val::LifecycleState::active, in_window(),
                              {}, diagnostic);
    EXPECT_EQ(status, val::ActionStatus::EvidenceIncomplete);
    EXPECT_NE(status, val::ActionStatus::Emitted);
    EXPECT_EQ(diagnostic.journal_status, val::JournalStatus::EvidenceIncomplete);
    EXPECT_EQ(fixture.emitter.calls.load(), 1U);
    const val::JournalSnapshot snapshot = fixture.journal.snapshot();
    EXPECT_EQ(snapshot.complete_intents, 1U);
    EXPECT_EQ(snapshot.outcomes, 0U);
    EXPECT_EQ(snapshot.orphan_intents, 1U);
    EXPECT_EQ(fixture.path->snapshot().evidence_incomplete, 1U);
    ++id;
  }
}

/** T29-TS-009 (CHK-11, CHK-14, NEG-17, NEG-23): a restart recovers the exact orphan identity and
 *  never reports an incomplete outcome as success. */
TEST(XcomStimulationMatrixJournalRecovery, JournalRestartRecoversExactIdentity) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  MatrixFixture fixture;
  fixture.storage.append_fault = StorageFault::WriteFailed;
  fixture.storage.append_fault_on = 2U; // intent durable, outcome append fails.
  ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
  val::ActionDiagnostic diagnostic;
  ASSERT_EQ(fixture.path->execute(make_request(permit, 660U), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
            val::ActionStatus::EvidenceIncomplete);
  const val::StimulationIntent emitted = fixture.emitter.last_item().intent;
  ASSERT_EQ(emitted.request_id, 660U);
  ASSERT_EQ(fixture.journal.snapshot().orphan_intents, 1U);

  // Reopen a fresh accepted journal over the same durable bytes and recover.
  val::StimulationJournal restarted;
  ASSERT_EQ(restarted.open(fixture.storage, default_journal_config()), val::JournalStatus::Ok);
  const val::RecoveryReport report = restarted.last_recovery();
  EXPECT_EQ(report.status, val::JournalStatus::Ok);
  EXPECT_EQ(report.complete_intents, 1U);
  EXPECT_EQ(report.outcomes, 0U);
  EXPECT_EQ(report.orphan_intents, 1U);
  ASSERT_EQ(report.orphan_request_ids.size(), 1U);
  EXPECT_EQ(report.orphan_request_ids.front(), emitted.request_id);
  const std::vector<val::StimulationIntent> recovered = restarted.recovered_intents();
  ASSERT_EQ(recovered.size(), 1U);
  EXPECT_EQ(recovered.front(), emitted);
}

/** T29-TS-010 (CHK-11, NEG-07): an exhausted retained-record bound fails closed with zero
 *  emission and no over-bound record. */
TEST(XcomStimulationMatrixJournalRecovery, JournalCapacityExhaustionFailsClosed) {
  const val::Permit permit = make_permit();
  val::JournalConfig config = default_journal_config();
  config.max_retained_records = 2U;
  MatrixFixture fixture;
  ASSERT_EQ(fixture.open_journal(config), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, make_policy(permit), make_config()), val::GuardStatus::Ok);
  val::ActionDiagnostic diagnostic;
  ASSERT_EQ(fixture.path->execute(make_request(permit, 680U), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
            val::ActionStatus::Emitted);
  ASSERT_EQ(fixture.journal.snapshot().retained_records, 2U);
  const std::size_t before_calls = fixture.emitter.calls.load();

  EXPECT_EQ(fixture.path->execute(make_request(permit, 681U), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
            val::ActionStatus::CapacityExhausted);
  EXPECT_EQ(fixture.emitter.calls.load(), before_calls);
  EXPECT_EQ(fixture.journal.snapshot().retained_records, 2U);
  EXPECT_EQ(fixture.path->snapshot().emitted, 1U);
}
