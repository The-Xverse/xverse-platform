/**
 * @file tool_gateway_grpc.hpp
 * @brief Real generated gRPC `ToolGateway`/`GatewayLiveness` services and the protected local
 *        Unix-socket server that carries them for one accepted T031 gateway session.
 * @details Binds the accepted `xverse.xcom.v1.ToolGateway` and `xverse.xcom.v1.GatewayLiveness`
 *          generated contracts to the accepted in-process `GatewaySession` boundary over an
 *          `AF_UNIX` listener only; no TCP address or `AF_INET`/`AF_INET6` socket is accepted.
 *          Every stateful RPC requires the session's single current watch association and passes
 *          the per-request deadline, cancellation, and message-bound admission checks before it
 *          reaches the session, and the dispatch surface is serialized against the accepted lease
 *          and stimulation boundaries. The linked gRPC runtime is the admitted unsanitized T032
 *          binary; the `GRPC_ASAN_SUPPRESSED` layout keeps its POSIX mutex ABI compatible while
 *          compiler ASan/UBSan instrumentation stays enabled with no `-fno-sanitize` site.
 * @ingroup xcom_gw
 * @ownership `GatewayGrpcService` borrows the caller-owned `GatewaySession`, copies the bounded
 *            `GatewayConfig` by value, and exclusively owns one watch association (identifier
 *            plus active/failed flags) and the dispatch mutex. `GatewayGrpcServer` owns the local
 *            listener, its poller thread, the retained socket path, and the socket inode it
 *            unlinks on destruction.
 * @lifetime The referenced `GatewaySession` (and the configuration it holds) must outlive the
 *           service, and the `GatewayGrpcServer` must be destroyed before both; a watch identifier
 *           is valid only while its association is current and is cleared when the watch ends.
 * @thread_safety gRPC worker threads may enter any RPC concurrently; session-mutating dispatch is
 *                serialized by the private dispatch mutex, watch state combines atomics with the
 *                watch mutex, and `poll`, `request_shutdown`, and `disconnect` are safe to call
 *                from the owning application thread.
 * @failure Admission failures return bounded gRPC statuses (`CANCELLED`, `DEADLINE_EXCEEDED`,
 *          `RESOURCE_EXHAUSTED`, `FAILED_PRECONDITION`, `ALREADY_EXISTS`, `UNAVAILABLE`) and do
 *          not mutate unrelated session state; `GatewayGrpcServer::start` returns `nullptr` for an
 *          unsupported message bound, an unprotected parent directory, or a failed bind.
 * @par Traceability
 * Realizes accepted `T031-SR-012` (exclusive generation-bound lease delegation over the local
 * transport) and `T031-SR-013` (disconnect/idle cleanup of validation-owned resources). See
 * docs/engineering/xcom/t031/{requirements,detailed-design,unit-specifications}.md and
 * docs/engineering/xcom/t039/transport-repair.md.
 */

#ifndef XVERSE_XCOM_TOOL_GATEWAY_GRPC_HPP_
#define XVERSE_XCOM_TOOL_GATEWAY_GRPC_HPP_

#include "xverse/xcom/tool_gateway.hpp"
#include "xverse/xcom/v1/gateway_liveness.grpc.pb.h"
#include "xverse/xcom/v1/tool_gateway.grpc.pb.h"

#include <grpcpp/grpcpp.h>

#include <cstddef>
#include <atomic>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

namespace xverse::xcom {

// The admitted gRPC binary uses the POSIX mutex layout. Its optional ASan
// leak-checker field changes the ABI; compiler sanitizer instrumentation stays on.
static_assert(sizeof(gpr_mu) == sizeof(pthread_mutex_t),
              "gRPC consumer mutex ABI must match the admitted POSIX binary");

/**
 * @brief The real generated `ToolGateway` and local `GatewayLiveness` services for one
 *        permit-bound gateway session.
 * @ownership Borrows the caller-owned `GatewaySession`, copies the bounded `GatewayConfig` by
 *            value, and owns the watch association (identifier, active/failed flags) and the
 *            private dispatch mutex; it owns no session, provider, or transport state.
 * @lifetime The referenced session must outlive this service, and the owning application must
 *           keep the session and its dependencies alive until shutdown. The caller's
 *           configuration is copied by value, so it need not outlive the construction call.
 * @thread_safety gRPC worker threads may call the RPCs concurrently; stateful dispatch is
 *                serialized by the dispatch mutex and watch state is guarded by atomics plus the
 *                watch mutex. `poll`, `request_shutdown`, and `disconnect` are callable from the
 *                owning thread.
 * @failure RPCs return bounded gRPC statuses for rejection and never mutate unrelated session
 *          state on an admission or watch failure.
 */
class GatewayGrpcService final : public v1::ToolGateway::Service,
                                 public v1::GatewayLiveness::Service {
 public:
  /// @brief Bind the service to one session and its validated configuration without I/O.
  /// @param session Borrowed gateway session that must outlive this service.
  /// @param config Validated configuration held by value for message-bound enforcement.
  GatewayGrpcService(GatewaySession &session, const GatewayConfig &config) noexcept;

  /// @brief Report the accepted protocol version without requiring a watch association.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted version query request.
  /// @param response Populated from the bound session.
  /// @return `OK`, or an admission status when cancelled, past deadline, or over the bound.
  grpc::Status QueryVersion(grpc::ServerContext *context, const v1::QueryVersionRequest *request,
                            v1::QueryVersionResponse *response) override;
  /// @brief Open one bounded observation stream on the bound session.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted observation-open request.
  /// @param response Populated from the bound session.
  /// @return `OK`, or the admission/watch status that rejected the call.
  grpc::Status OpenObservation(grpc::ServerContext *context,
                               const v1::OpenObservationRequest *request,
                               v1::OpenObservationResponse *response) override;
  /// @brief Read bounded observation records and stream them to the caller.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted observation-read request bounding the granted record count.
  /// @param writer Server writer that receives each bounded observation record.
  /// @return `OK`, `DEADLINE_EXCEEDED`/`FAILED_PRECONDITION` for the session outcome, `CANCELLED`
  ///         when the reader disconnects, or the admission/watch status that rejected the call.
  grpc::Status ReadObservations(grpc::ServerContext *context,
                                const v1::ReadObservationsRequest *request,
                                grpc::ServerWriter<v1::ObservationRecord> *writer) override;
  /// @brief Close one observation stream previously opened on the bound session.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted observation-close request.
  /// @param response Populated from the bound session.
  /// @return `OK`, or the admission/watch status that rejected the call.
  grpc::Status CloseObservation(grpc::ServerContext *context,
                                const v1::CloseObservationRequest *request,
                                v1::CloseObservationResponse *response) override;
  /// @brief Arm the bound session after negotiating an accepted protocol version.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted arm request; its protocol version must be supported.
  /// @param response Populated from the bound session.
  /// @return `OK`, `FAILED_PRECONDITION` for an unsupported protocol, or the admission/watch
  ///         status that rejected the call.
  grpc::Status ArmSession(grpc::ServerContext *context, const v1::ArmSessionRequest *request,
                          v1::ArmSessionResponse *response) override;
  /// @brief Revoke the bound session and release its validation-owned resources.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted revoke request.
  /// @param response Populated from the bound session.
  /// @return `OK`, or the admission/watch status that rejected the call.
  grpc::Status RevokeSession(grpc::ServerContext *context,
                             const v1::RevokeSessionRequest *request,
                             v1::RevokeSessionResponse *response) override;
  /// @brief Submit one bounded stimulation through the accepted action boundary.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted stimulation request whose echoed identifiers must fit the bound.
  /// @param response Populated from the bound session, including the transport diagnostic.
  /// @return `OK`, `RESOURCE_EXHAUSTED` when the reserved response bound would be exceeded,
  ///         `CANCELLED` when the transport ended before dispatch, or the admission/watch status.
  grpc::Status SubmitStimulation(grpc::ServerContext *context,
                                  const v1::SubmitStimulationRequest *request,
                                  v1::SubmitStimulationResponse *response) override;
  /// @brief Acquire the single owned generation-bound lease for the bound session.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted lease-acquire request.
  /// @param response Populated with the fresh, never-reused allocation identity on success.
  /// @return The call returns `OK` whenever it is admitted and watched; the acquisition outcome
  ///         is carried by `AcquireLeaseResponse.state`, including `LEASE_CONFLICT` when a lease
  ///         is already held or the allocation space is exhausted. The admission or watch status
  ///         is returned instead when the call is rejected before dispatch.
  grpc::Status AcquireLease(grpc::ServerContext *context,
                            const v1::AcquireLeaseRequest *request,
                            v1::AcquireLeaseResponse *response) override;
  /// @brief Release the currently owned lease only for its exact public identity.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted lease-release request carrying the caller's identity.
  /// @param response Populated with the release outcome; a stale identity is rejected without
  ///        releasing the current allocation.
  /// @return `OK`, or the admission/watch status that rejected the call.
  grpc::Status ReleaseLease(grpc::ServerContext *context,
                            const v1::ReleaseLeaseRequest *request,
                            v1::ReleaseLeaseResponse *response) override;
  /// @brief Reconcile a committed outcome without requiring a watch association.
  /// @param context Server context carrying the request deadline and cancellation state.
  /// @param request Accepted session-query request.
  /// @param response Populated from the bound session, including any durable lease identity.
  /// @return `OK`, or an admission status when cancelled, past deadline, or over the bound.
  grpc::Status QuerySession(grpc::ServerContext *context, const v1::QuerySessionRequest *request,
                            v1::QuerySessionResponse *response) override;
  /// @brief Keep one local session watch open until the client disconnects or cancels it.
  /// @param context Server context whose cancellation ends the watch.
  /// @param request Accepted watch-session request.
  /// @param writer Server writer that delivers the single ready frame carrying the watch id.
  /// @return `CANCELLED` once the watch closes: the call holds after the ready frame is written
  ///         until the client cancels or the watch is marked failed, and it also returns
  ///         `CANCELLED` when that ready frame cannot be delivered. `ALREADY_EXISTS`,
  ///         `FAILED_PRECONDITION`, or `UNAVAILABLE` reject a second, terminal, or unidentifiable
  ///         watch, and the admission statuses reject a cancelled, past-deadline, or over-bound
  ///         call. Closing the watch makes the session terminal.
  grpc::Status WatchSession(grpc::ServerContext *context, const v1::WatchSessionRequest *request,
                            grpc::ServerWriter<v1::WatchSessionReady> *writer) override;
  /// @brief Advance the bound session's time authority from the owner poller thread.
  void poll() noexcept;
  /// @brief Mark the watch failed and notify the session of a disconnect.
  void disconnect() noexcept;
  /// @brief Stop accepting stateful calls and terminate a live watch before server shutdown.
  void request_shutdown() noexcept;
  /// @brief Maximum request and response size configured for this service.
  /// @return The validated per-frame message bound in bytes.
  [[nodiscard]] std::size_t message_bound() const noexcept;

 private:
  grpc::Status check(grpc::ServerContext *, std::size_t request_bytes) const;
  grpc::Status require_watch(grpc::ServerContext *) const;
  GatewaySession &session_;
  GatewayConfig config_;
  std::atomic<bool> watch_active_{false};
  std::atomic<bool> watch_failed_{false};
  mutable std::mutex watch_mutex_{};
  std::string watch_id_{};
  std::mutex dispatch_mutex_{};
};

/**
 * @brief Owns a protected local Unix-socket gRPC listener; no TCP address is accepted.
 * @ownership Owns the local listener, its poller thread, the retained socket path, and the socket
 *            inode that is unlinked on destruction; it borrows the bound service.
 * @lifetime The referenced service must outlive this server; destruction stops the listener and
 *           joins the poller before the owning application tears down the session.
 * @thread_safety Construction returns a fully started server; `wait` blocks the calling thread
 *                until shutdown, while the poller runs independently. The type is non-copyable
 *                and non-assignable.
 * @failure `start` returns `nullptr` when the message bound is unsupported or inconsistent, the
 *          socket parent is unprotected, the bind fails, or the socket cannot be restricted.
 */
class GatewayGrpcServer final {
 public:
  /// @brief Start a protected local listener bound to the supplied service.
  /// @param socket_path Absolute Unix-socket path whose parent is a private, owned directory.
  /// @param service Borrowed service whose message bound and lifecycle must agree with this call.
  /// @param max_message_bytes Per-frame bound; must be within the local transport floor.
  /// @return A started server, or `nullptr` when validation or the bind fails.
  static std::unique_ptr<GatewayGrpcServer> start(const std::string &socket_path,
                                                   GatewayGrpcService &service,
                                                   std::size_t max_message_bytes);
  ~GatewayGrpcServer();
  GatewayGrpcServer(const GatewayGrpcServer &) = delete;
  GatewayGrpcServer &operator=(const GatewayGrpcServer &) = delete;
  /// @brief Block until the underlying gRPC server is shut down.
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
