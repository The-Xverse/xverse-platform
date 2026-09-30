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

TEST(XcomGrpcGeneratedClient, SeparateServerHonorsContractAndWireRejection) {
  ServerProcess process;
  ASSERT_TRUE(process.connected());
  struct stat socket_info {};
  ASSERT_EQ(::stat(process.path().c_str(), &socket_info), 0);
  EXPECT_TRUE(S_ISSOCK(socket_info.st_mode));
  EXPECT_EQ(socket_info.st_mode & 0777, 0600);
  auto client = v1::ToolGateway::NewStub(process.channel());

  grpc::ClientContext version_context;
  bound(version_context);
  v1::QueryVersionResponse version;
  ASSERT_TRUE(client->QueryVersion(&version_context, v1::QueryVersionRequest{}, &version).ok());
  EXPECT_EQ(version.protocol().major(), 1U);

  grpc::ClientContext arm_context;
  bound(arm_context);
  v1::ArmSessionResponse armed;
  ASSERT_TRUE(client->ArmSession(&arm_context, arm_request(), &armed).ok());
  ASSERT_EQ(armed.state(), v1::SESSION_ARMED);

  grpc::ClientContext valid_context;
  bound(valid_context);
  v1::SubmitStimulationResponse valid;
  ASSERT_TRUE(client->SubmitStimulation(
                  &valid_context,
                  stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "201"), &valid)
                  .ok());
  EXPECT_EQ(valid.outcome().kind(), v1::STIMULATION_OUTCOME_EMITTED);

  auto invalid = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "202");
  invalid.set_interaction(v1::INTERACTION_KIND_MESSAGE);
  grpc::ClientContext invalid_context;
  bound(invalid_context);
  v1::SubmitStimulationResponse rejected;
  ASSERT_TRUE(client->SubmitStimulation(&invalid_context, invalid, &rejected).ok());
  EXPECT_EQ(rejected.outcome().kind(), v1::STIMULATION_OUTCOME_REJECTED);
  EXPECT_EQ(rejected.diagnostic().code(), "gw.stimulation.interaction");

  auto wrong_direction = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "203");
  wrong_direction.set_direction(v1::DIRECTION_INBOUND);
  grpc::ClientContext direction_context;
  bound(direction_context);
  ASSERT_TRUE(client->SubmitStimulation(&direction_context, wrong_direction, &rejected).ok());
  EXPECT_EQ(rejected.diagnostic().code(), "gw.stimulation.direction");

  auto unknown_schedule = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "204");
  unknown_schedule.mutable_schedule()->set_mode(static_cast<v1::ScheduleMode>(99));
  grpc::ClientContext schedule_context;
  bound(schedule_context);
  ASSERT_TRUE(client->SubmitStimulation(&schedule_context, unknown_schedule, &rejected).ok());
  EXPECT_EQ(rejected.diagnostic().code(), "gw.schedule.unknown");

  auto foreign_clock = stimulation_request(v1::STIMULATION_ACTION_INJECT_SIGNAL, "205");
  foreign_clock.mutable_schedule()->set_clock_domain("foreign.clock");
  grpc::ClientContext clock_context;
  bound(clock_context);
  ASSERT_TRUE(client->SubmitStimulation(&clock_context, foreign_clock, &rejected).ok());
  EXPECT_EQ(rejected.diagnostic().code(), "gw.clock.unmapped");

  v1::OpenObservationRequest open;
  open.set_tap_id("tap.first");
  open.set_max_records(1U);
  open.set_deadline_millis(1000U);
  grpc::ClientContext open_context;
  bound(open_context);
  v1::OpenObservationResponse stream;
  ASSERT_TRUE(client->OpenObservation(&open_context, open, &stream).ok());
  ASSERT_FALSE(stream.stream_id().empty());

  v1::ReadObservationsRequest read;
  read.set_stream_id(stream.stream_id());
  read.set_max_records(1U);
  read.set_deadline_millis(1000U);
  grpc::ClientContext read_context;
  bound(read_context);
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
  bound(close_context);
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
  bound(acquire_context);
  v1::AcquireLeaseResponse lease;
  ASSERT_TRUE(client->AcquireLease(&acquire_context, acquire, &lease).ok());
  ASSERT_EQ(lease.state(), v1::LEASE_ACTIVE);

  v1::ReleaseLeaseRequest release;
  release.set_session_id("session-1");
  release.set_lease_id(lease.lease_id());
  grpc::ClientContext release_context;
  bound(release_context);
  v1::ReleaseLeaseResponse released;
  ASSERT_TRUE(client->ReleaseLease(&release_context, release, &released).ok());
  EXPECT_EQ(released.state(), v1::LEASE_RELEASED);

  grpc::ClientContext query_context;
  bound(query_context);
  v1::QuerySessionRequest query;
  query.set_session_id("session-1");
  v1::QuerySessionResponse snapshot;
  ASSERT_TRUE(client->QuerySession(&query_context, query, &snapshot).ok());
  EXPECT_EQ(snapshot.counters().emitted(), 1U);

  v1::RevokeSessionRequest revoke;
  revoke.set_session_id("session-1");
  revoke.set_reason_code("done");
  grpc::ClientContext revoke_context;
  bound(revoke_context);
  v1::RevokeSessionResponse revoked;
  ASSERT_TRUE(client->RevokeSession(&revoke_context, revoke, &revoked).ok());
  EXPECT_EQ(revoked.state(), v1::SESSION_REVOKED);
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
}  // namespace

int main(int argc, char **argv) {
  if (argc == 3 && std::strcmp(argv[1], "--xcom-grpc-server") == 0) {
    return serve(argv[2]);
  }
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
