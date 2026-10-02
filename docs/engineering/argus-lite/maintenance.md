# Argus Lite Phase 2 — maintenance and usage guide (feature `ARGUS2`)

| Field | Value |
| --- | --- |
| Feature | `ARGUS2` (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation projection import and read-only reconstruction) |
| Stage / role | documentation (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 5 |
| Revision basis | Revision 5 is the documentation rework bound to the revision-6 repaired implementation candidate: the additive repair of both `AR-F03` enclosing-depth failures on the restored rework snapshot `01M3Y16BYA3QHRC6FTRDNAWPAM` (independent frozen review returned rework with two residual `AR-F03` enclosing-depth failures and produced no candidate; the previous implementation handler then timed out at failed run `01M3XPJS7MQEGRNEKA0WV3MXW7`, and its files were completed additively here). Revision 4 was bound to the revision-5 repaired implementation candidate (the repair of the frozen rework snapshot `01M3XY5J8QSRV7V40Q98J73A4Q`, whose independent frozen review returned finding `AR-RVW-001` and produced no candidate). Revision 3 was bound to the revision-4 repaired candidate (frozen rework snapshot `01M3XTPJ9MFBFX8S17X78E0AMS`); revision 2 was the documentation rework for the terminal-review repair candidate; revision 1 was bound to the unaccepted pre-rework candidate (run `01M3WW66FB61DKFEPWFEH2BFJE`, candidate `2f7806599e7df6693b9899fb328762728dbf65d5`, verdict `rework`, findings `AR-F01`–`AR-F05`). No candidate was accepted, so no accepted revision is superseded; this guide is brought onto the reworked design and the repaired revision-6 implementation. |
| Date | 2026-10-02 |
| Model | DeepSeek V4 Flash (`provider=deepseek`, `backend=api`, `requested_model=deepseek-v4-flash`) |
| Admitted platform baseline | `c1fd213cd00259b74f8308d8ca58157ea985aaa0` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`1b6d30ee…`; `ARGUS2-SR-001` … `ARGUS2-SR-012`) |
| Design authority | [`architecture.md`](architecture.md) rev 1 rework (`f2a44c73…`), [`detailed-design.md`](detailed-design.md) rev 1 rework (`4f9537d6…`) |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 rework (`ea6fd473…`) |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 2 (`5e36301a…`) |
| Delivered implementation record | [`implementation.md`](implementation.md) rev 6 file `873b738f…` (authored and hashed by the implementation stage for the revision-6 repaired candidate and bound by `engineering/stage-results/argus2-implementation.json` `b1c08083…`; verified byte-preserved by this stage) |
| Integration / validation records | [`integration.md`](integration.md) rev 6 (`e59ab4b3…`), [`validation.md`](validation.md) rev 5 (`6a794de8…`) |
| Classification | Public-safe engineering work product |
| Maturity | **Implemented candidate, worker-verified only.** The trusted unit/static/integration/validation measures over the sealed candidate, the assembled pinned `xverse-platform` target, the separate read-only `internal_review` and terminal author acceptance are external gates; none is claimed here. Guidance only — it establishes no runtime, readiness, compatibility, parity, certification or delivery claim. |

This guide is for a maintainer or integrator reusing the Phase 2 Argus evidence package. It records the
reusable API/CLI surface, dependencies and compatible versions, frozen limits, loss/incomplete and
recovery behaviour, wheel packaging, clock and authority boundaries, and the change rules to follow when
maintaining or extending it. It authors **no** source, schema, fixture or test code and performs **no**
code repair.

The delivered implementation record for this capability is [`implementation.md`](implementation.md),
authored and hashed by the implementation stage for the revision-6 repaired candidate
(`sha256=873b738ffb75b9d24273c7cb0380cdca3b744ca50b6769af14994bd44ff2850a`, bound by
`engineering/stage-results/argus2-implementation.json`
`sha256=b1c08083b4953b6c4216053d085e21f9c9efaafde34d41b276c546f2370fd71d`). This documentation
stage verified it read-only and preserved it byte-for-byte; it did not rewrite it, because rewriting it
would have invalidated the implementation stage record's stored artifact hash. The repair contract
`AR-F01`–`AR-F05`, the revision-3 continuation gaps, the revision-4 residual repairs, the revision-5
`AR-RVW-001` bounded deep-nesting repair and the revision-6 `AR-F03` enclosing-depth repairs are
described in `implementation.md` sections 2, 2.1, 2.2, 2.3 and 2.4, and its section 5 worker table is
current (232 owned tests, 527 platform tests).

## 1. What the capability does (and does not do)

**Does:** persist a bounded, single-writer, offline evidence run for one accepted XDL resolved experiment
plan — an append-only versioned JSONL event stream plus an atomic JSON run manifest with an artifact
index, declared completeness obligations and an explicit evidence status; import a documented versioned
projection of owned C++ X-COM `ObservationRecord`/`ObservationSnapshot` values by value; and reconstruct
that evidence read-only with deterministic selection, hash verification and declared metric-input links.

**Does not:** execute, control, actuate or orchestrate anything; attach, pull or acknowledge a live tap;
change provider delivery, reserve lossless capacity, dispatch messages or interpret provider success as
experiment success; compute a metric, invoke an oracle or produce a dashboard; use an ambient clock,
random identity, locale, environment, user or home-directory lookup; convert or compare across clock
domains; access the network, a socket, a subprocess, a service, a daemon or a database; add a runtime
dependency; accept a new configuration dialect, Parquet, or a live cross-language bridge; or execute any
production or legacy workload. Replay is evidence reconstruction only.

## 2. Dependencies and compatible versions

Runtime dependencies (already declared in `pyproject.toml`; Phase 2 adds **none**):

| Dependency | Constraint | Role |
| --- | --- | --- |
| Python | `>=3.11` | runtime |
| `jsonschema[format]` | `>=4.26,<5` | accepted XDL schema registry (reused, unchanged) |
| `referencing` | `>=0.37,<1` | schema `$id` resolution (reused, unchanged) |
| `ruamel.yaml` | `>=0.19.1,<0.20` | accepted XDL resource parsing (reused, unchanged) |
| `pytest` | verification environment | test runner |

Argus itself imports only the Python standard library (`json`, `hashlib`, `os`, `pathlib`, `dataclasses`,
`copy`) plus the accepted `xverse_xdl.experiment_plan` public API for plan verification. No new
dependency, service, metrics backend or oracle is introduced.

Distribution and entry points (additive; the accepted names are unchanged):

| Item | Value |
| --- | --- |
| Distribution name | `xverse-xdl` (version `0.4.0`) — **unchanged** |
| Python package | `xverse.argus` (new) alongside `xverse_xdl` (unchanged) |
| Console scripts | `xdl = "xverse_xdl.cli:main"` (unchanged) and `xverse-argus = "xverse.argus.cli:main"` (new) |
| Argus package version token | `0.1.0`, exported as `ARGUS_VERSION` and reported as `argusVersion` and distinct from `xverse-xdl` |

Frozen version identities (see [`detailed-design.md`](detailed-design.md) section 2):

| Identity | Frozen value |
| --- | --- |
| Event record schema | `eventSchemaVersion = "1.0"` |
| Manifest schema | `manifestVersion = "1.0"` |
| Observation projection schema | `projectionVersion = "1.0"`; upstream `upstreamContractVersion = "1.0.0"` |
| Snapshot projection schema | `snapshotVersion = "1.0"` |
| Task token | `ARGUS2` |

Version rule: each version value must be a string `<major>.<minor>` of decimal integers. An unknown
`major` (anything other than `1`) is rejected with `ARGUS2-SCHEMA-MAJOR-UNSUPPORTED`. A `major` of `1`
with any `minor` is accepted, because a minor bump is additive. Unknown **fields** are **never silently
ignored**: they are rejected explicitly with `ARGUS2-SCHEMA-UNKNOWN-FIELD`.

## 3. Public Python API

The public surface is exported from `xverse.argus` (`EvidenceStore`, `EvidenceRun`, `EvidenceReader`,
`EvidenceManifest`, `EvidenceLimits`, `EvidenceDiagnostic`, `EvidenceError`, plus the version constants
`ARGUS_VERSION`, `EVENT_SCHEMA_VERSION`, `MANIFEST_VERSION`). Frozen signatures
([`detailed-design.md`](detailed-design.md) section 14):

```python
class EvidenceStore:
    @classmethod
    def open_run(cls, root, *, run_id, plan, run_envelope=None, source_byte_digests=None,
                 limits=None, obligations=(), clocks=None) -> "EvidenceRun": ...
    @classmethod
    def read_run(cls, root, *, limits=None) -> "EvidenceReader": ...

class EvidenceRun:
    @property
    def run_id(self) -> str: ...
    @property
    def writer_state(self) -> str: ...
    def append_event(self, *, event_id, producer_id, event_kind, producer_sequence=None,
                     correlation_id=None, causation_id=None, clocks=None, annotation=None,
                     extensions=None) -> int: ...
    def import_observation(self, projection) -> tuple[int, ...]: ...
    def import_snapshot(self, snapshot, *, event_id=None) -> int: ...
    def record_artifact(self, relative_path, *, media_type="application/json",
                        schema_version="1.0", role="evidence") -> dict: ...
    def flush_buffer(self) -> None: ...
    def finalize(self, *, finalized_at=None) -> "EvidenceManifest": ...
    def abort(self, *, reason=None) -> None: ...

class EvidenceReader:
    # read-only properties
    diagnostics: tuple[EvidenceDiagnostic, ...]
    manifest: dict                          # deep copy; property, not a method
    recorded_evidence_status: str | None    # recorded manifest fact, echoed verbatim
    recorded_evidence_reasons: list[str]
    assessed_evidence_status: str           # the reader's own conclusion
    assessed_evidence_reasons: list[str]
    # frozen camelCase aliases
    recordedEvidenceStatus / recordedEvidenceReasons
    assessedEvidenceStatus / assessedEvidenceReasons
    # methods
    def records(self) -> list[dict]: ...        # ingestion-ordinal order, independent copies
    def metric_inputs(self) -> list[dict]: ...  # declared links only; no metric computed
    def export_json(self) -> str: ...
    def export_jsonl(self) -> str: ...
```

`EvidenceRun.record_artifact` indexes a confined regular file already present inside the run root and
returns an independent copy of the index entry; its size/hash identity is computed and owned at record
time (see section 11 and [`detailed-design.md`](detailed-design.md) section 12.2). `EvidenceReader`
returns deep copies from `manifest`, `records` and `metric_inputs`, so a caller that mutates a returned
view cannot rewrite an internal admission fact or an indexed artifact hash (`AR-F05`).

Caller responsibilities: the caller supplies the output root, the unique `run_id`, the accepted resolved
plan, the run envelope, the explicit source-byte digests, the declared capture `obligations`, the clock
values and the finite `limits`. Argus never invents any of them and never defaults a scientific,
safety or campaign value. `plan` must verify against the accepted `plan_matches_digest` semantics; the
caller's source-byte digests are preserved **separately** as run provenance and are not folded into plan
identity.

Minimal usage (all values caller-supplied; no ambient state is read):

```python
from xverse.argus import EvidenceStore, EvidenceLimits

limits = EvidenceLimits(max_events=1_000, max_payload_bytes=256)
run = EvidenceStore.open_run(
    "/tmp/my-run", run_id="run-0001", plan=resolved_plan,
    source_byte_digests={"scenario.xdl.yaml": "…"}, limits=limits,
    obligations=(),
)
run.append_event(event_id="evt-0001", producer_id="caller", event_kind="annotation")
run.import_observation(projection_record)   # owned X-COM projection mapping (see section 5)
run.import_snapshot(snapshot_record)        # explicit interval/counter snapshot
run.finalize()

reader = EvidenceStore.read_run("/tmp/my-run")
records = reader.records()                    # ingestionOrdinal order, deterministic
export = reader.export_json()                 # assessed status is the primary evidenceStatus
status = reader.assessed_evidence_status      # "complete" only when assessed clean
```

`open_run` rejects an existing run root (`ARGUS2-STATE-RUN-EXISTS`), a second in-process owning writer
for the same root (`ARGUS2-STATE-WRITER-CONFLICT`) and any admission defect **before** the run root or
any file is created, so a rejected open leaves no partial state. A run is never reopened for writing.

## 4. CLI usage

The `xverse-argus` console script is strictly read-only; writing is programmatic only through
`EvidenceStore.open_run`.

```
usage: xverse-argus {verify|export} <run-root> [--format json|jsonl]
```

| Command | Behaviour | Exit code |
| --- | --- | --- |
| `xverse-argus verify <run-root>` | prints the manifest/verification summary (`runId`, `writerState`, both the assessed and the recorded evidence status/reasons, `eventCount`, diagnostics) as canonical JSON | `0` only when the **assessed** status is `complete` and there are no diagnostics; `1` incomplete/corrupt (including a manifest that recorded `complete`); `2` usage/input error |
| `xverse-argus export <run-root> --format json` | writes one canonical JSON export document to stdout | `0`; `2` on usage/input error |
| `xverse-argus export <run-root> --format jsonl` | writes the event records as canonical JSONL to stdout | `0`; `2` on usage/input error |

The CLI never mutates a run root and never repairs, upgrades or truncates evidence. `verify` echoes the
recorded manifest claims separately from the reader's assessed conclusion (`AR-F02`); a corrupt or
truncated run is never reported as primary `complete`.

## 5. Observation and snapshot inputs

Argus consumes an explicit versioned projection of the owned C++ `ObservationRecord` accessors
(`src/xverse/xcom/include/xverse/xcom/observation.hpp`, contract `1.0.0`), produced by a real owned
producer fixture that serializes the values. No callback, hub handle, provider handle or delivery
authority enters Argus.

Projection envelope: `{"projectionVersion": "1.0", "upstreamContractVersion": "1.0.0",
"exporter": {...}, "records": [ ... ]}`. Each record preserves, exactly and without reinterpretation:
logical identity and versions, interaction/origin, source and observation clock values and their
domains, optional sequence, correlation/causation references, route/provider, source payload size,
provider outcome, payload visibility state, visible bytes, tap identity and retention-time counters.

Fail-closed visibility invariants: `omitted`/`redacted` => 0 visible bytes and empty hex;
`complete` => `visibleByteCount == sourcePayloadSize`; `truncated` => `0 < visibleByteCount < sourcePayloadSize`;
`payloadSchemaState` is always `undecoded` in this slice; a byte count that disagrees with the encoded
bytes is rejected (`ARGUS2-INPUT-PAYLOAD-LENGTH`). Bytes are never synthesized or padded.

Snapshot input carries final counters, backpressure rejections, declared validity
effect/state and **caller-supplied** `intervalProvenance` (`streamId`, `intervalId`, `closure`
`closed|unclosed|unavailable`, `start`, `end`, `provenance`). The owned C++ snapshot carries no interval
window, so the interval is imported, never inferred from counters: a `closed` closure with absent
`start`/`end` is rejected (`ARGUS2-INPUT-INTERVAL-INCOMPLETE`), and an `unclosed`/`unavailable` closure
is recorded as unresolved and forces the dependent obligations to stay incomplete.

The narrower tool-gateway protobuf `ObservationRecord` is a **distinct** schema and must not be
substituted for the full owned projection; it may only be imported through a separate explicitly
versioned mapping that records missing fields as unavailable.

## 6. Limits

`EvidenceLimits` is a frozen dataclass of eleven positive integers, supplied by the caller and echoed
into the manifest so the reader verifies under the same bounds:

| Field | Library default | Meaning |
| --- | --- | --- |
| `max_event_bytes` | `1048576` | Maximum canonical bytes of one JSONL event line |
| `max_events` | `100000` | Maximum accepted events per run |
| `max_id_length` | `128` | Maximum length of `runId`/`eventId`/`producerId`/identities |
| `max_text_length` | `256` | Maximum length of clock domains/units and annotation text |
| `max_payload_bytes` | `1024` | Maximum visible payload bytes stored per observation |
| `max_artifacts` | `256` | Maximum entries in the artifact index |
| `max_obligations` | `64` | Maximum declared obligations |
| `max_diagnostic_count` | `256` | Maximum diagnostics returned/retained per operation |
| `max_manifest_bytes` | `4194304` | Maximum exact bytes of the manifest as written (canonical encoding plus its single trailing newline), measured at **every** publication |
| `max_causal_index_entries` | `4096` | Maximum causal-index entries |
| `max_read_records` | `100000` | Maximum records returned by one bounded read/export |

Any exceeded bound rejects with `ARGUS2-BOUND-EXCEEDED` naming the field, and no diagnostic is produced
without an actual violation. A non-positive or non-integer field is a library programming error
(`ValueError`), not an evidence diagnostic. **These are implementation limits, not scientific, safety or
performance thresholds**; no threshold, tolerance, deadline, seed or margin is defaulted or narrowed.

Caller limits are **authoritative**: a manifest `limits` echo is untrusted recorded data. On read, the
effective bound for each field is the stricter of the caller limit and the recorded echo, so a damaged
input cannot enlarge the bounds under which it is parsed (`AR-F01`). The manifest byte bound
(`max_manifest_bytes`) is measured on the exact serialized manifest bytes as written — the canonical
encoding plus its single trailing newline, including the artifact index, obligations and finalize/abort
metadata — through the single publication chokepoint (`AR-F04`). The `open_run` preflight applies the
same newline-inclusive rule, so an over-bound open is refused before any run root is created.

`EvidenceLimits` is the complete caller-configured bound set. The JSON nesting guard
`schema.MAX_JSON_NESTING` (128) is an **internal defensive bound, not a caller `EvidenceLimits` field
and not a scientific, safety or performance threshold**; it exists so that a small but adversarially
deep document cannot exhaust the interpreter stack (`AR-RVW-001`, see sections 7 and 8).

## 7. Loss, incomplete and recovery behaviour

`writerState` and evidence status are independent axes. Writer states are `new -> open -> closed`, or
`open -> failed`; any other transition is rejected with `ARGUS2-STATE-ILLEGAL-TRANSITION`.

Two evidence statuses are kept separate (`AR-F02`):

* **Recorded** (`recordedEvidenceStatus`/`recordedEvidenceReasons`) — the facts the manifest claims,
  echoed verbatim and never trusted as the reader's conclusion.
* **Assessed** (`assessedEvidenceStatus`/`assessedEvidenceReasons`) — the read-only reader's own
  verification conclusion. It is `complete` only when there are no assessed reasons and no diagnostics;
  otherwise it is `incomplete`. `export_json` carries the assessed status as the primary
  `evidenceStatus` and the recorded facts alongside.

| Situation | Recorded / assessed evidence status |
| --- | --- |
| While the writer is `open` | recorded `unassessed`; a read is assessed `incomplete` |
| Finalize with a clean stream, all artifacts verified, all `required` obligations satisfied, empty reasons | recorded `complete`; assessed `complete` |
| Truncated last line, missing/mutated artifact, unmet obligation, known drop, degraded/invalid interval, unresolved causation, unclosed/unavailable interval closure, unsupported schema, unexpected writer state | recorded `incomplete` with the applicable closed reason code; assessed `incomplete` |
| Corrupt/truncated manifest or event records with no valid recorded status | recorded facts absent/echoed; assessed `incomplete` (`ARGUS2-REASON-CORRUPT-MANIFEST` / `ARGUS2-REASON-CORRUPT-EVENT`) |
| Closed manifest whose status field is absent or unknown | assessed `incomplete` (`ARGUS2-REASON-WRITER-STATE`) |

Closed evidence reason codes: `ARGUS2-REASON-{TRUNCATED-STREAM, MISSING-ARTIFACT, MUTATED-ARTIFACT,
UNMET-OBLIGATION, KNOWN-LOSS, DEGRADED-INTERVAL, INVALID-INTERVAL, UNRESOLVED-CAUSATION,
UNCLOSED-INTERVAL, UNSUPPORTED-SCHEMA, WRITER-STATE, CORRUPT-MANIFEST, CORRUPT-EVENT}`. Known
observation loss, degraded/invalid intervals, unresolved causation and unclosed intervals **remain
visible and can never be upgraded to `complete` by finalization alone**. Closing the stream and proving
completeness are separate facts: `complete` means only that the caller-declared capture obligations and
integrity checks were verified, never that an experiment succeeded or is scientifically valid.

Durability is a **bounded local filesystem guarantee**: manifest publication uses
`write temp -> flush -> fsync -> os.replace -> fsync directory`; appended lines are durable at
`flush_buffer()` (`flush` + `fsync`), which `finalize()` calls before hashing. It is **not** a
power-loss, hardware, distributed or network-filesystem guarantee, and no such claim is made. Every
manifest publication (open, successful finalize, failed finalize and abort) is measured and bounded by
`max_manifest_bytes` before the atomic replace; on an exceeded bound or an I/O failure the prior
manifest bytes remain and the writer never reports `closed`/`complete` (`AR-F04`).

Recovery (`recover_stream`) reads a bounded, confined prefix and **never writes**. Path confinement
checks every recorded path component before any I/O: `os.lstat` traversal/symlink/escape rejection and
a required regular file, with `O_NOFOLLOW` opening and a device/inode re-check (TOCTOU). A final line
without a terminating `\n`, or a line that is not valid canonical JSON, is a truncated record reported
as `ARGUS2-CORRUPT-STREAM-TRUNCATED`; it is never counted as an accepted event, its apparent content is
never repaired, and the original run-root files are left byte-identical. Diagnostic emission is bounded
by `max_diagnostic_count` and adds one bounded `ARGUS2-BOUND-EXCEEDED` on overflow, so damaged input
cannot amplify diagnostics in memory (`AR-F01`).

A small but adversarially deep JSON document is refused by an iterative, string-aware, linear nesting
scan (`schema.json_text_depth_exceeded`) **before** any recursive decode or deep copy, so a too-deep
manifest or event line yields a stable bounded diagnostic instead of an uncaught `RecursionError`
(`AR-RVW-001`): `reader.read_run` reports `ARGUS2-CORRUPT-MANIFEST-SHAPE` and `recovery.recover_stream`
reports the existing `ARGUS2-CORRUPT-STREAM-TRUNCATED` line diagnostic.

An admitted event record or declared obligation whose nesting fits the standalone parse bound but
exceeds it once an owned document wrapper encloses it is contained the same way (`AR-F03` enclosing
depth, revision 6). `reader._EXPORT_WRAP_DEPTH = 2` records the two export-document wrap levels:
`reader.read_run` flags any admitted record exceeding `MAX_JSON_NESTING - 2` with one bounded
`ARGUS2-BOUND-EXCEEDED` diagnostic and assesses the run `incomplete`, `export_json` withholds only that
over-deep record so neither the JSON API nor the CLI `export` raises and neither reports a primary
`complete` status, and the admitted record remains visible through `records()`. Symmetrically,
`api.open_run` and `writer._publish` convert a manifest-preview nesting overflow into a bounded
`ARGUS2-INPUT-FIELD-INVALID` `EvidenceError` before any run root or temporary file is created, so the
prior manifest bytes are preserved and no `closed`/`complete` persistence is claimed.

## 8. Diagnostics

Every diagnostic carries `{code, category, severity, message, pointer?, path?, eventId?, remediation}`
and belongs to a closed catalogue. Categories distinguish the required classes:
`input-rejection` (`ARGUS2-INPUT-*`), `io-failure` (`ARGUS2-IO-FAILURE`), `unsupported-schema`
(`ARGUS2-SCHEMA-*`), `corrupt-artifact` (`ARGUS2-CORRUPT-*`), `missing-evidence` (`ARGUS2-MISSING-*`)
and `known-observation-loss` (`ARGUS2-LOSS-*`), plus the auxiliary `bounds` (`ARGUS2-BOUND-EXCEEDED`),
`path` (`ARGUS2-PATH-ESCAPE`, `ARGUS2-PATH-SYMLINK`, `ARGUS2-PATH-UNSAFE`, `ARGUS2-PATH-NOT-REGULAR`),
`state` (`ARGUS2-STATE-*`), `clock` (`ARGUS2-CLOCK-UNRESOLVED`), `causal` (`ARGUS2-CAUSAL-UNRESOLVED`)
and `plan` (`ARGUS2-PLAN-DIGEST-MISMATCH`, `ARGUS2-PLAN-VERSION-UNSUPPORTED`,
`ARGUS2-PLAN-ENVELOPE-CONFLICT`) families. `EvidenceError.diagnostics` carries the ordered diagnostics;
nothing is silently discarded, no timestamp is repaired and no producer or version is guessed. Malformed
container types, unsupported versions, damaged shapes and I/O faults are always converted into bounded
`corrupt-artifact`/`io-failure`/`unsupported-schema` diagnostics; no uncaught `TypeError` or `ValueError`
escapes the reader or the CLI (`AR-F03`). A parsed manifest that carries `NaN`, `Infinity` or
`-Infinity` at any depth — including an overflowing numeric literal such as `1e400` — is rejected as a
single bounded `ARGUS2-INPUT-NONFINITE` diagnostic **before** the schema-version check, the limits echo,
assessment or export, with the recorded manifest facts left separately visible and the run assessed
`incomplete`; no non-finite value ever reaches an `allow_nan=False` serialization. Adversarial deep
nesting is contained at every parse, serialize and admission boundary: the linear scanner rejects
over-deep raw JSON with a bounded `ValueError` before decoding, and `canonical_json` does the same for
an already-parsed value, so manifest parsing, event-line parsing, canonical serialization, `open_run`
obligations and `append_event` extensions/observation each return a closed bounded diagnostic
(`ARGUS2-CORRUPT-MANIFEST-SHAPE`, `ARGUS2-CORRUPT-STREAM-TRUNCATED` or `ARGUS2-INPUT-FIELD-INVALID`)
rather than an uncaught `RecursionError` (`AR-RVW-001`). The same containment covers the enclosing
depth of an owned document wrapper (`AR-F03`, revision 6): an admitted event record that would exceed
the bound once wrapped in the export document yields one bounded `ARGUS2-BOUND-EXCEEDED` diagnostic and
an assessed `incomplete` status on both the JSON and CLI export paths (the record is withheld, never a
primary `complete`, and the API/CLI never raise), and an admitted obligation that would overflow the
manifest preview yields a bounded `ARGUS2-INPUT-FIELD-INVALID` `EvidenceError` before any run root or
temporary file is created.

## 9. Wheel packaging and consumer compatibility

`pyproject.toml` changed additively only: `[project.scripts]` gained
`xverse-argus = "xverse.argus.cli:main"` (the `xdl` entry is unchanged), `name = "xverse-xdl"` is
unchanged, and the frozen wheel selection keeps `packages = ["src/xverse_xdl"]` while adding
`force-include` entries mapping `src/xverse/argus` -> `xverse/argus` and `src/xverse/__init__.py` ->
`xverse/__init__.py`. Only the Argus package (never the C++ `xcom` tree) enters the wheel.

Consumer contract verified by the owned integration module and repeated by the trusted host: the built
and installed wheel resolves both `xverse.argus` and `xverse_xdl.experiment_plan` **outside the source
tree** with `PYTHONPATH` pointing only at the installed target, while the accepted platform C++ sources
and XDL fixtures are resolved from the caller environment `ARGUS_PLATFORM_SOURCE_ROOT` (set to
`/target` during trusted checks; the repository root is the ordinary local-test fallback). Platform
`src` must never be injected into `sys.path` or `PYTHONPATH`. The accepted `xdl` CLI and the
`xverse_xdl` public API remain intact.

## 10. Clock and authority boundaries

* Clock values are always explicit: a caller-supplied `{domain, unit, value}` with a finite value. Argus
  reads no ambient clock, never infers a unit, never converts and never compares across domains. A
  missing clock, domain or unit is rejected (`ARGUS2-INPUT-CLOCK-MISSING` / `ARGUS2-INPUT-UNIT-MISSING`).
* Ingestion order (`ingestionOrdinal`) is local deterministic stream order and is **distinct** from
  temporal and causal order. A causation link or producer sequence is explicit evidence, not proof of
  clock synchronisation; unresolved causal references stay visible (`ARGUS2-CAUSAL-UNRESOLVED`).
* Authority is entirely caller-supplied: identity, clocks, limits and obligations. Argus holds no
  observation, delivery, control, orchestration or actuation authority, and it never acknowledges a
  degraded interval or changes provider delivery.
* Admission is a boundary: obligations (including nested `detail`), the run envelope, source-byte
  digests, clock declarations, annotation and extensions are deep-snapshotted by canonical round-trip at
  admission, so post-admission mutation of a caller-owned object cannot lower an obligation or rewrite
  an indexed file hash (`AR-F05`).

## 11. Maintenance and change rules

1. **Work product set.** This capability's work products are `docs/engineering/argus-lite/**`, the
   `engineering/stage-results/argus2-*.json` records, the ARGUS2 requirement/component/unit/measure/
   scenario records and the ARGUS2 trace links. Keep implemented, partial, target and exploratory work
   distinct and never weaken a record to make a gate pass.
2. **Additive evolution only.** A minor schema bump is additive; unknown fields must be rejected
   explicitly, never silently ignored. A new major version requires its own design freeze and gates.
3. **Ownership boundaries.** Do not modify accepted `src/xverse_xdl/**`, `xdl/**`,
   `src/xverse/xcom/**`, `proto/xverse/xcom/v1/**`, `tests/xcom/**`, historical accepted records/ADRs
   or `engineering/verification/measures/**`. C++ X-COM remains the owner of the observation contract;
   the owned C++ fixture is test material compiled under `/tmp` and no public C++ API changes.
4. **Diagnostics are closed.** Never emit an uncatalogued code and never relax an assertion. A change to
   the catalogue is a design change that requires the full workflow, not a maintenance edit.
5. **Trace upkeep.** `engineering/trace/links.json` binds each `implemented_by` endpoint to the exact
   file SHA-256. After any accepted change to an implementation file, refresh only the affected code
   endpoints; the validation stage owns the mutable current-endpoint finalization.
6. **Re-verification.** After any change, re-run the owned Argus suite
   (`python3 -m pytest -q -p no:cacheprovider tests/thesis_lite/argus`), the full platform suite
   (`python3 -m pytest -q -p no:cacheprovider tests`) and the installed-wheel consumer path from
   section 9. The trusted measures must be re-bound to the successor candidate revision; stale or
   mismatched evidence cannot support acceptance.
7. **Documentation duties.** Maintain this guide, list [`implementation.md`](implementation.md) as the
   delivered implementation record (do not rewrite it in place once its stage record binds its hash) and
   maintain the review index pointer; record findings from a separate read-only review before repairing
   them, and route the repaired candidate through repeated verification and review.
8. **Delivery.** After explicit author acceptance, merge the exact accepted artifacts into
   `xverse-platform/main`, verify the assembled platform, and record the resulting commit and
   verification evidence.

## 12. Known limitations

* Trusted unit/static/integration/validation measures over the sealed candidate, the assembled pinned
  `xverse-platform` target run, candidate sealing, the separate read-only `internal_review` and terminal
  author acceptance are external host/user gates. Worker-run checks recorded in
  [`implementation.md`](implementation.md), [`integration.md`](integration.md) and
  [`validation.md`](validation.md) are **not** reported as trusted verification.
* Durability is bounded and local (see section 7); no power-loss, distributed or network-filesystem
  guarantee is offered or tested.
* Successful finalization proves only that caller-declared capture obligations and integrity checks
  were satisfied. It never proves scientific validity, safety, compatibility, parity or readiness.
* `payloadSchemaState` is always `undecoded` in this slice: Argus never claims decoder success.
* Argus computes no metric and invokes no oracle; `metricInputs` are declared references and an
  incomplete selection is reported, never filled in.
* Record-consistency note (resolved): the earlier revision-3 presentation discrepancy between
  `implementation.md` and its stage record is resolved. The delivered [`implementation.md`](implementation.md)
  is now the revision-6 record (`873b738f…`), whose header and section 5 worker table agree with the
  revision-6 totals (`232` owned tests, `527` platform tests) recorded in
  `engineering/stage-results/argus2-implementation.json` (`b1c08083…`), [`integration.md`](integration.md)
  rev 6 (`e59ab4b3…`) and [`validation.md`](validation.md) rev 5 (`6a794de8…`).
* Internal defensive bound: `schema.MAX_JSON_NESTING` (128) is an implementation-internal guard against
  adversarial nesting (`AR-RVW-001`), not a caller `EvidenceLimits` field and not a scientific, safety
  or performance threshold; it does not constrain any legitimate bounded evidence.
* No REF-002 parent disposition is promoted or closed and no new system requirement ID is created by
  this capability.
* Inherited limitation: the admitted planning bundle names a required launch-evidence
  `admission/review.md` that is not an admitted input for this run; it remains an external, unverified
  later-gate input and is neither fabricated nor substituted.

## 13. Worker verification summary (candidate-local, not trusted evidence)

Transcribed from [`integration.md`](integration.md) rev 6 and [`validation.md`](validation.md) rev 5;
these are worker observations over the revision-6 repaired candidate, not trusted target-repository
verification:

* `python3 -m pytest -q -p no:cacheprovider tests/thesis_lite/argus` — `232 passed` (193 unit: 172
  frozen `ARGUS2-UNIT` plus 21 additive adversarial repair cases, 9 `ARGUS2-INTEGRATION`, 30
  `ARGUS2-VALIDATION`).
* `python3 -m pytest -q -p no:cacheprovider tests` — `527 passed`, no regression in the accepted XDL,
  catalog, lifecycle, CLI or C++ X-COM suites.
* All 211 frozen measure identifiers (172 unit + 9 integration + 30 validation) collected, 0 missing;
  the 21 additive cases include the `AR-RVW-001` bounded deep-nesting cases and the revision-6 `AR-F03`
  enclosing-depth cases.
* Static AST parse of every candidate `src/**/*.py` plus the owned tests — `STATIC_CHECK_PASSED` over
  the 18 `ARGUS2-STATIC` structural checks, without writes.
* Bounded `/tmp` replication of the installed-wheel consumer check: offline wheel build/install of
  `xverse-xdl-0.4.0`, `INSTALLED_CONSUMER_IMPORT_PASSED` for `xverse.argus` and
  `xverse_xdl.experiment_plan` outside the source tree with `PYTHONPATH` set only to the installed
  target and `ARGUS_PLATFORM_SOURCE_ROOT` set to the target, and `232 passed` for the copied owned
  tests.
* Real interoperability: the accepted XDL compiler compiles the owned neutral fixtures and the owned
  C++20 producer fixture is compiled with `g++ -std=c++20` against the accepted X-COM `observation.hpp`
  and its translation units to serialize owned `ObservationRecord`/`ObservationSnapshot` values; no
  public C++ source was changed.
* `fabro_engineering.core.validate_trace` returns `{'artifacts': 968, 'links': 3595}` with no stale
  endpoint.

## 14. Model and next step

The pinned `deepseek-v4-flash` with **high** reasoning remained the only authorized and most
cost-effective route for this deterministic documentation work; no model switch, no subagent and no
fallback occurred, and no benchmark or exact-cost claim is made. Escalation would be justified only by a
measured, reproducible failure this route cannot resolve.

Next step: **separate read-only `internal_review`** over the sealed candidate, replacing the interim
review pointer in `reports/review-index.md` with the reviewer's verdict and reviewed-file/hash map. The
trusted host must still bind and execute the four ARGUS2 measures against the sealed candidate, and
terminal author acceptance precedes any merge into `xverse-platform/main`. Blockers: none for this
stage.
