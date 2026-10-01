# XDL Lite Phase 1 — implementation record (feature `XDL1`)

| Field | Value |
| --- | --- |
| Feature | `XDL1` — XDL Lite Phase 1, offline declared experiment intent compilation |
| Stage / role | documentation (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 1 |
| Date | 2026-10-01 |
| Model | DeepSeek V4 Flash (`provider=deepseek`, `backend=api`, `requested_model=deepseek-v4-flash`) |
| Admitted platform baseline revision | `0c5e249621727b2d0041707de2661f0ed1e1ef23` |
| Admitted thesis revision | `fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`XDL1-SR-001` … `XDL1-SR-019`) |
| Design authorities | [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), [`integration.md`](integration.md), [`validation.md`](validation.md) rev 1 |
| Classification | Public-safe engineering work product |
| Maturity | **Implemented and candidate-locally verified only.** The trusted unit/static/integration/validation measures over the assembled pinned target, the separate read-only `internal_review`, and terminal user acceptance are pending host/user gates; none is claimed complete here. |

This record is produced by the `documentation` stage of the externally admitted feature delivery. It
describes the delivered Phase 1 change set, the reusable public API and CLI, the canonical semantic
identity, the failure semantics, and the preserved boundaries, and it records how the successor
candidate resolves the three predecessor review findings. It authors **no** source, schema, fixture,
or test code and performs **no** code repair. It makes no runtime, availability, readiness,
compatibility, parity, certification, or delivery claim.

## 1. Scope and change boundary

XDL Lite Phase 1 adds exactly one bounded capability: compile a closed, offline *declared experiment
intent* resource set into one versioned canonical **resolved experiment plan**, or reject it with
stable structured diagnostics and **no plan**. It draws intent from the existing five XDL v1alpha1
resource kinds (`System`, `Component`, `Deployment`, `Scenario`, `Profile`) through one explicitly
admitted neutral experiment Profile, and it performs no execution, retrieval, registry/network
access, or filesystem mutation.

Delivered change boundary (additive only; no accepted artifact rewritten):

| Path | Change |
| --- | --- |
| `src/xverse_xdl/experiment_plan.py` | **new** pure compiler module |
| `src/xverse_xdl/cli.py` | **additive** `experiment compile` subcommand; no existing behaviour changed |
| `src/xverse_xdl/__init__.py` | **additive** nine exports; `__all__` only grows |
| `xdl/profiles/experiment-lite-v0.1.schema.json` | **new** admitted neutral Profile payload schema |
| `tests/thesis_lite/**` | **new** owned neutral fixtures and pytest suites |
| `docs/engineering/xdl-lite/**` | **new** work-product set |
| `engineering/{requirements,architecture/components,unit-specifications}/XDL1-*.json`, `engineering/requirements/XVE-SYS-*.json` | **new** requirement/component/unit records and original parent anchors |
| `engineering/verification/measures/XDL1-*.json`, `engineering/validation/scenarios/XDL1-*.json` | **new** feature-scoped measure and scenario records |
| `engineering/trace/links.json` | **additive** XDL1 links and refreshed mutable current code-endpoint hashes only |
| `engineering/project.json` | **current** feature pointer `XDL1` |
| `engineering/stage-results/xdl1-*.json` | **new** stage records |
| `reports/xdl-lite/**`, `reports/review-index.md` | **new** stage report and an appended review-index section |

## 2. Delivered artifacts (exact identities)

The implementation stage froze these bytes; every hash below was re-verified unchanged by the later
integration, validation, and documentation stages.

### 2.1 Compiler, exposure, and schema

| Path | SHA-256 |
| --- | --- |
| `src/xverse_xdl/experiment_plan.py` | `4e4affa52fe77cea4f37598cd6bce2309a0a767a7e878372ecee0a5599603393` |
| `src/xverse_xdl/cli.py` | `15502fdf6deef6a6f6730d37cd4b755c9a125c223a9e919611536ebaceed2d6a` |
| `src/xverse_xdl/__init__.py` | `0e0ca25bf3afab9276a4a18900ed2fc3d82e4c3bf23854c4c9c69b3791cec8ce` |
| `xdl/profiles/experiment-lite-v0.1.schema.json` | `a2123b3349ab016fda829d57084d9142565bf76fdafd474fe19fe222562dfc30` |

### 2.2 Owned neutral fixtures

| Path | SHA-256 |
| --- | --- |
| `tests/thesis_lite/xdl/fixtures/component.xdl.yaml` | `e8318a2f1b4a2c88b2cdac23e74ee2ef3224152646074ceb1f03c29bbe568c0f` |
| `tests/thesis_lite/xdl/fixtures/system.xdl.yaml` | `3bab1149c88efbb63fce9a8ddfabf847e3b6b142f159aa2387014aaf45d3f4b7` |
| `tests/thesis_lite/xdl/fixtures/deployment.xdl.yaml` | `dc7f140fb3d9393fc0a4ce6f776c97802ee94fa039287363233dd9ff16b701b2` |
| `tests/thesis_lite/xdl/fixtures/scenario.xdl.yaml` | `0b5d8c9fdba1d364e76c1d4959fc34d9080aa38b11ce47aba6ec5d9b2c7c5361` |
| `tests/thesis_lite/xdl/fixtures/profile.xdl.yaml` | `4004f47e96e5af57bb5cb88ac3f5ed88d1726cf62c49afbd1188a51139cfe95c` |
| `tests/thesis_lite/xdl/fixtures/invalid-scenario.xdl.yaml` | `043dedcbaf46199c0353d90a2fa58df83e421e95cfe800ff27d16dae9a7ed7ae` |

`invalid-scenario.xdl.yaml` is the rejection fixture; the other five form the resolvable neutral set.

### 2.3 Test suites (pytest-discoverable)

| Path | Cases | SHA-256 |
| --- | --- | --- |
| `tests/thesis_lite/xdl/test_xdl1_profile_unit.py` | 10 | `efb427dbca44c1ffc2018f324fbe156a8385caf4c09a0db4188ecc30de25b722` |
| `tests/thesis_lite/xdl/test_xdl1_selection_unit.py` | 9 | `29f352ed0b42d46a8d7da1d2094755080e0f673d3321c4d0f592879068d2e18d` |
| `tests/thesis_lite/xdl/test_xdl1_quantity_unit.py` | 29 | `511edf123aed992ccc21be194f2d3b4e843e891049a6358bbbfee483e2d2d0d2` |
| `tests/thesis_lite/xdl/test_xdl1_time_unit.py` | 4 | `52c2b407c9d2b4f9421649102357dd8de43b38e626776548bf3e07f0f6117349` |
| `tests/thesis_lite/xdl/test_xdl1_order_unit.py` | 8 | `4af06c0c4641e38c28ccea5033cf241d464942cd97d3f06ebc731fb31c7b3ac0` |
| `tests/thesis_lite/xdl/test_xdl1_intent_unit.py` | 23 | `a85fbf534a2fe58c023af822d2298bc20391bba374185258028411e98d4974b3` |
| `tests/thesis_lite/xdl/test_xdl1_identity_unit.py` | 11 | `0d5b59405bbe60ee2e45b377e21c7ee68e345520f57afe5b1767666445bfeb8c` |
| `tests/thesis_lite/xdl/test_xdl1_diagnostics_unit.py` | 6 | `443feb989338db180d00bea7cd6404b25051e6b04b7a668a778f47268dcbbf07` |
| `tests/thesis_lite/xdl/test_xdl1_exposure_unit.py` | 9 | `e66c59fee80b92a43c1177e72a1e2616bc843e14456df17981c8227410385527` |
| `tests/thesis_lite/xdl/test_xdl1_side_effect_unit.py` | 7 | `22a06436439e36c31a053e150f5c3e80965cd29d3c40141825d12fecc8618d02` |
| `tests/thesis_lite/xdl/test_xdl1_metamorphic_unit.py` | 5 | `7bf0f900909273c567e45674d9ac749cd53747024e1f2dedfee31323abdacd4c` |
| `tests/thesis_lite/xdl/test_xdl1_integration.py` | 8 | `9594406e719f455b720f39d1a9cd4fb5fc318bb83e03d0f8d129bf572397f231` |
| `tests/thesis_lite/xdl/test_xdl1_validation.py` | 18 | `5a0358e6a13a2df86863a234c892d27a756a812ab0e0f2fe3fc9825ae3e4e8bd` |
| `tests/thesis_lite/xdl/support.py` (shared helpers) | — | `b31f3c6702ec023c1b4fcc91847ffbb1b5c5197cf204082d833e6c154ab5f6a9` |

Total pytest-discoverable XDL1 cases: **147** (121 unit + 8 integration + 18 validation); the
`XDL1-STATIC` measure additionally declares 19 declaration-bound static checks (no pytest discovery).
Feature-scoped measure records: `XDL1-UNIT`
(`8b69fc76f4f7b5a1785cda72eeec9b89a0e2a6ab7cfa2c0ac06f0571ea2ddcc1`), `XDL1-INTEGRATION`
(`2b3c853693be8306c3033148865081ec426d23cd0c68f252488204591d745515`), `XDL1-VALIDATION`
(`be287f53b98ef3ce0a128dafbf40fa3003523f96981c30f0b58477a4be3ad0f3`), `XDL1-STATIC`
(`7395deccc71d376a8772cad2f1ffeb37be2fc7ffcba84bb98cbd7fc2ad6c86de`).

## 3. Public API

Module `src/xverse_xdl/experiment_plan.py` exposes the frozen contract of
[`detailed-design.md`](detailed-design.md) §13.1. The additive package exports (in
`src/xverse_xdl/__init__.py`) are:

```python
ExperimentLimits, ExperimentPlanResult, canonical_plan_bytes, compile_experiment_files,
compile_experiment_plan, compile_experiment_sources, compute_plan_digest,
experiment_plan_status, plan_matches_digest
```

Entry points:

```python
compile_experiment_plan(resources, *, static_readiness=None, run_id=None, generated_at=None,
                        expected_input_semantic_digests=None, limits=None) -> ExperimentPlanResult
compile_experiment_sources(sources, *, profile_schema_paths=(), run_id=None, generated_at=None,
                           expected_input_semantic_digests=None, limits=None) -> ExperimentPlanResult
compile_experiment_files(paths, *, profile_schema_paths=(), run_id=None, generated_at=None,
                         expected_input_semantic_digests=None, limits=None) -> ExperimentPlanResult
```

* `compile_experiment_plan` consumes **only** immutable `NormalizedResource` values and performs no
  I/O.
* `compile_experiment_sources` / `compile_experiment_files` run the accepted `validate_sources` /
  `validate_files` (parse → core schema → Profile schema catalog → reference resolution → kind
  semantics + payload schema → normalization) and then feed the resulting resources to the pure
  compiler. No accepted signature, default, return shape, or diagnostic is changed.

Result and helpers:

```python
@dataclass(frozen=True)
class ExperimentPlanResult:
    diagnostics: tuple[Diagnostic, ...]
    plan: dict[str, Any] | None
    run: FrozenMap                      # volatile envelope (never part of the plan or its digest)
    @property
    def is_valid(self) -> bool          # no error diagnostic and plan is not None

canonical_plan_bytes(plan) -> bytes     # canonical JSON, integral floats as integers, allow_nan=False
compute_plan_digest(plan) -> str        # domain-separated sha256 of the plan body
plan_matches_digest(plan) -> bool
experiment_plan_status(plan) -> str     # always "resolved" for an emitted plan
```

`resource_semantic_digest` and `plan_public_data` are module-level helpers used by the CLI; they are
not re-exported at package level. `ExperimentLimits` is the frozen `frozen=True` dataclass of §4.

### 3.1 Reusable API examples

Compile a closed file set:

```python
from xverse_xdl import compile_experiment_files

result = compile_experiment_files(
    ("component.xdl.yaml", "system.xdl.yaml", "deployment.xdl.yaml",
     "scenario.xdl.yaml", "profile.xdl.yaml"),
    profile_schema_paths=("xdl/profiles/experiment-lite-v0.1.schema.json",),
    run_id="run-42",                       # volatile; never affects the plan digest
)
if result.is_valid:
    assert result.plan["status"] == "resolved"
    print(result.plan["digest"]["value"])
else:
    for diagnostic in result.diagnostics:
        print(diagnostic.code, diagnostic.pointer, diagnostic.message)
```

Compile already-normalized resources without any I/O (pure path):

```python
from xverse_xdl import compile_experiment_plan, plan_matches_digest

result = compile_experiment_plan(normalized_resources,
                                 static_readiness=readiness, limits=None)
plan = result.plan
assert plan is None or plan_matches_digest(plan)
```

`plan["components"][0]` is always the `scope = "system"` entry carrying the projected declared
`System.spec.parameters[]` (see §6 and [`detailed-design.md`](detailed-design.md) §7 / `XDL1-DD-14`).

## 4. Usage limits (`ExperimentLimits`)

`ExperimentLimits` is a frozen dataclass whose defaults are finite platform **library** bounds (not
thesis thresholds). Every field must be positive, otherwise construction raises `ValueError`.

| Field | Default | Applies to |
| --- | --- | --- |
| `max_resources` | 1 000 | closed input set |
| `max_bytes_per_file` | 5 242 880 (5 MiB) | each input source |
| `max_parameters` | 256 | three explicit scopes: each declared extension `parameterList`; the **total compiled-parameter count**; each declared core `Component`/`System`.`spec.parameters[]` list |
| `max_steps` | 256 | Scenario steps |
| `max_faults` | 256 | Scenario faults |
| `max_observers` | 256 | Scenario observers |
| `max_metrics` | 256 | Scenario metrics |
| `max_dependencies_per_step` | 64 | `dependsOn` entries per step |
| `max_flows` | 1 024 | System flows |
| `max_bindings` | 512 | Deployment bindings |
| `max_ticks` | 9 007 199 254 740 991 (2⁵³−1) | any canonical tick value |
| `max_seed` | 9 007 199 254 740 991 | seed value |
| `max_number_magnitude` | 1e15 | numeric parameter magnitude |
| `max_text_length` | 200 | text / limitation strings |
| `max_limitations` | 64 | merged plan limitations |
| `max_diagnostics` | 256 | returned diagnostics before failing closed |

`max_bytes_per_file` and `max_resources` are also handed to the accepted `LoadLimits` on the
loader-backed entry points.

The three `max_parameters` scopes are frozen in [`detailed-design.md`](detailed-design.md) §10.3 and
decision `XDL1-DD-13`. The **total compiled-parameter** scope is the deterministic count

```text
C_total = len(plan["parameters"])
        + Σ over entry in plan["lifecycleIntent"] of len(entry["parameters"])
        + Σ over entry in plan["faultSchedule"]  of len(entry["parameters"])
```

over the finished sections, checked once immediately before identity finalization. All three scopes
reuse `XDL1-PLAN-BOUND-EXCEEDED` and return `plan = None`.

## 5. CLI

The additive subcommand is:

```text
xdl experiment compile [--profile-schema PATH]... [--run-id ID] [--generated-at RFC3339]
                       [--expect-input-digest NAME=SHA256]... [--format text|json]
                       [-o PLAN.json] RESOURCE...
```

| Behaviour | Contract |
| --- | --- |
| exit `0` | a plan was emitted; stdout carries the text summary or the JSON envelope; `-o` receives canonical plan JSON |
| exit `1` | rejected; diagnostics on stdout (`--format json`) or stderr (text); no `-o` file is created or overwritten; `plan = null` |
| exit `2` | invocation/internal failure (bad `--expect-input-digest`, `-o` equal to an input path, digest self-check failure, runtime error) |
| `--format text` (default) | one line per diagnostic (`SEVERITY CODE [gate] location/pointer: message` + `correction`), or `resolved plan <digest> (<n> sections)` |
| `--format json` | `{"reportVersion":"1","toolVersion":…,"valid":…,"plan":<plan or null>,"run":{…},"diagnostics":[…]}` |

The existing `xdl validate`, `xdl normalize`, and `xdl version` commands, formats, and exit codes are
byte-preserved for existing inputs.

### 5.1 Reusable CLI examples

```bash
# Resolve the neutral example set and print the text summary (exit 0)
python3 -m xverse_xdl experiment compile \
  --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json \
  tests/thesis_lite/xdl/fixtures/component.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/system.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/deployment.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/scenario.xdl.yaml \
  tests/thesis_lite/xdl/fixtures/profile.xdl.yaml
# -> resolved plan ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d (23 sections)

# Emit the machine-readable envelope and pin the expected input semantic digest
python3 -m xverse_xdl experiment compile --format json \
  --expect-input-digest <name>=<sha256> \
  --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json \
  <component.xdl.yaml> <system.xdl.yaml> <deployment.xdl.yaml> <scenario.xdl.yaml> <profile.xdl.yaml>

# Rejection: exit 1, structured diagnostics, no file created
python3 -m xverse_xdl experiment compile \
  --profile-schema xdl/profiles/experiment-lite-v0.1.schema.json \
  <profile.xdl.yaml> <invalid-scenario.xdl.yaml>
```

## 6. Canonical semantic identity and declared-intent projection

Frozen in [`detailed-design.md`](detailed-design.md) §8 and realized as written:

* **Resource digest** — `sha256(RESOURCE_DOMAIN_SEPARATOR + canonical_json(normalized_resource))`
  with `include_source_map = False` and integral floats emitted as integers. Excludes authored
  locations, file names, source format, YAML anchors/comments/key order.
* **Input semantic digest** — `sha256(INPUT_DOMAIN_SEPARATOR + canonical_json(contributing_resources))`
  over exactly the contributing resource set (selected System, Deployment when present, Scenario,
  admitted Profile, referenced Components, and parameter/model suppliers), ordered by
  `(apiVersion, kind, namespace, name, version)`. An unrelated valid extra resource in the closed set
  does not change the plan.
* **Plan digest** — `sha256(PLAN_DOMAIN_SEPARATOR + canonical_plan_bytes(plan_without_digest))`,
  recomputed and self-checked after assembly (`XDL1-PLAN-DIGEST-SELFCHECK` on mismatch).
* **Volatile run envelope** (`runId`, `generatedAt`, `sourceByteDigests`, `planDigest`, `status`,
  `compilerVersion`) is never inside the plan body and therefore never affects the plan digest.
* **Late-mutation detection** — every resource semantic digest and the input semantic digest are
  recomputed immediately before finalizing; any change yields `XDL1-PLAN-INPUT-MUTATED` and no plan.

Consequently equivalent YAML/JSON encodings and resource/payload permutations produce equal canonical
plan bytes and an equal plan digest, while source-byte provenance stays separately reconstructible.

**Declared core parameters are never dropped.** `plan["components"]` always contains exactly one
`scope = "system"` entry first, whose `declaredParameters` project **every** declared
`System.spec.parameters[]` entry (`XDL1-DD-14`); each component-instance entry projects the
`spec.parameters[]` of its referenced `Component`. No System parameter is copied into a
component-instance entry and none is omitted. The digest above therefore covers the System-level
declared core parameter surface.

### 6.1 Frozen identities and compatible versions

| Constant | Value |
| --- | --- |
| XDL API version | `xverse.io/xdl/v1alpha1` |
| Profile payload schema file | `xdl/profiles/experiment-lite-v0.1.schema.json` |
| Payload `$id` (= Profile `spec.schemaRef`) | `https://xverse.io/profiles/experiment-lite/v0.1/schema.json` |
| Payload `schemaVersion` | `0.1` |
| Extension namespace | `io.xverse.experiment` |
| Profile resource `metadata.version` | `0.1.0` |
| Plan version | `1` |
| Plan generator | `{"task": "XDL1", "version": "0.1.0"}` |
| Time unit vocabulary | `tick`, `ns`, `us`, `ms`, `s` (canonical unit `tick`; 1 tick = 1 ns) |
| Supported realization classes | `simulated`, `virtual`, `hybrid` (`physical` rejected in Phase 1) |

Schema version, resource revision, Profile version, and artifact/model revision remain independent
dimensions; changing one does not change an unrelated version field.

## 7. Failure semantics

Accepted gates run first and unchanged (`XDL-PARSE-*`, `XDL-SCHEMA-*`, `XDL-POLICY-*`,
`XDL-REFERENCE-*`, `XDL-SEMANTIC-*`, `XDL-BINDING-ARTIFACT-INTEGRITY`). The compiler then reports its
own closed `XDL1-PLAN-*` catalogue (**42 codes**, [`detailed-design.md`](detailed-design.md) §9) with
a stable gate, JSON pointer, and remediation. Representative groups:

| Condition | Outcome / code | CLI exit |
| --- | --- | --- |
| accepted gate rejects (parse/schema/reference/semantic/Profile) | diagnostics, no plan | `1` |
| Profile absent / wrong version / wrong `schemaRef` / payload kind-target-duplicate-absent | `XDL1-PLAN-PROFILE-*` | `1` |
| System / Scenario / Deployment missing, ambiguous, or unbound | `XDL1-PLAN-{SYSTEM,SCENARIO,DEPLOYMENT}-*` | `1` |
| seed/parameter missing, mistyped, duplicated or out of bound | `XDL1-PLAN-SEED-*` / `-PARAMETER-*` | `1` |
| unknown unit, imprecise/negative/non-finite/overflow quantity | `XDL1-PLAN-QUANTITY-*` / `-TIME-*` | `1` |
| dependency cycle, unresolved dependency, competing declared order | `XDL1-PLAN-DEPENDENCY-*` / `-SCHEDULE-AMBIGUOUS` | `1` |
| unpinned artifact, unsupported realization/delivery/retry | `XDL1-PLAN-ARTIFACT-*` / `-REALIZATION-*` / `-DELIVERY-*` / `-RETRY-*` | `1` |
| incomplete metric linkage / unresolved observer | `XDL1-PLAN-METRIC-LINK-INCOMPLETE` / `-OBSERVER-UNRESOLVED` | `1` |
| credential-like leaf (value not echoed) | `XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT` | `1` |
| input re-hash differs after hashing | `XDL1-PLAN-INPUT-MUTATED` | `1` |
| entity/quantity bound exceeded, or any of the three `max_parameters` scopes violated | `XDL1-PLAN-BOUND-EXCEEDED` | `1` |
| plan digest self-check fails | `XDL1-PLAN-DIGEST-SELFCHECK` | `2` |
| bad CLI argument or `-o` collision with an input | no plan, no file written | `2` |

Any error diagnostic implies `plan is None`; no partial, best-effort, or executable plan is ever
returned.

## 8. Predecessor review finding resolution

The predecessor XDL1 attempt-1 candidate was frozen, hash-inventoried, and independently reviewed
read-only; the reviewer returned `verdict: rework` with three open major findings and no repair. That
review evidence is consumed read-only and is referenced by content hash:

| Evidence | SHA-256 |
| --- | --- |
| predecessor frozen-candidate manifest (2 852 files) | `820f3c47d264a6e75a75e3fb58f9465d9bb1ba3495b6c263797d145230c59093` |
| predecessor `review/internal-review.json` (`verdict: rework`) | `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4` |
| predecessor `review/stage.json` (reviewer stage record) | `9b09049a68c45160a9ee0e57b918c04dcad6ec7cdc732c94b0953009221e0e23` |

The successor requirement baseline resolves the findings in the affected acceptance criteria
([`requirements.md`](requirements.md) §3); the successor design freezes the concrete behaviour in
[`detailed-design.md`](detailed-design.md) §16.2 (`XDL1-DD-13`, `XDL1-DD-14`, §10.3); the successor
implementation realizes it. No assertion was weakened, renamed, skipped, xfailed, or deleted.

| Finding | Predecessor defect | Resolution in this delivered candidate |
| --- | --- | --- |
| `XDL1-RVW-001` (major) | `ExperimentLimits.max_parameters` was declared to apply to "per payload and total compiled parameters" but only individual lists were checked; a plan could carry more compiled parameters than the bound and still be emitted as resolved with no diagnostic. | `experiment_plan.py` computes `C_total` over the finished `parameters`, `lifecycleIntent[].parameters`, and `faultSchedule[].parameters` sections once before identity finalization and rejects above the bound with `XDL1-PLAN-BOUND-EXCEEDED` and `plan = None` (`XDL1-DD-13`, §10.3). |
| `XDL1-RVW-002` (major) | Declared `System.spec.parameters` were mapped to `components[].declaredParameters` by the frozen design but silently dropped from every plan section; only `Component.spec.parameters` was projected. | `components[]` always carries exactly one leading `scope = "system"` entry whose `declaredParameters` project every declared `System.spec.parameters[]` entry (and `modelRefs` project `System.spec.models[]`); component-instance entries project only their referenced Component's parameters. No drop, no cross-scope duplication (`XDL1-DD-14`). |
| `XDL1-RVW-003` (major) | `XDL1-PLAN-BOUND-EXCEEDED` was the only one of the frozen diagnostic codes with zero occurrences in `tests/thesis_lite/xdl`; no count-based library bound had a negative case. | Per-scope negative cases were added: `max_parameters` per payload, total compiled, and declared core; the count bounds `max_steps`, `max_faults`, `max_observers`, `max_metrics`, `max_dependencies_per_step`, `max_flows`, `max_bindings`, `max_resources`, `max_text_length`, `max_limitations`, `max_diagnostics`, `max_bytes_per_file`; the per-value parameter bound; the non-positive-limit constructor; and the validation-level duplicates. `XDL1-PLAN-BOUND-EXCEEDED` now occurs 17 times across `test_xdl1_quantity_unit.py` and `test_xdl1_validation.py`. |

These resolutions were re-executed candidate-locally by the integration and validation stages. The
findings are therefore **closed by executed candidate-local evidence, subject to terminal
confirmation by the separate read-only `internal_review` stage and the trusted host measures**; this
record does not itself close them or promote the feature.

## 9. Verification performed (candidate-local, preliminary)

These are the candidate's own **preliminary worker checks**, recorded by the earlier stages and
re-confirmed by this documentation stage; they are not the trusted measures, not the assembled-target
run, and not acceptance evidence.

| Check | Observed |
| --- | --- |
| Environment | Python 3.11.16, pytest 8.4.2, working directory the candidate checkout |
| `python3 -m pytest -q tests/thesis_lite/xdl` | `147 passed`; every bound unit (121), integration (8) and validation (18) identifier is discoverable |
| `python3 -m pytest -q` (whole repository) | `297 passed`; no regression in accepted loaders, catalog, lifecycle, CLI, or C++ X-COM suites |
| CLI over the five neutral fixtures | exit `0`, `resolved plan ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d (23 sections)`; the JSON-envelope plan digest is identical |
| CLI over the rejection fixture | exit `1`, structured diagnostics, no plan emitted, no file created or mutated |
| `fabro_engineering.core.validate_trace(checkout, "xverse-platform")` | `{"artifacts": 909, "links": 3334}` |
| Prior stage-artifact preservation | all 120 artifacts recorded by the six earlier `xdl1-*.json` stage records (39 + 21 + 20 + 13 + 26 + 1) re-hash exactly |

The resolved-plan digest changed from the rejected predecessor value
`8c82b2f1627113c1ea84916242668d692610407ba7d41bbd96c2353fe44e06db` to
`ccf08204181f47ae7868ed7b6795c1fb2ae2d6e0aeb04437000a1b4ab3988f7d` because the successor plan carries
the additional always-present `scope = "system"` `components[]` entry required by `XDL1-DD-14`; the
digest is stable run-to-run.

Trusted `unit`, `static_analysis`, `integration`, and `validation` measures, the assembled pinned
`xverse-platform` target run, the separate read-only `internal_review`, and terminal user acceptance
remain pending host/user gates. They are not failed and they are not claimed by this record.

## 10. Preserved boundaries

* Accepted XDL schemas `xdl/schemas/v1alpha1/**` unchanged; the new payload schema is a separate
  Profile artifact referenced through `spec.schemaRef`.
* Accepted public APIs, defaults, dataclass fields, enums, exported names, diagnostics and
  serialization unchanged; `__all__` only grows.
* C++ X-COM (`proto/xverse/xcom/v1/**`, `src/xverse/xcom/**`, `xdl/profiles/xcom-v0.1.schema.json`)
  not touched, imported, or invoked.
* M3 catalog/lifecycle (`derive_catalog`, `build_lifecycle_plan`, controller) keep their accepted
  semantics and are never executed by Phase 1.
* Only the standard library plus the already-admitted `jsonschema`, `referencing`, and `ruamel.yaml`
  are used; no packaging change is required (`pyproject.toml` already ships `xdl/profiles`).
* No legacy, compatibility, blueprint, oracle/assurance, or historical accepted record is modified;
  no REF-002 parent is closed, promoted, or marked implemented. The 19 `XVE-SYS-*` parent anchors keep
  their original IDs (including `XVE-SYS-00014`), source text, provenance, and
  `disposition = allocated`.

## 11. Limitations and open obligations

* **Candidate-local only.** The reported checks are preliminary worker checks. Only the trusted
  target-repository assembly measure is integration evidence, and only the trusted measures are
  verification evidence.
* **External host bindings.** The trusted policy must bind `unit → XDL1-UNIT`,
  `static_analysis → XDL1-STATIC`, `integration → XDL1-INTEGRATION`, and
  `validation → XDL1-VALIDATION`; without that binding the host gates fail closed.
* **No runtime claim.** A resolved plan proves declared-intent validation only — never artifact
  availability, executable readiness, runtime success, compatibility, parity, or delivery.
* **Scientific values remain caller inputs.** No threshold, tolerance, deadline, repetition, margin,
  or seed from a scientific protocol is defaulted, invented, or narrowed; only finite platform
  library bounds are enforced.
* **Public-safe.** This record uses repository-relative locators only and contains no secret,
  credential, host address, or private source excerpt.

## 12. Maintenance handoff and model recommendation

Reusable usage and maintenance guidance is in [`maintenance.md`](maintenance.md). The later read-only
`internal_review` stage authors `docs/engineering/xdl-lite/internal-review.json`; the review index
`reports/review-index.md` points at it.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most
cost-effective and only authorized route for the next stage, because it is deterministic transcription
of already-frozen, already-verified artifacts; no stronger tier is justified, and there is no new
Terra/Luna/Sol/Astra engineering route in this package, no fallback, and no model switch is claimed or
performed.

Blocker: none in this stage. The trusted measures, the assembled-target integration run, the separate
read-only internal review, and terminal user acceptance remain external host/user obligations and are
pending, not failed.
