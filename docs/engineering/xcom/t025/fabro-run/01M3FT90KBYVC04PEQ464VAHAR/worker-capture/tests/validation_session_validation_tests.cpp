/**
 * \file validation_session_validation_tests.cpp
 * \brief Intended-use scenario and zero-emission validation tests for T025.
 *
 * These cases run the standalone foundation end to end and check the zero normal-route
 * emission contract. Registered under the CTest label `validation`.
 */

#include <xverse/xcom/validation_session.hpp>

#include <dirent.h>

#include <gtest/gtest.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace v = xverse::xcom::validation;

namespace {

constexpr v::ClockDomainId kMono = 1;
constexpr v::Nonce kNonce = 0x5150U;

v::SessionId session_id(std::uint8_t seed) {
  v::SessionId id{};
  for (std::size_t index = 0; index < id.size(); ++index) {
    id[index] = static_cast<std::uint8_t>(seed * 3U + index);
  }
  return id;
}

v::PlanDigest plan_digest() {
  v::PlanDigest digest{};
  digest[1] = 0x11U;
  digest[7] = 0x22U;
  return digest;
}

v::ControllerId controller_id(std::uint8_t seed) {
  v::ControllerId id{};
  for (std::size_t index = 0; index < id.size(); ++index) {
    id[index] = static_cast<std::uint8_t>(0x70U + seed + index);
  }
  return id;
}

v::ManagerScope scope_id(std::uint8_t seed) {
  v::ManagerScope scope{};
  for (std::size_t index = 0; index < scope.size(); ++index) {
    scope[index] = static_cast<std::uint8_t>(0x50U + seed + index);
  }
  return scope;
}

v::ManagerConfig scoped_config(std::uint8_t seed = 1) {
  v::ManagerConfig config;
  config.scope = scope_id(seed);
  return config;
}

v::Permit make_permit() {
  v::PermitBuilder builder;
  builder.set_session_id(session_id(5));
  builder.set_plan_digest(plan_digest());
  builder.set_scenario("scenario-1");
  builder.set_deployment("deployment-1");
  builder.set_environment("environment-1");
  builder.set_tool("tool-1");
  builder.set_interface("interface-1");
  builder.set_target("target-1");
  builder.set_nonce(kNonce);
  builder.set_validity(kMono, 1000, 2000);
  builder.add_allowed_action(v::to_mask(v::Action::Arm));
  builder.add_allowed_action(v::to_mask(v::Action::Activate));
  builder.add_allowed_action(v::to_mask(v::Action::Close));
  builder.add_allowed_action(v::to_mask(v::Action::Finalize));
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

v::ClockSource constant_source(v::Timestamp value) {
  return [value]() -> std::optional<v::Timestamp> { return value; };
}

std::size_t open_descriptor_count() {
  std::size_t count = 0;
  DIR *directory = opendir("/proc/self/fd");
  if (directory == nullptr) {
    return count;
  }
  while (readdir(directory) != nullptr) {
    ++count;
  }
  closedir(directory);
  return count;
}

} // namespace

/// ZEM-01: the public surface exposes only the declared operations and the observable
/// normal-route emission counter remains zero. Symbol enumeration itself is a static
/// source scan; this case asserts the runtime contract.
TEST(Validation, ZEM_01) {
  v::SessionManager manager(scoped_config(1));
  EXPECT_EQ(manager.emission_count(), 0U);
  v::TimeAuthority &authority = manager.time_authority();
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1500), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "controller-z"), v::Result::Ok);
  const v::Permit permit = make_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(manager.consume(controller, permit, context_for(permit), handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  ASSERT_EQ(manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic), v::Result::Ok);
  EXPECT_EQ(manager.emission_count(), 0U);
  EXPECT_EQ(manager.manager_snapshot().emission_count, 0U);
}

/// ZEM-03: the nominal path opens no file or socket and performs no environment I/O.
TEST(Validation, ZEM_03) {
  v::SessionManager manager(scoped_config(1));
  const std::size_t before = open_descriptor_count();
  v::TimeAuthority &authority = manager.time_authority();
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1500), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "controller-io"), v::Result::Ok);
  const v::Permit permit = make_permit();
  v::SessionHandle handle{};
  ASSERT_EQ(manager.consume(controller, permit, context_for(permit), handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  ASSERT_EQ(manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic), v::Result::Ok);
  ASSERT_EQ(manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::Ok);
  ASSERT_EQ(manager.transition(handle, v::Action::Close, kMono, 1500, diagnostic), v::Result::Ok);
  ASSERT_EQ(manager.transition(handle, v::Action::Finalize, kMono, 1500, diagnostic),
            v::Result::Ok);
  const std::size_t after = open_descriptor_count();
  EXPECT_EQ(after, before);
}

/// Intended-use scenario: a host controller presents the admitted envelope, consumes the
/// permit exactly once, walks the declared lifecycle, and observes the documented results
/// with zero normal-route emissions.
TEST(Validation, EndToEndNominalScenario) {
  v::SessionManager manager{scoped_config(1)};
  v::TimeAuthority &authority = manager.time_authority();
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1500), v::ClockKind::Monotonic, 0, 1000000),
      v::Result::Ok);
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "controller-e2e"), v::Result::Ok);
  const v::Permit permit = make_permit();
  v::SessionHandle handle{};
  EXPECT_EQ(manager.consume(controller, permit, context_for(permit), handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic), v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Close, kMono, 1500, diagnostic), v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Finalize, kMono, 1500, diagnostic),
            v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::TerminalState);
  v::LifecycleState state = v::LifecycleState::declared;
  ASSERT_EQ(manager.state(handle, state), v::Result::Ok);
  EXPECT_EQ(state, v::LifecycleState::closed);
  EXPECT_EQ(manager.manager_snapshot().live_sessions, 0U);
  EXPECT_EQ(manager.emission_count(), 0U);
}
