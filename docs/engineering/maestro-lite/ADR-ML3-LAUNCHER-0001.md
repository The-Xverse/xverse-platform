# Catalog-selected born-frozen process staging

ML3-LAUNCHER9-2026-10-18-v3. Parent 53c4e779b2835cd6b05a8e90ddd77d0956b57340.
Capability 024, partial U2/U3/U4/U5. Implementation candidate; no run acceptance.

Retain Python for control-plane catalog/permit/registry/evidence composition and C
for clone3/execveat, original pidfds, FD confinement and original-parent control.
A dedicated explicitly built native helper performs executable I/O and child birth
outside the original Python C1 holder. It never thaws or releases a boundary.
The independent RG06 gate alone performs one-use Release after actual M3/Argus/Stage
acknowledgements. Initial helper Popen creation still needs outer supervision; this
increment bounds per-workload Stage RPC and does not close whole bootstrap/M1.

Derive one immutable private launch recipe from the actual accepted prepared unit,
ProcessAction, binding's digest-pinned executable artifact and original registered
intent. Require an unambiguous selected artifact whose file URI equals the declared
executable path. Never accept a caller command/callback. Exact argv/cwd and explicitly
supplied declared environment values are bounded; no environment or shell is inferred.
The native helper opens/retains the cwd, copies a regular ELF executable (<=8 MiB)
into a sealed memfd, hashes the actual copied bytes with OpenSSL EVP SHA-256, and
compares the catalog pin before clone3(CLONE_INTO_CGROUP|CLONE_PIDFD). Source-path
replacement after sealing cannot change that image. Direct shebang scripts require
an explicit pinned interpreter contract; this increment rejects them rather than
silently selecting an interpreter. ELF interpreters can be declared ProcessActions;
script/module/library/environment admission remains an explicit full-run dependency.
No claim of a hermetic environment, sandbox, physical fidelity or production timing.

Use optional OpenSSL 3 libcrypto for this explicitly built helper, not a bespoke
cryptographic implementation or a new Python/runtime framework. Record compiler,
linked dependency and helper identities; absence rejects helper admission. Building,
installing or importing the Python package never compiles/starts helpers.

Private LC09 packets bind scope, exact sequence/deadline, original cgroup device/
inode, child token/PID and observed state. Authenticate every packet with kernel
sender credentials. Native READY returns its retained cgroup FD; Stage returns its
original child pidfd. Check expected ancillary-FD count and actual original C1
identity, close all rejected FDs, and never infer ownership from the numeric PID.
Retain original registry plus full OwnedResourceHandle equality; copied registries,
forks, foreign/forged handles and lost issuers confer no ordinary authority.

The child is born frozen, so its trusted pre-exec stub and catalog instructions
remain silent until Release. After Release, the stub closes inherited control FDs,
uses only explicit argv/env/cwd, redirects standard streams and execveat's the sealed
image. A CLOEXEC error pipe distinguishes pending setup, successful exec and failure;
process existence alone must not bypass exec acknowledgement. Probes are bounded
component observations, not lifecycle readiness or a normal M3 successful outcome.

Bind the original launcher registry to ReleaseOwner before staging. Revalidate that
same live issuer/child/handle and boundary before and after bounded M3 revalidation
and immediately before Release. Extend RG06 with an explicit optional boundary-ACK
build that returns its actual original cgroup FD on READY; unchanged default RG06/
LG05 behavior remains supported. A catalog-issued Release requires this actual FD
to match original C1 and launcher; a matching digest alone does not prove FD binding.

Cancel does not wait for the Stage/RPC lock. Helper cancellation/owner loss/expiry
closes insertion and attempts exact direct-child kill/reap; parent C1 independently
covers descendants and late birth. Successful direct-child reap does not prove tree
empty/released, nor satisfy missing normal evidence. Never reconstruct C1, discover
resources by name/PID or broaden cleanup. Retained removed cgroup identity is the
late-birth fence: old clone requests cannot re-enter a C1-certified removed boundary.

Keep original bootstrap artifact/environment/FD authentication, whole caller bounds,
arbitrary kernel stalls, original-owner/issuer-loss cases, ordinary provider facade,
full U5/U7/U8 and all nine runtime cases open. Test storage timeout after Arm explicitly.
All 24 ML-SR and 18 unvalidated/null-mapped source parents remain binding; no author
scientific decision or accepted main changes.

Engineering mechanism sources only:
[clone3/cgroup birth](https://man7.org/linux/man-pages/man2/clone3.2.html),
[execveat](https://man7.org/linux/man-pages/man2/execveat.2.html),
[OpenSSL EVP digest](https://docs.openssl.org/3.0/man3/EVP_DigestInit/).
These API references are not dissertation literature evidence or citation approval.
