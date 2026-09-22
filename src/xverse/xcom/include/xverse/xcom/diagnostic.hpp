/**
 * @file diagnostic.hpp
 * @brief Stable fixed-capacity diagnostics for core value validation.
 * @ownership Diagnostics and sets own every reported byte.
 * @lifetime Returned views remain valid until their diagnostic owner is destroyed.
 * @thread_safety Values are immutable after construction and support concurrent const reads.
 * @failure Validated construction rejects invalid input without allocation or exceptions.
 */

#ifndef XVERSE_XCOM_DIAGNOSTIC_HPP
#define XVERSE_XCOM_DIAGNOSTIC_HPP

#include "xverse/xcom/value.hpp"

#include <array>
#include <optional>
#include <span>
#include <string>
#include <string_view>

namespace xverse::xcom {

/** Stable validation diagnostic codes. */
enum class DiagnosticCode {
  required_field,
  bound_exceeded,
  invalid_version,
  incompatible_direction,
  contract_mismatch,
};

/** Diagnostic severity ordered from informational to error. */
enum class DiagnosticSeverity { information, warning, error };

/** Validation phase that produced a diagnostic. */
enum class ValidationPhase { contract, item };

/**
 * @brief Return the stable external code string.
 * @param code Diagnostic code enumeration.
 * @return Static-lifetime code text.
 */
[[nodiscard]] std::string_view to_string(DiagnosticCode code) noexcept;
/**
 * @brief Return the stable external severity string.
 * @param severity Diagnostic severity enumeration.
 * @return Static-lifetime severity text.
 */
[[nodiscard]] std::string_view to_string(DiagnosticSeverity severity) noexcept;
/**
 * @brief Return the stable external validation-phase string.
 * @param phase Validation phase enumeration.
 * @return Static-lifetime phase text.
 */
[[nodiscard]] std::string_view to_string(ValidationPhase phase) noexcept;

/**
 * @brief Call-scoped input for validated diagnostic construction.
 * @ownership The factory copies all string views; this aggregate owns nothing.
 * @lifetime Input views need only remain valid for the factory call.
 * @thread_safety Distinct inputs may be used concurrently.
 * @failure Empty, unknown, control-containing, or over-bound fields are rejected.
 */
struct DiagnosticInput final {
  /** Stable diagnostic code. */
  DiagnosticCode code;
  /** Diagnostic severity. */
  DiagnosticSeverity severity;
  /** Validation phase. */
  ValidationPhase phase;
  /** Affected logical identity or field name. */
  std::string_view affected_identity;
  /** Human-readable deterministic reason. */
  std::string_view reason;
  /** Human-readable deterministic correction. */
  std::string_view correction;
};

/**
 * @brief A complete immutable diagnostic with a stable deterministic sort key.
 * @ownership Owns affected identity, reason, correction, and ordering key in fixed storage.
 * @lifetime Accessor views remain valid until destruction; rvalue construction copies.
 * @thread_safety Concurrent const access is safe.
 * @failure create() rejects invalid text or enumerations and is noexcept.
 */
class Diagnostic final {
 public:
  /** Maximum reason or correction byte count. */
  static constexpr std::size_t kMaximumTextBytes = 256U;
  /** Maximum escaped ordering-key byte count. */
  static constexpr std::size_t kMaximumOrderingKeyBytes = 1'320U;

  /**
   * @brief Validate and copy a diagnostic.
   * @param input Complete diagnostic fields.
   * @return A diagnostic or an empty optional when any field is invalid.
   */
  [[nodiscard]] static std::optional<Diagnostic> create(const DiagnosticInput& input) noexcept;

  /**
   * @brief Copy a validated diagnostic without changing the source.
   * @param other Valid source diagnostic.
   * @failure This operation cannot fail.
   */
  Diagnostic(const Diagnostic& other) noexcept = default;

  /** Assignment is disabled so previously returned views cannot be invalidated. */
  Diagnostic& operator=(const Diagnostic&) = delete;

  /** @return The stable diagnostic-code enumeration. */
  [[nodiscard]] DiagnosticCode code() const noexcept { return code_; }
  /** @return The declared severity. */
  [[nodiscard]] DiagnosticSeverity severity() const noexcept { return severity_; }
  /** @return The validation phase that produced the diagnostic. */
  [[nodiscard]] ValidationPhase phase() const noexcept { return phase_; }
  /** @return The bounded affected logical identity or field name. */
  [[nodiscard]] std::string_view affected_identity() const noexcept {
    return affected_identity_.view();
  }
  /** @return The bounded failure reason. */
  [[nodiscard]] std::string_view reason() const noexcept { return reason_.view(); }
  /** @return The bounded corrective action. */
  [[nodiscard]] std::string_view correction() const noexcept { return correction_.view(); }
  /** @return A stable lexical key covering every ordering field. */
  [[nodiscard]] std::string_view ordering_key() const noexcept { return ordering_key_.view(); }

  /**
   * @brief Copy the stable escaped line into a dynamic consumer string.
   * @return A byte-exact copy of ordering_key().
   * @throws std::bad_alloc if the consumer-requested dynamic copy cannot allocate.
   */
  [[nodiscard]] std::string serialize() const;

  /**
   * @brief Compare complete diagnostic values.
   * @param left First diagnostic.
   * @param right Second diagnostic.
   * @return true when every diagnostic field is equal.
   */
  friend bool operator==(const Diagnostic& left, const Diagnostic& right) = default;

 private:
  friend class DiagnosticSet;

  /**
   * @brief Construct a validated diagnostic from its input.
   * @param input Input already validated by create().
   * @failure This operation cannot fail.
   */
  explicit Diagnostic(const DiagnosticInput& input) noexcept;

  /**
   * @brief Construct a valid internal placeholder hidden beyond DiagnosticSet::size().
   * @failure This operation cannot fail.
   */
  Diagnostic() noexcept;

  /**
   * @brief Replace an internal, unexposed set slot during factory construction.
   * @param other Valid diagnostic to copy.
   * @failure This operation cannot fail.
   */
  void replace_with(const Diagnostic& other) noexcept;

  /** Stable diagnostic code. */
  DiagnosticCode code_{DiagnosticCode::required_field};
  /** Stable severity. */
  DiagnosticSeverity severity_{DiagnosticSeverity::error};
  /** Stable validation phase. */
  ValidationPhase phase_{ValidationPhase::contract};
  /** Owned affected identity. */
  detail::FixedText<kMaximumIdentityBytes> affected_identity_;
  /** Owned reason. */
  detail::FixedText<kMaximumTextBytes> reason_;
  /** Owned correction. */
  detail::FixedText<kMaximumTextBytes> correction_;
  /** Owned escaped deterministic ordering key. */
  detail::FixedText<kMaximumOrderingKeyBytes> ordering_key_;
};

/**
 * @brief A non-empty, deterministically sorted immutable diagnostic sequence.
 * @ownership Owns all diagnostics in fixed-capacity storage.
 * @lifetime The diagnostics span remains valid until destruction; rvalue construction copies.
 * @thread_safety Concurrent const access is safe.
 * @failure Factories reject empty, over-capacity, or invalid sequences without exceptions.
 */
class DiagnosticSet final {
 public:
  /** Maximum diagnostics retained for one bounded validation operation. */
  static constexpr std::size_t kMaximumDiagnostics = 32U;

  /**
   * @brief Sort and own a non-empty diagnostic sequence.
   * @param diagnostics Valid diagnostics in any input order.
   * @return A sorted set, or an empty optional for empty or over-capacity input.
   */
  [[nodiscard]] static std::optional<DiagnosticSet> create(
      std::span<const Diagnostic> diagnostics) noexcept;

  /**
   * @brief Validate, sort, and own a non-empty diagnostic-input sequence.
   * @param inputs Diagnostic inputs whose views remain valid for this call.
   * @return A sorted set, or an empty optional for invalid sequence input.
   */
  [[nodiscard]] static std::optional<DiagnosticSet> create_from_inputs(
      std::span<const DiagnosticInput> inputs) noexcept;

  /**
   * @brief Copy a diagnostic set without changing the source.
   * @param other Non-empty valid source set.
   * @failure This operation cannot fail.
   */
  DiagnosticSet(const DiagnosticSet& other) noexcept = default;

  /** Assignment is disabled so previously returned spans cannot be invalidated. */
  DiagnosticSet& operator=(const DiagnosticSet&) = delete;

  /** @return Deterministically ordered immutable diagnostics. */
  [[nodiscard]] std::span<const Diagnostic> values() const noexcept {
    return {diagnostics_.data(), size_};
  }
  /** @return The nonzero number of diagnostics. */
  [[nodiscard]] std::size_t size() const noexcept { return size_; }

  /**
   * @brief Join stable diagnostic lines with newline separators.
   * @return A byte-stable dynamic copy for reporting and test comparison.
   * @throws std::bad_alloc if the consumer-requested dynamic copy cannot allocate.
   */
  [[nodiscard]] std::string serialize() const;

  /**
   * @brief Compare exposed ordered diagnostic values.
   * @param left First diagnostic set.
   * @param right Second diagnostic set.
   * @return true when size, order, and fields are equal.
   */
  friend bool operator==(const DiagnosticSet& left, const DiagnosticSet& right) noexcept;

 private:
  /** @brief Construct empty internal storage used only by validated factories. */
  DiagnosticSet() noexcept = default;

  /** Sort the initialized prefix without exposing or assigning public values. */
  void sort_initialized() noexcept;

  /** Fixed-capacity owned diagnostic slots. */
  std::array<Diagnostic, kMaximumDiagnostics> diagnostics_{};
  /** Number of initialized and exposed slots. */
  std::size_t size_{0U};
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_DIAGNOSTIC_HPP
