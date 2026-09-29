/**
 * @file provider_contract_suite.hpp
 * @brief T033 reusable provider contract suite: one implementation-agnostic driver that any
 *        conforming `CommunicationProvider` can be validated against, plus the subject seam used to
 *        plug a provider in.
 * @ownership A subject owns its provider instance; the suite owns only its bounded report.
 * @lifetime The subject and its provider must outlive the suite call.
 * @thread_safety Single-threaded; the accepted composition/provider serialize their own state.
 * @bounds One provider, one route, one queue capacity of one item, <= 8 operations.
 * @failure A missing or failing conformance check is reported, never skipped; no legacy, network,
 *         or production resource is touched.
 * @par Traceability
 * Supports T033-SR-001 through T033-SR-003 and the accepted `XCOM-DU-007`/`XCOM-DU-021` provider
 * boundary over the accepted T015 loopback provider.
 */

#ifndef XVERSE_XCOM_CONTRACT_SUITES_PROVIDER_CONTRACT_SUITE_HPP_
#define XVERSE_XCOM_CONTRACT_SUITES_PROVIDER_CONTRACT_SUITE_HPP_

#include "core_matrix/test_support.hpp"
#include "suite_support.hpp"
#include "xverse/xcom/provider.hpp"

#include <string>
#include <string_view>

namespace xverse::xcom::contract_suites {

/**
 * @brief Reusable subject seam: supplies the concrete provider under test.
 * @ownership The subject owns the provider; the suite retains no reference after the call.
 * @lifetime The subject must outlive the suite call.
 * @thread_safety One caller.
 * @failure An incompatible provider is reported as a failing check, never substituted.
 */
class ProviderSubject {
 public:
  virtual ~ProviderSubject() = default;
  /// @return The provider instance under test.
  [[nodiscard]] virtual CommunicationProvider& provider() noexcept = 0;
};

/**
 * @brief Reusable, implementation-agnostic provider conformance suite.
 * @details The suite names only the accepted `CommunicationProvider` interface and the accepted
 *          `ProviderComposition` boundary. It validates descriptor identity/compatibility, explicit
 *          registration, duplicate rejection, fail-closed unsupported-version rejection, the
 *          prepare/activate/submit/receive/drain/close lifecycle, bounded reject-new saturation, and
 *          bounded reconcile reporting. A different conforming provider is validated by supplying a
 *          different `ProviderSubject`; the suite body is unchanged.
 */
class ProviderContractSuite final {
 public:
  /// @brief Run every provider conformance check against one subject.
  /// @param subject Provider subject under test.
  /// @param suffix Stable, unique fixture identity suffix.
  /// @return The bounded suite report.
  [[nodiscard]] static SuiteReport run(ProviderSubject& subject, const std::string_view suffix) {
    SuiteReport report;
    CommunicationProvider& provider = subject.provider();
    const ProviderDescriptor& descriptor = provider.descriptor();
    report.add("P-01",
               !descriptor.provider_id().value().empty() && provider.descriptor_compatible() &&
                   provider.instance_id() != 0U,
               "descriptor identity, compatibility, and instance identity");

    // A reject-new queue capacity of exactly one item makes saturation observable deterministically.
    test::CoreStackFixture fixture(InteractionKind::message_event, suffix, /*queue_capacity=*/1U,
                                   /*maximum_payload_bytes=*/1U, /*activate_now=*/false,
                                   /*external_provider=*/&provider, /*policy=*/nullptr,
                                   /*provider_id=*/descriptor.provider_id().value());
    report.add("P-02", fixture.ready(), "explicit provider registration");
    report.add("P-03",
               fixture.composition().register_provider(provider).outcome() ==
                   ProviderOutcome::duplicate_provider,
               "duplicate registration rejected");

    ProviderRouteRequirements unsupported = fixture.requirements();
    unsupported.provider_contract_version = "9.9.9";
    report.add("P-04",
               fixture.prepare(unsupported).outcome() ==
                   ProviderOutcome::unsupported_contract_version,
               "unsupported contract version rejected before dispatch");
    if (!fixture.ready()) {
      return report;
    }

    const ProviderResult<ProviderRouteHandle> activated = fixture.prepare_and_activate();
    report.add("P-05", activated.has_value() && fixture.activated(),
               "prepare and activate the exact route");
    if (!fixture.activated()) {
      return report;
    }

    const auto first = fixture.item(7U);
    const auto second = fixture.item(8U);
    if (!first.has_value() || !second.has_value()) {
      report.add("P-06", false, "fixture could not build a bounded item");
      return report;
    }
    report.add("P-06",
               fixture.submit(*first.value()).outcome() == ProviderOutcome::accepted,
               "first accepted item");
    report.add("P-07",
               fixture.submit(*second.value()).outcome() == ProviderOutcome::queue_saturated,
               "saturation rejects the new item without dropping earlier items");

    const auto active_state = fixture.route_state();
    report.add("P-08",
               active_state.has_value() &&
                   active_state.value()->state() == ProviderRouteState::active &&
                   active_state.value()->queued_items() == 1U &&
                   active_state.value()->queue_capacity() == 1U,
               "bounded active route state");
    const auto reconciled = fixture.reconcile();
    report.add("P-09",
               reconciled.has_value() &&
                   reconciled.outcome() == ProviderOutcome::reconciled,
               "bounded reconcile reporting");

    const auto received = fixture.receive();
    report.add("P-10",
               received.has_value() &&
                   received.outcome() == ProviderOutcome::received &&
                   *received.value() == *first.value(),
               "FIFO receive returns the exact earlier item");
    report.add("P-11",
               fixture.receive().outcome() == ProviderOutcome::queue_empty,
               "empty route reported explicitly");
    report.add("P-12", fixture.drain().outcome() == ProviderOutcome::draining, "drain");
    report.add("P-13", fixture.close().outcome() == ProviderOutcome::closed,
               "close an empty drained route");
    return report;
  }
};

}  // namespace xverse::xcom::contract_suites

#endif  // XVERSE_XCOM_CONTRACT_SUITES_PROVIDER_CONTRACT_SUITE_HPP_
