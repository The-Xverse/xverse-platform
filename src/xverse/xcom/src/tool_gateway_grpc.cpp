/**
 * @file tool_gateway_grpc.cpp
 * @brief Real generated gRPC `ToolGateway`/`GatewayLiveness` service and protected local
 *        Unix-socket server implementation for the accepted T031 gateway session.
 * @details Implements the per-request admission (cancellation, deadline, message bound), the
 *          single current watch association, serialized stateful dispatch onto the accepted
 *          `GatewaySession`, bounded observation streaming with disconnect handling, the
 *          pre-dispatch transport probe for stimulation, and the bounded server shutdown and
 *          destructor cleanup declared in `tool_gateway_grpc.hpp`. It links the admitted
 *          unsanitized gRPC runtime and opens no network, DNS, TLS, legacy, or process resource.
 * @ingroup xcom_gw
 * @par Traceability
 * Implements accepted `T031-SR-012` (exclusive generation-bound lease delegation) and
 * `T031-SR-013` (disconnect/idle cleanup of validation-owned resources); see
 * docs/engineering/xcom/t031/{requirements,detailed-design,unit-specifications}.md and
 * docs/engineering/xcom/t039/transport-repair.md.
 */

#include "xverse/xcom/tool_gateway_grpc.hpp"

#include <algorithm>
#include <array>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <limits>
#include <iterator>
#include <mutex>
#include <string>
#include <string_view>
#include <thread>
#include <utility>
#include <vector>

#include <sys/stat.h>
#include <sys/random.h>
#include <sys/un.h>
#include <unistd.h>

namespace xverse::xcom {

namespace {
std::mutex socket_creation_mutex;

bool new_watch_id(std::string &id) {
  std::array<unsigned char, 32U> bytes{};
  std::size_t filled = 0U;
  while (filled < bytes.size()) {
    const ssize_t count = ::getrandom(bytes.data() + filled, bytes.size() - filled, GRND_NONBLOCK);
    if (count < 0 && errno == EINTR) {
      continue;
    }
    if (count <= 0) {
      return false;
    }
    filled += static_cast<std::size_t>(count);
  }
  constexpr char hex[] = "0123456789abcdef";
  id.clear();
  id.reserve(2U * bytes.size());
  for (const unsigned char byte : bytes) {
    id.push_back(hex[byte >> 4U]);
    id.push_back(hex[byte & 15U]);
  }
  return true;
}

bool protected_parent(const std::string &path) {
  const std::size_t slash = path.find_last_of('/');
  if (slash == std::string::npos || slash == 0U || path.size() >= sizeof(sockaddr_un::sun_path)) {
    return false;
  }
  struct stat parent {};
  const std::string directory = path.substr(0U, slash);
  if (::stat(directory.c_str(), &parent) != 0 || !S_ISDIR(parent.st_mode) ||
      (parent.st_mode & 0077) != 0 || parent.st_uid != ::geteuid()) {
    return false;
  }
  struct stat existing {};
  return ::lstat(path.c_str(), &existing) != 0 && errno == ENOENT;
}
}  // namespace

GatewayGrpcService::GatewayGrpcService(GatewaySession &session,
                                       const GatewayConfig &config) noexcept
    : session_(session), config_(config) {}

void GatewayGrpcService::poll() noexcept { session_.poll_now(); }
void GatewayGrpcService::request_shutdown() noexcept { watch_failed_.store(true); }
void GatewayGrpcService::disconnect() noexcept {
  request_shutdown();
  session_.on_disconnect();
}
std::size_t GatewayGrpcService::message_bound() const noexcept {
  return config_.max_message_bytes();
}

grpc::Status GatewayGrpcService::check(grpc::ServerContext *context,
                                        std::size_t request_bytes) const {
  if (context == nullptr || context->IsCancelled()) {
    return {grpc::StatusCode::CANCELLED, "request cancelled"};
  }
  if (std::chrono::system_clock::now() >= context->deadline()) {
    return {grpc::StatusCode::DEADLINE_EXCEEDED, "request deadline expired"};
  }
  if (request_bytes > config_.max_message_bytes()) {
    return {grpc::StatusCode::RESOURCE_EXHAUSTED, "request exceeds message bound"};
  }
  return grpc::Status::OK;
}

grpc::Status GatewayGrpcService::require_watch(grpc::ServerContext *context) const {
  if (!watch_active_.load() || watch_failed_.load() || session_.snapshot().terminal) {
    return {grpc::StatusCode::FAILED_PRECONDITION, "active session watch required"};
  }
  const auto &metadata = context->client_metadata();
  const auto range = metadata.equal_range("x-xcom-watch-id");
  if (range.first == range.second || std::next(range.first) != range.second) {
    return {grpc::StatusCode::FAILED_PRECONDITION, "one watch association required"};
  }
  const auto &value = range.first->second;
  const std::string_view supplied(value.data(), value.size());
  std::lock_guard<std::mutex> lock(watch_mutex_);
  if (watch_id_.empty() || supplied != watch_id_) {
    return {grpc::StatusCode::FAILED_PRECONDITION, "watch association mismatch"};
  }
  return grpc::Status::OK;
}

grpc::Status GatewayGrpcService::WatchSession(
    grpc::ServerContext *context, const v1::WatchSessionRequest *request,
    grpc::ServerWriter<v1::WatchSessionReady> *writer) {
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  if (session_.snapshot().terminal) {
    return {grpc::StatusCode::FAILED_PRECONDITION, "session already terminal"};
  }
  bool expected = false;
  if (!watch_active_.compare_exchange_strong(expected, true)) {
    return {grpc::StatusCode::ALREADY_EXISTS, "session already watched"};
  }
  if (watch_failed_.load() || session_.snapshot().terminal) {
    watch_active_.store(false);
    return {grpc::StatusCode::FAILED_PRECONDITION, "session already terminal"};
  }
  std::string id;
  if (!new_watch_id(id)) {
    watch_active_.store(false);
    return {grpc::StatusCode::UNAVAILABLE, "watch association unavailable"};
  }
  {
    std::lock_guard<std::mutex> lock(watch_mutex_);
    watch_id_ = id;
  }
  v1::WatchSessionReady ready;
  ready.set_ready(true);
  ready.set_watch_id(id);
  const bool delivered = writer->Write(ready);
  if (delivered) {
    while (!context->IsCancelled() && !watch_failed_.load()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
  }
  watch_failed_.store(true);
  session_.on_disconnect();
  {
    std::lock_guard<std::mutex> lock(watch_mutex_);
    watch_id_.clear();
  }
  watch_active_.store(false);
  return {grpc::StatusCode::CANCELLED, "session watch closed"};
}

/// @brief Define one stateful unary `ToolGateway` RPC that admits, requires the watch, and
///        dispatches onto the bound session under the dispatch mutex.
/// @param method Bound `GatewaySession` method and generated service method name.
/// @param Request Generated request message type.
/// @param Response Generated response message type.
#define XCOM_GRPC_UNARY(method, Request, Response)                                      \
  grpc::Status GatewayGrpcService::method(grpc::ServerContext *context,                 \
                                           const v1::Request *request,                   \
                                           v1::Response *response) {                    \
    const auto arrival = session_.current_tick();                                        \
    std::lock_guard<std::mutex> dispatch(dispatch_mutex_);                                \
    const grpc::Status admitted = check(context, request->ByteSizeLong());              \
    if (!admitted.ok()) {                                                                \
      return admitted;                                                                   \
    }                                                                                    \
    const grpc::Status watched = require_watch(context);                                 \
    if (!watched.ok()) {                                                                  \
      return watched;                                                                    \
    }                                                                                    \
    *response = session_.method(*request, arrival);                                      \
    return grpc::Status::OK;                                                              \
  }

XCOM_GRPC_UNARY(OpenObservation, OpenObservationRequest, OpenObservationResponse)
XCOM_GRPC_UNARY(CloseObservation, CloseObservationRequest, CloseObservationResponse)
XCOM_GRPC_UNARY(RevokeSession, RevokeSessionRequest, RevokeSessionResponse)
XCOM_GRPC_UNARY(AcquireLease, AcquireLeaseRequest, AcquireLeaseResponse)
XCOM_GRPC_UNARY(ReleaseLease, ReleaseLeaseRequest, ReleaseLeaseResponse)

#undef XCOM_GRPC_UNARY

grpc::Status GatewayGrpcService::QuerySession(
    grpc::ServerContext *context, const v1::QuerySessionRequest *request,
    v1::QuerySessionResponse *response) {
  const auto arrival = session_.current_tick();
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  *response = session_.QuerySession(*request, arrival);
  return grpc::Status::OK;
}

grpc::Status GatewayGrpcService::SubmitStimulation(
    grpc::ServerContext *context, const v1::SubmitStimulationRequest *request,
    v1::SubmitStimulationResponse *response) {
  const auto arrival = session_.current_tick();
  std::lock_guard<std::mutex> dispatch(dispatch_mutex_);
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  const grpc::Status watched = require_watch(context);
  if (!watched.ok()) {
    return watched;
  }
  // Response diagnostics are bounded, but request_id is echoed. Reserve enough
  // space before entering the action path so send-size rejection cannot follow emission.
  constexpr std::size_t response_overhead = 512U;
  if (config_.max_message_bytes() <= response_overhead ||
      request->request_id().size() + request->contract_id().size() >
          config_.max_message_bytes() - response_overhead) {
    return {grpc::StatusCode::RESOURCE_EXHAUSTED, "response would exceed message bound"};
  }
  struct TransportProbe {
    grpc::ServerContext *call;
    GatewayGrpcService *service;
  } probe{context, this};
  const auto cancelled = [](void *opaque) noexcept {
    const auto *state = static_cast<TransportProbe *>(opaque);
    return state->call->IsCancelled() || state->service->watch_failed_.load() ||
           std::chrono::system_clock::now() >= state->call->deadline();
  };
  *response = session_.SubmitStimulation(*request, arrival, cancelled, &probe);
  if (response->diagnostic().code() == "gw.transport.cancelled") {
    const grpc::Status ended = check(context, 0U);
    return ended.ok() ? grpc::Status(grpc::StatusCode::CANCELLED, "transport ended before dispatch")
                      : ended;
  }
  return grpc::Status::OK;
}

grpc::Status GatewayGrpcService::QueryVersion(grpc::ServerContext *context,
                                               const v1::QueryVersionRequest *request,
                                               v1::QueryVersionResponse *response) {
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  *response = session_.QueryVersion(*request);
  return check(context, response->ByteSizeLong());
}

grpc::Status GatewayGrpcService::ArmSession(grpc::ServerContext *context,
                                             const v1::ArmSessionRequest *request,
                                             v1::ArmSessionResponse *response) {
  const auto arrival = session_.current_tick();
  std::lock_guard<std::mutex> dispatch(dispatch_mutex_);
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  const grpc::Status watched = require_watch(context);
  if (!watched.ok()) {
    return watched;
  }
  if (!request->has_protocol() ||
      session_.negotiate(request->protocol()) != GatewayOutcome::accepted) {
    return {grpc::StatusCode::FAILED_PRECONDITION, "unsupported protocol version"};
  }
  *response = session_.ArmSession(*request, arrival);
  return grpc::Status::OK;
}

grpc::Status GatewayGrpcService::ReadObservations(
    grpc::ServerContext *context, const v1::ReadObservationsRequest *request,
    grpc::ServerWriter<v1::ObservationRecord> *writer) {
  const auto arrival = session_.current_tick();
  std::lock_guard<std::mutex> dispatch(dispatch_mutex_);
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  const grpc::Status watched = require_watch(context);
  if (!watched.ok()) {
    return watched;
  }
  const std::size_t bound = std::min<std::size_t>(request->max_records(),
                                                 config_.max_observation_records());
  std::vector<v1::ObservationRecord> records(bound);
  GatewayOutcome outcome = GatewayOutcome::rejected;
  const std::size_t count = session_.ReadObservations(*request, records, arrival, &outcome);
  if (outcome == GatewayOutcome::expired) {
    return {grpc::StatusCode::DEADLINE_EXCEEDED, "observation read deadline expired"};
  }
  if (outcome != GatewayOutcome::accepted) {
    return {grpc::StatusCode::FAILED_PRECONDITION, "observation read rejected"};
  }
  for (std::size_t index = 0U; index < count; ++index) {
    const grpc::Status ready = check(context, records[index].ByteSizeLong());
    if (!ready.ok()) {
      session_.on_disconnect();
      return ready;
    }
    if (!writer->Write(records[index])) {
      session_.on_disconnect();
      return {grpc::StatusCode::CANCELLED, "observation reader disconnected"};
    }
  }
  return grpc::Status::OK;
}

GatewayGrpcServer::GatewayGrpcServer(std::string path,
                                     std::unique_ptr<grpc::Server> server,
                                     GatewayGrpcService &service)
    : path_(std::move(path)), server_(std::move(server)),
      service_(service),
      poller_([this, &service] {
        while (active_.load()) {
          std::this_thread::sleep_for(std::chrono::milliseconds(10));
          if (active_.load()) {
            service.poll();
          }
        }
      }) {}

std::unique_ptr<GatewayGrpcServer> GatewayGrpcServer::start(
    const std::string &socket_path, GatewayGrpcService &service,
    std::size_t max_message_bytes) {
  // Every fixed gateway response fits within this local transport floor.
  if (max_message_bytes < 1024U || max_message_bytes != service.message_bound() ||
      max_message_bytes > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
    return nullptr;
  }
  std::lock_guard<std::mutex> lock(socket_creation_mutex);
  if (!protected_parent(socket_path)) {
    return nullptr;
  }
  grpc::ServerBuilder builder;
  builder.SetMaxReceiveMessageSize(static_cast<int>(max_message_bytes));
  builder.SetMaxSendMessageSize(static_cast<int>(max_message_bytes));
  grpc::ResourceQuota quota;
  quota.Resize(8U * 1024U * 1024U + 2U * max_message_bytes).SetMaxThreads(8);
  builder.SetResourceQuota(quota);
  builder.SetSyncServerOption(grpc::ServerBuilder::MAX_POLLERS, 4);
  builder.RegisterService(static_cast<v1::ToolGateway::Service *>(&service));
  builder.RegisterService(static_cast<v1::GatewayLiveness::Service *>(&service));
  builder.AddListeningPort("unix://" + socket_path, grpc::InsecureServerCredentials());
  const mode_t prior_umask = ::umask(0077);
  std::unique_ptr<grpc::Server> server = builder.BuildAndStart();
  ::umask(prior_umask);
  if (!server) {
    return nullptr;
  }
  if (::chmod(socket_path.c_str(), 0600) != 0) {
    server->Shutdown();
    ::unlink(socket_path.c_str());
    return nullptr;
  }
  return std::unique_ptr<GatewayGrpcServer>(
      new GatewayGrpcServer(socket_path, std::move(server), service));
}

GatewayGrpcServer::~GatewayGrpcServer() {
  active_.store(false);
  service_.request_shutdown();
  server_->Shutdown(std::chrono::system_clock::now() + std::chrono::milliseconds(100));
  poller_.join();
  service_.disconnect();
  ::unlink(path_.c_str());
}

void GatewayGrpcServer::wait() { server_->Wait(); }

}  // namespace xverse::xcom
