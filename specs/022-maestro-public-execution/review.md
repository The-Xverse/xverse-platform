# Initial read-only consistency review

2026-10-29. Baseline 7fab6a290c3731533c2b88517158055c768b9d4e.
Finding MPX-R01 (BLOCKER for current Studio integration): candidate submission
requires a private runtime object; no admitted public effective-input submission.
Disposition: new separately authorized public capability; old boundary unchanged.
Finding MPX-R02 (MAJOR): Argus plan.semanticDigest identifies the compiled plan,
not Studio input-semantic identity. Disposition: preserve distinct digest fields.
Finding MPX-R03 (MAJOR): Lite flows/Zenoh telemetry cannot establish native X-COM.
Disposition: actual native observation/provider evidence required by AC-07/08.
Finding MPX-R04 (MAJOR): source inspection and generated reviews are not platform
acceptance. Disposition: explicit user acceptance and exact main integration retained.
No implementation, live acceptance or independent review is claimed by this pass.

## Inspection implementation review, pass1 (before repairs)

Candidate: initial public inspection implementation;7 installed-package checks pass.
This is a separate self-review pass, not independent user acceptance.

- MPX-IR01 MAJOR: CanonicalSubmission lacks an explicit resource-selection field.
  Expected plan digest binds the compiled selection, but the written contract also
  requires direct selection agreement. Add public ExperimentSelection and a mismatch
  test; do not silently rely on implicit selection.
- MPX-IR02 MAJOR claim boundary: inspection is static compilation/binding checking,
  not provider effective-configuration or runtime permission admission. Keep T02
  in_progress, executionAllowed false and runtime layers visibly unimplemented.
- MPX-IR03 MINOR: source has no process/writer calls, but tests should explicitly
  fail if compilation inspection dispatches a process or opens an Argus writer.
- MPX-IR04 MINOR: add inspection unit specifications and exact public-boundary
  source/test mapping before extending implementation.
- Packaging observation: force-included Maestro files are copied even for this
  editable install. Initial collection could not see the new module; rebuilt the
  installed package and7 checks passed. Do not validate against stale installed code.

## Effective preparation review, pass2 (before repairs)

13 installed-package checks pass. IR01 explicit selection and IR03 zero-effect
checks are now covered; IR04 unit specifications are present. IR02 remains the
correct stage boundary: no runtime permit or lifecycle dispatcher exists yet.

- MPX-IR05 MINOR: an invalid host provider_id of an unhashable type can produce a
  TypeError instead of the documented stable registration error. Guard its type.
- MPX-IR06 MINOR: a compiler I/O exception can escape the stable public failure
  boundary. Translate it without copying private filesystem diagnostics.
- MPX-IR07 MINOR: the public preparation summary should retain each provider's
  effective source-byte digests separately from the request, not only inside a
  configuration digest. Add the explicit provenance map.
- Residual: independent runtime consumption of the frozen provider configuration
  is not implemented or verified. A provider's source report and static equality
  cannot substitute for actual edited-input execution verification.

- MPX-IR08 MINOR: default dataclass repr can reveal submitted source bytes or
  private provider configuration during debugging. Hide those byte-bearing fields
  from repr and verify the public preparation representation stays metadata-only.


## Inspection/preparation review, pass3

The current installed source matches all inspected implementation modules.18 public-boundary
checks pass, including independent installed CLI identity, edited provider sources,
registration errors, source/config privacy and zero-effect static inspection. IR01,
IR03–IR08 are repaired in this bounded layer. IR02 remains an explicit implementation
boundary: static/effective-source checking does not grant runtime authority. No
independent acceptance, lifecycle execution, native exchange or full goal completion
is claimed. Next work is host runtime permission, phase planning and actual ownership.

## Lifecycle graph and host permission review, pass4

Separate read-only self-review after35 installed-package checks passed. Graph
coverage, explicit ancestor ordering, all-acquisition readiness, logical/provider
ownership, cycles, missing references, canonical order, finite per-phase bounds
and exact expiring host permissions were inspected. No runtime exists yet.

- MPX-LR01 MAJOR integration obligation: a graph does not interpret lifecycleIntent,
  simulation clocks, faults or profile behavior. The runtime provider must reject
  any unsupported semantics before effects and tests must prove actual edited-input
  consumption. Keep T02/T03 in_progress and T04 open.
- MPX-LR02 MAJOR integration obligation: the old public ProcessProvider uses group
  signals. Do not reuse it as proof of exact live resource ownership; implement and
  test original-child/pidfd authority, with unknown recovery after handle loss.
- MPX-LR03 MAJOR integration obligation: trusted Python callbacks cannot be forcibly
  time-bounded safely by a thread timeout. Require cooperative provider deadlines,
  verify concrete providers, and state that this is not a hostile-plugin sandbox.

## Initial runtime read-only review, pass5 (before repairs)

Runtime source is an unverified successor, not an accepted implementation. The
first runtime test run failed during fixture compilation (9 setup errors): XDL
requires nonempty steps/observers/metrics. No child was started. Preserve compiler
authority; replace the invalid fixture with explicit supported startup/measurement
semantics, never relax the schema or silently claim arbitrary plan support.

- MPX-RR01 MAJOR: launch transfers stdin before the provider receives its ownership
  handle. A delivery exception could leave a child after an unsuccessful bounded
  stop. Return/retain the owned child before transferring configuration data.
- MPX-RR02 MAJOR: runtime failure catches erase the stable reason and can leave an
  earlier failed Argus append labelled open if later cleanup writes succeed. Retain
  a bounded public failure code and make writer failure sticky independently of
  resource cleanup.
- MPX-RR03 MAJOR: readiness needs a bounded original provider observation to show
  actual consumed inputs/measurements rather than just a generated success enum.
  Preserve a bounded JSON observation through the real Argus writer, under the
  existing internal-only payload policy; this does not authorize raw browser logs.
- MPX-RR04 MAJOR: terminal readiness is a startup observation only. It does not
  establish ongoing process liveness. Add an explicit reconciliation observation
  path before live integration; reads must not relaunch or infer continued health.

## Runtime/Argus interoperability review, pass6 (before repairs)

The successor reached actual child execution:8 checks pass; the positive Argus
verification fails truthfully with ARGUS2-REASON-UNRESOLVED-CAUSATION. Inspecting
the public reader confirms this is the run-level correlation target, not a lost
phase event. A prior run also retained8 test-provider schema-key failures before
using the actual observer.payloadPolicy compiled representation.

- MPX-RR05 MAJOR: Argus indexes correlationId as a reference to an eventId. The
  generated run-level correlation currently names no event. Bind it to the actual
  start-request event identity; do not manufacture a placeholder predecessor or
  suppress the reader's incomplete verdict.
- MPX-RR06 MAJOR: public Argus append_event flushes userspace buffers but does not
  fsync. Explicitly call its public flush_buffer before any lifecycle dispatch to
  satisfy durable-before-effect intent. Retain writer faults as failures.

- MPX-RR07 MAJOR (subsequent ownership inspection, before repair): failure while
  acquiring the kernel process handle can raise before exposing the original child
  to the provider; the fallback bounded termination can also time out. Preserve
  the child in a public typed failure, retain unknown ownership and require the
  provider to retain that handle for cleanup/reconciliation. Never hide this case
  behind a successful stop or broad group signal.

Runtime ownership successor verification retained:43passed,7failed,3teardown
errors, caused by a removed time import in OwnedChild.stop. F821 caught the same
undefined name. No successful cleanup was claimed by those runs; unknown remained
visible. Restored the import in the successor before rebuilding and re-verifying.
This is a repair record, not evidence of a passing candidate.

## Runtime boundary review, pass7 (before repairs)

50 installed-package checks now pass. Review is a separate self-review, not
independent user acceptance. RR01/RR02/RR03/RR05/RR06/RR07 are covered by successor
code and checks. RR04 now has explicit timestamped inert read versus runtime
observation, actual exit detection and cleanup. The owned deadline also terminates
without a browser. No native exchange or Autoverse capability is inferred.

- MPX-RR08 MAJOR: per-phase cleanup limits alone allow a long aggregate cleanup
  budget. Add a finite host-owned overall cleanup deadline; exhausted phases remain
  unknown and cannot be reported released.
- MPX-RR09 MINOR: malformed service registry/read identities or damaged claim
  metadata can escape the stable public error boundary. Validate bounded host
  registry and claim schema before resource operations; reject writable shared roots.
- MPX-RR10 MAJOR verification gap: single-element execution does not establish
  cross-element scheduling or reverse cleanup. Compile an actual two-binding XDL
  selection and verify dependency order and partial-start rollback using two
  separately owned children.
- Residual: installed paths are trusted immutable host assets; immediate hash
  rechecks do not provide hostile-host filesystem isolation. Provider callbacks
  remain cooperative trusted code. Windows, process-tree containment and physical
  permissions remain unsupported, not inferred from these Linux tests.

- MPX-RR11 MAJOR (root replacement inspection): the lexical service root is
  checked before dispatch, but the Argus writer would still publish closure via
  that same lexical path during cleanup. Pin the original directory with an owned
  Linux descriptor for writer access so replacement roots are never modified.
  A separate actual public-Argus probe using /proc/self/fd/<owned-dirfd>/argus
  finalized and read as complete; it required no private Argus API or source edit.

## Runtime admission identity review, pass8 (before repairs)

54 checks passed and1 test assertion failed because its deliberately10ms cleanup
budget can expire during intent fsync before a child is signalled. Product state
correctly remained unknown; corrected the test's assumption that release must have
already occurred.108 existing public Maestro-preparation/admission and Argus-writer
checks also pass. Two real binding/child dependency and rollback cases pass.

- MPX-RR12 MAJOR: provider implementation identity and semantic private config do
  not currently pin a separately configurable installed command/environment.
  Freeze an explicit installation digest in effective preparation and revalidate
  the actual host provider installation identity before each dispatch. Static
  preparation without such an installation may remain usable but cannot run.
- MPX-RR13 MAJOR: permit environment_id is recorded but not checked against a
  runtime environment/root witness. Bind runtime host/root/kernel/limits identity
  into the host grant and validate it on every acquisition, preventing grant reuse
  under another runtime root. This is separate from private-runtime lane approvals.

## Public boundary review, pass9 (before repairs)

165 checks pass on the runtime/installation-bound successor (57new,108baseline).
RR08–RR13 have successor code and targeted checks, with prior failures retained.

- MPX-RR14 MINOR: an unexpected trusted-provider preparation/admission exception
  can escape as raw host details. Translate it into a stable bounded error without
  copying the original text. Correct ExecutionInputError's outdated claim that all
  uses imply no effects: runtime errors after a durable claim are distinct.
- MPX-RR15 MAJOR: a KeyboardInterrupt raised after child acquisition bypasses the
  start Exception handler. Attempt known reverse cleanup before propagating the
  interrupt; a durable claim must still prevent replay if the host dies or cleanup
  itself is interrupted. This is not a promise of cleanup after process death.

## Runtime prototype review, pass10

Separate self-review of the exact source hashes in evidence/runtime/verification.json:
167checks pass (59public-boundary +108baseline), all8 installed implementation
modules match source, F821 and diff checks pass. RR01–RR03 and RR05–RR15 are repaired
and covered in the bounded Linux prototype. RR04 has explicit historical read and
actual resource observation; LR01/LR03 remain continuing obligations for every
new provider, never automatically granted to a future native or legacy adapter.
Two existing native C++ baseline tests pass under the accepted pinned dependency
and warning policy, independently of this prototype run. They do not establish
the required correlated Maestro/native-X-COM/Argus experiment.

The next implementation stage is original native-observation ingestion and a
real native exchange bound to this public runtime, then concrete provider and Studio
integration. No platform acceptance, main integration, native Windows/physical
support, hostile-code/process-tree containment or overall goal completion is
claimed. The existing closed runtime's approvals were not changed.

## Native ingestion review, pass11 (before clock repair)

The actual native helper builds with the repository C++20/warning policy. Its
first composed run exchanges two real payloads through submit/receive and imports
the original native records.8 negative checks pass;1positive fails because Argus
recorded complete but independently assessed incomplete with CLOCK-UNRESOLVED.
The source domain was absent from the opening declaration. Preserve that result.

- MPX-NR01 MAJOR: declare native clock domains before Argus opens through a pure
  provider declaration. Use an explicit per-process elapsed-clock origin, not an
  invented source reading or an inferred Python/C++ clock mapping. Reject an
  undeclared native clock before import; retain actual original timestamps.
- MPX-NR02 workflow observation: during implementation the evidenceWriter snapshot
  was changed to expose the actual public writer_state after abort, replacing its
  former generic closed label. This repair was not recorded as a persisted finding
  beforehand; do not describe it as a prior separate review. Require affected
  verification and this separate review before accepting the successor.
- Native completeness still requires original source declarations, drain/closure
  and gap behavior. The neutral helper remains a fixed owned contract test, never
  proof of the full Autoverse/Studio integration or network fidelity.

- MPX-NR03 MAJOR (original-counter review, before repair): record counters are
  stamped when each observation is retained. Drops after the last retained record
  can therefore be absent from every record. Preserve/import the actual final
  native ObservationSnapshot and its quiesced interval, and verify observer pressure
  leaves actual FIFO payload delivery intact while Argus evidence remains incomplete.
  Do not rewrite an earlier record's original native counters to imply later loss.

## Native causal-source allocation, before implementation

18 composed native checks now pass, including actual observer saturation: both
payloads deliver, one native record drops, the original final snapshot declares it,
and actual Argus recorded/assessed statuses remain incomplete. No native counter
was rewritten. The positive no-loss run remains complete after clock declaration.

- MPX-NR04 integration obligation: the future external bridge needs its actual
  provider-recorded input/ingress fact before native forwarding, because the core
  requires causation identity. Add bounded original input facts to the host-only
  batch contract and persist their original IDs/clocks before observations. An
  unknown upstream cause remains absent; run correlation is not a substitute for
  per-message causation. A configured native test input has an actual launch cause.

- MPX-NR05 MAJOR (retry review before repair): Stop currently rejects a retry with
  the original expected_version after successful cleanup, although it accepts a
  second call after rereading the terminal version. Retain the original stop
  request/version and operation ID so an identical lost-response retry is inert;
  unrelated stale versions must still conflict. Persist the stop operation and
  bounded terminal failure code in actual Argus records for cross-view navigation.

## Scope and concrete-provider review, before final repairs

187 focused checks pass on the composed successor, including the original-version
Stop retry and persisted Stop operation identity. The following concrete boundaries
still need repair/verification before presenting an acceptance candidate:

- MPX-NR06 MAJOR: owned-simulation grants check realizationClass but should also
  reject targetClass physical/remote, matching the written prototype exclusions.
  Verify against actual compiled physical/remote declarations with zero effects.
- MPX-NR07 MAJOR: the native test provider's dispatch override omits its base
  provider's ProcessOwnershipError retention. Repair it and exercise actual native
  child acquisition failure; unknown cleanup must not become released because
  assignment of the returned handle was interrupted by the constructor exception.

Selected-baseline qualification for NR06: the attempted physical fixture first
failed semantic validation without its asset reference, then the authoritative
compiler rejected targetClass physical even with virtual realization. The final
negative case preserves that compiler rejection and asserts zero effects; no
physical compiled plan is fabricated. Remote/virtual does compile and is denied
by the host simulation grant. Failed test reports remain in private scope-* XML;
they describe test assumptions, not failed live hardware operations.

Failure-retention limitation: original native-initial.xml and subsequent reports
are retained, but the first temporary failing run's raw native/Argus directories
were not copied before normal pytest retention. The original CLOCK-UNRESOLVED
diagnosis was inspected through the actual reader and retained as a tool observation
and this review, not as a preserved raw original directory. Do not claim otherwise.
The final candidate will use a unique private basetemp and retain its actual data.

## Frozen platform candidate review and acceptance

Accepted source fingerprint0f1c5bd2040c1a8e1a0b6997269ec27ab5edcf32c0924a2a9fa2388595069045.
Final source/test bytes remain unchanged through190passing checks,0failures/errors/
skips,84.59seconds;3existing native build/consumer/observation CTest checks also pass.
All9 installed implementation modules match source. The unique private final-native
basetemp retains the actual source projections and Argus evidence. Source/header
baseline, binary, report, log and build-policy hashes are in evidence/native/verification.json.

Separate self-review confirms repaired NR01–NR07 and the earlier recorded runtime
findings within the bounded Linux prototype. Physical declarations are rejected by
the actual selected compiler; remote targets are denied before effects. Partial
native acquisition retains unknown authority, identical Stop retries are inert,
actual input/native/snapshot records preserve source identity and original clocks,
and real observer pressure cannot hide final loss or alter FIFO delivery in this
witness. No independent third-party software review is asserted.

The user explicitly said I accept; recorded2026-10-29 16:16:03UTC. Acceptance applies
to this frozen public platform boundary. Subsequent edits record documentation and
evidence only, with no source/test changes. Existing private-runtime/lane/physical
approvals remain closed; there is no publication approval. T10 proceeds through an
isolated exact-artifact main merge and assembled verification. T07 actual Studio/
Autoverse and the full goal remain required. No live user preview was changed.
