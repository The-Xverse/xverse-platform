/**
 * @file gateway_negative_tests.cpp
 * @brief T031 gateway negative cases: an over-bound payload is rejected before emission, an
 *        unarmed/expired session emits nothing, an unsupported major reaches no operation, local
 *        transport access does not authorize, and the production source contains no TCP/DNS/TLS
 *        facility token.
 * @ownership Each case owns one bounded gateway fixture, one session, and its local scan buffers.
 * @lifetime The fixture outlives the session under test.
 * @thread_safety Single-threaded.
 * @bounds <= 32 operations, one source read per scan, no network or external access.
 * @failure Any partial acceptance, emitted item, or forbidden API token fails the owning case
 *          closed.
 * @par Traceability
 * Supports T031-SR-003, T031-SR-004, T031-SR-005, T031-SR-008, T031-SR-009, T031-SR-011,
 * T031-SR-018 and the T31-TS-018..T31-TS-022 cases.
 */

#include <gtest/gtest.h>

#include "gateway_support.hpp"

#include <array>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace v1 = xverse::xcom::v1;
using xverse::xcom::GatewayOutcome;
using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::arm_request;
using xverse::xcom::tool_gateway_test::GatewayFixture;
using xverse::xcom::tool_gateway_test::stimulation_request;

void negotiate_accepted(GatewaySession &session) {
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  peer.set_minor(0U);
  ASSERT_EQ(session.negotiate(peer), GatewayOutcome::accepted);
}

std::string read_text_file(const char *path) {
  std::ifstream stream(path);
  std::ostringstream buffer;
  buffer << stream.rdbuf();
  return buffer.str();
}

}  // namespace

TEST(XcomToolGatewayNegative, OverBoundMessageRejected) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  const v1::SubmitStimulationResponse over_bound = session.SubmitStimulation(
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "3",
                          static_cast<std::uint32_t>(fixture.config().max_payload_bytes() + 1U)));
  EXPECT_EQ(over_bound.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(over_bound.diagnostic().code(), "gw.payload.overbound");
  EXPECT_EQ(fixture.emitter().calls, 0U);
  EXPECT_EQ(session.snapshot().emitted, 0U);
}

TEST(XcomToolGatewayNegative, ExpiredSessionRejectedZeroEmission) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);

  const v1::SubmitStimulationResponse unauthorized =
      session.SubmitStimulation(stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "4"));
  EXPECT_EQ(unauthorized.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(unauthorized.diagnostic().code(), "gw.session.notarmed");
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomToolGatewayNegative, UnsupportedMajorRejectedNoItem) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  v1::ProtocolVersion peer;
  peer.set_major(3U);
  EXPECT_EQ(session.negotiate(peer), GatewayOutcome::rejected);

  EXPECT_FALSE(session.ArmSession(arm_request()).state() == v1::SESSION_ARMED);
  EXPECT_EQ(session.SubmitStimulation(stimulation_request()).outcome().kind(),
            v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(fixture.emitter().calls, 0U);
  EXPECT_EQ(session.snapshot().emitted, 0U);
}

TEST(XcomToolGatewayNegative, TransportAccessDoesNotAuthorize) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  xverse::xcom::GatewaySessionBinding binding = fixture.binding();
  binding.has_permit = false;
  GatewaySession session(fixture.config(), fixture.dependencies(), binding);
  negotiate_accepted(session);

  const v1::ArmSessionResponse armed = session.ArmSession(arm_request());
  EXPECT_EQ(armed.diagnostic().code(), "gw.permit.absent");
  EXPECT_FALSE(session.snapshot().armed);

  const v1::SubmitStimulationResponse submitted =
      session.SubmitStimulation(stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "5"));
  EXPECT_EQ(submitted.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomToolGatewayNegative, IncompatibleInteractionRejectedZeroSideEffects) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::SubmitStimulationRequest request =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "21");
  request.set_interaction(v1::INTERACTION_KIND_RESPONSE);
  const v1::SubmitStimulationResponse response = session.SubmitStimulation(request);
  EXPECT_EQ(response.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(response.diagnostic().code(), "gw.stimulation.interaction");
  EXPECT_EQ(fixture.emitter().calls, 0U);
  EXPECT_EQ(session.snapshot().pending_requests, 0U);
}

TEST(XcomToolGatewayNegative, IncompatibleDirectionRejectedZeroSideEffects) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::SubmitStimulationRequest request =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "22");
  request.set_direction(v1::DIRECTION_INBOUND);
  const v1::SubmitStimulationResponse response = session.SubmitStimulation(request);
  EXPECT_EQ(response.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(response.diagnostic().code(), "gw.stimulation.direction");
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomToolGatewayNegative, UnknownScheduleModeRejectedZeroSideEffects) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::SubmitStimulationRequest request =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "23");
  request.mutable_schedule()->set_mode(static_cast<v1::ScheduleMode>(99));
  const v1::SubmitStimulationResponse response = session.SubmitStimulation(request);
  EXPECT_EQ(response.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(response.diagnostic().code(), "gw.schedule.unknown");
  EXPECT_EQ(fixture.emitter().calls, 0U);
  EXPECT_EQ(session.snapshot().pending_requests, 0U);
}

TEST(XcomToolGatewayNegative, UnmappedClockRejectedZeroSideEffects) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::SubmitStimulationRequest request =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "24");
  request.mutable_schedule()->set_clock_domain("unmapped.foreign");
  const v1::SubmitStimulationResponse response = session.SubmitStimulation(request);
  EXPECT_EQ(response.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(response.diagnostic().code(), "gw.clock.unmapped");
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomToolGatewayNegative, ContractMismatchRejectedZeroSideEffects) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::SubmitStimulationRequest request =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "25");
  request.set_contract_id("other.contract");
  const v1::SubmitStimulationResponse response = session.SubmitStimulation(request);
  EXPECT_EQ(response.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(response.diagnostic().code(), "gw.contract.mismatch");
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomToolGatewayNegative, UnauthorizedScheduledTargetNotQueued) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  v1::SubmitStimulationRequest request =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "26");
  request.set_target_endpoint("unauthorized.target");
  request.mutable_schedule()->set_mode(v1::SCHEDULE_SCHEDULED);
  const v1::SubmitStimulationResponse response = session.SubmitStimulation(request);
  EXPECT_EQ(response.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(session.snapshot().pending_requests, 0U);
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomToolGatewayNegative, NoInetOrDnsOrTlsApi) {
  const std::string header = read_text_file(XCOM_T031_HEADER_PATH);
  const std::string source = read_text_file(XCOM_T031_SOURCE_PATH);
  ASSERT_FALSE(header.empty());
  ASSERT_FALSE(source.empty());

  const std::array<std::string_view, 12U> forbidden = {
      "AF_INET", "sockaddr_in", "in_addr", "getaddrinfo", "gethostbyname",
      "inet_addr", "inet_ntoa", "res_query", "SSL_", "TLS_", "tls_", "openssl"};
  for (const std::string_view token : forbidden) {
    EXPECT_EQ(header.find(token), std::string::npos) << "header contains " << token;
    EXPECT_EQ(source.find(token), std::string::npos) << "source contains " << token;
  }
}
