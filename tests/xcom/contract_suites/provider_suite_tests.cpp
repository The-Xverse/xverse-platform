/**
 * @file provider_suite_tests.cpp
 * @brief T033 provider contract-suite drivers: the reusable `ProviderContractSuite` run against the
 *        accepted loopback provider and against a second independently implemented provider, proving
 *        the suite is reusable across provider implementations without editing the suite.
 * @ownership Each case owns its subject and provider; the suite owns only its bounded report.
 * @lifetime Subject, provider, and report are per-case.
 * @thread_safety Single-threaded.
 * @bounds One provider and one route per case.
 * @failure A failing or missing suite check fails the owning case closed with bounded detail.
 * @par Traceability
 * Supports T033-SR-001 through T033-SR-003 and the accepted `XCOM-DU-007`/`XCOM-DU-021` boundary.
 */

#include <gtest/gtest.h>

#include "provider_contract_suite.hpp"

#include <string>

namespace {

using xverse::xcom::CommunicationProvider;
using xverse::xcom::DeliveryCapability;
using xverse::xcom::LoopbackProvider;
using xverse::xcom::OrderingCapability;
using xverse::xcom::ProviderDescriptor;
using xverse::xcom::contract_suites::ProviderContractSuite;
using xverse::xcom::contract_suites::ProviderSubject;
using xverse::xcom::delivery_capability_bit;
using xverse::xcom::ordering_capability_bit;
using xverse::xcom::test::ProbeProvider;
using xverse::xcom::test::kAllInteractions;
using xverse::xcom::test::loopback_descriptor;
using xverse::xcom::test::make_descriptor;

/// @brief Provider subject over the accepted owned loopback provider.
class LoopbackProviderSubject final : public ProviderSubject {
 public:
  LoopbackProviderSubject()
      : descriptor_(loopback_descriptor("provider.t033.loopback", 1U, 1U)),
        provider_(descriptor_) {}
  CommunicationProvider& provider() noexcept override { return provider_; }

 private:
  ProviderDescriptor descriptor_;
  LoopbackProvider provider_;
};

/// @brief Provider subject over a second, independently implemented accepted test provider.
class ProbeProviderSubject final : public ProviderSubject {
 public:
  ProbeProviderSubject()
      : descriptor_(make_descriptor("provider.t033.probe", kAllInteractions,
                                    delivery_capability_bit(DeliveryCapability::best_effort),
                                    ordering_capability_bit(OrderingCapability::per_route_fifo),
                                    64U, 1U, 1U)),
        provider_(descriptor_, 0x7033U) {}
  CommunicationProvider& provider() noexcept override { return provider_; }

 private:
  ProviderDescriptor descriptor_;
  ProbeProvider provider_;
};

}  // namespace

TEST(T033ProviderContractSuite, AcceptedLoopbackProviderConforms) {
  LoopbackProviderSubject subject;
  const xverse::xcom::contract_suites::SuiteReport report =
      ProviderContractSuite::run(subject, "t033.provider.loopback");
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("P-01"));
  EXPECT_TRUE(report.passed("P-10"));
  EXPECT_TRUE(report.passed("P-13"));
}

TEST(T033ProviderContractSuite, SuiteIsReusableAcrossProviderImplementations) {
  ProbeProviderSubject subject;
  const xverse::xcom::contract_suites::SuiteReport report =
      ProviderContractSuite::run(subject, "t033.provider.probe");
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("P-02"));
  EXPECT_TRUE(report.passed("P-07"));
}
