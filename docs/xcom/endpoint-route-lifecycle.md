# X-COM endpoint and route lifecycle

State: **READY_FOR_REVIEW**

Feature: `FEAT-5cfe89f5d1214030`

Baseline: `BASE-39bb479b857541a99bab`

This prototype control-plane slice adds domain-neutral logical endpoint and route declarations to the
accepted C++20 X-COM core-types target. It does not compose a provider, transport data, retain a
`CommunicationItem`, compile XDL, or access an external system.

## Public contract

`EndpointSpec::create` binds a bounded logical endpoint identity, canonical 64-character lowercase
plan digest, explicit logical provider identity, contract, and one direction declared by that contract.
`RouteSpec::create` copies two endpoint declarations only when they have distinct identities and share
the exact plan, provider, contract, and source/target directions. Neither type contains an address,
protocol, physical-device identity, or domain-specific field.

`LifecycleConfiguration::create` admits nonzero caller capacities no greater than the compile-time
maxima of 32 endpoints and 32 routes. `LifecycleController` always contains fixed `std::array`
storage at those maxima and considers only the configured prefix. Declarations reuse empty or closed
slots and never grow storage. A duplicate nonclosed identity or exhausted configured capacity fails
without replacing a record.

Each successful declaration returns an opaque typed handle containing the issuing controller identity,
resource kind, logical identity, exact plan digest, and a controller-wide monotonically advancing
nonzero generation. Construction is private. Copies preserve the exact binding. A foreign, stale,
unknown, wrong typed, digest-mismatched, or generation-mismatched handle cannot mutate a resource.
Typed endpoint and route operations make wrong-kind mutation a compile-time error; the immutable
`kind()` accessor makes that binding inspectable.

## Lifecycle and idempotence

The permitted state sequence is:

```text
declared -> validated -> active -> draining -> closed
    |           |          |          |
    +-----------+----------+----------+-> failed -> closed
```

Repeating validation in `validated`, activation in `active`, drain in `draining`, failure in `failed`,
or close in `closed` returns the existing state and generation. Skipped or terminal transitions fail
without mutation. A closed handle remains queryable and its close is idempotent until the identity's
slot is recreated. Recreation issues a strictly higher generation, after which the earlier handle is
stale.

Route validation authenticates the current route, source, and destination handles and requires both
endpoints to be validated or active. Route activation repeats every exact identity, plan, provider,
contract, and direction check and additionally requires both endpoints to be active. An endpoint may
not drain or close while any declared, validated, active, draining, or failed route refers to it; the
route must be explicitly closed first.

Failure is allowed from declared, validated, active, and draining. Failed resources remain owned and,
for routes, continue to hold their endpoint-use relationship until explicit close.

## Ownership, lifetime, and concurrency

Specifications, handles, snapshots, results, and diagnostics own all returned bytes in bounded value
storage. No factory retains caller views. A snapshot is a point-in-time owned value and does not change
after a controller transition. A handle does not extend a controller or record lifetime; using it with
another controller or after same-identity recreation is rejected.

The controller is non-copyable. One internal mutex serializes declaration, authentication, query,
compatibility checking, transition, and record mutation. No callback runs under the lock. Immutable
values support concurrent reads, and safe repeated transitions under contention converge on one state
without duplicating a record or advancing its generation.

## Deterministic failure behavior

Lifecycle additions preserve `XCOM-TYPE-E001` through `XCOM-TYPE-E005` and add only:

| Code | Meaning |
|---|---|
| `XCOM-LIFE-E006` | malformed exact plan digest |
| `XCOM-LIFE-E007` | configured capacity exhausted |
| `XCOM-LIFE-E008` | duplicate nonclosed logical identity |
| `XCOM-LIFE-E009` | foreign, stale, unknown, or otherwise invalid handle |
| `XCOM-LIFE-E010` | invalid lifecycle transition |
| `XCOM-LIFE-E011` | endpoint retained by a nonclosed route |
| `XCOM-LIFE-E012` | route/endpoints are incompatible |
| `XCOM-LIFE-E013` | controller generation space exhausted |

Every rejected operation returns a sorted immutable `DiagnosticSet`. Tests compare exact serialized
bytes and snapshots before and after rejection.

The ordering-key capacity is a compile-time expression covering worst-case escaping of every phase,
severity, code, identity, reason, and correction byte plus all separators. Every append checks the
remaining fixed storage, so a future stable enum string that exceeds its published bound fails
diagnostic construction without an out-of-bounds write. Maximum-length pipe and backslash escaping
cases are regression tested.

## Review-finding closure

The repair of `REVIEW-5062aa21bd884561` independently exercises route validation and activation with
stale and foreign route, source, and destination handles; inactive endpoints; and retained-endpoint
closure. Each rejection compares exact diagnostic bytes and fresh route/source/destination snapshots.
The separate consumer also performs safe repeats, observes an invalid transition without mutation,
closes the route and both endpoints, and recreates all three resources with newer generations.

Traceability includes all eleven lifecycle requirements and all seven unit designs. The validator
loads the SESN verification-measure artifact as the authority and requires each requirement's check
allocation to equal that authority in both directions.

## Validation

Run the five admitted offline measures with the candidate revision bound to the unchanged Git `HEAD`:

```bash
export SESN_CANDIDATE_REVISION="$(git rev-parse HEAD)"
python3 scripts/validate_xcom_endpoint_route_lifecycle.py --unit
python3 scripts/validate_xcom_endpoint_route_lifecycle.py --lint
python3 scripts/validate_xcom_endpoint_route_lifecycle.py --static
python3 scripts/validate_xcom_endpoint_route_lifecycle.py --integration
python3 scripts/validate_xcom_endpoint_route_lifecycle.py --all
```

The complete measure also reruns the accepted core-types validator against the current integrated
candidate. Its ownership check is extended in memory only with this task's exact owned paths; no core
acceptance criterion is disabled.

## Maturity and limitations

This is an uncommitted prototype candidate awaiting Codex and user review. Its tests demonstrate only
bounded in-process lifecycle mechanics on the admitted Linux x86-64 build envelope. It makes no ABI,
performance, transport, provider, compatibility, distributed identity, crash-recovery, or production
readiness claim.
