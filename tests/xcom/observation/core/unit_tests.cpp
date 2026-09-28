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
 * (XCOM-SW-OBS-003, FR-013, SC-004). T023 adds the visible consumer-counter, disconnect-isolation,
 * failure-isolation, and blocking-isolation cases of docs/engineering/xcom/t023/verification-plan.md
 * (XCOM-SW-OBS-004, FR-014, SC-005). T024 adds the consolidated observation acceptance matrix of
 * docs/engineering/xcom/t024/verification-plan.md: metadata-only zero-payload completeness, the
 * bounded-prefix/redacted payload-view table, drop/coalesce ordering and multi-tap independence,
 * min/max saturation and lossless rejection/recovery, bounded deterministic concurrency over one
 * lossless tap, the declared-effect validity interval,
 * safe detach/ownership, and the complete normalized record
 * (XCOM-SW-OBS-001…-005, FR-011…FR-014, FR-023, SC-003…SC-005).
 */

#include "xverse/xcom/observation.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <thread>
#include <utility>
#include <vector>

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

/** @brief The four accepted interaction families exercised by the T024 matrix. */
constexpr std::array<InteractionKind, 4U> kT024Families{
    InteractionKind::signal_state_update, InteractionKind::message_event,
    InteractionKind::service_request, InteractionKind::service_response};

/**
 * @brief Commit one normalized event whose producer declared no sequence.
 * @ownership Owns the reservation it creates and consumes; caller items are borrowed for the call.
 * @lifetime The reservation is committed before return; the hub must outlive this call.
 * @thread_safety Serialized through the hub; single-threaded use only.
 * @failure Returns the stable reserve status without a provider or queue mutation when capacity is
 * unavailable.
 */
[[nodiscard]] ObservationStatus emit_absent_sequence(ObservationHub& hub, const CommunicationItem& item,
                                                     const std::int64_t observation_timestamp) {
  auto result = hub.reserve(item);
  if (!result.status.succeeded() || !result.reservation.has_value()) {
    return result.status;
  }
  return hub.commit(std::move(*result.reservation),
                    {item, Timestamp(observation_timestamp), "clock.observer", std::nullopt,
                     ObservationProviderOutcome::accepted});
}

/**
 * @brief Pull up to count retained records into owned values for FIFO assertions.
 * @ownership Owns every returned record copy; the hub and handle are borrowed.
 * @lifetime The returned records live independently of the hub; the handle must be current.
 * @thread_safety Serialized through the hub; single-threaded use only.
 * @failure Stops early at the first non-`accepted` pull; never loops without a finite bound.
 */
[[nodiscard]] std::vector<ObservationRecord> poll_all(ObservationHub& hub,
                                                      const ObservationTapHandle& handle,
                                                      const std::size_t count) {
  std::vector<ObservationRecord> records;
  for (std::size_t index = 0U; index < count; ++index) {
    auto result = hub.poll(handle);
    if (!result.record.has_value()) {
      break;
    }
    records.push_back(*result.record);
  }
  return records;
}

/**
 * @brief Assert the complete normalized self-description of one metadata-only record.
 * @ownership Borrows the record for the call; asserts only.
 * @lifetime The borrowed record must remain valid for the call.
 * @thread_safety Pure; concurrent const access is safe.
 * @failure Returns false and reports the first violated field expectation.
 */
[[nodiscard]] bool expect_metadata_record(const ObservationRecord& record,
                                          const InteractionKind family, const std::size_t source_size,
                                          const std::uint64_t sequence, const std::string_view tap_id,
                                          const OriginKind origin,
                                          const ObservationProviderOutcome provider_outcome) {
  return expect(record.payload_bytes().empty(), "metadata exposes zero payload bytes") &&
         expect(record.payload_view_state() == PayloadViewState::omitted, "metadata view omitted") &&
         expect(record.payload_schema_state() == PayloadSchemaState::undecoded,
                "metadata schema undecoded") &&
         expect(record.source_payload_size() == source_size, "metadata source size complete") &&
         expect(record.interaction_kind() == family, "metadata interaction preserved") &&
         expect(record.origin() == origin, "metadata origin preserved") &&
         expect(record.contract_id().value() == "contract.alpha", "metadata contract identity") &&
         expect(record.contract_version().value() == "1.2.3", "metadata contract version") &&
         expect(record.interface_id().value() == "interface.alpha", "metadata interface identity") &&
         expect(record.endpoint_id().value() == "endpoint.alpha", "metadata endpoint identity") &&
         expect(record.schema_id().value() == "schema.alpha", "metadata schema identity") &&
         expect(record.schema_version().value() == "2.0.1", "metadata schema version") &&
         expect(record.source_timestamp().nanoseconds() == 42, "metadata source timestamp") &&
         expect(record.source_clock_domain().value() == "clock.source", "metadata source clock") &&
         expect(record.observation_timestamp().nanoseconds() ==
                    static_cast<std::int64_t>(sequence),
                "metadata observation timestamp") &&
         expect(record.observation_clock_domain().value() == "clock.observer",
                "metadata observation clock") &&
         expect(record.sequence().has_value() && *record.sequence() == sequence,
                "metadata sequence") &&
         expect(record.correlation_id().value() == "correlation.alpha", "metadata correlation") &&
         expect(record.causation_id().value() == "causation.alpha", "metadata causation") &&
         expect(record.route_id().value() == "route.alpha", "metadata route identity") &&
         expect(record.provider_id().value() == "provider.alpha", "metadata provider identity") &&
         expect(record.provider_outcome() == provider_outcome, "metadata provider outcome") &&
         expect(record.tap_id().value() == tap_id, "metadata declared tap identity");
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

/** @brief Verify the synthetic sink's visible consumer counters track each pull outcome exactly. */
[[nodiscard]] bool test_synthetic_sink_visible_counters() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 4U,
                                        ObservationOverflowPolicy::drop_newest));
  if (!expect(tap.handle.has_value(), "visible counters attachment")) {
    return false;
  }
  SyntheticObservationSink sink(hub, *tap.handle);
  const SyntheticSinkCounters initial = sink.counters();
  bool valid = expect(initial.pulled == 0U && initial.empty == 0U &&
                          initial.disconnected == 0U && initial.failed == 0U,
                      "counters start at zero") &&
               expect(sink.connected(), "sink starts connected");
  static_cast<void>(emit(hub, alpha, 1U));
  static_cast<void>(emit(hub, alpha, 2U));
  const auto first = sink.pull();
  const auto second = sink.pull();
  const SyntheticSinkCounters after_records = sink.counters();
  valid = expect(first.record.has_value() && *first.record->sequence() == 1U &&
                     second.record.has_value() && *second.record->sequence() == 2U,
                 "records returned in FIFO order") &&
          expect(after_records.pulled == 2U && after_records.empty == 0U &&
                     after_records.disconnected == 0U && after_records.failed == 0U,
                 "successful pulls counted once each") &&
          valid;
  const auto empty = sink.pull();
  const SyntheticSinkCounters after_empty = sink.counters();
  valid = expect(empty.status.outcome == ObservationOutcome::no_record,
                 "empty pull reports no_record") &&
          expect(after_empty.pulled == 2U && after_empty.empty == 1U,
                 "empty pull counted once") &&
          valid;
  sink.disconnect();
  const auto disconnected = sink.pull();
  const SyntheticSinkCounters after_disconnect = sink.counters();
  valid = expect(!sink.connected() &&
                     disconnected.status.outcome == ObservationOutcome::sink_disconnected,
                 "disconnect reports sink_disconnected") &&
          expect(after_disconnect.disconnected == 1U && after_disconnect.empty == 1U,
                 "disconnected pull counted once") &&
          valid;
  const auto reconnected = sink.connect();
  const SyntheticSinkCounters after_connect = sink.counters();
  valid = expect(reconnected.succeeded() && sink.connected(), "reconnect restores pulling") &&
          expect(after_connect.disconnected == 1U && after_connect.pulled == 2U &&
                     after_connect.empty == 1U && after_connect.failed == 0U,
                 "connect does not change counters") &&
          valid;
  const auto detached = hub.detach(*tap.handle);
  const auto failed = sink.pull();
  const SyntheticSinkCounters final_counts = sink.counters();
  const std::uint64_t attempts = final_counts.pulled + final_counts.empty +
                                 final_counts.disconnected + final_counts.failed;
  return expect(detached.succeeded() &&
                    failed.status.outcome == ObservationOutcome::invalid_tap_handle,
                "stale handle reports invalid_tap_handle") &&
         expect(final_counts.failed == 1U && attempts == 5U,
                "accounting identity holds over five pull attempts") &&
         valid;
}

/** @brief Verify a local disconnect isolates its own sink and consumes no retained record. */
[[nodiscard]] bool test_synthetic_sink_disconnect_isolation() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  const auto first_tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                              ObservationOverflowPolicy::drop_newest));
  const auto second_tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                               ObservationOverflowPolicy::drop_newest));
  if (!expect(first_tap.handle.has_value() && second_tap.handle.has_value(),
              "disconnect isolation attachment")) {
    return false;
  }
  SyntheticObservationSink sink_a(hub, *first_tap.handle);
  SyntheticObservationSink sink_b(hub, *second_tap.handle);
  static_cast<void>(emit(hub, alpha, 1U));
  const auto before = hub.snapshot(*first_tap.handle);
  sink_a.disconnect();
  const auto blocked = sink_a.pull();
  const auto after = hub.snapshot(*first_tap.handle);
  bool valid = expect(blocked.status.outcome == ObservationOutcome::sink_disconnected &&
                          !blocked.record.has_value(),
                      "disconnected sink consumes nothing") &&
               expect(before.has_value() && before->queued == 1U && before->accepted == 1U &&
                          after.has_value() && after->queued == 1U && after->accepted == 1U &&
                          after->dropped == 0U,
                      "disconnect leaves the observed tap unchanged") &&
               expect(sink_a.counters().disconnected == 1U && sink_a.counters().pulled == 0U,
                      "disconnected counter visible");
  const auto other = sink_b.pull();
  valid = expect(other.record.has_value() && *other.record->sequence() == 1U &&
                     sink_b.counters().pulled == 1U,
                 "unrelated sink is unaffected") &&
          valid;
  const auto reconnected = sink_a.connect();
  const auto restored = sink_a.pull();
  valid = expect(reconnected.succeeded() && restored.record.has_value() &&
                     *restored.record->sequence() == 1U && sink_a.counters().pulled == 1U,
                 "reconnect restores the retained record") &&
          valid;
  return valid;
}

/** @brief Verify a stale, foreign, or closed exact handle fails without mutating any tap. */
[[nodiscard]] bool test_synthetic_sink_failure_isolation() {
  ObservationHub hub;
  ObservationHub foreign_hub;
  const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                        ObservationOverflowPolicy::drop_newest));
  const auto foreign_tap = foreign_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                                        ObservationOverflowPolicy::drop_newest));
  if (!expect(tap.handle.has_value() && foreign_tap.handle.has_value(),
              "failure isolation attachment")) {
    return false;
  }
  SyntheticObservationSink sink(hub, *tap.handle);
  SyntheticObservationSink foreign_sink(hub, *foreign_tap.handle);
  const auto foreign_pull = foreign_sink.pull();
  const auto foreign_snapshot = foreign_hub.snapshot(*foreign_tap.handle);
  const auto foreign_at_this_hub = hub.snapshot(*foreign_tap.handle);
  bool valid = expect(foreign_pull.status.outcome == ObservationOutcome::invalid_tap_handle &&
                          !foreign_pull.record.has_value() &&
                          foreign_sink.counters().failed == 1U,
                      "foreign handle fails and is counted") &&
               expect(foreign_snapshot.has_value() && foreign_snapshot->accepted == 0U &&
                          foreign_snapshot->queued == 0U,
                      "foreign hub slot unchanged") &&
               expect(!foreign_at_this_hub.has_value(),
                      "foreign handle authenticates at neither hub");
  const auto detached = hub.detach(*tap.handle);
  const auto failed = sink.pull();
  valid = expect(detached.succeeded() &&
                     failed.status.outcome == ObservationOutcome::invalid_tap_handle &&
                     sink.counters().failed == 1U,
                 "detached handle fails and is counted") &&
          valid;
  const auto recreated = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                              ObservationOverflowPolicy::drop_newest));
  const auto recreated_snapshot = hub.snapshot(*recreated.handle);
  const auto refused = sink.connect();
  valid = expect(recreated.handle.has_value() && recreated_snapshot.has_value() &&
                     recreated_snapshot->accepted == 0U && recreated_snapshot->queued == 0U,
                 "recreated slot keeps its own counters") &&
          expect(refused.outcome == ObservationOutcome::invalid_tap_handle && !sink.connected(),
                 "stale reconnect refused and leaves the sink disabled") &&
          valid;
  return valid;
}

/** @brief Verify a connected non-pulling sink never blocks a bounded, loss-visible tap. */
[[nodiscard]] bool test_synthetic_sink_blocking_isolation() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  const auto drop_tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                             ObservationOverflowPolicy::drop_newest));
  const auto coalesce_tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                                 ObservationOverflowPolicy::coalesce_latest));
  if (!expect(drop_tap.handle.has_value() && coalesce_tap.handle.has_value(),
              "blocking isolation attachment")) {
    return false;
  }
  SyntheticObservationSink drop_sink(hub, *drop_tap.handle);
  SyntheticObservationSink coalesce_sink(hub, *coalesce_tap.handle);
  bool accepted = true;
  for (std::uint64_t sequence = 1U; sequence <= 5U; ++sequence) {
    accepted = emit(hub, alpha, sequence).succeeded() && accepted;
  }
  const auto drop_snapshot = hub.snapshot(*drop_tap.handle);
  const auto coalesce_snapshot = hub.snapshot(*coalesce_tap.handle);
  const SyntheticSinkCounters drop_before = drop_sink.counters();
  const SyntheticSinkCounters coalesce_before = coalesce_sink.counters();
  bool valid = expect(accepted, "saturation stays best effort without blocking") &&
               expect(drop_snapshot.has_value() && drop_snapshot->queued == 2U &&
                          drop_snapshot->accepted == 2U && drop_snapshot->dropped == 3U,
                      "drop loss counters visible within the bound") &&
               expect(coalesce_snapshot.has_value() && coalesce_snapshot->queued == 2U &&
                          coalesce_snapshot->accepted == 2U && coalesce_snapshot->coalesced == 3U,
                      "coalesce loss counters visible within the bound") &&
               expect(drop_before.pulled == 0U && drop_before.empty == 0U &&
                          drop_before.disconnected == 0U && drop_before.failed == 0U &&
                          coalesce_before.pulled == 0U && coalesce_before.failed == 0U,
                      "sink counters stay zero until it pulls");
  const auto retained_first = drop_sink.pull();
  const auto retained_second = drop_sink.pull();
  const auto exhausted = drop_sink.pull();
  valid = expect(retained_first.record.has_value() && *retained_first.record->sequence() == 1U &&
                     retained_second.record.has_value() && *retained_second.record->sequence() == 2U,
                 "bounded records keep FIFO order after saturation") &&
          expect(exhausted.status.outcome == ObservationOutcome::no_record &&
                     drop_sink.counters().pulled == 2U && drop_sink.counters().empty == 1U,
                 "counters reflect only the sink's own pulls") &&
          valid;
  return valid;
}

/**
 * @brief Prove metadata-only zero-payload completeness and the bounded/redacted payload-view table.
 * @details Realizes T24-TS-001 (`metadata-only-zero-payload`, `controlled-payload-view`):
 * T024-SR-003, T024-SR-005, T024-SR-006; XCOM-SW-OBS-001/-002/-005; FR-011, FR-012, SC-003.
 * @return true only when every metadata and payload-view assertion holds.
 */
[[nodiscard]] bool test_observation_metadata_and_payload_view_matrix() {
  const std::array<std::byte, 4U> source{std::byte{11}, std::byte{22}, std::byte{33}, std::byte{44}};
  constexpr std::array<std::size_t, 3U> sizes{0U, 1U, 4U};

  ObservationHub hub;
  const auto metadata = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U,
                                             kMaximumObservationRecordsPerTap,
                                             ObservationOverflowPolicy::drop_newest, {},
                                             "tap.t024.metadata"));
  if (!expect(metadata.handle.has_value(), "T024 metadata attachment")) {
    return false;
  }
  bool valid = true;
  std::uint64_t sequence = 0U;
  for (const InteractionKind family : kT024Families) {
    for (const std::size_t size : sizes) {
      ++sequence;
      valid = expect(emit(hub,
                          make_item(source, "route.alpha", "provider.alpha", OriginKind::component,
                                    family, size),
                          sequence)
                         .succeeded(),
                     "T024 metadata publication") &&
              valid;
    }
  }
  const auto batch = hub.snapshot(*metadata.handle);
  valid = expect(batch.has_value() && batch->accepted == 12U && batch->queued == 12U &&
                     batch->dropped == 0U && batch->coalesced == 0U,
                 "T024 metadata batch retained exactly once") &&
          valid;
  sequence = 0U;
  for (const InteractionKind family : kT024Families) {
    for (const std::size_t size : sizes) {
      ++sequence;
      const auto pulled = hub.poll(*metadata.handle);
      valid = expect(pulled.record.has_value(), "T024 metadata record pulled exactly once") &&
              expect_metadata_record(*pulled.record, family, size, sequence, "tap.t024.metadata",
                                     OriginKind::component, ObservationProviderOutcome::accepted) &&
              valid;
    }
  }

  struct PrefixRow final {
    ObservationPayloadMode mode;
    std::size_t bound;
    std::size_t source_size;
    std::size_t visible;
    PayloadViewState state;
  };
  const std::array<PrefixRow, 8U> rows{{
      {ObservationPayloadMode::bounded_prefix, 1U, 0U, 0U, PayloadViewState::complete},
      {ObservationPayloadMode::bounded_prefix, 1U, 1U, 1U, PayloadViewState::complete},
      {ObservationPayloadMode::bounded_prefix, 1U, 4U, 1U, PayloadViewState::truncated},
      {ObservationPayloadMode::bounded_prefix, 3U, 4U, 3U, PayloadViewState::truncated},
      {ObservationPayloadMode::bounded_prefix, 4U, 4U, 4U, PayloadViewState::complete},
      {ObservationPayloadMode::bounded_prefix, kMaximumObservedPayloadBytes, 4U, 4U,
       PayloadViewState::complete},
      {ObservationPayloadMode::redacted, 0U, 4U, 0U, PayloadViewState::redacted},
      {ObservationPayloadMode::metadata_only, 0U, 4U, 0U, PayloadViewState::omitted},
  }};
  for (const PrefixRow& row : rows) {
    ObservationHub view_hub;
    const auto tap = view_hub.attach(make_spec(row.mode, row.bound, 1U,
                                               ObservationOverflowPolicy::drop_newest, {},
                                               "tap.t024.prefix"));
    if (!expect(tap.handle.has_value(), "T024 payload-view attachment") ||
        !expect(emit(view_hub,
                     make_item(source, "route.alpha", "provider.alpha", OriginKind::component,
                               InteractionKind::message_event, row.source_size),
                     1U)
                     .succeeded(),
                 "T024 payload-view publication")) {
      return false;
    }
    const auto pulled = view_hub.poll(*tap.handle);
    if (!expect(pulled.record.has_value(), "T024 payload-view record")) {
      return false;
    }
    const ObservationRecord& record = *pulled.record;
    const std::span<const std::byte> visible = record.payload_bytes();
    valid = expect(visible.size() == row.visible, "T024 payload-view visible size") &&
            expect(record.payload_view_state() == row.state, "T024 payload-view state") &&
            expect(record.payload_schema_state() == PayloadSchemaState::undecoded,
                   "T024 payload-view schema stays undecoded") &&
            expect(record.source_payload_size() == row.source_size,
                   "T024 payload-view complete source size") &&
            valid;
    for (std::size_t index = 0U; index < visible.size(); ++index) {
      valid = expect(visible[index] == source[index], "T024 payload-view exact leading byte") && valid;
    }
  }

  const auto minimum = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.t024.min", {}, ObservationPayloadMode::bounded_prefix, 1U,
       1U, ObservationOverflowPolicy::drop_newest});
  const auto maximum = ObservationTapSpec::create(
      {kObservationContractVersion, "tap.t024.max", {}, ObservationPayloadMode::bounded_prefix,
       kMaximumObservedPayloadBytes, kMaximumObservationRecordsPerTap,
       ObservationOverflowPolicy::drop_newest});
  valid = expect(minimum.has_value() && minimum->maximum_payload_bytes() == 1U,
                 "T024 minimum prefix bound accepted") &&
          expect(maximum.has_value() &&
                     maximum->maximum_payload_bytes() == kMaximumObservedPayloadBytes,
                 "T024 maximum prefix bound accepted") &&
          expect(!ObservationTapSpec::create(
                      {kObservationContractVersion, "tap.t024.reject", {},
                       ObservationPayloadMode::bounded_prefix, 0U, 1U,
                       ObservationOverflowPolicy::drop_newest})
                      .has_value(),
                 "T024 zero prefix bound rejected") &&
          expect(!ObservationTapSpec::create(
                      {kObservationContractVersion, "tap.t024.reject", {},
                       ObservationPayloadMode::bounded_prefix, kMaximumObservedPayloadBytes + 1U, 1U,
                       ObservationOverflowPolicy::drop_newest})
                      .has_value(),
                 "T024 over-bound prefix rejected") &&
          expect(!ObservationTapSpec::create(
                      {kObservationContractVersion, "tap.t024.reject", {},
                       ObservationPayloadMode::metadata_only, 1U, 1U,
                       ObservationOverflowPolicy::drop_newest})
                      .has_value(),
                 "T024 non-zero bound on metadata rejected") &&
          expect(!ObservationTapSpec::create(
                      {kObservationContractVersion, "tap.t024.reject", {},
                       ObservationPayloadMode::redacted, 1U, 1U,
                       ObservationOverflowPolicy::drop_newest})
                      .has_value(),
                 "T024 non-zero bound on redacted rejected") &&
          valid;
  return valid;
}

/**
 * @brief Prove per-tap FIFO under drop/coalesce, coalesce position, and multi-tap independence.
 * @details Realizes T24-TS-002 (`ordering`): T024-SR-007; XCOM-SW-OBS-003; FR-013, SC-004.
 * @return true only when every ordering assertion holds.
 */
[[nodiscard]] bool test_observation_ordering_matrix() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  const auto drop = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 4U,
                                         ObservationOverflowPolicy::drop_newest, {}, "tap.t024.drop"));
  const auto coalesce =
      hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 4U,
                           ObservationOverflowPolicy::coalesce_latest, {}, "tap.t024.coalesce"));
  if (!expect(drop.handle.has_value() && coalesce.handle.has_value(), "T024 ordering attachment")) {
    return false;
  }
  bool valid = true;
  for (std::uint64_t sequence = 1U; sequence <= 5U; ++sequence) {
    valid = expect(emit(hub, alpha, sequence).succeeded(), "T024 ordering publication") && valid;
  }
  const auto drop_snapshot = hub.snapshot(*drop.handle);
  const auto coalesce_snapshot = hub.snapshot(*coalesce.handle);
  const std::vector<ObservationRecord> drop_records = poll_all(hub, *drop.handle, 4U);
  const std::vector<ObservationRecord> coalesce_records = poll_all(hub, *coalesce.handle, 4U);
  valid = expect(drop_snapshot.has_value() && drop_snapshot->accepted == 4U &&
                     drop_snapshot->dropped == 1U && drop_snapshot->queued == 4U,
                 "T024 drop-newest ordering counters") &&
          expect(coalesce_snapshot.has_value() && coalesce_snapshot->accepted == 4U &&
                     coalesce_snapshot->coalesced == 1U && coalesce_snapshot->queued == 4U,
                 "T024 coalesce-latest ordering counters") &&
          expect(drop_records.size() == 4U && coalesce_records.size() == 4U,
                 "T024 ordering record counts") &&
          valid;
  constexpr std::array<std::uint64_t, 4U> drop_order{1U, 2U, 3U, 4U};
  constexpr std::array<std::uint64_t, 4U> coalesce_order{1U, 2U, 3U, 5U};
  for (std::size_t index = 0U; index < drop_records.size(); ++index) {
    valid = expect(drop_records[index].sequence().has_value() &&
                       *drop_records[index].sequence() == drop_order[index],
                   "T024 drop-newest preserves retained FIFO order") &&
            valid;
  }
  for (std::size_t index = 0U; index < coalesce_records.size(); ++index) {
    valid = expect(coalesce_records[index].sequence().has_value() &&
                       *coalesce_records[index].sequence() == coalesce_order[index],
                   "T024 coalesce replacement position") &&
            valid;
  }
  for (std::size_t index = 1U; index < drop_records.size(); ++index) {
    valid = expect(drop_records[index - 1U].sequence().has_value() &&
                       drop_records[index].sequence().has_value() &&
                       *drop_records[index - 1U].sequence() < *drop_records[index].sequence(),
                   "T024 pulled sequence strictly increasing") &&
            valid;
  }

  ObservationHub pair;
  const auto a = pair.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                       ObservationOverflowPolicy::drop_newest, {}, "tap.t024.a"));
  const auto b = pair.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                       ObservationOverflowPolicy::drop_newest, {}, "tap.t024.b"));
  if (!expect(a.handle.has_value() && b.handle.has_value(), "T024 multi-tap attachment")) {
    return false;
  }
  for (std::uint64_t sequence = 1U; sequence <= 3U; ++sequence) {
    valid = expect(emit(pair, alpha, sequence).succeeded(), "T024 multi-tap publication") && valid;
  }
  const auto a_snapshot = pair.snapshot(*a.handle);
  const auto b_snapshot = pair.snapshot(*b.handle);
  const std::vector<ObservationRecord> a_records = poll_all(pair, *a.handle, 3U);
  const auto b_after_a = pair.snapshot(*b.handle);
  const std::vector<ObservationRecord> b_records = poll_all(pair, *b.handle, 3U);
  valid = expect(a_snapshot.has_value() && a_snapshot->accepted == 2U && a_snapshot->queued == 2U &&
                     b_snapshot.has_value() && b_snapshot->accepted == 2U &&
                     b_snapshot->queued == 2U,
                 "T024 independent multi-tap counters") &&
          expect(a_records.size() == 2U && a_records[0].sequence().has_value() &&
                     *a_records[0].sequence() == 1U && a_records[1].sequence().has_value() &&
                     *a_records[1].sequence() == 2U,
                 "T024 first tap FIFO order") &&
          expect(b_after_a.has_value() && b_after_a->queued == 2U,
                 "T024 pulling one tap leaves the other queue") &&
          expect(b_records.size() == 2U && b_records[0].sequence().has_value() &&
                     *b_records[0].sequence() == 1U && b_records[1].sequence().has_value() &&
                     *b_records[1].sequence() == 2U,
                 "T024 second tap independent FIFO order") &&
          valid;
  return valid;
}

/**
 * @brief Prove drop-newest min/max bounds, coalesce key selection, lossless rejection/recovery, and
 * bounded deterministic concurrency.
 * @details Realizes T24-TS-003 (`saturation`): T024-SR-004, T024-SR-008, T024-SR-009, T024-SR-010,
 * and the T024-SR-018 deterministic bounded concurrency sub-check over one lossless tap;
 * XCOM-SW-OBS-003/-004; FR-013, FR-014, SC-003, SC-004.
 * @return true only when every saturation, accounting, and concurrency assertion holds.
 */
[[nodiscard]] bool test_observation_saturation_bound_matrix() {
  const std::array<std::byte, 4U> bytes{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  const CommunicationItem beta = make_item(bytes, "route.beta");
  const CommunicationItem gamma = make_item(bytes, "route.gamma");
  bool valid = true;

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.drop1"));
    if (!expect(tap.handle.has_value(), "T024 bound-min attachment")) {
      return false;
    }
    for (std::uint64_t sequence = 1U; sequence <= 5U; ++sequence) {
      valid = expect(emit(hub, alpha, sequence).succeeded(),
                     "T024 bound-min stays best effort") &&
              valid;
      const auto bounded = hub.snapshot(*tap.handle);
      valid = expect(bounded.has_value() && bounded->queued <= 1U,
                     "T024 bound-min queue within capacity") &&
              valid;
    }
    const auto snapshot = hub.snapshot(*tap.handle);
    const auto oldest = hub.poll(*tap.handle);
    const auto exhausted = hub.poll(*tap.handle);
    valid = expect(snapshot.has_value() && snapshot->accepted == 1U && snapshot->dropped == 4U &&
                       snapshot->queued == 1U,
                   "T024 bound-min loss counters") &&
            expect(oldest.record.has_value() && oldest.record->sequence().has_value() &&
                       *oldest.record->sequence() == 1U,
                   "T024 bound-min oldest retained") &&
            expect(exhausted.status.outcome == ObservationOutcome::no_record,
                   "T024 bound-min no phantom record") &&
            expect(snapshot->accepted + snapshot->dropped == 5U,
                   "T024 bound-min accounting identity") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U,
                                          kMaximumObservationRecordsPerTap,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.drop16"));
    if (!expect(tap.handle.has_value(), "T024 bound-max attachment")) {
      return false;
    }
    for (std::uint64_t sequence = 1U; sequence <= 20U; ++sequence) {
      valid = expect(emit(hub, alpha, sequence).succeeded(),
                     "T024 bound-max stays best effort") &&
              valid;
    }
    const auto snapshot = hub.snapshot(*tap.handle);
    const std::vector<ObservationRecord> records =
        poll_all(hub, *tap.handle, kMaximumObservationRecordsPerTap);
    const auto exhausted = hub.poll(*tap.handle);
    valid = expect(snapshot.has_value() &&
                       snapshot->queued <= kMaximumObservationRecordsPerTap,
                   "T024 bound-max queue within capacity") &&
            expect(records.size() == kMaximumObservationRecordsPerTap,
                   "T024 bound-max retains the declared capacity") &&
            expect(exhausted.status.outcome == ObservationOutcome::no_record,
                   "T024 bound-max no phantom record") &&
            expect(snapshot.has_value() && snapshot->accepted == 16U && snapshot->dropped == 4U &&
                       snapshot->queued == 16U,
                   "T024 bound-max loss counters") &&
            expect(snapshot->accepted + snapshot->dropped == 20U,
                   "T024 bound-max accounting identity") &&
            valid;
    for (std::size_t index = 0U; index < records.size(); ++index) {
      valid = expect(records[index].sequence().has_value() &&
                         *records[index].sequence() == static_cast<std::uint64_t>(index + 1U),
                     "T024 bound-max FIFO order") &&
              valid;
    }
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::coalesce_latest, {},
                                          "tap.t024.coal1"));
    if (!expect(tap.handle.has_value(), "T024 coalesce-min attachment")) {
      return false;
    }
    valid = expect(emit(hub, alpha, 1U).succeeded() && emit(hub, beta, 2U).succeeded() &&
                       emit(hub, alpha, 3U).succeeded() && emit(hub, gamma, 4U).succeeded(),
                   "T024 coalesce-min submissions") &&
            valid;
    const auto snapshot = hub.snapshot(*tap.handle);
    const auto record = hub.poll(*tap.handle);
    valid = expect(snapshot.has_value() && snapshot->accepted == 1U && snapshot->dropped == 2U &&
                       snapshot->coalesced == 1U && snapshot->queued == 1U,
                   "T024 coalesce-min key selection counters") &&
            expect(record.record.has_value() && record.record->route_id().value() == "route.alpha" &&
                       record.record->sequence().has_value() &&
                       *record.record->sequence() == 3U,
                   "T024 coalesce-min replaces only the matching key") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::lossless_validation, {},
                                          "tap.t024.lossless"));
    if (!expect(tap.handle.has_value(), "T024 lossless attachment")) {
      return false;
    }
    auto held = hub.reserve(alpha);
    const auto blocked = hub.reserve(alpha);
    const auto snapshot = hub.snapshot(*tap.handle);
    const auto cancelled = hub.cancel(std::move(*held.reservation));
    auto recovered = hub.reserve(alpha);
    const auto committed = hub.commit(
        std::move(*recovered.reservation),
        {alpha, Timestamp(1), "clock.observer", 1U, ObservationProviderOutcome::accepted});
    const auto after = hub.snapshot(*tap.handle);
    const auto record = hub.poll(*tap.handle);
    valid = expect(held.status.succeeded() && held.reservation.has_value(),
                   "T024 lossless capacity claimed before provider") &&
            expect(blocked.status.outcome == ObservationOutcome::observation_backpressure &&
                       !blocked.reservation.has_value(),
                   "T024 lossless rejection before mutation") &&
            expect(snapshot.has_value() && snapshot->backpressure_rejections == 1U &&
                       snapshot->experiment_validity_degraded && snapshot->queued == 0U &&
                       snapshot->accepted == 0U,
                   "T024 lossless rejection raises validity without mutation") &&
            expect(cancelled.succeeded() && recovered.status.succeeded() &&
                       recovered.reservation.has_value() && committed.succeeded(),
                   "T024 lossless recovery commits") &&
            expect(after.has_value() && after->queued == 1U && after->accepted == 1U,
                   "T024 lossless recovered queue state") &&
            expect(record.record.has_value() && record.record->sequence().has_value() &&
                       *record.record->sequence() == 1U,
                   "T024 lossless commit retained exactly once") &&
            valid;
  }

  {
    // T024-SR-018: bounded, deterministic concurrency over one lossless tap. Four publishers each
    // perform a fixed number of reserve/commit attempts; because lossless capacity is claimed before
    // provider mutation and every successful claim is committed, the finite-capacity rule makes the
    // total committed and rejected counts independent of thread interleaving. Three repeated runs
    // must produce the same observable outcome. No callback is installed under the hub mutex.
    constexpr std::size_t kPublishers = 4U;
    constexpr std::size_t kAttemptsPerPublisher = 4U;
    constexpr std::size_t kTotalAttempts = kPublishers * kAttemptsPerPublisher;
    for (std::size_t run = 0U; run < 3U; ++run) {
      ObservationHub hub;
      const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, kPublishers,
                                            ObservationOverflowPolicy::lossless_validation, {},
                                            "tap.t024.concurrent"));
      if (!expect(tap.handle.has_value(), "T024 concurrent attachment")) {
        return false;
      }
      std::atomic<std::uint64_t> committed{0U};
      std::atomic<std::uint64_t> rejected{0U};
      std::atomic<bool> consistent{true};
      std::array<std::thread, kPublishers> publishers;
      for (std::size_t index = 0U; index < publishers.size(); ++index) {
        publishers[index] = std::thread([&hub, &alpha, &committed, &rejected, &consistent, index]() {
          for (std::size_t step = 0U; step < kAttemptsPerPublisher; ++step) {
            const std::uint64_t sequence =
                static_cast<std::uint64_t>(index * kAttemptsPerPublisher + step + 1U);
            auto claim = hub.reserve(alpha);
            if (claim.status.succeeded() && claim.reservation.has_value()) {
              if (!hub
                       .commit(std::move(*claim.reservation),
                               {alpha, Timestamp(static_cast<std::int64_t>(sequence)),
                                "clock.observer", sequence, ObservationProviderOutcome::accepted})
                       .succeeded()) {
                consistent = false;
                continue;
              }
              ++committed;
            } else if (claim.status.outcome == ObservationOutcome::observation_backpressure &&
                       !claim.reservation.has_value()) {
              ++rejected;
            } else {
              consistent = false;
            }
          }
        });
      }
      for (std::thread& publisher : publishers) {
        publisher.join();
      }
      const auto snapshot = hub.snapshot(*tap.handle);
      const std::vector<ObservationRecord> records = poll_all(hub, *tap.handle, kPublishers);
      std::array<bool, kTotalAttempts> observed{};
      bool distinct = records.size() == kPublishers;
      for (const ObservationRecord& record : records) {
        if (!record.sequence().has_value() || *record.sequence() < 1U ||
            *record.sequence() > static_cast<std::uint64_t>(kTotalAttempts)) {
          distinct = false;
          continue;
        }
        const std::size_t slot = static_cast<std::size_t>(*record.sequence() - 1U);
        if (observed[slot]) {
          distinct = false;
        }
        observed[slot] = true;
      }
      valid = expect(consistent.load(), "T024 concurrent no unstable outcome") &&
              expect(committed.load() == kPublishers && rejected.load() == kTotalAttempts - kPublishers,
                     "T024 concurrent exact claim accounting") &&
              expect(snapshot.has_value() && snapshot->accepted == kPublishers &&
                         snapshot->queued == kPublishers && snapshot->dropped == 0U &&
                         snapshot->coalesced == 0U &&
                         snapshot->backpressure_rejections ==
                             static_cast<std::uint64_t>(kTotalAttempts - kPublishers) &&
                         snapshot->experiment_validity_degraded,
                     "T024 concurrent consistent counter and queue state") &&
              expect(distinct, "T024 concurrent no lost or duplicated claim") &&
              valid;
    }
  }
  return valid;
}

/**
 * @brief Prove the declared-effect to realized-status table and the validity interval semantics.
 * @details Realizes T24-TS-004 (`degraded-validity`): T024-SR-011, T024-SR-012;
 * XCOM-SW-OBS-003/-004; FR-013, FR-014, SC-004.
 * @return true only when every validity assertion holds.
 */
[[nodiscard]] bool test_observation_validity_interval_matrix() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  constexpr std::array<ObservationValidityEffect, 3U> effects{
      ObservationValidityEffect::none, ObservationValidityEffect::degrade_on_loss,
      ObservationValidityEffect::invalidate_on_loss};
  constexpr std::array<ObservationValidityState, 3U> expected{
      ObservationValidityState::valid, ObservationValidityState::degraded,
      ObservationValidityState::invalid};
  bool valid = true;
  for (std::size_t index = 0U; index < effects.size(); ++index) {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.effect", effects[index]));
    if (!expect(tap.handle.has_value(), "T024 effect-table attachment")) {
      return false;
    }
    valid = expect(emit(hub, alpha, 1U).succeeded() && emit(hub, alpha, 2U).succeeded(),
                   "T024 effect-table submissions") &&
            valid;
    const auto snapshot = hub.snapshot(*tap.handle);
    valid = expect(snapshot.has_value() && snapshot->validity_state == expected[index] &&
                       snapshot->experiment_validity_degraded ==
                           (expected[index] != ObservationValidityState::valid) &&
                       snapshot->dropped == 1U,
                   "T024 declared effect applied to a best-effort loss") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.mono",
                                          ObservationValidityEffect::degrade_on_loss));
    if (!expect(tap.handle.has_value(), "T024 monotonic attachment")) {
      return false;
    }
    static_cast<void>(emit(hub, alpha, 1U));
    static_cast<void>(emit(hub, alpha, 2U));
    const auto first = hub.snapshot(*tap.handle);
    const auto second = hub.snapshot(*tap.handle);
    const auto acknowledged = hub.acknowledge(*tap.handle);
    const auto restored = hub.snapshot(*tap.handle);
    static_cast<void>(emit(hub, alpha, 3U));
    static_cast<void>(emit(hub, alpha, 4U));
    const auto again = hub.snapshot(*tap.handle);
    valid = expect(first.has_value() &&
                       first->validity_state == ObservationValidityState::degraded,
                   "T024 loss raises degraded") &&
            expect(second.has_value() &&
                       second->validity_state == ObservationValidityState::degraded,
                   "T024 validity never lowered without acknowledgement") &&
            expect(acknowledged.succeeded() && restored.has_value() &&
                       restored->validity_state == ObservationValidityState::valid &&
                       restored->backpressure_rejections == 0U &&
                       !restored->experiment_validity_degraded,
                   "T024 acknowledgement closes the degraded interval") &&
            expect(again.has_value() &&
                       again->validity_state == ObservationValidityState::degraded,
                   "T024 a further loss degrades again") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.invalid",
                                          ObservationValidityEffect::invalidate_on_loss));
    if (!expect(tap.handle.has_value(), "T024 invalid-persistence attachment")) {
      return false;
    }
    static_cast<void>(emit(hub, alpha, 1U));
    static_cast<void>(emit(hub, alpha, 2U));
    const auto invalid = hub.snapshot(*tap.handle);
    const auto acknowledged = hub.acknowledge(*tap.handle);
    static_cast<void>(emit(hub, alpha, 3U));
    const auto still_invalid = hub.snapshot(*tap.handle);
    valid = expect(invalid.has_value() &&
                       invalid->validity_state == ObservationValidityState::invalid,
                   "T024 invalid status raised by a loss") &&
            expect(acknowledged.succeeded() && still_invalid.has_value() &&
                       still_invalid->validity_state == ObservationValidityState::invalid &&
                       still_invalid->dropped == 2U,
                   "T024 invalid status persists across acknowledgement and a further loss") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.recreate",
                                          ObservationValidityEffect::degrade_on_loss));
    if (!expect(tap.handle.has_value(), "T024 recreation attachment")) {
      return false;
    }
    static_cast<void>(emit(hub, alpha, 1U));
    static_cast<void>(emit(hub, alpha, 2U));
    const auto before = hub.snapshot(*tap.handle);
    const auto detached = hub.detach(*tap.handle);
    const auto recreated = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                                ObservationOverflowPolicy::drop_newest, {},
                                                "tap.t024.recreate",
                                                ObservationValidityEffect::degrade_on_loss));
    const auto fresh = hub.snapshot(*recreated.handle);
    const auto stale = hub.snapshot(*tap.handle);
    valid = expect(before.has_value() &&
                       before->validity_state == ObservationValidityState::degraded,
                   "T024 interval starts degraded") &&
            expect(detached.succeeded() && recreated.handle.has_value() &&
                       recreated.handle->generation() > tap.handle->generation(),
                   "T024 slot recreated with a new generation") &&
            expect(fresh.has_value() && fresh->validity_state == ObservationValidityState::valid &&
                       fresh->accepted == 0U && fresh->queued == 0U && fresh->dropped == 0U,
                   "T024 recreation discards the realized status and counters") &&
            expect(!stale.has_value(), "T024 old generation no longer authenticates") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::lossless_validation, {},
                                          "tap.t024.least", ObservationValidityEffect::none));
    if (!expect(tap.handle.has_value(), "T024 at-least-degraded attachment")) {
      return false;
    }
    auto held = hub.reserve(alpha);
    const auto blocked = hub.reserve(alpha);
    const auto snapshot = hub.snapshot(*tap.handle);
    const auto cancelled = hub.cancel(std::move(*held.reservation));
    valid = expect(held.status.succeeded() && held.reservation.has_value(),
                   "T024 at-least-degraded held claim") &&
            expect(blocked.status.outcome == ObservationOutcome::observation_backpressure,
                   "T024 at-least-degraded backpressure") &&
            expect(snapshot.has_value() &&
                       snapshot->validity_state == ObservationValidityState::degraded &&
                       snapshot->experiment_validity_degraded &&
                       snapshot->backpressure_rejections == 1U,
                   "T024 lossless realizes at least degraded under none") &&
            expect(cancelled.succeeded(), "T024 at-least-degraded claim released") &&
            valid;
  }
  return valid;
}

/**
 * @brief Prove detach/ownership semantics and that detach discards only its own records.
 * @details Realizes T24-TS-005 (`safe-detach`): T024-SR-013; XCOM-SW-OBS-004; FR-009, FR-014,
 * SC-005.
 * @return true only when every detach and ownership assertion holds.
 */
[[nodiscard]] bool test_observation_safe_detach_matrix() {
  const std::array<std::byte, 4U> bytes{};
  const CommunicationItem alpha = make_item(bytes, "route.alpha");
  ObservationHub hub;
  ObservationHub foreign_hub;
  const auto a = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                      ObservationOverflowPolicy::drop_newest, {}, "tap.t024.detach.a"));
  const auto b = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                      ObservationOverflowPolicy::drop_newest, {}, "tap.t024.detach.b"));
  if (!expect(a.handle.has_value() && b.handle.has_value(), "T024 detach attachment")) {
    return false;
  }
  static_cast<void>(emit(hub, alpha, 1U));
  static_cast<void>(emit(hub, alpha, 2U));
  const auto detached_a = hub.detach(*a.handle);
  const auto a_snapshot = hub.snapshot(*a.handle);
  const auto a_poll = hub.poll(*a.handle);
  const auto b_snapshot = hub.snapshot(*b.handle);
  const auto b_record = hub.poll(*b.handle);
  const auto duplicate_a = hub.detach(*a.handle);
  bool valid = expect(detached_a.succeeded(), "T024 detach accepted") &&
               expect(!a_snapshot.has_value(), "T024 detached snapshot absent") &&
               expect(a_poll.status.outcome == ObservationOutcome::invalid_tap_handle,
                      "T024 detached poll rejected") &&
               expect(b_snapshot.has_value() && b_snapshot->queued == 2U &&
                          b_snapshot->accepted == 2U && b_snapshot->dropped == 0U,
                      "T024 detach discards only its own records") &&
               expect(b_record.record.has_value() && b_record.record->sequence().has_value() &&
                          *b_record.record->sequence() == 1U,
                      "T024 other tap authenticates and keeps FIFO order") &&
               expect(duplicate_a.outcome == ObservationOutcome::tap_closed,
                      "T024 repeated close returns tap_closed");
  const auto c = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                      ObservationOverflowPolicy::lossless_validation, {},
                                      "tap.t024.detach.c"));
  if (!expect(c.handle.has_value(), "T024 claimed-tap attachment")) {
    return false;
  }
  auto held = hub.reserve(alpha);
  const auto busy = hub.detach(*c.handle);
  const auto claimed = hub.snapshot(*c.handle);
  const auto cancelled = hub.cancel(std::move(*held.reservation));
  const auto detached_c = hub.detach(*c.handle);
  valid = expect(busy.outcome == ObservationOutcome::tap_busy, "T024 claimed detach is busy") &&
          expect(claimed.has_value() && claimed->queued == 0U &&
                     claimed->validity_state == ObservationValidityState::valid,
                 "T024 claimed tap state untouched") &&
          expect(cancelled.succeeded() && detached_c.succeeded(),
                 "T024 detach succeeds after the claim is released") &&
          valid;
  const auto foreign = foreign_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                                    ObservationOverflowPolicy::drop_newest, {},
                                                    "tap.t024.detach.f"));
  if (!expect(foreign.handle.has_value(), "T024 foreign attachment")) {
    return false;
  }
  const auto foreign_detach = hub.detach(*foreign.handle);
  const auto foreign_here = hub.snapshot(*foreign.handle);
  const auto foreign_there = foreign_hub.snapshot(*foreign.handle);
  valid = expect(foreign_detach.outcome == ObservationOutcome::invalid_tap_handle,
                 "T024 foreign detach rejected") &&
          expect(!foreign_here.has_value(), "T024 foreign handle absent at this hub") &&
          expect(foreign_there.has_value(), "T024 foreign slot unchanged") &&
          valid;
  const auto recreated = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                              ObservationOverflowPolicy::drop_newest, {},
                                              "tap.t024.detach.a"));
  const auto fresh = hub.snapshot(*recreated.handle);
  const auto stale_detach = hub.detach(*a.handle);
  valid = expect(recreated.handle.has_value() &&
                     recreated.handle->generation() > a.handle->generation(),
                 "T024 recreated generation is newer") &&
          expect(fresh.has_value() && fresh->validity_state == ObservationValidityState::valid &&
                     fresh->accepted == 0U && fresh->queued == 0U && fresh->dropped == 0U,
                 "T024 recreated generation starts clean") &&
          expect(stale_detach.outcome == ObservationOutcome::invalid_tap_handle,
                 "T024 stale handle rejected after recreation") &&
          valid;
  return valid;
}

/**
 * @brief Prove the complete, self-describing, provider-neutral normalized record for every dimension.
 * @details Realizes T24-TS-006 (`metadata-only-zero-payload` normalized record): T024-SR-015,
 * T024-SR-016; XCOM-SW-OBS-005; FR-023.
 * @return true only when every normalized-record and value-ownership assertion holds.
 */
[[nodiscard]] bool test_observation_normalized_record_matrix() {
  const std::array<std::byte, 4U> source{std::byte{1}, std::byte{2}, std::byte{3}, std::byte{4}};
  constexpr std::array<OriginKind, 3U> origins{OriginKind::component, OriginKind::replay,
                                               OriginKind::validation_tool};
  constexpr std::array<ObservationProviderOutcome, 3U> outcomes{
      ObservationProviderOutcome::not_attempted, ObservationProviderOutcome::accepted,
      ObservationProviderOutcome::rejected};
  bool valid = true;
  for (const ObservationProviderOutcome outcome : outcomes) {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U,
                                          kMaximumObservationRecordsPerTap,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.norm"));
    if (!expect(tap.handle.has_value(), "T024 normalized attachment")) {
      return false;
    }
    std::uint64_t sequence = 0U;
    for (const InteractionKind family : kT024Families) {
      for (const OriginKind origin : origins) {
        ++sequence;
        valid = expect(emit(hub,
                            make_item(source, "route.alpha", "provider.alpha", origin, family, 4U),
                            sequence, outcome)
                           .succeeded(),
                       "T024 normalized publication") &&
                valid;
      }
    }
    const auto batch = hub.snapshot(*tap.handle);
    valid = expect(batch.has_value() && batch->accepted == 12U && batch->queued == 12U,
                   "T024 normalized batch retained exactly once") &&
            valid;
    sequence = 0U;
    for (const InteractionKind family : kT024Families) {
      for (const OriginKind origin : origins) {
        ++sequence;
        const auto pulled = hub.poll(*tap.handle);
        valid = expect(pulled.record.has_value(), "T024 normalized record pulled exactly once") &&
                expect_metadata_record(*pulled.record, family, 4U, sequence, "tap.t024.norm", origin,
                                       outcome) &&
                valid;
      }
    }
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 4U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.owner"));
    if (!expect(tap.handle.has_value(), "T024 value-ownership attachment")) {
      return false;
    }
    const CommunicationItem item = make_item(source, "route.alpha", "provider.alpha",
                                             OriginKind::component, InteractionKind::message_event,
                                             4U);
    static_cast<void>(emit(hub, item, 1U));
    const auto pulled = hub.poll(*tap.handle);
    if (!expect(pulled.record.has_value(), "T024 value-ownership record")) {
      return false;
    }
    const ObservationRecord copy = *pulled.record;
    const ObservationRecordCounters before = copy.counters();
    static_cast<void>(emit(hub, item, 2U));
    static_cast<void>(emit(hub, item, 3U));
    valid = expect(copy.sequence().has_value() && *copy.sequence() == 1U,
                   "T024 value-owned sequence independent of later mutation") &&
            expect(copy.route_id().value() == "route.alpha", "T024 value-owned route") &&
            expect(copy.source_payload_size() == 4U, "T024 value-owned source size") &&
            expect(copy.counters().queued == before.queued &&
                       copy.counters().accepted == before.accepted &&
                       copy.counters().dropped == before.dropped &&
                       copy.counters().coalesced == before.coalesced,
                   "T024 value-owned counter projection") &&
            valid;
    // Provider neutrality (T024-SR-016, ADR-0019): ObservationRecord exposes only the provider-neutral
    // normalized fields asserted above; no Argus-side or provider-specific accessor is introduced or
    // required by the accepted observation surface.
  }
  return valid;
}

/**
 * @brief Prove normalized edge values: absent sequence, distinct clock, zero payload, and counters.
 * @details Realizes T24-TS-007 (`controlled-payload-view` edge values): T024-SR-002, T024-SR-015;
 * XCOM-SW-OBS-005; FR-023.
 * @return true only when every edge-value assertion holds.
 */
[[nodiscard]] bool test_observation_record_edge_value_matrix() {
  const std::array<std::byte, 4U> source{std::byte{5}, std::byte{6}, std::byte{7}, std::byte{8}};
  bool valid = true;

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.edge"));
    const CommunicationItem item =
        make_item(source, "route.alpha", "provider.alpha", OriginKind::replay,
                  InteractionKind::service_request, 4U);
    const auto committed = emit_absent_sequence(hub, item, 77);
    const auto pulled = hub.poll(*tap.handle);
    valid = expect(committed.succeeded(), "T024 absent-sequence commit") &&
            expect(pulled.record.has_value() && !pulled.record->sequence().has_value(),
                   "T024 absent sequence is not defaulted") &&
            expect(pulled.record->contract_id().value() == "contract.alpha" &&
                       pulled.record->route_id().value() == "route.alpha" &&
                       pulled.record->provider_id().value() == "provider.alpha" &&
                       pulled.record->interaction_kind() == InteractionKind::service_request &&
                       pulled.record->origin() == OriginKind::replay,
                   "T024 absent-sequence fields preserved") &&
            expect(pulled.record->observation_timestamp().nanoseconds() == 77,
                   "T024 absent-sequence observation time preserved") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 2U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.edge"));
    const CommunicationItem item = make_item(source);
    auto reserved = hub.reserve(item);
    const auto committed = hub.commit(
        std::move(*reserved.reservation),
        {item, Timestamp(1234), "clock.distinct", 5U, ObservationProviderOutcome::accepted});
    const auto pulled = hub.poll(*tap.handle);
    valid = expect(committed.succeeded() && pulled.record.has_value(),
                   "T024 distinct observation clock commit") &&
            expect(pulled.record->source_timestamp().nanoseconds() == 42 &&
                       pulled.record->source_clock_domain().value() == "clock.source",
                   "T024 source clock preserved") &&
            expect(pulled.record->observation_timestamp().nanoseconds() == 1234 &&
                       pulled.record->observation_clock_domain().value() == "clock.distinct",
                   "T024 observation clock preserved independently") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.edge"));
    const CommunicationItem item =
        make_item(source, "route.alpha", "provider.alpha", OriginKind::component,
                  InteractionKind::message_event, 0U);
    const auto emitted = emit(hub, item, 1U);
    const auto pulled = hub.poll(*tap.handle);
    valid = expect(emitted.succeeded() && pulled.record.has_value() &&
                       pulled.record->source_payload_size() == 0U &&
                       pulled.record->payload_bytes().empty() &&
                       pulled.record->payload_view_state() == PayloadViewState::omitted,
                   "T024 zero-length payload metadata view") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto fresh = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                            ObservationOverflowPolicy::drop_newest, {},
                                            "tap.t024.count"));
    const CommunicationItem alpha = make_item(source, "route.alpha");
    static_cast<void>(emit(hub, alpha, 1U));
    const auto first = hub.poll(*fresh.handle);
    valid = expect(first.record.has_value() && first.record->counters().queued == 1U &&
                       first.record->counters().accepted == 1U &&
                       first.record->counters().dropped == 0U &&
                       first.record->counters().coalesced == 0U,
                   "T024 retention-time counter projection") &&
            valid;

    ObservationHub coalesce_hub;
    const auto coalesce =
        coalesce_hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U, 1U,
                                      ObservationOverflowPolicy::coalesce_latest, {},
                                      "tap.t024.count"));
    static_cast<void>(emit(coalesce_hub, alpha, 1U));
    static_cast<void>(emit(coalesce_hub, alpha, 2U));
    const auto replaced = coalesce_hub.poll(*coalesce.handle);
    valid = expect(replaced.record.has_value() && replaced.record->counters().coalesced == 1U &&
                       replaced.record->counters().queued == 1U &&
                       replaced.record->sequence().has_value() &&
                       *replaced.record->sequence() == 2U,
                   "T024 coalesced replacement counter projection") &&
            valid;
  }

  {
    ObservationHub hub;
    const auto tap = hub.attach(make_spec(ObservationPayloadMode::metadata_only, 0U,
                                          kMaximumObservationRecordsPerTap,
                                          ObservationOverflowPolicy::drop_newest, {},
                                          "tap.t024.family"));
    if (!expect(tap.handle.has_value(), "T024 family attachment")) {
      return false;
    }
    std::uint64_t sequence = 0U;
    for (const InteractionKind family : kT024Families) {
      ++sequence;
      static_cast<void>(emit(hub,
                             make_item(source, "route.alpha", "provider.alpha",
                                       OriginKind::component, family, 4U),
                             sequence));
    }
    for (const InteractionKind family : kT024Families) {
      const auto pulled = hub.poll(*tap.handle);
      valid = expect(pulled.record.has_value() && pulled.record->interaction_kind() == family,
                     "T024 family preserved for every record") &&
              valid;
    }
  }
  return valid;
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
                 test_synthetic_sink_concurrency() && test_synthetic_sink_visible_counters() &&
                 test_synthetic_sink_disconnect_isolation() &&
                 test_synthetic_sink_failure_isolation() &&
                 test_synthetic_sink_blocking_isolation() &&
                 test_observation_metadata_and_payload_view_matrix() &&
                 test_observation_ordering_matrix() &&
                 test_observation_saturation_bound_matrix() &&
                 test_observation_validity_interval_matrix() &&
                 test_observation_safe_detach_matrix() &&
                 test_observation_normalized_record_matrix() &&
                 test_observation_record_edge_value_matrix()
             ? 0
             : 1;
}
