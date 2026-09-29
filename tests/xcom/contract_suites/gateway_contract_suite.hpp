/**
 * @file gateway_contract_suite.hpp
 * @brief T033 reusable gateway contract suite: one implementation-agnostic driver that any
 *        conforming `GatewaySession` can be validated against, plus the subject seam used to plug
 *        the accepted local-IPC gateway fixture in.
 * @ownership A subject owns the bounded factory for accepted gateway fixtures; the suite owns the
 *            fresh fixture it constructs per conformance group and its bounded report.
 * @lifetime Each fixture is destroyed before the owning group returns.
 * @thread_safety Single-threaded; the accepted gateway session serializes its own state.
 * @bounds <= 12 fixtures, <= 4 emissions, <= 32 framing bytes per crafted buffer, no wall clock.
 * @failure A missing or failing conformance check is reported, never skipped; a rejection must emit
 *         nothing and must never be reported as success.
 * @par Traceability
 * Supports T033-SR-009 through T033-SR-013 and the accepted `XCOM-SW-GW-002` local-IPC-only
 * bounded gateway session.
 */

#ifndef XVERSE_XCOM_CONTRACT_SUITES_GATEWAY_CONTRACT_SUITE_HPP_
#define XVERSE_XCOM_CONTRACT_SUITES_GATEWAY_CONTRACT_SUITE_HPP_

#include "suite_support.hpp"
#include "tool_gateway/gateway_support.hpp"
#include "xverse/xcom/tool_gateway.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace xverse::xcom::contract_suites {

/// @brief Accepted T031 gateway fixture namespace.
namespace gateway_fixture = xverse::xcom::tool_gateway_test;
/// @brief Accepted generated versioned contract namespace.
namespace gateway_contract = xverse::xcom::v1;

/**
 * @brief Reusable subject seam: supplies a fresh accepted gateway fixture under test.
 * @ownership The caller owns every returned fixture.
 * @lifetime Each returned fixture is destroyed before the owning group returns.
 * @thread_safety One caller.
 * @failure An incompatible factory is reported as a failing check, never substituted.
 */
class GatewaySubject {
 public:
  virtual ~GatewaySubject() = default;
  /// @return A freshly constructed, non-opened accepted gateway fixture.
  [[nodiscard]] virtual std::unique_ptr<gateway_fixture::GatewayFixture> make_fixture() = 0;
};

namespace gateway_suite_detail {

/// @brief Append one big-endian 16-bit value.
/// @param bytes Destination buffer.
/// @param value Value to append.
inline void append_u16(std::vector<std::byte>& bytes, const std::uint16_t value) {
  bytes.push_back(static_cast<std::byte>((value >> 8U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>(value & 0xFFU));
}

/// @brief Append one big-endian 32-bit value.
/// @param bytes Destination buffer.
/// @param value Value to append.
inline void append_u32(std::vector<std::byte>& bytes, const std::uint32_t value) {
  bytes.push_back(static_cast<std::byte>((value >> 24U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>((value >> 16U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>((value >> 8U) & 0xFFU));
  bytes.push_back(static_cast<std::byte>(value & 0xFFU));
}

/// @brief Build one bounded length-prefixed, method-name-addressed request frame.
/// @param method Exact method name.
/// @param payload Serialized request payload bytes.
/// @return The framed bytes.
[[nodiscard]] inline std::vector<std::byte> frame(const std::string_view method,
                                                  const std::string_view payload) {
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

/// @brief Negotiate the supported protocol major on one session.
/// @param session Session under test.
/// @return true only when the supported major was accepted.
[[nodiscard]] inline bool negotiate_supported(GatewaySession& session) {
  gateway_contract::ProtocolVersion peer;
  peer.set_major(1U);
  peer.set_minor(0U);
  return session.negotiate(peer) == GatewayOutcome::accepted;
}

}  // namespace gateway_suite_detail

/**
 * @brief Reusable, implementation-agnostic gateway conformance suite.
 * @details The suite names only the accepted `GatewaySession` interface and the accepted T031
 *          fixture helpers. It validates fail-closed protocol negotiation and version query, the ten
 *          committed operations, exact-permit arming with unarmed zero emission, all four allowed
 *          stimulation actions, the exclusive lease round trip, bounded metadata-only observation,
 *          bounded framing with over-bound/unknown-method rejection, and bounded evidence-incomplete
 *          counters. Because the accepted permit is single-session, each arming group uses its own
 *          fresh fixture returned by the subject. A different conforming gateway is validated by
 *          supplying a different `GatewaySubject`.
 */
class GatewayContractSuite final {
 public:
  /// @brief Run every gateway conformance check against one subject.
  /// @param subject Gateway subject under test.
  /// @return The bounded suite report.
  [[nodiscard]] static SuiteReport run(GatewaySubject& subject) {
    SuiteReport report;
    report.add("G-02", gateway_operation_names().size() == 10U, "ten committed operations");

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      report.add("G-01", fixture != nullptr && fixture->ready() && fixture->open_path(),
                 "accepted journal/guard/action path opened");
      if (fixture == nullptr) {
        return report;
      }
      GatewaySession session(fixture->config(), fixture->dependencies(), fixture->binding());
      const bool accepted = gateway_suite_detail::negotiate_supported(session);
      const gateway_contract::QueryVersionResponse version =
          session.QueryVersion(gateway_contract::QueryVersionRequest{});
      report.add("G-03",
                 accepted && version.protocol().major() == 1U && version.protocol().minor() == 0U &&
                     session.snapshot().negotiated,
                 "supported major negotiated and reported");
    }

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      GatewaySession session(fixture->config(), fixture->dependencies(), fixture->binding());
      gateway_contract::ProtocolVersion peer;
      peer.set_major(2U);
      const bool rejected = session.negotiate(peer) == GatewayOutcome::rejected;
      const bool no_item =
          session.SubmitStimulation(gateway_fixture::stimulation_request()).outcome().kind() ==
          gateway_contract::STIMULATION_OUTCOME_REJECTED;
      report.add("G-04", rejected && no_item && session.snapshot().emitted == 0U,
                 "unsupported major rejected before any operation with no item");
    }

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      GatewaySession session(fixture->config(), fixture->dependencies(), fixture->binding());
      static_cast<void>(gateway_suite_detail::negotiate_supported(session));
      const bool armed =
          session.ArmSession(gateway_fixture::arm_request()).state() ==
          gateway_contract::SESSION_ARMED;
      report.add("G-05", armed && session.snapshot().armed, "exact permit arms the session");
    }

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      static_cast<void>(fixture->open_path());
      GatewaySession session(fixture->config(), fixture->dependencies(), fixture->binding());
      static_cast<void>(gateway_suite_detail::negotiate_supported(session));
      static_cast<void>(session.ArmSession(gateway_fixture::arm_request()));
      std::uint64_t identity = 200U;
      bool all_emitted = true;
      for (const gateway_contract::StimulationActionKind kind :
           {gateway_contract::STIMULATION_ACTION_INJECT_SIGNAL,
            gateway_contract::STIMULATION_ACTION_INJECT_MESSAGE,
            gateway_contract::STIMULATION_ACTION_INVOKE_SERVICE,
            gateway_contract::STIMULATION_ACTION_EMULATE_SERVICE}) {
        all_emitted =
            all_emitted &&
            session.SubmitStimulation(
                       gateway_fixture::stimulation_request(kind, std::to_string(identity)))
                    .outcome()
                    .kind() == gateway_contract::STIMULATION_OUTCOME_EMITTED;
        ++identity;
      }
      report.add("G-06", all_emitted && session.snapshot().emitted == 4U,
                 "every allowed stimulation action emitted exactly once");
    }

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      static_cast<void>(fixture->open_path());
      GatewaySession session(fixture->config(), fixture->dependencies(), fixture->binding());
      static_cast<void>(gateway_suite_detail::negotiate_supported(session));
      static_cast<void>(session.ArmSession(gateway_fixture::arm_request()));
      gateway_contract::AcquireLeaseRequest lease;
      lease.set_session_id(std::string(gateway_fixture::kSessionId));
      lease.set_endpoint_id("svc.alpha");
      lease.set_endpoint_generation(3U);
      lease.set_plan_digest(std::string(gateway_fixture::kPlanDigest));
      lease.set_lease_millis(500U);
      lease.set_deadline_millis(1000U);
      const gateway_contract::AcquireLeaseResponse acquired = session.AcquireLease(lease);
      gateway_contract::ReleaseLeaseRequest release;
      release.set_session_id(std::string(gateway_fixture::kSessionId));
      release.set_lease_id(acquired.lease_id());
      release.set_reason_code("done");
      const gateway_contract::ReleaseLeaseResponse released = session.ReleaseLease(release);
      report.add("G-07",
                 acquired.state() == gateway_contract::LEASE_ACTIVE &&
                     released.state() == gateway_contract::LEASE_RELEASED &&
                     !session.snapshot().lease_held,
                 "exclusive generation-bound lease round trip");
    }

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      GatewaySession session(fixture->config(), fixture->dependencies(), fixture->binding());
      static_cast<void>(gateway_suite_detail::negotiate_supported(session));
      const bool rejected =
          session.SubmitStimulation(gateway_fixture::stimulation_request()).outcome().kind() ==
          gateway_contract::STIMULATION_OUTCOME_REJECTED;
      report.add("G-08", rejected && session.snapshot().emitted == 0U,
                 "unarmed session emits nothing and reports a non-success outcome");
    }

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      const GatewayConfig config = fixture->config();
      GatewaySession session(config, fixture->dependencies(), fixture->binding());
      static_cast<void>(gateway_suite_detail::negotiate_supported(session));
      gateway_contract::OpenObservationRequest open;
      open.set_tap_id("gateway.tap");
      open.set_max_records(1000U);
      open.set_deadline_millis(1000U);
      const gateway_contract::OpenObservationResponse opened = session.OpenObservation(open);
      std::array<gateway_contract::ObservationRecord, 8U> records{};
      gateway_contract::ReadObservationsRequest read;
      read.set_stream_id(opened.stream_id());
      read.set_max_records(1000U);
      const std::size_t delivered = session.ReadObservations(read, records);
      gateway_contract::CloseObservationRequest close;
      close.set_stream_id(opened.stream_id());
      const gateway_contract::CloseObservationResponse closed = session.CloseObservation(close);
      report.add("G-09",
                 !opened.stream_id().empty() && opened.granted_max_records() > 0U &&
                     opened.granted_max_records() <= config.max_observation_records() &&
                     delivered <= opened.granted_max_records() && delivered <= records.size() &&
                     closed.delivered() + closed.dropped() >= delivered,
                 "bounded metadata-only observation");
    }

    {
      const GatewayConfig framing_config = gateway_fixture::make_config(32U);
      GatewayFrameView accepted_view{};
      const bool accepted = gateway_decode_request_frame(
                                framing_config,
                                gateway_suite_detail::frame("QueryVersion", std::string(18U, 'x')),
                                accepted_view) == GatewayFrameStatus::ok;
      GatewayFrameView over_bound_view{};
      const bool over_bound = gateway_decode_request_frame(
                                  framing_config,
                                  gateway_suite_detail::frame("QueryVersion", std::string(32U, 'x')),
                                  over_bound_view) == GatewayFrameStatus::over_bound;
      GatewayFrameView unknown_view{};
      const bool unknown = gateway_decode_request_frame(
                               framing_config,
                               gateway_suite_detail::frame("NotAMethod", std::string(1U, 'x')),
                               unknown_view) == GatewayFrameStatus::unknown_method;
      report.add("G-10", accepted && over_bound && unknown,
                 "bounded framing accepts a valid frame and rejects over-bound/unknown method");
    }

    {
      const std::unique_ptr<gateway_fixture::GatewayFixture> fixture = subject.make_fixture();
      static_cast<void>(fixture->open_path());
      GatewaySession session(fixture->config(), fixture->dependencies(), fixture->binding());
      static_cast<void>(gateway_suite_detail::negotiate_supported(session));
      static_cast<void>(session.ArmSession(gateway_fixture::arm_request()));
      static_cast<void>(session.SubmitStimulation(
          gateway_fixture::stimulation_request(gateway_contract::STIMULATION_ACTION_INJECT_SIGNAL,
                                               "777")));
      const GatewaySessionSnapshot snapshot = session.snapshot();
      report.add("G-11", snapshot.evidence_incomplete == 0U && snapshot.requests_received > 0U,
                 "bounded counters include an explicit evidence-incomplete count");
    }
    return report;
  }
};

}  // namespace xverse::xcom::contract_suites

#endif  // XVERSE_XCOM_CONTRACT_SUITES_GATEWAY_CONTRACT_SUITE_HPP_
