# ADR-ML3-CONTAINMENT-0001 — retained cgroup boundary and original cleanup registry

Date: 2026-10-18. Status: implementation-candidate decision, not accepted or runtime admitted.
Parent: ML3-SUPERVISION3-2026-10-18-v3; platform baseline c2997c0.
Basis: ML-SR-010/012/013/024, U4, descriptor contract C02–C09. No requirement is added.

Use Linux cgroup v2 for an exact boundary component under an explicitly supplied,
exclusive delegated parent descriptor. Verify actual filesystem type, domain kind and
control files. Create only fresh random child directories. Retain both original parent
and child descriptors; compare the private child name with its retained identity before
mutation. A path, PID, descriptor value or matching public data never reconstructs an
existing registry entry. Never freeze, kill or remove the delegated parent itself.

The original process owns an inert private registry. Its explicit admission facts bind
run, supervisor/AFFA/host sessions, bootstrap approval reference, initial epoch and fixed
teardown deadline. These are trusted integration inputs, not authenticated operator
approval; full owner/run/store/bootstrap admission remains pending. Creation reserves
private accounting before mkdir. Bind resources immediately, register a private C1
object, close nested-cgroup creation, request freeze and require observed frozen state.
The descriptor's creation epoch never changes when the cancellation epoch advances.
Cancellation before reservation rejects; cancellation during allocation retains partial
cleanup accounting and cannot return successful frozen Stage. No child insertion or
workload Release method is exposed by this component. **The option schema is empty**:
all keyword options, including historical helper options and identity aliases, reject.

BoundaryRecord is an immutable private-scope snapshot, never launch or cleanup authority.
Every operation validates the original holder/registry, exact descriptor, retained C1
or approved empty-reservation branch, host session and original deadline. Forked/copied
holders, a replacement registry and missing entries cannot adopt resources. After
expiry retain unresolved identity and require external cleanup. No public evidence
serializes C1, descriptors, raw resources or private approval facts.

Membership is read from the retained, verified frozen cgroup, independently of leader
existence. Bound bytes/member count, require stable duplicate-free samples consistent
with populated/frozen status, and reject nested groups, changed identity, errors and
partial/unstable samples. Empty is evidence only after complete successful observation.
An explicit per-operation limit (≤5 s) is separate from the fixed original generation
lease. The proposed maximum lease envelope is 394 s, derived from D3's 300 s active
budget plus 16×5 + 10 + 2 + 2 s reserve. Neither value is a measured guarantee.
Cleanup closes insertion admission in this component, uses cgroup.kill only under C1,
observes empty live membership, and removes the exact empty directory. Kernel removal
is the final facility fence: kernel control files must be absent below its retained
original descriptor, and its private name must be absent. Kernfs link counts are not
the removal predicate. Retain identity until confirmation. A failed
remove or unknown observation retains unresolved state. CP-02 permits only originally
approved, verified empty, never-started allocation release; CP-03 permits original C1
empty release without inventing child termination. A released tombstone is cached
terminal evidence and cannot supply a fresh membership observation.

Python matches existing control-plane contracts. A small fixed C **test fixture** uses
clone3 to create children directly in a frozen boundary; native child code avoids Python
interpreter work after raw clone. It is not the production launcher or a provider. C++
X-COM is unchanged. Library kernel I/O can stall: outer U3 supervision remains required,
and deadline guards are not kernel-enforced execution leases. Root exclusivity and no
untracked insertion are mandatory integration assumptions. Future launch code must be
admitted separately; passing a raw cgroup FD is not authorization to insert children.

## Kernel basis and verification limits

Linux 6.8 documents that freeze completion is observed in cgroup.events, frozen tasks
can still migrate, cgroup.kill handles concurrent forks, and deleted/dying groups cannot
receive processes or revive. These facts do not establish M1 cancellation ordering.
[cgroup v2](https://www.kernel.org/doc/html/v6.8/admin-guide/cgroup-v2.html).
clone3 can create a child directly in a frozen cgroup using a retained directory FD.
[clone3](https://man7.org/linux/man-pages/man2/clone3.2.html).

Verify actual frozen birth/zero marker before thaw, leader death with live descendant,
exact force/empty/removal, rejected insertion through a deleted retained FD, unrelated
sentinel survival, lost authority, CP-02/03, cancellation, identity replacement, failed
observation/release and deadline exhaustion. Keep pure/model checks distinct from real
kernel component checks and the nine full-ML3 runtime cases. No whole requirement,
source-parent semantics, full trace, runtime admission, acceptance or merge is implied.
