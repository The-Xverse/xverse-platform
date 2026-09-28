/**
 * @file gateway_logging_tests.cpp
 * @brief T031 gateway-logging unit cases: a payload-bearing stimulation never places a payload
 *        byte in a log record, and no log record carries permit contents.
 * @ownership Each case owns one bounded gateway fixture, one session, and one log capture.
 * @lifetime The fixture outlives the session under test.
 * @thread_safety Single-threaded.
 * @bounds <= 32 log records, <= 64 operations, no retained payload byte.
 * @failure Any payload byte or permit identity in a log record fails the owning case closed.
 * @par Traceability
 * Supports T031-SR-014 and the T31-TS-023..T31-TS-024 cases.
 */

#include <gtest/gtest.h>

#include "gateway_support.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace {

namespace v1 = xverse::xcom::v1;
using xverse::xcom::GatewayOutcome;
using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::arm_request;
using xverse::xcom::tool_gateway_test::GatewayFixture;
using xverse::xcom::tool_gateway_test::kPermitId;
using xverse::xcom::tool_gateway_test::stimulation_request;

void negotiate_accepted(GatewaySession &session) {
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  peer.set_minor(0U);
  ASSERT_EQ(session.negotiate(peer), GatewayOutcome::accepted);
}

}  // namespace

TEST(XcomToolGatewayLogging, PayloadNeverLogged) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  constexpr std::string_view kSentinel = "SENTINEL-PAYLOAD-9F3";
  v1::SubmitStimulationRequest submitted =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "11");
  submitted.set_payload(std::string(kSentinel));
  submitted.set_payload_bytes(static_cast<std::uint32_t>(kSentinel.size()));
  ASSERT_EQ(session.SubmitStimulation(submitted).outcome().kind(),
            v1::STIMULATION_OUTCOME_EMITTED);
  EXPECT_EQ(fixture.emitter().last_payload_size, kSentinel.size());

  const std::vector<xverse::xcom::tool_gateway_test::OwnedLogRecord> records =
      fixture.log().records();
  ASSERT_FALSE(records.empty());
  for (const auto &record : records) {
    EXPECT_EQ(record.code.find(kSentinel), std::string::npos);
    EXPECT_EQ(record.identity.find(kSentinel), std::string::npos);
  }
}

TEST(XcomToolGatewayLogging, PermitContentsNeverLogged) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);
  ASSERT_EQ(session.SubmitStimulation(stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "12"))
                .outcome()
                .kind(),
            v1::STIMULATION_OUTCOME_EMITTED);

  const std::vector<xverse::xcom::tool_gateway_test::OwnedLogRecord> records =
      fixture.log().records();
  ASSERT_FALSE(records.empty());
  for (const auto &record : records) {
    EXPECT_EQ(record.code.find(kPermitId), std::string::npos);
    EXPECT_EQ(record.identity.find(kPermitId), std::string::npos);
  }
}
