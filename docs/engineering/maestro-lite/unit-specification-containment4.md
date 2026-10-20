# U4 descriptor/C1 boundary component unit specification

Revision: ML3-CONTAINMENT4-2026-10-18-v4. Status: partial implementation candidate.
Exact signatures: `ProcessBoundaryOps.create_frozen(self, descriptor, **options)` and
`residual_membership(self, descriptor)`; BoundaryOps matches. FixtureBoundaryOps
and the complete broker/proxy integration remain pending; no fixture substitute
is presented as this kernel backend.

| Surface | Invariant | Positive/negative measure |
| --- | --- | --- |
| Descriptor/admission/limits | Strict immutable run/unit/generation/boundary/creation epoch; explicit sessions, provenance and finite original deadline | Exact identity, booleans/invalid/overlarge values reject; no mutable caller state retained |
| Original registry | Original object/process, retained actual cgroup parent, exact entry and private C1 identity | Copy/fork/replacement/fields-only reconstruction reject; no adoption |
| create_frozen | Reserve before allocation, bind FDs, C1 before child insertion, verify frozen; empty closed options | Real empty cgroup success; unknown options/epoch/cancel reject before mkdir; partial effects remain tracked |
| residual_membership | Leader-independent full frozen scope, bounded stable samples; no missing→empty | Real frozen clone3 children and surviving descendant; nested/changed/malformed/failed reads reject |
| force_cleanup | Original C1 only; fixed deadline, exact kill, verified empty and removal before FD disposal | Real scoped force and untouched sentinel; denied kill/remove, expiry/authority loss remain unresolved |
| CP-02/CP-03 | Approved empty reservation or original C1 may release verified empty allocation; no invented stop | Inject failure before C1 registration, compare surviving/lost/expired branches; no child termination event for empty allocation |
| Cancel/late result | Current epoch advances once, creation epoch fixed; no new Stage after close | Cancel before/during allocation; late frozen result cannot commit success; cleanup still addresses original epoch |
| Tombstone | Exact terminal outcome cached; no recreated resources or fresh observation after disposal | Repeated cleanup is idempotent; membership after release is unavailable |

Source work products precede code. Tests derive outcomes from descriptor C02–C09 and
the above kernel contracts, not copied implementation transitions. A native fixture
and test-only thaw are not an admitted launcher. No actual ML3 run is created. Freeze
exact source/helper/wheel identities, run source-excluded consumer/regression checks,
and record separate read-only findings before successor repairs. All 24 requirements,
18 allocation-only/unvalidated parents and full nine runtime cases remain in scope.
