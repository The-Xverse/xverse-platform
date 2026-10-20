# Original supervisor startup ownership and reservation

Status: DRAFT implementation refinement before code, finding266. This implements
the next internal layer of RUNTIME-0001; it does not expose or complete public start.

Keep one original startup owner per run in a bounded original registry. Its
caller is the trusted bootstrap admission owner and supplies the separate
BootstrapAdmission approval, original C1 manager and sealed images. Joint metadata
preflight, real facility/receipt validation and whole-run authorization remain
required in the complete entry. Existing low-level constructors stay compatible.
The registry has an explicit caller-supplied capacity, proposed cap128 records;
terminal identities are not evicted or reused implicitly. This is an engineering
resource bound, not a scientific parameter or increased execution authority.

The startup owner duplicates the original sealed supervisor image for immutable
execution and verifies its actual bytes plus every configured helper image against
the admitted hashes/seals before Popen. Execute through the retained descriptor,
with only original private config/channel/image/parent descriptors passed. Native
BS17 still validates its own helper bytes and exact parent. No shell/path lookup,
replacement issuer, PID discovery or existing-resource adoption.

Reserve identity before creation. Retain original Popen, channel and independent
pidfd immediately on return, before READY. On successful registration, original
BootstrapSession owns the actual root wait; the startup owner must not consume it
again. On registration failure, revoke/wait only via its original pidfd. A failure
before a usable process/capability is returned stays an explicit unknown birth;
do not silently dispose or recreate it. A local cancellation flag alone is not a
wait, fence, completed cleanup or authority to signal a discovered process.

Cancellation sets the original latch independently of the startup lock; launch
checks it before creation and after original Popen return. Startup/registration
and recovery drains keep explicit original ends; drain cap2s and existing helper
image cap32MiB are retained. Initial Popen/kernel scheduling is not claimed to
be bounded under host failure; full external facility admission remains a gate.

Disposal requires actual original root and registered-helper waits with no pending
births. It supplies no native workload wait or C1 release credit. Readiness and
lifecycle completion remain false at this layer. Owned tests may directly exercise
this internal bootstrap component under their explicit owned bootstrap approval;
they do not pass synthetic joint-attestation vectors as M1 execution authority.

Python owns reservation/validation/cleanup composition; unchanged native BS17/AFFA
own watchdog/epochs/containment and direct workload waits. Full public run registry,
control/terminal entry, M1 and source-parent/case verification, regression, independent
review, stable17 and author acceptance remain required.
