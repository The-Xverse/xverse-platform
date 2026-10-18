# Catalog launcher unit contract

ML3-LAUNCHER9-2026-10-18-v3, partial candidate; readiness false.

Recipe cap 64 KiB, 64 argv entries, 32 explicit environment values, 4096 bytes/string,
8 MiB regular ELF, fixed generation <=394 s, request <=5 s and drain <=2 s. These are
engineering bounds, not scientific protocol thresholds. Original C1 is registered
before any child can exist. All recipe identities derive from immutable accepted
XDL/catalog/permit/intent context, never from an arbitrary caller process request.

LC09 wire is 128 bytes: magic4/kind4/sequence8/deadline8/scope32/reason8/cgroup-dev8/
cgroup-ino8/child-pid8/child-token32/state8. Closed kinds Stage1, Cancel2, Query3,
Ready16, Staged17, Cancelled18, Error19, Observed20. Per-message original-child or
parent credentials are mandatory. Ready returns exactly its original cgroup FD;
Staged returns exactly the original clone pidfd. Other packets carry no FDs.
Commands/replies bind exact original deadline, scope, sequence and expected handle.
The wire scope is SHA-256 of the exact sealed private input, independently computed
by the native helper. The input header retains the original context digest.
No output bytes or public payload transfer C1 or mint an intent/ticket.

Verify real process-kind XDL compilation and current M3/Argus intent -> actual
catalog executable seal/hash -> born-frozen child -> original launcher/FD-bound
RG06 -> observed exec/probe -> original C1 cleanup and helper child reap. Before
Release, marker evidence must stay absent. Exercise wrong image/argv/artifact pin,
malformed/foreign/stale/duplicate protocol/FDs, changed source after sealing, unsafe
inherited FDs/environment, cancelled/late Stage, old removed-boundary birth, issuer/
child loss, failed exec, leader exit with descendants, copied/forked registry and
storage timeout after Arm. Keep observed direct-child, boundary and evidence states
separate. Installed-wheel/source regressions and strict native/static analysis are
required, along with findings recorded before repairs and exact hashes.
