/**
 * @file synthetic_client_bounds_tests.cpp
 * @brief T032 separate-process synthetic-client bound cases: the client declares an explicit maximum
 *        message size, per-request deadline, and transport timeout, rejects an over-bound message and
 *        an over-bound deadline before dispatch with zero emission, and reports an exhausted
 *        transport wait as a stable non-success outcome that is never success.
 * @ownership Each case owns one `SyntheticClientFixture`, one accepted `GatewaySession`, and its
 *            bounded scratch endpoint; the launched fixture process is reaped within a bounded wait.
 * @lifetime The fixture and session outlive the harness call and unlink their scratch path on
 *           destruction.
 * @thread_safety Single-threaded; the owned fixture child runs as a separate process.
 * @bounds One socket and at most one peer per case; the declared bounds are explicit values.
 * @failure An over-bound frame that is dispatched, an over-bound deadline that is sent, or an
 *          exhausted transport wait reported as success fails the owning case closed.
 * @par Traceability
 * Supports T032-SR-011, T032-SR-012 and cases T32-TS-020..T32-TS-022.
 */

#include <gtest/gtest.h>

#include "synthetic_client_support.hpp"

#include <string>

namespace {

using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::ClientRunResult;
using xverse::xcom::tool_gateway_test::ClientServerMode;
using xverse::xcom::tool_gateway_test::field_value;
using xverse::xcom::tool_gateway_test::find_method_line;
using xverse::xcom::tool_gateway_test::run_client_case;
using xverse::xcom::tool_gateway_test::SyntheticClientFixture;

}  // namespace

TEST(XcomSyntheticClientBounds, MessageSizeBoundEnforced) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "bnd-message.sock", "over_message",
                      ClientServerMode::none, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_FALSE(result.peer_accepted);
  EXPECT_EQ(result.requests_served, 0U);
  const std::string line = find_method_line(result, "SubmitStimulation");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "outcome"), "rejected");
  EXPECT_EQ(field_value(line, "reason"), "over_message_bound");
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomSyntheticClientBounds, DeadlineBoundEnforced) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "bnd-deadline.sock", "over_deadline",
                      ClientServerMode::none, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_FALSE(result.peer_accepted);
  EXPECT_EQ(result.requests_served, 0U);
  const std::string line = find_method_line(result, "SubmitStimulation");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "outcome"), "rejected");
  EXPECT_EQ(field_value(line, "reason"), "over_deadline_bound");
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomSyntheticClientBounds, TransportTimeoutBounded) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "bnd-timeout.sock", "stall",
                      ClientServerMode::silent, 4096U, 1000U, 150U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_TRUE(result.peer_accepted);
  const std::string line = find_method_line(result, "QueryVersion");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "outcome"), "failed");
  EXPECT_EQ(field_value(line, "reason"), "transport_timeout");
}
