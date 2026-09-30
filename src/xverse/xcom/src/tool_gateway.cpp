/**
 * @file tool_gateway.cpp
 * @brief T031 bounded, host-protected, local-IPC-only tool gateway session implementation.
 * @details Realizes the accepted `xverse.xcom.v1.ToolGateway` message and method contract over a
 *          bounded `AF_UNIX` local-IPC floor, delegates the ten operations onto the accepted
 *          T021-T029 in-process boundaries, and enforces explicit bounds, per-request deadlines,
 *          bounded flow control, deterministic disconnect/expiry cleanup, and payload-free logs.
 * @ingroup xcom_gw
 */

#include "xverse/xcom/tool_gateway.hpp"

#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

#include <fcntl.h>

#include <algorithm>
#include <array>
#include <cerrno>
#include <charconv>
#include <cstdio>
#include <cstring>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace xverse::xcom {
namespace {

namespace val = validation;

/// @brief Maximum accepted frame size, 16 MiB.
constexpr std::size_t kGatewayMaxMessageBytes = 16U * 1024U * 1024U;
/// @brief Maximum accepted concurrent sessions.
constexpr std::uint32_t kGatewayMaxSessions = 1024U;
/// @brief Maximum accepted concurrent streams per session.
constexpr std::uint32_t kGatewayMaxStreams = 1024U;
/// @brief Maximum accepted pending/in-flight requests.
constexpr std::uint32_t kGatewayMaxPendingRequests = 65536U;
/// @brief Maximum accepted deadline, one day in milliseconds.
constexpr std::uint64_t kGatewayMaxDeadlineMillis = 86U * 1000U * 1000U;
/// @brief Maximum accepted idle timeout, one day in milliseconds.
constexpr std::uint64_t kGatewayMaxIdleMillis = 86U * 1000U * 1000U;
/// @brief Declared default tap identity when the request omits one.
constexpr std::string_view kDefaultTapId = "gateway.tap";
/// @brief Declared default target/interface tags used only when the binding omits them.
constexpr std::string_view kDefaultInterface = "gateway.iface";

}  // namespace

std::string_view to_string(GatewayOutcome outcome) noexcept {
  switch (outcome) {
  case GatewayOutcome::accepted:
    return "accepted";
  case GatewayOutcome::rejected:
    return "rejected";
  case GatewayOutcome::expired:
    return "expired";
  case GatewayOutcome::failed:
    return "failed";
  case GatewayOutcome::evidence_incomplete:
    return "evidence_incomplete";
  }
  return {};
}

std::string_view to_string(GatewayPhase phase) noexcept {
  switch (phase) {
  case GatewayPhase::negotiate:
    return "negotiate";
  case GatewayPhase::session:
    return "session";
  case GatewayPhase::observation:
    return "observation";
  case GatewayPhase::stimulation:
    return "stimulation";
  case GatewayPhase::lease:
    return "lease";
  case GatewayPhase::query:
    return "query";
  case GatewayPhase::transport:
    return "transport";
  }
  return {};
}

std::optional<GatewayConfig> GatewayConfig::create(const GatewayConfigInput &input) noexcept {
  if (input.max_message_bytes == 0U || input.max_message_bytes > kGatewayMaxMessageBytes) {
    return std::nullopt;
  }
  if (input.max_concurrent_sessions == 0U || input.max_concurrent_sessions > kGatewayMaxSessions) {
    return std::nullopt;
  }
  if (input.max_streams_per_session == 0U || input.max_streams_per_session > kGatewayMaxStreams) {
    return std::nullopt;
  }
  if (input.max_pending_requests == 0U || input.max_pending_requests > kGatewayMaxPendingRequests) {
    return std::nullopt;
  }
  if (input.max_deadline_millis == 0U || input.max_deadline_millis > kGatewayMaxDeadlineMillis) {
    return std::nullopt;
  }
  if (input.session_idle_timeout_millis == 0U ||
      input.session_idle_timeout_millis > kGatewayMaxIdleMillis) {
    return std::nullopt;
  }
  if (input.max_observation_records == 0U ||
      input.max_observation_records > kMaximumObservationRecordsPerTap) {
    return std::nullopt;
  }
  if (input.max_payload_bytes == 0U || input.max_payload_bytes > kMaximumObservedPayloadBytes) {
    return std::nullopt;
  }
  GatewayConfig config;
  config.values_ = input;
  return config;
}

namespace {

/// @brief Reads a big-endian 32-bit value.
std::uint32_t read_u32_be(const std::byte *bytes) noexcept {
  return (static_cast<std::uint32_t>(std::to_integer<unsigned>(bytes[0])) << 24U) |
         (static_cast<std::uint32_t>(std::to_integer<unsigned>(bytes[1])) << 16U) |
         (static_cast<std::uint32_t>(std::to_integer<unsigned>(bytes[2])) << 8U) |
         static_cast<std::uint32_t>(std::to_integer<unsigned>(bytes[3]));
}

/// @brief Reads a big-endian 16-bit value.
std::uint16_t read_u16_be(const std::byte *bytes) noexcept {
  return static_cast<std::uint16_t>(
      (static_cast<std::uint32_t>(std::to_integer<unsigned>(bytes[0])) << 8U) |
      static_cast<std::uint32_t>(std::to_integer<unsigned>(bytes[1])));
}

/// @brief Maps an accepted action status onto the bounded gateway outcome.
GatewayOutcome outcome_from_status(val::ActionStatus status) noexcept {
  switch (status) {
  case val::ActionStatus::Emitted:
    return GatewayOutcome::accepted;
  case val::ActionStatus::Queued:
    return GatewayOutcome::accepted;
  case val::ActionStatus::Expired:
    return GatewayOutcome::expired;
  case val::ActionStatus::EvidenceIncomplete:
  case val::ActionStatus::EmissionUnavailable:
    return GatewayOutcome::evidence_incomplete;
  case val::ActionStatus::Failed:
  case val::ActionStatus::JournalFailed:
    return GatewayOutcome::failed;
  default:
    return GatewayOutcome::rejected;
  }
}

/// @brief Maps the accepted lease status onto the bounded gateway outcome.
GatewayOutcome outcome_from_lease(val::LeaseStatus status) noexcept {
  switch (status) {
  case val::LeaseStatus::Ok:
    return GatewayOutcome::accepted;
  case val::LeaseStatus::Expired:
    return GatewayOutcome::expired;
  case val::LeaseStatus::Quarantined:
    return GatewayOutcome::evidence_incomplete;
  case val::LeaseStatus::RejectedConfiguration:
    return GatewayOutcome::failed;
  default:
    return GatewayOutcome::rejected;
  }
}

/// @brief Maps the accepted lifecycle state onto the wire session-state vocabulary.
v1::SessionState wire_state(bool terminal, bool armed, bool revoked, bool expired) noexcept {
  if (revoked) {
    return v1::SESSION_REVOKED;
  }
  if (expired) {
    return v1::SESSION_EXPIRED;
  }
  if (terminal) {
    return v1::SESSION_EVIDENCE_INCOMPLETE;
  }
  return armed ? v1::SESSION_ARMED : v1::SESSION_DECLARED;
}

/// @brief Maps the wire action kind onto the accepted stimulation action.
val::StimulationAction action_from_kind(v1::StimulationActionKind kind, bool &known) noexcept {
  known = true;
  switch (kind) {
  case v1::STIMULATION_ACTION_INJECT_SIGNAL:
    return val::StimulationAction::InjectSignal;
  case v1::STIMULATION_ACTION_INJECT_MESSAGE:
    return val::StimulationAction::InjectMessage;
  case v1::STIMULATION_ACTION_INVOKE_SERVICE:
    return val::StimulationAction::InvokeService;
  case v1::STIMULATION_ACTION_EMULATE_SERVICE:
    return val::StimulationAction::EmulateService;
  default:
    known = false;
    return val::StimulationAction::InjectSignal;
  }
}

/// @brief Reports whether a declared wire interaction is the canonical family of one action.
/// @param wire Declared wire interaction kind.
/// @param action Declared stimulation action.
/// @return `true` only for the one compatible family; every other value is rejected.
bool wire_interaction_matches(v1::InteractionKind wire, val::StimulationAction action) noexcept {
  switch (action) {
  case val::StimulationAction::InjectMessage:
    return wire == v1::INTERACTION_KIND_MESSAGE;
  case val::StimulationAction::InvokeService:
    return wire == v1::INTERACTION_KIND_REQUEST;
  case val::StimulationAction::EmulateService:
    return wire == v1::INTERACTION_KIND_RESPONSE;
  case val::StimulationAction::InjectSignal:
  default:
    return wire == v1::INTERACTION_KIND_SIGNAL;
  }
}

/// @brief Preserves the declared wire interaction as the accepted interaction family.
/// @param wire Declared wire interaction kind; call only after `wire_interaction_matches` holds.
/// @return The accepted interaction family for the declared wire value.
InteractionKind interaction_from_wire(v1::InteractionKind wire) noexcept {
  switch (wire) {
  case v1::INTERACTION_KIND_MESSAGE:
    return InteractionKind::message_event;
  case v1::INTERACTION_KIND_REQUEST:
    return InteractionKind::service_request;
  case v1::INTERACTION_KIND_RESPONSE:
    return InteractionKind::service_response;
  case v1::INTERACTION_KIND_SIGNAL:
  default:
    return InteractionKind::signal_state_update;
  }
}

/// @brief Reports whether a declared wire direction is the only valid outbound stimulation one.
/// @param wire Declared wire direction.
/// @return `true` only for `DIRECTION_OUTBOUND`; every other value is rejected.
bool wire_direction_valid(v1::Direction wire) noexcept {
  return wire == v1::DIRECTION_OUTBOUND;
}

/// @brief Reports whether a declared schedule mode is one of the two accepted explicit values.
/// @param mode Declared schedule mode.
/// @return `true` only for `SCHEDULE_IMMEDIATE` or `SCHEDULE_SCHEDULED`.
bool wire_schedule_mode_known(v1::ScheduleMode mode) noexcept {
  return mode == v1::SCHEDULE_IMMEDIATE || mode == v1::SCHEDULE_SCHEDULED;
}

/// @brief Adds a bounded delta to a declared tick without signed overflow.
/// @param base Declared base tick.
/// @param delta Non-negative declared delta.
/// @return The saturated sum.
val::Timestamp saturating_add(val::Timestamp base, val::Timestamp delta) noexcept {
  const val::Timestamp maximum = std::numeric_limits<val::Timestamp>::max();
  const val::Timestamp minimum = std::numeric_limits<val::Timestamp>::min();
  if (delta > 0 && base > maximum - delta) {
    return maximum;
  }
  if (delta < 0 && base < minimum - delta) {
    return minimum;
  }
  return base + delta;
}

/// @brief Maps the accepted action onto its canonical endpoint direction.
EndpointDirection direction_for(val::StimulationAction action) noexcept {
  switch (action) {
  case val::StimulationAction::InvokeService:
    return EndpointDirection::request;
  case val::StimulationAction::EmulateService:
    return EndpointDirection::respond;
  case val::StimulationAction::InjectMessage:
  case val::StimulationAction::InjectSignal:
  default:
    return EndpointDirection::produce;
  }
}

/// @brief Returns the declared schema key paired with one accepted action.
val::SchemaKey schema_for(val::StimulationAction action) noexcept {
  switch (action) {
  case val::StimulationAction::InjectMessage:
    return val::SchemaKey{val::Tag(std::string("msg.v1")), val::Tag(std::string("1"))};
  case val::StimulationAction::InvokeService:
    return val::SchemaKey{val::Tag(std::string("req.v1")), val::Tag(std::string("1"))};
  case val::StimulationAction::EmulateService:
    return val::SchemaKey{val::Tag(std::string("resp.v1")), val::Tag(std::string("1"))};
  case val::StimulationAction::InjectSignal:
  default:
    return val::SchemaKey{val::Tag(std::string("sig.v1")), val::Tag(std::string("1"))};
  }
}

/// @brief Parses a bounded decimal identity; a malformed value yields zero.
std::uint64_t parse_identity(std::string_view text) noexcept {
  if (text.empty()) {
    return 0U;
  }
  std::uint64_t value = 0U;
  const auto parsed = std::from_chars(text.data(), text.data() + text.size(), value);
  return parsed.ec == std::errc{} && parsed.ptr == text.data() + text.size() ? value : 0U;
}

/// @brief Reports whether a method name is the committed operation table.
bool is_known_method(std::string_view method) noexcept {
  for (const std::string_view known : gateway_operation_names()) {
    if (known == method) {
      return true;
    }
  }
  return false;
}

}  // namespace

// ------------------------------------------------------------------------------------------------
// LocalIpcEndpoint
// ------------------------------------------------------------------------------------------------

LocalIpcEndpoint::LocalIpcEndpoint(int fd, int family, std::uint32_t permissions,
                                   std::string path) noexcept
    : fd_(fd), family_(family), permissions_(permissions), path_(std::move(path)) {}

std::optional<LocalIpcEndpoint> LocalIpcEndpoint::create(const GatewayConfig &config,
                                                         std::string_view local_path) noexcept {
  if (local_path.empty()) {
    return std::nullopt;
  }
  struct sockaddr_un address {};
  if (local_path.size() >= sizeof(address.sun_path)) {
    return std::nullopt;
  }
  const int descriptor = ::socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
  if (descriptor < 0) {
    return std::nullopt;
  }
  address.sun_family = AF_UNIX;
  std::memcpy(address.sun_path, local_path.data(), local_path.size());
  const std::string owned_path(local_path);
  ::unlink(owned_path.c_str());
  if (::bind(descriptor, reinterpret_cast<struct sockaddr *>(&address), sizeof(address)) != 0) {
    ::close(descriptor);
    return std::nullopt;
  }
  if (::chmod(owned_path.c_str(), 0600) != 0) {
    ::unlink(owned_path.c_str());
    ::close(descriptor);
    return std::nullopt;
  }
  if (::listen(descriptor, static_cast<int>(config.max_concurrent_sessions())) != 0) {
    ::unlink(owned_path.c_str());
    ::close(descriptor);
    return std::nullopt;
  }
  struct sockaddr_un bound {};
  socklen_t bound_length = sizeof(bound);
  if (::getsockname(descriptor, reinterpret_cast<struct sockaddr *>(&bound), &bound_length) != 0 ||
      bound.sun_family != AF_UNIX) {
    ::unlink(owned_path.c_str());
    ::close(descriptor);
    return std::nullopt;
  }
  struct stat status {};
  if (::stat(owned_path.c_str(), &status) != 0) {
    ::unlink(owned_path.c_str());
    ::close(descriptor);
    return std::nullopt;
  }
  const std::uint32_t permissions =
      static_cast<std::uint32_t>(status.st_mode) & 0777U;
  if (permissions != 0600U) {
    ::unlink(owned_path.c_str());
    ::close(descriptor);
    return std::nullopt;
  }
  const int flags = ::fcntl(descriptor, F_GETFL, 0);
  if (flags < 0 || ::fcntl(descriptor, F_SETFL, flags | O_NONBLOCK) != 0) {
    ::unlink(owned_path.c_str());
    ::close(descriptor);
    return std::nullopt;
  }
  return LocalIpcEndpoint(descriptor, bound.sun_family, permissions, owned_path);
}

LocalIpcEndpoint::~LocalIpcEndpoint() {
  if (fd_ >= 0) {
    ::close(fd_);
    fd_ = -1;
  }
  if (!path_.empty()) {
    ::unlink(path_.c_str());
  }
}

LocalIpcEndpoint::LocalIpcEndpoint(LocalIpcEndpoint &&other) noexcept
    : fd_(other.fd_), family_(other.family_), permissions_(other.permissions_),
      path_(std::move(other.path_)) {
  other.fd_ = -1;
  other.family_ = -1;
  other.permissions_ = 0U;
  other.path_.clear();
}

LocalIpcEndpoint &LocalIpcEndpoint::operator=(LocalIpcEndpoint &&other) noexcept {
  if (this != &other) {
    if (fd_ >= 0) {
      ::close(fd_);
    }
    if (!path_.empty()) {
      ::unlink(path_.c_str());
    }
    fd_ = other.fd_;
    family_ = other.family_;
    permissions_ = other.permissions_;
    path_ = std::move(other.path_);
    other.fd_ = -1;
    other.family_ = -1;
    other.permissions_ = 0U;
    other.path_.clear();
  }
  return *this;
}

bool LocalIpcEndpoint::is_local_unix() const noexcept {
  if (fd_ < 0) {
    return false;
  }
  struct sockaddr_un bound {};
  socklen_t bound_length = sizeof(bound);
  if (::getsockname(fd_, reinterpret_cast<struct sockaddr *>(&bound), &bound_length) != 0) {
    return false;
  }
  return bound.sun_family == AF_UNIX;
}

int LocalIpcEndpoint::accept_one() const noexcept {
  if (fd_ < 0) {
    return -1;
  }
  return ::accept(fd_, nullptr, nullptr);
}

// ------------------------------------------------------------------------------------------------
// Framing
// ------------------------------------------------------------------------------------------------

GatewayFrameStatus gateway_decode_request_frame(const GatewayConfig &config,
                                                std::span<const std::byte> frame,
                                                GatewayFrameView &out) noexcept {
  if (frame.size() < 6U) {
    return GatewayFrameStatus::malformed;
  }
  const std::uint32_t total = read_u32_be(frame.data());
  if (total > config.max_message_bytes()) {
    return GatewayFrameStatus::over_bound;
  }
  if (frame.size() < static_cast<std::size_t>(total) + 4U || total < 2U) {
    return GatewayFrameStatus::malformed;
  }
  const std::uint16_t method_length = read_u16_be(frame.data() + 4U);
  if (method_length == 0U || static_cast<std::size_t>(method_length) + 2U > total) {
    return GatewayFrameStatus::malformed;
  }
  const auto *method_begin = reinterpret_cast<const char *>(frame.data() + 6U);
  const std::string_view method(method_begin, method_length);
  if (!is_known_method(method)) {
    return GatewayFrameStatus::unknown_method;
  }
  out.method = method;
  out.payload = frame.subspan(6U + method_length, total - 2U - method_length);
  return GatewayFrameStatus::ok;
}

// ------------------------------------------------------------------------------------------------
// GatewaySession
// ------------------------------------------------------------------------------------------------

namespace {

/// @brief Fills one bounded payload-free diagnostic.
void set_diagnostic(v1::Diagnostic *diagnostic, std::string_view code, v1::Severity severity,
                    std::string_view phase, std::string_view reason) noexcept {
  if (diagnostic == nullptr) {
    return;
  }
  diagnostic->set_code(std::string(code));
  diagnostic->set_severity(severity);
  diagnostic->set_phase(std::string(phase));
  diagnostic->set_reason(std::string(reason));
}

}  // namespace

GatewaySession::GatewaySession(const GatewayConfig &config,
                               const GatewayDependencies &dependencies,
                               GatewaySessionBinding binding) noexcept
    : config_(config), dependencies_(dependencies), binding_(std::move(binding)),
      last_activity_tick_(binding_.arrival_tick),
      flow_tokens_(config.max_pending_requests()) {}

GatewayOutcome GatewaySession::negotiate(const v1::ProtocolVersion &peer) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  if (!open_ || terminal_) {
    negotiation_ = GatewayOutcome::evidence_incomplete;
    return negotiation_;
  }
  ++requests_received_;
  if (peer.major() == kGatewaySupportedMajor) {
    negotiated_ = true;
    peer_version_ = peer;
    negotiation_ = GatewayOutcome::accepted;
    ++requests_authorized_;
    log(GatewayOutcome::accepted, GatewayPhase::negotiate, "gw.protocol.accepted",
        binding_.session_id, sizeof(peer_version_), peer.minor());
    return negotiation_;
  }
  negotiated_ = false;
  negotiation_ = GatewayOutcome::rejected;
  ++requests_rejected_;
  log(GatewayOutcome::rejected, GatewayPhase::negotiate, "gw.protocol.rejected", binding_.session_id,
      0U, peer.major());
  return negotiation_;
}

val::Timestamp GatewaySession::resolve_dispatch_tick() const noexcept {
  val::Timestamp value = binding_.arrival_tick;
  if (dependencies_.time_authority != nullptr &&
      binding_.arrival_domain != val::kInvalidClockDomain) {
    val::Timestamp reading = value;
    if (dependencies_.time_authority->now(binding_.arrival_domain, reading) == val::Result::Ok) {
      value = reading;
    }
  }
  return value;
}

bool GatewaySession::session_matches(const std::string &session_id) const noexcept {
  return !binding_.session_id.empty() && binding_.session_id == session_id;
}

GatewaySession::Admission GatewaySession::admit(
    std::uint64_t deadline_millis, std::optional<val::Timestamp> arrival_tick) noexcept {
  Admission admission{};
  ++requests_received_;
  if (!open_ || terminal_) {
    admission.outcome = GatewayOutcome::evidence_incomplete;
    ++requests_rejected_;
    log(admission.outcome, GatewayPhase::transport, "gw.session.terminal", binding_.session_id, 0U,
        0U);
    return admission;
  }
  if (!negotiated_) {
    admission.outcome = GatewayOutcome::rejected;
    ++requests_rejected_;
    log(admission.outcome, GatewayPhase::negotiate, "gw.protocol.unnegotiated", binding_.session_id,
        0U, 0U);
    return admission;
  }
  if (deadline_millis > config_.max_deadline_millis()) {
    admission.outcome = GatewayOutcome::rejected;
    ++requests_rejected_;
    log(admission.outcome, GatewayPhase::transport, "gw.deadline.overbound", binding_.session_id, 0U,
        deadline_millis);
    return admission;
  }
  // The arrival is captured for this request before dispatch. In-process callers that do not
  // supply one begin their request at the current declared tick. An explicit arrival lets a
  // transport reject work delayed after reception without using the session-creation tick.
  const std::uint64_t effective =
      deadline_millis == 0U ? config_.max_deadline_millis() : deadline_millis;
  const val::Timestamp now = resolve_dispatch_tick();
  const val::Timestamp arrival = arrival_tick.value_or(now);
  const val::Timestamp due = saturating_add(arrival, static_cast<val::Timestamp>(effective));
  if (now > due) {
    admission.outcome = GatewayOutcome::expired;
    ++requests_rejected_;
    log(admission.outcome, GatewayPhase::transport, "gw.deadline.expired", binding_.session_id, 0U,
        static_cast<std::uint64_t>(now));
    return admission;
  }
  if (flow_tokens_ == 0U) {
    admission.outcome = GatewayOutcome::rejected;
    ++requests_rejected_;
    ++flow_rejections_;
    log(admission.outcome, GatewayPhase::transport, "gw.flow.saturated", binding_.session_id, 0U,
        0U);
    return admission;
  }
  --flow_tokens_;
  last_activity_tick_ = now;
  admission.proceed = true;
  admission.outcome = GatewayOutcome::accepted;
  return admission;
}

void GatewaySession::log(GatewayOutcome outcome, GatewayPhase phase, std::string_view code,
                         std::string_view identity, std::uint64_t size,
                         std::uint64_t timing) noexcept {
  if (dependencies_.log == nullptr) {
    return;
  }
  GatewayLogRecord record{};
  record.outcome = outcome;
  record.phase = phase;
  record.code = code;
  record.identity = identity;
  record.size = size;
  record.timing = timing;
  dependencies_.log->record(record);
}

GatewaySession::StreamOwnership *
GatewaySession::find_stream_locked(std::string_view stream_id) noexcept {
  for (StreamOwnership &stream : streams_) {
    if (stream.id == stream_id) {
      return &stream;
    }
  }
  return nullptr;
}

void GatewaySession::detach_all_streams_locked() noexcept {
  if (dependencies_.observations != nullptr) {
    for (StreamOwnership &stream : streams_) {
      static_cast<void>(dependencies_.observations->detach(*stream.handle));
    }
  }
  streams_.clear();
  active_streams_ = 0U;
}

std::uint32_t GatewaySession::action_pending_locked() const noexcept {
  if (dependencies_.actions == nullptr) {
    return 0U;
  }
  const val::ActionPathSnapshot snapshot = dependencies_.actions->snapshot();
  const std::size_t bounded =
      std::min<std::size_t>(snapshot.pending, config_.max_pending_requests());
  return static_cast<std::uint32_t>(bounded);
}

void GatewaySession::drain_scheduled_locked(val::Timestamp now) noexcept {
  if (dependencies_.actions == nullptr) {
    return;
  }
  val::CompletionRequest completion{};
  completion.now = now;
  completion.domain = binding_.arrival_domain;
  completion.session_state = val::LifecycleState::active;
  const val::CompletionReport report = dependencies_.actions->drain(completion);
  emitted_ += report.drained;
  evidence_incomplete_ += report.evidence_incomplete;
  if (report.drained > 0U) {
    last_pending_outcome_ = GatewayOutcome::accepted;
  }
  pending_requests_ = action_pending_locked();
}

void GatewaySession::cleanup_locked(GatewayOutcome pending_outcome, GatewayPhase phase) noexcept {
  detach_all_streams_locked();
  if (dependencies_.actions != nullptr && pending_requests_ > 0U) {
    val::CompletionRequest completion{};
    completion.now = resolve_dispatch_tick();
    completion.domain = binding_.arrival_domain;
    completion.session_state = val::LifecycleState::evidence_incomplete;
    static_cast<void>(dependencies_.actions->close(completion));
  }
  if (lease_held_ && dependencies_.leases != nullptr) {
    const val::LeaseStatus released = dependencies_.leases->release(lease_key_, lease_request_id_);
    if (released != val::LeaseStatus::Ok) {
      static_cast<void>(dependencies_.leases->quarantine(lease_key_, val::QuarantineReason::Conflict));
    }
  }
  lease_held_ = false;
  if (pending_requests_ > 0U) {
    evidence_incomplete_ += pending_requests_;
    last_pending_outcome_ = pending_outcome;
    pending_requests_ = 0U;
  }
  terminal_ = true;
  terminal_state_ = pending_outcome == GatewayOutcome::expired
                        ? v1::SESSION_EXPIRED : v1::SESSION_EVIDENCE_INCOMPLETE;
  armed_ = false;
  log(pending_outcome, phase, "gw.session.cleanup", binding_.session_id, 0U, 0U);
}

void GatewaySession::on_disconnect() noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  if (terminal_) {
    return;
  }
  cleanup_locked(GatewayOutcome::evidence_incomplete, GatewayPhase::transport);
}

void GatewaySession::on_idle_tick(val::Timestamp now) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  if (terminal_) {
    return;
  }
  // Idle timeout is measured from the most recent declared activity, not from session creation.
  const val::Timestamp deadline = saturating_add(
      last_activity_tick_, static_cast<val::Timestamp>(config_.session_idle_timeout_millis()));
  if (now >= deadline) {
    cleanup_locked(GatewayOutcome::expired, GatewayPhase::session);
    return;
  }
  flow_tokens_ = config_.max_pending_requests();
  if (armed_ && has_handle_) {
    drain_scheduled_locked(now);
  }
}

void GatewaySession::poll_now() noexcept { on_idle_tick(resolve_dispatch_tick()); }

val::Timestamp GatewaySession::current_tick() const noexcept { return resolve_dispatch_tick(); }

bool GatewaySession::flow_tokens_available() const noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  return flow_tokens_ > 0U;
}

GatewaySessionSnapshot GatewaySession::snapshot() const noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  GatewaySessionSnapshot result{};
  result.negotiation = negotiation_;
  result.negotiated = negotiated_;
  result.terminal = terminal_;
  result.armed = armed_;
  result.active_streams = active_streams_;
  result.pending_requests = pending_requests_;
  result.requests_received = requests_received_;
  result.requests_authorized = requests_authorized_;
  result.requests_rejected = requests_rejected_;
  result.emitted = emitted_;
  result.evidence_incomplete = evidence_incomplete_;
  result.flow_rejections = flow_rejections_;
  result.flow_tokens = flow_tokens_;
  result.last_pending_outcome = last_pending_outcome_;
  result.lease_held = lease_held_;
  return result;
}

v1::QueryVersionResponse GatewaySession::QueryVersion(const v1::QueryVersionRequest &request) noexcept {
  static_cast<void>(request);
  std::lock_guard<std::mutex> lock(mutex_);
  v1::QueryVersionResponse response;
  response.mutable_protocol()->set_major(kGatewaySupportedMajor);
  response.mutable_protocol()->set_minor(kGatewaySupportedMinor);
  v1::GatewayCapabilities *capabilities = response.mutable_capabilities();
  *capabilities->mutable_protocol() = response.protocol();
  capabilities->set_max_message_bytes(static_cast<std::uint32_t>(config_.max_message_bytes()));
  capabilities->set_max_concurrent_streams(config_.max_streams_per_session());
  capabilities->set_max_deadline_millis(config_.max_deadline_millis());
  capabilities->set_max_observation_queue(config_.max_observation_records());
  v1::Capability *capability = capabilities->add_capabilities();
  capability->set_id("xcom.tool_gateway.local_ipc");
  capability->set_revision(1U);
  capability = capabilities->add_capabilities();
  capability->set_id("xcom.gateway_liveness.local_ipc");
  capability->set_revision(1U);
  capability = capabilities->add_capabilities();
  capability->set_id("xcom.stimulation_outcome_lookup");
  capability->set_revision(1U);
  v1::Diagnostic *diagnostic = response.mutable_diagnostic();
  if (negotiated_) {
    set_diagnostic(diagnostic, "gw.protocol.accepted", v1::SEVERITY_INFO, "negotiate",
                   "supported major");
  } else {
    set_diagnostic(diagnostic, "gw.protocol.rejected", v1::SEVERITY_ERROR, "negotiate",
                   "unsupported or unnegotiated major");
  }
  return response;
}

v1::OpenObservationResponse
GatewaySession::OpenObservation(const v1::OpenObservationRequest &request,
                                std::optional<val::Timestamp> arrival_tick) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::OpenObservationResponse response;
  const Admission admission = admit(request.deadline_millis(), arrival_tick);
  if (!admission.proceed) {
    set_diagnostic(response.mutable_diagnostic(), "gw.observation.declined", v1::SEVERITY_ERROR,
                   "observation", to_string(admission.outcome));
    return response;
  }
  if (dependencies_.observations == nullptr) {
    ++requests_rejected_;
    set_diagnostic(response.mutable_diagnostic(), "gw.observation.unavailable", v1::SEVERITY_ERROR,
                   "observation", "no observation boundary");
    return response;
  }
  if (active_streams_ >= config_.max_streams_per_session()) {
    ++requests_rejected_;
    set_diagnostic(response.mutable_diagnostic(), "gw.stream.capacity", v1::SEVERITY_ERROR,
                   "observation", "stream capacity reached");
    return response;
  }
  ObservationFilterInput filter{};
  if (!request.filter().contract_id().empty()) {
    filter.contract_id = request.filter().contract_id();
  }
  if (!request.filter().route_id().empty()) {
    filter.route_id = request.filter().route_id();
  }
  ObservationTapSpecInput spec_input{};
  spec_input.contract_version = kObservationContractVersion;
  spec_input.tap_id =
      request.tap_id().empty() ? kDefaultTapId : std::string_view(request.tap_id());
  spec_input.filter = filter;
  spec_input.payload_mode = ObservationPayloadMode::metadata_only;
  spec_input.maximum_payload_bytes = 0U;
  const std::uint32_t requested = request.max_records() == 0U ? 1U : request.max_records();
  spec_input.record_capacity = std::min(requested, config_.max_observation_records());
  spec_input.overflow_policy = ObservationOverflowPolicy::drop_newest;
  const std::optional<ObservationTapSpec> spec = ObservationTapSpec::create(spec_input);
  if (!spec.has_value()) {
    ++requests_rejected_;
    set_diagnostic(response.mutable_diagnostic(), "gw.tap.invalid", v1::SEVERITY_ERROR,
                   "observation", "invalid tap specification");
    return response;
  }
  const ObservationAttachResult attached = dependencies_.observations->attach(*spec);
  if (!attached.status.succeeded() || !attached.handle.has_value()) {
    ++requests_rejected_;
    set_diagnostic(response.mutable_diagnostic(), "gw.tap.attach", v1::SEVERITY_ERROR,
                   "observation", "observation boundary rejected the tap");
    return response;
  }
  ++stream_counter_;
  streams_.push_back(StreamOwnership{
      std::string("gw-stream-" + std::to_string(stream_counter_)),
      std::make_unique<ObservationTapHandle>(*attached.handle)});
  ++active_streams_;
  ++requests_authorized_;
  response.set_stream_id(streams_.back().id);
  response.set_granted_max_records(config_.max_observation_records());
  response.set_granted_max_record_bytes(0U);
  set_diagnostic(response.mutable_diagnostic(), "gw.observation.opened", v1::SEVERITY_INFO,
                 "observation", "bounded metadata-only stream granted");
  log(GatewayOutcome::accepted, GatewayPhase::observation, "gw.observation.opened",
      streams_.back().id, static_cast<std::uint64_t>(streams_.back().id.size()), 0U);
  return response;
}

std::size_t
GatewaySession::ReadObservations(const v1::ReadObservationsRequest &request,
                                 std::span<v1::ObservationRecord> out,
                                 std::optional<val::Timestamp> arrival_tick,
                                 GatewayOutcome *outcome) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  const Admission admission = admit(request.deadline_millis(), arrival_tick);
  if (outcome != nullptr) {
    *outcome = admission.outcome;
  }
  if (!admission.proceed) {
    return 0U;
  }
  StreamOwnership *stream =
      request.stream_id().empty() ? nullptr : find_stream_locked(request.stream_id());
  if (stream == nullptr) {
    ++requests_rejected_;
    if (outcome != nullptr) {
      *outcome = GatewayOutcome::rejected;
    }
    log(GatewayOutcome::rejected, GatewayPhase::observation, "gw.stream.unknown", binding_.session_id,
        0U, 0U);
    return 0U;
  }
  const std::size_t requested = static_cast<std::size_t>(request.max_records());
  const std::size_t configured = static_cast<std::size_t>(config_.max_observation_records());
  const std::size_t bound = std::min({requested, configured, out.size()});
  std::size_t written = 0U;
  for (std::size_t index = 0U; index < bound; ++index) {
    if (dependencies_.observations == nullptr) {
      break;
    }
    ObservationPollResult poll = dependencies_.observations->poll(*stream->handle);
    if (!poll.record.has_value()) {
      break;
    }
    const ObservationRecord &record = *poll.record;
    v1::ObservationRecord &target = out[index];
    target.Clear();
    target.set_route_id(std::string(record.route_id().value()));
    target.set_contract_id(std::string(record.contract_id().value()));
    target.set_clock_domain(std::string(record.observation_clock_domain().value()));
    if (record.sequence().has_value()) {
      target.set_sequence(*record.sequence());
    }
    target.set_outcome("accepted");
    target.set_payload_state(v1::PAYLOAD_METADATA_ONLY);
    target.set_payload_bytes(0U);
    ++written;
  }
  ++requests_authorized_;
  log(GatewayOutcome::accepted, GatewayPhase::observation, "gw.observation.read", stream->id,
      static_cast<std::uint64_t>(written), 0U);
  return written;
}

v1::CloseObservationResponse
GatewaySession::CloseObservation(const v1::CloseObservationRequest &request,
                                 std::optional<val::Timestamp> arrival_tick) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::CloseObservationResponse response;
  const Admission admission = admit(0U, arrival_tick);
  if (!admission.proceed) {
    set_diagnostic(response.mutable_diagnostic(), "gw.observation.close.declined",
                   v1::SEVERITY_ERROR, "observation", to_string(admission.outcome));
    return response;
  }
  StreamOwnership *stream =
      request.stream_id().empty() ? nullptr : find_stream_locked(request.stream_id());
  if (stream == nullptr || dependencies_.observations == nullptr) {
    ++requests_rejected_;
    set_diagnostic(response.mutable_diagnostic(), "gw.stream.unknown", v1::SEVERITY_ERROR,
                   "observation", "unknown stream");
    return response;
  }
  const std::optional<ObservationSnapshot> snapshot =
      dependencies_.observations->snapshot(*stream->handle);
  const std::uint64_t delivered = snapshot.has_value() ? snapshot->accepted : 0U;
  const std::uint64_t dropped = snapshot.has_value() ? snapshot->dropped : 0U;
  static_cast<void>(dependencies_.observations->detach(*stream->handle));
  streams_.erase(streams_.begin() + (stream - streams_.data()));
  if (active_streams_ > 0U) {
    --active_streams_;
  }
  ++requests_authorized_;
  response.set_delivered(delivered);
  response.set_dropped(dropped);
  set_diagnostic(response.mutable_diagnostic(), "gw.observation.closed", v1::SEVERITY_INFO,
                 "observation", "bounded stream closed");
  log(GatewayOutcome::accepted, GatewayPhase::observation, "gw.observation.closed", binding_.session_id,
      delivered, 0U);
  return response;
}

v1::ArmSessionResponse
GatewaySession::ArmSession(const v1::ArmSessionRequest &request,
                           std::optional<val::Timestamp> arrival_tick) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::ArmSessionResponse response;
  const Admission admission = admit(request.deadline_millis(), arrival_tick);
  if (!admission.proceed) {
    response.set_state(wire_state(terminal_, armed_, terminal_, admission.outcome == GatewayOutcome::expired));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.arm.declined", v1::SEVERITY_ERROR,
                   "session", to_string(admission.outcome));
    return response;
  }
  if (!binding_.has_permit) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.permit.absent", v1::SEVERITY_ERROR, "session",
                   "no exact permit bound");
    return response;
  }
  if (request.permit_id() != binding_.permit_id || !session_matches(request.session_id())) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.permit.mismatch", v1::SEVERITY_ERROR, "session",
                   "permit or session identity mismatch");
    return response;
  }
  if (request.has_protocol() && request.protocol().major() != kGatewaySupportedMajor) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.protocol.rejected", v1::SEVERITY_ERROR,
                   "session", "unsupported major");
    return response;
  }
  if (dependencies_.sessions == nullptr) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.unavailable", v1::SEVERITY_ERROR,
                   "session", "no validation-session boundary");
    return response;
  }
  if (has_handle_) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.already_armed", v1::SEVERITY_ERROR,
                   "session", "session already armed");
    return response;
  }
  val::SessionHandle handle{};
  if (dependencies_.sessions->consume(binding_.controller, binding_.permit, binding_.context,
                                      handle) != val::Result::Ok) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.consume", v1::SEVERITY_ERROR, "session",
                   "permit consumption declined");
    return response;
  }
  const val::Timestamp now = resolve_dispatch_tick();
  val::Diagnostic detail;
  if (dependencies_.sessions->transition(handle, val::Action::Arm, binding_.arrival_domain, now,
                                         detail) != val::Result::Ok) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.arm", v1::SEVERITY_ERROR, "session",
                   "arm transition declined");
    return response;
  }
  if (dependencies_.sessions->transition(handle, val::Action::Activate, binding_.arrival_domain, now,
                                         detail) != val::Result::Ok) {
    ++requests_rejected_;
    response.set_state(v1::SESSION_ARMED);
    set_diagnostic(response.mutable_diagnostic(), "gw.session.activate", v1::SEVERITY_ERROR,
                   "session", "activate transition declined");
    return response;
  }
  handle_ = handle;
  has_handle_ = true;
  armed_ = true;
  ++requests_authorized_;
  response.set_state(v1::SESSION_ARMED);
  set_diagnostic(response.mutable_diagnostic(), "gw.session.armed", v1::SEVERITY_INFO, "session",
                 "exact permit armed and activated");
  log(GatewayOutcome::accepted, GatewayPhase::session, "gw.session.armed", binding_.session_id, 0U,
      static_cast<std::uint64_t>(now));
  return response;
}

v1::RevokeSessionResponse
GatewaySession::RevokeSession(const v1::RevokeSessionRequest &request,
                              std::optional<val::Timestamp> arrival_tick) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::RevokeSessionResponse response;
  const Admission admission = admit(0U, arrival_tick);
  if (!admission.proceed) {
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.revoke.declined", v1::SEVERITY_ERROR,
                   "session", to_string(admission.outcome));
    return response;
  }
  if (!session_matches(request.session_id()) || !has_handle_ ||
      dependencies_.sessions == nullptr) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.unknown", v1::SEVERITY_ERROR,
                   "session", "unknown or unarmed session");
    return response;
  }
  const val::Timestamp now = resolve_dispatch_tick();
  val::Diagnostic detail;
  if (dependencies_.sessions->transition(handle_, val::Action::Revoke, binding_.arrival_domain, now,
                                         detail) != val::Result::Ok) {
    ++requests_rejected_;
    response.set_state(wire_state(terminal_, armed_, false, false));
    set_diagnostic(response.mutable_diagnostic(), "gw.session.revoke", v1::SEVERITY_ERROR, "session",
                   "revoke transition declined");
    return response;
  }
  ++requests_authorized_;
  log(GatewayOutcome::accepted, GatewayPhase::session, "gw.session.revoked", binding_.session_id, 0U,
      static_cast<std::uint64_t>(now));
  cleanup_locked(GatewayOutcome::evidence_incomplete, GatewayPhase::session);
  terminal_state_ = v1::SESSION_REVOKED;
  response.set_state(v1::SESSION_REVOKED);
  set_diagnostic(response.mutable_diagnostic(), "gw.session.revoked", v1::SEVERITY_INFO, "session",
                 "session revoked");
  return response;
}

v1::SubmitStimulationResponse
GatewaySession::SubmitStimulation(const v1::SubmitStimulationRequest &request,
                                  std::optional<val::Timestamp> arrival_tick,
                                  bool (*abort_before_dispatch)(void *) noexcept,
                                  void *abort_context) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::SubmitStimulationResponse response;
  response.set_request_id(request.request_id());
  const Admission admission = admit(request.deadline_millis(), arrival_tick);
  if (!admission.proceed) {
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(),
                   admission.outcome == GatewayOutcome::expired ? "gw.deadline.expired"
                                                                 : "gw.stimulation.declined",
                   v1::SEVERITY_ERROR,
                   "stimulation", to_string(admission.outcome));
    return response;
  }
  if (!binding_.has_permit || !armed_ || !has_handle_) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.session.notarmed", v1::SEVERITY_ERROR,
                   "stimulation", "session is not armed under an exact permit");
    return response;
  }
  if (!session_matches(request.session_id())) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.session.mismatch", v1::SEVERITY_ERROR,
                   "stimulation", "session identity mismatch");
    return response;
  }
  if (request.payload_bytes() > config_.max_payload_bytes() ||
      request.payload().size() > config_.max_payload_bytes()) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.payload.overbound", v1::SEVERITY_ERROR,
                   "stimulation", "payload exceeds the declared bound");
    return response;
  }
  bool known = false;
  const val::StimulationAction action = action_from_kind(request.action().kind(), known);
  if (!known) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.action.unknown", v1::SEVERITY_ERROR,
                   "stimulation", "unknown stimulation action kind");
    return response;
  }
  // R2: validate and preserve every declared wire field before any side effect. A request is
  // rejected, never silently normalized, when its declared semantics are incompatible with the
  // action, its contract, its schedule mode, or its declared clock domain.
  if (!wire_interaction_matches(request.interaction(), action)) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.interaction", v1::SEVERITY_ERROR,
                   "stimulation", "declared interaction is incompatible with the action");
    return response;
  }
  if (!wire_direction_valid(request.direction())) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.direction", v1::SEVERITY_ERROR,
                   "stimulation", "declared direction is not an outbound stimulation direction");
    return response;
  }
  if (!binding_.contract_id.empty() && request.contract_id() != binding_.contract_id) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.contract.mismatch", v1::SEVERITY_ERROR,
                   "stimulation", "declared contract identity differs from the bound contract");
    return response;
  }
  if (!wire_schedule_mode_known(request.schedule().mode())) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.schedule.unknown", v1::SEVERITY_ERROR,
                   "stimulation", "unknown schedule mode");
    return response;
  }
  if (!binding_.arrival_domain_name.empty() &&
      request.schedule().clock_domain() != binding_.arrival_domain_name) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.clock.unmapped", v1::SEVERITY_ERROR,
                   "stimulation", "declared clock domain is unmapped");
    return response;
  }
  if (dependencies_.actions == nullptr) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.actions.unavailable", v1::SEVERITY_ERROR,
                   "stimulation", "no accepted action-path boundary");
    return response;
  }
  const std::optional<val::Tag> target = val::Tag::make(request.target_endpoint());
  if (!target.has_value()) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.target.invalid", v1::SEVERITY_ERROR,
                   "stimulation", "invalid target tag");
    return response;
  }
  const bool scheduled = request.schedule().mode() == v1::SCHEDULE_SCHEDULED;
  const val::Timestamp now = resolve_dispatch_tick();
  const std::uint64_t effective_deadline = request.deadline_millis() == 0U
                                               ? config_.max_deadline_millis()
                                               : request.deadline_millis();
  const val::Timestamp request_horizon = saturating_add(
      arrival_tick.value_or(now), static_cast<val::Timestamp>(effective_deadline));
  if (now > request_horizon) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.deadline.expired", v1::SEVERITY_ERROR,
                   "stimulation", "request deadline expired before action dispatch");
    return response;
  }
  const std::uint64_t raw_due = request.schedule().due_nanos();
  const val::Timestamp declared_due =
      raw_due > static_cast<std::uint64_t>(std::numeric_limits<val::Timestamp>::max())
          ? std::numeric_limits<val::Timestamp>::max()
          : static_cast<val::Timestamp>(raw_due);
  // R4: the declared schedule must fall inside this request's own deadline window; a schedule that
  // cannot complete within the request bound is rejected before it can be queued.
  if (scheduled && declared_due > request_horizon) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.deadline.schedule", v1::SEVERITY_ERROR,
                   "stimulation", "declared schedule exceeds the request deadline");
    return response;
  }
  // R3: the bounded pending queue is the real accepted scheduler queue, not a counter. Capacity is
  // enforced before enqueueing, independent of transient flow-credit replenishment.
  if (scheduled && action_pending_locked() >= config_.max_pending_requests()) {
    ++requests_rejected_;
    ++flow_rejections_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.flow.saturated", v1::SEVERITY_ERROR,
                   "stimulation", "bounded scheduled queue is full");
    return response;
  }
  // This is the last gateway-owned point before the accepted action path may commit an item.
  // A later transport loss is not a failed business request and is reconciled by request ID.
  if (abort_before_dispatch != nullptr && abort_before_dispatch(abort_context)) {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.transport.cancelled", v1::SEVERITY_ERROR,
                   "stimulation", "transport ended before action dispatch");
    return response;
  }
  val::StimulationRequest stimulation{};
  stimulation.permit_id = binding_.permit.permit_id();
  stimulation.session_id = binding_.permit.session_id();
  stimulation.plan_digest = binding_.permit.plan_digest();
  stimulation.action = action;
  stimulation.interaction = interaction_from_wire(request.interaction());
  stimulation.direction = direction_for(action);
  stimulation.schema = schema_for(action);
  stimulation.target = *target;
  const std::optional<val::Tag> interface_tag =
      val::Tag::make(binding_.context.interface_name.empty() ? kDefaultInterface
                                                             : binding_.context.interface_name);
  stimulation.interface_tag = interface_tag.has_value() ? *interface_tag
                                                        : val::Tag(std::string(kDefaultInterface));
  stimulation.service_owner = binding_.service_owner;
  stimulation.clock_domain = binding_.arrival_domain;
  stimulation.scheduled_at = scheduled ? declared_due : 0;
  stimulation.immediate = !scheduled;
  stimulation.request_id = parse_identity(request.request_id());
  stimulation.correlation_id = parse_identity(request.action().correlation_id());
  stimulation.causation_id = request.action().causation_id();
  stimulation.quota_cost = 0U;
  const val::ResolvedTime resolved{binding_.arrival_domain, now, val::Result::Ok};
  const auto *payload_bytes = reinterpret_cast<const std::byte *>(request.payload().data());
  const std::span<const std::byte> payload(payload_bytes, request.payload().size());
  val::ActionDiagnostic diagnostic{};
  const val::ActionStatus status =
      dependencies_.actions->execute(stimulation, val::LifecycleState::active, resolved, payload,
                                     diagnostic);
  const GatewayOutcome outcome = outcome_from_status(status);
  if (status == val::ActionStatus::Emitted) {
    ++emitted_;
    ++requests_authorized_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_EMITTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.emitted", v1::SEVERITY_INFO,
                   "stimulation", "synthetic item emitted");
    response.mutable_diagnostic()->set_identity(request.contract_id());
  } else if (outcome == GatewayOutcome::accepted) {
    pending_requests_ = action_pending_locked();
    last_pending_outcome_ = GatewayOutcome::accepted;
    ++requests_authorized_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_QUEUED);
    set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.queued", v1::SEVERITY_INFO,
                   "stimulation", "bounded scheduled action retained in the accepted queue");
  } else if (outcome == GatewayOutcome::evidence_incomplete) {
    ++evidence_incomplete_;
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(v1::STIMULATION_OUTCOME_EVIDENCE_INCOMPLETE);
    set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.incomplete", v1::SEVERITY_ERROR,
                   "stimulation", "durable outcome unknown");
  } else {
    ++requests_rejected_;
    response.mutable_outcome()->set_kind(outcome == GatewayOutcome::failed
                                             ? v1::STIMULATION_OUTCOME_FAILED
                                             : v1::STIMULATION_OUTCOME_REJECTED);
    set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.declined", v1::SEVERITY_ERROR,
                   "stimulation", val::action_status_name(status));
  }
  log(outcome, GatewayPhase::stimulation, "gw.stimulation", request.request_id(), 0U,
      static_cast<std::uint64_t>(stimulation.request_id));
  return response;
}

v1::AcquireLeaseResponse
GatewaySession::AcquireLease(const v1::AcquireLeaseRequest &request,
                             std::optional<val::Timestamp> arrival_tick) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::AcquireLeaseResponse response;
  const Admission admission = admit(request.deadline_millis(), arrival_tick);
  if (!admission.proceed) {
    response.set_state(v1::LEASE_STATE_UNSPECIFIED);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.declined", v1::SEVERITY_ERROR, "lease",
                   to_string(admission.outcome));
    return response;
  }
  if (!binding_.has_permit || !armed_ || !has_handle_ || !session_matches(request.session_id()) ||
      dependencies_.leases == nullptr) {
    ++requests_rejected_;
    response.set_state(v1::LEASE_CONFLICT);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.unauthorized", v1::SEVERITY_ERROR,
                   "lease", "session not armed or no lease boundary");
    return response;
  }
  const std::optional<val::Tag> endpoint = val::Tag::make(request.endpoint_id());
  if (!endpoint.has_value()) {
    ++requests_rejected_;
    response.set_state(v1::LEASE_CONFLICT);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.invalid", v1::SEVERITY_ERROR, "lease",
                   "invalid endpoint identity");
    return response;
  }
  val::EndpointGeneration key{};
  key.session = binding_.permit.session_id();
  key.endpoint = *endpoint;
  key.generation = request.endpoint_generation();
  key.plan_digest = binding_.permit.plan_digest();
  const val::Timestamp now = resolve_dispatch_tick();
  const val::Timestamp expires =
      saturating_add(now, static_cast<val::Timestamp>(request.lease_millis()));
  lease_request_id_ = request.endpoint_generation() + 1U;
  const val::LeaseStatus status =
      dependencies_.leases->acquire(key, lease_request_id_, binding_.arrival_domain, now, expires);
  const GatewayOutcome outcome = outcome_from_lease(status);
  if (status == val::LeaseStatus::Ok) {
    lease_key_ = key;
    lease_held_ = true;
    lease_id_ = "gw-lease-" + std::to_string(request.endpoint_generation());
    ++requests_authorized_;
    response.set_lease_id(lease_id_);
    response.set_state(v1::LEASE_ACTIVE);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.acquired", v1::SEVERITY_INFO, "lease",
                   "exclusive generation-bound lease held");
  } else {
    ++requests_rejected_;
    response.set_state(status == val::LeaseStatus::Conflict ? v1::LEASE_CONFLICT : v1::LEASE_EXPIRED);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.declined", v1::SEVERITY_ERROR, "lease",
                   val::lease_status_name(status));
  }
  log(outcome, GatewayPhase::lease, "gw.lease.acquire", request.session_id(), 0U,
      static_cast<std::uint64_t>(now));
  return response;
}

v1::ReleaseLeaseResponse
GatewaySession::ReleaseLease(const v1::ReleaseLeaseRequest &request,
                             std::optional<val::Timestamp> arrival_tick) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::ReleaseLeaseResponse response;
  const Admission admission = admit(0U, arrival_tick);
  if (!admission.proceed) {
    response.set_state(v1::LEASE_STATE_UNSPECIFIED);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.release.declined", v1::SEVERITY_ERROR,
                   "lease", to_string(admission.outcome));
    return response;
  }
  if (!lease_held_ || !session_matches(request.session_id()) ||
      dependencies_.leases == nullptr) {
    ++requests_rejected_;
    response.set_state(v1::LEASE_QUARANTINED);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.notheld", v1::SEVERITY_ERROR, "lease",
                   "no held lease for this session");
    return response;
  }
  // R6: the release must name the exact held lease identity. A mismatched or stale identity is
  // rejected without changing any lease or session state.
  if (request.lease_id() != lease_id_) {
    ++requests_rejected_;
    response.set_state(v1::LEASE_QUARANTINED);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.identity", v1::SEVERITY_ERROR, "lease",
                   "lease identity does not match the held lease");
    return response;
  }
  const val::LeaseStatus status = dependencies_.leases->release(lease_key_, lease_request_id_);
  if (status == val::LeaseStatus::Ok) {
    lease_held_ = false;
    ++requests_authorized_;
    response.set_state(v1::LEASE_RELEASED);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.released", v1::SEVERITY_INFO, "lease",
                   "lease released");
  } else {
    ++requests_rejected_;
    response.set_state(v1::LEASE_QUARANTINED);
    set_diagnostic(response.mutable_diagnostic(), "gw.lease.release.declined", v1::SEVERITY_ERROR,
                   "lease", val::lease_status_name(status));
  }
  log(GatewayOutcome::accepted, GatewayPhase::lease, "gw.lease.release", request.lease_id(), 0U, 0U);
  return response;
}

v1::QuerySessionResponse
GatewaySession::QuerySession(const v1::QuerySessionRequest &request,
                             std::optional<val::Timestamp> arrival_tick) noexcept {
  std::lock_guard<std::mutex> lock(mutex_);
  v1::QuerySessionResponse response;
  const auto populate_state = [&] {
    response.set_state(terminal_ ? terminal_state_ : wire_state(false, armed_, false, false));
    response.set_lease_held(lease_held_);
    if (lease_held_) {
      response.set_lease_id(lease_id_);
    }
    response.set_active_observation_streams(active_streams_);
    v1::SessionCounters *counters = response.mutable_counters();
    counters->set_requests_received(requests_received_);
    counters->set_requests_authorized(requests_authorized_);
    counters->set_requests_rejected(requests_rejected_);
    counters->set_emitted(emitted_);
    counters->set_evidence_incomplete(evidence_incomplete_);
  };
  if (!request.stimulation_request_id().empty()) {
    // Reconciliation is read-only and remains available after the transport
    // watch has ended or the session has become terminal.
    if (!session_matches(request.session_id()) || dependencies_.journal == nullptr ||
        parse_identity(request.stimulation_request_id()) == 0U) {
      set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.lookup.invalid",
                     v1::SEVERITY_ERROR, "query", "invalid reconciliation identity");
      return response;
    }
    populate_state();
    const std::uint64_t id = parse_identity(request.stimulation_request_id());
    const auto intents = dependencies_.journal->recovered_intents();
    const bool found = std::any_of(intents.begin(), intents.end(),
        [this, id](const auto &intent) {
          return intent.request_id == id && intent.session_id == binding_.permit.session_id();
        });
    if (!found) {
      set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.lookup.absent",
                     v1::SEVERITY_INFO, "query", "no durable intent for request");
      return response;
    }
    response.set_stimulation_intent_found(true);
    auto *reconciled = response.mutable_stimulation_outcome();
    reconciled->set_request_id(request.stimulation_request_id());
    reconciled->set_kind(v1::STIMULATION_OUTCOME_EVIDENCE_INCOMPLETE);
    const auto outcomes = dependencies_.journal->recovered_outcomes();
    for (const auto &outcome : outcomes) {
      if (outcome.request_id != id) {
        continue;
      }
      switch (outcome.kind) {
      case val::OutcomeKind::Delivered:
        reconciled->set_kind(v1::STIMULATION_OUTCOME_EMITTED);
        break;
      case val::OutcomeKind::Rejected:
      case val::OutcomeKind::Expired:
      case val::OutcomeKind::Cancelled:
        reconciled->set_kind(v1::STIMULATION_OUTCOME_REJECTED);
        break;
      case val::OutcomeKind::Unknown:
        break;
      }
      break;
    }
    set_diagnostic(response.mutable_diagnostic(), "gw.stimulation.lookup.found",
                   reconciled->kind() == v1::STIMULATION_OUTCOME_EVIDENCE_INCOMPLETE
                       ? v1::SEVERITY_WARNING : v1::SEVERITY_INFO,
                   "query", "durable stimulation outcome");
    return response;
  }
  const Admission admission = admit(0U, arrival_tick);
  if (!admission.proceed) {
    if (session_matches(request.session_id())) {
      populate_state();
    }
    set_diagnostic(response.mutable_diagnostic(), "gw.query.declined", v1::SEVERITY_ERROR, "query",
                   to_string(admission.outcome));
    return response;
  }
  if (!session_matches(request.session_id())) {
    ++requests_rejected_;
    set_diagnostic(response.mutable_diagnostic(), "gw.session.unknown", v1::SEVERITY_ERROR, "query",
                   "unknown session");
    return response;
  }
  ++requests_authorized_;
  populate_state();
  set_diagnostic(response.mutable_diagnostic(), "gw.session.query", v1::SEVERITY_INFO, "query",
                 "bounded counters");
  return response;
}

std::span<const std::string_view> gateway_operation_names() noexcept {
  static constexpr std::array<std::string_view, 10> kOperations = {
      "QueryVersion",      "OpenObservation", "ReadObservations", "CloseObservation",
      "ArmSession",        "RevokeSession",   "SubmitStimulation", "AcquireLease",
      "ReleaseLease",      "QuerySession",
  };
  return kOperations;
}

}  // namespace xverse::xcom
