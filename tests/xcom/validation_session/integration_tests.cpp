/**
 * \file integration_tests.cpp
 * \brief Cross-component integration tests for the standalone T025 foundation.
 *
 * These cases exercise the time authority, permit registry, and session manager together
 * on flows that no single unit owns. Registered under the CTest label `integration`.
 */

#include <xverse/xcom/validation_session.hpp>

#include <gtest/gtest.h>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace v = xverse::xcom::validation;

namespace {

constexpr v::ClockDomainId kMono = 1;
constexpr v::ClockDomainId kWall = 2;
constexpr v::Nonce kNonce = 0x4321U;

v::SessionId session_id(std::uint8_t seed) {
  v::SessionId id{};
  for (std::size_t index = 0; index < id.size(); ++index) {
    id[index] = static_cast<std::uint8_t>(seed + index);
  }
  return id;
}

v::PlanDigest plan_digest() {
  v::PlanDigest digest{};
  digest[0] = 0x33U;
  digest[5] = 0x77U;
  return digest;
}

v::ControllerId controller_id(std::uint8_t seed) {
  v::ControllerId id{};
  for (std::size_t index = 0; index < id.size(); ++index) {
    id[index] = static_cast<std::uint8_t>(0xA0U + seed + index);
  }
  return id;
}

v::ManagerScope scope_id(std::uint8_t seed) {
  v::ManagerScope scope{};
  for (std::size_t index = 0; index < scope.size(); ++index) {
    scope[index] = static_cast<std::uint8_t>(0xC0U + seed + index);
  }
  return scope;
}

v::ManagerConfig scoped_config(std::uint8_t seed = 1) {
  v::ManagerConfig config;
  config.scope = scope_id(seed);
  return config;
}

v::Permit make_permit(v::SessionId sid, v::Nonce nonce, std::uint32_t quota) {
  v::PermitBuilder builder;
  builder.set_session_id(sid);
  builder.set_plan_digest(plan_digest());
  builder.set_scenario("scn");
  builder.set_deployment("dep");
  builder.set_environment("env");
  builder.set_tool("tool");
  builder.set_interface("iface");
  builder.set_target("tgt");
  builder.set_nonce(nonce);
  builder.set_validity(kMono, 1000, 2000);
  builder.add_allowed_action(v::to_mask(v::Action::Arm));
  builder.add_allowed_action(v::to_mask(v::Action::Activate));
  builder.add_allowed_action(v::to_mask(v::Action::Close));
  builder.add_allowed_action(v::to_mask(v::Action::Finalize));
  builder.add_quota(v::Quota{v::QuotaKind::Operations, quota});
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

} // namespace

/// A consumed session completes its lifecycle when validity is asserted in a foreign domain
/// and mapped into the permit domain within tolerance.
TEST(Integration, MappedValidityCrossDomainLifecycle) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "controller-a"), v::Result::Ok);
  v::TimeAuthority &authority = manager.time_authority();
  ASSERT_EQ(
      authority.declare_clock(kMono, constant_source(1500), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(
      authority.declare_clock(kWall, constant_source(1500), v::ClockKind::WallClock, 0, 1000000),
      v::Result::Ok);
  ASSERT_EQ(authority.declare_mapping(kWall, kMono, 0, 10), v::Result::Ok);
  const v::Permit permit = make_permit(session_id(1), kNonce, 10U);
  v::SessionHandle handle{};
  ASSERT_EQ(manager.consume(controller, permit, context_for(permit), handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager.transition(handle, v::Action::Arm, kWall, 1500, diagnostic), v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Close, kMono, 1500, diagnostic), v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Finalize, kMono, 1500, diagnostic),
            v::Result::Ok);
  v::LifecycleState state = v::LifecycleState::declared;
  ASSERT_EQ(manager.state(handle, state), v::Result::Ok);
  EXPECT_EQ(state, v::LifecycleState::closed);
}

/// Quota exhaustion is reached through the real transition path and does not disturb the
/// consumed-identity bookkeeping.
TEST(Integration, QuotaExhaustionThroughTransitionPath) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "controller-b"), v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_clock(kMono, constant_source(1500),
                                                   v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  const v::Permit permit = make_permit(session_id(2), kNonce, 2U);
  v::SessionHandle handle{};
  ASSERT_EQ(manager.consume(controller, permit, context_for(permit), handle), v::Result::Ok);
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic), v::Result::Ok);
  EXPECT_EQ(manager.transition(handle, v::Action::Activate, kMono, 1500, diagnostic),
            v::Result::Ok);
  const v::ManagerSnapshot before = manager.manager_snapshot();
  EXPECT_EQ(manager.transition(handle, v::Action::Close, kMono, 1500, diagnostic),
            v::Result::QuotaExhausted);
  EXPECT_EQ(manager.manager_snapshot(), before);
  EXPECT_EQ(manager.consume(controller, permit, context_for(permit), handle),
            v::Result::SessionAlreadyConsumed);
}

/// Advancing a controller generation makes every handle issued under the old generation
/// unreachable without mutating the session it addressed.
TEST(Integration, GenerationRotationInvalidatesLiveHandle) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId controller = controller_id(1);
  ASSERT_EQ(manager.register_controller(controller, "controller-c"), v::Result::Ok);
  ASSERT_EQ(manager.time_authority().declare_clock(kMono, constant_source(1500),
                                                   v::ClockKind::Monotonic, 0, 1000000),
            v::Result::Ok);
  const v::Permit permit = make_permit(session_id(3), kNonce, 10U);
  v::SessionHandle handle{};
  ASSERT_EQ(manager.consume(controller, permit, context_for(permit), handle), v::Result::Ok);
  v::SessionSnapshot before;
  ASSERT_EQ(manager.session_snapshot(handle, before), v::Result::Ok);
  const v::Generation rotated = manager.advance_generation(controller);
  ASSERT_GT(rotated, handle.generation);
  v::Diagnostic diagnostic;
  EXPECT_EQ(manager.transition(handle, v::Action::Arm, kMono, 1500, diagnostic),
            v::Result::StaleHandle);
  v::LifecycleState state = v::LifecycleState::closed;
  EXPECT_EQ(manager.state(handle, state), v::Result::StaleHandle);
}

/// Two independent controllers consume independent permits and never share replay scope.
TEST(Integration, IndependentControllerScopes) {
  v::SessionManager manager(scoped_config(1));
  const v::ControllerId first = controller_id(1);
  const v::ControllerId second = controller_id(2);
  ASSERT_EQ(manager.register_controller(first, "controller-d"), v::Result::Ok);
  ASSERT_EQ(manager.register_controller(second, "controller-e"), v::Result::Ok);
  const v::Permit permit = make_permit(session_id(4), kNonce, 10U);
  v::SessionHandle first_handle{};
  v::SessionHandle second_handle{};
  EXPECT_EQ(manager.consume(first, permit, context_for(permit), first_handle), v::Result::Ok);
  EXPECT_EQ(manager.consume(second, permit, context_for(permit), second_handle), v::Result::Ok);
  EXPECT_NE(first_handle.controller, second_handle.controller);
  EXPECT_EQ(first_handle.scope, second_handle.scope);
  EXPECT_EQ(manager.manager_snapshot().live_sessions, 2U);
  EXPECT_EQ(manager.emission_count(), 0U);
}
