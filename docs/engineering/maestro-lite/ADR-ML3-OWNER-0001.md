# Original-owner evidence-to-Release integration

ML3-OWNER7-2026-10-18-v1, implementation candidate. Parent 288f7004a29b9a0e78fa1e3032c3fd20aa750476.
Same capability 024, U2/U3/U4/U7. Main acceptance and whole lifecycle remain open.

Use Python for control-plane composition of the actual PermitSession, accepted
EvidenceRun public append_event/flush_buffer and original C1 boundary observation;
retain the native RG06 one-use unfreeze gate unchanged. No new framework, daemon,
protocol dialect, thesis/domain import or compilation-on-import is introduced.
Kernel/socket and storage calls are not hard-time bounded: native gate expiry
prevents a late acknowledgement from reviving permission, but disposable I/O worker
and bounded helper bootstrap integration remain required for whole caller bounds.
This increment supplies the original-owner integration; it is not complete U5.

Reconcile two prototype integration gaps without changing the frozen contract:
actual unit identities are complete XDL references; BoundaryDescriptor must retain
those strings exactly as logical data, never use them as paths. D7 payload v2 uses
execution generation 1, whereas the prior U2 component admits only generation 0.
Add an explicit initial_generation=1 admission option, retaining the default 0;
only 0 or 1 is allowed. Runtime owner requires generation 1. No arbitrary later
generation/restart permission is inferred. Permit claims retain original receipt
object identity and exact stored-record equality, and are revalidated at Release.
Copies/forks/field equality or changed journal history cannot adopt a claim.

One original ReleaseOwner binds exact PermitSession/EvidenceRun/StageSupervisor/
CancellationLatch objects. It durably claims M3 intent, mirrors a public-redacted
lifecycle v2 intent with explicit host/UTC clocks through append_event, and only
registers a private original claim after successful public flush_buffer and all
post-call deadline/latch checks. No caller-supplied receipt hash is accepted as
truth. Persistence failure leaves the intent consumed; append-only or late flush
cannot issue a ticket. Keep normal evidence gaps even if later C1 cleanup succeeds.

A separate original StageSupervisor observes the exact originally registered C1
boundary, fixed descriptor/creation epoch and live frozen membership, checks the
original gate's matching READY session and issues a fresh private ACK. Before
Release, revalidate permit, journal, original objects, descriptor, host session,
C1, current frozen membership and the gate. Bind actual observed claim/flush/Stage
identities into native Arm, then send Release only through that same gate/channel.
No public fields, copied receipt, replacement owner or cleanup capability may mint
start authority. C1 is never passed to the gate or serialized into public evidence.

The original trusted bootstrap owner must supply the actual Popen/socket before
dispatch, enable per-message credentials before READY, pin the admitted binary,
and prevent concurrent waiters. Retain its pidfd and original socket identity;
authenticate native replies by kernel credentials, not socketpair SO_PEERCRED
creation-time credentials. Bounded nonblocking IPC, strict RG06 matching and one-use
owner state are required. Unknown replies fail closed and retain cleanup accounting.
Bootstrap/operator approval and executable creation remain trusted integration inputs,
not authenticated by the object constructors. No full run readiness is granted.

Cancel uses the independent latch and control-channel shutdown without the owner
mutation lock, so a hung journal/provider does not prevent revocation from being
requested. Native ordering determines whether Release committed before Cancel;
a late result cannot become readiness. The original external C1 still owns cleanup.
Helper/owner loss, arbitrary kernel stalls, ordinary provider handles, complete
reverse teardown/restart/recovery, full evidence/coverage/collection and all nine
runtime cases stay open. Preserve all 24 ML-SR and 18 unvalidated source parents.
