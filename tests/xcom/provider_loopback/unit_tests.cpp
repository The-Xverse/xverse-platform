/**
 * @file unit_tests.cpp
 * @brief Provider registration, interaction-family, FIFO, lifecycle, and concurrency tests.
 */

#include "test_support.hpp"
#include "independent_provider.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <iostream>
#include <string>
#include <thread>

namespace {

using namespace xverse::xcom;
using xverse::xcom::test::Scenario;

/** Report one failed expectation. */
[[nodiscard]] bool expect(const bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << "provider unit failure: " << message << '\n';
  }
  return condition;
}

/** Verify registration and stable descriptor retention. */
[[nodiscard]] bool test_explicit_registration_and_descriptor() {
  const auto registry_configuration = ProviderRegistryConfiguration::create(1U);
  const auto provider_descriptor = test::descriptor("provider.registration");
  LoopbackProvider provider(provider_descriptor);
  ProviderComposition composition(*registry_configuration.value());
  const auto registered = composition.register_provider(provider);
  return expect(registered.outcome() == ProviderOutcome::registered && registered.has_value(),
                "explicit provider registration failed") &&
         expect(registered.value()->descriptor().provider_id().value() ==
                    "provider.registration",
                "registered identity differs") &&
         expect(registered.value()->descriptor().source_link().value() ==
                    "source.xverse.xcom.loopback",
                "source link differs") &&
         expect(registered.value()->descriptor().maximum_routes() ==
                    LoopbackProvider::kMaximumRoutes,
                "route limit differs") &&
         expect(registered.diagnostic_code() == "XCOM-PROV-S001",
                "registration diagnostic code differs");
}

/** Verify a separately implemented provider composes, activates, and exchanges an owned item. */
[[nodiscard]] bool test_independent_provider_contract() {
  constexpr std::string_view digest =
      "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
  const auto contract = CommunicationContract::create(
      {"contract.independent", "1.0.0", "interface.independent", "schema.independent",
       "1.0.0", InteractionKind::message_event, EndpointDirection::produce,
       EndpointDirection::consume});
  if (!contract.has_value()) return expect(false, "independent contract failed");
  const auto source = EndpointSpec::create(
      {"source.independent", digest, "provider.independent", EndpointDirection::produce},
      *contract.value());
  const auto destination = EndpointSpec::create(
      {"destination.independent", digest, "provider.independent", EndpointDirection::consume},
      *contract.value());
  if (!source.has_value() || !destination.has_value()) {
    return expect(false, "independent endpoints failed");
  }
  const auto route = RouteSpec::create(
      {"route.independent", digest, "provider.independent"}, *source.value(),
      *destination.value());
  const auto lifecycle_configuration = LifecycleConfiguration::create({2U, 1U});
  const auto registry_configuration = ProviderRegistryConfiguration::create(1U);
  const auto provider_descriptor = ProviderDescriptor::create(
      {"provider.independent", "1.0.0", "source.fixture.independent", 0x0FU,
       delivery_capability_bit(DeliveryCapability::best_effort),
       ordering_capability_bit(OrderingCapability::per_route_fifo), 16U, 1U, 1U});
  if (!route.has_value() || !lifecycle_configuration.has_value() ||
      !registry_configuration.has_value() || !provider_descriptor.has_value()) {
    return expect(false, "independent fixture configuration failed");
  }
  LifecycleController lifecycle(*lifecycle_configuration.value());
  const auto source_handle = lifecycle.declare_endpoint(*source.value());
  const auto destination_handle = lifecycle.declare_endpoint(*destination.value());
  const auto route_handle = lifecycle.declare_route(*route.value());
  if (!source_handle.has_value() || !destination_handle.has_value() ||
      !route_handle.has_value() ||
      !lifecycle.validate_endpoint(*source_handle.value()).has_value() ||
      !lifecycle.validate_endpoint(*destination_handle.value()).has_value() ||
      !lifecycle
           .validate_route(*route_handle.value(), *source_handle.value(),
                           *destination_handle.value())
           .has_value() ||
      !lifecycle.activate_endpoint(*source_handle.value()).has_value() ||
      !lifecycle.activate_endpoint(*destination_handle.value()).has_value()) {
    return expect(false, "independent lifecycle setup failed");
  }
  test::IndependentProvider provider(*provider_descriptor.value(), 9001U);
  ProviderComposition composition(*registry_configuration.value());
  if (composition.register_provider(provider).outcome() != ProviderOutcome::registered) {
    return expect(false, "independent provider registration failed");
  }
  const ProviderRouteRequirements requirements{
      "1.0.0", InteractionKind::message_event, DeliveryCapability::best_effort,
      OrderingCapability::per_route_fifo, 16U, 1U};
  const auto prepared = composition.prepare_route(
      lifecycle, *route.value(), *route_handle.value(), *source_handle.value(),
      *destination_handle.value(), requirements);
  const std::array<std::byte, 1U> payload{std::byte{0x5AU}};
  const auto item = CommunicationItem::create(
      {"contract.independent", "1.0.0", "interface.independent", "source.independent",
       "schema.independent", "1.0.0", InteractionKind::message_event,
       OriginKind::component, Timestamp(1), "clock.independent", "correlation.independent",
       "causation.independent", "route.independent", "provider.independent", payload},
      *contract.value());
  const auto wrong_item = CommunicationItem::create(
      {"contract.independent", "1.0.0", "interface.independent", "source.independent",
       "schema.independent", "1.0.0", InteractionKind::message_event,
       OriginKind::component, Timestamp(1), "clock.independent", "correlation.wrong",
       "causation.independent", "route.wrong", "provider.independent", payload},
      *contract.value());
  LifecycleController foreign_lifecycle(*lifecycle_configuration.value());
  if (!prepared.has_value() || !item.has_value() || !wrong_item.has_value() ||
      composition.activate_route(*prepared.value(), foreign_lifecycle).outcome() !=
          ProviderOutcome::lifecycle_mismatch ||
      provider.activate_calls() != 0U ||
      composition.activate_route(*prepared.value(), lifecycle).outcome() !=
          ProviderOutcome::activated ||
      provider.activate_calls() != 1U ||
      composition.submit(*prepared.value(), *wrong_item.value(), lifecycle).outcome() !=
          ProviderOutcome::item_mismatch ||
      provider.submit_calls() != 0U ||
      composition.submit(*prepared.value(), *item.value(), lifecycle).outcome() !=
          ProviderOutcome::accepted ||
      provider.submit_calls() != 1U) {
    return expect(false, "independent provider activation or submission failed");
  }
  const auto received = composition.receive(*prepared.value(), lifecycle);
  return expect(received.has_value() && *received.value() == *item.value(),
                "independent provider did not return the exact owned item");
}

/** Verify provider descriptor callbacks may safely re-enter registration before registry locking. */
[[nodiscard]] bool test_registration_reentry() {
  const auto registry_configuration = ProviderRegistryConfiguration::create(2U);
  const auto outer_descriptor = ProviderDescriptor::create(
      {"provider.reentry.outer", "1.0.0", "source.fixture.reentry.outer", 0x0FU,
       delivery_capability_bit(DeliveryCapability::best_effort),
       ordering_capability_bit(OrderingCapability::per_route_fifo), 8U, 1U, 1U});
  const auto nested_descriptor = ProviderDescriptor::create(
      {"provider.reentry.nested", "1.0.0", "source.fixture.reentry.nested", 0x0FU,
       delivery_capability_bit(DeliveryCapability::best_effort),
       ordering_capability_bit(OrderingCapability::per_route_fifo), 8U, 1U, 1U});
  if (!registry_configuration.has_value() || !outer_descriptor.has_value() ||
      !nested_descriptor.has_value()) {
    return expect(false, "re-entry fixture configuration failed");
  }
  ProviderComposition composition(*registry_configuration.value());
  test::IndependentProvider nested(*nested_descriptor.value(), 9101U);
  test::IndependentProvider outer(*outer_descriptor.value(), 9102U);
  outer.configure_registration_reentry(&composition, &nested);
  const auto registered = composition.register_provider(outer);
  return expect(registered.outcome() == ProviderOutcome::registered,
                "outer re-entry provider was not registered") &&
         expect(outer.reentry_outcome().has_value() &&
                    *outer.reentry_outcome() == ProviderOutcome::registered,
                "nested registration did not complete during provider callback");
}

/** Verify exact owned delivery for all four interaction families. */
[[nodiscard]] bool test_all_interaction_families() {
  constexpr std::array kinds{
      InteractionKind::signal_state_update, InteractionKind::message_event,
      InteractionKind::service_request, InteractionKind::service_response};
  unsigned int sequence = 1U;
  for (const InteractionKind kind : kinds) {
    Scenario scenario(kind, 2U, 16U, "family." + std::to_string(sequence));
    if (!expect(scenario.ready(), "interaction scenario setup failed")) {
      return false;
    }
    const auto item = scenario.item(sequence);
    if (!expect(item.has_value(), "interaction item construction failed") ||
        !expect(scenario.composition()
                    .submit(scenario.provider_handle(), *item.value(), scenario.lifecycle())
                    .outcome() == ProviderOutcome::accepted,
                "interaction item was not accepted")) {
      return false;
    }
    const auto received = scenario.composition().receive(scenario.provider_handle(),
                                                         scenario.lifecycle());
    if (!expect(received.outcome() == ProviderOutcome::received && received.has_value(),
                "interaction item was not received") ||
        !expect(*received.value() == *item.value(), "interaction item bytes or provenance differ")) {
      return false;
    }
    ++sequence;
  }
  return true;
}

/** Verify reject-new saturation preserves FIFO contents and fixed capacity. */
[[nodiscard]] bool test_saturation_fifo_and_recovery() {
  Scenario scenario(InteractionKind::message_event, 2U, 16U, "saturation");
  if (!expect(scenario.ready(), "saturation scenario setup failed")) {
    return false;
  }
  const auto first = scenario.item(1U);
  const auto second = scenario.item(2U);
  const auto third = scenario.item(3U);
  if (!first.has_value() || !second.has_value() || !third.has_value()) {
    return expect(false, "saturation items were invalid");
  }
  if (!expect(scenario.composition()
                  .submit(scenario.provider_handle(), *first.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::accepted,
              "first FIFO item rejected") ||
      !expect(scenario.composition()
                  .submit(scenario.provider_handle(), *second.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::accepted,
              "second FIFO item rejected")) {
    return false;
  }
  const auto before = scenario.composition().route_state(scenario.provider_handle());
  if (!expect(scenario.composition()
                  .submit(scenario.provider_handle(), *third.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::queue_saturated,
              "overflow did not report stable saturation")) {
    return false;
  }
  const auto after = scenario.composition().route_state(scenario.provider_handle());
  if (!expect(before.has_value() && after.has_value() &&
                  before.value()->queued_items() == 2U && after.value()->queued_items() == 2U &&
                  before.value()->queue_capacity() == 2U &&
                  after.value()->queue_capacity() == 2U,
              "saturation changed queue contents or capacity")) {
    return false;
  }
  const auto received_first =
      scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
  if (!expect(received_first.has_value() && *received_first.value() == *first.value(),
              "first retained item lost or reordered") ||
      !expect(scenario.composition()
                  .submit(scenario.provider_handle(), *third.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::accepted,
              "queue did not recover after one receive")) {
    return false;
  }
  const auto received_second =
      scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
  const auto received_third =
      scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
  return expect(received_second.has_value() && *received_second.value() == *second.value(),
                "second retained item lost or reordered") &&
         expect(received_third.has_value() && *received_third.value() == *third.value(),
                "recovery item lost or reordered");
}

/** Verify two fixed routes retain independent FIFO state. */
[[nodiscard]] bool test_multiple_bounded_routes() {
  Scenario scenario(InteractionKind::signal_state_update, 2U, 16U, "routes");
  if (!expect(scenario.ready(), "multi-route scenario setup failed")) {
    return false;
  }
  const auto second_spec = RouteSpec::create(
      {"route.routes.secondary", scenario.route_spec().plan_digest(), "provider.loopback"},
      scenario.source_spec(), scenario.destination_spec());
  if (!expect(second_spec.has_value(), "secondary route spec failed")) {
    return false;
  }
  const auto second_lifecycle_handle = scenario.lifecycle().declare_route(*second_spec.value());
  if (!expect(second_lifecycle_handle.has_value(), "secondary route declaration failed") ||
      !expect(scenario.lifecycle()
                  .validate_route(*second_lifecycle_handle.value(), scenario.source_handle(),
                                  scenario.destination_handle())
                  .has_value(),
              "secondary route validation failed")) {
    return false;
  }
  const auto prepared = scenario.composition().prepare_route(
      scenario.lifecycle(), *second_spec.value(), *second_lifecycle_handle.value(),
      scenario.source_handle(), scenario.destination_handle(), scenario.requirements());
  if (!expect(prepared.has_value(), "secondary provider route preparation failed") ||
      !expect(scenario.composition()
                  .activate_route(*prepared.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::activated,
              "secondary provider route activation failed")) {
    return false;
  }
  const auto primary = scenario.item(10U);
  const std::array<std::byte, 1U> payload{std::byte{20U}};
  const auto secondary = scenario.item_with_binding(
      scenario.source_spec().endpoint_id().value(), second_spec.value()->route_id().value(),
      "provider.loopback", payload);
  if (!primary.has_value() || !secondary.has_value()) {
    return expect(false, "multi-route items were invalid");
  }
  if (!expect(scenario.composition()
                  .submit(*prepared.value(), *secondary.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::accepted,
              "secondary item rejected") ||
      !expect(scenario.composition()
                  .submit(scenario.provider_handle(), *primary.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::accepted,
              "primary item rejected")) {
    return false;
  }
  const auto primary_received =
      scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
  const auto secondary_received =
      scenario.composition().receive(*prepared.value(), scenario.lifecycle());
  return expect(primary_received.has_value() && *primary_received.value() == *primary.value(),
                "primary route state crossed routes") &&
         expect(secondary_received.has_value() &&
                    *secondary_received.value() == *secondary.value(),
                "secondary route state crossed routes");
}

/** Verify drain disposition, stopped submissions, empty close, and reconciliation. */
[[nodiscard]] bool test_drain_close_and_reconcile() {
  Scenario scenario(InteractionKind::service_request, 2U, 16U, "drain");
  if (!expect(scenario.ready(), "drain scenario setup failed")) {
    return false;
  }
  const auto item = scenario.item(1U);
  if (!item.has_value() ||
      scenario.composition()
              .submit(scenario.provider_handle(), *item.value(), scenario.lifecycle())
              .outcome() != ProviderOutcome::accepted) {
    return expect(false, "drain fixture submit failed");
  }
  if (!expect(scenario.composition()
                  .drain_route(scenario.provider_handle(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::draining,
              "route did not enter draining") ||
      !expect(scenario.composition()
                  .submit(scenario.provider_handle(), *item.value(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::inactive_route,
              "draining route accepted a new item") ||
      !expect(scenario.composition()
                  .close_route(scenario.provider_handle(), scenario.lifecycle())
                  .outcome() == ProviderOutcome::queued_items_remain,
              "close hid queued-item disposition")) {
    return false;
  }
  const auto reconciled = scenario.composition().reconcile_route(scenario.provider_handle(),
                                                                  scenario.lifecycle());
  const auto received =
      scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
  if (!expect(reconciled.has_value() &&
                  reconciled.value()->state() == ProviderRouteState::draining &&
                  reconciled.value()->queued_items() == 1U,
              "draining state did not reconcile") ||
      !expect(received.has_value() && *received.value() == *item.value(),
              "draining receive lost the queued item")) {
    return false;
  }
  return expect(scenario.composition()
                    .close_route(scenario.provider_handle(), scenario.lifecycle())
                    .outcome() == ProviderOutcome::closed,
                "empty drained route did not close") &&
         expect(scenario.composition()
                    .close_route(scenario.provider_handle(), scenario.lifecycle())
                    .outcome() == ProviderOutcome::closed,
                "safe close repeat did not remain closed");
}

/** Verify overlapping producers/consumers deliver each unique item exactly once. */
[[nodiscard]] bool test_concurrent_submission_and_receive() {
  Scenario scenario(InteractionKind::message_event, 8U, 16U, "concurrent");
  if (!expect(scenario.ready(), "concurrency scenario setup failed")) {
    return false;
  }
  constexpr std::size_t count = 24U;
  constexpr std::size_t producer_count = 4U;
  constexpr std::size_t consumer_count = 2U;
  constexpr std::size_t maximum_attempts = 1000000U;
  std::array<std::optional<CommunicationItem>, count> items;
  for (std::size_t index = 0U; index < count; ++index) {
    const auto item = scenario.item(static_cast<unsigned int>(index + 1U));
    if (!item.has_value()) {
      return expect(false, "concurrent item construction failed");
    }
    items[index].emplace(*item.value());
  }
  std::atomic<std::size_t> accepted{0U};
  std::atomic<std::size_t> received{0U};
  std::atomic<bool> begin_consuming{false};
  std::atomic<bool> failed{false};
  std::atomic<bool> overlap_observed{false};
  std::array<std::atomic<bool>, count> seen{};
  std::array<std::thread, producer_count> producers;
  for (std::size_t producer = 0U; producer < producer_count; ++producer) {
    producers[producer] = std::thread([&scenario, &items, &accepted, &begin_consuming,
                                       &failed, producer]() {
      for (std::size_t index = producer; index < count; index += producer_count) {
        bool submitted = false;
        for (std::size_t attempt = 0U; attempt < maximum_attempts; ++attempt) {
          if (failed.load()) {
            return;
          }
          const ProviderOutcome outcome =
              scenario.composition()
                  .submit(scenario.provider_handle(), *items[index], scenario.lifecycle())
                  .outcome();
          if (outcome == ProviderOutcome::accepted) {
            const std::size_t total = accepted.fetch_add(1U) + 1U;
            if (total >= LoopbackProvider::kMaximumQueueItems) {
              begin_consuming.store(true);
            }
            submitted = true;
            break;
          }
          if (outcome != ProviderOutcome::queue_saturated) {
            failed.store(true);
            return;
          }
          std::this_thread::yield();
        }
        if (!submitted) {
          failed.store(true);
          return;
        }
      }
    });
  }
  std::array<std::thread, consumer_count> consumers;
  for (auto& thread : consumers) {
    thread = std::thread([&scenario, &accepted, &received, &begin_consuming, &failed,
                          &overlap_observed, &seen]() {
      while (!begin_consuming.load()) {
        if (failed.load()) {
          return;
        }
        std::this_thread::yield();
      }
      std::size_t empty_polls = 0U;
      while (received.load() < count && !failed.load()) {
        const auto result =
            scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
        if (result.outcome() == ProviderOutcome::queue_empty) {
          ++empty_polls;
          if (empty_polls == maximum_attempts) {
            failed.store(true);
            return;
          }
          std::this_thread::yield();
          continue;
        }
        empty_polls = 0U;
        if (!result.has_value() || result.outcome() != ProviderOutcome::received ||
            result.value()->payload().size() != 1U) {
          failed.store(true);
          return;
        }
        if (accepted.load() < count) {
          overlap_observed.store(true);
        }
        const auto sequence =
            std::to_integer<unsigned int>(result.value()->payload().bytes()[0]);
        if (sequence == 0U || sequence > count || seen[sequence - 1U].exchange(true)) {
          failed.store(true);
          return;
        }
        received.fetch_add(1U);
      }
    });
  }
  for (auto& thread : producers) {
    thread.join();
  }
  for (auto& thread : consumers) {
    thread.join();
  }
  const auto state = scenario.composition().route_state(scenario.provider_handle());
  return expect(!failed.load(), "concurrent operation returned an invalid outcome") &&
         expect(accepted.load() == count, "concurrent accepted count differs") &&
         expect(received.load() == count, "concurrent received count differs") &&
         expect(overlap_observed.load(), "producers and consumers did not overlap") &&
         expect(state.has_value() && state.value()->queued_items() == 0U,
                "concurrent queue did not drain exactly");
}

}  // namespace

/** @return Zero when all provider-loopback unit checks pass. */
int main() {
  const bool passed =
      test_explicit_registration_and_descriptor() && test_independent_provider_contract() &&
      test_registration_reentry() && test_all_interaction_families() &&
      test_saturation_fifo_and_recovery() && test_multiple_bounded_routes() &&
      test_drain_close_and_reconcile() && test_concurrent_submission_and_receive();
  return passed ? 0 : 1;
}
