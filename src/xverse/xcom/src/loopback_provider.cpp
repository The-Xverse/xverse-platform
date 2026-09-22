/**
 * @file loopback_provider.cpp
 * @brief Serialized fixed-array loopback route and reject-new FIFO mechanics.
 * @ownership Route bindings and queued items are copied into provider-owned fixed storage.
 * @lifetime Queue removal returns an independent owned CommunicationItem copy.
 * @thread_safety One mutex serializes every route and queue operation.
 * @failure Every rejected operation leaves unrelated routes and retained FIFO items unchanged.
 */

#include "xverse/xcom/loopback_provider.hpp"

#include <atomic>
#include <limits>

namespace xverse::xcom {
namespace {

std::atomic<std::uint64_t> next_provider_instance{1U};

}  // namespace

LoopbackProvider::LoopbackProvider(const ProviderDescriptor& descriptor) noexcept
    : descriptor_(descriptor), instance_id_(next_provider_instance.fetch_add(1U)) {
  if (instance_id_ == 0U) {
    instance_id_ = next_provider_instance.fetch_add(1U);
  }
}

bool LoopbackProvider::descriptor_compatible() const noexcept {
  constexpr std::uint8_t all_interactions = 0x0FU;
  return descriptor_.interaction_mask() == all_interactions &&
         descriptor_.delivery_mask() ==
             delivery_capability_bit(DeliveryCapability::best_effort) &&
         descriptor_.ordering_mask() ==
             ordering_capability_bit(OrderingCapability::per_route_fifo) &&
         descriptor_.maximum_routes() <= kMaximumRoutes &&
         descriptor_.maximum_queue_items() <= kMaximumQueueItems;
}

ProviderResult<ProviderRouteToken> LoopbackProvider::prepare(
    const ProviderRouteBinding& binding) noexcept {
  const std::lock_guard lock(mutex_);
  const std::size_t configured_routes =
      descriptor_.maximum_routes() < kMaximumRoutes ? descriptor_.maximum_routes()
                                                    : kMaximumRoutes;
  std::size_t reusable = configured_routes;
  for (std::size_t index = 0U; index < configured_routes; ++index) {
    if (!routes_[index].has_value()) {
      if (reusable == configured_routes) {
        reusable = index;
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
        (reusable == configured_routes ||
         routes_[index]->binding.route_spec().route_id() ==
             binding.route_spec().route_id())) {
      reusable = index;
    }
  }
  if (reusable == configured_routes ||
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
  routes_[reusable].reset();
  routes_[reusable].emplace(binding, *token);
  return ProviderResult<ProviderRouteToken>::with_value(ProviderOutcome::prepared, *token);
}

LoopbackProvider::RouteRecord* LoopbackProvider::authenticate(
    const ProviderRouteToken& token) noexcept {
  for (auto& route : routes_) {
    if (route.has_value() && route->token == token) {
      return &*route;
    }
  }
  return nullptr;
}

const LoopbackProvider::RouteRecord* LoopbackProvider::authenticate(
    const ProviderRouteToken& token) const noexcept {
  return const_cast<LoopbackProvider*>(this)->authenticate(token);
}

bool LoopbackProvider::lifecycle_matches(const RouteRecord& record,
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

std::optional<ProviderRouteStateValue> LoopbackProvider::state_value(
    const RouteRecord& record) noexcept {
  return ProviderRouteStateValue::create(record.token, record.state, record.queue.size,
                                         record.queue.capacity);
}

ProviderStatus LoopbackProvider::activate(const ProviderRouteToken& token,
                                          const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate(token);
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

ProviderStatus LoopbackProvider::submit(const ProviderRouteToken& token,
                                        const CommunicationItem& item,
                                        const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate(token);
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
  if (record->queue.size == record->queue.capacity) {
    return ProviderStatus(ProviderOutcome::queue_saturated);
  }
  const std::size_t tail = (record->queue.head + record->queue.size) % record->queue.capacity;
  record->queue.items[tail].emplace(item);
  ++record->queue.size;
  return ProviderStatus(ProviderOutcome::accepted);
}

ProviderResult<CommunicationItem> LoopbackProvider::receive(
    const ProviderRouteToken& token, const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate(token);
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
  if (record->queue.size == 0U) {
    return ProviderResult<CommunicationItem>::without_value(ProviderOutcome::queue_empty);
  }
  const CommunicationItem item(*record->queue.items[record->queue.head]);
  record->queue.items[record->queue.head].reset();
  record->queue.head = (record->queue.head + 1U) % record->queue.capacity;
  --record->queue.size;
  return ProviderResult<CommunicationItem>::with_value(ProviderOutcome::received, item);
}

ProviderStatus LoopbackProvider::drain(const ProviderRouteToken& token,
                                       const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate(token);
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

ProviderStatus LoopbackProvider::close(const ProviderRouteToken& token,
                                       const LifecycleController& lifecycle) noexcept {
  const std::lock_guard lock(mutex_);
  RouteRecord* record = authenticate(token);
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
  if (record->queue.size != 0U) {
    return ProviderStatus(ProviderOutcome::queued_items_remain);
  }
  record->state = ProviderRouteState::closed;
  return ProviderStatus(ProviderOutcome::closed);
}

ProviderResult<ProviderRouteStateValue> LoopbackProvider::state(
    const ProviderRouteToken& token) const noexcept {
  const std::lock_guard lock(mutex_);
  const RouteRecord* record = authenticate(token);
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

ProviderResult<ProviderRouteStateValue> LoopbackProvider::reconcile(
    const ProviderRouteToken& token,
    const LifecycleController& lifecycle) const noexcept {
  const std::lock_guard lock(mutex_);
  const RouteRecord* record = authenticate(token);
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
