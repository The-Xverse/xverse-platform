/**
 * @file synthetic_client_support.hpp
 * @brief T032 bounded, payload-free, test-local support for the separate-process synthetic client:
 *        the bounded single-peer server harness over the accepted T031 `GatewaySession`, the
 *        separate-process launcher, and the bounded result parser.
 * @details This header is T032-local and is not the T033 reusable contract-suite abstraction. It
 *          owns one bounded `AF_UNIX` endpoint under the build-tree scratch directory, launches the
 *          owned `xverse_xcom_synthetic_client` fixture with an explicit bounded argument vector and
 *          a scrubbed admitted environment, serves one peer through the accepted T031 session, and
 *          parses the client's bounded payload-free result lines. It never prints a host path into
 *          public evidence, contacts no external peer, and reads no legacy artifact.
 * @ownership The harness owns its endpoint and its captured result lines; the accepted
 *            `GatewayFixture` and `GatewaySession` remain owned by the owning case and must outlive
 *            the harness call.
 * @lifetime The endpoint and captured lines live for the harness call; the launched child is reaped
 *           within a bounded wait before return.
 * @thread_safety One declared user; the harness serves exactly one peer at a time. No thread is
 *                created; the child process is launched before the single-threaded serve loop.
 * @bounds One socket, one peer, <= 32 request frames per case, <= 8 published observation records
 *         per case, one bounded result file, no retained payload byte, no wall-clock verdict.
 * @failure A failed bind, launch, accept, decode, or reap fails the owning case closed; the harness
 *          never weakens an accepted check and never reports an unknown outcome as success.
 * @par Traceability
 * Supports T032-SR-001 through T032-SR-021 and the T32-TS-001..T32-TS-022 cases.
 */

#ifndef XVERSE_XCOM_SYNTHETIC_CLIENT_SUPPORT_HPP_
#define XVERSE_XCOM_SYNTHETIC_CLIENT_SUPPORT_HPP_

#ifndef XCOM_T032_SYNTHETIC_CLIENT_PATH
#error "T032 tests require the bounded XCOM_T032_SYNTHETIC_CLIENT_PATH definition"
#endif
#ifndef XCOM_T032_SCRATCH_DIR
#error "T032 tests require the bounded XCOM_T032_SCRATCH_DIR definition"
#endif
// The accepted T031 test fixture declares an inline scratch helper that names its own build-tree
// macro. The T032 suites reuse the accepted helper values but own the bounded T032 scratch path, so
// the accepted macro is aliased to the T032 scratch directory without changing the accepted header.
#ifndef XCOM_T031_SCRATCH_DIR
#define XCOM_T031_SCRATCH_DIR XCOM_T032_SCRATCH_DIR
#endif

#include "gateway_support.hpp"

#include "xverse/xcom/tool_gateway.hpp"

#include <array>
#include <csignal>
#include <cstddef>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <map>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include <poll.h>
#include <sys/wait.h>
#include <unistd.h>

namespace xverse::xcom::tool_gateway_test {

/// @brief Maximum request frames served for one case.
inline constexpr std::size_t kClientMaxServedRequests = 32U;
/// @brief Maximum observation records granted into one bounded read.
inline constexpr std::size_t kClientMaxGrantedRecords = 8U;
/// @brief Bounded accept wait for a well-behaved separate-process peer.
inline constexpr std::uint64_t kClientAcceptTimeoutMillis = 2000U;
/// @brief Bounded accept wait when the declared exercise contacts no peer.
inline constexpr std::uint64_t kClientNoPeerTimeoutMillis = 300U;
/// @brief Bounded transport wait used by the silence and timeout cases.
inline constexpr std::uint64_t kClientSilentTimeoutMillis = 2000U;
/// @brief Bounded sink capacity retained by the T032 capture.
inline constexpr std::size_t kClientLogCaptureBound = 32U;

/**
 * @brief T032-local bounded emission recorder that preserves the accepted synthetic origin.
 * @ownership Owns fixed counters and one recorded origin; retains no payload byte.
 * @lifetime Outlives the action path that references it.
 * @thread_safety Single declared user per case.
 * @failure Never throws; records only the accepted item metadata and the call-scoped payload size.
 */
class ProvenanceEmitter final : public val::ActionEmitter {
 public:
  /// @brief Delivers one descriptor and records its accepted synthetic origin.
  /// @param item Accepted synthetic descriptor carrying the declared provenance.
  /// @param payload Call-scoped payload view; only its size is recorded.
  /// @return `Delivered`, the only success outcome.
  val::EmissionStatus emit(const val::SyntheticStimulationItem &item,
                           std::span<const std::byte> payload) override {
    ++calls;
    last_origin = item.origin;
    last_request_id = item.intent.request_id;
    last_payload_size = payload.size();
    return val::EmissionStatus::Delivered;
  }

  /// @brief Number of emission calls.
  std::size_t calls{0U};
  /// @brief Origin carried by the most recent accepted descriptor.
  OriginKind last_origin{OriginKind::component};
  /// @brief Most recent emitted request identity.
  std::uint64_t last_request_id{0U};
  /// @brief Most recent call-scoped payload size.
  std::size_t last_payload_size{0U};
};

/**
 * @brief T032-local bounded composing fixture over the accepted in-process boundaries.
 * @details This fixture mirrors the accepted T031 test-local composition but owns a T032-local
 *          emission recorder so the separate-process stimulation cases can assert the accepted
 *          persistent synthetic provenance. It reuses the accepted T031 test helper values and
 *          weakens no accepted check. It is T032-local and is not the T033 reusable abstraction.
 * @ownership Owns its manager, clock, storage, journal, registry, emitter, action path, hub, and
 *            bounded log capture.
 * @lifetime Every referenced component outlives the gateway session under test.
 * @thread_safety One declared user per case.
 * @failure An unavailable or unopened component leaves `ready()` false and fails the case.
 */
class SyntheticClientFixture final {
 public:
  /// @brief Constructs the fixture and binds the accepted boundaries.
  SyntheticClientFixture() : config_(make_config()) {
    val::ManagerConfig manager_config;
    manager_config.scope = manager_scope();
    manager_.emplace(manager_config);
    ready_ = manager_->register_controller(controller_identity(), "gateway-controller") ==
             val::Result::Ok;
    ready_ = ready_ &&
             manager_->time_authority().declare_clock(kDomain, clock_.source(),
                                                      val::ClockKind::WallClock, -1000000, 1000000) ==
                 val::Result::Ok;
    permit_ = make_permit();
    binding_.permit_id = std::string(kPermitId);
    binding_.session_id = std::string(kSessionId);
    binding_.plan_digest = std::string(kPlanDigest);
    binding_.graph_digest = std::string(kGraphDigest);
    binding_.permit = permit_;
    binding_.has_permit = true;
    binding_.controller = controller_identity();
    binding_.context = context_for(permit_);
    binding_.arrival_domain = kDomain;
    binding_.arrival_domain_name = "clock.gateway";
    binding_.arrival_tick = clock_.get();
    binding_.service_owner = val::ServiceOwner{tag("svc.alpha"), 3U, true};
    binding_.blueprint_id = "gateway.blueprint";
    binding_.contract_id = "gateway.contract";
    bind();
  }

  /// @brief Copy construction is deleted; the fixture owns a mutex-bearing manager.
  SyntheticClientFixture(const SyntheticClientFixture &) = delete;
  /// @brief Copy assignment is deleted.
  SyntheticClientFixture &operator=(const SyntheticClientFixture &) = delete;

  /// @brief Opens the accepted journal and action path over the fixture components.
  /// @return `true` when the journal and guard both opened.
  bool open_path() {
    val::JournalConfig journal_config;
    journal_config.max_record_bytes = 320U;
    journal_config.max_retained_records = 32U;
    journal_config.max_journal_bytes = 16U * 1024U;
    ready_ = ready_ && journal_.open(storage_, journal_config) == val::JournalStatus::Ok;
    val::ActionPathConfig action_config;
    action_config.max_pending_actions = 8U;
    action_config.max_lineage_entries = 8U;
    action_config.max_drain_steps = 8U;
    action_config.max_payload_bytes = 64U;
    action_config.late_tolerance = 100;
    action_config.tool = tag("tool");
    path_.emplace(action_config, journal_, registry_, emitter_);
    ready_ = ready_ && path_->open(permit_, make_policy(permit_)) == val::GuardStatus::Ok;
    bind();
    return ready_;
  }

  /// @brief Points the dependency bundle at the owned accepted boundaries.
  void bind() {
    dependencies_.sessions = manager_.has_value() ? &*manager_ : nullptr;
    dependencies_.time_authority = manager_.has_value() ? &manager_->time_authority() : nullptr;
    dependencies_.journal = &journal_;
    dependencies_.guard = nullptr;
    dependencies_.actions = path_.has_value() ? &*path_ : nullptr;
    dependencies_.leases = &registry_;
    dependencies_.observations = &hub_;
    dependencies_.log = &log_;
  }

  /// @brief Returns the validated gateway configuration.
  [[nodiscard]] const GatewayConfig &config() const noexcept { return config_; }
  /// @brief Returns the dependency bundle.
  [[nodiscard]] const GatewayDependencies &dependencies() const noexcept { return dependencies_; }
  /// @brief Returns the resolved session binding.
  [[nodiscard]] GatewaySessionBinding binding() const { return binding_; }
  /// @brief Returns the manual declared clock.
  [[nodiscard]] ManualClock &clock() noexcept { return clock_; }
  /// @brief Returns the recording emitter.
  [[nodiscard]] ProvenanceEmitter &emitter() noexcept { return emitter_; }
  /// @brief Returns the bounded log capture.
  [[nodiscard]] LogCapture &log() noexcept { return log_; }
  /// @brief Returns the accepted observation hub.
  [[nodiscard]] ObservationHub &hub() noexcept { return hub_; }
  /// @brief Reports whether every bounded component is ready.
  [[nodiscard]] bool ready() const noexcept { return ready_; }

 private:
  GatewayConfig config_;
  ManualClock clock_{0};
  std::optional<val::SessionManager> manager_{};
  val::Permit permit_{};
  GatewaySessionBinding binding_{};
  GatewayDependencies dependencies_{};
  InMemoryStorage storage_{};
  val::StimulationJournal journal_{};
  val::ServiceEmulationRegistry registry_{4U};
  ProvenanceEmitter emitter_{};
  std::optional<val::StimulationActionPath> path_{};
  ObservationHub hub_{};
  LogCapture log_{};
  bool ready_{false};
};


/// @brief Declared bounded server behavior for one separate-process case.
enum class ClientServerMode : std::uint8_t {
  dispatch, ///< Decode and dispatch each frame through the accepted gateway session.
  echo,     ///< Return the parsed generated request message unchanged (contract fidelity).
  silent,   ///< Accept the peer and never respond (bounded transport-timeout stimulus).
  none,     ///< Serve no peer (the declared exercise contacts no peer).
};

/// @brief Bounded observed result of one separate-process client case.
struct ClientRunResult final {
  /// @brief Bounded child exit status (`-1` when the child could not be reaped).
  int exit_status{-1};
  /// @brief Captured bounded payload-free result lines.
  std::vector<std::string> lines;
  /// @brief Request frames served through the accepted session.
  std::size_t requests_served{0U};
  /// @brief Whether a separate-process peer was accepted.
  bool peer_accepted{false};
};

/// @brief Returns one bounded build-tree scratch socket path.
/// @param name Bounded file name.
/// @return The scratch path.
[[nodiscard]] inline std::string client_scratch_path(std::string_view name) {
  const std::string directory = XCOM_T032_SCRATCH_DIR;
  ::mkdir(directory.c_str(), 0700);
  return directory + "/" + std::string(name);
}

/// @brief Returns the fields of one bounded `key=value` result line.
/// @param line Bounded result line.
/// @return Key to value map; an unparsable token is skipped.
[[nodiscard]] inline std::map<std::string, std::string> parse_fields(const std::string &line) {
  std::map<std::string, std::string> fields;
  std::size_t start = 0U;
  while (start < line.size()) {
    while (start < line.size() && (line[start] == ' ' || line[start] == '\n')) {
      ++start;
    }
    const std::size_t end = line.find(' ', start);
    const std::string token = line.substr(start, end == std::string::npos ? std::string::npos : end - start);
    const std::size_t separator = token.find('=');
    if (separator != std::string::npos) {
      fields[token.substr(0U, separator)] = token.substr(separator + 1U);
    }
    if (end == std::string::npos) {
      break;
    }
    start = end + 1U;
  }
  return fields;
}

/// @brief Groups the client's bounded key/value lines into logical result records.
/// @details The client emits one `key=value` token per line. A new record begins at every `method=`
///          token; single-token records (`selftest`, `roundtrip`, `transport`, `config`) remain one
///          record.
/// @param result Bounded captured result.
/// @return Joined records, in write order.
[[nodiscard]] inline std::vector<std::string> join_result_records(const ClientRunResult &result) {
  std::vector<std::string> records;
  std::string current;
  for (const std::string &line : result.lines) {
    if (line.empty()) {
      continue;
    }
    if (line.find("method=") != std::string::npos && !current.empty()) {
      records.push_back(current);
      current.clear();
    }
    if (!current.empty()) {
      current.push_back(' ');
    }
    current += line;
  }
  if (!current.empty()) {
    records.push_back(current);
  }
  return records;
}

/// @brief Returns the first captured result record whose `method` field equals `method`.
/// @param result Bounded captured result.
/// @param method Exact committed method name.
/// @return The matching joined record, or an empty string when absent.
[[nodiscard]] inline std::string find_method_line(const ClientRunResult &result,
                                                  std::string_view method) {
  for (const std::string &record : join_result_records(result)) {
    const std::map<std::string, std::string> fields = parse_fields(record);
    const auto found = fields.find("method");
    if (found != fields.end() && found->second == method) {
      return record;
    }
  }
  return {};
}

/// @brief Returns the last captured result record whose `method` field equals `method`.
/// @param result Bounded captured result.
/// @param method Exact committed method name.
/// @return The matching joined record, or an empty string when absent.
[[nodiscard]] inline std::string find_last_method_line(const ClientRunResult &result,
                                                       std::string_view method) {
  std::string match;
  for (const std::string &record : join_result_records(result)) {
    const std::map<std::string, std::string> fields = parse_fields(record);
    const auto found = fields.find("method");
    if (found != fields.end() && found->second == method) {
      match = record;
    }
  }
  return match;
}

/// @brief Returns one named field of a result line.
/// @param line Bounded result line.
/// @param key Field key.
/// @return The value, or an empty string when absent.
[[nodiscard]] inline std::string field_value(const std::string &line, std::string_view key) {
  const std::map<std::string, std::string> fields = parse_fields(line);
  const auto found = fields.find(std::string(key));
  return found == fields.end() ? std::string{} : found->second;
}

/// @brief Returns the first captured line containing `<key>=`.
/// @param result Bounded captured result.
/// @param key Exact field key.
/// @return The matching line, or an empty string when absent.
[[nodiscard]] inline std::string find_first_line(const ClientRunResult &result,
                                                 std::string_view key) {
  const std::string prefix = std::string(key) + "=";
  for (const std::string &line : result.lines) {
    if (line.find(prefix) != std::string::npos) {
      return line;
    }
  }
  return {};
}

/// @brief Bounded raw read of exactly `length` bytes with a bounded wait.
/// @param fd Connected descriptor.
/// @param length Bounded byte count.
/// @param timeout_millis Bounded wait.
/// @param out Receives the bytes on success.
/// @return `true` when every byte arrived.
[[nodiscard]] inline bool harness_read_exact(int fd, std::size_t length,
                                             std::uint64_t timeout_millis,
                                             std::vector<std::byte> &out) {
  out.assign(length, std::byte{0});
  std::size_t read = 0U;
  while (read < length) {
    struct pollfd wait {};
    wait.fd = fd;
    wait.events = POLLIN;
    const int ready = ::poll(&wait, 1, static_cast<int>(timeout_millis));
    if (ready <= 0) {
      return false;
    }
    const ssize_t count = ::read(fd, out.data() + read, length - read);
    if (count <= 0) {
      return false;
    }
    read += static_cast<std::size_t>(count);
  }
  return true;
}

/// @brief Bounded raw write of a complete byte span.
/// @param fd Connected descriptor.
/// @param bytes Bounded source.
/// @return `true` when every byte was written.
[[nodiscard]] inline bool harness_write_all(int fd, std::span<const std::byte> bytes) {
  std::size_t written = 0U;
  while (written < bytes.size()) {
    const ssize_t count = ::write(fd, bytes.data() + written, bytes.size() - written);
    if (count <= 0) {
      return false;
    }
    written += static_cast<std::size_t>(count);
  }
  return true;
}

/// @brief Writes one bounded response frame (4-byte big-endian length then payload).
/// @param fd Connected descriptor.
/// @param payload Bounded response payload; empty writes a zero-length terminator.
/// @return `true` when the frame was written.
[[nodiscard]] inline bool write_response_frame(int fd, std::span<const std::byte> payload) {
  const std::uint32_t length = static_cast<std::uint32_t>(payload.size());
  const std::array<std::byte, 4U> prefix = {
      static_cast<std::byte>((length >> 24U) & 0xFFU),
      static_cast<std::byte>((length >> 16U) & 0xFFU),
      static_cast<std::byte>((length >> 8U) & 0xFFU),
      static_cast<std::byte>(length & 0xFFU),
  };
  return harness_write_all(fd, prefix) && harness_write_all(fd, payload);
}

/// @brief Writes one serialized generated message as a bounded response frame.
/// @param fd Connected descriptor.
/// @param message Generated response message.
/// @return `true` when the frame was written.
[[nodiscard]] inline bool write_message_frame(int fd,
                                              const google::protobuf::MessageLite &message) {
  std::string bytes;
  static_cast<void>(message.SerializeToString(&bytes));
  const auto *data = reinterpret_cast<const std::byte *>(bytes.data());
  return write_response_frame(fd, std::span<const std::byte>(data, bytes.size()));
}

/// @brief Builds one bounded provider-neutral observation item for the fixture hub.
/// @return A valid item carrying no payload byte.
[[nodiscard]] inline CommunicationItem make_observation_item() {
  const auto contract_result = CommunicationContract::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "schema.alpha", "2.0.1",
       InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume});
  const CommunicationContract contract = *contract_result.value();
  const auto item_result = CommunicationItem::create(
      {"contract.alpha", "1.2.3", "interface.alpha", "endpoint.alpha", "schema.alpha", "2.0.1",
       InteractionKind::message_event, OriginKind::validation_tool, Timestamp(42), "clock.source",
       "correlation.alpha", "causation.alpha", "route.alpha", "provider.alpha",
       std::span<const std::byte>{}},
      contract);
  return *item_result.value();
}

/// @brief Publishes a bounded number of metadata-only observation records to the fixture hub.
/// @param hub Accepted observation hub.
/// @param count Bounded record count.
/// @return The number of records accepted into the bounded tap.
[[nodiscard]] inline std::size_t publish_records(ObservationHub &hub, std::size_t count) {
  const CommunicationItem item = make_observation_item();
  std::size_t accepted = 0U;
  for (std::size_t index = 0U; index < count; ++index) {
    auto reservation = hub.reserve(item);
    if (!reservation.status.succeeded() || !reservation.reservation.has_value()) {
      break;
    }
    const std::uint64_t sequence = static_cast<std::uint64_t>(index) + 1U;
    if (hub.commit(std::move(*reservation.reservation),
                   {item, Timestamp(static_cast<std::int64_t>(sequence)), "clock.observer", sequence,
                    ObservationProviderOutcome::accepted})
            .succeeded()) {
      ++accepted;
    }
  }
  return accepted;
}

/// @brief Bounded separate-process launcher.
/// @ownership Forks exactly one owned fixture child and reaps it within a bounded wait.
/// @lifetime The child is reaped before return; no descriptor is retained.
/// @thread_safety Must be called from the single-threaded test process.
/// @failure A failed fork or exec leaves a bounded non-zero status; the parent never blocks
///          unboundedly.
class SyntheticClientLauncher final {
 public:
  /// @brief Launches the owned fixture client with an explicit bounded argument vector.
  /// @param exercise Declared exercise label.
  /// @param socket_path Bounded local endpoint path.
  /// @param result_path Bounded result file path.
  /// @param max_message Declared maximum message size.
  /// @param deadline Declared per-request deadline.
  /// @param timeout Declared transport timeout.
  /// @return The child process identifier on success.
  [[nodiscard]] static std::optional<pid_t>
  launch(std::string_view exercise, const std::string &socket_path, const std::string &result_path,
         std::size_t max_message, std::uint64_t deadline, std::uint64_t timeout) {
    const std::string executable = XCOM_T032_SYNTHETIC_CLIENT_PATH;
    const pid_t child = ::fork();
    if (child < 0) {
      return std::nullopt;
    }
    if (child == 0) {
      std::vector<std::string> owned = {
          executable,
          socket_path,
          std::string(exercise),
          std::to_string(max_message),
          std::to_string(deadline),
          std::to_string(timeout),
          result_path,
      };
      std::vector<char *> argv;
      argv.reserve(owned.size() + 1U);
      for (std::string &argument : owned) {
        argv.push_back(argument.data());
      }
      argv.push_back(nullptr);
      char *const environment[] = {nullptr};
      ::execve(executable.c_str(), argv.data(), environment);
      ::_exit(127);
    }
    return child;
  }

  /// @brief Reaps one child within a bounded wait, terminating it if necessary.
  /// @param child Child process identifier.
  /// @return The bounded exit status.
  [[nodiscard]] static int reap(pid_t child) noexcept {
    for (std::size_t attempt = 0U; attempt < 400U; ++attempt) {
      int status = 0;
      const pid_t observed = ::waitpid(child, &status, WNOHANG);
      if (observed == child) {
        if (WIFEXITED(status)) {
          return WEXITSTATUS(status);
        }
        if (WIFSIGNALED(status)) {
          return 128 + WTERMSIG(status);
        }
        return -1;
      }
      if (observed < 0) {
        return -1;
      }
      struct timespec pause {};
      pause.tv_nsec = 5'000'000L;
      static_cast<void>(::nanosleep(&pause, nullptr));
    }
    static_cast<void>(::kill(child, SIGKILL));
    int status = 0;
    static_cast<void>(::waitpid(child, &status, 0));
    return -1;
  }
};

/// @brief Reads the bounded payload-free result lines written by one client run.
/// @param path Bounded result file path.
/// @return The captured lines, in write order.
[[nodiscard]] inline std::vector<std::string> read_result_lines(const std::string &path) {
  std::vector<std::string> lines;
  std::ifstream stream(path);
  std::string line;
  while (std::getline(stream, line) && lines.size() < 256U) {
    lines.push_back(line);
  }
  return lines;
}

/// @brief Runs one bounded separate-process client case against the accepted session.
/// @param session Accepted gateway session served for the case.
/// @param config Validated bounded gateway configuration.
/// @param hub Accepted observation hub used for bounded published records.
/// @param socket_name Bounded scratch socket file name.
/// @param exercise Declared exercise label.
/// @param mode Bounded server behavior.
/// @param max_message Declared maximum message size.
/// @param deadline Declared per-request deadline.
/// @param timeout Declared transport timeout.
/// @param publish_after_open Records published after an accepted observation open.
/// @param publish_after_stimulation Records published after an emitted stimulation.
/// @return The bounded observed result of the case.
[[nodiscard]] inline ClientRunResult
run_client_case(GatewaySession &session, const GatewayConfig &config, ObservationHub &hub,
                std::string_view socket_name, std::string_view exercise, ClientServerMode mode,
                std::size_t max_message, std::uint64_t deadline, std::uint64_t timeout,
                std::size_t publish_after_open = 0U, std::size_t publish_after_stimulation = 0U) {
  ClientRunResult result{};
  const std::string socket_path = client_scratch_path(socket_name);
  const std::string result_path = client_scratch_path(std::string(socket_name) + ".result");
  static_cast<void>(::unlink(result_path.c_str()));
  const std::optional<LocalIpcEndpoint> endpoint = LocalIpcEndpoint::create(config, socket_path);
  if (!endpoint.has_value()) {
    return result;
  }
  // The parent owns the accepted session; it performs the declared supported-major negotiation
  // before serving exactly one peer. The client's own declared protocol major is carried on the
  // wire and evaluated fail-closed by the accepted session on the first operation.
  v1::ProtocolVersion negotiated_peer{};
  negotiated_peer.set_major(kGatewaySupportedMajor);
  negotiated_peer.set_minor(kGatewaySupportedMinor);
  static_cast<void>(session.negotiate(negotiated_peer));
  const std::optional<pid_t> child =
      SyntheticClientLauncher::launch(exercise, socket_path, result_path, max_message, deadline, timeout);
  if (!child.has_value()) {
    return result;
  }
  const std::uint64_t accept_timeout =
      mode == ClientServerMode::none ? kClientNoPeerTimeoutMillis : kClientAcceptTimeoutMillis;
  int peer = -1;
  for (std::size_t attempt = 0U; attempt < 400U && peer < 0; ++attempt) {
    struct pollfd wait {};
    wait.fd = endpoint->listen_fd();
    wait.events = POLLIN;
    const int ready = ::poll(&wait, 1, static_cast<int>(accept_timeout));
    if (ready > 0) {
      peer = endpoint->accept_one();
      break;
    }
    break;
  }
  result.peer_accepted = peer >= 0;
  if (peer >= 0) {
    if (mode == ClientServerMode::silent) {
      std::vector<std::byte> buffer;
      while (harness_read_exact(peer, 1U, kClientSilentTimeoutMillis, buffer)) {
      }
    } else {
      for (std::size_t step = 0U; step < kClientMaxServedRequests; ++step) {
        std::vector<std::byte> prefix;
        if (!harness_read_exact(peer, 4U, kClientSilentTimeoutMillis, prefix)) {
          break;
        }
        const std::uint32_t length = (static_cast<std::uint32_t>(prefix[0]) << 24U) |
                                     (static_cast<std::uint32_t>(prefix[1]) << 16U) |
                                     (static_cast<std::uint32_t>(prefix[2]) << 8U) |
                                     static_cast<std::uint32_t>(prefix[3]);
        if (length == 0U || length > config.max_message_bytes()) {
          break;
        }
        std::vector<std::byte> body;
        if (!harness_read_exact(peer, length, kClientSilentTimeoutMillis, body)) {
          break;
        }
        std::vector<std::byte> frame;
        frame.reserve(4U + body.size());
        frame.insert(frame.end(), prefix.begin(), prefix.end());
        frame.insert(frame.end(), body.begin(), body.end());
        GatewayFrameView view{};
        if (gateway_decode_request_frame(config, frame, view) != GatewayFrameStatus::ok) {
          break;
        }
        ++result.requests_served;
        if (mode == ClientServerMode::echo) {
          v1::ArmSessionRequest parsed;
          if (!parsed.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          if (!write_message_frame(peer, parsed)) {
            break;
          }
          continue;
        }
        const std::string method(view.method);
        if (method == "QueryVersion") {
          v1::QueryVersionRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          if (!write_message_frame(peer, session.QueryVersion(request))) {
            break;
          }
        } else if (method == "OpenObservation") {
          v1::OpenObservationRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          const v1::OpenObservationResponse response = session.OpenObservation(request);
          if (!write_message_frame(peer, response)) {
            break;
          }
          if (!response.stream_id().empty() && publish_after_open > 0U) {
            static_cast<void>(publish_records(hub, publish_after_open));
          }
        } else if (method == "ReadObservations") {
          v1::ReadObservationsRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          std::array<v1::ObservationRecord, kClientMaxGrantedRecords> records{};
          const std::size_t written = session.ReadObservations(request, records);
          bool ok = true;
          for (std::size_t index = 0U; index < written; ++index) {
            if (!write_message_frame(peer, records[index])) {
              ok = false;
              break;
            }
          }
          if (!ok || !write_response_frame(peer, {})) {
            break;
          }
        } else if (method == "CloseObservation") {
          v1::CloseObservationRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          if (!write_message_frame(peer, session.CloseObservation(request))) {
            break;
          }
        } else if (method == "ArmSession") {
          v1::ArmSessionRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          if (!write_message_frame(peer, session.ArmSession(request))) {
            break;
          }
        } else if (method == "SubmitStimulation") {
          v1::SubmitStimulationRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          const v1::SubmitStimulationResponse response = session.SubmitStimulation(request);
          const bool emitted = response.outcome().kind() == v1::STIMULATION_OUTCOME_EMITTED;
          if (!write_message_frame(peer, response)) {
            break;
          }
          if (emitted && publish_after_stimulation > 0U) {
            static_cast<void>(publish_records(hub, publish_after_stimulation));
          }
        } else if (method == "AcquireLease") {
          v1::AcquireLeaseRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          if (!write_message_frame(peer, session.AcquireLease(request))) {
            break;
          }
        } else if (method == "ReleaseLease") {
          v1::ReleaseLeaseRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          if (!write_message_frame(peer, session.ReleaseLease(request))) {
            break;
          }
        } else if (method == "QuerySession") {
          v1::QuerySessionRequest request;
          if (!request.ParseFromArray(view.payload.data(), static_cast<int>(view.payload.size()))) {
            break;
          }
          if (!write_message_frame(peer, session.QuerySession(request))) {
            break;
          }
        } else {
          break;
        }
      }
    }
    ::close(peer);
  }
  result.exit_status = SyntheticClientLauncher::reap(*child);
  result.lines = read_result_lines(result_path);
  return result;
}

}  // namespace xverse::xcom::tool_gateway_test

#endif  // XVERSE_XCOM_SYNTHETIC_CLIENT_SUPPORT_HPP_
