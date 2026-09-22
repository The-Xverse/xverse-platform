/**
 * @file result.hpp
 * @brief Exclusive immutable success-or-diagnostics result for validated construction.
 * @ownership A result owns either its value or its non-empty diagnostic set.
 * @lifetime Accessor pointers remain valid until the owning result is destroyed.
 * @thread_safety Concurrent const reads are safe when the contained value supports them.
 * @failure Factories are noexcept when the bounded value type has noexcept copy construction.
 */

#ifndef XVERSE_XCOM_RESULT_HPP
#define XVERSE_XCOM_RESULT_HPP

#include "xverse/xcom/diagnostic.hpp"

#include <type_traits>
#include <variant>

namespace xverse::xcom {

/**
 * @brief Holds exactly one validated value or one non-empty immutable diagnostic sequence.
 * @tparam T Value-owned successful result type with noexcept copy construction.
 * @ownership Owns its active fixed-capacity alternative.
 * @lifetime Returned pointers remain valid until destruction. Copy construction,
 * including construction from an rvalue, leaves the source result unchanged.
 * @thread_safety Concurrent const reads are safe if T supports concurrent const reads.
 * @failure Public factories cannot allocate or throw; invalid states have no public constructor.
 */
template <typename T>
class Result final {
 public:
  static_assert(std::is_nothrow_copy_constructible_v<T>,
                "Result values must support exception-free copy construction");

  /**
   * @brief Own a successful validated value.
   * @param value Valid source value, copied without modification.
   * @return An exclusive success result.
   */
  [[nodiscard]] static Result success(const T& value) noexcept { return Result(value); }

  /**
   * @brief Own a failed non-empty diagnostic set.
   * @param diagnostics Valid source diagnostic set, copied without modification.
   * @return An exclusive failure result.
   */
  [[nodiscard]] static Result failure(const DiagnosticSet& diagnostics) noexcept {
    return Result(diagnostics);
  }

  /**
   * @brief Copy a result without changing the source or active alternative.
   * @param other Valid source result.
   * @failure This operation cannot fail.
   */
  Result(const Result& other) noexcept = default;

  /** Assignment is disabled so accessor pointers cannot be invalidated by replacement. */
  Result& operator=(const Result&) = delete;

  /** @return true only when the value alternative is active. */
  [[nodiscard]] bool has_value() const noexcept { return std::holds_alternative<T>(state_); }
  /** @return The value pointer, or nullptr for failure. */
  [[nodiscard]] const T* value() const noexcept { return std::get_if<T>(&state_); }
  /** @return The diagnostic-set pointer, or nullptr for success. */
  [[nodiscard]] const DiagnosticSet* diagnostics() const noexcept {
    return std::get_if<DiagnosticSet>(&state_);
  }

 private:
  /**
   * @brief Copy a valid success alternative.
   * @param value Valid source value.
   * @failure This operation cannot fail.
   */
  explicit Result(const T& value) noexcept : state_(value) {}

  /**
   * @brief Copy a valid failure alternative.
   * @param diagnostics Non-empty source diagnostics.
   * @failure This operation cannot fail.
   */
  explicit Result(const DiagnosticSet& diagnostics) noexcept : state_(diagnostics) {}

  /** Exclusive owned result state. */
  std::variant<T, DiagnosticSet> state_;
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_RESULT_HPP
