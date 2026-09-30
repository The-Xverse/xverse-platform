/**
 * @file tool_gateway.hpp
 * @brief T031 bounded, host-protected, local-IPC-only X-COM tool gateway session realizing the
 *        accepted T030 `xverse.xcom.v1.ToolGateway` message and method contract.
 * @details This public interface maps the ten accepted `ToolGateway` operations onto the accepted
 *          in-process T021-T029 boundaries over a bounded framing whose committed operation table
 *          is pinned 1:1 to the T030 descriptor method set. It binds only `AF_UNIX`/`socketpair`
 *          local IPC, exposes a bounded payload-free structured-log boundary, enforces explicit
 *          message/stream/queue/record/payload bounds, per-request deadlines against the accepted
 *          T025 time authority, and deterministic disconnect/expiry cleanup. It adds no admitted
 *          dependency, links no gRPC runtime, and defines no competing contract, RPC, or
 *          configuration language.
 * @ingroup xcom_gw
 * @par Traceability
 * Realizes accepted `XCOM-DU-020` (local-IPC-only gateway session), `XCOM-CMP-010` (local tool
 * gateway), `XCOM-XLC-002` (external-rpc contract), and boundaries `XCOM-XB-008`/`XCOM-XB-010`.
 */

#ifndef XVERSE_XCOM_TOOL_GATEWAY_HPP_
#define XVERSE_XCOM_TOOL_GATEWAY_HPP_

#include "xverse/xcom/observation.hpp"
#include "xverse/xcom/stimulation_actions.hpp"
#include "xverse/xcom/stimulation_guard.hpp"
#include "xverse/xcom/stimulation_journal.hpp"
#include "xverse/xcom/validation_session.hpp"
#include "xverse/xcom/v1/tool_gateway.pb.h"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

/// @brief Root namespace of the X-COM subsystem.
namespace xverse::xcom {

/// @brief Accepted protocol major realized by this gateway slice.
inline constexpr std::uint32_t kGatewaySupportedMajor = 1U;
/// @brief Negotiated protocol minor realized by this gateway slice.
inline constexpr std::uint32_t kGatewaySupportedMinor = 0U;

/**
 * @brief Caller-supplied bounds for one gateway configuration.
 * @ownership Copyable plain value; owns no resource.
 * @lifetime Value lifetime.
 * @thread_safety Safe to copy and read concurrently.
 * @failure `GatewayConfig::create` rejects a zero or over-maximum field fail-closed.
 */
struct GatewayConfigInput final {
  /// @brief Maximum accepted request/response frame size in bytes.
  std::size_t max_message_bytes{0U};
  /// @brief Maximum concurrent peer sessions.
  std::uint32_t max_concurrent_sessions{0U};
  /// @brief Maximum concurrent observation streams per session.
  std::uint32_t max_streams_per_session{0U};
  /// @brief Maximum pending/in-flight requests per session (bounded rate budget).
  std::uint32_t max_pending_requests{0U};
  /// @brief Maximum accepted per-request deadline in milliseconds.
  std::uint64_t max_deadline_millis{0U};
  /// @brief Session idle timeout in milliseconds.
  std::uint64_t session_idle_timeout_millis{0U};
  /// @brief Maximum observation records granted per read.
  std::uint32_t max_observation_records{0U};
  /// @brief Maximum accepted payload size in bytes.
  std::size_t max_payload_bytes{0U};
};

/**
 * @brief Validated, immutable gateway configuration.
 * @ownership Owns one bounded value; non-copyable configuration holder is copyable as a value.
 * @lifetime Value lifetime; must outlive every session that references it.
 * @thread_safety Concurrent const access is safe.
 * @failure An invalid input yields an empty optional from `create`; no unbounded default exists.
 */
class GatewayConfig final {
 public:
  /// @brief Validates a configuration and rejects any zero or over-maximum bound.
  /// @param input Candidate bounded configuration.
  /// @return A validated configuration, or no value when a bound is zero/over-maximum.
  [[nodiscard]] static std::optional<GatewayConfig> create(const GatewayConfigInput &input) noexcept;

  /// @return Maximum accepted frame size in bytes.
  [[nodiscard]] std::size_t max_message_bytes() const noexcept { return values_.max_message_bytes; }
  /// @return Maximum concurrent peer sessions.
  [[nodiscard]] std::uint32_t max_concurrent_sessions() const noexcept {
    return values_.max_concurrent_sessions;
  }
  /// @return Maximum concurrent observation streams per session.
  [[nodiscard]] std::uint32_t max_streams_per_session() const noexcept {
    return values_.max_streams_per_session;
  }
  /// @return Maximum pending/in-flight requests per session.
  [[nodiscard]] std::uint32_t max_pending_requests() const noexcept {
    return values_.max_pending_requests;
  }
  /// @return Maximum accepted per-request deadline in milliseconds.
  [[nodiscard]] std::uint64_t max_deadline_millis() const noexcept {
    return values_.max_deadline_millis;
  }
  /// @return Session idle timeout in milliseconds.
  [[nodiscard]] std::uint64_t session_idle_timeout_millis() const noexcept {
    return values_.session_idle_timeout_millis;
  }
  /// @return Maximum observation records granted per read.
  [[nodiscard]] std::uint32_t max_observation_records() const noexcept {
    return values_.max_observation_records;
  }
  /// @return Maximum accepted payload size in bytes.
  [[nodiscard]] std::size_t max_payload_bytes() const noexcept { return values_.max_payload_bytes; }

 private:
  GatewayConfig() noexcept = default;
  GatewayConfigInput values_{};
};

/**
 * @brief Stable, bounded gateway outcome vocabulary.
 * @ownership Value enumeration; owns no resource.
 * @lifetime Static-lifetime vocabulary.
 * @thread_safety Immutable; safe to read concurrently.
 * @failure Only `accepted` reports a successful operation; `evidence_incomplete` is never success.
 */
enum class GatewayOutcome : std::uint8_t {
  accepted,            ///< The operation completed successfully.
  rejected,            ///< Fail-closed decline with no emitted item.
  expired,             ///< The declared deadline or validity elapsed; no emitted item.
  failed,              ///< Deterministic failure; no emitted item.
  evidence_incomplete, ///< Durable state is unknown; never reported as success.
};

/// @brief Stable, bounded gateway phase vocabulary.
enum class GatewayPhase : std::uint8_t {
  negotiate,   ///< Protocol negotiation.
  session,     ///< Validation-session lifecycle.
  observation, ///< Observation stream.
  stimulation, ///< Stimulation submission.
  lease,       ///< Service-emulation lease.
  query,       ///< Bounded counter query.
  transport,   ///< Local-IPC framing/transport.
};

/// @brief Returns the stable name of a gateway outcome.
/// @param outcome Gateway outcome.
/// @return Static-lifetime name.
[[nodiscard]] std::string_view to_string(GatewayOutcome outcome) noexcept;

/// @brief Returns the stable name of a gateway phase.
/// @param phase Gateway phase.
/// @return Static-lifetime name.
[[nodiscard]] std::string_view to_string(GatewayPhase phase) noexcept;

/**
 * @brief Bounded, payload-free structured log record.
 * @ownership Owns no bytes; `code`/`identity` are call-scoped views.
 * @lifetime Views must remain valid for the duration of the sink call.
 * @thread_safety Value lifetime; safe to copy.
 * @failure Never carries a payload byte, permit content, or unrestricted content.
 */
struct GatewayLogRecord final {
  /// @brief Stable outcome.
  GatewayOutcome outcome{GatewayOutcome::accepted};
  /// @brief Stable phase.
  GatewayPhase phase{GatewayPhase::transport};
  /// @brief Stable non-empty code.
  std::string_view code;
  /// @brief Logical identity only.
  std::string_view identity;
  /// @brief Byte size, never the bytes.
  std::uint64_t size{0U};
  /// @brief Declared tick/millis, never an ambient timestamp.
  std::uint64_t timing{0U};
};

/**
 * @brief Host-owned safe log sink.
 * @ownership Host-owned; the gateway holds a non-owning reference that must outlive it.
 * @lifetime Must outlive every gateway session that references it.
 * @thread_safety May be invoked concurrently; an implementation must synchronize its own state.
 * @failure `record` is `noexcept` and never throws into the gateway.
 */
class GatewayLogSink {
 public:
  /// @brief Destructor.
  virtual ~GatewayLogSink() = default;

  /// @brief Records one bounded payload-free log record.
  /// @param record Bounded record carrying code/phase/identity/size/timing/outcome only.
  virtual void record(const GatewayLogRecord &record) noexcept = 0;
};

/**
 * @brief Bounded, framed local-IPC channel seam (in-process realization for tests).
 * @ownership Implementation-owned; the gateway never owns the channel.
 * @lifetime Must outlive every read/write that references it.
 * @thread_safety One declared user; the production endpoint serializes access.
 * @failure A read/write returns at most the destination/source length and never blocks unbounded.
 */
class LocalIpcChannel {
 public:
  /// @brief Destructor.
  virtual ~LocalIpcChannel() = default;

  /// @brief Reads at most `destination.size()` bytes.
  /// @param destination Bounded destination buffer.
  /// @return Number of bytes read.
  [[nodiscard]] virtual std::size_t read(std::span<std::byte> destination) noexcept = 0;

  /// @brief Writes at most `source.size()` bytes.
  /// @param source Bounded source buffer.
  /// @return Number of bytes written.
 [[nodiscard]] virtual std::size_t write(std::span<const std::byte> source) noexcept = 0;
};

/**
 * @brief Host-protected `AF_UNIX` local-IPC endpoint; the only bind path.
 * @ownership Owns exactly one socket descriptor and its bound path.
 * @lifetime The descriptor lives until destruction, which closes it and unlinks the bound path.
 * @thread_safety `accept_one`/`family`/`permission_restricted` are non-mutating reads; one caller.
 * @failure `create` returns no value for a non-local/empty path or a bind/permission failure; no
 *          non-local address family, name-resolution, or transport-security facility is ever
 *          referenced.
 */
class LocalIpcEndpoint final {
 public:
  /// @brief Binds one host-protected `AF_UNIX` stream socket at `local_path`.
  /// @param config Validated bounded gateway configuration.
  /// @param local_path Non-empty local filesystem socket path under a restricted directory.
  /// @return The bound endpoint, or no value when the path is empty/non-local or bind fails.
  [[nodiscard]] static std::optional<LocalIpcEndpoint>
  create(const GatewayConfig &config, std::string_view local_path) noexcept;

  /// @brief Destructor; closes the descriptor and unlinks the bound socket path.
  ~LocalIpcEndpoint();
  /// @brief Move construction transfers descriptor ownership.
  /// @param other Source endpoint whose descriptor ownership is transferred.
  LocalIpcEndpoint(LocalIpcEndpoint &&other) noexcept;
  /// @brief Move assignment releases any held descriptor and takes ownership.
  /// @param other Source endpoint whose descriptor ownership is transferred.
  /// @return This endpoint after taking ownership.
  LocalIpcEndpoint &operator=(LocalIpcEndpoint &&other) noexcept;
  /// @brief Copy construction is deleted; the endpoint owns a unique descriptor.
  LocalIpcEndpoint(const LocalIpcEndpoint &) = delete;
  /// @brief Copy assignment is deleted; the endpoint owns a unique descriptor.
  LocalIpcEndpoint &operator=(const LocalIpcEndpoint &) = delete;

  /// @brief Reports whether the bound address family is `AF_UNIX`.
  /// @return `true` only when `getsockname` reports `AF_UNIX`.
  [[nodiscard]] bool is_local_unix() const noexcept;
  /// @brief Returns the bound address family.
  /// @return The `getsockname` address family, or `-1` when the descriptor is invalid.
  [[nodiscard]] int family() const noexcept { return family_; }
  /// @brief Returns the bound socket file mode permission bits.
  /// @return The mode permission bits, or `0` when `stat` fails.
  [[nodiscard]] std::uint32_t permission_bits() const noexcept { return permissions_; }
  /// @brief Returns the bound local path.
  /// @return The bound local path.
  [[nodiscard]] std::string_view path() const noexcept { return path_; }
  /// @brief Returns the raw listening descriptor (for the bounded test connect step only).
  /// @return The listening descriptor, or `-1` when invalid.
  [[nodiscard]] int listen_fd() const noexcept { return fd_; }
  /// @brief Non-blocking, bounded accept of at most one peer.
  /// @return The accepted descriptor, or `-1` when no peer is ready.
  [[nodiscard]] int accept_one() const noexcept;

 private:
  LocalIpcEndpoint(int fd, int family, std::uint32_t permissions, std::string path) noexcept;
  int fd_{-1};
  int family_{-1};
  std::uint32_t permissions_{0U};
  std::string path_;
};

/**
 * @brief Non-owning bundle of the accepted in-process boundaries the gateway delegates to.
 * @ownership Non-owning; every referenced component must outlive every session that uses it.
 * @lifetime Must outlive the gateway session.
 * @thread_safety Components synchronize their own state; the bundle is read-only after construction.
 * @failure A null component fails the dependent operation closed with no emitted item.
 */
struct GatewayDependencies final {
  /// @brief Accepted T025 validation permit/session manager.
  validation::SessionManager *sessions{nullptr};
  /// @brief Accepted T025 time authority (may equal `sessions->time_authority()`).
  validation::TimeAuthority *time_authority{nullptr};
  /// @brief Accepted T026 durable intent/outcome journal.
  validation::StimulationJournal *journal{nullptr};
  /// @brief Accepted T027 fail-closed pre-emission guard (owned by the action path when present).
  validation::StimulationGuard *guard{nullptr};
  /// @brief Accepted T028 guarded action path.
  validation::StimulationActionPath *actions{nullptr};
  /// @brief Accepted T028 exclusive generation-bound service-emulation lease registry.
  validation::ServiceEmulationRegistry *leases{nullptr};
  /// @brief Accepted T021-T024 bounded observation hub.
  ObservationHub *observations{nullptr};
  /// @brief Optional safe log sink; null disables logging.
  GatewayLogSink *log{nullptr};
};

/**
 * @brief Resolved accepted in-process identity bound to one gateway session.
 * @details The wire contract carries logical identities only; this bundle carries the exact
 *          resolved accepted T025 permit/context/controller that the gateway maps the wire
 *          request onto. No wire field bypasses it.
 * @ownership Owns bounded value copies of the permit and context.
 * @lifetime Value lifetime; the session copies the fields it needs.
 * @thread_safety Safe to copy and read concurrently.
 * @failure A missing permit, or a wire identity that differs from the bound logical identity,
 *          fails the dependent operation closed with no emitted item.
 */
struct GatewaySessionBinding final {
  /// @brief Logical permit identity expected on the wire.
  std::string permit_id;
  /// @brief Logical session identity expected on the wire.
  std::string session_id;
  /// @brief Logical plan digest expected on the wire.
  std::string plan_digest;
  /// @brief Logical graph digest expected on the wire.
  std::string graph_digest;
  /// @brief Exact accepted T025 permit.
  validation::Permit permit{};
  /// @brief Whether `permit` is a built, usable permit.
  bool has_permit{false};
  /// @brief Issuing, registered controller identity.
  validation::ControllerId controller{};
  /// @brief Asserted runtime envelope compared field-by-field to `permit`.
  validation::SessionContext context{};
  /// @brief Declared arrival clock domain for deadlines.
  validation::ClockDomainId arrival_domain{validation::kInvalidClockDomain};
  /// @brief Logical wire name of the bound arrival clock domain; a request naming another domain is
  ///        rejected as unmapped rather than silently rewritten.
  std::string arrival_domain_name;
  /// @brief Declared arrival tick used as the initial session activity anchor.
  validation::Timestamp arrival_tick{0};
  /// @brief Logical contract identity expected on the wire for a stimulation submission; a request
  ///        naming another contract is rejected rather than silently dropped.
  std::string contract_id;
  /// @brief Declared service-owner identity validated only for service actions.
  validation::ServiceOwner service_owner{};
  /// @brief Logical blueprint/contract tag used for log identities.
  std::string blueprint_id;
};

/// @brief Bounded request-frame decode outcome.
enum class GatewayFrameStatus : std::uint8_t {
  ok,             ///< A bounded, well-formed, known-method frame.
  over_bound,     ///< `total_length` exceeds the configured maximum.
  unknown_method, ///< `method_name` is absent from the committed operation table.
  malformed,      ///< A truncated or structurally invalid frame.
};

/// @brief Bounded view over one decoded request frame.
/// @ownership Borrows the caller's buffer.
/// @lifetime Valid while the decoded buffer lives.
/// @thread_safety Read-only view.
/// @failure Never owns or copies a payload byte.
struct GatewayFrameView final {
  /// @brief Decoded method name.
  std::string_view method;
  /// @brief Decoded serialized request message bytes.
  std::span<const std::byte> payload;
};

/// @brief Decodes one bounded length-prefixed, method-name-addressed request frame.
/// @param config Validated bounded configuration.
/// @param frame Candidate frame bytes.
/// @param out Receives the decoded view only on `GatewayFrameStatus::ok`.
/// @return The bounded decode status; an over-bound or unknown-method frame is rejected without
///         allocation or dispatch.
[[nodiscard]] GatewayFrameStatus
gateway_decode_request_frame(const GatewayConfig &config, std::span<const std::byte> frame,
                             GatewayFrameView &out) noexcept;

/**
 * @brief Immutable bounded snapshot of one gateway session's own bookkeeping.
 * @ownership Value copy; owns no shared state.
 * @lifetime Value lifetime.
 * @thread_safety Safe to copy and read concurrently.
 * @failure Counters are finite and include an explicit evidence-incomplete count.
 */
struct GatewaySessionSnapshot final {
  /// @brief Terminal negotiation outcome.
  GatewayOutcome negotiation{GatewayOutcome::rejected};
  /// @brief Whether a supported protocol major was negotiated.
  bool negotiated{false};
  /// @brief Whether the session is terminal.
  bool terminal{false};
  /// @brief Whether the validation session is armed.
  bool armed{false};
  /// @brief Active observation streams.
  std::uint32_t active_streams{0U};
  /// @brief Pending requests awaiting completion.
  std::uint32_t pending_requests{0U};
  /// @brief Requests received.
  std::uint64_t requests_received{0U};
  /// @brief Requests authorized.
  std::uint64_t requests_authorized{0U};
  /// @brief Requests rejected.
  std::uint64_t requests_rejected{0U};
  /// @brief Items emitted on the normal route.
  std::uint64_t emitted{0U};
  /// @brief Requests ending evidence-incomplete.
  std::uint64_t evidence_incomplete{0U};
  /// @brief Flow-control rejections.
  std::uint64_t flow_rejections{0U};
  /// @brief Remaining bounded in-flight/rate budget.
  std::uint32_t flow_tokens{0U};
  /// @brief Explicit outcome of the most recently ended pending request.
  GatewayOutcome last_pending_outcome{GatewayOutcome::accepted};
  /// @brief Whether a service-emulation lease is held.
  bool lease_held{false};

  /// @brief Value equality over every observed field.
  friend bool operator==(const GatewaySessionSnapshot &, const GatewaySessionSnapshot &) noexcept =
      default;
};

/**
 * @brief One accepted peer session realizing all ten accepted `ToolGateway` operations.
 * @ownership Owns its bounded per-session state; holds non-owning references to the accepted
 *            in-process boundaries and the log sink, which must outlive it.
 * @lifetime The session retains only bounded state; destroy it before the referenced components.
 * @thread_safety Internally synchronized by one per-session mutex plus a bounded flow-control
 *                budget; no ambient wall-clock time, randomness, or environment is consulted.
 * @failure Every unwelcome, over-bound, expired, unauthorized, or unsupported-version operation
 *          returns a stable outcome without unrelated mutation and without emitting an item.
 */
class GatewaySession final {
 public:
  /// @brief Constructs a bounded, non-negotiated, open session.
  /// @param config Validated bounded configuration; copied.
  /// @param dependencies Non-owning accepted boundary bundle; must outlive the session.
  /// @param binding Resolved accepted in-process identity and arrival tick.
  GatewaySession(const GatewayConfig &config, const GatewayDependencies &dependencies,
                 GatewaySessionBinding binding = {}) noexcept;

  /// @brief Copy construction is deleted; the session owns a mutex.
  GatewaySession(const GatewaySession &) = delete;
  /// @brief Copy assignment is deleted; the session owns a mutex.
  GatewaySession &operator=(const GatewaySession &) = delete;
  /// @brief Move construction is deleted; the session owns a mutex.
  GatewaySession(GatewaySession &&) = delete;
  /// @brief Move assignment is deleted; the session owns a mutex.
  GatewaySession &operator=(GatewaySession &&) = delete;

  /// @brief Applies the production fail-closed protocol compatibility predicate.
  /// @param peer Declared peer protocol version.
  /// @return `accepted` for the supported major (any minor, additively) or `rejected` otherwise.
  [[nodiscard]] GatewayOutcome negotiate(const v1::ProtocolVersion &peer) noexcept;

  /// @brief Returns the negotiated protocol and bounded capabilities.
  /// @param request Empty version request (retained for contract fidelity).
  /// @return Negotiation response carrying the supported protocol, declared bounds, and diagnostic.
  [[nodiscard]] v1::QueryVersionResponse QueryVersion(const v1::QueryVersionRequest &request) noexcept;

  /// @brief Opens one bounded observation stream.
  /// @param request Bounded open request.
  /// @return The bounded observation stream handle, or a declining diagnostic.
  [[nodiscard]] v1::OpenObservationResponse
  OpenObservation(const v1::OpenObservationRequest &request) noexcept;

  /// @brief Reads at most the granted bounded number of metadata-only records.
  /// @param request Bounded read request.
  /// @param out Destination span of at most `request.max_records()` records.
  /// @return The number of records written, never above the granted, configured, or span bound.
  [[nodiscard]] std::size_t ReadObservations(const v1::ReadObservationsRequest &request,
                                             std::span<v1::ObservationRecord> out) noexcept;

  /// @brief Closes one bounded observation stream and returns delivered/dropped counters.
  /// @param request Bounded close request.
  /// @return The bounded delivered/dropped counters, or a declining diagnostic.
  [[nodiscard]] v1::CloseObservationResponse
  CloseObservation(const v1::CloseObservationRequest &request) noexcept;

  /// @brief Arms one validation session under the exact accepted permit.
  /// @param request Bounded arm request carrying the exact permit.
  /// @return The bounded arming result, or a declining diagnostic.
  [[nodiscard]] v1::ArmSessionResponse ArmSession(const v1::ArmSessionRequest &request) noexcept;

  /// @brief Revokes one validation session; revocation is terminal.
  /// @param request Bounded revoke request.
  /// @return The bounded terminal revocation result, or a declining diagnostic.
  [[nodiscard]] v1::RevokeSessionResponse
  RevokeSession(const v1::RevokeSessionRequest &request) noexcept;

  /// @brief Submits one bounded stimulation action through the accepted action path.
  /// @param request Bounded stimulation request.
  /// @return The bounded emission/outcome result, or a declining diagnostic.
  [[nodiscard]] v1::SubmitStimulationResponse
  SubmitStimulation(const v1::SubmitStimulationRequest &request) noexcept;

  /// @brief Acquires one exclusive generation-bound service-emulation lease.
  /// @param request Bounded lease-acquire request.
  /// @return The bounded lease result, or a declining diagnostic.
  [[nodiscard]] v1::AcquireLeaseResponse
  AcquireLease(const v1::AcquireLeaseRequest &request) noexcept;

  /// @brief Releases one held service-emulation lease.
  /// @param request Bounded lease-release request.
  /// @return The bounded lease-release result, or a declining diagnostic.
  [[nodiscard]] v1::ReleaseLeaseResponse
  ReleaseLease(const v1::ReleaseLeaseRequest &request) noexcept;

  /// @brief Queries bounded session state and finite counters.
  /// @param request Bounded query request.
  /// @return The bounded session state and counters, or a declining diagnostic.
  [[nodiscard]] v1::QuerySessionResponse
  QuerySession(const v1::QuerySessionRequest &request) noexcept;

  /// @brief Deterministic disconnect cleanup: close streams, drain/revoke/release/quarantine.
  void on_disconnect() noexcept;

  /// @brief Deterministic idle-timeout cleanup evaluated against a declared tick.
  /// @param now Caller-supplied declared tick.
  void on_idle_tick(validation::Timestamp now) noexcept;

  /// @brief Whether the bounded in-flight/rate budget admitted the most recent request.
  /// @return `true` when the most recent request was admitted within the bounded budget.
  [[nodiscard]] bool flow_tokens_available() const noexcept;

  /// @brief Returns an immutable bounded snapshot of the session's own bookkeeping.
  /// @return The bounded snapshot.
  [[nodiscard]] GatewaySessionSnapshot snapshot() const noexcept;

 private:
  /// @brief Outcome of the shared per-request admission gate.
  struct Admission final {
    /// @brief Whether the request may proceed.
    bool proceed{false};
    /// @brief Declared declining outcome when `proceed` is false.
    GatewayOutcome outcome{GatewayOutcome::rejected};
  };

  /// @brief Resolves the declared dispatch tick from the accepted time authority or arrival tick.
  [[nodiscard]] validation::Timestamp resolve_dispatch_tick() const noexcept;

  /// @brief Applies version, terminal, deadline, and flow-control admission.
  /// @param deadline_millis Declared request deadline in milliseconds.
  /// @return The admission decision; a declining decision has already counted the request.
  [[nodiscard]] Admission admit(std::uint64_t deadline_millis) noexcept;

  /// @brief Records one bounded payload-free log record when a sink is present.
  void log(GatewayOutcome outcome, GatewayPhase phase, std::string_view code,
           std::string_view identity, std::uint64_t size, std::uint64_t timing) noexcept;

  /// @brief Performs the shared disconnect/expiry cleanup under the session mutex.
  void cleanup_locked(GatewayOutcome pending_outcome, GatewayPhase phase) noexcept;

  /// @brief Validates the wire session identity against the bound logical identity.
  [[nodiscard]] bool session_matches(const std::string &session_id) const noexcept;

  /// @brief One accepted bounded observation stream and its independent exact handle.
  struct StreamOwnership final {
    /// @brief Stable logical stream identity granted to the peer.
    std::string id;
    /// @brief Exact detached-able hub handle for this stream only.
    std::unique_ptr<ObservationTapHandle> handle;
  };

  /// @brief Finds the accepted stream with the exact logical identity; call only holding the mutex.
  /// @param stream_id Declared stream identity.
  /// @return Pointer to the retained stream ownership, or `nullptr` when absent.
  [[nodiscard]] StreamOwnership *find_stream_locked(std::string_view stream_id) noexcept;
  /// @brief Detaches and forgets every accepted stream; call only holding the mutex.
  void detach_all_streams_locked() noexcept;
  /// @brief Reports the bounded scheduled queue depth from the accepted action path.
  [[nodiscard]] std::uint32_t action_pending_locked() const noexcept;
  /// @brief Executes every due scheduled action and applies the bounded terminal outcome.
  /// @param now Caller-supplied declared tick in the bound arrival domain.
  void drain_scheduled_locked(validation::Timestamp now) noexcept;

  GatewayConfig config_;
  GatewayDependencies dependencies_{};
  GatewaySessionBinding binding_{};
  mutable std::mutex mutex_{};
  bool open_{true};
  bool terminal_{false};
  bool negotiated_{false};
  bool armed_{false};
  GatewayOutcome negotiation_{GatewayOutcome::rejected};
  v1::ProtocolVersion peer_version_{};
  validation::SessionHandle handle_{};
  bool has_handle_{false};
  std::vector<StreamOwnership> streams_{};
  std::uint32_t stream_counter_{0U};
  std::uint32_t active_streams_{0U};
  validation::Timestamp last_activity_tick_{0};
  std::uint32_t pending_requests_{0U};
  GatewayOutcome last_pending_outcome_{GatewayOutcome::accepted};
  std::uint32_t flow_tokens_{0U};
  validation::EndpointGeneration lease_key_{};
  std::string lease_id_;
  std::uint64_t lease_request_id_{0U};
  bool lease_held_{false};
  std::uint64_t requests_received_{0U};
  std::uint64_t requests_authorized_{0U};
  std::uint64_t requests_rejected_{0U};
  std::uint64_t emitted_{0U};
  std::uint64_t evidence_incomplete_{0U};
  std::uint64_t flow_rejections_{0U};
};

/**
 * @brief Returns the committed gateway operation-name table.
 * @details Pinned 1:1 and in order to the accepted T030 `xverse.xcom.v1.ToolGateway` descriptor
 *          method set.
 * @return Static-lifetime span of the ten accepted method names.
 */
[[nodiscard]] std::span<const std::string_view> gateway_operation_names() noexcept;

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_TOOL_GATEWAY_HPP_
