/**
 * \file unit_tests.cpp
 * \brief GoogleTest/gmock unit tests for the standalone T025 validation foundation.
 *
 * Each test name is the exact unit-specification case ID (hyphens converted to
 * underscores). Expected results follow `engineering/verification-plan.md`; they are not
 * weakened to accommodate the implementation.
 */

#include <xverse/xcom/validation_session.hpp>

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace v = xverse::xcom::validation;

namespace xverse {
namespace xcom {
namespace validation {

/// \brief Test-only accessor for the SessionManager deterministic interleaving probe.
/// \details Defined only in this test translation unit; the `friend` declaration in the manager
///          keeps it out of the production public API. `set_hook` installs a callback that the
///          real `SessionManager::transition` runs after time observation and before the deferred
///          baseline commit, so a re-declaration can be placed exactly in that window without
///          depending on thread scheduling.
struct SessionManagerProbe {
  static void set_hook(SessionManager &manager, std::function<void()> hook) {
    manager.before_commit_probe_ = std::move(hook);
  }
  static void clear_hook(SessionManager &manager) { manager.before_commit_probe_ = nullptr; }
};

} // namespace validation
} // namespace xcom
} // namespace xverse

namespace {

constexpr v::ClockDomainId kMono = 1;
constexpr v::ClockDomainId kWall = 2;
constexpr v::ClockDomainId kOther = 3;
constexpr v::Nonce kNonce = 0x1234U;
constexpr v::ActionMask kArm = v::to_mask(v::Action::Arm);
constexpr v::ActionMask kActivate = v::to_mask(v::Action::Activate);
constexpr v::ActionMask kClose = v::to_mask(v::Action::Close);
constexpr v::ActionMask kFinalize = v::to_mask(v::Action::Finalize);
constexpr v::ActionMask kExpire = v::to_mask(v::Action::Expire);
constexpr v::ActionMask kRevoke = v::to_mask(v::Action::Revoke);
constexpr v::ActionMask kIncomplete = v::to_mask(v::Action::MarkEvidenceIncomplete);

/// Mock host clock source used to prove that host-injected failure is reported.
class MockClockSource {
public:
  MOCK_METHOD(std::optional<v::Timestamp>, read, (), ());
};

v::SessionId session_id(std::uint8_t seed) {
  v::SessionId id{};
  for (std::size_t index = 0; index < id.size(); ++index) {
    id[index] = static_cast<std::uint8_t>(seed + index);
  }
  return id;
}

v::PlanDigest plan_digest(std::uint8_t seed) {
  v::PlanDigest digest{};
  for (std::size_t index = 0; index < digest.size(); ++index) {
    digest[index] = static_cast<std::uint8_t>(seed + index);
  }
  return digest;
}

v::ControllerId controller_id(std::uint8_t seed) {
  v::ControllerId id{};
  for (std::size_t index = 0; index < id.size(); ++index) {
    id[index] = static_cast<std::uint8_t>(seed + index);
  }
  return id;
}

v::ManagerScope scope_id(std::uint8_t seed) {
  v::ManagerScope scope{};
  for (std::size_t index = 0; index < scope.size(); ++index) {
    scope[index] = static_cast<std::uint8_t>(0xE0U + seed + index);
  }
  return scope;
}

v::PermitId permit_id_from(std::uint8_t seed) {
  return v::canonical_digest(std::vector<std::uint8_t>{seed, static_cast<std::uint8_t>(seed + 1U)});
}

v::Permit make_permit(v::SessionId sid, v::Nonce nonce, std::uint32_t quota,
                      v::ClockDomainId domain) {
  v::PermitBuilder builder;
  EXPECT_EQ(builder.set_session_id(sid), v::Result::Ok);
  EXPECT_EQ(builder.set_plan_digest(plan_digest(0x40U)), v::Result::Ok);
  EXPECT_EQ(builder.set_scenario("scn"), v::Result::Ok);
  EXPECT_EQ(builder.set_deployment("dep"), v::Result::Ok);
  EXPECT_EQ(builder.set_environment("env"), v::Result::Ok);
  EXPECT_EQ(builder.set_tool("tool"), v::Result::Ok);
  EXPECT_EQ(builder.set_interface("iface"), v::Result::Ok);
  EXPECT_EQ(builder.set_target("tgt"), v::Result::Ok);
  EXPECT_EQ(builder.set_nonce(nonce), v::Result::Ok);
  EXPECT_EQ(builder.set_validity(domain, 1000, 2000), v::Result::Ok);
  EXPECT_EQ(builder.add_allowed_action(kArm), v::Result::Ok);
  EXPECT_EQ(builder.add_allowed_action(kActivate), v::Result::Ok);
  EXPECT_EQ(builder.add_allowed_action(kClose), v::Result::Ok);
  EXPECT_EQ(builder.add_allowed_action(kFinalize), v::Result::Ok);
  EXPECT_EQ(builder.add_quota(v::Quota{v::QuotaKind::Operations, quota}), v::Result::Ok);
  v::Permit permit;
  EXPECT_EQ(builder.build(permit), v::Result::Ok);
  return permit;
}

v::Permit make_valid_permit() { return make_permit(session_id(1), kNonce, 10, kMono); }

v::Permit make_distinct_permit(std::uint8_t seed) {
  return make_permit(session_id(seed), kNonce + seed, 10, kMono);
}

v::Permit make_full_permit() {
  v::PermitBuilder builder;
  builder.set_session_id(session_id(1));
  builder.set_plan_digest(plan_digest(0x40U));
  builder.set_scenario("scn");
  builder.set_deployment("dep");
  builder.set_environment("env");
  builder.set_tool("tool");
  builder.set_interface("iface");
  builder.set_target("tgt");
  builder.set_nonce(kNonce);
  builder.set_validity(kMono, 1000, 2000);
  for (const v::ActionMask mask :
       {kArm, kActivate, kClose, kFinalize, kExpire, kRevoke, kIncomplete}) {
    builder.add_allowed_action(mask);
  }
  builder.add_quota(v::Quota{v::QuotaKind::Operations, 10U});
  v::Permit permit;
  EXPECT_EQ(builder.build(permit), v::Result::Ok);
  return permit;
}

v::SessionContext context_for(const v::Permit &permit) {
  v::SessionContext context;
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

v::ClockSource constant_source(std::optional<v::Timestamp> value) {
  return [value]() -> std::optional<v::Timestamp> { return value; };
}

v::ManagerConfig scoped_config(std::uint8_t seed = 1) {
  v::ManagerConfig config;
  config.scope = scope_id(seed);
  return config;
}

} // namespace

TEST(ValidationTypes, TYP_01) {
  const std::vector<std::uint8_t> bytes{1U, 2U, 3U, 4U, 5U};
  EXPECT_EQ(v::canonical_digest(bytes), v::canonical_digest(bytes));
}

TEST(ValidationTypes, TYP_02) {
  const std::vector<std::uint8_t> first{1U, 2U, 3U};
  const std::vector<std::uint8_t> second{9U, 8U, 7U};
  const v::PermitId first_id = v::canonical_digest(first);
  const v::PermitId second_id = v::canonical_digest(second);
  EXPECT_EQ(first_id.size(), 16U);
  EXPECT_EQ(second_id.size(), 16U);
  EXPECT_NE(first_id, second_id);
}

TEST(ValidationTypes, TYP_03) {
  EXPECT_FALSE(v::is_terminal(v::LifecycleState::declared));
  EXPECT_FALSE(v::is_terminal(v::LifecycleState::armed));
  EXPECT_FALSE(v::is_terminal(v::LifecycleState::active));
  EXPECT_FALSE(v::is_terminal(v::LifecycleState::closing));
  EXPECT_TRUE(v::is_terminal(v::LifecycleState::closed));
  EXPECT_TRUE(v::is_terminal(v::LifecycleState::expired));
  EXPECT_TRUE(v::is_terminal(v::LifecycleState::revoked));
  EXPECT_TRUE(v::is_terminal(v::LifecycleState::evidence_incomplete));
}

TEST(ValidationTypes, TYP_04) {
  EXPECT_TRUE(v::is_defined_action(kArm));
  EXPECT_TRUE(v::is_defined_action(kArm | kActivate));
  EXPECT_FALSE(v::is_defined_action(0U));
  EXPECT_FALSE(v::is_defined_action(0x80U));
  EXPECT_EQ(v::defined_action_bits() & 0x80U, 0U);
}

TEST(ValidationTypes, TYP_05) {
  const std::string printable(63, 'a');
  EXPECT_TRUE(v::Tag::is_valid(printable));
  EXPECT_TRUE(v::Tag::make(printable).has_value());
  EXPECT_FALSE(v::Tag::is_valid(std::string(64, 'a')));
  EXPECT_FALSE(v::Tag::is_valid(std::string("ab\0cd", 5)));
  EXPECT_FALSE(v::Tag::is_valid(std::string(1, static_cast<char>(0x07))));
  EXPECT_FALSE(v::Tag::is_valid(""));
}

TEST(ValidationTypes, TYP_06) {
  EXPECT_EQ(v::action_mask_name(kArm), "Arm");
  EXPECT_EQ(v::action_mask_name(kActivate), "Activate");
  EXPECT_EQ(v::action_mask_name(kClose), "Close");
  EXPECT_EQ(v::action_mask_name(kFinalize), "Finalize");
  EXPECT_EQ(v::action_mask_name(kExpire), "Expire");
  EXPECT_EQ(v::action_mask_name(kRevoke), "Revoke");
  EXPECT_EQ(v::action_mask_name(kIncomplete), "MarkEvidenceIncomplete");
  EXPECT_TRUE(v::action_mask_name(0x80U).empty());
  EXPECT_TRUE(v::action_mask_name(kArm | kActivate).empty());
  EXPECT_TRUE(v::action_mask_name(0U).empty());
}

TEST(DiagnosticUnit, DIA_01) {
  const v::Diagnostic diagnostic = v::Diagnostic::from_first({v::Result::InvalidHandle});
  ASSERT_EQ(diagnostic.size(), 1U);
  EXPECT_EQ(diagnostic.codes().front(), v::Result::InvalidHandle);
  EXPECT_EQ(diagnostic.primary(), v::Result::InvalidHandle);
  EXPECT_FALSE(diagnostic.locator().has_value());
}

TEST(DiagnosticUnit, DIA_02) {
  const v::Diagnostic diagnostic = v::Diagnostic::from_first(
      {v::Result::StaleHandle, v::Result::ForeignHandle, v::Result::PermitExpired});
  ASSERT_EQ(diagnostic.size(), 1U);
  EXPECT_EQ(diagnostic.codes().front(), v::Result::ForeignHandle);
}

TEST(DiagnosticUnit, DIA_03) {
  const v::Diagnostic diagnostic =
      v::Diagnostic::from_first({v::Result::UndefinedAction, v::Result::PermitExpired});
  ASSERT_EQ(diagnostic.size(), 1U);
  EXPECT_EQ(diagnostic.codes().front(), v::Result::PermitExpired);
}

TEST(DiagnosticUnit, DIA_04) {
  const v::Diagnostic diagnostic = v::Diagnostic::from_first({v::Result::TerminalState});
  ASSERT_EQ(diagnostic.size(), 1U);
  EXPECT_EQ(diagnostic.codes().front(), v::Result::TerminalState);
}

TEST(DiagnosticUnit, DIA_05) {
  const v::Diagnostic diagnostic = v::Diagnostic::accumulate(
      {v::Result::InvalidHandle, v::Result::ForeignHandle, v::Result::RecreatedController,
       v::Result::StaleHandle, v::Result::SessionNotFound, v::Result::UnknownClock,
       v::Result::ClockSourceFailure, v::Result::ClockOutOfBounds, v::Result::ClockRegression,
       v::Result::ClockOverflow});
  EXPECT_EQ(diagnostic.size(), v::Diagnostic::capacity);
  for (std::size_t index = 1; index < diagnostic.size(); ++index) {
    EXPECT_LT(v::precedence_rank(diagnostic.codes()[index - 1]),
              v::precedence_rank(diagnostic.codes()[index]));
  }
}

TEST(DiagnosticUnit, DIA_06) {
  const v::Diagnostic first = v::Diagnostic::accumulate(
      {v::Result::TerminalState, v::Result::ForeignHandle, v::Result::PermitExpired});
  const v::Diagnostic second = v::Diagnostic::accumulate(
      {v::Result::TerminalState, v::Result::ForeignHandle, v::Result::PermitExpired});
  EXPECT_EQ(first, second);
  EXPECT_TRUE(std::equal(first.codes().begin(), first.codes().end(), second.codes().begin(),
                         second.codes().end()));
}

namespace {

v::PermitBuilder valid_builder(std::uint32_t quota = 10, v::Nonce nonce = kNonce,
                               v::SessionId sid = session_id(1)) {
  v::PermitBuilder builder;
  builder.set_session_id(sid);
  builder.set_plan_digest(plan_digest(0x40U));
  builder.set_scenario("scn");
  builder.set_deployment("dep");
  builder.set_environment("env");
  builder.set_tool("tool");
  builder.set_interface("iface");
  builder.set_target("tgt");
  builder.set_nonce(nonce);
  builder.set_validity(kMono, 1000, 2000);
  builder.add_allowed_action(kArm);
  builder.add_allowed_action(kActivate);
  builder.add_allowed_action(kClose);
  builder.add_allowed_action(kFinalize);
  builder.add_quota(v::Quota{v::QuotaKind::Operations, quota});
  return builder;
}

void expect_invalid(const v::PermitBuilder &builder, v::FieldLocator locator) {
  v::Permit permit;
  EXPECT_EQ(builder.build(permit), v::Result::InvalidPermit);
  ASSERT_TRUE(builder.last_locator().has_value());
  EXPECT_EQ(builder.last_locator().value(), locator);
}

} // namespace

TEST(PermitUnit, PRM_01) {
  const v::PermitBuilder builder = valid_builder();
  v::Permit permit;
  ASSERT_EQ(builder.build(permit), v::Result::Ok);
  EXPECT_NE(permit.permit_id(), v::PermitId{});
  EXPECT_EQ(permit.session_id(), session_id(1));
  EXPECT_EQ(permit.plan_digest(), plan_digest(0x40U));
  EXPECT_EQ(permit.scenario(), "scn");
  EXPECT_EQ(permit.deployment(), "dep");
  EXPECT_EQ(permit.environment(), "env");
  EXPECT_EQ(permit.tool(), "tool");
  EXPECT_EQ(permit.interface_name(), "iface");
  EXPECT_EQ(permit.target(), "tgt");
  EXPECT_EQ(permit.nonce(), kNonce);
  EXPECT_EQ(permit.validity_domain(), kMono);
  EXPECT_EQ(permit.valid_from(), 1000);
  EXPECT_EQ(permit.valid_until(), 2000);
  EXPECT_EQ(permit.allowed_actions().size(), 4U);
  ASSERT_EQ(permit.quotas().size(), 1U);
  EXPECT_EQ(permit.quotas().front().limit, 10U);
  EXPECT_TRUE(permit.allows(kArm));
  EXPECT_FALSE(permit.allows(kArm | kActivate));
}

TEST(PermitUnit, PRM_02) {
  v::PermitBuilder builder = valid_builder();
  builder.set_session_id(v::SessionId{});
  expect_invalid(builder, v::FieldLocator::SessionId);
}

TEST(PermitUnit, PRM_03) {
  v::PermitBuilder builder = valid_builder();
  builder.set_scenario("");
  expect_invalid(builder, v::FieldLocator::Scenario);
}

TEST(PermitUnit, PRM_04) {
  v::PermitBuilder builder = valid_builder();
  builder.add_allowed_action(0x80U);
  expect_invalid(builder, v::FieldLocator::AllowedActions);
}

TEST(PermitUnit, PRM_05) {
  v::PermitBuilder builder = valid_builder();
  builder.add_allowed_action(kArm | kActivate);
  expect_invalid(builder, v::FieldLocator::AllowedActions);
}

TEST(PermitUnit, PRM_06) {
  v::PermitBuilder builder = valid_builder();
  builder.add_quota(v::Quota{static_cast<v::QuotaKind>(99), 5U});
  expect_invalid(builder, v::FieldLocator::Quota);
}

TEST(PermitUnit, PRM_07) {
  v::PermitBuilder builder = valid_builder();
  builder.add_quota(v::Quota{v::QuotaKind::Operations, 0U});
  expect_invalid(builder, v::FieldLocator::Quota);
}

TEST(PermitUnit, PRM_08) {
  v::PermitBuilder builder = valid_builder();
  builder.set_validity(kMono, 2000, 1000);
  expect_invalid(builder, v::FieldLocator::Validity);
}

TEST(PermitUnit, PRM_09) {
  const v::PermitBuilder first_builder = valid_builder();
  const v::PermitBuilder second_builder = valid_builder(10U, kNonce + 1U);
  const v::PermitBuilder third_builder = valid_builder();
  v::Permit first;
  v::Permit second;
  v::Permit third;
  ASSERT_EQ(first_builder.build(first), v::Result::Ok);
  ASSERT_EQ(second_builder.build(second), v::Result::Ok);
  ASSERT_EQ(third_builder.build(third), v::Result::Ok);
  EXPECT_EQ(third.permit_id(), first.permit_id());
  EXPECT_NE(second.permit_id(), first.permit_id());
}

TEST(TimeAuthorityUnit, CLK_01) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.now(kMono, out), v::Result::Ok);
  EXPECT_EQ(out, 1000);
}

TEST(TimeAuthorityUnit, CLK_02) {
  v::TimeAuthority authority(4, 8);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.now(0xDEADU, out), v::Result::UnknownClock);
  EXPECT_EQ(authority.domain_count(), 0U);
  EXPECT_EQ(authority.mapping_count(), 0U);
}

TEST(TimeAuthorityUnit, CLK_03) {
  MockClockSource mock;
  v::TimeAuthority authority(4, 8);
  v::ClockSource source = [&mock]() -> std::optional<v::Timestamp> { return mock.read(); };
  ASSERT_EQ(authority.declare_clock(kMono, source, v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  EXPECT_CALL(mock, read()).WillOnce(::testing::Return(std::optional<v::Timestamp>{}));
  v::Timestamp out = 0;
  EXPECT_EQ(authority.now(kMono, out), v::Result::ClockSourceFailure);
  EXPECT_FALSE(authority.baseline(kMono).has_value());
}

TEST(TimeAuthorityUnit, CLK_04) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000001), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.now(kMono, out), v::Result::ClockOutOfBounds);
  EXPECT_FALSE(authority.baseline(kMono).has_value());
}

TEST(TimeAuthorityUnit, CLK_05) {
  std::vector<v::Timestamp> readings{1000, 999, 1001};
  std::size_t position = 0;
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(authority.declare_clock(
                kMono,
                [&readings, &position]() -> std::optional<v::Timestamp> {
                  return readings.at(position++);
                },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.now(kMono, out), v::Result::Ok);
  EXPECT_EQ(out, 1000);
  EXPECT_EQ(authority.now(kMono, out), v::Result::ClockRegression);
  ASSERT_TRUE(authority.baseline(kMono).has_value());
  EXPECT_EQ(authority.baseline(kMono).value(), 1000);
  EXPECT_EQ(authority.now(kMono, out), v::Result::Ok);
  EXPECT_EQ(out, 1001);
}

TEST(TimeAuthorityUnit, CLK_06) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1000), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 5, 10), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, 1000, out), v::Result::Ok);
  EXPECT_EQ(out, 1005);
}

TEST(TimeAuthorityUnit, CLK_07) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1000), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 5, 10), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kWall, kMono, 1000, out), v::Result::MissingMapping);
}

TEST(TimeAuthorityUnit, CLK_08) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kOther, 1000, out), v::Result::MissingMapping);
}

TEST(TimeAuthorityUnit, CLK_09) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1000), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 10, 10), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, 1001, out), v::Result::ToleranceExceeded);
}

TEST(TimeAuthorityUnit, CLK_10) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1000), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 10, 10), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, 1000, out), v::Result::Ok);
  EXPECT_EQ(out, 1010);
}

TEST(TimeAuthorityUnit, CLK_11) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(authority.declare_clock(kMono, constant_source(0), v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(authority.declare_clock(kWall, constant_source(0), v::ClockKind::WallClock, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 1, 10), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, std::numeric_limits<v::Timestamp>::max(), out),
            v::Result::ClockOverflow);
}

TEST(TimeAuthorityUnit, CLK_12) {
  std::vector<v::Timestamp> readings{1000, 999};
  std::size_t position = 0;
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(authority.declare_clock(
                kMono,
                [&readings, &position]() -> std::optional<v::Timestamp> {
                  return readings.at(position++);
                },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1000), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 10, 10), v::Result::Ok);
  v::Timestamp out = 0;
  ASSERT_EQ(authority.now(kMono, out), v::Result::Ok);
  const v::Result regression = authority.now(kMono, out);
  const v::Result tolerance = authority.convert(kMono, kWall, 1001, out);
  EXPECT_EQ(regression, v::Result::ClockRegression);
  EXPECT_EQ(tolerance, v::Result::ToleranceExceeded);
  EXPECT_NE(regression, tolerance);
}

TEST(TimeAuthorityUnit, CLK_13) {
  const v::Timestamp kMin = std::numeric_limits<v::Timestamp>::min();
  const v::Timestamp kMax = std::numeric_limits<v::Timestamp>::max();
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(kMin), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(kMax), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 0, 1), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, kMin, out), v::Result::ToleranceExceeded);
  EXPECT_FALSE(authority.baseline(kWall).has_value());
}

TEST(TimeAuthorityUnit, CLK_14) {
  const v::Timestamp kMin = std::numeric_limits<v::Timestamp>::min();
  const v::Timestamp kMax = std::numeric_limits<v::Timestamp>::max();
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(kMax), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(kMin), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 0, 1), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, kMax, out), v::Result::ToleranceExceeded);
  EXPECT_FALSE(authority.baseline(kWall).has_value());
}

TEST(TimeAuthorityUnit, CLK_15) {
  const v::Timestamp kMin = std::numeric_limits<v::Timestamp>::min();
  const v::Timestamp kMax = std::numeric_limits<v::Timestamp>::max();
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(kMin), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(kMax), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 0, std::numeric_limits<v::Tolerance>::max()),
            v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, kMin, out), v::Result::Ok);
  EXPECT_EQ(out, kMin);
  ASSERT_EQ(
      authority.declare_mapping(kMono, kWall, 0, std::numeric_limits<v::Tolerance>::max() - 1U),
      v::Result::Ok);
  EXPECT_EQ(authority.convert(kMono, kWall, kMin, out), v::Result::ToleranceExceeded);
}

TEST(TimeAuthorityUnit, CLK_16) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(200), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(100), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 0, 1), v::Result::Ok);
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(authority.now(kWall, baseline_out), v::Result::Ok);
  EXPECT_EQ(baseline_out, 100);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, 200, out), v::Result::ToleranceExceeded);
  ASSERT_TRUE(authority.baseline(kWall).has_value());
  EXPECT_EQ(authority.baseline(kWall).value(), 100);
  v::Timestamp next = 0;
  EXPECT_EQ(authority.now(kWall, next), v::Result::Ok);
  EXPECT_EQ(next, 100);
}

TEST(TimeAuthorityUnit, CLK_17) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1000), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 10, 10), v::Result::Ok);
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(authority.now(kWall, baseline_out), v::Result::Ok);
  const auto baseline_before = authority.baseline(kWall);
  v::Timestamp out = 12345;
  EXPECT_EQ(authority.convert(0xDEADU, kWall, 1000, out), v::Result::UnknownClock);
  EXPECT_EQ(authority.baseline(kWall), baseline_before);
  EXPECT_EQ(authority.convert(kMono, kOther, 1000, out), v::Result::MissingMapping);
  EXPECT_EQ(authority.baseline(kWall), baseline_before);
  EXPECT_EQ(authority.convert(kMono, kWall, std::numeric_limits<v::Timestamp>::max(), out),
            v::Result::ClockOverflow);
  EXPECT_EQ(authority.baseline(kWall), baseline_before);
  EXPECT_EQ(authority.convert(kMono, kWall, 1001, out), v::Result::ToleranceExceeded);
  EXPECT_EQ(authority.baseline(kWall), baseline_before);
}

TEST(TimeAuthorityUnit, ADV_R3) {
  const v::Timestamp kMin = std::numeric_limits<v::Timestamp>::min();
  const v::Timestamp kMax = std::numeric_limits<v::Timestamp>::max();
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(kMin), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(kMax), v::ClockKind::WallClock, kMin, kMax),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 0, 1), v::Result::Ok);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, kMin, out), v::Result::ToleranceExceeded);
  EXPECT_FALSE(authority.baseline(kWall).has_value());
}

TEST(TimeAuthorityUnit, ADV_R4) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(200), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(100), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 0, 1), v::Result::Ok);
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(authority.now(kWall, baseline_out), v::Result::Ok);
  EXPECT_EQ(baseline_out, 100);
  v::Timestamp out = 0;
  EXPECT_EQ(authority.convert(kMono, kWall, 200, out), v::Result::ToleranceExceeded);
  ASSERT_TRUE(authority.baseline(kWall).has_value());
  EXPECT_EQ(authority.baseline(kWall).value(), 100);
  v::Timestamp next = 0;
  EXPECT_EQ(authority.now(kWall, next), v::Result::Ok);
  EXPECT_EQ(next, 100);
}

TEST(TimeAuthorityUnit, CON_04) {
  v::TimeAuthority authority(4, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  constexpr std::size_t kThreads = 8;
  std::atomic<int> failures{0};
  std::atomic<int> values{0};
  std::vector<std::thread> workers;
  workers.reserve(kThreads);
  for (std::size_t index = 0; index < kThreads; ++index) {
    workers.emplace_back([&authority, &failures, &values]() {
      v::Timestamp out = 0;
      if (authority.now(kMono, out) != v::Result::Ok) {
        ++failures;
      }
      if (out == 1000) {
        ++values;
      }
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }
  EXPECT_EQ(failures.load(), 0);
  EXPECT_EQ(values.load(), static_cast<int>(kThreads));
}

namespace {

v::ValidationSession make_session(std::uint32_t operations,
                                  v::LifecycleState initial = v::LifecycleState::declared) {
  const std::vector<std::uint8_t> bytes{7U, 8U, 9U};
  return v::ValidationSession(v::canonical_digest(bytes), session_id(1), controller_id(1), 1,
                              {v::Quota{v::QuotaKind::Operations, operations}}, initial);
}

v::ValidationSession advance(std::vector<v::Action> actions, std::uint32_t operations = 100U) {
  v::ValidationSession session = make_session(operations);
  for (const v::Action action : actions) {
    EXPECT_EQ(session.apply(action, 1500), v::Result::Ok);
  }
  return session;
}

} // namespace

TEST(ValidationSessionUnit, LIF_01) {
  v::ValidationSession session = make_session(100U);
  EXPECT_EQ(session.apply(v::Action::Arm, 1500), v::Result::Ok);
  EXPECT_EQ(session.state(), v::LifecycleState::armed);
}

TEST(ValidationSessionUnit, LIF_02) {
  v::ValidationSession session = advance({v::Action::Arm});
  EXPECT_EQ(session.apply(v::Action::Activate, 1500), v::Result::Ok);
  EXPECT_EQ(session.state(), v::LifecycleState::active);
}

TEST(ValidationSessionUnit, LIF_03) {
  v::ValidationSession session = advance({v::Action::Arm, v::Action::Activate});
  EXPECT_EQ(session.apply(v::Action::Close, 1500), v::Result::Ok);
  EXPECT_EQ(session.state(), v::LifecycleState::closing);
}

TEST(ValidationSessionUnit, LIF_04) {
  v::ValidationSession session = advance({v::Action::Arm, v::Action::Activate, v::Action::Close});
  EXPECT_EQ(session.apply(v::Action::Finalize, 1500), v::Result::Ok);
  EXPECT_EQ(session.state(), v::LifecycleState::closed);
  EXPECT_TRUE(session.is_terminal());
}

TEST(ValidationSessionUnit, LIF_05) {
  v::ValidationSession session = advance({v::Action::Arm});
  EXPECT_EQ(session.apply(v::Action::Expire, 1500), v::Result::Ok);
  EXPECT_EQ(session.state(), v::LifecycleState::expired);
}

TEST(ValidationSessionUnit, LIF_06) {
  v::ValidationSession session = advance({v::Action::Arm, v::Action::Activate});
  EXPECT_EQ(session.apply(v::Action::Revoke, 1500), v::Result::Ok);
  EXPECT_EQ(session.state(), v::LifecycleState::revoked);
}

TEST(ValidationSessionUnit, LIF_07) {
  v::ValidationSession session = advance({v::Action::Arm, v::Action::Activate});
  EXPECT_EQ(session.apply(v::Action::MarkEvidenceIncomplete, 1500), v::Result::Ok);
  EXPECT_EQ(session.state(), v::LifecycleState::evidence_incomplete);
}

TEST(ValidationSessionUnit, LIF_08) {
  v::ValidationSession session = advance({v::Action::Arm, v::Action::Expire});
  ASSERT_EQ(session.state(), v::LifecycleState::expired);
  EXPECT_EQ(session.apply(v::Action::Arm, 1500), v::Result::TerminalState);
  EXPECT_EQ(session.state(), v::LifecycleState::expired);
}

TEST(ValidationSessionUnit, LIF_09) {
  v::ValidationSession session =
      advance({v::Action::Arm, v::Action::Activate, v::Action::Close, v::Action::Finalize});
  ASSERT_EQ(session.state(), v::LifecycleState::closed);
  EXPECT_EQ(session.apply(v::Action::Arm, 1500), v::Result::TerminalState);
  EXPECT_EQ(session.state(), v::LifecycleState::closed);
}

TEST(ValidationSessionUnit, LIF_10) {
  v::ValidationSession session = make_session(100U);
  EXPECT_EQ(session.apply(v::Action::Activate, 1500), v::Result::InvalidTransition);
  EXPECT_EQ(session.state(), v::LifecycleState::declared);
}

TEST(ValidationSessionUnit, LIF_11) {
  v::ValidationSession session = advance({v::Action::Arm, v::Action::Activate});
  EXPECT_EQ(session.apply(v::Action::Arm, 1500), v::Result::InvalidTransition);
  EXPECT_EQ(session.state(), v::LifecycleState::active);
}

TEST(ValidationSessionUnit, LIF_12) {
  v::ValidationSession session = advance({v::Action::Arm});
  EXPECT_EQ(session.apply(v::Action::Arm, 1500), v::Result::AlreadyApplied);
  EXPECT_EQ(session.state(), v::LifecycleState::armed);
}

TEST(ValidationSessionUnit, LIF_13) {
  v::ValidationSession session =
      advance({v::Action::Arm, v::Action::Activate, v::Action::Close, v::Action::Finalize});
  EXPECT_EQ(session.apply(v::Action::Finalize, 1500), v::Result::AlreadyApplied);
  EXPECT_EQ(session.state(), v::LifecycleState::closed);
}

TEST(ValidationSessionUnit, LIF_14) {
  v::ValidationSession session = advance({v::Action::Arm, v::Action::Revoke});
  EXPECT_EQ(session.apply(v::Action::Revoke, 1500), v::Result::AlreadyApplied);
  EXPECT_EQ(session.state(), v::LifecycleState::revoked);
}

TEST(ValidationSessionUnit, LIF_15) {
  v::ValidationSession session = make_session(100U);
  EXPECT_EQ(session.apply(v::Action::Close, 1500), v::Result::InvalidTransition);
  EXPECT_EQ(session.state(), v::LifecycleState::declared);
}

TEST(ValidationSessionUnit, LIF_16) {
  const std::array<std::pair<v::LifecycleState, std::vector<v::Action>>, 8> table{{
      {v::LifecycleState::declared, {}},
      {v::LifecycleState::armed, {v::Action::Arm}},
      {v::LifecycleState::active, {v::Action::Arm, v::Action::Activate}},
      {v::LifecycleState::closing, {v::Action::Arm, v::Action::Activate, v::Action::Close}},
      {v::LifecycleState::closed,
       {v::Action::Arm, v::Action::Activate, v::Action::Close, v::Action::Finalize}},
      {v::LifecycleState::expired, {v::Action::Arm, v::Action::Expire}},
      {v::LifecycleState::revoked, {v::Action::Arm, v::Action::Revoke}},
      {v::LifecycleState::evidence_incomplete, {v::Action::Arm, v::Action::MarkEvidenceIncomplete}},
  }};
  for (const auto &row : table) {
    const v::ValidationSession session = advance(row.second);
    EXPECT_EQ(session.state(), row.first);
  }
}

TEST(ValidationSessionUnit, QUO_01) {
  v::ValidationSession session = make_session(1U, v::LifecycleState::armed);
  EXPECT_EQ(session.apply(v::Action::Activate, 1500), v::Result::Ok);
  EXPECT_EQ(session.remaining_quota(v::QuotaKind::Operations), 0U);
  EXPECT_EQ(session.state(), v::LifecycleState::active);
  EXPECT_EQ(session.apply(v::Action::Activate, 1500), v::Result::QuotaExhausted);
  EXPECT_EQ(session.state(), v::LifecycleState::active);
}

TEST(ValidationSessionUnit, QUO_02) {
  v::ValidationSession session = make_session(3U);
  EXPECT_EQ(session.apply(v::Action::Arm, 1500), v::Result::Ok);
  EXPECT_EQ(session.apply(v::Action::Activate, 1500), v::Result::Ok);
  EXPECT_EQ(session.apply(v::Action::Close, 1500), v::Result::Ok);
  EXPECT_EQ(session.remaining_quota(v::QuotaKind::Operations), 0U);
  EXPECT_EQ(session.apply(v::Action::Finalize, 1500), v::Result::QuotaExhausted);
  EXPECT_EQ(session.state(), v::LifecycleState::closing);
}

TEST(PermitRegistryUnit, REG_01) {
  v::PermitRegistry registry(16, 16);
  const v::ControllerId controller = controller_id(1);
  const v::PermitId permit = permit_id_from(1);
  const v::SessionId session = session_id(1);
  EXPECT_EQ(registry.try_consume(controller, permit, session), v::Result::Ok);
  EXPECT_TRUE(registry.is_consumed_permit(controller, permit));
  EXPECT_TRUE(registry.is_consumed_session(controller, session));
}

TEST(PermitRegistryUnit, REG_02) {
  v::PermitRegistry registry(16, 16);
  const v::ControllerId controller = controller_id(1);
  const v::PermitId permit = permit_id_from(1);
  const v::SessionId session = session_id(1);
  ASSERT_EQ(registry.try_consume(controller, permit, session), v::Result::Ok);
  EXPECT_EQ(registry.try_consume(controller, permit, session), v::Result::SessionAlreadyConsumed);
  EXPECT_EQ(registry.size(), 1U);
  EXPECT_EQ(registry.session_size(), 1U);
}

TEST(PermitRegistryUnit, REG_03) {
  v::PermitRegistry registry(16, 16);
  const v::ControllerId controller = controller_id(1);
  const v::PermitId permit = permit_id_from(1);
  ASSERT_EQ(registry.try_consume(controller, permit, session_id(1)), v::Result::Ok);
  EXPECT_EQ(registry.try_consume(controller, permit, session_id(2)),
            v::Result::PermitAlreadyConsumed);
  EXPECT_EQ(registry.size(), 1U);
  EXPECT_EQ(registry.session_size(), 1U);
}

TEST(PermitRegistryUnit, REG_04) {
  v::PermitRegistry registry(16, 16);
  const v::ControllerId controller = controller_id(1);
  const v::SessionId session = session_id(1);
  ASSERT_EQ(registry.try_consume(controller, permit_id_from(1), session), v::Result::Ok);
  EXPECT_EQ(registry.try_consume(controller, permit_id_from(9), session),
            v::Result::SessionAlreadyConsumed);
  EXPECT_EQ(registry.size(), 1U);
}

TEST(PermitRegistryUnit, QUO_05) {
  v::PermitRegistry registry(2, 16);
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(registry.try_consume(controller, permit_id_from(1), session_id(1)), v::Result::Ok);
  ASSERT_EQ(registry.try_consume(controller, permit_id_from(2), session_id(2)), v::Result::Ok);
  EXPECT_EQ(registry.try_consume(controller, permit_id_from(3), session_id(3)),
            v::Result::CapacityExhausted);
  EXPECT_EQ(registry.size(), 2U);
  EXPECT_EQ(registry.session_size(), 2U);
  EXPECT_FALSE(registry.is_consumed_permit(controller, permit_id_from(3)));
  EXPECT_FALSE(registry.is_consumed_session(controller, session_id(3)));
}

TEST(PermitRegistryUnit, REG_06) {
  v::PermitRegistry registry(16, 16);
  const v::ControllerId controller = controller_id(1);
  const v::PermitId permit = permit_id_from(1);
  const v::SessionId session = session_id(1);
  constexpr std::size_t kThreads = 16;
  std::vector<v::Result> results(kThreads, v::Result::Ok);
  std::vector<std::thread> workers;
  workers.reserve(kThreads);
  for (std::size_t index = 0; index < kThreads; ++index) {
    workers.emplace_back([&registry, &results, controller, permit, session, index]() {
      results[index] = registry.try_consume(controller, permit, session);
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }
  const auto successes =
      static_cast<std::size_t>(std::count(results.begin(), results.end(), v::Result::Ok));
  const auto replays = static_cast<std::size_t>(
      std::count(results.begin(), results.end(), v::Result::SessionAlreadyConsumed));
  EXPECT_EQ(successes, 1U);
  EXPECT_EQ(replays, kThreads - 1U);
}

namespace {

struct ManagerFixture {
  v::SessionManager manager;
  v::ControllerId controller;
  std::optional<v::Timestamp> mono_value{1500};
  std::optional<v::Timestamp> wall_value{1500};

  ManagerFixture() : manager(scoped_config(1)), controller(controller_id(1)) {
    EXPECT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
    EXPECT_EQ(manager.time_authority().declare_clock(
                  kMono, [this]() -> std::optional<v::Timestamp> { return mono_value; },
                  v::ClockKind::Monotonic, 0, 1000000),
              v::Result::Ok);
    EXPECT_EQ(manager.time_authority().declare_clock(
                  kWall, [this]() -> std::optional<v::Timestamp> { return wall_value; },
                  v::ClockKind::WallClock, 0, 1000000),
              v::Result::Ok);
  }
};

v::Result consume_permit(v::SessionManager &manager, const v::ControllerId &controller,
                         const v::Permit &permit, v::SessionHandle &handle) {
  return manager.consume(controller, permit, context_for(permit), handle);
}

void expect_mismatch(v::SessionManager &manager, const v::ControllerId &controller,
                     const v::Permit &permit, v::SessionContext context, v::FieldLocator locator) {
  v::SessionHandle handle{};
  EXPECT_EQ(manager.consume(controller, permit, context, handle), v::Result::PermitMismatch);
  ASSERT_TRUE(manager.last_diagnostic().locator().has_value());
  EXPECT_EQ(manager.last_diagnostic().locator().value(), static_cast<std::uint32_t>(locator));
  EXPECT_EQ(handle, v::SessionHandle{});
}

/// Immutable snapshot of every observable manager, session, and authority baseline used to
/// prove that a rejected transition is non-mutating.
struct TransitionFixtureSnapshot {
  v::ManagerSnapshot manager;
  v::SessionSnapshot session;
  std::optional<v::Timestamp> mono_baseline;
  std::optional<v::Timestamp> wall_baseline;
  friend bool operator==(const TransitionFixtureSnapshot &,
                         const TransitionFixtureSnapshot &) noexcept = default;
};

TransitionFixtureSnapshot capture_transition_state(v::SessionManager &manager,
                                                   const v::SessionHandle &handle) {
  TransitionFixtureSnapshot snapshot;
  snapshot.manager = manager.manager_snapshot();
  EXPECT_EQ(manager.session_snapshot(handle, snapshot.session), v::Result::Ok);
  snapshot.mono_baseline = manager.time_authority().baseline(kMono);
  snapshot.wall_baseline = manager.time_authority().baseline(kWall);
  return snapshot;
}

void expect_transition_rejects_unchanged(v::SessionManager &manager, const v::SessionHandle &handle,
                                         v::Action action, v::ClockDomainId now_domain,
                                         v::Timestamp now_value, v::Result expected) {
  const TransitionFixtureSnapshot before = capture_transition_state(manager, handle);
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager.transition(handle, action, now_domain, now_value, diagnostic), expected);
  EXPECT_EQ(diagnostic.primary(), expected);
  EXPECT_EQ(diagnostic.size(), 1U);
  const TransitionFixtureSnapshot after = capture_transition_state(manager, handle);
  EXPECT_EQ(after, before);
}

void declare_cross_domain_pair(v::SessionManager &manager,
                               const std::function<std::optional<v::Timestamp>()> &mono_source,
                               const std::function<std::optional<v::Timestamp>()> &wall_source) {
  EXPECT_EQ(manager.time_authority().declare_clock(kMono, mono_source, v::ClockKind::WallClock, 0,
                                                   1000000),
            v::Result::Ok);
  EXPECT_EQ(manager.time_authority().declare_clock(kWall, wall_source, v::ClockKind::WallClock, 0,
                                                   1000000),
            v::Result::Ok);
  EXPECT_EQ(manager.time_authority().declare_mapping(kWall, kMono, 0, 1000000), v::Result::Ok);
}

} // namespace

TEST(SessionManagerUnit, NOM_01) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::LifecycleState state = v::LifecycleState::closed;
  ASSERT_EQ(fixture.manager.state(handle, state), v::Result::Ok);
  EXPECT_EQ(state, v::LifecycleState::declared);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::Ok);
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Close, kMono, 1500, diagnostic),
            v::Result::Ok);
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Finalize, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.state(handle, state), v::Result::Ok);
  EXPECT_EQ(state, v::LifecycleState::closed);
}

TEST(SessionManagerUnit, NOM_02) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
}

TEST(SessionManagerUnit, NOM_03) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  ASSERT_EQ(fixture.manager.time_authority().declare_mapping(kWall, kMono, 0, 10), v::Result::Ok);
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, kWall, 1500, diagnostic),
            v::Result::Ok);
}

TEST(SessionManagerUnit, NOM_04) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, kWall, 1500, diagnostic),
            v::Result::MissingMapping);
}

TEST(SessionManagerUnit, MIS_01) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.session_id = session_id(9);
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::SessionId);
}

TEST(SessionManagerUnit, MIS_02) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.plan_digest = plan_digest(9);
  expect_mismatch(fixture.manager, fixture.controller, permit, context,
                  v::FieldLocator::PlanDigest);
}

TEST(SessionManagerUnit, MIS_03) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.scenario = "other";
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::Scenario);
}

TEST(SessionManagerUnit, MIS_04) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.deployment = "other";
  expect_mismatch(fixture.manager, fixture.controller, permit, context,
                  v::FieldLocator::Deployment);
}

TEST(SessionManagerUnit, MIS_05) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.environment = "other";
  expect_mismatch(fixture.manager, fixture.controller, permit, context,
                  v::FieldLocator::Environment);
}

TEST(SessionManagerUnit, MIS_06) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.tool = "other";
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::Tool);
}

TEST(SessionManagerUnit, MIS_07) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.interface_name = "other";
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::Interface);
}

TEST(SessionManagerUnit, MIS_08) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.target = "other";
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::Target);
}

TEST(SessionManagerUnit, MIS_09) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.nonce = kNonce + 1U;
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::Nonce);
}

TEST(SessionManagerUnit, MIS_10) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.allowed_actions.pop_back();
  expect_mismatch(fixture.manager, fixture.controller, permit, context,
                  v::FieldLocator::AllowedActions);
}

TEST(SessionManagerUnit, MIS_11) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.valid_until = 2500;
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::Validity);
}

TEST(SessionManagerUnit, MIS_12) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionContext context = context_for(permit);
  context.quotas.clear();
  expect_mismatch(fixture.manager, fixture.controller, permit, context, v::FieldLocator::Quota);
}

TEST(SessionManagerUnit, MIS_13) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  EXPECT_NE(handle, v::SessionHandle{});
}

TEST(SessionManagerUnit, RP_01) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle),
            v::Result::SessionAlreadyConsumed);
}

TEST(SessionManagerUnit, RP_02) {
  ManagerFixture fixture;
  const v::Permit first = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, first, handle), v::Result::Ok);
  const v::Permit changed = make_permit(session_id(1), kNonce + 1U, 10, kMono);
  EXPECT_NE(changed.permit_id(), first.permit_id());
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, changed, handle),
            v::Result::SessionAlreadyConsumed);
}

TEST(SessionManagerUnit, RP_03) {
  ManagerFixture fixture;
  const v::Permit first = make_permit(session_id(1), kNonce, 10, kMono);
  const v::Permit rebound = make_permit(session_id(2), kNonce, 10, kMono);
  EXPECT_EQ(first.permit_id(), rebound.permit_id());
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, first, handle), v::Result::Ok);
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, rebound, handle),
            v::Result::PermitAlreadyConsumed);
}

TEST(SessionManagerUnit, RP_04) {
  ManagerFixture fixture;
  const v::Permit first = make_permit(session_id(1), kNonce, 10, kMono);
  const v::Permit second = make_permit(session_id(2), kNonce, 10, kMono);
  const v::Permit third = make_permit(session_id(3), kNonce, 10, kMono);
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, first, handle), v::Result::Ok);
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, second, handle),
            v::Result::PermitAlreadyConsumed);
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, third, handle),
            v::Result::PermitAlreadyConsumed);
}

TEST(SessionManagerUnit, RP_05) {
  ManagerFixture fixture;
  const v::Permit first = make_permit(session_id(1), kNonce, 10, kMono);
  const v::Permit second = make_permit(session_id(2), kNonce + 1U, 10, kMono);
  EXPECT_NE(first.permit_id(), second.permit_id());
  v::SessionHandle first_handle{};
  v::SessionHandle second_handle{};
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, first, first_handle),
            v::Result::Ok);
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, second, second_handle),
            v::Result::Ok);
}

TEST(SessionManagerUnit, QUO_03) {
  ManagerFixture fixture;
  std::vector<v::SessionHandle> handles;
  for (std::uint8_t seed = 1; seed <= 8; ++seed) {
    v::SessionHandle handle{};
    ASSERT_EQ(
        consume_permit(fixture.manager, fixture.controller, make_distinct_permit(seed), handle),
        v::Result::Ok);
    handles.push_back(handle);
  }
  EXPECT_EQ(fixture.manager.manager_snapshot().live_sessions, 8U);
  v::SessionHandle rejected{};
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(9), rejected),
            v::Result::CapacityExhausted);
  EXPECT_EQ(rejected, v::SessionHandle{});
  EXPECT_EQ(fixture.manager.manager_snapshot().live_sessions, 8U);
}

TEST(SessionManagerUnit, QUO_04) {
  ManagerFixture fixture;
  v::SessionHandle first{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(1), first),
            v::Result::Ok);
  for (std::uint8_t seed = 2; seed <= 8; ++seed) {
    v::SessionHandle handle{};
    ASSERT_EQ(
        consume_permit(fixture.manager, fixture.controller, make_distinct_permit(seed), handle),
        v::Result::Ok);
  }
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(first, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.transition(first, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.transition(first, v::Action::Close, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.transition(first, v::Action::Finalize, kMono, 1500, diagnostic),
            v::Result::Ok);
  v::SessionHandle reused{};
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(9), reused),
            v::Result::Ok);
  EXPECT_EQ(fixture.manager.manager_snapshot().live_sessions, 8U);
}

TEST(SessionManagerUnit, QUO_06) {
  ManagerFixture fixture;
  const v::Permit permit = make_permit(session_id(1), kNonce, 1, kMono);
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
  const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
  v::SessionSnapshot session_before;
  ASSERT_EQ(fixture.manager.session_snapshot(handle, session_before), v::Result::Ok);
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::QuotaExhausted);
  EXPECT_EQ(fixture.manager.manager_snapshot(), before);
  v::SessionSnapshot session_after;
  ASSERT_EQ(fixture.manager.session_snapshot(handle, session_after), v::Result::Ok);
  EXPECT_EQ(session_after, session_before);

  ManagerFixture capacity;
  for (std::uint8_t seed = 1; seed <= 8; ++seed) {
    v::SessionHandle live{};
    ASSERT_EQ(
        consume_permit(capacity.manager, capacity.controller, make_distinct_permit(seed), live),
        v::Result::Ok);
  }
  const v::ManagerSnapshot full = capacity.manager.manager_snapshot();
  v::SessionHandle rejected{};
  EXPECT_EQ(
      consume_permit(capacity.manager, capacity.controller, make_distinct_permit(9), rejected),
      v::Result::CapacityExhausted);
  EXPECT_EQ(capacity.manager.manager_snapshot(), full);
}

/// F-IMP-01: replay precedence over live-session capacity. When the session table is full,
/// re-presenting an already-consumed session identity reports SessionAlreadyConsumed (not
/// CapacityExhausted) and leaves every observed manager counter unchanged.
TEST(SessionManagerUnit, ReplayOnFullTableReportsSessionAlreadyConsumed) {
  ManagerFixture fixture;
  std::vector<v::SessionHandle> handles;
  for (std::uint8_t seed = 1; seed <= 8; ++seed) {
    v::SessionHandle handle{};
    ASSERT_EQ(
        consume_permit(fixture.manager, fixture.controller, make_distinct_permit(seed), handle),
        v::Result::Ok);
    handles.push_back(handle);
  }
  const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
  ASSERT_EQ(before.live_sessions, 8U);
  v::SessionHandle rejected{};
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(1), rejected),
            v::Result::SessionAlreadyConsumed);
  EXPECT_EQ(rejected, v::SessionHandle{});
  EXPECT_EQ(fixture.manager.last_diagnostic().primary(), v::Result::SessionAlreadyConsumed);
  EXPECT_EQ(fixture.manager.manager_snapshot(), before);
}

/// F-IMP-01: replay precedence over live-session capacity for a rebound permit identity. With a
/// full session table, a fresh session identity carrying an already-consumed PermitId reports
/// PermitAlreadyConsumed (not CapacityExhausted), and manager state is unchanged.
TEST(SessionManagerUnit, ReplayOnFullTableReportsPermitAlreadyConsumed) {
  ManagerFixture fixture;
  for (std::uint8_t seed = 1; seed <= 8; ++seed) {
    v::SessionHandle handle{};
    ASSERT_EQ(
        consume_permit(fixture.manager, fixture.controller, make_distinct_permit(seed), handle),
        v::Result::Ok);
  }
  const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
  ASSERT_EQ(before.live_sessions, 8U);
  // Same permit envelope as make_distinct_permit(1) (identical PermitId) but a fresh session id.
  const v::Permit rebound = make_permit(session_id(9), kNonce + 1U, 10, kMono);
  v::SessionHandle rejected{};
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, rebound, rejected),
            v::Result::PermitAlreadyConsumed);
  EXPECT_EQ(rejected, v::SessionHandle{});
  EXPECT_EQ(fixture.manager.last_diagnostic().primary(), v::Result::PermitAlreadyConsumed);
  EXPECT_EQ(fixture.manager.manager_snapshot(), before);
}

/// F-IMP-01: transactional capacity rejection. When the session table is full, an unconsumed
/// permit reports CapacityExhausted and its identities must not become consumed; every observed
/// manager counter (live sessions and both consumed sets) is byte-identical before and after.
TEST(SessionManagerUnit, UnconsumedPermitOnFullTableRejectedTransactionally) {
  ManagerFixture fixture;
  for (std::uint8_t seed = 1; seed <= 8; ++seed) {
    v::SessionHandle handle{};
    ASSERT_EQ(
        consume_permit(fixture.manager, fixture.controller, make_distinct_permit(seed), handle),
        v::Result::Ok);
  }
  const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
  ASSERT_EQ(before.live_sessions, 8U);
  ASSERT_EQ(before.consumed_permits, 8U);
  ASSERT_EQ(before.consumed_sessions, 8U);
  v::SessionHandle rejected{};
  EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(9), rejected),
            v::Result::CapacityExhausted);
  EXPECT_EQ(rejected, v::SessionHandle{});
  EXPECT_EQ(fixture.manager.last_diagnostic().primary(), v::Result::CapacityExhausted);
  EXPECT_EQ(fixture.manager.manager_snapshot(), before);
}

TEST(SessionManagerUnit, HND_01) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
}

TEST(SessionManagerUnit, HND_02) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  const v::SessionHandle stale = handle;
  EXPECT_GT(fixture.manager.advance_generation(fixture.controller), stale.generation);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(stale, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::StaleHandle);
}

TEST(SessionManagerUnit, HND_03) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  const v::SessionHandle foreign{scope_id(1), controller_id(200), 1, handle.session};
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(foreign, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::ForeignHandle);
}

TEST(SessionManagerUnit, HND_04) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  const v::SessionHandle recreated = handle;
  const v::ControllerId replacement = controller_id(2);
  ASSERT_EQ(fixture.manager.register_controller(replacement, "ctrl"), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(recreated, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::RecreatedController);
}

TEST(SessionManagerUnit, HND_05) {
  ManagerFixture fixture;
  const v::SessionHandle forged{scope_id(1), controller_id(250), 7, session_id(250)};
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(forged, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::InvalidHandle);
}

TEST(SessionManagerUnit, HND_06) {
  ManagerFixture first;
  const v::ControllerId second = controller_id(2);
  ASSERT_EQ(first.manager.register_controller(second, "other"), v::Result::Ok);
  v::SessionHandle first_handle{};
  ASSERT_EQ(consume_permit(first.manager, first.controller, make_distinct_permit(1), first_handle),
            v::Result::Ok);
  v::SessionHandle second_handle{};
  ASSERT_EQ(consume_permit(first.manager, second, make_distinct_permit(2), second_handle),
            v::Result::Ok);
  const v::SessionHandle borrowed{scope_id(1), first.controller, first_handle.generation,
                                  second_handle.session};
  v::Diagnostic diagnostic;
  EXPECT_EQ(first.manager.transition(borrowed, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::SessionNotFound);
}

TEST(SessionManagerUnit, HND_07) {
  ManagerFixture fixture;
  v::SessionHandle handle_a{};
  v::SessionHandle handle_b{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(1), handle_a),
            v::Result::Ok);
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(2), handle_b),
            v::Result::Ok);
  v::SessionSnapshot snapshot_b;
  ASSERT_EQ(fixture.manager.session_snapshot(handle_b, snapshot_b), v::Result::Ok);
  const v::SessionHandle forged{scope_id(1), controller_id(251), 3, session_id(251)};
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(forged, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::InvalidHandle);
  v::SessionSnapshot after_forgery;
  ASSERT_EQ(fixture.manager.session_snapshot(handle_b, after_forgery), v::Result::Ok);
  EXPECT_EQ(after_forgery, snapshot_b);
  v::Diagnostic applied;
  EXPECT_EQ(fixture.manager.transition(handle_a, v::Action::Arm, kMono, 1500, applied),
            v::Result::Ok);
  v::SessionSnapshot after_a;
  EXPECT_EQ(fixture.manager.session_snapshot(handle_b, after_a), v::Result::Ok);
  EXPECT_EQ(after_a, snapshot_b);
}

TEST(SessionManagerUnit, HND_08) {
  v::SessionManager manager_a(scoped_config(1));
  v::SessionManager manager_b(scoped_config(2));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager_a.register_controller(controller, "ctrl"), v::Result::Ok);
  ASSERT_EQ(manager_b.register_controller(controller, "ctrl"), v::Result::Ok);
  ASSERT_EQ(manager_b.time_authority().declare_clock(kMono, constant_source(1500),
                                                     v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  const v::Permit permit_a = make_distinct_permit(1);
  const v::Permit permit_b = make_distinct_permit(2);
  v::SessionHandle handle_a{};
  v::SessionHandle handle_b{};
  ASSERT_EQ(manager_a.consume(controller, permit_a, context_for(permit_a), handle_a),
            v::Result::Ok);
  ASSERT_EQ(manager_b.consume(controller, permit_b, context_for(permit_b), handle_b),
            v::Result::Ok);
  v::SessionSnapshot snapshot_b;
  ASSERT_EQ(manager_b.session_snapshot(handle_b, snapshot_b), v::Result::Ok);
  const v::ManagerSnapshot manager_before = manager_b.manager_snapshot();
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager_b.transition(handle_a, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::ForeignHandle);
  v::SessionSnapshot after_b;
  ASSERT_EQ(manager_b.session_snapshot(handle_b, after_b), v::Result::Ok);
  EXPECT_EQ(after_b, snapshot_b);
  EXPECT_EQ(manager_b.manager_snapshot(), manager_before);
}

TEST(SessionManagerUnit, HND_09) {
  v::SessionHandle pre_recreation{};
  {
    v::SessionManager manager(scoped_config(1));
    const v::ControllerId controller = controller_id(1);
    ASSERT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
    ASSERT_EQ(manager.time_authority().declare_clock(kMono, constant_source(1500),
                                                     v::ClockKind::Monotonic, 0, 1000000),
              v::Result::Ok);
    const v::Permit permit = make_valid_permit();
    ASSERT_EQ(manager.consume(controller, permit, context_for(permit), pre_recreation),
              v::Result::Ok);
  }
  v::SessionManager recreated(scoped_config(2));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(recreated.register_controller(controller, "ctrl"), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(recreated.transition(pre_recreation, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::ForeignHandle);
}

TEST(SessionManagerUnit, HND_10) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
  const v::ManagerSnapshot before = manager.manager_snapshot();
  EXPECT_EQ(manager.register_controller(controller, "other"), v::Result::InvalidController);
  EXPECT_EQ(manager.manager_snapshot(), before);
}

TEST(SessionManagerUnit, HND_11) {
  v::SessionManager manager(scoped_config(1));
  EXPECT_EQ(manager.register_controller(v::ControllerId{}, "zero"), v::Result::InvalidController);
  v::ManagerConfig zero_config;
  EXPECT_THROW(v::SessionManager bad(zero_config), std::invalid_argument);
}

TEST(SessionManagerUnit, CON_01) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  const v::SessionContext context = context_for(permit);
  constexpr std::size_t kThreads = 16;
  std::vector<v::Result> results(kThreads, v::Result::Ok);
  std::vector<std::thread> workers;
  workers.reserve(kThreads);
  for (std::size_t index = 0; index < kThreads; ++index) {
    workers.emplace_back([&fixture, &permit, &context, &results, index]() {
      v::SessionHandle handle{};
      results[index] = fixture.manager.consume(fixture.controller, permit, context, handle);
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }
  EXPECT_EQ(std::count(results.begin(), results.end(), v::Result::Ok), 1);
  EXPECT_EQ(std::count(results.begin(), results.end(), v::Result::SessionAlreadyConsumed),
            static_cast<std::ptrdiff_t>(kThreads) - 1);
}

TEST(SessionManagerUnit, CON_02) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  constexpr std::size_t kThreads = 16;
  std::vector<v::Result> results(kThreads, v::Result::Ok);
  std::vector<std::thread> workers;
  workers.reserve(kThreads);
  for (std::size_t index = 0; index < kThreads; ++index) {
    workers.emplace_back([&fixture, handle, &results, index]() {
      v::Diagnostic diagnostic;
      results[index] = fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic);
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }
  EXPECT_EQ(std::count(results.begin(), results.end(), v::Result::Ok), 1);
  EXPECT_EQ(std::count(results.begin(), results.end(), v::Result::AlreadyApplied),
            static_cast<std::ptrdiff_t>(kThreads) - 1);
  v::LifecycleState state = v::LifecycleState::closed;
  ASSERT_EQ(fixture.manager.state(handle, state), v::Result::Ok);
  EXPECT_EQ(state, v::LifecycleState::armed);
}

TEST(SessionManagerUnit, CON_03) {
  ManagerFixture fixture;
  constexpr std::size_t kThreads = 8;
  std::vector<v::Permit> permits;
  for (std::uint8_t seed = 1; seed <= kThreads; ++seed) {
    permits.push_back(make_distinct_permit(seed));
  }
  std::vector<v::Result> results(kThreads, v::Result::Ok);
  std::vector<std::thread> workers;
  workers.reserve(kThreads);
  for (std::size_t index = 0; index < kThreads; ++index) {
    workers.emplace_back([&fixture, &permits, &results, index]() {
      v::SessionHandle handle{};
      results[index] = consume_permit(fixture.manager, fixture.controller, permits[index], handle);
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }
  EXPECT_EQ(std::count(results.begin(), results.end(), v::Result::Ok),
            static_cast<std::ptrdiff_t>(kThreads));
  EXPECT_EQ(fixture.manager.manager_snapshot().live_sessions, kThreads);
}

TEST(SessionManagerUnit, CON_05) {
  ManagerFixture fixture;
  constexpr std::size_t kThreads = 16;
  constexpr std::size_t kPermits = 8;
  std::vector<v::Permit> permits;
  for (std::uint8_t seed = 1; seed <= kPermits; ++seed) {
    permits.push_back(make_distinct_permit(seed));
  }
  std::vector<v::Result> results(kThreads, v::Result::InvalidHandle);
  std::vector<std::thread> workers;
  workers.reserve(kThreads);
  for (std::size_t index = 0; index < kThreads; ++index) {
    workers.emplace_back([&fixture, &permits, &results, index]() {
      const v::Permit &permit = permits[index % kPermits];
      v::SessionHandle handle{};
      const v::Result consumed =
          consume_permit(fixture.manager, fixture.controller, permit, handle);
      results[index] = consumed;
      if (consumed == v::Result::Ok) {
        v::Diagnostic diagnostic;
        const v::Result applied =
            fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic);
        results[index] = applied == v::Result::Ok ? v::Result::Ok : applied;
      }
    });
  }
  for (std::thread &worker : workers) {
    worker.join();
  }
  const auto successes = std::count(results.begin(), results.end(), v::Result::Ok);
  EXPECT_GE(successes, 1);
  EXPECT_EQ(fixture.manager.manager_snapshot().live_sessions, static_cast<std::size_t>(successes));
  EXPECT_EQ(fixture.manager.manager_snapshot().consumed_permits,
            static_cast<std::size_t>(successes));
  for (const v::Result result : results) {
    EXPECT_TRUE(result == v::Result::Ok || result == v::Result::SessionAlreadyConsumed ||
                result == v::Result::PermitAlreadyConsumed ||
                result == v::Result::CapacityExhausted);
  }
}

TEST(SessionManagerUnit, ZEM_02) {
  ManagerFixture fixture;
  EXPECT_EQ(fixture.manager.emission_count(), 0U);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Close, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Finalize, kMono, 1500, diagnostic),
            v::Result::Ok);
  EXPECT_EQ(fixture.manager.emission_count(), 0U);
  EXPECT_EQ(fixture.manager.manager_snapshot().emission_count, 0U);
}

TEST(SessionManagerUnit, NOMUT_01) {
  using Mutator = std::function<void(v::SessionContext &)>;
  const std::vector<std::pair<v::FieldLocator, Mutator>> cases{
      {v::FieldLocator::SessionId,
       [](v::SessionContext &context) { context.session_id = session_id(9); }},
      {v::FieldLocator::PlanDigest,
       [](v::SessionContext &context) { context.plan_digest = plan_digest(9); }},
      {v::FieldLocator::Scenario, [](v::SessionContext &context) { context.scenario = "other"; }},
      {v::FieldLocator::Deployment,
       [](v::SessionContext &context) { context.deployment = "other"; }},
      {v::FieldLocator::Environment,
       [](v::SessionContext &context) { context.environment = "other"; }},
      {v::FieldLocator::Tool, [](v::SessionContext &context) { context.tool = "other"; }},
      {v::FieldLocator::Interface,
       [](v::SessionContext &context) { context.interface_name = "other"; }},
      {v::FieldLocator::Target, [](v::SessionContext &context) { context.target = "other"; }},
      {v::FieldLocator::Nonce, [](v::SessionContext &context) { context.nonce = kNonce + 1U; }},
      {v::FieldLocator::AllowedActions,
       [](v::SessionContext &context) { context.allowed_actions.pop_back(); }},
      {v::FieldLocator::Validity, [](v::SessionContext &context) { context.valid_until = 2500; }},
      {v::FieldLocator::Quota, [](v::SessionContext &context) { context.quotas.clear(); }},
  };
  for (const auto &row : cases) {
    ManagerFixture fixture;
    const v::Permit permit = make_valid_permit();
    v::SessionContext context = context_for(permit);
    row.second(context);
    const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
    v::SessionHandle handle{};
    EXPECT_EQ(fixture.manager.consume(fixture.controller, permit, context, handle),
              v::Result::PermitMismatch);
    EXPECT_EQ(fixture.manager.manager_snapshot(), before);
    ASSERT_TRUE(fixture.manager.last_diagnostic().locator().has_value());
    EXPECT_EQ(fixture.manager.last_diagnostic().locator().value(),
              static_cast<std::uint32_t>(row.first));
  }
}

TEST(SessionManagerUnit, NOMUT_02) {
  {
    ManagerFixture fixture;
    const v::Permit permit = make_valid_permit();
    v::SessionHandle handle{};
    ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
    const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
    EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle),
              v::Result::SessionAlreadyConsumed);
    EXPECT_EQ(fixture.manager.manager_snapshot(), before);
  }
  {
    ManagerFixture fixture;
    const v::Permit permit = make_valid_permit();
    v::SessionHandle handle{};
    ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
    const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
    const v::Permit changed = make_permit(session_id(1), kNonce + 1U, 10, kMono);
    EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, changed, handle),
              v::Result::SessionAlreadyConsumed);
    EXPECT_EQ(fixture.manager.manager_snapshot(), before);
  }
  {
    ManagerFixture fixture;
    const v::Permit first = make_permit(session_id(1), kNonce, 10, kMono);
    const v::Permit rebound = make_permit(session_id(2), kNonce, 10, kMono);
    v::SessionHandle handle{};
    ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, first, handle), v::Result::Ok);
    const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
    EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, rebound, handle),
              v::Result::PermitAlreadyConsumed);
    EXPECT_EQ(fixture.manager.manager_snapshot(), before);
  }
  {
    ManagerFixture fixture;
    const v::Permit first = make_permit(session_id(1), kNonce, 10, kMono);
    const v::Permit second = make_permit(session_id(2), kNonce, 10, kMono);
    const v::Permit third = make_permit(session_id(3), kNonce, 10, kMono);
    v::SessionHandle handle{};
    ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, first, handle), v::Result::Ok);
    ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, second, handle),
              v::Result::PermitAlreadyConsumed);
    const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
    EXPECT_EQ(consume_permit(fixture.manager, fixture.controller, third, handle),
              v::Result::PermitAlreadyConsumed);
    EXPECT_EQ(fixture.manager.manager_snapshot(), before);
  }
}

TEST(SessionManagerUnit, NOMUT_03) {
  v::TimeAuthority authority(8, 8);
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1000), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1000), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_clock(4, constant_source(std::nullopt), v::ClockKind::Monotonic, 0,
                                    1000000),
            v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(5, constant_source(1000001), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  std::vector<v::Timestamp> readings{1000, 999};
  std::size_t position = 0;
  ASSERT_EQ(authority.declare_clock(
                6,
                [&readings, &position]() -> std::optional<v::Timestamp> {
                  return readings.at(position++);
                },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kMono, kWall, 11, 10), v::Result::Ok);
  v::Timestamp out = 0;
  ASSERT_EQ(authority.now(6, out), v::Result::Ok);
  const std::size_t domains = authority.domain_count();
  const std::size_t mappings = authority.mapping_count();
  EXPECT_EQ(authority.now(0xDEADU, out), v::Result::UnknownClock);
  EXPECT_EQ(authority.now(4, out), v::Result::ClockSourceFailure);
  EXPECT_EQ(authority.now(5, out), v::Result::ClockOutOfBounds);
  EXPECT_EQ(authority.now(6, out), v::Result::ClockRegression);
  EXPECT_EQ(authority.convert(kMono, kOther, 1000, out), v::Result::MissingMapping);
  EXPECT_EQ(authority.convert(kMono, kWall, 1000, out), v::Result::ToleranceExceeded);
  EXPECT_EQ(authority.convert(kMono, kWall, std::numeric_limits<v::Timestamp>::max(), out),
            v::Result::ClockOverflow);
  EXPECT_EQ(authority.domain_count(), domains);
  EXPECT_EQ(authority.mapping_count(), mappings);
  ASSERT_TRUE(authority.baseline(6).has_value());
  EXPECT_EQ(authority.baseline(6).value(), 1000);
}

TEST(SessionManagerUnit, NOMUT_04) {
  const auto check = [](const std::vector<v::Action> &setup, v::Action attempt,
                        v::Result expected) {
    ManagerFixture fixture;
    const v::Permit permit = make_full_permit();
    v::SessionHandle handle{};
    ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
    v::Diagnostic diagnostic;
    for (const v::Action action : setup) {
      ASSERT_EQ(fixture.manager.transition(handle, action, kMono, 1500, diagnostic), v::Result::Ok);
    }
    v::SessionSnapshot before;
    ASSERT_EQ(fixture.manager.session_snapshot(handle, before), v::Result::Ok);
    EXPECT_EQ(fixture.manager.transition(handle, attempt, kMono, 1500, diagnostic), expected);
    v::SessionSnapshot after;
    ASSERT_EQ(fixture.manager.session_snapshot(handle, after), v::Result::Ok);
    EXPECT_EQ(after, before);
  };
  check({v::Action::Arm, v::Action::Expire}, v::Action::Arm, v::Result::TerminalState);
  check({v::Action::Arm, v::Action::Activate, v::Action::Close, v::Action::Finalize},
        v::Action::Arm, v::Result::TerminalState);
  check({}, v::Action::Activate, v::Result::InvalidTransition);
  check({v::Action::Arm, v::Action::Activate}, v::Action::Arm, v::Result::InvalidTransition);
  check({v::Action::Arm}, v::Action::Arm, v::Result::AlreadyApplied);
  check({v::Action::Arm, v::Action::Activate, v::Action::Close, v::Action::Finalize},
        v::Action::Finalize, v::Result::AlreadyApplied);
  check({v::Action::Arm, v::Action::Revoke}, v::Action::Revoke, v::Result::AlreadyApplied);
  check({}, v::Action::Close, v::Result::InvalidTransition);
}

TEST(SessionManagerUnit, NOMUT_05) {
  {
    v::ValidationSession session = make_session(1U, v::LifecycleState::armed);
    const v::SessionSnapshot before_ok = session.snapshot();
    ASSERT_EQ(session.apply(v::Action::Activate, 1500), v::Result::Ok);
    const v::SessionSnapshot exhausted = session.snapshot();
    EXPECT_EQ(session.apply(v::Action::Activate, 1500), v::Result::QuotaExhausted);
    EXPECT_EQ(session.snapshot(), exhausted);
    EXPECT_NE(before_ok, exhausted);
  }
  {
    ManagerFixture fixture;
    for (std::uint8_t seed = 1; seed <= 8; ++seed) {
      v::SessionHandle live{};
      ASSERT_EQ(
          consume_permit(fixture.manager, fixture.controller, make_distinct_permit(seed), live),
          v::Result::Ok);
    }
    const v::ManagerSnapshot before = fixture.manager.manager_snapshot();
    v::SessionHandle rejected{};
    EXPECT_EQ(
        consume_permit(fixture.manager, fixture.controller, make_distinct_permit(9), rejected),
        v::Result::CapacityExhausted);
    EXPECT_EQ(fixture.manager.manager_snapshot(), before);
  }
  {
    v::PermitRegistry registry(2, 16);
    const v::ControllerId controller = controller_id(1);
    ASSERT_EQ(registry.try_consume(controller, permit_id_from(1), session_id(1)), v::Result::Ok);
    ASSERT_EQ(registry.try_consume(controller, permit_id_from(2), session_id(2)), v::Result::Ok);
    const std::size_t permits = registry.size();
    const std::size_t sessions = registry.session_size();
    EXPECT_EQ(registry.try_consume(controller, permit_id_from(3), session_id(3)),
              v::Result::CapacityExhausted);
    EXPECT_EQ(registry.size(), permits);
    EXPECT_EQ(registry.session_size(), sessions);
  }
}

TEST(SessionManagerUnit, NOMUT_06) {
  ManagerFixture fixture;
  v::SessionHandle handle_a{};
  v::SessionHandle handle_b{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(1), handle_a),
            v::Result::Ok);
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, make_distinct_permit(2), handle_b),
            v::Result::Ok);
  v::SessionSnapshot snapshot_a;
  v::SessionSnapshot snapshot_b;
  ASSERT_EQ(fixture.manager.session_snapshot(handle_a, snapshot_a), v::Result::Ok);
  ASSERT_EQ(fixture.manager.session_snapshot(handle_b, snapshot_b), v::Result::Ok);
  const v::SessionHandle forged{scope_id(1), controller_id(252), 4, session_id(252)};
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(forged, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::InvalidHandle);
  v::SessionSnapshot after_a;
  v::SessionSnapshot after_b;
  ASSERT_EQ(fixture.manager.session_snapshot(handle_a, after_a), v::Result::Ok);
  ASSERT_EQ(fixture.manager.session_snapshot(handle_b, after_b), v::Result::Ok);
  EXPECT_EQ(after_a, snapshot_a);
  EXPECT_EQ(after_b, snapshot_b);
}

TEST(SessionManagerUnit, NOMUT_07) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
  v::Timestamp mono_now = 100;
  v::Timestamp wall_now = 200;
  ASSERT_EQ(manager.time_authority().declare_clock(
                kMono, [&mono_now]() -> std::optional<v::Timestamp> { return mono_now; },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_clock(
                kWall, [&wall_now]() -> std::optional<v::Timestamp> { return wall_now; },
                v::ClockKind::WallClock, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_mapping(kWall, kMono, 0, 1), v::Result::Ok);
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(manager.time_authority().now(kMono, baseline_out), v::Result::Ok);
  EXPECT_EQ(baseline_out, 100);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(manager.consume(controller, permit, context_for(permit), handle), v::Result::Ok);
  const TransitionFixtureSnapshot before = capture_transition_state(manager, handle);
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager.transition(handle, v::Action::Arm, kWall, 200, diagnostic),
            v::Result::ToleranceExceeded);
  EXPECT_EQ(diagnostic.primary(), v::Result::ToleranceExceeded);
  EXPECT_EQ(capture_transition_state(manager, handle), before);
  ASSERT_TRUE(manager.time_authority().baseline(kMono).has_value());
  EXPECT_EQ(manager.time_authority().baseline(kMono).value(), 100);
  v::Timestamp next = 0;
  EXPECT_EQ(manager.time_authority().now(kMono, next), v::Result::Ok);
  EXPECT_EQ(next, 100);
}

/// F-02: an in-domain now earlier than the permit validity start is rejected with the exact
/// result and leaves manager, session, and authority state byte-identical.
TEST(SessionManagerUnit, TransitionRejectsPermitNotYetValidInDomain) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 500;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Arm, kMono, 500,
                                      v::Result::PermitNotYetValid);
}

/// F-02: an in-domain now at or after the permit validity end is rejected without mutation.
TEST(SessionManagerUnit, TransitionRejectsPermitExpiredInDomain) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 2000;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Arm, kMono, 2000,
                                      v::Result::PermitExpired);
}

/// F-01/F-02: a cross-domain now that maps before the validity start is rejected with the
/// exact result and, critically, leaves the destination authority baseline unchanged.
TEST(SessionManagerUnit, TransitionRejectsPermitNotYetValidCrossDomain) {
  ManagerFixture fixture;
  v::Timestamp mono_reading = 1500;
  v::Timestamp wall_reading = 500;
  declare_cross_domain_pair(
      fixture.manager, [&mono_reading]() -> std::optional<v::Timestamp> { return mono_reading; },
      [&wall_reading]() -> std::optional<v::Timestamp> { return wall_reading; });
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, baseline_out), v::Result::Ok);
  ASSERT_EQ(baseline_out, 1500);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  mono_reading = 500;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Arm, kWall, 500,
                                      v::Result::PermitNotYetValid);
}

/// F-01/F-02: a cross-domain now that maps at or after the validity end is rejected and the
/// destination authority baseline is byte-identical before and after.
TEST(SessionManagerUnit, TransitionRejectsPermitExpiredCrossDomain) {
  ManagerFixture fixture;
  v::Timestamp mono_reading = 1500;
  v::Timestamp wall_reading = 2000;
  declare_cross_domain_pair(
      fixture.manager, [&mono_reading]() -> std::optional<v::Timestamp> { return mono_reading; },
      [&wall_reading]() -> std::optional<v::Timestamp> { return wall_reading; });
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, baseline_out), v::Result::Ok);
  ASSERT_EQ(baseline_out, 1500);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  mono_reading = 2000;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Arm, kWall, 2000,
                                      v::Result::PermitExpired);
}

/// F-01/F-02: an action outside the permit allowed set is rejected after a cross-domain
/// conversion and leaves the destination authority baseline unchanged.
TEST(SessionManagerUnit, TransitionRejectsActionNotAllowed) {
  ManagerFixture fixture;
  v::Timestamp mono_reading = 1500;
  v::Timestamp wall_reading = 1500;
  declare_cross_domain_pair(
      fixture.manager, [&mono_reading]() -> std::optional<v::Timestamp> { return mono_reading; },
      [&wall_reading]() -> std::optional<v::Timestamp> { return wall_reading; });
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, baseline_out), v::Result::Ok);
  ASSERT_EQ(baseline_out, 1500);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Expire, kWall, 1500,
                                      v::Result::ActionNotAllowed);
}

/// F-02: an undefined action mask is rejected through the real transition path with the exact
/// result and no state mutation.
TEST(SessionManagerUnit, TransitionRejectsUndefinedAction) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  expect_transition_rejects_unchanged(fixture.manager, handle, static_cast<v::Action>(0x80U), kMono,
                                      1500, v::Result::UndefinedAction);
}

/// Design §8.3: time validation precedes action validation, so an expired permit with an
/// undefined action reports PermitExpired (not UndefinedAction) without any mutation.
TEST(SessionManagerUnit, TransitionExpiredWithUndefinedActionReportsPermitExpired) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 2000;
  expect_transition_rejects_unchanged(fixture.manager, handle, static_cast<v::Action>(0x80U), kMono,
                                      2000, v::Result::PermitExpired);
}

TEST(SessionManagerUnit, ADV_R1a) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  const TransitionFixtureSnapshot before = capture_transition_state(fixture.manager, handle);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, 0xDEADU, 1500, diagnostic),
            v::Result::UnknownClock);
  EXPECT_EQ(diagnostic.primary(), v::Result::UnknownClock);
  EXPECT_EQ(capture_transition_state(fixture.manager, handle), before);
}

TEST(SessionManagerUnit, ADV_R1b) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 2500;
  const TransitionFixtureSnapshot before = capture_transition_state(fixture.manager, handle);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::ToleranceExceeded);
  EXPECT_EQ(diagnostic.primary(), v::Result::ToleranceExceeded);
  EXPECT_EQ(capture_transition_state(fixture.manager, handle), before);
}

TEST(SessionManagerUnit, ADV_R1c) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  // Out of bounds.
  fixture.mono_value = 1000001;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Arm, kMono, 1500,
                                      v::Result::ClockOutOfBounds);
  // Regressing clock: establish a baseline, then regress.
  fixture.mono_value = 1000;
  v::Timestamp baseline_out = 0;
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, baseline_out), v::Result::Ok);
  fixture.mono_value = 999;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Arm, kMono, 1500,
                                      v::Result::ClockRegression);
  // Source failure.
  fixture.mono_value = std::nullopt;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Arm, kMono, 1500,
                                      v::Result::ClockSourceFailure);
}

TEST(SessionManagerUnit, ADV_R1d) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 2500;
  const TransitionFixtureSnapshot before = capture_transition_state(fixture.manager, handle);
  v::Diagnostic diagnostic;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 2500, diagnostic),
            v::Result::PermitExpired);
  EXPECT_EQ(diagnostic.primary(), v::Result::PermitExpired);
  EXPECT_EQ(capture_transition_state(fixture.manager, handle), before);
}

TEST(SessionManagerUnit, ADV_R2a) {
  v::SessionManager manager_a(scoped_config(1));
  v::SessionManager manager_b(scoped_config(2));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager_a.register_controller(controller, "ctrl"), v::Result::Ok);
  ASSERT_EQ(manager_b.register_controller(controller, "ctrl"), v::Result::Ok);
  ASSERT_EQ(manager_b.time_authority().declare_clock(kMono, constant_source(1500),
                                                     v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  const v::Permit permit_a = make_distinct_permit(1);
  const v::Permit permit_b = make_distinct_permit(2);
  v::SessionHandle handle_a{};
  v::SessionHandle handle_b{};
  ASSERT_EQ(manager_a.consume(controller, permit_a, context_for(permit_a), handle_a),
            v::Result::Ok);
  ASSERT_EQ(manager_b.consume(controller, permit_b, context_for(permit_b), handle_b),
            v::Result::Ok);
  v::SessionSnapshot snapshot_b;
  ASSERT_EQ(manager_b.session_snapshot(handle_b, snapshot_b), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager_b.transition(handle_a, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::ForeignHandle);
  v::SessionSnapshot after_b;
  ASSERT_EQ(manager_b.session_snapshot(handle_b, after_b), v::Result::Ok);
  EXPECT_EQ(after_b, snapshot_b);
}

TEST(SessionManagerUnit, ADV_R2b) {
  v::SessionHandle pre_recreation{};
  {
    v::SessionManager manager(scoped_config(1));
    const v::ControllerId controller = controller_id(1);
    ASSERT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
    ASSERT_EQ(manager.time_authority().declare_clock(kMono, constant_source(1500),
                                                     v::ClockKind::Monotonic, 0, 1000000),
              v::Result::Ok);
    const v::Permit permit = make_valid_permit();
    ASSERT_EQ(manager.consume(controller, permit, context_for(permit), pre_recreation),
              v::Result::Ok);
  }
  v::SessionManager recreated(scoped_config(2));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(recreated.register_controller(controller, "ctrl"), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(recreated.transition(pre_recreation, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::ForeignHandle);
  EXPECT_EQ(recreated.manager_snapshot().live_sessions, 0U);
}

/// R6: with no pre-existing baseline, a successful same-domain transition establishes the
/// monotonic baseline, so a later backward reading is rejected as ClockRegression without
/// mutating session state or quota, while a non-regressing later reading is still accepted.
TEST(SessionManagerUnit, BUG_R6_UnseededSameDomain) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  ASSERT_FALSE(fixture.manager.time_authority().baseline(kMono).has_value());
  fixture.mono_value = 1500;
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_TRUE(fixture.manager.time_authority().baseline(kMono).has_value());
  EXPECT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1500);
  const TransitionFixtureSnapshot before = capture_transition_state(fixture.manager, handle);
  fixture.mono_value = 1400;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Activate, kMono, 1400, diagnostic),
            v::Result::ClockRegression);
  EXPECT_EQ(diagnostic.primary(), v::Result::ClockRegression);
  EXPECT_EQ(diagnostic.size(), 1U);
  EXPECT_EQ(capture_transition_state(fixture.manager, handle), before);
  fixture.mono_value = 1600;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Activate, kMono, 1600, diagnostic),
            v::Result::Ok);
}

/// R6: a successful same-domain transition advances a baseline that was already seeded through
/// the public authority path, so a backward reading below the advanced baseline is rejected.
TEST(SessionManagerUnit, BUG_R6_SeededSameDomain) {
  ManagerFixture fixture;
  fixture.mono_value = 1500;
  v::Timestamp seeded = 0;
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, seeded), v::Result::Ok);
  EXPECT_EQ(seeded, 1500);
  ASSERT_TRUE(fixture.manager.time_authority().baseline(kMono).has_value());
  ASSERT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1500);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 1600;
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1600, diagnostic),
            v::Result::Ok);
  ASSERT_TRUE(fixture.manager.time_authority().baseline(kMono).has_value());
  EXPECT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1600);
  const TransitionFixtureSnapshot before = capture_transition_state(fixture.manager, handle);
  fixture.mono_value = 1500;
  EXPECT_EQ(fixture.manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::ClockRegression);
  EXPECT_EQ(diagnostic.primary(), v::Result::ClockRegression);
  EXPECT_EQ(capture_transition_state(fixture.manager, handle), before);
}

/// R6: a successful transition that resolves through a declared mapping advances both the
/// source (now) domain baseline and the destination (validity) domain baseline, so a backward
/// reading in either domain is rejected as ClockRegression without side effects.
TEST(SessionManagerUnit, BUG_R6_MappedDomain) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
  v::Timestamp source_value = 1500;
  v::Timestamp destination_value = 1500;
  ASSERT_EQ(manager.time_authority().declare_clock(
                kWall, [&source_value]() -> std::optional<v::Timestamp> { return source_value; },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_clock(
                kMono,
                [&destination_value]() -> std::optional<v::Timestamp> { return destination_value; },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_mapping(kWall, kMono, 0, 10), v::Result::Ok);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(manager, controller, permit, handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  ASSERT_EQ(manager.transition(handle, v::Action::Arm, kWall, 1500, diagnostic), v::Result::Ok);
  ASSERT_TRUE(manager.time_authority().baseline(kWall).has_value());
  EXPECT_EQ(manager.time_authority().baseline(kWall).value(), 1500);
  ASSERT_TRUE(manager.time_authority().baseline(kMono).has_value());
  EXPECT_EQ(manager.time_authority().baseline(kMono).value(), 1500);
  const TransitionFixtureSnapshot before = capture_transition_state(manager, handle);
  source_value = 1400;
  EXPECT_EQ(manager.transition(handle, v::Action::Activate, kWall, 1400, diagnostic),
            v::Result::ClockRegression);
  EXPECT_EQ(diagnostic.primary(), v::Result::ClockRegression);
  EXPECT_EQ(capture_transition_state(manager, handle), before);
  source_value = 1500;
  destination_value = 1400;
  EXPECT_EQ(manager.transition(handle, v::Action::Activate, kWall, 1500, diagnostic),
            v::Result::ClockRegression);
  EXPECT_EQ(capture_transition_state(manager, handle), before);
}

/// R6: every rejected transition category (time, validity, action, state, quota) after a
/// successful baseline-establishing transition leaves the authority baselines, session state,
/// quota, and manager bookkeeping unchanged.
TEST(SessionManagerUnit, BUG_R6_RejectionPreservesState) {
  ManagerFixture fixture;
  const v::Permit permit = make_permit(session_id(1), kNonce, 1U, kMono);
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 1500;
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_TRUE(fixture.manager.time_authority().baseline(kMono).has_value());
  ASSERT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1500);
  fixture.mono_value = 1400;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Activate, kMono, 1400,
                                      v::Result::ClockRegression);
  fixture.mono_value = 2000;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Activate, kMono, 2000,
                                      v::Result::PermitExpired);
  fixture.mono_value = 1500;
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Expire, kMono, 1500,
                                      v::Result::ActionNotAllowed);
  expect_transition_rejects_unchanged(fixture.manager, handle, static_cast<v::Action>(0x80U), kMono,
                                      1500, v::Result::UndefinedAction);
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Close, kMono, 1500,
                                      v::Result::InvalidTransition);
  expect_transition_rejects_unchanged(fixture.manager, handle, v::Action::Activate, kMono, 1500,
                                      v::Result::QuotaExhausted);
  ASSERT_TRUE(fixture.manager.time_authority().baseline(kMono).has_value());
  EXPECT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1500);
  v::LifecycleState state = v::LifecycleState::closed;
  ASSERT_EQ(fixture.manager.state(handle, state), v::Result::Ok);
  EXPECT_EQ(state, v::LifecycleState::armed);
  v::SessionSnapshot snapshot;
  ASSERT_EQ(fixture.manager.session_snapshot(handle, snapshot), v::Result::Ok);
  EXPECT_EQ(snapshot.operations_remaining, 0U);
}

/// R6 concurrency: a successful transition's deferred baseline advance races concurrent public
/// authority reads without ever lowering the retained baseline; the backward reading is still
/// rejected once every concurrent reader has completed.
TEST(SessionManagerUnit, BUG_R6_ConcurrentAuthorityAccess) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
  std::atomic<v::Timestamp> source{1500};
  ASSERT_EQ(manager.time_authority().declare_clock(
                kMono, [&source]() -> std::optional<v::Timestamp> { return source.load(); },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(manager, controller, permit, handle), v::Result::Ok);
  constexpr std::size_t kReaders = 8;
  std::atomic<int> failures{0};
  std::vector<std::thread> readers;
  readers.reserve(kReaders);
  for (std::size_t index = 0; index < kReaders; ++index) {
    readers.emplace_back([&manager, &failures]() {
      for (int iteration = 0; iteration < 200; ++iteration) {
        v::Timestamp out = 0;
        if (manager.time_authority().now(kMono, out) != v::Result::Ok) {
          ++failures;
        }
      }
    });
  }
  v::Diagnostic diagnostic;
  ASSERT_EQ(manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic), v::Result::Ok);
  for (std::thread &reader : readers) {
    reader.join();
  }
  EXPECT_EQ(failures.load(), 0);
  ASSERT_TRUE(manager.time_authority().baseline(kMono).has_value());
  EXPECT_EQ(manager.time_authority().baseline(kMono).value(), 1500);
  source = 1400;
  const TransitionFixtureSnapshot before = capture_transition_state(manager, handle);
  EXPECT_EQ(manager.transition(handle, v::Action::Activate, kMono, 1400, diagnostic),
            v::Result::ClockRegression);
  EXPECT_EQ(capture_transition_state(manager, handle), before);
  v::Timestamp out = 0;
  EXPECT_EQ(manager.time_authority().now(kMono, out), v::Result::ClockRegression);
}

/// R6 re-declaration: an observation captured from one clock declaration must never seed the
/// retained baseline of a replacement declaration of the same domain. The deterministic probe
/// places the re-declaration between the transition's non-mutating peek and its deferred commit;
/// the stale commit must be refused, leaving the replacement declaration with no baseline.
TEST(SessionManagerUnit, BUG_R6_ConcurrentRedeclaration) {
  ManagerFixture fixture;
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 1500;
  v::SessionManagerProbe::set_hook(fixture.manager, [&fixture]() {
    // A re-declaration that lands after the transition's peek and before its commit.
    fixture.mono_value = 1500;
    EXPECT_EQ(fixture.manager.time_authority().declare_clock(
                  kMono, [&fixture]() -> std::optional<v::Timestamp> { return fixture.mono_value; },
                  v::ClockKind::Monotonic, 0, 1000000),
              v::Result::Ok);
  });
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::Ok);
  v::SessionManagerProbe::clear_hook(fixture.manager);
  // The replacement declaration must not inherit the pre-declaration observation.
  EXPECT_FALSE(fixture.manager.time_authority().baseline(kMono).has_value());
  // It still serves ordinary public reads, and regression is measured against its own baseline.
  fixture.mono_value = 1400;
  v::Timestamp out = 0;
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, out), v::Result::Ok);
  EXPECT_EQ(out, 1400);
  ASSERT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1400);
  fixture.mono_value = 1300;
  EXPECT_EQ(fixture.manager.time_authority().now(kMono, out), v::Result::ClockRegression);
}

/// R6 mapped re-declaration: for a mapped transition the destination baseline is committed to
/// the destination-domain host reading used by the tolerance check. The deterministic probe
/// re-declares the destination domain between that read and the deferred commit, so the reading
/// must not be attributed to the replacement. The untouched source declaration is retained.
TEST(SessionManagerUnit, BUG_R6_MappedRedeclaration) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "ctrl"), v::Result::Ok);
  v::Timestamp source_value = 1500;
  v::Timestamp destination_value = 1500;
  ASSERT_EQ(manager.time_authority().declare_clock(
                kWall, [&source_value]() -> std::optional<v::Timestamp> { return source_value; },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_clock(
                kMono,
                [&destination_value]() -> std::optional<v::Timestamp> { return destination_value; },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_mapping(kWall, kMono, 0, 10), v::Result::Ok);
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(manager, controller, permit, handle), v::Result::Ok);
  v::SessionManagerProbe::set_hook(manager, [&manager, &destination_value]() {
    EXPECT_EQ(
        manager.time_authority().declare_clock(
            kMono,
            [&destination_value]() -> std::optional<v::Timestamp> { return destination_value; },
            v::ClockKind::Monotonic, 0, 1000000),
        v::Result::Ok);
  });
  v::Diagnostic diagnostic;
  ASSERT_EQ(manager.transition(handle, v::Action::Arm, kWall, 1500, diagnostic), v::Result::Ok);
  v::SessionManagerProbe::clear_hook(manager);
  // The untouched source declaration retains the reading it produced.
  ASSERT_TRUE(manager.time_authority().baseline(kWall).has_value());
  EXPECT_EQ(manager.time_authority().baseline(kWall).value(), 1500);
  // The replacement destination declaration must not inherit the mapped destination reading.
  EXPECT_FALSE(manager.time_authority().baseline(kMono).has_value());
  destination_value = 1400;
  v::Timestamp out = 0;
  ASSERT_EQ(manager.time_authority().now(kMono, out), v::Result::Ok);
  EXPECT_EQ(out, 1400);
}

/// R6 re-declaration, ordinary public reads: replacing a declared domain clears its retained
/// baseline, so public reads after the re-declaration are not blocked by the stale baseline, are
/// measured only against the replacement's baseline, and a later successful transition commits to
/// the replacement declaration.
TEST(SessionManagerUnit, BUG_R6_PublicReadAfterRedeclare) {
  ManagerFixture fixture;
  v::Timestamp out = 0;
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, out), v::Result::Ok);
  EXPECT_EQ(out, 1500);
  ASSERT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1500);

  // Re-declaration resets the retained baseline.
  fixture.mono_value = 1400;
  ASSERT_EQ(fixture.manager.time_authority().declare_clock(
                kMono, [&fixture]() -> std::optional<v::Timestamp> { return fixture.mono_value; },
                v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  ASSERT_FALSE(fixture.manager.time_authority().baseline(kMono).has_value());

  // An ordinary public read admits the new, lower reading and seeds the replacement baseline.
  ASSERT_EQ(fixture.manager.time_authority().now(kMono, out), v::Result::Ok);
  EXPECT_EQ(out, 1400);
  ASSERT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1400);

  // Regression is measured against the replacement baseline only.
  fixture.mono_value = 1300;
  EXPECT_EQ(fixture.manager.time_authority().now(kMono, out), v::Result::ClockRegression);

  // A later successful transition commits to the replacement declaration.
  const v::Permit permit = make_valid_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(consume_permit(fixture.manager, fixture.controller, permit, handle), v::Result::Ok);
  fixture.mono_value = 1450;
  v::Diagnostic diagnostic;
  ASSERT_EQ(fixture.manager.transition(handle, v::Action::Arm, kMono, 1450, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(fixture.manager.time_authority().baseline(kMono).value(), 1450);
  fixture.mono_value = 1440;
  EXPECT_EQ(fixture.manager.time_authority().now(kMono, out), v::Result::ClockRegression);
}
