#include "gateway_support.hpp"
#include "xverse/xcom/tool_gateway_grpc.hpp"

#include <gtest/gtest.h>

#include <chrono>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <thread>

#include <sys/stat.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <unistd.h>

namespace {
namespace v1 = xverse::xcom::v1;
using xverse::xcom::GatewayGrpcServer;
using xverse::xcom::GatewayGrpcService;
using xverse::xcom::GatewaySession;
using xverse::xcom::tool_gateway_test::GatewayFixture;
using xverse::xcom::tool_gateway_test::arm_request;
using xverse::xcom::tool_gateway_test::stimulation_request;

int serve(const char *path) {
  GatewayFixture fixture;
  if (!fixture.ready() || !fixture.open_path()) {
    return 2;
  }
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  GatewayGrpcService service(session, fixture.config());
  auto server = GatewayGrpcServer::start(path, service, fixture.config().max_message_bytes());
  if (!server) {
    return 3;
  }
  server->wait();
  return 0;
}

class ServerProcess final {
 public:
  ServerProcess() {
    char directory[] = "/tmp/xcom-grpc-XXXXXX";
    char *created = ::mkdtemp(directory);
    if (created == nullptr) {
      return;
    }
    directory_ = created;
    path_ = directory_ + "/gateway.sock";
    child_ = ::fork();
    if (child_ == 0) {
      static_cast<void>(::prctl(PR_SET_PDEATHSIG, SIGTERM));
      ::execl("/proc/self/exe", "/proc/self/exe", "--xcom-grpc-server",
              path_.c_str(), static_cast<char *>(nullptr));
      ::_exit(127);
    }
    if (child_ < 0) {
      return;
    }
    channel_ = grpc::CreateChannel("unix://" + path_, grpc::InsecureChannelCredentials());
    connected_ = channel_->WaitForConnected(std::chrono::system_clock::now() +
                                             std::chrono::seconds(3));
  }

  ~ServerProcess() {
    if (child_ > 0) {
      ::kill(child_, SIGTERM);
      int status = 0;
      static_cast<void>(::waitpid(child_, &status, 0));
    }
    if (!path_.empty()) {
      ::unlink(path_.c_str());
    }
    if (!directory_.empty()) {
      ::rmdir(directory_.c_str());
    }
  }

  [[nodiscard]] bool connected() const { return connected_; }
  [[nodiscard]] std::shared_ptr<grpc::Channel> channel() const { return channel_; }
  [[nodiscard]] const std::string &path() const { return path_; }

 private:
  std::string directory_;
  std::string path_;
  pid_t child_{-1};
  std::shared_ptr<grpc::Channel> channel_;
  bool connected_{false};
};

void bound(grpc::ClientContext &context) {
  context.set_deadline(std::chrono::system_clock::now() + std::chrono::seconds(2));
}

class SessionWatch final {
 public:
  explicit SessionWatch(const std::shared_ptr<grpc::Channel> &channel)
      : stub_(v1::GatewayLiveness::NewStub(channel)),
        reader_(stub_->WatchSession(&context_, v1::WatchSessionRequest{})) {}

  [[nodiscard]] bool ready() {
    v1::WatchSessionReady response;
    if (!reader_->Read(&response) || !response.ready() || response.watch_id().size() != 64U) {
      return false;
    }
    watch_id_ = response.watch_id();
    return true;
  }

  void bind(grpc::ClientContext &context) const {
    context.AddMetadata("x-xcom-watch-id", watch_id_);
  }

  void close() {
    if (reader_) {
      context_.TryCancel();
      static_cast<void>(reader_->Finish());
      reader_.reset();
    }
  }

  ~SessionWatch() { close(); }

 private:
  std::unique_ptr<v1::GatewayLiveness::Stub> stub_;
  grpc::ClientContext context_;
  std::string watch_id_;
  std::unique_ptr<grpc::ClientReader<v1::WatchSessionReady>> reader_;
};

void bound(grpc::ClientContext &context, const SessionWatch &watch) {
  bound(context);
  watch.bind(context);
}

[[noreturn]] void abrupt_client(const char *path) {
  auto channel = grpc::CreateChannel(std::string("unix://") + path,
                                     grpc::InsecureChannelCredentials());
  if (!channel->WaitForConnected(std::chrono::system_clock::now() +
                                 std::chrono::seconds(2))) {
    ::_exit(2);
  }
  auto client = v1::ToolGateway::NewStub(channel);
  SessionWatch watch(channel);
  if (!watch.ready()) {
    ::_exit(3);
  }
  grpc::ClientContext arm_context;
  bound(arm_context, watch);
  v1::ArmSessionResponse armed;
  if (!client->ArmSession(&arm_context, arm_request(), &armed).ok() ||
      armed.state() != v1::SESSION_ARMED) {
    ::_exit(4);
  }
  v1::OpenObservationRequest open;
  open.set_tap_id("tap.first");
  open.set_max_records(1U);
  open.set_deadline_millis(1000U);
  grpc::ClientContext open_context;
  bound(open_context, watch);
  v1::OpenObservationResponse stream;
  if (!client->OpenObservation(&open_context, open, &stream).ok() ||
      stream.stream_id().empty()) {
    ::_exit(5);
  }
  v1::AcquireLeaseRequest acquire;
  acquire.set_session_id("session-1");
  acquire.set_endpoint_id("svc.alpha");
  acquire.set_endpoint_generation(3U);
  acquire.set_plan_digest("plan-1");
  acquire.set_lease_millis(500U);
  acquire.set_deadline_millis(1000U);
  grpc::ClientContext lease_context;
  bound(lease_context, watch);
  v1::AcquireLeaseResponse lease;
  if (!client->AcquireLease(&lease_context, acquire, &lease).ok() ||
      lease.state() != v1::LEASE_ACTIVE) {
    ::_exit(6);
  }
  ::_exit(0);  // No local destructor cancels the watch or releases resources.
}

[[noreturn]] void unassociated_client(const char *path) {
  auto channel = grpc::CreateChannel(std::string("unix://") + path,
                                     grpc::InsecureChannelCredentials());
  if (!channel->WaitForConnected(std::chrono::system_clock::now() +
                                 std::chrono::seconds(2))) {
    ::_exit(2);
  }
  auto client = v1::ToolGateway::NewStub(channel);
  grpc::ClientContext arm_context;
  bound(arm_context);
  v1::ArmSessionResponse armed;
  if (client->ArmSession(&arm_context, arm_request(), &armed).error_code() !=
      grpc::StatusCode::FAILED_PRECONDITION) {
    ::_exit(3);
  }
  v1::OpenObservationRequest open;
  open.set_tap_id("tap.first");
  open.set_max_records(1U);
  open.set_deadline_millis(1000U);
  grpc::ClientContext open_context;
  bound(open_context);
  v1::OpenObservationResponse stream;
  if (client->OpenObservation(&open_context, open, &stream).error_code() !=
      grpc::StatusCode::FAILED_PRECONDITION) {
    ::_exit(4);
  }
  v1::AcquireLeaseRequest acquire;
  acquire.set_session_id("session-1");
  acquire.set_endpoint_id("svc.alpha");
  acquire.set_endpoint_generation(3U);
  acquire.set_plan_digest("plan-1");
  acquire.set_lease_millis(500U);
  acquire.set_deadline_millis(1000U);
  grpc::ClientContext lease_context;
  bound(lease_context);
  v1::AcquireLeaseResponse lease;
  if (client->AcquireLease(&lease_context, acquire, &lease).error_code() !=
      grpc::StatusCode::FAILED_PRECONDITION) {
    ::_exit(5);
  }
  ::_exit(0);
}

void exercise_live_owner(bool shutdown) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  GatewayGrpcService service(session, fixture.config());
  char directory[] = "/tmp/xcom-owner-XXXXXX";
  ASSERT_NE(::mkdtemp(directory), nullptr);
  const std::string path = std::string(directory) + "/gateway.sock";
  auto server = GatewayGrpcServer::start(path, service, fixture.config().max_message_bytes());
  ASSERT_NE(server, nullptr);
  auto channel = grpc::CreateChannel("unix://" + path, grpc::InsecureChannelCredentials());
  ASSERT_TRUE(channel->WaitForConnected(std::chrono::system_clock::now() +
                                        std::chrono::seconds(2)));
  auto client = v1::ToolGateway::NewStub(channel);
  SessionWatch watch(channel);
  ASSERT_TRUE(watch.ready());
  grpc::ClientContext arm_context;
  bound(arm_context, watch);
  v1::ArmSessionResponse armed;
  ASSERT_TRUE(client->ArmSession(&arm_context, arm_request(), &armed).ok());
  ASSERT_EQ(armed.state(), v1::SESSION_ARMED);
  v1::OpenObservationRequest open;
  open.set_tap_id("tap.first");
  open.set_max_records(1U);
  open.set_deadline_millis(1000U);
  grpc::ClientContext open_context;
  bound(open_context, watch);
  v1::OpenObservationResponse stream;
  ASSERT_TRUE(client->OpenObservation(&open_context, open, &stream).ok());
  ASSERT_FALSE(stream.stream_id().empty());
  v1::AcquireLeaseRequest acquire;
  acquire.set_session_id("session-1");
  acquire.set_endpoint_id("svc.alpha");
  acquire.set_endpoint_generation(3U);
  acquire.set_plan_digest("plan-1");
  acquire.set_lease_millis(500U);
  acquire.set_deadline_millis(1000U);
  grpc::ClientContext lease_context;
  bound(lease_context, watch);
  v1::AcquireLeaseResponse lease;
  ASSERT_TRUE(client->AcquireLease(&lease_context, acquire, &lease).ok());
  ASSERT_EQ(lease.state(), v1::LEASE_ACTIVE);
  const auto before = session.snapshot();
  ASSERT_TRUE(before.lease_held);
  ASSERT_EQ(before.active_streams, 1U);

  if (shutdown) {
    const auto started = std::chrono::steady_clock::now();
    server.reset();  // The owner deliberately keeps its indefinite watch open.
    EXPECT_LT(std::chrono::steady_clock::now() - started, std::chrono::seconds(1));
    EXPECT_NE(::access(path.c_str(), F_OK), 0);
    watch.close();
  } else {
    grpc::ClientContext wrong_context;
    bound(wrong_context);
    wrong_context.AddMetadata("x-xcom-watch-id", "not-the-owner");
    v1::ArmSessionResponse denied;
    EXPECT_EQ(client->ArmSession(&wrong_context, arm_request(), &denied).error_code(),
              grpc::StatusCode::FAILED_PRECONDITION);
    grpc::ClientContext duplicate_context;
    bound(duplicate_context, watch);
    watch.bind(duplicate_context);
    EXPECT_EQ(client->ArmSession(&duplicate_context, arm_request(), &denied).error_code(),
              grpc::StatusCode::FAILED_PRECONDITION);
    SessionWatch second_watch(channel);
    EXPECT_FALSE(second_watch.ready());
    second_watch.close();
    const pid_t child = ::fork();
    ASSERT_GE(child, 0);
    if (child == 0) {
      static_cast<void>(::prctl(PR_SET_PDEATHSIG, SIGTERM));
      ::execl("/proc/self/exe", "/proc/self/exe", "--xcom-grpc-unassociated-client",
              path.c_str(), static_cast<char *>(nullptr));
      ::_exit(127);
    }
    int status = 0;
    ASSERT_EQ(::waitpid(child, &status, 0), child);
    ASSERT_TRUE(WIFEXITED(status));
    ASSERT_EQ(WEXITSTATUS(status), 0);
    const auto after_peer = session.snapshot();
    EXPECT_FALSE(after_peer.terminal);
    EXPECT_TRUE(after_peer.lease_held);
    EXPECT_EQ(after_peer.active_streams, 1U);
    EXPECT_EQ(after_peer.requests_received, before.requests_received);
    watch.close();
  }
  const auto cleanup_limit = std::chrono::steady_clock::now() + std::chrono::seconds(1);
  while (!session.snapshot().terminal && std::chrono::steady_clock::now() < cleanup_limit) {
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
  }
  const auto after = session.snapshot();
  EXPECT_TRUE(after.terminal);
  EXPECT_FALSE(after.lease_held);
  EXPECT_EQ(after.active_streams, 0U);
  server.reset();
  EXPECT_EQ(::rmdir(directory), 0);
}

TEST(XcomGrpcGeneratedClient, UnassociatedPeerCannotBorrowLiveWatch) {
  exercise_live_owner(false);
}

TEST(XcomGrpcGeneratedClient, ShutdownTerminatesLiveWatchAndCleansResources) {
  exercise_live_owner(true);
}

TEST(XcomGrpcGeneratedClient, SeparateServerHonorsContractAndWireRejection) {
  ServerProcess process;
  ASSERT_TRUE(process.connected());
  struct stat socket_info {};
  ASSERT_EQ(::stat(process.path().c_str(), &socket_info), 0);
  EXPECT_TRUE(S_ISSOCK(socket_info.st_mode));
  EXPECT_EQ(socket_info.st_mode & 0777, 0600);
  auto client = v1::ToolGateway::NewStub(process.channel());
  SessionWatch watch(process.channel());
  ASSERT_TRUE(watch.ready());

  grpc::ClientContext version_context;
  bound(version_context, watch);
  v1::QueryVersionResponse version;
  ASSERT_TRUE(client->QueryVersion(&version_context, v1::QueryVersionRequest{}, &version).ok());
  EXPECT_EQ(version.protocol().major(), 1U);
  bool associated_watch_advertised = false;
  for (const auto &capability : version.capabilities().capabilities()) {
    if (capability.id() == "xcom.gateway_liveness.local_ipc" && capability.revision() == 2U) {
      associated_watch_advertised = true;
    }
  }
  EXPECT_TRUE(associated_watch_advertised);

  grpc::ClientContext arm_context;
  bound(arm_context, watch);
  v1::ArmSessionResponse armed;
  ASSERT_TRUE(client->ArmSession(&arm_context, arm_request(), &armed).ok());
  ASSERT_EQ(armed.state(), v1::SESSION_ARMED);

  grpc::ClientContext valid_context;
  bound(valid_context, watch);
  v1::SubmitStimulationResponse valid;
  ASSERT_TRUE(client->SubmitStimulation(
                  &valid_context,
                  stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "201"), &valid)
                  .ok());
  EXPECT_EQ(valid.outcome().kind(), v1::STIMULATION_OUTCOME_EMITTED);

  auto invalid = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "202");
  invalid.set_interaction(v1::INTERACTION_KIND_MESSAGE);
  grpc::ClientContext invalid_context;
  bound(invalid_context, watch);
  v1::SubmitStimulationResponse rejected;
  ASSERT_TRUE(client->SubmitStimulation(&invalid_context, invalid, &rejected).ok());
  EXPECT_EQ(rejected.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(rejected.diagnostic().code(), "gw.stimulation.interaction");

  auto wrong_direction = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "203");
  wrong_direction.set_direction(v1::DIRECTION_INBOUND);
  grpc::ClientContext direction_context;
  bound(direction_context, watch);
  ASSERT_TRUE(client->SubmitStimulation(&direction_context, wrong_direction, &rejected).ok());
  EXPECT_EQ(rejected.diagnostic().code(), "gw.stimulation.direction");

  auto unknown_schedule = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "204");
  unknown_schedule.mutable_schedule()->set_mode(static_cast<v1::ScheduleMode>(99));
  grpc::ClientContext schedule_context;
  bound(schedule_context, watch);
  ASSERT_TRUE(client->SubmitStimulation(&schedule_context, unknown_schedule, &rejected).ok());
  EXPECT_EQ(rejected.diagnostic().code(), "gw.schedule.unknown");

  auto foreign_clock = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "205");
  foreign_clock.mutable_schedule()->set_clock_domain("foreign.clock");
  grpc::ClientContext clock_context;
  bound(clock_context, watch);
  ASSERT_TRUE(client->SubmitStimulation(&clock_context, foreign_clock, &rejected).ok());
  EXPECT_EQ(rejected.diagnostic().code(), "gw.clock.unmapped");

  v1::OpenObservationRequest open;
  open.set_tap_id("tap.first");
  open.set_max_records(1U);
  open.set_deadline_millis(1000U);
  grpc::ClientContext open_context;
  bound(open_context, watch);
  v1::OpenObservationResponse stream;
  ASSERT_TRUE(client->OpenObservation(&open_context, open, &stream).ok());
  ASSERT_FALSE(stream.stream_id().empty());

  v1::ReadObservationsRequest read;
  read.set_stream_id(stream.stream_id());
  read.set_max_records(1U);
  read.set_deadline_millis(1000U);
  grpc::ClientContext read_context;
  bound(read_context, watch);
  auto reader = client->ReadObservations(&read_context, read);
  v1::ObservationRecord record;
  while (reader->Read(&record)) {
    EXPECT_LE(record.ByteSizeLong(), 4096U);
  }
  EXPECT_TRUE(reader->Finish().ok());

  // The server's declared-clock poller renews transport credit without changing queue capacity.
  std::this_thread::sleep_for(std::chrono::milliseconds(30));

  v1::CloseObservationRequest close;
  close.set_stream_id(stream.stream_id());
  grpc::ClientContext close_context;
  bound(close_context, watch);
  v1::CloseObservationResponse closed;
  ASSERT_TRUE(client->CloseObservation(&close_context, close, &closed).ok());
  EXPECT_EQ(closed.diagnostic().code(), "gw.observation.closed");

  std::this_thread::sleep_for(std::chrono::milliseconds(30));

  v1::AcquireLeaseRequest acquire;
  acquire.set_session_id("session-1");
  acquire.set_endpoint_id("svc.alpha");
  acquire.set_endpoint_generation(3U);
  acquire.set_plan_digest("plan-1");
  acquire.set_lease_millis(500U);
  acquire.set_deadline_millis(1000U);
  grpc::ClientContext acquire_context;
  bound(acquire_context, watch);
  v1::AcquireLeaseResponse lease;
  ASSERT_TRUE(client->AcquireLease(&acquire_context, acquire, &lease).ok());
  ASSERT_EQ(lease.state(), v1::LEASE_ACTIVE);

  v1::QuerySessionRequest query;
  query.set_session_id("session-1");
  grpc::ClientContext held_context;
  bound(held_context, watch);
  v1::QuerySessionResponse snapshot;
  ASSERT_TRUE(client->QuerySession(&held_context, query, &snapshot).ok());
  EXPECT_TRUE(snapshot.lease_held());
  EXPECT_EQ(snapshot.lease_id(), lease.lease_id());

  v1::ReleaseLeaseRequest release;
  release.set_session_id("session-1");
  release.set_lease_id(lease.lease_id());
  grpc::ClientContext release_context;
  bound(release_context, watch);
  v1::ReleaseLeaseResponse released;
  ASSERT_TRUE(client->ReleaseLease(&release_context, release, &released).ok());
  EXPECT_EQ(released.state(), v1::LEASE_RELEASED);

  grpc::ClientContext query_context;
  bound(query_context, watch);
  ASSERT_TRUE(client->QuerySession(&query_context, query, &snapshot).ok());
  EXPECT_EQ(snapshot.counters().emitted(), 1U);
  EXPECT_FALSE(snapshot.lease_held());

  v1::RevokeSessionRequest revoke;
  revoke.set_session_id("session-1");
  revoke.set_reason_code("done");
  grpc::ClientContext revoke_context;
  bound(revoke_context, watch);
  v1::RevokeSessionResponse revoked;
  ASSERT_TRUE(client->RevokeSession(&revoke_context, revoke, &revoked).ok());
  EXPECT_EQ(revoked.state(), v1::SESSION_REVOKED);
  grpc::ClientContext terminal_query_context;
  bound(terminal_query_context, watch);
  ASSERT_TRUE(client->QuerySession(&terminal_query_context, query, &snapshot).ok());
  EXPECT_EQ(snapshot.state(), v1::SESSION_REVOKED);
  EXPECT_FALSE(snapshot.lease_held());
}

TEST(XcomGrpcGeneratedClient, DeadlineAndCancellationAreTransportEnforced) {
  ServerProcess process;
  ASSERT_TRUE(process.connected());
  auto client = v1::ToolGateway::NewStub(process.channel());

  grpc::ClientContext expired;
  expired.set_deadline(std::chrono::system_clock::now() - std::chrono::seconds(1));
  v1::QueryVersionResponse response;
  const grpc::Status deadline =
      client->QueryVersion(&expired, v1::QueryVersionRequest{}, &response);
  EXPECT_EQ(deadline.error_code(), grpc::StatusCode::DEADLINE_EXCEEDED);

  grpc::ClientContext cancelled;
  bound(cancelled);
  cancelled.TryCancel();
  const grpc::Status cancellation =
      client->QueryVersion(&cancelled, v1::QueryVersionRequest{}, &response);
  EXPECT_EQ(cancellation.error_code(), grpc::StatusCode::CANCELLED);
}

TEST(XcomGrpcGeneratedClient, RejectedObservationReadHasExplicitTransportStatus) {
  ServerProcess process;
  ASSERT_TRUE(process.connected());
  auto client = v1::ToolGateway::NewStub(process.channel());
  SessionWatch watch(process.channel());
  ASSERT_TRUE(watch.ready());
  v1::ReadObservationsRequest request;
  request.set_stream_id("missing-stream");
  request.set_max_records(1U);
  request.set_deadline_millis(100U);

  grpc::ClientContext unnegotiated;
  bound(unnegotiated, watch);
  auto early = client->ReadObservations(&unnegotiated, request);
  v1::ObservationRecord record;
  EXPECT_FALSE(early->Read(&record));
  EXPECT_EQ(early->Finish().error_code(), grpc::StatusCode::FAILED_PRECONDITION);

  grpc::ClientContext arm_context;
  bound(arm_context, watch);
  v1::ArmSessionResponse armed;
  ASSERT_TRUE(client->ArmSession(&arm_context, arm_request(), &armed).ok());
  ASSERT_EQ(armed.state(), v1::SESSION_ARMED);

  grpc::ClientContext missing;
  bound(missing, watch);
  auto absent = client->ReadObservations(&missing, request);
  EXPECT_FALSE(absent->Read(&record));
  EXPECT_EQ(absent->Finish().error_code(), grpc::StatusCode::FAILED_PRECONDITION);

  grpc::ClientContext expired;
  expired.set_deadline(std::chrono::system_clock::now() - std::chrono::seconds(1));
  auto overdue = client->ReadObservations(&expired, request);
  EXPECT_FALSE(overdue->Read(&record));
  EXPECT_EQ(overdue->Finish().error_code(), grpc::StatusCode::DEADLINE_EXCEEDED);
}

TEST(XcomGrpcGeneratedClient, WatchCancellationReleasesLiveResources) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  GatewayGrpcService service(session, fixture.config());
  char directory[] = "/tmp/xcom-watch-XXXXXX";
  ASSERT_NE(::mkdtemp(directory), nullptr);
  const std::string path = std::string(directory) + "/gateway.sock";
  auto server = GatewayGrpcServer::start(path, service, fixture.config().max_message_bytes());
  ASSERT_NE(server, nullptr);
  auto channel = grpc::CreateChannel("unix://" + path, grpc::InsecureChannelCredentials());
  ASSERT_TRUE(channel->WaitForConnected(std::chrono::system_clock::now() +
                                        std::chrono::seconds(2)));
  auto client = v1::ToolGateway::NewStub(channel);

  grpc::ClientContext unwatched_context;
  bound(unwatched_context);
  v1::ArmSessionResponse unwatched_response;
  EXPECT_EQ(client->ArmSession(&unwatched_context, arm_request(), &unwatched_response).error_code(),
            grpc::StatusCode::FAILED_PRECONDITION);

  SessionWatch watch(channel);
  ASSERT_TRUE(watch.ready());
  grpc::ClientContext arm_context;
  bound(arm_context, watch);
  v1::ArmSessionResponse armed;
  ASSERT_TRUE(client->ArmSession(&arm_context, arm_request(), &armed).ok());
  ASSERT_EQ(armed.state(), v1::SESSION_ARMED);

  v1::OpenObservationRequest open;
  open.set_tap_id("tap.first");
  open.set_max_records(1U);
  open.set_deadline_millis(1000U);
  grpc::ClientContext open_context;
  bound(open_context, watch);
  v1::OpenObservationResponse stream;
  ASSERT_TRUE(client->OpenObservation(&open_context, open, &stream).ok());
  ASSERT_FALSE(stream.stream_id().empty());

  v1::AcquireLeaseRequest acquire;
  acquire.set_session_id("session-1");
  acquire.set_endpoint_id("svc.alpha");
  acquire.set_endpoint_generation(3U);
  acquire.set_plan_digest("plan-1");
  acquire.set_lease_millis(500U);
  acquire.set_deadline_millis(1000U);
  grpc::ClientContext lease_context;
  bound(lease_context, watch);
  v1::AcquireLeaseResponse lease;
  ASSERT_TRUE(client->AcquireLease(&lease_context, acquire, &lease).ok());
  ASSERT_EQ(lease.state(), v1::LEASE_ACTIVE);
  ASSERT_EQ(session.snapshot().active_streams, 1U);
  ASSERT_TRUE(session.snapshot().lease_held);

  watch.close();
  const auto limit = std::chrono::steady_clock::now() + std::chrono::seconds(1);
  while (!session.snapshot().terminal && std::chrono::steady_clock::now() < limit) {
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
  }
  const auto after = session.snapshot();
  EXPECT_TRUE(after.terminal);
  EXPECT_EQ(after.active_streams, 0U);
  EXPECT_FALSE(after.lease_held);
  grpc::ClientContext query_context;
  bound(query_context, watch);
  v1::QuerySessionRequest query;
  query.set_session_id("session-1");
  v1::QuerySessionResponse state;
  ASSERT_TRUE(client->QuerySession(&query_context, query, &state).ok());
  EXPECT_EQ(state.state(), v1::SESSION_EVIDENCE_INCOMPLETE);
  EXPECT_FALSE(state.lease_held());
  EXPECT_EQ(state.active_observation_streams(), 0U);
  grpc::ClientContext terminal_context;
  bound(terminal_context, watch);
  v1::ReadObservationsRequest terminal_read;
  terminal_read.set_stream_id(stream.stream_id());
  terminal_read.set_max_records(1U);
  auto rejected = client->ReadObservations(&terminal_context, terminal_read);
  v1::ObservationRecord record;
  EXPECT_FALSE(rejected->Read(&record));
  EXPECT_EQ(rejected->Finish().error_code(), grpc::StatusCode::FAILED_PRECONDITION);
  server.reset();
  EXPECT_EQ(::rmdir(directory), 0);
}

TEST(XcomGrpcGeneratedClient, AbruptClientExitReleasesLiveResources) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  GatewayGrpcService service(session, fixture.config());
  char directory[] = "/tmp/xcom-exit-XXXXXX";
  ASSERT_NE(::mkdtemp(directory), nullptr);
  const std::string path = std::string(directory) + "/gateway.sock";
  auto server = GatewayGrpcServer::start(path, service, fixture.config().max_message_bytes());
  ASSERT_NE(server, nullptr);
  const pid_t child = ::fork();
  ASSERT_GE(child, 0);
  if (child == 0) {
    static_cast<void>(::prctl(PR_SET_PDEATHSIG, SIGTERM));
    ::execl("/proc/self/exe", "/proc/self/exe", "--xcom-grpc-disconnect-client",
            path.c_str(), static_cast<char *>(nullptr));
    ::_exit(127);
  }
  int child_status = 0;
  ASSERT_EQ(::waitpid(child, &child_status, 0), child);
  ASSERT_TRUE(WIFEXITED(child_status));
  ASSERT_EQ(WEXITSTATUS(child_status), 0);
  const auto limit = std::chrono::steady_clock::now() + std::chrono::seconds(1);
  while (!session.snapshot().terminal && std::chrono::steady_clock::now() < limit) {
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
  }
  const auto after = session.snapshot();
  EXPECT_TRUE(after.terminal);
  EXPECT_EQ(after.active_streams, 0U);
  EXPECT_FALSE(after.lease_held);
  server.reset();
  EXPECT_EQ(::rmdir(directory), 0);
}

TEST(XcomGrpcGeneratedClient, LateTransportFailuresReconcileCommittedEmission) {
  GatewayFixture fixture;
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.open_path());
  GatewaySession session(fixture.config(), fixture.dependencies(), fixture.binding());
  GatewayGrpcService service(session, fixture.config());
  char directory[] = "/tmp/xcom-commit-XXXXXX";
  ASSERT_NE(::mkdtemp(directory), nullptr);
  const std::string path = std::string(directory) + "/gateway.sock";
  auto server = GatewayGrpcServer::start(path, service, fixture.config().max_message_bytes());
  ASSERT_NE(server, nullptr);
  auto channel = grpc::CreateChannel("unix://" + path, grpc::InsecureChannelCredentials());
  ASSERT_TRUE(channel->WaitForConnected(std::chrono::system_clock::now() +
                                        std::chrono::seconds(2)));
  auto client = v1::ToolGateway::NewStub(channel);
  SessionWatch watch(channel);
  ASSERT_TRUE(watch.ready());
  grpc::ClientContext arm_context;
  bound(arm_context, watch);
  v1::ArmSessionResponse armed;
  ASSERT_TRUE(client->ArmSession(&arm_context, arm_request(), &armed).ok());
  ASSERT_EQ(armed.state(), v1::SESSION_ARMED);

  auto overbound_response =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, std::string(3600U, '1'));
  grpc::ClientContext overbound_context;
  bound(overbound_context, watch);
  v1::SubmitStimulationResponse overbound_result;
  EXPECT_EQ(client->SubmitStimulation(&overbound_context, overbound_response, &overbound_result)
                .error_code(), grpc::StatusCode::RESOURCE_EXHAUSTED);
  EXPECT_EQ(fixture.emitter().calls, 0U);

  fixture.emitter().delay_millis.store(100U);
  const auto request = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "901");
  grpc::ClientContext context;
  bound(context, watch);
  v1::SubmitStimulationResponse first;
  grpc::Status status;
  std::thread caller([&] { status = client->SubmitStimulation(&context, request, &first); });
  const auto limit = std::chrono::steady_clock::now() + std::chrono::seconds(1);
  while (!fixture.emitter().entered_emit.load() && std::chrono::steady_clock::now() < limit) {
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  const bool entered = fixture.emitter().entered_emit.load();
  context.TryCancel();
  caller.join();
  static_cast<void>(session.snapshot());  // Wait for the already-entered action to finish.
  EXPECT_TRUE(entered);
  EXPECT_EQ(status.error_code(), grpc::StatusCode::CANCELLED);
  EXPECT_EQ(fixture.emitter().calls, 1U);

  grpc::ClientContext retry_context;
  bound(retry_context, watch);
  v1::SubmitStimulationResponse retry;
  ASSERT_TRUE(client->SubmitStimulation(&retry_context, request, &retry).ok());
  EXPECT_NE(retry.outcome().kind(), v1::STIMULATION_OUTCOME_EMITTED);
  EXPECT_EQ(fixture.emitter().calls, 1U);

  fixture.emitter().entered_emit.store(false);
  fixture.emitter().delay_millis.store(600U);
  grpc::ClientContext deadline_context;
  deadline_context.set_deadline(std::chrono::system_clock::now() +
                                std::chrono::milliseconds(300));
  watch.bind(deadline_context);
  const auto timed_request =
      stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "903");
  v1::SubmitStimulationResponse timed_response;
  const grpc::Status timed =
      client->SubmitStimulation(&deadline_context, timed_request, &timed_response);
  static_cast<void>(session.snapshot());
  EXPECT_TRUE(fixture.emitter().entered_emit.load());
  EXPECT_EQ(timed.error_code(), grpc::StatusCode::DEADLINE_EXCEEDED);
  EXPECT_EQ(fixture.emitter().calls, 2U);
  watch.close();
  grpc::ClientContext lookup_context;
  bound(lookup_context, watch);
  v1::QuerySessionRequest lookup;
  lookup.set_session_id("session-1");
  lookup.set_stimulation_request_id("901");
  v1::QuerySessionResponse reconciled;
  ASSERT_TRUE(client->QuerySession(&lookup_context, lookup, &reconciled).ok());
  EXPECT_TRUE(reconciled.stimulation_intent_found());
  EXPECT_EQ(reconciled.stimulation_outcome().kind(), v1::STIMULATION_OUTCOME_EMITTED);
  grpc::ClientContext timed_lookup_context;
  bound(timed_lookup_context, watch);
  lookup.set_stimulation_request_id("903");
  ASSERT_TRUE(client->QuerySession(&timed_lookup_context, lookup, &reconciled).ok());
  EXPECT_TRUE(reconciled.stimulation_intent_found());
  EXPECT_EQ(reconciled.stimulation_outcome().kind(), v1::STIMULATION_OUTCOME_EMITTED);
  server.reset();
  EXPECT_EQ(::rmdir(directory), 0);
}
}  // namespace

int main(int argc, char **argv) {
  if (argc == 3 && std::strcmp(argv[1], "--xcom-grpc-server") == 0) {
    return serve(argv[2]);
  }
  if (argc == 3 && std::strcmp(argv[1], "--xcom-grpc-disconnect-client") == 0) {
    abrupt_client(argv[2]);
  }
  if (argc == 3 && std::strcmp(argv[1], "--xcom-grpc-unassociated-client") == 0) {
    unassociated_client(argv[2]);
  }
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
