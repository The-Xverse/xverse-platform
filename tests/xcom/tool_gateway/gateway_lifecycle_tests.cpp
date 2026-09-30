/**
 * @file gateway_lifecycle_tests.cpp
 * @brief T031 gateway-lifecycle unit cases: disconnect closes observation streams, disconnect
 *        drains or quarantines a held lease, a pending request ends evidence-incomplete, and idle
 *        timeout performs the deterministic cleanup table.
 * @ownership Each case owns one bounded gateway fixture and one bounded session.
 * @lifetime The fixture outlives the session under test.
 * @thread_safety Single-threaded.
 * @bounds <= 64 operations, <= 4 streams, no retained payload byte, no wall-clock dependence.
 * @failure An unknown or expired outcome reported as success, or a missed cleanup, fails the
 *          owning case closed.
 * @par Traceability
 * Supports T031-SR-010, T031-SR-012, T031-SR-013, T031-SR-015 and the T31-TS-011..T31-TS-014
 * cases.
 */

#include <gtest/gtest.h>

#include "gateway_support.hpp"

#include <array>
#include <cstddef>
#include <string>

namespace {

namespace v1 = xverse::xcom::v1;
using xverse::xcom::GatewayOutcome;
using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::arm_request;
using xverse::xcom::tool_gateway_test::GatewayFixture;
using xverse::xcom::tool_gateway_test::kSessionId;
using xverse::xcom::tool_gateway_test::stimulation_request;

void negotiate_accepted(GatewaySession &session) {
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  peer.set_minor(0U);
  ASSERT_EQ(session.negotiate(peer), GatewayOutcome::accepted);
}

}  // namespace

TEST(XcomToolGatewayLifecycle, DisconnectClosesObservationStreams) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);

  v1::OpenObservationRequest open;
  open.set_tap_id("gateway.tap");
  open.set_max_records(2U);
  open.set_deadline_millis(1000U);
  const v1::OpenObservationResponse opened = session.OpenObservation(open);
  ASSERT_FALSE(opened.stream_id().empty());
  EXPECT_EQ(session.snapshot().active_streams, 1U);

  session.on_disconnect();
  EXPECT_TRUE(session.snapshot().terminal);
  EXPECT_EQ(session.snapshot().active_streams, 0U);

  v1::ReadObservationsRequest read;
  read.set_stream_id(opened.stream_id());
  read.set_max_records(2U);
  std::array<v1::ObservationRecord, 2U> records{};
  EXPECT_EQ(session.ReadObservations(read, records), 0U);

  v1::CloseObservationRequest close;
  close.set_stream_id(opened.stream_id());
  EXPECT_EQ(session.CloseObservation(close).diagnostic().code(), "gw.observation.close.declined");

  v1::OpenObservationRequest reopened;
  reopened.set_tap_id("gateway.tap");
  reopened.set_max_records(2U);
  reopened.set_deadline_millis(1000U);
  EXPECT_EQ(session.OpenObservation(reopened).diagnostic().code(), "gw.observation.declined");
}

TEST(XcomToolGatewayLifecycle, DisconnectDrainsOrQuarantinesLease) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::AcquireLeaseRequest lease;
  lease.set_session_id(std::string(kSessionId));
  lease.set_endpoint_id("svc.alpha");
  lease.set_endpoint_generation(3U);
  lease.set_plan_digest("plan-1");
  lease.set_lease_millis(500U);
  lease.set_deadline_millis(1000U);
  EXPECT_EQ(session.AcquireLease(lease).state(), v1::LEASE_ACTIVE);
  EXPECT_TRUE(session.snapshot().lease_held);
  EXPECT_EQ(fixture.registry().snapshot().active, 1U);

  session.on_disconnect();
  EXPECT_FALSE(session.snapshot().lease_held);
  EXPECT_EQ(fixture.registry().snapshot().active, 0U);
  EXPECT_NE(fixture.registry().snapshot().released + fixture.registry().snapshot().quarantined, 0U);
}

TEST(XcomToolGatewayLifecycle, PendingRequestEndsEvidenceIncomplete) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::SubmitStimulationRequest scheduled =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "9");
  scheduled.mutable_schedule()->set_mode(v1::SCHEDULE_SCHEDULED);
  const v1::SubmitStimulationResponse queued = session.SubmitStimulation(scheduled);
  EXPECT_EQ(queued.outcome().kind(), v1::STIMULATION_OUTCOME_QUEUED);
  EXPECT_EQ(session.snapshot().pending_requests, 1U);

  session.on_disconnect();
  const xverse::xcom::GatewaySessionSnapshot snapshot = session.snapshot();
  EXPECT_EQ(snapshot.pending_requests, 0U);
  EXPECT_GE(snapshot.evidence_incomplete, 1U);
  EXPECT_EQ(snapshot.last_pending_outcome, GatewayOutcome::evidence_incomplete);
}

TEST(XcomToolGatewayLifecycle, IdleTimeoutCleanup) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);

  session.on_idle_tick(0);
  EXPECT_FALSE(session.snapshot().terminal);

  session.on_idle_tick(1000000);
  EXPECT_TRUE(session.snapshot().terminal);

  v1::QuerySessionRequest query;
  query.set_session_id(std::string(kSessionId));
  const auto terminal = session.QuerySession(query);
  EXPECT_EQ(terminal.diagnostic().code(), "gw.query.declined");
  EXPECT_EQ(terminal.state(), v1::SESSION_EXPIRED);
  EXPECT_FALSE(terminal.lease_held());
}

TEST(XcomToolGatewayLifecycle, IndependentObservationStreamsClose) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);

  v1::OpenObservationRequest open;
  open.set_tap_id("tap.first");
  open.set_max_records(1U);
  open.set_deadline_millis(1000U);
  const v1::OpenObservationResponse first = session.OpenObservation(open);
  ASSERT_FALSE(first.stream_id().empty());
  open.set_tap_id("tap.second");
  const v1::OpenObservationResponse second = session.OpenObservation(open);
  ASSERT_FALSE(second.stream_id().empty());
  EXPECT_NE(first.stream_id(), second.stream_id());
  EXPECT_EQ(session.snapshot().active_streams, 2U);

  v1::CloseObservationRequest close_first;
  close_first.set_stream_id(first.stream_id());
  EXPECT_EQ(session.CloseObservation(close_first).diagnostic().code(), "gw.observation.closed");
  EXPECT_EQ(session.snapshot().active_streams, 1U);

  v1::CloseObservationRequest close_second;
  close_second.set_stream_id(second.stream_id());
  EXPECT_EQ(session.CloseObservation(close_second).diagnostic().code(), "gw.observation.closed");
  EXPECT_EQ(session.snapshot().active_streams, 0U);
}

TEST(XcomToolGatewayLifecycle, LeaseReleaseRequiresExactIdentity) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::AcquireLeaseRequest lease;
  lease.set_session_id(std::string(kSessionId));
  lease.set_endpoint_id("svc.alpha");
  lease.set_endpoint_generation(3U);
  lease.set_plan_digest("plan-1");
  lease.set_lease_millis(500U);
  lease.set_deadline_millis(1000U);
  const v1::AcquireLeaseResponse acquired = session.AcquireLease(lease);
  ASSERT_EQ(acquired.state(), v1::LEASE_ACTIVE);
  ASSERT_FALSE(acquired.lease_id().empty());

  v1::ReleaseLeaseRequest wrong;
  wrong.set_session_id(std::string(kSessionId));
  wrong.set_lease_id("wrong-lease-identity");
  EXPECT_NE(session.ReleaseLease(wrong).state(), v1::LEASE_RELEASED);
  EXPECT_TRUE(session.snapshot().lease_held);

  v1::ReleaseLeaseRequest exact;
  exact.set_session_id(std::string(kSessionId));
  exact.set_lease_id(acquired.lease_id());
  EXPECT_EQ(session.ReleaseLease(exact).state(), v1::LEASE_RELEASED);
  EXPECT_FALSE(session.snapshot().lease_held);
}

TEST(XcomToolGatewayLifecycle, IdleTimeoutTracksLastActivity) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  fixture.clock().set(600);
  ASSERT_EQ(session.SubmitStimulation(stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL,
                                                          "61"))
                .outcome()
                .kind(),
            v1::STIMULATION_OUTCOME_EMITTED);

  session.on_idle_tick(1200);
  EXPECT_FALSE(session.snapshot().terminal);
  session.on_idle_tick(1600);
  EXPECT_TRUE(session.snapshot().terminal);
}
