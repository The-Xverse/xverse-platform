/**
 * @file concurrency_tests.cpp
 * @brief T029 bounded deterministic concurrency: a declared guard quota is never exceeded under
 *        four threads, a lease race has exactly one winner, and repeated runs produce identical
 *        statuses, outcomes, and snapshots.
 * @ownership Each case owns one fixture, at most four joined threads, and the golden result.
 * @lifetime Every thread is joined before its fixture or registry is destroyed.
 * @thread_safety At most four threads; the accepted guard, journal, registry, and action path
 *                serialize their own state and invoke no callback under a lock.
 * @bounds <= 4 threads, <= 16 operations per thread, 3 repeated runs, no wall-clock verdict.
 * @failure More than the declared quota emitted, two lease winners, or a non-deterministic
 *          repeated run fails the case.
 */

#include "test_support.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <thread>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::stimulation_matrix_test::digest_a;
using xverse::xcom::stimulation_matrix_test::in_window;
using xverse::xcom::stimulation_matrix_test::kDomain;
using xverse::xcom::stimulation_matrix_test::kMaxOperationsPerThread;
using xverse::xcom::stimulation_matrix_test::kMaxThreads;
using xverse::xcom::stimulation_matrix_test::make_config;
using xverse::xcom::stimulation_matrix_test::make_permit;
using xverse::xcom::stimulation_matrix_test::make_policy;
using xverse::xcom::stimulation_matrix_test::make_request;
using xverse::xcom::stimulation_matrix_test::MatrixFixture;
using xverse::xcom::stimulation_matrix_test::session_a;
using xverse::xcom::stimulation_matrix_test::tag;

namespace {

/// @brief Declared per-session guard quota for the concurrent-emission case.
constexpr std::size_t kQuota = 7U;

/// @brief Aggregated bounded result of one concurrent-emission run.
struct QuotaRun {
  /// @brief Actions emitted.
  std::size_t emitted{0U};
  /// @brief Actions rejected.
  std::size_t rejected{0U};
  /// @brief Emitter calls observed.
  std::size_t emitter_calls{0U};
  /// @brief Whether the fixture snapshot reports the declared quota.
  std::size_t snapshot_emitted{0U};

  /// @brief Compares every field.
  /// @param other Other run result.
  /// @return `true` when every field is equal.
  bool operator==(const QuotaRun &other) const = default;
};

/// @brief Runs four threads submitting bounded immediate actions to one action path.
/// @return The aggregated bounded result.
[[nodiscard]] QuotaRun run_concurrent_quota() {
  const val::Permit permit = make_permit();
  MatrixFixture fixture;
  EXPECT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  EXPECT_EQ(fixture.open_path(permit, make_policy(permit, kQuota), make_config(8U, 16U, 8U)),
            val::GuardStatus::Ok);

  std::atomic<std::size_t> emitted{0U};
  std::atomic<std::size_t> rejected{0U};
  std::array<std::thread, kMaxThreads> threads;
  for (std::size_t thread = 0U; thread < kMaxThreads; ++thread) {
    threads[thread] = std::thread([&, thread]() {
      for (std::size_t index = 0U; index < kMaxOperationsPerThread; ++index) {
        const std::uint64_t id = 1U + thread * kMaxOperationsPerThread + index;
        val::ActionDiagnostic diagnostic;
        const val::ActionStatus status =
            fixture.path->execute(make_request(permit, id), val::LifecycleState::active,
                                  in_window(), {}, diagnostic);
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
  QuotaRun result;
  result.emitted = emitted.load();
  result.rejected = rejected.load();
  result.emitter_calls = fixture.emitter.calls.load();
  result.snapshot_emitted = fixture.path->snapshot().emitted;
  return result;
}

/// @brief Aggregated bounded result of one lease-race and completion run.
struct LeaseRun {
  /// @brief Acquisition winners.
  std::size_t winners{0U};
  /// @brief Conflicted acquisitions.
  std::size_t conflicts{0U};
  /// @brief Active leases in the final snapshot.
  std::size_t active{0U};
  /// @brief Drained actions from the deterministic completion.
  std::size_t drained{0U};
  /// @brief Drained request identities in emission order.
  std::vector<std::uint64_t> order{};

  /// @brief Compares every field.
  /// @param other Other run result.
  /// @return `true` when every field is equal.
  bool operator==(const LeaseRun &other) const = default;
};

/// @brief Runs a bounded lease race and a deterministic concurrent-enqueue completion.
/// @return The aggregated bounded result.
[[nodiscard]] LeaseRun run_concurrent_lease_and_completion() {
  val::ServiceEmulationRegistry registry{4U};
  val::EndpointGeneration key;
  key.session = session_a();
  key.endpoint = tag("svc.alpha");
  key.generation = 3U;
  key.plan_digest = digest_a();

  std::atomic<std::size_t> winners{0U};
  std::atomic<std::size_t> conflicts{0U};
  std::array<std::thread, kMaxThreads> race;
  for (std::size_t thread = 0U; thread < kMaxThreads; ++thread) {
    race[thread] = std::thread([&, thread]() {
      for (std::size_t index = 0U; index < kMaxOperationsPerThread; ++index) {
        const std::uint64_t id = 1U + thread * kMaxOperationsPerThread + index;
        const val::LeaseStatus status = registry.acquire(key, id, kDomain, 0, 100);
        if (status == val::LeaseStatus::Ok) {
          winners.fetch_add(1U, std::memory_order_relaxed);
        } else if (status == val::LeaseStatus::Conflict) {
          conflicts.fetch_add(1U, std::memory_order_relaxed);
        }
      }
    });
  }
  for (std::thread &thread : race) {
    thread.join();
  }

  const val::Permit permit = make_permit();
  MatrixFixture fixture;
  EXPECT_EQ(fixture.open_journal(), val::JournalStatus::Ok);
  EXPECT_EQ(fixture.open_path(permit, make_policy(permit, 16U), make_config(64U, 64U, 64U)),
            val::GuardStatus::Ok);
  std::atomic<std::size_t> not_queued{0U};
  std::array<std::thread, kMaxThreads> enqueue;
  for (std::size_t thread = 0U; thread < kMaxThreads; ++thread) {
    enqueue[thread] = std::thread([&, thread]() {
      for (std::size_t index = 0U; index < 4U; ++index) {
        const std::uint64_t id = 1U + thread * 4U + index;
        val::ActionDiagnostic diagnostic;
        const val::ActionStatus status =
            fixture.path->execute(make_request(permit, id, val::StimulationAction::InjectSignal,
                                               false, static_cast<val::Timestamp>(id)),
                                  val::LifecycleState::active, in_window(), {}, diagnostic);
        if (status != val::ActionStatus::Queued) {
          not_queued.fetch_add(1U, std::memory_order_relaxed);
        }
      }
    });
  }
  for (std::thread &thread : enqueue) {
    thread.join();
  }
  const val::CompletionReport report =
      fixture.path->drain(val::CompletionRequest{100, kDomain, val::LifecycleState::active});
  EXPECT_EQ(not_queued.load(), 0U);

  LeaseRun result;
  result.winners = winners.load();
  result.conflicts = conflicts.load();
  result.active = registry.snapshot().active;
  result.drained = report.drained;
  result.order = fixture.emitter.emission_order();
  return result;
}

} // namespace

/** T29-TS-019 (CHK-16, NEG-08, NEG-31, NEG-33): the declared guard quota holds under four
 *  threads and three runs are identical. */
TEST(XcomStimulationMatrixConcurrency, ConcurrentQuotaEmissionDeterminism) {
  QuotaRun golden;
  for (std::size_t run = 0U; run < 3U; ++run) {
    const QuotaRun result = run_concurrent_quota();
    if (run == 0U) {
      golden = result;
    } else {
      EXPECT_EQ(result, golden);
    }
  }
  EXPECT_EQ(golden.emitted, kQuota);
  EXPECT_EQ(golden.emitter_calls, kQuota);
  EXPECT_EQ(golden.snapshot_emitted, kQuota);
  EXPECT_EQ(golden.rejected, kMaxThreads * kMaxOperationsPerThread - kQuota);
}

/** T29-TS-020 (CHK-16, NEG-24, NEG-31, NEG-32): a lease race has exactly one winner and the
 *  concurrent-enqueue completion is deterministic across repeated runs. */
TEST(XcomStimulationMatrixConcurrency, ConcurrentLeaseSingleWinnerAndCompletion) {
  LeaseRun golden;
  for (std::size_t run = 0U; run < 3U; ++run) {
    const LeaseRun result = run_concurrent_lease_and_completion();
    if (run == 0U) {
      golden = result;
    } else {
      EXPECT_EQ(result, golden);
    }
  }
  EXPECT_EQ(golden.winners, 1U);
  EXPECT_EQ(golden.conflicts, kMaxThreads * kMaxOperationsPerThread - 1U);
  EXPECT_EQ(golden.active, 1U);
  EXPECT_EQ(golden.drained, kMaxThreads * 4U);
  ASSERT_EQ(golden.order.size(), kMaxThreads * 4U);
  for (std::size_t index = 0U; index < golden.order.size(); ++index) {
    EXPECT_EQ(golden.order[index], index + 1U);
  }
}
