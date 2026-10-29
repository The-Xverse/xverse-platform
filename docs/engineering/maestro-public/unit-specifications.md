# Public execution unit specifications

Status: prototype inspection, admission, lifecycle, Linux child and Argus units
implemented; native integration and acceptance remain open.
Capability: specs/022-maestro-public-execution. This is not acceptance or certification.

| Unit | Responsibility and invariants | Verification |
|---|---|---|
| MPX-U01 CanonicalSubmission/ExperimentSelection | Immutable explicit source bytes, selected resource URIs and expected independent digests; document/count/byte bounds; no executable host instructions | public inspection positive, mismatch, invalid XDL, name/size and selection tests |
| MPX-U02 InspectionHost/SchemaPin/TargetBinding | Static host-installed provider and schema identities; duplicate/bounds checks; schema content verified before and after actual compilation; no runtime permit | target rejection and schema replacement tests |
| MPX-U03 inspect_submission | Actual public compiler, exact input/plan/selection agreement, preserved logical device/component identity, no process/writer calls, static-only readiness | installed-package public API and zero-effects tests |
| MPX-U04 EffectiveInspection | Independent JSON copies, canonical receipt and stable domain-separated digest; executionAllowed false until a separate runtime layer actually admits execution | mutation/repeatability test |
| MPX-U05 prepare_execution | Independently compile provider-effective documents; freeze bounded private configuration, source and installation identities; reject preset divergence | test_admission.py; actual edited-input consumption in test_runtime.py |
| MPX-U06 plan_lifecycle | Bounded complete logical/provider ownership; explicit prepare/start/ready ancestry; cycle/reference rejection; deterministic topological tie order, no invented causality | test_planning.py and actual two-binding test_multi_element.py |
| MPX-U07 HostExecutionPermit | Exact host, preparation, graph, environment and runtime-root/limit identity; finite expiry; simulated/virtual scope; no legacy authority | test_planning.py and runtime admission negatives |
| MPX-U08 PublicExecutionService | Exclusive root and durable start claim; idempotency/conflicts; versioned inert reads; original observations; partial-start reverse cleanup; no replay after handle loss; finite aggregate/runtime deadlines | test_runtime.py and test_multi_element.py |
| MPX-U09 LifecycleEvidence | Actual public Argus open/append/flush/finalize/abort; original input versus plan identity; correlation names original request event; persistent writer failures independent of cleanup; root pinned through owned directory FD | actual writer/reader interop, fsync/open failure and root-replacement tests |
| MPX-U10 FixedProcessInstallation/OwnedChild | Fixed pinned host command/environment; no imported executable strings; bounded stdin after handle retention; original Popen/pidfd/birth witness; no unknown/group signals | actual child, changed installation/birth, kernel-handle failure, runtime exit and timed stop tests |
| MPX-U11 RuntimeProvider | Trusted installed pure mapping/admission and bounded effect/observation/cleanup contract; real installations separately admitted | owned test providers verify mechanics only; Autoverse/native provider admission unfinished |

Sources: src/xverse/maestro/execution/{inspection,admission,planning,permissions,
runtime,evidence,process}.py and public __init__.py. Tests: tests/maestro_public/.
Prototype fixtures cannot satisfy the full user's native-X-COM/Autoverse/Studio
goal. Provider callbacks are cooperative trusted code, not a hostile-code sandbox;
resource-tree containment, Windows and physical effects are unsupported.
