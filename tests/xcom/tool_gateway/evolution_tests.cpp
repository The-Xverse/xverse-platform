/**
 * @file evolution_tests.cpp
 * @brief T030 additive-evolution generated-contract tests: the reserved extension band, the pinned
 *        field-number manifest, additive field insertion, unknown-field preservation, and unmapped
 *        proto3 enum preservation across a round trip.
 * @ownership Each case owns only local value probes and bounded wire buffers.
 * @lifetime The generated descriptor is process-static; crafted buffers are case-local values.
 * @thread_safety Single-threaded; no shared mutable state.
 * @bounds <= 30 messages, <= 32 pinned fields, <= 24-byte crafted buffers, no wall-clock dependence.
 * @failure Any renumbering, rename, silent removal, dropped unknown field, or remapped enum value
 *          fails the owning case closed.
 */

#include <gtest/gtest.h>

#include "contract_support.hpp"

#include <google/protobuf/unknown_field_set.h>

#include "xverse/xcom/v1/tool_gateway.pb.h"

#include <cstdint>
#include <string>

namespace {

using xverse::xcom::tool_gateway_test::AppendVarintField;
using xverse::xcom::tool_gateway_test::ContractFile;
using xverse::xcom::tool_gateway_test::DeclaresAdditiveReservedBand;
using xverse::xcom::tool_gateway_test::EnumWireValue;
using xverse::xcom::tool_gateway_test::FindMessage;
using xverse::xcom::tool_gateway_test::HasFieldInsideAdditiveBand;
using xverse::xcom::tool_gateway_test::PinnedManifest;

std::size_t UnknownFieldCount(const google::protobuf::Message& message) {
  return static_cast<std::size_t>(
      message.GetReflection()->GetUnknownFields(message).field_count());
}

const google::protobuf::UnknownField* LastUnknownField(
    const google::protobuf::Message& message) {
  const google::protobuf::UnknownFieldSet& fields =
      message.GetReflection()->GetUnknownFields(message);
  if (fields.field_count() <= 0) {
    return nullptr;
  }
  return &fields.field(fields.field_count() - 1);
}

}  // namespace

TEST(XcomToolGatewayEvolution, ReservedExtensionBandDeclared) {
  const google::protobuf::FileDescriptor* file = ContractFile();
  ASSERT_NE(file, nullptr);
  ASSERT_GT(file->message_type_count(), 0);
  for (int index = 0; index < file->message_type_count(); ++index) {
    const google::protobuf::Descriptor* message = file->message_type(index);
    EXPECT_TRUE(DeclaresAdditiveReservedBand(message)) << message->full_name();
    EXPECT_FALSE(HasFieldInsideAdditiveBand(message)) << message->full_name();
  }
}

TEST(XcomToolGatewayEvolution, FieldNumberManifestPinned) {
  ASSERT_FALSE(PinnedManifest().empty());
  for (const auto& pinned : PinnedManifest()) {
    const google::protobuf::Descriptor* message = FindMessage(pinned.message);
    ASSERT_NE(message, nullptr) << pinned.message;
    ASSERT_EQ(message->field_count(), static_cast<int>(pinned.fields.size()))
        << pinned.message;
    for (const auto& field : pinned.fields) {
      const google::protobuf::FieldDescriptor* live = message->FindFieldByNumber(field.number);
      ASSERT_NE(live, nullptr) << pinned.message << " #" << field.number;
      EXPECT_EQ(live->name(), field.name) << pinned.message << " #" << field.number;
      EXPECT_EQ(message->FindFieldByName(field.name), live) << pinned.message;
    }
  }
}

TEST(XcomToolGatewayEvolution, AdditiveFieldInsertionBackwardCompatible) {
  xverse::xcom::v1::ObservationRecord producer;
  producer.set_sequence(4096U);
  producer.mutable_identity()->set_tool_id("tool-additive");
  std::string wire;
  ASSERT_TRUE(producer.SerializeToString(&wire));
  const std::size_t baseline_bytes = wire.size();
  // A later additive producer inserts field 41, below the reserved extension band.
  AppendVarintField(wire, 41U, 77U);
  ASSERT_GT(wire.size(), baseline_bytes);

  xverse::xcom::v1::ObservationRecord consumer;
  ASSERT_TRUE(consumer.ParseFromString(wire));
  EXPECT_EQ(consumer.sequence(), 4096U);
  EXPECT_EQ(consumer.identity().tool_id(), "tool-additive");
  ASSERT_EQ(UnknownFieldCount(consumer), 1U);
  ASSERT_NE(LastUnknownField(consumer), nullptr);
  EXPECT_EQ(LastUnknownField(consumer)->number(), 41);
  EXPECT_EQ(LastUnknownField(consumer)->varint(), 77U);

  std::string reserialized;
  ASSERT_TRUE(consumer.SerializeToString(&reserialized));
  xverse::xcom::v1::ObservationRecord third;
  ASSERT_TRUE(third.ParseFromString(reserialized));
  EXPECT_EQ(third.sequence(), 4096U);
  ASSERT_EQ(UnknownFieldCount(third), 1U);
  ASSERT_NE(LastUnknownField(third), nullptr);
  EXPECT_EQ(LastUnknownField(third)->number(), 41);
}

TEST(XcomToolGatewayEvolution, UnknownFieldForwardCompatible) {
  // A crafted bounded buffer carrying one field tag the compiled contract does not know.
  std::string wire = EnumWireValue(900U, 4242U);
  ASSERT_LE(wire.size(), std::size_t{24});
  xverse::xcom::v1::ObservationRecord record;
  ASSERT_TRUE(record.ParseFromString(wire));
  ASSERT_EQ(UnknownFieldCount(record), 1U);
  ASSERT_NE(LastUnknownField(record), nullptr);
  EXPECT_EQ(LastUnknownField(record)->number(), 900);
  EXPECT_EQ(LastUnknownField(record)->varint(), 4242U);

  std::string round_trip;
  ASSERT_TRUE(record.SerializeToString(&round_trip));
  EXPECT_EQ(round_trip, wire);

  xverse::xcom::v1::ObservationRecord reparsed;
  ASSERT_TRUE(reparsed.ParseFromString(round_trip));
  EXPECT_EQ(UnknownFieldCount(reparsed), 1U);
}

TEST(XcomToolGatewayEvolution, UnmappedEnumValuePreserved) {
  const google::protobuf::Descriptor* record_descriptor =
      xverse::xcom::v1::ObservationRecord::descriptor();
  const google::protobuf::FieldDescriptor* payload_state =
      record_descriptor->FindFieldByName("payload_state");
  ASSERT_NE(payload_state, nullptr);
  ASSERT_NE(payload_state->enum_type(), nullptr);

  // Field 7 (payload_state) as a varint carrying an unmapped value 99.
  const std::string wire = EnumWireValue(7U, 99U);
  xverse::xcom::v1::ObservationRecord record;
  ASSERT_TRUE(record.ParseFromString(wire));
  EXPECT_EQ(record.GetReflection()->GetEnumValue(record, payload_state), 99);

  std::string round_trip;
  ASSERT_TRUE(record.SerializeToString(&round_trip));
  xverse::xcom::v1::ObservationRecord reparsed;
  ASSERT_TRUE(reparsed.ParseFromString(round_trip));
  EXPECT_EQ(reparsed.GetReflection()->GetEnumValue(reparsed, payload_state), 99);

  // The unmapped value is not remapped to the zero/unspecified value.
  EXPECT_NE(reparsed.GetReflection()->GetEnumValue(reparsed, payload_state), 0);
}
