# X-COM provider composition and owned loopback provider

State: **READY_FOR_REVIEW**

Capability: `FEAT-e17d4ee9f29848f5` (`XCOM-PROVIDER-LOOPBACK`)

Evidence repair: `FEAT-7795845feff2492c` (`XCOM-PROVIDER-EVIDENCE-REPAIR`)

Evidence-repair baseline: `BASE-d84842bcd394994eed06`

Delivery identity is supplied by the SESN host feature and evidence records through
`SESN_CANDIDATE_REVISION`; the host requires that value to equal `git rev-parse HEAD` for the
immutable candidate under measurement.

This C++20 prototype implements only explicit source-linked provider composition and an owned
in-process loopback provider on the accepted core-types and endpoint/route lifecycle baseline. The
loopback proves bounded mechanics; it is not evidence of network, protocol, timing, reliability,
compatibility, or production fidelity. This bounded evidence repair addresses R4-R6 from
`REVIEW-c07845b2416645ef` of the historical rejected revision
`0c0c82457d111a33828d9d6c168875e8caf17611` without adding capability scope.

## Public contract and policy limits

`ProviderDescriptor::create` owns a logical provider identity, canonical source contract version,
source-link identity, supported interaction/delivery/ordering masks, and nonzero payload, route, and
queue limits. Version `1.0.0` is the only admitted source contract. `ProviderComposition` retains at
most eight explicitly supplied provider object addresses. There is no directory scan, discovery,
dynamic library, address, middleware, socket, or stable binary plugin ABI.

The owned `LoopbackProvider` declares all four interaction families, best-effort delivery, and
per-route FIFO ordering. Its hard policy limits are four simultaneous route records, eight items per
route, and the accepted core item maximum of 65,536 payload bytes. A prepared route selects a smaller
nonzero payload and queue bound. The complete fixed item arrays exist when the provider object is
constructed; submit never grows storage.

`ProviderRouteHandle` binds the issuing composition identity, provider object identity, exact
provider registration generation, provider and route identities, plan digest, provider route
generation, lifecycle route generation, and both endpoint generations. Constructors are private.
Every operation authenticates the complete binding. Even the same provider object explicitly
registered in two compositions cannot transfer a handle between them. Names and addresses never
establish ownership.

## Validation ownership and exact operation sequence

The lifecycle controller owns logical endpoint/route declarations, handles, generations, and
transitions. Its authenticated `endpoint_declaration` and `route_declaration` accessors return owned
copies only for exact current handles. `ProviderComposition` owns provider registration,
cross-boundary validation, public provider-route authority, and lifecycle/provider sequencing. A
provider owns its bounded route and queue resources and defensively validates the internal binding
and token it receives; it does not mint public authority or change lifecycle-controller state.

The exact preparation, activation, and submission sequence is:

1. The caller declares and validates the source endpoint, destination endpoint, and route through
   `LifecycleController`. Endpoint activation may occur before preparation; the route remains
   validated.
2. `ProviderComposition::prepare_route` authenticates the three exact handles and obtains their
   retained declarations. It compares the complete route, endpoint identities, provider, digest,
   contract, endpoint directions, current generations and states, requested interaction and policy
   capabilities, and finite payload/queue limits before dispatch.
3. Composition calls the explicitly registered provider's `prepare` with an owned
   `ProviderRouteBinding`. The provider may allocate only its fixed route resource and returns a
   non-authoritative `ProviderRouteToken`; preparation emits no traffic. Composition alone wraps the
   token and lifecycle bindings in the public `ProviderRouteHandle`.
4. After both endpoints are active, `ProviderComposition::activate_route` reauthenticates the exact
   lifecycle resources, calls provider `activate`, and only after provider activation succeeds calls
   `LifecycleController::activate_route`. The provider activation operation itself cannot mutate the
   lifecycle controller. A repeated activation of an already active exact pair remains bounded and
   does not repeat the lifecycle transition.
5. `ProviderComposition::submit` first authenticates the public handle, exact active lifecycle route
   and endpoint generations, retained provider identity, and every item contract identity/version,
   interface, schema identity/version, interaction kind, logical source endpoint, route, provider,
   and payload limit. Only then does it dispatch the internal token and item to the provider, which
   retains defensive validation and returns a bounded outcome.

Any composition-side rejection occurs before the corresponding provider operation and preserves
provider, route, endpoint, and queue state. The activation order is therefore prepare provider,
activate provider, activate lifecycle route, then submit; the documentation does not imply that
provider activation follows lifecycle-route activation.

## Independent source-level provider extension

`CommunicationProvider` is a source-level C++ interface for explicitly linked objects. A conforming
implementation supplies an immutable descriptor, compatibility check, nonzero instance identity,
and bounded prepare/activate/submit/receive/drain/close/state/reconcile operations. It returns owned
`ProviderStatus`, `ProviderResult<ProviderRouteToken>`, and `ProviderRouteStateValue` values.
`ProviderRouteToken` and `ProviderRouteStateValue` are deliberately non-authoritative; only
`ProviderComposition`, through private constructors, can issue public `ProviderRouteHandle` and
`ProviderRouteSnapshot` values.

The separately implemented `IndependentProvider` test fixture derives from the public interface,
registers without loopback internals, prepares and activates one fixed resource, rejects a malformed
item before provider dispatch, and exchanges an exact owned item. This proves source-level
replaceability, not a stable binary ABI, dynamic provider loading, discovery, or transport
interoperability.

Registration copies `descriptor()`, evaluates `descriptor_compatible()`, and captures
`instance_id()` before acquiring the composition registry mutex. The mutex then protects only fixed
registry lookup/mutation. All route operations copy the selected provider pointer and retained
metadata under that mutex, release it, and only then invoke a provider virtual method. The re-entry
fixture registers another provider from a descriptor callback, demonstrating that no provider call
is made under the composition lock. Each provider remains responsible for serializing its own shared
state; `LoopbackProvider` uses one mutex and invokes no callback while it is held.

## Item ownership, FIFO, and saturation

Submit accepts only an exact active provider-route handle. Accepted items are copied into
provider-owned `CommunicationItem` storage. Caller storage may be destroyed as soon as submit
returns. Receive is pull-based and returns a new owned result value. No queue reference, view, or
callback escapes the provider lock.

Each route has an independent circular FIFO. When full, submit returns `queue-saturated`, leaves the
head, size, capacity, and every accepted item unchanged, and allocates no storage. After one receive,
one new item may be accepted. Best-effort means acceptance into this owned in-process queue only; it
does not strengthen reliability or network delivery claims.

## Drain, close, reconciliation, and lifetime

Drain authenticates the exact active handle, asks the provider to stop new submissions, and only
after provider success transitions the lifecycle route to draining. All accepted items remain
available to receive. Close reports `queued-items-remain` without mutation until the queue is empty;
it then releases the provider resource before closing the exact lifecycle route. A safe close repeat
remains closed until same-identity recreation replaces the slot with higher provider and lifecycle
route generations. The earlier handle then fails authentication.

Reconciliation returns an owned public snapshot only when the composition validates the provider's
internal token, state and queue capacity and the provider and lifecycle states and generations agree.
Failed, closed-out-of-sequence, foreign, or absent resources report `interrupted-resource` or
`invalid-provider-route-handle` without inferred health.

Callers own each provider object and lifecycle controller and must keep them alive for longer than
the composition and all operations using issued handles. Composition retains non-owning provider
pointers; handles and results own values but do not retain provider resources. Concurrent operations
through composition are supported under the documented locks. Concurrent independent mutation of
the same lifecycle resources outside provider composition is unsupported and is rejected as a
lifecycle mismatch where observable.

## Stable outcomes

Every result owns its optional value and maps its outcome to stable `XCOM-PROV-*` code and message
text. Success codes are `S001` through `S008`, empty queue is `I009`, and rejection codes are `E010`
through `E028`. Rejections cover saturation, descriptor/registry failures, unsupported source
contract or capabilities, payload/queue/route limits, invalid handles, lifecycle/route/provider/item
mismatch, inactive state, queued close disposition, and interrupted reconciliation. Unknown enum
values map to `XCOM-PROV-E000`; they are never accepted as capabilities.

## R4-R6 evidence-repair disposition

| Finding | Disposition and evidence |
|---|---|
| R4 | Repaired. `src/xverse/xcom/src/provider.cpp` is allocated reciprocally to `XCOM-PROV-005` submission and `XCOM-PROV-008` drain/close cleanup, in the requirement, unit-design, and reverse-artifact edges. The allocation reflects composition operations that authenticate the issued handle before dispatch or resource release; it does not transfer raw provider mutation authority to consumers. |
| R5 | Repaired. Preparation calls the provider with a non-authoritative binding/token and, only on successful preparation, composition issues the public `ProviderRouteHandle`. Composition then activates the provider before transitioning the lifecycle route. The sequence is represented in this document and the traceability evidence, with no inferred authority from names or addresses. |
| R6 | Repaired. Delivery evidence is bound to the SESN host feature/evidence records and their supplied `SESN_CANDIDATE_REVISION`, which must exactly equal `git rev-parse HEAD`. Historical authority and verification task revisions remain predecessor evidence and are not delivery identity. |

## Excluded behavior and compatibility impact

This slice adds one source-level library and public headers. The repair adds authenticated read-only
lifecycle declaration accessors and non-authoritative provider result types while preserving accepted
core-type and endpoint/route lifecycle semantics. It adds no dependency and performs no filesystem,
environment, process, socket, network, secret, legacy-repository, XDL compilation, observation,
stimulation, session/permit, time-authority, journal, service-emulation lease, Protobuf/gRPC gateway,
dashboard, Argus, Maestro, Faults, or compatibility-adapter operation. No persistent state or
automatic recovery is claimed.

## SWE.1-SWE.6 work products and reciprocal traceability

SESN produced the original capability work products under
`specs/014-feat-e17d4ee9f29848f5`: software requirements (SWE.1), architecture and models (SWE.2),
detailed design and seven unit specifications (SWE.3), unit/lint/static measures (SWE.4), integration
checks (SWE.5), and requirement validation and traceability (SWE.6). The bounded repair work products
under `specs/015-feat-80e5f94a8484412b` preserve the same eleven accepted requirements and seven unit
design identities. The dependency-ordered evidence-repair work product under
`specs/016-feat-7795845feff2492c` records the R4-R6 corrections. Its predecessor task revisions are
task evidence only, not a delivery-candidate claim. These artifacts support an
Automotive-SPICE-inspired workflow; they do not claim certification or a capability level.

The reciprocal register is
`docs/xcom/provider-composition-loopback-traceability.json`. It maps every requirement to design,
code, tests and authoritative measures, and maps every listed artifact and design back to its
requirements. Evidence-repair metadata records the rejected review/revision, the host-bound delivery
candidate binding, the three dependency-ordered repair tasks, and the R4-R6 evidence paths without rewriting
the original capability identity.

## REF-002 SADS disposition

The capability-007 allocation remains authoritative. This provider slice records every direct
communication ID so none disappears:

| Requirement IDs | Disposition in this slice | Rationale |
|---|---|---|
| `XVE-SYS-0139`, `XVE-SYS-0140`, `XVE-SYS-0142`, `XVE-SYS-0145`-`XVE-SYS-0147`, `XVE-SYS-0149`, `XVE-SYS-0152`, `XVE-SYS-0154`, `XVE-SYS-0156` | partial | The bounded source-level provider and loopback contribute local contract, lifecycle, item, and failure evidence; broader capability-007 behavior is not claimed. |
| `XVE-SYS-0141` | deferred | Protocol/provider adapters are separate capabilities. |
| `XVE-SYS-0143`, `XVE-SYS-0157` | deferred | Registry discovery and dynamic reconfiguration are explicitly excluded. |
| `XVE-SYS-0144`, `XVE-SYS-0153`, `XVE-SYS-0155` | deferred | Security and deployment capabilities own these requirements. |
| `XVE-SYS-0148`, `XVE-SYS-0150`, `XVE-SYS-0151` | deferred | Record/replay, edge/cloud, and Argus adapters are separate capabilities. |
| `XVE-SYS-0158` | partial | Stable bounded failure outcomes are implemented; automatic Faults/Runtime recovery remains deferred. |

The shared SADS IDs listed in `specs/007-xcom-core/reference-traceability.md` remain allocated to
their owning capabilities. This slice neither supersedes nor conflicts with them.

## Verification and exact-revision evidence

The admitted offline verification commands are:

```bash
export SESN_CANDIDATE_REVISION="$(git rev-parse HEAD)"
python3 scripts/validate_xcom_provider_loopback.py --unit
python3 scripts/validate_xcom_provider_loopback.py --lint
python3 scripts/validate_xcom_provider_loopback.py --static
python3 scripts/validate_xcom_provider_loopback.py --integration
python3 scripts/validate_xcom_provider_loopback.py --all
```

The provider validator binds the host-supplied `SESN_CANDIDATE_REVISION` to `git rev-parse HEAD`.
The SESN host feature and evidence records identify the exact immutable candidate under measurement;
the static measure covers admitted
compiler analysis, strict warning-as-error Doxygen, fixed-storage and forbidden-access scans,
symbol/dependency isolation, the F1-F6 verification fixtures, and reciprocal traceability.

Host measure results and independent review are recorded against the same host-bound candidate by
SESN; this document does not embed or independently restate that candidate revision.

The complete measure also invokes the accepted endpoint/route lifecycle validator with explicit
additive paths; that validator invokes the accepted core-types validator the same way. Tests cover
all interaction families, multiple bounded routes, FIFO bytes and provenance, saturation
retention/recovery, every declared compatibility boundary, foreign and stale handles,
drain/close/recreation, interrupted reconciliation, independent provider integration, registration
re-entry, overlapping producer/consumer mutation with unique delivery, and a separately compiled
public consumer.

## Maturity and limitations

This is repaired prototype evidence at `READY_FOR_REVIEW`, awaiting the separately required exact
candidate review and user validation. It demonstrates only owned in-process behavior on the admitted
Linux x86-64 build envelope. Fixed limits are policy choices for this slice, not measured production
sizing. The implementation makes no stable ABI, process-crash durability, real-time, throughput,
latency, networking, hardware, interoperability, legacy parity, migration, or production-readiness
claim.
