/**
 * @file gateway_bounds_tests.cpp
 * @brief T031 gateway-bounds unit cases: message-size bound, deadline enforcement before
 *        emission, bounded flow control, and the bounded observation record queue.
 * @ownership Each case owns one bounded gateway fixture and one bounded session.
 * @lifetime The fixture outlives the session under test.
 * @thread_safety Single-threaded.
 * @bounds <= 64 operations, <= 4 streams, <= 32 frame bytes per crafted buffer, no wall-clock
 *         dependence.
 * @failure An over-bound message, an overdue request, or a saturated queue that still emits or
 *          grows unbounded fails the owning case closed.
 * @par Traceability
 * Supports T031-SR-005, T031-SR-006, T031-SR-007, T031-SR-010, T031-SR-016 and the
 * T31-TS-007..T31-TS-010 cases.
 */

#include <gtest/gtest.h>

#include "gateway_support.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace v1 = xverse::xcom::v1;
using xverse::xcom::GatewayFrameStatus;
using xverse::xcom::GatewayFrameView;
using xverse::xcom::GatewayOutcome;
using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::arm_request;
using xverse::xcom::tool_gateway_test::GatewayFixture;
using xverse::xcom::tool_gateway_test::kSessionId;
using xverse::xcom::tool_gateway_test::stimulation_request;

void append_u16(std::vector<std::byte> &bytes, std::uint16_t value) {
  bytes.push_back(static_cast<std::byte>((value >> 8U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>(value & 0xFFU));
}

void append_u32(std::vector<std::byte> &bytes, std::uint32_t value) {
  bytes.push_back(static_cast<std::byte>((value >> 24U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>((value >> 16U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>((value >> 8U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>(value & 0xFFU));
}

std::vector<std::byte> make_frame(std::string_view method, std::string_view payload) {
  std::vector<std::byte> bytes;
  append_u32(bytes, static_cast<std::uint32_t>(2U + method.size() + payload.size()));
  append_u16(bytes, static_cast<std::uint16_t>(method.size()));
  for (const char character : method) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  for (const char character : payload) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  return bytes;
}

void negotiate_accepted(GatewaySession &session) {
  v1::ProtocolVersion peer;
  peer.set_major(1U);
  peer.set_minor(0U);
  ASSERT_EQ(session.negotiate(peer), GatewayOutcome::accepted);
}

}  // namespace

TEST(XcomToolGatewayBounds, MessageSizeBoundEnforced) {
  const xverse::xcom::GatewayConfig config = xverse::xcom::tool_gateway_test::make_config(32U);
  const std::vector<std::byte> accepted = make_frame("QueryVersion", std::string(18U, 'x'));
  GatewayFrameView view{};
  EXPECT_EQ(xverse::xcom::gateway_decode_request_frame(config, accepted, view),
            GatewayFrameStatus::ok);
  EXPECT_EQ(view.method, "QueryVersion");
  EXPECT_EQ(view.payload.size(), 18U);

  const std::vector<std::byte> over_bound = make_frame("QueryVersion", std::string(32U, 'x'));
  GatewayFrameView rejected{};
  EXPECT_EQ(xverse::xcom::gateway_decode_request_frame(config, over_bound, rejected),
            GatewayFrameStatus::over_bound);

  const std::vector<std::byte> unknown = make_frame("NotAMethod", std::string(1U, 'x'));
  GatewayFrameView unknown_view{};
  EXPECT_EQ(xverse::xcom::gateway_decode_request_frame(config, unknown, unknown_view),
            GatewayFrameStatus::unknown_method);
}

TEST(XcomToolGatewayBounds, DeadlineEnforcedBeforeEmission) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);
  ASSERT_EQ(session.ArmSession(arm_request()).state(), v1::SESSION_ARMED);

  fixture.clock().set(5000);
  const v1::SubmitStimulationResponse submitted =
      session.SubmitStimulation(stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "7"));
  EXPECT_EQ(submitted.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(fixture.emitter().calls, 0U);
  EXPECT_EQ(session.snapshot().emitted, 0U);
}

TEST(XcomToolGatewayBounds, FlowControlWindowBounded) {
  const xverse::xcom::GatewayConfig config =
      xverse::xcom::tool_gateway_test::make_config(4096U, 8U, 4U, 1U);
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  GatewaySession session(config, fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);

  v1::QuerySessionRequest query;
  query.set_session_id(std::string(kSessionId));
  EXPECT_EQ(session.QuerySession(query).state(), v1::SESSION_DECLARED);
  EXPECT_EQ(session.snapshot().flow_tokens, 0U);

  const v1::QuerySessionResponse saturated = session.QuerySession(query);
  EXPECT_EQ(saturated.diagnostic().code(), "gw.query.declined");
  EXPECT_EQ(session.snapshot().flow_rejections, 1U);
  EXPECT_EQ(session.snapshot().flow_tokens, 0U);
}

TEST(XcomToolGatewayBounds, ObservationQueueBounded) {
  const xverse::xcom::GatewayConfig config =
      xverse::xcom::tool_gateway_test::make_config(4096U, 8U, 4U, 8U, 100000U, 1000U, 2U);
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  GatewaySession session(config, fixture.dependencies(), fixture.binding());
  negotiate_accepted(session);

  v1::OpenObservationRequest open;
  open.set_tap_id("gateway.tap");
  open.set_max_records(1000U);
  open.set_deadline_millis(1000U);
  const v1::OpenObservationResponse opened = session.OpenObservation(open);
  ASSERT_FALSE(opened.stream_id().empty());
  EXPECT_EQ(opened.granted_max_records(), 2U);

  v1::ReadObservationsRequest read;
  read.set_stream_id(opened.stream_id());
  read.set_max_records(1000U);
  std::array<v1::ObservationRecord, 5U> records{};
  const std::size_t delivered = session.ReadObservations(read, records);
  EXPECT_LE(delivered, 2U);
  EXPECT_LE(delivered, records.size());
}
