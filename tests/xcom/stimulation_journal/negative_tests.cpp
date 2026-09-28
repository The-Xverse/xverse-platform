/**
 * \file negative_tests.cpp
 * \brief T026 fail-closed negative matrix: capacity-bound exhaustion with zero emission,
 *        resolution reference handling, and the null/throwing callback contract.
 *
 * \details
 * Every case injects one controlled defect and asserts the declared fail-closed behaviour
 * with no partial value, no mutation of a complete retained record, and no output claiming
 * success. The suite uses only the public journal surface over an in-memory storage seam.
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

/// \brief In-memory storage seam used by the negative matrix.
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

/// \brief Emission callback that throws; leaves a durable orphan intent.
StimulationJournal::EmissionCallback throwing() {
  return [](const StimulationIntent &) -> StimulationOutcome {
    throw std::runtime_error("t026 synthetic callback failure");
  };
}

} // namespace

/// \brief T26-TS-006: fail-closed capacity exhaustion with zero emission and preservation.
TEST(T026JournalNegative, test_journal_capacity_bound_matrix) {
  StimulationOutcome out;

  // Record-count bound. A throwing callback leaves one durable orphan intent.
  MemoryStorage count_storage;
  StimulationJournal count_journal;
  ASSERT_EQ(count_journal.open(count_storage, JournalConfig{320U, 1U, 4096U}),
            JournalStatus::Ok);
  try {
    (void)count_journal.journal_then_emit(make_intent(1U), throwing(), out);
  } catch (const std::runtime_error &) {
  }
  const std::size_t count_bytes = count_storage.bytes_.size();
  std::size_t count_emissions = 0;
  const JournalStatus count_status = count_journal.journal_then_emit(
      make_intent(2U),
      [&count_emissions](const StimulationIntent &intent) {
        ++count_emissions;
        return make_outcome(intent.request_id, OutcomeKind::Delivered);
      },
      out);
  EXPECT_EQ(count_status, JournalStatus::CapacityExhausted);
  EXPECT_EQ(count_emissions, 0U);
  EXPECT_EQ(count_storage.bytes_.size(), count_bytes);

  // Byte bound for a new intent. One pair uses 157 + 66 = 223 bytes.
  MemoryStorage byte_storage;
  StimulationJournal byte_journal;
  ASSERT_EQ(byte_journal.open(byte_storage, JournalConfig{320U, 4U, 350U}), JournalStatus::Ok);
  std::size_t byte_emissions = 0;
  const auto byte_callback = [&byte_emissions](const StimulationIntent &intent) {
    ++byte_emissions;
    return make_outcome(intent.request_id, OutcomeKind::Delivered);
  };
  ASSERT_EQ(byte_journal.journal_then_emit(make_intent(1U), byte_callback, out),
            JournalStatus::Ok);
  const std::size_t byte_bytes = byte_storage.bytes_.size();
  EXPECT_EQ(byte_bytes, 223U);
  byte_emissions = 0U;
  EXPECT_EQ(byte_journal.journal_then_emit(make_intent(2U), byte_callback, out),
            JournalStatus::CapacityExhausted);
  EXPECT_EQ(byte_emissions, 0U);
  EXPECT_EQ(byte_storage.bytes_.size(), byte_bytes);

  // Byte bound reached only by the outcome: the intent is durable and becomes an orphan.
  MemoryStorage tight_storage;
  StimulationJournal tight_journal;
  ASSERT_EQ(tight_journal.open(tight_storage, JournalConfig{157U, 4U, 200U}), JournalStatus::Ok);
  std::size_t tight_emissions = 0;
  const JournalStatus tight_status = tight_journal.journal_then_emit(
      make_intent(3U),
      [&tight_emissions](const StimulationIntent &intent) {
        ++tight_emissions;
        return make_outcome(intent.request_id, OutcomeKind::Delivered);
      },
      out);
  EXPECT_EQ(tight_status, JournalStatus::EvidenceIncomplete);
  EXPECT_EQ(tight_emissions, 1U);
  EXPECT_EQ(tight_storage.bytes_.size(), 157U);
  EXPECT_EQ(tight_journal.snapshot().orphan_intents, 1U);
  const auto tight_report = tight_journal.recover();
  EXPECT_EQ(tight_report.status, JournalStatus::Ok);
  EXPECT_EQ(tight_report.orphan_intents, 1U);
  EXPECT_EQ(tight_report.outcomes, 0U);
}

/// \brief T26-TS-007: `NotFound`, `AlreadyResolved`, and `Unknown` staying `Unknown`.
TEST(T026JournalNegative, test_journal_resolution_reference_matrix) {
  MemoryStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 8U, 4096U}), JournalStatus::Ok);
  StimulationOutcome out;

  EXPECT_EQ(journal.resolve(999U, make_outcome(999U, OutcomeKind::Unknown)),
            JournalStatus::NotFound);
  EXPECT_EQ(journal.snapshot().retained_records, 0U);

  ASSERT_EQ(journal.journal_then_emit(
                make_intent(2U),
                [](const StimulationIntent &intent) {
                  return make_outcome(intent.request_id, OutcomeKind::Delivered);
                },
                out),
            JournalStatus::Ok);
  EXPECT_EQ(journal.resolve(2U, make_outcome(2U, OutcomeKind::Delivered)),
            JournalStatus::AlreadyResolved);

  StimulationOutcome unresolved;
  try {
    (void)journal.journal_then_emit(make_intent(3U), throwing(), unresolved);
  } catch (const std::runtime_error &) {
  }
  const std::size_t before = storage.bytes_.size();
  EXPECT_EQ(journal.resolve(3U, make_outcome(3U, OutcomeKind::Unknown)), JournalStatus::Ok);
  EXPECT_GT(storage.bytes_.size(), before);
  const std::vector<StimulationOutcome> outcomes = journal.recovered_outcomes();
  ASSERT_FALSE(outcomes.empty());
  EXPECT_EQ(outcomes.back().request_id, 3U);
  EXPECT_EQ(outcomes.back().kind, OutcomeKind::Unknown);
  EXPECT_NE(outcomes.back().kind, OutcomeKind::Delivered);
  EXPECT_EQ(journal.resolve(3U, make_outcome(3U, OutcomeKind::Unknown)),
            JournalStatus::AlreadyResolved);

  // An out-of-vocabulary outcome kind is rejected before any mutation, so the journal never
  // writes a record its own recovery scan would later reject as corrupt. Vocabulary validation
  // precedes the reference check, so even an unknown reference with a bad kind is
  // `RejectedConfiguration`, not `NotFound`.
  const std::size_t before_kind = storage.bytes_.size();
  StimulationOutcome invalid_kind = make_outcome(3U, OutcomeKind::Delivered);
  invalid_kind.kind = static_cast<OutcomeKind>(99);
  EXPECT_EQ(journal.resolve(3U, invalid_kind), JournalStatus::RejectedConfiguration);
  EXPECT_EQ(storage.bytes_.size(), before_kind);
  EXPECT_EQ(journal.snapshot().orphan_intents, 0U);
  EXPECT_EQ(journal.resolve(7777U, invalid_kind), JournalStatus::RejectedConfiguration);
  EXPECT_EQ(storage.bytes_.size(), before_kind);

  // The request identity is the durable linking key and is unique across retained intents: a
  // second intent carrying a retained id is refused before any append and before any emission,
  // so no unresolved duplicate intent can be hidden by another intent's outcome.
  StimulationOutcome duplicate_out;
  std::size_t duplicate_emissions = 0U;
  EXPECT_EQ(journal.journal_then_emit(
                make_intent(2U),
                [&duplicate_emissions](const StimulationIntent &intent) {
                  ++duplicate_emissions;
                  return make_outcome(intent.request_id, OutcomeKind::Delivered);
                },
                duplicate_out),
            JournalStatus::RejectedConfiguration);
  EXPECT_EQ(duplicate_emissions, 0U);
  EXPECT_EQ(storage.bytes_.size(), before_kind);

  // An unrelated reference changes no record.
  const std::size_t after = storage.bytes_.size();
  EXPECT_EQ(journal.resolve(4242U, make_outcome(4242U, OutcomeKind::Delivered)),
            JournalStatus::NotFound);
  EXPECT_EQ(storage.bytes_.size(), after);
}

/// \brief T26-TS-008: null callback rejection and throwing-callback orphan behaviour.
TEST(T026JournalNegative, test_journal_callback_contract_matrix) {
  MemoryStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 8U, 4096U}), JournalStatus::Ok);
  StimulationOutcome out;

  const StimulationJournal::EmissionCallback absent;
  EXPECT_EQ(journal.journal_then_emit(make_intent(1U), absent, out),
            JournalStatus::RejectedConfiguration);
  EXPECT_TRUE(storage.bytes_.empty());
  EXPECT_EQ(journal.snapshot().retained_records, 0U);

  try {
    (void)journal.journal_then_emit(make_intent(2U), throwing(), out);
    FAIL() << "a throwing callback must not be converted to success";
  } catch (const std::runtime_error &) {
  }
  const auto snapshot = journal.snapshot();
  EXPECT_EQ(snapshot.complete_intents, 1U);
  EXPECT_EQ(snapshot.outcomes, 0U);
  EXPECT_EQ(snapshot.orphan_intents, 1U);

  // The throwing-callback contract: the host exception propagates unmodified, the durable intent
  // has no outcome, and recovery classifies it as an explicit `EvidenceIncomplete` orphan (never
  // delivered) with no `Ok` success for that request.
  const auto throw_report = journal.recover();
  EXPECT_EQ(throw_report.status, JournalStatus::Ok);
  EXPECT_EQ(throw_report.complete_intents, 1U);
  EXPECT_EQ(throw_report.outcomes, 0U);
  EXPECT_EQ(throw_report.orphan_intents, 1U);
  ASSERT_EQ(throw_report.orphan_request_ids.size(), 1U);
  EXPECT_EQ(throw_report.orphan_request_ids.front(), 2U);
  EXPECT_TRUE(journal.recovered_outcomes().empty());

  // A callback-returned out-of-vocabulary kind is rejected without appending the invalid outcome,
  // so the durable intent remains an orphan and the journal stays decodable on reopen. The
  // emission callback (the host emission seam) has already run when the kind is known, so no
  // outcome is recorded and the rejected outcome is not exposed through `out`.
  const std::size_t before_invalid = storage.bytes_.size();
  StimulationOutcome invalid_out;
  const JournalStatus invalid_status = journal.journal_then_emit(
      make_intent(3U),
      [](const StimulationIntent &intent) {
        StimulationOutcome produced = make_outcome(intent.request_id, OutcomeKind::Delivered);
        produced.kind = static_cast<OutcomeKind>(99);
        return produced;
      },
      invalid_out);
  EXPECT_EQ(invalid_status, JournalStatus::RejectedConfiguration);
  EXPECT_EQ(storage.bytes_.size(), before_invalid + 157U); // intent durable, invalid outcome not appended
  const auto after_invalid = journal.snapshot();
  EXPECT_EQ(after_invalid.complete_intents, 2U);
  EXPECT_EQ(after_invalid.outcomes, 0U);
  EXPECT_EQ(after_invalid.orphan_intents, 2U);

  StimulationJournal reopened;
  ASSERT_EQ(reopened.open(storage, JournalConfig{320U, 8U, 4096U}), JournalStatus::Ok);
  const auto reopened_snapshot = reopened.snapshot();
  EXPECT_EQ(reopened_snapshot.complete_intents, 2U);
  EXPECT_EQ(reopened_snapshot.outcomes, 0U);
  EXPECT_EQ(reopened_snapshot.orphan_intents, 2U);
}
