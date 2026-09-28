/**
 * @file provenance_tests.cpp
 * @brief T029 persistent synthetic provenance matrix: every emitted descriptor carries
 *        `OriginKind::validation_tool` and the exact identity, the accepted provider route and
 *        observation tap preserve classification and correlation/causation identity, a
 *        `validation_tool` filter matches only synthetic records, and a journal restart preserves
 *        the exact identity. No path relabels or drops provenance.
 * @ownership Each case owns its fixture, bridge, tap, sink, captured descriptor, and restart
 *            journal.
 * @lifetime The bridge, hub, and lifecycle outlive the tap and sink.
 * @thread_safety Single-threaded.
 * @bounds <= 4 emissions, one tap, one sink, one restart per case.
 * @failure Any non-synthetic descriptor, relabelled record, dropped identity, or restart mismatch
 *          fails the case.
 */

#include "test_support.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace val = xverse::xcom::validation;
namespace xc = xverse::xcom;
using xverse::xcom::stimulation_matrix_test::default_journal_config;
using xverse::xcom::stimulation_matrix_test::in_window;
using xverse::xcom::stimulation_matrix_test::make_config;
using xverse::xcom::stimulation_matrix_test::make_permit;
using xverse::xcom::stimulation_matrix_test::make_policy;
using xverse::xcom::stimulation_matrix_test::make_request;
using xverse::xcom::stimulation_matrix_test::MatrixFixture;
using xverse::xcom::stimulation_matrix_test::ObservationBridge;
using xverse::xcom::stimulation_matrix_test::session_decimal;
using xverse::xcom::stimulation_matrix_test::StorageFault;
using xverse::xcom::stimulation_matrix_test::to_decimal;

namespace {

/// @brief One declared action kind with a distinct request identity.
struct ActionRow {
  /// @brief Declared stimulation action.
  val::StimulationAction action;
  /// @brief Request identity.
  std::uint64_t request_id;
};

/// @brief The four declared action kinds.
constexpr std::array<ActionRow, 4U> kActionKinds{{
    {val::StimulationAction::InjectSignal, 800U},
    {val::StimulationAction::InjectMessage, 801U},
    {val::StimulationAction::InvokeService, 802U},
    {val::StimulationAction::EmulateService, 803U},
}};

/// @brief Emits one immediate authorized action and returns the captured descriptor.
/// @param fixture The opened fixture.
/// @param permit The bound permit.
/// @param row The action row.
/// @return The captured descriptor.
[[nodiscard]] val::SyntheticStimulationItem emit_one(MatrixFixture &fixture, const val::Permit &permit,
                                                      const ActionRow &row) {
  val::ActionDiagnostic diagnostic;
  EXPECT_EQ(fixture.path->execute(make_request(permit, row.request_id, row.action),
                                  val::LifecycleState::active, in_window(), {}, diagnostic),
            val::ActionStatus::Emitted);
  return fixture.emitter.last_item();
}

} // namespace

/** T29-TS-012 (CHK-13, NEG-21): every emitted descriptor carries the synthetic classification and
 *  the exact tool/permit/session/plan/request/correlation/causation identity. */
TEST(XcomStimulationMatrixProvenance, ProvenanceDescriptorCarriesSyntheticIdentity) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  for (const ActionRow &row : kActionKinds) {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    val::StimulationRequest request = make_request(permit, row.request_id, row.action);
    request.correlation_id = 9000U + row.request_id;
    request.causation_id = 7000U + row.request_id;
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(fixture.path->execute(request, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::Emitted);
    const val::SyntheticStimulationItem descriptor = fixture.emitter.last_item();
    EXPECT_EQ(descriptor.origin, xc::OriginKind::validation_tool);
    const val::StimulationIntent &intent = descriptor.intent;
    EXPECT_EQ(intent.permit_id, permit.permit_id());
    EXPECT_EQ(intent.session_id, permit.session_id());
    EXPECT_EQ(intent.plan_digest, permit.plan_digest());
    EXPECT_EQ(intent.request_id, request.request_id);
    EXPECT_EQ(intent.correlation_id, request.correlation_id);
    EXPECT_EQ(intent.causation_id, request.causation_id);
    EXPECT_EQ(intent.target, request.target);
    EXPECT_EQ(intent.tool.value(), "tool");
    EXPECT_EQ(intent.action_mask, val::to_stimulation_mask(row.action));
    EXPECT_TRUE(intent.immediate);
  }
}

/** T29-TS-013 (CHK-13, NEG-22, NEG-23): the accepted provider route and observation tap preserve
 *  origin and correlation/causation identity, and the origin filter matches only synthetic
 *  records. */
TEST(XcomStimulationMatrixProvenance, ProvenanceSurvivesRoutingAndObservation) {
  const val::Permit permit = make_permit();
  MatrixFixture fixture;
  ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, make_policy(permit), make_config()), val::GuardStatus::Ok);
  const val::SyntheticStimulationItem descriptor = emit_one(
      fixture, permit, ActionRow{val::StimulationAction::InjectMessage, 810U});
  ASSERT_EQ(fixture.emitter.calls.load(), 1U);

  ObservationBridge bridge;
  ASSERT_TRUE(bridge.ready());
  const xc::ObservationAttachResult attach = bridge.attach_synthetic_tap(4U);
  ASSERT_TRUE(attach.handle.has_value());
  const std::optional<xc::CommunicationItem> item = bridge.make_item(descriptor);
  ASSERT_TRUE(item.has_value());
  EXPECT_EQ(item->origin(), xc::OriginKind::validation_tool);
  EXPECT_EQ(bridge.submit(*item).outcome(), xc::ProviderOutcome::accepted);

  xc::SyntheticObservationSink sink(bridge.hub(), *attach.handle);
  const xc::ObservationPollResult poll = sink.pull();
  ASSERT_TRUE(poll.record.has_value());
  const xc::ObservationRecord &record = *poll.record;
  EXPECT_EQ(record.origin(), xc::OriginKind::validation_tool);
  EXPECT_EQ(record.correlation_id().value(), to_decimal(descriptor.intent.correlation_id));
  EXPECT_EQ(record.causation_id().value(), to_decimal(descriptor.intent.causation_id));
  EXPECT_EQ(record.endpoint_id().value(), session_decimal(descriptor.intent.session_id));
  EXPECT_EQ(record.route_id().value(), bridge.route_id());
  EXPECT_EQ(record.provider_id().value(), descriptor.intent.tool.value());

  // P-04: a filter constrained to the synthetic origin matches; a foreign origin does not.
  xc::ObservationFilterInput synthetic_filter{};
  synthetic_filter.origin = xc::OriginKind::validation_tool;
  const auto synthetic = xc::ObservationFilter::create(synthetic_filter);
  xc::ObservationFilterInput foreign_filter{};
  foreign_filter.origin = xc::OriginKind::replay;
  const auto foreign = xc::ObservationFilter::create(foreign_filter);
  ASSERT_TRUE(synthetic.has_value() && foreign.has_value());
  EXPECT_TRUE(synthetic->matches(*item));
  EXPECT_FALSE(foreign->matches(*item));
}

/** T29-TS-014 (CHK-13, NEG-23): a journal restart preserves the exact synthetic identity. */
TEST(XcomStimulationMatrixProvenance, ProvenanceSurvivesJournalRestart) {
  const val::Permit permit = make_permit();
  MatrixFixture fixture;
  fixture.storage.append_fault = StorageFault::WriteFailed;
  fixture.storage.append_fault_on = 2U;
  ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, make_policy(permit), make_config()), val::GuardStatus::Ok);
  val::StimulationRequest request = make_request(permit, 820U);
  request.correlation_id = 8200U;
  request.causation_id = 7200U;
  val::ActionDiagnostic diagnostic;
  ASSERT_EQ(fixture.path->execute(request, val::LifecycleState::active, in_window(), {},
                                  diagnostic),
            val::ActionStatus::EvidenceIncomplete);
  const val::SyntheticStimulationItem descriptor = fixture.emitter.last_item();
  EXPECT_EQ(descriptor.origin, xc::OriginKind::validation_tool);

  val::StimulationJournal restarted;
  ASSERT_EQ(restarted.open(fixture.storage, default_journal_config()), val::JournalStatus::Ok);
  const std::vector<val::StimulationIntent> recovered = restarted.recovered_intents();
  ASSERT_EQ(recovered.size(), 1U);
  EXPECT_EQ(recovered.front(), descriptor.intent);
  EXPECT_EQ(recovered.front().correlation_id, 8200U);
  EXPECT_EQ(recovered.front().causation_id, 7200U);
  EXPECT_EQ(restarted.last_recovery().orphan_intents, 1U);
}

/** T29-TS-015 (CHK-13, NEG-21, NEG-22): no path emits, routes, observes, or relabels provenance. */
TEST(XcomStimulationMatrixProvenance, ProvenanceNeverRelabelled) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  // Every action kind is emitted with the synthetic classification.
  for (const ActionRow &row : kActionKinds) {
    MatrixFixture fixture;
    ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
    ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
    const val::SyntheticStimulationItem descriptor = emit_one(fixture, permit, row);
    EXPECT_EQ(descriptor.origin, xc::OriginKind::validation_tool);
    EXPECT_FALSE(descriptor.intent.tool.value().empty());
  }

  // A foreign-origin item never matches the synthetic filter; a synthetic item does.
  ObservationBridge bridge;
  ASSERT_TRUE(bridge.ready());
  const std::optional<xc::CommunicationItem> foreign_component =
      bridge.make_foreign_item(xc::OriginKind::component);
  ASSERT_TRUE(foreign_component.has_value());
  EXPECT_EQ(foreign_component->origin(), xc::OriginKind::component);
  EXPECT_EQ(foreign_component->correlation_id().value(), to_decimal(1U));
  EXPECT_EQ(foreign_component->causation_id().value(), to_decimal(0U));

  xc::ObservationFilterInput synthetic_filter{};
  synthetic_filter.origin = xc::OriginKind::validation_tool;
  const auto synthetic = xc::ObservationFilter::create(synthetic_filter);
  ASSERT_TRUE(synthetic.has_value());
  EXPECT_FALSE(synthetic->matches(*foreign_component));

  MatrixFixture fixture;
  ASSERT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  ASSERT_EQ(fixture.open_path(permit, policy, make_config()), val::GuardStatus::Ok);
  const val::SyntheticStimulationItem descriptor = emit_one(
      fixture, permit, ActionRow{val::StimulationAction::InjectSignal, 830U});
  const std::optional<xc::CommunicationItem> synthetic_item = bridge.make_item(descriptor);
  ASSERT_TRUE(synthetic_item.has_value());
  EXPECT_TRUE(synthetic->matches(*synthetic_item));
  EXPECT_EQ(synthetic_item->origin(), xc::OriginKind::validation_tool);
}
