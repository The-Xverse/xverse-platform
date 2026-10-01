# XDL Lite Phase 1 — maintenance and usage guide (feature `XDL1`)

| Field | Value |
| --- | --- |
| Feature | `XDL1` — XDL Lite Phase 1, offline declared experiment intent compilation |
| Stage / role | documentation (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 1 |
| Date | 2026-10-01 |
| Model | DeepSeek V4 Flash (`provider=deepseek`, `backend=api`, `requested_model=deepseek-v4-flash`) |
| Delivered implementation record | [`implementation.md`](implementation.md) rev 1 |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`XDL1-SR-001` … `XDL1-SR-019`) |
| Classification | Public-safe engineering work product |
| Maturity | **Implemented and candidate-locally verified only.** Guidance only; it establishes no runtime, readiness, compatibility, parity, certification, or delivery claim. |

This guide is for a maintainer or integrator reusing the Phase 1 XDL Lite compiler. It records the
reusable API/CLI surface, dependencies and compatible versions, usage limits, exact source/semantic
identities, failure semantics, and the change rules to follow when maintaining or extending it.

## 1. What the capability does (and does not do)

**Does:** compile a closed, offline, explicitly supplied set of XDL v1alpha1 resources plus one
admitted neutral `io.xverse.experiment` Profile into one versioned canonical **resolved experiment
plan** carrying selection, seed/parameters, components (including the always-present System-scope
entry), time domains/mappings, dependency order, flows, bindings, lifecycle intent, intended fault
schedule, observers, metric references, declared limitations, a non-readiness statement, and input
provenance — or reject it with stable structured diagnostics and no plan.

**Does not:** start, stop, probe, or connect to anything; activate faults; invoke observers, metrics,
or oracles; retrieve or unpack artifacts; read the clock, locale, environment, hostname, user, or
CWD into the plan; perform registry, catalog, DNS, or network access; accept online learning; invent,
default, or narrow a scientific protocol value; or execute any production or legacy workload. Phase 1
does not complete legacy selection, implement a legacy provider, permit legacy execution, or establish
compatibility/parity.

## 2. Dependencies and compatible versions

Runtime dependencies (already declared in `pyproject.toml`; Phase 1 adds none):

| Dependency | Constraint | Role |
| --- | --- | --- |
| Python | `>=3.11` (verified on 3.11.16; classifiers cover 3.11–3.14) | runtime |
| `jsonschema[format]` | `>=4.26,<5` | accepted schema registry / 2020-12 payload validation |
| `referencing` | `>=0.37,<1` | schema `$id` resolution |
| `ruamel.yaml` | `>=0.19.1,<0.20` | YAML 1.2 parsing |
| `pytest` | 8.4.2 (verification environment) | test runner |

The distribution is `xverse-xdl`; the `xdl` console script maps to `xverse_xdl.cli:main`.
`pyproject.toml` already ships `xdl/schemas/v1alpha1` and `xdl/profiles` in the wheel via
`force-include`, so the new Profile schema is packaged without a build change.

Compatible version dimensions (independent of one another):

| Dimension | Phase 1 value | Notes |
| --- | --- | --- |
| XDL API version | `xverse.io/xdl/v1alpha1` | Accepted; unchanged |
| Profile payload `schemaVersion` | `0.1` | New |
| Profile resource `metadata.version` | `0.1.0` | New; exact match required |
| Payload `$id` / `schemaRef` | `https://xverse.io/profiles/experiment-lite/v0.1/schema.json` | New; exact match required |
| Plan version | `1` | New |
| Tool version (`__version__`) | `0.4.0` | Unchanged by Phase 1 |

Anything else fails closed: an unknown namespace, version, `schemaRef`, kind, or field is rejected
rather than coerced.

## 3. Reusable examples

### 3.1 Compile files (loader path)

```python
from xverse_xdl import compile_experiment_files

result = compile_experiment_files(
    paths,                                  # explicit closed set; no discovery
    profile_schema_paths=("xdl/profiles/experiment-lite-v0.1.schema.json",),
    run_id="run-42",                        # volatile
    generated_at="2026-10-01T12:00:00Z",    # volatile; injected explicitly, never read from a clock
)
if result.is_valid:
    plan = result.plan                     # canonical dict; plan["digest"]["value"] is the plan digest
else:
    for d in result.diagnostics:           # stable code, gate, pointer, severity, correction
        print(d.severity.value, d.code, d.pointer, d.message)
```

### 3.2 Compile already-normalized resources (pure path)

```python
from xverse_xdl import compile_experiment_plan, plan_matches_digest

result = compile_experiment_plan(normalized_resources, static_readiness=readiness)
assert result.plan is None or plan_matches_digest(result.plan)
```

### 3.3 Pin inputs against silent mutation

```python
result = compile_experiment_files(
    paths,
    profile_schema_paths=(schema,),
    expected_input_semantic_digests={"<resource-key>": "<sha256>"},
)
# A mismatch, or a late mutation detected after hashing, yields XDL1-PLAN-INPUT-MUTATED and no plan.
```

### 3.4 Read the always-present System-scope component entry

```python
plan = result.plan
system_entry = plan["components"][0]
assert system_entry["scope"] == "system"
for parameter in system_entry["declaredParameters"]:
    print(parameter["id"], parameter["valueType"], parameter["mutability"])
```

`components[0]` is always the `scope = "system"` entry projecting every declared
`System.spec.parameters[]`; component-instance entries follow in declared order and project only
their referenced Component's parameters. No System parameter is dropped and none is duplicated
across scopes.

### 3.5 CLI

```bash
# Resolve the neutral example set (exit 0) -> text summary on stdout
python3 -m xverse_xdl experiment compile \
  --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json \
  tests/thesis_lite/xdl/fixtures/component.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/system.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/deployment.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/scenario.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/profile.xdl.yaml
# -> resolved plan ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d (23 sections)

# Machine-readable envelope (exit 0) and persisted canonical plan
python3 -m xverse_xdl experiment compile --format json \
  --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json \
  -o plan.json <component> <system> <deployment> <scenario> <profile>

# Rejection path (exit 1; diagnostics on stderr for text, stdout for json; no -o file written)
python3 -m xverse_xdl experiment compile \
  --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json \
  <profile> <invalid-scenario>
```

CLI exit codes: `0` resolved, `1` declared rejection, `2` invocation/internal failure (bad
`--expect-input-digest`, `-o` colliding with an input path, digest self-check failure, runtime error).

## 4. Usage limits

`ExperimentLimits` (frozen dataclass; all fields positive, else `ValueError`) — defaults:

`max_resources` 1 000 · `max_bytes_per_file` 5 242 880 · `max_parameters` 256 · `max_steps` 256 ·
`max_faults` 256 · `max_observers` 256 · `max_metrics` 256 · `max_dependencies_per_step` 64 ·
`max_flows` 1 024 · `max_bindings` 512 · `max_ticks` 9 007 199 254 740 991 · `max_seed`
9 007 199 254 740 991 · `max_number_magnitude` 1e15 · `max_text_length` 200 · `max_limitations` 64 ·
`max_diagnostics` 256.

These are platform **library** limits. They are **not** thesis safety thresholds, tolerances,
deadlines, or protocol values, and must not be reinterpreted as such. Every declared bound is
enforced over its **full declared scope** and carries at least one independent negative case;
exceeding a bound yields `XDL1-PLAN-BOUND-EXCEEDED` and no plan.

`max_parameters` in particular has three frozen scopes
([`detailed-design.md`](detailed-design.md) §10.3, `XDL1-DD-13`):

1. **per-payload** — each declared extension `parameterList`;
2. **total compiled** — `len(plan["parameters"]) + Σ lifecycleIntent[].parameters +
   Σ faultSchedule[].parameters` over the finished plan;
3. **declared core** — each declared `System.spec.parameters[]` and referenced
   `Component.spec.parameters[]` list projected into `components[].declaredParameters`.

Time is expressed only through the closed vocabulary `tick`, `ns`, `us`, `ms`, `s` with exact
rational scaling to integer ticks (`1 tick = 1 ns`); unknown, ambiguous, negative, non-finite,
overflowing, or imprecise values are rejected. A declared `unitSemantics` label is recorded verbatim
and is never used for conversion.

## 5. Exact source and semantic identities

* **Resource semantic digest** = `sha256(RESOURCE_DOMAIN_SEPARATOR + canonical_json(resource))` where
  `canonical_json` is the accepted `normalize.canonical_json` with `include_source_map=False` and
  integral floats emitted as integers. Included: identity, revision, provenance, labels, elements,
  references, extensions, content. Excluded: source maps, file names, source format, YAML
  anchors/comments/key order.
* **Input semantic digest** = `sha256(INPUT_DOMAIN_SEPARATOR + canonical_json(contributing_resources))`
  over exactly the contributing set, ordered by `(apiVersion, kind, namespace, name, version)`.
* **Plan digest** = `sha256(PLAN_DOMAIN_SEPARATOR + canonical_plan_bytes(plan_without_digest))`,
  recomputed and self-checked.
* Domain separators: `b"xverse.xdl.experiment-resource.v1\x00"`,
  `b"xverse.xdl.experiment-input.v1\x00"`, `b"xverse.xdl.experiment-plan.v1\x00"`.
* Canonical plan serialization: `json.dumps(value, ensure_ascii=False, sort_keys=True,
  separators=(",", ":"), allow_nan=False)` with integral floats as integers.
* Volatile only (never affect the plan digest): `runId`, `generatedAt`, `sourceByteDigests`,
  `planDigest`, `status`, `compilerVersion`.

Delivered source identities (SHA-256), re-verified unchanged through the documentation stage:

| Artifact | SHA-256 |
| --- | --- |
| `src/xverse_xdl/experiment_plan.py` | `4e4affa52fe77cea4f37598cd6bce2309a0a767a7e878372ecee0a5599603393` |
| `src/xverse_xdl/cli.py` | `15502fdf6deef6a6f6730d37cd4b755c9a125c223a9e919611536ebaceed2d6a` |
| `src/xverse_xdl/__init__.py` | `0e0ca25bf3afab9276a4a18900ed2fc3d82e4c3bf23854c4c9c69b3791cec8ce` |
| `xdl/profiles/experiment-lite-v0.1.schema.json` | `a2123b3349ab016fda829d57084d9142565bf76fdafd474fe19fe222562dfc30` |

**Maintenance rule:** any change that alters a canonical ordering, a domain separator, the
inclusion/exclusion set above, the declared-intent projection of `System.spec.parameters`, or a
numeric encoding changes semantic identity and is a breaking change requiring a reviewed successor
candidate and a refreshed plan version — not an in-place edit.

## 6. Failure semantics

All declared defects are `error`-severity diagnostics with a stable code, gate, JSON pointer, and
remediation, and always return `plan is None`. Accepted-gate codes keep their existing `XDL-*`
identifiers (`XDL-PARSE-*`, `XDL-SCHEMA-*`, `XDL-POLICY-*`, `XDL-REFERENCE-*`, `XDL-SEMANTIC-*`,
`XDL-BINDING-ARTIFACT-INTEGRITY`). The compiler's own closed catalogue is `XDL1-PLAN-*` (**42
codes**), grouped by profile admission, selection, seed/parameter, quantity/time,
dependency/schedule, artifact/realization/delivery/retry, metric/observer, secret scan, input
mutation, bounds, and digest self-check. The credential/secret scan matches credential-like
assignments, private-key markers, and URI userinfo in emitted leaf strings; a match rejects the
compile and never echoes the value.

Typical outcomes: an accepted-gate or `XDL1-PLAN-*` rejection returns diagnostics and no plan at CLI
exit `1`; a plan digest self-check failure, a bad CLI argument, or an `-o` collision with an input
returns exit `2` and writes no file.

## 7. Maintaining the capability

Change rules (repository-wide, ADR-0020 / ADR-THESIS-LITE-0001):

1. **Additive only.** Do not rename or remove public API, change the accepted
   `validate_sources`/`validate_files`/`normalize`/`catalog`/`lifecycle`/`xcom_plan` contracts, or
   modify `xdl/schemas/v1alpha1/**`, `src/xverse/xcom/**`, `proto/**`, accepted tests, or any
   historical requirement/design/unit/measure/scenario/stage record.
2. **Version a new payload, never mutate the old one.** A new Profile payload form or field requires a
   new `schemaVersion`, a new `$id`/`schemaRef`, a new Profile `metadata.version`, and a reviewed
   successor candidate. Unknown versions/namespaces/fields must keep failing closed.
3. **Preserve identity rules.** Keep the semantic/plan identity computed from declared content only,
   excluding run identifiers, wall-clock observations, and byte provenance (see §5).
4. **Preserve declared-intent projection.** Every declared `System.spec.parameters[]` entry must stay
   in the always-present `components[scope="system"]` entry, never duplicated into a component entry
   and never dropped; new plan sections must not introduce a second destination.
5. **Preserve neutrality.** No automotive, thesis, or domain-specific primitive, threshold, or name.
   Scientific numbers stay caller inputs.
6. **Keep the test contract.** Every claimed behaviour remains bound to exact pytest-discoverable
   identifiers in `tests/thesis_lite/xdl/**`; the `XDL1-UNIT`, `XDL1-INTEGRATION`, `XDL1-VALIDATION`,
   and `XDL1-STATIC` records are the measure contract. Every declared library bound must keep at least
   one independent negative case per scope (including the total compiled-parameter scope). Do not
   rename, drop, skip, xfail, or weaken a bound identifier; a required identifier change is a reviewed
   change.
7. **Refresh trace endpoints, not history.** `engineering/trace/links.json` is a mutable current trace
   file; when a bound source file changes, refresh only the affected mutable code-endpoint
   `target_revision` hashes. Never rewrite a historical record's bytes.
8. **Keep the trusted bindings coherent.** The trusted host policy binds `unit → XDL1-UNIT`,
   `static_analysis → XDL1-STATIC`, `integration → XDL1-INTEGRATION`,
   `validation → XDL1-VALIDATION`; whole-system integration is only the assembled
   `mode = target_repository` measure over the pinned revision. If a maintainer changes the records,
   the external binding must be re-established by the owner; the gates fail closed otherwise.
9. **Re-verify after a change.** Re-run the candidate-local suite and the accepted repository suite,
   then obtain the trusted measures and a separate read-only review on the successor candidate.
   A separate review records findings without repairing them; repairs create a successor candidate
   and require repeated verification.

### 7.1 Where things live

| Concern | Location |
| --- | --- |
| Compiler | `src/xverse_xdl/experiment_plan.py` |
| CLI subcommand | `src/xverse_xdl/cli.py` |
| Additive exports | `src/xverse_xdl/__init__.py` |
| Profile payload schema | `xdl/profiles/experiment-lite-v0.1.schema.json` |
| Fixtures and tests | `tests/thesis_lite/xdl/**` |
| Measure records | `engineering/verification/measures/XDL1-{UNIT,INTEGRATION,VALIDATION,STATIC}.json` |
| Unit / component / requirement records | `engineering/{unit-specifications,architecture/components,requirements}/XDL1-*.json` |
| Parent anchors | `engineering/requirements/XVE-SYS-*.json` (original IDs — including `XVE-SYS-00014` — `disposition = allocated`) |
| Current trace | `engineering/trace/links.json` |
| Work products | `docs/engineering/xdl-lite/**` |
| Review index / internal review | `reports/review-index.md`, `docs/engineering/xdl-lite/internal-review.json` (authored by the later read-only stage) |

## 8. Limitations

* This guide and the capability it documents are **candidate-local** until the trusted measures, the
  assembled-target integration run, the separate read-only internal review, and terminal user
  acceptance complete. No runtime, readiness, availability, compatibility, parity, or certification is
  claimed.
* A resolved plan proves declared-intent validation only; it is not evidence of executable artifact
  availability or live readiness.
* The three predecessor findings `XDL1-RVW-001/002/003` are closed by executed candidate-local
  evidence; their terminal confirmation belongs to the separate read-only `internal_review` stage and
  the trusted host measures, and is not claimed here.
* `status: accepted` on `XDL1-SR-*`, component, unit, and measure records is internal engineering
  intent, never implementation satisfaction or external delivery acceptance. No REF-002 parent is
  closed, promoted, or marked implemented.
* Public-safe: repository-relative locators only; no secret, credential, host address, private source
  excerpt, or sensitive deployment detail.

## 9. Next step and model recommendation

Next stage: **read-only `internal_review`** (host makes the checkout read-only; it writes
`/review/internal-review.json` and `/review/stage.json`, mirrored to
`docs/engineering/xdl-lite/internal-review.json`). It may run read-only tests and must not modify the
candidate.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most
cost-effective and only authorized route for that review, because it is a bounded, evidence-bound
inspection of frozen artifacts; no stronger tier is justified, and there is no new
Terra/Luna/Sol/Astra engineering route in this package, no fallback, and no model switch is claimed or
performed.

Blocker: none. The trusted measures, the assembled-target integration run, the read-only internal
review, and terminal user acceptance remain external host/user obligations and are pending, not
failed.
