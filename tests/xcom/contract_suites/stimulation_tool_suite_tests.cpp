/**
 * @file stimulation_tool_suite_tests.cpp
 * @brief T033 stimulation-tool contract-suite drivers: the reusable
 *        `StimulationToolContractSuite` run against two independent accepted stimulation fixtures,
 *        proving the suite is reusable across composed fixtures without editing the suite.
 * @ownership Each case owns its subject and composed accepted components; the suite owns only its
 *            bounded report.
 * @lifetime Subject, components, and report are per-case.
 * @thread_safety Single-threaded.
 * @bounds One open path, four allowed actions, <= 6 evaluations per case.
 * @failure A failing or missing suite check fails the owning case closed with bounded detail.
 * @par Traceability
 * Supports T033-SR-007 and T033-SR-008 and the accepted stimulation boundary.
 */

#include <gtest/gtest.h>

#include "stimulation_tool_contract_suite.hpp"

#include <cstddef>
#include <cstdint>

namespace {

using xverse::xcom::OriginKind;
using xverse::xcom::contract_suites::StimulationToolContractSuite;
using xverse::xcom::contract_suites::StimulationToolSubject;
using xverse::xcom::contract_suites::stimulation_fixture::make_config;
using xverse::xcom::contract_suites::stimulation_fixture::make_permit;
using xverse::xcom::contract_suites::stimulation_fixture::make_policy;
using xverse::xcom::contract_suites::stimulation_fixture::MatrixFixture;
using xverse::xcom::contract_suites::stimulation_validation::GuardStatus;
using xverse::xcom::contract_suites::stimulation_validation::JournalStatus;
using xverse::xcom::contract_suites::stimulation_validation::Permit;
using xverse::xcom::contract_suites::stimulation_validation::StimulationActionPath;

/// @brief Stimulation-tool subject over one owned accepted stimulation fixture.
class MatrixStimulationSubject final : public StimulationToolSubject {
 public:
  MatrixStimulationSubject() : permit_(make_permit()) {
    opened_ = fixture_.open_journal() == JournalStatus::Ok;
    opened_ = opened_ &&
              fixture_.open_path(permit_, make_policy(permit_), make_config()) == GuardStatus::Ok;
  }

  /// @return true only when the journal and guard/action path opened.
  [[nodiscard]] bool opened() const noexcept { return opened_; }

  StimulationActionPath& path() noexcept override { return *fixture_.path; }
  const Permit& permit() const noexcept override { return permit_; }
  std::size_t emission_calls() noexcept override { return fixture_.emitter.calls.load(); }
  bool last_emission_synthetic() override {
    return fixture_.emitter.last_item().origin == OriginKind::validation_tool;
  }
  std::uint64_t last_emission_request_id() override {
    return fixture_.emitter.last_item().intent.request_id;
  }
  bool intent_durable_before_emission() override {
    return fixture_.emitter.intent_durable_before_emit();
  }

 private:
  Permit permit_{};
  MatrixFixture fixture_{};
  bool opened_{false};
};

}  // namespace

TEST(T033StimulationToolContractSuite, AcceptedStimulationPathConforms) {
  MatrixStimulationSubject subject;
  ASSERT_TRUE(subject.opened());
  const xverse::xcom::contract_suites::SuiteReport report =
      StimulationToolContractSuite::run(subject);
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("S-01"));
  EXPECT_TRUE(report.passed("S-02-3"));
  EXPECT_TRUE(report.passed("S-05"));
}

TEST(T033StimulationToolContractSuite, SuiteIsReusableAcrossFixtures) {
  MatrixStimulationSubject subject;
  ASSERT_TRUE(subject.opened());
  const xverse::xcom::contract_suites::SuiteReport report =
      StimulationToolContractSuite::run(subject);
  EXPECT_TRUE(report.ok()) << report.failure_detail();
  EXPECT_TRUE(report.passed("S-03"));
  EXPECT_TRUE(report.passed("S-04"));
}
