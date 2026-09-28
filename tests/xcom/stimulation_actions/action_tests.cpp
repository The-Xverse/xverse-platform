/**
 * @file action_tests.cpp
 * @brief T028 nominal action kinds, guard-decision mapping, synthetic provenance, closed
 *        vocabularies and determinism, and the configuration/precondition matrix.
 * @ownership Each case owns the permit, policy, config, journal storage, registry, emitter, and
 *            action path it constructs.
 * @lifetime The journal, registry, and emitter outlive the action path; snapshots are copies.
 * @thread_safety Single-threaded.
 * @bounds Finite declared tables and bounded operation sequences; no wall-clock verdict.
 * @failure A nominal action that is not `Emitted`, an unstable vocabulary entry, a
 *          non-deterministic run, or an accepted invalid configuration fails the case.
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
using xverse::xcom::OriginKind;

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr val::Timestamp kFrom = 0;
constexpr val::Timestamp kUntil = 100;

[[nodiscard]] val::SessionId session_a() {
  val::SessionId value{};
  value[0] = 1U;
  value[15] = 0x11U;
  return value;
}
[[nodiscard]] val::PlanDigest digest_a() {
  val::PlanDigest value{};
  value[0] = 2U;
  value[31] = 0x22U;
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
  builder.set_validity(kDomain, kFrom, kUntil);
  builder.add_allowed_action(val::to_mask(val::Action::Activate));
  builder.add_quota(val::Quota{val::QuotaKind::Operations, 16U});
  val::Permit permit;
  EXPECT_EQ(builder.build(permit), val::Result::Ok);
  return permit;
}

[[nodiscard]] val::StimulationPolicy make_policy(const val::Permit &permit,
                                                 std::size_t quota = 8U) {
  val::StimulationPolicy policy;
  policy.plan_digest = permit.plan_digest();
  policy.interface_tag = tag("iface.v1");
  policy.target = tag("target.alpha");
  policy.validity_domain = permit.validity_domain();
  policy.allowed_actions = val::kDefinedStimulationActions;
  policy.allowed_interactions = 0x0FU;
  policy.allowed_directions = 0x0FU;
  policy.allowed_schemas = {val::SchemaKey{tag("sig.v1"), tag("1")},
                            val::SchemaKey{tag("msg.v1"), tag("1")},
                            val::SchemaKey{tag("req.v1"), tag("1")},
                            val::SchemaKey{tag("resp.v1"), tag("1")}};
  policy.max_actions_per_session = quota;
  policy.max_actions_per_window = quota;
  policy.action_window = quota;
  policy.loop_window = quota;
  policy.allow_service_emulation = true;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return policy;
}

[[nodiscard]] val::ActionPathConfig make_config() {
  val::ActionPathConfig config;
  config.max_pending_actions = 8U;
  config.max_lineage_entries = 8U;
  config.max_drain_steps = 8U;
  config.max_payload_bytes = 64U;
  config.tool = tag("tool");
  return config;
}

[[nodiscard]] val::StimulationRequest make_request(const val::Permit &permit, std::uint64_t id,
                                                   val::StimulationAction action =
                                                       val::StimulationAction::InjectSignal) {
  val::StimulationRequest request;
  request.permit_id = permit.permit_id();
  request.session_id = permit.session_id();
  request.plan_digest = permit.plan_digest();
  request.action = action;
  switch (action) {
  case val::StimulationAction::InjectSignal:
    request.interaction = InteractionKind::signal_state_update;
    request.direction = EndpointDirection::produce;
    request.schema = val::SchemaKey{tag("sig.v1"), tag("1")};
    break;
  case val::StimulationAction::InjectMessage:
    request.interaction = InteractionKind::message_event;
    request.direction = EndpointDirection::produce;
    request.schema = val::SchemaKey{tag("msg.v1"), tag("1")};
    break;
  case val::StimulationAction::InvokeService:
    request.interaction = InteractionKind::service_request;
    request.direction = EndpointDirection::request;
    request.schema = val::SchemaKey{tag("req.v1"), tag("1")};
    request.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
    break;
  case val::StimulationAction::EmulateService:
  default:
    request.interaction = InteractionKind::service_response;
    request.direction = EndpointDirection::respond;
    request.schema = val::SchemaKey{tag("resp.v1"), tag("1")};
    request.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
    break;
  }
  request.target = tag("target.alpha");
  request.interface_tag = tag("iface.v1");
  request.clock_domain = kDomain;
  request.scheduled_at = 0;
  request.immediate = true;
  request.request_id = id;
  request.correlation_id = id + 1000U;
  request.causation_id = 0U;
  return request;
}

[[nodiscard]] val::ResolvedTime in_window() {
  return val::ResolvedTime{kDomain, 50, val::Result::Ok};
}

/// @brief In-memory journal storage seam used by the action-path matrix.
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

/// @brief Recording host emission seam; records the durable-intent order via the storage seam.
class RecordingEmitter final : public val::ActionEmitter {
public:
  val::EmissionStatus emit(const val::SyntheticStimulationItem &item,
                           std::span<const std::byte> payload) override {
    ++calls;
    last = item;
    last_payload_size = payload.size();
    durable_before_emit = storage != nullptr && storage->bytes_.size() > 0U;
    return status;
  }

  std::size_t calls{0};
  val::SyntheticStimulationItem last{};
  std::size_t last_payload_size{0};
  bool durable_before_emit{false};
  val::EmissionStatus status{val::EmissionStatus::Delivered};
  MemoryStorage *storage{nullptr};
};

/// @brief Bundle of an opened journal, registry, emitter, and action path.
struct Harness {
  MemoryStorage storage{};
  val::StimulationJournal journal{};
  val::ServiceEmulationRegistry registry{4U};
  RecordingEmitter emitter{};
  std::optional<val::StimulationActionPath> path{};

  Harness() { emitter.storage = &storage; }

  void open_journal() {
    val::JournalConfig config;
    config.max_record_bytes = 320U;
    config.max_retained_records = 32U;
    config.max_journal_bytes = 32768U;
    EXPECT_EQ(journal.open(storage, config), val::JournalStatus::Ok);
  }
  void build(const val::ActionPathConfig &config) {
    open_journal();
    path.emplace(config, journal, registry, emitter);
  }
};

} // namespace

/** T28-TS-001 (CHK-08, CHK-09): the four action kinds emit once with the intent durable first. */
TEST(XcomStimulationActionsAction, ActionPathExecutesNominalActionKinds) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  Harness harness;
  harness.build(make_config());
  ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);

  const std::array<val::StimulationAction, 4U> kinds{
      val::StimulationAction::InjectSignal, val::StimulationAction::InjectMessage,
      val::StimulationAction::InvokeService, val::StimulationAction::EmulateService};
  val::ActionDiagnostic diagnostic;
  for (std::size_t index = 0; index < kinds.size(); ++index) {
    const val::StimulationRequest request = make_request(permit, 11U + index, kinds[index]);
    ASSERT_EQ(harness.path->execute(request, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::Emitted);
    EXPECT_TRUE(harness.emitter.durable_before_emit);
  }
  EXPECT_EQ(harness.emitter.calls, 4U);
  // Only the emulation action acquires the exclusive lease.
  const val::EndpointGeneration key{permit.session_id(), tag("svc.alpha"), 3U,
                                    permit.plan_digest()};
  EXPECT_TRUE(harness.registry.holds(key));
  const val::ActionPathSnapshot snapshot = harness.path->snapshot();
  EXPECT_EQ(snapshot.emitted, 4U);
  EXPECT_EQ(snapshot.pending, 0U);
  EXPECT_EQ(harness.journal.snapshot().complete_intents, 4U);
  EXPECT_EQ(harness.journal.snapshot().outcomes, 4U);

  // T028-IR2-F03: a host Rejected/Unavailable outcome is durable but is never delivered success.
  for (const val::EmissionStatus non_delivery :
       {val::EmissionStatus::Rejected, val::EmissionStatus::Unavailable}) {
    Harness host;
    host.build(make_config());
    ASSERT_EQ(host.path->open(permit, policy), val::GuardStatus::Ok);
    host.emitter.status = non_delivery;
    val::ActionDiagnostic host_out;
    const val::ActionStatus host_status =
        host.path->execute(make_request(permit, 61U + static_cast<std::uint64_t>(non_delivery)),
                           val::LifecycleState::active, in_window(), {}, host_out);
    EXPECT_EQ(host_out.emission_status, non_delivery);
    const val::ActionPathSnapshot host_snapshot = host.path->snapshot();
    EXPECT_EQ(host_snapshot.emitted, 0U);
    if (non_delivery == val::EmissionStatus::Rejected) {
      EXPECT_EQ(host_status, val::ActionStatus::EmissionRejected);
      EXPECT_EQ(host_snapshot.emission_rejected, 1U);
    } else {
      EXPECT_EQ(host_status, val::ActionStatus::EmissionUnavailable);
      EXPECT_EQ(host_snapshot.emission_unavailable, 1U);
    }
  }
}

/** T28-TS-002 (CHK-07): every guard decline maps to a bounded non-emitting status. */
TEST(XcomStimulationActionsAction, ActionPathGuardDecisionMapping) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  Harness harness;
  harness.build(make_config());
  ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
  val::ActionDiagnostic diagnostic;

  const auto declines = [&](val::StimulationRequest request, val::LifecycleState state,
                            val::ResolvedTime time, val::ActionStatus status,
                            val::GuardReason reason) {
    const std::size_t before_calls = harness.emitter.calls;
    const val::JournalSnapshot before_journal = harness.journal.snapshot();
    const val::LeaseSnapshot before_leases = harness.registry.snapshot();
    EXPECT_EQ(harness.path->execute(request, state, time, {}, diagnostic), status);
    EXPECT_EQ(diagnostic.guard_reason, reason);
    EXPECT_EQ(harness.emitter.calls, before_calls);
    EXPECT_EQ(harness.journal.snapshot(), before_journal);
    // A guard decline acquires no lease: the whole lease table, including its acquisition and
    // release accounting, is byte-identical (T028-IR2-F01).
    EXPECT_EQ(harness.registry.snapshot(), before_leases);
  };

  {
    val::StimulationRequest request = make_request(permit, 21U);
    request.target = tag("target.beta");
    declines(request, val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
             val::GuardReason::TargetMismatch);
  }
  {
    // A guard-declined EmulateService action must not acquire and release a lease.
    val::StimulationRequest request =
        make_request(permit, 31U, val::StimulationAction::EmulateService);
    request.target = tag("target.beta");
    declines(request, val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
             val::GuardReason::TargetMismatch);
    EXPECT_EQ(harness.registry.snapshot().active, 0U);
    EXPECT_EQ(harness.registry.snapshot().released, 0U);
    EXPECT_EQ(harness.registry.snapshot().acquisitions, 0U);
  }
  {
    val::StimulationRequest request = make_request(permit, 22U);
    request.schema = val::SchemaKey{tag("sig.v1"), tag("9")};
    declines(request, val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
             val::GuardReason::SchemaMismatch);
  }
  {
    val::StimulationRequest request = make_request(permit, 23U);
    request.direction = EndpointDirection::consume;
    declines(request, val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
             val::GuardReason::DirectionMismatch);
  }
  {
    val::StimulationRequest request = make_request(permit, 24U);
    request.interaction = InteractionKind::message_event;
    declines(request, val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
             val::GuardReason::InteractionMismatch);
  }
  {
    val::StimulationPolicy signal_only = policy;
    signal_only.allowed_actions = val::to_stimulation_mask(val::StimulationAction::InjectSignal);
    Harness narrow;
    narrow.build(make_config());
    ASSERT_EQ(narrow.path->open(permit, signal_only), val::GuardStatus::Ok);
    val::ActionDiagnostic narrow_diagnostic;
    EXPECT_EQ(narrow.path->execute(make_request(permit, 25U, val::StimulationAction::InjectMessage),
                                   val::LifecycleState::active, in_window(), {}, narrow_diagnostic),
              val::ActionStatus::Rejected);
    EXPECT_EQ(narrow_diagnostic.guard_reason, val::GuardReason::ActionMismatch);
    EXPECT_EQ(narrow.emitter.calls, 0U);
  }
  {
    val::StimulationRequest request = make_request(permit, 26U);
    request.permit_id[0] ^= 0xFFU;
    declines(request, val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
             val::GuardReason::PermitMismatch);
  }
  {
    val::StimulationRequest request = make_request(permit, 27U, val::StimulationAction::InvokeService);
    request.service_owner.declared = false;
    declines(request, val::LifecycleState::active, in_window(), val::ActionStatus::Rejected,
             val::GuardReason::OwnershipConflict);
  }
  declines(make_request(permit, 28U), val::LifecycleState::active,
           val::ResolvedTime{kDomain, 50, val::Result::MissingMapping}, val::ActionStatus::Failed,
           val::GuardReason::TimeUnmapped);
  declines(make_request(permit, 29U), val::LifecycleState::active,
           val::ResolvedTime{kDomain, kUntil, val::Result::Ok}, val::ActionStatus::Rejected,
           val::GuardReason::TimeOutOfWindow);
  declines(make_request(permit, 30U), val::LifecycleState::armed, in_window(),
           val::ActionStatus::NotActive, val::GuardReason::None);
}

/** T28-TS-003 (CHK-09, NEG-08): the emitted descriptor carries synthetic identity exactly. */
TEST(XcomStimulationActionsAction, ActionPathSyntheticProvenance) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  Harness harness;
  harness.build(make_config());
  ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);

  val::StimulationRequest request = make_request(permit, 41U);
  request.correlation_id = 9001U;
  request.causation_id = 7001U;
  val::ActionDiagnostic diagnostic;
  ASSERT_EQ(harness.path->execute(request, val::LifecycleState::active, in_window(), {},
                                  diagnostic),
            val::ActionStatus::Emitted);

  EXPECT_EQ(harness.emitter.calls, 1U);
  EXPECT_EQ(harness.emitter.last.origin, OriginKind::validation_tool);
  const val::StimulationIntent &intent = harness.emitter.last.intent;
  EXPECT_EQ(intent.permit_id, permit.permit_id());
  EXPECT_EQ(intent.session_id, permit.session_id());
  EXPECT_EQ(intent.plan_digest, permit.plan_digest());
  EXPECT_EQ(intent.request_id, 41U);
  EXPECT_EQ(intent.correlation_id, 9001U);
  EXPECT_EQ(intent.causation_id, 7001U);
  EXPECT_EQ(intent.target.value(), "target.alpha");
  EXPECT_EQ(intent.tool.value(), "tool");
  EXPECT_EQ(intent.action_mask, val::to_stimulation_mask(val::StimulationAction::InjectSignal));
  EXPECT_TRUE(intent.immediate);
  const std::vector<val::StimulationIntent> recovered = harness.journal.recovered_intents();
  ASSERT_EQ(recovered.size(), 1U);
  EXPECT_EQ(recovered.front(), intent);
}

/** T28-TS-004 (CHK-17, NEG-28): closed stable vocabularies and three identical runs. */
TEST(XcomStimulationActionsAction, ActionPathVocabularyAndDeterminism) {
  constexpr std::array<val::ActionStatus, 15U> actions{
      val::ActionStatus::Emitted,        val::ActionStatus::Rejected,
      val::ActionStatus::Failed,         val::ActionStatus::LeaseConflict,
      val::ActionStatus::Queued,         val::ActionStatus::Cancelled,
      val::ActionStatus::Expired,        val::ActionStatus::EvidenceIncomplete,
      val::ActionStatus::JournalFailed,  val::ActionStatus::CapacityExhausted,
      val::ActionStatus::NotActive,      val::ActionStatus::NotOpen,
      val::ActionStatus::RejectedConfiguration, val::ActionStatus::EmissionRejected,
      val::ActionStatus::EmissionUnavailable};
  constexpr std::array<std::string_view, 15U> action_names{
      "Emitted",       "Rejected",        "Failed",       "LeaseConflict", "Queued",
      "Cancelled",     "Expired",         "EvidenceIncomplete", "JournalFailed",
      "CapacityExhausted", "NotActive",   "NotOpen",      "RejectedConfiguration",
      "EmissionRejected", "EmissionUnavailable"};
  for (std::size_t index = 0; index < actions.size(); ++index) {
    EXPECT_EQ(val::action_status_name(actions[index]), action_names[index]);
    EXPECT_EQ(val::precedence_rank(actions[index]), static_cast<std::uint8_t>(index));
  }
  EXPECT_EQ(val::action_status_name(static_cast<val::ActionStatus>(200U)), std::string_view{});

  constexpr std::array<val::LeaseStatus, 12U> leases{
      val::LeaseStatus::Ok,          val::LeaseStatus::Conflict,
      val::LeaseStatus::NotFound,    val::LeaseStatus::NotHeld,
      val::LeaseStatus::AlreadyReleased, val::LeaseStatus::SessionMismatch,
      val::LeaseStatus::GenerationMismatch, val::LeaseStatus::PlanMismatch,
      val::LeaseStatus::Expired,     val::LeaseStatus::Quarantined,
      val::LeaseStatus::CapacityExhausted, val::LeaseStatus::RejectedConfiguration};
  constexpr std::array<std::string_view, 12U> lease_names{
      "Ok", "Conflict", "NotFound", "NotHeld", "AlreadyReleased", "SessionMismatch",
      "GenerationMismatch", "PlanMismatch", "Expired", "Quarantined", "CapacityExhausted",
      "RejectedConfiguration"};
  for (std::size_t index = 0; index < leases.size(); ++index) {
    EXPECT_EQ(val::lease_status_name(leases[index]), lease_names[index]);
    EXPECT_EQ(val::precedence_rank(leases[index]), static_cast<std::uint8_t>(index));
  }
  EXPECT_EQ(val::lease_state_name(val::LeaseState::Active), "Active");
  EXPECT_EQ(val::lease_state_name(val::LeaseState::Quarantined), "Quarantined");
  EXPECT_EQ(val::ordering_rule_name(val::OrderingRule::ScheduledThenArrival),
            "ScheduledThenArrival");
  EXPECT_EQ(val::late_item_policy_name(val::LateItemPolicy::DiscardLate), "DiscardLate");
  EXPECT_EQ(val::drain_state_name(val::DrainState::Cancelled), "Cancelled");
  EXPECT_EQ(val::emission_status_name(val::EmissionStatus::Unavailable), "Unavailable");
  EXPECT_EQ(val::completion_outcome_name(val::CompletionOutcome::EvidenceIncomplete),
            "EvidenceIncomplete");
  EXPECT_EQ(val::quarantine_reason_name(val::QuarantineReason::Disconnect), "Disconnect");

  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  std::vector<std::pair<val::ActionStatus, val::GuardReason>> golden;
  val::ActionPathSnapshot golden_snapshot;
  for (std::size_t run = 0; run < 3U; ++run) {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    std::vector<std::pair<val::ActionStatus, val::GuardReason>> sequence;
    sequence.emplace_back(
        harness.path->execute(make_request(permit, 51U), val::LifecycleState::active, in_window(),
                              {}, diagnostic),
        diagnostic.guard_reason);
    {
      val::StimulationRequest rejected = make_request(permit, 52U);
      rejected.target = tag("target.beta");
      sequence.emplace_back(harness.path->execute(rejected, val::LifecycleState::active,
                                                  in_window(), {}, diagnostic),
                            diagnostic.guard_reason);
    }
    sequence.emplace_back(
        harness.path->execute(make_request(permit, 53U, val::StimulationAction::InjectMessage),
                              val::LifecycleState::active, in_window(), {}, diagnostic),
        diagnostic.guard_reason);
    if (run == 0U) {
      golden = sequence;
      golden_snapshot = harness.path->snapshot();
    } else {
      EXPECT_EQ(sequence, golden);
      EXPECT_EQ(harness.path->snapshot(), golden_snapshot);
    }
  }
}

/** T28-TS-005 (CHK-06, CHK-18): every configuration and precondition row. */
TEST(XcomStimulationActionsAction, ActionPathConfigAndPreconditionMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);

  const auto rejects = [&](const val::ActionPathConfig &config) {
    Harness harness;
    harness.build(config);
    EXPECT_EQ(harness.path->open(permit, policy), val::GuardStatus::RejectedConfiguration);
    EXPECT_FALSE(harness.path->is_open());
    EXPECT_EQ(harness.path->snapshot(), (val::ActionPathSnapshot{}));
  };
  {
    Harness harness;
    harness.build(make_config());
    EXPECT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    EXPECT_TRUE(harness.path->is_open());
  }
  { auto config = make_config(); config.max_pending_actions = 0U; rejects(config); }
  {
    auto config = make_config();
    config.max_pending_actions = val::kActionPathMaxPendingActions + 1U;
    rejects(config);
  }
  { auto config = make_config(); config.max_lineage_entries = 0U; rejects(config); }
  {
    auto config = make_config();
    config.max_lineage_entries = val::kActionPathMaxLineage + 1U;
    rejects(config);
  }
  { auto config = make_config(); config.max_drain_steps = 0U; rejects(config); }
  {
    auto config = make_config();
    config.max_drain_steps = val::kActionPathMaxDrainSteps + 1U;
    rejects(config);
  }
  { auto config = make_config(); config.max_payload_bytes = 0U; rejects(config); }
  {
    auto config = make_config();
    config.max_payload_bytes = val::kActionPathMaxPayloadBytes + 1U;
    rejects(config);
  }
  { auto config = make_config(); config.tool = val::Tag{}; rejects(config); }

  EXPECT_THROW((val::ServiceEmulationRegistry{0U}), std::invalid_argument);
  EXPECT_THROW((val::ServiceEmulationRegistry{val::kActionPathMaxActiveLeases + 1U}),
               std::invalid_argument);

  // A malformed request consumes no guard quota: a later valid request is still emitted.
  {
    const val::StimulationPolicy quota_one = make_policy(permit, 1U);
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, quota_one), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(harness.path->execute(make_request(permit, 0U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::RejectedConfiguration);
    EXPECT_EQ(harness.emitter.calls, 0U);
    EXPECT_EQ(harness.path->execute(make_request(permit, 61U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
  }
  // A non-active session consumes no guard quota.
  {
    const val::StimulationPolicy quota_one = make_policy(permit, 1U);
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, quota_one), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(harness.path->execute(make_request(permit, 62U), val::LifecycleState::armed,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::NotActive);
    EXPECT_EQ(harness.path->execute(make_request(permit, 63U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
  }
  // A capacity decline consumes no guard quota.
  {
    val::ActionPathConfig config = make_config();
    config.max_pending_actions = 1U;
    const val::StimulationPolicy quota_two = make_policy(permit, 2U);
    Harness harness;
    harness.build(config);
    ASSERT_EQ(harness.path->open(permit, quota_two), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    val::StimulationRequest scheduled = make_request(permit, 64U);
    scheduled.immediate = false;
    scheduled.scheduled_at = 10;
    ASSERT_EQ(harness.path->execute(scheduled, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::Queued);
    val::StimulationRequest second = make_request(permit, 65U);
    second.immediate = false;
    second.scheduled_at = 20;
    EXPECT_EQ(harness.path->execute(second, val::LifecycleState::active, in_window(), {},
                                    diagnostic),
              val::ActionStatus::CapacityExhausted);
    EXPECT_EQ(harness.path->execute(make_request(permit, 66U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::Emitted);
  }
  // A closed path evaluates nothing and consumes no quota.
  {
    Harness harness;
    harness.build(make_config());
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(harness.path->execute(make_request(permit, 67U), val::LifecycleState::active,
                                    in_window(), {}, diagnostic),
              val::ActionStatus::NotOpen);
    EXPECT_EQ(harness.emitter.calls, 0U);
  }
  // An over-bound payload view is rejected before any state work.
  {
    Harness harness;
    harness.build(make_config());
    ASSERT_EQ(harness.path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    std::vector<std::byte> payload(make_config().max_payload_bytes + 1U);
    EXPECT_EQ(harness.path->execute(make_request(permit, 68U), val::LifecycleState::active,
                                    in_window(), payload, diagnostic),
              val::ActionStatus::RejectedConfiguration);
    EXPECT_EQ(harness.emitter.calls, 0U);
  }
}
