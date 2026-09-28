/**
 * \file stimulation_journal.hpp
 * \brief T026 bounded durable stimulation intent/outcome journal: a payload-free,
 *        append-only, self-checking journal with an explicit host storage seam.
 *
 * \details
 * This header is the source-free T026 engineering candidate of `xverse::xcom::validation`.
 * It provides a bounded durable journal that records a payload-free stimulation intent
 * durably *before* a host-supplied emission callback runs, then records an explicit
 * outcome; an intent that loses its outcome is surfaced as an explicit `EvidenceIncomplete`
 * orphan across a restart and is never converted into success. The unit uses only the C++
 * standard library plus the accepted T025 `validation_session.hpp` identity/diagnostic/digest
 * vocabulary, which it consumes read-only and never redefines.
 *
 * The journal performs no authorization, schema, target, direction, action, quota, loop, or
 * ownership validation (T027), emits nothing on a normal route, injects nothing, invokes no
 * service, and implements no routed item, provider, endpoint, observation tap, gateway,
 * payload decoder, or unrestricted log (T028–T034). It accesses only a host-supplied storage
 * seam or a host-supplied local file path and performs no network, ambient-configuration,
 * secret, dynamic-load, subprocess, or legacy access.
 *
 * \note This is an internal candidate. It does not establish accepted X-COM delivery,
 *       predecessor regression, source compatibility, protected verification, or
 *       production readiness. "Durable" means a declared write and sync through the host
 *       storage seam on the local filesystem; it is not a claim of crash consistency,
 *       media-failure atomicity, encryption, or tamper resistance.
 *
 * \ingroup xcom_stim
 */

#ifndef XVERSE_XCOM_STIMULATION_JOURNAL_HPP_
#define XVERSE_XCOM_STIMULATION_JOURNAL_HPP_

#include <cstddef>
#include <cstdint>
#include <functional>
#include <initializer_list>
#include <memory>
#include <mutex>
#include <span>
#include <string>
#include <string_view>
#include <type_traits>
#include <vector>

#include "xverse/xcom/validation_session.hpp"

namespace xverse {
namespace xcom {
namespace validation {

/// \brief Fixed frame magic, little-endian on disk as the bytes `X` `J` `R` `N`.
/// \unitspec{T026-U-FRAME}
inline constexpr std::uint32_t kJournalFrameMagic = 0x4E524A58U;
/// \brief Fixed frame format version.
/// \unitspec{T026-U-FRAME}
inline constexpr std::uint16_t kJournalFormatVersion = 1U;
/// \brief Frame header (28 bytes) plus frame trailer (16 bytes).
/// \unitspec{T026-U-FRAME}
inline constexpr std::size_t kJournalFrameOverhead = 44U;
/// \brief Minimum intent payload (permit, session, plan, ids, action, quota, clock, time, tags).
/// \unitspec{T026-U-FRAME}
inline constexpr std::size_t kJournalMinIntentPayload = 111U;
/// \brief Exact outcome payload size.
/// \unitspec{T026-U-FRAME}
inline constexpr std::size_t kJournalOutcomePayload = 22U;
/// \brief Configuration floor in bytes: the 44-byte frame overhead plus the 111-byte minimum
///        intent payload computed for empty tags. It is the arithmetic minimum accepted by
///        `JournalConfig`, not a legal record: empty tags are rejected (T026-SR-004), so the
///        smallest legal intent record is 157 bytes (one printable byte in each tag).
/// \unitspec{T026-U-FRAME}
inline constexpr std::size_t kJournalMinRecordBytes = 155U;
/// \brief Largest legal record frame (intent with two 63-byte tags).
/// \unitspec{T026-U-FRAME}
inline constexpr std::size_t kJournalMaxRecordBytes = 281U;
/// \brief Frame kind byte for an intent record.
/// \unitspec{T026-U-FRAME}
inline constexpr std::uint8_t kJournalKindIntent = 1U;
/// \brief Frame kind byte for an outcome record.
/// \unitspec{T026-U-FRAME}
inline constexpr std::uint8_t kJournalKindOutcome = 2U;

/**
 * \brief Closed, enumerable, deterministically ordered journal status vocabulary.
 *
 * Declaration order is precedence order, most severe first, so a lower
 * `precedence_rank` binds earlier and `from_first` retains the most severe applicable code.
 * The vocabulary is a comparison-free, payload-free enumeration.
 * \ownership platform-owns-shared; the value is a plain copyable enum.
 * \lifetime value type; no lifetime coupling.
 * \thread_safety immutable value, safe to copy across threads.
 * \failure every enumerator names one bounded, explicit failure or success outcome; no
 *          enumerator is a catch-all.
 */
enum class JournalStatus : std::uint8_t {
  RejectedConfiguration, ///< Invalid/zero/inconsistent configuration or invalid tag/bound input.
  RecordTooLarge,        ///< The encoded frame exceeds `max_record_bytes`.
  CorruptRecord,         ///< A complete frame failed its integrity check during the scan.
  PartialWrite,          ///< A short append or a torn trailing frame was detected.
  WriteFailed,           ///< Append, sync, or truncate I/O failure (including disk full).
  CapacityExhausted,     ///< The retained-record or retained-byte bound was reached.
  AlreadyResolved,       ///< Every retained intent with the identity already has a distinct outcome.
  NotFound,              ///< No intent matches the referenced request identity.
  EvidenceIncomplete,    ///< The intent is durable but no durable outcome exists yet.
  Ok,                    ///< The operation completed and is durable.
};

/// \brief Returns the stable, non-empty name of a journal status.
/// \param status A journal status.
/// \return A stable, non-empty view; the same input always yields the same name.
/// \unitspec{T026-U-STATUS}
[[nodiscard]] std::string_view status_name(JournalStatus status) noexcept;

/// \brief Returns the zero-based precedence rank of a journal status.
/// \param status A journal status.
/// \return The zero-based precedence rank (lower rank binds earlier).
/// \unitspec{T026-U-STATUS}
[[nodiscard]] std::uint8_t precedence_rank(JournalStatus status) noexcept;

/// \brief Retains the highest-precedence (lowest-rank) applicable status.
/// \param applicable Candidate statuses.
/// \return The candidate with the lowest precedence rank, or `JournalStatus::Ok` for an
///         empty list.
/// \unitspec{T026-U-STATUS}
[[nodiscard]] JournalStatus
from_first(std::initializer_list<JournalStatus> applicable) noexcept;

/// \brief Closed outcome-kind vocabulary; `Unknown` is a first-class explicit value.
/// \unitspec{T026-U-MODEL}
enum class OutcomeKind : std::uint8_t {
  Delivered = 1U, ///< The stimulus was delivered.
  Rejected = 2U,  ///< The host rejected the stimulus.
  Expired = 3U,   ///< The stimulus expired before delivery.
  Cancelled = 4U, ///< The stimulus was cancelled.
  Unknown = 5U,   ///< The outcome is explicitly unknown; never relabelled delivered.
};

/// \brief Returns the stable, non-empty name of an outcome kind.
/// \param kind An outcome kind.
/// \return A stable, non-empty view.
/// \unitspec{T026-U-MODEL}
[[nodiscard]] std::string_view outcome_kind_name(OutcomeKind kind) noexcept;

/// \brief Production local-file storage implementation; defined in the unit source.
/// \unitspec{T026-U-STORAGE}
struct LocalFileStorage;

/**
 * \brief Bounded journal configuration: every record, count, and byte is declared and finite.
 *
 * An open with a zero bound, `max_record_bytes < 155`, or `max_journal_bytes <
 * max_record_bytes` is `RejectedConfiguration` and mutates no file.
 * \ownership platform-owns-shared; a caller-owned, copyable value.
 * \lifetime value type; copied into the journal at open.
 * \thread_safety immutable value, safe to copy across threads.
 * \failure an inconsistent configuration is rejected at open; no append occurs.
 */
struct JournalConfig {
  /// \brief Maximum encoded record frame size in bytes; must be at least 155.
  /// \unitspec{T026-U-MODEL}
  std::size_t max_record_bytes{320U};
  /// \brief Maximum number of retained complete records; must be non-zero.
  /// \unitspec{T026-U-MODEL}
  std::size_t max_retained_records{64U};
  /// \brief Maximum durable journal byte size; must be at least `max_record_bytes`.
  /// \unitspec{T026-U-MODEL}
  std::size_t max_journal_bytes{16384U};
};

/**
 * \brief Bounded, payload-free stimulation intent record.
 *
 * The record carries only identity and bounded metadata: permit, session, plan digest,
 * request/correlation/causation identity, action mask, bounded target/tool tags, quota
 * cost, clock domain, scheduled timestamp, and an explicit immediate flag. It carries no
 * signal/message payload bytes, value body, address, free-form text, or secret.
 * \ownership platform-owns-shared; a caller-owned, copyable value.
 * \lifetime value type; copied into a frame and never retained by reference.
 * \thread_safety immutable value, safe to copy across threads.
 * \failure invalid/empty/over-long/non-printable tags are rejected at the journal boundary.
 */
struct StimulationIntent {
  /// \brief Permit identity bound into the intent.
  /// \unitspec{T026-U-MODEL}
  PermitId permit_id{};
  /// \brief Session identity bound into the intent.
  /// \unitspec{T026-U-MODEL}
  SessionId session_id{};
  /// \brief Plan digest bound into the intent.
  /// \unitspec{T026-U-MODEL}
  PlanDigest plan_digest{};
  /// \brief Request identity; the durable key that links an intent to its outcome. It is unique
  ///        across the retained intents: a second intent carrying a retained identity is refused.
  /// \unitspec{T026-U-MODEL}
  std::uint64_t request_id{0U};
  /// \brief Correlation identity.
  /// \unitspec{T026-U-MODEL}
  std::uint64_t correlation_id{0U};
  /// \brief Causation identity.
  /// \unitspec{T026-U-MODEL}
  std::uint64_t causation_id{0U};
  /// \brief Action mask; recorded only, never authorized here.
  /// \unitspec{T026-U-MODEL}
  ActionMask action_mask{0U};
  /// \brief Bounded target tag.
  /// \unitspec{T026-U-MODEL}
  Tag target{};
  /// \brief Bounded tool tag.
  /// \unitspec{T026-U-MODEL}
  Tag tool{};
  /// \brief Recorded quota cost; informational only.
  /// \unitspec{T026-U-MODEL}
  std::uint32_t quota_cost{0U};
  /// \brief Authority-issued clock-domain token.
  /// \unitspec{T026-U-MODEL}
  ClockDomainId clock_domain{kInvalidClockDomain};
  /// \brief Scheduled timestamp in the record's clock domain.
  /// \unitspec{T026-U-MODEL}
  Timestamp scheduled_at{0};
  /// \brief Explicit immediate/scheduled label.
  /// \unitspec{T026-U-MODEL}
  bool immediate{false};

  /// \brief Value equality over every field.
  /// \unitspec{T026-U-MODEL}
  friend bool operator==(const StimulationIntent &, const StimulationIntent &) noexcept =
      default;
};

/**
 * \brief Bounded, payload-free explicit stimulation outcome record.
 *
 * \ownership platform-owns-shared; a caller-owned, copyable value.
 * \lifetime value type; copied into a frame and never retained by reference.
 * \thread_safety immutable value, safe to copy across threads.
 * \failure an absent outcome stays `EvidenceIncomplete`; `Unknown` is never relabelled.
 */
struct StimulationOutcome {
  /// \brief Request identity this outcome references.
  /// \unitspec{T026-U-MODEL}
  std::uint64_t request_id{0U};
  /// \brief Closed outcome kind.
  /// \unitspec{T026-U-MODEL}
  OutcomeKind kind{OutcomeKind::Unknown};
  /// \brief Accepted T025 bounded diagnostic code.
  /// \unitspec{T026-U-MODEL}
  Result reason{Result::Ok};
  /// \brief Authority-issued clock-domain token.
  /// \unitspec{T026-U-MODEL}
  ClockDomainId clock_domain{kInvalidClockDomain};
  /// \brief Observed timestamp in the record's clock domain.
  /// \unitspec{T026-U-MODEL}
  Timestamp observed_at{0};

  /// \brief Value equality over every field.
  /// \unitspec{T026-U-MODEL}
  friend bool operator==(const StimulationOutcome &, const StimulationOutcome &) noexcept =
      default;
};

// Compile-time bounded/no-payload-constructor rule: neither record may be constructible from a
// byte container or free-form text, and both must stay within their declared size bounds. These
// assertions reject a payload-accepting constructor and unbounded growth of `sizeof`; the absence
// of a payload-bearing member is established by this declaration and the design inspection, not
// asserted here (an added member that keeps the type constructible from these argument types and
// within the size bound is not detectable without reflection).
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

/// \brief Immutable bounded snapshot of the journal's durable counters.
/// \unitspec{T026-U-JOURNAL}
struct JournalSnapshot {
  /// \brief Number of complete retained records (intents plus outcomes).
  /// \unitspec{T026-U-JOURNAL}
  std::size_t retained_records{0U};
  /// \brief Durable byte count of the complete retained records.
  /// \unitspec{T026-U-JOURNAL}
  std::size_t retained_bytes{0U};
  /// \brief Number of complete retained intent records.
  /// \unitspec{T026-U-JOURNAL}
  std::size_t complete_intents{0U};
  /// \brief Number of complete retained outcome records.
  /// \unitspec{T026-U-JOURNAL}
  std::size_t outcomes{0U};
  /// \brief Number of intents with no distinct matching durable outcome (one-to-one accounting).
  /// \unitspec{T026-U-JOURNAL}
  std::size_t orphan_intents{0U};

  /// \brief Value equality over every field.
  /// \unitspec{T026-U-JOURNAL}
  friend bool operator==(const JournalSnapshot &, const JournalSnapshot &) noexcept =
      default;
};

/// \brief Deterministic recovery summary of one journal scan.
/// \unitspec{T026-U-RECOVERY}
struct RecoveryReport {
  /// \brief Scan status: `Ok`, `CorruptRecord`, `PartialWrite`, `WriteFailed`, or
  ///        `CapacityExhausted` (the durable journal exceeds a declared bound).
  /// \unitspec{T026-U-RECOVERY}
  JournalStatus status{JournalStatus::Ok};
  /// \brief Number of complete intent frames retained.
  /// \unitspec{T026-U-RECOVERY}
  std::size_t complete_intents{0U};
  /// \brief Number of complete outcome frames retained.
  /// \unitspec{T026-U-RECOVERY}
  std::size_t outcomes{0U};
  /// \brief Number of intents with no distinct matching durable outcome (one-to-one accounting).
  /// \unitspec{T026-U-RECOVERY}
  std::size_t orphan_intents{0U};
  /// \brief Number of trailing bytes discarded as a torn/truncated frame.
  /// \unitspec{T026-U-RECOVERY}
  std::size_t discarded_trailing_bytes{0U};
  /// \brief Number of complete retained records.
  /// \unitspec{T026-U-RECOVERY}
  std::size_t retained_records{0U};
  /// \brief Durable byte count of the complete retained records.
  /// \unitspec{T026-U-RECOVERY}
  std::size_t retained_bytes{0U};
  /// \brief Request identities of the orphan intents, in durable order.
  /// \unitspec{T026-U-RECOVERY}
  std::vector<std::uint64_t> orphan_request_ids{};
};

/**
 * \brief Bounded durable stimulation intent/outcome journal over a host storage seam.
 *
 * The journal records a payload-free intent durably before invoking a host-supplied
 * single-shot emission callback exactly once and outside the journal mutex, then records
 * the explicit outcome. It enforces a declared maximum record size, retained-record count,
 * and journal byte size, and fails closed with `CapacityExhausted` rather than dropping,
 * overwriting, or truncating a complete retained record. Each record is one self-checking
 * frame; a short append, sync failure, or torn trailing frame fails closed and discards no
 * complete preceding record. Re-opening an existing journal scans its complete frames and
 * reports every intent without an outcome as an orphan classified `EvidenceIncomplete`; a
 * durable journal that already exceeds a declared retained-record or byte bound fails closed
 * at recovery with `CapacityExhausted`, presents no over-bound index, and refuses further
 * appends.
 *
 * \ownership platform-owns-shared; the journal owns its bounded index and, for
 *            `open_local_file`, its file storage. A caller-supplied `Storage` reference is
 *            non-owning and MUST outlive the journal.
 * \lifetime session-scoped; the journal retains at most `max_retained_records` records and
 *           a storage reference must outlive the journal and every callback.
 * \thread_safety internally-synchronized; one per-journal mutex serializes appends,
 *               capacity accounting, boundary restoration, and the index, and exactly one
 *               declared writer exists. The emission callback is invoked with the mutex
 *               released and MUST NOT be invoked concurrently by the caller.
 * \failure every operation returns an explicit `JournalStatus`; a failure never reports
 *          success, never mutates a complete retained record, and never invokes the
 *          emission callback on a failed intent append or sync.
 */
class StimulationJournal {
public:
  /**
   * \brief Host storage seam: the only I/O boundary of the journal.
   *
   * A concrete storage is host-supplied for `open` (and host-injected for deterministic
   * fault testing) or owned by the journal for `open_local_file`. It is non-owning with
   * respect to the journal and must outlive it.
   * \ownership platform-owns-shared; the caller owns a supplied implementation.
   * \lifetime must outlive the journal that references it.
   * \thread_safety the journal serializes every call; the implementation need not be
   *               internally synchronized for one journal.
   * \failure each method returns an explicit `JournalStatus`; no method throws on an I/O
   *          failure.
   */
  class Storage {
  public:
    /// \brief Destructor.
    /// \unitspec{T026-U-STORAGE}
    virtual ~Storage() = default;

    /// \brief Appends bytes at the durable end.
    /// \param bytes Bytes to append.
    /// \return `JournalStatus::Ok` when every byte was appended,
    ///         `JournalStatus::PartialWrite` when fewer bytes than requested were appended,
    ///         or `JournalStatus::WriteFailed` on an I/O failure.
    /// \unitspec{T026-U-STORAGE}
    virtual JournalStatus append(std::span<const std::uint8_t> bytes) = 0;

    /// \brief Flushes the durable end to stable storage.
    /// \return `JournalStatus::Ok` or `JournalStatus::WriteFailed`.
    /// \unitspec{T026-U-STORAGE}
    virtual JournalStatus sync() = 0;

    /// \brief Reads every durable byte.
    /// \param out Receives every durable byte; replaced on success.
    /// \return `JournalStatus::Ok` or `JournalStatus::WriteFailed`.
    /// \unitspec{T026-U-STORAGE}
    virtual JournalStatus read_all(std::vector<std::uint8_t> &out) = 0;

    /// \brief Returns the current durable byte count.
    /// \return The current durable byte count, or `0` when unavailable.
    /// \unitspec{T026-U-STORAGE}
    [[nodiscard]] virtual std::size_t size() = 0;

    /// \brief Restores the durable end to a known-good offset.
    /// \param size The known-good offset.
    /// \return `JournalStatus::Ok` or `JournalStatus::WriteFailed`.
    /// \unitspec{T026-U-STORAGE}
    virtual JournalStatus truncate(std::size_t size) = 0;
  };

  /// \brief Host emission callback invoked exactly once per successful intent append.
  /// \unitspec{T026-U-JOURNAL}
  using EmissionCallback = std::function<StimulationOutcome(const StimulationIntent &)>;

  /// \brief Constructs an unopened journal; call `open` or `open_local_file` before use.
  /// \unitspec{T026-U-JOURNAL}
  StimulationJournal() noexcept;

  /// \brief Destructor; releases any owned local-file storage.
  /// \unitspec{T026-U-JOURNAL}
  ~StimulationJournal();

  /// \brief Copy construction is deleted; the journal is non-copyable.
  /// \unitspec{T026-U-JOURNAL}
  StimulationJournal(const StimulationJournal &) = delete;
  /// \brief Copy assignment is deleted; the journal is non-copyable.
  /// \unitspec{T026-U-JOURNAL}
  StimulationJournal &operator=(const StimulationJournal &) = delete;
  /// \brief Move construction is deleted; the journal is non-movable.
  /// \unitspec{T026-U-JOURNAL}
  StimulationJournal(StimulationJournal &&) = delete;
  /// \brief Move assignment is deleted; the journal is non-movable.
  /// \unitspec{T026-U-JOURNAL}
  StimulationJournal &operator=(StimulationJournal &&) = delete;

  /// \brief Opens the journal over a host storage seam and performs one recovery scan.
  /// \param storage Host storage; non-owning and must outlive the journal.
  /// \param config Bounded configuration.
  /// \return `JournalStatus::RejectedConfiguration` for an invalid configuration (no
  ///         mutation), otherwise the recovery scan status (`Ok`, `CorruptRecord`,
  ///         `PartialWrite`, `WriteFailed`, or `CapacityExhausted` when the durable journal
  ///         already exceeds a declared retained-record or byte bound).
  /// \pre `storage` outlives the journal.
  /// \post on `Ok` the journal accepts appends and reports the recovered index.
  /// \unitspec{T026-U-JOURNAL}
  JournalStatus open(Storage &storage, const JournalConfig &config);

  /// \brief Opens the journal over a host-supplied local file path.
  /// \param path Local file path; must be non-empty.
  /// \param config Bounded configuration.
  /// \return `JournalStatus::RejectedConfiguration` for an empty path or an invalid
  ///         configuration (no file created or mutated), `JournalStatus::WriteFailed` when
  ///         the file cannot be opened, otherwise the recovery scan status.
  /// \pre the parent directory of `path` exists; the journal creates no directory.
  /// \unitspec{T026-U-JOURNAL}
  JournalStatus open_local_file(const std::string &path, const JournalConfig &config);

  /// \brief Re-runs the recovery scan and returns its deterministic summary.
  /// \return The recovery summary; a torn trailing frame is discarded, an intent with no
  ///         outcome is reported as an orphan, and a durable journal that exceeds a declared
  ///         retained-record or byte bound fails closed with `CapacityExhausted` and presents
  ///         no over-bound index. Does not otherwise mutate durable state.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] RecoveryReport recover();

  /// \brief Returns the summary of the most recent scan (from `open` or `recover`).
  /// \return A copy of the most recent recovery summary.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] RecoveryReport last_recovery() const;

  /// \brief Returns the bounded durable counters without a scan.
  /// \return The bounded counters.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] JournalSnapshot snapshot() const;

  /// \brief Returns the complete retained intents, in durable order.
  /// \return At most `max_retained_records` recovered, payload-free intent values.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] std::vector<StimulationIntent> recovered_intents() const;

  /// \brief Returns the complete retained outcomes, in durable order.
  /// \return At most `max_retained_records` recovered, payload-free outcome values.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] std::vector<StimulationOutcome> recovered_outcomes() const;

  /// \brief Durably journals an intent, emits once outside the mutex, then journals the outcome.
  /// \param intent Bounded payload-free intent. Its `request_id` is the durable linking key and
  ///               must be unique across the retained intents.
  /// \param emit Host emission callback invoked exactly once after the durable intent and with
  ///             the mutex released. It MUST return an outcome whose `kind` is one of the closed
  ///             `OutcomeKind` enumerators.
  /// \param out Receives the emitted outcome when the callback ran and returned an
  ///            in-vocabulary kind.
  /// \return `JournalStatus::RejectedConfiguration` for an invalid tag, a null callback, a
  ///         `request_id` already carried by a retained intent (no append, no emission), or a
  ///         callback-returned `OutcomeKind` outside the closed vocabulary (the invalid outcome
  ///         is not appended and the durable intent remains an orphan); `JournalStatus::RecordTooLarge`
  ///         for an over-size frame (no append, no emission); `JournalStatus::CapacityExhausted`
  ///         when a bound would be exceeded or the durable journal already exceeds a declared
  ///         bound (no append, no emission); `JournalStatus::WriteFailed` or
  ///         `JournalStatus::PartialWrite` when the intent append or sync fails (no emission);
  ///         `JournalStatus::EvidenceIncomplete` when the intent is durable but the outcome
  ///         could not be recorded; `JournalStatus::Ok` only when both frames are durable.
  /// \pre the journal is open and `emit` is non-null for a successful call; the retained intent
  ///      identities do not already contain `intent.request_id`.
  /// \post on `Ok` the intent and its outcome are durable; on a failure no complete retained
  ///       record is mutated.
  /// \note A callback that throws a host exception is not caught: the exception propagates
  ///       unmodified after the durable intent. The intent then has no outcome, is surfaced by
  ///       recovery as an explicit `EvidenceIncomplete` orphan, and the call never reports `Ok`.
  /// \unitspec{T026-U-JOURNAL}
  JournalStatus journal_then_emit(const StimulationIntent &intent,
                                  const EmissionCallback &emit, StimulationOutcome &out);

  /// \brief Appends exactly one explicit resolution outcome for an orphan intent.
  /// \param request_id Request identity of the intent to resolve.
  /// \param outcome Explicit bounded outcome; its `request_id` is bound to `request_id` and its
  ///                `kind` MUST be one of the closed `OutcomeKind` enumerators.
  /// \return `JournalStatus::RejectedConfiguration` when `outcome.kind` is outside the closed
  ///         `OutcomeKind` vocabulary (no append); `JournalStatus::NotFound` when no intent
  ///         matches; `JournalStatus::AlreadyResolved` when every retained intent carrying the
  ///         identity already has a distinct outcome; `JournalStatus::CapacityExhausted` or a
  ///         write status on failure; `JournalStatus::Ok` when the outcome is durable and
  ///         resolves exactly one still-unresolved intent. An explicit `Unknown` resolution
  ///         stays `Unknown`.
  /// \unitspec{T026-U-JOURNAL}
  JournalStatus resolve(std::uint64_t request_id, const StimulationOutcome &outcome);

private:
  /// \brief One bounded index entry describing a complete retained frame.
  /// \unitspec{T026-U-JOURNAL}
  struct IndexEntry {
    /// \brief Whether the frame is an outcome frame.
    /// \unitspec{T026-U-JOURNAL}
    bool is_outcome{false};
    /// \brief True only while the owning callback is running; never persisted.
    bool in_flight{false};
    /// \brief Identity carried by the frame (intent request id or outcome request id).
    /// \unitspec{T026-U-JOURNAL}
    std::uint64_t request_id{0U};
    /// \brief Recovered intent value; valid only when `is_outcome` is false.
    /// \unitspec{T026-U-JOURNAL}
    StimulationIntent intent{};
    /// \brief Recovered outcome value; valid only when `is_outcome` is true.
    /// \unitspec{T026-U-JOURNAL}
    StimulationOutcome outcome{};
  };

  /// \brief Reports whether a configuration is legal.
  /// \param config Candidate configuration.
  /// \return `true` when every declared bound is non-zero and consistent.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] static bool config_is_legal(const JournalConfig &config) noexcept;

  /// \brief Reports whether an intent's bounded tags are valid.
  /// \param intent Candidate intent.
  /// \return `true` when both tags are non-empty, at most 63 printable ASCII bytes, and NUL-free.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] static bool intent_tags_valid(const StimulationIntent &intent) noexcept;

  /// \brief Appends one complete frame and commits it only when durable.
  /// \param frame Complete encoded frame.
  /// \param entry Index entry to commit when the frame becomes durable.
  /// \return `JournalStatus::Ok` when the frame is durable; otherwise the failure status.
  /// \pre the caller holds `mutex_` and has already checked the declared bounds.
  /// \unitspec{T026-U-JOURNAL}
  JournalStatus append_frame_locked(std::span<const std::uint8_t> frame,
                                    const IndexEntry &entry);

  /// \brief Rebuilds the bounded index and counters from the durable bytes.
  /// \return The deterministic recovery summary.
  /// \pre the caller holds `mutex_` and `opened_` is true.
  /// \unitspec{T026-U-JOURNAL}
  RecoveryReport scan_locked();

  /// \brief Binds a storage seam, resets the counters, and performs one recovery scan.
  /// \param storage Host storage that will outlive the journal.
  /// \param config Already-legal bounded configuration.
  /// \return The recovery scan status.
  /// \pre the caller holds `mutex_` and `config` is legal.
  /// \unitspec{T026-U-JOURNAL}
  JournalStatus bind_and_scan_locked(Storage &storage, const JournalConfig &config);

  /// \brief Counts intents with no matching outcome in the current index.
  /// \return The number of orphan intents.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] std::size_t orphan_count_locked() const noexcept;

  /// \brief Builds the request identities of the orphan intents in durable order.
  /// \return The orphan request identities.
  /// \unitspec{T026-U-JOURNAL}
  [[nodiscard]] std::vector<std::uint64_t> orphan_ids_locked() const;

  /// \brief Serializes appends, accounting, boundary restoration, and the index.
  /// \unitspec{T026-U-JOURNAL}
  mutable std::mutex mutex_;
  /// \brief Bound configuration.
  /// \unitspec{T026-U-JOURNAL}
  JournalConfig config_{};
  /// \brief Bound storage seam, when open.
  /// \unitspec{T026-U-JOURNAL}
  Storage *storage_{nullptr};
  /// \brief Owned local-file storage for `open_local_file`.
  /// \unitspec{T026-U-JOURNAL}
  std::unique_ptr<LocalFileStorage> owned_storage_;
  /// \brief Whether the journal is open.
  /// \unitspec{T026-U-JOURNAL}
  bool opened_{false};
  /// \brief Whether a corrupt scan made the journal unusable for further appends.
  /// \unitspec{T026-U-JOURNAL}
  bool corrupt_{false};
  /// \brief Whether a boundary-restoration failure made the journal unusable.
  /// \unitspec{T026-U-JOURNAL}
  bool unusable_{false};
  /// \brief Whether recovery refused an over-bound durable journal.
  ///
  /// Set when the durable bytes exceed `max_journal_bytes` or the complete retained frames
  /// exceed `max_retained_records`; every subsequent append and resolution fails closed with
  /// `CapacityExhausted` and no over-bound index is presented.
  /// \unitspec{T026-U-JOURNAL}
  bool over_bound_{false};
  /// \brief Bounded index of complete retained frames, in durable order.
  /// \unitspec{T026-U-JOURNAL}
  std::vector<IndexEntry> index_{};
  /// \brief Durable byte count of the complete retained records.
  /// \unitspec{T026-U-JOURNAL}
  std::size_t retained_bytes_{0U};
  /// \brief Summary of the most recent recovery scan.
  /// \unitspec{T026-U-JOURNAL}
  RecoveryReport last_report_{};
};

static_assert(!std::is_copy_constructible_v<StimulationJournal>,
              "StimulationJournal must not be copyable");
static_assert(!std::is_move_constructible_v<StimulationJournal>,
              "StimulationJournal must not be movable");

} // namespace validation
} // namespace xcom
} // namespace xverse

#endif // XVERSE_XCOM_STIMULATION_JOURNAL_HPP_
