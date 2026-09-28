/**
 * @file contract_tests.cpp
 * @brief T030 generated-contract tests for the versioned xverse.xcom.v1 tool-gateway contract:
 *        package/version identity, the exact service and method surface, the message/enum
 *        vocabulary, version negotiation, observation, session, stimulation, lease, outcome,
 *        diagnostic, and declared-bound shapes read from the generated FileDescriptor.
 * @ownership Each case owns only local descriptor views and value probes; no shared mutable state.
 * @lifetime The generated descriptor is process-static; local probes are value copies.
 * @thread_safety Single-threaded; read-only descriptor access.
 * @bounds <= 30 messages, <= 10 methods, <= 32 pinned fields, no wall-clock dependence.
 * @failure Any missing or mismatched contract element fails the owning case closed.
 */

#include <gtest/gtest.h>

#include "contract_support.hpp"

#include <google/protobuf/descriptor.pb.h>

#include "xverse/xcom/v1/tool_gateway.pb.h"

#include <cstdint>
#include <string>
#include <vector>

namespace {

using xverse::xcom::tool_gateway_test::ContractFile;
using xverse::xcom::tool_gateway_test::DeclaresAdditiveReservedBand;
using xverse::xcom::tool_gateway_test::FindEnum;
using xverse::xcom::tool_gateway_test::FindMessage;
using xverse::xcom::tool_gateway_test::FindService;
using xverse::xcom::tool_gateway_test::HasFieldInsideAdditiveBand;
using xverse::xcom::tool_gateway_test::IsSupportedProtocolVersion;
using xverse::xcom::tool_gateway_test::kFileName;
using xverse::xcom::tool_gateway_test::kPackage;
using xverse::xcom::tool_gateway_test::kServiceName;
using xverse::xcom::tool_gateway_test::MessageHasField;
using xverse::xcom::tool_gateway_test::MessageHasFieldNamed;
using xverse::xcom::tool_gateway_test::MessageHasFieldOfType;
using xverse::xcom::tool_gateway_test::PinnedManifest;
using xverse::xcom::tool_gateway_test::RequiredEnums;
using xverse::xcom::tool_gateway_test::RequiredMessages;

struct ExpectedMethod {
  const char* name;
  const char* input;
  const char* output;
  bool server_streaming;
};

const std::vector<ExpectedMethod>& ExpectedSurface() {
  static const std::vector<ExpectedMethod> methods = {
      {"QueryVersion", "QueryVersionRequest", "QueryVersionResponse", false},
      {"OpenObservation", "OpenObservationRequest", "OpenObservationResponse", false},
      {"ReadObservations", "ReadObservationsRequest", "ObservationRecord", true},
      {"CloseObservation", "CloseObservationRequest", "CloseObservationResponse", false},
      {"ArmSession", "ArmSessionRequest", "ArmSessionResponse", false},
      {"RevokeSession", "RevokeSessionRequest", "RevokeSessionResponse", false},
      {"SubmitStimulation", "SubmitStimulationRequest", "SubmitStimulationResponse", false},
      {"AcquireLease", "AcquireLeaseRequest", "AcquireLeaseResponse", false},
      {"ReleaseLease", "ReleaseLeaseRequest", "ReleaseLeaseResponse", false},
      {"QuerySession", "QuerySessionRequest", "QuerySessionResponse", false},
  };
  return methods;
}

bool EnumHasUnspecifiedZero(const google::protobuf::EnumDescriptor* enumeration) {
  if (enumeration == nullptr) {
    return false;
  }
  const google::protobuf::EnumValueDescriptor* zero = enumeration->FindValueByNumber(0);
  return zero != nullptr && zero->name().size() > std::string("_UNSPECIFIED").size() &&
         zero->name().compare(zero->name().size() - std::string("_UNSPECIFIED").size(),
                              std::string("_UNSPECIFIED").size(), "_UNSPECIFIED") == 0;
}

}  // namespace

TEST(XcomToolGatewayContract, PackageSyntaxVersioned) {
  const google::protobuf::FileDescriptor* file = ContractFile();
  ASSERT_NE(file, nullptr);
  EXPECT_EQ(file->name(), kFileName);
  EXPECT_EQ(file->package(), kPackage);

  google::protobuf::FileDescriptorProto proto;
  file->CopyTo(&proto);
  EXPECT_EQ(proto.syntax(), "proto3");
  EXPECT_EQ(proto.name(), kFileName);
  EXPECT_EQ(proto.package(), kPackage);

  const google::protobuf::Descriptor* version = FindMessage("ProtocolVersion");
  ASSERT_NE(version, nullptr);
  EXPECT_TRUE(MessageHasField(version, 1, "major"));
  EXPECT_TRUE(MessageHasField(version, 2, "minor"));
}

TEST(XcomToolGatewayContract, ServiceSurfaceComplete) {
  const google::protobuf::ServiceDescriptor* service = FindService(kServiceName);
  ASSERT_NE(service, nullptr);
  ASSERT_EQ(service->method_count(), static_cast<int>(ExpectedSurface().size()));
  for (int index = 0; index < service->method_count(); ++index) {
    const google::protobuf::MethodDescriptor* method = service->method(index);
    ASSERT_LT(index, static_cast<int>(ExpectedSurface().size()));
    const ExpectedMethod& expected = ExpectedSurface()[static_cast<std::size_t>(index)];
    EXPECT_EQ(method->name(), expected.name);
    EXPECT_EQ(method->input_type()->name(), expected.input);
    EXPECT_EQ(method->output_type()->name(), expected.output);
    EXPECT_FALSE(method->client_streaming());
    EXPECT_EQ(method->server_streaming(), expected.server_streaming);
  }
}

TEST(XcomToolGatewayContract, MessageVocabularyComplete) {
  const google::protobuf::FileDescriptor* file = ContractFile();
  ASSERT_NE(file, nullptr);
  for (const std::string_view name : RequiredMessages()) {
    EXPECT_NE(FindMessage(name), nullptr) << name;
  }
  for (const std::string_view name : RequiredEnums()) {
    const google::protobuf::EnumDescriptor* enumeration = FindEnum(name);
    ASSERT_NE(enumeration, nullptr) << name;
    EXPECT_TRUE(EnumHasUnspecifiedZero(enumeration)) << name;
  }
  EXPECT_GE(file->message_type_count(), static_cast<int>(RequiredMessages().size()));
  EXPECT_GE(file->enum_type_count(), static_cast<int>(RequiredEnums().size()));
}

TEST(XcomToolGatewayContract, VersionNegotiationAndCapabilities) {
  const google::protobuf::Descriptor* version = FindMessage("ProtocolVersion");
  ASSERT_NE(version, nullptr);
  EXPECT_TRUE(MessageHasFieldOfType(version, "major",
                                    google::protobuf::FieldDescriptor::TYPE_UINT32));
  EXPECT_TRUE(MessageHasFieldOfType(version, "minor",
                                    google::protobuf::FieldDescriptor::TYPE_UINT32));

  const google::protobuf::Descriptor* capabilities = FindMessage("GatewayCapabilities");
  ASSERT_NE(capabilities, nullptr);
  EXPECT_TRUE(MessageHasField(capabilities, 1, "protocol"));
  EXPECT_TRUE(MessageHasField(capabilities, 2, "capabilities"));
  EXPECT_TRUE(MessageHasField(capabilities, 3, "max_message_bytes"));
  EXPECT_TRUE(MessageHasField(capabilities, 4, "max_concurrent_streams"));
  EXPECT_TRUE(MessageHasField(capabilities, 5, "max_deadline_millis"));
  EXPECT_TRUE(MessageHasField(capabilities, 6, "max_observation_queue"));

  EXPECT_TRUE(IsSupportedProtocolVersion(1U));
  EXPECT_FALSE(IsSupportedProtocolVersion(0U));
  EXPECT_FALSE(IsSupportedProtocolVersion(2U));
  EXPECT_FALSE(IsSupportedProtocolVersion(99U));
}

TEST(XcomToolGatewayContract, ObservationStreamContractAndBounds) {
  const google::protobuf::MethodDescriptor* read = FindService(kServiceName)->FindMethodByName(
      "ReadObservations");
  ASSERT_NE(read, nullptr);
  EXPECT_TRUE(read->server_streaming());
  EXPECT_FALSE(read->client_streaming());

  const google::protobuf::Descriptor* record = FindMessage("ObservationRecord");
  ASSERT_NE(record, nullptr);
  EXPECT_TRUE(MessageHasField(record, 1, "identity"));
  EXPECT_TRUE(MessageHasField(record, 2, "route_id"));
  EXPECT_TRUE(MessageHasField(record, 3, "contract_id"));
  EXPECT_TRUE(MessageHasField(record, 4, "clock_domain"));
  EXPECT_TRUE(MessageHasField(record, 5, "sequence"));
  EXPECT_TRUE(MessageHasField(record, 6, "outcome"));
  EXPECT_TRUE(MessageHasField(record, 7, "payload_state"));
  EXPECT_TRUE(MessageHasFieldNamed(record, "payload_view"));
  EXPECT_TRUE(MessageHasFieldNamed(record, "payload_bytes"));

  const google::protobuf::Descriptor* open = FindMessage("OpenObservationRequest");
  ASSERT_NE(open, nullptr);
  EXPECT_TRUE(MessageHasFieldOfType(open, "allow_payload_view",
                                    google::protobuf::FieldDescriptor::TYPE_BOOL));
  EXPECT_TRUE(MessageHasFieldNamed(open, "max_records"));
  EXPECT_TRUE(MessageHasFieldNamed(open, "max_record_bytes"));

  xverse::xcom::v1::ObservationRecord metadata_only;
  EXPECT_EQ(metadata_only.payload_state(),
            xverse::xcom::v1::PAYLOAD_STATE_UNSPECIFIED);
  EXPECT_EQ(metadata_only.payload_bytes(), 0U);
  EXPECT_TRUE(metadata_only.payload_view().empty());
}

TEST(XcomToolGatewayContract, SessionArmRevokeContract) {
  const google::protobuf::Descriptor* arm = FindMessage("ArmSessionRequest");
  ASSERT_NE(arm, nullptr);
  EXPECT_TRUE(MessageHasField(arm, 1, "permit_id"));
  EXPECT_TRUE(MessageHasField(arm, 2, "session_id"));
  EXPECT_TRUE(MessageHasField(arm, 3, "plan_digest"));
  EXPECT_TRUE(MessageHasField(arm, 4, "graph_digest"));
  EXPECT_TRUE(MessageHasField(arm, 5, "protocol"));
  EXPECT_TRUE(MessageHasField(arm, 6, "validity_millis"));
  EXPECT_TRUE(MessageHasField(arm, 7, "deadline_millis"));

  const google::protobuf::Descriptor* revoke = FindMessage("RevokeSessionRequest");
  ASSERT_NE(revoke, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(revoke, "session_id"));

  ASSERT_NE(FindEnum("SessionState"), nullptr);
  EXPECT_NE(FindEnum("SessionState")->FindValueByName("SESSION_EVIDENCE_INCOMPLETE"), nullptr);

  const google::protobuf::Descriptor* arm_response = FindMessage("ArmSessionResponse");
  ASSERT_NE(arm_response, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(arm_response, "state"));
  EXPECT_TRUE(MessageHasFieldNamed(arm_response, "diagnostic"));
  EXPECT_FALSE(MessageHasFieldNamed(arm, "bypass_permit"));
}

TEST(XcomToolGatewayContract, StimulationActionCoverage) {
  const google::protobuf::EnumDescriptor* action = FindEnum("StimulationActionKind");
  ASSERT_NE(action, nullptr);
  ASSERT_EQ(action->value_count(), 5);
  EXPECT_EQ(action->FindValueByNumber(1)->name(), "STIMULATION_ACTION_INJECT_SIGNAL");
  EXPECT_EQ(action->FindValueByNumber(2)->name(), "STIMULATION_ACTION_INJECT_MESSAGE");
  EXPECT_EQ(action->FindValueByNumber(3)->name(), "STIMULATION_ACTION_INVOKE_SERVICE");
  EXPECT_EQ(action->FindValueByNumber(4)->name(), "STIMULATION_ACTION_EMULATE_SERVICE");

  const google::protobuf::EnumDescriptor* schedule_mode = FindEnum("ScheduleMode");
  ASSERT_NE(schedule_mode, nullptr);
  ASSERT_EQ(schedule_mode->value_count(), 3);
  EXPECT_NE(schedule_mode->FindValueByName("SCHEDULE_IMMEDIATE"), nullptr);
  EXPECT_NE(schedule_mode->FindValueByName("SCHEDULE_SCHEDULED"), nullptr);

  ASSERT_NE(FindEnum("InteractionKind"), nullptr);
  ASSERT_NE(FindEnum("Direction"), nullptr);

  const google::protobuf::Descriptor* submit = FindMessage("SubmitStimulationRequest");
  ASSERT_NE(submit, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(submit, "target_endpoint"));
  EXPECT_TRUE(MessageHasFieldNamed(submit, "contract_id"));
  EXPECT_TRUE(MessageHasFieldNamed(submit, "interaction"));
  EXPECT_TRUE(MessageHasFieldNamed(submit, "direction"));
  EXPECT_TRUE(MessageHasFieldNamed(submit, "schedule"));
  EXPECT_TRUE(MessageHasFieldNamed(submit, "deadline_millis"));
  EXPECT_TRUE(MessageHasFieldNamed(submit, "payload_bytes"));

  const google::protobuf::Descriptor* stimulation_action = FindMessage("StimulationAction");
  ASSERT_NE(stimulation_action, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(stimulation_action, "correlation_id"));
  EXPECT_TRUE(MessageHasFieldNamed(stimulation_action, "causation_id"));
}

TEST(XcomToolGatewayContract, ServiceEmulationLeaseContract) {
  const google::protobuf::Descriptor* acquire = FindMessage("AcquireLeaseRequest");
  ASSERT_NE(acquire, nullptr);
  EXPECT_TRUE(MessageHasField(acquire, 1, "session_id"));
  EXPECT_TRUE(MessageHasField(acquire, 2, "endpoint_id"));
  EXPECT_TRUE(MessageHasField(acquire, 3, "endpoint_generation"));
  EXPECT_TRUE(MessageHasField(acquire, 4, "plan_digest"));
  EXPECT_TRUE(MessageHasField(acquire, 5, "lease_millis"));
  EXPECT_TRUE(MessageHasField(acquire, 6, "deadline_millis"));

  const google::protobuf::Descriptor* release = FindMessage("ReleaseLeaseRequest");
  ASSERT_NE(release, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(release, "session_id"));
  EXPECT_TRUE(MessageHasFieldNamed(release, "lease_id"));

  const google::protobuf::EnumDescriptor* lease = FindEnum("LeaseState");
  ASSERT_NE(lease, nullptr);
  for (const char* value : {"LEASE_ACTIVE", "LEASE_RELEASED", "LEASE_QUARANTINED",
                            "LEASE_EXPIRED", "LEASE_CONFLICT"}) {
    EXPECT_NE(lease->FindValueByName(value), nullptr) << value;
  }
}

TEST(XcomToolGatewayContract, SessionOutcomeCountersContract) {
  const google::protobuf::EnumDescriptor* outcome = FindEnum("StimulationOutcomeKind");
  ASSERT_NE(outcome, nullptr);
  EXPECT_NE(outcome->FindValueByName("STIMULATION_OUTCOME_EVIDENCE_INCOMPLETE"), nullptr);

  const google::protobuf::Descriptor* counters = FindMessage("SessionCounters");
  ASSERT_NE(counters, nullptr);
  EXPECT_TRUE(MessageHasField(counters, 1, "requests_received"));
  EXPECT_TRUE(MessageHasField(counters, 2, "requests_authorized"));
  EXPECT_TRUE(MessageHasField(counters, 3, "requests_rejected"));
  EXPECT_TRUE(MessageHasField(counters, 4, "emitted"));
  EXPECT_TRUE(MessageHasField(counters, 5, "evidence_incomplete"));
  EXPECT_EQ(counters->field_count(), 5);

  const google::protobuf::Descriptor* query = FindMessage("QuerySessionResponse");
  ASSERT_NE(query, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(query, "state"));
  EXPECT_TRUE(MessageHasFieldNamed(query, "counters"));
}

TEST(XcomToolGatewayContract, DiagnosticContract) {
  const google::protobuf::Descriptor* diagnostic = FindMessage("Diagnostic");
  ASSERT_NE(diagnostic, nullptr);
  EXPECT_TRUE(MessageHasField(diagnostic, 1, "code"));
  EXPECT_TRUE(MessageHasField(diagnostic, 2, "severity"));
  EXPECT_TRUE(MessageHasField(diagnostic, 3, "phase"));
  EXPECT_TRUE(MessageHasField(diagnostic, 4, "identity"));
  EXPECT_TRUE(MessageHasField(diagnostic, 5, "reason"));
  EXPECT_TRUE(MessageHasField(diagnostic, 6, "correction"));

  const google::protobuf::EnumDescriptor* severity = FindEnum("Severity");
  ASSERT_NE(severity, nullptr);
  for (const char* value : {"SEVERITY_INFO", "SEVERITY_WARNING", "SEVERITY_ERROR"}) {
    EXPECT_NE(severity->FindValueByName(value), nullptr) << value;
  }
}

TEST(XcomToolGatewayContract, DeclaredBoundsPresent) {
  const google::protobuf::Descriptor* capabilities = FindMessage("GatewayCapabilities");
  ASSERT_NE(capabilities, nullptr);
  for (const char* bound : {"max_message_bytes", "max_concurrent_streams",
                            "max_deadline_millis", "max_observation_queue"}) {
    EXPECT_TRUE(MessageHasFieldNamed(capabilities, bound)) << bound;
  }

  const google::protobuf::Descriptor* open = FindMessage("OpenObservationRequest");
  ASSERT_NE(open, nullptr);
  for (const char* bound : {"max_records", "max_record_bytes", "deadline_millis"}) {
    EXPECT_TRUE(MessageHasFieldNamed(open, bound)) << bound;
  }

  const google::protobuf::Descriptor* read = FindMessage("ReadObservationsRequest");
  ASSERT_NE(read, nullptr);
  for (const char* bound : {"max_records", "deadline_millis"}) {
    EXPECT_TRUE(MessageHasFieldNamed(read, bound)) << bound;
  }

  const google::protobuf::Descriptor* submit = FindMessage("SubmitStimulationRequest");
  ASSERT_NE(submit, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(submit, "payload_bytes"));
  EXPECT_TRUE(MessageHasFieldNamed(submit, "deadline_millis"));

  const google::protobuf::Descriptor* acquire = FindMessage("AcquireLeaseRequest");
  ASSERT_NE(acquire, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(acquire, "lease_millis"));
  EXPECT_TRUE(MessageHasFieldNamed(acquire, "deadline_millis"));

  const google::protobuf::Descriptor* close = FindMessage("CloseObservationResponse");
  ASSERT_NE(close, nullptr);
  EXPECT_TRUE(MessageHasFieldNamed(close, "delivered"));
  EXPECT_TRUE(MessageHasFieldNamed(close, "dropped"));
}
