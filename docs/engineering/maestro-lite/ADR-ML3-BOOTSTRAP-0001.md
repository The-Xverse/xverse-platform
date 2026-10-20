# Supervised creation of the three Maestro helper roles

ML3-BOOTSTRAP10-2026-10-18-v4; parent 9616ec973188bb392b3b820c584ba90be47ac210.
Capability 024, partial U2/U3/U4. Implementation candidate; no run acceptance.

Keep Python for original C1, admission facts, typed clients and ownership records.
Use an explicitly built C11/OpenSSL native bootstrap supervisor for helper birth,
activation and lease enforcement. Its original Python parent is independently
supervised by the external admitted runner. Starting/admitting this first native
supervisor and sealing its input/images are external bootstrap prerequisites,
not recursively claimed bounded runtime operations. No helper is compiled or
started on import/install. Keep all legacy direct-Popen paths compatible.

The native supervisor accepts only three fixed helper roles: catalog launcher,
C1-bound RG06 gate and isolated persistence interpreter/module. Sealed admission
binds exact helper image bytes/digests, argv0, environment identity, run/lifecycle,
bootstrap approval reference, generation and finite lease. Approval references are
external admitted facts, not authentication minted by a dataclass. In-memory image
sealing and dependency/environment admission happen before operation dispatch.
Native initialization independently checks all image seals and SHA-256 pins.
No arbitrary command, script, callback, inherited environment or shell is accepted.
Python's interpreter/site/stdlib/shared-library dependencies still need external
environment admission; sealing one ELF is not a hermetic-environment proof.

Before every helper birth, the original C1 holder creates/registers an exclusive
empty frozen helper boundary distinct from workload boundaries. Native
clone3(CLONE_PARENT|CLONE_PIDFD|CLONE_INTO_CGROUP) creates an actual child of the
original Python controller, preserving existing per-message parent credentials
and exclusive original-parent wait authority without a Python Popen in the
operation path. The native supervisor retains the helper boundary, any workload
freeze-only boundary and original pidfd. It cannot thaw a workload boundary.

Birth returns the actual clone pidfd. Python records a sealed original-registry
BootstrapChild before a separate one-use activation may thaw that helper boundary.
It is an actual kernel-issued child capability, not a fabricated Popen. Shared
original wait accounting lets the typed client and bootstrap drain consume/cache
the same exact wait result; no broad wait, PID discovery or replacement registry.
Existing clients continue their actual HELLO/READY/input/C1 checks after activation.
Helper activation is not a workload Release ticket or lifecycle readiness.

Finite requests and a nonblocking mutation lock keep cancellation independent.
EOF, malformed/foreign messages, original-parent loss and lease expiry close helper
birth/activation. Cleanup kills only retained helper pidfds, observes their exit,
and refreezes retained workload boundaries after helper exits so a dead gate cannot
perform a later thaw. It never kills a workload or deletes C1; original C1 separately
observes/terminates/releases trees. A stalled kernel or a missed birth acknowledgement
retains explicit unresolved accounting; no metadata-based adoption or inferred reap.
Late genuine pidfd acknowledgements may add cleanup-only evidence, never activate.
The spawn-to-ACK crash gap remains unresolved if no exact pidfd is recoverable;
the external controller supervisor and original helper C1 remain necessary.

Root lease renewal must arrive before expiry and cannot extend the fixed generation.
Gate leases cannot exceed the current admitted bootstrap lease. Root loss invalidates
ordinary BootstrapChild authority, but retained exact pidfds still permit cleanup.
All observations keep readiness/whole cleanup false. Full original-owner/guard-loss
M1 proof, provider facade, current-generation readiness, reverse lifecycle/recovery,
normal M3 outcomes, U7/U8, G1/G3/G4/G5 and nine runtime cases remain binding.

Keep all 24 ML-SR and 18 unvalidated/null-mapped REF-002 source parents. Add partial
links for ML-SR-005/009/010/011/012/013/018/019/023/024 without closing requirements.
Resolve launcher finding 10 in this successor before freezing source.

Mechanism references (engineering API sources, not thesis citation approval):
[clone3 flags and parent/wait semantics](https://man7.org/linux/man-pages/man2/clone.2.html),
[kernel cgroup-v2 freezer and deletion](https://docs.kernel.org/admin-guide/cgroup-v2.html),
[OpenSSL EVP digest](https://docs.openssl.org/3.0/man3/EVP_DigestInit/).

Durable bootstrap-permit consumption/authentication remains a full U2 admission
gate; the current approval reference supplies continuity, not a mintable execution
permission. No unit permit implicitly authorizes orchestration helpers.

Successor v3 identity repair: Linux 6.8 anonymous pidfd inodes are not process
identity. Retain a private original duplicate for each root/issued child. Verify
borrowed FD aliases against that exact open file description using own-process
KCMP_FILE before ordinary use; signal/wait/duplicate only the private original.
Never reopen by PID or accept inode equality. Missing comparison permission/syscall
rejects bootstrap admission. The x86-64 backend is exercised here; the AArch64 UAPI
number is recorded for capability-gated use, not claimed tested on that architecture.
This does not defend against malicious code that controls the entire holder process.

[KCMP_FILE semantics](https://man7.org/linux/man-pages/man2/kcmp.2.html),
[Linux v6.8 x86-64 syscall table](https://github.com/torvalds/linux/blob/v6.8/arch/x86/entry/syscalls/syscall_64.tbl),
[Linux v6.8 asm-generic UAPI](https://github.com/torvalds/linux/blob/v6.8/include/uapi/asm-generic/unistd.h).

Successor v4 also routes typed persistence failure/escalation signals through the
original BootstrapChild capability. Client-visible descriptor aliases are inputs
for validation, never signal targets. A substituted sentinel cannot acquire helper
cleanup authority. Legacy genuine-Popen behavior remains unchanged.
