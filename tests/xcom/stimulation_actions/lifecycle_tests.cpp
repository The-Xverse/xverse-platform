/**
 * @file lifecycle_tests.cpp
 * @brief T028 lifecycle completion matrix: bounded scheduled queue and ordering, late-item
 *        policy and lineage bounds, drain/close/revoke/expire, evidence-incomplete completion,
 *        and immediate labeling with unmapped-clock fail-closed behaviour.
 * @ownership Each case owns the permit, policy, config, journal storage, registry, emitter, and
 *            action path it constructs.
 * @lifetime The journal, registry, and emitter outlive the action path.
 * @thread_safety Single-threaded.
 * @bounds Finite queues, bounded drain budgets, bounded operation sequences; no wall-clock verdict.
 * @failure A completion that emits when it must cancel, a late action that emits, an
 *          evidence-incomplete intent reported as success, or an unmapped time that emits fails.
 */

#include "xverse/xcom/stimulation_actions.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <utility>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr val::ClockDomainId kForeignDomain = 8U;
constexpr val::Timestamp kUntil = 100;

[[nodiscard]] val::SessionId session_a() {
  val::SessionId value{};
  value[0] = 1U;
  return value;
}
[[nodiscard]] val::PlanDigest digest_a() {
  val::PlanDigest value{};
  value[0] = 2U;
  return value;
}
[[nodiscard]] val::Tag tag(std::string_view text) { return val::Tag::make(text).value(); }

[[nodiscard]] val::Permit make_permit() {
  val::PermitBuilder builder;
  builder.set_session_id(session_a());
  builder.set_plan_digest(digest_a());
  builder.set_scenario("scenario");
  builder.set_deployment("deployment");
  builder.set_environment("environment");
  builder.set_tool("tool");
  builder.set_interface("iface.v1");
  builder.set_target("target.alpha");
  builder.set_nonce(1U);
  builder.set_validity(kDomain, 0, kUntil);
  builder.add_allowed_action(val::to_mask(val::Action::Activate));
  builder.add_quota(val::Quota{val::QuotaKind::Operations, 16U});
  val::Permit permit;
  EXPECT_EQ(builder.build(permit), val::Result::Ok);
  return permit;
}

[[nodiscard]] val::StimulationPolicy make_policy(const val::Permit &permit,
                                                 std::size_t quota = 8U,
                                                 std::size_t loop_window = 4U) {
  val::StimulationPolicy policy;
  policy.plan_digest = permit.plan_digest();
  policy.interface_tag = tag("iface.v1");
  policy.target = tag("target.alpha");
  policy.validity_domain = permit.validity_domain();
  policy.allowed_actions = val::kDefinedStimulationActions;
  policy.allowed_interactions = 0x0FU;
  policy.allowed_directions = 0x0FU;
  policy.allowed_schemas = {val::SchemaKey{tag("sig.v1"), tag("1")},
                            val::SchemaKey{tag("resp.v1"), tag("1")}};
  policy.max_actions_per_session = quota;
  policy.max_actions_per_window = quota;
  policy.action_window = quota;
  policy.loop_window = loop_window;
  policy.allow_service_emulation = true;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return policy;
}

[[nodiscard]] val::ActionPathConfig make_config() {
  val::ActionPathConfig config;
  config.max_pending_actions = 4U;
  config.max_lineage_entries = 2U;
  config.max_drain_steps = 4U;
  config.late_tolerance = 100;
  config.tool = tag("tool");
  return config;
}

[[nodiscard]] val::StimulationRequest make_signal(const val::Permit &permit, std::uint64_t id,
                                                  bool immediate = true,
                                                  val::Timestamp scheduled_at = 0,
                                                  val::ClockDomainId domain = kDomain) {
  val::StimulationRequest request;
  request.permit_id = permit.permit_id();
  request.session_id = permit.session_id();
  request.plan_digest = permit.plan_digest();
  request.action = val::StimulationAction::InjectSignal;
  request.interaction = InteractionKind::signal_state_update;
  request.direction = EndpointDirection::produce;
  request.schema = val::SchemaKey{tag("sig.v1"), tag("1")};
  request.target = tag("target.alpha");
  request.interface_tag = tag("iface.v1");
  request.clock_domain = domain;
  request.scheduled_at = scheduled_at;
  request.immediate = immediate;
  request.request_id = id;
  request.correlation_id = id + 2000U;
  return request;
}

[[nodiscard]] val::StimulationRequest make_emulate(const val::Permit &permit, std::uint64_t id) {
  val::StimulationRequest request = make_signal(permit, id, true);
  request.action = val::StimulationAction::EmulateService;
  request.interaction = InteractionKind::service_response;
  request.direction = EndpointDirection::respond;
  request.schema = val::SchemaKey{tag("resp.v1"), tag("1")};
  request.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return request;
}

[[nodiscard]] val::ResolvedTime in_window() {
  return val::ResolvedTime{kDomain, 50, val::Result::Ok};
}

class MemoryStorage final : public val::StimulationJournal::Storage {
public:
  val::JournalStatus append(std::span<const std::uint8_t> bytes) override {
    bytes_.insert(bytes_.end(), bytes.begin(), bytes.end());
    return val::JournalStatus::Ok;
  }
  val::JournalStatus sync() override { return val::JournalStatus::Ok; }
  val::JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    out = bytes_;
    return val::JournalStatus::Ok;
  }
  [[nodiscard]] std::size_t size() override { return bytes_.size(); }
  val::JournalStatus truncate(std::size_t size) override {
    bytes_.resize(size);
    return val::JournalStatus::Ok;
  }
  std::vector<std::uint8_t> bytes_{};
};

/// @brief Storage seam that fails one declared append to force an evidence-incomplete intent.
class FaultStorage final : public val::StimulationJournal::Storage {
public:
  explicit FaultStorage(std::size_t fail_on) : fail_on_(fail_on) {}

  val::JournalStatus append(std::span<const std::uint8_t> bytes) override {
    ++append_calls_;
    if (append_calls_ == fail_on_) {
      return val::JournalStatus::WriteFailed;
    }
    bytes_.insert(bytes_.end(), bytes.begin(), bytes.end());
    return val::JournalStatus::Ok;
  }
  val::JournalStatus sync() override { return val::JournalStatus::Ok; }
  val::JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    out = bytes_;
    return val::JournalStatus::Ok;
  }
  [[nodiscard]] std::size_t size() override { return bytes_.size(); }
  val::JournalStatus truncate(std::size_t size) override {
    bytes_.resize(size);
    return val::JournalStatus::Ok;
  }

  std::size_t fail_on_{0};
  std::size_t append_calls_{0};
  std::vector<std::uint8_t> bytes_{};
};

class RecordingEmitter final : public val::ActionEmitter {
public:
  val::EmissionStatus emit(const val::SyntheticStimulationItem &item,
                           std::span<const std::byte>) override {
    ++calls;
    last = item;
    order.push_back(item.intent.request_id);
    return val::EmissionStatus::Delivered;
  }

  std::size_t calls{0};
  val::SyntheticStimulationItem last{};
  std::vector<std::uint64_t> order{};
};

struct Harness {
  MemoryStorage storage{};
  val::StimulationJournal journal{};
  val::ServiceEmulationRegistry registry{4U};
  RecordingEmitter emitter{};
  std::optional<val::StimulationActionPath> path{};

  void build(const val::ActionPathConfig &config) {
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 32U;
    journal_config.max_journal_bytes = 32768U;
    EXPECT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    path.emplace(config, journal, registry, emitter);
  }
};

[[nodiscard]] val::CompletionRequest completion(val::Timestamp now,
                                               val::ClockDomainId domain = kDomain,
                                               val::LifecycleState state =
                                                   val::LifecycleState::active) {
  return val::CompletionRequest{now, domain, state};
}

} // namespace

/** T28-TS-011 (CHK-15): bounded enqueue, declared ordering, and deterministic drain order. */
TEST(XcomStimulationActionsLifecycle, LifecycleScheduledQueueAndOrdering) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  Harness harness;
  harness.build(make_config());
  ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);

  val::ActionDiagnostic diagnostic;
  ASSERT_EQ(harness.path->execute(make_signal(permit, 30U, false, 60), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
            val::ActionStatus::Queued);
  ASSERT_EQ(harness.path->execute(make_signal(permit, 10U, false, 20), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
            val::ActionStatus::Queued);
  ASSERT_EQ(harness.path->execute(make_signal(permit, 20U, false, 20), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
            val::ActionStatus::Queued);
  EXPECT_EQ(harness.path->snapshot().pending, 3U);

  const val::CompletionReport partial = harness.path->drain(completion(50));
  EXPECT_EQ(partial.drained, 2U);
  EXPECT_EQ(partial.outcome, val::CompletionOutcome::None);
  EXPECT_EQ(harness.path->snapshot().pending, 1U);
  ASSERT_EQ(harness.emitter.order.size(), 2U);
  EXPECT_EQ(harness.emitter.order[0], 10U);
  EXPECT_EQ(harness.emitter.order[1], 20U);

  const val::CompletionReport final_report = harness.path->drain(completion(kUntil - 1));
  EXPECT_EQ(final_report.outcome, val::CompletionOutcome::Drained);
  EXPECT_EQ(harness.emitter.order.size(), 3U);
  EXPECT_EQ(harness.emitter.order[2], 30U);
  EXPECT_EQ(harness.path->snapshot().drain_state, val::DrainState::Drained);
}

/** T28-TS-012 (CHK-14, CHK-15): lineage bounds, prohibited reinjection, and late-item policy. */
TEST(XcomStimulationActionsLifecycle, LifecycleLateItemPolicyMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit, 8U, 2U);

  // Lineage bound and prohibited reinjection.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    for (std::uint64_t id = 100U; id <= 102U; ++id) {
      ASSERT_EQ(harness.path->execute(make_signal(permit, id), val::LifecycleState::active,
                                      in_window(), {}, diagnostic),
                val::ActionStatus::Emitted);
    }
    EXPECT_EQ(harness.path->snapshot().lineage_entries, 2U);
    // The oldest identity was evicted, so it is not a prohibited reinjection.
    val::StimulationRequest evicted = make_signal(permit, 103U);
    evicted.causation_id = 100U;
    EXPECT_EQ(harness.path->execute(evicted, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::Emitted);
    // A retained lineage identity is a prohibited reinjection with no emission and no journal.
    const val::JournalSnapshot before_journal = harness.journal.snapshot();
    const std::size_t before_calls = harness.emitter.calls;
    val::StimulationRequest loop = make_signal(permit, 104U);
    loop.causation_id = 102U;
    EXPECT_EQ(harness.path->execute(loop, val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Rejected);
    EXPECT_EQ(harness.emitter.calls, before_calls);
    EXPECT_EQ(harness.journal.snapshot(), before_journal);
    // A zero causation identity is never a loop rejection.
    val::StimulationRequest zero = make_signal(permit, 105U);
    zero.causation_id = 0U;
    EXPECT_EQ(harness.path->execute(zero, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::Emitted);
  }
  // Late-item policies emit nothing.
  for (const val::LateItemPolicy late_policy :
       {val::LateItemPolicy::RejectLate, val::LateItemPolicy::DiscardLate}) {
    val::ActionPathConfig config = make_config();
    config.late_policy = late_policy;
    config.late_tolerance = 0;
    Harness harness;
    harness.build(config);
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_signal(permit, 110U, false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = harness.path->drain(completion(50));
    EXPECT_EQ(report.drained, 0U);
    EXPECT_EQ(harness.emitter.calls, 0U);
    if (late_policy == val::LateItemPolicy::RejectLate) {
      EXPECT_EQ(harness.path->snapshot().expired, 1U);
    } else {
      EXPECT_EQ(harness.path->snapshot().discarded, 1U);
    }
  }
  // Within tolerance the action is emitted.
  {
    val::ActionPathConfig config = make_config();
    config.late_tolerance = 4;
    Harness harness;
    harness.build(config);
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_signal(permit, 120U, false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    EXPECT_EQ(harness.path->drain(completion(14)).drained, 1U);
    EXPECT_EQ(harness.emitter.calls, 1U);
  }
  // The drain budget bounds each call.
  {
    val::ActionPathConfig config = make_config();
    config.max_drain_steps = 1U;
    Harness harness;
    harness.build(config);
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    for (std::uint64_t id = 130U; id <= 131U; ++id) {
      ASSERT_EQ(harness.path->execute(make_signal(permit, id, false, 10),
                                      val::LifecycleState::active, in_window(), {}, diagnostic),
                val::ActionStatus::Queued);
    }
    EXPECT_EQ(harness.path->drain(completion(50)).drained, 1U);
    EXPECT_EQ(harness.path->snapshot().pending, 1U);
  }
}

/** T28-TS-013 (CHK-16): drain, close, revoke, and expire completion. */
TEST(XcomStimulationActionsLifecycle, LifecycleDrainCloseRevokeExpire) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  const val::EndpointGeneration key{session_a(), tag("svc.alpha"), 3U, digest_a()};

  // drain of a terminal session cancels every pending action with zero emission.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_signal(permit, 200U, false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = harness.path->drain(completion(50, kDomain,
                                                                        val::LifecycleState::closed));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Closed);
    EXPECT_EQ(report.cancelled, 1U);
    EXPECT_EQ(harness.emitter.calls, 0U);
    EXPECT_EQ(harness.path->snapshot().drain_state, val::DrainState::Cancelled);
  }
  // close drains due work, cancels the rest, and releases every held lease.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_emulate(permit, 201U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    ASSERT_EQ(harness.path->execute(make_signal(permit, 202U, false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = harness.path->close(completion(kUntil - 1));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Closed);
    EXPECT_EQ(report.drained, 1U);
    EXPECT_EQ(report.released_leases, 1U);
    EXPECT_EQ(harness.registry.state_of(key), val::LeaseState::Released);
  }
  // revoke cancels every pending action and releases every held lease.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_emulate(permit, 203U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    ASSERT_EQ(harness.path->execute(make_signal(permit, 204U, false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport report = harness.path->revoke(completion(50));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Revoked);
    EXPECT_EQ(report.cancelled, 1U);
    EXPECT_EQ(report.released_leases, 1U);
    EXPECT_EQ(harness.emitter.calls, 1U);
  }
  // expire cancels every pending action and expires every held lease.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_emulate(permit, 205U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
    const val::CompletionReport report = harness.path->expire(completion(kUntil));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::Expired);
    EXPECT_EQ(report.expired_leases, 1U);
    EXPECT_EQ(harness.registry.state_of(key), val::LeaseState::Expired);
  }
  // A foreign completion domain mutates nothing.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_signal(permit, 206U, false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    const val::ActionPathSnapshot before = harness.path->snapshot();
    const val::CompletionReport report = harness.path->close(completion(50, kForeignDomain));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::None);
    EXPECT_EQ(harness.path->snapshot(), before);
  }
}

/** T28-TS-014 (CHK-08, CHK-16, NEG-07): an intent without a durable outcome is never success. */
TEST(XcomStimulationActionsLifecycle, LifecycleEvidenceIncompleteCompletion) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  FaultStorage storage{2U};
  val::StimulationJournal journal;
  val::JournalConfig journal_config;
  journal_config.max_retained_records = 16U;
  ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
  val::ServiceEmulationRegistry registry{4U};
  RecordingEmitter emitter;
  val::ActionPathConfig config = make_config();
  val::StimulationActionPath path{config, journal, registry, emitter};
  ASSERT_EQ(path.open(permit, policy), val::GuardStatus::Ok);

  val::ActionDiagnostic diagnostic;
  EXPECT_EQ(path.execute(make_signal(permit, 300U), val::LifecycleState::active, in_window(), {},
                         diagnostic),
            val::ActionStatus::EvidenceIncomplete);
  EXPECT_EQ(diagnostic.journal_status, val::JournalStatus::EvidenceIncomplete);
  // The intent was durable before the single emitter call.
  EXPECT_EQ(emitter.calls, 1U);
  EXPECT_EQ(path.snapshot().evidence_incomplete, 1U);
  EXPECT_EQ(journal.snapshot().orphan_intents, 1U);

  const val::CompletionReport report = path.close(completion(kUntil - 1));
  EXPECT_EQ(report.outcome, val::CompletionOutcome::EvidenceIncomplete);
  EXPECT_EQ(report.evidence_incomplete, 1U);
  EXPECT_NE(report.outcome, val::CompletionOutcome::Closed);
  EXPECT_EQ(path.mark_evidence_incomplete(completion(kUntil)).outcome,
            val::CompletionOutcome::EvidenceIncomplete);

  // T028-IR2-F04: a due action whose drain-time intent append fails is surfaced as a non-success,
  // never dropped silently behind a clean `Drained` outcome.
  {
    const val::Permit drain_permit = make_permit();
    const val::StimulationPolicy drain_policy = make_policy(drain_permit);
    FaultStorage drain_storage{1U};
    val::StimulationJournal drain_journal;
    val::JournalConfig drain_config;
    drain_config.max_retained_records = 16U;
    ASSERT_EQ(drain_journal.open(drain_storage, drain_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry drain_registry{4U};
    RecordingEmitter drain_emitter;
    val::StimulationActionPath drain_path{make_config(), drain_journal, drain_registry,
                                          drain_emitter};
    ASSERT_EQ(drain_path.open(drain_permit, drain_policy), val::GuardStatus::Ok);
    val::ActionDiagnostic drain_diagnostic;
    ASSERT_EQ(drain_path.execute(make_signal(drain_permit, 310U, false, 10),
                                 val::LifecycleState::active, in_window(), {}, drain_diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport drain_report = drain_path.drain(completion(kUntil - 1));
    EXPECT_EQ(drain_report.failed, 1U);
    EXPECT_EQ(drain_report.drained, 0U);
    EXPECT_NE(drain_report.outcome, val::CompletionOutcome::Drained);
    EXPECT_EQ(drain_report.outcome, val::CompletionOutcome::EvidenceIncomplete);
    EXPECT_EQ(drain_emitter.calls, 0U);
  }

  // T028-IR5-F01: a due scheduled action whose drain-time *outcome* append fails leaves a durable
  // intent without a durable outcome. `drain` must surface `EvidenceIncomplete`, never a clean
  // `Drained`, and report the authoritative single orphan intent.
  {
    const val::Permit incomplete_permit = make_permit();
    const val::StimulationPolicy incomplete_policy = make_policy(incomplete_permit);
    FaultStorage incomplete_storage{2U}; // intent append Ok, outcome append fails.
    val::StimulationJournal incomplete_journal;
    val::JournalConfig incomplete_config;
    incomplete_config.max_retained_records = 16U;
    ASSERT_EQ(incomplete_journal.open(incomplete_storage, incomplete_config),
              val::JournalStatus::Ok);
    val::ServiceEmulationRegistry incomplete_registry{4U};
    RecordingEmitter incomplete_emitter;
    val::StimulationActionPath incomplete_path{make_config(), incomplete_journal,
                                               incomplete_registry, incomplete_emitter};
    ASSERT_EQ(incomplete_path.open(incomplete_permit, incomplete_policy), val::GuardStatus::Ok);
    val::ActionDiagnostic incomplete_diagnostic;
    ASSERT_EQ(incomplete_path.execute(make_signal(incomplete_permit, 320U, false, 10),
                                      val::LifecycleState::active, in_window(), {},
                                      incomplete_diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport incomplete_report = incomplete_path.drain(completion(kUntil - 1));
    EXPECT_EQ(incomplete_report.outcome, val::CompletionOutcome::EvidenceIncomplete);
    EXPECT_NE(incomplete_report.outcome, val::CompletionOutcome::Drained);
    EXPECT_EQ(incomplete_report.drained, 0U);
    EXPECT_EQ(incomplete_report.evidence_incomplete, 1U);
    EXPECT_EQ(incomplete_report.evidence_incomplete, incomplete_journal.snapshot().orphan_intents);
    EXPECT_EQ(incomplete_journal.snapshot().orphan_intents, 1U);
  }

  // T028-IR5-F02: `close` reports each distinct drain-time orphan intent once, matching the
  // authoritative journal orphan count (no double count of the loop increment).
  {
    const val::Permit close_permit = make_permit();
    const val::StimulationPolicy close_policy = make_policy(close_permit);
    FaultStorage close_storage{2U}; // intent append Ok, outcome append fails.
    val::StimulationJournal close_journal;
    val::JournalConfig close_config;
    close_config.max_retained_records = 16U;
    ASSERT_EQ(close_journal.open(close_storage, close_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry close_registry{4U};
    RecordingEmitter close_emitter;
    val::StimulationActionPath close_path{make_config(), close_journal, close_registry,
                                          close_emitter};
    ASSERT_EQ(close_path.open(close_permit, close_policy), val::GuardStatus::Ok);
    val::ActionDiagnostic close_diagnostic;
    ASSERT_EQ(close_path.execute(make_signal(close_permit, 330U, false, 10),
                                 val::LifecycleState::active, in_window(), {}, close_diagnostic),
              val::ActionStatus::Queued);
    const val::CompletionReport close_report = close_path.close(completion(kUntil - 1));
    EXPECT_EQ(close_report.outcome, val::CompletionOutcome::EvidenceIncomplete);
    EXPECT_EQ(close_report.evidence_incomplete, 1U);
    EXPECT_EQ(close_report.evidence_incomplete, close_journal.snapshot().orphan_intents);
    EXPECT_EQ(close_journal.snapshot().orphan_intents, 1U);
  }
}

/** T28-TS-014 (CHK-16, NEG-22): a terminal completion never masks an orphan intent as `Closed`. */
TEST(XcomStimulationActionsLifecycle, LifecycleTerminalEvidenceIncompleteNeverClosed) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  // `close(closed)` with a durable intent that has no durable outcome is `EvidenceIncomplete`.
  {
    FaultStorage storage{2U};
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 16U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    RecordingEmitter emitter;
    val::StimulationActionPath path{make_config(), journal, registry, emitter};
    ASSERT_EQ(path.open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(path.execute(make_signal(permit, 500U), val::LifecycleState::active, in_window(), {},
                           diagnostic),
              val::ActionStatus::EvidenceIncomplete);
    ASSERT_EQ(journal.snapshot().orphan_intents, 1U);
    const val::CompletionReport report =
        path.close(completion(kUntil, kDomain, val::LifecycleState::closed));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::EvidenceIncomplete);
    EXPECT_GE(report.evidence_incomplete, 1U);
    EXPECT_NE(report.outcome, val::CompletionOutcome::Closed);
  }
  // `drain(closed)` with a durable intent that has no durable outcome is `EvidenceIncomplete`.
  {
    FaultStorage storage{2U};
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 16U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    RecordingEmitter emitter;
    val::StimulationActionPath path{make_config(), journal, registry, emitter};
    ASSERT_EQ(path.open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(path.execute(make_signal(permit, 501U), val::LifecycleState::active, in_window(), {},
                           diagnostic),
              val::ActionStatus::EvidenceIncomplete);
    const val::CompletionReport report =
        path.drain(completion(kUntil, kDomain, val::LifecycleState::closed));
    EXPECT_EQ(report.outcome, val::CompletionOutcome::EvidenceIncomplete);
    EXPECT_GE(report.evidence_incomplete, 1U);
    EXPECT_NE(report.outcome, val::CompletionOutcome::Closed);
  }
  // A terminal completion with no orphan intent still returns the matching terminal outcome.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(harness.path->execute(make_signal(permit, 502U, false, 10),
                                    val::LifecycleState::active, in_window(), {}, diagnostic),
              val::ActionStatus::Queued);
    EXPECT_EQ(harness.path->close(completion(kUntil, kDomain, val::LifecycleState::closed)).outcome,
              val::CompletionOutcome::Closed);
    EXPECT_EQ(harness.emitter.calls, 0U);
  }
}

/** T28-TS-013 (CHK-16): a non-active, non-terminal completion cancels with zero emission. */
TEST(XcomStimulationActionsLifecycle, LifecycleNonActiveCompletionFailsClosed) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  for (const val::LifecycleState state :
       {val::LifecycleState::declared, val::LifecycleState::armed}) {
    // A scheduled action is due at the completion time; only the non-active state prevents emission.
    {
      Harness harness;
      harness.build(make_config());
      ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
      val::ActionDiagnostic diagnostic;
      ASSERT_EQ(harness.path->execute(make_signal(permit, 600U, false, 10),
                                      val::LifecycleState::active, in_window(), {}, diagnostic),
                val::ActionStatus::Queued);
      const val::CompletionReport report = harness.path->drain(completion(50, kDomain, state));
      EXPECT_EQ(harness.emitter.calls, 0U);
      EXPECT_EQ(report.drained, 0U);
      EXPECT_EQ(report.cancelled, 1U);
      EXPECT_NE(report.outcome, val::CompletionOutcome::Drained);
      EXPECT_NE(report.outcome, val::CompletionOutcome::Closed);
      EXPECT_EQ(harness.path->snapshot().pending, 0U);
    }
    {
      Harness harness;
      harness.build(make_config());
      ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
      val::ActionDiagnostic diagnostic;
      ASSERT_EQ(harness.path->execute(make_signal(permit, 601U, false, 10),
                                      val::LifecycleState::active, in_window(), {}, diagnostic),
                val::ActionStatus::Queued);
      const val::CompletionReport report = harness.path->close(completion(50, kDomain, state));
      EXPECT_EQ(harness.emitter.calls, 0U);
      EXPECT_EQ(report.drained, 0U);
      EXPECT_EQ(report.cancelled, 1U);
      EXPECT_NE(report.outcome, val::CompletionOutcome::Drained);
      EXPECT_NE(report.outcome, val::CompletionOutcome::Closed);
      EXPECT_EQ(harness.path->snapshot().pending, 0U);
    }
  }
}

/** T28-TS-015 (CHK-13, CHK-19): immediate labeling and unmapped-clock fail-closed behaviour. */
TEST(XcomStimulationActionsLifecycle, LifecycleImmediateAndUnmappedClock) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  Harness harness;
  harness.build(make_config());
  ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
  val::ActionDiagnostic diagnostic;

  ASSERT_EQ(harness.path->execute(make_signal(permit, 400U), val::LifecycleState::active,
                                  in_window(), {}, diagnostic),
            val::ActionStatus::Emitted);
  EXPECT_TRUE(harness.emitter.last.intent.immediate);
  EXPECT_EQ(harness.emitter.last.intent.clock_domain, kDomain);

  ASSERT_EQ(harness.path->execute(make_signal(permit, 401U, false, 10),
                                  val::LifecycleState::active, in_window(), {}, diagnostic),
            val::ActionStatus::Queued);
  const std::vector<val::StimulationIntent> recovered = harness.journal.recovered_intents();
  ASSERT_EQ(recovered.size(), 1U);
  EXPECT_TRUE(recovered.front().immediate);

  const std::array<val::Result, 4U> unmapped{val::Result::UnknownClock, val::Result::MissingMapping,
                                             val::Result::ToleranceExceeded,
                                             val::Result::ClockSourceFailure};
  for (std::size_t index = 0; index < unmapped.size(); ++index) {
    const std::size_t before_calls = harness.emitter.calls;
    const val::JournalSnapshot before_journal = harness.journal.snapshot();
    EXPECT_EQ(harness.path->execute(make_signal(permit, 410U + index), val::LifecycleState::active,
                                    val::ResolvedTime{kDomain, 50, unmapped[index]}, {},
                                    diagnostic),
              val::ActionStatus::Failed);
    EXPECT_EQ(diagnostic.guard_reason, val::GuardReason::TimeUnmapped);
    EXPECT_EQ(harness.emitter.calls, before_calls);
    EXPECT_EQ(harness.journal.snapshot(), before_journal);
  }
  // An out-of-window resolved time is rejected before emission and before journaling.
  const std::size_t before_calls = harness.emitter.calls;
  const val::JournalSnapshot before_journal = harness.journal.snapshot();
  EXPECT_EQ(harness.path->execute(make_signal(permit, 420U), val::LifecycleState::active,
                                  val::ResolvedTime{kDomain, kUntil, val::Result::Ok}, {},
                                  diagnostic),
            val::ActionStatus::Rejected);
  EXPECT_EQ(diagnostic.guard_reason, val::GuardReason::TimeOutOfWindow);
  EXPECT_EQ(harness.emitter.calls, before_calls);
  EXPECT_EQ(harness.journal.snapshot(), before_journal);
}
