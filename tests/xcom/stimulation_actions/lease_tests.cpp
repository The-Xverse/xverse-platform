/**
 * @file lease_tests.cpp
 * @brief T028 exclusive generation-bound service-emulation lease matrix: identity binding,
 *        conflict and capacity, release and quarantine, expiry and clock domain, and generation
 *        supersession.
 * @ownership Each case owns the registry, permit, policy, journal storage, emitter, action path,
 *            and the lease values it constructs.
 * @lifetime The registry outlives every caller; leases are values.
 * @thread_safety Single-threaded.
 * @bounds Finite declared lease tables and bounded operation sequences; no wall-clock verdict.
 * @failure A foreign or superseded identity that acquires a lease, a conflicting acquisition that
 *          mutates an entry, or a lease that remains active after expiry fails the case.
 */

#include "xverse/xcom/stimulation_actions.hpp"

#include <gtest/gtest.h>

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

[[nodiscard]] val::SessionId session_a() {
  val::SessionId value{};
  value[0] = 1U;
  return value;
}
[[nodiscard]] val::SessionId session_b() {
  val::SessionId value{};
  value[0] = 2U;
  return value;
}
[[nodiscard]] val::PlanDigest digest_a() {
  val::PlanDigest value{};
  value[0] = 3U;
  return value;
}
[[nodiscard]] val::PlanDigest digest_b() {
  val::PlanDigest value{};
  value[0] = 4U;
  return value;
}
[[nodiscard]] val::Tag tag(std::string_view text) { return val::Tag::make(text).value(); }

[[nodiscard]] val::EndpointGeneration key(val::SessionId session, std::string_view endpoint,
                                          val::Generation generation, val::PlanDigest digest) {
  val::EndpointGeneration value;
  value.session = session;
  value.endpoint = tag(endpoint);
  value.generation = generation;
  value.plan_digest = digest;
  return value;
}

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
  builder.set_validity(kDomain, 0, 100);
  builder.add_allowed_action(val::to_mask(val::Action::Activate));
  builder.add_quota(val::Quota{val::QuotaKind::Operations, 16U});
  val::Permit permit;
  EXPECT_EQ(builder.build(permit), val::Result::Ok);
  return permit;
}

[[nodiscard]] val::StimulationPolicy make_policy(const val::Permit &permit,
                                                 val::Generation generation = 3U,
                                                 std::size_t quota = 8U) {
  val::StimulationPolicy policy;
  policy.plan_digest = permit.plan_digest();
  policy.interface_tag = tag("iface.v1");
  policy.target = tag("target.alpha");
  policy.validity_domain = permit.validity_domain();
  policy.allowed_actions = val::kDefinedStimulationActions;
  policy.allowed_interactions = 0x0FU;
  policy.allowed_directions = 0x0FU;
  policy.allowed_schemas = {val::SchemaKey{tag("resp.v1"), tag("1")}};
  policy.max_actions_per_session = quota;
  policy.max_actions_per_window = quota;
  policy.action_window = quota;
  policy.loop_window = quota;
  policy.allow_service_emulation = true;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), generation, true};
  return policy;
}

[[nodiscard]] val::StimulationRequest make_emulate(const val::Permit &permit, std::uint64_t id,
                                                   val::Generation generation = 3U) {
  val::StimulationRequest request;
  request.permit_id = permit.permit_id();
  request.session_id = permit.session_id();
  request.plan_digest = permit.plan_digest();
  request.action = val::StimulationAction::EmulateService;
  request.interaction = InteractionKind::service_response;
  request.direction = EndpointDirection::respond;
  request.schema = val::SchemaKey{tag("resp.v1"), tag("1")};
  request.target = tag("target.alpha");
  request.interface_tag = tag("iface.v1");
  request.service_owner = val::ServiceOwner{tag("svc.alpha"), generation, true};
  request.clock_domain = kDomain;
  request.scheduled_at = 0;
  request.immediate = true;
  request.request_id = id;
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

class NullEmitter final : public val::ActionEmitter {
public:
  val::EmissionStatus emit(const val::SyntheticStimulationItem &,
                           std::span<const std::byte>) override {
    ++calls;
    return val::EmissionStatus::Delivered;
  }
  std::size_t calls{0};
};

} // namespace

/** T28-TS-006 (CHK-10): the lease key binds session, endpoint, generation, and plan digest. */
TEST(XcomStimulationActionsLease, LeaseAcquireIdentityBindingMatrix) {
  val::ServiceEmulationRegistry registry{8U};
  const val::EndpointGeneration base = key(session_a(), "svc.alpha", 3U, digest_a());
  ASSERT_EQ(registry.acquire(base, 10U, kDomain, 0, 50), val::LeaseStatus::Ok);
  EXPECT_TRUE(registry.holds(base));
  EXPECT_EQ(registry.state_of(base), val::LeaseState::Active);

  EXPECT_EQ(registry.acquire(base, 11U, kDomain, 0, 50), val::LeaseStatus::Conflict);

  const val::EndpointGeneration foreign_plan =
      key(session_a(), "svc.alpha", 3U, digest_b());
  EXPECT_EQ(registry.acquire(foreign_plan, 12U, kDomain, 0, 50), val::LeaseStatus::PlanMismatch);

  const val::EndpointGeneration foreign_session =
      key(session_b(), "svc.alpha", 3U, digest_a());
  EXPECT_EQ(registry.acquire(foreign_session, 13U, kDomain, 0, 50),
            val::LeaseStatus::SessionMismatch);

  const val::EndpointGeneration superseded = key(session_a(), "svc.alpha", 4U, digest_a());
  EXPECT_EQ(registry.acquire(superseded, 14U, kDomain, 0, 50),
            val::LeaseStatus::GenerationMismatch);

  const val::EndpointGeneration other_endpoint =
      key(session_a(), "svc.beta", 3U, digest_a());
  EXPECT_EQ(registry.acquire(other_endpoint, 15U, kDomain, 0, 50), val::LeaseStatus::Ok);

  // A malformed key is rejected without mutating the table.
  const val::LeaseSnapshot before = registry.snapshot();
  val::EndpointGeneration malformed = key(session_a(), "svc.alpha", 9U, digest_a());
  malformed.session.fill(0U);
  EXPECT_EQ(registry.acquire(malformed, 16U, kDomain, 0, 50),
            val::LeaseStatus::RejectedConfiguration);
  EXPECT_EQ(registry.snapshot(), before);
}

/** T28-TS-007 (CHK-11): same-generation conflict and the active-lease capacity bound. */
TEST(XcomStimulationActionsLease, LeaseConflictAndCapacityMatrix) {
  {
    val::ServiceEmulationRegistry registry{1U};
    ASSERT_EQ(registry.acquire(key(session_a(), "svc.alpha", 3U, digest_a()), 1U, kDomain, 0, 50),
              val::LeaseStatus::Ok);
    const val::LeaseSnapshot before = registry.snapshot();
    EXPECT_EQ(registry.acquire(key(session_a(), "svc.beta", 3U, digest_a()), 2U, kDomain, 0, 50),
              val::LeaseStatus::CapacityExhausted);
    EXPECT_EQ(registry.snapshot(), before);
    EXPECT_EQ(registry.capacity(), 1U);
  }
  {
    val::ServiceEmulationRegistry registry{2U};
    ASSERT_EQ(registry.acquire(key(session_a(), "svc.alpha", 3U, digest_a()), 1U, kDomain, 0, 50),
              val::LeaseStatus::Ok);
    ASSERT_EQ(registry.acquire(key(session_a(), "svc.beta", 3U, digest_a()), 2U, kDomain, 0, 50),
              val::LeaseStatus::Ok);
    EXPECT_EQ(registry.acquire(key(session_a(), "svc.gamma", 3U, digest_a()), 3U, kDomain, 0, 50),
              val::LeaseStatus::CapacityExhausted);
    EXPECT_EQ(registry.snapshot().active, 2U);
    EXPECT_EQ(registry.snapshot().conflicts, 0U);
  }
}

/** T28-TS-008 (CHK-12): exact-owner release, unknown/already-released, and quarantine. */
TEST(XcomStimulationActionsLease, LeaseReleaseQuarantineMatrix) {
  val::ServiceEmulationRegistry registry{4U};
  const val::EndpointGeneration a = key(session_a(), "svc.alpha", 3U, digest_a());
  const val::EndpointGeneration b = key(session_a(), "svc.beta", 3U, digest_a());
  ASSERT_EQ(registry.acquire(a, 5U, kDomain, 0, 50), val::LeaseStatus::Ok);
  ASSERT_EQ(registry.acquire(b, 6U, kDomain, 0, 50), val::LeaseStatus::Ok);

  EXPECT_EQ(registry.release(a, 6U), val::LeaseStatus::NotHeld);
  EXPECT_EQ(registry.state_of(a), val::LeaseState::Active);
  EXPECT_EQ(registry.release(a, 5U), val::LeaseStatus::Ok);
  EXPECT_EQ(registry.state_of(a), val::LeaseState::Released);
  EXPECT_EQ(registry.release(a, 5U), val::LeaseStatus::AlreadyReleased);
  EXPECT_EQ(registry.release(key(session_a(), "svc.unknown", 3U, digest_a()), 5U),
            val::LeaseStatus::NotFound);

  EXPECT_EQ(registry.quarantine(b, val::QuarantineReason::Conflict), val::LeaseStatus::Ok);
  EXPECT_EQ(registry.state_of(b), val::LeaseState::Quarantined);
  EXPECT_EQ(registry.holds(b), false);
  EXPECT_EQ(registry.quarantine(b, val::QuarantineReason::Disconnect), val::LeaseStatus::NotHeld);
  EXPECT_EQ(registry.quarantine(key(session_a(), "svc.unknown", 3U, digest_a()),
                                val::QuarantineReason::Conflict),
            val::LeaseStatus::NotFound);

  // A released lease no longer blocks a new acquisition for the same key.
  EXPECT_EQ(registry.acquire(a, 7U, kDomain, 0, 50), val::LeaseStatus::Ok);
  EXPECT_TRUE(registry.holds(a));
}

/** T28-TS-009 (CHK-13, NEG-23): an elapsed lease becomes inactive and foreign domains are not ordered. */
TEST(XcomStimulationActionsLease, LeaseExpiryAndDomainMatrix) {
  val::ServiceEmulationRegistry registry{4U};
  const val::EndpointGeneration a = key(session_a(), "svc.alpha", 3U, digest_a());
  const val::EndpointGeneration b = key(session_a(), "svc.beta", 3U, digest_a());
  ASSERT_EQ(registry.acquire(a, 1U, kDomain, 0, 50), val::LeaseStatus::Ok);
  ASSERT_EQ(registry.acquire(b, 2U, kForeignDomain, 0, 50), val::LeaseStatus::Ok);

  EXPECT_EQ(registry.expire_elapsed(kDomain, 40), 0U);
  EXPECT_EQ(registry.state_of(a), val::LeaseState::Active);
  EXPECT_TRUE(registry.holds(a));

  // Only the declared domain is compared; the foreign-domain entry is untouched.
  EXPECT_EQ(registry.expire_elapsed(kDomain, 50), 1U);
  EXPECT_EQ(registry.state_of(a), val::LeaseState::Expired);
  EXPECT_FALSE(registry.holds(a));
  EXPECT_EQ(registry.state_of(b), val::LeaseState::Active);

  EXPECT_EQ(registry.expire_elapsed(kForeignDomain, 100), 1U);
  EXPECT_EQ(registry.state_of(b), val::LeaseState::Expired);

  // An expired lease no longer blocks a later acquisition for the generation.
  EXPECT_EQ(registry.acquire(a, 3U, kDomain, 60, 70), val::LeaseStatus::Ok);
}

/** T28-TS-010 (CHK-10, CHK-12): a superseded generation neither authorizes nor conflict-blocks. */
TEST(XcomStimulationActionsLease, LeaseGenerationSupersessionMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit, 3U);
  MemoryStorage storage;
  val::StimulationJournal journal;
  val::JournalConfig journal_config;
  journal_config.max_retained_records = 16U;
  ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
  val::ServiceEmulationRegistry registry{4U};
  NullEmitter emitter;
  val::ActionPathConfig config;
  config.max_pending_actions = 4U;
  config.max_lineage_entries = 4U;
  config.max_drain_steps = 4U;
  config.tool = tag("tool");
  val::StimulationActionPath path{config, journal, registry, emitter};
  ASSERT_EQ(path.open(permit, policy), val::GuardStatus::Ok);

  const val::EndpointGeneration generation_n = key(session_a(), "svc.alpha", 3U, digest_a());
  val::ActionDiagnostic diagnostic;
  ASSERT_EQ(path.execute(make_emulate(permit, 71U, 3U), val::LifecycleState::active, in_window(),
                         {}, diagnostic),
            val::ActionStatus::Emitted);
  EXPECT_TRUE(registry.holds(generation_n));

  // T028-IR2-F02: a second emulation request for the already-held endpoint generation is rejected
  // as a conflict and must never emit as a second owner under a lease it does not own.
  {
    const std::size_t before_calls = emitter.calls;
    const val::LeaseSnapshot before_leases = registry.snapshot();
    EXPECT_EQ(path.execute(make_emulate(permit, 74U, 3U), val::LifecycleState::active, in_window(),
                           {}, diagnostic),
              val::ActionStatus::LeaseConflict);
    EXPECT_EQ(diagnostic.lease_status, val::LeaseStatus::Conflict);
    EXPECT_EQ(emitter.calls, before_calls);
    EXPECT_EQ(registry.snapshot(), before_leases);
    EXPECT_EQ(registry.snapshot().acquisitions, 1U);
    EXPECT_TRUE(registry.holds(generation_n));
  }

  // A request under generation n+1 is rejected as a lease conflict before any guard quota is used.
  const val::JournalSnapshot before_journal = journal.snapshot();
  const std::size_t before_calls = emitter.calls;
  EXPECT_EQ(path.execute(make_emulate(permit, 72U, 4U), val::LifecycleState::active, in_window(),
                         {}, diagnostic),
            val::ActionStatus::LeaseConflict);
  EXPECT_EQ(diagnostic.lease_status, val::LeaseStatus::GenerationMismatch);
  EXPECT_EQ(emitter.calls, before_calls);
  EXPECT_EQ(journal.snapshot(), before_journal);

  // Releasing generation n makes generation n+1 acquirable.
  ASSERT_EQ(registry.release(generation_n, 71U), val::LeaseStatus::Ok);
  const val::EndpointGeneration generation_next = key(session_a(), "svc.alpha", 4U, digest_a());
  EXPECT_EQ(registry.acquire(generation_next, 73U, kDomain, 50, 90), val::LeaseStatus::Ok);
  EXPECT_TRUE(registry.holds(generation_next));
}
