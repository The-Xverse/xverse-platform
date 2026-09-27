/**
 * @file concurrency_tests.cpp
 * @brief T016 bounded deterministic concurrency matrix: exactly-once per-route FIFO delivery,
 * repeated-run determinism, and lock-safe registration re-entry.
 * @ownership Each case owns its fixture; the fixture outlives every spawned thread, and every thread
 * is joined before a verdict is formed.
 * @lifetime Per-case; no thread outlives the case.
 * @thread_safety The subject under test is the accepted provider/composition mutex serialization; the
 * cases assert exactly-once delivery, per-route FIFO, and no re-entry deadlock.
 * @failure A lost, duplicated, or reordered item, a deadlock or timeout, or a callback observed under
 * a lock fails the case. Every wait is bounded by an explicit finite iteration cap.
 */

#include "test_support.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace {

using namespace xverse::xcom;
using xverse::xcom::test::CoreStackFixture;
using xverse::xcom::test::kAllInteractions;
using xverse::xcom::test::ProbeProvider;

/** Bounded per-consumer spin cap; no unbounded wait is permitted. */
constexpr std::size_t kMaximumSpinIterations = 4096U;
/** Fixed item count exchanged per concurrency run (equals the loopback queue bound). */
constexpr std::size_t kExchangeItems = 8U;

/**
 * @brief Run one producer/consumer exchange and return the observed FIFO payload sequence.
 * @param suffix Stable fixture identity suffix.
 * @return Observed payload bytes in completion order.
 * @failure Returns a shorter-than-expected sequence when an item is lost.
 */
[[nodiscard]] std::vector<int> run_exchange(const std::string_view suffix) {
  CoreStackFixture fixture(InteractionKind::message_event, suffix, kExchangeItems, 16U, true);
  std::vector<int> observed;
  std::size_t accepted = 0U;
  if (!fixture.ready() || !fixture.activated()) {
    return observed;
  }
  std::array<std::optional<CommunicationItem>, kExchangeItems> items{};
  for (std::size_t index = 0U; index < kExchangeItems; ++index) {
    const auto created = fixture.item(static_cast<unsigned int>(index));
    if (!created.has_value()) {
      return observed;
    }
    items[index].emplace(*created.value());
  }
  std::thread producer([&fixture, &items, &accepted]() {
    for (std::size_t index = 0U; index < kExchangeItems; ++index) {
      if (fixture.submit(*items[index]).outcome() == ProviderOutcome::accepted) {
        ++accepted;
      }
    }
  });
  std::thread consumer([&fixture, &observed]() {
    std::size_t spins = 0U;
    while (observed.size() < kExchangeItems && spins < kMaximumSpinIterations) {
      const auto received = fixture.receive();
      if (received.has_value() && received.outcome() == ProviderOutcome::received) {
        observed.push_back(static_cast<int>(std::to_integer<unsigned char>(
            received.value()->payload().bytes().front())));
      } else {
        ++spins;
        std::this_thread::yield();
      }
    }
  });
  producer.join();
  consumer.join();
  return accepted == kExchangeItems ? observed : std::vector<int>{};
}

}  // namespace

/** CHK-15: concurrent submit/receive delivers each accepted item exactly once in per-route FIFO. */
TEST(CoreMatrixConcurrency, ConcurrentSubmitReceive_ExactlyOncePerRouteFifo) {
  const std::vector<int> observed = run_exchange("concurrent.exactly-once");
  ASSERT_EQ(observed.size(), kExchangeItems);
  for (std::size_t index = 0U; index < kExchangeItems; ++index) {
    EXPECT_EQ(observed[index], static_cast<int>(index));
  }
  // Every payload byte appeared exactly once.
  std::array<int, kExchangeItems> counts{};
  for (const int value : observed) {
    if (value >= 0 && value < static_cast<int>(kExchangeItems)) {
      ++counts[static_cast<std::size_t>(value)];
    }
  }
  for (const int count : counts) {
    EXPECT_EQ(count, 1);
  }
}

/** CHK-15: repeated bounded runs produce the same observable outcome. */
TEST(CoreMatrixConcurrency, ConcurrentRepeatedRuns_DeterministicOutcome) {
  const std::vector<int> baseline = run_exchange("concurrent.repeat.0");
  ASSERT_EQ(baseline.size(), kExchangeItems);
  for (std::size_t run = 1U; run <= 32U; ++run) {
    const std::vector<int> observed =
        run_exchange("concurrent.repeat." + std::to_string(run));
    EXPECT_EQ(observed, baseline);
  }
}

/** CHK-15: registration re-entry completes with no callback invoked under the registry lock. */
TEST(CoreMatrixConcurrency, NoCallbackUnderLock_ReentryCompletes) {
  const auto first_descriptor = xverse::xcom::test::make_descriptor(
      "provider.reentry.first", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  const auto second_descriptor = xverse::xcom::test::make_descriptor(
      "provider.reentry.second", kAllInteractions,
      delivery_capability_bit(DeliveryCapability::best_effort),
      ordering_capability_bit(OrderingCapability::per_route_fifo), 64U, 1U, 1U);
  ProbeProvider first(first_descriptor, 92001U);
  ProbeProvider second(second_descriptor, 92002U);
  const auto configuration = ProviderRegistryConfiguration::create(2U);
  ASSERT_TRUE(configuration.has_value());
  ProviderComposition composition(*configuration.value());
  first.configure_registration_reentry(&composition, &second);
  EXPECT_EQ(composition.register_provider(first).outcome(), ProviderOutcome::registered);
  ASSERT_TRUE(first.reentry_outcome().has_value());
  EXPECT_EQ(*first.reentry_outcome(), ProviderOutcome::registered);
  // Both providers occupy distinct registry slots.
  EXPECT_EQ(composition.register_provider(first).outcome(), ProviderOutcome::duplicate_provider);
  EXPECT_EQ(composition.register_provider(second).outcome(), ProviderOutcome::duplicate_provider);
}
