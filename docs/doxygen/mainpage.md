# X-Verse Platform Code Reference {#mainpage}

X-Verse vNext is a domain-neutral cyber-physical systems experimentation platform under
development. This reference documents the current Python package, command-line interface,
validation tools, and test sources. It complements the normative XDL and architecture documents;
it does not replace them.

## Start here

- **Package API**: browse the `xverse_xdl` namespace for loading, validation, normalization,
  catalog derivation, lifecycle planning, and isolated provider APIs.
- **Source files**: use the file list and source browser to inspect all Python code in `src/`,
  `scripts/`, and `tests/`.
- **Architecture**: read `docs/architecture/METAMODEL.md` and the ADRs under `docs/adr/` before
  changing domain concepts or dependency direction.
- **Capability contracts**: read the active specification packages under `specs/` for accepted
  behavior, failure semantics, evidence, and maturity.

## Package flow

The public validation path is deliberately staged:

1. `xverse_xdl.loader` parses bounded local YAML or JSON and retains source locations.
2. `xverse_xdl.schema` applies the packaged XDL v1alpha1 schemas and explicitly supplied profile schemas.
3. `xverse_xdl.semantics` resolves references and applies cross-resource semantic rules.
4. `xverse_xdl.normalize` creates immutable resources and deterministic JSON.
5. `xverse_xdl.catalog` derives compatibility catalog entries and side-effect-free lifecycle plans.
6. `xverse_xdl.lifecycle` applies permit, ownership, isolation, and evidence controls to prototype providers.

The CLI in `xverse_xdl.cli` exposes validation and normalization. Scripts under `scripts/` are
acceptance, benchmark, and repository validation tools; they are not additional platform APIs.
`scripts/validate_sd0001.py` verifies the nominated candidate's content lock and deterministic
blocked plan without invoking a provider or lifecycle action.

## Maturity and safety boundary

The XDL loader, validator, normalizer, derived catalog, planner, and isolated lifecycle mechanics
are **prototype implementations**. Static readiness means declarations are complete enough for
planning; it is not evidence that any live target is reachable or ready.

One legacy component is nominated through an exact but unplannable candidate graph; selection is
incomplete, and no target provider or legacy component is executed. The fixture provider demonstrates
lifecycle mechanics only. The process provider is constrained by
an explicit execution root, allowlist, isolation attestation, exact ownership handles, and durable
evidence, but an attestation does not itself create an operating-system sandbox. Existing legacy
repositories remain read-only and no compatibility, parity, migration, or production-readiness
claim follows from the documented code.

## Documentation policy

Python docstrings are the source of symbol documentation. Public callables describe purpose,
parameters, results, and relevant exceptions. Private helpers are documented where their policy or
transformation matters. Tests remain executable specifications: Doxygen includes their modules and
source, while descriptive test names and assertions carry method-level intent.

Generated HTML is a disposable local artifact under `build/doxygen`. Run:

```sh
python3 scripts/check_doxygen.py
```

The check enforces production docstring coverage, invokes Doxygen, rejects warnings, verifies that
all repository Python files are indexed, and confirms the HTML entry point exists.

## Architectural invariants

- The platform core stays domain-neutral; automotive concepts belong in profiles and blueprints.
- XDL remains the canonical versioned representation.
- Logical identity stays separate from simulated, virtual, physical, or hybrid realization.
- Dependencies flow from blueprints through profiles and platform APIs toward runtime abstractions.
- Legacy systems evolve in parallel through explicit compatibility boundaries.
- Evidence and documentation distinguish implemented, partial, target, and exploratory claims.
