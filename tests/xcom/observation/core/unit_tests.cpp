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
 * observation.cpp. XCOM-OBS-009 remains a source/interface inspection obligation. T021 adds the
 * declared observation-point, declared filter-constraint, validity-effect, self-describing record,
 * counter-projection, snapshot-declaration, and repeated-declaration cases of
 * docs/engineering/xcom/t021/verification-plan.md (XCOM-SW-OBS-001, FR-011). T022 adds the bounded
 * drop, coalesce, lossless pre-dispatch, applied validity-effect, realized-status, and
 * acknowledgement-interval cases of docs/engineering/xcom/t022/verification-plan.md
 * (XCOM-SW-OBS-003, FR-013, SC-004).
 */

#include "xverse/xcom/observation.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <iostream>
#include <span>
#include <string>
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

/** @return A valid value-owned item with caller-selected logical fields and payload size. */
[[nodiscard]] CommunicationItem make_item(
    const std::array<std::byte, 4U>& payload, const std::string_view route_id = "route.alpha",
    const std::string_view provider_id = "provider.alpha",
    const OriginKind origin = OriginKind::component,
    const InteractionKind kind = InteractionKind::message_event,
    const std::size_t payload_size = 4U) {
  const CommunicationContract contract = make_contract(kind);
  const auto result = CommunicationItem::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "endpoint.alpha", "schema.alpha", "2.0.1",
       kind, origin, Timestamp(42), "clock.source", "correlation.alpha", "causation.alpha", route_id,
       provider_id, std::span<const std::byte>(payload.data(), payload_size)},
      contract);
  return *result.value();
}

/** @return One valid policy with a caller-selected filter, payload, and declared observation point. */
[[nodiscard]] ObservationTapSpec make_spec(
    const ObservationPayloadMode payload_mode, const std::size_t maximum_payload_bytes,
    const std::size_t record_capacity, const ObservationOverflowPolicy overflow_policy,
    const ObservationFilterInput& filter = {}, const std::string_view tap_id = "tap.unit",
    const ObservationValidityEffect validity_effect = ObservationValidityEffect::none) {
  const auto result = ObservationTapSpec::create(
      {kObservationContractVersion, tap_id, filter, payload_mode, maximum_payload_bytes,
       record_capacity, overflow_policy, validity_effect});
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
      {"2.0.0", "tap.unit", {}, ObservationPayloadMode::metadata_only, 0U, 1U,
       ObservationOverflowPolicy::drop_newest});
  const auto zero_capacity = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.unit", {}, ObservationPayloadMode::metadata_only, 0U, 0U,
       ObservationOverflowPolicy::drop_newest});
  const auto oversized_prefix = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.unit", {}, ObservationPayloadMode::bounded_prefix,
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

/** @brief Verify declared-constraint accessors round-trip while the matching matrix is unchanged. */
[[nodiscard]] bool test_filter_declared_constraints() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem item = make_item(bytes);
  const auto declared = ObservationFilter::create(
      {"contract.alpha", "interface.alpha", "endpoint.alpha", "route.alpha", "provider.alpha",
       InteractionKind::message_event, OriginKind::component});
  const auto route_only =
      ObservationFilter::create({{}, {}, {}, "route.alpha", {}, std::nullopt});
  if (!expect(declared.has_value() && route_only.has_value(), "declared filter creation")) {
    return false;
  }
  const ObservationFilter& filter = *declared;
  bool valid =
      expect(filter.contract_id().has_value() && filter.contract_id()->value() == "contract.alpha",
             "declared contract accessor") &&
      expect(filter.interface_id().has_value() &&
                 filter.interface_id()->value() == "interface.alpha",
             "declared interface accessor") &&
      expect(filter.endpoint_id().has_value() && filter.endpoint_id()->value() == "endpoint.alpha",
             "declared endpoint accessor") &&
      expect(filter.route_id().has_value() && filter.route_id()->value() == "route.alpha",
             "declared route accessor") &&
      expect(filter.provider_id().has_value() &&
                 filter.provider_id()->value() == "provider.alpha",
             "declared provider accessor") &&
      expect(filter.interaction_kind().has_value() &&
                 *filter.interaction_kind() == InteractionKind::message_event,
             "declared interaction accessor") &&
      expect(filter.origin().has_value() && *filter.origin() == OriginKind::component,
             "declared origin accessor") &&
      expect(filter.matches(item), "declared filter match matrix unchanged");
  const ObservationFilter& partial = *route_only;
  valid = expect(partial.route_id().has_value() && partial.route_id()->value() == "route.alpha",
                 "route-only declared point") &&
          expect(!partial.contract_id().has_value() && !partial.interface_id().has_value() &&
                     !partial.endpoint_id().has_value() && !partial.provider_id().has_value() &&
                     !partial.interaction_kind().has_value() && !partial.origin().has_value(),
                 "unconstrained fields report no value") &&
          expect(partial.matches(item), "route-only match matrix unchanged") && valid;
  return valid;
}

/** @brief Verify a declared tap policy exposes its exact declared observation point and vocabulary. */
[[nodiscard]] bool test_declared_tap_binding() {
  ObservationFilterInput filter{};
  filter.route_id = "route.alpha";
  filter.provider_id = "provider.alpha";
  const auto spec = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.declared", filter, ObservationPayloadMode::bounded_prefix,
       64U, 4U, ObservationOverflowPolicy::coalesce_latest,
       ObservationValidityEffect::degrade_on_loss});
  if (!expect(spec.has_value(), "declared tap policy creation")) {
    return false;
  }
  return expect(spec->declared_tap_id().value() == "tap.declared", "declared tap identity") &&
         expect(spec->declared_route_point().has_value() &&
                    spec->declared_route_point()->value() == "route.alpha",
                "declared route point reported") &&
         expect(spec->declared_route_point() == spec->filter().route_id(),
                "declared route point single source of truth") &&
         expect(spec->validity_effect() == ObservationValidityEffect::degrade_on_loss,
                "declared validity effect round-trip") &&
         expect(spec->contract_version().value() == kObservationContractVersion,
                "declared contract version round-trip") &&
         expect(spec->payload_mode() == ObservationPayloadMode::bounded_prefix,
                "declared payload mode round-trip") &&
         expect(spec->maximum_payload_bytes() == 64U, "declared payload bound round-trip") &&
         expect(spec->record_capacity() == 4U, "declared capacity round-trip") &&
         expect(spec->overflow_policy() == ObservationOverflowPolicy::coalesce_latest,
                "declared overflow round-trip");
}

/** @brief Verify every malformed declaration fails closed with no partial policy value. */
[[nodiscard]] bool test_declared_tap_rejections() {
  const std::string too_long(129U, 'a');
  std::string control_byte = "tap";
  control_byte.push_back(static_cast<char>(0x1FU));
  const std::string leading_space = " tap";
  const std::string trailing_space = "tap ";
  ObservationFilterInput malformed_filter{};
  malformed_filter.interface_id = too_long;
  const auto rejects = [](const ObservationTapSpecInput& input) {
    return !ObservationTapSpec::create(input).has_value();
  };
  return expect(rejects({kObservationContractVersion, "", {}, ObservationPayloadMode::metadata_only,
                         0U, 1U, ObservationOverflowPolicy::drop_newest}),
                "empty declared identity") &&
         expect(rejects({kObservationContractVersion, too_long, {},
                         ObservationPayloadMode::metadata_only, 0U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "over-bound declared identity") &&
         expect(rejects({kObservationContractVersion, control_byte, {},
                         ObservationPayloadMode::metadata_only, 0U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "control-byte declared identity") &&
         expect(rejects({kObservationContractVersion, leading_space, {},
                         ObservationPayloadMode::metadata_only, 0U, 1U,
                         ObservationOverflowPolicy::drop_newest}) &&
                    rejects({kObservationContractVersion, trailing_space, {},
                             ObservationPayloadMode::metadata_only, 0U, 1U,
                             ObservationOverflowPolicy::drop_newest}),
                "whitespace-padded declared identity") &&
         expect(rejects({"2.0.0", "tap.unit", {}, ObservationPayloadMode::metadata_only, 0U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "wrong observation version") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         static_cast<ObservationPayloadMode>(0x7FU), 0U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "unknown payload mode") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         ObservationPayloadMode::metadata_only, 0U, 1U,
                         static_cast<ObservationOverflowPolicy>(0x7FU)}),
                "unknown overflow policy") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         ObservationPayloadMode::metadata_only, 0U, 1U,
                         ObservationOverflowPolicy::drop_newest,
                         static_cast<ObservationValidityEffect>(0x7FU)}),
                "unknown validity effect") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         ObservationPayloadMode::metadata_only, 0U, 0U,
                         ObservationOverflowPolicy::drop_newest}),
                "zero record capacity") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         ObservationPayloadMode::metadata_only, 0U,
                         kMaximumObservationRecordsPerTap + 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "over-bound record capacity") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         ObservationPayloadMode::bounded_prefix, 0U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "zero prefix bound") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         ObservationPayloadMode::bounded_prefix,
                         kMaximumObservedPayloadBytes + 1U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "over-bound prefix") &&
         expect(rejects({kObservationContractVersion, "tap.unit", {},
                         ObservationPayloadMode::metadata_only, 1U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "non-zero bound on metadata mode") &&
         expect(rejects({kObservationContractVersion, "tap.unit", malformed_filter,
                         ObservationPayloadMode::metadata_only, 0U, 1U,
                         ObservationOverflowPolicy::drop_newest}),
                "malformed filter identity");
}

/** @brief Verify the declared validity-effect vocabulary and its stable external text. */
[[nodiscard]] bool test_validity_effect_vocabulary() {
  bool valid = expect(to_string(ObservationValidityEffect::none) == "none",
                      "none external text") &&
               expect(to_string(ObservationValidityEffect::degrade_on_loss) == "degrade-on-loss",
                      "degrade external text") &&
               expect(to_string(ObservationValidityEffect::invalidate_on_loss) ==
                          "invalidate-on-loss",
                      "invalidate external text");
  for (const ObservationValidityEffect effect :
       {ObservationValidityEffect::none, ObservationValidityEffect::degrade_on_loss,
        ObservationValidityEffect::invalidate_on_loss}) {
    const auto spec = ObservationTapSpec::create(
        {kObservationContractVersion, "tap.unit", {}, ObservationPayloadMode::metadata_only, 0U, 2U,
         ObservationOverflowPolicy::drop_newest, effect});
    valid = expect(spec.has_value() && spec->validity_effect() == effect,
                   "declared validity effect accepted") &&
            valid;
  }
  return expect(!ObservationTapSpec::create(
                    {kObservationContractVersion, "tap.unit", {},
                     ObservationPayloadMode::metadata_only, 0U, 2U,
                     ObservationOverflowPolicy::drop_newest,
                     static_cast<ObservationValidityEffect>(0x9FU)})
                    .has_value(),
                "unknown validity effect rejected") &&
         valid;
}

/** @brief Verify declared payload bounds echo exactly and drive complete/truncated views. */
[[nodiscard]] bool test_payload_policy_bounds() {
  const std::array<std::byte, 4U> bytes{std::byte{5}, std::byte{6}, std::byte{7}, std::byte{8}};
  const auto smallest = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.min", {}, ObservationPayloadMode::bounded_prefix, 1U, 1U,
       ObservationOverflowPolicy::drop_newest});
  const auto largest = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.max", {}, ObservationPayloadMode::bounded_prefix,
       kMaximumObservedPayloadBytes, kMaximumObservationRecordsPerTap,
       ObservationOverflowPolicy::drop_newest});
  if (!expect(smallest.has_value() && smallest->maximum_payload_bytes() == 1U &&
                  smallest->record_capacity() == 1U,
              "smallest prefix policy") ||
      !expect(largest.has_value() &&
                  largest->maximum_payload_bytes() == kMaximumObservedPayloadBytes &&
                  largest->record_capacity() == kMaximumObservationRecordsPerTap,
              "largest prefix policy")) {
    return false;
  }
  ObservationHub hub;
  const auto tap = hub.attach(make_spec(ObservationPayloadMode::bounded_prefix, 2U, 4U,
                                        ObservationOverflowPolicy::drop_newest));
  if (!expect(tap.handle.has_value(), "prefix tap attachment") ||
      !expect(emit(hub, make_item(bytes, "route.alpha", "provider.alpha", OriginKind::component,
                                  InteractionKind::message_event, 0U),
                   1U)
                  .succeeded() &&
                  emit(hub, make_item(bytes, "route.alpha", "provider.alpha",
                                      OriginKind::component, InteractionKind::message_event, 2U),
                       2U)
                      .succeeded() &&
                  emit(hub, make_item(bytes), 3U).succeeded(),
              "prefix submissions")) {
    return false;
  }
  const auto empty = hub.poll(*tap.handle);
  const auto exact = hub.poll(*tap.handle);
  const auto oversized = hub.poll(*tap.handle);
  return expect(empty.record.has_value() && empty.record->payload_bytes().empty() &&
                    empty.record->payload_view_state() == PayloadViewState::complete,
                "zero-byte source complete") &&
         expect(exact.record.has_value() && exact.record->payload_bytes().size() == 2U &&
                    exact.record->payload_view_state() == PayloadViewState::complete,
                "source equal to bound complete") &&
         expect(oversized.record.has_value() && oversized.record->payload_bytes().size() == 2U &&
                    oversized.record->payload_bytes()[0] == std::byte{5} &&
                    oversized.record->payload_view_state() == PayloadViewState::truncated,
                "source over bound truncated");
}

/** @brief Verify a pulled record reports its producing declared point and every baseline field. */
[[nodiscard]] bool test_record_self_description() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem item = make_item(bytes);
  ObservationHub hub;
  const auto attach = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                           ObservationOverflowPolicy::drop_newest, {},
                                           "tap.declared"));
  if (!expect(attach.handle.has_value() && emit(hub, item, 5U).succeeded(),
              "record self-description publication")) {
    return false;
  }
  const auto pulled = hub.poll(*attach.handle);
  if (!expect(pulled.record.has_value(), "record self-description pull")) {
    return false;
  }
  const ObservationRecord& record = *pulled.record;
  static_cast<void>(emit(hub, item, 6U));
  return expect(record.tap_id().value() == "tap.declared", "record declared tap identity") &&
         expect(record.contract_id().value() == "contract.alpha", "record contract identity") &&
         expect(record.contract_version().value() == "1.2.3", "record contract version") &&
         expect(record.interface_id().value() == "interface.alpha", "record interface identity") &&
         expect(record.endpoint_id().value() == "endpoint.alpha", "record endpoint identity") &&
         expect(record.schema_id().value() == "schema.alpha", "record schema identity") &&
         expect(record.schema_version().value() == "2.0.1", "record schema version") &&
         expect(record.interaction_kind() == InteractionKind::message_event, "record interaction") &&
         expect(record.origin() == OriginKind::component, "record origin") &&
         expect(record.source_timestamp().nanoseconds() == 42, "record source timestamp") &&
         expect(record.source_clock_domain().value() == "clock.source", "record source clock") &&
         expect(record.observation_timestamp().nanoseconds() == 5, "record observation timestamp") &&
         expect(record.observation_clock_domain().value() == "clock.observer",
                "record observation clock") &&
         expect(record.sequence().has_value() && *record.sequence() == 5U, "record sequence") &&
         expect(record.correlation_id().value() == "correlation.alpha", "record correlation") &&
         expect(record.causation_id().value() == "causation.alpha", "record causation") &&
         expect(record.route_id().value() == "route.alpha", "record route identity") &&
         expect(record.provider_id().value() == "provider.alpha", "record provider identity") &&
         expect(record.source_payload_size() == bytes.size(), "record source size") &&
         expect(record.provider_outcome() == ObservationProviderOutcome::accepted,
                "record provider outcome") &&
         expect(record.payload_view_state() == PayloadViewState::omitted, "record payload state") &&
         expect(record.payload_schema_state() == PayloadSchemaState::undecoded,
                "record schema state");
}

/** @brief Verify retained and coalesced records carry their post-retention counter projection. */
[[nodiscard]] bool test_record_counter_projection() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  const CommunicationItem beta = make_item(bytes, "route.beta");
  ObservationHub drop_hub;
  const auto drop = drop_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                              ObservationOverflowPolicy::drop_newest));
  const auto first = emit(drop_hub, alpha, 1U);
  const auto second = emit(drop_hub, alpha, 2U);
  const auto drop_snapshot = drop_hub.snapshot(*drop.handle);
  const auto retained = drop_hub.poll(*drop.handle);
  const auto no_second = drop_hub.poll(*drop.handle);

  ObservationHub coalesce_hub;
  const auto coalesce = coalesce_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                                      ObservationOverflowPolicy::coalesce_latest));
  static_cast<void>(emit(coalesce_hub, alpha, 1U));
  static_cast<void>(emit(coalesce_hub, beta, 2U));
  static_cast<void>(emit(coalesce_hub, alpha, 3U));
  const auto replaced = coalesce_hub.poll(*coalesce.handle);

  ObservationHub lossless_hub;
  const auto lossless = lossless_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                                      ObservationOverflowPolicy::lossless_validation));
  static_cast<void>(emit(lossless_hub, alpha, 1U));
  const auto backpressure = emit(lossless_hub, alpha, 2U);
  const auto lossless_retained = lossless_hub.poll(*lossless.handle);
  return expect(first.succeeded() && second.succeeded(), "counter projection submissions") &&
         expect(drop_snapshot.has_value() && drop_snapshot->queued == 1U &&
                    drop_snapshot->accepted == 1U && drop_snapshot->dropped == 1U,
                "drop snapshot counters") &&
         expect(retained.record.has_value() && retained.record->counters().queued == 1U &&
                    retained.record->counters().accepted == 1U &&
                    retained.record->counters().dropped == 0U &&
                    retained.record->counters().coalesced == 0U,
                "retained record counter projection") &&
         expect(no_second.status.outcome == ObservationOutcome::no_record,
                "dropped submission produced no record") &&
         expect(replaced.record.has_value() && replaced.record->counters().coalesced == 1U &&
                    replaced.record->counters().queued == 2U &&
                    *replaced.record->sequence() == 3U,
                "coalesced replacement counter projection") &&
         expect(backpressure.outcome == ObservationOutcome::observation_backpressure &&
                    lossless_retained.record.has_value() &&
                    lossless_retained.record->counters().queued == 1U,
                "backpressure rejection produced no replacement record");
}

/** @brief Verify the snapshot reports the declared point and rejects foreign or stale handles. */
[[nodiscard]] bool test_snapshot_reports_declaration() {
  ObservationHub hub;
  ObservationHub foreign_hub;
  const auto attach = hub.attach(
      make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                ObservationOverflowPolicy::drop_newest, {}, "tap.snapshot",
                ObservationValidityEffect::invalidate_on_loss));
  if (!expect(attach.handle.has_value(), "snapshot declaration attachment")) {
    return false;
  }
  const auto snapshot = hub.snapshot(*attach.handle);
  const auto foreign = foreign_hub.snapshot(*attach.handle);
  const auto closed = hub.detach(*attach.handle);
  const auto stale = hub.snapshot(*attach.handle);
  return expect(snapshot.has_value() && snapshot->declared_tap_id.value() == "tap.snapshot" &&
                    snapshot->validity_effect == ObservationValidityEffect::invalidate_on_loss &&
                    snapshot->queued == 0U && snapshot->accepted == 0U && snapshot->dropped == 0U,
                "snapshot reports the declaration") &&
         expect(!foreign.has_value(), "foreign snapshot absent") &&
         expect(closed.succeeded() && !stale.has_value(), "closed snapshot absent");
}

/** @brief Verify two taps may declare one observation point with independent slots and counters. */
[[nodiscard]] bool test_repeated_declaration_capacity() {
  ObservationHub hub;
  const auto first = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::drop_newest, {}, "tap.shared"));
  const auto second = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                           ObservationOverflowPolicy::drop_newest, {}, "tap.shared"));
  if (!expect(first.handle.has_value() && second.handle.has_value() &&
                  first.handle->hub_instance_id() == second.handle->hub_instance_id() &&
                  first.handle->tap_id() != second.handle->tap_id(),
              "repeated declared-point slots")) {
    return false;
  }
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem item = make_item(bytes);
  static_cast<void>(emit(hub, item, 1U));
  const auto first_snapshot = hub.snapshot(*first.handle);
  const auto second_snapshot = hub.snapshot(*second.handle);
  const auto detached = hub.detach(*first.handle);
  const auto second_after = hub.snapshot(*second.handle);
  const auto first_after = hub.snapshot(*first.handle);
  const auto recreated = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                              ObservationOverflowPolicy::drop_newest, {},
                                              "tap.shared"));
  return expect(first_snapshot.has_value() &&
                    first_snapshot->declared_tap_id.value() == "tap.shared" &&
                    second_snapshot.has_value() &&
                    second_snapshot->declared_tap_id.value() == "tap.shared",
                "both taps report the declared identity") &&
         expect(first_snapshot->accepted == 1U && second_snapshot->accepted == 1U,
                "independent counters") &&
         expect(detached.succeeded() && second_after.has_value() &&
                    second_after->declared_tap_id.value() == "tap.shared" &&
                    !first_after.has_value(),
                "detaching one leaves the other active") &&
         expect(recreated.handle.has_value() &&
                    recreated.handle->tap_id() == first.handle->tap_id() &&
                    recreated.handle->generation() > first.handle->generation() &&
                    recreated.handle->generation() != second.handle->generation(),
                "recreated generation independent of the other tap");
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

/** @brief Verify drop-newest keeps the oldest records in FIFO order and counts each loss. */
[[nodiscard]] bool test_drop_newest_bounded_loss() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{0}, std::byte{0}, std::byte{0}};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                        ObservationOverflowPolicy::drop_newest));
  if (!expect(tap.handle.has_value(), "bounded drop attachment")) {
    return false;
  }
  const auto first = emit(hub, alpha, 1U);
  const auto second = emit(hub, alpha, 2U);
  const auto third = emit(hub, alpha, 3U);
  const auto snapshot = hub.snapshot(*tap.handle);
  const auto retained_first = hub.poll(*tap.handle);
  const auto retained_second = hub.poll(*tap.handle);
  const auto exhausted = hub.poll(*tap.handle);
  return expect(first.succeeded() && second.succeeded() && third.succeeded(),
                "drop-newest stays best effort") &&
         expect(snapshot.has_value() && snapshot->queued == 2U && snapshot->accepted == 2U &&
                    snapshot->dropped == 1U && snapshot->coalesced == 0U &&
                    snapshot->validity_state == ObservationValidityState::valid &&
                    !snapshot->experiment_validity_degraded,
                "bounded drop counters and bound") &&
         expect(retained_first.record.has_value() && *retained_first.record->sequence() == 1U &&
                    retained_second.record.has_value() && *retained_second.record->sequence() == 2U,
                "oldest records retained in FIFO order") &&
         expect(exhausted.status.outcome == ObservationOutcome::no_record,
                "dropped submission produced no record");
}

/** @brief Verify coalesce-latest replaces only the newest matching key and drops a non-match. */
[[nodiscard]] bool test_coalesce_latest_key_selection() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  const CommunicationItem beta = make_item(bytes, "route.beta");
  const CommunicationItem gamma = make_item(bytes, "route.gamma");
  ObservationHub hub;
  const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 3U,
                                        ObservationOverflowPolicy::coalesce_latest));
  if (!expect(tap.handle.has_value(), "coalesce attachment")) {
    return false;
  }
  static_cast<void>(emit(hub, alpha, 1U));
  static_cast<void>(emit(hub, beta, 2U));
  static_cast<void>(emit(hub, alpha, 3U));
  const auto replaced = emit(hub, alpha, 4U);
  const auto dropped = emit(hub, gamma, 5U);
  const auto snapshot = hub.snapshot(*tap.handle);
  const auto first = hub.poll(*tap.handle);
  const auto second = hub.poll(*tap.handle);
  const auto third = hub.poll(*tap.handle);
  return expect(replaced.succeeded() && dropped.succeeded(), "coalesce stays best effort") &&
         expect(snapshot.has_value() && snapshot->queued == 3U && snapshot->accepted == 3U &&
                    snapshot->coalesced == 1U && snapshot->dropped == 1U,
                "coalesce counters stay within the declared bound") &&
         expect(first.record.has_value() && first.record->route_id().value() == "route.alpha" &&
                    *first.record->sequence() == 1U,
                "oldest matching record untouched") &&
         expect(second.record.has_value() && second.record->route_id().value() == "route.beta" &&
                    *second.record->sequence() == 2U,
                "unrelated FIFO order preserved") &&
         expect(third.record.has_value() && third.record->route_id().value() == "route.alpha" &&
                    *third.record->sequence() == 4U,
                "only the newest matching record replaced");
}

/** @brief Verify lossless capacity is claimed before dispatch and rejects exactly once. */
[[nodiscard]] bool test_lossless_backpressure_pre_dispatch() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                        ObservationOverflowPolicy::lossless_validation));
  if (!expect(tap.handle.has_value(), "lossless pre-dispatch attachment")) {
    return false;
  }
  auto claim = hub.reserve(alpha);
  const auto blocked = hub.reserve(alpha);
  const auto degraded = hub.snapshot(*tap.handle);
  const auto cancelled = hub.cancel(std::move(*claim.reservation));
  auto recovered = hub.reserve(alpha);
  const auto committed = hub.commit(
      std::move(*recovered.reservation),
      {alpha, Timestamp(9), "clock.observer", 9U, ObservationProviderOutcome::accepted});
  const auto after = hub.snapshot(*tap.handle);
  const auto retained = hub.poll(*tap.handle);
  return expect(claim.status.succeeded() && claim.reservation.has_value(),
                "lossless capacity claimed before dispatch") &&
         expect(blocked.status.outcome == ObservationOutcome::observation_backpressure &&
                    !blocked.reservation.has_value(),
                "lossless capacity unavailable before provider mutation") &&
         expect(degraded.has_value() && degraded->backpressure_rejections == 1U &&
                    degraded->experiment_validity_degraded &&
                    degraded->validity_state == ObservationValidityState::degraded,
                "lossless rejection realizes at least degraded") &&
         expect(cancelled.succeeded() && recovered.status.succeeded() &&
                    recovered.reservation.has_value() && committed.succeeded(),
                "exact cancellation recovers capacity") &&
         expect(retained.record.has_value() && *retained.record->sequence() == 9U &&
                    after.has_value() && after->queued == 1U && after->accepted == 1U,
                "recovered claim retained exactly one record");
}

/** @brief Verify the declared validity effect applied to best-effort drop and coalesce losses. */
[[nodiscard]] bool test_validity_effect_on_best_effort_loss() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  const std::array<ObservationValidityEffect, 3U> effects{
      ObservationValidityEffect::none, ObservationValidityEffect::degrade_on_loss,
      ObservationValidityEffect::invalidate_on_loss};
  const std::array<ObservationValidityState, 3U> expected{
      ObservationValidityState::valid, ObservationValidityState::degraded,
      ObservationValidityState::invalid};
  ObservationHub drop_hub;
  ObservationHub coalesce_hub;
  bool valid = true;
  for (std::size_t index = 0U; index < effects.size(); ++index) {
    const auto drop = drop_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                                ObservationOverflowPolicy::drop_newest, {},
                                                "tap.drop", effects[index]));
    const auto coalesce = coalesce_hub.attach(make_spec(
        ObservationPayloadMode::metadata_only, 0U, 1U,
        ObservationOverflowPolicy::coalesce_latest, {}, "tap.coalesce", effects[index]));
    if (!expect(drop.handle.has_value() && coalesce.handle.has_value(),
                "validity-effect loss attachment")) {
      return false;
    }
    static_cast<void>(emit(drop_hub, alpha, 1U));
    static_cast<void>(emit(drop_hub, alpha, 2U));
    static_cast<void>(emit(coalesce_hub, alpha, 1U));
    static_cast<void>(emit(coalesce_hub, alpha, 2U));
    const auto drop_snapshot = drop_hub.snapshot(*drop.handle);
    const auto coalesce_snapshot = coalesce_hub.snapshot(*coalesce.handle);
    const bool lost = expected[index] != ObservationValidityState::valid;
    valid = expect(drop_snapshot.has_value() && coalesce_snapshot.has_value(),
                   "validity-effect snapshot") &&
            expect(drop_snapshot->validity_state == expected[index] &&
                       drop_snapshot->experiment_validity_degraded == lost &&
                       drop_snapshot->dropped == 1U,
                   "declared effect applied to a drop loss") &&
            expect(coalesce_snapshot->validity_state == expected[index] &&
                       coalesce_snapshot->experiment_validity_degraded == lost &&
                       coalesce_snapshot->coalesced == 1U,
                   "declared effect applied to a coalesce loss") &&
            valid;
  }
  return valid;
}

/** @brief Verify a lossless backpressure realizes at least degraded under every declaration. */
[[nodiscard]] bool test_validity_effect_on_lossless_backpressure() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  const std::array<ObservationValidityEffect, 3U> effects{
      ObservationValidityEffect::none, ObservationValidityEffect::degrade_on_loss,
      ObservationValidityEffect::invalidate_on_loss};
  const std::array<ObservationValidityState, 3U> expected{
      ObservationValidityState::degraded, ObservationValidityState::degraded,
      ObservationValidityState::invalid};
  bool valid = true;
  for (std::size_t index = 0U; index < effects.size(); ++index) {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::lossless_validation, {},
                                          "tap.lossless", effects[index]));
    if (!expect(tap.handle.has_value(), "lossless validity attachment")) {
      return false;
    }
    const auto first = emit(hub, alpha, 1U);
    const auto blocked = emit(hub, alpha, 2U);
    const auto snapshot = hub.snapshot(*tap.handle);
    valid = expect(first.succeeded(), "lossless first submission") &&
            expect(blocked.outcome == ObservationOutcome::observation_backpressure,
                   "lossless backpressure outcome") &&
            expect(snapshot.has_value() && snapshot->validity_state == expected[index] &&
                       snapshot->experiment_validity_degraded &&
                       snapshot->backpressure_rejections == 1U,
                   "lossless realizes at least degraded") &&
            valid;
  }
  return valid;
}

/** @brief Verify the realized status vocabulary, ordering, and snapshot compatibility projection. */
[[nodiscard]] bool test_validity_state_vocabulary() {
  bool valid =
      expect(to_string(ObservationValidityState::valid) == "valid", "valid external text") &&
      expect(to_string(ObservationValidityState::degraded) == "degraded",
             "degraded external text") &&
      expect(to_string(ObservationValidityState::invalid) == "invalid",
             "invalid external text") &&
      expect(static_cast<std::uint8_t>(ObservationValidityState::valid) <
                     static_cast<std::uint8_t>(ObservationValidityState::degraded) &&
                 static_cast<std::uint8_t>(ObservationValidityState::degraded) <
                     static_cast<std::uint8_t>(ObservationValidityState::invalid),
             "valid < degraded < invalid");
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                        ObservationOverflowPolicy::drop_newest, {}, "tap.vocab",
                                        ObservationValidityEffect::degrade_on_loss));
  if (!expect(tap.handle.has_value(), "vocabulary attachment")) {
    return false;
  }
  const auto before = hub.snapshot(*tap.handle);
  valid = expect(before.has_value() &&
                     before->validity_state == ObservationValidityState::valid &&
                     !before->experiment_validity_degraded,
                 "no loss reports valid") &&
          valid;
  static_cast<void>(emit(hub, alpha, 1U));
  static_cast<void>(emit(hub, alpha, 2U));
  const auto after = hub.snapshot(*tap.handle);
  return expect(after.has_value() &&
                    after->validity_state == ObservationValidityState::degraded &&
                    after->experiment_validity_degraded ==
                        (after->validity_state != ObservationValidityState::valid),
                "loss reports the realized status projection") &&
         valid;
}

/** @brief Verify acknowledgement closes a degraded interval while an invalid status persists. */
[[nodiscard]] bool test_acknowledge_closes_validity_interval() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub degraded_hub;
  const auto degraded_tap = degraded_hub.attach(make_spec(
      ObservationPayloadMode::metadata_only, 0U, 1U, ObservationOverflowPolicy::lossless_validation,
      {}, "tap.degraded", ObservationValidityEffect::degrade_on_loss));
  if (!expect(degraded_tap.handle.has_value(), "degraded interval attachment")) {
    return false;
  }
  auto held = degraded_hub.reserve(alpha);
  const auto blocked = degraded_hub.reserve(alpha);
  const auto degraded = degraded_hub.snapshot(*degraded_tap.handle);
  const auto acknowledged = degraded_hub.acknowledge(*degraded_tap.handle);
  const auto restored = degraded_hub.snapshot(*degraded_tap.handle);
  const auto cancelled = degraded_hub.cancel(std::move(*held.reservation));
  auto recovered = degraded_hub.reserve(alpha);
  const auto committed = degraded_hub.commit(
      std::move(*recovered.reservation),
      {alpha, Timestamp(1), "clock.observer", 1U, ObservationProviderOutcome::accepted});
  const auto retained = degraded_hub.poll(*degraded_tap.handle);

  ObservationHub invalid_hub;
  const auto invalid_tap = invalid_hub.attach(make_spec(
      ObservationPayloadMode::metadata_only, 0U, 1U, ObservationOverflowPolicy::drop_newest, {},
      "tap.invalid", ObservationValidityEffect::invalidate_on_loss));
  if (!expect(invalid_tap.handle.has_value(), "invalid persistence attachment")) {
    return false;
  }
  static_cast<void>(emit(invalid_hub, alpha, 1U));
  static_cast<void>(emit(invalid_hub, alpha, 2U));
  const auto invalid = invalid_hub.snapshot(*invalid_tap.handle);
  const auto invalid_acknowledged = invalid_hub.acknowledge(*invalid_tap.handle);
  static_cast<void>(emit(invalid_hub, alpha, 3U));
  const auto still_invalid = invalid_hub.snapshot(*invalid_tap.handle);

  ObservationHub foreign_hub;
  const auto foreign_tap = foreign_hub.attach(make_spec(
      ObservationPayloadMode::metadata_only, 0U, 1U, ObservationOverflowPolicy::drop_newest, {},
      "tap.foreign", ObservationValidityEffect::degrade_on_loss));
  if (!expect(foreign_tap.handle.has_value(), "foreign handle attachment")) {
    return false;
  }
  static_cast<void>(emit(foreign_hub, alpha, 1U));
  static_cast<void>(emit(foreign_hub, alpha, 2U));
  const auto foreign_acknowledged = degraded_hub.acknowledge(*foreign_tap.handle);
  const auto foreign_after = foreign_hub.snapshot(*foreign_tap.handle);
  const auto detached = foreign_hub.detach(*foreign_tap.handle);
  const auto stale_acknowledged = foreign_hub.acknowledge(*foreign_tap.handle);
  const auto stale_snapshot = foreign_hub.snapshot(*foreign_tap.handle);

  return expect(blocked.status.outcome == ObservationOutcome::observation_backpressure &&
                    degraded.has_value() &&
                    degraded->validity_state == ObservationValidityState::degraded &&
                    degraded->backpressure_rejections == 1U &&
                    degraded->experiment_validity_degraded,
                "degraded interval reported before acknowledgement") &&
         expect(acknowledged.succeeded() && restored.has_value() &&
                    restored->validity_state == ObservationValidityState::valid &&
                    restored->backpressure_rejections == 0U &&
                    !restored->experiment_validity_degraded,
                "acknowledgement closes the degraded interval") &&
         expect(cancelled.succeeded() && committed.succeeded() && retained.record.has_value() &&
                    retained.record->sequence().has_value(),
                "acknowledgement leaves exact claim authority intact") &&
         expect(invalid.has_value() && invalid->validity_state == ObservationValidityState::invalid &&
                    invalid->dropped == 1U && invalid_acknowledged.succeeded() &&
                    still_invalid.has_value() &&
                    still_invalid->validity_state == ObservationValidityState::invalid &&
                    still_invalid->dropped == 2U,
                "invalid status persists across acknowledgement and a further loss") &&
         expect(foreign_acknowledged.outcome == ObservationOutcome::invalid_tap_handle &&
                    foreign_after.has_value() &&
                    foreign_after->validity_state == ObservationValidityState::degraded &&
                    foreign_after->dropped == 1U,
                "foreign acknowledgement performs no interval reset") &&
         expect(detached.succeeded() &&
                    stale_acknowledged.outcome == ObservationOutcome::invalid_tap_handle &&
                    !stale_snapshot.has_value(),
                "stale acknowledgement performs no interval reset");
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
  return test_values_filters_and_versions() && test_filter_declared_constraints() &&
                 test_declared_tap_binding() && test_declared_tap_rejections() &&
                 test_validity_effect_vocabulary() && test_payload_policy_bounds() &&
                 test_record_self_description() && test_record_counter_projection() &&
                 test_snapshot_reports_declaration() && test_repeated_declaration_capacity() &&
                 test_metadata_only() && test_controlled_payload_states() &&
                 test_best_effort_overflow() && test_drop_newest_bounded_loss() &&
                 test_coalesce_latest_key_selection() &&
                 test_lossless_backpressure_pre_dispatch() &&
                 test_validity_effect_on_best_effort_loss() &&
                 test_validity_effect_on_lossless_backpressure() &&
                 test_validity_state_vocabulary() && test_acknowledge_closes_validity_interval() &&
                 test_lossless_reservations() &&
                 test_competing_reservation_interleaving() && test_exact_tap_handles() &&
                 test_synthetic_sink_concurrency()
             ? 0
             : 1;
}
