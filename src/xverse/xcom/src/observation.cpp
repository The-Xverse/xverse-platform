/**
 * @file observation.cpp
 * @brief Fixed-storage implementation of the provider-neutral observation boundary.
 * @ownership Hub slots retain value-owned policies and records only.
 * @lifetime All returned records/snapshots are copied after serialized state access.
 * @thread_safety The hub mutex guards every slot operation; no consumer callback is invoked.
 * @failure Saturation is explicit and never grows storage or performs external operations.
 * @par Traceability
 * Implements the declarations and requirement allocation documented in observation.hpp; focused
 * behavior is exercised by tests/xcom/observation/core/unit_tests.cpp.
 */

#include "xverse/xcom/observation.hpp"

#include <algorithm>
#include <limits>

namespace xverse::xcom {
namespace {

[[nodiscard]] bool known_payload_mode(const ObservationPayloadMode mode) noexcept {
  switch (mode) {
    case ObservationPayloadMode::metadata_only:
    case ObservationPayloadMode::bounded_prefix:
    case ObservationPayloadMode::redacted:
      return true;
  }
  return false;
}

[[nodiscard]] bool known_overflow_policy(const ObservationOverflowPolicy policy) noexcept {
  switch (policy) {
    case ObservationOverflowPolicy::drop_newest:
    case ObservationOverflowPolicy::coalesce_latest:
    case ObservationOverflowPolicy::lossless_validation:
      return true;
  }
  return false;
}

[[nodiscard]] std::optional<Identity> optional_identity(const std::string_view value) noexcept {
  if (value.empty()) {
    return std::optional<Identity>{};
  }
  return Identity::create(value);
}

[[nodiscard]] bool matches(const std::optional<Identity>& constraint,
                           const Identity& value) noexcept {
  return !constraint.has_value() || *constraint == value;
}

}  // namespace

std::atomic<std::uint64_t> ObservationHub::next_hub_instance_id_{1U};

std::string_view to_string(const ObservationOutcome outcome) noexcept {
  switch (outcome) {
    case ObservationOutcome::accepted:
      return "accepted";
    case ObservationOutcome::invalid_argument:
      return "invalid_argument";
    case ObservationOutcome::tap_capacity_exhausted:
      return "tap_capacity_exhausted";
    case ObservationOutcome::record_capacity_exhausted:
      return "record_capacity_exhausted";
    case ObservationOutcome::invalid_tap_handle:
      return "invalid_tap_handle";
    case ObservationOutcome::tap_closed:
      return "tap_closed";
    case ObservationOutcome::observation_backpressure:
      return "observation_backpressure";
    case ObservationOutcome::no_record:
      return "no_record";
    case ObservationOutcome::sink_disconnected:
      return "sink_disconnected";
  }
  return "unknown";
}

ObservationFilter::ObservationFilter(std::optional<Identity> contract_id,
                                     std::optional<Identity> interface_id,
                                     std::optional<Identity> endpoint_id,
                                     std::optional<Identity> route_id,
                                     std::optional<Identity> provider_id,
                                     std::optional<InteractionKind> interaction_kind) noexcept
    : contract_id_(contract_id),
      interface_id_(interface_id),
      endpoint_id_(endpoint_id),
      route_id_(route_id),
      provider_id_(provider_id),
      interaction_kind_(interaction_kind) {}

std::optional<ObservationFilter> ObservationFilter::create(
    const ObservationFilterInput& input) noexcept {
  const auto contract_id = optional_identity(input.contract_id);
  const auto interface_id = optional_identity(input.interface_id);
  const auto endpoint_id = optional_identity(input.endpoint_id);
  const auto route_id = optional_identity(input.route_id);
  const auto provider_id = optional_identity(input.provider_id);
  if ((!input.contract_id.empty() && !contract_id.has_value()) ||
      (!input.interface_id.empty() && !interface_id.has_value()) ||
      (!input.endpoint_id.empty() && !endpoint_id.has_value()) ||
      (!input.route_id.empty() && !route_id.has_value()) ||
      (!input.provider_id.empty() && !provider_id.has_value())) {
    return std::nullopt;
  }
  return ObservationFilter(contract_id, interface_id, endpoint_id, route_id, provider_id,
                           input.interaction_kind);
}

bool ObservationFilter::matches(const CommunicationItem& item) const noexcept {
  return xverse::xcom::matches(contract_id_, item.contract_id()) &&
         xverse::xcom::matches(interface_id_, item.interface_id()) &&
         xverse::xcom::matches(endpoint_id_, item.endpoint_id()) &&
         xverse::xcom::matches(route_id_, item.route_id()) &&
         xverse::xcom::matches(provider_id_, item.provider_id()) &&
         (!interaction_kind_.has_value() || *interaction_kind_ == item.interaction_kind());
}

ObservationTapSpec::ObservationTapSpec(const SemanticVersion& contract_version,
                                       const ObservationFilter& filter,
                                       const ObservationPayloadMode payload_mode,
                                       const std::size_t maximum_payload_bytes,
                                       const std::size_t record_capacity,
                                       const ObservationOverflowPolicy overflow_policy) noexcept
    : contract_version_(contract_version),
      filter_(filter),
      payload_mode_(payload_mode),
      maximum_payload_bytes_(maximum_payload_bytes),
      record_capacity_(record_capacity),
      overflow_policy_(overflow_policy) {}

std::optional<ObservationTapSpec> ObservationTapSpec::create(
    const ObservationTapSpecInput& input) noexcept {
  const auto version = SemanticVersion::create(input.contract_version);
  const auto filter = ObservationFilter::create(input.filter);
  if (!version.has_value() || !filter.has_value() ||
      input.contract_version != kObservationContractVersion || !known_payload_mode(input.payload_mode) ||
      !known_overflow_policy(input.overflow_policy) || input.record_capacity == 0U ||
      input.record_capacity > kMaximumObservationRecordsPerTap) {
    return std::nullopt;
  }
  const bool prefix = input.payload_mode == ObservationPayloadMode::bounded_prefix;
  if ((prefix && (input.maximum_payload_bytes == 0U ||
                  input.maximum_payload_bytes > kMaximumObservedPayloadBytes)) ||
      (!prefix && input.maximum_payload_bytes != 0U)) {
    return std::nullopt;
  }
  return ObservationTapSpec(*version, *filter, input.payload_mode, input.maximum_payload_bytes,
                            input.record_capacity, input.overflow_policy);
}

ObservationRecord::ObservationRecord(const ObservationEvent& event,
                                     const Identity& observation_clock_domain,
                                     const ObservationPayloadMode mode,
                                     const std::size_t maximum_payload_bytes) noexcept
    : contract_id_(event.item.contract_id()),
      contract_version_(event.item.contract_version()),
      interface_id_(event.item.interface_id()),
      endpoint_id_(event.item.endpoint_id()),
      schema_id_(event.item.schema_id()),
      schema_version_(event.item.schema_version()),
      interaction_kind_(event.item.interaction_kind()),
      origin_(event.item.origin()),
      source_timestamp_(event.item.timestamp()),
      source_clock_domain_(event.item.clock_domain()),
      observation_timestamp_(event.observation_timestamp),
      observation_clock_domain_(observation_clock_domain),
      sequence_(event.sequence),
      correlation_id_(event.item.correlation_id()),
      causation_id_(event.item.causation_id()),
      route_id_(event.item.route_id()),
      provider_id_(event.item.provider_id()),
      source_payload_size_(event.item.payload().size()),
      provider_outcome_(event.provider_outcome),
      payload_view_state_(PayloadViewState::omitted) {
  if (mode == ObservationPayloadMode::redacted) {
    payload_view_state_ = PayloadViewState::redacted;
    return;
  }
  if (mode != ObservationPayloadMode::bounded_prefix) {
    return;
  }
  const auto source = event.item.payload().bytes();
  payload_size_ = std::min(source.size(), maximum_payload_bytes);
  std::copy_n(source.begin(), payload_size_, payload_bytes_.begin());
  payload_view_state_ = source.size() <= maximum_payload_bytes ? PayloadViewState::complete
                                                                 : PayloadViewState::truncated;
}

ObservationHub::ObservationHub() noexcept
    : hub_instance_id_(next_hub_instance_id_.fetch_add(1U, std::memory_order_relaxed)) {}

ObservationTapHandle ObservationHub::make_handle(const std::size_t index,
                                                  const std::uint64_t generation) const noexcept {
  return ObservationTapHandle(hub_instance_id_, static_cast<std::uint64_t>(index + 1U), generation);
}

ObservationHub::TapSlot* ObservationHub::authenticate(const ObservationTapHandle& handle) noexcept {
  if (handle.hub_instance_id() != hub_instance_id_ || handle.tap_id() == 0U ||
      handle.tap_id() > taps_.size()) {
    return nullptr;
  }
  TapSlot& slot = taps_[static_cast<std::size_t>(handle.tap_id() - 1U)];
  return slot.spec.has_value() && slot.generation == handle.generation() ? &slot : nullptr;
}

const ObservationHub::TapSlot* ObservationHub::authenticate(
    const ObservationTapHandle& handle) const noexcept {
  if (handle.hub_instance_id() != hub_instance_id_ || handle.tap_id() == 0U ||
      handle.tap_id() > taps_.size()) {
    return nullptr;
  }
  const TapSlot& slot = taps_[static_cast<std::size_t>(handle.tap_id() - 1U)];
  return slot.spec.has_value() && slot.generation == handle.generation() ? &slot : nullptr;
}

ObservationAttachResult ObservationHub::attach(const ObservationTapSpec& spec) noexcept {
  std::lock_guard lock(mutex_);
  for (std::size_t index = 0U; index < taps_.size(); ++index) {
    TapSlot& slot = taps_[index];
    if (slot.spec.has_value()) {
      continue;
    }
    if (slot.generation == std::numeric_limits<std::uint64_t>::max()) {
      return {{ObservationOutcome::tap_capacity_exhausted}, std::nullopt};
    }
    ++slot.generation;
    slot.spec.emplace(spec);
    slot.head = 0U;
    slot.size = 0U;
    slot.accepted = 0U;
    slot.dropped = 0U;
    slot.coalesced = 0U;
    slot.backpressure_rejections = 0U;
    slot.experiment_validity_degraded = false;
    return {{ObservationOutcome::accepted}, make_handle(index, slot.generation)};
  }
  return {{ObservationOutcome::tap_capacity_exhausted}, std::nullopt};
}

bool ObservationHub::has_lossless_capacity(const CommunicationItem& item) const noexcept {
  for (const TapSlot& slot : taps_) {
    if (slot.spec.has_value() &&
        slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation &&
        slot.spec->filter().matches(item) && slot.size == slot.spec->record_capacity()) {
      return false;
    }
  }
  return true;
}

ObservationStatus ObservationHub::preflight(const CommunicationItem& item) noexcept {
  std::lock_guard lock(mutex_);
  if (has_lossless_capacity(item)) {
    return {ObservationOutcome::accepted};
  }
  for (TapSlot& slot : taps_) {
    if (slot.spec.has_value() &&
        slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation &&
        slot.spec->filter().matches(item) && slot.size == slot.spec->record_capacity()) {
      ++slot.backpressure_rejections;
      slot.experiment_validity_degraded = true;
    }
  }
  return {ObservationOutcome::observation_backpressure};
}

ObservationStatus ObservationHub::retain(TapSlot& slot, const ObservationEvent& event) noexcept {
  const ObservationTapSpec& spec = *slot.spec;
  const auto observation_clock_domain = Identity::create(event.observation_clock_domain);
  if (!observation_clock_domain.has_value()) {
    return {ObservationOutcome::invalid_argument};
  }
  if (slot.size == spec.record_capacity()) {
    if (spec.overflow_policy() == ObservationOverflowPolicy::drop_newest) {
      ++slot.dropped;
      return {ObservationOutcome::accepted};
    }
    if (spec.overflow_policy() == ObservationOverflowPolicy::coalesce_latest) {
      const std::size_t latest = (slot.head + slot.size - 1U) % spec.record_capacity();
      const ObservationRecord record(event, *observation_clock_domain, spec.payload_mode(),
                                     spec.maximum_payload_bytes());
      slot.records[latest].emplace(record);
      ++slot.coalesced;
      return {ObservationOutcome::accepted};
    }
    ++slot.backpressure_rejections;
    slot.experiment_validity_degraded = true;
    return {ObservationOutcome::observation_backpressure};
  }
  const std::size_t tail = (slot.head + slot.size) % spec.record_capacity();
  const ObservationRecord record(event, *observation_clock_domain, spec.payload_mode(),
                                 spec.maximum_payload_bytes());
  slot.records[tail].emplace(record);
  ++slot.size;
  ++slot.accepted;
  return {ObservationOutcome::accepted};
}

ObservationStatus ObservationHub::publish(const ObservationEvent& event) noexcept {
  if (!Identity::create(event.observation_clock_domain).has_value()) {
    return {ObservationOutcome::invalid_argument};
  }
  std::lock_guard lock(mutex_);
  if (!has_lossless_capacity(event.item)) {
    for (TapSlot& slot : taps_) {
      if (slot.spec.has_value() &&
          slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation &&
          slot.spec->filter().matches(event.item) && slot.size == slot.spec->record_capacity()) {
        ++slot.backpressure_rejections;
        slot.experiment_validity_degraded = true;
      }
    }
    return {ObservationOutcome::observation_backpressure};
  }
  for (TapSlot& slot : taps_) {
    if (slot.spec.has_value() && slot.spec->filter().matches(event.item)) {
      const ObservationStatus status = retain(slot, event);
      if (!status.succeeded()) {
        return status;
      }
    }
  }
  return {ObservationOutcome::accepted};
}

ObservationPollResult ObservationHub::poll(const ObservationTapHandle& handle) noexcept {
  std::lock_guard lock(mutex_);
  TapSlot* slot = authenticate(handle);
  if (slot == nullptr) {
    return {{ObservationOutcome::invalid_tap_handle}, std::nullopt};
  }
  if (slot->size == 0U) {
    return {{ObservationOutcome::no_record}, std::nullopt};
  }
  std::optional<ObservationRecord>& stored = slot->records[slot->head];
  ObservationRecord result(*stored);
  stored.reset();
  slot->head = (slot->head + 1U) % slot->spec->record_capacity();
  --slot->size;
  return {{ObservationOutcome::accepted}, result};
}

std::optional<ObservationSnapshot> ObservationHub::snapshot(
    const ObservationTapHandle& handle) const noexcept {
  std::lock_guard lock(mutex_);
  const TapSlot* slot = authenticate(handle);
  if (slot == nullptr) {
    return std::nullopt;
  }
  return ObservationSnapshot{handle, slot->size, slot->accepted, slot->dropped, slot->coalesced,
                             slot->backpressure_rejections, slot->experiment_validity_degraded};
}

ObservationStatus ObservationHub::acknowledge(const ObservationTapHandle& handle) noexcept {
  std::lock_guard lock(mutex_);
  TapSlot* slot = authenticate(handle);
  if (slot == nullptr) {
    return {ObservationOutcome::invalid_tap_handle};
  }
  slot->experiment_validity_degraded = false;
  return {ObservationOutcome::accepted};
}

ObservationStatus ObservationHub::detach(const ObservationTapHandle& handle) noexcept {
  std::lock_guard lock(mutex_);
  if (handle.hub_instance_id() != hub_instance_id_ || handle.tap_id() == 0U ||
      handle.tap_id() > taps_.size()) {
    return {ObservationOutcome::invalid_tap_handle};
  }
  TapSlot& slot = taps_[static_cast<std::size_t>(handle.tap_id() - 1U)];
  if (!slot.spec.has_value() && slot.generation == handle.generation()) {
    return {ObservationOutcome::tap_closed};
  }
  if (!slot.spec.has_value() || slot.generation != handle.generation()) {
    return {ObservationOutcome::invalid_tap_handle};
  }
  for (std::optional<ObservationRecord>& record : slot.records) {
    record.reset();
  }
  slot.spec.reset();
  slot.head = 0U;
  slot.size = 0U;
  return {ObservationOutcome::accepted};
}

SyntheticObservationSink::SyntheticObservationSink(ObservationHub& hub,
                                                   const ObservationTapHandle& handle) noexcept
    : hub_(&hub), handle_(handle) {}

ObservationStatus SyntheticObservationSink::connect() noexcept {
  if (!hub_->snapshot(handle_).has_value()) {
    connected_ = false;
    return {ObservationOutcome::invalid_tap_handle};
  }
  connected_ = true;
  return {ObservationOutcome::accepted};
}

ObservationPollResult SyntheticObservationSink::pull() noexcept {
  if (!connected_) {
    return {{ObservationOutcome::sink_disconnected}, std::nullopt};
  }
  return hub_->poll(handle_);
}

}  // namespace xverse::xcom
