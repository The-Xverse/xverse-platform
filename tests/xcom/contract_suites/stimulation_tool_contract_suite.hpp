/**
 * @file stimulation_tool_contract_suite.hpp
 * @brief T033 reusable stimulation-tool contract suite: one implementation-agnostic driver that any
 *        conforming guarded stimulation action path can be validated against, plus the subject seam
 *        used to plug the accepted journal/guard/action-path/lease composition in.
 * @ownership A subject owns its permit, journal, guard, action path, lease registry, and emitter;
 *            the suite owns only its bounded report.
 * @lifetime The subject and every composed component must outlive the suite call.
 * @thread_safety Single-threaded; the accepted action path/guard/journal/registry serialize state.
 * @bounds One open path, four allowed actions, <= 6 evaluations, no retained payload byte.
 * @failure A missing or failing conformance check is reported, never skipped; a decline must emit
 *         nothing and must never be reported as success.
 * @par Traceability
 * Supports T033-SR-007 and T033-SR-008 and the accepted `XCOM-SW-STIM-001`/`XCOM-SW-STIM-004`/
 * `XCOM-SW-STIM-007`/`XCOM-SW-STIM-008` stimulation boundary.
 */

#ifndef XVERSE_XCOM_CONTRACT_SUITES_STIMULATION_TOOL_CONTRACT_SUITE_HPP_
#define XVERSE_XCOM_CONTRACT_SUITES_STIMULATION_TOOL_CONTRACT_SUITE_HPP_

#include "stimulation_matrix/test_support.hpp"
#include "suite_support.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>

namespace xverse::xcom::contract_suites {

/// @brief Accepted validation namespace used by the stimulation boundary.
namespace stimulation_validation = xverse::xcom::validation;
/// @brief Accepted T029 stimulation-matrix helper namespace.
namespace stimulation_fixture = xverse::xcom::stimulation_matrix_test;

/**
 * @brief Reusable subject seam: supplies the concrete stimulation action path under test.
 * @ownership The subject owns the composed accepted components.
 * @lifetime The subject must outlive the suite call.
 * @thread_safety One caller.
 * @failure An incompatible path is reported as a failing check, never substituted.
 */
class StimulationToolSubject {
 public:
  virtual ~StimulationToolSubject() = default;
  /// @return The guarded action path under test.
  [[nodiscard]] virtual stimulation_validation::StimulationActionPath& path() noexcept = 0;
  /// @return The exact permit the path was opened with.
  [[nodiscard]] virtual const stimulation_validation::Permit& permit() const noexcept = 0;
  /// @return Number of host emission calls observed.
  [[nodiscard]] virtual std::size_t emission_calls() noexcept = 0;
  /// @return true only when the most recent emitted descriptor was synthetic.
  [[nodiscard]] virtual bool last_emission_synthetic() = 0;
  /// @return Request identity of the most recent emitted descriptor.
  [[nodiscard]] virtual std::uint64_t last_emission_request_id() = 0;
  /// @return true only when a durable intent existed before the most recent emission.
  [[nodiscard]] virtual bool intent_durable_before_emission() = 0;
};

/**
 * @brief Reusable, implementation-agnostic stimulation-tool conformance suite.
 * @details The suite names only the accepted guarded action path and the accepted T029 stimulation
 *          fixture helpers. It validates that the path opens over the exact permit/policy, that all
 *          four allowed actions emit exactly once with persistent synthetic provenance and
 *          journal-before-emission ordering, and that an out-of-window request and a non-active
 *          session are rejected with zero emission. A different conforming stimulation composition
 *          is validated by supplying a different `StimulationToolSubject`.
 */
class StimulationToolContractSuite final {
 public:
  /// @brief Run every stimulation-tool conformance check against one subject.
  /// @param subject Stimulation-tool subject under test.
  /// @return The bounded suite report.
  [[nodiscard]] static SuiteReport run(StimulationToolSubject& subject) {
    SuiteReport report;
    stimulation_validation::StimulationActionPath& path = subject.path();
    const stimulation_validation::Permit& permit = subject.permit();
    report.add("S-01", path.is_open(), "guard/action path opened over the exact permit and policy");
    if (!path.is_open()) {
      return report;
    }

    const std::array<stimulation_validation::StimulationAction, 4U> actions{
        stimulation_validation::StimulationAction::InjectSignal,
        stimulation_validation::StimulationAction::InjectMessage,
        stimulation_validation::StimulationAction::InvokeService,
        stimulation_validation::StimulationAction::EmulateService};
    std::uint64_t request_id = 1U;
    for (std::size_t index = 0U; index < actions.size(); ++index) {
      const std::size_t before = subject.emission_calls();
      stimulation_validation::ActionDiagnostic diagnostic;
      const stimulation_validation::ActionStatus status = path.execute(
          stimulation_fixture::make_request(permit, request_id, actions[index]),
          stimulation_validation::LifecycleState::active, stimulation_fixture::in_window(), {},
          diagnostic);
      const bool conforms = status == stimulation_validation::ActionStatus::Emitted &&
                            subject.emission_calls() == before + 1U &&
                            subject.last_emission_synthetic() &&
                            subject.last_emission_request_id() == request_id;
      report.add("S-02-" + std::to_string(index), conforms,
                 std::string(stimulation_validation::action_status_name(status)));
      ++request_id;
    }

    const std::size_t before_decline = subject.emission_calls();
    stimulation_validation::ActionDiagnostic decline_diagnostic;
    const stimulation_validation::ActionStatus out_of_window = path.execute(
        stimulation_fixture::make_request(permit, request_id),
        stimulation_validation::LifecycleState::active, stimulation_fixture::out_of_window(), {},
        decline_diagnostic);
    report.add("S-03",
               out_of_window != stimulation_validation::ActionStatus::Emitted &&
                   subject.emission_calls() == before_decline,
               "out-of-window request rejected with zero emission");
    ++request_id;

    const stimulation_validation::ActionStatus inactive = path.execute(
        stimulation_fixture::make_request(permit, request_id),
        stimulation_validation::LifecycleState::closed, stimulation_fixture::in_window(), {},
        decline_diagnostic);
    report.add("S-04",
               inactive != stimulation_validation::ActionStatus::Emitted &&
                   subject.emission_calls() == before_decline,
               "non-active session rejected with zero emission");
    report.add("S-05", subject.intent_durable_before_emission(),
               "persistent synthetic provenance with journal-before-emission ordering");
    return report;
  }
};

}  // namespace xverse::xcom::contract_suites

#endif  // XVERSE_XCOM_CONTRACT_SUITES_STIMULATION_TOOL_CONTRACT_SUITE_HPP_
