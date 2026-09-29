/**
 * @file second_provider_suite_tests.cpp
 * @brief T034 `t034-replaceability` driver: runs the unchanged accepted T033
 *        `ProviderContractSuite` against the second minimal synthetic provider through a new
 *        `ProviderSubject` adapter, and proves bounded capability/saturation and full lifecycle.
 * @ownership Each case owns its subject, provider, and report; the reused suite owns only its
 *            bounded report.
 * @lifetime Subject, provider, and report are per-case values.
 * @thread_safety Single-threaded; the accepted composition and provider serialize their own state.
 * @bounds One second provider, one reused suite run, one route per case.
 * @failure A failing or missing suite check fails the owning case closed with bounded detail.
 * @par Traceability
 * Supports T034-SR-001 through T034-SR-004 and T034-SR-010 over the accepted `XCOM-DU-007`/
 * `XCOM-DU-008` provider boundary and the unchanged T033 `ProviderContractSuite`.
 */

#include <gtest/gtest.h>

#include "provider_contract_suite.hpp"
#include "synthetic_provider.hpp"

#include <cstdint>
#include <type_traits>

namespace {

using xverse::xcom::CommunicationProvider;
using xverse::xcom::DeliveryCapability;
using xverse::xcom::LoopbackProvider;
using xverse::xcom::OrderingCapability;
using xverse::xcom::ProviderDescriptor;
using xverse::xcom::SyntheticProvider;
using xverse::xcom::contract_suites::ProviderContractSuite;
using xverse::xcom::contract_suites::ProviderSubject;
using xverse::xcom::contract_suites::SuiteReport;
using xverse::xcom::delivery_capability_bit;
using xverse::xcom::ordering_capability_bit;
using xverse::xcom::test::kAllInteractions;
using xverse::xcom::test::loopback_descriptor;
using xverse::xcom::test::make_descriptor;

static_assert(std::is_base_of_v<CommunicationProvider, SyntheticProvider>,
              "the second provider must implement the accepted CommunicationProvider interface");

/// @brief Provider subject over the T034 second minimal synthetic provider.
class SyntheticProviderSubject final : public ProviderSubject {
 public:
  SyntheticProviderSubject()
      : descriptor_(make_descriptor("provider.t034.synthetic", kAllInteractions,
                                    delivery_capability_bit(DeliveryCapability::best_effort),
                                    ordering_capability_bit(OrderingCapability::per_route_fifo),
                                    1U, 1U, 1U)),
        provider_(descriptor_) {}
  CommunicationProvider& provider() noexcept override { return provider_; }

 private:
  ProviderDescriptor descriptor_;
  SyntheticProvider provider_;
};

}  // namespace

TEST(T034SecondProviderSuite, ReusedProviderContractSuitePasses) {
  SyntheticProviderSubject subject;
  const SuiteReport report =
      ProviderContractSuite::run(subject, "t034.provider.synthetic");
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("P-01"));
  EXPECT_TRUE(report.passed("P-05"));
  EXPECT_TRUE(report.passed("P-13"));
}

TEST(T034SecondProviderSuite, ProviderIsIndependentOfLoopback) {
  const ProviderDescriptor synthetic_descriptor =
      make_descriptor("provider.t034.synthetic.identity", kAllInteractions,
                      delivery_capability_bit(DeliveryCapability::best_effort),
                      ordering_capability_bit(OrderingCapability::per_route_fifo), 1U, 1U, 1U);
  SyntheticProvider synthetic(synthetic_descriptor);
  const ProviderDescriptor loopback_descriptor_value =
      loopback_descriptor("provider.t034.loopback.identity", 1U, 1U);
  LoopbackProvider loopback(loopback_descriptor_value);

  EXPECT_TRUE(synthetic.descriptor_compatible());
  EXPECT_NE(synthetic.instance_id(), 0U);
  EXPECT_NE(loopback.instance_id(), 0U);
  EXPECT_NE(synthetic.instance_id(), loopback.instance_id());
  EXPECT_TRUE(synthetic.descriptor().provider_id() == synthetic_descriptor.provider_id());
}

TEST(T034SecondProviderSuite, BoundedCapabilitiesAndSaturation) {
  SyntheticProviderSubject subject;
  const SuiteReport report =
      ProviderContractSuite::run(subject, "t034.provider.bounded");
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("P-02"));
  EXPECT_TRUE(report.passed("P-06"));
  EXPECT_TRUE(report.passed("P-07"));
  EXPECT_TRUE(report.passed("P-08"));
}

TEST(T034SecondProviderLifecycle, CompletesFullBoundedLifecycle) {
  SyntheticProviderSubject subject;
  const SuiteReport report =
      ProviderContractSuite::run(subject, "t034.provider.lifecycle");
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("P-05"));
  EXPECT_TRUE(report.passed("P-09"));
  EXPECT_TRUE(report.passed("P-10"));
  EXPECT_TRUE(report.passed("P-11"));
  EXPECT_TRUE(report.passed("P-12"));
  EXPECT_TRUE(report.passed("P-13"));
}
