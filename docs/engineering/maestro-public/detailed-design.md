# Public execution detailed design

Status: proposed runtime design; static inspection alone is implemented so far.

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

## Verification and delivery

Rebuild installed packages when force-included source changes; do not test stale
copied modules. Verification covers zero effects before admission, edited-input
behavior, real per-element process/container ownership, actual native exchange,
Argus verification, gap/pressure/writer failures and GUI cross-view navigation.
Separate review and user acceptance precede exact platform-main integration.
