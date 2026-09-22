# Contract: Local X-COM tool gateway

The first external-tool proof uses a versioned gRPC service with Protocol Buffers on a host-protected
local IPC endpoint. The server must not bind a TCP address. Exact dependency versions, generated-code
toolchain, licenses, and hashes are pinned by the SESN implementation preflight.

## Service surface

- inspect gateway version and non-sensitive capabilities;
- open/close one observation stream using an exact tap policy;
- arm/revoke one validation session using an exact validation permit;
- submit signal/message stimuli and service calls;
- acquire/use/release one service-emulation lease;
- query bounded session outcomes and counters.

Every unary request has a deadline. Streams have bounded message size, queue, idle timeout, and
shutdown behavior. Flow control cannot create unbounded memory or silently block the normal data plane.
Disconnect closes observation handles and drains, revokes, or quarantines validation-owned resources
according to the durable session state.

Local socket file permissions and host account boundaries restrict access to the endpoint but do not
authorize stimulation. The validation permit remains mandatory. The gateway logs only safe identities,
codes, sizes, timing, and outcomes; unrestricted payloads and permit contents are never logged.

The `.proto` definition is an external API and follows additive field evolution, reserved removed field
numbers/names, explicit protocol version negotiation, generated-client contract tests, and a separate
compatibility review before any breaking revision.

