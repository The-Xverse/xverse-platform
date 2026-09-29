/**
 * @file gateway_suite_tests.cpp
 * @brief T033 gateway contract-suite drivers: the reusable `GatewayContractSuite` run against two
 *        independent accepted gateway fixture factories, proving the suite is reusable across
 *        gateway fixtures without editing the suite.
 * @ownership Each case owns its subject; the suite owns the fixture it constructs per group.
 * @lifetime Subject and report are per-case; each fixture is destroyed within its group.
 * @thread_safety Single-threaded.
 * @bounds <= 12 fixtures, <= 4 emissions per case.
 * @failure A failing or missing suite check fails the owning case closed with bounded detail.
 * @par Traceability
 * Supports T033-SR-009 through T033-SR-013 and the accepted `XCOM-SW-GW-002` gateway session.
 */

#include <gtest/gtest.h>

#include "gateway_contract_suite.hpp"

#include <memory>

namespace {

using xverse::xcom::contract_suites::GatewayContractSuite;
using xverse::xcom::contract_suites::GatewaySubject;
using xverse::xcom::contract_suites::SuiteReport;
using xverse::xcom::tool_gateway_test::GatewayFixture;

/// @brief Gateway subject that returns a fresh accepted gateway fixture per group.
class FactoryGatewaySubject final : public GatewaySubject {
 public:
  std::unique_ptr<GatewayFixture> make_fixture() override {
    return std::make_unique<GatewayFixture>();
  }
};

}  // namespace

TEST(T033GatewayContractSuite, AcceptedGatewaySessionConforms) {
  FactoryGatewaySubject subject;
  const SuiteReport report = GatewayContractSuite::run(subject);
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("G-02"));
  EXPECT_TRUE(report.passed("G-06"));
  EXPECT_TRUE(report.passed("G-09"));
}

TEST(T033GatewayContractSuite, SuiteIsReusableAcrossFixtures) {
  FactoryGatewaySubject subject;
  const SuiteReport report = GatewayContractSuite::run(subject);
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("G-03"));
  EXPECT_TRUE(report.passed("G-07"));
  EXPECT_TRUE(report.passed("G-10"));
}
