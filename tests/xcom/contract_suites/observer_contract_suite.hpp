/**
 * @file observer_contract_suite.hpp
 * @brief T033 reusable observer contract suite: one implementation-agnostic driver that any
 *        conforming observation boundary can be validated against, plus the subject seam used to
 *        plug an observation hub in.
 * @ownership A subject owns its hub; the suite owns only its bounded report.
 * @lifetime The subject, hub, and composed route must outlive the suite call.
 * @thread_safety Single-threaded; the accepted provider/composition/hub serialize their own state.
 * @bounds One tap with capacity one, one route with queue capacity three, <= 3 submissions.
 * @failure A missing or failing conformance check is reported, never skipped.
 * @par Traceability
 * Supports T033-SR-004 through T033-SR-006 and the accepted `XCOM-SW-OBS-001`/`XCOM-SW-OBS-004`
 * observation boundary.
 */

#ifndef XVERSE_XCOM_CONTRACT_SUITES_OBSERVER_CONTRACT_SUITE_HPP_
#define XVERSE_XCOM_CONTRACT_SUITES_OBSERVER_CONTRACT_SUITE_HPP_

#include "observation/integration/test_support.hpp"
#include "suite_support.hpp"
#include "xverse/xcom/observation.hpp"

#include <string_view>

namespace xverse::xcom::contract_suites {

/**
 * @brief Reusable subject seam: supplies the concrete observation boundary under test.
 * @ownership The subject owns the hub; the suite retains no reference after the call.
 * @lifetime The subject must outlive the suite call.
 * @thread_safety One caller.
 * @failure An incompatible hub is reported as a failing check, never substituted.
 */
class ObserverSubject {
 public:
  virtual ~ObserverSubject() = default;
  /// @return The observation hub under test.
  [[nodiscard]] virtual ObservationHub& hub() noexcept = 0;
};

/**
 * @brief Reusable, implementation-agnostic observation conformance suite.
 * @details The suite names only the accepted observation boundary and the accepted
 *          provider/observation integration fixture. It validates metadata-only attachment,
 *          normalized metadata-only records with identity preservation, the bounded drop-newest
 *          counter, exact-handle detach, detached/foreign-handle rejection, and normal-route
 *          isolation after detach. A different conforming observer is validated by supplying a
 *          different `ObserverSubject`.
 */
class ObserverContractSuite final {
 public:
  /// @brief Run every observation conformance check against one subject.
  /// @param subject Observer subject under test.
  /// @param suffix Stable, unique fixture identity suffix.
  /// @return The bounded suite report.
  [[nodiscard]] static SuiteReport run(ObserverSubject& subject, const std::string_view suffix) {
    SuiteReport report;
    ObservationHub& hub = subject.hub();

    ObservationFilterInput filter{};
    filter.interaction_kind = InteractionKind::message_event;
    const auto spec = ObservationTapSpec::create(
        {kObservationContractVersion, "tap.t033", filter, ObservationPayloadMode::metadata_only, 0U,
         1U, ObservationOverflowPolicy::drop_newest});
    report.add("O-01", spec.has_value(), "validated metadata-only tap policy");
    if (!spec.has_value()) {
      return report;
    }

    const ObservationAttachResult attached = hub.attach(*spec);
    report.add("O-02", attached.status.succeeded() && attached.handle.has_value(),
               "attach one free tap");
    if (!attached.handle.has_value()) {
      return report;
    }

    observation_test::Scenario scenario(suffix, InteractionKind::message_event, 3U, &hub);
    report.add("O-03", scenario.ready(), "composed route with an enabled hub");
    if (!scenario.ready()) {
      return report;
    }
    const auto first = scenario.item(1U);
    const auto second = scenario.item(2U);
    if (!first.has_value() || !second.has_value()) {
      report.add("O-04", false, "fixture could not build a bounded item");
      return report;
    }

    report.add("O-04",
               scenario.composition()
                       .submit(scenario.provider_handle(), *first.value(), scenario.lifecycle())
                       .outcome() == ProviderOutcome::accepted,
               "publish the first item");
    report.add("O-05",
               scenario.composition()
                       .submit(scenario.provider_handle(), *second.value(), scenario.lifecycle())
                       .outcome() == ProviderOutcome::accepted,
               "publish a second item before the queue is drained");

    const auto snapshot = hub.snapshot(*attached.handle);
    report.add("O-06", snapshot.has_value() && snapshot->queued == 1U && snapshot->dropped >= 1U,
               "bounded drop-newest counter increments on overflow");

    const ObservationPollResult polled = hub.poll(*attached.handle);
    report.add("O-07",
               polled.status.succeeded() && polled.record.has_value() &&
                   polled.record->payload_bytes().empty() &&
                   polled.record->payload_view_state() == PayloadViewState::omitted &&
                   polled.record->route_id() == first.value()->route_id() &&
                   polled.record->correlation_id() == first.value()->correlation_id() &&
                   polled.record->source_payload_size() == first.value()->payload().size(),
               "metadata-only normalized record with identity preservation");
    report.add("O-08",
               hub.poll(*attached.handle).status.outcome == ObservationOutcome::no_record,
               "bounded queue is drained exactly once");

    report.add("O-09", hub.detach(*attached.handle).succeeded(), "safe exact-handle detach");
    report.add("O-10",
               hub.poll(*attached.handle).status.outcome == ObservationOutcome::invalid_tap_handle &&
                   !hub.snapshot(*attached.handle).has_value(),
               "detached handle rejected");
    report.add("O-11",
               scenario.composition()
                       .submit(scenario.provider_handle(), *first.value(), scenario.lifecycle())
                       .outcome() == ProviderOutcome::accepted,
               "normal route unaffected after observer detach");
    return report;
  }
};

}  // namespace xverse::xcom::contract_suites

#endif  // XVERSE_XCOM_CONTRACT_SUITES_OBSERVER_CONTRACT_SUITE_HPP_
