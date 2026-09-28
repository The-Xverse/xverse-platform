/**
 * @file test_support.hpp
 * @brief T029 bounded, payload-free owned fixture for the complete stimulation verification
 *        matrix: it composes the accepted T025 permit/session, T026 fault-injectable journal
 *        storage, T027 policy, T028 action path and exclusive lease registry, a recording
 *        emitter, and a bounded bridge into the accepted provider/observation boundary.
 * @ownership Each MatrixFixture owns its permit/policy values, bounded storage, journal,
 *            registry, emitter, and closed action path. An ObservationBridge owns its route,
 *            lifecycle, provider, composition, and hub. No fixture re-implements, weakens, or
 *            bypasses an accepted guard, journal, provider, or observation check.
 * @lifetime The storage, journal, registry, and emitter outlive the action path; the hub and
 *          lifecycle outlive the observation tap.
 * @thread_safety Single declared user per case, except the concurrency cases which use at most
 *                four joined threads; the accepted components serialize their own state and the
 *                fixture invokes no callback under a lock.
 * @bounds Durable bytes <= 16 KiB, <= 4 declared fault points, <= 64 operations per case,
 *         <= 1 captured descriptor, one observation tap with a fixed record capacity. No
 *         payload byte is retained, logged, or forwarded beyond the call-scoped emitter view.
 * @failure A fixture construction or open failure fails the case; an injected storage fault is
 *          surfaced as the declared JournalStatus and never silently succeeds.
 * @par Traceability
 * Supports T029-SR-003, T029-SR-022 and the XCOM-DU-014..018 verification matrix.
 */

#ifndef XVERSE_XCOM_STIMULATION_MATRIX_TEST_SUPPORT_HPP_
#define XVERSE_XCOM_STIMULATION_MATRIX_TEST_SUPPORT_HPP_

#include "xverse/xcom/loopback_provider.hpp"
#include "xverse/xcom/observation.hpp"
#include "xverse/xcom/provider.hpp"
#include "xverse/xcom/stimulation_actions.hpp"

#include <gtest/gtest.h>

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace xverse::xcom::stimulation_matrix_test {

namespace val = xverse::xcom::validation;
namespace xc = xverse::xcom;

/// \brief Declared validity clock domain used by every matrix case.
inline constexpr val::ClockDomainId kDomain = 7U;
/// \brief Declared foreign clock domain, never compared with `kDomain`.
inline constexpr val::ClockDomainId kForeignDomain = 8U;
/// \brief Inclusive permit validity start.
inline constexpr val::Timestamp kFrom = 0;
/// \brief Exclusive permit validity end.
inline constexpr val::Timestamp kUntil = 100;
/// \brief Maximum test threads in a concurrency case.
inline constexpr std::size_t kMaxThreads = 4U;
/// \brief Maximum bounded operations per concurrency case.
inline constexpr std::size_t kMaxOperationsPerThread = 16U;
/// \brief Maximum durable journal bytes in the fixture.
inline constexpr std::size_t kMaxDurableBytes = 16U * 1024U;
/// \brief Maximum declared fault points in the fault-injectable storage.
inline constexpr std::size_t kMaxInjectionPoints = 4U;

/// \brief Bound session identity `A`.
/// \return The declared session identity.
[[nodiscard]] inline val::SessionId session_a() {
  val::SessionId value{};
  value[0] = 1U;
  value[15] = 0x11U;
  return value;
}

/// \brief Bound plan digest `A`.
/// \return The declared plan digest.
[[nodiscard]] inline val::PlanDigest digest_a() {
  val::PlanDigest value{};
  value[0] = 2U;
  value[31] = 0x22U;
  return value;
}

/// \brief Bound session identity `B`.
/// \return The declared session identity.
[[nodiscard]] inline val::SessionId session_b() {
  val::SessionId value{};
  value[0] = 5U;
  value[15] = 0x55U;
  return value;
}

/// \brief Bound plan digest `B`.
/// \return The declared plan digest.
[[nodiscard]] inline val::PlanDigest digest_b() {
  val::PlanDigest value{};
  value[0] = 6U;
  value[31] = 0x66U;
  return value;
}

/// \brief Validates a short declared tag.
/// \param text Candidate tag text.
/// \return The validated tag.
[[nodiscard]] inline val::Tag tag(std::string_view text) { return val::Tag::make(text).value(); }

/// \brief Builds one valid accepted permit bound to the declared identity and validity domain.
/// \return The immutable permit.
[[nodiscard]] inline val::Permit make_permit() {
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

/// \brief Builds one declared policy consistent with the permit.
/// \param permit The bound permit.
/// \param quota Per-session authorized-action budget.
/// \param loop_window Declared guard loop-detection window depth.
/// \param window_quota Per-window budget; `0` means equal to `quota`.
/// \param action_window Ordinal window width; `0` means the guard default of `quota`.
/// \return The declared policy.
[[nodiscard]] inline val::StimulationPolicy make_policy(const val::Permit &permit,
                                                        std::size_t quota = 8U,
                                                        std::size_t loop_window = 4U,
                                                        std::size_t window_quota = 0U,
                                                        std::size_t action_window = 0U) {
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
  policy.max_actions_per_window = window_quota == 0U ? quota : window_quota;
  policy.action_window = action_window == 0U ? quota : action_window;
  policy.loop_window = loop_window;
  policy.allow_service_emulation = true;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return policy;
}

/// \brief Builds a bounded declared action-path configuration.
/// \param pending Maximum pending scheduled actions.
/// \param lineage Maximum emission-time lineage entries.
/// \param drain Maximum drain steps per call.
/// \param tolerance Declared late tolerance in the validity domain.
/// \return The declared configuration.
[[nodiscard]] inline val::ActionPathConfig make_config(std::size_t pending = 8U,
                                                       std::size_t lineage = 8U,
                                                       std::size_t drain = 8U,
                                                       val::Timestamp tolerance = 100) {
  val::ActionPathConfig config;
  config.max_pending_actions = pending;
  config.max_lineage_entries = lineage;
  config.max_drain_steps = drain;
  config.max_payload_bytes = 64U;
  config.late_tolerance = tolerance;
  config.tool = tag("tool");
  return config;
}

/// \brief Builds a declared request with the action/interaction/direction/schema pairing.
/// \param permit The bound permit.
/// \param id Non-zero request identity.
/// \param action Declared stimulation action.
/// \param immediate Immediate/scheduled label.
/// \param scheduled_at Declared schedule in the request clock domain.
/// \param domain Declared request clock domain.
/// \return The declared request.
[[nodiscard]] inline val::StimulationRequest
make_request(const val::Permit &permit, std::uint64_t id,
             val::StimulationAction action = val::StimulationAction::InjectSignal,
             bool immediate = true, val::Timestamp scheduled_at = 0,
             val::ClockDomainId domain = kDomain) {
  val::StimulationRequest request;
  request.permit_id = permit.permit_id();
  request.session_id = permit.session_id();
  request.plan_digest = permit.plan_digest();
  request.action = action;
  switch (action) {
  case val::StimulationAction::InjectSignal:
    request.interaction = xc::InteractionKind::signal_state_update;
    request.direction = xc::EndpointDirection::produce;
    request.schema = val::SchemaKey{tag("sig.v1"), tag("1")};
    break;
  case val::StimulationAction::InjectMessage:
    request.interaction = xc::InteractionKind::message_event;
    request.direction = xc::EndpointDirection::produce;
    request.schema = val::SchemaKey{tag("msg.v1"), tag("1")};
    break;
  case val::StimulationAction::InvokeService:
    request.interaction = xc::InteractionKind::service_request;
    request.direction = xc::EndpointDirection::request;
    request.schema = val::SchemaKey{tag("req.v1"), tag("1")};
    request.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
    break;
  case val::StimulationAction::EmulateService:
  default:
    request.interaction = xc::InteractionKind::service_response;
    request.direction = xc::EndpointDirection::respond;
    request.schema = val::SchemaKey{tag("resp.v1"), tag("1")};
    request.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
    break;
  }
  request.target = tag("target.alpha");
  request.interface_tag = tag("iface.v1");
  request.clock_domain = domain;
  request.scheduled_at = scheduled_at;
  request.immediate = immediate;
  request.request_id = id;
  request.correlation_id = id + 1000U;
  request.causation_id = 0U;
  return request;
}

/// \brief A caller-resolved in-window time.
/// \return The `Ok` resolution at the window midpoint.
[[nodiscard]] inline val::ResolvedTime in_window() {
  return val::ResolvedTime{kDomain, 50, val::Result::Ok};
}

/// \brief A caller-resolved time at the exclusive window end.
/// \return The out-of-window `Ok` resolution.
[[nodiscard]] inline val::ResolvedTime out_of_window() {
  return val::ResolvedTime{kDomain, kUntil, val::Result::Ok};
}

/// \brief A caller-resolved non-`Ok` time.
/// \param resolution Declared resolution failure.
/// \return The unmapped resolution in the declared domain.
[[nodiscard]] inline val::ResolvedTime unmapped(val::Result resolution) {
  return val::ResolvedTime{kDomain, 50, resolution};
}

/// \brief Default bounded journal configuration.
/// \return The declared journal configuration.
[[nodiscard]] inline val::JournalConfig default_journal_config() {
  val::JournalConfig config;
  config.max_record_bytes = 320U;
  config.max_retained_records = 32U;
  config.max_journal_bytes = kMaxDurableBytes;
  return config;
}

/// \brief Closed injectable storage fault vocabulary.
enum class StorageFault : std::uint8_t {
  None,        ///< No fault injected.
  WriteFailed, ///< The matching call returns `WriteFailed`.
  PartialWrite,///< The matching append writes a short prefix and returns `PartialWrite`.
};

/**
 * @brief Bounded in-test journal storage seam with a declared, finite set of injectable faults.
 * @ownership Owns a bounded durable byte buffer and its own serialization mutex.
 * @lifetime Outlives the journal that references it.
 * @thread_safety Internally synchronized; safe for the concurrent cases.
 * @bounds Durable bytes are declared by the caller's `JournalConfig`; no unbounded growth is
 *         introduced by the seam itself.
 * @failure A matching injected fault returns the declared `JournalStatus` and never throws.
 */
class FaultStorage final : public val::StimulationJournal::Storage {
public:
  /// \brief Declared append fault.
  StorageFault append_fault{StorageFault::None};
  /// \brief One-based append call index the fault applies to.
  std::size_t append_fault_on{0U};
  /// \brief Declared sync fault.
  StorageFault sync_fault{StorageFault::None};
  /// \brief One-based sync call index the fault applies to.
  std::size_t sync_fault_on{0U};
  /// \brief Whether `read_all` fails.
  bool read_failed{false};
  /// \brief Whether `truncate` fails.
  bool truncate_failed{false};

  /// \brief Appends bytes at the durable end, or injects the declared fault.
  /// \param bytes Bytes to append.
  /// \return `Ok`, `WriteFailed`, or `PartialWrite`.
  val::JournalStatus append(std::span<const std::uint8_t> bytes) override {
    std::lock_guard<std::mutex> lock(mutex_);
    ++append_calls;
    if (append_fault_on != 0U && append_calls == append_fault_on &&
        append_fault != StorageFault::None) {
      if (append_fault == StorageFault::WriteFailed) {
        return val::JournalStatus::WriteFailed;
      }
      bytes_.insert(bytes_.end(), bytes.begin(),
                    bytes.begin() + static_cast<std::ptrdiff_t>(bytes.size() / 2U));
      return val::JournalStatus::PartialWrite;
    }
    bytes_.insert(bytes_.end(), bytes.begin(), bytes.end());
    return val::JournalStatus::Ok;
  }

  /// \brief Flushes the durable end, or injects the declared fault.
  /// \return `Ok` or `WriteFailed`.
  val::JournalStatus sync() override {
    std::lock_guard<std::mutex> lock(mutex_);
    ++sync_calls;
    if (sync_fault_on != 0U && sync_calls == sync_fault_on &&
        sync_fault == StorageFault::WriteFailed) {
      return val::JournalStatus::WriteFailed;
    }
    return val::JournalStatus::Ok;
  }

  /// \brief Reads every durable byte.
  /// \param out Receives every durable byte.
  /// \return `Ok` or `WriteFailed`.
  val::JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    std::lock_guard<std::mutex> lock(mutex_);
    if (read_failed) {
      return val::JournalStatus::WriteFailed;
    }
    out = bytes_;
    return val::JournalStatus::Ok;
  }

  /// \brief Returns the current durable byte count.
  /// \return The durable byte count.
  [[nodiscard]] std::size_t size() override {
    std::lock_guard<std::mutex> lock(mutex_);
    return bytes_.size();
  }

  /// \brief Restores the durable end to a known-good offset.
  /// \param size The known-good offset.
  /// \return `Ok` or `WriteFailed`.
  val::JournalStatus truncate(std::size_t size) override {
    std::lock_guard<std::mutex> lock(mutex_);
    if (truncate_failed) {
      return val::JournalStatus::WriteFailed;
    }
    bytes_.resize(size);
    return val::JournalStatus::Ok;
  }

  /// \brief Number of append calls observed.
  std::size_t append_calls{0U};
  /// \brief Number of sync calls observed.
  std::size_t sync_calls{0U};

private:
  /// \brief Serializes byte-buffer access.
  mutable std::mutex mutex_{};
  /// \brief Bounded durable bytes.
  std::vector<std::uint8_t> bytes_{};
};

/**
 * @brief Bounded recording host emission seam.
 * @ownership Owns its counters, its captured descriptor copy, and its ordering record.
 * @lifetime Must outlive the action path that references it.
 * @thread_safety Internally synchronized; `emit` is invoked outside every action-path lock.
 * @bounds Captures at most one descriptor and at most one ordering entry per call.
 * @failure Returns the declared `EmissionStatus`; never throws.
 */
class RecordingEmitter final : public val::ActionEmitter {
public:
  /// \brief Delivers one descriptor and records the call.
  /// \param item Bounded payload-free synthetic descriptor.
  /// \param payload Call-scoped payload view; never retained.
  /// \return The declared emission status.
  val::EmissionStatus emit(const val::SyntheticStimulationItem &item,
                           std::span<const std::byte> payload) override {
    calls.fetch_add(1U, std::memory_order_relaxed);
    const std::size_t durable = storage != nullptr ? storage->size() : 0U;
    std::lock_guard<std::mutex> lock(mutex_);
    last = item;
    last_payload_size = payload.size();
    order.push_back(item.intent.request_id);
    durable_size_before_emit = durable;
    durable_before_emit = durable > 0U;
    return status.load(std::memory_order_relaxed);
  }

  /// \brief Number of emission calls.
  std::atomic<std::size_t> calls{0U};
  /// \brief Declared host emission status.
  std::atomic<val::EmissionStatus> status{val::EmissionStatus::Delivered};
  /// \brief Optional storage seam observed for durable-intent ordering.
  FaultStorage *storage{nullptr};

  /// \brief Returns the captured descriptor.
  /// \return The most recent descriptor copy.
  [[nodiscard]] val::SyntheticStimulationItem last_item() {
    std::lock_guard<std::mutex> lock(mutex_);
    return last;
  }
  /// \brief Returns the recorded emission order.
  /// \return A copy of the recorded request identities.
  [[nodiscard]] std::vector<std::uint64_t> emission_order() {
    std::lock_guard<std::mutex> lock(mutex_);
    return order;
  }
  /// \brief Reports whether the durable intent preceded the first call.
  /// \return `true` when durable bytes existed at the call.
  [[nodiscard]] bool intent_durable_before_emit() {
    std::lock_guard<std::mutex> lock(mutex_);
    return durable_before_emit;
  }
  /// \brief Returns the durable byte count observed at the first call.
  /// \return The observed durable byte count.
  [[nodiscard]] std::size_t durable_size_at_call() {
    std::lock_guard<std::mutex> lock(mutex_);
    return durable_size_before_emit;
  }
  /// \brief Returns the call-scoped payload size observed.
  /// \return The observed payload size.
  [[nodiscard]] std::size_t payload_size_at_call() {
    std::lock_guard<std::mutex> lock(mutex_);
    return last_payload_size;
  }

private:
  /// \brief Serializes capture of the last descriptor and ordering record.
  mutable std::mutex mutex_{};
  /// \brief Most recent descriptor copy.
  val::SyntheticStimulationItem last{};
  /// \brief Recorded request identities in emission order.
  std::vector<std::uint64_t> order{};
  /// \brief Durable byte count observed at the most recent call.
  std::size_t durable_size_before_emit{0U};
  /// \brief Whether durable bytes existed at the most recent call.
  bool durable_before_emit{false};
  /// \brief Call-scoped payload size observed at the most recent call.
  std::size_t last_payload_size{0U};
};

/**
 * @brief One bounded owned fixture composing the accepted stimulation surfaces.
 * @ownership Owns its bounded storage, journal, registry, emitter, and closed action path.
 * @lifetime The storage, journal, registry, and emitter outlive the action path.
 * @thread_safety Single declared user, except the concurrency cases that join every thread
 *                before the fixture is destroyed.
 * @bounds One permit, one policy, one action path, <= 64 operations, <= 16 KiB durable bytes.
 * @failure A failed journal open or path open is asserted by the case; no fixture weakens an
 *         accepted check.
 */
class MatrixFixture {
public:
  /// \brief Constructs an unopened fixture with a bounded lease-registry capacity.
  /// \param registry_capacity Active-lease capacity.
  explicit MatrixFixture(std::size_t registry_capacity = 4U) : registry(registry_capacity) {
    emitter.storage = &storage;
  }

  /// \brief Copy construction is deleted; the fixture owns its unique components.
  MatrixFixture(const MatrixFixture &) = delete;
  /// \brief Copy assignment is deleted.
  MatrixFixture &operator=(const MatrixFixture &) = delete;

  /// \brief Opens the accepted journal over the fixture storage.
  /// \param config Bounded journal configuration.
  /// \return The declared journal status.
  val::JournalStatus open_journal(const val::JournalConfig &config = default_journal_config()) {
    return journal.open(storage, config);
  }

  /// \brief Opens the accepted action path over the fixture components.
  /// \param permit The immutable permit.
  /// \param policy The declared policy.
  /// \param config Bounded action-path configuration.
  /// \return The declared guard status.
  val::GuardStatus open_path(const val::Permit &permit, const val::StimulationPolicy &policy,
                             const val::ActionPathConfig &config) {
    path.emplace(config, journal, registry, emitter);
    return path->open(permit, policy);
  }

  /// \brief Constructs the accepted action path without opening it, for the closed-path case.
  /// \param config Bounded action-path configuration.
  void build_closed_path(const val::ActionPathConfig &config) {
    path.emplace(config, journal, registry, emitter);
  }

  /// \brief The bounded fault-injectable durable storage seam.
  FaultStorage storage{};
  /// \brief The accepted durable intent/outcome journal.
  val::StimulationJournal journal{};
  /// \brief The accepted exclusive service-emulation lease registry.
  val::ServiceEmulationRegistry registry;
  /// \brief The bounded recording host emission seam.
  RecordingEmitter emitter{};
  /// \brief The accepted guarded action path, once opened.
  std::optional<val::StimulationActionPath> path{};
};

/// \brief Encodes a 64-bit identity as a bounded zero-padded decimal string.
/// \param value Value to encode.
/// \return The 20-byte zero-padded decimal encoding.
[[nodiscard]] inline std::string to_decimal(std::uint64_t value) {
  std::string text(20U, '0');
  for (std::size_t index = 0U; index < 20U; ++index) {
    text[19U - index] = static_cast<char>('0' + static_cast<char>(value % 10U));
    value /= 10U;
  }
  return text;
}

/// \brief Folds a 16-byte session identity into a bounded decimal encoding.
/// \param session Session identity.
/// \return The zero-padded decimal fold of the session bytes.
[[nodiscard]] inline std::string session_decimal(const val::SessionId &session) {
  std::uint64_t fold = 0U;
  for (const std::uint8_t byte : session) {
    fold = (fold << 3U) ^ static_cast<std::uint64_t>(byte);
  }
  return to_decimal(fold);
}

/**
 * @brief Bounded bridge from an emitted descriptor into the accepted provider/observation
 *        boundary.
 * @ownership Owns one fixed loopback route, its lifecycle, provider, composition, hub, and the
 *            attached tap handle.
 * @lifetime The hub, lifecycle, and composition outlive the attached tap.
 * @thread_safety Construction and use are single-threaded.
 * @bounds One route, one provider, one tap, one item per case; the bridged item carries no
 *         payload byte.
 * @failure `ready()` is `false` when any bounded fixture resource cannot be created.
 */
class ObservationBridge {
public:
  /// \brief Constructs the bounded route, provider, composition, and enabled hub.
  ObservationBridge() {
    constexpr std::string_view digest =
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
    const auto contract = xc::CommunicationContract::create(
        {"matrix.contract", "1.0.0", "matrix.interface", "matrix.schema", "1.0.0",
         xc::InteractionKind::message_event, xc::EndpointDirection::produce,
         xc::EndpointDirection::consume});
    if (!contract.has_value()) {
      return;
    }
    contract_.emplace(*contract.value());
    const std::string source_endpoint = session_decimal(session_a());
    const auto source = xc::EndpointSpec::create(
        {source_endpoint, digest, "tool", xc::EndpointDirection::produce}, *contract_);
    const auto destination = xc::EndpointSpec::create(
        {"matrix.destination", digest, "tool", xc::EndpointDirection::consume},
        *contract_);
    if (!source.has_value() || !destination.has_value()) {
      return;
    }
    source_spec_.emplace(*source.value());
    destination_spec_.emplace(*destination.value());
    const auto route = xc::RouteSpec::create(
        {"matrix.route", digest, "tool"}, *source_spec_, *destination_spec_);
    const auto lifecycle_configuration = xc::LifecycleConfiguration::create({2U, 1U});
    if (!route.has_value() || !lifecycle_configuration.has_value()) {
      return;
    }
    route_spec_.emplace(*route.value());
    lifecycle_.emplace(*lifecycle_configuration.value());
    const auto source_handle = lifecycle_->declare_endpoint(*source_spec_);
    const auto destination_handle = lifecycle_->declare_endpoint(*destination_spec_);
    const auto route_handle = lifecycle_->declare_route(*route_spec_);
    if (!source_handle.has_value() || !destination_handle.has_value() ||
        !route_handle.has_value()) {
      return;
    }
    source_handle_.emplace(*source_handle.value());
    destination_handle_.emplace(*destination_handle.value());
    route_handle_.emplace(*route_handle.value());
    if (!lifecycle_->validate_endpoint(*source_handle_).has_value() ||
        !lifecycle_->validate_endpoint(*destination_handle_).has_value() ||
        !lifecycle_->validate_route(*route_handle_, *source_handle_, *destination_handle_)
             .has_value() ||
        !lifecycle_->activate_endpoint(*source_handle_).has_value() ||
        !lifecycle_->activate_endpoint(*destination_handle_).has_value()) {
      return;
    }

    constexpr std::uint8_t all_interactions = 0x0FU;
    const auto descriptor = xc::ProviderDescriptor::create(
        {"tool", "1.0.0", "source.fixture.matrix", all_interactions,
         xc::delivery_capability_bit(xc::DeliveryCapability::best_effort),
         xc::ordering_capability_bit(xc::OrderingCapability::per_route_fifo),
         xc::kMaximumPayloadBytes, xc::LoopbackProvider::kMaximumRoutes,
         xc::LoopbackProvider::kMaximumQueueItems});
    const auto registry_configuration = xc::ProviderRegistryConfiguration::create(1U);
    if (!descriptor.has_value() || !registry_configuration.has_value()) {
      return;
    }
    descriptor_.emplace(*descriptor.value());
    provider_.emplace(*descriptor_);
    composition_.emplace(*registry_configuration.value(), hub_);
    if (composition_->register_provider(*provider_).outcome() != xc::ProviderOutcome::registered) {
      return;
    }
    const xc::ProviderRouteRequirements requirements{
        "1.0.0", xc::InteractionKind::message_event, xc::DeliveryCapability::best_effort,
        xc::OrderingCapability::per_route_fifo, 16U, 4U};
    const auto prepared = composition_->prepare_route(*lifecycle_, *route_spec_, *route_handle_,
                                                      *source_handle_, *destination_handle_,
                                                      requirements);
    if (!prepared.has_value()) {
      return;
    }
    provider_handle_.emplace(*prepared.value());
    if (composition_->activate_route(*provider_handle_, *lifecycle_).outcome() !=
        xc::ProviderOutcome::activated) {
      return;
    }
    ready_ = true;
  }

  /// \brief Copy construction is deleted; the bridge owns unique components.
  ObservationBridge(const ObservationBridge &) = delete;
  /// \brief Copy assignment is deleted.
  ObservationBridge &operator=(const ObservationBridge &) = delete;

  /// \brief Reports whether every bounded resource is active.
  /// \return `true` only when the route and provider are ready.
  [[nodiscard]] bool ready() const noexcept { return ready_; }

  /// \brief Attaches one bounded observation tap constrained to the synthetic origin.
  /// \param capacity Fixed record capacity.
  /// \return The attach result carrying an exact handle on success.
  [[nodiscard]] xc::ObservationAttachResult
  attach_synthetic_tap(std::size_t capacity = 4U) {
    xc::ObservationFilterInput filter{};
    filter.route_id = route_spec_->route_id().value();
    filter.provider_id = route_spec_->provider_id().value();
    filter.interaction_kind = xc::InteractionKind::message_event;
    filter.origin = xc::OriginKind::validation_tool;
    const auto spec = xc::ObservationTapSpec::create(
        {xc::kObservationContractVersion, "tap.matrix", filter,
         xc::ObservationPayloadMode::metadata_only, 0U, capacity,
         xc::ObservationOverflowPolicy::drop_newest});
    if (!spec.has_value()) {
      return xc::ObservationAttachResult{};
    }
    return hub_.attach(*spec);
  }

  /// \brief Builds one bounded payload-free item from an emitted descriptor.
  /// \param descriptor Emitted payload-free synthetic descriptor.
  /// \return The validated item, or no value on a bridge defect.
  [[nodiscard]] std::optional<xc::CommunicationItem>
  make_item(const val::SyntheticStimulationItem &descriptor) const {
    if (!ready_ || !contract_.has_value()) {
      return std::nullopt;
    }
    const std::string correlation = to_decimal(descriptor.intent.correlation_id);
    const std::string causation = to_decimal(descriptor.intent.causation_id);
    const std::string endpoint = session_decimal(descriptor.intent.session_id);
    const xc::CommunicationItemInput input{
        contract_->contract_id().value(),
        contract_->contract_version().value(),
        contract_->interface_id().value(),
        endpoint,
        contract_->schema_id().value(),
        contract_->schema_version().value(),
        contract_->interaction_kind(),
        xc::OriginKind::validation_tool,
        xc::Timestamp(descriptor.intent.scheduled_at),
        "clock.matrix",
        correlation,
        causation,
        route_spec_->route_id().value(),
        descriptor.intent.tool.value(),
        std::span<const std::byte>{}};
    const auto built = xc::CommunicationItem::create(input, *contract_);
    if (!built.has_value()) {
      return std::nullopt;
    }
    return std::optional<xc::CommunicationItem>(*built.value());
  }

  /// \brief Builds one bounded item of a foreign origin for the negative provenance case.
  /// \param origin Declared foreign origin.
  /// \return The validated item, or no value on a bridge defect.
  [[nodiscard]] std::optional<xc::CommunicationItem> make_foreign_item(xc::OriginKind origin) const {
    if (!ready_ || !contract_.has_value()) {
      return std::nullopt;
    }
    const std::string correlation = to_decimal(1U);
    const std::string causation = to_decimal(0U);
    const xc::CommunicationItemInput input{
        contract_->contract_id().value(),
        contract_->contract_version().value(),
        contract_->interface_id().value(),
        source_spec_->endpoint_id().value(),
        contract_->schema_id().value(),
        contract_->schema_version().value(),
        contract_->interaction_kind(),
        origin,
        xc::Timestamp(0),
        "clock.matrix",
        correlation,
        causation,
        route_spec_->route_id().value(),
        route_spec_->provider_id().value(),
        std::span<const std::byte>{}};
    const auto built = xc::CommunicationItem::create(input, *contract_);
    if (!built.has_value()) {
      return std::nullopt;
    }
    return std::optional<xc::CommunicationItem>(*built.value());
  }

  /// \brief Submits one item through the accepted provider route with observation enabled.
  /// \param item Valid route-bound item.
  /// \return The declared provider status.
  [[nodiscard]] xc::ProviderStatus submit(const xc::CommunicationItem &item) {
    return composition_->submit(*provider_handle_, item, *lifecycle_);
  }

  /// \brief Returns the owned observation hub.
  /// \return The observation hub.
  [[nodiscard]] xc::ObservationHub &hub() noexcept { return hub_; }

  /// \brief Returns the declared route identity.
  /// \return The declared route identity.
  [[nodiscard]] std::string_view route_id() const noexcept {
    return route_spec_->route_id().value();
  }

  /// \brief Returns the declared provider identity.
  /// \return The declared provider identity.
  [[nodiscard]] std::string_view provider_id() const noexcept {
    return route_spec_->provider_id().value();
  }

private:
  bool ready_{false};
  xc::ObservationHub hub_{};
  std::optional<xc::CommunicationContract> contract_{};
  std::optional<xc::EndpointSpec> source_spec_{};
  std::optional<xc::EndpointSpec> destination_spec_{};
  std::optional<xc::RouteSpec> route_spec_{};
  std::optional<xc::LifecycleController> lifecycle_{};
  std::optional<xc::EndpointHandle> source_handle_{};
  std::optional<xc::EndpointHandle> destination_handle_{};
  std::optional<xc::RouteHandle> route_handle_{};
  std::optional<xc::ProviderDescriptor> descriptor_{};
  std::optional<xc::LoopbackProvider> provider_{};
  std::optional<xc::ProviderComposition> composition_{};
  std::optional<xc::ProviderRouteHandle> provider_handle_{};
};

} // namespace xverse::xcom::stimulation_matrix_test

#endif // XVERSE_XCOM_STIMULATION_MATRIX_TEST_SUPPORT_HPP_
