/**
 * \file concurrency_tests.cpp
 * \brief T026 bounded deterministic concurrency and callback-outside-lock probe.
 *
 * \details
 * The suite uses at most four threads, one writer per journal, no shared mutable state
 * between journals, and no wall-clock verdict. It proves that independent journals produce
 * the single-threaded golden byte stream and that the emission callback runs with the
 * journal mutex released.
 *
 * \ingroup xcom_stim
 */

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <future>
#include <span>
#include <string>
#include <thread>
#include <vector>

#include <gtest/gtest.h>

#include "xverse/xcom/stimulation_journal.hpp"

namespace {

using xverse::xcom::validation::JournalConfig;
using xverse::xcom::validation::JournalStatus;
using xverse::xcom::validation::OutcomeKind;
using xverse::xcom::validation::Result;
using xverse::xcom::validation::StimulationIntent;
using xverse::xcom::validation::StimulationJournal;
using xverse::xcom::validation::StimulationOutcome;
using xverse::xcom::validation::Tag;
using xverse::xcom::validation::Timestamp;

/// \brief In-memory storage seam used by the concurrency matrix.
class MemoryStorage final : public StimulationJournal::Storage {
public:
  JournalStatus append(std::span<const std::uint8_t> bytes) override {
    bytes_.insert(bytes_.end(), bytes.begin(), bytes.end());
    return JournalStatus::Ok;
  }
  JournalStatus sync() override { return JournalStatus::Ok; }
  JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    out = bytes_;
    return JournalStatus::Ok;
  }
  std::size_t size() override { return bytes_.size(); }
  JournalStatus truncate(std::size_t size) override {
    bytes_.resize(size);
    return JournalStatus::Ok;
  }

  std::vector<std::uint8_t> bytes_{};
};

/// \brief Builds a deterministic synthetic intent.
StimulationIntent make_intent(std::uint64_t request_id, const std::string &target = "T",
                              const std::string &tool = "U") {
  StimulationIntent intent;
  intent.permit_id.fill(static_cast<std::uint8_t>(request_id & 0xFFU));
  intent.session_id.fill(static_cast<std::uint8_t>((request_id + 1U) & 0xFFU));
  intent.plan_digest.fill(static_cast<std::uint8_t>((request_id + 2U) & 0xFFU));
  intent.request_id = request_id;
  intent.correlation_id = request_id + 1000U;
  intent.causation_id = request_id + 2000U;
  intent.action_mask = 0x01U;
  intent.target = *Tag::make(target);
  intent.tool = *Tag::make(tool);
  intent.quota_cost = 3U;
  intent.clock_domain = 7U;
  intent.scheduled_at = static_cast<Timestamp>(100000) + static_cast<Timestamp>(request_id);
  intent.immediate = false;
  return intent;
}

/// \brief Builds a deterministic synthetic outcome.
StimulationOutcome make_outcome(std::uint64_t request_id, OutcomeKind kind) {
  StimulationOutcome outcome;
  outcome.request_id = request_id;
  outcome.kind = kind;
  outcome.reason = Result::Ok;
  outcome.clock_domain = 7U;
  outcome.observed_at = static_cast<Timestamp>(200000) + static_cast<Timestamp>(request_id);
  return outcome;
}

/// \brief Runs the fixed four-operation sequence on one journal.
JournalStatus run_sequence(StimulationJournal &journal) {
  for (std::uint64_t request_id = 1U; request_id <= 4U; ++request_id) {
    StimulationOutcome out;
    const JournalStatus status = journal.journal_then_emit(
        make_intent(request_id),
        [request_id](const StimulationIntent &) {
          return make_outcome(request_id, OutcomeKind::Delivered);
        },
        out);
    if (status != JournalStatus::Ok) {
      return status;
    }
  }
  return JournalStatus::Ok;
}

} // namespace

/// \brief T26-TS-015: four independent journals reproduce the single-threaded golden stream.
TEST(T026JournalConcurrency, test_journal_bounded_deterministic_concurrency) {
  std::vector<std::uint8_t> golden;
  {
    MemoryStorage storage;
    StimulationJournal journal;
    ASSERT_EQ(journal.open(storage, JournalConfig{320U, 16U, 8192U}), JournalStatus::Ok);
    ASSERT_EQ(run_sequence(journal), JournalStatus::Ok);
    golden = storage.bytes_;
  }
  ASSERT_EQ(golden.size(), 4U * (157U + 66U));

  for (std::size_t run = 0; run < 3U; ++run) {
    constexpr std::size_t kThreads = 4U;
    std::array<MemoryStorage, kThreads> storages{};
    std::array<StimulationJournal, kThreads> journals{};
    std::array<std::atomic<int>, kThreads> statuses{};
    for (std::size_t index = 0; index < kThreads; ++index) {
      statuses[index].store(-1);
      ASSERT_EQ(journals[index].open(storages[index], JournalConfig{320U, 16U, 8192U}),
                JournalStatus::Ok);
    }
    std::vector<std::thread> threads;
    threads.reserve(kThreads);
    for (std::size_t index = 0; index < kThreads; ++index) {
      threads.emplace_back([&journals, &statuses, index]() {
        statuses[index].store(static_cast<int>(run_sequence(journals[index])));
      });
    }
    for (std::thread &thread : threads) {
      thread.join();
    }
    for (std::size_t index = 0; index < kThreads; ++index) {
      EXPECT_EQ(statuses[index].load(), static_cast<int>(JournalStatus::Ok));
      EXPECT_EQ(storages[index].bytes_, golden);
    }
  }
}

/// \brief T26-TS-016: the emission callback observes the journal mutex as released.
TEST(T026JournalConcurrency, test_journal_callback_outside_lock_probe) {
  MemoryStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);

  std::atomic<bool> probed{false};
  StimulationJournal *journal_ptr = &journal;
  const auto callback = [journal_ptr, &probed](const StimulationIntent &intent) {
    // Re-entrant probes: both lock the journal mutex. If the callback ran under the lock,
    // these calls deadlock and the bounded wait below fails.
    const auto snapshot = journal_ptr->snapshot();
    const auto intents = journal_ptr->recovered_intents();
    EXPECT_EQ(snapshot.complete_intents, 1U);
    EXPECT_EQ(intents.size(), 1U);
    probed.store(true);
    return make_outcome(intent.request_id, OutcomeKind::Delivered);
  };

  auto future = std::async(std::launch::async, [&journal, &callback]() {
    StimulationOutcome out;
    return journal.journal_then_emit(make_intent(1U), callback, out);
  });
  ASSERT_EQ(future.wait_for(std::chrono::seconds(5)), std::future_status::ready);
  EXPECT_EQ(future.get(), JournalStatus::Ok);
  EXPECT_TRUE(probed.load());
  EXPECT_EQ(journal.snapshot().orphan_intents, 0U);
}
