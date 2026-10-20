# Original waits and single-use local disposal

2026-10-19. Unaccepted candidate refinement of runtime lifecycle cleanup, before
repair344. Capability024; ML-SR-011/012/013/019/020/022/023; DV06/07/10. Python
owns host lifecycle composition. Original native BS17/AFFA children and C1 retain
process and containment authority. No protocol, XDL, M3 or Argus interface changes.

Original three-case source/wheel controls in runtime-disposal-20261019a show
that a client-local unresolved drain can outlive a genuine root-consumed helper
wait, and that retrying broker image disposal can close a reused descriptor
number. The test guard blocked that close. Preserve every initial outcome.

PersistenceClient.dispose may verify a nonblocking wait through its exact
original BootstrapChild and existing original pidfd capability when its own
earlier drain was unresolved. A live helper or uncertain wait still rejects.
This grants only disposal of the client's own descriptors. It never replaces
the earlier drain, RuntimeResult or startup outcome and never grants normal
writer/evidence completion. Plain Popen clients retain the existing requirement
for their own reaped drain. Serialize disposal with the original client lock,
retain terminal disposal success, and consume a raw pidfd before attempting its
close so an ambiguous error cannot authorize closing a reused number on retry.

At broker admission, retain an original per-broker image-disposal state containing
the original context, a lock, the finite admitted image/cwd/recipe descriptor list
and any close failures. Before the first close require the original cleanup
context and actual authority-child wait. Remove each descriptor from that list
before its close attempt, attempt remaining original entries even if one close
fails, and retain uncertainty rather than retrying any consumed number. Matching
successful replay authenticates the original object and disposal state without
requiring already-closed client transports or ordinary generation registries.
Copies, replaced state/context and concurrent disposal reject. No discovered FD,
PID, path or replacement resource is adopted.

Verify the original three whole-entry cases and an ambiguous image-close control
using owned guarded canaries. Verify live-child rejection, unchanged earlier
drain/result, actual original waits, successful matching replay and zero canary
close attempts. A close-error control must remain unresolved without another
close attempt. Repeat affected persistence, bootstrap, broker, closure and whole
runtime checks against identical frozen source and installed-wheel bytes.

Earlier timeout causes, complete runtime cases, source-parent semantics, M1,
full regression, independent review, acceptance and merge remain open. This
decision is local engineering support, not CAPA effectiveness or scientific evidence.
