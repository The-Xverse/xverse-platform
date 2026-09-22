/**
 * @file unit_tests.cpp
 * @brief Focused bounded observation-boundary unit and concurrency fixtures.
 * @ownership Fixtures own every contract, item, hub, tap policy, source byte, and pulled record.
 * @lifetime Each check validates returned records after their source event storage has gone out of scope.
 * @thread_safety The final fixture concurrently publishes and pulls through one serialized hub.
 * @failure The executable reports failed assertions and exits nonzero; it performs no external I/O.
 * @par Traceability
 * Verifies XCOM-OBS-002 through XCOM-OBS-006 and XCOM-OBS-008 against observation.hpp and
 * observation.cpp. XCOM-OBS-001 and XCOM-OBS-009 remain source/interface inspection obligations.
 */

#include "xverse/xcom/observation.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <iostream>
#include <string>
#include <thread>

namespace {

using namespace xverse::xcom;

/** @brief Report one focused expectation. @param condition Expected result. @param message Detail. */
[[nodiscard]] bool expect(const bool condition, const std::string_view message) {
  if (!condition) {
    std::cerr << "observation unit failure: " << message << '\n';
  }
  return condition;
}

/** @return A valid message contract for all local records. */
[[nodiscard]] CommunicationContract make_contract() {
  const auto result = CommunicationContract::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "schema.alpha", "2.0.1",
       InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume});
  return *result.value();
}

/** @return A valid value-owned item with a caller-selected two-byte payload prefix. */
[[nodiscard]] CommunicationItem make_item(const std::array<std::byte, 4U>& payload) {
  const CommunicationContract contract = make_contract();
  const auto result = CommunicationItem::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "endpoint.alpha", "schema.alpha", "2.0.1",
       InteractionKind::message_event, OriginKind::component, Timestamp(42), "clock.source",
       "correlation.alpha", "causation.alpha", "route.alpha", "provider.alpha", payload},
      contract);
  return *result.value();
}

/** @return One valid policy with a caller-selected payload and overflow behavior. */
[[nodiscard]] ObservationTapSpec make_spec(const ObservationPayloadMode payload_mode,
                                           const std::size_t maximum_payload_bytes,
                                           const std::size_t record_capacity,
                                           const ObservationOverflowPolicy overflow_policy) {
  const auto result = ObservationTapSpec::create(
      {kObservationContractVersion,
       {"contract.alpha", "interface.alpha", "endpoint.alpha", "route.alpha", "provider.alpha",
        InteractionKind::message_event},
       payload_mode, maximum_payload_bytes, record_capacity, overflow_policy});
  return *result;
}

/** @brief Verify default metadata-only records expose no bytes while retaining complete metadata. */
[[nodiscard]] bool test_metadata_only() {
  ObservationHub hub;
  const auto attach = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                           ObservationOverflowPolicy::drop_newest));
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem item = make_item(bytes);
  if (!expect(attach.status.succeeded() && attach.handle.has_value(), "metadata tap attachment") ||
      !expect(hub.publish({item, Timestamp(99), "clock.observer", 7U,
                           ObservationProviderOutcome::accepted})
                  .succeeded(),
              "metadata record publication")) {
    return false;
  }
  const auto pulled = hub.poll(*attach.handle);
  if (!expect(pulled.status.succeeded() && pulled.record.has_value(), "metadata record pull")) {
    return false;
  }
  const ObservationRecord& record = *pulled.record;
  return expect(record.payload_bytes().empty(), "metadata policy leaked payload bytes") &&
         expect(record.payload_view_state() == PayloadViewState::omitted, "metadata state") &&
         expect(record.payload_schema_state() == PayloadSchemaState::undecoded, "schema state") &&
         expect(record.source_payload_size() == bytes.size(), "source size") &&
         expect(record.contract_id().value() == "contract.alpha", "contract identity") &&
         expect(record.interface_id().value() == "interface.alpha", "interface identity") &&
         expect(record.endpoint_id().value() == "endpoint.alpha", "endpoint identity") &&
         expect(record.route_id().value() == "route.alpha", "route identity") &&
         expect(record.provider_id().value() == "provider.alpha", "provider identity") &&
         expect(record.correlation_id().value() == "correlation.alpha", "correlation") &&
         expect(record.causation_id().value() == "causation.alpha", "causation") &&
         expect(record.source_timestamp().nanoseconds() == 42, "source timestamp") &&
         expect(record.observation_timestamp().nanoseconds() == 99, "observation timestamp") &&
         expect(record.sequence().has_value() && *record.sequence() == 7U, "sequence") &&
         expect(record.provider_outcome() == ObservationProviderOutcome::accepted, "provider outcome");
}

/** @brief Verify bounded payload, truncation, and explicit redaction states are never inferred. */
[[nodiscard]] bool test_controlled_payload_states() {
  const std::array<std::byte, 4U> bytes{std::byte{8}, std::byte{9}, std::byte{10}, std::byte{11}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub prefix_hub;
  const auto prefix = prefix_hub.attach(make_spec(ObservationPayloadMode::bounded_prefix, 2U, 1U,
                                                  ObservationOverflowPolicy::drop_newest));
  if (!expect(prefix_hub.publish({item, Timestamp(1), "clock.observer", std::nullopt,
                                  ObservationProviderOutcome::rejected})
                  .succeeded(),
              "prefix publication")) {
    return false;
  }
  const auto prefix_record = prefix_hub.poll(*prefix.handle);
  ObservationHub redacted_hub;
  const auto redacted = redacted_hub.attach(make_spec(ObservationPayloadMode::redacted, 0U, 1U,
                                                      ObservationOverflowPolicy::drop_newest));
  const auto redacted_publish = redacted_hub.publish(
      {item, Timestamp(2), "clock.observer", std::nullopt, ObservationProviderOutcome::accepted});
  const auto redacted_record = redacted_hub.poll(*redacted.handle);
  return expect(prefix_record.record.has_value(), "prefix record") &&
         expect(prefix_record.record->payload_bytes().size() == 2U, "prefix byte bound") &&
         expect(prefix_record.record->payload_bytes()[0] == std::byte{8}, "prefix byte zero") &&
         expect(prefix_record.record->payload_view_state() == PayloadViewState::truncated,
                "truncation state") &&
         expect(prefix_record.record->provider_outcome() == ObservationProviderOutcome::rejected,
                "rejected outcome retained") &&
         expect(redacted_publish.succeeded() && redacted_record.record.has_value(), "redacted record") &&
         expect(redacted_record.record->payload_bytes().empty(), "redacted payload empty") &&
         expect(redacted_record.record->payload_view_state() == PayloadViewState::redacted,
                "redacted state");
}

/** @brief Verify best-effort saturation counts loss without changing pull order. */
[[nodiscard]] bool test_best_effort_overflow() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{0}, std::byte{0}, std::byte{0}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub drop_hub;
  const auto drop = drop_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                              ObservationOverflowPolicy::drop_newest));
  const auto first = drop_hub.publish(
      {item, Timestamp(1), "clock.observer", 1U, ObservationProviderOutcome::accepted});
  const auto second = drop_hub.publish(
      {item, Timestamp(2), "clock.observer", 2U, ObservationProviderOutcome::accepted});
  const auto drop_snapshot = drop_hub.snapshot(*drop.handle);
  const auto retained = drop_hub.poll(*drop.handle);
  ObservationHub coalesce_hub;
  const auto coalesce = coalesce_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                                      ObservationOverflowPolicy::coalesce_latest));
  static_cast<void>(coalesce_hub.publish(
      {item, Timestamp(3), "clock.observer", 3U, ObservationProviderOutcome::accepted}));
  static_cast<void>(coalesce_hub.publish(
      {item, Timestamp(4), "clock.observer", 4U, ObservationProviderOutcome::accepted}));
  const auto coalesce_snapshot = coalesce_hub.snapshot(*coalesce.handle);
  const auto replacement = coalesce_hub.poll(*coalesce.handle);
  return expect(first.succeeded() && second.succeeded(), "drop operations stay best effort") &&
         expect(drop_snapshot.has_value() && drop_snapshot->accepted == 1U &&
                    drop_snapshot->dropped == 1U && drop_snapshot->queued == 1U,
                "drop counters") &&
         expect(retained.record.has_value() && retained.record->sequence().has_value() &&
                    *retained.record->sequence() == 1U,
                "drop preserves oldest record") &&
         expect(coalesce_snapshot.has_value() && coalesce_snapshot->coalesced == 1U &&
                    coalesce_snapshot->queued == 1U,
                "coalesce counters") &&
         expect(replacement.record.has_value() && replacement.record->sequence().has_value() &&
                    *replacement.record->sequence() == 4U,
                "coalesce retains latest record");
}

/** @brief Verify lossless preflight is explicit, degrading, acknowledgeable, and handle-scoped. */
[[nodiscard]] bool test_lossless_and_exact_handles() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub hub;
  ObservationHub foreign_hub;
  const auto attach = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                           ObservationOverflowPolicy::lossless_validation));
  const auto foreign = foreign_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                                    ObservationOverflowPolicy::drop_newest));
  static_cast<void>(hub.publish(
      {item, Timestamp(1), "clock.observer", 1U, ObservationProviderOutcome::accepted}));
  const auto blocked = hub.preflight(item);
  const auto degraded = hub.snapshot(*attach.handle);
  const auto acknowledged = hub.acknowledge(*attach.handle);
  const auto restored = hub.snapshot(*attach.handle);
  const auto foreign_poll = hub.poll(*foreign.handle);
  const auto detached = hub.detach(*attach.handle);
  const auto duplicate = hub.detach(*attach.handle);
  return expect(blocked.outcome == ObservationOutcome::observation_backpressure, "lossless status") &&
         expect(degraded.has_value() && degraded->experiment_validity_degraded &&
                    degraded->backpressure_rejections == 1U,
                "degraded counter") &&
         expect(acknowledged.succeeded() && restored.has_value() &&
                    !restored->experiment_validity_degraded,
                "exact acknowledge") &&
         expect(foreign_poll.status.outcome == ObservationOutcome::invalid_tap_handle, "foreign handle") &&
         expect(detached.succeeded() && duplicate.outcome == ObservationOutcome::tap_closed,
                "safe exact detach");
}

/** @brief Verify pull consumers have no callback path and tolerate concurrent publish/pull serialization. */
[[nodiscard]] bool test_synthetic_sink_concurrency() {
  const std::array<std::byte, 4U> bytes{std::byte{4}, std::byte{3}, std::byte{2}, std::byte{1}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub hub;
  const auto attach = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 16U,
                                           ObservationOverflowPolicy::drop_newest));
  SyntheticObservationSink sink(hub, *attach.handle);
  std::atomic<bool> valid{true};
  std::thread writer([&hub, &item, &valid]() {
    for (std::uint64_t index = 0U; index < 64U; ++index) {
      if (!hub.publish({item, Timestamp(static_cast<std::int64_t>(index)), "clock.observer", index,
                        ObservationProviderOutcome::accepted})
               .succeeded()) {
        valid = false;
      }
    }
  });
  std::thread reader([&sink, &valid]() {
    for (std::size_t index = 0U; index < 64U; ++index) {
      const auto result = sink.pull();
      if (!result.status.succeeded() && result.status.outcome != ObservationOutcome::no_record) {
        valid = false;
      }
    }
  });
  writer.join();
  reader.join();
  sink.disconnect();
  return expect(valid.load(), "serialized concurrent pull/publish") &&
         expect(sink.pull().status.outcome == ObservationOutcome::sink_disconnected,
                "local disconnect isolation");
}

}  // namespace

/** @brief Run all focused observation fixtures. @return Zero only when every check passes. */
int main() {
  return test_metadata_only() && test_controlled_payload_states() && test_best_effort_overflow() &&
                 test_lossless_and_exact_handles() && test_synthetic_sink_concurrency()
             ? 0
             : 1;
}
