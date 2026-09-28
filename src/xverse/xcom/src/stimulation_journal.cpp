/**
 * \file stimulation_journal.cpp
 * \brief T026 bounded durable stimulation intent/outcome journal implementation: canonical
 *        frame codec, capacity accounting, fail-closed partial-write handling, restart
 *        recovery, and the production local-file storage seam.
 *
 * \details
 * All integers are little-endian. One frame is written per record. The unit provides no
 * network, ambient-configuration, secret, dynamic-load, subprocess, or legacy access and
 * performs no payload decoding or unrestricted logging.
 *
 * \ingroup xcom_stim
 */

#include "xverse/xcom/stimulation_journal.hpp"

#include <array>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <fcntl.h>
#include <span>
#include <string>
#include <string_view>
#include <sys/stat.h>
#include <unistd.h>
#include <utility>
#include <vector>

namespace xverse {
namespace xcom {
namespace validation {
namespace {

/// \brief Appends a 16-bit little-endian value.
/// \param out Destination byte buffer.
/// \param value Value to append.
void put_u16(std::vector<std::uint8_t> &out, std::uint16_t value) {
  out.push_back(static_cast<std::uint8_t>(value & 0xFFU));
  out.push_back(static_cast<std::uint8_t>((value >> 8U) & 0xFFU));
}

/// \brief Appends a 32-bit little-endian value.
/// \param out Destination byte buffer.
/// \param value Value to append.
void put_u32(std::vector<std::uint8_t> &out, std::uint32_t value) {
  out.push_back(static_cast<std::uint8_t>(value & 0xFFU));
  out.push_back(static_cast<std::uint8_t>((value >> 8U) & 0xFFU));
  out.push_back(static_cast<std::uint8_t>((value >> 16U) & 0xFFU));
  out.push_back(static_cast<std::uint8_t>((value >> 24U) & 0xFFU));
}

/// \brief Appends a 64-bit little-endian value.
/// \param out Destination byte buffer.
/// \param value Value to append.
void put_u64(std::vector<std::uint8_t> &out, std::uint64_t value) {
  for (std::size_t index = 0; index < 8U; ++index) {
    out.push_back(static_cast<std::uint8_t>((value >> (index * 8U)) & 0xFFU));
  }
}

/// \brief Appends a byte span.
/// \param out Destination byte buffer.
/// \param bytes Bytes to append.
void put_bytes(std::vector<std::uint8_t> &out, std::span<const std::uint8_t> bytes) {
  out.insert(out.end(), bytes.begin(), bytes.end());
}

/// \brief Appends a fixed 16-byte digest array.
/// \param out Destination byte buffer.
/// \param digest Digest to append.
void put_digest(std::vector<std::uint8_t> &out, const PermitId &digest) {
  out.insert(out.end(), digest.begin(), digest.end());
}

/// \brief Reads a 16-bit little-endian value from a buffer.
/// \param bytes Source buffer.
/// \param offset Byte offset.
/// \return The decoded value.
[[nodiscard]] std::uint16_t read_u16(const std::vector<std::uint8_t> &bytes,
                                     std::size_t offset) noexcept {
  return static_cast<std::uint16_t>(
      static_cast<std::uint16_t>(bytes[offset]) |
      static_cast<std::uint16_t>(static_cast<std::uint16_t>(bytes[offset + 1U]) << 8U));
}

/// \brief Reads a 32-bit little-endian value from a buffer.
/// \param bytes Source buffer.
/// \param offset Byte offset.
/// \return The decoded value.
[[nodiscard]] std::uint32_t read_u32(const std::vector<std::uint8_t> &bytes,
                                     std::size_t offset) noexcept {
  return static_cast<std::uint32_t>(bytes[offset]) |
         (static_cast<std::uint32_t>(bytes[offset + 1U]) << 8U) |
         (static_cast<std::uint32_t>(bytes[offset + 2U]) << 16U) |
         (static_cast<std::uint32_t>(bytes[offset + 3U]) << 24U);
}

/// \brief Reads a 64-bit little-endian value from a buffer.
/// \param bytes Source buffer.
/// \param offset Byte offset.
/// \return The decoded value.
[[nodiscard]] std::uint64_t read_u64(const std::vector<std::uint8_t> &bytes,
                                     std::size_t offset) noexcept {
  std::uint64_t value = 0U;
  for (std::size_t index = 0; index < 8U; ++index) {
    value |= static_cast<std::uint64_t>(bytes[offset + index]) << (index * 8U);
  }
  return value;
}

/// \brief Copies a fixed 16-byte digest out of a buffer.
/// \param bytes Source buffer.
/// \param offset Byte offset.
/// \return The copied digest.
[[nodiscard]] PermitId digest_at(const std::vector<std::uint8_t> &bytes,
                                 std::size_t offset) noexcept {
  PermitId digest{};
  for (std::size_t index = 0; index < digest.size(); ++index) {
    digest[index] = bytes[offset + index];
  }
  return digest;
}

/// \brief Encodes the canonical intent payload.
/// \param intent Bounded intent.
/// \return The canonical intent payload bytes.
[[nodiscard]] std::vector<std::uint8_t>
encode_intent_payload(const StimulationIntent &intent) {
  std::vector<std::uint8_t> payload;
  payload.reserve(kJournalMinIntentPayload);
  put_digest(payload, intent.permit_id);
  put_digest(payload, intent.session_id);
  put_bytes(payload, intent.plan_digest);
  put_u64(payload, intent.request_id);
  put_u64(payload, intent.correlation_id);
  put_u64(payload, intent.causation_id);
  put_u32(payload, intent.action_mask);
  put_u32(payload, intent.quota_cost);
  put_u32(payload, intent.clock_domain);
  put_u64(payload, static_cast<std::uint64_t>(intent.scheduled_at));
  payload.push_back(intent.immediate ? std::uint8_t{1U} : std::uint8_t{0U});
  const std::string &target = intent.target.value();
  payload.push_back(static_cast<std::uint8_t>(target.size()));
  put_bytes(payload,
            std::span<const std::uint8_t>(
                reinterpret_cast<const std::uint8_t *>(target.data()), target.size()));
  const std::string &tool = intent.tool.value();
  payload.push_back(static_cast<std::uint8_t>(tool.size()));
  put_bytes(payload, std::span<const std::uint8_t>(
                         reinterpret_cast<const std::uint8_t *>(tool.data()), tool.size()));
  return payload;
}

/// \brief Encodes the canonical outcome payload.
/// \param outcome Bounded outcome.
/// \return The canonical outcome payload bytes.
[[nodiscard]] std::vector<std::uint8_t>
encode_outcome_payload(const StimulationOutcome &outcome) {
  std::vector<std::uint8_t> payload;
  payload.reserve(kJournalOutcomePayload);
  put_u64(payload, outcome.request_id);
  payload.push_back(static_cast<std::uint8_t>(outcome.kind));
  payload.push_back(static_cast<std::uint8_t>(outcome.reason));
  put_u32(payload, outcome.clock_domain);
  put_u64(payload, static_cast<std::uint64_t>(outcome.observed_at));
  return payload;
}

/// \brief Wraps one payload in a self-checking frame.
/// \param kind Frame kind byte.
/// \param flags Frame flags byte.
/// \param payload Canonical payload.
/// \return The complete frame bytes.
[[nodiscard]] std::vector<std::uint8_t> encode_frame(std::uint8_t kind, std::uint8_t flags,
                                                     const std::vector<std::uint8_t> &payload) {
  std::vector<std::uint8_t> frame;
  frame.reserve(kJournalFrameOverhead + payload.size());
  put_u32(frame, kJournalFrameMagic);
  put_u16(frame, kJournalFormatVersion);
  frame.push_back(kind);
  frame.push_back(flags);
  put_u32(frame, static_cast<std::uint32_t>(payload.size()));
  put_digest(frame, canonical_digest(payload));
  put_bytes(frame, payload);
  put_digest(frame, canonical_digest(frame));
  return frame;
}

/// \brief Encodes a complete intent frame.
/// \param intent Bounded intent.
/// \return The complete intent frame bytes.
[[nodiscard]] std::vector<std::uint8_t>
encode_intent_frame(const StimulationIntent &intent) {
  return encode_frame(kJournalKindIntent, intent.immediate ? std::uint8_t{1U} : std::uint8_t{0U},
                      encode_intent_payload(intent));
}

/// \brief Encodes a complete outcome frame.
/// \param outcome Bounded outcome.
/// \return The complete outcome frame bytes.
[[nodiscard]] std::vector<std::uint8_t>
encode_outcome_frame(const StimulationOutcome &outcome) {
  return encode_frame(kJournalKindOutcome, 0U, encode_outcome_payload(outcome));
}

/// \brief Reports whether a candidate payload length can form a legal frame.
/// \param declared Declared payload length.
/// \return `true` when the payload length is within the accepted record bound.
[[nodiscard]] bool declared_length_legal(std::uint32_t declared) noexcept {
  return declared <= kJournalMaxRecordBytes;
}

/// \brief Reports whether an integrity-checked byte range is a bounded, printable tag.
/// \param bytes Source buffer.
/// \param offset First byte of the tag text.
/// \param length Tag text length.
/// \return `true` when the range is a non-empty, at most `Tag::max_length`-byte, NUL-free
///         printable-ASCII tag. A recovered tag can therefore never exceed the accepted
///         `Tag` bound, even for a digest-valid frame that declares an over-long length.
[[nodiscard]] bool tag_bytes_valid(const std::vector<std::uint8_t> &bytes, std::size_t offset,
                                   std::size_t length) noexcept {
  if (length == 0U || length > Tag::max_length) {
    return false;
  }
  return Tag::is_valid(
      std::string_view(reinterpret_cast<const char *>(bytes.data() + offset), length));
}

/// \brief Copies a byte range into a bounded tag value.
/// \param bytes Source buffer.
/// \param offset First byte of the tag text.
/// \param length Tag text length.
/// \return The tag value; the range was validated by `tag_bytes_valid` before decoding.
[[nodiscard]] Tag tag_at(const std::vector<std::uint8_t> &bytes, std::size_t offset,
                         std::size_t length) {
  return Tag(std::string(reinterpret_cast<const char *>(bytes.data() + offset), length));
}

/// \brief Decodes a canonical intent payload.
/// \param payload Integrity-checked payload bytes.
/// \param out Receives the decoded intent only on success.
/// \return `true` when the payload has the exact canonical intent shape.
[[nodiscard]] bool decode_intent_payload(const std::vector<std::uint8_t> &payload,
                                         StimulationIntent &out) {
  if (payload.size() < kJournalMinIntentPayload) {
    return false;
  }
  const std::size_t target_length = payload[109U];
  if (target_length > Tag::max_length || 110U + target_length + 1U > payload.size()) {
    return false;
  }
  const std::size_t tool_length = payload[110U + target_length];
  if (tool_length > Tag::max_length ||
      110U + target_length + 1U + tool_length != payload.size()) {
    return false;
  }
  if (!tag_bytes_valid(payload, 110U, target_length) ||
      !tag_bytes_valid(payload, 110U + target_length + 1U, tool_length)) {
    return false;
  }
  StimulationIntent intent;
  for (std::size_t index = 0; index < intent.permit_id.size(); ++index) {
    intent.permit_id[index] = payload[index];
    intent.session_id[index] = payload[16U + index];
  }
  for (std::size_t index = 0; index < intent.plan_digest.size(); ++index) {
    intent.plan_digest[index] = payload[32U + index];
  }
  intent.request_id = read_u64(payload, 64U);
  intent.correlation_id = read_u64(payload, 72U);
  intent.causation_id = read_u64(payload, 80U);
  intent.action_mask = read_u32(payload, 88U);
  intent.quota_cost = read_u32(payload, 92U);
  intent.clock_domain = read_u32(payload, 96U);
  intent.scheduled_at = static_cast<Timestamp>(read_u64(payload, 100U));
  intent.immediate = payload[108U] != 0U;
  intent.target = tag_at(payload, 110U, target_length);
  intent.tool = tag_at(payload, 110U + target_length + 1U, tool_length);
  out = intent;
  return true;
}

/// \brief Reports whether an outcome kind is one of the closed `OutcomeKind` enumerators.
/// \param kind Candidate kind.
/// \return `true` when `kind` is `Delivered`, `Rejected`, `Expired`, `Cancelled`, or `Unknown`;
///         `false` for any underlying byte outside the closed vocabulary.
[[nodiscard]] bool outcome_kind_in_vocabulary(OutcomeKind kind) noexcept {
  switch (kind) {
  case OutcomeKind::Delivered:
  case OutcomeKind::Rejected:
  case OutcomeKind::Expired:
  case OutcomeKind::Cancelled:
  case OutcomeKind::Unknown:
    return true;
  }
  return false;
}

/// \brief Decodes a canonical outcome payload.
/// \param payload Integrity-checked payload bytes.
/// \param out Receives the decoded outcome only on success.
/// \return `true` when the payload has the exact canonical outcome shape.
[[nodiscard]] bool decode_outcome_payload(const std::vector<std::uint8_t> &payload,
                                          StimulationOutcome &out) {
  if (payload.size() != kJournalOutcomePayload) {
    return false;
  }
  const std::uint8_t kind = payload[8U];
  if (!outcome_kind_in_vocabulary(static_cast<OutcomeKind>(kind))) {
    return false;
  }
  StimulationOutcome outcome;
  outcome.request_id = read_u64(payload, 0U);
  outcome.kind = static_cast<OutcomeKind>(kind);
  outcome.reason = static_cast<Result>(payload[9U]);
  outcome.clock_domain = read_u32(payload, 10U);
  outcome.observed_at = static_cast<Timestamp>(read_u64(payload, 14U));
  out = outcome;
  return true;
}

} // namespace

std::string_view status_name(JournalStatus status) noexcept {
  switch (status) {
  case JournalStatus::RejectedConfiguration:
    return "RejectedConfiguration";
  case JournalStatus::RecordTooLarge:
    return "RecordTooLarge";
  case JournalStatus::CorruptRecord:
    return "CorruptRecord";
  case JournalStatus::PartialWrite:
    return "PartialWrite";
  case JournalStatus::WriteFailed:
    return "WriteFailed";
  case JournalStatus::CapacityExhausted:
    return "CapacityExhausted";
  case JournalStatus::AlreadyResolved:
    return "AlreadyResolved";
  case JournalStatus::NotFound:
    return "NotFound";
  case JournalStatus::EvidenceIncomplete:
    return "EvidenceIncomplete";
  case JournalStatus::Ok:
    return "Ok";
  }
  return "Unknown";
}

std::uint8_t precedence_rank(JournalStatus status) noexcept {
  return static_cast<std::uint8_t>(status);
}

JournalStatus from_first(std::initializer_list<JournalStatus> applicable) noexcept {
  JournalStatus selected = JournalStatus::Ok;
  bool first = true;
  for (const JournalStatus candidate : applicable) {
    if (first || precedence_rank(candidate) < precedence_rank(selected)) {
      selected = candidate;
      first = false;
    }
  }
  return selected;
}

std::string_view outcome_kind_name(OutcomeKind kind) noexcept {
  switch (kind) {
  case OutcomeKind::Delivered:
    return "Delivered";
  case OutcomeKind::Rejected:
    return "Rejected";
  case OutcomeKind::Expired:
    return "Expired";
  case OutcomeKind::Cancelled:
    return "Cancelled";
  case OutcomeKind::Unknown:
    return "Unknown";
  }
  return "Unknown";
}

/**
 * \brief Production local-file storage over a host-supplied local path.
 *
 * The implementation opens only the host-supplied path with `O_RDWR|O_CREAT`, appends with
 * `pwrite` at the durable end, syncs with `fsync`, restores with `ftruncate`, and reads with
 * `pread`. It creates no directory, reads no environment variable, resolves no network path,
 * and never logs payload.
 */
struct LocalFileStorage final : public StimulationJournal::Storage {
  /// \brief Opens the host-supplied local path.
  /// \param path Local file path.
  explicit LocalFileStorage(const std::string &path) noexcept
      : fd_(::open(path.c_str(), O_RDWR | O_CREAT, 0600)) {}

  /// \brief Destructor; closes the file descriptor.
  ~LocalFileStorage() override {
    if (fd_ >= 0) {
      ::close(fd_);
    }
  }

  /// \brief Reports whether the file opened successfully.
  /// \return `true` when the descriptor is valid.
  [[nodiscard]] bool is_open() const noexcept { return fd_ >= 0; }

  JournalStatus append(std::span<const std::uint8_t> bytes) override {
    if (fd_ < 0) {
      return JournalStatus::WriteFailed;
    }
    const off_t end = ::lseek(fd_, 0, SEEK_END);
    if (end < 0) {
      return JournalStatus::WriteFailed;
    }
    std::size_t written = 0U;
    while (written < bytes.size()) {
      const ssize_t result =
          ::pwrite(fd_, bytes.data() + written, bytes.size() - written,
                   end + static_cast<off_t>(written));
      if (result < 0) {
        if (errno == EINTR) {
          continue;
        }
        return JournalStatus::WriteFailed;
      }
      if (result == 0) {
        break;
      }
      written += static_cast<std::size_t>(result);
    }
    if (written < bytes.size()) {
      return JournalStatus::PartialWrite;
    }
    return JournalStatus::Ok;
  }

  JournalStatus sync() override {
    if (fd_ < 0) {
      return JournalStatus::WriteFailed;
    }
    return ::fsync(fd_) == 0 ? JournalStatus::Ok : JournalStatus::WriteFailed;
  }

  JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    out.clear();
    if (fd_ < 0) {
      return JournalStatus::WriteFailed;
    }
    struct stat status {};
    if (::fstat(fd_, &status) != 0) {
      return JournalStatus::WriteFailed;
    }
    const std::size_t total = static_cast<std::size_t>(status.st_size);
    out.resize(total);
    std::size_t read_bytes = 0U;
    while (read_bytes < total) {
      const ssize_t result =
          ::pread(fd_, out.data() + read_bytes, total - read_bytes,
                  static_cast<off_t>(read_bytes));
      if (result < 0) {
        if (errno == EINTR) {
          continue;
        }
        out.resize(read_bytes);
        return JournalStatus::WriteFailed;
      }
      if (result == 0) {
        break;
      }
      read_bytes += static_cast<std::size_t>(result);
    }
    if (read_bytes < total) {
      out.resize(read_bytes);
      return JournalStatus::WriteFailed;
    }
    return JournalStatus::Ok;
  }

  std::size_t size() override {
    if (fd_ < 0) {
      return 0U;
    }
    const off_t end = ::lseek(fd_, 0, SEEK_END);
    if (end < 0) {
      return 0U;
    }
    return static_cast<std::size_t>(end);
  }

  JournalStatus truncate(std::size_t size) override {
    if (fd_ < 0) {
      return JournalStatus::WriteFailed;
    }
    return ::ftruncate(fd_, static_cast<off_t>(size)) == 0 ? JournalStatus::Ok
                                                          : JournalStatus::WriteFailed;
  }

private:
  /// \brief Open file descriptor, or `-1` when unavailable.
  int fd_{-1};
};

StimulationJournal::StimulationJournal() noexcept = default;

StimulationJournal::~StimulationJournal() = default;

bool StimulationJournal::config_is_legal(const JournalConfig &config) noexcept {
  if (config.max_record_bytes < kJournalMinRecordBytes) {
    return false;
  }
  if (config.max_retained_records == 0U) {
    return false;
  }
  if (config.max_journal_bytes == 0U) {
    return false;
  }
  return config.max_journal_bytes >= config.max_record_bytes;
}

bool StimulationJournal::intent_tags_valid(const StimulationIntent &intent) noexcept {
  return Tag::is_valid(intent.target.value()) && Tag::is_valid(intent.tool.value());
}

// Orphan accounting is one-to-one: each durable outcome resolves at most one intent sharing its
// request identity, and an intent is resolved only when a distinct outcome can be assigned to it.
// The k-th retained intent carrying identity `X` (in durable order) is therefore resolved exactly
// when at least `k + 1` retained outcomes carry `X`; any intent without an outcome of its own is
// reported as an orphan. This is allocation-free and bounded by the retained index size, so it is
// safe on the `noexcept` counter path.

std::size_t StimulationJournal::orphan_count_locked() const noexcept {
  std::size_t orphans = 0U;
  for (std::size_t index = 0U; index < index_.size(); ++index) {
    const IndexEntry &intent = index_[index];
    if (intent.is_outcome) {
      continue;
    }
    std::size_t rank = 0U;
    for (std::size_t earlier = 0U; earlier < index; ++earlier) {
      if (!index_[earlier].is_outcome && index_[earlier].request_id == intent.request_id) {
        ++rank;
      }
    }
    std::size_t outcomes = 0U;
    for (const IndexEntry &entry : index_) {
      if (entry.is_outcome && entry.request_id == intent.request_id) {
        ++outcomes;
      }
    }
    if (outcomes <= rank) {
      ++orphans;
    }
  }
  return orphans;
}

std::vector<std::uint64_t> StimulationJournal::orphan_ids_locked() const {
  std::vector<std::uint64_t> identifiers;
  for (std::size_t index = 0U; index < index_.size(); ++index) {
    const IndexEntry &intent = index_[index];
    if (intent.is_outcome) {
      continue;
    }
    std::size_t rank = 0U;
    for (std::size_t earlier = 0U; earlier < index; ++earlier) {
      if (!index_[earlier].is_outcome && index_[earlier].request_id == intent.request_id) {
        ++rank;
      }
    }
    std::size_t outcomes = 0U;
    for (const IndexEntry &entry : index_) {
      if (entry.is_outcome && entry.request_id == intent.request_id) {
        ++outcomes;
      }
    }
    if (outcomes <= rank) {
      identifiers.push_back(intent.request_id);
    }
  }
  return identifiers;
}

RecoveryReport StimulationJournal::scan_locked() {
  index_.clear();
  retained_bytes_ = 0U;
  corrupt_ = false;
  unusable_ = false;
  over_bound_ = false;

  RecoveryReport report;
  if (storage_ == nullptr) {
    report.status = JournalStatus::RejectedConfiguration;
    last_report_ = report;
    return report;
  }

  // Fail closed before reading when the durable journal already exceeds the declared byte
  // bound. This refuses an over-bound state and keeps the read bounded by the configuration
  // rather than by the physical file length, so no over-bound allocation occurs.
  if (storage_->size() > config_.max_journal_bytes) {
    over_bound_ = true;
    report.status = JournalStatus::CapacityExhausted;
    last_report_ = report;
    return report;
  }

  std::vector<std::uint8_t> bytes;
  const JournalStatus read_status = storage_->read_all(bytes);
  if (read_status != JournalStatus::Ok) {
    report.status = read_status;
    unusable_ = true;
    last_report_ = report;
    return report;
  }
  if (bytes.size() > config_.max_journal_bytes) {
    over_bound_ = true;
    report.status = JournalStatus::CapacityExhausted;
    last_report_ = report;
    return report;
  }

  const std::size_t total = bytes.size();
  std::size_t offset = 0U;
  std::size_t last_good = 0U;
  std::size_t torn = 0U;
  bool stopped_corrupt = false;
  bool stopped_over_bound = false;

  while (offset < total) {
    const std::size_t remaining = total - offset;
    if (remaining < 28U) {
      torn = remaining;
      break;
    }
    const std::uint32_t magic = read_u32(bytes, offset);
    const std::uint16_t version = read_u16(bytes, offset + 4U);
    const std::uint8_t kind = bytes[offset + 6U];
    const std::uint32_t declared = read_u32(bytes, offset + 8U);
    if (magic != kJournalFrameMagic || version != kJournalFormatVersion ||
        (kind != kJournalKindIntent && kind != kJournalKindOutcome) ||
        !declared_length_legal(declared)) {
      stopped_corrupt = true;
      break;
    }
    const std::size_t frame_size = 28U + static_cast<std::size_t>(declared) + 16U;
    if (remaining < frame_size) {
      torn = remaining;
      break;
    }
    // Fail closed as soon as one more complete frame would exceed either declared bound; the
    // over-bound frame is not retained and no over-bound index is presented.
    if (index_.size() + 1U > config_.max_retained_records ||
        last_good + frame_size > config_.max_journal_bytes) {
      stopped_over_bound = true;
      break;
    }
    const std::vector<std::uint8_t> payload(bytes.begin() + static_cast<std::ptrdiff_t>(offset) +
                                                28,
                                            bytes.begin() + static_cast<std::ptrdiff_t>(offset) +
                                                28 + static_cast<std::ptrdiff_t>(declared));
    const PermitId payload_digest = digest_at(bytes, offset + 12U);
    const PermitId frame_digest = digest_at(bytes, offset + 28U + declared);
    bool complete = payload_digest == canonical_digest(payload);
    if (complete) {
      const std::vector<std::uint8_t> framed(
          bytes.begin() + static_cast<std::ptrdiff_t>(offset),
          bytes.begin() + static_cast<std::ptrdiff_t>(offset + 28U + declared));
      complete = frame_digest == canonical_digest(framed);
    }
    if (!complete) {
      stopped_corrupt = true;
      break;
    }
    const bool is_outcome = kind == kJournalKindOutcome;
    IndexEntry entry;
    entry.is_outcome = is_outcome;
    if (is_outcome) {
      if (!decode_outcome_payload(payload, entry.outcome)) {
        stopped_corrupt = true;
        break;
      }
      entry.request_id = entry.outcome.request_id;
    } else {
      if (!decode_intent_payload(payload, entry.intent)) {
        stopped_corrupt = true;
        break;
      }
      entry.request_id = entry.intent.request_id;
    }
    index_.push_back(entry);
    offset += frame_size;
    last_good = offset;
  }

  if (stopped_corrupt) {
    corrupt_ = true;
    report.status = JournalStatus::CorruptRecord;
    report.discarded_trailing_bytes = 0U;
  } else if (stopped_over_bound) {
    over_bound_ = true;
    report.status = JournalStatus::CapacityExhausted;
    report.discarded_trailing_bytes = 0U;
  } else if (torn > 0U) {
    if (storage_->truncate(last_good) == JournalStatus::Ok) {
      report.status = JournalStatus::Ok;
      report.discarded_trailing_bytes = torn;
    } else {
      unusable_ = true;
      report.status = JournalStatus::PartialWrite;
    }
  } else {
    report.status = JournalStatus::Ok;
  }

  retained_bytes_ = last_good;
  report.complete_intents = 0U;
  report.outcomes = 0U;
  for (const IndexEntry &entry : index_) {
    if (entry.is_outcome) {
      ++report.outcomes;
    } else {
      ++report.complete_intents;
    }
  }
  report.orphan_intents = orphan_count_locked();
  report.orphan_request_ids = orphan_ids_locked();
  report.retained_records = index_.size();
  report.retained_bytes = last_good;
  last_report_ = report;
  return report;
}

JournalStatus StimulationJournal::append_frame_locked(std::span<const std::uint8_t> frame,
                                                      const IndexEntry &entry) {
  if (storage_ == nullptr) {
    return JournalStatus::RejectedConfiguration;
  }
  if (corrupt_) {
    return JournalStatus::CorruptRecord;
  }
  if (unusable_) {
    return JournalStatus::WriteFailed;
  }
  if (over_bound_) {
    return JournalStatus::CapacityExhausted;
  }

  const std::size_t before = retained_bytes_;
  JournalStatus status = storage_->append(frame);
  if (status == JournalStatus::Ok && storage_->size() != before + frame.size()) {
    status = JournalStatus::PartialWrite;
  }
  if (status != JournalStatus::Ok) {
    if (storage_->truncate(before) != JournalStatus::Ok) {
      unusable_ = true;
    }
    return status;
  }
  if (storage_->sync() != JournalStatus::Ok) {
    if (storage_->truncate(before) != JournalStatus::Ok) {
      unusable_ = true;
    }
    return JournalStatus::WriteFailed;
  }

  retained_bytes_ = before + frame.size();
  index_.push_back(entry);
  return JournalStatus::Ok;
}

JournalStatus StimulationJournal::bind_and_scan_locked(Storage &storage,
                                                      const JournalConfig &config) {
  storage_ = &storage;
  config_ = config;
  opened_ = true;
  corrupt_ = false;
  unusable_ = false;
  over_bound_ = false;
  index_.clear();
  retained_bytes_ = 0U;
  const RecoveryReport report = scan_locked();
  return report.status;
}

JournalStatus StimulationJournal::open(Storage &storage, const JournalConfig &config) {
  if (!config_is_legal(config)) {
    return JournalStatus::RejectedConfiguration;
  }
  std::lock_guard<std::mutex> lock(mutex_);
  owned_storage_.reset();
  return bind_and_scan_locked(storage, config);
}

JournalStatus StimulationJournal::open_local_file(const std::string &path,
                                                  const JournalConfig &config) {
  if (path.empty() || !config_is_legal(config)) {
    return JournalStatus::RejectedConfiguration;
  }
  auto storage = std::make_unique<LocalFileStorage>(path);
  if (!storage->is_open()) {
    return JournalStatus::WriteFailed;
  }
  std::lock_guard<std::mutex> lock(mutex_);
  owned_storage_ = std::move(storage);
  return bind_and_scan_locked(*owned_storage_, config);
}

RecoveryReport StimulationJournal::recover() {
  std::lock_guard<std::mutex> lock(mutex_);
  if (!opened_ || storage_ == nullptr) {
    RecoveryReport report;
    report.status = JournalStatus::RejectedConfiguration;
    last_report_ = report;
    return report;
  }
  return scan_locked();
}

RecoveryReport StimulationJournal::last_recovery() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return last_report_;
}

JournalSnapshot StimulationJournal::snapshot() const {
  JournalSnapshot snapshot_value;
  std::lock_guard<std::mutex> lock(mutex_);
  snapshot_value.retained_records = index_.size();
  snapshot_value.retained_bytes = retained_bytes_;
  for (const IndexEntry &entry : index_) {
    if (entry.is_outcome) {
      ++snapshot_value.outcomes;
    } else {
      ++snapshot_value.complete_intents;
    }
  }
  snapshot_value.orphan_intents = orphan_count_locked();
  return snapshot_value;
}

std::vector<StimulationIntent> StimulationJournal::recovered_intents() const {
  std::lock_guard<std::mutex> lock(mutex_);
  std::vector<StimulationIntent> intents;
  for (const IndexEntry &entry : index_) {
    if (!entry.is_outcome) {
      intents.push_back(entry.intent);
    }
  }
  return intents;
}

std::vector<StimulationOutcome> StimulationJournal::recovered_outcomes() const {
  std::lock_guard<std::mutex> lock(mutex_);
  std::vector<StimulationOutcome> outcomes;
  for (const IndexEntry &entry : index_) {
    if (entry.is_outcome) {
      outcomes.push_back(entry.outcome);
    }
  }
  return outcomes;
}

JournalStatus StimulationJournal::journal_then_emit(const StimulationIntent &intent,
                                                    const EmissionCallback &emit,
                                                    StimulationOutcome &out) {
  if (!emit) {
    return JournalStatus::RejectedConfiguration;
  }
  if (!intent_tags_valid(intent)) {
    return JournalStatus::RejectedConfiguration;
  }

  const std::vector<std::uint8_t> intent_frame = encode_intent_frame(intent);
  {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!opened_ || storage_ == nullptr) {
      return JournalStatus::RejectedConfiguration;
    }
    // The request identity is the durable key linking an intent to its outcome, so a retained
    // intent's `request_id` is unique. A second intent carrying a retained identity is refused
    // before any append and before any emission, so no ambiguous or unaccounted intent exists.
    for (const IndexEntry &entry : index_) {
      if (!entry.is_outcome && entry.request_id == intent.request_id) {
        return JournalStatus::RejectedConfiguration;
      }
    }
    if (intent_frame.size() > config_.max_record_bytes) {
      return JournalStatus::RecordTooLarge;
    }
    if (corrupt_) {
      return JournalStatus::CorruptRecord;
    }
    if (unusable_) {
      return JournalStatus::WriteFailed;
    }
    if (over_bound_) {
      return JournalStatus::CapacityExhausted;
    }
    if (index_.size() + 1U > config_.max_retained_records) {
      return JournalStatus::CapacityExhausted;
    }
    if (retained_bytes_ + intent_frame.size() > config_.max_journal_bytes) {
      return JournalStatus::CapacityExhausted;
    }
    IndexEntry intent_entry;
    intent_entry.is_outcome = false;
    intent_entry.in_flight = true;
    intent_entry.request_id = intent.request_id;
    intent_entry.intent = intent;
    const JournalStatus append_status = append_frame_locked(intent_frame, intent_entry);
    if (append_status != JournalStatus::Ok) {
      return append_status;
    }
  }

  // A throwing host callback is intentionally not caught: its exception propagates after the
  // durable intent, which then has no outcome and is surfaced by recovery as an explicit
  // `EvidenceIncomplete` orphan. The call never reports `Ok` for a missing outcome.
  StimulationOutcome produced;
  try {
    produced = emit(intent);
  } catch (...) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (IndexEntry &entry : index_) {
      if (!entry.is_outcome && entry.request_id == intent.request_id) {
        entry.in_flight = false;
        break;
      }
    }
    throw;
  }
  produced.request_id = intent.request_id;
  // Validate the callback-returned kind against the closed vocabulary before encoding: an
  // out-of-vocabulary kind is never appended (which would make the journal write a record its
  // own scan later rejects), so the durable journal stays decodable and the intent is orphaned.
  if (!outcome_kind_in_vocabulary(produced.kind)) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (IndexEntry &entry : index_) {
      if (!entry.is_outcome && entry.request_id == intent.request_id) {
        entry.in_flight = false;
        break;
      }
    }
    return JournalStatus::RejectedConfiguration;
  }
  out = produced;

  const std::vector<std::uint8_t> outcome_frame = encode_outcome_frame(produced);
  {
    std::lock_guard<std::mutex> lock(mutex_);
    for (IndexEntry &entry : index_) {
      if (!entry.is_outcome && entry.request_id == intent.request_id) {
        entry.in_flight = false;
        break;
      }
    }
    if (index_.size() + 1U > config_.max_retained_records) {
      return JournalStatus::EvidenceIncomplete;
    }
    if (retained_bytes_ + outcome_frame.size() > config_.max_journal_bytes) {
      return JournalStatus::EvidenceIncomplete;
    }
    IndexEntry outcome_entry;
    outcome_entry.is_outcome = true;
    outcome_entry.request_id = produced.request_id;
    outcome_entry.outcome = produced;
    const JournalStatus append_status = append_frame_locked(outcome_frame, outcome_entry);
    if (append_status != JournalStatus::Ok) {
      return JournalStatus::EvidenceIncomplete;
    }
  }
  return JournalStatus::Ok;
}

JournalStatus StimulationJournal::resolve(std::uint64_t request_id,
                                          const StimulationOutcome &outcome) {
  StimulationOutcome normalized = outcome;
  normalized.request_id = request_id;
  // Reject an out-of-vocabulary kind before encoding and before any mutation, so a resolution can
  // never write a record that the recovery scan would later reject as corrupt.
  if (!outcome_kind_in_vocabulary(normalized.kind)) {
    return JournalStatus::RejectedConfiguration;
  }
  const std::vector<std::uint8_t> outcome_frame = encode_outcome_frame(normalized);

  std::lock_guard<std::mutex> lock(mutex_);
  if (!opened_ || storage_ == nullptr) {
    return JournalStatus::RejectedConfiguration;
  }
  if (corrupt_) {
    return JournalStatus::CorruptRecord;
  }
  if (unusable_) {
    return JournalStatus::WriteFailed;
  }
  if (over_bound_) {
    return JournalStatus::CapacityExhausted;
  }

  std::size_t intents_with_id = 0U;
  std::size_t outcomes_with_id = 0U;
  for (const IndexEntry &entry : index_) {
    if (entry.request_id != request_id) {
      continue;
    }
    if (entry.is_outcome) {
      ++outcomes_with_id;
    } else {
      if (entry.in_flight) {
        return JournalStatus::RejectedConfiguration;
      }
      ++intents_with_id;
    }
  }
  if (intents_with_id == 0U) {
    return JournalStatus::NotFound;
  }
  // One-to-one resolution: an identity is fully resolved only when every retained intent carrying
  // it has a distinct outcome, so a still-unresolved duplicate intent remains resolvable and each
  // resolution resolves exactly one intent.
  if (outcomes_with_id >= intents_with_id) {
    return JournalStatus::AlreadyResolved;
  }
  if (index_.size() + 1U > config_.max_retained_records) {
    return JournalStatus::CapacityExhausted;
  }
  if (retained_bytes_ + outcome_frame.size() > config_.max_journal_bytes) {
    return JournalStatus::CapacityExhausted;
  }
  IndexEntry outcome_entry;
  outcome_entry.is_outcome = true;
  outcome_entry.request_id = request_id;
  outcome_entry.outcome = normalized;
  return append_frame_locked(outcome_frame, outcome_entry);
}

} // namespace validation
} // namespace xcom
} // namespace xverse
