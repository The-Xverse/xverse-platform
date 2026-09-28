/**
 * \file recovery_tests.cpp
 * \brief T026 restart recovery, torn-tail/corrupt-frame handling, and durable provenance
 *        round-trip over a real local file.
 *
 * \details
 * The suite writes only bounded synthetic bytes to test-local scratch files beneath the
 * build-time `XCOM_T026_SCRATCH_DIR` path, removes only its own files, and never prints the
 * scratch path into public evidence. It performs no network, ambient, or external access.
 *
 * \ingroup xcom_stim
 */

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "xverse/xcom/stimulation_journal.hpp"

#ifndef XCOM_T026_SCRATCH_DIR
#error "XCOM_T026_SCRATCH_DIR must name a bounded test-local scratch directory"
#endif

namespace {

using xverse::xcom::validation::JournalConfig;
using xverse::xcom::validation::JournalSnapshot;
using xverse::xcom::validation::JournalStatus;
using xverse::xcom::validation::OutcomeKind;
using xverse::xcom::validation::PermitId;
using xverse::xcom::validation::Result;
using xverse::xcom::validation::StimulationIntent;
using xverse::xcom::validation::StimulationJournal;
using xverse::xcom::validation::StimulationOutcome;
using xverse::xcom::validation::Tag;
using xverse::xcom::validation::Timestamp;
using xverse::xcom::validation::canonical_digest;

/// \brief Bounded test-local scratch file with deterministic cleanup.
class ScratchFile {
public:
  /// \brief Creates the scratch directory and reserves a unique file path.
  /// \param name Unique case name within the scratch directory.
  explicit ScratchFile(const std::string &name) {
    std::filesystem::create_directories(XCOM_T026_SCRATCH_DIR);
    path_ = std::string(XCOM_T026_SCRATCH_DIR) + "/" + name;
    std::error_code code;
    std::filesystem::remove(path_, code);
  }

  /// \brief Removes the scratch file.
  ~ScratchFile() {
    std::error_code code;
    std::filesystem::remove(path_, code);
  }

  ScratchFile(const ScratchFile &) = delete;
  ScratchFile &operator=(const ScratchFile &) = delete;
  ScratchFile(ScratchFile &&) = delete;
  ScratchFile &operator=(ScratchFile &&) = delete;

  /// \brief Returns the scratch file path.
  [[nodiscard]] const std::string &path() const { return path_; }

private:
  std::string path_;
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

/// \brief Appends raw bytes to a scratch file.
void append_raw(const std::string &path, const std::vector<std::uint8_t> &bytes) {
  std::ofstream stream(path, std::ios::binary | std::ios::app);
  stream.write(reinterpret_cast<const char *>(bytes.data()),
               static_cast<std::streamsize>(bytes.size()));
}

/// \brief Reads every byte of a scratch file.
std::vector<std::uint8_t> read_raw(const std::string &path) {
  std::ifstream stream(path, std::ios::binary);
  return std::vector<std::uint8_t>(std::istreambuf_iterator<char>(stream),
                                   std::istreambuf_iterator<char>());
}

/// \brief Writes one orphan intent into a scratch file and closes it.
void write_orphan_intent(const std::string &path, std::uint64_t request_id) {
  StimulationJournal journal;
  ASSERT_EQ(journal.open_local_file(path, JournalConfig{320U, 8U, 4096U}), JournalStatus::Ok);
  StimulationOutcome out;
  try {
    (void)journal.journal_then_emit(make_intent(request_id), throwing(), out);
  } catch (const std::runtime_error &) {
  }
}

/// \brief Builds a byte-exact digest-valid intent frame with the requested raw tag bytes.
///
/// The production journal rejects invalid tags before writing, so this independently crafted
/// frame is the only way to present a durable frame whose declared tag length or bytes are
/// invalid; every digest is computed with the accepted `canonical_digest`.
/// \param target Raw target tag bytes; its length is recorded as-is.
/// \param tool Raw tool tag bytes; its length is recorded as-is.
/// \return The complete self-checking frame bytes.
std::vector<std::uint8_t> craft_intent_frame(const std::string &target, const std::string &tool) {
  std::vector<std::uint8_t> payload(109U, 0U);
  payload.push_back(static_cast<std::uint8_t>(target.size() & 0xFFU));
  payload.insert(payload.end(), target.begin(), target.end());
  payload.push_back(static_cast<std::uint8_t>(tool.size() & 0xFFU));
  payload.insert(payload.end(), tool.begin(), tool.end());

  std::vector<std::uint8_t> frame;
  frame.push_back('X');
  frame.push_back('J');
  frame.push_back('R');
  frame.push_back('N');
  frame.push_back(1U);
  frame.push_back(0U);
  frame.push_back(1U); // intent kind
  frame.push_back(0U); // flags
  const std::uint32_t declared = static_cast<std::uint32_t>(payload.size());
  for (std::size_t index = 0; index < 4U; ++index) {
    frame.push_back(static_cast<std::uint8_t>((declared >> (index * 8U)) & 0xFFU));
  }
  const PermitId payload_digest = canonical_digest(payload);
  frame.insert(frame.end(), payload_digest.begin(), payload_digest.end());
  frame.insert(frame.end(), payload.begin(), payload.end());
  const PermitId frame_digest = canonical_digest(frame);
  frame.insert(frame.end(), frame_digest.begin(), frame_digest.end());
  return frame;
}

} // namespace

/// \brief T26-TS-009: every complete-content row of detailed-design §6.4 across a reopen.
TEST(T026JournalRecovery, test_journal_restart_recovery_and_orphans) {
  const JournalConfig config{320U, 8U, 4096U};

  {
    ScratchFile scratch("t026-ts009-empty");
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.status, JournalStatus::Ok);
    EXPECT_EQ(report.complete_intents, 0U);
    EXPECT_EQ(report.outcomes, 0U);
    EXPECT_EQ(report.orphan_intents, 0U);
    EXPECT_EQ(report.discarded_trailing_bytes, 0U);
  }

  {
    ScratchFile scratch("t026-ts009-intent");
    write_orphan_intent(scratch.path(), 1U);
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.complete_intents, 1U);
    EXPECT_EQ(report.outcomes, 0U);
    EXPECT_EQ(report.orphan_intents, 1U);
    EXPECT_EQ(report.discarded_trailing_bytes, 0U);
    ASSERT_EQ(report.orphan_request_ids.size(), 1U);
    EXPECT_EQ(report.orphan_request_ids.front(), 1U);
  }

  {
    ScratchFile scratch("t026-ts009-pair");
    {
      StimulationJournal journal;
      ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
      StimulationOutcome out;
      ASSERT_EQ(journal.journal_then_emit(make_intent(1U),
                                          returning(make_outcome(1U, OutcomeKind::Delivered)), out),
                JournalStatus::Ok);
    }
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.complete_intents, 1U);
    EXPECT_EQ(report.outcomes, 1U);
    EXPECT_EQ(report.orphan_intents, 0U);
    EXPECT_EQ(report.discarded_trailing_bytes, 0U);
  }

  {
    ScratchFile scratch("t026-ts009-two-one");
    {
      StimulationJournal journal;
      ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
      StimulationOutcome out;
      ASSERT_EQ(journal.journal_then_emit(make_intent(1U),
                                          returning(make_outcome(1U, OutcomeKind::Delivered)), out),
                JournalStatus::Ok);
      try {
        (void)journal.journal_then_emit(make_intent(2U), throwing(), out);
      } catch (const std::runtime_error &) {
      }
    }
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.complete_intents, 2U);
    EXPECT_EQ(report.outcomes, 1U);
    EXPECT_EQ(report.orphan_intents, 1U);
  }

  // One-to-one orphan accounting over a crafted duplicate identity. The production write path
  // refuses a repeated request id, so this independently assembled file is the only way to present
  // two intents with the same identity and a single outcome; the second intent must remain an
  // orphan rather than being falsely marked resolved by the first intent's outcome.
  {
    ScratchFile scratch("t026-ts009-duplicate");
    ScratchFile source("t026-ts009-duplicate-source");
    {
      StimulationJournal journal;
      ASSERT_EQ(journal.open_local_file(source.path(), config), JournalStatus::Ok);
      StimulationOutcome out;
      ASSERT_EQ(journal.journal_then_emit(make_intent(7U),
                                          returning(make_outcome(7U, OutcomeKind::Delivered)), out),
                JournalStatus::Ok);
    }
    const std::vector<std::uint8_t> source_bytes = read_raw(source.path());
    ASSERT_EQ(source_bytes.size(), 223U);
    const std::vector<std::uint8_t> intent_frame(source_bytes.begin(),
                                                 source_bytes.begin() + 157);
    append_raw(scratch.path(), source_bytes);
    append_raw(scratch.path(), intent_frame);
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.status, JournalStatus::Ok);
    EXPECT_EQ(report.complete_intents, 2U);
    EXPECT_EQ(report.outcomes, 1U);
    EXPECT_EQ(report.orphan_intents, 1U);
    ASSERT_EQ(report.orphan_request_ids.size(), 1U);
    EXPECT_EQ(report.orphan_request_ids.front(), 7U);

    // A resolution resolves exactly one still-unresolved intent (the duplicate), not both.
    EXPECT_EQ(journal.resolve(7U, make_outcome(7U, OutcomeKind::Unknown)), JournalStatus::Ok);
    EXPECT_EQ(journal.snapshot().orphan_intents, 0U);
    EXPECT_EQ(journal.resolve(7U, make_outcome(7U, OutcomeKind::Unknown)),
              JournalStatus::AlreadyResolved);
  }

  {
    ScratchFile scratch("t026-ts009-torn");
    ScratchFile source("t026-ts009-torn-source");
    {
      StimulationJournal journal;
      ASSERT_EQ(journal.open_local_file(source.path(), config), JournalStatus::Ok);
      StimulationOutcome out;
      ASSERT_EQ(journal.journal_then_emit(make_intent(1U),
                                          returning(make_outcome(1U, OutcomeKind::Delivered)), out),
                JournalStatus::Ok);
    }
    const std::vector<std::uint8_t> source_bytes = read_raw(source.path());
    ASSERT_EQ(source_bytes.size(), 223U);
    write_orphan_intent(scratch.path(), 1U);
    append_raw(scratch.path(),
               std::vector<std::uint8_t>(source_bytes.begin() + 157, source_bytes.begin() + 197));
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.complete_intents, 1U);
    EXPECT_EQ(report.orphan_intents, 1U);
    EXPECT_EQ(report.discarded_trailing_bytes, 40U);
    EXPECT_EQ(read_raw(scratch.path()).size(), 157U);
  }

  {
    ScratchFile scratch("t026-ts009-garbage");
    {
      StimulationJournal journal;
      ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
      StimulationOutcome out;
      ASSERT_EQ(journal.journal_then_emit(make_intent(1U),
                                          returning(make_outcome(1U, OutcomeKind::Delivered)), out),
                JournalStatus::Ok);
    }
    std::vector<std::uint8_t> garbage{1U, 2U, 3U, 4U, 5U};
    append_raw(scratch.path(), garbage);
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.complete_intents, 1U);
    EXPECT_EQ(report.outcomes, 1U);
    EXPECT_EQ(report.orphan_intents, 0U);
    EXPECT_EQ(report.discarded_trailing_bytes, 5U);
  }
}

/// \brief T26-TS-010: torn-tail discard, `CorruptRecord` stop, and complete-record preservation.
TEST(T026JournalRecovery, test_journal_torn_tail_and_corrupt_frame) {
  const JournalConfig config{320U, 8U, 4096U};

  {
    ScratchFile scratch("t026-ts010-torn");
    ScratchFile source("t026-ts010-source");
    {
      StimulationJournal journal;
      ASSERT_EQ(journal.open_local_file(source.path(), config), JournalStatus::Ok);
      StimulationOutcome out;
      ASSERT_EQ(journal.journal_then_emit(make_intent(1U),
                                          returning(make_outcome(1U, OutcomeKind::Delivered)), out),
                JournalStatus::Ok);
    }
    const std::vector<std::uint8_t> source_bytes = read_raw(source.path());
    ASSERT_EQ(source_bytes.size(), 223U);
    const std::vector<std::uint8_t> outcome_frame(source_bytes.begin() + 157,
                                                  source_bytes.begin() + 223);
    write_orphan_intent(scratch.path(), 5U);
    append_raw(scratch.path(), std::vector<std::uint8_t>(outcome_frame.begin(),
                                                         outcome_frame.begin() + 40));
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.status, JournalStatus::Ok);
    EXPECT_EQ(report.complete_intents, 1U);
    EXPECT_EQ(report.outcomes, 0U);
    EXPECT_EQ(report.orphan_intents, 1U);
    EXPECT_EQ(report.discarded_trailing_bytes, 40U);
    EXPECT_EQ(read_raw(scratch.path()).size(), 157U);
  }

  {
    ScratchFile scratch("t026-ts010-corrupt");
    ScratchFile source("t026-ts010-corrupt-source");
    {
      StimulationJournal journal;
      ASSERT_EQ(journal.open_local_file(source.path(), config), JournalStatus::Ok);
      StimulationOutcome out;
      ASSERT_EQ(journal.journal_then_emit(make_intent(1U),
                                          returning(make_outcome(1U, OutcomeKind::Delivered)), out),
                JournalStatus::Ok);
    }
    const std::vector<std::uint8_t> source_bytes = read_raw(source.path());
    std::vector<std::uint8_t> outcome_frame(source_bytes.begin() + 157, source_bytes.begin() + 223);
    outcome_frame[30U] ^= 0xFFU; // corrupt one payload byte, leaving length and kind intact
    write_orphan_intent(scratch.path(), 6U);
    append_raw(scratch.path(), outcome_frame);
    StimulationJournal journal;
    const JournalStatus open_status = journal.open_local_file(scratch.path(), config);
    EXPECT_EQ(open_status, JournalStatus::CorruptRecord);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.status, JournalStatus::CorruptRecord);
    EXPECT_EQ(report.complete_intents, 1U);
    EXPECT_EQ(report.outcomes, 0U);
    EXPECT_EQ(report.orphan_intents, 1U);
    EXPECT_EQ(report.retained_bytes, 157U);
    EXPECT_EQ(read_raw(scratch.path()).size(), 157U + 66U); // the defect is preserved, not dropped
    EXPECT_EQ(journal.recovered_intents().size(), 1U);
  }
}

/// \brief T26-TS-011: durable provenance round-trip of every intent identity field.
TEST(T026JournalRecovery, test_journal_provenance_roundtrip_matrix) {
  const JournalConfig config{320U, 8U, 4096U};
  ScratchFile scratch("t026-ts011-provenance");

  const std::vector<StimulationIntent> intents = {
      make_intent(11U, "alpha", "tool-a"),
      make_intent(22U, "beta-target", "tool-b"),
      make_intent(33U, "gamma", "tool-c"),
  };
  {
    StimulationJournal journal;
    ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
    for (const StimulationIntent &intent : intents) {
      StimulationOutcome out;
      try {
        (void)journal.journal_then_emit(intent, throwing(), out);
      } catch (const std::runtime_error &) {
      }
    }
  }

  StimulationJournal journal;
  ASSERT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::Ok);
  const std::vector<StimulationIntent> recovered = journal.recovered_intents();
  ASSERT_EQ(recovered.size(), intents.size());
  for (std::size_t index = 0; index < intents.size(); ++index) {
    EXPECT_EQ(recovered[index].permit_id, intents[index].permit_id);
    EXPECT_EQ(recovered[index].session_id, intents[index].session_id);
    EXPECT_EQ(recovered[index].plan_digest, intents[index].plan_digest);
    EXPECT_EQ(recovered[index].request_id, intents[index].request_id);
    EXPECT_EQ(recovered[index].correlation_id, intents[index].correlation_id);
    EXPECT_EQ(recovered[index].causation_id, intents[index].causation_id);
    EXPECT_EQ(recovered[index].action_mask, intents[index].action_mask);
    EXPECT_EQ(recovered[index].target, intents[index].target);
    EXPECT_EQ(recovered[index].tool, intents[index].tool);
    EXPECT_EQ(recovered[index].quota_cost, intents[index].quota_cost);
    EXPECT_EQ(recovered[index].clock_domain, intents[index].clock_domain);
    EXPECT_EQ(recovered[index].scheduled_at, intents[index].scheduled_at);
    EXPECT_EQ(recovered[index].immediate, intents[index].immediate);
    EXPECT_EQ(recovered[index], intents[index]);
  }
}

/// \brief T26-TS-017: an over-bound durable journal fails closed at recovery.
///
/// Closes internal-review finding T026-IR2-05-F01: reopening a journal whose durable state
/// exceeds the declared retained-record or byte bound must not report `Ok`, must present no
/// over-bound index, and must refuse further appends without emitting.
TEST(T026JournalRecovery, test_journal_over_bound_recovery_fails_closed) {
  // (a) Durable bytes exceed max_journal_bytes when reopened with a tighter byte bound.
  {
    ScratchFile scratch("t026-ts017-bytes");
    {
      StimulationJournal writer;
      ASSERT_EQ(writer.open_local_file(scratch.path(), JournalConfig{320U, 64U, 16384U}),
                JournalStatus::Ok);
      for (std::uint64_t request_id = 1U; request_id <= 6U; ++request_id) {
        StimulationOutcome out;
        ASSERT_EQ(writer.journal_then_emit(
                      make_intent(request_id, "T", "U"),
                      returning(make_outcome(request_id, OutcomeKind::Delivered)), out),
                  JournalStatus::Ok);
      }
    }
    ASSERT_GT(read_raw(scratch.path()).size(), 320U);

    StimulationJournal journal;
    const JournalStatus status =
        journal.open_local_file(scratch.path(), JournalConfig{320U, 2U, 320U});
    EXPECT_NE(status, JournalStatus::Ok);
    EXPECT_EQ(status, JournalStatus::CapacityExhausted);
    const JournalSnapshot snapshot = journal.snapshot();
    EXPECT_LE(snapshot.retained_records, 2U);
    EXPECT_LE(snapshot.retained_bytes, 320U);
    EXPECT_LE(journal.recovered_intents().size(), 2U);
    EXPECT_LE(journal.recovered_outcomes().size(), 2U);

    // The over-bound journal refuses a further append and emits nothing.
    std::size_t emissions = 0U;
    StimulationOutcome out;
    EXPECT_EQ(journal.journal_then_emit(
                  make_intent(99U, "T", "U"),
                  [&emissions](const StimulationIntent &intent) {
                    ++emissions;
                    return make_outcome(intent.request_id, OutcomeKind::Delivered);
                  },
                  out),
              JournalStatus::CapacityExhausted);
    EXPECT_EQ(emissions, 0U);
  }

  // (b) Complete frames exceed max_retained_records while the durable bytes stay in bound.
  {
    ScratchFile scratch("t026-ts017-records");
    {
      StimulationJournal writer;
      ASSERT_EQ(writer.open_local_file(scratch.path(), JournalConfig{320U, 64U, 16384U}),
                JournalStatus::Ok);
      for (std::uint64_t request_id = 1U; request_id <= 4U; ++request_id) {
        StimulationOutcome out;
        try {
          (void)writer.journal_then_emit(make_intent(request_id, "T", "U"), throwing(), out);
        } catch (const std::runtime_error &) {
        }
      }
    }
    ASSERT_EQ(read_raw(scratch.path()).size(), 4U * 157U);

    StimulationJournal journal;
    const JournalStatus status =
        journal.open_local_file(scratch.path(), JournalConfig{320U, 2U, 4096U});
    EXPECT_NE(status, JournalStatus::Ok);
    EXPECT_EQ(status, JournalStatus::CapacityExhausted);
    const JournalSnapshot snapshot = journal.snapshot();
    EXPECT_LE(snapshot.retained_records, 2U);
    EXPECT_LE(snapshot.retained_bytes, 4096U);
    EXPECT_LE(journal.recovered_intents().size(), 2U);
    EXPECT_EQ(journal.recovered_outcomes().size(), 0U);
  }
}

/// \brief T26-TS-018: a digest-valid frame with an out-of-contract tag is corrupt at recovery.
///
/// Closes internal-review finding T026-IR2-05-F03: recovery must reject a frame whose declared
/// target/tool length exceeds `Tag::max_length`, or whose tag bytes are empty/NUL/non-printable,
/// with `CorruptRecord` and no recovered value and no false orphan.
TEST(T026JournalRecovery, test_journal_over_long_recovered_tag_is_corrupt) {
  const JournalConfig config{320U, 8U, 4096U};

  {
    ScratchFile scratch("t026-ts018-over-long");
    const std::vector<std::uint8_t> frame = craft_intent_frame(std::string(64U, 'z'), "U");
    ASSERT_EQ(frame.size(), 44U + 111U + 64U + 1U);
    append_raw(scratch.path(), frame);

    StimulationJournal journal;
    EXPECT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::CorruptRecord);
    const auto report = journal.last_recovery();
    EXPECT_EQ(report.status, JournalStatus::CorruptRecord);
    EXPECT_EQ(report.complete_intents, 0U);
    EXPECT_EQ(report.outcomes, 0U);
    EXPECT_EQ(report.orphan_intents, 0U);
    EXPECT_TRUE(journal.recovered_intents().empty());
  }

  {
    ScratchFile scratch("t026-ts018-nul");
    const std::vector<std::uint8_t> frame = craft_intent_frame(std::string("a\0b", 3U), "U");
    append_raw(scratch.path(), frame);

    StimulationJournal journal;
    EXPECT_EQ(journal.open_local_file(scratch.path(), config), JournalStatus::CorruptRecord);
    EXPECT_EQ(journal.last_recovery().orphan_intents, 0U);
    EXPECT_TRUE(journal.recovered_intents().empty());
  }
}
