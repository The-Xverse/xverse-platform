# xverse-platform

X-Verse vNext is a multi-industry cyber-physical systems experimentation platform under development.

Owns the domain-neutral platform, authoritative architecture decisions, and cross-repository M0 inventory. Future code belongs here only after its capability specification and gates are satisfied.

## Current maturity
This repository contains engineering setup, approved M0 discovery, M1 metamodel, the approved M2 XDL
Core v0.1 specification/schema package, and the approved capability 004 prototype loader, validator,
normalizer, local CLI, derived compatibility catalog, deterministic lifecycle planner, and isolated
fixture runtime. It has no legacy compatibility wrapper, registry, legacy adapter, or executable
blueprint. Legacy capabilities documented by M0 have not been executed or certified by this work.

## Engineering workflow
Spec Kit **0.14.0** is initialized with its official generic integration, Bash scripts, templates,
and bundled workflow. The generic integration uses `.specify/commands` because this workspace's
`.agents` and `.codex` directories are read-only. No permissions or agent directories were changed.

Read [engineering rules](AGENTS.md) and the [constitution](.specify/memory/constitution.md).
Ask the agent to read and follow `.specify/commands/speckit.<stage>.md`, supplying the feature
request as its input. Stages: constitution, specify, clarify, plan, tasks, analyze, implement.
Follow implementation with a separate architecture review. These Markdown commands are not shell
executables; slash-command discovery is not assumed for the generic integration.

The [M0 feature](specs/001-legacy-repository-inventory/spec.md) and its tasks live only in
xverse-platform. Run M0 prerequisite and evidence checks from that repository; companion
repositories intentionally have no active feature pointer until their own first capability.
See the [M0 quickstart](specs/001-legacy-repository-inventory/quickstart.md).

## Architecture and review gates
Dependencies flow from blueprints through domain profiles and XDL/platform APIs to runtime
abstractions. Existing production repositories remain read-only. Features must pass architecture,
compatibility, runtime (when applicable), test, reproducibility, and documentation gates.

See [architecture guidance](docs/architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md)
and the [legacy inventory](docs/legacy/REPOSITORY_INVENTORY.md). Relative cross-repository
links assume sibling checkouts with their repository names, as in this workspace.

The supplied SADS v0.1 remains a target-architecture input. Its 275 requirement IDs are accounted for
in the public-safe [SADS traceability register](docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md);
allocation or deferment never constitutes implementation evidence.

The future orchestration, communication, and observability subsystems are named **Maestro**,
**X-COM**, and **Argus**, with Python namespaces `xverse.maestro`, `xverse.xcom`, and `xverse.argus`.
See the [subsystem map](docs/architecture/PLATFORM_SUBSYSTEMS.md) and
[ADR-0016](docs/adr/ADR-0016-platform-subsystem-names.md). These names currently identify
architectural targets; their packages are introduced only through separately accepted capabilities.

[ADR-0017](docs/adr/ADR-0017-controlled-derivative-rebuilds.md) authorizes a build-only controlled
derivative strategy in `xverse-compat`. Its reusable envelope is implemented with synthetic fixtures;
the restricted SD-0001 patch, immutable containment environment, and every runtime gate remain pending.

[ADR-0018](docs/adr/ADR-0018-platform-first-delivery-sequence.md) records the later formal decision to
implement and accept the main platform capability baselines before target-specific legacy integration.
SD-0001 derivative and parity work are therefore deferred. The next planned capability is X-COM core,
including the validation observation/stimulation boundaries in
[ADR-0019](docs/adr/ADR-0019-xcom-validation-and-observation-boundaries.md).

M0 documents are intended for public-safe review. Referenced private GitHub evidence requires
existing repository access. Review of inventory boundaries, classifications, interfaces, and
dependencies is required before M1. Changes from this delivery remain local and unpublished.

## License
See [LICENSE](LICENSE); the existing license is unchanged.

## M0 review package

The [inventory](docs/legacy/REPOSITORY_INVENTORY.md) accounts for 29 legacy repositories and all three
vNext repositories. See the [architecture review](docs/reviews/001-legacy-repository-inventory-architecture-review.md),
[validation results](specs/001-legacy-repository-inventory/validation.md), and
[confirmed human review](docs/reviews/M0_REVIEW_CHECKLIST.md). The user confirmed M0 on 2026-09-20,
satisfying the entry gate to M1 specification/design. The [supplemental reference register](docs/architecture/REFERENCE_REGISTER.md)
records the technical synthesis and SADS without copying internal originals into this repository.
## M1 architecture package
The approved [domain-neutral metamodel](docs/architecture/METAMODEL.md), its
[conceptual diagram](docs/architecture/METAMODEL_DIAGRAM.md), and ADR-0005–ADR-0008 are complete
as architecture documentation. See the [M1 specification](specs/002-domain-neutral-metamodel/spec.md),
[validation record](specs/002-domain-neutral-metamodel/validation.md),
[architecture review](docs/reviews/002-domain-neutral-metamodel-architecture-review.md), and
[human decision record](specs/002-domain-neutral-metamodel/checklists/acceptance.md).
The M2 entry gate was satisfied for specification/design; loader/runtime implementation remains
outside the approved scope.

## M2 XDL Core package

The approved [XDL Core v0.1 specification](xdl/specification/XDL_CORE_V0_1.md) defines System,
Component, Deployment, Scenario, and Profile resources with strict Draft 2020-12 schemas and
public-safe YAML examples. The [M2 feature](specs/003-xdl-core/spec.md),
[validation record](specs/003-xdl-core/validation.md), and
[architecture review](docs/reviews/003-xdl-core-architecture-review.md) describe the scope and
evidence. The user approved the [M2 acceptance checklist](specs/003-xdl-core/checklists/acceptance.md)
on 2026-09-20. The local validation script is documentary acceptance tooling; it is not a production
XDL loader or general JSON Schema implementation.

## Prototype XDL tooling

Capability 004 implements the approved v1alpha1 document boundary as the local `xverse_xdl` Python
package and `xdl` command. It loads bounded YAML 1.2/JSON inputs, validates the closed supplied graph
with packaged Draft 2020-12 schemas, validates extensions against explicitly supplied local Profile
schemas, and returns immutable normalized resources. It performs no discovery or network access.

Install the locked environment and validate the approved example graph:

```sh
uv sync --frozen
uv run xdl validate --format text \
  --profile-schema tests/fixtures/measurement-profile.schema.json \
  xdl/examples/v1alpha1/profile.xdl.yaml \
  xdl/examples/v1alpha1/component.xdl.yaml \
  xdl/examples/v1alpha1/system.xdl.yaml \
  xdl/examples/v1alpha1/deployment.xdl.yaml \
  xdl/examples/v1alpha1/scenario.xdl.yaml
```

See the [capability quickstart](specs/004-xdl-loader-validator/quickstart.md),
[library contract](specs/004-xdl-loader-validator/contracts/library.md), and
[CLI contract](specs/004-xdl-loader-validator/contracts/cli.md). `Ready` in this capability means
statically complete declarations; it never claims that a live target was contacted or is ready.
The user approved capability 004 and ADR-0013 on 2026-09-20, allowing M3 specification to begin.

## M3 component catalog and compatibility runtime

The [M3 capability](specs/005-component-catalog-compat-runtime/spec.md) now implements an
XDL-anchored derived catalog, deterministic permit-free planning, execution permits, provider-issued
ownership handles, durable intent/outcome evidence, and an isolated in-memory fixture. Its process
provider requires an explicit execution root, executable allowlist, and isolation attestation, uses
no implicit shell or ambient environment, and mutates only resources selected by exact issued handles
bound to the selected provider ID and kind.
The attestation is a fail-closed trust input and does not itself create an OS sandbox.

The separately reviewed companion capability in `xverse-compat` defines an explicit
process-action-only provider boundary for platform API `0.4.0` and implements a controlled in-memory
conformance fixture. SD-0001 now supplies one exact candidate graph and a reviewed target-contract
draft, but its seven planning blockers prevent completed selection or provider implementation.

Run `.venv/bin/python scripts/validate_sd0001.py` to verify the locked candidate without execution.
The [closure packet](specs/005-component-catalog-compat-runtime/evidence/SD-0001-closure-packet.md)
lists the exact external evidence required before any blocker can be removed.
The [static interface audit](specs/005-component-catalog-compat-runtime/evidence/SD-0001-static-interface-audit.md)
narrows the six-route contract while retaining every runtime and owner-dependent blocker.
The user selected the configurable-rebuild disposition on 2026-09-21, then formally reordered delivery
to platform-first development. The strategy and evidence remain available, but the derivative target,
legacy selection, and parity work are deferred until the relevant platform baselines are accepted. The
seven candidate planning blockers remain unchanged.

Run the public fixture validation:

```sh
.venv/bin/python scripts/validate_m3.py
```

The fixture establishes lifecycle mechanics only. No legacy component or production workload is
executed, and no compatibility, application parity, or production-readiness claim is made.

## Code documentation

The versioned [Doxygen configuration](Doxyfile) covers every Python source file under `src/`,
`scripts/`, and `tests/`. The authored [code-reference main page](docs/doxygen/mainpage.md) explains
package flow, maturity, and safety boundaries. Generate and validate the local HTML reference with:

```sh
python3 scripts/check_doxygen.py
```

This enforces docstring coverage for the production package and reusable scripts, rejects Doxygen
warnings, verifies source indexing, and writes the ignored local entry point to
`build/doxygen/html/index.html`. Run `python3 scripts/check_doxygen.py --self-test --coverage-only`
to prove that the coverage gate rejects an undocumented synthetic module and function.
