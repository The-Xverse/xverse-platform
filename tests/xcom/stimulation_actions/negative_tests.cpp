/**
 * @file negative_tests.cpp
 * @brief T028 zero-mutation and zero-emission negative cases, the closed/capacity precondition
 *        reject, and a bounded payload-free declaration inspection.
 * @ownership Each case owns the permit, policy, config, journal storage, registry, emitter,
 *            action path, and the bounded scan of the committed header and source.
 * @lifetime The journal, registry, and emitter outlive the action path; snapshots are copies.
 * @thread_safety Single-threaded.
 * @bounds Finite decline families, bounded operation sequences, and one comment-stripped read of
 *          at most 128 KiB per scanned file.
 * @failure A decline that mutates operational state or emits, a precondition that reaches the
 *          guard or journal, or a forbidden retention/I-O vocabulary fails the case.
 */

#include "xverse/xcom/stimulation_actions.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cctype>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;

// CHK-05 / NEG-03: non-vacuous compile-time rules against payload-bearing values.
static_assert(!std::is_constructible_v<val::ActionPathConfig, std::string_view>,
              "ActionPathConfig must reject free-form text");
static_assert(!std::is_constructible_v<val::ActionPathConfig, std::vector<std::uint8_t>>,
              "ActionPathConfig must reject a payload byte container");
static_assert(!std::is_constructible_v<val::EmulationLease, std::string_view>,
              "EmulationLease must reject free-form text");
static_assert(!std::is_constructible_v<val::PendingAction, std::vector<std::uint8_t>>,
              "PendingAction must reject a payload byte container");
static_assert(!std::is_constructible_v<val::SyntheticStimulationItem, std::span<const std::byte>>,
              "SyntheticStimulationItem must not retain a payload view");
static_assert(!std::is_copy_constructible_v<val::StimulationActionPath>,
              "StimulationActionPath must not be copyable");
static_assert(!std::is_move_constructible_v<val::StimulationActionPath>,
              "StimulationActionPath must not be movable");
static_assert(!std::is_copy_constructible_v<val::ServiceEmulationRegistry>,
              "ServiceEmulationRegistry must not be copyable");

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr val::Timestamp kUntil = 100;
constexpr std::size_t kMaximumSourceBytes = 131072U;

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
  config.max_pending_actions = 2U;
  config.max_lineage_entries = 2U;
  config.max_drain_steps = 2U;
  config.max_payload_bytes = 16U;
  config.tool = tag("tool");
  return config;
}

[[nodiscard]] val::StimulationRequest make_signal(const val::Permit &permit, std::uint64_t id,
                                                  bool immediate = true) {
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
  request.scheduled_at = 10;
  request.immediate = immediate;
  request.request_id = id;
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

/// @brief Storage seam that fails every append, to force a journal-write decline.
class FailingStorage final : public val::StimulationJournal::Storage {
public:
  val::JournalStatus append(std::span<const std::uint8_t>) override {
    return val::JournalStatus::WriteFailed;
  }
  val::JournalStatus sync() override { return val::JournalStatus::Ok; }
  val::JournalStatus read_all(std::vector<std::uint8_t> &out) override {
    out.clear();
    return val::JournalStatus::Ok;
  }
  [[nodiscard]] std::size_t size() override { return 0U; }
  val::JournalStatus truncate(std::size_t) override { return val::JournalStatus::Ok; }
};

class CountingEmitter final : public val::ActionEmitter {
public:
  val::EmissionStatus emit(const val::SyntheticStimulationItem &,
                           std::span<const std::byte>) override {
    ++calls;
    return val::EmissionStatus::Delivered;
  }
  std::size_t calls{0};
};

/// @brief Operational fields that a decline must leave unchanged.
struct OperationalState {
  bool open{false};
  std::size_t pending{0};
  std::size_t lineage{0};
  std::uint64_t emitted{0};
  std::uint64_t evidence_incomplete{0};
  val::DrainState drain_state{val::DrainState::Idle};

  [[nodiscard]] static OperationalState of(const val::ActionPathSnapshot &snapshot) {
    return OperationalState{snapshot.open,          snapshot.pending,
                            snapshot.lineage_entries, snapshot.emitted,
                            snapshot.evidence_incomplete, snapshot.drain_state};
  }
  friend bool operator==(const OperationalState &, const OperationalState &) = default;
};

/// @brief Lease-table fields that a decline must leave unchanged (declared counters may advance).
struct LeaseOperationalState {
  std::size_t active{0};
  std::size_t released{0};
  std::size_t quarantined{0};
  std::size_t expired{0};

  [[nodiscard]] static LeaseOperationalState of(const val::LeaseSnapshot &snapshot) {
    return LeaseOperationalState{snapshot.active, snapshot.released, snapshot.quarantined,
                                 snapshot.expired};
  }
  friend bool operator==(const LeaseOperationalState &, const LeaseOperationalState &) = default;
};

[[nodiscard]] bool is_word_char(char character) noexcept {
  return (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9') ||
         character == '_';
}

[[nodiscard]] bool contains_word(const std::string_view haystack,
                                 const std::string_view needle) noexcept {
  std::size_t position = haystack.find(needle);
  while (position != std::string_view::npos) {
    const bool left_ok = position == 0U || !is_word_char(haystack[position - 1U]);
    const std::size_t after = position + needle.size();
    const bool right_ok = after >= haystack.size() || !is_word_char(haystack[after]);
    if (left_ok && right_ok) {
      return true;
    }
    position = haystack.find(needle, position + 1U);
  }
  return false;
}

/** @return the comment-stripped, lowercased code content, or empty when it cannot be read. */
[[nodiscard]] std::string read_lowercase_code(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    return {};
  }
  std::string raw;
  raw.resize(kMaximumSourceBytes);
  stream.read(raw.data(), static_cast<std::streamsize>(raw.size()));
  raw.resize(static_cast<std::size_t>(stream.gcount()));

  std::string code;
  code.reserve(raw.size());
  enum class State { code, line_comment, block_comment, string_literal, char_literal };
  State state = State::code;
  char previous = '\0';
  for (const char character : raw) {
    switch (state) {
    case State::code:
      if (character == '/' && previous == '/') {
        code.pop_back();
        state = State::line_comment;
      } else if (character == '*' && previous == '/') {
        code.pop_back();
        state = State::block_comment;
      } else if (character == '"') {
        state = State::string_literal;
        code.push_back(character);
      } else if (character == '\'') {
        state = State::char_literal;
        code.push_back(character);
      } else {
        code.push_back(character);
      }
      break;
    case State::line_comment:
      if (character == '\n') {
        state = State::code;
        code.push_back(character);
      }
      break;
    case State::block_comment:
      if (character == '/' && previous == '*') {
        state = State::code;
      }
      break;
    case State::string_literal:
      code.push_back(character);
      if (character == '"' && previous != '\\') {
        state = State::code;
      }
      break;
    case State::char_literal:
      code.push_back(character);
      if (character == '\'' && previous != '\\') {
        state = State::code;
      }
      break;
    }
    previous = character;
  }
  for (char &character : code) {
    character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
  }
  return code;
}

} // namespace

/** T28-TS-016 (CHK-14, CHK-21, NEG-25..NEG-27): every decline mutates nothing and emits nothing. */
TEST(XcomStimulationActionsNegative, ActionPathDeclineZeroMutationAndZeroEmission) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy policy = make_policy(permit);
  val::ActionPathConfig config = make_config();

  const auto assert_decline = [](std::optional<val::StimulationActionPath> &path,
                                 MemoryStorage &storage, CountingEmitter &emitter,
                                 const val::ServiceEmulationRegistry &registry,
                                 const val::StimulationRequest &request,
                                 val::LifecycleState state, const val::ResolvedTime &time,
                                 std::span<const std::byte> payload,
                                 val::ActionStatus expected) {
    const std::size_t before_calls = emitter.calls;
    const std::size_t before_bytes = storage.bytes_.size();
    const LeaseOperationalState before_leases = LeaseOperationalState::of(registry.snapshot());
    std::optional<OperationalState> before;
    if (path.has_value()) {
      before = OperationalState::of(path->snapshot());
    }
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(path->execute(request, state, time, payload, diagnostic), expected);
    if (before.has_value()) {
      EXPECT_EQ(OperationalState::of(path->snapshot()), *before);
    }
    EXPECT_EQ(emitter.calls, before_calls);
    EXPECT_EQ(storage.bytes_.size(), before_bytes);
    EXPECT_EQ(LeaseOperationalState::of(registry.snapshot()), before_leases);
  };

  // Closed path.
  {
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 8U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    std::optional<val::StimulationActionPath> path;
    path.emplace(config, journal, registry, emitter);
    assert_decline(path, storage, emitter, registry, make_signal(permit, 1U),
                   val::LifecycleState::active, in_window(), {}, val::ActionStatus::NotOpen);
  }
  // Malformed request and over-bound payload, then a guard rejection, a guard failure, a loop, a
  // capacity decline, a non-active session, and a lease conflict, each on one open path.
  {
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 8U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    std::optional<val::StimulationActionPath> path;
    path.emplace(config, journal, registry, emitter);
    ASSERT_EQ(path->open(permit, policy), val::GuardStatus::Ok);

    val::StimulationRequest malformed = make_signal(permit, 0U);
    assert_decline(path, storage, emitter, registry, malformed, val::LifecycleState::active,
                   in_window(), {}, val::ActionStatus::RejectedConfiguration);

    val::StimulationRequest over_bound = make_signal(permit, 2U);
    std::vector<std::byte> payload(config.max_payload_bytes + 1U);
    assert_decline(path, storage, emitter, registry, over_bound, val::LifecycleState::active,
                   in_window(), payload, val::ActionStatus::RejectedConfiguration);

    val::StimulationRequest mismatched = make_signal(permit, 3U);
    mismatched.target = tag("target.beta");
    assert_decline(path, storage, emitter, registry, mismatched, val::LifecycleState::active,
                   in_window(), {}, val::ActionStatus::Rejected);

    val::StimulationRequest unmapped = make_signal(permit, 4U);
    assert_decline(path, storage, emitter, registry, unmapped, val::LifecycleState::active,
                   val::ResolvedTime{kDomain, 50, val::Result::MissingMapping}, {},
                   val::ActionStatus::Failed);

    val::StimulationRequest inactive = make_signal(permit, 5U);
    assert_decline(path, storage, emitter, registry, inactive, val::LifecycleState::armed,
                   in_window(), {}, val::ActionStatus::NotActive);

    // Fill the bounded queue, then a second scheduled action is a capacity decline.
    val::ActionDiagnostic scratch;
    ASSERT_EQ(path->execute(make_signal(permit, 6U, false), val::LifecycleState::active,
                            in_window(), {}, scratch),
              val::ActionStatus::Queued);
    ASSERT_EQ(path->execute(make_signal(permit, 7U, false), val::LifecycleState::active,
                            in_window(), {}, scratch),
              val::ActionStatus::Queued);
    assert_decline(path, storage, emitter, registry, make_signal(permit, 8U, false),
                   val::LifecycleState::active, in_window(), {}, val::ActionStatus::CapacityExhausted);
    // The queue still has its two retained scheduled actions, so a loop identity on an emitted
    // action is exercised on a second path.
  }
  // A prohibited reinjection and a journal-write decline.
  {
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 8U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    std::optional<val::StimulationActionPath> path;
    path.emplace(config, journal, registry, emitter);
    ASSERT_EQ(path->open(permit, policy), val::GuardStatus::Ok);
    val::ActionDiagnostic scratch;
    ASSERT_EQ(path->execute(make_signal(permit, 9U), val::LifecycleState::active, in_window(), {},
                            scratch),
              val::ActionStatus::Emitted);
    val::StimulationRequest loop = make_signal(permit, 10U);
    loop.causation_id = 9U;
    assert_decline(path, storage, emitter, registry, loop, val::LifecycleState::active, in_window(),
                   {}, val::ActionStatus::Rejected);
  }
  // A lease conflict mutates no lease and emits nothing.
  {
    const val::Permit permit = make_permit();
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 8U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    const val::EndpointGeneration occupied{permit.session_id(), tag("svc.alpha"), 9U,
                                           permit.plan_digest()};
    ASSERT_EQ(registry.acquire(occupied, 500U, kDomain, 0, kUntil), val::LeaseStatus::Ok);
    CountingEmitter emitter;
    std::optional<val::StimulationActionPath> path;
    path.emplace(config, journal, registry, emitter);
    ASSERT_EQ(path->open(permit, make_policy(permit)), val::GuardStatus::Ok);
    assert_decline(path, storage, emitter, registry, make_emulate(permit, 11U),
                   val::LifecycleState::active, in_window(), {}, val::ActionStatus::LeaseConflict);
  }
  // T028-IR2-F01: a guard quota decline on an emulation action acquires no lease, so the whole
  // lease table (including its acquisition and release accounting) is byte-identical.
  {
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 8U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    std::optional<val::StimulationActionPath> path;
    path.emplace(config, journal, registry, emitter);
    ASSERT_EQ(path->open(permit, make_policy(permit, 1U)), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    ASSERT_EQ(path->execute(make_signal(permit, 30U), val::LifecycleState::active, in_window(), {},
                            diagnostic),
              val::ActionStatus::Emitted);
    const val::LeaseSnapshot before_leases = registry.snapshot();
    const std::size_t before_calls = emitter.calls;
    EXPECT_EQ(path->execute(make_emulate(permit, 31U), val::LifecycleState::active, in_window(), {},
                            diagnostic),
              val::ActionStatus::Rejected);
    EXPECT_EQ(diagnostic.guard_reason, val::GuardReason::QuotaExhausted);
    EXPECT_EQ(emitter.calls, before_calls);
    EXPECT_EQ(registry.snapshot(), before_leases);
    EXPECT_EQ(registry.snapshot().acquisitions, 0U);
    EXPECT_EQ(registry.snapshot().released, 0U);
  }
  // A journal-write decline on the intent append mutates no durable record and emits nothing.
  {
    FailingStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    journal_config.max_retained_records = 8U;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    std::optional<val::StimulationActionPath> path;
    path.emplace(config, journal, registry, emitter);
    ASSERT_EQ(path->open(permit, make_policy(permit)), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(path->execute(make_signal(permit, 12U), val::LifecycleState::active, in_window(), {},
                            diagnostic),
              val::ActionStatus::JournalFailed);
    EXPECT_EQ(emitter.calls, 0U);
    EXPECT_EQ(storage.size(), 0U);
    EXPECT_EQ(journal.snapshot().retained_records, 0U);
  }
}

/** T28-TS-017 (CHK-18, CHK-21, NEG-33, NEG-34): closed and capacity declines precede the guard. */
TEST(XcomStimulationActionsNegative, ActionPathClosedAndCapacityReject) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy quota_one = make_policy(permit, 1U);
  {
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    val::ActionPathConfig config = make_config();
    val::StimulationActionPath path{config, journal, registry, emitter};
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(path.execute(make_signal(permit, 20U), val::LifecycleState::active, in_window(), {},
                           diagnostic),
              val::ActionStatus::NotOpen);
    EXPECT_EQ(emitter.calls, 0U);
    EXPECT_EQ(storage.bytes_.size(), 0U);
    // An invalid configuration is rejected and leaves the path closed.
    val::ActionPathConfig invalid = config;
    invalid.max_pending_actions = 0U;
    std::optional<val::StimulationActionPath> invalid_path;
    invalid_path.emplace(invalid, journal, registry, emitter);
    EXPECT_EQ(invalid_path->open(permit, quota_one), val::GuardStatus::RejectedConfiguration);
    EXPECT_FALSE(invalid_path->is_open());
  }
  // A malformed request consumes no guard quota; the next valid request is still emitted.
  {
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    val::ActionPathConfig config = make_config();
    val::StimulationActionPath path{config, journal, registry, emitter};
    ASSERT_EQ(path.open(permit, quota_one), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(path.execute(make_signal(permit, 0U), val::LifecycleState::active, in_window(), {},
                           diagnostic),
              val::ActionStatus::RejectedConfiguration);
    EXPECT_EQ(path.execute(make_signal(permit, 21U), val::LifecycleState::active, in_window(), {},
                           diagnostic),
              val::ActionStatus::Emitted);
  }
  // A full pending queue consumes no guard quota; the next immediate request is still emitted.
  {
    MemoryStorage storage;
    val::StimulationJournal journal;
    val::JournalConfig journal_config;
    ASSERT_EQ(journal.open(storage, journal_config), val::JournalStatus::Ok);
    val::ServiceEmulationRegistry registry{4U};
    CountingEmitter emitter;
    val::ActionPathConfig config = make_config();
    config.max_pending_actions = 1U;
    val::StimulationActionPath path{config, journal, registry, emitter};
    ASSERT_EQ(path.open(permit, make_policy(permit, 2U)), val::GuardStatus::Ok);
    val::ActionDiagnostic diagnostic;
    EXPECT_EQ(path.execute(make_signal(permit, 22U, false), val::LifecycleState::active, in_window(),
                           {}, diagnostic),
              val::ActionStatus::Queued);
    EXPECT_EQ(path.execute(make_signal(permit, 23U, false), val::LifecycleState::active, in_window(),
                           {}, diagnostic),
              val::ActionStatus::CapacityExhausted);
    EXPECT_EQ(path.execute(make_signal(permit, 24U), val::LifecycleState::active, in_window(), {},
                           diagnostic),
              val::ActionStatus::Emitted);
  }
}

/** T28-TS-018 (CHK-05, CHK-20, NEG-02, NEG-03, NEG-30): payload-free offline declaration surface. */
TEST(XcomStimulationActionsNegative, ActionPathPayloadFreeDeclarationInspection) {
  constexpr std::array<std::string_view, 20U> forbidden{{
      "network", "socket", "resolver", "tls",      "ssl",        "dlopen",
      "getenv",  "subprocess", "filesystem", "ifstream", "ofstream", "fopen",
      "storage", "decoder", "redaction",  "dashboard", "export",  "telemetry",
      "opentelemetry", "publish"}};
  constexpr std::array<const char *, 2U> scanned_paths{{XCOM_T028_HEADER_PATH,
                                                        XCOM_T028_SOURCE_PATH}};
  for (const char *path : scanned_paths) {
    const std::string code = read_lowercase_code(path);
    ASSERT_FALSE(code.empty()) << "committed action-path file is unreadable";
    for (const std::string_view token : forbidden) {
      EXPECT_FALSE(contains_word(code, token)) << "forbidden vocabulary '" << token << "'";
    }
  }
  EXPECT_LE(sizeof(val::ActionPathConfig), 512U);
  EXPECT_LE(sizeof(val::PendingAction), 768U);
  EXPECT_LE(sizeof(val::SyntheticStimulationItem), 320U);
  EXPECT_LE(sizeof(val::ActionDiagnostic), 256U);
  EXPECT_LE(sizeof(val::CompletionReport), 64U);
  EXPECT_LE(val::kActionPathMaxPendingActions, 64U);
  EXPECT_LE(val::kActionPathMaxActiveLeases, 64U);
}
