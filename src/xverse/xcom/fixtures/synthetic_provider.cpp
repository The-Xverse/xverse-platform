/**
 * @file synthetic_provider.cpp
 * @ingroup xcom_gw
 * @brief T034 independently written fixed-array route and reject-new FIFO mechanics for the second
 *        minimal synthetic provider.
 * @ownership Route bindings, provider-local tokens, and queued items are copied into this fixture's
 *            own fixed storage; no accepted provider storage is borrowed or shared.
 * @lifetime Queue removal returns an independent owned `CommunicationItem` copy that remains valid
 *           after later provider operations.
 * @thread_safety One mutex serializes every route, queue, and counter operation. No callback,
 *                registry, filesystem, environment, process, socket, or network operation occurs.
 * @failure Every rejected operation leaves unrelated routes and retained FIFO items unchanged; a
 *          configured forced failure returns its exact stable outcome without mutating route state.
 * @par Traceability
 * Supports the T034 `t034-replaceability`, `t034-version`, and `t034-isolation` suites and the
 * unchanged T033 `ProviderContractSuite` over accepted `XCOM-DU-007`/`XCOM-DU-008`.
 */

#include "synthetic_provider.hpp"

#include <atomic>
#include <limits>

namespace xverse::xcom {
namespace {

/** Independent per-process instance sequence; disjoint from the loopback provider's low sequence. */
std::atomic<std::uint64_t> next_synthetic_instance{SyntheticProvider::kInstanceIdentityBase};

}  // namespace

SyntheticProvider::SyntheticProvider(const ProviderDescriptor& descriptor) noexcept
    : descriptor_(descriptor), instance_id_(next_synthetic_instance.fetch_add(1U)) {
  if (instance_id_ == 0U) {
    instance_id_ = next_synthetic_instance.fetch_add(1U);
  }
}

bool SyntheticProvider::descriptor_compatible() const noexcept {
  return descriptor_.interaction_mask() != 0U && descriptor_.delivery_mask() != 0U &&
         descriptor_.ordering_mask() != 0U && descriptor_.maximum_routes() >= 1U &&
         descriptor_.maximum_routes() <= kMaximumRoutes &&
         descriptor_.maximum_queue_items() >= 1U &&
         descriptor_.maximum_queue_items() <= kMaximumQueueItems;
}

void SyntheticProvider::configure_forced_failure(const ProviderOutcome outcome) noexcept {
  const std::lock_guard lock(mutex_);
  forced_failure_.emplace(outcome);
}

std::size_t SyntheticProvider::prepare_dispatch_count() const noexcept {
  const std::lock_guard lock(mutex_);
  return prepare_dispatches_;
}

std::size_t SyntheticProvider::submit_dispatch_count() const noexcept {
  const std::lock_guard lock(mutex_);
  return submit_dispatches_;
}

std::size_t SyntheticProvider::accepted_item_count() const noexcept {
  const std::lock_guard lock(mutex_);
  return accepted_items_;
}

ProviderResult<ProviderRouteToken> SyntheticProvider::prepare(
    const ProviderRouteBinding& binding) noexcept {
  const std::lock_guard lock(mutex_);
  ++prepare_dispatches_;
  if (forced_failure_.has_value()) {
    return ProviderResult<ProviderRouteToken>::without_value(*forced_failure_);
  }
  const std::size_t configured_routes = descriptor_.maximum_routes() < kMaximumRoutes
                                            ? descriptor_.maximum_routes()
                                            : kMaximumRoutes;
  std::size_t target = configured_routes;
  for (std::size_t index = 0U; index < configured_routes; ++index) {
    if (!routes_[index].has_value()) {
      if (target == configured_routes) {
        target = index;
      }
      continue;
    }
    if (routes_[index]->state != ProviderRouteState::closed &&
        routes_[index]->binding.route_spec().route_id() ==
            binding.route_spec().route_id()) {
      return ProviderResult<ProviderRouteToken>::without_value(
          ProviderOutcome::route_mismatch);
    }
    if (routes_[index]->state == ProviderRouteState::closed &&
        (target == configured_routes ||
         routes_[index]->binding.route_spec().route_id() ==
             binding.route_spec().route_id())) {
      target = index;
    }
  }
  if (target == configured_routes ||
      next_route_generation_ == std::numeric_limits<std::uint64_t>::max()) {
    return ProviderResult<ProviderRouteToken>::without_value(
        ProviderOutcome::route_capacity_exhausted);
  }
  const auto token = ProviderRouteToken::create(next_route_generation_);
  if (!token.has_value()) {
    return ProviderResult<ProviderRouteToken>::without_value(
        ProviderOutcome::route_capacity_exhausted);
  }
  ++next_route_generation_;
  routes_[target].reset();
  routes_[target].emplace(binding, *token);
  return ProviderResult<ProviderRouteToken>::with_value(ProviderOutcome::prepared, *token);
}

SyntheticProvider::RouteRecord* SyntheticProvider::route_for(
    const ProviderRouteToken& token) noexcept {
  for (auto& route : routes_) {
    if (route.has_value() && route->token == token) {
      return &*route;
    }
  }
  return nullptr;
}

const SyntheticProvider::RouteRecord* SyntheticProvider::route_for(
    const ProviderRouteToken& token) const noexcept {
  return const_cast<SyntheticProvider*>(this)->route_for(token);
}

bool SyntheticProvider::lifecycle_matches(const RouteRecord& record,
                                          const LifecycleController& lifecycle,
                                          const bool allow_draining) noexcept {
  const auto route = lifecycle.route_snapshot(record.binding.route_handle());
  const auto source = lifecycle.endpoint_snapshot(record.binding.source_handle());
  const auto destination = lifecycle.endpoint_snapshot(record.binding.destination_handle());
  if (!route.has_value() || !source.has_value() || !destination.has_value() ||
      route.value()->generation() != record.binding.route_handle().generation() ||
      source.value()->generation() != record.binding.source_handle().generation() ||
      destination.value()->generation() != record.binding.destination_handle().generation() ||
      route.value()->plan_digest() != record.binding.route_spec().plan_digest() ||
      source.value()->plan_digest() != record.binding.route_spec().plan_digest() ||
      destination.value()->plan_digest() != record.binding.route_spec().plan_digest()) {
    return false;
  }
  if (record.state == ProviderRouteState::prepared) {
    return route.value()->state() == LifecycleState::validated &&
           (source.value()->state() == LifecycleState::validated ||
            source.value()->state() == LifecycleState::active) &&
           (destination.value()->state() == LifecycleState::validated ||
            destination.value()->state() == LifecycleState::active);
  }
  if (record.state == ProviderRouteState::active) {
    return route.value()->state() == LifecycleState::active &&
           source.value()->state() == LifecycleState::active &&
           destination.value()->state() == LifecycleState::active;
  }
  if (record.state == ProviderRouteState::draining) {
    return allow_draining && route.value()->state() == LifecycleState::draining &&
           source.value()->state() == LifecycleState::active &&
           destination.value()->state() == LifecycleState::active;
  }
  return route.value()->state() == LifecycleState::closed;
}

std::optional<ProviderRouteStateValue> SyntheticProvider::state_value(
    const RouteRecord& record) noexcept {
  return ProviderRouteStateValue::create(record.token, record.state, record.queue.count,
                                         record.queue.capacity);
}

ProviderStatus SyntheticProvider::activate(const ProviderRouteToken& token,
                                           const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = route_for(token);
  if (record == nullptr) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  if (record->state == ProviderRouteState::active) {
    const auto route = lifecycle.route_snapshot(record->binding.route_handle());
    return route.has_value() &&
                   (route.value()->state() == LifecycleState::validated ||
                    lifecycle_matches(*record, lifecycle, false))
               ? ProviderStatus(ProviderOutcome::activated)
               : ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  if (record->state != ProviderRouteState::prepared ||
      !lifecycle_matches(*record, lifecycle, false)) {
    return ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  record->state = ProviderRouteState::active;
  return ProviderStatus(ProviderOutcome::activated);
}

ProviderStatus SyntheticProvider::submit(const ProviderRouteToken& token,
                                         const CommunicationItem& item,
                                         const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  ++submit_dispatches_;
  if (forced_failure_.has_value()) {
    return ProviderStatus(*forced_failure_);
  }
  RouteRecord* record = route_for(token);
  if (record == nullptr) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  if (record->state != ProviderRouteState::active) {
    return ProviderStatus(ProviderOutcome::inactive_route);
  }
  if (!lifecycle_matches(*record, lifecycle, false)) {
    return ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  const RouteSpec& route = record->binding.route_spec();
  const CommunicationContract& contract = route.contract();
  if (item.contract_id() != contract.contract_id() ||
      item.contract_version() != contract.contract_version() ||
      item.interface_id() != contract.interface_id() ||
      item.schema_id() != contract.schema_id() ||
      item.schema_version() != contract.schema_version() ||
      item.interaction_kind() != contract.interaction_kind() ||
      item.endpoint_id() != route.source_endpoint_id() ||
      item.route_id() != route.route_id() || item.provider_id() != route.provider_id()) {
    return ProviderStatus(ProviderOutcome::item_mismatch);
  }
  if (item.payload().size() > record->binding.maximum_payload_bytes()) {
    return ProviderStatus(ProviderOutcome::payload_limit_exceeded);
  }
  if (record->queue.count == record->queue.capacity) {
    return ProviderStatus(ProviderOutcome::queue_saturated);
  }
  const std::size_t write_index =
      (record->queue.read_index + record->queue.count) % record->queue.capacity;
  record->queue.slots[write_index].emplace(item);
  ++record->queue.count;
  ++accepted_items_;
  return ProviderStatus(ProviderOutcome::accepted);
}

ProviderResult<CommunicationItem> SyntheticProvider::receive(
    const ProviderRouteToken& token, const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = route_for(token);
  if (record == nullptr) {
    return ProviderResult<CommunicationItem>::without_value(
        ProviderOutcome::invalid_provider_route_handle);
  }
  if (record->state != ProviderRouteState::active &&
      record->state != ProviderRouteState::draining) {
    return ProviderResult<CommunicationItem>::without_value(ProviderOutcome::inactive_route);
  }
  if (!lifecycle_matches(*record, lifecycle, true)) {
    return ProviderResult<CommunicationItem>::without_value(
        ProviderOutcome::lifecycle_mismatch);
  }
  if (record->queue.count == 0U) {
    return ProviderResult<CommunicationItem>::without_value(ProviderOutcome::queue_empty);
  }
  const CommunicationItem item(*record->queue.slots[record->queue.read_index]);
  record->queue.slots[record->queue.read_index].reset();
  record->queue.read_index = (record->queue.read_index + 1U) % record->queue.capacity;
  --record->queue.count;
  return ProviderResult<CommunicationItem>::with_value(ProviderOutcome::received, item);
}

ProviderStatus SyntheticProvider::drain(const ProviderRouteToken& token,
                                        const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = route_for(token);
  if (record == nullptr) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  if (record->state == ProviderRouteState::draining) {
    return lifecycle_matches(*record, lifecycle, true)
               ? ProviderStatus(ProviderOutcome::draining)
               : ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  if (record->state != ProviderRouteState::active ||
      !lifecycle_matches(*record, lifecycle, false)) {
    return ProviderStatus(ProviderOutcome::inactive_route);
  }
  record->state = ProviderRouteState::draining;
  return ProviderStatus(ProviderOutcome::draining);
}

ProviderStatus SyntheticProvider::close(const ProviderRouteToken& token,
                                        const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = route_for(token);
  if (record == nullptr) {
    return ProviderStatus(ProviderOutcome::invalid_provider_route_handle);
  }
  if (record->state == ProviderRouteState::closed) {
    return lifecycle_matches(*record, lifecycle, true)
               ? ProviderStatus(ProviderOutcome::closed)
               : ProviderStatus(ProviderOutcome::lifecycle_mismatch);
  }
  if (record->state != ProviderRouteState::draining ||
      !lifecycle_matches(*record, lifecycle, true)) {
    return ProviderStatus(ProviderOutcome::inactive_route);
  }
  if (record->queue.count != 0U) {
    return ProviderStatus(ProviderOutcome::queued_items_remain);
  }
  record->state = ProviderRouteState::closed;
  return ProviderStatus(ProviderOutcome::closed);
}

ProviderResult<ProviderRouteStateValue> SyntheticProvider::state(
    const ProviderRouteToken& token) const noexcept {
  const std::lock_guard lock(mutex_);
  const RouteRecord* record = route_for(token);
  if (record == nullptr) {
    return ProviderResult<ProviderRouteStateValue>::without_value(
        ProviderOutcome::invalid_provider_route_handle);
  }
  const auto current = state_value(*record);
  return current.has_value()
             ? ProviderResult<ProviderRouteStateValue>::with_value(
                   ProviderOutcome::reconciled, *current)
             : ProviderResult<ProviderRouteStateValue>::without_value(
                   ProviderOutcome::interrupted_resource);
}

ProviderResult<ProviderRouteStateValue> SyntheticProvider::reconcile(
    const ProviderRouteToken& token,
    const LifecycleController& lifecycle) const noexcept {
  const std::lock_guard lock(mutex_);
  const RouteRecord* record = route_for(token);
  if (record == nullptr) {
    return ProviderResult<ProviderRouteStateValue>::without_value(
        ProviderOutcome::invalid_provider_route_handle);
  }
  if (!lifecycle_matches(*record, lifecycle, true)) {
    return ProviderResult<ProviderRouteStateValue>::without_value(
        ProviderOutcome::interrupted_resource);
  }
  const auto current = state_value(*record);
  return current.has_value()
             ? ProviderResult<ProviderRouteStateValue>::with_value(
                   ProviderOutcome::reconciled, *current)
             : ProviderResult<ProviderRouteStateValue>::without_value(
                   ProviderOutcome::interrupted_resource);
}

}  // namespace xverse::xcom
