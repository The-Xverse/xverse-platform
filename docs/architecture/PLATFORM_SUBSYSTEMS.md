# X-Verse vNext platform subsystems

**Status**: Architectural target. Only capabilities identified as implemented in their Spec Kit
packages and validation records exist today.

ADR-0016 assigns stable names to three major platform subsystems. The intended monorepo structure is:

```text
xverse-platform/
├── xdl/
│   ├── metamodel/
│   ├── loader/
│   ├── validator/
│   ├── compiler/
│   └── runtime-plan/
├── src/xverse/
│   ├── core/
│   ├── maestro/       # Maestro: orchestration
│   ├── runtime/
│   ├── xcom/          # X-COM: communication
│   ├── devices/
│   ├── time/
│   ├── faults/
│   ├── argus/         # Argus: observability
│   ├── plugins/
│   └── sdk/
└── cli/
```

## Naming boundary

| Name | Responsibility target | Current maturity |
|---|---|---|
| Maestro | Plan and coordinate declared lifecycle actions and experiments. | Architectural target; early M3 lifecycle mechanics currently remain in `xverse_xdl`. |
| X-COM | Realize declared communication semantics through explicit provider/protocol bindings; expose controlled observation and stimulation boundaries for validation tools. | Next platform-first capability; no X-COM runtime exists. |
| Argus | Collect, store/export, query, and visualize declared observations and experiment evidence, including X-COM tap streams. | Architectural target; M3 evidence journaling is a precursor, not Argus. |

The current `xverse_xdl` API is pinned by the M3 compatibility conformance package. Moving its catalog,
planning, lifecycle, or evidence code into the future namespaces requires a separate Spec Kit feature,
ADR-backed API transition, compatibility tests, and a reviewed release. Empty placeholder packages do
not establish progress toward these capabilities.

## Delivery order

[ADR-0018](../adr/ADR-0018-platform-first-delivery-sequence.md) supersedes the original
legacy-parity-first milestone order. Platform-owned baseline capabilities and their extension contracts
are implemented and accepted before target-specific legacy integrations resume. For X-COM,
[ADR-0019](../adr/ADR-0019-xcom-validation-and-observation-boundaries.md) requires observation and
controlled stimulation to be designed with the normal communication path. Dashboards and persistence
remain Argus or third-party responsibilities.

## SADS component coverage

The supplied SADS also requires simulation/model execution, an FMI/FMU boundary, runtime management,
user interfaces, results management, security, time, and fault recovery. ADR-0018 includes these in the
platform-baseline gate even when they do not yet have product names or source packages. The
[SADS requirements traceability](SADS_REQUIREMENTS_TRACEABILITY.md) allocates all 275 source IDs to
their owning future capabilities. Listing an owner is an architectural target, not an implementation
claim or permission to scaffold its package.
