# BC17 / BS17 exact private bootstrap successor

DRAFT engineering contract before implementation. Related: AF06/10/12/20/22,
ML-SR-005–014/016–020/022–024 partial; no parent requirement is discharged here.

BC17 header:80 bytes. Original BC10 offsets0..55 retain generation/lease/context,
but magic BC17 and version2. At56 original delegated-parent FD uint64;64 device;
72 inode. Four original sealed-image records then use BC10's fd:uint32,
SHA256:32bytes, argv0length:uint32, UTF8 argv0 and finalNUL encoding.
Whole input remains sealed, at most65536 bytes. The parent must be the exact
original ProcessBoundaryOps parent; it is not frozen and no ownership is inferred
from a pathname. The admission retains images1..3 as exact historical pins. Storage role3, AFFA
role4 and explicitly budgeted disposable-controller role5 may execute; role5 uses
Python image3 with a fixed controller_worker module, not a fifth image record. Legacy roles1/2 are disabled to
exclude an alternate Stage/Release path. BS10 is unchanged.

BS17 remains exactly128 bytes, BS10 offsets, distinct magic. Kinds1/2/3 retain
birth/activate/renew; kind4 WATCH and ACK20 use seq/end/scope, watch slot1..128,
zero pid/token/state/reason/reserved. WATCH transfers exactly one original leaf
cgroup FD. Native checks original parent identity, frozen1/populated0/no descendants,
unique identity and sequential watch slot. ACK20 echoes the exact slot/end/sequence.
The original supervisor retains an immutable inventory log; a timeout closes starts.

Role4 requires helper==unit (its own original helper boundary), at least one watched
workload boundary, no overlap with any watched boundary and no prior AFFA birth.
Its AC17 version2 config must have the same generation, lease within the original
bootstrap lease,1..16 units and exact160-byte unit records with initial boundary
identities already present in the watchdog inventory. Fixed argv is ELF,channel,config.
It inherits neither cgroup parent FD nor workload watch FDs after exec.

Before code, expected real controls:
- Actual native birth/activation yields an original-parent waitable AFFA, without
  coordinator Popen. A second role4 birth fails closed.
- Role4 without all initial watches rejects before clone; unregistered boundary
  identity in a valid sealed AC17 config never becomes a watched capability.
- Both actual released workload units become frozen when bootstrap lease expires
  while AFFA is SIGSTOPped. AFFA death is observed before C1 cleanup; native workload
  direct-child waits remain unknown after its forced death.
- AFFA death triggers bootstrap watchdog cleanup before the lease even if original
  supervisor remains alive. No per-unit scope is replaced with a container.
- Wrong parent, duplicate watch, late watch, changed version and extra rights reject.
- Existing BS10 tests continue to pass and still reject role4/WATCH.

Full supervisor-death, simultaneous bootstrap loss, actual storage-worker loss,
fresh-generation/controller composition and complete environment admission remain
separate mandatory integration controls. A component test is not a factory run.

Storage-supervision successor: BS17 admits one original role3 child as well as one
role4. It monitors both original pidfds independently of Python. Actual storage
child death triggers helper termination followed by the exact watched-leaf freeze.
This extends no lease and changes no BS10 role contract. Storage stall still relies
on independent cancellation or expiry of the original native leases; no hard kernel
or control-I/O bound is claimed.


Controller continuation: role5 uses an exact fresh own helper C1 and inherits only
its private request channel/sealed input. Native admission rejects watched workload
scopes and any previously used helper identity. Actual role5 death does not invoke
the storage/AFFA global death path; original bootstrap lease/supervisor loss still
kills all helpers and freezes exact workload leaves. BS10 rejects role5. Broker
controller budget/C1 capacity, new host-session labels, original death/wait/channel
retirement and real durable/native reconciliation are specified in
affa-controller-replacement.md. Focused controller-v5 source/wheel11/11 verifies
this component; broader current regression and full selected M1 remain pending.

## Cleanup-only terminal extension (candidate, 2026-10-19)

The original BS17/version2 fixed128-byte channel adds request5/reply21 for terminal
entry and request6/reply22 for cleanup-only lease service. Both retain original
peer credentials, scope, increasing sequence, zero rights, zero slot/PID/token/
reason/reserved fields and an original future operation end within the old root
lease, <=5s and generation-2s. Request5 has state0; reply21 reports the current root
lease. Request6 has the requested nondecreasing lease in state; reply22 reports its
actual accepted value. The lease remains <=now+5s and <=original generation-2s.
A missing/changed/late ACK closes the original root and cannot replay entry.

Entry irreversibly freezes every originally watched workload C1; removed original
cgroups cannot accept another task. Only after the transition does the native loop
tolerate original authority death. Native terminal mode accepts only request6:
birth, activation, ordinary renewal, new watches and repeated terminal entry are
rejected with cleanup. Original parent, storage and root-lease/generation watchdogs
remain active. No new child, channel, admission or writer is created. Freezing or
reaping the authority does not establish any workload wait/retirement/normal record.

The genuine broker and lower original-session entry independently require the same
original registered AuthorityConnection and its pinned native CANCELLED receipt or
actual original-parent consumed issuer wait. Shared local cancellation alone is
insufficient. Ordinary Python helper/authority access stays closed. BS10/version1
rejects these kinds and otherwise retains its existing behavior. Absent terminal
use leaves BS17 behavior unchanged. Full dispatcher/report/closure and M1/races
remain separate gates; see findings136–142 and the exact terminal-service evidence.
