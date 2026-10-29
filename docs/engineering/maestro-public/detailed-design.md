# Public execution detailed design

Status: prototype static/effective inspection, host-bound dispatch, Linux child
ownership and real Argus lifecycle persistence implemented. Native integration,
full acceptance and platform-main delivery remain unfinished.

## Existing boundaries and reuse

Use the actual public XDL compiler and its compiled bindings, selection,
provenance, lifecycleIntent, dependencyOrder and time metadata. The existing
Maestro prepare_lifecycle is restricted to bound component instances, one
simulation clock and a closed provider registry. It remains unchanged: a new
public execution capability must explicitly support declared logical devices,
host time and registered providers without flipping that preparation's permanent
ready_for_execution=false flag or manufacturing private-runtime approval records.

## Host provider contract and effective configuration

A trusted installed provider implements side-effect-free effective preparation
against the immutable submission and compiled binding. It returns actual effective
XDL/configuration identities and a bounded frozen configuration consumed by its
runtime operations. The platform independently compiles those effective inputs
and rejects unsupported semantics or any input/plan mismatch before effects.
Expected hashes or echoed request fields alone are not execution evidence.

Provider installations, fixed executables, environment/secret references,
permissions and binary/configuration identities are host inputs. The project
cannot install code or supply commands. Runtime registration must include a
reviewed implementation identity and verified installation; the static
TargetBinding implemented initially is not sufficient for runtime admission.

## Per-element lifecycle expansion

Providers may expand each actual compiler binding into bounded preparation,
start, readiness, stop and cleanup operations referring only to that binding's
stable logical identity and trusted provider support resources. They declare
readiness dependencies on other selected binding phases. The platform validates
all references, finite budgets, phase transitions and cycles before execution,
schedules eligible operations, observes receipts and performs bounded reverse
cleanup. The expansion is derived provider realization policy bound into the
host/runtime inspection identity, not another System or graph-library definition.

This supports an unchanged external simulator whose server must be prepared before
other units start, while its vehicle client starts only after those units are
available. No industry names or dispatch enter shared Maestro scheduling code.
Readiness receipts distinguish process/container liveness, interface readiness
and functional observations; missing health contracts cannot become invented
functional success.

## Real platform demonstration, including existing Autoverse

An owned neutral native exchange is useful for adapter verification but does not
replace integration with the user's current demonstration. The Studio provider
must preserve the existing public component CLIs and exact owned resources while
delegating per-binding lifecycle orchestration to the new public Maestro service.

For native X-COM, a reviewed adapter must place real C++ X-COM exchange into a
declared route. Merely copying Zenoh events into a panel labelled X-COM is not
acceptable. One candidate route uses separate owned Zenoh endpoints around the
VCU's existing public configurable connection, with the native X-COM provider
carrying actual traffic between them. This proposal requires native binary,
profile/route, transport and failure verification before implementation admission.
No companion VCU, simulator, S-CORE or cluster source change is authorized.

Real source message correlation should be propagated where the public transports
support it, preserving payload compatibility. A run-level correlation is distinct
from per-message causation. Deferred legacy processing which drops causation must
remain unknown; temporal proximity cannot manufacture an end-to-end cause.

## Evidence and projections

Maestro persists actual lifecycle receipts through public Argus APIs. Native
X-COM observations retain their provider/route/interface identity, original clock,
sequence, outcome, correlation/causation and payload policy. The three Studio views
query original source references and share one verified run/plan/element context.
Argus plan.semanticDigest binds the compiled plan, not the distinct input-semantic
digest. Reader recorded/assessed outcomes and incompleteness remain separate.
Browser payload/log filtering and live snapshot pagination must be implemented
before exposing the internal original-record reader online.

## Public host lifecycle service design

LifecyclePhase realizes one compiled logical binding under its registered provider.
The graph must cover prepare/start/ready for every binding, validate cross-provider
references and cycles, and make every acquiring phase an ancestor of an actual
readiness phase. Topological tie-breaking does not create causal dependencies.
Provider interpretation of scenario steps, time domains, faults and other semantics
remains mandatory; graph validation alone cannot claim those features are supported.

HostExecutionPermit is a trusted in-process host input, never deserialized from
browser/project content. It binds the exact host, preparation and lifecycle graph,
environment, external authorization reference and at most one hour of validity.
It permits owned simulated/virtual resources only. The application registers this
authority separately from imported documents; no legacy lane/physical/containment
approval is minted here. Expiry prevents new acquisitions, never owned cleanup.

The service persists an exclusive start claim before effects; retries compare
the whole request identity. An existing claim without its original in-memory
handles is unknown, never permission to replay. Argus opens before provider launch
and records each intent before dispatch; failures after effects still require
cleanup of every attempted mutating phase, including a phase that raised before
returning a handle. Providers must retain their own exact ownership receipts and
implement bounded cleanup for partially completed calls. No PID/group/name lookup
can recover signal authority after a lost opaque handle.

Provider methods are installed trusted code with cooperative finite deadlines;
they are not a hostile-plugin sandbox. A provider that fails to honor its bound
must remain an explicit unknown/failed result. Native Linux ownership verification
uses original child handles and kernel pidfds where supported. It does not
reuse the older process-group stop implementation or infer descendant ownership.

EffectiveConfiguration now separately freezes installation_digest. A runtime
provider reports its actual current installation identity, and admission compares
it before every dispatch. FixedProcessInstallation hashes the fixed executable,
argv, cwd, explicit environment and content pins; verify independently checks file
contents. Static providers may omit this identity but cannot execute. Runtime host
grants also bind the actual root inode/device/path, kernel, user, host identity and
host-owned time limits. No paths/environment strings enter public summaries.

One service admits at most one unresolved active experiment and at most128 durable
run claims. A previous service's unreconciled claims bar new activation. Restarted
runs remain unknown even if a previous in-memory observation was terminal: this
prototype does not reconstruct resource authority from files. Host operators must
reconcile affected installations separately; a new directory is not a new resource
permission. The installed provider must enforce its installation-wide reservation.

Default total run budget is600seconds, capped at3600 and at permit expiry; a host
timer requests cancellation and cleanup independently of the browser. Cooperative
provider deadlines remain required. Cleanup has an aggregate30second budget capped
at60seconds; exhausted operations remain unknown. Reads are inert historical
snapshots. Explicit observe checks actual provider resources, records its original
clock and initiates cleanup on exit/uncertainty. It does not assert functional fitness.

The original service directory is retained through an owned Linux directory FD.
Argus uses its public API beneath /proc/self/fd/<fd>, so lexical root replacement
blocks new dispatch without redirecting cleanup evidence into a replacement root.
The actual public writer/reader probe and runtime root-replacement test verify this
behavior. Argus append is followed by its public flush_buffer durability operation.
Run correlation names the original start-request event, matching Argus's reference
contract; no unresolved generated placeholder is substituted for a predecessor.

## Verification and delivery

Rebuild installed packages when force-included source changes; do not test stale
copied modules. Verification covers zero effects before admission, edited-input
behavior, real per-element process/container ownership, actual native exchange,
Argus verification, gap/pressure/writer failures and GUI cross-view navigation.
Separate review and user acceptance precede exact platform-main integration.
