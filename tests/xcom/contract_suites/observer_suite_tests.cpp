/**
 * @file observer_suite_tests.cpp
 * @brief T033 observer contract-suite drivers: the reusable `ObserverContractSuite` run against
 *        two independent accepted observation hubs, proving the suite is reusable across hub
 *        instances without editing the suite.
 * @ownership Each case owns its subject and hub; the suite owns only its bounded report.
 * @lifetime Subject, hub, and report are per-case.
 * @thread_safety Single-threaded.
 * @bounds One tap, one route, <= 3 submissions per case.
 * @failure A failing or missing suite check fails the owning case closed with bounded detail.
 * @par Traceability
 * Supports T033-SR-004 through T033-SR-006 and the accepted observation boundary.
 */

#include <gtest/gtest.h>

#include "observer_contract_suite.hpp"

#include <string_view>

namespace {

using xverse::xcom::ObservationHub;
using xverse::xcom::contract_suites::ObserverContractSuite;
using xverse::xcom::contract_suites::ObserverSubject;
using xverse::xcom::contract_suites::SuiteReport;

/// @brief Observer subject over one owned observation hub.
class OwnedHubSubject final : public ObserverSubject {
 public:
  ObservationHub& hub() noexcept override { return hub_; }

 private:
  ObservationHub hub_{};
};

}  // namespace

TEST(T033ObserverContractSuite, AcceptedObservationHubConforms) {
  OwnedHubSubject subject;
  const SuiteReport report = ObserverContractSuite::run(subject, "t033.observer.a");
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("O-01"));
  EXPECT_TRUE(report.passed("O-07"));
  EXPECT_TRUE(report.passed("O-10"));
}

TEST(T033ObserverContractSuite, SuiteIsReusableAcrossHubInstances) {
  OwnedHubSubject subject;
  const SuiteReport report = ObserverContractSuite::run(subject, "t033.observer.b");
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("O-06"));
  EXPECT_TRUE(report.passed("O-11"));
}
