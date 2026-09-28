/**
 * @file synthetic_client_contract_tests.cpp
 * @brief T032 generated-client contract cases: the client usage carries no payload or permit
 *        content, a generated request message round-trips through the client exchange unchanged, an
 *        unknown field survives the proto3 client round trip, and the committed client operation
 *        table equals the generated `ToolGateway` service descriptor method set in order.
 * @ownership Each case owns one `SyntheticClientFixture`, one accepted `GatewaySession`, and its
 *            bounded scratch endpoint; the launched fixture process is reaped within a bounded wait.
 * @lifetime The fixture and session outlive the harness call and unlink their scratch path on
 *           destruction.
 * @thread_safety Single-threaded; the descriptor pool is process-static read-only state.
 * @bounds One socket and one peer per case; <= 10 operation lines; no payload byte is retained.
 * @failure A failed launch, decode, descriptor lookup, or reap fails the owning case closed.
 * @par Traceability
 * Supports T032-SR-001, T032-SR-002, T032-SR-013, T032-SR-015, T032-SR-017 and cases
 * T32-TS-011..T32-TS-014.
 */

#include <gtest/gtest.h>

#include <google/protobuf/descriptor.h>

#include "synthetic_client_support.hpp"

#include <string>
#include <vector>

namespace {

using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::ClientRunResult;
using xverse::xcom::tool_gateway_test::ClientServerMode;
using xverse::xcom::tool_gateway_test::find_first_line;
using xverse::xcom::tool_gateway_test::field_value;
using xverse::xcom::tool_gateway_test::kPermitId;
using xverse::xcom::tool_gateway_test::parse_fields;
using xverse::xcom::tool_gateway_test::run_client_case;
using xverse::xcom::tool_gateway_test::SyntheticClientFixture;

}  // namespace

TEST(XcomSyntheticClientContract, ClientUsageCarriesNoPayloadOrPermitSecret) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "con-usage.sock", "stimulate_signal",
                      ClientServerMode::dispatch, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  ASSERT_FALSE(result.lines.empty());
  for (const std::string &line : result.lines) {
    EXPECT_EQ(line.find(std::string(kPermitId)), std::string::npos);
    EXPECT_EQ(line.find("payload"), std::string::npos);
  }
  for (const auto &record : fixture.log().records()) {
    EXPECT_NE(record.identity, std::string(kPermitId));
    EXPECT_EQ(record.code.find("payload="), std::string::npos);
  }
}

TEST(XcomSyntheticClientContract, GeneratedRequestRoundTripsThroughClient) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "con-roundtrip.sock", "roundtrip",
                      ClientServerMode::echo, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  const std::string line = find_first_line(result, "roundtrip");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "roundtrip"), "match");
}

TEST(XcomSyntheticClientContract, UnknownFieldSurvivesClientRoundTrip) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result = run_client_case(
      session, fixture.config(), fixture.hub(), "con-unknown.sock", "roundtrip_unknown",
      ClientServerMode::echo, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  const std::string line = find_first_line(result, "roundtrip");
  ASSERT_FALSE(line.empty());
  EXPECT_EQ(field_value(line, "roundtrip"), "match");
}

TEST(XcomSyntheticClientContract, ClientOperationTableMatchesGeneratedDescriptor) {
  SyntheticClientFixture fixture;
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  const ClientRunResult result =
      run_client_case(session, fixture.config(), fixture.hub(), "con-surface.sock", "selftest",
                      ClientServerMode::none, 4096U, 1000U, 500U);
  ASSERT_EQ(result.exit_status, 0);
  std::vector<std::string> operations;
  for (const std::string &line : result.lines) {
    const auto fields = parse_fields(line);
    const auto found = fields.find("operation");
    if (found != fields.end()) {
      operations.push_back(found->second);
    }
  }
  const google::protobuf::FileDescriptor *file =
      google::protobuf::DescriptorPool::generated_pool()->FindFileByName(
          "xverse/xcom/v1/tool_gateway.proto");
  ASSERT_NE(file, nullptr);
  const google::protobuf::ServiceDescriptor *service = file->FindServiceByName("ToolGateway");
  ASSERT_NE(service, nullptr);
  ASSERT_EQ(operations.size(), static_cast<std::size_t>(service->method_count()));
  for (int index = 0; index < service->method_count(); ++index) {
    EXPECT_EQ(operations[static_cast<std::size_t>(index)], service->method(index)->name());
  }
  const std::string selftest = find_first_line(result, "selftest");
  ASSERT_FALSE(selftest.empty());
  EXPECT_EQ(field_value(selftest, "selftest"), "ok");
}
