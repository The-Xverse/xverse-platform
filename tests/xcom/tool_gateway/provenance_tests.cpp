/**
 * @file provenance_tests.cpp
 * @brief T030 generated-code provenance tests: the admitted Protocol Buffers runtime version guard
 *        and schema name in the generated message header, the declared service and method surface
 *        in the provenance-only gRPC stub header, and the self-consistent serialized descriptor.
 * @ownership Each case owns only local file buffers and value probes; no shared mutable state.
 * @lifetime The generated descriptor is process-static; the read header text is case-local.
 * @thread_safety Single-threaded; bounded read-only file access plus descriptor access.
 * @bounds one bounded (<= 4 MiB) read of each generated header; <= 10 method-name probes.
 * @failure A missing or mismatched generated artifact, version guard, schema name, service class,
 *          or method, or a descriptor round-trip mismatch, fails the owning case closed.
 */

#include <gtest/gtest.h>

#include "contract_support.hpp"

#include <google/protobuf/descriptor.pb.h>
#include <google/protobuf/stubs/common.h>

#include <cstddef>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#if !defined(XCOM_T030_PB_HEADER_PATH) || !defined(XCOM_T030_GRPC_HEADER_PATH)
#error "T030 provenance test requires the generated build-tree header paths"
#endif

// The generated contract is compiled against the single admitted Protocol Buffers runtime.
static_assert(GOOGLE_PROTOBUF_VERSION == 3012004,
              "T030 requires the admitted Protocol Buffers 3.12.4 runtime");

namespace {

using xverse::xcom::tool_gateway_test::ContractFile;
using xverse::xcom::tool_gateway_test::kFileName;
using xverse::xcom::tool_gateway_test::kPackage;

bool ReadBounded(const char* path, std::string* content) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    return false;
  }
  std::ostringstream buffer;
  buffer << input.rdbuf();
  *content = buffer.str();
  return input.good() || input.eof();
}

bool Contains(const std::string& haystack, const std::string& needle) {
  return haystack.find(needle) != std::string::npos;
}

const std::vector<std::string>& MethodNames() {
  static const std::vector<std::string> names = {
      "QueryVersion",   "OpenObservation", "ReadObservations", "CloseObservation",
      "ArmSession",     "RevokeSession",   "SubmitStimulation", "AcquireLease",
      "ReleaseLease",   "QuerySession",
  };
  return names;
}

}  // namespace

TEST(XcomToolGatewayProvenance, GeneratedCodeProvenanceRecorded) {
  std::string header;
  ASSERT_TRUE(ReadBounded(XCOM_T030_PB_HEADER_PATH, &header));
  EXPECT_LE(header.size(), std::size_t{4} * 1024U * 1024U);
  // The generated header carries the admitted protoc version guard and the committed schema name.
  EXPECT_TRUE(Contains(header, "PROTOBUF_VERSION"));
  EXPECT_TRUE(Contains(header, "3012004"));
  EXPECT_TRUE(Contains(header, kFileName));
  EXPECT_FALSE(header.empty());
}

TEST(XcomToolGatewayProvenance, GeneratedGrpcStubDeclaresService) {
  std::string header;
  ASSERT_TRUE(ReadBounded(XCOM_T030_GRPC_HEADER_PATH, &header));
  EXPECT_LE(header.size(), std::size_t{4} * 1024U * 1024U);
  EXPECT_TRUE(Contains(header, "class ToolGateway"));
  EXPECT_TRUE(Contains(header, kFileName));
  for (const std::string& method : MethodNames()) {
    EXPECT_TRUE(Contains(header, method)) << method;
  }
}

TEST(XcomToolGatewayProvenance, SerializedDescriptorMatchesSource) {
  const google::protobuf::FileDescriptor* file = ContractFile();
  ASSERT_NE(file, nullptr);
  google::protobuf::FileDescriptorProto descriptor;
  file->CopyTo(&descriptor);
  EXPECT_EQ(descriptor.name(), kFileName);
  EXPECT_EQ(descriptor.package(), kPackage);
  EXPECT_EQ(descriptor.syntax(), "proto3");

  std::string serialized;
  ASSERT_TRUE(descriptor.SerializeToString(&serialized));
  ASSERT_FALSE(serialized.empty());

  google::protobuf::FileDescriptorProto reparsed;
  ASSERT_TRUE(reparsed.ParseFromString(serialized));
  EXPECT_EQ(reparsed.SerializeAsString(), serialized);
  EXPECT_EQ(reparsed.name(), kFileName);
  EXPECT_EQ(reparsed.package(), kPackage);

  const google::protobuf::FileDescriptor* round_tripped =
      google::protobuf::DescriptorPool::generated_pool()->FindFileByName(kFileName);
  ASSERT_NE(round_tripped, nullptr);
  EXPECT_EQ(round_tripped->name(), kFileName);
}
