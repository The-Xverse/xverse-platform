#include "xverse/xcom/tool_gateway_grpc.hpp"

#include <algorithm>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <limits>
#include <mutex>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

namespace xverse::xcom {

namespace {
std::mutex socket_creation_mutex;

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
void GatewayGrpcService::disconnect() noexcept { session_.on_disconnect(); }

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

#define XCOM_GRPC_UNARY(method, Request, Response)                                      \
  grpc::Status GatewayGrpcService::method(grpc::ServerContext *context,                 \
                                           const v1::Request *request,                   \
                                           v1::Response *response) {                    \
    const auto arrival = session_.current_tick();                                        \
    const grpc::Status admitted = check(context, request->ByteSizeLong());              \
    if (!admitted.ok()) {                                                                \
      return admitted;                                                                   \
    }                                                                                    \
    *response = session_.method(*request, arrival);                                      \
    return check(context, response->ByteSizeLong());                                     \
  }

XCOM_GRPC_UNARY(OpenObservation, OpenObservationRequest, OpenObservationResponse)
XCOM_GRPC_UNARY(CloseObservation, CloseObservationRequest, CloseObservationResponse)
XCOM_GRPC_UNARY(RevokeSession, RevokeSessionRequest, RevokeSessionResponse)
XCOM_GRPC_UNARY(SubmitStimulation, SubmitStimulationRequest, SubmitStimulationResponse)
XCOM_GRPC_UNARY(AcquireLease, AcquireLeaseRequest, AcquireLeaseResponse)
XCOM_GRPC_UNARY(ReleaseLease, ReleaseLeaseRequest, ReleaseLeaseResponse)
XCOM_GRPC_UNARY(QuerySession, QuerySessionRequest, QuerySessionResponse)

#undef XCOM_GRPC_UNARY

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
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  if (!request->has_protocol() ||
      session_.negotiate(request->protocol()) != GatewayOutcome::accepted) {
    return {grpc::StatusCode::FAILED_PRECONDITION, "unsupported protocol version"};
  }
  *response = session_.ArmSession(*request, arrival);
  return check(context, response->ByteSizeLong());
}

grpc::Status GatewayGrpcService::ReadObservations(
    grpc::ServerContext *context, const v1::ReadObservationsRequest *request,
    grpc::ServerWriter<v1::ObservationRecord> *writer) {
  const auto arrival = session_.current_tick();
  const grpc::Status admitted = check(context, request->ByteSizeLong());
  if (!admitted.ok()) {
    return admitted;
  }
  const std::size_t bound = std::min<std::size_t>(request->max_records(),
                                                 config_.max_observation_records());
  std::vector<v1::ObservationRecord> records(bound);
  const std::size_t count = session_.ReadObservations(*request, records, arrival);
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
  if (max_message_bytes == 0U ||
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
  builder.RegisterService(&service);
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
  poller_.join();
  server_->Shutdown();
  service_.disconnect();
  ::unlink(path_.c_str());
}

void GatewayGrpcServer::wait() { server_->Wait(); }

}  // namespace xverse::xcom
