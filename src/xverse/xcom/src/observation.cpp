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
 * T023 maintains the synthetic sink's visible SyntheticSinkCounters projection on the actual
 * disconnect/no_record/invalid_tap_handle outcomes and re-validates the copied exact handle in
 * connect(); the accepted T021/T022 declaration, retention, and validity behavior is unchanged
 * (XCOM-SW-OBS-004).
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

[[nodiscard]] bool known_validity_effect(const ObservationValidityEffect effect) noexcept {
  switch (effect) {
    case ObservationValidityEffect::none:
    case ObservationValidityEffect::degrade_on_loss:
    case ObservationValidityEffect::invalidate_on_loss:
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

[[nodiscard]] bool has_coalescing_key(const ObservationRecord& record,
                                      const CommunicationItem& item) noexcept {
  return record.contract_id() == item.contract_id() &&
         record.contract_version() == item.contract_version() &&
         record.interface_id() == item.interface_id() && record.endpoint_id() == item.endpoint_id() &&
         record.schema_id() == item.schema_id() && record.schema_version() == item.schema_version() &&
         record.interaction_kind() == item.interaction_kind() && record.origin() == item.origin() &&
         record.route_id() == item.route_id() && record.provider_id() == item.provider_id();
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
    case ObservationOutcome::invalid_reservation:
      return "invalid_reservation";
    case ObservationOutcome::tap_closed:
      return "tap_closed";
    case ObservationOutcome::tap_busy:
      return "tap_busy";
    case ObservationOutcome::observation_backpressure:
      return "observation_backpressure";
    case ObservationOutcome::no_record:
      return "no_record";
    case ObservationOutcome::sink_disconnected:
      return "sink_disconnected";
  }
  return "unknown";
}

std::string_view to_string(const ObservationValidityEffect effect) noexcept {
  switch (effect) {
    case ObservationValidityEffect::none:
      return "none";
    case ObservationValidityEffect::degrade_on_loss:
      return "degrade-on-loss";
    case ObservationValidityEffect::invalidate_on_loss:
      return "invalidate-on-loss";
  }
  return "unknown";
}

std::string_view to_string(const ObservationValidityState state) noexcept {
  switch (state) {
    case ObservationValidityState::valid:
      return "valid";
    case ObservationValidityState::degraded:
      return "degraded";
    case ObservationValidityState::invalid:
      return "invalid";
  }
  return "unknown";
}

ObservationFilter::ObservationFilter(std::optional<Identity> contract_id,
                                     std::optional<Identity> interface_id,
                                     std::optional<Identity> endpoint_id,
                                     std::optional<Identity> route_id,
                                     std::optional<Identity> provider_id,
                                     std::optional<InteractionKind> interaction_kind,
                                     std::optional<OriginKind> origin) noexcept
    : contract_id_(contract_id),
      interface_id_(interface_id),
      endpoint_id_(endpoint_id),
      route_id_(route_id),
      provider_id_(provider_id),
      interaction_kind_(interaction_kind),
      origin_(origin) {}

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
                           input.interaction_kind, input.origin);
}

bool ObservationFilter::matches(const CommunicationItem& item) const noexcept {
  return xverse::xcom::matches(contract_id_, item.contract_id()) &&
         xverse::xcom::matches(interface_id_, item.interface_id()) &&
         xverse::xcom::matches(endpoint_id_, item.endpoint_id()) &&
         xverse::xcom::matches(route_id_, item.route_id()) &&
         xverse::xcom::matches(provider_id_, item.provider_id()) &&
         (!interaction_kind_.has_value() || *interaction_kind_ == item.interaction_kind()) &&
         (!origin_.has_value() || *origin_ == item.origin());
}

ObservationTapSpec::ObservationTapSpec(const SemanticVersion& contract_version,
                                       const Identity& declared_tap_id,
                                       const ObservationFilter& filter,
                                       const ObservationPayloadMode payload_mode,
                                       const std::size_t maximum_payload_bytes,
                                       const std::size_t record_capacity,
                                       const ObservationOverflowPolicy overflow_policy,
                                       const ObservationValidityEffect validity_effect) noexcept
    : contract_version_(contract_version),
      declared_tap_id_(declared_tap_id),
      filter_(filter),
      payload_mode_(payload_mode),
      maximum_payload_bytes_(maximum_payload_bytes),
      record_capacity_(record_capacity),
      overflow_policy_(overflow_policy),
      validity_effect_(validity_effect) {}

std::optional<ObservationTapSpec> ObservationTapSpec::create(
    const ObservationTapSpecInput& input) noexcept {
  const auto version = SemanticVersion::create(input.contract_version);
  if (!version.has_value() || input.contract_version != kObservationContractVersion) {
    return std::nullopt;
  }
  const auto declared_tap_id = Identity::create(input.tap_id);
  if (!declared_tap_id.has_value()) {
    return std::nullopt;
  }
  const auto filter = ObservationFilter::create(input.filter);
  if (!filter.has_value() || !known_payload_mode(input.payload_mode) ||
      !known_overflow_policy(input.overflow_policy) || input.record_capacity == 0U ||
      input.record_capacity > kMaximumObservationRecordsPerTap ||
      !known_validity_effect(input.validity_effect)) {
    return std::nullopt;
  }
  const bool prefix = input.payload_mode == ObservationPayloadMode::bounded_prefix;
  if ((prefix && (input.maximum_payload_bytes == 0U ||
                  input.maximum_payload_bytes > kMaximumObservedPayloadBytes)) ||
      (!prefix && input.maximum_payload_bytes != 0U)) {
    return std::nullopt;
  }
  return ObservationTapSpec(*version, *declared_tap_id, *filter, input.payload_mode,
                            input.maximum_payload_bytes, input.record_capacity,
                            input.overflow_policy, input.validity_effect);
}

ObservationRecord::ObservationRecord(const ObservationEvent& event,
                                     const Identity& observation_clock_domain,
                                     const ObservationPayloadMode mode,
                                     const std::size_t maximum_payload_bytes,
                                     const Identity& tap_id,
                                     const ObservationRecordCounters& counters) noexcept
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
      payload_view_state_(PayloadViewState::omitted),
      tap_id_(tap_id),
      counters_(counters) {
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

ObservationReservation::ObservationReservation(
    ObservationHub& hub, const std::uint64_t hub_instance_id, const std::uint64_t reservation_id,
    const CommunicationItem& item,
    const std::array<std::uint64_t, kMaximumObservationTaps>& tap_generations) noexcept
    : hub_(&hub),
      hub_instance_id_(hub_instance_id),
      reservation_id_(reservation_id),
      item_(item),
      tap_generations_(tap_generations) {}

ObservationReservation::ObservationReservation(ObservationReservation&& other) noexcept
    : hub_(other.hub_),
      hub_instance_id_(other.hub_instance_id_),
      reservation_id_(other.reservation_id_),
      item_(other.item_),
      tap_generations_(other.tap_generations_),
      active_(other.active_) {
  other.hub_ = nullptr;
  other.active_ = false;
}

ObservationReservation::~ObservationReservation() {
  if (active_ && hub_ != nullptr) {
    hub_->cancel_from_destructor(*this);
  }
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
    slot.reserved_lossless = 0U;
    slot.active_claims = 0U;
    slot.realized_validity = ObservationValidityState::valid;
    return {{ObservationOutcome::accepted}, make_handle(index, slot.generation)};
  }
  return {{ObservationOutcome::tap_capacity_exhausted}, std::nullopt};
}

ObservationReserveResult ObservationHub::reserve(const CommunicationItem& item) noexcept {
  std::lock_guard lock(mutex_);
  bool unavailable = false;
  for (TapSlot& slot : taps_) {
    if (slot.spec.has_value() &&
        slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation &&
        slot.spec->filter().matches(item) &&
        slot.size + slot.reserved_lossless >= slot.spec->record_capacity()) {
      ++slot.backpressure_rejections;
      raise_realized_validity(slot, true);
      unavailable = true;
    }
  }
  if (unavailable) {
    return {{ObservationOutcome::observation_backpressure}, std::nullopt};
  }

  std::array<std::uint64_t, kMaximumObservationTaps> tap_generations{};
  for (std::size_t index = 0U; index < taps_.size(); ++index) {
    TapSlot& slot = taps_[index];
    if (!slot.spec.has_value() || !slot.spec->filter().matches(item)) {
      continue;
    }
    tap_generations[index] = slot.generation;
    ++slot.active_claims;
    if (slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation) {
      ++slot.reserved_lossless;
    }
  }
  const std::uint64_t reservation_id = next_reservation_id_++;
  ObservationReservation reservation(*this, hub_instance_id_, reservation_id, item, tap_generations);
  return {{ObservationOutcome::accepted},
          std::optional<ObservationReservation>(std::move(reservation))};
}

void ObservationHub::raise_realized_validity(TapSlot& slot, const bool required_loss) noexcept {
  ObservationValidityState target = ObservationValidityState::valid;
  switch (slot.spec->validity_effect()) {
    case ObservationValidityEffect::none:
      target = ObservationValidityState::valid;
      break;
    case ObservationValidityEffect::degrade_on_loss:
      target = ObservationValidityState::degraded;
      break;
    case ObservationValidityEffect::invalidate_on_loss:
      target = ObservationValidityState::invalid;
      break;
  }
  if (required_loss &&
      static_cast<std::uint8_t>(target) <
          static_cast<std::uint8_t>(ObservationValidityState::degraded)) {
    target = ObservationValidityState::degraded;
  }
  if (static_cast<std::uint8_t>(target) > static_cast<std::uint8_t>(slot.realized_validity)) {
    slot.realized_validity = target;
  }
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
      raise_realized_validity(slot, false);
      return {ObservationOutcome::accepted};
    }
    if (spec.overflow_policy() == ObservationOverflowPolicy::coalesce_latest) {
      for (std::size_t offset = 0U; offset < slot.size; ++offset) {
        const std::size_t candidate =
            (slot.head + slot.size - 1U - offset) % spec.record_capacity();
        if (has_coalescing_key(*slot.records[candidate], event.item)) {
          ++slot.coalesced;
          const ObservationRecord record(event, *observation_clock_domain, spec.payload_mode(),
                                         spec.maximum_payload_bytes(), spec.declared_tap_id(),
                                         {slot.size, slot.accepted, slot.dropped, slot.coalesced});
          slot.records[candidate].emplace(record);
          raise_realized_validity(slot, false);
          return {ObservationOutcome::accepted};
        }
      }
      ++slot.dropped;
      raise_realized_validity(slot, false);
      return {ObservationOutcome::accepted};
    }
    ++slot.backpressure_rejections;
    raise_realized_validity(slot, true);
    return {ObservationOutcome::observation_backpressure};
  }
  const std::size_t tail = (slot.head + slot.size) % spec.record_capacity();
  ++slot.size;
  ++slot.accepted;
  const ObservationRecord record(event, *observation_clock_domain, spec.payload_mode(),
                                 spec.maximum_payload_bytes(), spec.declared_tap_id(),
                                 {slot.size, slot.accepted, slot.dropped, slot.coalesced});
  slot.records[tail].emplace(record);
  return {ObservationOutcome::accepted};
}

void ObservationHub::release_claims(ObservationReservation& reservation) noexcept {
  for (std::size_t index = 0U; index < taps_.size(); ++index) {
    if (reservation.tap_generations_[index] == 0U) {
      continue;
    }
    TapSlot& slot = taps_[index];
    if (slot.spec.has_value() && slot.generation == reservation.tap_generations_[index]) {
      --slot.active_claims;
      if (slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation) {
        --slot.reserved_lossless;
      }
    }
  }
  reservation.active_ = false;
  reservation.hub_ = nullptr;
}

void ObservationHub::cancel_from_destructor(ObservationReservation& reservation) noexcept {
  std::lock_guard lock(mutex_);
  if (reservation.active_ && reservation.hub_ == this &&
      reservation.hub_instance_id_ == hub_instance_id_) {
    release_claims(reservation);
  }
}

ObservationStatus ObservationHub::cancel(ObservationReservation&& reservation) noexcept {
  std::lock_guard lock(mutex_);
  if (!reservation.active_ || reservation.hub_ != this ||
      reservation.hub_instance_id_ != hub_instance_id_ || reservation.reservation_id_ == 0U) {
    return {ObservationOutcome::invalid_reservation};
  }
  release_claims(reservation);
  return {ObservationOutcome::accepted};
}

ObservationStatus ObservationHub::commit(ObservationReservation&& reservation,
                                         const ObservationEvent& event) noexcept {
  if (!reservation.active_ || reservation.hub_ != this ||
      reservation.hub_instance_id_ != hub_instance_id_ || reservation.reservation_id_ == 0U) {
    return {ObservationOutcome::invalid_reservation};
  }
  if (!(reservation.item_ == event.item) ||
      !Identity::create(event.observation_clock_domain).has_value()) {
    return {ObservationOutcome::invalid_argument};
  }
  std::lock_guard lock(mutex_);
  for (std::size_t index = 0U; index < taps_.size(); ++index) {
    if (reservation.tap_generations_[index] == 0U) {
      continue;
    }
    const TapSlot& slot = taps_[index];
    if (!slot.spec.has_value() || slot.generation != reservation.tap_generations_[index] ||
        slot.active_claims == 0U ||
        (slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation &&
         slot.reserved_lossless == 0U)) {
      return {ObservationOutcome::invalid_reservation};
    }
  }
  for (std::size_t index = 0U; index < taps_.size(); ++index) {
    if (reservation.tap_generations_[index] == 0U) {
      continue;
    }
    TapSlot& slot = taps_[index];
    --slot.active_claims;
    if (slot.spec->overflow_policy() == ObservationOverflowPolicy::lossless_validation) {
      --slot.reserved_lossless;
    }
    static_cast<void>(retain(slot, event));
  }
  reservation.active_ = false;
  reservation.hub_ = nullptr;
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
  return ObservationSnapshot{handle,
                             slot->size,
                             slot->accepted,
                             slot->dropped,
                             slot->coalesced,
                             slot->backpressure_rejections,
                             slot->realized_validity != ObservationValidityState::valid,
                             slot->spec->declared_tap_id(),
                             slot->spec->validity_effect(),
                             slot->realized_validity};
}

ObservationStatus ObservationHub::acknowledge(const ObservationTapHandle& handle) noexcept {
  std::lock_guard lock(mutex_);
  TapSlot* slot = authenticate(handle);
  if (slot == nullptr) {
    return {ObservationOutcome::invalid_tap_handle};
  }
  slot->backpressure_rejections = 0U;
  if (slot->realized_validity == ObservationValidityState::degraded) {
    slot->realized_validity = ObservationValidityState::valid;
  }
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
  if (slot.active_claims != 0U) {
    return {ObservationOutcome::tap_busy};
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
    ++counters_.disconnected;
    return {{ObservationOutcome::sink_disconnected}, std::nullopt};
  }
  ObservationPollResult result = hub_->poll(handle_);
  if (result.status.succeeded()) {
    ++counters_.pulled;
    return result;
  }
  if (result.status.outcome == ObservationOutcome::no_record) {
    ++counters_.empty;
    return result;
  }
  ++counters_.failed;
  return result;
}

}  // namespace xverse::xcom
