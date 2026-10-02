# Argus Lite Phase 2 — implementation record

| Field | Value |
| --- | --- |
| Feature | ARGUS2 (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation projection import and read-only reconstruction) |
| Stage / role | implementation (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 6 |
| Revision basis | Continuation of the frozen-review rework of the 2026-10-01 implementation (independent review run `01M3WW66FB61DKFEPWFEH2BFJE`, candidate `2f7806599e7df6693b9889fb328762728dbf65d5`, verdict `rework`, findings `AR-F01`–`AR-F05`), of the revision-3/4/5 continuations (`01M3XTPJ9MFBFX8S17X78E0AMS`, `01M3XY5J8QSRV7V40Q98J73A4Q`), and of the restored rework snapshot `01M3Y16BYA3QHRC6FTRDNAWPAM` whose independent frozen review returned the two residual `AR-F03` enclosing-depth failures and produced no candidate. The previous implementation handler timed out (failed run `01M3XPJS7MQEGRNEKA0WV3MXW7`); its source, tests and stage record were restored as unfinished draft evidence and are completed additively here. The rejected candidate was never accepted, so no accepted revision is superseded; every previously passing case is preserved and the continuation cases are additive. This revision-7 continuation starts from the rebased, hash-verified revision-6 snapshot whose frozen review returned the residual `AR-F01` recorded `eventStream.path` defect and produced no candidate. |
| Date | 2026-10-02 |
| Admitted platform baseline | `c1fd213cd00259b74f8308d8ca58157ea985aaa0` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`ARGUS2-SR-001` … `ARGUS2-SR-012`, immutable) |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 (`f2a44c73…`), [`detailed-design.md`](detailed-design.md) rev 1 (`4f9537d6…`) |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 (`ea6fd473…`) |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 rev 2 (`5e36301a…`) |
| Language | Python 3.11+ for `src/xverse/argus/**` (rationale in `architecture.md` §8.1) |
| Classification | Public-safe engineering work product |
| Maturity | **Implemented candidate.** Local worker execution only; trusted unit/static/integration/validation measures, the pinned target assembly, independent review and author acceptance are external gates and are not claimed here. |

## 1. What was implemented

The reworked frozen Argus design was implemented exactly: a bounded, single-writer, offline Python
evidence package that persists a versioned causal event stream plus an atomic run manifest, imports a
documented versioned projection of owned C++ X-COM `ObservationRecord`/`ObservationSnapshot` values,
and reconstructs that evidence read-only. No design change or independent decision was made; the
diagnostic catalogue, event/manifest/projection schemas, API/CLI signatures, bounds, durability steps,
confinement rules, assessed-completeness semantics and admission-snapshot isolation follow the frozen
`detailed-design.md` sections 4.4, 8.5, 11.1, 12.1, 12.2 and 14.1 verbatim.

## 2. Terminal-review repair (`AR-F01`–`AR-F05`, `ARGUS2-ADV-01`–`ARGUS2-ADV-07`)

| Finding | Repair in the candidate |
| --- | --- |
| `AR-F01` read confinement and resource bounds (`ARGUS2-ADV-01`, `ARGUS2-ADV-02`) | `recovery.open_confined` validates the recorded path text, `os.lstat`-checks every path component for symlinks and resolved escape, requires a regular file, opens with `O_NOFOLLOW` and re-checks `os.fstat` (device/inode) before any read. `read_confined_bytes` reads at most the caller bound + 1 and never parses partial bytes. `recover_stream` reads line-by-line, bounds each line by `max_event_bytes` and the stream by the derived `max_events × max_event_bytes` total, and caps records by `max_read_records`; diagnostics are capped by `max_diagnostic_count`. The reader's manifest read is bounded by `max_manifest_bytes`. Caller limits are authoritative; a manifest `limits` echo is recorded data only and is combined with the stricter per-field minimum. Continuation: `recover_stream` emits diagnostics through a bounded collector that stops at `max_diagnostic_count` and adds one bounded `ARGUS2-BOUND-EXCEEDED`, so damaged input cannot amplify diagnostics in memory. |
| `AR-F02` assessed completeness reflects corruption (`ARGUS2-ADV-03`) | `EvidenceReader` exposes `recorded_evidence_status`/`recorded_evidence_reasons` (recorded manifest facts, echoed verbatim) separately from `assessed_evidence_status`/`assessed_evidence_reasons` (the reader's own conclusion). `export_json` carries the assessed status as the primary `evidenceStatus` and the recorded facts alongside; the CLI exits `0` only when the assessed status is `complete`. A corrupt/truncated/unsupported/malformed run is never primary `complete`. |
| `AR-F03` strict schemas, identities and stable diagnostics (`ARGUS2-ADV-04`, `ARGUS2-ADV-05`) | `recovery.validate_event_record` re-applies the complete closed event/clock/observation/snapshot schema on read, requires `runId`/`eventId`/`producerId`, positive `ingestionOrdinal`, declared clock domains/units and finite values; the recovery loop enforces per-run `eventId` uniqueness (`ARGUS2-CORRUPT-DUPLICATE-EVENT`), strictly increasing ordinals (`ARGUS2-CORRUPT-ORDINAL`) and manifest run-ID consistency (`ARGUS2-CORRUPT-RUN-ID-MISMATCH`). Malformed containers/versions/decode/I/O faults become bounded closed-catalogue diagnostics; no `TypeError`/`ValueError`/JSON error escapes the reader or CLI. Continuation: malformed `clockDomains` is rejected as `ARGUS2-CORRUPT-MANIFEST-SHAPE` and malformed `metricInputs` entries are tolerated (`_string_list`) instead of raising while exporting. Revision 4: `schema.find_nonfinite` scans the parsed manifest iteratively and the reader rejects any NaN/Infinity (including an overflowing `1e400` literal) anywhere in it with a single bounded `ARGUS2-INPUT-NONFINITE` diagnostic *before* any assessment, limit handling or export, so no non-finite value ever reaches an `allow_nan=False` serialization. |
| `AR-F04` manifest byte bound at every publication (`ARGUS2-ADV-06`) | `writer._publish` is the single publication chokepoint: it measures the actual canonical serialized bytes against `max_manifest_bytes` before creating a temporary file, and only then writes + `flush` + `fsync` + atomic `os.replace`. Open, successful finalize, failed finalize and abort all route through it; the writer state advances to `closed` only after the publication succeeds, so a bound or I/O failure preserves the prior manifest bytes and never reports `closed`/`complete`. Revision 4: the measured value is the exact on-disk form, the canonical encoding **plus its single trailing newline** (`len(encoded) + 1`), and the `open_run` preflight uses the same rule so an over-bound open is refused before any run root is created. |
| `AR-F05` admission snapshots and immutable views (`ARGUS2-ADV-07`) | `api._admission_snapshot` canonical-round-trips every admitted obligation (including nested `detail`); the run envelope clock, source-byte digests, clocks, annotation and extensions are deep-copied at admission, so no caller-owned mutable reference is retained. Continuation: `annotation` and `extensions` are canonical-round-tripped (`_admission_snapshot`) and a final serialization guard converts any residual non-finite/non-JSON content into a stable `ARGUS2-INPUT-FIELD-INVALID` before any byte is written. `record_artifact` returns an independent copy while owning its size/hash identity internally; `EvidenceReader.records`/`manifest`/`metric_inputs` and the `EvidenceManifest` accessors return defensive deep copies, so a caller that mutates a returned view cannot rewrite an internal admission fact or an indexed artifact hash. |

### 2.1 Continuation repairs (revision 3)

An independent adversarial audit of the restored draft found three residual `AR-F01`/`AR-F03`/`AR-F05`
gaps; all are repaired additively and proved by eight new owned cases in
`tests/thesis_lite/argus/test_argus2_repair_unit.py`. No inherited assertion, diagnostic, identifier or
fixture is changed.

| Residual gap | Continuation repair |
| --- | --- |
| `AR-F03` malformed manifest member containers raised an uncaught `TypeError` | A non-list `clockDomains` is now a frozen-shape defect (`ARGUS2-CORRUPT-MANIFEST-SHAPE`) and the declared-domain loop is guarded; `EvidenceReader.metric_inputs` uses `_string_list` so scalar/`null` sub-members of a damaged `metricInputs` entry can never raise during `export_json`/CLI export. |
| `AR-F01` recovery diagnostic emission was unbounded in memory | `recover_stream` routes every diagnostic through a bounded `emit` collector that reserves one slot and appends a single `ARGUS2-BOUND-EXCEEDED` once `max_diagnostic_count` is reached. |
| `AR-F05` non-finite/non-JSON `annotation`/`extensions` escaped as a raw `ValueError`/`TypeError` | `_admission_snapshot` canonical-round-trips `annotation` and `extensions` at admission (`ARGUS2-INPUT-FIELD-INVALID`), and the event serialization is guarded so no raw serialization error escapes and no byte is written. |

### 2.2 Continuation repairs (revision 4)

The frozen independent review of the revision-3 candidate returned rework and produced no candidate. Two
residual `AR-F03`/`AR-F04` defects were repaired additively; they are proved by three new owned cases in
`tests/thesis_lite/argus/test_argus2_repair_unit.py` (renumbered 8 → 11 additive unit cases). No
inherited assertion, diagnostic, identifier, frozen unit record or measure record is changed.

| Residual gap | Continuation repair |
| --- | --- |
| `AR-F03` a manifest parsed with `json.loads` can carry `NaN`/`Infinity`/`-Infinity` (and an overflowing literal such as `1e400` parses to `inf`) at any depth; the reader previously carried it into assessment/export where an `allow_nan=False` serialization could raise. | `schema.find_nonfinite(value, max_reports=1)` performs a bounded, iterative (non-recursive) scan of the parsed manifest. `reader.read_run` rejects any non-finite value immediately after parsing and before the schema-version check, limits echo, assessment or export, returning one stable `ARGUS2-INPUT-NONFINITE` diagnostic with an assessed `incomplete` status while preserving the recorded manifest facts separately. |
| `AR-F04` `_publish` bounded `len(canonical_bytes(candidate))` but wrote `canonical_bytes(candidate) + b"\n"`, so the manifest could exceed `max_manifest_bytes` by the final newline; `open_run`'s preflight had the same off-by-one. | `writer._publish` and the `api.open_run` preflight both enforce `len(encoded) + 1 > max_manifest_bytes`, i.e. the exact serialized bytes that would be written including the single trailing newline, before any temporary file or run root is created. The four frozen publication-bound cases now size their limit from the actual on-disk byte count (still asserting the same refusal and prior-bytes-preserved behaviour); a new adversarial exact-limit case proves the boundary is exactly the newline-inclusive byte count. |

### 2.3 Continuation repairs (revision 5, `AR-RVW-001`)

The frozen independent review of the revision-4 candidate returned rework (finding `AR-RVW-001`) and
produced no candidate. A *small* JSON document nested deeply enough to exhaust the interpreter stack
raised an uncaught `RecursionError` at five boundaries: manifest parsing, event-line parsing, canonical
serialization, `EvidenceStore.open_run` obligations and `EvidenceRun.append_event` extensions (and the
same recursion risk reached `copy.deepcopy` of an admitted observation/snapshot). All five boundaries
are now guarded *additively* by an iterative, bounded nesting check; seven new owned cases in
`tests/thesis_lite/argus/test_argus2_repair_unit.py` prove the repair. No inherited assertion, diagnostic
code, identifier, frozen unit record or measure record is changed.

| Residual gap | Continuation repair |
| --- | --- |
| `AR-RVW-001` a small but deeply nested manifest or event line can exceed the recursive `json` decoder depth and raise an uncaught `RecursionError` (and a merely deep-but-parseable manifest can later crash the recursive encoder or `copy.deepcopy`). | `schema.MAX_JSON_NESTING` (128) is an internal defensive bound, not a caller `EvidenceLimits` field and not a scientific/safety threshold. `schema.json_text_depth_exceeded` scans raw JSON text *iteratively* (ignoring brackets inside strings) before decoding; `schema.parse_json_bounded` rejects an over-deep document with a bounded `ValueError` before `json.loads` and converts any residual `RecursionError`. `reader.read_run` maps that rejection to `ARGUS2-CORRUPT-MANIFEST-SHAPE` and `recovery.recover_stream` maps it to the existing `ARGUS2-CORRUPT-STREAM-TRUNCATED` line diagnostic, so neither boundary ever raises. |
| `AR-RVW-001` `schema.canonical_json` recursed on deeply nested values, so serialization (and every caller that relies on it) could raise an uncaught `RecursionError`. | `schema.json_depth_exceeded` checks the parsed value *iteratively* and `canonical_json` raises a bounded `ValueError` before `json.dumps` (converting a residual encoder `RecursionError` too). `api._admission_snapshot` and `writer._admission_snapshot` already catch `ValueError`, so both `open_run` obligations and `append_event` annotation/extensions now yield a stable `ARGUS2-INPUT-FIELD-INVALID` rejection and retain no caller reference. |
| `AR-RVW-001` `append_event` admitted a deeply nested observation/snapshot and then deep-copied it into the record before any bound could be applied. | `EvidenceRun._append` rejects any over-deep `clocks`/`annotation`/`extensions`/`observation`/`snapshot` argument iteratively with `ARGUS2-INPUT-FIELD-INVALID` *before* any validation, deep copy or serialization, so no byte is written and no recursion error escapes. The event-line canonicalization and final record serialization catch `RecursionError` defensively as well. |

### 2.4 Continuation repairs (revision 6, `AR-F03` enclosing depth)

The frozen independent review of the revision-5 candidate returned rework with two residual `AR-F03`
enclosing-depth failures and produced no candidate: a record/obligation admitted at the standalone parse
bound (`schema.MAX_JSON_NESTING`) can exceed that bound once an owned document wrapper encloses it, so
the *wrapped* serialization raised an uncaught `ValueError` (the same bounded `ValueError` that
`canonical_json` raises for an over-deep value). Both boundaries are now repaired additively and proved
by three new owned cases in `tests/thesis_lite/argus/test_argus2_repair_unit.py`. No inherited assertion,
diagnostic code, identifier, frozen unit record or measure record is changed; the revision-3/4/5
non-finite, exact-on-disk-size and deep-nesting repairs and their tests are preserved.

| Residual gap | Continuation repair |
| --- | --- |
| `AR-F03` an event record admitted at the standalone parse bound exceeds the bound once the read-only JSON export document wraps it (root object → `records` array → record); `EvidenceReader.export_json` and the CLI `export` then raised an uncaught `ValueError` after document wrapping. | `reader._EXPORT_WRAP_DEPTH` records the two enclosing levels. `read_run` flags any admitted record that exceeds `MAX_JSON_NESTING - 2` with one bounded `ARGUS2-BOUND-EXCEEDED` diagnostic and an assessed `incomplete` status; the admitted record stays in the trusted result (`records()`), but `export_json` withholds it from the wrapped document and reports the stable bounded diagnostic, so the primary export status is never `complete` and neither the JSON API nor the CLI `export` raises. |
| `AR-F03` an obligation admitted at the standalone parse bound exceeds the bound once the manifest preview encloses it (manifest object → `obligations` array → obligation) *and* once the full manifest is enclosed; `api.open_run`'s preview serialization and `writer._publish` raised an uncaught `ValueError`. | `api.open_run` serializes the preview under a bounded `try/except (ValueError, RecursionError)` and converts a nesting overflow into a stable bounded `ARGUS2-INPUT-FIELD-INVALID` `EvidenceError` before any run root is created; `writer._publish` applies the same bounded conversion before creating any temporary file, so the prior manifest bytes are preserved and no `closed`/`complete` persistence is claimed (also reinforcing `AR-F04`). |

### 2.5 Continuation repair (revision 7, `AR-F01` recorded event-stream path)

The rebased frozen review of the revision-6 snapshot returned rework for a residual `AR-F01` defect and
produced no candidate: the reader validated the manifest-recorded `eventStream.path` on its text but then
called `recover_stream`, which always opened the hardcoded `events.jsonl`. A manifest that recorded a
missing, different, symlinked or nested stream path was therefore read from the wrong file, and the
recorded size/SHA-256 were compared against that wrong file.

| Defect | Repair |
| --- | --- |
| `AR-F01` the reader and recovery did not confine and open the exact recorded `eventStream.path`; a missing/different/symlinked/nested recorded path either silently read `events.jsonl` or compared its recorded facts against the wrong file. | `recovery.recover_stream` takes the exact run-relative `relative` path (default `events.jsonl`), confines and `O_NOFOLLOW`-opens *that* file, names it in every diagnostic, and hashes/measures *that* file. `reader.read_run` passes the manifest-recorded `stream_relative` and threads the effective recorded path through the enclosing-depth diagnostic and the assessed-reason mapping; `EvidenceReader.export_json` names the recorded path too. The recorded `bytes`/`sha256` are compared only against the same confined file that was opened, so a wrong or corrupt recorded stream is assessed `incomplete` and is never exported as primary `complete`. |

Five additive adversarial cases in `test_argus2_repair_unit.py` prove the repair: a direct recovery
against a non-default relative path; a missing recorded path whose canonical `events.jsonl` is present
but never substituted; a wrong recorded path whose recorded facts describe a different file; an
in-root symlinked recorded path; and a valid nested recorded path that is read instead of the canonical
decoy. No inherited case, assertion, identifier or fixture was removed, renamed or weakened.

## 3. Source layout (new, additive)

| Path | Responsibility |
| --- | --- |
| `src/xverse/__init__.py` | Additive `xverse` package marker; imports nothing from `xcom` |
| `src/xverse/argus/__init__.py` | Public surface |
| `src/xverse/argus/api.py` | `EvidenceStore.open_run`/`read_run`, run admission, deep admission snapshots, bounded diagnostics |
| `src/xverse/argus/planbinding.py` | XDL digest reuse via the accepted `plan_matches_digest` public API |
| `src/xverse/argus/diagnostics.py` | Closed diagnostic catalogue and categories (including the repair-specific corrupt/container codes) |
| `src/xverse/argus/limits.py` | Frozen `EvidenceLimits` (11 positive integers) |
| `src/xverse/argus/schema.py` | Canonical JSON, versions, closed-field validation |
| `src/xverse/argus/clocks.py` | Explicit clock values; no inference, no cross-domain arithmetic |
| `src/xverse/argus/artifacts.py` | Confined run-relative artifact paths and reverification |
| `src/xverse/argus/causation.py` | Bounded causal index without invention |
| `src/xverse/argus/observation.py` | X-COM observation projection import and visibility invariants |
| `src/xverse/argus/snapshot.py` | Snapshot projection import and interval-closure rules |
| `src/xverse/argus/writer.py` | `EvidenceRun`, single publication chokepoint, obligation evaluation |
| `src/xverse/argus/reader.py` | Bounded, confined, assessed read-only reader and JSON/JSONL export |
| `src/xverse/argus/recovery.py` | Pre-I/O confined reads and bounded streaming recovery |
| `src/xverse/argus/cli.py` | Read-only `xverse-argus verify|export` entry point (assessed completeness) |
| `pyproject.toml` | Additive `xverse-argus` console script and wheel `force-include` for the Argus package only |

Owned tests and fixtures (additive): `tests/thesis_lite/argus/**` — 15 unit modules, one integration
module and one validation module, the neutral XDL fixtures compiled by the real accepted compiler, and
the owned C++20 producer fixture `tests/thesis_lite/argus/fixtures/argus2_owned_record_producer.cpp`.
The repair additively adds 33 unit cases and 5 adversarial validation cases; the revision-3
continuation adds 8 further additive unit cases in `test_argus2_repair_unit.py`, the revision-4
continuation adds 3 more there (non-finite manifest rejection and the newline-inclusive publication
bound), the revision-5 continuation adds 7 more there (bounded deep-nesting rejection at manifest,
event-line, canonical-serialization, obligation and extension/observation admission boundaries), and
the revision-6 continuation adds 3 more there (last-accepted/first-rejected enclosing-depth boundary
cases for JSON event export, CLI event export and obligation admission), and the revision-7 continuation
adds 5 more there (the exact recorded `eventStream.path`: non-default recovery, missing, wrong, in-root
symlink and nested recorded paths). No inherited case, assertion,
identifier or fixture was removed, renamed or weakened.

## 4. Frozen identifiers created

* 172 unit cases (`ARGUS2-UNIT`) — the 139 preserved cases plus 33 additive terminal-review repair
  cases, created verbatim as `tests/thesis_lite/argus/<module>.py::test_<case>`.
* 9 integration cases (`ARGUS2-INTEGRATION`) in `tests/thesis_lite/argus/test_argus2_integration.py`.
* 30 validation cases (`ARGUS2-VALIDATION`) — 25 preserved plus the 5 additive `ARGUS2-VS-08`
  adversarial cases.
* 18 static rules (`ARGUS2-STATIC`) — 12 base plus the 6 additive repair static checks
  (`ARGUS2-SR-001-U-STATIC-SNAPSHOT`, `ARGUS2-SR-002-U-STATIC-PUBLISH`,
  `ARGUS2-SR-005-U-STATIC-DIAGNOSTICS`, `ARGUS2-SR-006-U-STATIC-READBOUND`,
  `ARGUS2-SR-007-U-STATIC-CONFINE`, `ARGUS2-SR-010-U-STATIC-CONFINE`); the static measure parses all
  candidate `src` Python plus the owned tests without writes.
* The revision-3 continuation adds 8 further owned unit cases (219 owned tests total) that prove the
  residual `AR-F01`/`AR-F03`/`AR-F05` repairs, the revision-4 continuation adds 3 more (222 owned tests)
  for non-finite manifest rejection and the newline-inclusive publication bound, the revision-5
  continuation adds 7 more (229 owned tests) for bounded deep-nesting rejection, the revision-6
  continuation adds 3 more (232 owned tests) for the `AR-F03` enclosing-depth boundary at JSON event
  export, CLI event export and obligation admission, and the revision-7 continuation adds 5 more (237
  owned tests) for the exact recorded `eventStream.path` (non-default, missing, wrong, in-root symlink
  and nested recorded paths). They are additive adversarial cases only; the four
  frozen measure records are unchanged, every declared identifier (172 unit, 9 integration, 30
  validation, 18 static) is still produced, and no declared identifier was renamed or dropped.

## 5. Local worker execution (candidate-local, not trusted evidence)

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/thesis_lite/argus` | 237 passed |
| `python3 -m pytest -q tests/thesis_lite/argus/test_argus2_integration.py` | 9 passed |
| `python3 -m pytest -q tests/thesis_lite/argus/test_argus2_validation.py` | 30 passed |
| `python3 -m pytest -q tests/thesis_lite/argus/test_argus2_repair_unit.py` | 26 passed |
| `python3 -m pytest -q tests` (platform regression) | 532 passed |
| installed-wheel consumer path (owned `test_argus2_consumer_unit.py`: wheel built/installed offline, `xverse.argus`/`xverse_xdl` imported outside the source tree, owned unit tests repeated against the wheel) | passed (part of the 237 owned cases) |
| `pytest --collect-only -q tests/thesis_lite/argus` against the four frozen measure records | all 211 declared identifiers (172 + 9 + 30) collected, 0 missing |
| static AST parse of every `src/**/*.py` and `tests/thesis_lite/argus/**/*.py` | `STATIC_CHECK_PASSED` |

Real interoperability is exercised, not simulated: the accepted XDL compiler compiles the owned
neutral fixtures, and the owned C++20 fixture is compiled with `g++ -std=c++20` against the accepted
`src/xverse/xcom/include/xverse/xcom/observation.hpp` and the accepted `observation.cpp`/`item.cpp`/
`contract.cpp`/`value.cpp`/`diagnostic.cpp` translation units under `/tmp`, then drives an in-process
`ObservationHub` (`attach → reserve → commit → poll/snapshot`) to produce owned records and a
degraded interval. No accepted C++ header, source, schema, CLI, test or historical record was
changed. The built wheel resolves `xverse.argus` and `xverse_xdl` outside the source tree with a
`PYTHONPATH` set only to the installed target, and the owned Argus tests repeat against that wheel.

## 6. Trace endpoints

`engineering/trace/links.json` retains its 92 `implemented_by` links (`ARGUS2-L-801` …
`ARGUS2-L-892`) that bind each accepted `ARGUS2-SR-*` requirement, its allocation component and its
unit record to the exact implementation file and the exact SHA-256 of the candidate revision. The
revision-5 continuation refreshed the `target_revision` of the 27 code endpoints (`schema.py` 6,
`api.py` 6, `reader.py` 6, `writer.py` 6, `recovery.py` 3); this revision-6 continuation refreshed the
`target_revision` of the 18 affected code endpoints (`api.py` 6, `reader.py` 6, `writer.py` 6) to the
exact current hash; this revision-7 continuation refreshed the `target_revision` of the 9 affected code
endpoints (`recovery.py` 3, `reader.py` 6) to the exact current hash. All 3595 link objects, all endpoint
revisions of the other relations, and the
additive design-stage relations are preserved in order and content.

## 7. Limitations and boundaries

* Local worker checks are not trusted measure evidence; the trusted host re-runs the exact sealed
  candidate and assembles it over the pinned platform revision.
* The bounded durability claim is a local filesystem guarantee (`flush`/`fsync`/atomic rename on the
  local run root). It is **not** a power-loss, hardware, distributed or network-filesystem guarantee.
* Argus performs no execution, control, actuation, provider delivery, metric computation, dashboard,
  oracle, network access or live tap attachment; replay is evidence reconstruction only.
* Successful finalization means only that the caller-declared capture obligations and integrity
  checks were satisfied. It never proves scientific validity, safety, compatibility, parity or
  readiness.
* The reader's assessed completeness is a bounded verification conclusion over readable evidence; an
  unreadable or structurally invalid container is reported incomplete rather than repaired.
* No REF-002 parent disposition is promoted or closed; no new system requirement ID is created.
* Inherited limitation: the admitted planning bundle names a required launch-evidence
  `admission/review.md` that is not an admitted input for this run; it remains an external, unverified
  later-gate input and is neither fabricated nor substituted.

## 8. Model and next step

The pinned `deepseek-v4-flash` with **high** reasoning was the authorized route for this bounded
transcription and local-test work; no model switch occurred, no subagent was used, and no benchmark or
exact-cost claim is made. Escalation would be justified only by a measured, reproducible failure this
route cannot resolve.

Next stage: **integration** — write `integration.md` and the stage record, run the real XDL compiler →
writer → owned C++ projection importer → finalize/reader/export path, and confirm the owned tests run
against the installed wheel with no source-tree `sys.path` entry. Blockers: none; the trusted host
must bind and execute the four ARGUS2 measures against the sealed candidate.
