/**
 * \file validation_session.hpp
 * \brief Standalone C++20 foundation for an explicit time authority, an immutable
 *        local validation permit, and a bounded validation-session lifecycle.
 *
 * \details
 * This header belongs to the source-free T025 engineering candidate of
 * `xverse::xcom::validation`. It uses only the C++20 standard library and includes no
 * predecessor header. It defines no communication item, transport, gateway, network
 * listener, journal, lease, dashboard, persistent store, or external-service surface, and
 * every nominal code path is free of file, socket, and environment I/O.
 *
 * The three cooperating components are:
 * - `TimeAuthority` — declared clock domains, bounded current-time reads, and directed
 *   source-to-destination mappings with a live tolerance cross-check.
 * - `Permit` / `PermitBuilder` — an immutable envelope binding exactly one session
 *   identity and its full operational context, with a deterministic FNV-1a content
 *   identity and a closed allowed-action set.
 * - `SessionManager` — controller identity/generation, exactly-once consumption, bounded
 *   live-session capacity, and the validation-session lifecycle state machine.
 *
 * \note This is an internal candidate. It does not establish accepted X-COM delivery,
 *       predecessor regression, source compatibility, protected verification, or
 *       production readiness.
 */

#ifndef XVERSE_XCOM_VALIDATION_SESSION_HPP_
#define XVERSE_XCOM_VALIDATION_SESSION_HPP_

#include <array>
#include <compare>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <initializer_list>
#include <limits>
#include <mutex>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>

/// \brief Root namespace of the sanitized standalone candidate.
/// \unitspec{T025-U-TYPES}
namespace xverse {

/// \brief Communication subsystem namespace reserved for the source-free candidate.
/// \unitspec{T025-U-TYPES}
namespace xcom {

/// \brief Bounded validation-session foundation namespace; uses only the C++20 standard library.
/// \unitspec{T025-U-TYPES}
namespace validation {

/// \brief Domain-local integer timestamp.
/// \unitspec{T025-U-TYPES}
using Timestamp = std::int64_t;
/// \brief Maximum admissible magnitude of a mapping divergence.
/// \unitspec{T025-U-TYPES}
using Tolerance = std::uint64_t;
/// \brief Signed offset applied by a directed clock mapping.
/// \unitspec{T025-U-TYPES}
using SignedOffset = std::int64_t;
/// \brief Authority-issued clock-domain token; the value `0` is reserved as invalid.
/// \unitspec{T025-U-TYPES}
using ClockDomainId = std::uint32_t;
/// \brief Monotonic per-controller generation.
/// \unitspec{T025-U-TYPES}
using Generation = std::uint64_t;
/// \brief Host-supplied one-time value bound into a permit.
/// \unitspec{T025-U-TYPES}
using Nonce = std::uint64_t;
/// \brief Host-issued controller identity (16 bytes).
/// \unitspec{T025-U-TYPES}
using ControllerId = std::array<std::uint8_t, 16>;
/// \brief Host-issued manager uniqueness scope (16 bytes); non-zero and distinct per manager
///        instance and per recreation, and bound into every issued handle.
/// \unitspec{T025-U-TYPES}
using ManagerScope = std::array<std::uint8_t, 16>;
/// \brief Host-issued session identity (16 bytes).
/// \unitspec{T025-U-TYPES}
using SessionId = std::array<std::uint8_t, 16>;
/// \brief Deterministic permit content identity (16 bytes).
/// \unitspec{T025-U-TYPES}
using PermitId = std::array<std::uint8_t, 16>;
/// \brief Host-supplied plan digest bound into a permit (32 bytes).
/// \unitspec{T025-U-TYPES}
using PlanDigest = std::array<std::uint8_t, 32>;
/// \brief Bitmask of one or more `Action` bits.
/// \unitspec{T025-U-TYPES}
using ActionMask = std::uint32_t;

/// \brief Reserved invalid clock-domain token.
/// \unitspec{T025-U-TYPES}
inline constexpr ClockDomainId kInvalidClockDomain = 0;
/// \brief All currently defined action bits.
/// \unitspec{T025-U-TYPES}
inline constexpr ActionMask kDefinedActionMask = 0x7FU;

/// \brief Closed classification of a declared clock domain.
/// \unitspec{T025-U-TYPES}
enum class ClockKind : std::uint8_t {
  Monotonic, ///< Non-decreasing host clock; readings below the prior baseline are a regression. \unitspec{T025-U-TYPES}
  WallClock, ///< Wall-clock domain; readings are not required to be monotonic. \unitspec{T025-U-TYPES}
};

/// \brief Closed set of lifecycle actions; each enumerator is one atomic bit.
/// \unitspec{T025-U-TYPES}
enum class Action : std::uint32_t {
  Arm = 1U << 0U,      ///< Arms a declared session. \unitspec{T025-U-TYPES}
  Activate = 1U << 1U, ///< Activates an armed session. \unitspec{T025-U-TYPES}
  Close = 1U << 2U,    ///< Begins closing an active session. \unitspec{T025-U-TYPES}
  Finalize =
      1U
      << 3U, ///< Finalizes a closing session into the terminal `closed` state. \unitspec{T025-U-TYPES}
  Expire = 1U << 4U, ///< Moves a session to the terminal `expired` state. \unitspec{T025-U-TYPES}
  Revoke = 1U << 5U, ///< Moves a session to the terminal `revoked` state. \unitspec{T025-U-TYPES}
  MarkEvidenceIncomplete =
      1U
      << 6U, ///< Moves a session to the terminal `evidence_incomplete` state. \unitspec{T025-U-TYPES}
};

/// \brief Returns the mask of every currently defined action bit.
/// \return The mask of all defined action bits.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr ActionMask defined_action_bits() noexcept { return kDefinedActionMask; }

/// \brief Reports whether a candidate action mask contains only defined bits.
/// \param mask Candidate action mask.
/// \return `true` when `mask` is non-zero and contains no undefined action bit.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr bool is_defined_action(ActionMask mask) noexcept {
  return mask != 0U && (mask & ~kDefinedActionMask) == 0U;
}

/// \brief Reports whether a candidate action mask holds exactly one bit.
/// \param mask Candidate action mask.
/// \return `true` when `mask` contains exactly one bit.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr bool is_single_action(ActionMask mask) noexcept {
  return mask != 0U && (mask & (mask - 1U)) == 0U;
}

/// \brief Converts an action into its single-bit mask.
/// \param action A lifecycle action.
/// \return The single-bit mask of `action`.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr ActionMask to_mask(Action action) noexcept {
  return static_cast<ActionMask>(action);
}

/// \brief Returns the stable name of a single defined action mask.
/// \param mask Candidate action mask.
/// \return The stable, non-empty action name for a single defined action bit, or an empty
///         view for a zero, composite, or undefined-bit mask. A mask containing an undefined
///         bit is never named as a defined action.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr std::string_view action_mask_name(ActionMask mask) noexcept {
  switch (mask) {
  case 1U << 0U:
    return "Arm";
  case 1U << 1U:
    return "Activate";
  case 1U << 2U:
    return "Close";
  case 1U << 3U:
    return "Finalize";
  case 1U << 4U:
    return "Expire";
  case 1U << 5U:
    return "Revoke";
  case 1U << 6U:
    return "MarkEvidenceIncomplete";
  default:
    return {};
  }
}

/// \brief Lifecycle states of a validation session.
/// \unitspec{T025-U-TYPES}
enum class LifecycleState : std::uint8_t {
  declared, ///< Created by a successful consumption; no action applied. \unitspec{T025-U-TYPES}
  armed,    ///< `Arm` applied. \unitspec{T025-U-TYPES}
  active,   ///< `Activate` applied. \unitspec{T025-U-TYPES}
  closing,  ///< `Close` applied. \unitspec{T025-U-TYPES}
  closed,   ///< Terminal; `Finalize` applied. \unitspec{T025-U-TYPES}
  expired,  ///< Terminal; `Expire` applied. \unitspec{T025-U-TYPES}
  revoked,  ///< Terminal; `Revoke` applied. \unitspec{T025-U-TYPES}
  evidence_incomplete, ///< Terminal; `MarkEvidenceIncomplete` applied. \unitspec{T025-U-TYPES}
};

/// \brief Reports whether a lifecycle state is terminal.
/// \param state A lifecycle state.
/// \return `true` for the terminal states `closed`, `expired`, `revoked`, and
///         `evidence_incomplete`.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr bool is_terminal(LifecycleState state) noexcept {
  return state == LifecycleState::closed || state == LifecycleState::expired ||
         state == LifecycleState::revoked || state == LifecycleState::evidence_incomplete;
}

/// \brief Closed set of finite quota kinds.
/// \unitspec{T025-U-TYPES}
enum class QuotaKind : std::uint8_t {
  Operations, ///< Consumed by each successful mutating lifecycle transition. \unitspec{T025-U-TYPES}
  Evidence, ///< Reserved for evidence bookkeeping; not decremented by a transition. \unitspec{T025-U-TYPES}
};

/// \brief A finite named quota.
/// \unitspec{T025-U-TYPES}
struct Quota {
  /// \brief Quota family.
  /// \unitspec{T025-U-TYPES}
  QuotaKind kind{QuotaKind::Operations};
  /// \brief Non-zero finite limit; zero is rejected at permit construction.
  /// \unitspec{T025-U-TYPES}
  std::uint32_t limit{0};

  /// \brief Value equality over both fields.
  /// \unitspec{T025-U-TYPES}
  friend constexpr bool operator==(const Quota &, const Quota &) noexcept = default;
};

/// \brief Closed, enumerable outcome vocabulary; declaration order is diagnostic precedence
///        order, highest precedence first.
/// \unitspec{T025-U-TYPES}
enum class Result : std::uint8_t {
  InvalidHandle, ///< Handle matches no live session and no registered controller. \unitspec{T025-U-TYPES}
  ForeignHandle, ///< Controller id never registered by this manager. \unitspec{T025-U-TYPES}
  RecreatedController, ///< Controller id superseded by a recreated controller of the same name. \unitspec{T025-U-TYPES}
  StaleHandle, ///< Controller matches but the handle generation is older. \unitspec{T025-U-TYPES}
  SessionNotFound, ///< Controller/generation match but the session id is not live. \unitspec{T025-U-TYPES}
  UnknownClock,       ///< Clock domain not declared. \unitspec{T025-U-TYPES}
  ClockSourceFailure, ///< Host time source returned no reading. \unitspec{T025-U-TYPES}
  ClockOutOfBounds, ///< Reading or mapped value outside the declared bound. \unitspec{T025-U-TYPES}
  ClockRegression,  ///< Monotonic reading earlier than the prior reading. \unitspec{T025-U-TYPES}
  ClockOverflow,    ///< Mapped value not representable in `Timestamp`. \unitspec{T025-U-TYPES}
  MissingMapping,   ///< No declared source-to-destination mapping. \unitspec{T025-U-TYPES}
  ToleranceExceeded, ///< Mapped value diverges from destination beyond tolerance. \unitspec{T025-U-TYPES}
  PermitNotYetValid, ///< Resolved time is before the permit validity start. \unitspec{T025-U-TYPES}
  PermitExpired, ///< Resolved time is at or after the permit validity end. \unitspec{T025-U-TYPES}
  UndefinedAction,   ///< Requested mask contains an undefined action bit. \unitspec{T025-U-TYPES}
  ActionNotAllowed,  ///< Requested action is not in the permit allowed set. \unitspec{T025-U-TYPES}
  TerminalState,     ///< Transition attempted from a terminal state. \unitspec{T025-U-TYPES}
  InvalidTransition, ///< Legal-state conflict with a non-terminal state. \unitspec{T025-U-TYPES}
  PermitMismatch, ///< Context differs from the permit in the located field. \unitspec{T025-U-TYPES}
  InvalidPermit,  ///< Permit construction validation failed. \unitspec{T025-U-TYPES}
  SessionAlreadyConsumed, ///< Session identity already bound to a consumed permit. \unitspec{T025-U-TYPES}
  PermitAlreadyConsumed, ///< Permit identity already consumed. \unitspec{T025-U-TYPES}
  QuotaExhausted,        ///< The action's mapped quota is zero. \unitspec{T025-U-TYPES}
  CapacityExhausted,     ///< A bounded table or set is full. \unitspec{T025-U-TYPES}
  InvalidController, ///< A zero or already-registered controller identity was presented. \unitspec{T025-U-TYPES}
  AlreadyApplied, ///< Safe idempotent repeat. \unitspec{T025-U-TYPES}
  Ok,             ///< Success. \unitspec{T025-U-TYPES}
};

/// \brief Returns the zero-based precedence rank of a result code.
/// \param result A result code.
/// \return The zero-based precedence rank (lower rank binds earlier).
/// \unitspec{T025-U-DIAGNOSTIC}
[[nodiscard]] constexpr std::uint8_t precedence_rank(Result result) noexcept {
  return static_cast<std::uint8_t>(result);
}

/// \brief Orders two result codes by precedence rank.
/// \param a First result.
/// \param b Second result.
/// \return Strong ordering by precedence rank, so that a lower rank is "less".
/// \unitspec{T025-U-DIAGNOSTIC}
[[nodiscard]] constexpr std::strong_ordering compare(Result a, Result b) noexcept {
  return precedence_rank(a) <=> precedence_rank(b);
}

/// \brief Names the bound permit field that produced a `PermitMismatch`.
/// \unitspec{T025-U-TYPES}
enum class FieldLocator : std::uint8_t {
  SessionId,      ///< Session identity. \unitspec{T025-U-TYPES}
  PlanDigest,     ///< Plan digest. \unitspec{T025-U-TYPES}
  Scenario,       ///< Scenario tag. \unitspec{T025-U-TYPES}
  Deployment,     ///< Deployment tag. \unitspec{T025-U-TYPES}
  Environment,    ///< Environment tag. \unitspec{T025-U-TYPES}
  Tool,           ///< Tool tag. \unitspec{T025-U-TYPES}
  Interface,      ///< Interface tag. \unitspec{T025-U-TYPES}
  Target,         ///< Target tag. \unitspec{T025-U-TYPES}
  Nonce,          ///< One-time nonce. \unitspec{T025-U-TYPES}
  AllowedActions, ///< Allowed action set. \unitspec{T025-U-TYPES}
  Validity,       ///< Validity interval (domain, start, end). \unitspec{T025-U-TYPES}
  Quota,          ///< Quota list. \unitspec{T025-U-TYPES}
};

/**
 * \brief Bounded, ordered, payload-free diagnostic value.
 *
 * A `Diagnostic` holds at most `capacity` enumerable `Result` codes ordered from the
 * highest precedence to the lowest, plus at most one bounded numeric locator. It holds no
 * string, item, observation, or free-form content. The same input yields the same code
 * sequence across runs and builds. It has no shared state and is safe to copy across
 * threads.
 * \unitspec{T025-U-DIAGNOSTIC}
 */
class Diagnostic {
public:
  /// \brief Maximum number of retained result codes.
  /// \unitspec{T025-U-DIAGNOSTIC}
  static constexpr std::size_t capacity = 8;

  /// \brief Constructs an empty diagnostic whose primary code is `Result::Ok`.
  /// \unitspec{T025-U-DIAGNOSTIC}
  Diagnostic() noexcept = default;

  /// \brief Builds a single-code diagnostic from the first applicable failure.
  /// \param applicable Candidate failure codes; the highest-precedence (lowest rank)
  ///        entry is retained. An empty list yields a single `Result::Ok` code.
  /// \param locator Optional bounded numeric locator for the located field.
  /// \return An immutable diagnostic with exactly one code.
  /// \unitspec{T025-U-DIAGNOSTIC}
  [[nodiscard]] static Diagnostic
  from_first(std::initializer_list<Result> applicable,
             std::optional<std::uint32_t> locator = std::nullopt) noexcept;

  /// \brief Builds an ordered multi-code diagnostic for precedence inspection.
  /// \param codes Candidate result codes; they are ordered by precedence and the
  ///        sequence is capped at `capacity` entries.
  /// \param locator Optional bounded numeric locator for the located field.
  /// \return An immutable, bounded, deterministically ordered diagnostic.
  /// \unitspec{T025-U-DIAGNOSTIC}
  [[nodiscard]] static Diagnostic
  accumulate(std::initializer_list<Result> codes,
             std::optional<std::uint32_t> locator = std::nullopt) noexcept;

  /// \brief Returns the retained code sequence, highest precedence first.
  /// \return The retained code sequence.
  /// \unitspec{T025-U-DIAGNOSTIC}
  [[nodiscard]] std::span<const Result> codes() const noexcept;

  /// \brief Returns the primary (first) code.
  /// \return The primary code, or `Result::Ok` when the sequence is empty.
  /// \unitspec{T025-U-DIAGNOSTIC}
  [[nodiscard]] Result primary() const noexcept;

  /// \brief Returns the number of retained codes.
  /// \return The number of retained codes.
  /// \unitspec{T025-U-DIAGNOSTIC}
  [[nodiscard]] std::size_t size() const noexcept;

  /// \brief Reports whether no code is retained.
  /// \return `true` when no code is retained.
  /// \unitspec{T025-U-DIAGNOSTIC}
  [[nodiscard]] bool empty() const noexcept;

  /// \brief Returns the optional bounded numeric locator.
  /// \return The optional bounded numeric locator.
  /// \unitspec{T025-U-DIAGNOSTIC}
  [[nodiscard]] std::optional<std::uint32_t> locator() const noexcept;

  /// \brief Value equality over the retained sequence and locator.
  /// \unitspec{T025-U-DIAGNOSTIC}
  friend bool operator==(const Diagnostic &, const Diagnostic &) noexcept = default;

private:
  /// \brief Retained result-code storage.
  /// \unitspec{T025-U-DIAGNOSTIC}
  std::array<Result, capacity> codes_{};
  /// \brief Number of retained result codes.
  /// \unitspec{T025-U-DIAGNOSTIC}
  std::size_t size_{0};
  /// \brief Optional bounded numeric locator.
  /// \unitspec{T025-U-DIAGNOSTIC}
  std::optional<std::uint32_t> locator_{};
};

static_assert(!std::is_constructible_v<Diagnostic, std::string_view>,
              "Diagnostic must be payload-free");
static_assert(sizeof(Diagnostic) <= 128U, "Diagnostic must stay bounded");

/**
 * \brief Bounded printable-ASCII tag (at most 63 bytes, no NUL).
 *
 * Used for the scenario, deployment, environment, tool, interface, and target fields.
 * Construction does not validate; use `make` or `is_valid` at a validation boundary. A
 * `Tag` is an immutable value safe to copy across threads.
 * \unitspec{T025-U-TYPES}
 */
class Tag {
public:
  /// \brief Maximum accepted tag length in bytes.
  /// \unitspec{T025-U-TYPES}
  static constexpr std::size_t max_length = 63;
  /// \brief Maximum accepted tag length as a signed value for length comparisons.
  /// \unitspec{T025-U-TYPES}
  static constexpr std::ptrdiff_t max_length_signed = 63;

  /// \brief Constructs an empty tag.
  /// \unitspec{T025-U-TYPES}
  Tag() noexcept = default;

  /// \brief Constructs a tag from already validated text.
  /// \param value Already validated tag text.
  /// \unitspec{T025-U-TYPES}
  explicit Tag(std::string value);

  /// \brief Builds a validated tag or reports invalidity.
  /// \param candidate Candidate tag text.
  /// \return A validated tag, or `std::nullopt` when `candidate` is not a valid tag.
  /// \unitspec{T025-U-TYPES}
  [[nodiscard]] static std::optional<Tag> make(std::string_view candidate);

  /// \brief Reports whether candidate text is a valid tag.
  /// \param candidate Candidate tag text.
  /// \return `true` when `candidate` is non-empty, at most 63 bytes of printable
  ///         non-NUL ASCII, and contains no NUL byte.
  /// \unitspec{T025-U-TYPES}
  [[nodiscard]] static bool is_valid(std::string_view candidate) noexcept;

  /// \brief Returns the tag text.
  /// \return The tag text.
  /// \unitspec{T025-U-TYPES}
  [[nodiscard]] const std::string &value() const noexcept;

  /// \brief Reports whether the tag text is empty.
  /// \return `true` when the tag text is empty.
  /// \unitspec{T025-U-TYPES}
  [[nodiscard]] bool empty() const noexcept;

  /// \brief Value equality over the tag text.
  /// \unitspec{T025-U-TYPES}
  friend bool operator==(const Tag &, const Tag &) noexcept = default;

private:
  /// \brief Tag text storage.
  /// \unitspec{T025-U-TYPES}
  std::string value_{};
};

/// \brief File-local helpers backing the public deterministic content digest.
/// \unitspec{T025-U-TYPES}
namespace detail {

/// \brief High 64 bits of the FNV-1a 128-bit prime.
/// \unitspec{T025-U-TYPES}
inline constexpr std::uint64_t kFnvPrimeHigh = 0x0000000001000000ULL;
/// \brief Low 64 bits of the FNV-1a 128-bit prime.
/// \unitspec{T025-U-TYPES}
inline constexpr std::uint64_t kFnvPrimeLow = 0x000000000000013BULL;
/// \brief High 64 bits of the FNV-1a 128-bit offset basis.
/// \unitspec{T025-U-TYPES}
inline constexpr std::uint64_t kFnvOffsetHigh = 0x6C62272E07BB0142ULL;
/// \brief Low 64 bits of the FNV-1a 128-bit offset basis.
/// \unitspec{T025-U-TYPES}
inline constexpr std::uint64_t kFnvOffsetLow = 0x62B821756295C58DULL;

/// \brief Returns the high 64 bits of an unsigned 64x64 product.
/// \param a First factor.
/// \param b Second factor.
/// \return The high 64 bits of `a * b`.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] inline std::uint64_t multiply_high(std::uint64_t a, std::uint64_t b) noexcept {
  const std::uint64_t a_low = a & 0xFFFFFFFFULL;
  const std::uint64_t a_high = a >> 32U;
  const std::uint64_t b_low = b & 0xFFFFFFFFULL;
  const std::uint64_t b_high = b >> 32U;
  const std::uint64_t low_product = a_low * b_low;
  const std::uint64_t middle = a_high * b_low + (low_product >> 32U);
  const std::uint64_t upper = a_low * b_high + (middle & 0xFFFFFFFFULL);
  return a_high * b_high + (middle >> 32U) + (upper >> 32U);
}

/// \brief Computes the deterministic 128-bit FNV-1a digest of a byte span.
/// \param bytes Byte sequence to digest.
/// \return The 16-byte FNV-1a digest.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] inline PermitId fnv1a_128(std::span<const std::uint8_t> bytes) noexcept {
  std::uint64_t high = kFnvOffsetHigh;
  std::uint64_t low = kFnvOffsetLow;
  for (const std::uint8_t byte : bytes) {
    low ^= static_cast<std::uint64_t>(byte);
    const std::uint64_t carry = multiply_high(low, kFnvPrimeLow);
    const std::uint64_t next_high = carry + (high * kFnvPrimeLow) + (low * kFnvPrimeHigh);
    high = next_high;
    low *= kFnvPrimeLow;
  }
  PermitId digest{};
  for (std::size_t index = 0; index < 8; ++index) {
    const std::size_t shift = index * 8U;
    digest[index] = static_cast<std::uint8_t>((low >> shift) & 0xFFU);
    digest[index + 8U] = static_cast<std::uint8_t>((high >> shift) & 0xFFU);
  }
  return digest;
}

} // namespace detail

/// \brief Computes the deterministic 128-bit FNV-1a content digest of a byte sequence.
/// \param bytes Arbitrary byte sequence.
/// \return The 16-byte content digest.
/// \note This is local bookkeeping identity, not a cryptographic claim.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] inline PermitId canonical_digest(const std::vector<std::uint8_t> &bytes) {
  return detail::fnv1a_128(bytes);
}

/**
 * \brief Opaque handle addressing one live validation session.
 *
 * Authenticity rests on the issuing `SessionManager`'s internal table plus the host-
 * controlled uniqueness scope (opaque issuance), not on cryptography. A handle binds the
 * issuing manager scope, controller identity, generation, and session identity; it is
 * meaningful only with the matching scope, controller identity, and generation, and is a
 * bounded prototype control.
 * \unitspec{T025-U-SESSION}
 */
struct SessionHandle {
  /// \brief Issuing manager uniqueness scope.
  /// \unitspec{T025-U-SESSION}
  ManagerScope scope{};
  /// \brief Issuing controller identity.
  /// \unitspec{T025-U-SESSION}
  ControllerId controller{};
  /// \brief Controller generation at issuance.
  /// \unitspec{T025-U-SESSION}
  Generation generation{0};
  /// \brief Bound session identity.
  /// \unitspec{T025-U-SESSION}
  SessionId session{};

  /// \brief Value equality over all three fields.
  /// \unitspec{T025-U-SESSION}
  friend bool operator==(const SessionHandle &, const SessionHandle &) noexcept = default;
};

/**
 * \brief Immutable observable snapshot of one validation session.
 *
 * Used to prove that a rejected operation left state byte-identical.
 * \unitspec{T025-U-SESSION}
 */
struct SessionSnapshot {
  /// \brief Current lifecycle state.
  /// \unitspec{T025-U-SESSION}
  LifecycleState state{LifecycleState::declared};
  /// \brief Bound permit identity.
  /// \unitspec{T025-U-SESSION}
  PermitId permit_id{};
  /// \brief Bound session identity.
  /// \unitspec{T025-U-SESSION}
  SessionId session_id{};
  /// \brief Owning controller identity.
  /// \unitspec{T025-U-SESSION}
  ControllerId controller{};
  /// \brief Owning controller generation.
  /// \unitspec{T025-U-SESSION}
  Generation generation{0};
  /// \brief Remaining `QuotaKind::Operations` budget.
  /// \unitspec{T025-U-SESSION}
  std::uint32_t operations_remaining{0};
  /// \brief Remaining `QuotaKind::Evidence` budget.
  /// \unitspec{T025-U-SESSION}
  std::uint32_t evidence_remaining{0};

  /// \brief Value equality over every observed field.
  /// \unitspec{T025-U-SESSION}
  friend bool operator==(const SessionSnapshot &, const SessionSnapshot &) noexcept = default;
};

/**
 * \brief Caller-asserted runtime envelope compared field-by-field to a `Permit`.
 *
 * The consumption path compares each field to the bound permit and reports the first
 * mismatch with its `FieldLocator`. A `SessionContext` is a plain value; it is copied into
 * the comparison and never retained by the manager.
 * \unitspec{T025-U-SESSION}
 */
struct SessionContext {
  /// \brief Asserted session identity.
  /// \unitspec{T025-U-SESSION}
  SessionId session_id{};
  /// \brief Asserted plan digest.
  /// \unitspec{T025-U-SESSION}
  PlanDigest plan_digest{};
  /// \brief Asserted scenario tag.
  /// \unitspec{T025-U-SESSION}
  std::string scenario;
  /// \brief Asserted deployment tag.
  /// \unitspec{T025-U-SESSION}
  std::string deployment;
  /// \brief Asserted environment tag.
  /// \unitspec{T025-U-SESSION}
  std::string environment;
  /// \brief Asserted tool tag.
  /// \unitspec{T025-U-SESSION}
  std::string tool;
  /// \brief Asserted interface tag.
  /// \unitspec{T025-U-SESSION}
  std::string interface_name;
  /// \brief Asserted target tag.
  /// \unitspec{T025-U-SESSION}
  std::string target;
  /// \brief Asserted one-time nonce.
  /// \unitspec{T025-U-SESSION}
  Nonce nonce{0};
  /// \brief Asserted validity domain.
  /// \unitspec{T025-U-SESSION}
  ClockDomainId validity_domain{kInvalidClockDomain};
  /// \brief Asserted validity start.
  /// \unitspec{T025-U-SESSION}
  Timestamp valid_from{0};
  /// \brief Asserted validity end (exclusive).
  /// \unitspec{T025-U-SESSION}
  Timestamp valid_until{0};
  /// \brief Asserted allowed action set.
  /// \unitspec{T025-U-SESSION}
  std::vector<ActionMask> allowed_actions;
  /// \brief Asserted quota list.
  /// \unitspec{T025-U-SESSION}
  std::vector<Quota> quotas;
};

/// \brief Host-injected bounded clock source returning the domain-local reading.
///
/// Returns the domain-local reading, or `std::nullopt` to signal a source failure. The
/// authority never fabricates time and never falls back to another domain.
/// \unitspec{T025-U-TYPES}
using ClockSource = std::function<std::optional<Timestamp>()>;

/**
 * \brief Immutable host-issued validation permit.
 *
 * A permit binds exactly one session identity, plan digest, six tags, nonce, one validity
 * interval, one allowed action set, and a finite quota list. It exposes const accessors
 * only and is copyable because it is immutable; it may be shared across threads without
 * synchronization. It is produced only by `PermitBuilder`.
 *
 * \note `permit_id()` is the deterministic content digest of the permit envelope
 *       *excluding* the session identity. The session identity is still bound and reported
 *       by `session_id()`, but excluding it makes a permit presented for a different
 *       session a detectable permit replay (`Result::PermitAlreadyConsumed`) rather than a
 *       fresh permit, as required by the RP-03/RP-04 expected results.
 * \unitspec{T025-U-PERMIT}
 */
class Permit {
public:
  /// \brief Constructs an unbuilt permit with zero identities and a zero content identity.
  /// \unitspec{T025-U-PERMIT}
  Permit() = default;
  /// \brief Copy constructor; permits are immutable values.
  /// \unitspec{T025-U-PERMIT}
  Permit(const Permit &) = default;
  /// \brief Copy assignment; permits are immutable values.
  /// \unitspec{T025-U-PERMIT}
  Permit &operator=(const Permit &) = default;
  /// \brief Move constructor; permits are immutable values.
  /// \unitspec{T025-U-PERMIT}
  Permit(Permit &&) = default;
  /// \brief Move assignment; permits are immutable values.
  /// \unitspec{T025-U-PERMIT}
  Permit &operator=(Permit &&) = default;
  /// \brief Destructor.
  /// \unitspec{T025-U-PERMIT}
  ~Permit() = default;

  /// \brief Returns the bound session identity.
  /// \return The bound session identity.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const SessionId &session_id() const noexcept;
  /// \brief Returns the bound plan digest.
  /// \return The bound plan digest.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const PlanDigest &plan_digest() const noexcept;
  /// \brief Returns the bound scenario tag.
  /// \return The bound scenario tag.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::string &scenario() const noexcept;
  /// \brief Returns the bound deployment tag.
  /// \return The bound deployment tag.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::string &deployment() const noexcept;
  /// \brief Returns the bound environment tag.
  /// \return The bound environment tag.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::string &environment() const noexcept;
  /// \brief Returns the bound tool tag.
  /// \return The bound tool tag.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::string &tool() const noexcept;
  /// \brief Returns the bound interface tag.
  /// \return The bound interface tag.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::string &interface_name() const noexcept;
  /// \brief Returns the bound target tag.
  /// \return The bound target tag.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::string &target() const noexcept;
  /// \brief Returns the bound one-time nonce.
  /// \return The bound one-time nonce.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] Nonce nonce() const noexcept;
  /// \brief Returns the declared validity clock domain.
  /// \return The declared validity clock domain.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] ClockDomainId validity_domain() const noexcept;
  /// \brief Returns the inclusive validity start.
  /// \return The inclusive validity start.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] Timestamp valid_from() const noexcept;
  /// \brief Returns the exclusive validity end.
  /// \return The exclusive validity end.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] Timestamp valid_until() const noexcept;
  /// \brief Returns the explicitly allowed action masks, in insertion order.
  /// \return The explicitly allowed action masks.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::vector<ActionMask> &allowed_actions() const noexcept;
  /// \brief Returns the finite quota list, in insertion order.
  /// \return The finite quota list.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const std::vector<Quota> &quotas() const noexcept;
  /// \brief Returns the deterministic content identity of the permit envelope.
  /// \return The deterministic content identity.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] const PermitId &permit_id() const noexcept;

  /// \brief Reports whether a mask is listed verbatim in the allowed set.
  /// \param mask Requested action mask.
  /// \return `true` when `mask` is listed verbatim in the allowed set. A composite mask is
  ///         never interpreted as its component actions.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] bool allows(ActionMask mask) const noexcept;

private:
  /// \brief Builder granted private access to construct and fill a permit.
  /// \unitspec{T025-U-PERMIT}
  friend class PermitBuilder;

  /// \brief Bound session identity.
  /// \unitspec{T025-U-PERMIT}
  SessionId session_id_{};
  /// \brief Bound plan digest.
  /// \unitspec{T025-U-PERMIT}
  PlanDigest plan_digest_{};
  /// \brief Bound scenario tag.
  /// \unitspec{T025-U-PERMIT}
  std::string scenario_{};
  /// \brief Bound deployment tag.
  /// \unitspec{T025-U-PERMIT}
  std::string deployment_{};
  /// \brief Bound environment tag.
  /// \unitspec{T025-U-PERMIT}
  std::string environment_{};
  /// \brief Bound tool tag.
  /// \unitspec{T025-U-PERMIT}
  std::string tool_{};
  /// \brief Bound interface tag.
  /// \unitspec{T025-U-PERMIT}
  std::string interface_name_{};
  /// \brief Bound target tag.
  /// \unitspec{T025-U-PERMIT}
  std::string target_{};
  /// \brief Bound one-time nonce.
  /// \unitspec{T025-U-PERMIT}
  Nonce nonce_{0};
  /// \brief Declared validity clock domain.
  /// \unitspec{T025-U-PERMIT}
  ClockDomainId validity_domain_{kInvalidClockDomain};
  /// \brief Inclusive validity start.
  /// \unitspec{T025-U-PERMIT}
  Timestamp valid_from_{0};
  /// \brief Exclusive validity end.
  /// \unitspec{T025-U-PERMIT}
  Timestamp valid_until_{0};
  /// \brief Explicitly allowed action masks.
  /// \unitspec{T025-U-PERMIT}
  std::vector<ActionMask> allowed_actions_{};
  /// \brief Finite quota list.
  /// \unitspec{T025-U-PERMIT}
  std::vector<Quota> quotas_{};
  /// \brief Deterministic content identity.
  /// \unitspec{T025-U-PERMIT}
  PermitId permit_id_{};
};

/**
 * \brief Transient validator that produces an immutable `Permit`.
 *
 * Setters record candidate values and return `Result::Ok`; all structural validation is
 * performed by `build`, so that a partially populated builder never yields a permit. A
 * builder is single-threaded by construction and is not shared across threads.
 * \unitspec{T025-U-PERMIT}
 */
class PermitBuilder {
public:
  /// \brief Maximum number of explicitly allowed action masks.
  /// \unitspec{T025-U-PERMIT}
  static constexpr std::size_t max_allowed_actions = 16;
  /// \brief Maximum number of finite quota entries.
  /// \unitspec{T025-U-PERMIT}
  static constexpr std::size_t max_quotas = 8;

  /// \brief Constructs an empty builder.
  /// \unitspec{T025-U-PERMIT}
  PermitBuilder() noexcept = default;

  /// \brief Records the session identity.
  /// \param value Session identity.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_session_id(const SessionId &value) noexcept;
  /// \brief Records the plan digest.
  /// \param value Plan digest.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_plan_digest(const PlanDigest &value) noexcept;
  /// \brief Records the scenario tag text.
  /// \param value Scenario tag text.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_scenario(std::string value);
  /// \brief Records the deployment tag text.
  /// \param value Deployment tag text.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_deployment(std::string value);
  /// \brief Records the environment tag text.
  /// \param value Environment tag text.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_environment(std::string value);
  /// \brief Records the tool tag text.
  /// \param value Tool tag text.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_tool(std::string value);
  /// \brief Records the interface tag text.
  /// \param value Interface tag text.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_interface(std::string value);
  /// \brief Records the target tag text.
  /// \param value Target tag text.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_target(std::string value);
  /// \brief Records the one-time nonce.
  /// \param value One-time nonce.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_nonce(Nonce value) noexcept;
  /// \brief Records the validity interval.
  /// \param domain Validity clock domain.
  /// \param from Inclusive validity start.
  /// \param until Exclusive validity end.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result set_validity(ClockDomainId domain, Timestamp from, Timestamp until) noexcept;
  /// \brief Records an explicitly allowed action mask.
  /// \param mask An explicitly allowed action mask.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result add_allowed_action(ActionMask mask) noexcept;
  /// \brief Records a finite quota entry.
  /// \param quota A finite quota entry.
  /// \return `Result::Ok`.
  /// \unitspec{T025-U-PERMIT}
  Result add_quota(Quota quota) noexcept;

  /// \brief Validates and finalizes the permit.
  /// \param out Receives the built permit only when validation succeeds.
  /// \return `Result::Ok` on success; otherwise `Result::InvalidPermit` with the offending
  ///         field reported by `last_locator()`, or `Result::CapacityExhausted` when a
  ///         bounded builder list is over-full.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] Result build(Permit &out) const;

  /// \brief Returns the locator of the most recent `build` failure, if any.
  /// \return The locator of the most recent `build` failure, if any.
  /// \unitspec{T025-U-PERMIT}
  [[nodiscard]] std::optional<FieldLocator> last_locator() const noexcept;

private:
  /// \brief Candidate session identity.
  /// \unitspec{T025-U-PERMIT}
  SessionId session_id_{};
  /// \brief Candidate plan digest.
  /// \unitspec{T025-U-PERMIT}
  PlanDigest plan_digest_{};
  /// \brief Candidate scenario tag.
  /// \unitspec{T025-U-PERMIT}
  std::string scenario_;
  /// \brief Candidate deployment tag.
  /// \unitspec{T025-U-PERMIT}
  std::string deployment_;
  /// \brief Candidate environment tag.
  /// \unitspec{T025-U-PERMIT}
  std::string environment_;
  /// \brief Candidate tool tag.
  /// \unitspec{T025-U-PERMIT}
  std::string tool_;
  /// \brief Candidate interface tag.
  /// \unitspec{T025-U-PERMIT}
  std::string interface_name_;
  /// \brief Candidate target tag.
  /// \unitspec{T025-U-PERMIT}
  std::string target_;
  /// \brief Candidate one-time nonce.
  /// \unitspec{T025-U-PERMIT}
  Nonce nonce_{0};
  /// \brief Candidate validity clock domain.
  /// \unitspec{T025-U-PERMIT}
  ClockDomainId validity_domain_{kInvalidClockDomain};
  /// \brief Candidate inclusive validity start.
  /// \unitspec{T025-U-PERMIT}
  Timestamp valid_from_{0};
  /// \brief Candidate exclusive validity end.
  /// \unitspec{T025-U-PERMIT}
  Timestamp valid_until_{0};
  /// \brief Candidate allowed action masks.
  /// \unitspec{T025-U-PERMIT}
  std::vector<ActionMask> allowed_actions_;
  /// \brief Candidate quota entries.
  /// \unitspec{T025-U-PERMIT}
  std::vector<Quota> quotas_;
  /// \brief Locator of the most recent `build` failure, if any.
  /// \unitspec{T025-U-PERMIT}
  mutable std::optional<FieldLocator> last_locator_{};
};

/**
 * \brief Explicit time authority owning declared domains and directed mappings.
 *
 * The authority is non-copyable and non-movable: moving would silently invalidate the
 * injected host sources and regression baselines. Construct it with capacity bounds and
 * destroy it before any thread that used it exits. Every method is internally synchronized
 * by one mutex, so concurrent `now`/`convert` calls serialize into a deterministic total
 * order. No code path compares a raw timestamp from one domain with a raw timestamp from
 * another; conversion requires a declared directed mapping. Every declaration carries a
 * monotonic declaration generation, and a deferred commit is accepted only while the addressed
 * domain still carries the generation that produced the observation, so a concurrent
 * re-declaration can never attribute an old reading to its replacement.
 * \unitspec{T025-U-TIME}
 */
class TimeAuthority {
public:
  /// \brief Constructs an authority with bounded domain and mapping tables.
  /// \param max_domains Maximum number of declared clock domains.
  /// \param max_mappings Maximum number of directed mappings.
  /// \unitspec{T025-U-TIME}
  TimeAuthority(std::size_t max_domains, std::size_t max_mappings);
  /// \brief Destructor.
  /// \unitspec{T025-U-TIME}
  ~TimeAuthority() = default;

  /// \brief Copy construction is deleted; the authority is non-copyable.
  /// \unitspec{T025-U-TIME}
  TimeAuthority(const TimeAuthority &) = delete;
  /// \brief Copy assignment is deleted; the authority is non-copyable.
  /// \unitspec{T025-U-TIME}
  TimeAuthority &operator=(const TimeAuthority &) = delete;
  /// \brief Move construction is deleted; the authority is non-movable.
  /// \unitspec{T025-U-TIME}
  TimeAuthority(TimeAuthority &&) = delete;
  /// \brief Move assignment is deleted; the authority is non-movable.
  /// \unitspec{T025-U-TIME}
  TimeAuthority &operator=(TimeAuthority &&) = delete;

  /// \brief Declares or replaces a clock domain.
  /// \param id Domain token; `0` is reserved invalid.
  /// \param source Host-injected reading source, moved into the authority.
  /// \param kind Monotonic or wall-clock semantics.
  /// \param min_value Inclusive lower bound.
  /// \param max_value Inclusive upper bound.
  /// \return `Result::Ok`; `Result::CapacityExhausted` when the domain table is full and
  ///         `id` is new; `Result::UnknownClock` when `id == 0` or the bounds are inverted.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] Result declare_clock(ClockDomainId id, ClockSource source, ClockKind kind,
                                     Timestamp min_value, Timestamp max_value);

  /// \brief Declares or replaces a directed source-to-destination mapping.
  /// \param src Source domain; must already be declared.
  /// \param dst Destination domain; must already be declared.
  /// \param offset Signed offset added to the source value.
  /// \param tolerance Maximum admissible divergence from the destination reading.
  /// \return `Result::Ok`; `Result::UnknownClock` when either domain is undeclared;
  ///         `Result::CapacityExhausted` when the mapping table is full.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] Result declare_mapping(ClockDomainId src, ClockDomainId dst, SignedOffset offset,
                                       Tolerance tolerance);

  /// \brief Reads the bounded current time of a domain.
  /// \param id Declared domain token.
  /// \param out Receives the reading only on `Result::Ok`.
  /// \return `Result::Ok`; `Result::UnknownClock`; `Result::ClockSourceFailure`;
  ///         `Result::ClockOutOfBounds`; `Result::ClockRegression` for a monotonic domain
  ///         whose reading is below the retained baseline. A rejected read leaves the
  ///         baseline unchanged.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] Result now(ClockDomainId id, Timestamp &out);

  /// \brief Maps a source value into a destination domain under a declared rule.
  /// \param src Declared source domain.
  /// \param dst Declared destination domain.
  /// \param value Source-domain value.
  /// \param out Receives the mapped value only on `Result::Ok`.
  /// \return `Result::Ok`; `Result::UnknownClock` when `src` is undeclared;
  ///         `Result::MissingMapping` when no directed `src -> dst` rule exists;
  ///         `Result::ClockOverflow`; `Result::ClockOutOfBounds`;
  ///         `Result::ClockSourceFailure`; `Result::ClockRegression`;
  ///         `Result::ToleranceExceeded` when the mapped value diverges from the
  ///         destination reading by more than the tolerance.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] Result convert(ClockDomainId src, ClockDomainId dst, Timestamp value,
                               Timestamp &out);

  /// \brief Returns the retained regression baseline of a domain.
  /// \param id Domain token.
  /// \return The retained regression baseline, or `std::nullopt` when the domain is
  ///         undeclared or has no successful prior read.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] std::optional<Timestamp> baseline(ClockDomainId id) const;

  /// \brief Returns the number of declared clock domains.
  /// \return The number of declared clock domains.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] std::size_t domain_count() const;

  /// \brief Returns the number of declared mappings.
  /// \return The number of declared mappings.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] std::size_t mapping_count() const;

private:
  /// \brief Grants the session manager access to the non-mutating time-resolution path and to
  ///        the generation-checked deferred baseline advance, so a successful transition advances
  ///        the relevant monotonic baselines of the declarations it observed, and a rejected
  ///        transition — or one whose domain was re-declared in the meantime — changes none of
  ///        them.
  /// \unitspec{T025-U-TIME}
  friend class SessionManager;

  /// \brief Internal clock-domain entry: identity, semantics, bounds, source, and baseline.
  /// \unitspec{T025-U-TIME}
  struct ClockEntry {
    /// \brief Declared domain token.
    /// \unitspec{T025-U-TIME}
    ClockDomainId id{kInvalidClockDomain};
    /// \brief Monotonic or wall-clock semantics.
    /// \unitspec{T025-U-TIME}
    ClockKind kind{ClockKind::Monotonic};
    /// \brief Inclusive lower bound.
    /// \unitspec{T025-U-TIME}
    Timestamp min_value{0};
    /// \brief Inclusive upper bound.
    /// \unitspec{T025-U-TIME}
    Timestamp max_value{0};
    /// \brief Host-injected reading source.
    /// \unitspec{T025-U-TIME}
    ClockSource source{};
    /// \brief Retained regression baseline, if any.
    /// \unitspec{T025-U-TIME}
    std::optional<Timestamp> baseline{};
    /// \brief Monotonic declaration generation, assigned on every successful declaration.
    /// \details A deferred baseline commit is accepted only while the addressed entry still
    ///          carries the generation that produced the observation, so a reading captured
    ///          under one declaration never seeds the baseline of its replacement.
    /// \unitspec{T025-U-TIME}
    std::uint64_t declaration{0};
    /// \brief Whether this slot is occupied.
    /// \unitspec{T025-U-TIME}
    bool occupied{false};
  };

  /// \brief Internal directed-mapping entry: source, destination, offset, and tolerance.
  /// \unitspec{T025-U-TIME}
  struct MappingEntry {
    /// \brief Source domain token.
    /// \unitspec{T025-U-TIME}
    ClockDomainId src{kInvalidClockDomain};
    /// \brief Destination domain token.
    /// \unitspec{T025-U-TIME}
    ClockDomainId dst{kInvalidClockDomain};
    /// \brief Signed offset added to the source value.
    /// \unitspec{T025-U-TIME}
    SignedOffset offset{0};
    /// \brief Maximum admissible divergence from the destination reading.
    /// \unitspec{T025-U-TIME}
    Tolerance tolerance{0};
    /// \brief Whether this slot is occupied.
    /// \unitspec{T025-U-TIME}
    bool occupied{false};
  };

  /// \brief Finds a declared domain by token; call only while holding the mutex.
  /// \param id Domain token.
  /// \return Pointer to the entry, or `nullptr` when undeclared.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] ClockEntry *find_clock_locked(ClockDomainId id) noexcept;
  /// \brief Finds a declared domain by token; const overload, call only while holding the mutex.
  /// \param id Domain token.
  /// \return Pointer to the entry, or `nullptr` when undeclared.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] const ClockEntry *find_clock_locked(ClockDomainId id) const noexcept;
  /// \brief Finds a directed mapping; call only while holding the mutex.
  /// \param src Source domain token.
  /// \param dst Destination domain token.
  /// \return Pointer to the mapping, or `nullptr` when undeclared.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] const MappingEntry *find_mapping_locked(ClockDomainId src,
                                                        ClockDomainId dst) const noexcept;
  /// \brief Core bounded current-time acquisition; acquires the authority lock itself.
  /// \param id Declared domain token.
  /// \param out Receives the reading only on `Result::Ok`.
  /// \param commit_baseline When `true`, a successful read advances the retained regression
  ///        baseline (public `now` semantics). When `false`, the read is a non-mutating peek
  ///        used by `SessionManager::transition`; the manager advances the baseline only after
  ///        the transition succeeds, through `advance_baseline`.
  /// \param declaration When non-null and the read succeeds, receives the reading domain's
  ///        declaration generation, so a deferred commit can be bound to the exact declaration
  ///        that produced the observation.
  /// \return The same outcomes as `now`.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] Result now_impl(ClockDomainId id, Timestamp &out, bool commit_baseline,
                                std::uint64_t *declaration = nullptr);
  /// \brief Reads and validates one domain's current time; call only while holding the mutex.
  /// \param entry Domain entry.
  /// \param out Receives the reading only on `Result::Ok`.
  /// \param commit_baseline When `true`, a successful read advances the retained regression
  ///        baseline (public `now` and `convert` semantics). When `false`, the read is a
  ///        non-mutating peek used by `SessionManager::transition`, which advances the
  ///        baseline only after the transition succeeds.
  /// \return The read outcome; a rejected read leaves the baseline unchanged.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] Result read_clock_locked(ClockEntry &entry, Timestamp &out,
                                         bool commit_baseline = true);

  /// \brief Core directed-mapping conversion; acquires the authority lock itself.
  /// \param src Declared source domain.
  /// \param dst Declared destination domain.
  /// \param value Source-domain value.
  /// \param out Receives the mapped value only on `Result::Ok`.
  /// \param commit_baseline When `true`, the destination regression baseline advances on a
  ///        successful destination read (public `convert` semantics). When `false`, the read
  ///        is a non-mutating peek used by `SessionManager::transition`.
  /// \param destination_reading When non-null and the destination read succeeds, receives the
  ///        destination-domain host reading used for the tolerance check, so the manager can
  ///        advance that baseline after the transition succeeds.
  /// \param destination_declaration When non-null and the destination read succeeds, receives the
  ///        destination domain's declaration generation, so the deferred destination-baseline
  ///        advance is bound to the exact declaration that produced the reading.
  /// \return The same outcomes as `convert`.
  /// \unitspec{T025-U-TIME}
  [[nodiscard]] Result convert_impl(ClockDomainId src, ClockDomainId dst, Timestamp value,
                                    Timestamp &out, bool commit_baseline,
                                    Timestamp *destination_reading = nullptr,
                                    std::uint64_t *destination_declaration = nullptr);

  /// \brief Advances a domain's retained baseline to `reading` without ever lowering it,
  ///        provided the domain still carries the observation's declaration generation.
  /// \param id Declared domain token.
  /// \param reading Reading to retain; a reading below the current baseline is ignored.
  /// \param declaration Declaration generation captured when `reading` was observed. The advance
  ///        is a no-op unless the addressed entry's current generation matches, so an
  ///        observation is committed only to the same clock declaration that produced it and a
  ///        concurrent re-declaration cannot inherit a stale reading.
  /// \details Acquires the authority lock, so a deferred advance is serialized with concurrent
  ///          public `now`/`convert` calls together with the regression check. A domain that is
  ///          undeclared, or whose declaration generation no longer matches, is ignored. Used by
  ///          `SessionManager::transition` only after a transition succeeds; monotonic
  ///          baselines therefore never move backwards and a later backward reading is
  ///          rejected with `Result::ClockRegression`.
  /// \unitspec{T025-U-TIME}
  void advance_baseline(ClockDomainId id, Timestamp reading, std::uint64_t declaration);

  /// \brief Serializes all authority access.
  /// \unitspec{T025-U-TIME}
  mutable std::mutex mutex_;
  /// \brief Monotonic source of declaration generations; never reused within one authority.
  /// \unitspec{T025-U-TIME}
  std::uint64_t declaration_counter_{0};
  /// \brief Bounded domain table.
  /// \unitspec{T025-U-TIME}
  std::vector<ClockEntry> clocks_;
  /// \brief Bounded mapping table.
  /// \unitspec{T025-U-TIME}
  std::vector<MappingEntry> mappings_;
};

/// \brief Closed outcome of evaluating one `(state, action)` pair.
/// \unitspec{T025-U-TYPES}
enum class TransitionOutcome : std::uint8_t {
  Ok,                ///< Legal forward transition; state and quota change. \unitspec{T025-U-TYPES}
  AlreadyApplied,    ///< Safe idempotent repeat; state unchanged. \unitspec{T025-U-TYPES}
  InvalidTransition, ///< Legal-state conflict with a non-terminal state. \unitspec{T025-U-TYPES}
  TerminalState,     ///< Any transition attempted from a terminal state. \unitspec{T025-U-TYPES}
};

/// \brief Returns the action that produced a lifecycle state, if any.
/// \param state A lifecycle state.
/// \return The action that produced `state`, or `static_cast<Action>(0)` when none does.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr Action producing_action(LifecycleState state) noexcept {
  switch (state) {
  case LifecycleState::armed:
    return Action::Arm;
  case LifecycleState::active:
    return Action::Activate;
  case LifecycleState::closing:
    return Action::Close;
  case LifecycleState::closed:
    return Action::Finalize;
  case LifecycleState::expired:
    return Action::Expire;
  case LifecycleState::revoked:
    return Action::Revoke;
  case LifecycleState::evidence_incomplete:
    return Action::MarkEvidenceIncomplete;
  case LifecycleState::declared:
    return static_cast<Action>(0);
  }
  return static_cast<Action>(0);
}

/// \brief Returns the successor state of a legal forward transition.
/// \param state A non-terminal lifecycle state.
/// \param action A lifecycle action.
/// \return The successor state, or `state` when the pair is not a legal forward transition.
/// \unitspec{T025-U-TYPES}
[[nodiscard]] constexpr LifecycleState successor_state(LifecycleState state,
                                                       Action action) noexcept {
  if (state == LifecycleState::declared && action == Action::Arm) {
    return LifecycleState::armed;
  }
  if (state == LifecycleState::armed && action == Action::Activate) {
    return LifecycleState::active;
  }
  if (state == LifecycleState::active && action == Action::Close) {
    return LifecycleState::closing;
  }
  if (state == LifecycleState::closing && action == Action::Finalize) {
    return LifecycleState::closed;
  }
  if (!is_terminal(state)) {
    if (action == Action::Expire) {
      return LifecycleState::expired;
    }
    if (action == Action::Revoke) {
      return LifecycleState::revoked;
    }
    if (action == Action::MarkEvidenceIncomplete) {
      return LifecycleState::evidence_incomplete;
    }
  }
  return state;
}

/**
 * \brief Exhaustive constexpr evaluation of the lifecycle transition table.
 * \param state Current lifecycle state.
 * \param action Requested lifecycle action.
 * \return `TransitionOutcome::TerminalState` from a terminal state (except a safe repeat
 *         of the producing action, which is `AlreadyApplied`); `AlreadyApplied` for a safe
 *         idempotent repeat; `Ok` for a legal forward transition; otherwise
 *         `InvalidTransition`.
 * \unitspec{T025-U-TYPES}
 */
[[nodiscard]] constexpr TransitionOutcome transition_outcome(LifecycleState state,
                                                             Action action) noexcept {
  if (is_terminal(state)) {
    if (action == producing_action(state)) {
      return TransitionOutcome::AlreadyApplied;
    }
    return TransitionOutcome::TerminalState;
  }
  if (action == producing_action(state)) {
    return TransitionOutcome::AlreadyApplied;
  }
  if (successor_state(state, action) != state) {
    return TransitionOutcome::Ok;
  }
  return TransitionOutcome::InvalidTransition;
}

static_assert(transition_outcome(LifecycleState::declared, Action::Arm) == TransitionOutcome::Ok);
static_assert(transition_outcome(LifecycleState::armed, Action::Arm) ==
              TransitionOutcome::AlreadyApplied);
static_assert(transition_outcome(LifecycleState::declared, Action::Close) ==
              TransitionOutcome::InvalidTransition);
static_assert(transition_outcome(LifecycleState::closed, Action::Arm) ==
              TransitionOutcome::TerminalState);
static_assert(transition_outcome(LifecycleState::evidence_incomplete,
                                 Action::MarkEvidenceIncomplete) ==
              TransitionOutcome::AlreadyApplied);

/**
 * \brief Lifecycle state machine of one validation session.
 *
 * A `ValidationSession` owns its lifecycle state and per-session remaining quota. It is
 * reached by `SessionManager` only while that manager holds its single mutex, which gives
 * a deterministic total order; it is not individually synchronized. It is copyable and
 * movable because it is a plain value once created.
 * \unitspec{T025-U-SESSION}
 */
class ValidationSession {
public:
  /// \brief Constructs a `declared` session with zero quotas and zero identities.
  /// \unitspec{T025-U-SESSION}
  ValidationSession() noexcept = default;

  /// \brief Constructs a session with bound identities and finite quotas.
  /// \param permit_id Bound permit identity.
  /// \param session_id Bound session identity.
  /// \param controller Owning controller identity.
  /// \param generation Owning controller generation.
  /// \param quotas Finite quota list; the first entry of each kind wins.
  /// \param initial_state Starting lifecycle state. `SessionManager` always passes
  ///        `LifecycleState::declared`; other values exist so the transition table can be
  ///        exercised directly without fabricating intermediate successes.
  /// \unitspec{T025-U-SESSION}
  ValidationSession(const PermitId &permit_id, const SessionId &session_id,
                    const ControllerId &controller, Generation generation,
                    const std::vector<Quota> &quotas,
                    LifecycleState initial_state = LifecycleState::declared);

  /// \brief Applies one action and decrements the operations quota on a legal transition.
  /// \param action Requested action; an undefined or non-atomic mask yields
  ///        `Result::UndefinedAction`.
  /// \param now Caller-resolved current time in the permit validity domain. It is retained
  ///        for interface symmetry; validity comparison is performed by the manager.
  /// \return `Result::Ok` on a legal forward transition; `Result::AlreadyApplied` for a
  ///         safe repeat; `Result::InvalidTransition`; `Result::TerminalState`; or
  ///         `Result::QuotaExhausted` when the operations budget is zero. A non-`Ok`
  ///         outcome leaves state and quota unchanged.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] Result apply(Action action, Timestamp now) noexcept;

  /// \brief Returns the current lifecycle state.
  /// \return The current lifecycle state.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] LifecycleState state() const noexcept;

  /// \brief Reports whether the current state is terminal.
  /// \return `true` when the current state is terminal.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] bool is_terminal() const noexcept;

  /// \brief Returns the remaining budget of a quota kind.
  /// \param kind Quota family.
  /// \return The remaining budget, or `0` when the permit bound no quota of that kind.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] std::uint32_t remaining_quota(QuotaKind kind) const noexcept;

  /// \brief Returns an immutable observable snapshot of this session.
  /// \return An immutable observable snapshot of this session.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] SessionSnapshot snapshot() const noexcept;

  /// \brief Returns the bound permit identity.
  /// \return The bound permit identity.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] const PermitId &permit_id() const noexcept;

  /// \brief Returns the bound session identity.
  /// \return The bound session identity.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] const SessionId &session_id() const noexcept;

  /// \brief Returns the owning controller identity.
  /// \return The owning controller identity.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] const ControllerId &controller() const noexcept;

  /// \brief Returns the owning controller generation.
  /// \return The owning controller generation.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] Generation generation() const noexcept;

private:
  /// \brief Number of quota kinds.
  /// \unitspec{T025-U-SESSION}
  static constexpr std::size_t kQuotaKindCount = 2;
  /// \brief Maps a quota kind to its storage index.
  /// \param kind Quota family.
  /// \return The storage index, or `kQuotaKindCount` when unknown.
  /// \unitspec{T025-U-SESSION}
  [[nodiscard]] static std::size_t quota_index(QuotaKind kind) noexcept;

  /// \brief Current lifecycle state.
  /// \unitspec{T025-U-SESSION}
  LifecycleState state_{LifecycleState::declared};
  /// \brief Bound permit identity.
  /// \unitspec{T025-U-SESSION}
  PermitId permit_id_{};
  /// \brief Bound session identity.
  /// \unitspec{T025-U-SESSION}
  SessionId session_id_{};
  /// \brief Owning controller identity.
  /// \unitspec{T025-U-SESSION}
  ControllerId controller_{};
  /// \brief Owning controller generation.
  /// \unitspec{T025-U-SESSION}
  Generation generation_{0};
  /// \brief Remaining budget per quota kind.
  /// \unitspec{T025-U-SESSION}
  std::array<std::uint32_t, kQuotaKindCount> quotas_{0, 0};
};

/**
 * \brief Controller-scoped, exactly-once consumed-identity bookkeeping.
 *
 * `try_consume` performs a single atomic check-then-insert under this registry's own mutex,
 * so N concurrent consumptions of one identity yield exactly one `Result::Ok` and N-1
 * deterministic failures. Check order is session identity first, then permit identity, then
 * capacity, so a changed-nonce replay is reported as `Result::SessionAlreadyConsumed`. No
 * partial insertion occurs on any failure, and the bookkeeping never grows past its
 * configured capacity. The registry is non-copyable and non-movable.
 * \unitspec{T025-U-REGISTRY}
 */
class PermitRegistry {
public:
  /// \brief Constructs a registry with bounded consumed-identity capacities.
  /// \param max_consumed_permits Maximum consumed permit identities.
  /// \param max_consumed_sessions Maximum consumed session identities.
  /// \unitspec{T025-U-REGISTRY}
  PermitRegistry(std::size_t max_consumed_permits, std::size_t max_consumed_sessions);
  /// \brief Destructor.
  /// \unitspec{T025-U-REGISTRY}
  ~PermitRegistry() = default;

  /// \brief Copy construction is deleted; the registry is non-copyable.
  /// \unitspec{T025-U-REGISTRY}
  PermitRegistry(const PermitRegistry &) = delete;
  /// \brief Copy assignment is deleted; the registry is non-copyable.
  /// \unitspec{T025-U-REGISTRY}
  PermitRegistry &operator=(const PermitRegistry &) = delete;
  /// \brief Move construction is deleted; the registry is non-movable.
  /// \unitspec{T025-U-REGISTRY}
  PermitRegistry(PermitRegistry &&) = delete;
  /// \brief Move assignment is deleted; the registry is non-movable.
  /// \unitspec{T025-U-REGISTRY}
  PermitRegistry &operator=(PermitRegistry &&) = delete;

  /// \brief Atomically checks and inserts a consumed `(controller, permit, session)` triple.
  /// \param controller Consumption scope.
  /// \param permit_id Permit identity.
  /// \param session_id Session identity.
  /// \return `Result::Ok` when both identities were inserted; otherwise
  ///         `Result::SessionAlreadyConsumed`, `Result::PermitAlreadyConsumed`, or
  ///         `Result::CapacityExhausted`. Nothing is inserted on failure.
  /// \unitspec{T025-U-REGISTRY}
  [[nodiscard]] Result try_consume(const ControllerId &controller, const PermitId &permit_id,
                                   const SessionId &session_id);

  /// \brief Reports whether a permit identity was consumed in a scope.
  /// \param controller Consumption scope.
  /// \param permit_id Permit identity.
  /// \return `true` when the permit identity was consumed in this scope.
  /// \unitspec{T025-U-REGISTRY}
  [[nodiscard]] bool is_consumed_permit(const ControllerId &controller,
                                        const PermitId &permit_id) const;

  /// \brief Reports whether a session identity was consumed in a scope.
  /// \param controller Consumption scope.
  /// \param session_id Session identity.
  /// \return `true` when the session identity was consumed in this scope.
  /// \unitspec{T025-U-REGISTRY}
  [[nodiscard]] bool is_consumed_session(const ControllerId &controller,
                                         const SessionId &session_id) const;

  /// \brief Returns the configured maximum consumed permit identities.
  /// \return The configured maximum consumed permit identities.
  /// \unitspec{T025-U-REGISTRY}
  [[nodiscard]] std::size_t capacity() const noexcept;

  /// \brief Returns the number of consumed permit identities.
  /// \return The number of consumed permit identities.
  /// \unitspec{T025-U-REGISTRY}
  [[nodiscard]] std::size_t size() const;

  /// \brief Returns the number of consumed session identities.
  /// \return The number of consumed session identities.
  /// \unitspec{T025-U-REGISTRY}
  [[nodiscard]] std::size_t session_size() const;

private:
  /// \brief Consumed permit key: controller scope plus permit identity.
  /// \unitspec{T025-U-REGISTRY}
  struct PermitKey {
    /// \brief Consumption scope.
    /// \unitspec{T025-U-REGISTRY}
    ControllerId controller{};
    /// \brief Consumed permit identity.
    /// \unitspec{T025-U-REGISTRY}
    PermitId permit{};
  };
  /// \brief Consumed session key: controller scope plus session identity.
  /// \unitspec{T025-U-REGISTRY}
  struct SessionKey {
    /// \brief Consumption scope.
    /// \unitspec{T025-U-REGISTRY}
    ControllerId controller{};
    /// \brief Consumed session identity.
    /// \unitspec{T025-U-REGISTRY}
    SessionId session{};
  };

  /// \brief Serializes all registry access.
  /// \unitspec{T025-U-REGISTRY}
  mutable std::mutex mutex_;
  /// \brief Configured maximum consumed permit identities.
  /// \unitspec{T025-U-REGISTRY}
  std::size_t max_permits_{0};
  /// \brief Configured maximum consumed session identities.
  /// \unitspec{T025-U-REGISTRY}
  std::size_t max_sessions_{0};
  /// \brief Consumed permit keys.
  /// \unitspec{T025-U-REGISTRY}
  std::vector<PermitKey> permits_;
  /// \brief Consumed session keys.
  /// \unitspec{T025-U-REGISTRY}
  std::vector<SessionKey> sessions_;
};

/// \brief Bounded, host-configured capacities for a `SessionManager`.
/// \unitspec{T025-U-MANAGER}
struct ManagerConfig {
  /// \brief Host-supplied, non-zero uniqueness scope; a zero scope is rejected at manager
  ///        construction. The host MUST mint a fresh, distinct scope per instance/recreation.
  /// \unitspec{T025-U-MANAGER}
  ManagerScope scope{};
  /// \brief Maximum live (non-terminal) sessions.
  /// \unitspec{T025-U-MANAGER}
  std::size_t max_sessions{8};
  /// \brief Maximum declared clock domains.
  /// \unitspec{T025-U-MANAGER}
  std::size_t max_domains{4};
  /// \brief Maximum declared clock mappings.
  /// \unitspec{T025-U-MANAGER}
  std::size_t max_mappings{8};
  /// \brief Maximum consumed permit identities.
  /// \unitspec{T025-U-MANAGER}
  std::size_t max_consumed_permits{16};
  /// \brief Maximum consumed session identities.
  /// \unitspec{T025-U-MANAGER}
  std::size_t max_consumed_sessions{16};
  /// \brief Maximum retained superseded controller identities.
  /// \unitspec{T025-U-MANAGER}
  std::size_t max_superseded{8};
  /// \brief Maximum registered controller identities.
  /// \unitspec{T025-U-MANAGER}
  std::size_t max_controllers{64};
};

/// \brief Immutable observable snapshot of all bounded manager bookkeeping.
/// \unitspec{T025-U-MANAGER}
struct ManagerSnapshot {
  /// \brief Number of live (non-terminal) sessions.
  /// \unitspec{T025-U-MANAGER}
  std::size_t live_sessions{0};
  /// \brief Number of consumed permit identities.
  /// \unitspec{T025-U-MANAGER}
  std::size_t consumed_permits{0};
  /// \brief Number of consumed session identities.
  /// \unitspec{T025-U-MANAGER}
  std::size_t consumed_sessions{0};
  /// \brief Number of registered controllers (current and superseded).
  /// \unitspec{T025-U-MANAGER}
  std::size_t registered_controllers{0};
  /// \brief Normal-route emission count, always zero.
  /// \unitspec{T025-U-MANAGER}
  std::uint64_t emission_count{0};

  /// \brief Value equality over every observed field.
  /// \unitspec{T025-U-MANAGER}
  friend bool operator==(const ManagerSnapshot &, const ManagerSnapshot &) noexcept = default;
};

/**
 * \brief Owns a host-supplied uniqueness scope, controller identity/generation, exactly-once
 *        consumption, bounded session capacity, and the validation-session lifecycle.
 *
 * All operations take one internal mutex, so concurrent consumption and transitions
 * serialize into a deterministic total order and exactly-once consumption holds under
 * concurrency. The manager is non-copyable and non-movable. It owns its `TimeAuthority`
 * and `PermitRegistry`; destroy the manager before any thread that used it exits. Every
 * public method that returns a value is `[[nodiscard]]`, and every path that fails leaves
 * session state, consumed sets, quota counters, and authority baselines unchanged. A
 * successful lifecycle transition advances the retained baselines of the authority domains it
 * observed, binding each advance to the clock declaration generation that produced the
 * observation, so a later backward monotonic reading is rejected, a concurrent re-declaration
 * cannot inherit the old reading, and a rejected transition advances no baseline. The class
 * exposes no emission, transport, journal, or persistence entry point,
 * and `emission_count()` is always zero.
 * \unitspec{T025-U-MANAGER}
 */
class SessionManager {
public:
  /// \brief Constructs a manager with bounded capacities and a non-zero uniqueness scope.
  /// \param config Bounded capacities and the host-supplied uniqueness scope; the manager
  ///        copies this value.
  /// \throws std::invalid_argument when `config.scope` is zero.
  /// \unitspec{T025-U-MANAGER}
  explicit SessionManager(ManagerConfig config = {});

  /// \brief Destructor.
  /// \unitspec{T025-U-MANAGER}
  ~SessionManager() = default;

  /// \brief Copy construction is deleted; the manager is non-copyable.
  /// \unitspec{T025-U-MANAGER}
  SessionManager(const SessionManager &) = delete;
  /// \brief Copy assignment is deleted; the manager is non-copyable.
  /// \unitspec{T025-U-MANAGER}
  SessionManager &operator=(const SessionManager &) = delete;
  /// \brief Move construction is deleted; the manager is non-movable.
  /// \unitspec{T025-U-MANAGER}
  SessionManager(SessionManager &&) = delete;
  /// \brief Move assignment is deleted; the manager is non-movable.
  /// \unitspec{T025-U-MANAGER}
  SessionManager &operator=(SessionManager &&) = delete;

  /// \brief Returns the owned time authority, for host clock/mapping declarations.
  /// \return The owned time authority.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] TimeAuthority &time_authority() noexcept;

  /// \brief Returns the owned time authority.
  /// \return The owned time authority.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] const TimeAuthority &time_authority() const noexcept;

  /// \brief Registers a host-issued controller identity under a controller name.
  /// \param id Host-issued, non-zero, globally unique controller identity. The manager never
  ///        derives an identity from the name or from a per-manager sequence.
  /// \param name Controller name; re-registering a name supersedes its previous identity.
  /// \return `Result::Ok` (issues generation 1 under this manager's uniqueness scope);
  ///         `Result::InvalidController` when `id` is zero or already registered;
  ///         `Result::CapacityExhausted` when the controller table is full and no superseded
  ///         entry can be evicted.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Result register_controller(const ControllerId &id, std::string_view name);

  /// \brief Advances the generation of a registered, current controller.
  /// \param controller Registered controller identity.
  /// \return The new generation, or `0` when `controller` is unknown or superseded. Handles
  ///         issued under an older generation become `Result::StaleHandle`.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Generation advance_generation(const ControllerId &controller);

  /// \brief Validates the context against the permit and consumes the permit exactly once.
  /// \param controller Issuing, registered, current controller identity.
  /// \param permit Immutable permit to consume.
  /// \param context Asserted runtime envelope, compared field-by-field to `permit`.
  /// \param out Receives a usable handle only on `Result::Ok`.
  /// \return `Result::Ok`; `Result::PermitMismatch` (see `last_diagnostic().locator()`);
  ///         `Result::SessionAlreadyConsumed`; `Result::PermitAlreadyConsumed`;
  ///         `Result::CapacityExhausted`; `Result::ForeignHandle`;
  ///         `Result::RecreatedController`. A failure returns no usable handle and leaves
  ///         capacity and consumed sets unchanged.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Result consume(const ControllerId &controller, const Permit &permit,
                               const SessionContext &context, SessionHandle &out);

  /// \brief Validates and applies one lifecycle action to the addressed session.
  /// \param handle Session handle issued by this manager.
  /// \param action Requested lifecycle action.
  /// \param now_domain Domain of the caller's current-time claim.
  /// \param now_value Caller's current-time claim.
  /// \param out Receives the ordered, payload-free diagnostic of this operation.
  /// \return `Result::Ok`; the handle outcomes `InvalidHandle`, `ForeignHandle`,
  ///         `RecreatedController`, `StaleHandle`, `SessionNotFound`; the time outcomes
  ///         `UnknownClock`, `ClockSourceFailure`, `ClockOutOfBounds`, `ClockRegression`,
  ///         `ClockOverflow`, `MissingMapping`, `ToleranceExceeded`, `PermitNotYetValid`,
  ///         `PermitExpired`; and the action outcomes `UndefinedAction`,
  ///         `ActionNotAllowed`, `TerminalState`, `InvalidTransition`, `QuotaExhausted`,
  ///         `AlreadyApplied`. Handle, context, time, and action validation all precede
  ///         any state mutation, so a failure is non-mutating. On `Result::Ok` the transition
  ///         advances the retained baseline of the resolved time domain (and of the mapped
  ///         validity domain, when a declared mapping was used) to the authority observation
  ///         it relied on, but only while that domain still carries the declaration generation
  ///         that produced the observation, so a concurrent re-declaration cannot inherit the
  ///         old reading; a later backward monotonic reading is then `ClockRegression`. No
  ///         other outcome advances a baseline.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Result transition(const SessionHandle &handle, Action action,
                                  ClockDomainId now_domain, Timestamp now_value, Diagnostic &out);

  /// \brief Reads the lifecycle state of the addressed session without mutating it.
  /// \param handle Session handle issued by this manager.
  /// \param out Receives the lifecycle state only on `Result::Ok`.
  /// \return The same handle outcomes as `transition`, and `Result::Ok` on success.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Result state(const SessionHandle &handle, LifecycleState &out) const;

  /// \brief Reads an immutable snapshot of the addressed session without mutating it.
  /// \param handle Session handle issued by this manager.
  /// \param out Receives the snapshot only on `Result::Ok`.
  /// \return The same handle outcomes as `transition`, and `Result::Ok` on success.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Result session_snapshot(const SessionHandle &handle, SessionSnapshot &out) const;

  /// \brief Returns the diagnostic of the most recent `consume` or `transition` call.
  /// \return The diagnostic of the most recent `consume` or `transition` call.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Diagnostic last_diagnostic() const;

  /// \brief Returns an immutable snapshot of all bounded manager bookkeeping.
  /// \return An immutable snapshot of all bounded manager bookkeeping.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] ManagerSnapshot manager_snapshot() const;

  /// \brief Returns the configured maximum number of live sessions.
  /// \return The configured maximum number of live sessions.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] std::size_t capacity() const noexcept;

  /// \brief Returns the normal-route emission count, always `0`.
  /// \return The normal-route emission count, always `0`.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] std::uint64_t emission_count() const noexcept;

private:
  /// \brief Internal controller entry: identity, name, generation, and superseded flag.
  /// \unitspec{T025-U-MANAGER}
  struct ControllerEntry {
    /// \brief Issued controller identity.
    /// \unitspec{T025-U-MANAGER}
    ControllerId id{};
    /// \brief Registered controller name.
    /// \unitspec{T025-U-MANAGER}
    std::string name;
    /// \brief Current controller generation.
    /// \unitspec{T025-U-MANAGER}
    Generation generation{0};
    /// \brief Whether this identity was superseded by a re-registration.
    /// \unitspec{T025-U-MANAGER}
    bool superseded{false};
  };

  /// \brief Internal live-session slot: occupancy, identities, permit, and validation state.
  /// \unitspec{T025-U-MANAGER}
  struct SessionEntry {
    /// \brief Whether this slot is occupied.
    /// \unitspec{T025-U-MANAGER}
    bool occupied{false};
    /// \brief Whether the session reached a terminal state.
    /// \unitspec{T025-U-MANAGER}
    bool terminal{false};
    /// \brief Owning controller identity.
    /// \unitspec{T025-U-MANAGER}
    ControllerId controller{};
    /// \brief Owning controller generation.
    /// \unitspec{T025-U-MANAGER}
    Generation generation{0};
    /// \brief Bound session identity.
    /// \unitspec{T025-U-MANAGER}
    SessionId session{};
    /// \brief Bound immutable permit, if occupied.
    /// \unitspec{T025-U-MANAGER}
    std::optional<Permit> permit{};
    /// \brief Per-session lifecycle and quota state.
    /// \unitspec{T025-U-MANAGER}
    ValidationSession validation{};
  };

  /// \brief Sentinel for "no slot index".
  /// \unitspec{T025-U-MANAGER}
  static constexpr std::size_t kNoIndex = static_cast<std::size_t>(-1);

  /// \brief Finds a controller entry by identity; call only while holding the mutex.
  /// \param id Controller identity.
  /// \return Pointer to the entry, or `nullptr` when unknown.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] ControllerEntry *find_controller_locked(const ControllerId &id) noexcept;
  /// \brief Finds a controller entry by identity; const overload, call only while holding the mutex.
  /// \param id Controller identity.
  /// \return Pointer to the entry, or `nullptr` when unknown.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] const ControllerEntry *
  find_controller_locked(const ControllerId &id) const noexcept;
  /// \brief Reports whether any live session carries a session identity.
  /// \param id Session identity.
  /// \return `true` when any live session carries the identity.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] bool any_session_with_id_locked(const SessionId &id) const noexcept;
  /// \brief Resolves a handle to a live slot index; call only while holding the mutex.
  /// \param handle Session handle.
  /// \param index Receives the slot index only on `Result::Ok`.
  /// \return The handle outcome.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] Result locate_locked(const SessionHandle &handle,
                                     std::size_t &index) const noexcept;
  /// \brief Allocates an empty or reclaimable terminal slot; call only while holding the mutex.
  /// \return Pointer to the slot, or `nullptr` when none is available.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] SessionEntry *allocate_slot_locked() noexcept;
  /// \brief Counts live (non-terminal) sessions; call only while holding the mutex.
  /// \return The number of live sessions.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] std::size_t live_session_count_locked() const noexcept;
  /// \brief Evicts the oldest superseded controller entry; call only while holding the mutex.
  /// \return `true` when an entry was evicted.
  /// \unitspec{T025-U-MANAGER}
  [[nodiscard]] bool evict_one_superseded_locked();

  /// \brief Serializes all manager access.
  /// \unitspec{T025-U-MANAGER}
  mutable std::mutex mutex_;
  /// \brief Bounded capacities.
  /// \unitspec{T025-U-MANAGER}
  ManagerConfig config_;
  /// \brief Owned time authority.
  /// \unitspec{T025-U-MANAGER}
  TimeAuthority authority_;
  /// \brief Owned exactly-once consumption registry.
  /// \unitspec{T025-U-MANAGER}
  PermitRegistry registry_;
  /// \brief Bounded controller table.
  /// \unitspec{T025-U-MANAGER}
  std::vector<ControllerEntry> controllers_;
  /// \brief Superseded controller identities in eviction order.
  /// \unitspec{T025-U-MANAGER}
  std::vector<ControllerId> superseded_order_;
  /// \brief Bounded live-session table.
  /// \unitspec{T025-U-MANAGER}
  std::vector<SessionEntry> sessions_;
  /// \brief Diagnostic of the most recent `consume` or `transition` call.
  /// \unitspec{T025-U-MANAGER}
  Diagnostic last_diagnostic_{};
  /// \brief Test-only interleaving probe, invoked after a successful transition's time
  ///        observation and before its deferred baseline commit.
  /// \details Empty in every production configuration, so `transition` behaves identically and
  ///          no external code runs. The focused R6 tests set it through `SessionManagerProbe` to
  ///          place a clock re-declaration deterministically between observation and commit,
  ///          instead of relying on thread scheduling. It is invoked only on the success path,
  ///          after `apply` returns `Result::Ok` and before any baseline is advanced, so it
  ///          cannot affect a rejected transition.
  /// \unitspec{T025-U-MANAGER}
  std::function<void()> before_commit_probe_{};
  /// \brief Test-only probe granting deterministic control of `before_commit_probe_`.
  /// \unitspec{T025-U-MANAGER}
  friend struct SessionManagerProbe;
};

static_assert(!std::is_copy_constructible_v<TimeAuthority>, "TimeAuthority must not be copyable");
static_assert(!std::is_move_constructible_v<TimeAuthority>, "TimeAuthority must not be movable");
static_assert(!std::is_copy_constructible_v<PermitRegistry>, "PermitRegistry must not be copyable");
static_assert(!std::is_move_constructible_v<PermitRegistry>, "PermitRegistry must not be movable");
static_assert(!std::is_copy_constructible_v<SessionManager>, "SessionManager must not be copyable");
static_assert(!std::is_move_constructible_v<SessionManager>, "SessionManager must not be movable");
static_assert(std::is_copy_constructible_v<Permit>, "Permit is an immutable value");
static_assert(std::is_copy_constructible_v<Diagnostic>, "Diagnostic is an immutable value");

} // namespace validation
} // namespace xcom
} // namespace xverse

#endif // XVERSE_XCOM_VALIDATION_SESSION_HPP_
