#include "test_support.hpp"
#include <limits>
#include <stdexcept>

namespace t = xverse::xcom::stimulation_matrix_test;
namespace v = xverse::xcom::validation;

TEST(ExternalReview, ImmediateControl) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p), t::make_config()), v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  EXPECT_EQ(f.path->execute(t::make_request(p, 1), v::LifecycleState::active,
                           t::in_window(), {}, d), v::ActionStatus::Emitted);
  EXPECT_EQ(f.emitter.calls.load(), 1U);
}

TEST(ExternalReview, ScheduledActionCannotEmitAtPermitExpiry) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p), t::make_config()), v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  ASSERT_EQ(f.path->execute(t::make_request(p, 1, v::StimulationAction::InjectSignal, false, 60),
                           v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::Queued);
  const auto report = f.path->drain({p.valid_until(), t::kDomain, v::LifecycleState::active});
  EXPECT_EQ(report.outcome, v::CompletionOutcome::Expired);
  EXPECT_EQ(f.emitter.calls.load(), 0U);
}

TEST(ExternalReview, CloseAndClosingDrainRespectExclusivePermitEnd) {
  for (const bool close : {false, true}) {
    t::MatrixFixture f;
    const auto p = t::make_permit();
    ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
    ASSERT_EQ(f.open_path(p, t::make_policy(p), t::make_config()), v::GuardStatus::Ok);
    v::ActionDiagnostic d;
    ASSERT_EQ(f.path->execute(t::make_request(p, 1, v::StimulationAction::InjectSignal,
                                              false, 60), v::LifecycleState::active,
                              t::in_window(), {}, d), v::ActionStatus::Queued);
    const v::CompletionRequest request{p.valid_until(), t::kDomain,
                                        v::LifecycleState::closing};
    const auto report = close ? f.path->close(request) : f.path->drain(request);
    EXPECT_EQ(report.outcome, v::CompletionOutcome::Expired);
    EXPECT_EQ(report.cancelled, 1U);
    EXPECT_EQ(f.emitter.calls.load(), 0U);
  }
}

TEST(ExternalReview, MappedScheduledActionCanDrain) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p), t::make_config()), v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  const auto request = t::make_request(p, 1, v::StimulationAction::InjectSignal,
                                     false, 60, t::kForeignDomain);
  ASSERT_EQ(f.path->execute(request, v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::Queued);
  const auto report = f.path->drain({50, t::kDomain, v::LifecycleState::active});
  EXPECT_EQ(report.drained, 1U);
  EXPECT_EQ(f.path->snapshot().pending, 0U);
  EXPECT_EQ(f.emitter.last_item().intent.clock_domain, t::kForeignDomain);
  EXPECT_EQ(f.emitter.last_item().intent.scheduled_at, 60);
}

TEST(ExternalReview, ReplacedLeaseCannotAuthorizeOldQueuedRequest) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p), t::make_config()), v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  const auto request = t::make_request(p, 1, v::StimulationAction::EmulateService, false, 60);
  ASSERT_EQ(f.path->execute(request, v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::Queued);
  const v::EndpointGeneration key{p.session_id(), request.service_owner.endpoint,
                                  request.service_owner.generation, p.plan_digest()};
  ASSERT_EQ(f.registry.release(key, 1), v::LeaseStatus::Ok);
  ASSERT_EQ(f.registry.acquire(key, 2, t::kDomain, 50, 100), v::LeaseStatus::Ok);
  const auto report = f.path->drain({60, t::kDomain, v::LifecycleState::active});
  EXPECT_EQ(report.cancelled, 1U);
  EXPECT_EQ(f.emitter.calls.load(), 0U);
}

TEST(ExternalReview, QuarantinedLeaseCannotAuthorizeQueuedEmission) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p), t::make_config()), v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  const auto request = t::make_request(p, 1, v::StimulationAction::EmulateService, false, 60);
  ASSERT_EQ(f.path->execute(request, v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::Queued);
  const v::EndpointGeneration key{p.session_id(), request.service_owner.endpoint,
                                  request.service_owner.generation, p.plan_digest()};
  ASSERT_EQ(f.registry.quarantine(key, v::QuarantineReason::Conflict), v::LeaseStatus::Ok);
  EXPECT_EQ(f.path->drain({60, t::kDomain, v::LifecycleState::active}).cancelled, 1U);
  EXPECT_EQ(f.emitter.calls.load(), 0U);
}

TEST(ExternalReview, EmissionReservationBlocksReplacementUntilFinished) {
  v::ServiceEmulationRegistry registry(2);
  const auto p = t::make_permit();
  const auto request = t::make_request(p, 1, v::StimulationAction::EmulateService);
  const v::EndpointGeneration key{p.session_id(), request.service_owner.endpoint,
                                  request.service_owner.generation, p.plan_digest()};
  ASSERT_EQ(registry.acquire(key, 1, t::kDomain, 50, 100), v::LeaseStatus::Ok);
  ASSERT_TRUE(registry.reserve_emission(key, 1));
  ASSERT_EQ(registry.release(key, 1), v::LeaseStatus::Ok);
  EXPECT_EQ(registry.acquire(key, 2, t::kDomain, 50, 100), v::LeaseStatus::Conflict);
  registry.finish_emission(key, 1);
  EXPECT_EQ(registry.acquire(key, 2, t::kDomain, 50, 100), v::LeaseStatus::Ok);
  EXPECT_FALSE(registry.reserve_emission(key, 1));
}

TEST(ExternalReview, DuplicateRejectionDoesNotConsumeQuota) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p, 2), t::make_config()), v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  const auto request = t::make_request(p, 1);
  ASSERT_EQ(f.path->execute(request, v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::Emitted);
  ASSERT_EQ(f.path->execute(request, v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::RejectedConfiguration);
  EXPECT_EQ(f.path->execute(t::make_request(p, 2), v::LifecycleState::active,
                           t::in_window(), {}, d), v::ActionStatus::Emitted);
}

TEST(ExternalReview, FailedIntentDoesNotKeepEmulationLease) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p), t::make_config()), v::GuardStatus::Ok);
  f.storage.append_fault = t::StorageFault::WriteFailed;
  f.storage.append_fault_on = 1;
  v::ActionDiagnostic d;
  ASSERT_EQ(f.path->execute(t::make_request(p, 1, v::StimulationAction::EmulateService),
                           v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::JournalFailed);
  EXPECT_EQ(f.emitter.calls.load(), 0U);
  EXPECT_EQ(f.registry.snapshot().active, 0U);
}

v::StimulationIntent intent_for_probe() {
  const auto p = t::make_permit();
  v::StimulationIntent intent;
  intent.permit_id = p.permit_id();
  intent.session_id = p.session_id();
  intent.plan_digest = p.plan_digest();
  intent.request_id = 1;
  intent.target = t::tag("target.alpha");
  intent.tool = t::tag("tool");
  intent.clock_domain = t::kDomain;
  return intent;
}

TEST(ExternalReview, InFlightResolutionCannotProduceTwoOutcomes) {
  t::FaultStorage storage;
  v::StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, t::default_journal_config()), v::JournalStatus::Ok);
  const auto callback = [&](const v::StimulationIntent &intent) {
    v::StimulationOutcome early;
    early.kind = v::OutcomeKind::Unknown;
    early.clock_domain = t::kDomain;
    const auto resolution = journal.resolve(intent.request_id, early);
    EXPECT_EQ(resolution, v::JournalStatus::RejectedConfiguration);
    early.kind = v::OutcomeKind::Delivered;
    return early;
  };
  v::StimulationOutcome out;
  EXPECT_EQ(journal.journal_then_emit(intent_for_probe(), callback, out), v::JournalStatus::Ok);
  EXPECT_EQ(journal.snapshot().complete_intents, 1U);
  EXPECT_EQ(journal.snapshot().outcomes, 1U);
}

TEST(ExternalReview, ThrownCallbackLeavesOneResolvableOrphan) {
  t::FaultStorage storage;
  v::StimulationJournal journal;
  ASSERT_EQ(journal.open(storage, t::default_journal_config()), v::JournalStatus::Ok);
  v::StimulationOutcome out;
  EXPECT_THROW((void)journal.journal_then_emit(
                   intent_for_probe(),
                   [](const v::StimulationIntent &) -> v::StimulationOutcome {
                     throw std::runtime_error("test callback failure");
                   }, out), std::runtime_error);
  EXPECT_EQ(journal.snapshot().orphan_intents, 1U);
  v::StimulationOutcome unknown;
  unknown.kind = v::OutcomeKind::Unknown;
  unknown.clock_domain = t::kDomain;
  EXPECT_EQ(journal.resolve(1, unknown), v::JournalStatus::Ok);
  EXPECT_EQ(journal.resolve(1, unknown), v::JournalStatus::AlreadyResolved);
  EXPECT_EQ(journal.snapshot().outcomes, 1U);
}

TEST(ExternalReview, LegalLateToleranceDoesNotOverflow) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p),
                       t::make_config(8, 8, 8, std::numeric_limits<v::Timestamp>::max())),
            v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  ASSERT_EQ(f.path->execute(t::make_request(p, 1, v::StimulationAction::InjectSignal, false, 60),
                           v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::Queued);
  const auto report = f.path->drain({60, t::kDomain, v::LifecycleState::active});
  EXPECT_EQ(report.drained, 1U);
}

TEST(ExternalReview, CloseWithMaximumLateToleranceDoesNotOverflow) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  ASSERT_EQ(f.open_path(p, t::make_policy(p),
                        t::make_config(8, 8, 8, std::numeric_limits<v::Timestamp>::max())),
            v::GuardStatus::Ok);
  v::ActionDiagnostic d;
  ASSERT_EQ(f.path->execute(t::make_request(p, 1, v::StimulationAction::InjectSignal, false, 60),
                            v::LifecycleState::active, t::in_window(), {}, d),
            v::ActionStatus::Queued);
  EXPECT_EQ(f.path->close({60, t::kDomain, v::LifecycleState::closing}).drained, 1U);
}

TEST(ExternalReview, MalformedCapacityFailsClosedWithoutProcessTermination) {
  t::MatrixFixture f;
  const auto p = t::make_permit();
  ASSERT_EQ(f.open_journal(), v::JournalStatus::Ok);
  auto config = t::make_config();
  config.max_pending_actions = std::numeric_limits<std::size_t>::max();
  EXPECT_EQ(f.open_path(p, t::make_policy(p), config),
            v::GuardStatus::RejectedConfiguration);
  config = t::make_config();
  config.max_lineage_entries = std::numeric_limits<std::size_t>::max();
  EXPECT_EQ(f.open_path(p, t::make_policy(p), config),
            v::GuardStatus::RejectedConfiguration);
  config = t::make_config();
  config.max_pending_actions = 0;
  EXPECT_EQ(f.open_path(p, t::make_policy(p), config),
            v::GuardStatus::RejectedConfiguration);
}
