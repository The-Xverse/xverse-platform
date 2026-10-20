# Actual evidence checks and private whole-lifecycle entry

Status: implemented internal components with selected owned source/wheel checks;
full public admitted execution remains pending. DRAFT
[RUNTIME-0003](ADR-ML3-RUNTIME-0003.md) records the allocation before code.

`runtime_evidence.verify_runtime_evidence` now reads actual externally pinned
authorization/facility canonical bytes and all nine referenced receipt files.
It requires regular files, bounds each read to1MiB, retains caller offsets,
checks identity/size/timestamps before and after reading, and verifies exact
bytes/hashes under one original host deadline. It checks actual kernel release,
the original empty cgroup-v2 parent/controls and current self-pidfd/KCMP support.
Authorization, active-window and lease bindings are revalidated using fresh
actual clocks after reading, before returning inert descriptive pins.

Matching bytes do not authenticate the submitting caller or establish receipt
semantics, source-parent approval or full facility coverage. Positive unit files
are explicitly SYNTHETIC/INERT and never authorize execution. No subprocess,
C1 creation, M3 journal or Argus writer occurs during evidence validation.

The private `_OriginalRuntimeRun` composes one separately approved original
low-level bootstrap/permit scope through storage, exact C1 units, native AFFA,
controller, lazy finite dispatcher, collection, terminal report and RunClosure.
It retains original startup/active/terminal/closure ends and returns after actual
root/helper cleanup observations. Execution, cleanup and normal evidence remain
separate; all readiness/lifecycle-completion flags remain false at this layer.
It is not exported as public `xverse.maestro.start` and accepts no synthetic
evidence pin as an execution capability.

Matching completed start and collect return retained original objects; changed
repeats/concurrent starts reject. Stop sets the original latch independently of
the start lock, uses original pinned cancellation ownership, and returns the
retained epoch on matching repeats without another signal/RPC. The existing
active dispatcher remains the only restart coordinator. Full public control/
recovery/registry integration and its complete verification are still required.

Original98653 passes84 checks per source/wheel phase on initial80 production
files; auditadcf00 retains160 absent owned reservations,4 whole-entry contexts,
220 M3/Argus links and4 durable closed roots. These initial bytes lack the later
post-I/O authorization-window correction and are historical evidence only.

Original31119 fails before test execution: the probe driver expected plural
"tests collected" while pytest reported one test. Its original frozen wheel,
source/collection log and driver are preserved. Audit9f1ba4 confirms zero executed
cases/parents/helpers. The corrected driver runs the new probe on unchanged
production bytes: original23294 fails in both phases because actual authorization
expires during a1.1s read without rejection. Audita8da38 retains both failures,
two absent empty parents and zero execution permission/helper claims.

The production correction repeats original admission checks after file/host
validation with fresh actual clocks. Original45046 verifies the corrected window
and18 evidence-input controls per phase. Its new concurrent-stop control then
fails because the test requires unknown waits despite genuine source wait/retire
acknowledgements. Auditf89170 retains26 passed/1 failed per phase,54 absent
reservations,6 whole-entry contexts,254 exact source links and4 closed roots;
the remaining59 controls per phase were not executed. Physical cleanup true,
execution false, normal evidence incomplete is the correct recorded combination.

Successor c corrects only that test expectation and runs the affected8 entry
controls plus the59 skipped adjacent checks on identical80 production files.
The selected current scope is19 evidence/window checks from b plus67 from c,
86 per phase across those runs. Passing component scope is not whole-platform
regression or completion of the nine full runtime cases. See the linked audits
and partial trace for original receipt/manifest identities and terminal handles.

Evidence: [initial](evidence/affa17/runtime-entry-20261019a/verification.json),
[original driver error](evidence/affa17/runtime-entry-window-20261019a/verification.json),
[original expiry counterexample](evidence/affa17/runtime-entry-window-20261019b/verification.json),
[partial successor](evidence/affa17/runtime-entry-20261019b/verification.json),
[current entry verification](evidence/affa17/runtime-entry-20261019c/verification.json).

Actual externally approved receipt semantics/authorization and current admitted
host/load proof, source-parent/G4 dispositions, complete public run/control entry,
24 requirements/18 source parents/30 pairs/90 endpoints/nine cases, all seven P3
tasks, M1, complete regression/review and stable17 remain open.135/222 are unresolved
stability gates. No automatic acceptance, merge, canonical-note update, factory
run, scientific parameter or scientific result follows from these components.

Later [private controls](runtime-controls.md) add original registry routing and
correct startup cleanup/result retention after ordinary alias loss. Startup14/14
controls pass per phase. New recovery/nominal failures286/287 remain unresolved
despite favorable diagnostic probes; the older86-check scope above is historical
and cannot establish current full stability.


Later [candidate service](runtime-service.md) adds a default-closed externally
pinned admission facade and typed start-window restrictions around original runs.
Selected unit/owned-component checks do not establish actual approved service
execution, full M1 or resolution of135/222/286/287. The trusted host must authenticate
approval and validate review semantics; current synthetic positives remain inert.


The [RPC failure diagnostic](rpc-failure-context.md) now adds an optional original
in-memory observation to private RuntimeResult. Source/wheel57 affected checks
pass each; the old timeout causes and full-scope gates remain unresolved. Context
is neither a durable worker outcome nor an authority grant, and None stays unknown.
