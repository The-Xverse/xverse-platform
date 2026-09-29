/**
 * @file synthetic_tool.cpp
 * @brief T032 bounded, separate-process synthetic tool client realizing the accepted T030
 *        `xverse.xcom.v1.ToolGateway` generated message and method contract over the accepted T031
 *        host-protected `AF_UNIX` local-IPC framing.
 * @details This fixture process is one declared owner of the accepted `XCOM-DU-021` separate-process
 *          synthetic tool client. It parses an explicit bounded argument vector, connects only to a
 *          host-protected local endpoint, serializes the generated Protocol Buffers request messages
 *          into the T031 method-name-addressed request frame, reads bounded response frames, and
 *          writes bounded payload-free result lines (`method`, stable `outcome`, `size`, `timing`,
 *          and logical counters only). It recognizes the ten accepted `ToolGateway` operations by
 *          their exact committed method names and fails closed when its committed operation table
 *          differs from the generated `ToolGateway` service descriptor method set. It declares
 *          explicit maximum message size, per-request deadline, and transport timeout bounds, adds
 *          no admitted dependency, links no transport runtime, and defines no competing contract,
 *          RPC definition, or configuration language.
 * @ingroup xcom_gw
 * @par Traceability
 * Realizes accepted `XCOM-DU-021` (separate-process synthetic tool client), `XCOM-CMP-011`
 * (synthetic sink and tools), `XCOM-XLC-002` (external-rpc contract), and boundary `XCOM-XB-010`.
 * Verified by the T032 `t032-` suites and the generated-client contract cases.
 * @ownership The process owns its bounded buffers, one local socket descriptor, and one result
 *            stream for the whole run; it holds no gateway session handle (the parent harness owns
 *            the accepted `GatewaySession`).
 * @lifetime The socket descriptor and buffers live for the bounded run; every value is released on
 *           process exit.
 * @thread_safety One declared user; one request or bounded stream at a time. Externally synchronized.
 * @failure An invalid, over-bound, timed-out, disconnected, or unknown exchange returns a stable
 *          non-success result and never reports success.
 */

#include "xverse/xcom/tool_gateway.hpp"

#include <google/protobuf/descriptor.h>

#include <array>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include <fcntl.h>
#include <poll.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

/// @brief Root namespace of the X-COM subsystem.
namespace xverse::xcom::synthetic {

namespace v1 = xverse::xcom::v1;
namespace proto = google::protobuf;

/// @brief Accepted protocol major realized by this client slice.
inline constexpr std::uint32_t kClientSupportedMajor = 1U;
/// @brief Negotiated protocol minor realized by this client slice.
inline constexpr std::uint32_t kClientSupportedMinor = 0U;
/// @brief Maximum accepted client frame size.
inline constexpr std::size_t kClientMaxMessageBytes = 1U << 20U;
/// @brief Maximum accepted client per-request deadline.
inline constexpr std::uint64_t kClientMaxDeadlineMillis = 600000U;
/// @brief Maximum accepted client transport timeout.
inline constexpr std::uint64_t kClientMaxTransportMillis = 60000U;
/// @brief Maximum bounded response frames consumed for one observation read.
inline constexpr std::size_t kClientMaxReadFrames = 64U;

/// @brief Logical permit identity expected on the wire.
inline constexpr std::string_view kPermitIdentity = "permit-1";
/// @brief Logical session identity expected on the wire.
inline constexpr std::string_view kSessionIdentity = "session-1";
/// @brief Logical plan digest expected on the wire.
inline constexpr std::string_view kPlanIdentity = "plan-1";
/// @brief Logical graph digest expected on the wire.
inline constexpr std::string_view kGraphIdentity = "graph-1";
/// @brief Logical target endpoint used by stimulation submissions.
inline constexpr std::string_view kTargetIdentity = "target.alpha";
/// @brief Logical contract identity used by stimulation submissions.
inline constexpr std::string_view kContractIdentity = "gateway.contract";

/**
 * @brief Explicit bounded client configuration.
 * @ownership Copyable plain value; owns no resource.
 * @lifetime Value lifetime.
 * @thread_safety Safe to copy and read concurrently.
 * @failure `make_client_config` rejects a zero, unbounded, or malformed value fail-closed.
 */
struct SyntheticClientConfig final {
  /// @brief Maximum accepted request/response frame size in bytes.
  std::size_t max_message_bytes{0U};
  /// @brief Maximum accepted per-request deadline in milliseconds.
  std::uint64_t request_deadline_millis{0U};
  /// @brief Bounded transport wait in milliseconds.
  std::uint64_t transport_timeout_millis{0U};
};

/// @brief Bounded result of one client exchange.
struct SyntheticClientResult final {
  /// @brief Exact T030 `ToolGateway` method name, or a stable transport phase label.
  std::string_view method;
  /// @brief Stable success or non-success outcome code.
  std::string_view outcome;
  /// @brief Bounded record/byte/rejection count.
  std::uint64_t size{0U};
  /// @brief Declared bounded timing value.
  std::uint64_t timing{0U};
};

/// @brief Bounded frame receive outcome.
enum class FrameResult : std::uint8_t {
  ok,        ///< A non-empty payload frame was read.
  terminator,///< A bounded zero-length terminator frame was read.
  timeout,   ///< The bounded transport wait elapsed.
  closed,    ///< The peer closed before a complete frame arrived.
  error,     ///< A malformed or over-bound frame was observed.
};

/// @brief Parses one bounded decimal unsigned value.
/// @param text Non-empty decimal text.
/// @param out Receives the parsed value only on success.
/// @return `true` when the whole text is decimal and fits.
[[nodiscard]] bool parse_unsigned(std::string_view text, std::uint64_t &out) noexcept {
  if (text.empty() || text.size() > 19U) {
    return false;
  }
  std::uint64_t value = 0U;
  for (const char digit : text) {
    if (digit < '0' || digit > '9') {
      return false;
    }
    value = value * 10U + static_cast<std::uint64_t>(digit - '0');
  }
  out = value;
  return true;
}

/**
 * @brief Validates the explicit bounded client configuration.
 * @param max_text Declared maximum message size text.
 * @param deadline_text Declared per-request deadline text.
 * @param timeout_text Declared transport timeout text.
 * @return The validated configuration, or no value when a bound is zero, malformed, or
 *         over-maximum.
 * @ownership Owns one bounded value.
 * @lifetime Value lifetime.
 * @thread_safety Pure and deterministic.
 * @failure Any malformed or over-bound value yields no value; no implicit default exists.
 */
[[nodiscard]] std::optional<SyntheticClientConfig> make_client_config(std::string_view max_text,
                                                                     std::string_view deadline_text,
                                                                     std::string_view timeout_text) noexcept {
  SyntheticClientConfig config{};
  std::uint64_t max_message = 0U;
  std::uint64_t deadline = 0U;
  std::uint64_t timeout = 0U;
  if (!parse_unsigned(max_text, max_message) || !parse_unsigned(deadline_text, deadline) ||
      !parse_unsigned(timeout_text, timeout)) {
    return std::nullopt;
  }
  if (max_message < 16U || max_message > kClientMaxMessageBytes) {
    return std::nullopt;
  }
  if (deadline == 0U || deadline > kClientMaxDeadlineMillis) {
    return std::nullopt;
  }
  if (timeout == 0U || timeout > kClientMaxTransportMillis) {
    return std::nullopt;
  }
  config.max_message_bytes = static_cast<std::size_t>(max_message);
  config.request_deadline_millis = deadline;
  config.transport_timeout_millis = timeout;
  return config;
}

/**
 * @brief Bounded local-only connect/read/write seam; the only client transport.
 * @details It connects only to a host-protected local filesystem endpoint. It references no remote
 *          facility, resolver, or transport-security facility, and exposes no listening socket.
 * @ownership Owns exactly one connected socket descriptor.
 * @lifetime The descriptor lives until destruction, which closes it.
 * @thread_safety One declared user; bounded one-way exchanges only.
 * @failure `connect` returns no value for an empty/unreachable path or a non-local bound family;
 *          a read/write never blocks beyond the declared timeout.
 */
class LocalClientChannel final {
 public:
  /// @brief Connects one bounded local stream channel.
  /// @param local_path Non-empty local filesystem endpoint path.
  /// @param timeout_millis Bounded connect timeout.
  /// @return The connected channel, or no value when the path is empty or connect fails.
  [[nodiscard]] static std::optional<LocalClientChannel>
  connect(std::string_view local_path, std::uint64_t timeout_millis) noexcept {
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
    for (std::size_t index = 0U; index < local_path.size(); ++index) {
      address.sun_path[index] = local_path[index];
    }
    const int original_flags = ::fcntl(descriptor, F_GETFL, 0);
    if (original_flags < 0 || ::fcntl(descriptor, F_SETFL, original_flags | O_NONBLOCK) != 0) {
      ::close(descriptor);
      return std::nullopt;
    }
    const int connected =
        ::connect(descriptor, reinterpret_cast<struct sockaddr *>(&address), sizeof(address));
    if (connected != 0) {
      if (errno != EINPROGRESS) {
        ::close(descriptor);
        return std::nullopt;
      }
      struct pollfd wait {};
      wait.fd = descriptor;
      wait.events = POLLOUT;
      const int ready = ::poll(&wait, 1, static_cast<int>(timeout_millis));
      if (ready <= 0) {
        ::close(descriptor);
        return std::nullopt;
      }
      int pending_error = 0;
      socklen_t error_length = sizeof(pending_error);
      if (::getsockopt(descriptor, SOL_SOCKET, SO_ERROR, &pending_error, &error_length) != 0 ||
          pending_error != 0) {
        ::close(descriptor);
        return std::nullopt;
      }
    }
    static_cast<void>(::fcntl(descriptor, F_SETFL, original_flags));
    return LocalClientChannel(descriptor);
  }

  /// @brief Destructor; closes the owned descriptor.
  ~LocalClientChannel() {
    if (fd_ >= 0) {
      ::close(fd_);
      fd_ = -1;
    }
  }
  /// @brief Move construction transfers descriptor ownership.
  /// @param other Source channel whose descriptor ownership is transferred.
  LocalClientChannel(LocalClientChannel &&other) noexcept : fd_(other.fd_) { other.fd_ = -1; }
  /// @brief Copy construction is deleted; the channel owns a unique descriptor.
  LocalClientChannel(const LocalClientChannel &) = delete;
  /// @brief Copy assignment is deleted.
  LocalClientChannel &operator=(const LocalClientChannel &) = delete;
  /// @brief Move assignment is deleted; the channel is a single-use scope owner.
  LocalClientChannel &operator=(LocalClientChannel &&) = delete;

  /// @brief Reports whether the connected bound address family is local.
  /// @return `true` only when `getsockname` reports the local family.
  [[nodiscard]] bool is_local_endpoint() const noexcept {
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

  /// @brief Writes the complete bounded byte span.
  /// @param bytes Bounded source.
  /// @return `true` when every byte was written.
  [[nodiscard]] bool write_all(std::span<const std::byte> bytes) const noexcept {
    std::size_t written = 0U;
    while (written < bytes.size()) {
      const ssize_t count = ::write(fd_, bytes.data() + written, bytes.size() - written);
      if (count <= 0) {
        return false;
      }
      written += static_cast<std::size_t>(count);
    }
    return true;
  }

  /// @brief Reads exactly `length` bytes under a bounded wait.
  /// @param length Bounded byte count.
  /// @param timeout_millis Bounded wait.
  /// @param out Receives the bytes on success.
  /// @return The bounded read outcome.
  [[nodiscard]] FrameResult read_exact(std::size_t length, std::uint64_t timeout_millis,
                                       std::vector<std::byte> &out) const noexcept {
    out.assign(length, std::byte{0});
    std::size_t read = 0U;
    while (read < length) {
      struct pollfd wait {};
      wait.fd = fd_;
      wait.events = POLLIN;
      const int ready = ::poll(&wait, 1, static_cast<int>(timeout_millis));
      if (ready == 0) {
        return FrameResult::timeout;
      }
      if (ready < 0) {
        return FrameResult::error;
      }
      const ssize_t count = ::read(fd_, out.data() + read, length - read);
      if (count == 0) {
        return FrameResult::closed;
      }
      if (count < 0) {
        return FrameResult::error;
      }
      read += static_cast<std::size_t>(count);
    }
    return FrameResult::ok;
  }

  /// @brief Returns the raw connected descriptor.
  /// @return The descriptor, or `-1` when invalid.
  [[nodiscard]] int fd() const noexcept { return fd_; }

 private:
  explicit LocalClientChannel(int descriptor) noexcept : fd_(descriptor) {}
  int fd_{-1};
};

/// @brief Encodes one bounded method-name-addressed request frame.
/// @param method Exact committed method name.
/// @param message Serialized request message.
/// @return The bounded request frame bytes.
[[nodiscard]] std::vector<std::byte>
encode_request(std::string_view method, const std::string &message) {
  const std::size_t total = 2U + method.size() + message.size();
  std::vector<std::byte> frame;
  frame.reserve(4U + total);
  const auto push_u32 = [&frame](std::uint32_t value) {
    frame.push_back(static_cast<std::byte>((value >> 24U) & 0xFFU));
    frame.push_back(static_cast<std::byte>((value >> 16U) & 0xFFU));
    frame.push_back(static_cast<std::byte>((value >> 8U) & 0xFFU));
    frame.push_back(static_cast<std::byte>(value & 0xFFU));
  };
  push_u32(static_cast<std::uint32_t>(total));
  frame.push_back(static_cast<std::byte>((method.size() >> 8U) & 0xFFU));
  frame.push_back(static_cast<std::byte>(method.size() & 0xFFU));
  for (const char character : method) {
    frame.push_back(static_cast<std::byte>(static_cast<unsigned char>(character)));
  }
  for (const char character : message) {
    frame.push_back(static_cast<std::byte>(static_cast<unsigned char>(character)));
  }
  return frame;
}

/// @brief Reads one bounded response frame (4-byte big-endian length then payload).
/// @param channel Connected local channel.
/// @param config Explicit client bounds.
/// @param out Receives the payload bytes (empty for a zero-length terminator).
/// @return The bounded frame outcome.
[[nodiscard]] FrameResult read_response_frame(const LocalClientChannel &channel,
                                             const SyntheticClientConfig &config,
                                             std::vector<std::byte> &out) noexcept {
  std::vector<std::byte> prefix;
  FrameResult result =
      channel.read_exact(4U, config.transport_timeout_millis, prefix);
  if (result != FrameResult::ok) {
    return result;
  }
  const std::uint32_t length = (static_cast<std::uint32_t>(prefix[0]) << 24U) |
                               (static_cast<std::uint32_t>(prefix[1]) << 16U) |
                               (static_cast<std::uint32_t>(prefix[2]) << 8U) |
                               static_cast<std::uint32_t>(prefix[3]);
  if (length > config.max_message_bytes) {
    return FrameResult::error;
  }
  if (length == 0U) {
    out.clear();
    return FrameResult::terminator;
  }
  return channel.read_exact(length, config.transport_timeout_millis, out);
}

/// @brief Returns the committed client operation table.
/// @return Static-lifetime span of the ten accepted method names, in generated order.
[[nodiscard]] std::span<const std::string_view> synthetic_client_operation_names() noexcept {
  static const std::array<std::string_view, 10U> names = {
      "QueryVersion",  "OpenObservation", "ReadObservations", "CloseObservation", "ArmSession",
      "RevokeSession", "SubmitStimulation", "AcquireLease",   "ReleaseLease",     "QuerySession",
  };
  return names;
}

/// @brief Verifies the committed operation table against the generated service descriptor.
/// @return `true` when the table equals the generated `ToolGateway` method set in order.
[[nodiscard]] bool operation_table_matches_descriptor() noexcept {
  const proto::Descriptor *const generated_anchor = v1::ObservationRecord::descriptor();
  static_cast<void>(generated_anchor);
  const proto::FileDescriptor *file =
      proto::DescriptorPool::generated_pool()->FindFileByName("xverse/xcom/v1/tool_gateway.proto");
  if (file == nullptr) {
    return false;
  }
  const proto::ServiceDescriptor *service = file->FindServiceByName("ToolGateway");
  if (service == nullptr || static_cast<std::size_t>(service->method_count()) !=
                                synthetic_client_operation_names().size()) {
    return false;
  }
  const std::span<const std::string_view> table = synthetic_client_operation_names();
  for (std::size_t index = 0U; index < table.size(); ++index) {
    if (table[index] != service->method(static_cast<int>(index))->name()) {
      return false;
    }
  }
  return true;
}

/// @brief Bounded writer for payload-free result lines.
class ResultWriter final {
 public:
  /// @brief Opens the bounded result stream.
  /// @param path Non-empty result file path.
  explicit ResultWriter(const std::string &path) : stream_(path, std::ios::out | std::ios::trunc) {}

  /// @brief Returns whether the stream is usable.
  /// @return `true` when the result stream opened.
  [[nodiscard]] bool ok() const noexcept { return stream_.is_open(); }

  /// @brief Writes one bounded payload-free result line.
  /// @param result Bounded result to record.
  void write(const SyntheticClientResult &result) {
    stream_ << "method=" << result.method << " outcome=" << result.outcome
            << " size=" << result.size << " timing=" << result.timing << '\n';
  }

  /// @brief Writes one bounded payload-free key/value line.
  /// @param key Stable key (no whitespace, no payload).
  /// @param value Bounded stable value.
  void write(std::string_view key, std::string_view value) {
    stream_ << key << '=' << value << '\n';
  }

  /// @brief Writes one bounded payload-free key/value pair with a numeric value.
  /// @param key Stable key.
  /// @param value Bounded numeric value.
  void write(std::string_view key, std::uint64_t value) {
    stream_ << key << '=' << value << '\n';
  }

 private:
  std::ofstream stream_;
};

/// @brief Builds a bounded `SubmitStimulationRequest` for one action kind.
/// @param kind Committed stimulation action kind.
/// @param identity Bounded decimal request identity.
/// @param deadline Declared request deadline.
/// @return The bounded request.
[[nodiscard]] v1::SubmitStimulationRequest make_stimulation_request(v1::StimulationActionKind kind,
                                                                    std::string identity,
                                                                    std::uint64_t deadline) {
  v1::SubmitStimulationRequest request;
  request.set_session_id(std::string(kSessionIdentity));
  request.set_request_id(std::move(identity));
  request.mutable_action()->set_kind(kind);
  request.mutable_action()->set_action_id("action-1");
  request.mutable_action()->set_correlation_id("1000");
  request.set_target_endpoint(std::string(kTargetIdentity));
  request.set_contract_id(std::string(kContractIdentity));
  switch (kind) {
  case v1::STIMULATION_ACTION_INJECT_MESSAGE:
    request.set_interaction(v1::INTERACTION_KIND_MESSAGE);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  case v1::STIMULATION_ACTION_INVOKE_SERVICE:
    request.set_interaction(v1::INTERACTION_KIND_REQUEST);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  case v1::STIMULATION_ACTION_EMULATE_SERVICE:
    request.set_interaction(v1::INTERACTION_KIND_RESPONSE);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  case v1::STIMULATION_ACTION_INJECT_SIGNAL:
  default:
    request.set_interaction(v1::INTERACTION_KIND_SIGNAL);
    request.set_direction(v1::DIRECTION_OUTBOUND);
    break;
  }
  request.mutable_schedule()->set_mode(v1::SCHEDULE_IMMEDIATE);
  request.mutable_schedule()->set_clock_domain("clock.gateway");
  request.set_deadline_millis(deadline);
  return request;
}

/// @brief Builds a bounded `ArmSessionRequest`.
/// @param major Declared protocol major.
/// @param deadline Declared request deadline.
/// @return The bounded request.
[[nodiscard]] v1::ArmSessionRequest make_arm_request(std::uint32_t major, std::uint64_t deadline) {
  v1::ArmSessionRequest request;
  request.set_permit_id(std::string(kPermitIdentity));
  request.set_session_id(std::string(kSessionIdentity));
  request.set_plan_digest(std::string(kPlanIdentity));
  request.set_graph_digest(std::string(kGraphIdentity));
  request.mutable_protocol()->set_major(major);
  request.mutable_protocol()->set_minor(kClientSupportedMinor);
  request.set_validity_millis(1000U);
  request.set_deadline_millis(deadline);
  return request;
}

/// @brief Serializes one generated request message into a bounded string.
/// @param message Generated request message.
/// @return The serialized bytes.
[[nodiscard]] std::string serialize(const google::protobuf::MessageLite &message) {
  std::string bytes;
  static_cast<void>(message.SerializeToString(&bytes));
  return bytes;
}

/// @brief Sends one request frame and reads exactly one bounded response payload.
/// @param channel Connected local channel.
/// @param config Explicit client bounds.
/// @param method Exact committed method name.
/// @param message Serialized request message.
/// @param response Receives the response payload.
/// @return The bounded frame outcome.
[[nodiscard]] FrameResult exchange(const LocalClientChannel &channel,
                                  const SyntheticClientConfig &config, std::string_view method,
                                  const std::string &message, std::vector<std::byte> &response) {
  const std::vector<std::byte> frame = encode_request(method, message);
  if (frame.size() < 4U || frame.size() - 4U > config.max_message_bytes) {
    return FrameResult::error;
  }
  if (!channel.write_all(frame)) {
    return FrameResult::error;
  }
  return read_response_frame(channel, config, response);
}

/// @brief Parses one bounded response payload into a generated message.
/// @tparam Message Generated response type.
/// @param bytes Response payload.
/// @param out Receives the parsed message.
/// @return `true` when the payload parsed.
template <typename Message>
[[nodiscard]] bool parse_response(const std::vector<std::byte> &bytes, Message &out) {
  return out.ParseFromArray(bytes.data(), static_cast<int>(bytes.size()));
}

/// @brief Runs the descriptor self-test and writes the committed operation table.
/// @param writer Bounded result writer.
/// @return Bounded process status.
[[nodiscard]] int run_selftest(ResultWriter &writer) {
  const std::span<const std::string_view> table = synthetic_client_operation_names();
  for (const std::string_view name : table) {
    writer.write("operation", name);
  }
  const bool matches = operation_table_matches_descriptor();
  writer.write("selftest", matches ? "ok" : "mismatch");
  return matches ? 0 : 3;
}

/// @brief Runs one bounded local exchange exercise.
/// @details The named exercise is declared by the test harness through the bounded argument vector;
///          an unknown exercise fails closed without contacting a peer.
/// @param exercise Declared exercise label.
/// @param channel Connected local channel.
/// @param config Explicit client bounds.
/// @param writer Bounded result writer.
/// @return Bounded process status.
[[nodiscard]] int run_exercise(std::string_view exercise, const LocalClientChannel &channel,
                               const SyntheticClientConfig &config, ResultWriter &writer) {
  if (!channel.is_local_endpoint()) {
    writer.write("transport", "nonlocal_endpoint");
    return 4;
  }
  if (exercise == "version") {
    v1::QueryVersionRequest request;
    std::vector<std::byte> response;
    if (exchange(channel, config, "QueryVersion", serialize(request), response) !=
        FrameResult::ok) {
      writer.write("method", "QueryVersion");
      writer.write("outcome", "failed");
      return 0;
    }
    v1::QueryVersionResponse parsed;
    if (!parse_response(response, parsed)) {
      writer.write("method", "QueryVersion");
      writer.write("outcome", "failed");
      return 0;
    }
    writer.write("method", "QueryVersion");
    writer.write("outcome", "accepted");
    writer.write("size", static_cast<std::uint64_t>(parsed.protocol().major()));
    return 0;
  }
  if (exercise == "stall") {
    v1::QueryVersionRequest request;
    std::vector<std::byte> response;
    const FrameResult result = exchange(channel, config, "QueryVersion", serialize(request), response);
    writer.write("method", "QueryVersion");
    writer.write("outcome", result == FrameResult::ok ? "accepted" : "failed");
    writer.write("reason", result == FrameResult::timeout ? "transport_timeout" : "peer");
    return 0;
  }
  if (exercise == "observation" || exercise == "observation_stimulus") {
    v1::OpenObservationRequest open;
    open.set_tap_id("tap.client");
    open.set_max_records(8U);
    open.set_deadline_millis(config.request_deadline_millis);
    std::vector<std::byte> response;
    if (exchange(channel, config, "OpenObservation", serialize(open), response) != FrameResult::ok) {
      writer.write("method", "OpenObservation");
      writer.write("outcome", "failed");
      return 0;
    }
    v1::OpenObservationResponse opened;
    if (!parse_response(response, opened) || opened.stream_id().empty()) {
      writer.write("method", "OpenObservation");
      writer.write("outcome", "rejected");
      return 0;
    }
    writer.write("method", "OpenObservation");
    writer.write("outcome", "accepted");
    writer.write("size", static_cast<std::uint64_t>(opened.granted_max_records()));

    if (exercise == "observation_stimulus") {
      v1::ArmSessionRequest arm = make_arm_request(kClientSupportedMajor, config.request_deadline_millis);
      std::vector<std::byte> arm_response;
      if (exchange(channel, config, "ArmSession", serialize(arm), arm_response) != FrameResult::ok) {
        writer.write("method", "ArmSession");
        writer.write("outcome", "failed");
        return 0;
      }
      v1::ArmSessionResponse armed;
      if (!parse_response(arm_response, armed)) {
        writer.write("method", "ArmSession");
        writer.write("outcome", "failed");
        return 0;
      }
      writer.write("method", "ArmSession");
      writer.write("outcome", "accepted");
      writer.write("size", static_cast<std::uint64_t>(armed.state()));
      v1::SubmitStimulationRequest submit =
          make_stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "1", config.request_deadline_millis);
      std::vector<std::byte> submit_response;
      if (exchange(channel, config, "SubmitStimulation", serialize(submit), submit_response) !=
          FrameResult::ok) {
        writer.write("method", "SubmitStimulation");
        writer.write("outcome", "failed");
        return 0;
      }
      v1::SubmitStimulationResponse submitted;
      if (!parse_response(submit_response, submitted)) {
        writer.write("method", "SubmitStimulation");
        writer.write("outcome", "failed");
        return 0;
      }
      const bool emitted = submitted.outcome().kind() == v1::STIMULATION_OUTCOME_EMITTED;
      writer.write("method", "SubmitStimulation");
      writer.write("outcome", emitted ? "accepted" : "rejected");
      writer.write("size", emitted ? 1U : 0U);
    }

    v1::ReadObservationsRequest read;
    read.set_stream_id(opened.stream_id());
    read.set_max_records(opened.granted_max_records());
    read.set_deadline_millis(config.request_deadline_millis);
    const std::vector<std::byte> read_frame =
        encode_request("ReadObservations", serialize(read));
    if (!channel.write_all(read_frame)) {
      writer.write("method", "ReadObservations");
      writer.write("outcome", "failed");
      return 0;
    }
    std::uint64_t records = 0U;
    bool metadata_only = true;
    for (std::size_t step = 0U; step < kClientMaxReadFrames; ++step) {
      std::vector<std::byte> frame_payload;
      const FrameResult result = read_response_frame(channel, config, frame_payload);
      if (result == FrameResult::terminator) {
        break;
      }
      if (result != FrameResult::ok) {
        writer.write("method", "ReadObservations");
        writer.write("outcome", "failed");
        return 0;
      }
      v1::ObservationRecord record;
      if (!parse_response(frame_payload, record) ||
          record.payload_state() != v1::PAYLOAD_METADATA_ONLY || record.payload_bytes() != 0U ||
          !record.payload_view().empty()) {
        metadata_only = false;
      }
      ++records;
    }
    writer.write("method", "ReadObservations");
    writer.write("outcome", metadata_only ? "accepted" : "rejected");
    writer.write("size", records);
    writer.write("metadata", metadata_only ? records : 0U);

    v1::CloseObservationRequest close;
    close.set_stream_id(opened.stream_id());
    std::vector<std::byte> close_response;
    if (exchange(channel, config, "CloseObservation", serialize(close), close_response) !=
        FrameResult::ok) {
      writer.write("method", "CloseObservation");
      writer.write("outcome", "failed");
      return 0;
    }
    v1::CloseObservationResponse closed;
    if (!parse_response(close_response, closed)) {
      writer.write("method", "CloseObservation");
      writer.write("outcome", "failed");
      return 0;
    }
    writer.write("method", "CloseObservation");
    writer.write("outcome", "accepted");
    writer.write("size", closed.delivered());
    writer.write("dropped", closed.dropped());
    return 0;
  }
  if (exercise == "arm_reject" || exercise.rfind("stimulate_", 0U) == 0U ||
      exercise == "lease" || exercise == "query") {
    std::uint32_t major = kClientSupportedMajor;
    if (exercise == "arm_reject") {
      major = kClientSupportedMajor + 1U;
    }
    v1::ArmSessionRequest arm = make_arm_request(major, config.request_deadline_millis);
    std::vector<std::byte> arm_response;
    if (exchange(channel, config, "ArmSession", serialize(arm), arm_response) != FrameResult::ok) {
      writer.write("method", "ArmSession");
      writer.write("outcome", "failed");
      return 0;
    }
    v1::ArmSessionResponse armed;
    if (!parse_response(arm_response, armed)) {
      writer.write("method", "ArmSession");
      writer.write("outcome", "failed");
      return 0;
    }
    const bool armed_ok = armed.state() == v1::SESSION_ARMED;
    writer.write("method", "ArmSession");
    writer.write("outcome", armed_ok ? "accepted" : "rejected");
    writer.write("size", static_cast<std::uint64_t>(armed.state()));
    if (!armed_ok) {
      return 0;
    }
    if (exercise == "lease") {
      v1::AcquireLeaseRequest acquire;
      acquire.set_session_id(std::string(kSessionIdentity));
      acquire.set_endpoint_id("endpoint.alpha");
      acquire.set_endpoint_generation(1U);
      acquire.set_plan_digest(std::string(kPlanIdentity));
      acquire.set_lease_millis(1000U);
      acquire.set_deadline_millis(config.request_deadline_millis);
      std::vector<std::byte> acquire_response;
      if (exchange(channel, config, "AcquireLease", serialize(acquire), acquire_response) !=
          FrameResult::ok) {
        writer.write("method", "AcquireLease");
        writer.write("outcome", "failed");
        return 0;
      }
      v1::AcquireLeaseResponse acquired;
      if (!parse_response(acquire_response, acquired)) {
        writer.write("method", "AcquireLease");
        writer.write("outcome", "failed");
        return 0;
      }
      const bool held = acquired.state() == v1::LEASE_ACTIVE;
      writer.write("method", "AcquireLease");
      writer.write("outcome", held ? "accepted" : "rejected");
      writer.write("size", static_cast<std::uint64_t>(acquired.state()));
      v1::ReleaseLeaseRequest release;
      release.set_session_id(std::string(kSessionIdentity));
      release.set_lease_id(acquired.lease_id());
      release.set_reason_code("done");
      std::vector<std::byte> release_response;
      if (exchange(channel, config, "ReleaseLease", serialize(release), release_response) !=
          FrameResult::ok) {
        writer.write("method", "ReleaseLease");
        writer.write("outcome", "failed");
        return 0;
      }
      v1::ReleaseLeaseResponse released;
      if (!parse_response(release_response, released)) {
        writer.write("method", "ReleaseLease");
        writer.write("outcome", "failed");
        return 0;
      }
      writer.write("method", "ReleaseLease");
      writer.write("outcome", released.state() == v1::LEASE_RELEASED ? "accepted" : "rejected");
      writer.write("size", static_cast<std::uint64_t>(released.state()));
      return 0;
    }
    if (exercise == "query") {
      v1::QuerySessionRequest query;
      query.set_session_id(std::string(kSessionIdentity));
      std::vector<std::byte> query_response;
      if (exchange(channel, config, "QuerySession", serialize(query), query_response) !=
          FrameResult::ok) {
        writer.write("method", "QuerySession");
        writer.write("outcome", "failed");
        return 0;
      }
      v1::QuerySessionResponse queried;
      if (!parse_response(query_response, queried)) {
        writer.write("method", "QuerySession");
        writer.write("outcome", "failed");
        return 0;
      }
      writer.write("method", "QuerySession");
      writer.write("outcome", "accepted");
      writer.write("size", queried.counters().requests_received());
      return 0;
    }
    v1::StimulationActionKind kind = v1::STIMULATION_ACTION_INJECT_SIGNAL;
    if (exercise == "stimulate_message") {
      kind = v1::STIMULATION_ACTION_INJECT_MESSAGE;
    } else if (exercise == "stimulate_invoke") {
      kind = v1::STIMULATION_ACTION_INVOKE_SERVICE;
    } else if (exercise == "stimulate_emulate") {
      kind = v1::STIMULATION_ACTION_EMULATE_SERVICE;
    }
    v1::SubmitStimulationRequest submit =
        make_stimulation_request(kind, "1", config.request_deadline_millis);
    std::vector<std::byte> submit_response;
    if (exchange(channel, config, "SubmitStimulation", serialize(submit), submit_response) !=
        FrameResult::ok) {
      writer.write("method", "SubmitStimulation");
      writer.write("outcome", "failed");
      return 0;
    }
    v1::SubmitStimulationResponse submitted;
    if (!parse_response(submit_response, submitted)) {
      writer.write("method", "SubmitStimulation");
      writer.write("outcome", "failed");
      return 0;
    }
    const bool emitted = submitted.outcome().kind() == v1::STIMULATION_OUTCOME_EMITTED;
    writer.write("method", "SubmitStimulation");
    writer.write("outcome", emitted ? "accepted" : "rejected");
    writer.write("size", emitted ? 1U : 0U);
    return 0;
  }
  if (exercise == "roundtrip" || exercise == "roundtrip_unknown") {
    v1::ArmSessionRequest canonical = make_arm_request(kClientSupportedMajor, 1000U);
    std::string sent = serialize(canonical);
    if (exercise == "roundtrip_unknown") {
      // One bounded upstream unknown varint field (number 1500) appended to the wire bytes.
      std::uint64_t tag = (1500U << 3U);
      while (tag >= 0x80U) {
        sent.push_back(static_cast<char>((tag & 0x7FU) | 0x80U));
        tag >>= 7U;
      }
      sent.push_back(static_cast<char>(tag));
      sent.push_back(static_cast<char>(0x2AU));
    }
    std::vector<std::byte> response;
    if (exchange(channel, config, "ArmSession", sent, response) != FrameResult::ok) {
      writer.write("roundtrip", "failed");
      return 0;
    }
    std::string returned(reinterpret_cast<const char *>(response.data()), response.size());
    writer.write("roundtrip", returned == sent ? "match" : "mismatch");
    return 0;
  }
  writer.write("exercise", "unknown");
  return 5;
}

/// @brief Runs one bounded over-bound local rejection without contacting a peer.
/// @details The declared bound is exercised against a genuinely over-bound request before the
///          rejection is reported; an unexpectedly in-bound value fails the client closed.
/// @param over_message Whether the declared message bound is exceeded.
/// @param config Explicit client bounds.
/// @param writer Bounded result writer.
/// @return Bounded process status.
[[nodiscard]] int run_over_bound(bool over_message, const SyntheticClientConfig &config,
                                 ResultWriter &writer) {
  if (over_message) {
    v1::SubmitStimulationRequest request =
        make_stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "1",
                                 config.request_deadline_millis);
    request.set_payload(std::string(config.max_message_bytes, 'x'));
    const std::vector<std::byte> frame = encode_request("SubmitStimulation", serialize(request));
    if (frame.size() < 4U || frame.size() - 4U <= config.max_message_bytes) {
      writer.write("method", "SubmitStimulation");
      writer.write("outcome", "failed");
      writer.write("reason", "bound_not_exceeded");
      return 6;
    }
    writer.write("method", "SubmitStimulation");
    writer.write("outcome", "rejected");
    writer.write("reason", "over_message_bound");
    writer.write("size", static_cast<std::uint64_t>(frame.size() - 4U));
    return 0;
  }
  const std::uint64_t declared_deadline = config.request_deadline_millis + 1U;
  if (declared_deadline <= config.request_deadline_millis) {
    writer.write("method", "SubmitStimulation");
    writer.write("outcome", "failed");
    writer.write("reason", "bound_not_exceeded");
    return 6;
  }
  v1::SubmitStimulationRequest request =
      make_stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "1", declared_deadline);
  if (request.deadline_millis() <= config.request_deadline_millis) {
    writer.write("method", "SubmitStimulation");
    writer.write("outcome", "failed");
    writer.write("reason", "bound_not_exceeded");
    return 6;
  }
  writer.write("method", "SubmitStimulation");
  writer.write("outcome", "rejected");
  writer.write("reason", "over_deadline_bound");
  writer.write("size", request.deadline_millis());
  return 0;
}

}  // namespace xverse::xcom::synthetic

/**
 * @brief Bounded process entry point.
 * @param argc Explicit bounded argument count.
 * @param argv Explicit bounded argument vector:
 *             `<local_path> <exercise> <max_message_bytes> <request_deadline_millis>
 *              <transport_timeout_millis> <result_path>`.
 * @return Bounded process status; zero when the declared exercise ran and reported, non-zero when
 *         the client failed closed before or during the declared exercise.
 */
int synthetic_client_run(int argc, char **argv) noexcept {
  using namespace xverse::xcom::synthetic;
  if (argc < 7) {
    return 1;
  }
  const std::string_view local_path(argv[1]);
  const std::string_view exercise(argv[2]);
  const std::string result_path(argv[6]);
  ResultWriter writer(result_path);
  if (!writer.ok()) {
    return 1;
  }
  const std::optional<SyntheticClientConfig> config =
      make_client_config(argv[3], argv[4], argv[5]);
  if (!config.has_value()) {
    writer.write("config", "rejected");
    return 2;
  }
  if (exercise == "selftest") {
    return run_selftest(writer);
  }
  if (exercise == "over_message") {
    return run_over_bound(true, *config, writer);
  }
  if (exercise == "over_deadline") {
    return run_over_bound(false, *config, writer);
  }
  const std::optional<LocalClientChannel> channel =
      LocalClientChannel::connect(local_path, config->transport_timeout_millis);
  if (!channel.has_value()) {
    writer.write("transport", "connect_failed");
    return 0;
  }
  return run_exercise(exercise, *channel, *config, writer);
}

/**
 * @brief Process entry point.
 * @param argc Argument count.
 * @param argv Argument vector.
 * @return The bounded synthetic-client status.
 */
int main(int argc, char **argv) {
  return synthetic_client_run(argc, argv);
}
