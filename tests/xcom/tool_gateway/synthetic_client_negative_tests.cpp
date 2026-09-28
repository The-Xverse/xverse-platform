/**
 * @file synthetic_client_negative_tests.cpp
 * @brief T032 separate-process synthetic-client negative cases: the local endpoint family is
 *        `AF_UNIX` only with no non-local listener, an invalid/substituted permit and an expired
 *        session emit zero items, an unsupported protocol major fails closed before any emission,
 *        and the committed client source references no non-local, resolver, transport-security,
 *        dynamic-load, or external-process facility.
 * @ownership Each case owns one `SyntheticClientFixture`, one accepted `GatewaySession`, and its
 *            bounded scratch endpoint; the launched fixture process is reaped within a bounded wait.
 * @lifetime The fixture and session outlive the harness call and unlink their scratch path on
 *           destruction.
 * @thread_safety Single-threaded; the owned fixture child runs as a separate process.
 * @bounds One socket and one peer per case; no network peer is contacted.
 * @failure A non-local family, a permit bypass, an emitted invalid-session item, an implicit
 *          version acceptance, or a forbidden client token fails the owning case closed.
 * @par Traceability
 * Supports T032-SR-003, T032-SR-004, T032-SR-009, T032-SR-010, T032-SR-012, T032-SR-017 and cases
 * T32-TS-015..T32-TS-019.
 */

#include <gtest/gtest.h>

#include "synthetic_client_support.hpp"

#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include <sys/socket.h>

namespace {

using xverse::xcom::GatewaySession;
using xverse::xcom::GatewaySessionBinding;
using xverse::xcom::LocalIpcEndpoint;
using xverse::xcom::tool_gateway_test::client_scratch_path;
using xverse::xcom::tool_gateway_test::ClientRunResult;
using xverse::xcom::tool_gateway_test::ClientServerMode;
using xverse::xcom::tool_gateway_test::field_value;
using xverse::xcom::tool_gateway_test::find_method_line;
using xverse::xcom::tool_gateway_test::run_client_case;
using xverse::xcom::tool_gateway_test::SyntheticClientFixture;

/// @brief Runs one bounded stimulation case and asserts the client stopped with zero emission.
/// @param socket_name Unique bounded scratch name.
/// @return The bounded observed result.
[[nodiscard]] ClientRunResult run_zero_emission(const std::string &socket_name,
                                                SyntheticClientFixture &fixture,
                                                const GatewaySessionBinding &binding) {
  GatewaySession session(fixture.config(), fixture.dependencies(), binding);
  return run_client_case(session, fixture.config(), fixture.hub(), socket_name, "stimulate_signal",
                         ClientServerMode::dispatch, 4096U, 1000U, 500U);
}

}  // namespace

TEST(XcomSyntheticClientNegative, NoTcpListenerForClientEndpoint) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  const std::string path = client_scratch_path("neg-local.sock");
  const std::optional<LocalIpcEndpoint> endpoint = LocalIpcEndpoint::create(fixture.config(), path);
  ASSERT_TRUE(endpoint.has_value());
  EXPECT_TRUE(endpoint->is_local_unix());
  EXPECT_EQ(endpoint->family(), AF_UNIX);
  EXPECT_NE(endpoint->family(), AF_INET);
  EXPECT_NE(endpoint->family(), AF_INET6);
  EXPECT_EQ(endpoint->permission_bits(), 0600U);

  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "neg-local-run.sock", "version",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_EQ(field_value(find_method_line(result, "QueryVersion"), "outcome"), "accepted");
}

TEST(XcomSyntheticClientNegative, InvalidSessionEmitsZeroItems) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  const GatewaySessionBinding empty_binding{};
  const ClientRunResult result = run_zero_emission("neg-invalid.sock", fixture, empty_binding);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_EQ(field_value(find_method_line(result, "ArmSession"), "outcome"), "rejected");
  EXPECT_TRUE(find_method_line(result, "SubmitStimulation").empty());
  EXPECT_EQ(fixture.emitter().calls, 0U);

  GatewaySessionBinding substituted = fixture.binding();
  substituted.permit_id = "permit-other";
  const ClientRunResult substituted_result =
      run_zero_emission("neg-substituted.sock", fixture, substituted);
  ASSERT_EQ(substituted_result.exit_status, 0);
  EXPECT_EQ(field_value(find_method_line(substituted_result, "ArmSession"), "outcome"), "rejected");
  EXPECT_EQ(fixture.emitter().calls, 0U);
}

TEST(XcomSyntheticClientNegative, ExpiredSessionEmitsZeroItems) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  fixture.clock().set(2000);
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "neg-expired.sock", "stimulate_signal",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_EQ(field_value(find_method_line(result, "ArmSession"), "outcome"), "rejected");
  EXPECT_TRUE(find_method_line(result, "SubmitStimulation").empty());
  EXPECT_EQ(fixture.emitter().calls, 0U);
  EXPECT_EQ(session.snapshot().emitted, 0U);
}

TEST(XcomSyntheticClientNegative, UnsupportedMajorFailsClosed) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "neg-major.sock", "arm_reject",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  EXPECT_EQ(field_value(find_method_line(result, "ArmSession"), "outcome"), "rejected");
  EXPECT_TRUE(find_method_line(result, "SubmitStimulation").empty());
  EXPECT_EQ(fixture.emitter().calls, 0U);
  EXPECT_EQ(session.snapshot().emitted, 0U);
  EXPECT_FALSE(session.snapshot().armed);
}

TEST(XcomSyntheticClientNegative, ClientForbiddenApiScan) {
  std::ifstream stream(XCOM_T032_CLIENT_SOURCE_PATH, std::ios::in | std::ios::binary);
  ASSERT_TRUE(stream.is_open());
  std::ostringstream buffer;
  buffer << stream.rdbuf();
  const std::string source = buffer.str();
  ASSERT_FALSE(source.empty());
  const std::vector<std::string> forbidden = {
      "AF_INET", "AF_INET6", "sockaddr_in", "in_addr",     "getaddrinfo", "gethostbyname",
      "inet_addr", "inet_ntoa", "res_query", "SSL_",       "TLS_",        "tls_",
      "openssl",   "dlopen",    "popen(",    "system(",     "grpc",
  };
  for (const std::string &token : forbidden) {
    EXPECT_EQ(source.find(token), std::string::npos) << "forbidden client token: " << token;
  }
}
