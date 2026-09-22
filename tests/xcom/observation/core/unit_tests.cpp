/**
 * @file unit_tests.cpp
 * @brief Focused bounded observation-boundary unit and concurrency fixtures.
 * @ownership Fixtures own every contract, item, hub, tap policy, reservation, and pulled record.
 * @lifetime Returned records are checked independently of source-event storage; every reservation is
 * committed, cancelled, or scope-cancelled before its hub is destroyed.
 * @thread_safety Concurrency fixtures force competing reservations and serialized publication/pulls.
 * @failure The executable reports failed assertions and exits nonzero; it performs no external I/O.
 * @par Traceability
 * Verifies XCOM-OBS-001 through XCOM-OBS-006 and XCOM-OBS-008 against observation.hpp and
 * observation.cpp. XCOM-OBS-009 remains a source/interface inspection obligation.
 */

#include "xverse/xcom/observation.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <iostream>
#include <string_view>
#include <thread>
#include <utility>

namespace {

using namespace xverse::xcom;

/** @brief Report one focused expectation. @param condition Expected result. @param message Detail. */
[[nodiscard]] bool expect(const bool condition, const std::string_view message) {
  if (!condition) {
    std::cerr << "observation unit failure: " << message << '\n';
  }
  return condition;
}

/** @return Source direction compatible with kind. */
[[nodiscard]] EndpointDirection source_direction(const InteractionKind kind) noexcept {
  if (kind == InteractionKind::service_request) {
    return EndpointDirection::request;
  }
  if (kind == InteractionKind::service_response) {
    return EndpointDirection::respond;
  }
  return EndpointDirection::produce;
}

/** @return Target direction compatible with kind. */
[[nodiscard]] EndpointDirection target_direction(const InteractionKind kind) noexcept {
  if (kind == InteractionKind::service_request) {
    return EndpointDirection::respond;
  }
  if (kind == InteractionKind::service_response) {
    return EndpointDirection::request;
  }
  return EndpointDirection::consume;
}

/** @return A valid contract for the selected interaction family. */
[[nodiscard]] CommunicationContract make_contract(const InteractionKind kind) {
  const auto result = CommunicationContract::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "schema.alpha", "2.0.1", kind,
       source_direction(kind), target_direction(kind)});
  return *result.value();
}

/** @return A valid value-owned item with caller-selected logical coalescing fields. */
[[nodiscard]] CommunicationItem make_item(
    const std::array<std::byte, 4U>& payload, const std::string_view route_id = "route.alpha",
    const std::string_view provider_id = "provider.alpha",
    const OriginKind origin = OriginKind::component,
    const InteractionKind kind = InteractionKind::message_event) {
  const CommunicationContract contract = make_contract(kind);
  const auto result = CommunicationItem::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "endpoint.alpha", "schema.alpha", "2.0.1",
       kind, origin, Timestamp(42), "clock.source", "correlation.alpha", "causation.alpha", route_id,
       provider_id, payload},
      contract);
  return *result.value();
}

/** @return One valid policy with a caller-selected filter, payload, and overflow behavior. */
[[nodiscard]] ObservationTapSpec make_spec(
    const ObservationPayloadMode payload_mode, const std::size_t maximum_payload_bytes,
    const std::size_t record_capacity, const ObservationOverflowPolicy overflow_policy,
    const ObservationFilterInput& filter = {}) {
  const auto result = ObservationTapSpec::create({kObservationContractVersion, filter, payload_mode,
                                                   maximum_payload_bytes, record_capacity,
                                                   overflow_policy});
  return *result;
}

/** @brief Reserve before the simulated provider point, then commit an explicit provider outcome. */
[[nodiscard]] ObservationStatus emit(ObservationHub& hub, const CommunicationItem& item,
                                     const std::uint64_t sequence,
                                     const ObservationProviderOutcome provider_outcome =
                                         ObservationProviderOutcome::accepted) {
  auto result = hub.reserve(item);
  if (!result.status.succeeded() || !result.reservation.has_value()) {
    return result.status;
  }
  return hub.commit(std::move(*result.reservation),
                    {item, Timestamp(static_cast<std::int64_t>(sequence)), "clock.observer", sequence,
                     provider_outcome});
}

/** @brief Verify exact filters, origin constraints, versions, bounds, and all interaction families. */
[[nodiscard]] bool test_values_filters_and_versions() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem item = make_item(bytes);
  const auto exact = ObservationFilter::create(
      {"contract.alpha", "interface.alpha", "endpoint.alpha", "route.alpha", "provider.alpha",
       InteractionKind::message_event, OriginKind::component});
  const auto wrong_contract = ObservationFilter::create({"contract.other", {}, {}, {}, {}, std::nullopt});
  const auto wrong_interface = ObservationFilter::create({{}, "interface.other", {}, {}, {}, std::nullopt});
  const auto wrong_endpoint = ObservationFilter::create({{}, {}, "endpoint.other", {}, {}, std::nullopt});
  const auto wrong_route = ObservationFilter::create({{}, {}, {}, "route.other", {}, std::nullopt});
  const auto wrong_provider = ObservationFilter::create({{}, {}, {}, {}, "provider.other", std::nullopt});
  const auto wrong_kind = ObservationFilter::create(
      {{}, {}, {}, {}, {}, InteractionKind::service_request});
  const auto wrong_origin = ObservationFilter::create(
      {{}, {}, {}, {}, {}, std::nullopt, OriginKind::validation_tool});
  const auto unsupported = ObservationTapSpec::create(
      {"2.0.0", {}, ObservationPayloadMode::metadata_only, 0U, 1U,
       ObservationOverflowPolicy::drop_newest});
  const auto zero_capacity = ObservationTapSpec::create(
      {kObservationContractVersion, {}, ObservationPayloadMode::metadata_only, 0U, 0U,
       ObservationOverflowPolicy::drop_newest});
  const auto oversized_prefix = ObservationTapSpec::create(
      {kObservationContractVersion, {}, ObservationPayloadMode::bounded_prefix,
       kMaximumObservedPayloadBytes + 1U, 1U, ObservationOverflowPolicy::drop_newest});
  bool valid = expect(exact.has_value() && exact->matches(item), "exact filter") &&
               expect(wrong_contract.has_value() && !wrong_contract->matches(item), "contract filter") &&
               expect(wrong_interface.has_value() && !wrong_interface->matches(item), "interface filter") &&
               expect(wrong_endpoint.has_value() && !wrong_endpoint->matches(item), "endpoint filter") &&
               expect(wrong_route.has_value() && !wrong_route->matches(item), "route filter") &&
               expect(wrong_provider.has_value() && !wrong_provider->matches(item), "provider filter") &&
               expect(wrong_kind.has_value() && !wrong_kind->matches(item), "interaction filter") &&
               expect(wrong_origin.has_value() && !wrong_origin->matches(item), "origin filter") &&
               expect(!unsupported.has_value(), "unsupported observation version") &&
               expect(!zero_capacity.has_value(), "zero record capacity") &&
               expect(!oversized_prefix.has_value(), "oversized payload prefix");

  const std::array<InteractionKind, 4U> kinds{
      InteractionKind::signal_state_update, InteractionKind::message_event,
      InteractionKind::service_request, InteractionKind::service_response};
  ObservationHub hub;
  const auto attached = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, kinds.size(),
                                             ObservationOverflowPolicy::drop_newest));
  for (std::size_t index = 0U; index < kinds.size(); ++index) {
    const CommunicationItem family_item = make_item(bytes, "route.alpha", "provider.alpha",
                                                    OriginKind::component, kinds[index]);
    valid = expect(emit(hub, family_item, index).succeeded(), "interaction publication") && valid;
  }
  for (const InteractionKind kind : kinds) {
    const auto pulled = hub.poll(*attached.handle);
    valid = expect(pulled.record.has_value() && pulled.record->interaction_kind() == kind,
                   "interaction family retained") &&
            valid;
  }
  return valid;
}

/** @brief Verify metadata-only exposes no bytes while retaining all normalized metadata. */
[[nodiscard]] bool test_metadata_only() {
  ObservationHub hub;
  const auto attach = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                           ObservationOverflowPolicy::drop_newest));
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem item = make_item(bytes);
  if (!expect(attach.status.succeeded() && attach.handle.has_value(), "metadata tap attachment") ||
      !expect(emit(hub, item, 99U).succeeded(), "metadata record publication")) {
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
         expect(record.origin() == OriginKind::component, "origin") &&
         expect(record.route_id().value() == "route.alpha", "route identity") &&
         expect(record.provider_id().value() == "provider.alpha", "provider identity") &&
         expect(record.correlation_id().value() == "correlation.alpha", "correlation") &&
         expect(record.causation_id().value() == "causation.alpha", "causation") &&
         expect(record.source_timestamp().nanoseconds() == 42, "source timestamp") &&
         expect(record.observation_timestamp().nanoseconds() == 99, "observation timestamp") &&
         expect(record.sequence().has_value() && *record.sequence() == 99U, "sequence") &&
         expect(record.provider_outcome() == ObservationProviderOutcome::accepted, "provider outcome");
}

/** @brief Verify bounded complete/truncated payload views and explicit redaction without decoding. */
[[nodiscard]] bool test_controlled_payload_states() {
  const std::array<std::byte, 4U> bytes{std::byte{8}, std::byte{9}, std::byte{10}, std::byte{11}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub hub;
  const auto truncated = hub.attach(make_spec(ObservationPayloadMode::bounded_prefix, 2U, 1U,
                                              ObservationOverflowPolicy::drop_newest));
  const auto complete = hub.attach(make_spec(ObservationPayloadMode::bounded_prefix, bytes.size(), 1U,
                                             ObservationOverflowPolicy::drop_newest));
  const auto redacted = hub.attach(make_spec(ObservationPayloadMode::redacted, 0U, 1U,
                                             ObservationOverflowPolicy::drop_newest));
  if (!expect(emit(hub, item, 1U, ObservationProviderOutcome::rejected).succeeded(),
              "controlled payload publication")) {
    return false;
  }
  const auto truncated_record = hub.poll(*truncated.handle);
  const auto complete_record = hub.poll(*complete.handle);
  const auto redacted_record = hub.poll(*redacted.handle);
  return expect(truncated_record.record.has_value() &&
                    truncated_record.record->payload_bytes().size() == 2U &&
                    truncated_record.record->payload_bytes()[0] == std::byte{8} &&
                    truncated_record.record->payload_view_state() == PayloadViewState::truncated,
                "truncated bounded prefix") &&
         expect(complete_record.record.has_value() &&
                    complete_record.record->payload_bytes().size() == bytes.size() &&
                    complete_record.record->payload_view_state() == PayloadViewState::complete,
                "complete bounded payload") &&
         expect(redacted_record.record.has_value() && redacted_record.record->payload_bytes().empty() &&
                    redacted_record.record->payload_view_state() == PayloadViewState::redacted,
                "explicit redaction") &&
         expect(complete_record.record->payload_schema_state() == PayloadSchemaState::undecoded,
                "decoding success not invented") &&
         expect(complete_record.record->provider_outcome() == ObservationProviderOutcome::rejected,
                "rejected provider outcome retained");
}

/** @brief Verify fixed best-effort overflow and exact logical-key coalescing. */
[[nodiscard]] bool test_best_effort_overflow() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{0}, std::byte{0}, std::byte{0}};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  const CommunicationItem beta = make_item(bytes, "route.beta");
  const CommunicationItem gamma = make_item(bytes, "route.gamma");
  ObservationHub drop_hub;
  const auto drop = drop_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                              ObservationOverflowPolicy::drop_newest));
  const auto first = emit(drop_hub, alpha, 1U);
  const auto second = emit(drop_hub, alpha, 2U);
  const auto drop_snapshot = drop_hub.snapshot(*drop.handle);
  const auto retained = drop_hub.poll(*drop.handle);

  ObservationHub coalesce_hub;
  const auto coalesce = coalesce_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                                      ObservationOverflowPolicy::coalesce_latest));
  static_cast<void>(emit(coalesce_hub, alpha, 1U));
  static_cast<void>(emit(coalesce_hub, beta, 2U));
  static_cast<void>(emit(coalesce_hub, alpha, 3U));
  static_cast<void>(emit(coalesce_hub, gamma, 4U));
  const auto coalesce_snapshot = coalesce_hub.snapshot(*coalesce.handle);
  const auto replaced_alpha = coalesce_hub.poll(*coalesce.handle);
  const auto retained_beta = coalesce_hub.poll(*coalesce.handle);
  return expect(first.succeeded() && second.succeeded(), "drop operations stay best effort") &&
         expect(drop_snapshot.has_value() && drop_snapshot->accepted == 1U &&
                    drop_snapshot->dropped == 1U && drop_snapshot->queued == 1U,
                "drop counters") &&
         expect(retained.record.has_value() && *retained.record->sequence() == 1U,
                "drop preserves oldest record") &&
         expect(coalesce_snapshot.has_value() && coalesce_snapshot->accepted == 2U &&
                    coalesce_snapshot->coalesced == 1U && coalesce_snapshot->dropped == 1U &&
                    coalesce_snapshot->queued == 2U,
                "logical-key coalesce counters") &&
         expect(replaced_alpha.record.has_value() &&
                    replaced_alpha.record->route_id().value() == "route.alpha" &&
                    *replaced_alpha.record->sequence() == 3U,
                "matching logical slot replaced") &&
         expect(retained_beta.record.has_value() &&
                    retained_beta.record->route_id().value() == "route.beta" &&
                    *retained_beta.record->sequence() == 2U,
                "nonmatching logical slot retained");
}

/** @brief Verify reservations claim capacity, authenticate exactly, reset counters, and auto-cancel. */
[[nodiscard]] bool test_lossless_reservations() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub hub;
  ObservationHub foreign_hub;
  const auto attach = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                           ObservationOverflowPolicy::lossless_validation));
  auto first = hub.reserve(item);
  const auto busy = hub.detach(*attach.handle);
  const auto blocked = hub.reserve(item);
  const auto degraded = hub.snapshot(*attach.handle);
  const auto acknowledged = hub.acknowledge(*attach.handle);
  const auto restored = hub.snapshot(*attach.handle);
  const auto blocked_again = hub.reserve(item);
  const auto degraded_again = hub.snapshot(*attach.handle);
  const auto foreign_cancel = foreign_hub.cancel(std::move(*first.reservation));
  const auto cancelled = hub.cancel(std::move(*first.reservation));
  const auto duplicate_cancel = hub.cancel(std::move(*first.reservation));
  {
    auto abandoned = hub.reserve(item);
    if (!expect(abandoned.status.succeeded(), "scope reservation")) {
      return false;
    }
  }
  auto committed = hub.reserve(item);
  const auto commit_status = hub.commit(
      std::move(*committed.reservation),
      {item, Timestamp(7), "clock.observer", 7U, ObservationProviderOutcome::accepted});
  const auto duplicate_commit = hub.commit(
      std::move(*committed.reservation),
      {item, Timestamp(8), "clock.observer", 8U, ObservationProviderOutcome::accepted});
  const auto full = hub.reserve(item);
  return expect(first.status.succeeded() && first.reservation.has_value(), "first reservation") &&
         expect(busy.outcome == ObservationOutcome::tap_busy, "detach while claimed") &&
         expect(blocked.status.outcome == ObservationOutcome::observation_backpressure,
                "reserved capacity blocks competitor") &&
         expect(degraded.has_value() && degraded->experiment_validity_degraded &&
                    degraded->backpressure_rejections == 1U,
                "degraded reservation counter") &&
         expect(acknowledged.succeeded() && restored.has_value() &&
                    !restored->experiment_validity_degraded &&
                    restored->backpressure_rejections == 0U,
                "acknowledgement resets interval state") &&
         expect(blocked_again.status.outcome == ObservationOutcome::observation_backpressure &&
                    degraded_again->backpressure_rejections == 1U,
                "post-acknowledgement interval counter") &&
         expect(foreign_cancel.outcome == ObservationOutcome::invalid_reservation,
                "foreign reservation authority") &&
         expect(cancelled.succeeded() && duplicate_cancel.outcome == ObservationOutcome::invalid_reservation,
                "single-use cancellation") &&
         expect(commit_status.succeeded() &&
                    duplicate_commit.outcome == ObservationOutcome::invalid_reservation,
                "single-use commit") &&
         expect(full.status.outcome == ObservationOutcome::observation_backpressure,
                "queued lossless capacity blocks before provider");
}

/** @brief Force two publishers to contend for one empty lossless slot before either can commit. */
[[nodiscard]] bool test_competing_reservation_interleaving() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem item = make_item(bytes);
  ObservationHub hub;
  static_cast<void>(hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                         ObservationOverflowPolicy::lossless_validation)));
  std::atomic<bool> reserved{false};
  std::atomic<bool> release{false};
  std::atomic<bool> holder_valid{true};
  std::thread holder([&]() {
    auto claim = hub.reserve(item);
    holder_valid = claim.status.succeeded() && claim.reservation.has_value();
    reserved = true;
    while (!release.load()) {
      std::this_thread::yield();
    }
    if (holder_valid.load()) {
      holder_valid = hub.cancel(std::move(*claim.reservation)).succeeded();
    }
  });
  while (!reserved.load()) {
    std::this_thread::yield();
  }
  const auto competitor = hub.reserve(item);
  release = true;
  holder.join();
  const auto recovered = hub.reserve(item);
  const bool result = expect(holder_valid.load(), "holder reservation lifecycle") &&
                      expect(competitor.status.outcome == ObservationOutcome::observation_backpressure,
                             "forced competing publisher rejected") &&
                      expect(recovered.status.succeeded(), "capacity recovered after cancellation");
  return result;
}

/** @brief Verify tap capacity, foreign authority, duplicate close, and recreated generations. */
[[nodiscard]] bool test_exact_tap_handles() {
  ObservationHub hub;
  ObservationHub foreign_hub;
  const ObservationTapSpec spec = make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                            ObservationOverflowPolicy::drop_newest);
  const auto first = hub.attach(spec);
  bool valid = expect(first.status.succeeded(), "first tap");
  for (std::size_t index = 1U; index < kMaximumObservationTaps; ++index) {
    valid = expect(hub.attach(spec).status.succeeded(), "fixed tap slot") && valid;
  }
  valid = expect(hub.attach(spec).status.outcome == ObservationOutcome::tap_capacity_exhausted,
                 "tap registry exhaustion") &&
          valid;
  const auto foreign = foreign_hub.attach(spec);
  valid = expect(!hub.snapshot(*foreign.handle).has_value(), "foreign snapshot") && valid;
  valid = expect(hub.acknowledge(*foreign.handle).outcome == ObservationOutcome::invalid_tap_handle,
                 "foreign acknowledgement") &&
          valid;
  valid = expect(hub.detach(*foreign.handle).outcome == ObservationOutcome::invalid_tap_handle,
                 "foreign detach") &&
          valid;
  valid = expect(hub.poll(*foreign.handle).status.outcome == ObservationOutcome::invalid_tap_handle,
                 "foreign poll") &&
          valid;
  valid = expect(hub.detach(*first.handle).succeeded(), "exact detach") && valid;
  valid = expect(hub.detach(*first.handle).outcome == ObservationOutcome::tap_closed,
                 "duplicate detach") &&
          valid;
  const auto recreated = hub.attach(spec);
  return expect(recreated.status.succeeded() &&
                    recreated.handle->tap_id() == first.handle->tap_id() &&
                    recreated.handle->generation() != first.handle->generation(),
                "slot generation recreation") &&
         expect(!hub.snapshot(*first.handle).has_value(), "stale snapshot") &&
         expect(hub.acknowledge(*first.handle).outcome == ObservationOutcome::invalid_tap_handle,
                "stale acknowledgement") &&
         expect(hub.detach(*first.handle).outcome == ObservationOutcome::invalid_tap_handle,
                "stale detach") &&
         valid;
}

/** @brief Verify pull consumers isolate disconnects and tolerate concurrent publication/pulling. */
[[nodiscard]] bool test_synthetic_sink_concurrency() {
  const std::array<std::byte, 4U> bytes{std::byte{4}, std::byte{3}, std::byte{2}, std::byte{1}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub hub;
  const auto attach = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 16U,
                                           ObservationOverflowPolicy::drop_newest));
  SyntheticObservationSink sink(hub, *attach.handle);
  std::atomic<bool> valid{true};
  std::thread writer([&]() {
    for (std::uint64_t index = 0U; index < 64U; ++index) {
      if (!emit(hub, item, index).succeeded()) {
        valid = false;
      }
    }
  });
  std::thread reader([&]() {
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
  return expect(valid.load(), "serialized concurrent pull/publication") &&
         expect(sink.pull().status.outcome == ObservationOutcome::sink_disconnected,
                "local disconnect isolation") &&
         expect(sink.connect().succeeded(), "sink reconnect") &&
         expect(sink.pull().status.outcome != ObservationOutcome::sink_disconnected,
                "reconnected pull path");
}

}  // namespace

/** @brief Run all focused observation fixtures. @return Zero only when every check passes. */
int main() {
  return test_values_filters_and_versions() && test_metadata_only() &&
                 test_controlled_payload_states() && test_best_effort_overflow() &&
                 test_lossless_reservations() && test_competing_reservation_interleaving() &&
                 test_exact_tap_handles() && test_synthetic_sink_concurrency()
             ? 0
             : 1;
}
