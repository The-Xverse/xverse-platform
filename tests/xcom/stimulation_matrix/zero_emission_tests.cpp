/**
 * @file zero_emission_tests.cpp
 * @brief T029 zero-emission matrix: for every decline family the recording emitter observes zero
 *        calls, the durable journal bytes are unchanged, and the operational snapshot is
 *        unchanged apart from the declared counters.
 * @ownership Each family owns a bounded fixture, its snapshots, and its counter captures.
 * @lifetime The fixture outlives each decline; snapshots are value copies.
 * @thread_safety Single-threaded.
 * @bounds <= 11 decline families, <= 11 evaluations, no wall-clock verdict.
 * @failure Any decline that emits or mutates the declined dimension fails the case.
 */

#include "test_support.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::stimulation_matrix_test::in_window;
using xverse::xcom::stimulation_matrix_test::make_config;
using xverse::xcom::stimulation_matrix_test::make_permit;
using xverse::xcom::stimulation_matrix_test::make_policy;
using xverse::xcom::stimulation_matrix_test::make_request;
using xverse::xcom::stimulation_matrix_test::MatrixFixture;
using xverse::xcom::stimulation_matrix_test::out_of_window;
using xverse::xcom::stimulation_matrix_test::tag;
using xverse::xcom::stimulation_matrix_test::unmapped;

namespace {

/// @brief Asserts that no emitter call and no durable byte appeared since a capture.
/// @param fixture The owned fixture.
/// @param calls Emission calls captured before the decline.
/// @param bytes Durable bytes captured before the decline.
void expect_zero_emission(MatrixFixture &fixture, std::size_t calls, std::size_t bytes) {
  EXPECT_EQ(fixture.emitter.calls.load(), calls);
  EXPECT_EQ(fixture.storage.size(), bytes);
}

} // namespace

/** T29-TS-011 (CHK-12, NEG-04..NEG-06, NEG-18..NEG-20): every decline family emits nothing and
 *  appends no durable record. */
TEST(XcomStimulationMatrixZeroEmission, ZeroEmissionAcrossEveryRejectionFamily) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  val::ActionDiagnostic diagnostic;

  // Z-01: a closed path evaluates nothing.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    fixture.build_closed_path(make_config());
    const val::ActionPathSnapshot before = fixture.path->snapshot();
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    EXPECT_EQ(fixture.path->execute(make_request(permit, 700U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::NotOpen);
    expect_zero_emission(fixture, calls, bytes);
    EXPECT_EQ(fixture.path->snapshot(), before);
  }

  // Z-02/Z-03: a malformed request and an over-bound payload are rejected before any state work.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    const val::ActionPathSnapshot before = fixture.path->snapshot();
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    val::StimulationRequest malformed = make_request(permit, 701U);
    malformed.request_id = 0U;
    EXPECT_EQ(fixture.path->execute(malformed, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::RejectedConfiguration);
    const std::vector<std::byte> over_bound(make_config().max_payload_bytes + 1U);
    EXPECT_EQ(fixture.path->execute(make_request(permit, 702U), val::LifecycleState::active,
                                    in_window(), over_bound, diagnostic),
              val::ActionStatus::RejectedConfiguration);
    expect_zero_emission(fixture, calls, bytes);
    EXPECT_EQ(fixture.path->snapshot(), before);
  }

  // Z-04: a loop/lineage rejection emits nothing and appends nothing.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    ASSERT_EQ(fixture.path->execute(make_request(permit, 710U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    const std::size_t pending = fixture.path->snapshot().pending;
    val::StimulationRequest loop = make_request(permit, 711U);
    loop.causation_id = 710U;
    EXPECT_EQ(fixture.path->execute(loop, val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Rejected);
    expect_zero_emission(fixture, calls, bytes);
    EXPECT_EQ(fixture.path->snapshot().pending, pending);
    EXPECT_EQ(fixture.path->snapshot().emitted, 1U);
  }

  // Z-05: a full pending queue fails closed.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config(1U, 4U, 4U)), val::GuardStatus::Ok);
    ASSERT_EQ(fixture.path->execute(make_request(permit, 720U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    EXPECT_EQ(fixture.path->execute(make_request(permit, 721U, val::StimulationAction::InjectSignal,
                                                 false, 20),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::CapacityExhausted);
    expect_zero_emission(fixture, calls, bytes);
    EXPECT_EQ(fixture.path->snapshot().pending, 1U);
  }

  // Z-06: an emulation-lease conflict emits nothing and mutates no lease entry.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    ASSERT_EQ(fixture.path->execute(
                  make_request(permit, 730U, val::StimulationAction::EmulateService),
                  val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    const val::LeaseSnapshot leases = fixture.registry.snapshot();
    EXPECT_EQ(fixture.path->execute(
                  make_request(permit, 731U, val::StimulationAction::EmulateService),
                  val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::LeaseConflict);
    expect_zero_emission(fixture, calls, bytes);
    EXPECT_EQ(fixture.registry.snapshot(), leases);
  }

  // Z-07: a non-active session emits nothing.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    EXPECT_EQ(fixture.path->execute(make_request(permit, 740U), val::LifecycleState::armed,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::NotActive);
    expect_zero_emission(fixture, calls, bytes);
  }

  // Z-08: a guard rejection and a guard failure emit nothing.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    val::StimulationRequest mismatch = make_request(permit, 750U);
    mismatch.target = tag("target.beta");
    EXPECT_EQ(fixture.path->execute(mismatch, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::Rejected);
    EXPECT_EQ(fixture.path->execute(make_request(permit, 751U), val::LifecycleState::active,
                                    unmapped(val::Result::UnknownClock), {}, diagnostic),
              val::ActionStatus::Failed);
    expect_zero_emission(fixture, calls, bytes);
  }

  // Z-09: a quota-exhausted request emits nothing.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, make_policy(permit, 1U), make_config()),
              val::GuardStatus::Ok);
    ASSERT_EQ(fixture.path->execute(make_request(permit, 760U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    EXPECT_EQ(fixture.path->execute(make_request(permit, 761U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Rejected);
    expect_zero_emission(fixture, calls, bytes);
    EXPECT_EQ(fixture.path->snapshot().emitted, 1U);
  }

  // Z-10: a late action under either policy emits nothing.
  for (const val::LateItemPolicy late_policy :
       {val::LateItemPolicy::RejectLate, val::LateItemPolicy::DiscardLate}) {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    val::ActionPathConfig config = make_config(4U, 4U, 4U, 0);
    config.late_policy = late_policy;
    ASSERT_EQ(fixture.open_path(permit, policy, config), val::GuardStatus::Ok);
    ASSERT_EQ(fixture.path->execute(make_request(permit, 770U, val::StimulationAction::InjectSignal,
                                                 false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    const val::CompletionReport report = fixture.path->drain(val::CompletionRequest{50U, 7U,
                                                                                    val::LifecycleState::active});
    EXPECT_EQ(report.drained, 0U);
    expect_zero_emission(fixture, calls, bytes);
    EXPECT_EQ(fixture.path->snapshot().pending, 0U);
  }

  // Z-11: an unmapped or out-of-tolerance time emits nothing.
  {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    const std::size_t calls = fixture.emitter.calls.load();
    const std::size_t bytes = fixture.storage.size();
    EXPECT_EQ(fixture.path->execute(make_request(permit, 780U), val::LifecycleState::active,
                                    unmapped(val::Result::ToleranceExceeded), {}, diagnostic),
              val::ActionStatus::Failed);
    EXPECT_EQ(fixture.path->execute(make_request(permit, 781U), val::LifecycleState::active,
                                    out_of_window(), {}, diagnostic),
              val::ActionStatus::Rejected);
    expect_zero_emission(fixture, calls, bytes);
  }
}
