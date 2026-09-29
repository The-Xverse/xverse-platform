/**
 * @file suite_support.hpp
 * @brief T033 reusable contract-suite reporting vocabulary shared by the provider, observer,
 *        stimulation-tool, and gateway conformance suites.
 * @ownership A report owns copied check records and strings only.
 * @lifetime Value lifetime; no suite or subject storage is referenced.
 * @thread_safety One report is single-writer; distinct reports are independent.
 * @failure A missing or failing check is reported as a failure and never silently skipped.
 * @par Traceability
 * Supports T033-SR-014 and the reusable provider/observer/stimulation-tool/gateway conformance
 * suites of the accepted T-CORE (`XCOM-DU-021`) slice.
 */

#ifndef XVERSE_XCOM_CONTRACT_SUITES_SUITE_SUPPORT_HPP_
#define XVERSE_XCOM_CONTRACT_SUITES_SUITE_SUPPORT_HPP_

#include <cstddef>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace xverse::xcom::contract_suites {

/// @brief One named, bounded conformance check outcome.
struct SuiteCheck final {
  /// @brief Stable check identity (for example `P-01`).
  std::string id;
  /// @brief Whether the check passed.
  bool passed{false};
  /// @brief Bounded non-sensitive failure detail.
  std::string detail;
};

/**
 * @brief Bounded, owned report of one reusable contract-suite run.
 * @ownership Owns copied check records; never borrows subject storage.
 * @lifetime Value lifetime.
 * @thread_safety One writer; `const` reads are safe.
 * @failure `ok()` is false when any recorded check failed; a missing check is never a pass.
 */
class SuiteReport final {
 public:
  /// @brief Record one bounded check result.
  /// @param id Stable check identity.
  /// @param passed Whether the check passed.
  /// @param detail Bounded non-sensitive detail.
  void add(std::string id, const bool passed, std::string detail = {}) {
    checks_.push_back(SuiteCheck{std::move(id), passed, std::move(detail)});
  }

  /// @return true only when at least one check was recorded and every check passed.
  [[nodiscard]] bool ok() const noexcept {
    if (checks_.empty()) {
      return false;
    }
    for (const SuiteCheck& check : checks_) {
      if (!check.passed) {
        return false;
      }
    }
    return true;
  }

  /// @brief Report the recorded outcome of one named check.
  /// @param id Check identity.
  /// @return true only when a check with `id` was recorded and passed.
  [[nodiscard]] bool passed(const std::string_view id) const noexcept {
    for (const SuiteCheck& check : checks_) {
      if (check.id == id) {
        return check.passed;
      }
    }
    return false;
  }

  /// @return Number of recorded checks that failed.
  [[nodiscard]] std::size_t failures() const noexcept {
    std::size_t count = 0U;
    for (const SuiteCheck& check : checks_) {
      if (!check.passed) {
        ++count;
      }
    }
    return count;
  }

  /// @return Every recorded check.
  [[nodiscard]] const std::vector<SuiteCheck>& checks() const noexcept { return checks_; }

  /// @brief Build a bounded, non-sensitive summary of every failed check.
  /// @return Semicolon-separated failing check identities and details.
  [[nodiscard]] std::string failure_detail() const {
    std::string text;
    for (const SuiteCheck& check : checks_) {
      if (check.passed) {
        continue;
      }
      if (!text.empty()) {
        text += "; ";
      }
      text += check.id;
      if (!check.detail.empty()) {
        text += " (";
        text += check.detail;
        text += ")";
      }
    }
    return text;
  }

 private:
  std::vector<SuiteCheck> checks_{};
};

}  // namespace xverse::xcom::contract_suites

#endif  // XVERSE_XCOM_CONTRACT_SUITES_SUITE_SUPPORT_HPP_
