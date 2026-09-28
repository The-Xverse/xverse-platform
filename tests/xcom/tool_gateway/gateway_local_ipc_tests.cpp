/**
 * @file gateway_local_ipc_tests.cpp
 * @brief T031 local-IPC unit cases: the endpoint family is `AF_UNIX` only, no TCP listener is
 *        bound, and the socket file carries restrictive permissions under a restricted directory.
 * @ownership Each case owns one bounded endpoint and its scratch path.
 * @lifetime The endpoint is destroyed before the case ends and unlinks its path.
 * @thread_safety Single-threaded.
 * @bounds One socket per case; no network, DNS, resolver, TLS, or external peer is contacted.
 * @failure A non-local family, a TCP listener, or weak socket-file permissions fails the owning
 *          case closed.
 * @par Traceability
 * Supports T031-SR-008, T031-SR-009 and the T31-TS-015..T31-TS-017 cases.
 */

#include <gtest/gtest.h>

#include "gateway_support.hpp"

#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace {

using xverse::xcom::GatewayConfig;
using xverse::xcom::LocalIpcEndpoint;
using xverse::xcom::tool_gateway_test::make_config;
using xverse::xcom::tool_gateway_test::scratch_path;

}  // namespace

TEST(XcomToolGatewayLocalIpc, EndpointFamilyIsUnixOnly) {
  const GatewayConfig config = make_config();
  const std::string path = scratch_path("gateway-unix.sock");
  const std::optional<LocalIpcEndpoint> endpoint = LocalIpcEndpoint::create(config, path);
  ASSERT_TRUE(endpoint.has_value());
  EXPECT_TRUE(endpoint->is_local_unix());
  EXPECT_EQ(endpoint->family(), AF_UNIX);
  EXPECT_FALSE(endpoint->path().empty());

  EXPECT_FALSE(LocalIpcEndpoint::create(config, std::string_view{}).has_value());
}

TEST(XcomToolGatewayLocalIpc, NoTcpListenerBound) {
  const GatewayConfig config = make_config();
  const std::string path = scratch_path("gateway-no-tcp.sock");
  const std::optional<LocalIpcEndpoint> endpoint = LocalIpcEndpoint::create(config, path);
  ASSERT_TRUE(endpoint.has_value());
  EXPECT_NE(endpoint->family(), AF_INET);
  EXPECT_NE(endpoint->family(), AF_INET6);

  const int client = ::socket(AF_UNIX, SOCK_STREAM, 0);
  ASSERT_GE(client, 0);
  struct sockaddr_un address {};
  address.sun_family = AF_UNIX;
  std::string owned_path(path);
  ASSERT_LT(owned_path.size(), sizeof(address.sun_path));
  for (std::size_t index = 0U; index < owned_path.size(); ++index) {
    address.sun_path[index] = owned_path[index];
  }
  ASSERT_EQ(::connect(client, reinterpret_cast<struct sockaddr *>(&address), sizeof(address)), 0);
  const int accepted = endpoint->accept_one();
  EXPECT_GE(accepted, 0);
  if (accepted >= 0) {
    ::close(accepted);
  }
  ::close(client);
}

TEST(XcomToolGatewayLocalIpc, EndpointPermissionsRestrictAccess) {
  const GatewayConfig config = make_config();
  const std::string path = scratch_path("gateway-perms.sock");
  const std::optional<LocalIpcEndpoint> endpoint = LocalIpcEndpoint::create(config, path);
  ASSERT_TRUE(endpoint.has_value());
  EXPECT_EQ(endpoint->permission_bits(), 0600U);
}
