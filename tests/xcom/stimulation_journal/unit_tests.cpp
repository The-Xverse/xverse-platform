/**
 * \file unit_tests.cpp
 * \brief T026 unit acceptance matrix: exact frame layout and round-trip, configuration
 *        validation, record-size and tag bounds, status determinism and no-mutation, and
 *        snapshot/capacity accounting.
 *
 * \details
 * The suite exercises only the public `xverse::xcom::validation::StimulationJournal`
 * surface over an in-memory `Storage` seam. It uses the C++ standard library plus the
 * admitted GTest prefix, performs no network or ambient access, and asserts no wall-clock
 * behaviour.
 *
 * \ingroup xcom_stim
 */

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <vector>

#include <gtest/gtest.h>

#include "xverse/xcom/stimulation_journal.hpp"

namespace {

using xverse::xcom::validation::ActionMask;
using xverse::xcom::validation::ClockDomainId;
using xverse::xcom::validation::JournalConfig;
using xverse::xcom::validation::JournalSnapshot;
using xverse::xcom::validation::JournalStatus;
using xverse::xcom::validation::OutcomeKind;
using xverse::xcom::validation::Result;
using xverse::xcom::validation::StimulationIntent;
using xverse::xcom::validation::StimulationJournal;
using xverse::xcom::validation::StimulationOutcome;
using xverse::xcom::validation::Tag;
using xverse::xcom::validation::Timestamp;

/// \brief In-memory storage seam used by the unit matrix.
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
StimulationIntent make_intent(std::uint64_t request_id, const std::string &target = "target",
                              const std::string &tool = "tool") {
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
  intent.immediate = (request_id % 2U) == 0U;
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

/// \brief Emission callback that always returns the supplied outcome.
StimulationJournal::EmissionCallback returning(StimulationOutcome outcome) {
  return [outcome](const StimulationIntent &) { return outcome; };
}

/// \brief Emission callback that throws; leaves a durable orphan intent.
StimulationJournal::EmissionCallback throwing() {
  return [](const StimulationIntent &) -> StimulationOutcome {
    throw std::runtime_error("t026 synthetic callback failure");
  };
}

/// \brief Encodes a little-endian 32-bit value for frame-layout assertions.
std::array<std::uint8_t, 4> le32(std::uint32_t value) {
  return {static_cast<std::uint8_t>(value & 0xFFU),
          static_cast<std::uint8_t>((value >> 8U) & 0xFFU),
          static_cast<std::uint8_t>((value >> 16U) & 0xFFU),
          static_cast<std::uint8_t>((value >> 24U) & 0xFFU)};
}

/// \brief Copies four consecutive bytes for little-endian field assertions.
std::array<std::uint8_t, 4> window4(const std::vector<std::uint8_t> &bytes,
                                    std::size_t offset) {
  return {bytes[offset], bytes[offset + 1U], bytes[offset + 2U], bytes[offset + 3U]};
}

} // namespace

/// \brief T26-TS-001: exact frame layout and round-trip for minimal/maximal intents and an outcome.
TEST(T026JournalUnit, test_journal_frame_layout_and_roundtrip) {
  MemoryStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 8U, 4096U}), JournalStatus::Ok);

  const StimulationIntent minimal = make_intent(1U, "T", "U");
  StimulationOutcome out;
  ASSERT_EQ(journal.journal_then_emit(minimal, returning(make_outcome(1U, OutcomeKind::Delivered)),
                                      out),
            JournalStatus::Ok);
  // Minimal legal intent: 44 overhead + 111 payload + one 1-byte tag each = 157 bytes.
  EXPECT_EQ(storage.bytes_.size(), 157U + 66U);

  const std::array<std::uint8_t, 4> magic = le32(0x4E524A58U);
  for (std::size_t index = 0; index < magic.size(); ++index) {
    EXPECT_EQ(storage.bytes_[index], magic[index]);
  }
  EXPECT_EQ(storage.bytes_[4], 1U);
  EXPECT_EQ(storage.bytes_[5], 0U);
  EXPECT_EQ(storage.bytes_[6], 1U);
  EXPECT_EQ(storage.bytes_[7], 0U); // make_intent(1) is not immediate
  EXPECT_EQ(window4(storage.bytes_, 8U), le32(113U));
  EXPECT_EQ(storage.bytes_[28U + 110U], static_cast<std::uint8_t>('T'));
  EXPECT_EQ(storage.bytes_[28U + 112U], static_cast<std::uint8_t>('U'));
  EXPECT_EQ(storage.bytes_[157U + 6U], 2U); // outcome kind
  EXPECT_EQ(storage.bytes_[157U + 7U], 0U); // outcome flags
  EXPECT_EQ(window4(storage.bytes_, 157U + 8U), le32(22U));

  MemoryStorage maximal_storage;
  StimulationJournal maximal_journal;
  ASSERT_EQ(maximal_journal.open(maximal_storage, JournalConfig{320U, 4U, 4096U}),
            JournalStatus::Ok);
  const StimulationIntent maximal = make_intent(2U, std::string(63U, 'a'), std::string(63U, 'b'));
  try {
    (void)maximal_journal.journal_then_emit(maximal, throwing(), out);
  } catch (const std::runtime_error &) {
  }
  EXPECT_EQ(maximal_storage.bytes_.size(), 281U);

  MemoryStorage reopen_storage;
  {
    StimulationJournal writer;
    ASSERT_EQ(writer.open(reopen_storage, JournalConfig{320U, 8U, 4096U}), JournalStatus::Ok);
    StimulationOutcome writer_out;
    ASSERT_EQ(writer.journal_then_emit(
                  minimal, returning(make_outcome(1U, OutcomeKind::Delivered)), writer_out),
              JournalStatus::Ok);
  }
  StimulationJournal reader;
  ASSERT_EQ(reader.open(reopen_storage, JournalConfig{320U, 8U, 4096U}), JournalStatus::Ok);
  ASSERT_EQ(reader.recovered_intents().size(), 1U);
  EXPECT_EQ(reader.recovered_intents().front(), minimal);
  ASSERT_EQ(reader.recovered_outcomes().size(), 1U);
  EXPECT_EQ(reader.recovered_outcomes().front(), make_outcome(1U, OutcomeKind::Delivered));
  EXPECT_EQ(reader.snapshot().orphan_intents, 0U);
  // The 155-byte constant is the configuration floor (44 + 111), not a legal zero-tag record.
  EXPECT_EQ(xverse::xcom::validation::kJournalMinRecordBytes, 155U);

  // NEG-03 (non-vacuous): the compile-time bounded/no-payload-constructor rule. A
  // payload-accepting constructor or unbounded growth of `sizeof` must fail to compile. These
  // duplicate the header rule at the test boundary and fail this translation unit if it is
  // removed. The absence of a payload-bearing member is established by the header declaration
  // and design inspection, not by these assertions: an added member that leaves the type
  // constructible from these argument types and within the size bound is not detectable here
  // without reflection.
  static_assert(!std::is_constructible_v<StimulationIntent, std::vector<std::uint8_t>>,
                "StimulationIntent must not accept a payload byte container");
  static_assert(!std::is_constructible_v<StimulationIntent, std::string_view>,
                "StimulationIntent must not accept free-form payload text");
  static_assert(!std::is_constructible_v<StimulationOutcome, std::vector<std::uint8_t>>,
                "StimulationOutcome must not accept a payload byte container");
  static_assert(!std::is_constructible_v<StimulationOutcome, std::string_view>,
                "StimulationOutcome must not accept free-form payload text");
  static_assert(sizeof(StimulationIntent) <= 256U, "StimulationIntent must stay bounded");
  static_assert(sizeof(StimulationOutcome) <= 64U, "StimulationOutcome must stay bounded");
}

/// \brief T26-TS-002: every configuration row of detailed-design §6.1.
TEST(T026JournalUnit, test_journal_config_validation_matrix) {
  struct Row {
    JournalConfig config;
    JournalStatus expected;
  };
  const Row rows[] = {
      {JournalConfig{320U, 64U, 16384U}, JournalStatus::Ok},
      {JournalConfig{0U, 64U, 16384U}, JournalStatus::RejectedConfiguration},
      {JournalConfig{320U, 0U, 16384U}, JournalStatus::RejectedConfiguration},
      {JournalConfig{320U, 64U, 0U}, JournalStatus::RejectedConfiguration},
      {JournalConfig{154U, 64U, 16384U}, JournalStatus::RejectedConfiguration},
      {JournalConfig{320U, 64U, 319U}, JournalStatus::RejectedConfiguration},
      {JournalConfig{155U, 1U, 155U}, JournalStatus::Ok},
  };
  for (const Row &row : rows) {
    MemoryStorage storage;
    StimulationJournal journal;
    EXPECT_EQ(journal.open(storage, row.config), row.expected);
    EXPECT_TRUE(storage.bytes_.empty()); // a rejected configuration mutates nothing
  }
}

/// \brief T26-TS-003: record-size and tag matrix of detailed-design §6.2.
TEST(T026JournalUnit, test_journal_record_size_and_tag_matrix) {
  MemoryStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);
  StimulationOutcome out;

  const StimulationIntent maximal = make_intent(1U, std::string(63U, 'a'), std::string(63U, 'b'));
  try {
    (void)journal.journal_then_emit(maximal, throwing(), out);
  } catch (const std::runtime_error &) {
  }
  EXPECT_EQ(storage.bytes_.size(), 281U); // a legal 63-byte tag is accepted

  MemoryStorage tight_storage;
  StimulationJournal tight_journal;
  ASSERT_EQ(tight_journal.open(tight_storage, JournalConfig{155U, 4U, 2048U}), JournalStatus::Ok);
  const std::size_t before = tight_storage.bytes_.size();
  EXPECT_EQ(tight_journal.journal_then_emit(make_intent(2U, "T", "U"),
                                            returning(make_outcome(2U, OutcomeKind::Delivered)), out),
            JournalStatus::RecordTooLarge);
  EXPECT_EQ(tight_storage.bytes_.size(), before);

  MemoryStorage tag_storage;
  StimulationJournal tag_journal;
  ASSERT_EQ(tag_journal.open(tag_storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);
  const std::size_t tag_before = tag_storage.bytes_.size();

  StimulationIntent empty_target = make_intent(3U, "T", "U");
  empty_target.target = Tag();
  EXPECT_EQ(tag_journal.journal_then_emit(
                empty_target, returning(make_outcome(3U, OutcomeKind::Delivered)), out),
            JournalStatus::RejectedConfiguration);

  StimulationIntent long_target = make_intent(4U, "T", "U");
  long_target.target = Tag(std::string(64U, 'z'));
  EXPECT_EQ(tag_journal.journal_then_emit(
                long_target, returning(make_outcome(4U, OutcomeKind::Delivered)), out),
            JournalStatus::RejectedConfiguration);

  StimulationIntent non_printable = make_intent(5U, "T", "U");
  non_printable.target = Tag(std::string("a\0b", 3U));
  EXPECT_EQ(tag_journal.journal_then_emit(
                non_printable, returning(make_outcome(5U, OutcomeKind::Delivered)), out),
            JournalStatus::RejectedConfiguration);
  EXPECT_EQ(tag_storage.bytes_.size(), tag_before);
}

/// \brief T26-TS-004: closed status vocabulary, stable precedence, and no-mutation on rejection.
TEST(T026JournalUnit, test_journal_status_determinism_and_no_mutation) {
  using xverse::xcom::validation::from_first;
  using xverse::xcom::validation::precedence_rank;
  using xverse::xcom::validation::status_name;

  const JournalStatus vocabulary[] = {
      JournalStatus::RejectedConfiguration, JournalStatus::RecordTooLarge,
      JournalStatus::CorruptRecord,         JournalStatus::PartialWrite,
      JournalStatus::WriteFailed,           JournalStatus::CapacityExhausted,
      JournalStatus::AlreadyResolved,       JournalStatus::NotFound,
      JournalStatus::EvidenceIncomplete,    JournalStatus::Ok,
  };
  const char *expected_names[] = {"RejectedConfiguration", "RecordTooLarge", "CorruptRecord",
                                  "PartialWrite",         "WriteFailed",    "CapacityExhausted",
                                  "AlreadyResolved",      "NotFound",       "EvidenceIncomplete",
                                  "Ok"};
  for (std::size_t index = 0; index < 10U; ++index) {
    EXPECT_EQ(status_name(vocabulary[index]), expected_names[index]);
    EXPECT_EQ(precedence_rank(vocabulary[index]), static_cast<std::uint8_t>(index));
  }
  EXPECT_EQ(from_first({JournalStatus::Ok, JournalStatus::WriteFailed,
                        JournalStatus::RejectedConfiguration}),
            JournalStatus::RejectedConfiguration);
  EXPECT_EQ(from_first({}), JournalStatus::Ok);

  std::vector<std::vector<std::uint8_t>> runs;
  for (std::size_t run = 0; run < 3U; ++run) {
    MemoryStorage storage;
    StimulationJournal journal;
    ASSERT_EQ(journal.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);
    const JournalSnapshot before = journal.snapshot();
    StimulationIntent invalid = make_intent(9U, "T", "U");
    invalid.tool = Tag();
    StimulationOutcome out;
    EXPECT_EQ(journal.journal_then_emit(
                  invalid, returning(make_outcome(9U, OutcomeKind::Delivered)), out),
              JournalStatus::RejectedConfiguration);
    EXPECT_EQ(journal.snapshot(), before);
    EXPECT_TRUE(storage.bytes_.empty());
    StimulationOutcome produced;
    ASSERT_EQ(journal.journal_then_emit(
                  make_intent(10U, "T", "U"), returning(make_outcome(10U, OutcomeKind::Rejected)),
                  produced),
              JournalStatus::Ok);
    runs.push_back(storage.bytes_);
  }
  ASSERT_EQ(runs.size(), 3U);
  EXPECT_EQ(runs[0], runs[1]);
  EXPECT_EQ(runs[1], runs[2]);
}

/// \brief T26-TS-005: snapshot and capacity accounting with the byte identity.
TEST(T026JournalUnit, test_journal_snapshot_and_capacity_accounting) {
  MemoryStorage storage;
  StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, JournalConfig{320U, 4U, 4096U}), JournalStatus::Ok);

  StimulationOutcome out;
  try {
    (void)journal.journal_then_emit(make_intent(1U, "T", "U"), throwing(), out);
    FAIL() << "throwing callback must propagate";
  } catch (const std::runtime_error &) {
  }
  JournalSnapshot snapshot = journal.snapshot();
  EXPECT_EQ(snapshot.retained_records, 1U);
  EXPECT_EQ(snapshot.retained_bytes, 157U);
  EXPECT_EQ(snapshot.complete_intents, 1U);
  EXPECT_EQ(snapshot.outcomes, 0U);
  EXPECT_EQ(snapshot.orphan_intents, 1U);

  ASSERT_EQ(journal.resolve(1U, make_outcome(1U, OutcomeKind::Delivered)), JournalStatus::Ok);
  snapshot = journal.snapshot();
  EXPECT_EQ(snapshot.retained_records, 2U);
  EXPECT_EQ(snapshot.retained_bytes, 157U + 66U);
  EXPECT_EQ(snapshot.complete_intents, 1U);
  EXPECT_EQ(snapshot.outcomes, 1U);
  EXPECT_EQ(snapshot.orphan_intents, 0U);
  EXPECT_EQ(storage.bytes_.size(), snapshot.retained_bytes);
}
