/**
 * @file argus2_owned_record_producer.cpp
 * @brief Owned, neutral ARGUS2 producer fixture over the accepted C++ X-COM observation boundary.
 *
 * This fixture is owned test material, never a change to any accepted C++ header or source. It
 * drives an in-process xverse::xcom::ObservationHub (attach -> reserve -> commit -> poll/snapshot)
 * to produce owned ObservationRecord and ObservationSnapshot values for the four payload
 * visibility states plus one dropped/degraded interval, and serializes them into the frozen ARGUS2
 * observation/snapshot projection (projectionVersion 1.0, upstreamContractVersion
 * kObservationContractVersion). It attaches no live tap outside the fixture, holds no delivery
 * authority, claims no scientific result and performs no I/O beyond stdout.
 */

#include "xverse/xcom/observation.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace {

using namespace xverse::xcom;

/** @return Stable external text for one provider outcome. */
[[nodiscard]] std::string_view provider_outcome_text(const ObservationProviderOutcome value) noexcept {
  switch (value) {
    case ObservationProviderOutcome::not_attempted:
      return "not_attempted";
    case ObservationProviderOutcome::accepted:
      return "accepted";
    case ObservationProviderOutcome::rejected:
      return "rejected";
  }
  return "not_attempted";
}

/** @return Stable external text for one payload view state. */
[[nodiscard]] std::string_view payload_view_text(const PayloadViewState value) noexcept {
  switch (value) {
    case PayloadViewState::omitted:
      return "omitted";
    case PayloadViewState::complete:
      return "complete";
    case PayloadViewState::truncated:
      return "truncated";
    case PayloadViewState::redacted:
      return "redacted";
  }
  return "omitted";
}

/** @return The frozen ARGUS2 projection interaction vocabulary for one interaction family. */
[[nodiscard]] std::string_view interaction_text(const InteractionKind value) noexcept {
  switch (value) {
    case InteractionKind::signal_state_update:
      return "signal_state_update";
    case InteractionKind::message_event:
      return "message_event";
    case InteractionKind::service_request:
      return "service_request";
    case InteractionKind::service_response:
      return "service_response";
  }
  return "message_event";
}

/** @return The frozen ARGUS2 projection origin vocabulary for one origin kind. */
[[nodiscard]] std::string_view origin_text(const OriginKind value) noexcept {
  switch (value) {
    case OriginKind::component:
      return "component";
    case OriginKind::validation_tool:
      return "validation_tool";
    case OriginKind::replay:
      return "replay";
    case OriginKind::provider_generated:
      return "provider_generated";
  }
  return "component";
}

/** @return The frozen ARGUS2 projection validity-effect vocabulary for one declaration. */
[[nodiscard]] std::string_view validity_effect_text(const ObservationValidityEffect value) noexcept {
  switch (value) {
    case ObservationValidityEffect::none:
      return "none";
    case ObservationValidityEffect::degrade_on_loss:
      return "degrade_on_loss";
    case ObservationValidityEffect::invalidate_on_loss:
      return "invalidate_on_loss";
  }
  return "none";
}

/** @return Lowercase hexadecimal text of the visible payload bytes. */
[[nodiscard]] std::string hex_bytes(const std::span<const std::byte> bytes) {
  static constexpr char kDigits[] = "0123456789abcdef";
  std::string result;
  result.reserve(bytes.size() * 2U);
  for (const std::byte value : bytes) {
    const auto byte = static_cast<unsigned int>(std::to_integer<unsigned char>(value));
    result.push_back(kDigits[byte >> 4U]);
    result.push_back(kDigits[byte & 0x0FU]);
  }
  return result;
}

/** @brief Print one owned observation record as the frozen projection object. */
void print_record(const ObservationRecord& record) {
  std::cout << "{";
  std::cout << "\"contractId\":\"" << record.contract_id().value() << "\",";
  std::cout << "\"contractVersion\":\"" << record.contract_version().value() << "\",";
  std::cout << "\"interfaceId\":\"" << record.interface_id().value() << "\",";
  std::cout << "\"endpointId\":\"" << record.endpoint_id().value() << "\",";
  std::cout << "\"schemaId\":\"" << record.schema_id().value() << "\",";
  std::cout << "\"schemaVersion\":\"" << record.schema_version().value() << "\",";
  std::cout << "\"interactionKind\":\"" << interaction_text(record.interaction_kind()) << "\",";
  std::cout << "\"origin\":\"" << origin_text(record.origin()) << "\",";
  std::cout << "\"sourceClock\":{\"domain\":\"" << record.source_clock_domain().value()
            << "\",\"unit\":\"ns\",\"value\":" << record.source_timestamp().nanoseconds() << "},";
  std::cout << "\"observationClock\":{\"domain\":\"" << record.observation_clock_domain().value()
            << "\",\"unit\":\"ns\",\"value\":" << record.observation_timestamp().nanoseconds() << "},";
  if (record.sequence().has_value()) {
    std::cout << "\"sequence\":" << *record.sequence() << ",";
  }
  std::cout << "\"correlationId\":\"" << record.correlation_id().value() << "\",";
  std::cout << "\"causationId\":\"" << record.causation_id().value() << "\",";
  std::cout << "\"routeId\":\"" << record.route_id().value() << "\",";
  std::cout << "\"providerId\":\"" << record.provider_id().value() << "\",";
  std::cout << "\"sourcePayloadSize\":" << record.source_payload_size() << ",";
  std::cout << "\"providerOutcome\":\"" << provider_outcome_text(record.provider_outcome()) << "\",";
  std::cout << "\"payloadViewState\":\"" << payload_view_text(record.payload_view_state()) << "\",";
  std::cout << "\"payloadSchemaState\":\"undecoded\",";
  std::cout << "\"visibleBytesHex\":\"" << hex_bytes(record.payload_bytes()) << "\",";
  std::cout << "\"visibleByteCount\":" << record.payload_bytes().size() << ",";
  std::cout << "\"tapId\":\"" << record.tap_id().value() << "\",";
  std::cout << "\"counters\":{"
            << "\"queued\":" << record.counters().queued << ","
            << "\"accepted\":" << record.counters().accepted << ","
            << "\"dropped\":" << record.counters().dropped << ","
            << "\"coalesced\":" << record.counters().coalesced << "}}";
}

/** @brief Print one exact handle object. */
void print_handle(const ObservationTapHandle& handle) {
  std::cout << "{\"hubInstanceId\":" << handle.hub_instance_id() << ",\"tapId\":" << handle.tap_id()
            << ",\"generation\":" << handle.generation() << "}";
}

/** @brief Print one owned observation snapshot as the frozen snapshot projection. */
void print_snapshot(const ObservationSnapshot& snapshot) {
  std::cout << "{";
  std::cout << "\"snapshotVersion\":\"1.0\",";
  std::cout << "\"handle\":";
  print_handle(snapshot.handle);
  std::cout << ",";
  std::cout << "\"queued\":" << snapshot.queued << ",";
  std::cout << "\"accepted\":" << snapshot.accepted << ",";
  std::cout << "\"dropped\":" << snapshot.dropped << ",";
  std::cout << "\"coalesced\":" << snapshot.coalesced << ",";
  std::cout << "\"backpressureRejections\":" << snapshot.backpressure_rejections << ",";
  std::cout << "\"experimentValidityDegraded\":" << (snapshot.experiment_validity_degraded ? "true" : "false") << ",";
  std::cout << "\"declaredTapId\":\"" << snapshot.declared_tap_id.value() << "\",";
  std::cout << "\"validityEffect\":\"" << validity_effect_text(snapshot.validity_effect) << "\",";
  std::cout << "\"validityState\":\"" << to_string(snapshot.validity_state) << "\",";
  std::cout << "\"intervalProvenance\":{\"streamId\":\"stream.argus2\",\"intervalId\":\"interval.1\","
               "\"closure\":\"closed\","
               "\"start\":{\"domain\":\"clock.observer\",\"unit\":\"ns\",\"value\":0},"
               "\"end\":{\"domain\":\"clock.observer\",\"unit\":\"ns\",\"value\":1000},"
               "\"provenance\":\"owned-cpp-fixture-declared\"}";
  std::cout << "}";
}

/** @return A valid contract for the selected interaction family. */
[[nodiscard]] CommunicationContract make_contract(const InteractionKind kind) {
  const auto result = CommunicationContract::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "schema.alpha", "2.0.1", kind,
       EndpointDirection::produce, EndpointDirection::consume});
  return *result.value();
}

/** @return A valid value-owned item with a caller-selected payload and route. */
[[nodiscard]] CommunicationItem make_item(const std::array<std::byte, 8U>& payload,
                                          const std::size_t payload_size, const std::string_view tap) {
  const CommunicationContract contract = make_contract(InteractionKind::message_event);
  const auto result = CommunicationItem::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "endpoint.alpha", "schema.alpha", "2.0.1",
       InteractionKind::message_event, OriginKind::component, Timestamp(42), "clock.source",
       "correlation.alpha", "causation.alpha", "route.alpha", "provider.alpha",
       std::span<const std::byte>(payload.data(), payload_size)},
      contract);
  (void)tap;
  return *result.value();
}

/** @brief Reserve before the simulated provider point, then commit an explicit accepted outcome. */
[[nodiscard]] bool emit(ObservationHub& hub, const CommunicationItem& item, const std::uint64_t sequence) {
  auto result = hub.reserve(item);
  if (!result.status.succeeded() || !result.reservation.has_value()) {
    return false;
  }
  const auto status = hub.commit(std::move(*result.reservation),
                                 {item, Timestamp(static_cast<std::int64_t>(sequence)), "clock.observer",
                                  sequence, ObservationProviderOutcome::accepted});
  return status.succeeded();
}

/** @brief Emit every projection case: metadata-only, redacted, bounded prefix, complete, snapshot. */
bool produce() {
  ObservationHub hub;
  const std::array<std::byte, 8U> payload{std::byte{0x00}, std::byte{0xFF}, std::byte{0x10},
                                          std::byte{0x20}, std::byte{0x30}, std::byte{0x40},
                                          std::byte{0x50}, std::byte{0x60}};

  struct Case final {
    const char* tap;
    ObservationPayloadMode mode;
    std::size_t maximum;
    std::size_t size;
  };
  const std::array<Case, 4U> cases{{
      {"tap.omitted", ObservationPayloadMode::metadata_only, 0U, 8U},
      {"tap.redacted", ObservationPayloadMode::redacted, 0U, 8U},
      {"tap.truncated", ObservationPayloadMode::bounded_prefix, 2U, 8U},
      {"tap.complete", ObservationPayloadMode::bounded_prefix, 8U, 8U},
  }};

  std::vector<std::optional<ObservationTapHandle>> handles;
  handles.reserve(cases.size());
  for (std::size_t index = 0U; index < cases.size(); ++index) {
    const auto spec = ObservationTapSpec::create(
        {kObservationContractVersion, cases[index].tap, ObservationFilterInput{}, cases[index].mode,
         cases[index].maximum, 4U, ObservationOverflowPolicy::drop_newest,
         ObservationValidityEffect::none});
    if (!spec.has_value()) {
      return false;
    }
    auto attached = hub.attach(*spec);
    if (!attached.status.succeeded() || !attached.handle.has_value()) {
      return false;
    }
    handles.push_back(*attached.handle);
    const CommunicationItem item = make_item(payload, cases[index].size, cases[index].tap);
    if (!emit(hub, item, static_cast<std::uint64_t>(index + 1U))) {
      return false;
    }
  }

  std::cout << "{\"contractVersion\":\"" << kObservationContractVersion << "\",";
  std::cout << "\"projection\":{\"projectionVersion\":\"1.0\",\"upstreamContractVersion\":\""
            << kObservationContractVersion
            << "\",\"exporter\":{\"task\":\"ARGUS2\",\"toolVersion\":\"0.1.0\","
               "\"provenance\":{\"available\":true,\"note\":\"owned C++20 producer fixture\"}},"
               "\"records\":[";
  bool first = true;
  for (std::size_t index = 0U; index < handles.size(); ++index) {
    auto polled = hub.poll(*handles[index]);
    if (!polled.record.has_value()) {
      return false;
    }
    if (!first) {
      std::cout << ",";
    }
    first = false;
    print_record(*polled.record);
  }
  std::cout << "]},";

  // A separate tap with declared degrade-on-loss over a capacity-one queue produces a real
  // dropped and degraded interval for the snapshot case.
  const auto degraded_spec = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.degraded", ObservationFilterInput{},
       ObservationPayloadMode::metadata_only, 0U, 1U, ObservationOverflowPolicy::drop_newest,
       ObservationValidityEffect::degrade_on_loss});
  if (!degraded_spec.has_value()) {
    return false;
  }
  auto degraded = hub.attach(*degraded_spec);
  if (!degraded.status.succeeded() || !degraded.handle.has_value()) {
    return false;
  }
  const CommunicationItem first_item = make_item(payload, 8U, "tap.degraded");
  const CommunicationItem second_item = make_item(payload, 8U, "tap.degraded");
  if (!emit(hub, first_item, 101U) || !emit(hub, second_item, 102U)) {
    return false;
  }
  const auto snapshot = hub.snapshot(*degraded.handle);
  if (!snapshot.has_value()) {
    return false;
  }
  std::cout << "\"snapshot\":";
  print_snapshot(*snapshot);
  std::cout << "}" << std::endl;
  return true;
}

}  // namespace

/** @brief Entry point: emit the owned projection JSON or exit nonzero without partial output. */
int main() {
  if (!produce()) {
    std::cerr << "argus2 owned producer failure" << std::endl;
    return 1;
  }
  return 0;
}
