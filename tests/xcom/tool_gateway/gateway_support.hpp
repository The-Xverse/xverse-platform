/**
 * @file gateway_support.hpp
 * @brief T031 bounded, payload-free, test-local fixture for the local-IPC-only gateway: a manual
 *        clock-driven accepted T025 time authority, an in-process bounded `LocalIpcChannel`, a
 *        bounded log-capture sink, and a composing fixture over the accepted T025-T028 boundaries.
 * @ownership The fixture owns its bounded storage, journal, registry, emitter, action path, hub,
 *            manager, and manual clock. The gateway holds non-owning references that the fixture
 *            keeps alive for the case lifetime.
 * @lifetime The storage, journal, registry, and emitter outlive the action path; the manager,
 *           authority, and hub outlive the gateway session.
 * @thread_safety One declared user per case; the accepted components serialize their own state.
 * @bounds One permit, one policy, <= 16 KiB durable bytes, <= 64 operations, <= 4 streams, no
 *         retained payload byte, and no wall-clock dependence.
 * @failure A fixture construction or open failure fails the owning case; no fixture weakens or
 *          bypasses an accepted check.
 * @par Traceability
 * Supports T031-SR-001 through T031-SR-021 and the T31-TS-001..T31-TS-024 cases.
 */

#ifndef XVERSE_XCOM_TOOL_GATEWAY_SUPPORT_HPP_
#define XVERSE_XCOM_TOOL_GATEWAY_SUPPORT_HPP_

#include "xverse/xcom/tool_gateway.hpp"

#include <gtest/gtest.h>

#include <cstddef>
#include <cstdint>
#include <atomic>
#include <chrono>
#include <memory>
#include <mutex>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <thread>
#include <utility>
#include <vector>

#include <sys/stat.h>

namespace xverse::xcom::tool_gateway_test {

namespace val = xverse::xcom::validation;

/// @brief Declared validity/arrival clock domain used by every case.
inline constexpr val::ClockDomainId kDomain = 7U;
/// @brief Logical permit identity bound to the fixture.
inline constexpr std::string_view kPermitId = "permit-1";
/// @brief Logical session identity bound to the fixture.
inline constexpr std::string_view kSessionId = "session-1";
/// @brief Logical plan digest bound to the fixture.
inline constexpr std::string_view kPlanDigest = "plan-1";
/// @brief Logical graph digest bound to the fixture.
inline constexpr std::string_view kGraphDigest = "graph-1";
/// @brief Logical wire name of the bound arrival clock domain.
inline constexpr std::string_view kClockDomainName = "clock.gateway";
/// @brief Logical contract identity expected on the wire.
inline constexpr std::string_view kContractId = "gateway.contract";

/// @brief Bound declared session identity.
[[nodiscard]] inline val::SessionId session_identity() {
  val::SessionId value{};
  value[0] = 1U;
  value[15] = 0x11U;
  return value;
}

/// @brief Bound declared plan digest.
[[nodiscard]] inline val::PlanDigest plan_digest_identity() {
  val::PlanDigest value{};
  value[0] = 2U;
  value[31] = 0x22U;
  return value;
}

/// @brief Bound declared controller identity.
[[nodiscard]] inline val::ControllerId controller_identity() {
  val::ControllerId value{};
  for (std::size_t index = 0U; index < value.size(); ++index) {
    value[index] = static_cast<std::uint8_t>(0xA0U + index);
  }
  return value;
}

/// @brief Bound non-zero manager uniqueness scope.
[[nodiscard]] inline val::ManagerScope manager_scope() {
  val::ManagerScope value{};
  for (std::size_t index = 0U; index < value.size(); ++index) {
    value[index] = static_cast<std::uint8_t>(0xC0U + index);
  }
  return value;
}

/// @brief Validates a short declared tag.
/// @param text Candidate tag text.
/// @return The validated tag.
[[nodiscard]] inline val::Tag tag(std::string_view text) {
  return val::Tag::make(text).value();
}

/// @brief Builds the default bounded gateway configuration.
/// @param max_message Maximum frame size.
/// @param sessions Maximum concurrent sessions.
/// @param streams Maximum streams per session.
/// @param pending Maximum pending/in-flight requests.
/// @param max_deadline Maximum accepted deadline in milliseconds.
/// @param idle Session idle timeout in milliseconds.
/// @param records Maximum observation records per read.
/// @param payload Maximum accepted payload bytes.
/// @return The validated configuration.
[[nodiscard]] inline GatewayConfig
make_config(std::size_t max_message = 4096U, std::uint32_t sessions = 8U,
            std::uint32_t streams = 4U, std::uint32_t pending = 8U,
            std::uint64_t max_deadline = 100000U, std::uint64_t idle = 1000U,
            std::uint32_t records = 4U, std::size_t payload = 64U) {
  GatewayConfigInput input{};
  input.max_message_bytes = max_message;
  input.max_concurrent_sessions = sessions;
  input.max_streams_per_session = streams;
  input.max_pending_requests = pending;
  input.max_deadline_millis = max_deadline;
  input.session_idle_timeout_millis = idle;
  input.max_observation_records = records;
  input.max_payload_bytes = payload;
  const std::optional<GatewayConfig> config = GatewayConfig::create(input);
  EXPECT_TRUE(config.has_value());
  return *config;
}

/// @brief Builds one valid accepted permit bound to the declared identity and domain.
/// @return The immutable permit.
[[nodiscard]] inline val::Permit make_permit() {
  val::PermitBuilder builder;
  builder.set_session_id(session_identity());
  builder.set_plan_digest(plan_digest_identity());
  builder.set_scenario("scn");
  builder.set_deployment("dep");
  builder.set_environment("env");
  builder.set_tool("tool");
  builder.set_interface("iface.v1");
  builder.set_target("target.alpha");
  builder.set_nonce(1U);
  builder.set_validity(kDomain, 0, 1000);
  builder.add_allowed_action(val::to_mask(val::Action::Arm));
  builder.add_allowed_action(val::to_mask(val::Action::Activate));
  builder.add_allowed_action(val::to_mask(val::Action::Close));
  builder.add_allowed_action(val::to_mask(val::Action::Finalize));
  builder.add_allowed_action(val::to_mask(val::Action::Revoke));
  builder.add_allowed_action(val::to_mask(val::Action::Expire));
  builder.add_allowed_action(val::to_mask(val::Action::MarkEvidenceIncomplete));
  builder.add_quota(val::Quota{val::QuotaKind::Operations, 16U});
  val::Permit permit;
  EXPECT_EQ(builder.build(permit), val::Result::Ok);
  return permit;
}

/// @brief Builds the accepted session context matching one permit.
/// @param permit The bound permit.
/// @return The asserted context.
[[nodiscard]] inline val::SessionContext context_for(const val::Permit &permit) {
  val::SessionContext context;
  context.session_id = permit.session_id();
  context.plan_digest = permit.plan_digest();
  context.scenario = permit.scenario();
  context.deployment = permit.deployment();
  context.environment = permit.environment();
  context.tool = permit.tool();
  context.interface_name = permit.interface_name();
  context.target = permit.target();
  context.nonce = permit.nonce();
  context.validity_domain = permit.validity_domain();
  context.valid_from = permit.valid_from();
  context.valid_until = permit.valid_until();
  context.allowed_actions = permit.allowed_actions();
  context.quotas = permit.quotas();
  return context;
}

/// @brief Builds one declared policy consistent with the permit.
/// @param permit The bound permit.
/// @return The declared policy.
[[nodiscard]] inline val::StimulationPolicy make_policy(const val::Permit &permit) {
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
  policy.max_actions_per_session = 8U;
  policy.max_actions_per_window = 8U;
  policy.action_window = 8U;
  policy.loop_window = 4U;
  policy.allow_service_emulation = true;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return policy;
}

/**
 * @brief Declared manual clock source; the only time seam the gateway consults.
 * @ownership Owns one shared mutable declared tick.
 * @lifetime Outlives the authority that captured its source.
 * @thread_safety Single declared user per case.
 * @failure The source never fails and never reads an ambient clock.
 */
class ManualClock final {
 public:
  /// @brief Constructs a clock at a declared initial tick.
  /// @param initial Initial declared tick.
  explicit ManualClock(val::Timestamp initial = 0) : value_(std::make_shared<val::Timestamp>(initial)) {}

  /// @brief Returns a bounded clock source over the declared tick.
  /// @return The declared clock source.
  [[nodiscard]] val::ClockSource source() const {
    const std::shared_ptr<val::Timestamp> value = value_;
    return [value]() -> std::optional<val::Timestamp> { return *value; };
  }

  /// @brief Sets the declared tick.
  /// @param value New declared tick.
  void set(val::Timestamp value) noexcept { *value_ = value; }
  /// @brief Returns the declared tick.
  /// @return The declared tick.
  [[nodiscard]] val::Timestamp get() const noexcept { return *value_; }

 private:
  std::shared_ptr<val::Timestamp> value_;
};

/// @brief One owned copy of a captured payload-free log record.
struct OwnedLogRecord final {
  /// @brief Captured outcome.
  GatewayOutcome outcome{GatewayOutcome::accepted};
  /// @brief Captured phase.
  GatewayPhase phase{GatewayPhase::transport};
  /// @brief Captured code.
  std::string code;
  /// @brief Captured logical identity.
  std::string identity;
  /// @brief Captured byte size.
  std::uint64_t size{0U};
  /// @brief Captured declared timing.
  std::uint64_t timing{0U};
};

/**
 * @brief Bounded log-capture sink.
 * @ownership Owns up to a declared bounded number of copied records.
 * @lifetime Outlives the gateway session under test.
 * @thread_safety Internally synchronized.
 * @failure Never throws; never stores a payload byte.
 */
class LogCapture final : public GatewayLogSink {
 public:
  /// @brief Records one bounded payload-free record.
  /// @param record Captured record.
  void record(const GatewayLogRecord &record) noexcept override {
    std::lock_guard<std::mutex> lock(mutex_);
    if (records_.size() >= kCaptureBound) {
      return;
    }
    OwnedLogRecord owned{};
    owned.outcome = record.outcome;
    owned.phase = record.phase;
    owned.code = std::string(record.code);
    owned.identity = std::string(record.identity);
    owned.size = record.size;
    owned.timing = record.timing;
    records_.push_back(std::move(owned));
  }

  /// @brief Returns a copy of every captured record.
  /// @return The captured records.
  [[nodiscard]] std::vector<OwnedLogRecord> records() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return records_;
  }

  /// @brief Maximum retained records.
  static constexpr std::size_t kCaptureBound = 32U;

 private:
  mutable std::mutex mutex_{};
  std::vector<OwnedLogRecord> records_{};
};

/**
 * @brief Bounded in-process `LocalIpcChannel` realization for tests.
 * @ownership Owns a fixed-capacity byte queue.
 * @lifetime Outlives the reads/writes under test.
 * @thread_safety Single declared user.
 * @failure A full write stores at most the remaining capacity; reads return at most the request.
 */
class BoundedChannel final : public LocalIpcChannel {
 public:
  /// @brief Constructs a channel with a fixed capacity.
  /// @param capacity Fixed byte capacity.
  explicit BoundedChannel(std::size_t capacity = 256U) : capacity_(capacity) {}

  /// @brief Reads at most `destination.size()` queued bytes.
  /// @param destination Bounded destination.
  /// @return Number of bytes read.
  std::size_t read(std::span<std::byte> destination) noexcept override {
    const std::size_t count = std::min(destination.size(), bytes_.size() - offset_);
    for (std::size_t index = 0U; index < count; ++index) {
      destination[index] = bytes_[offset_ + index];
    }
    offset_ += count;
    return count;
  }

  /// @brief Writes at most the remaining capacity.
  /// @param source Bounded source.
  /// @return Number of bytes written.
  std::size_t write(std::span<const std::byte> source) noexcept override {
    const std::size_t room = capacity_ - bytes_.size();
    const std::size_t count = std::min(source.size(), room);
    bytes_.insert(bytes_.end(), source.begin(), source.begin() + static_cast<std::ptrdiff_t>(count));
    return count;
  }

 private:
  std::size_t capacity_{256U};
  std::vector<std::byte> bytes_{};
  std::size_t offset_{0U};
};

/// @brief Bounded in-memory journal storage seam.
class InMemoryStorage final : public val::StimulationJournal::Storage {
 public:
  /// @brief Appends bytes.
  val::JournalStatus append(std::span<const std::uint8_t> bytes) override {
    bytes_.insert(bytes_.end(), bytes.begin(), bytes.end());
    return val::JournalStatus::Ok;
  }
  /// @brief Flushes (no-op).
  val::JournalStatus sync() override { return val::JournalStatus::Ok; }
  /// @brief Reads every durable byte.
  val::JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    out = bytes_;
    return val::JournalStatus::Ok;
  }
  /// @brief Returns the durable byte count.
  std::size_t size() override { return bytes_.size(); }
  /// @brief Truncates to a known-good offset.
  val::JournalStatus truncate(std::size_t size) override {
    bytes_.resize(size);
    return val::JournalStatus::Ok;
  }

 private:
  std::vector<std::uint8_t> bytes_{};
};

/// @brief Bounded recording host emission seam.
class RecordingEmitter final : public val::ActionEmitter {
 public:
  /// @brief Delivers one descriptor and records the call count.
  val::EmissionStatus emit(const val::SyntheticStimulationItem &item,
                           std::span<const std::byte> payload) override {
    entered_emit.store(true);
    const auto delay = delay_millis.load();
    if (delay > 0U) {
      std::this_thread::sleep_for(std::chrono::milliseconds(delay));
    }
    ++calls;
    last_request_id = item.intent.request_id;
    last_payload_size = payload.size();
    return val::EmissionStatus::Delivered;
  }

  /// @brief Number of emission calls.
  std::size_t calls{0U};
  /// @brief Last emitted request identity.
  std::uint64_t last_request_id{0U};
  /// @brief Last observed call-scoped payload size.
  std::size_t last_payload_size{0U};
  std::atomic<bool> entered_emit{false};
  std::atomic<unsigned> delay_millis{0U};
};

/**
 * @brief One bounded composing gateway fixture.
 * @ownership Owns its manager, clock, storage, journal, registry, emitter, action path, hub, and
 *            log capture.
 * @lifetime Every referenced component outlives the gateway session under test.
 * @thread_safety One declared user per case.
 * @failure An unavailable or unopened component leaves `ready()` false and fails the case.
 */
class GatewayFixture final {
 public:
  /// @brief Constructs the fixture and binds the accepted boundaries.
  GatewayFixture() : config_(make_config()) {
    val::ManagerConfig manager_config;
    manager_config.scope = manager_scope();
    manager_.emplace(manager_config);
    ready_ = manager_->register_controller(controller_identity(), "gateway-controller") ==
             val::Result::Ok;
    ready_ = ready_ &&
             manager_->time_authority().declare_clock(kDomain, clock_.source(),
                                                      val::ClockKind::WallClock, -1000000, 1000000) ==
                 val::Result::Ok;
    permit_ = make_permit();
    binding_.permit_id = std::string(kPermitId);
    binding_.session_id = std::string(kSessionId);
    binding_.plan_digest = std::string(kPlanDigest);
    binding_.graph_digest = std::string(kGraphDigest);
    binding_.permit = permit_;
    binding_.has_permit = true;
    binding_.controller = controller_identity();
    binding_.context = context_for(permit_);
    binding_.arrival_domain = kDomain;
    binding_.arrival_domain_name = std::string(kClockDomainName);
    binding_.arrival_tick = clock_.get();
    binding_.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
    binding_.blueprint_id = "gateway.blueprint";
    binding_.contract_id = std::string(kContractId);
    bind();
  }

  /// @brief Copy construction is deleted; the fixture owns a mutex-bearing manager.
  GatewayFixture(const GatewayFixture &) = delete;
  /// @brief Copy assignment is deleted.
  GatewayFixture &operator=(const GatewayFixture &) = delete;

  /// @brief Opens the accepted journal and action path over the fixture components.
  /// @return `true` when the journal and guard both opened.
  bool open_path() {
    val::JournalConfig journal_config;
    journal_config.max_record_bytes = 320U;
    journal_config.max_retained_records = 32U;
    journal_config.max_journal_bytes = 16U * 1024U;
    ready_ = ready_ && journal_.open(storage_, journal_config) == val::JournalStatus::Ok;
    val::ActionPathConfig action_config;
    action_config.max_pending_actions = 8U;
    action_config.max_lineage_entries = 8U;
    action_config.max_drain_steps = 8U;
    action_config.max_payload_bytes = 64U;
    action_config.late_tolerance = 100;
    action_config.tool = tag("tool");
    path_.emplace(action_config, journal_, registry_, emitter_);
    ready_ = ready_ && path_->open(permit_, make_policy(permit_)) == val::GuardStatus::Ok;
    bind();
    return ready_;
  }

  /// @brief Points the dependency bundle at the owned accepted boundaries.
  void bind() {
    dependencies_.sessions = manager_.has_value() ? &*manager_ : nullptr;
    dependencies_.time_authority =
        manager_.has_value() ? &manager_->time_authority() : nullptr;
    dependencies_.journal = &journal_;
    dependencies_.guard = nullptr;
    dependencies_.actions = path_.has_value() ? &*path_ : nullptr;
    dependencies_.leases = &registry_;
    dependencies_.observations = &hub_;
    dependencies_.log = &log_;
  }

  /// @brief Builds the default bounded gateway configuration.
  /// @return The validated gateway configuration.
  [[nodiscard]] const GatewayConfig &config() const noexcept { return config_; }
  /// @brief Returns the dependency bundle.
  [[nodiscard]] const GatewayDependencies &dependencies() const noexcept { return dependencies_; }
  /// @brief Returns the resolved session binding.
  [[nodiscard]] GatewaySessionBinding binding() const { return binding_; }
  /// @brief Returns the manual clock.
  [[nodiscard]] ManualClock &clock() noexcept { return clock_; }
  /// @brief Returns the recording emitter.
  [[nodiscard]] RecordingEmitter &emitter() noexcept { return emitter_; }
  /// @brief Returns the log capture.
  [[nodiscard]] LogCapture &log() noexcept { return log_; }
  /// @brief Returns the accepted lease registry.
  [[nodiscard]] val::ServiceEmulationRegistry &registry() noexcept { return registry_; }
  /// @brief Returns the accepted observation hub.
  [[nodiscard]] ObservationHub &hub() noexcept { return hub_; }
  /// @brief Returns the bound permit.
  [[nodiscard]] const val::Permit &permit() const noexcept { return permit_; }
  /// @brief Reports whether every bounded component is ready.
  [[nodiscard]] bool ready() const noexcept { return ready_; }

 private:
  GatewayConfig config_;
  ManualClock clock_{0};
  std::optional<val::SessionManager> manager_{};
  val::Permit permit_{};
  GatewaySessionBinding binding_{};
  GatewayDependencies dependencies_{};
  InMemoryStorage storage_{};
  val::StimulationJournal journal_{};
  val::ServiceEmulationRegistry registry_{4U};
  RecordingEmitter emitter_{};
  std::optional<val::StimulationActionPath> path_{};
  ObservationHub hub_{};
  LogCapture log_{};
  bool ready_{false};
};

/// @brief Builds a bounded `ArmSessionRequest` for the fixture.
/// @param major Declared protocol major.
/// @return The bounded request.
[[nodiscard]] inline v1::ArmSessionRequest arm_request(std::uint32_t major = 1U) {
  v1::ArmSessionRequest request;
  request.set_permit_id(std::string(kPermitId));
  request.set_session_id(std::string(kSessionId));
  request.set_plan_digest(std::string(kPlanDigest));
  request.set_graph_digest(std::string(kGraphDigest));
  request.mutable_protocol()->set_major(major);
  request.mutable_protocol()->set_minor(0U);
  request.set_deadline_millis(1000U);
  return request;
}

/// @brief Builds a bounded `SubmitStimulationRequest` for the fixture.
/// @param kind Declared action kind.
/// @param id Decimal request identity.
/// @param payload_bytes Declared payload size.
/// @return The bounded request.
[[nodiscard]] inline v1::SubmitStimulationRequest
stimulation_request(v1::StimulationActionKind kind = v1::STIMULATION_ACTION_INJECT_SIGNAL,
                    std::string id = "1", std::uint32_t payload_bytes = 0U) {
  v1::SubmitStimulationRequest request;
  request.set_session_id(std::string(kSessionId));
  request.set_request_id(std::move(id));
  request.mutable_action()->set_kind(kind);
  request.mutable_action()->set_action_id("action-1");
  request.mutable_action()->set_correlation_id("1000");
  request.set_target_endpoint("target.alpha");
  request.set_contract_id("gateway.contract");
  switch (kind) {
  case v1::STIMULATION_ACTION_INJECT_MESSAGE:
    request.set_interaction(v1::INTERACTION_KIND_MESSAGE);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  case v1::STIMULATION_ACTION_INVOKE_SERVICE:
    request.set_interaction(v1::INTERACTION_KIND_REQUEST);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  case v1::STIMULATION_ACTION_EMULATE_SERVICE:
    request.set_interaction(v1::INTERACTION_KIND_RESPONSE);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  case v1::STIMULATION_ACTION_INJECT_SIGNAL:
  default:
    request.set_interaction(v1::INTERACTION_KIND_SIGNAL);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  }
  request.mutable_schedule()->set_mode(v1::SCHEDULE_IMMEDIATE);
  request.mutable_schedule()->set_clock_domain("clock.gateway");
  request.set_payload_bytes(payload_bytes);
  request.set_deadline_millis(1000U);
  return request;
}

/// @brief Returns a bounded scratch path under the declared build-tree scratch directory.
/// @param name Bounded file name.
/// @return The scratch path.
[[nodiscard]] inline std::string scratch_path(std::string_view name) {
  const std::string directory = XCOM_T031_SCRATCH_DIR;
  ::mkdir(directory.c_str(), 0700);
  return directory + "/" + std::string(name);
}

}  // namespace xverse::xcom::tool_gateway_test

#endif  // XVERSE_XCOM_TOOL_GATEWAY_SUPPORT_HPP_
