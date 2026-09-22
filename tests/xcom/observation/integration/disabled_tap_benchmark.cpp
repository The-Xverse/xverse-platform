/**
 * @file disabled_tap_benchmark.cpp
 * @brief Repeated paired benchmark for the source-compatible disabled observation path.
 * @ownership The process owns both loopback scenarios and all timing samples.
 * @lifetime No measured value escapes the process.
 * @thread_safety Measurement is single-threaded to avoid fixture-created contention.
 * @failure Returns nonzero when setup/delivery fails or either median regression exceeds two percent.
 * @par Traceability
 * Verifies the disabled-tap portion of XCOM-OBS-010 and SC-008 on the admitted owned loopback fixture.
 * Results are local prototype evidence and are not production performance claims.
 */

#include "test_support.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string_view>
#include <thread>
#include <vector>

namespace {

using namespace xverse::xcom;
using xverse::xcom::observation_test::Scenario;

constexpr std::size_t kPairedSamples = 21U;
constexpr std::size_t kIterationsPerSample = 5000U;
constexpr double kMaximumMedianRegressionPercent = 2.0;

/** @return Compile-time target description without ambient environment access. */
[[nodiscard]] constexpr std::string_view target_name() noexcept {
#if defined(__linux__) && defined(__x86_64__)
  return "linux-x86_64";
#elif defined(__linux__)
  return "linux-other";
#else
  return "non-linux";
#endif
}

/** @param values Nonempty sample vector copied for sorting. @return Statistical median. */
[[nodiscard]] double median(std::vector<double> values) {
  std::sort(values.begin(), values.end());
  const std::size_t middle = values.size() / 2U;
  return values.size() % 2U == 0U ? (values[middle - 1U] + values[middle]) / 2.0
                                 : values[middle];
}

/**
 * @brief Time balanced submit/receive operations on one empty-at-end loopback route.
 * @param scenario Ready disabled-observation scenario.
 * @param item Reused immutable item.
 * @return Elapsed nanoseconds, or infinity if a normal-route operation fails.
 */
[[nodiscard]] double run_sample(Scenario& scenario, const CommunicationItem& item) {
  const auto start = std::chrono::steady_clock::now();
  std::uint64_t checksum = 0U;
  for (std::size_t iteration = 0U; iteration < kIterationsPerSample; ++iteration) {
    const ProviderStatus submitted = scenario.composition().submit(
        scenario.provider_handle(), item, scenario.lifecycle());
    const auto received =
        scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
    if (submitted.outcome() != ProviderOutcome::accepted || !received.has_value()) {
      return std::numeric_limits<double>::infinity();
    }
    checksum += static_cast<std::uint64_t>(received.value()->payload().size());
  }
  const auto stop = std::chrono::steady_clock::now();
  if (checksum != kIterationsPerSample * item.payload().size()) {
    return std::numeric_limits<double>::infinity();
  }
  return std::chrono::duration<double, std::nano>(stop - start).count();
}

/** @param elapsed_ns Sample duration. @return Mean operation-pair latency in nanoseconds. */
[[nodiscard]] double latency_per_iteration(const double elapsed_ns) noexcept {
  return elapsed_ns / static_cast<double>(kIterationsPerSample);
}

/** @param latency_ns Mean iteration latency. @return Submit/receive pairs per second. */
[[nodiscard]] double throughput(const double latency_ns) noexcept {
  return 1'000'000'000.0 / latency_ns;
}

}  // namespace

/** @return Zero only when both accepted two-percent median thresholds hold. */
int main() {
  Scenario baseline("bench.a", InteractionKind::message_event, 1U);
  Scenario disabled("bench.b", InteractionKind::message_event, 1U);
  const auto baseline_item = baseline.item(1U, 1U);
  const auto disabled_item = disabled.item(1U, 1U);
  if (!baseline.ready() || !disabled.ready() || !baseline_item.has_value() ||
      !disabled_item.has_value()) {
    std::cerr << "benchmark setup failed\n";
    return 1;
  }

  static_cast<void>(run_sample(baseline, *baseline_item.value()));
  static_cast<void>(run_sample(disabled, *disabled_item.value()));

  std::vector<double> baseline_latency;
  std::vector<double> disabled_latency;
  std::vector<double> baseline_throughput;
  std::vector<double> disabled_throughput;
  baseline_latency.reserve(kPairedSamples);
  disabled_latency.reserve(kPairedSamples);
  baseline_throughput.reserve(kPairedSamples);
  disabled_throughput.reserve(kPairedSamples);

  for (std::size_t sample = 0U; sample < kPairedSamples; ++sample) {
    double baseline_elapsed = 0.0;
    double disabled_elapsed = 0.0;
    if (sample % 2U == 0U) {
      baseline_elapsed = run_sample(baseline, *baseline_item.value());
      disabled_elapsed = run_sample(disabled, *disabled_item.value());
    } else {
      disabled_elapsed = run_sample(disabled, *disabled_item.value());
      baseline_elapsed = run_sample(baseline, *baseline_item.value());
    }
    if (!std::isfinite(baseline_elapsed) || !std::isfinite(disabled_elapsed)) {
      std::cerr << "benchmark route operation failed\n";
      return 1;
    }
    const double baseline_sample_latency = latency_per_iteration(baseline_elapsed);
    const double disabled_sample_latency = latency_per_iteration(disabled_elapsed);
    baseline_latency.push_back(baseline_sample_latency);
    disabled_latency.push_back(disabled_sample_latency);
    baseline_throughput.push_back(throughput(baseline_sample_latency));
    disabled_throughput.push_back(throughput(disabled_sample_latency));
  }

  const double baseline_latency_median = median(baseline_latency);
  const double disabled_latency_median = median(disabled_latency);
  const double baseline_throughput_median = median(baseline_throughput);
  const double disabled_throughput_median = median(disabled_throughput);
  const double latency_regression =
      ((disabled_latency_median / baseline_latency_median) - 1.0) * 100.0;
  const double throughput_regression =
      (1.0 - (disabled_throughput_median / baseline_throughput_median)) * 100.0;

  std::cout << "fixture=owned-loopback-disabled-observation\n"
            << "target=" << target_name() << '\n'
            << "compiler=" << __VERSION__ << '\n'
            << "steady_clock=" << (std::chrono::steady_clock::is_steady ? "true" : "false")
            << '\n'
            << "hardware_concurrency_hint=" << std::thread::hardware_concurrency() << '\n'
            << "paired_samples=" << kPairedSamples << '\n'
            << "iterations_per_sample=" << kIterationsPerSample << '\n'
            << "pair_order=alternating\n"
            << "baseline_median_latency_ns=" << baseline_latency_median << '\n'
            << "disabled_median_latency_ns=" << disabled_latency_median << '\n'
            << "latency_regression_percent=" << latency_regression << '\n'
            << "baseline_median_throughput_pairs_per_second="
            << baseline_throughput_median << '\n'
            << "disabled_median_throughput_pairs_per_second="
            << disabled_throughput_median << '\n'
            << "throughput_regression_percent=" << throughput_regression << '\n'
            << "accepted_threshold_percent=" << kMaximumMedianRegressionPercent << '\n'
            << "uncertainty=single-process steady-clock; CPU affinity, scheduler load, DVFS, "
               "thermal state, and cache state are uncontrolled\n"
            << "claim=prototype fixture only; not a production performance claim\n";

  const bool latency_pass = latency_regression <= kMaximumMedianRegressionPercent;
  const bool throughput_pass = throughput_regression <= kMaximumMedianRegressionPercent;
  std::cout << "latency_threshold=" << (latency_pass ? "PASS" : "FAIL") << '\n'
            << "throughput_threshold=" << (throughput_pass ? "PASS" : "FAIL") << '\n';
  return latency_pass && throughput_pass ? 0 : 1;
}
