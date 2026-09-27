/**
 * @file integration_tests.cpp
 * @brief ProviderComposition, loopback, and ObservationHub integration fixtures.
 * @ownership Fixtures own every normal-route resource, hub, tap, sink, item, record, and snapshot.
 * @lifetime No returned view outlives its owning fixture value.
 * @thread_safety Concurrency fixtures submit through independent compositions sharing one hub;
 * exact reservations serialize only hub claims and no test callback executes under an X-COM lock.
 * @failure Failed expectations are printed and produce a nonzero process result.
 * @par Traceability
 * Verifies XCOM-OBS-001 through XCOM-OBS-008 at the provider integration boundary. Core-only policy,
 * handle, and record behavior remains covered by tests/xcom/observation/core/unit_tests.cpp.
 */

#include "test_support.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>
#include <thread>
#include <utility>

namespace {

using namespace xverse::xcom;
using xverse::xcom::observation_test::Scenario;
using xverse::xcom::observation_test::make_tap_spec;

/** @param condition Expected condition. @param message Failure detail. @return condition. */
[[nodiscard]] bool expect(const bool condition, const std::string_view message) {
  if (!condition) {
    std::cerr << "observation integration failure: " << message << '\n';
  }
  return condition;
}

/** Verify policy-bounded records and normalized accepted/rejected provider outcomes. */
[[nodiscard]] bool test_payload_policies_and_provider_outcomes() {
  ObservationHub hub;
  const ObservationFilterInput filter{};
  const auto metadata = hub.attach(make_tap_spec(
      filter, ObservationPayloadMode::metadata_only, 0U, 4U,
      ObservationOverflowPolicy::drop_newest));
  const auto prefix = hub.attach(make_tap_spec(
      filter, ObservationPayloadMode::bounded_prefix, 2U, 4U,
      ObservationOverflowPolicy::drop_newest));
  const auto complete = hub.attach(make_tap_spec(
      filter, ObservationPayloadMode::bounded_prefix, 4U, 4U,
      ObservationOverflowPolicy::drop_newest));
  const auto redacted = hub.attach(make_tap_spec(
      filter, ObservationPayloadMode::redacted, 0U, 4U,
      ObservationOverflowPolicy::drop_newest));
  Scenario scenario("payload", InteractionKind::message_event, 1U, &hub);
  const auto first = scenario.item(1U);
  const auto second = scenario.item(2U);
  if (!expect(metadata.handle.has_value() && prefix.handle.has_value() &&
                  complete.handle.has_value() && redacted.handle.has_value() && scenario.ready() &&
                  first.has_value() && second.has_value(),
              "payload fixture setup")) {
    return false;
  }
  const ProviderStatus accepted = scenario.composition().submit(
      scenario.provider_handle(), *first.value(), scenario.lifecycle());
  const ProviderStatus rejected = scenario.composition().submit(
      scenario.provider_handle(), *second.value(), scenario.lifecycle());
  const auto metadata_first = hub.poll(*metadata.handle);
  const auto metadata_second = hub.poll(*metadata.handle);
  const auto prefix_first = hub.poll(*prefix.handle);
  const auto complete_first = hub.poll(*complete.handle);
  const auto redacted_first = hub.poll(*redacted.handle);
  if (!expect(accepted.outcome() == ProviderOutcome::accepted &&
                  rejected.outcome() == ProviderOutcome::queue_saturated,
              "provider outcomes") ||
      !expect(metadata_first.record.has_value() && metadata_second.record.has_value() &&
                  prefix_first.record.has_value() && complete_first.record.has_value() &&
                  redacted_first.record.has_value(),
              "normalized records")) {
    return false;
  }
  const ObservationRecord& record = *metadata_first.record;
  return expect(record.payload_bytes().empty() &&
                    record.payload_view_state() == PayloadViewState::omitted,
                "metadata-only payload exposure") &&
         expect(record.contract_id() == first.value()->contract_id() &&
                    record.interface_id() == first.value()->interface_id() &&
                    record.endpoint_id() == first.value()->endpoint_id() &&
                    record.interaction_kind() == first.value()->interaction_kind() &&
                    record.origin() == first.value()->origin() &&
                    record.correlation_id() == first.value()->correlation_id() &&
                    record.causation_id() == first.value()->causation_id() &&
                    record.route_id() == first.value()->route_id() &&
                    record.provider_id() == first.value()->provider_id() &&
                    record.source_payload_size() == first.value()->payload().size(),
                "metadata preservation") &&
         expect(record.source_timestamp().nanoseconds() == 1 &&
                    record.observation_timestamp().nanoseconds() == 1 &&
                    record.source_clock_domain().value() == "clock.fixture" &&
                    record.observation_clock_domain().value() == "clock.fixture",
                "declared source-clock observation point") &&
         expect(record.provider_outcome() == ObservationProviderOutcome::accepted &&
                    metadata_second.record->provider_outcome() ==
                        ObservationProviderOutcome::rejected,
                "normalized post-provider outcomes") &&
         expect(prefix_first.record->payload_bytes().size() == 2U &&
                    prefix_first.record->payload_view_state() == PayloadViewState::truncated &&
                    prefix_first.record->payload_schema_state() ==
                        PayloadSchemaState::undecoded,
                "bounded undecoded prefix") &&
         expect(complete_first.record->payload_bytes().size() ==
                        first.value()->payload().size() &&
                    complete_first.record->payload_view_state() == PayloadViewState::complete &&
                    complete_first.record->payload_schema_state() ==
                        PayloadSchemaState::undecoded,
                "complete bounded undecoded payload") &&
         expect(redacted_first.record->payload_bytes().empty() &&
                    redacted_first.record->payload_view_state() == PayloadViewState::redacted,
                "explicit redaction");
}

/** Verify exact route/provider/interaction/origin filters and observation-contract rejection. */
[[nodiscard]] bool test_versioned_exact_filters() {
  ObservationHub hub;
  ObservationFilterInput matching_filter{};
  matching_filter.route_id = "route.filtered";
  matching_filter.provider_id = "provider.filtered";
  matching_filter.interaction_kind = InteractionKind::message_event;
  matching_filter.origin = OriginKind::component;
  ObservationFilterInput wrong_origin_filter = matching_filter;
  wrong_origin_filter.origin = OriginKind::replay;
  const auto matching = hub.attach(make_tap_spec(
      matching_filter, ObservationPayloadMode::metadata_only, 0U, 1U,
      ObservationOverflowPolicy::drop_newest));
  const auto wrong_origin = hub.attach(make_tap_spec(
      wrong_origin_filter, ObservationPayloadMode::metadata_only, 0U, 1U,
      ObservationOverflowPolicy::drop_newest));
  const auto unsupported = ObservationTapSpec::create(
      {"2.0.0", "tap.integration", {}, ObservationPayloadMode::metadata_only, 0U, 1U,
       ObservationOverflowPolicy::drop_newest});
  Scenario scenario("filtered", InteractionKind::message_event, 1U, &hub);
  const auto item = scenario.item(1U);
  if (!expect(matching.handle.has_value() && wrong_origin.handle.has_value() && scenario.ready() &&
                  item.has_value() && !unsupported.has_value(),
              "versioned filter fixture setup")) {
    return false;
  }
  const ProviderStatus submitted = scenario.composition().submit(
      scenario.provider_handle(), *item.value(), scenario.lifecycle());
  const auto matching_record = hub.poll(*matching.handle);
  const auto wrong_origin_record = hub.poll(*wrong_origin.handle);
  return expect(submitted.outcome() == ProviderOutcome::accepted,
                "filtered provider submission") &&
         expect(matching_record.record.has_value() &&
                    matching_record.record->origin() == OriginKind::component &&
                    matching_record.record->route_id().value() == "route.filtered" &&
                    matching_record.record->provider_id().value() == "provider.filtered",
                "exact provider-neutral filter match") &&
         expect(wrong_origin_record.status.outcome == ObservationOutcome::no_record,
                "origin mismatch excluded");
}

/** Verify one provider-neutral hub filters all interaction families and distinct logical providers. */
[[nodiscard]] bool test_domain_neutral_routes_providers_and_families() {
  ObservationHub hub;
  const auto attached = hub.attach(make_tap_spec(
      {}, ObservationPayloadMode::metadata_only, 0U, 8U,
      ObservationOverflowPolicy::drop_newest));
  constexpr std::array kinds{
      InteractionKind::signal_state_update, InteractionKind::message_event,
      InteractionKind::service_request, InteractionKind::service_response};
  if (!expect(attached.handle.has_value(), "domain-neutral tap attachment")) {
    return false;
  }
  for (std::size_t index = 0U; index < kinds.size(); ++index) {
    const std::string suffix = "family." + std::to_string(index);
    const auto scenario = std::make_unique<Scenario>(suffix, kinds[index], 1U, &hub);
    const auto item = scenario->item(static_cast<unsigned int>(index + 1U));
    if (!expect(scenario->ready() && item.has_value(), "family fixture setup") ||
        !expect(scenario->composition()
                    .submit(scenario->provider_handle(), *item.value(), scenario->lifecycle())
                    .outcome() == ProviderOutcome::accepted,
                "family provider submission")) {
      return false;
    }
    const auto pulled = hub.poll(*attached.handle);
    if (!expect(pulled.record.has_value() &&
                    pulled.record->interaction_kind() == kinds[index] &&
                    pulled.record->route_id().value() == scenario->route_id() &&
                    pulled.record->provider_id().value() == scenario->provider_id(),
                "provider-neutral family record")) {
      return false;
    }
  }
  return true;
}

/** Verify bounded best-effort loss and sink failure cannot alter delivery count, order, or outcome. */
[[nodiscard]] bool test_best_effort_isolation() {
  ObservationHub hub;
  const auto dropped = hub.attach(make_tap_spec(
      {}, ObservationPayloadMode::metadata_only, 0U, 1U,
      ObservationOverflowPolicy::drop_newest));
  const auto coalesced = hub.attach(make_tap_spec(
      {}, ObservationPayloadMode::metadata_only, 0U, 1U,
      ObservationOverflowPolicy::coalesce_latest));
  Scenario scenario("isolation", InteractionKind::signal_state_update, 8U, &hub);
  if (!expect(dropped.handle.has_value() && coalesced.handle.has_value() && scenario.ready(),
              "isolation fixture setup")) {
    return false;
  }
  SyntheticObservationSink sink(hub, *dropped.handle);
  sink.disconnect();
  for (unsigned int sequence = 1U; sequence <= 4U; ++sequence) {
    const auto item = scenario.item(sequence);
    if (!expect(item.has_value() &&
                    scenario.composition()
                            .submit(scenario.provider_handle(), *item.value(),
                                    scenario.lifecycle())
                            .outcome() == ProviderOutcome::accepted,
                "isolated provider delivery")) {
      return false;
    }
  }
  const auto route = scenario.composition().route_state(scenario.provider_handle());
  const auto drop_snapshot = hub.snapshot(*dropped.handle);
  const auto coalesce_snapshot = hub.snapshot(*coalesced.handle);
  if (!expect(route.has_value() && route.value()->queued_items() == 4U,
              "observer changed provider count") ||
      !expect(drop_snapshot.has_value() && drop_snapshot->accepted == 1U &&
                  drop_snapshot->dropped == 3U && drop_snapshot->queued == 1U,
              "drop-newest counters") ||
      !expect(coalesce_snapshot.has_value() && coalesce_snapshot->accepted == 1U &&
                  coalesce_snapshot->coalesced == 3U && coalesce_snapshot->queued == 1U,
              "coalesce-latest counters") ||
      !expect(sink.pull().status.outcome == ObservationOutcome::sink_disconnected,
              "disconnected sink status")) {
    return false;
  }
  for (unsigned int sequence = 1U; sequence <= 4U; ++sequence) {
    const auto received =
        scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
    if (!expect(received.has_value() &&
                    received.value()->timestamp().nanoseconds() ==
                        static_cast<std::int64_t>(sequence),
                "provider FIFO changed by observer")) {
      return false;
    }
  }
  static_cast<void>(hub.detach(*dropped.handle));
  static_cast<void>(hub.detach(*coalesced.handle));
  const auto fifth = scenario.item(5U);
  return expect(fifth.has_value() &&
                    scenario.composition()
                            .submit(scenario.provider_handle(), *fifth.value(),
                                    scenario.lifecycle())
                            .outcome() == ProviderOutcome::accepted,
                "detached observers changed provider outcome") &&
         expect(sink.connect().outcome == ObservationOutcome::invalid_tap_handle,
                "failed stale sink remained authoritative");
}

/** Verify lossless capacity rejects exactly before provider queue mutation and recovers explicitly. */
[[nodiscard]] bool test_lossless_pre_dispatch_reservation() {
  ObservationHub hub;
  const auto attached = hub.attach(make_tap_spec(
      {}, ObservationPayloadMode::metadata_only, 0U, 1U,
      ObservationOverflowPolicy::lossless_validation));
  Scenario scenario("lossless", InteractionKind::service_request, 2U, &hub);
  const auto first = scenario.item(1U);
  const auto second = scenario.item(2U);
  if (!expect(attached.handle.has_value() && scenario.ready() && first.has_value() &&
                  second.has_value(),
              "lossless fixture setup")) {
    return false;
  }
  const auto accepted = scenario.composition().submit(
      scenario.provider_handle(), *first.value(), scenario.lifecycle());
  const auto blocked = scenario.composition().submit(
      scenario.provider_handle(), *second.value(), scenario.lifecycle());
  const auto route_before_recovery =
      scenario.composition().route_state(scenario.provider_handle());
  const auto degraded = hub.snapshot(*attached.handle);
  if (!expect(accepted.outcome() == ProviderOutcome::accepted &&
                  blocked.outcome() == ProviderOutcome::observation_backpressure &&
                  blocked.diagnostic_code() == "XCOM-PROV-E029",
              "stable lossless backpressure outcome") ||
      !expect(route_before_recovery.has_value() &&
                  route_before_recovery.value()->queued_items() == 1U,
              "provider mutated after lossless rejection") ||
      !expect(degraded.has_value() && degraded->experiment_validity_degraded &&
                  degraded->backpressure_rejections == 1U,
              "degraded validity evidence")) {
    return false;
  }
  const auto record = hub.poll(*attached.handle);
  const auto acknowledged = hub.acknowledge(*attached.handle);
  const auto recovered = scenario.composition().submit(
      scenario.provider_handle(), *second.value(), scenario.lifecycle());
  const auto route_after_recovery =
      scenario.composition().route_state(scenario.provider_handle());
  const auto restored = hub.snapshot(*attached.handle);
  return expect(record.record.has_value() && acknowledged.succeeded(),
                "lossless acknowledgement setup") &&
         expect(recovered.outcome() == ProviderOutcome::accepted &&
                    route_after_recovery.has_value() &&
                    route_after_recovery.value()->queued_items() == 2U,
                "lossless recovery") &&
         expect(restored.has_value() && !restored->experiment_validity_degraded &&
                    restored->backpressure_rejections == 0U,
                "validity acknowledgement interval reset");
}

/** Verify a direct shared-hub claim rejects a competing composition before provider mutation. */
[[nodiscard]] bool test_shared_hub_competing_reservation() {
  ObservationHub hub;
  const auto attached = hub.attach(make_tap_spec(
      {}, ObservationPayloadMode::metadata_only, 0U, 1U,
      ObservationOverflowPolicy::lossless_validation));
  Scenario holder("claim.a", InteractionKind::message_event, 1U, &hub);
  Scenario competitor("claim.b", InteractionKind::message_event, 1U, &hub);
  const auto held_item = holder.item(1U);
  const auto competing_item = competitor.item(2U);
  if (!expect(attached.handle.has_value() && holder.ready() && competitor.ready() &&
                  held_item.has_value() && competing_item.has_value(),
              "shared-hub reservation fixture setup")) {
    return false;
  }

  ObservationReserveResult held = hub.reserve(*held_item.value());
  if (!expect(held.status.succeeded() && held.reservation.has_value(),
              "first publisher exact claim")) {
    return false;
  }
  const ProviderStatus blocked = competitor.composition().submit(
      competitor.provider_handle(), *competing_item.value(), competitor.lifecycle());
  const auto holder_route = holder.composition().route_state(holder.provider_handle());
  const auto competitor_before =
      competitor.composition().route_state(competitor.provider_handle());
  const auto degraded = hub.snapshot(*attached.handle);
  const ObservationStatus cancelled = hub.cancel(std::move(*held.reservation));
  const ProviderStatus recovered = competitor.composition().submit(
      competitor.provider_handle(), *competing_item.value(), competitor.lifecycle());
  const auto competitor_after = competitor.composition().route_state(competitor.provider_handle());
  const auto retained = hub.poll(*attached.handle);

  return expect(blocked.outcome() == ProviderOutcome::observation_backpressure &&
                    blocked.diagnostic_code() == "XCOM-PROV-E029",
                "competing publisher rejected before dispatch") &&
         expect(holder_route.has_value() && holder_route.value()->queued_items() == 0U &&
                    competitor_before.has_value() &&
                    competitor_before.value()->queued_items() == 0U,
                "no provider mutation while exact claim is held") &&
         expect(degraded.has_value() && degraded->experiment_validity_degraded &&
                    degraded->backpressure_rejections == 1U,
                "competing claim loss remains visible") &&
         expect(cancelled.succeeded() && recovered.outcome() == ProviderOutcome::accepted &&
                    competitor_after.has_value() &&
                    competitor_after.value()->queued_items() == 1U,
                "capacity recovery after exact cancellation") &&
         expect(retained.record.has_value() &&
                    retained.record->route_id().value() == competitor.route_id(),
                "recovered publication consumed its own claim");
}

/** Verify concurrent submissions produce bounded owned records without callback or provider loss. */
[[nodiscard]] bool test_concurrent_publication() {
  ObservationHub hub;
  const auto attached = hub.attach(make_tap_spec(
      {}, ObservationPayloadMode::metadata_only, 0U, 8U,
      ObservationOverflowPolicy::lossless_validation));
  Scenario scenario("concurrent", InteractionKind::message_event, 8U, &hub);
  std::array<Result<CommunicationItem>, 4U> items{
      scenario.item(1U), scenario.item(2U), scenario.item(3U), scenario.item(4U)};
  if (!expect(attached.handle.has_value() && scenario.ready(), "concurrency fixture setup")) {
    return false;
  }
  std::atomic<bool> accepted{true};
  std::array<std::thread, 4U> workers;
  for (std::size_t index = 0U; index < workers.size(); ++index) {
    workers[index] = std::thread([&scenario, &items, &accepted, index]() {
      if (!items[index].has_value() ||
          scenario.composition()
                  .submit(scenario.provider_handle(), *items[index].value(), scenario.lifecycle())
                  .outcome() != ProviderOutcome::accepted) {
        accepted = false;
      }
    });
  }
  for (std::thread& worker : workers) {
    worker.join();
  }
  const auto route = scenario.composition().route_state(scenario.provider_handle());
  const auto snapshot = hub.snapshot(*attached.handle);
  if (!expect(accepted.load() && route.has_value() && route.value()->queued_items() == 4U,
              "concurrent provider delivery") ||
      !expect(snapshot.has_value() && snapshot->accepted == 4U && snapshot->queued == 4U &&
                  snapshot->backpressure_rejections == 0U,
              "concurrent observation publication")) {
    return false;
  }
  for (std::size_t index = 0U; index < 4U; ++index) {
    if (!expect(hub.poll(*attached.handle).record.has_value(), "owned concurrent record")) {
      return false;
    }
  }
  return true;
}

}  // namespace

/** @return Zero only when every integration fixture passes. */
int main() {
  const bool passed = test_payload_policies_and_provider_outcomes() &&
                      test_versioned_exact_filters() &&
                      test_domain_neutral_routes_providers_and_families() &&
                      test_best_effort_isolation() &&
                      test_lossless_pre_dispatch_reservation() &&
                      test_shared_hub_competing_reservation() &&
                      test_concurrent_publication();
  return passed ? 0 : 1;
}
