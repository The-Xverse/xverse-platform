/**
 * @file concurrency_tests.cpp
 * @brief T028 bounded deterministic concurrency: a declared guard quota under four threads, and
 *        a concurrent exclusive-lease race with exactly one winner.
 * @ownership Each case owns the permit, policy, config, journal storage, registry, emitter,
 *            action path, joined threads, and the golden sequence.
 * @lifetime Every thread is joined before its harness is destroyed.
 * @thread_safety ≤ 4 threads; the guard and registry each serialize their own state.
 * @bounds ≤ 4 threads, ≤ 16 evaluations per thread, 3 repeated runs, no wall-clock verdict.
 * @failure More than the declared quota emitted, two lease winners, or non-deterministic
 *          repeated runs fails the case.
 */

#include "xverse/xcom/stimulation_actions.hpp"

#include <gtest/gtest.h>

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <thread>
#include <utility>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;
using xverse::xcom::OriginKind;

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr std::size_t kThreads = 4U;
constexpr std::size_t kPerThread = 16U;
constexpr std::size_t kQuota = 7U;

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
  builder.set_validity(kDomain, 0, 100);
  builder.add_allowed_action(val::to_mask(val::Action::Activate));
  builder.add_quota(val::Quota{val::QuotaKind::Operations, 16U});
  val::Permit permit;
  EXPECT_EQ(builder.build(permit), val::Result::Ok);
  return permit;
}

[[nodiscard]] val::StimulationPolicy make_policy(const val::Permit &permit) {
  val::StimulationPolicy policy;
  policy.plan_digest = permit.plan_digest();
  policy.interface_tag = tag("iface.v1");
  policy.target = tag("target.alpha");
  policy.validity_domain = permit.validity_domain();
  policy.allowed_actions = val::kDefinedStimulationActions;
  policy.allowed_interactions = 0x0FU;
  policy.allowed_directions = 0x0FU;
  policy.allowed_schemas = {val::SchemaKey{tag("sig.v1"), tag("1")}};
  policy.max_actions_per_session = kQuota;
  policy.max_actions_per_window = kQuota;
  policy.action_window = kQuota;
  policy.loop_window = kQuota;
  policy.allow_service_emulation = true;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return policy;
}

[[nodiscard]] val::StimulationRequest make_signal(const val::Permit &permit, std::uint64_t id) {
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
  request.clock_domain = kDomain;
  request.immediate = true;
  request.request_id = id;
  return request;
}

class MemoryStorage final : public val::StimulationJournal::Storage {
public:
  val::JournalStatus append(std::span<const std::uint8_t> bytes) override {
    std::lock_guard<std::mutex> lock(mutex_);
    bytes_.insert(bytes_.end(), bytes.begin(), bytes.end());
    return val::JournalStatus::Ok;
  }
  val::JournalStatus sync() override { return val::JournalStatus::Ok; }
  val::JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    std::lock_guard<std::mutex> lock(mutex_);
    out = bytes_;
    return val::JournalStatus::Ok;
  }
  [[nodiscard]] std::size_t size() override {
    std::lock_guard<std::mutex> lock(mutex_);
    return bytes_.size();
  }
  val::JournalStatus truncate(std::size_t size) override {
    std::lock_guard<std::mutex> lock(mutex_);
    bytes_.resize(size);
    return val::JournalStatus::Ok;
  }

  std::mutex mutex_{};
  std::vector<std::uint8_t> bytes_{};
};

/// @brief Thread-safe counting host emission seam.
class CountingEmitter final : public val::ActionEmitter {
public:
  val::EmissionStatus emit(const val::SyntheticStimulationItem &item,
                           std::span<const std::byte>) override {
    calls.fetch_add(1U, std::memory_order_relaxed);
    if (item.origin != OriginKind::validation_tool) {
      foreign_origin.fetch_add(1U, std::memory_order_relaxed);
    }
    return val::EmissionStatus::Delivered;
  }

  std::atomic<std::size_t> calls{0U};
  std::atomic<std::size_t> foreign_origin{0U};
};

/// @brief Result of one bounded concurrent run.
struct RunResult {
  std::size_t emitted{0};
  std::size_t rejected{0};
  bool operator==(const RunResult &) const = default;
};

/// @brief Runs four threads submitting bounded immediate actions to one action path.
[[nodiscard]] RunResult run_concurrent_actions() {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  MemoryStorage storage;
  val::StimulationJournal journal;
  val::JournalConfig journal_config;
  journal_config.max_retained_records = 32U;
  journal_config.max_journal_bytes = 32768U;
  EXPECT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
  val::ServiceEmulationRegistry registry{4U};
  CountingEmitter emitter;
  val::ActionPathConfig config;
  config.max_pending_actions = 8U;
  config.max_lineage_entries = 16U;
  config.max_drain_steps = 8U;
  config.tool = tag("tool");
  val::StimulationActionPath path{config, journal, registry, emitter};
  EXPECT_EQ(path.open(permit, policy), val::GuardStatus::Ok);

  std::atomic<std::size_t> emitted{0U};
  std::atomic<std::size_t> rejected{0U};
  std::array<std::thread, kThreads> threads;
  for (std::size_t thread = 0; thread < kThreads; ++thread) {
    threads[thread] = std::thread([&, thread]() {
      for (std::size_t index = 0; index < kPerThread; ++index) {
        const std::uint64_t id = 1U + thread * kPerThread + index;
        val::ActionDiagnostic diagnostic;
        const val::ActionStatus status =
            path.execute(make_signal(permit, id), val::LifecycleState::active,
                         val::ResolvedTime{kDomain, 50, val::Result::Ok}, {}, diagnostic);
        if (status == val::ActionStatus::Emitted) {
          emitted.fetch_add(1U, std::memory_order_relaxed);
        } else if (status == val::ActionStatus::Rejected) {
          rejected.fetch_add(1U, std::memory_order_relaxed);
        }
      }
    });
  }
  for (std::thread &thread : threads) {
    thread.join();
  }
  EXPECT_EQ(emitter.foreign_origin.load(), 0U);
  EXPECT_EQ(emitter.calls.load(), kQuota);
  RunResult result;
  result.emitted = emitted.load();
  result.rejected = rejected.load();
  EXPECT_EQ(result.emitted, kQuota);
  EXPECT_EQ(result.rejected, kThreads * kPerThread - kQuota);
  EXPECT_EQ(path.snapshot().emitted, kQuota);
  return result;
}

} // namespace

/** T28-TS-019 (CHK-18, NEG-29, NEG-36): a declared guard quota holds under four threads. */
TEST(XcomStimulationActionsConcurrency, ActionPathBoundedDeterministicConcurrency) {
  RunResult golden;
  for (std::size_t run = 0; run < 3U; ++run) {
    const RunResult result = run_concurrent_actions();
    if (run == 0U) {
      golden = result;
    } else {
      EXPECT_EQ(result, golden);
    }
  }
  EXPECT_EQ(golden.emitted, kQuota);
}

/** T28-TS-020 (CHK-11, CHK-18, NEG-11, NEG-29): one endpoint generation has exactly one winner. */
TEST(XcomStimulationActionsConcurrency, LeaseConcurrentRaceSingleWinner) {
  val::ServiceEmulationRegistry registry{4U};
  val::EndpointGeneration key;
  key.session = session_a();
  key.endpoint = tag("svc.alpha");
  key.generation = 3U;
  key.plan_digest = digest_a();

  std::atomic<std::size_t> winners{0U};
  std::atomic<std::size_t> losers{0U};
  std::array<std::thread, kThreads> threads;
  for (std::size_t thread = 0; thread < kThreads; ++thread) {
    threads[thread] = std::thread([&, thread]() {
      for (std::size_t index = 0; index < kPerThread; ++index) {
        const val::LeaseStatus status =
            registry.acquire(key, 1U + thread * kPerThread + index, kDomain, 0, 100);
        if (status == val::LeaseStatus::Ok) {
          winners.fetch_add(1U, std::memory_order_relaxed);
        } else if (status == val::LeaseStatus::Conflict) {
          losers.fetch_add(1U, std::memory_order_relaxed);
        }
      }
    });
  }
  for (std::thread &thread : threads) {
    thread.join();
  }
  EXPECT_EQ(winners.load(), 1U);
  EXPECT_EQ(losers.load(), kThreads * kPerThread - 1U);
  const val::LeaseSnapshot snapshot = registry.snapshot();
  EXPECT_EQ(snapshot.active, 1U);
  EXPECT_EQ(snapshot.acquisitions, 1U);
  EXPECT_EQ(snapshot.conflicts, kThreads * kPerThread - 1U);
  EXPECT_TRUE(registry.holds(key));
}
