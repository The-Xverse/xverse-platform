/**
 * \file failure_tests.cpp
 * \brief T026 fault-injected failure semantics: intent write failure with zero emission,
 *        sync failure and partial-write boundary restoration, and the outcome-write orphan.
 *
 * \details
 * The suite injects faults through the journal's own `Storage` seam and asserts the declared
 * fail-closed behaviour. It uses no network or ambient access and no wall-clock verdict.
 *
 * \ingroup xcom_stim
 */

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
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

/// \brief In-memory storage seam with deterministic, single-fault injection.
class FaultyStorage final : public StimulationJournal::Storage {
public:
  JournalStatus append(std::span<const std::uint8_t> bytes) override {
    ++append_calls_;
    if (fail_append_ || (fail_append_on_call_ != 0U && append_calls_ == fail_append_on_call_)) {
      return JournalStatus::WriteFailed;
    }
    std::size_t take = bytes.size();
    if (partial_ < take) {
      take = partial_;
    }
    bytes_.insert(bytes_.end(), bytes.begin(), bytes.begin() + static_cast<std::ptrdiff_t>(take));
    if (take < bytes.size()) {
      return JournalStatus::PartialWrite;
    }
    return JournalStatus::Ok;
  }
  JournalStatus sync() override {
    return fail_sync_ ? JournalStatus::WriteFailed : JournalStatus::Ok;
  }
  JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    out = bytes_;
    return JournalStatus::Ok;
  }
  std::size_t size() override { return bytes_.size(); }
  JournalStatus truncate(std::size_t size) override {
    if (fail_truncate_) {
      return JournalStatus::WriteFailed;
    }
    bytes_.resize(size);
    return JournalStatus::Ok;
  }

  std::vector<std::uint8_t> bytes_{};
  bool fail_append_{false};
  bool fail_sync_{false};
  bool fail_truncate_{false};
  std::size_t partial_{static_cast<std::size_t>(-1)};
  std::size_t fail_append_on_call_{0U};
  std::size_t append_calls_{0U};
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

} // namespace

/// \brief T26-TS-012: an intent write failure invokes the callback zero times.
TEST(T026JournalFailure, test_journal_write_failure_no_emission) {
  FaultyStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);
  StimulationOutcome out;
  std::size_t emissions = 0;
  const auto callback = [&emissions](const StimulationIntent &intent) {
    ++emissions;
    return make_outcome(intent.request_id, OutcomeKind::Delivered);
  };

  storage.fail_append_ = true;
  EXPECT_EQ(journal.journal_then_emit(make_intent(1U), callback, out), JournalStatus::WriteFailed);
  EXPECT_EQ(emissions, 0U);
  EXPECT_TRUE(storage.bytes_.empty());

  storage.fail_append_ = false;
  storage.partial_ = 0U;
  EXPECT_EQ(journal.journal_then_emit(make_intent(2U), callback, out),
            JournalStatus::PartialWrite);
  EXPECT_EQ(emissions, 0U);
  EXPECT_TRUE(storage.bytes_.empty());

  storage.partial_ = 78U; // half of a 157-byte minimal intent frame
  EXPECT_EQ(journal.journal_then_emit(make_intent(3U), callback, out),
            JournalStatus::PartialWrite);
  EXPECT_EQ(emissions, 0U);
  EXPECT_TRUE(storage.bytes_.empty());
  EXPECT_EQ(journal.snapshot().retained_records, 0U);
}

/// \brief T26-TS-013: sync failure and partial write with boundary restoration.
TEST(T026JournalFailure, test_journal_sync_failure_and_partial_write) {
  StimulationOutcome out;
  std::size_t emissions = 0;
  const auto callback = [&emissions](const StimulationIntent &intent) {
    ++emissions;
    return make_outcome(intent.request_id, OutcomeKind::Delivered);
  };

  FaultyStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);
  storage.fail_sync_ = true;
  EXPECT_EQ(journal.journal_then_emit(make_intent(1U), callback, out), JournalStatus::WriteFailed);
  EXPECT_EQ(emissions, 0U);
  EXPECT_TRUE(storage.bytes_.empty()); // the boundary was restored
  EXPECT_EQ(journal.snapshot().retained_bytes, 0U);

  storage.fail_sync_ = true;
  storage.fail_truncate_ = true;
  EXPECT_EQ(journal.journal_then_emit(make_intent(2U), callback, out),
            JournalStatus::WriteFailed);
  EXPECT_EQ(emissions, 0U);
  // Restoration failed: the journal is marked unusable and appends no further record.
  EXPECT_EQ(storage.bytes_.size(), 157U);
  EXPECT_EQ(journal.journal_then_emit(make_intent(3U), callback, out),
            JournalStatus::WriteFailed);
  EXPECT_EQ(emissions, 0U);
}

/// \brief T26-TS-014: an outcome write failure yields `EvidenceIncomplete` and one orphan.
TEST(T026JournalFailure, test_journal_outcome_write_failure_orphan) {
  FaultyStorage storage;
  StimulationOutcome out;
  std::size_t emissions = 0;
  {
    StimulationJournal journal;
    ASSERT_EQ(journal.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);
    storage.fail_append_on_call_ = 2U; // the first append (intent) succeeds; the outcome fails
    const JournalStatus status = journal.journal_then_emit(
        make_intent(1U),
        [&emissions](const StimulationIntent &intent) {
          ++emissions;
          return make_outcome(intent.request_id, OutcomeKind::Delivered);
        },
        out);
    EXPECT_EQ(status, JournalStatus::EvidenceIncomplete);
    EXPECT_EQ(emissions, 1U);
    EXPECT_EQ(storage.bytes_.size(), 157U); // the durable intent alone remains
  }

  StimulationJournal reopened;
  ASSERT_EQ(reopened.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);
  const auto report = reopened.recover();
  EXPECT_EQ(report.status, JournalStatus::Ok);
  EXPECT_EQ(report.complete_intents, 1U);
  EXPECT_EQ(report.outcomes, 0U);
  EXPECT_EQ(report.orphan_intents, 1U);
}
