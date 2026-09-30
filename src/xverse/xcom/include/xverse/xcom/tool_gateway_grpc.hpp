#ifndef XVERSE_XCOM_TOOL_GATEWAY_GRPC_HPP_
#define XVERSE_XCOM_TOOL_GATEWAY_GRPC_HPP_

#include "xverse/xcom/tool_gateway.hpp"
#include "xverse/xcom/v1/gateway_liveness.grpc.pb.h"
#include "xverse/xcom/v1/tool_gateway.grpc.pb.h"

#include <grpcpp/grpcpp.h>

#include <cstddef>
#include <atomic>
#include <memory>
#include <string>
#include <thread>

namespace xverse::xcom {

/// The real generated gRPC and local liveness services for one permit-bound gateway session.
/// The owning application must keep the session and its dependencies alive until shutdown.
class GatewayGrpcService final : public v1::ToolGateway::Service,
                                 public v1::GatewayLiveness::Service {
 public:
  GatewayGrpcService(GatewaySession &session, const GatewayConfig &config) noexcept;

  grpc::Status QueryVersion(grpc::ServerContext *, const v1::QueryVersionRequest *,
                            v1::QueryVersionResponse *) override;
  grpc::Status OpenObservation(grpc::ServerContext *, const v1::OpenObservationRequest *,
                               v1::OpenObservationResponse *) override;
  grpc::Status ReadObservations(grpc::ServerContext *, const v1::ReadObservationsRequest *,
                                grpc::ServerWriter<v1::ObservationRecord> *) override;
  grpc::Status CloseObservation(grpc::ServerContext *, const v1::CloseObservationRequest *,
                                v1::CloseObservationResponse *) override;
  grpc::Status ArmSession(grpc::ServerContext *, const v1::ArmSessionRequest *,
                          v1::ArmSessionResponse *) override;
  grpc::Status RevokeSession(grpc::ServerContext *, const v1::RevokeSessionRequest *,
                             v1::RevokeSessionResponse *) override;
  grpc::Status SubmitStimulation(grpc::ServerContext *, const v1::SubmitStimulationRequest *,
                                  v1::SubmitStimulationResponse *) override;
  grpc::Status AcquireLease(grpc::ServerContext *, const v1::AcquireLeaseRequest *,
                            v1::AcquireLeaseResponse *) override;
  grpc::Status ReleaseLease(grpc::ServerContext *, const v1::ReleaseLeaseRequest *,
                            v1::ReleaseLeaseResponse *) override;
  grpc::Status QuerySession(grpc::ServerContext *, const v1::QuerySessionRequest *,
                            v1::QuerySessionResponse *) override;
  /// Keep one local session watch open until the client disconnects or cancels it.
  grpc::Status WatchSession(grpc::ServerContext *, const v1::WatchSessionRequest *,
                            grpc::ServerWriter<v1::WatchSessionReady> *) override;
  void poll() noexcept;
  void disconnect() noexcept;
  /// Maximum request and response size configured for this service.
  [[nodiscard]] std::size_t message_bound() const noexcept;

 private:
  grpc::Status check(grpc::ServerContext *, std::size_t request_bytes) const;
  grpc::Status require_watch() const;
  GatewaySession &session_;
  GatewayConfig config_;
  std::atomic<bool> watch_active_{false};
  std::atomic<bool> watch_failed_{false};
};

/// Owns a protected local Unix-socket gRPC listener. No TCP address is accepted.
class GatewayGrpcServer final {
 public:
  static std::unique_ptr<GatewayGrpcServer> start(const std::string &socket_path,
                                                   GatewayGrpcService &service,
                                                   std::size_t max_message_bytes);
  ~GatewayGrpcServer();
  GatewayGrpcServer(const GatewayGrpcServer &) = delete;
  GatewayGrpcServer &operator=(const GatewayGrpcServer &) = delete;
  void wait();

 private:
  GatewayGrpcServer(std::string path, std::unique_ptr<grpc::Server> server,
                    GatewayGrpcService &service);
  std::string path_;
  std::unique_ptr<grpc::Server> server_;
  GatewayGrpcService &service_;
  std::atomic<bool> active_{true};
  std::thread poller_;
};

}  // namespace xverse::xcom

#endif
