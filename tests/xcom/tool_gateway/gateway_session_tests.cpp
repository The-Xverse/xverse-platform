/**
 * @file gateway_session_tests.cpp
 * @brief T031 gateway-session unit cases: protocol negotiation, the committed operation surface,
 *        exact-permit arming, terminal revocation, and bounded session counters.
 * @ownership Each case owns one bounded gateway fixture and one bounded session.
 * @lifetime The fixture outlives the session under test.
 * @thread_safety Single-threaded.
 * @bounds <= 64 operations, <= 4 streams, no retained payload byte, no wall-clock dependence.
 * @failure Any mismatch or unexpected emission fails the owning case closed.
 * @par Traceability
 * Supports T031-SR-001, T031-SR-002, T031-SR-003, T031-SR-004, T031-SR-013, T031-SR-015,
 * T031-SR-021 and the T31-TS-001..T31-TS-006 cases.
 */

#include <gtest/gtest.h>

#include "gateway_support.hpp"

#include <google/protobuf/descriptor.h>

#include <cstddef>
#include <string>

namespace {

namespace v1 = xverse::xcom::v1;
using xverse::xcom::GatewayOutcome;
using xverse::xcom::GatewaySession;
using xverse::xcom::gateway_operation_names;
using xverse::xcom::tool_gateway_test::arm_request;
using xverse::xcom::tool_gateway_test::GatewayFixture;
using xverse::xcom::tool_gateway_test::stimulation_request;

constexpr std::size_t kExpectedOperations = 10U;

}  // namespace

TEST(XcomToolGatewaySession, VersionNegotiationAcceptsSupportedMajor) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  peer.set_minor(99U);
  EXPECT_EQ(session.negotiate(peer), GatewayOutcome::accepted);
  const xverse::xcom::GatewaySessionSnapshot snapshot = session.snapshot();
  EXPECT_TRUE(snapshot.negotiated);
  EXPECT_EQ(snapshot.negotiation, GatewayOutcome::accepted);
  const v1::QueryVersionResponse version = session.QueryVersion(v1::QueryVersionRequest{});
  EXPECT_EQ(version.protocol().major(), 1U);
  EXPECT_EQ(version.protocol().minor(), 1U);
}

TEST(XcomToolGatewaySession, VersionNegotiationRejectsUnsupportedMajor) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  v1::ProtocolVersion peer;
  peer.set_major(2U);
  peer.set_minor(0U);
  EXPECT_EQ(session.negotiate(peer), GatewayOutcome::rejected);
  const xverse::xcom::GatewaySessionSnapshot snapshot = session.snapshot();
  EXPECT_FALSE(snapshot.negotiated);
  EXPECT_EQ(snapshot.negotiation, GatewayOutcome::rejected);
}

TEST(XcomToolGatewaySession, OperationSurfaceMatchesContract) {
  const auto operations = gateway_operation_names();
  ASSERT_EQ(operations.size(), kExpectedOperations);
  const google::protobuf::FileDescriptor *file =
      google::protobuf::DescriptorPool::generated_pool()->FindFileByName(
          "xverse/xcom/v1/tool_gateway.proto");
  ASSERT_NE(file, nullptr);
  const google::protobuf::ServiceDescriptor *service = file->FindServiceByName("ToolGateway");
  ASSERT_NE(service, nullptr);
  ASSERT_EQ(service->method_count(), static_cast<int>(kExpectedOperations));
  for (std::size_t index = 0U; index < operations.size(); ++index) {
    EXPECT_EQ(operations[index], service->method(static_cast<int>(index))->name())
        << "operation table differs from the T030 descriptor method set at index " << index;
  }
}

TEST(XcomToolGatewaySession, ArmRequiresExactPermit) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  peer.set_minor(0U);
  ASSERT_EQ(session.negotiate(peer), GatewayOutcome::accepted);

  const v1::ArmSessionResponse armed = session.ArmSession(arm_request());
  EXPECT_EQ(armed.state(), v1::SESSION_ARMED);
  const xverse::xcom::GatewaySessionSnapshot armed_snapshot = session.snapshot();
  EXPECT_TRUE(armed_snapshot.armed);
  EXPECT_GT(armed_snapshot.requests_authorized, 0U);

  std::uint64_t identity = 101U;
  for (const v1::StimulationActionKind kind :
       {v1::STIMULATION_ACTION_INJECT_SIGNAL, v1::STIMULATION_ACTION_INJECT_MESSAGE,
        v1::STIMULATION_ACTION_INVOKE_SERVICE, v1::STIMULATION_ACTION_EMULATE_SERVICE}) {
    const v1::SubmitStimulationResponse submitted =
        session.SubmitStimulation(stimulation_request(kind, std::to_string(identity)));
    EXPECT_EQ(submitted.outcome().kind(), v1::STIMULATION_OUTCOME_EMITTED)
        << "declared action kind " << static_cast<int>(kind) << " did not route to emission";
    ++identity;
  }
  EXPECT_EQ(fixture.emitter().calls, 4U);

  GatewayFixture mismatched;
  ASSERT_TRUE(mismatched.ready());
  ASSERT_TRUE(mismatched.open_path());
  GatewaySession other(mismatched.config(), mismatched.dependencies(), mismatched.binding());
  ASSERT_EQ(other.negotiate(peer), GatewayOutcome::accepted);
  v1::ArmSessionRequest invalid = arm_request();
  invalid.set_permit_id("not-the-bound-permit");
  const v1::ArmSessionResponse rejected = other.ArmSession(invalid);
  EXPECT_EQ(rejected.state(), v1::SESSION_DECLARED);
  EXPECT_FALSE(other.snapshot().armed);
}

TEST(XcomToolGatewaySession, RevokeTerminalState) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  ASSERT_EQ(session.negotiate(peer), GatewayOutcome::accepted);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::RevokeSessionRequest revoke;
  revoke.set_session_id(std::string(xverse::xcom::tool_gateway_test::kSessionId));
  revoke.set_reason_code("operator");
  EXPECT_EQ(session.RevokeSession(revoke).state(), v1::SESSION_REVOKED);
  EXPECT_TRUE(session.snapshot().terminal);

  const v1::RevokeSessionResponse repeated = session.RevokeSession(revoke);
  EXPECT_NE(repeated.state(), v1::SESSION_REVOKED);
  EXPECT_EQ(repeated.diagnostic().code(), "gw.session.revoke.declined");
}

TEST(XcomToolGatewaySession, QuerySessionCountersBounded) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  ASSERT_EQ(session.negotiate(peer), GatewayOutcome::accepted);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::QuerySessionRequest query;
  query.set_session_id(std::string(xverse::xcom::tool_gateway_test::kSessionId));
  const v1::QuerySessionResponse response = session.QuerySession(query);
  EXPECT_EQ(response.state(), v1::SESSION_ARMED);
  EXPECT_GT(response.counters().requests_received(), 0U);
  EXPECT_GT(response.counters().requests_authorized(), 0U);
  EXPECT_EQ(response.counters().evidence_incomplete(), 0U);
  const xverse::xcom::GatewaySessionSnapshot snapshot = session.snapshot();
  EXPECT_EQ(snapshot.evidence_incomplete, 0U);
  EXPECT_EQ(snapshot.last_pending_outcome, GatewayOutcome::accepted);
}
