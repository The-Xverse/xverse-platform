# R1 and R4 Codex repair

This change follows the rejected T030–T038 terminal repair candidate `6d28ce1dab3ce26541c949d3416a1085f45e7de9`. It closes the two findings left open by the external rereview. Earlier T030/T031 documents describe the dependency gap at the time those stages ran; their historical results are retained.

## R1: generated gRPC service on local IPC

The offline package lock now includes `libc-ares2` version `1.18.1-1ubuntu0.22.04.3`, archive SHA-256 `d1c9a66669d6a4ec968efebb670a72d2188d98a1f37823c1f6cde8da23b51e0c`. The 13-entry package manifest has SHA-256 `9879911b35058e8c8e0ee78ad5faef258c34d9e490b78b2121d6b9565c92945c`. The manifest and extracted prefix are verified against the lock before build. The admitted `libgrpc++.so.1.30.2` resolves `libcares.so.2` from this prefix. No package-manager or network operation occurs during admission or build.

`xverse_xcom_tool_gateway_grpc` compiles the generated gRPC service source and implements all ten `ToolGateway` methods over the existing bounded, permit-bound `GatewaySession`. `GatewayGrpcServer::start` accepts a filesystem Unix-socket path only, requires an owned private parent directory, refuses an existing path, creates the socket with a restrictive umask, and verifies mode `0600`. It sets message, memory, and worker-thread bounds. Its declared-clock poller drives scheduled completion and idle cleanup; server shutdown invokes the session's resource cleanup. The existing custom-frame fixture remains for its inherited tests; it is not presented as the gRPC service.

The generated-client regression executable starts the production gRPC adapter in a separate server process. It calls all ten methods through the generated stub, checks an authorized emission, four rejected wire-field variants with no extra emission, observation stream open/read/close, exact lease acquire/release, session query/revoke, transport deadline and cancellation, and protected socket mode.

## R4: actual per-request deadline

`GatewaySession::admit` accepts the request's captured arrival tick and compares dispatch time to that arrival plus the declared deadline. In-process callers without an explicit arrival start at their dispatch tick. Every gRPC method captures the session clock at handler entry and passes that arrival through admission; the transport also enforces its absolute deadline and cancellation. Stimulation rechecks expiry immediately before the action path. The new unit case advances the declared clock beyond a request-specific deadline while the permit is still valid, requires the exact `gw.deadline.expired` diagnostic and zero emission, then verifies acceptance at the exact boundary. Scheduled request horizons use that same request arrival.

## Verification

The 13-package offline admission, focused generated-client and deadline cases, the build contract, and the complete local CTest suite pass. Target-repository integration and final candidate evidence are recorded separately after assembly at the pinned platform revision.
