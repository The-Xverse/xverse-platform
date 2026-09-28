/**
 * @file contract_support.hpp
 * @brief T030 bounded, payload-free, test-local descriptor helpers and the pinned field manifest
 *        for the versioned xverse.xcom.v1 external-tool gateway contract.
 * @ownership The helpers own no runtime state. They return bounded views over the generated
 *            immutable FileDescriptor and require no registration or teardown. No helper mutates
 *            the descriptor, writes repository files, or retains a payload byte.
 * @lifetime The generated file and message descriptors have process-static lifetime; every
 *           returned pointer or reference is valid for the process. The compatibility predicate is
 *           a pure function of its argument.
 * @thread_safety Read-only descriptor access; each suite runs single-threaded.
 * @bounds <= 40 messages, <= 12 enums, <= 10 service methods, <= 32 pinned fields per manifest
 *         entry, one crafted wire buffer of <= 24 bytes per case, no wall-clock dependence.
 * @failure A missing message, enum, service, method, bound, or reserved band, an unexpected field
 *          number or name, a forbidden transport/address fragment, or a failed proto3 round trip
 *          fails the owning case closed.
 * @par Traceability
 * Supports T030-SR-001 through T030-SR-016 and the accepted XCOM-DU-019 tool gateway Protocol
 * Buffers API.
 */

#ifndef XVERSE_XCOM_TOOL_GATEWAY_CONTRACT_SUPPORT_HPP_
#define XVERSE_XCOM_TOOL_GATEWAY_CONTRACT_SUPPORT_HPP_

#include <google/protobuf/descriptor.h>

#include "xverse/xcom/v1/tool_gateway.pb.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xverse::xcom::tool_gateway_test {

using google::protobuf::Descriptor;
using google::protobuf::EnumDescriptor;
using google::protobuf::EnumValueDescriptor;
using google::protobuf::FieldDescriptor;
using google::protobuf::FileDescriptor;
using google::protobuf::MethodDescriptor;
using google::protobuf::ServiceDescriptor;

inline constexpr char kPackage[] = "xverse.xcom.v1";
inline constexpr char kFileName[] = "xverse/xcom/v1/tool_gateway.proto";
inline constexpr char kServiceName[] = "ToolGateway";
inline constexpr std::uint32_t kSupportedMajor = 1U;
inline constexpr int kReservedBandBegin = 1000;
inline constexpr int kReservedBandEndExclusive = 2000;
inline constexpr std::size_t kExpectedMethodCount = 10U;

// Fail-closed protocol-version predicate. It accepts only the published major and rejects every
// other major without depending on an absent field (T030-SR-003, T30-TS-004/T30-TS-020).
inline bool IsSupportedProtocolVersion(std::uint32_t major) noexcept {
  return major == kSupportedMajor;
}

// The single generated file descriptor for the committed contract. The generated descriptor
// anchor keeps the generated translation unit in the link so its pool registration always runs,
// even in suites that reach the contract only through reflection.
inline const FileDescriptor* ContractFile() {
  static const google::protobuf::Descriptor* const generated_anchor =
      xverse::xcom::v1::ObservationRecord::descriptor();
  static_cast<void>(generated_anchor);
  return google::protobuf::DescriptorPool::generated_pool()->FindFileByName(kFileName);
}

inline const Descriptor* FindMessage(std::string_view name) {
  const FileDescriptor* file = ContractFile();
  if (file == nullptr) {
    return nullptr;
  }
  return file->FindMessageTypeByName(std::string(name));
}

inline const EnumDescriptor* FindEnum(std::string_view name) {
  const FileDescriptor* file = ContractFile();
  if (file == nullptr) {
    return nullptr;
  }
  return file->FindEnumTypeByName(std::string(name));
}

inline const ServiceDescriptor* FindService(std::string_view name) {
  const FileDescriptor* file = ContractFile();
  if (file == nullptr) {
    return nullptr;
  }
  return file->FindServiceByName(std::string(name));
}

inline bool MessageHasField(const Descriptor* message, int number, std::string_view name) {
  if (message == nullptr) {
    return false;
  }
  const FieldDescriptor* field = message->FindFieldByNumber(number);
  return field != nullptr && field->name() == name;
}

inline bool MessageHasFieldNamed(const Descriptor* message, std::string_view name) {
  if (message == nullptr) {
    return false;
  }
  return message->FindFieldByName(std::string(name)) != nullptr;
}

inline bool MessageHasFieldOfType(const Descriptor* message, std::string_view name,
                                  FieldDescriptor::Type type) {
  if (message == nullptr) {
    return false;
  }
  const FieldDescriptor* field = message->FindFieldByName(std::string(name));
  return field != nullptr && field->type() == type;
}

// A declared reserved band that covers the whole [1000, 1999] additive band.
inline bool DeclaresAdditiveReservedBand(const Descriptor* message) {
  if (message == nullptr) {
    return false;
  }
  for (int index = 0; index < message->reserved_range_count(); ++index) {
    const Descriptor::ReservedRange* range = message->reserved_range(index);
    if (range->start <= kReservedBandBegin && range->end >= kReservedBandEndExclusive) {
      return true;
    }
  }
  return false;
}

inline bool HasFieldInsideAdditiveBand(const Descriptor* message) {
  if (message == nullptr) {
    return false;
  }
  for (int index = 0; index < message->field_count(); ++index) {
    const int number = message->field(index)->number();
    if (number >= kReservedBandBegin && number < kReservedBandEndExclusive) {
      return true;
    }
  }
  return false;
}

inline bool HasAnyFieldInsideAnyReservedBand(const Descriptor* message) {
  if (message == nullptr) {
    return false;
  }
  for (int index = 0; index < message->field_count(); ++index) {
    if (message->FindReservedRangeContainingNumber(message->field(index)->number()) != nullptr) {
      return true;
    }
  }
  return false;
}

// Forbidden transport/address/credential field-name fragments (T030-SR-011). Logical identities
// such as ``target_endpoint``, ``contract_id``, and ``endpoint_generation`` are permitted.
inline const std::array<std::string_view, 15>& ForbiddenNameFragments() {
  static const std::array<std::string_view, 15> fragments = {
      "tcp",        "udp",       "socket",     "address", "hostname",
      "dns",        "tls",       "credential", "password", "secret",
      "token",      "ip_addr",   "url",        "uri",      "port",
  };
  return fragments;
}

inline bool NameHasForbiddenFragment(std::string_view name) {
  for (const std::string_view fragment : ForbiddenNameFragments()) {
    if (name.find(fragment) != std::string_view::npos) {
      return true;
    }
  }
  return false;
}

// The committed pinned number -> name manifest (detailed-design.md section 3.3). A renumbering,
// rename, or silent removal fails the pinning case deterministically.
struct PinnedField {
  int number;
  const char* name;
};

struct PinnedMessage {
  const char* message;
  std::vector<PinnedField> fields;
};

inline const std::vector<PinnedMessage>& PinnedManifest() {
  static const std::vector<PinnedMessage> manifest = {
      {"ProtocolVersion", {{1, "major"}, {2, "minor"}}},
      {"GatewayCapabilities",
       {{1, "protocol"},
        {2, "capabilities"},
        {3, "max_message_bytes"},
        {4, "max_concurrent_streams"},
        {5, "max_deadline_millis"},
        {6, "max_observation_queue"}}},
      {"ObservationRecord",
       {{1, "identity"},
        {2, "route_id"},
        {3, "contract_id"},
        {4, "clock_domain"},
        {5, "sequence"},
        {6, "outcome"},
        {7, "payload_state"},
        {8, "payload_view"},
        {9, "payload_bytes"}}},
      {"ArmSessionRequest",
       {{1, "permit_id"},
        {2, "session_id"},
        {3, "plan_digest"},
        {4, "graph_digest"},
        {5, "protocol"},
        {6, "validity_millis"},
        {7, "deadline_millis"}}},
      {"SubmitStimulationRequest",
       {{1, "session_id"},
        {2, "request_id"},
        {3, "action"},
        {4, "target_endpoint"},
        {5, "contract_id"},
        {6, "interaction"},
        {7, "direction"},
        {8, "schedule"},
        {9, "payload"},
        {10, "payload_bytes"},
        {11, "deadline_millis"}}},
      {"AcquireLeaseRequest",
       {{1, "session_id"},
        {2, "endpoint_id"},
        {3, "endpoint_generation"},
        {4, "plan_digest"},
        {5, "lease_millis"},
        {6, "deadline_millis"}}},
      {"SessionCounters",
       {{1, "requests_received"},
        {2, "requests_authorized"},
        {3, "requests_rejected"},
        {4, "emitted"},
        {5, "evidence_incomplete"}}},
      {"Diagnostic",
       {{1, "code"}, {2, "severity"}, {3, "phase"},
        {4, "identity"}, {5, "reason"}, {6, "correction"}}},
  };
  return manifest;
}

// The required message vocabulary (T030-SR-002/T030-SR-016). Every entry must exist.
inline const std::vector<std::string_view>& RequiredMessages() {
  static const std::vector<std::string_view> messages = {
      "ProtocolVersion",          "Capability",            "GatewayCapabilities",
      "QueryVersionRequest",      "QueryVersionResponse",  "Diagnostic",
      "ObservationFilter",        "Identity",              "ObservationRecord",
      "OpenObservationRequest",   "OpenObservationResponse", "ReadObservationsRequest",
      "CloseObservationRequest",  "CloseObservationResponse", "ArmSessionRequest",
      "ArmSessionResponse",       "RevokeSessionRequest",  "RevokeSessionResponse",
      "StimulationAction",        "Schedule",              "SubmitStimulationRequest",
      "StimulationOutcome",       "SubmitStimulationResponse", "AcquireLeaseRequest",
      "AcquireLeaseResponse",     "ReleaseLeaseRequest",   "ReleaseLeaseResponse",
      "SessionCounters",          "QuerySessionRequest",   "QuerySessionResponse",
  };
  return messages;
}

// The required enum vocabulary. Every enum must expose a zero ``*_UNSPECIFIED`` value.
inline const std::vector<std::string_view>& RequiredEnums() {
  static const std::vector<std::string_view> enums = {
      "Severity",              "PayloadState",   "SessionState",
      "StimulationActionKind", "InteractionKind", "Direction",
      "ScheduleMode",          "StimulationOutcomeKind", "LeaseState",
  };
  return enums;
}

// One upstream (producer) unknown varint field appended to a bounded buffer.
inline void AppendVarintField(std::string& buffer, std::uint64_t number,
                              std::uint64_t value) {
  std::uint64_t tag = (number << 3U);
  while (tag >= 0x80U) {
    buffer.push_back(static_cast<char>((tag & 0x7FU) | 0x80U));
    tag >>= 7U;
  }
  buffer.push_back(static_cast<char>(tag));
  while (value >= 0x80U) {
    buffer.push_back(static_cast<char>((value & 0x7FU) | 0x80U));
    value >>= 7U;
  }
  buffer.push_back(static_cast<char>(value));
}

// Wire tag plus an unvalidated enum value for an open proto3 enum field.
inline std::string EnumWireValue(std::uint64_t number, std::uint64_t value) {
  std::string buffer;
  AppendVarintField(buffer, number, value);
  return buffer;
}

}  // namespace xverse::xcom::tool_gateway_test

#endif  // XVERSE_XCOM_TOOL_GATEWAY_CONTRACT_SUPPORT_HPP_
