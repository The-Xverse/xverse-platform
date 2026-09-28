/**
 * @file negative_tests.cpp
 * @brief T030 fail-closed generated-contract tests: no transport/address/credential primitive, no
 *        unbound bytes payload, no permit/session bypass, fail-closed unsupported-major rejection,
 *        and no reuse of a reserved field number.
 * @ownership Each case owns only local descriptor views; no shared mutable state.
 * @lifetime The generated descriptor is process-static; probes are value copies.
 * @thread_safety Single-threaded; read-only descriptor access.
 * @bounds <= 30 messages, <= 32 fields per message, <= 16 major probes, no wall-clock dependence.
 * @failure Any forbidden fragment, unbound payload, missing session/permit identity, accepted
 *          unsupported major, or reused reserved number fails the owning case closed.
 */

#include <gtest/gtest.h>

#include "contract_support.hpp"

#include <google/protobuf/descriptor.h>

#include <cstdint>
#include <string>

namespace {

using xverse::xcom::tool_gateway_test::ContractFile;
using xverse::xcom::tool_gateway_test::FindMessage;
using xverse::xcom::tool_gateway_test::HasAnyFieldInsideAnyReservedBand;
using xverse::xcom::tool_gateway_test::IsSupportedProtocolVersion;
using xverse::xcom::tool_gateway_test::MessageHasFieldNamed;
using xverse::xcom::tool_gateway_test::NameHasForbiddenFragment;

bool HasBoundForEachBytesField(const google::protobuf::Descriptor* message) {
  bool has_bytes = false;
  bool has_bound = false;
  for (int index = 0; index < message->field_count(); ++index) {
    const google::protobuf::FieldDescriptor* field = message->field(index);
    if (field->type() == google::protobuf::FieldDescriptor::TYPE_BYTES) {
      has_bytes = true;
    } else if (field->cpp_type() == google::protobuf::FieldDescriptor::CPPTYPE_INT32 ||
               field->cpp_type() == google::protobuf::FieldDescriptor::CPPTYPE_INT64 ||
               field->cpp_type() == google::protobuf::FieldDescriptor::CPPTYPE_UINT32 ||
               field->cpp_type() == google::protobuf::FieldDescriptor::CPPTYPE_UINT64) {
      const std::string& name = field->name();
      if (name.find("bytes") != std::string::npos || name.find("size") != std::string::npos ||
          name.find("bound") != std::string::npos || name.find("len") != std::string::npos) {
        has_bound = true;
      }
    }
  }
  return !has_bytes || has_bound;
}

}  // namespace

TEST(XcomToolGatewayNegative, NoTcpOrAddressPrimitive) {
  const google::protobuf::FileDescriptor* file = ContractFile();
  ASSERT_NE(file, nullptr);
  int scanned_fields = 0;
  for (int message_index = 0; message_index < file->message_type_count(); ++message_index) {
    const google::protobuf::Descriptor* message = file->message_type(message_index);
    for (int field_index = 0; field_index < message->field_count(); ++field_index) {
      const std::string& name = message->field(field_index)->name();
      ++scanned_fields;
      EXPECT_FALSE(NameHasForbiddenFragment(name))
          << message->full_name() << "." << name;
    }
  }
  EXPECT_GT(scanned_fields, 0);
}

TEST(XcomToolGatewayNegative, NoImplicitUnboundedPayload) {
  const google::protobuf::FileDescriptor* file = ContractFile();
  ASSERT_NE(file, nullptr);
  int payload_messages = 0;
  for (int message_index = 0; message_index < file->message_type_count(); ++message_index) {
    const google::protobuf::Descriptor* message = file->message_type(message_index);
    EXPECT_TRUE(HasBoundForEachBytesField(message)) << message->full_name();
    if (message->FindFieldByName("payload_view") != nullptr ||
        message->FindFieldByName("payload") != nullptr) {
      ++payload_messages;
    }
  }
  EXPECT_GT(payload_messages, 0);
}

TEST(XcomToolGatewayNegative, NoBypassOfPermitOrSession) {
  const google::protobuf::Descriptor* submit = FindMessage("SubmitStimulationRequest");
  ASSERT_NE(submit, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(submit, "session_id"));

  const google::protobuf::Descriptor* acquire = FindMessage("AcquireLeaseRequest");
  ASSERT_NE(acquire, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(acquire, "session_id"));

  const google::protobuf::Descriptor* release = FindMessage("ReleaseLeaseRequest");
  ASSERT_NE(release, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(release, "session_id"));

  const google::protobuf::Descriptor* revoke = FindMessage("RevokeSessionRequest");
  ASSERT_NE(revoke, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(revoke, "session_id"));

  const google::protobuf::Descriptor* arm = FindMessage("ArmSessionRequest");
  ASSERT_NE(arm, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(arm, "permit_id"));
  EXPECT_TRUE(MessageHasFieldNamed(arm, "session_id"));
}

TEST(XcomToolGatewayNegative, UnsupportedMajorVersionRejectedByPredicate) {
  EXPECT_TRUE(IsSupportedProtocolVersion(1U));
  for (std::uint32_t major = 0U; major <= 16U; ++major) {
    if (major == 1U) {
      continue;
    }
    EXPECT_FALSE(IsSupportedProtocolVersion(major)) << major;
  }
  EXPECT_FALSE(IsSupportedProtocolVersion(0xFFFFFFFFU));
}

TEST(XcomToolGatewayNegative, ReservedNumberCannotBeReused) {
  const google::protobuf::FileDescriptor* file = ContractFile();
  ASSERT_NE(file, nullptr);
  for (int message_index = 0; message_index < file->message_type_count(); ++message_index) {
    const google::protobuf::Descriptor* message = file->message_type(message_index);
    EXPECT_FALSE(HasAnyFieldInsideAnyReservedBand(message)) << message->full_name();
    for (int range_index = 0; range_index < message->reserved_range_count(); ++range_index) {
      const google::protobuf::Descriptor::ReservedRange* range =
          message->reserved_range(range_index);
      EXPECT_EQ(message->FindFieldByNumber(range->start), nullptr)
          << message->full_name() << " reserved start " << range->start;
      EXPECT_EQ(message->FindFieldByNumber(range->end - 1), nullptr)
          << message->full_name() << " reserved end " << (range->end - 1);
    }
  }
}
