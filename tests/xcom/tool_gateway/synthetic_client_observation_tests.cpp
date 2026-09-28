/**
 * @file synthetic_client_observation_tests.cpp
 * @brief T032 separate-process synthetic-client observation cases: the client runs as its own
 *        process, negotiates the supported protocol, opens a bounded metadata-only observation
 *        stream, reads at most the granted bounded records, closes with bounded delivered/dropped
 *        counters, and observes an emitted stimulation item as one metadata-only record.
 * @ownership Each case owns one `SyntheticClientFixture`, one accepted `GatewaySession`, and its
 *            bounded scratch endpoint; the launched fixture process is reaped within a bounded wait.
 * @lifetime The fixture and session outlive the harness call and unlink their scratch path on
 *           destruction.
 * @thread_safety Single-threaded; the owned fixture child runs as a separate process.
 * @bounds One socket and one peer per case; <= 8 published records; no network, resolver, or
 *         transport-security facility is contacted.
 * @failure A failed launch, connect, decode, bound, or reap fails the owning case closed.
 * @par Traceability
 * Supports T032-SR-003, T032-SR-005, T032-SR-006, T032-SR-014 and cases T32-TS-001..T32-TS-005.
 */

#include <gtest/gtest.h>

#include "synthetic_client_support.hpp"

#include <string>

namespace {

using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::ClientRunResult;
using xverse::xcom::tool_gateway_test::ClientServerMode;
using xverse::xcom::tool_gateway_test::field_value;
using xverse::xcom::tool_gateway_test::find_last_method_line;
using xverse::xcom::tool_gateway_test::find_method_line;
using xverse::xcom::tool_gateway_test::run_client_case;
using xverse::xcom::tool_gateway_test::SyntheticClientFixture;

}  // namespace

TEST(XcomSyntheticClientObservation, ClientProcessQueryVersion) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "obs-qv.sock", "version",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_TRUE(result.peer_accepted);
  EXPECT_GE(result.requests_served, 1U);
  const std::string line = find_last_method_line(result, "QueryVersion");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "outcome"), "accepted");
  EXPECT_EQ(field_value(line, "size"), "1");
  EXPECT_EQ(session.snapshot().negotiated, true);
}

TEST(XcomSyntheticClientObservation, ClientOpensBoundedObservationStream) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "obs-open.sock", "observation",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  const std::string line = find_method_line(result, "OpenObservation");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "outcome"), "accepted");
  EXPECT_EQ(field_value(line, "size"), "4");
}

TEST(XcomSyntheticClientObservation, ClientReadsMetadataOnlyRecords) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "obs-read.sock", "observation",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U, 6U, 0U);
  ASSERT_EQ(result.exit_status, 0);
  const std::string line = find_last_method_line(result, "ReadObservations");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "outcome"), "accepted");
  EXPECT_EQ(field_value(line, "size"), "4");
  EXPECT_EQ(field_value(line, "metadata"), "4");
}

TEST(XcomSyntheticClientObservation, ClientClosesStreamWithCounters) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "obs-close.sock", "observation",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U, 6U, 0U);
  ASSERT_EQ(result.exit_status, 0);
  const std::string line = find_method_line(result, "CloseObservation");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "outcome"), "accepted");
  EXPECT_EQ(field_value(line, "size"), "4");
  EXPECT_EQ(field_value(line, "dropped"), "2");
}

TEST(XcomSyntheticClientObservation, ClientObservesEmittedTraffic) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result = run_client_case(
      session, fixture.config(), fixture.hub(), "obs-emitted.sock", "observation_stimulus",
      ClientServerMode::dispatch, 4096U, 1000U, 500U, 0U, 1U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_EQ(fixture.emitter().calls, 1U);
  const std::string submit = find_method_line(result, "SubmitStimulation");
  ASSERT_FALSE(submit.empty());
  EXPECT_EQ(field_value(submit, "outcome"), "accepted");
  const std::string read = find_last_method_line(result, "ReadObservations");
  ASSERT_FALSE(read.empty());
  EXPECT_EQ(field_value(read, "outcome"), "accepted");
  EXPECT_EQ(field_value(read, "size"), "1");
  EXPECT_EQ(field_value(read, "metadata"), "1");
  EXPECT_EQ(session.snapshot().emitted, 1U);
}
