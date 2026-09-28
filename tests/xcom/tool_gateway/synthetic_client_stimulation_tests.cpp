/**
 * @file synthetic_client_stimulation_tests.cpp
 * @brief T032 separate-process synthetic-client stimulation cases: the client arms the exact permit
 *        and submits each of the four allowed stimulation actions through the accepted guard,
 *        journal, and action path, observes an emitted outcome, keeps persistent synthetic
 *        provenance, and acquires and releases the accepted exclusive generation-bound lease.
 * @ownership Each case owns one `SyntheticClientFixture`, one accepted `GatewaySession`, and its
 *            bounded scratch endpoint; the launched fixture process is reaped within a bounded wait.
 * @lifetime The fixture and session outlive the harness call and unlink their scratch path on
 *           destruction.
 * @thread_safety Single-threaded; the owned fixture child runs as a separate process.
 * @bounds One socket and one peer per case; one bounded submission per action; no network peer.
 * @failure A failed launch, connect, guard, lease, or reap fails the owning case closed.
 * @par Traceability
 * Supports T032-SR-007, T032-SR-008 and cases T32-TS-006..T32-TS-010.
 */

#include <gtest/gtest.h>

#include "synthetic_client_support.hpp"

#include <string>

namespace {

using xverse::xcom::GatewaySession;
using xverse::xcom::OriginKind;
using xverse::xcom::tool_gateway_test::ClientRunResult;
using xverse::xcom::tool_gateway_test::ClientServerMode;
using xverse::xcom::tool_gateway_test::field_value;
using xverse::xcom::tool_gateway_test::find_method_line;
using xverse::xcom::tool_gateway_test::run_client_case;
using xverse::xcom::tool_gateway_test::SyntheticClientFixture;

/// @brief Runs one bounded stimulation case and asserts the accepted emitted outcome.
/// @param socket_name Unique bounded scratch name.
/// @param exercise Declared client exercise.
void expect_emitted_action(const std::string &socket_name, const std::string &exercise) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), socket_name, exercise,
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  const std::string armed = find_method_line(result, "ArmSession");
  ASSERT_FALSE(armed.empty());
  EXPECT_EQ(field_value(armed, "outcome"), "accepted");
  const std::string submit = find_method_line(result, "SubmitStimulation");
  ASSERT_FALSE(submit.empty());
  EXPECT_EQ(field_value(submit, "outcome"), "accepted");
  EXPECT_EQ(field_value(submit, "size"), "1");
  EXPECT_EQ(fixture.emitter().calls, 1U);
  EXPECT_EQ(fixture.emitter().last_origin, OriginKind::validation_tool);
  EXPECT_EQ(session.snapshot().emitted, 1U);
}

}  // namespace

TEST(XcomSyntheticClientStimulation, ClientInjectsSignal) {
  expect_emitted_action("sti-signal.sock", "stimulate_signal");
}

TEST(XcomSyntheticClientStimulation, ClientInjectsMessage) {
  expect_emitted_action("sti-message.sock", "stimulate_message");
}

TEST(XcomSyntheticClientStimulation, ClientInvokesService) {
  expect_emitted_action("sti-invoke.sock", "stimulate_invoke");
}

TEST(XcomSyntheticClientStimulation, ClientEmulatesService) {
  expect_emitted_action("sti-emulate.sock", "stimulate_emulate");
}

TEST(XcomSyntheticClientStimulation, ClientAcquiresAndReleasesLease) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "sti-lease.sock", "lease",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  const std::string acquired = find_method_line(result, "AcquireLease");
  ASSERT_FALSE(acquired.empty());
  EXPECT_EQ(field_value(acquired, "outcome"), "accepted");
  EXPECT_EQ(field_value(acquired, "size"), "1");
  const std::string released = find_method_line(result, "ReleaseLease");
  ASSERT_FALSE(released.empty());
  EXPECT_EQ(field_value(released, "outcome"), "accepted");
  EXPECT_EQ(field_value(released, "size"), "2");
  EXPECT_FALSE(session.snapshot().lease_held);
}
