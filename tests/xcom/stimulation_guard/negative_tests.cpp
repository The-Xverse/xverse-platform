/**
 * @file negative_tests.cpp
 * @brief T027 zero-mutation/zero-emission negative cases, the closed-guard precondition, the
 *        bounded-configuration matrix, and a payload-free declaration inspection.
 * @ownership Each case owns the permit, policy, guard, requests, snapshots, and scanned header.
 * @lifetime One guard per family; snapshot copies bracket each evaluation.
 * @thread_safety Single-threaded.
 * @bounds Finite declared rejection families, ≤ 8 evaluations, one bounded comment-stripped header
 *          read of at most 128 KiB.
 * @failure A rejection that mutates operational state, a guard surface that exposes an emission
 *          entry point, or an accepted invalid bound fails the case.
 */

#include "xverse/xcom/stimulation_guard.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cctype>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>

namespace val = xverse::xcom::validation;
using xverse::xcom::EndpointDirection;
using xverse::xcom::InteractionKind;

// CHK-05 / NEG-03: a non-vacuous compile-time negative rule against payload-bearing values.
static_assert(!std::is_constructible_v<val::SchemaKey, std::string_view>,
              "SchemaKey must reject free-form text");
static_assert(!std::is_constructible_v<val::StimulationRequest, std::string_view>,
              "StimulationRequest must reject free-form text");
static_assert(!std::is_constructible_v<val::StimulationRequest, std::vector<std::uint8_t>>,
              "StimulationRequest must reject a payload byte container");
static_assert(!std::is_constructible_v<val::StimulationPolicy, std::string_view>,
              "StimulationPolicy must reject free-form text");
static_assert(!std::is_copy_constructible_v<val::StimulationGuard>,
              "StimulationGuard must not be copyable");
static_assert(!std::is_move_constructible_v<val::StimulationGuard>,
              "StimulationGuard must not be movable");

namespace {

constexpr val::ClockDomainId kDomain = 7U;
constexpr std::size_t kMaximumHeaderBytes = 131072U;

[[nodiscard]] val::Tag tag(std::string_view text) { return val::Tag::make(text).value(); }

[[nodiscard]] val::Permit make_permit() {
  val::PermitBuilder builder;
  val::SessionId session{};
  session[0] = 1U;
  val::PlanDigest digest{};
  digest[0] = 2U;
  builder.set_session_id(session);
  builder.set_plan_digest(digest);
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
  const val::Result result = builder.build(permit);
  EXPECT_EQ(result, val::Result::Ok);
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
  policy.max_actions_per_session = 8U;
  policy.max_actions_per_window = 4U;
  policy.action_window = 4U;
  policy.loop_window = 4U;
  policy.allow_service_emulation = true;
  policy.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
  return policy;
}

[[nodiscard]] val::StimulationRequest make_request(const val::Permit &permit, std::uint64_t id) {
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
  request.immediate = false;
  request.request_id = id;
  return request;
}

[[nodiscard]] val::ResolvedTime in_window() {
  return val::ResolvedTime{kDomain, 50, val::Result::Ok};
}

[[nodiscard]] bool operational_equal(const val::GuardSnapshot &lhs,
                                     const val::GuardSnapshot &rhs) {
  return lhs.open == rhs.open && lhs.actions_authorized == rhs.actions_authorized &&
         lhs.actions_remaining == rhs.actions_remaining && lhs.window_actions == rhs.window_actions &&
         lhs.window_remaining == rhs.window_remaining && lhs.loop_entries == rhs.loop_entries;
}

/** @return true when the byte can appear inside a scanned vocabulary word. */
[[nodiscard]] bool is_word_char(char character) noexcept {
  return (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9') ||
         character == '_';
}

/** @return true when the lowercase haystack contains the needle at a word boundary. */
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
  raw.resize(kMaximumHeaderBytes);
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

/** T27-TS-016 (CHK-14, CHK-15, CHK-21): zero mutation, zero emission, payload-free declarations. */
TEST(XcomStimulationGuardNegative, GuardRejectionZeroMutationAndNoEmission) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy base = make_policy(permit);
  val::GuardDiagnostic diagnostic;

  const auto rejects = [&](const val::StimulationPolicy &policy, val::StimulationRequest request,
                           val::LifecycleState state, val::ResolvedTime resolved,
                           val::GuardReason expected) {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    const val::GuardSnapshot before = guard.snapshot();
    const val::GuardOutcome outcome = guard.authorize(request, state, resolved, diagnostic);
    EXPECT_NE(outcome, val::GuardOutcome::Authorized);
    EXPECT_EQ(diagnostic.reason, expected);
    EXPECT_TRUE(operational_equal(before, guard.snapshot()));
  };

  val::StimulationRequest malformed = make_request(permit, 301U);
  malformed.request_id = 0U;
  rejects(base, malformed, val::LifecycleState::active, in_window(),
          val::GuardReason::RejectedConfiguration);

  val::StimulationRequest foreign = make_request(permit, 302U);
  foreign.session_id[0] = 0xEEU;
  rejects(base, foreign, val::LifecycleState::active, in_window(), val::GuardReason::PermitMismatch);

  rejects(base, make_request(permit, 303U), val::LifecycleState::revoked, in_window(),
          val::GuardReason::Revoked);

  val::StimulationRequest bad_schema = make_request(permit, 304U);
  bad_schema.schema = val::SchemaKey{tag("other.v1"), tag("1")};
  rejects(base, bad_schema, val::LifecycleState::active, in_window(), val::GuardReason::SchemaMismatch);

  val::StimulationRequest bad_direction = make_request(permit, 305U);
  bad_direction.direction = EndpointDirection::consume;
  rejects(base, bad_direction, val::LifecycleState::active, in_window(),
          val::GuardReason::DirectionMismatch);

  val::StimulationRequest bad_interaction = make_request(permit, 306U);
  bad_interaction.interaction = InteractionKind::service_request;
  rejects(base, bad_interaction, val::LifecycleState::active, in_window(),
          val::GuardReason::InteractionMismatch);

  val::StimulationRequest bad_target = make_request(permit, 307U);
  bad_target.target = tag("target.beta");
  rejects(base, bad_target, val::LifecycleState::active, in_window(), val::GuardReason::TargetMismatch);

  val::StimulationPolicy signal_only = make_policy(permit);
  signal_only.allowed_actions = val::to_stimulation_mask(val::StimulationAction::InjectSignal);
  val::StimulationRequest disallowed = make_request(permit, 308U);
  disallowed.action = val::StimulationAction::InjectMessage;
  disallowed.interaction = InteractionKind::message_event;
  rejects(signal_only, disallowed, val::LifecycleState::active, in_window(),
          val::GuardReason::ActionMismatch);

  val::StimulationRequest unowned = make_request(permit, 309U);
  unowned.action = val::StimulationAction::InvokeService;
  unowned.interaction = InteractionKind::service_request;
  unowned.direction = EndpointDirection::request;
  rejects(base, unowned, val::LifecycleState::active, in_window(), val::GuardReason::OwnershipConflict);

  val::StimulationRequest out_of_window = make_request(permit, 310U);
  rejects(base, out_of_window, val::LifecycleState::active,
          val::ResolvedTime{kDomain, 100, val::Result::Ok}, val::GuardReason::TimeOutOfWindow);

  val::StimulationRequest unmapped = make_request(permit, 311U);
  rejects(base, unmapped, val::LifecycleState::active,
          val::ResolvedTime{kDomain, 50, val::Result::MissingMapping}, val::GuardReason::TimeUnmapped);

  // Quota exhaustion mutates no tally.
  {
    val::StimulationPolicy policy = make_policy(permit);
    policy.max_actions_per_session = 1U;
    policy.max_actions_per_window = 1U;
    policy.action_window = 1U;
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
    ASSERT_EQ(guard.authorize(make_request(permit, 312U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    const val::GuardSnapshot before = guard.snapshot();
    ASSERT_EQ(guard.authorize(make_request(permit, 313U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::QuotaExhausted);
    EXPECT_TRUE(operational_equal(before, guard.snapshot()));
  }

  // Prohibited reinjection mutates no loop entry.
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, base), val::GuardStatus::Ok);
    ASSERT_EQ(guard.authorize(make_request(permit, 314U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Authorized);
    const val::GuardSnapshot before = guard.snapshot();
    val::StimulationRequest reinjection = make_request(permit, 315U);
    reinjection.causation_id = 314U;
    ASSERT_EQ(guard.authorize(reinjection, val::LifecycleState::active, in_window(), diagnostic),
              val::GuardOutcome::Rejected);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::LoopBound);
    EXPECT_TRUE(operational_equal(before, guard.snapshot()));
  }

  // Declaration inspection: no emission/action/lease vocabulary in the comment-stripped header or
  // implementation source.
  constexpr std::array<std::string_view, 17U> forbidden{{
      "emit",      "emission", "route",    "inject",     "invoke",   "emulate",
      "emulation", "lease",    "provider", "callback",   "transport", "socket",
      "network",   "dlopen",   "getenv",   "subprocess", "publish"}};
  constexpr std::array<const char *, 2U> scanned_paths{{XCOM_T027_HEADER_PATH,
                                                        XCOM_T027_SOURCE_PATH}};
  for (const char *path : scanned_paths) {
    const std::string code = read_lowercase_code(path);
    ASSERT_FALSE(code.empty()) << "committed guard file is unreadable: " << path;
    for (const std::string_view token : forbidden) {
      EXPECT_FALSE(contains_word(code, token)) << "forbidden emission vocabulary '" << token << "'";
    }
  }
  EXPECT_LE(sizeof(val::StimulationRequest), 512U);
  EXPECT_LE(sizeof(val::StimulationPolicy), 4096U);
  EXPECT_LE(sizeof(val::SchemaKey), 128U);
  EXPECT_LE(sizeof(val::ServiceOwner), 128U);
  EXPECT_LE(sizeof(val::GuardSnapshot), 128U);
}

/** T27-TS-017 (CHK-15, CHK-15): a closed guard authorizes nothing and mutates nothing. */
TEST(XcomStimulationGuardNegative, GuardClosedGuardRejects) {
  val::StimulationGuard guard;
  EXPECT_FALSE(guard.is_open());
  EXPECT_EQ(guard.status(), val::GuardStatus::NotOpen);
  const val::GuardSnapshot before = guard.snapshot();
  EXPECT_EQ(before, (val::GuardSnapshot{}));

  val::PermitBuilder builder;
  val::SessionId session{};
  session[0] = 1U;
  builder.set_session_id(session);
  val::PlanDigest digest{};
  digest[0] = 2U;
  builder.set_plan_digest(digest);
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
  ASSERT_EQ(builder.build(permit), val::Result::Ok);

  val::StimulationRequest request = make_request(permit, 321U);
  val::GuardDiagnostic diagnostic;
  for (std::size_t attempt = 0; attempt < 3U; ++attempt) {
    request.request_id = 321U + attempt;
    const val::GuardOutcome outcome =
        guard.authorize(request, val::LifecycleState::active, in_window(), diagnostic);
    EXPECT_EQ(outcome, val::GuardOutcome::Failed);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::NotOpen);
    EXPECT_EQ(val::outcome_of(diagnostic.reason), val::GuardOutcome::Failed);
  }
  EXPECT_EQ(guard.snapshot(), before);
}

/** T27-TS-018 (CHK-18): the remaining §5.1 bound rows and an over-full schema table. */
TEST(XcomStimulationGuardNegative, GuardBoundsConfigMatrix) {
  const val::Permit permit = make_permit();
  const val::StimulationPolicy base = make_policy(permit);

  const auto rejects = [&](const val::StimulationPolicy &policy) {
    val::StimulationGuard guard;
    EXPECT_EQ(guard.open(permit, policy), val::GuardStatus::RejectedConfiguration);
    EXPECT_EQ(guard.status(), val::GuardStatus::NotOpen);
    EXPECT_EQ(guard.snapshot(), (val::GuardSnapshot{}));
  };

  {
    val::StimulationPolicy policy = base;
    policy.allowed_schemas.assign(val::kGuardMaxSchemas, val::SchemaKey{tag("s.v1"), tag("1")});
    val::StimulationGuard guard;
    EXPECT_EQ(guard.open(permit, policy), val::GuardStatus::Ok);
  }
  {
    val::StimulationPolicy policy = base;
    policy.allowed_schemas.assign(val::kGuardMaxSchemas + 1U, val::SchemaKey{tag("s.v1"), tag("1")});
    rejects(policy);
  }
  { val::StimulationPolicy policy = base; policy.allowed_interactions = 0U; rejects(policy); }
  { val::StimulationPolicy policy = base; policy.allowed_interactions = 0x10U; rejects(policy); }
  { val::StimulationPolicy policy = base; policy.allowed_directions = 0U; rejects(policy); }
  { val::StimulationPolicy policy = base; policy.allowed_directions = 0x10U; rejects(policy); }
  {
    val::StimulationPolicy policy = base;
    policy.allowed_schemas = {val::SchemaKey{tag("s.v1"), val::Tag(std::string(64U, 'x'))}};
    rejects(policy);
  }
  { val::StimulationPolicy policy = base; policy.loop_window = 0U; rejects(policy); }
  { val::StimulationPolicy policy = base; policy.max_actions_per_session = 0U; rejects(policy); }
  { val::StimulationPolicy policy = base; policy.max_actions_per_window = 0U; rejects(policy); }
  { val::StimulationPolicy policy = base; policy.action_window = 0U; rejects(policy); }

  // SR-021: a rejected re-open closes an already-open guard so no request may pass.
  {
    val::StimulationGuard guard;
    ASSERT_EQ(guard.open(permit, base), val::GuardStatus::Ok);
    EXPECT_TRUE(guard.is_open());
    val::StimulationPolicy invalid = base;
    invalid.loop_window = 0U;
    EXPECT_EQ(guard.open(permit, invalid), val::GuardStatus::RejectedConfiguration);
    EXPECT_FALSE(guard.is_open());
    EXPECT_EQ(guard.status(), val::GuardStatus::NotOpen);
    val::GuardDiagnostic diagnostic;
    EXPECT_EQ(guard.authorize(make_request(permit, 331U), val::LifecycleState::active, in_window(),
                              diagnostic),
              val::GuardOutcome::Failed);
    EXPECT_EQ(diagnostic.reason, val::GuardReason::NotOpen);
  }
}
