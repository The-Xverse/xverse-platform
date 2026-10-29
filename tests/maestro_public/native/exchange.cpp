/**
 * @file exchange.cpp
 * @brief Owned actual native FIFO exchange for public Maestro/Argus verification.
 * @ownership Owns lifecycle endpoints, native provider route, messages and tap.
 * @lifetime Owns its fixed output and stays alive until its exact owner stops it.
 * @thread_safety Single threaded. No external transport or application is touched.
 * @failure Bounded invalid input or failed public operation exits with failure.
 * This is a native contract test, not the requested Autoverse/Studio demonstration.
 */
#include "xverse/xcom/loopback_provider.hpp"

#include <nlohmann/json.hpp>

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace {
using namespace xverse::xcom;
using Json = nlohmann::json;

/** Copy an accepted public value; never dereference a failed factory. */
template <typename Result>
[[nodiscard]] auto need(const Result& result) {
  if (!result.has_value()) throw std::runtime_error("native public operation rejected");
  return *result.value();
}

/** Convert one validated hexadecimal byte nibble. */
[[nodiscard]] unsigned int nibble(const char value) {
  if (value >= '0' && value <= '9') return static_cast<unsigned int>(value - '0');
  if (value >= 'a' && value <= 'f') return 10U + static_cast<unsigned int>(value - 'a');
  throw std::runtime_error("invalid payload hex");
}

/** Decode at most128 owned bytes; no command text is interpreted. */
[[nodiscard]] std::vector<std::byte> decode(const std::string& text) {
  if (text.size() > 256U || text.size() % 2U != 0U) throw std::runtime_error("payload bound");
  std::vector<std::byte> result;
  for (std::size_t i = 0U; i < text.size(); i += 2U) {
    result.push_back(static_cast<std::byte>((nibble(text[i]) << 4U) | nibble(text[i + 1U])));
  }
  return result;
}

/** Serialize the exact visible bytes from an original ObservationRecord. */
[[nodiscard]] std::string hex(const std::span<const std::byte> bytes) {
  constexpr std::string_view digits = "0123456789abcdef";
  std::string result;
  for (const std::byte value : bytes) {
    const auto byte = std::to_integer<unsigned int>(value);
    result.push_back(digits[byte >> 4U]);
    result.push_back(digits[byte & 15U]);
  }
  return result;
}

/** Map original public accessors into Argus's versioned observation projection. */
[[nodiscard]] Json project(const ObservationRecord& record) {
  if (record.interaction_kind() != InteractionKind::message_event ||
      record.origin() != OriginKind::provider_generated ||
      record.payload_view_state() != PayloadViewState::complete ||
      record.provider_outcome() != ObservationProviderOutcome::accepted) {
    throw std::runtime_error("unexpected native observation");
  }
  Json result = {
      {"contractId", std::string(record.contract_id().value())},
      {"contractVersion", std::string(record.contract_version().value())},
      {"interfaceId", std::string(record.interface_id().value())},
      {"endpointId", std::string(record.endpoint_id().value())},
      {"schemaId", std::string(record.schema_id().value())},
      {"schemaVersion", std::string(record.schema_version().value())},
      {"interactionKind", "message_event"}, {"origin", "provider_generated"},
      {"sourceClock", {{"domain", std::string(record.source_clock_domain().value())},
                       {"unit", "ns"}, {"value", record.source_timestamp().nanoseconds()}}},
      {"observationClock", {{"domain", std::string(record.observation_clock_domain().value())},
                            {"unit", "ns"}, {"value", record.observation_timestamp().nanoseconds()}}},
      {"correlationId", std::string(record.correlation_id().value())},
      {"causationId", std::string(record.causation_id().value())},
      {"routeId", std::string(record.route_id().value())},
      {"providerId", std::string(record.provider_id().value())},
      {"sourcePayloadSize", record.source_payload_size()}, {"providerOutcome", "accepted"},
      {"payloadViewState", "complete"}, {"payloadSchemaState", "undecoded"},
      {"visibleBytesHex", hex(record.payload_bytes())},
      {"visibleByteCount", record.payload_bytes().size()},
      {"tapId", std::string(record.tap_id().value())},
      {"counters", {{"queued", record.counters().queued}, {"accepted", record.counters().accepted},
                    {"dropped", record.counters().dropped}, {"coalesced", record.counters().coalesced}}}};
  if (record.sequence().has_value()) result["sequence"] = *record.sequence();
  return result;
}

/** Perform actual provider submission and receipt, not synthetic hub publication. */
void exchange(const Json& config, const std::chrono::steady_clock::time_point origin) {
  const auto provider_id = config.at("providerId").get<std::string>();
  const auto interface_id = config.at("interfaceId").get<std::string>();
  const auto schema_id = config.at("schemaId").get<std::string>();
  const auto source_id = config.at("sourceEndpointId").get<std::string>();
  const auto destination_id = config.at("destinationEndpointId").get<std::string>();
  const auto route_id = config.at("routeId").get<std::string>();
  const auto plan_digest = config.at("planDigest").get<std::string>().substr(7U);
  const auto correlation = config.at("correlationId").get<std::string>();
  const auto cause = config.at("causationId").get<std::string>();
  const auto clock = config.at("nativeClockDomain").get<std::string>();
  const auto contract = need(CommunicationContract::create({interface_id, "1.0.0", interface_id,
      schema_id, "1.0.0", InteractionKind::message_event, EndpointDirection::produce,
      EndpointDirection::consume}));
  const auto source = need(EndpointSpec::create({source_id, plan_digest, provider_id,
      EndpointDirection::produce}, contract));
  const auto destination = need(EndpointSpec::create({destination_id, plan_digest, provider_id,
      EndpointDirection::consume}, contract));
  const auto route = need(RouteSpec::create({route_id, plan_digest, provider_id}, source, destination));
  LifecycleController lifecycle(need(LifecycleConfiguration::create({2U, 1U})));
  const auto source_handle = need(lifecycle.declare_endpoint(source));
  const auto destination_handle = need(lifecycle.declare_endpoint(destination));
  const auto route_handle = need(lifecycle.declare_route(route));
  static_cast<void>(need(lifecycle.validate_endpoint(source_handle)));
  static_cast<void>(need(lifecycle.validate_endpoint(destination_handle)));
  static_cast<void>(need(lifecycle.validate_route(route_handle, source_handle, destination_handle)));
  static_cast<void>(need(lifecycle.activate_endpoint(source_handle)));
  static_cast<void>(need(lifecycle.activate_endpoint(destination_handle)));
  ObservationHub hub;
  const auto tap_capacity = config.at("tapCapacity").get<std::size_t>();
  const bool deferred = config.at("deferPoll").get<bool>();
  if (tap_capacity == 0U || tap_capacity > 4U) throw std::runtime_error("tap capacity");
  const auto policy = ObservationTapSpec::create({kObservationContractVersion, "tap.mpx.native",
      {}, ObservationPayloadMode::bounded_prefix, 128U, tap_capacity,
      ObservationOverflowPolicy::drop_newest, ObservationValidityEffect::degrade_on_loss});
  if (!policy.has_value()) throw std::runtime_error("tap policy");
  const auto attached = hub.attach(*policy);
  if (!attached.handle.has_value()) throw std::runtime_error("tap attach");
  LoopbackProvider provider(need(ProviderDescriptor::create({provider_id, "1.0.0",
      "source.mpx.owned-native", 0x0FU, delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 128U, 1U, 1U})));
  ProviderComposition composition(need(ProviderRegistryConfiguration::create(1U)), hub);
  if (composition.register_provider(provider).outcome() != ProviderOutcome::registered) {
    throw std::runtime_error("provider registration");
  }
  const auto prepared = need(composition.prepare_route(lifecycle, route, route_handle,
      source_handle, destination_handle, {"1.0.0", InteractionKind::message_event,
      DeliveryCapability::best_effort, OrderingCapability::per_route_fifo, 128U, 1U}));
  if (composition.activate_route(prepared, lifecycle).outcome() != ProviderOutcome::activated) {
    throw std::runtime_error("route activation");
  }
  Json records = Json::array();
  Json inputs = Json::array();
  Json received = Json::array();
  const auto messages = config.at("messages").get<std::vector<std::string>>();
  if (messages.empty() || messages.size() > 4U) throw std::runtime_error("message bound");
  for (const auto& message : messages) {
    const auto payload = decode(message);
    const auto timestamp = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now() - origin).count();
    const std::string input_id = config.at("operationId").get<std::string>() +
        ".input." + std::to_string(inputs.size() + 1U);
    inputs.push_back({{"schemaVersion", "1.0"}, {"eventId", input_id},
        {"producerId", provider_id + ".input"}, {"origin", "configured-input"},
        {"sourceClock", {{"domain", clock}, {"unit", "ns"}, {"value", timestamp}}},
        {"correlationId", correlation}, {"upstreamCausationId", cause},
        {"routeId", route_id}, {"endpointId", source_id}, {"sourcePayloadSize", payload.size()}});
    const auto item = need(CommunicationItem::create({interface_id, "1.0.0", interface_id,
        source_id, schema_id, "1.0.0", InteractionKind::message_event, OriginKind::provider_generated,
        Timestamp(timestamp), clock, correlation, input_id, route_id, provider_id, payload}, contract));
    if (composition.submit(prepared, item, lifecycle).outcome() != ProviderOutcome::accepted) {
      throw std::runtime_error("native submit");
    }
    const auto delivered = need(composition.receive(prepared, lifecycle));
    if (delivered != item) throw std::runtime_error("native payload mismatch");
    received.push_back(hex(delivered.payload().bytes()));
    if (!deferred) {
      const auto observed = hub.poll(*attached.handle);
      if (!observed.record.has_value()) throw std::runtime_error("native observation missing");
      records.push_back(project(*observed.record));
    }
  }
  if (composition.drain_route(prepared, lifecycle).outcome() != ProviderOutcome::draining ||
      composition.close_route(prepared, lifecycle).outcome() != ProviderOutcome::closed) {
    throw std::runtime_error("native route cleanup");
  }
  if (deferred) {
    for (;;) {
      const auto observed = hub.poll(*attached.handle);
      if (observed.status.outcome == ObservationOutcome::no_record) break;
      if (!observed.record.has_value()) throw std::runtime_error("native observation poll");
      records.push_back(project(*observed.record));
    }
  }
  const auto snapshot = hub.snapshot(*attached.handle);
  if (!snapshot.has_value()) throw std::runtime_error("native final snapshot");
  const auto end = std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::steady_clock::now() - origin).count();
  const Json final_snapshot = {
      {"snapshotVersion", "1.0"},
      {"handle", {{"hubInstanceId", snapshot->handle.hub_instance_id()},
                  {"tapId", snapshot->handle.tap_id()}, {"generation", snapshot->handle.generation()}}},
      {"queued", snapshot->queued}, {"accepted", snapshot->accepted},
      {"dropped", snapshot->dropped}, {"coalesced", snapshot->coalesced},
      {"backpressureRejections", snapshot->backpressure_rejections},
      {"experimentValidityDegraded", snapshot->experiment_validity_degraded},
      {"declaredTapId", std::string(snapshot->declared_tap_id.value())},
      {"validityEffect", "degrade_on_loss"},
      {"validityState", std::string(to_string(snapshot->validity_state))},
      {"intervalProvenance", {{"streamId", config.at("runId").get<std::string>() + ".native"},
          {"intervalId", "batch.1"}, {"closure", "closed"},
          {"start", {{"domain", clock}, {"unit", "ns"}, {"value", 0}}},
          {"end", {{"domain", clock}, {"unit", "ns"}, {"value", end}}},
          {"provenance", "actual-native-route-quiesced-before-snapshot"}}}};
  if (hub.detach(*attached.handle).outcome != ObservationOutcome::accepted) {
    throw std::runtime_error("native tap detach");
  }
  Json witness = {{"runId", config.at("runId")}, {"planDigest", config.at("planDigest")},
      {"inputSemanticDigest", config.at("inputSemanticDigest")}, {"providerId", provider_id},
      {"installationDigest", config.at("installationDigest")}, {"batchSequence", 1}};
  const Json projection = {{"projectionVersion", "1.0"},
      {"upstreamContractVersion", std::string(kObservationContractVersion)},
      {"exporter", {{"task", "MPX-T06-owned-native-exchange"}, {"toolVersion", "1.0"}}},
      {"records", records}, {"extensions", {{"io.xverse.maestro.execution", witness},
      {"io.xverse.native.snapshots", Json::array({final_snapshot})},
      {"io.xverse.native.inputs", inputs},
      {"io.xverse.native.receipt", {{"receivedPayloadsHex", received},
          {"transport", "owned-native-in-process-fifo"}, {"routeReleased", true}}}}}};
  const auto encoded = projection.dump();
  if (encoded.size() > 65536U) throw std::runtime_error("projection bound");
  std::ofstream output("native-projection.tmp", std::ios::binary | std::ios::trunc);
  output << encoded;
  output.close();
  if (!output) throw std::runtime_error("projection persistence");
  std::filesystem::rename("native-projection.tmp", "native-projection.json");
}
}  // namespace

/** Bounded frozen input only; stays an owned child until Maestro stops it. */
int main() {
  try {
    const auto origin = std::chrono::steady_clock::now();
    std::string raw;
    char value{};
    while (std::cin.get(value)) {
      if (raw.size() >= 4096U) return 2;
      raw.push_back(value);
    }
    exchange(Json::parse(raw), origin);
    for (;;) std::this_thread::sleep_for(std::chrono::milliseconds(50));
  } catch (const std::exception&) {
    return 2;
  }
}
