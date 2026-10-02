# Argus Lite Phase 2 Detailed Design — frozen evidence, projection and API contracts

## 1. Document control

| Field | Value |
| --- | --- |
| Feature | ARGUS2 (Argus Lite Phase 2) |
| Stage / role | architecture (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 1 |
| Revision basis | Revision 1 incorporates the terminal-review rework of findings `AR-F01`–`AR-F05` (verdict `rework`); the rejected candidate was never accepted, so no accepted revision is superseded. The frozen adversarial registry `ARGUS2-ADV-01`–`ARGUS2-ADV-07` is fixed before code. |
| Date | 2026-10-02 (rework of the 2026-10-01 revision) |
| Admitted platform baseline revision | `c1fd213cd00259b74f8308d8ca58157ea985aaa0` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Maturity | **Planned / target — design only.** Every identifier, field, value and step below is a contract to be implemented, not implementation evidence. |

This document freezes the versioned evidence schemas, the public Python API and CLI, XDL digest reuse,
the single-writer state and durability steps, the caller bounds, confined-artifact rules, incomplete
classification, clock/causation representation, payload/loss/snapshot mapping, read-only replay/export,
metric-input links and the additive packaging. Any later change to a frozen item requires a reviewed
successor candidate, not a silent implementation change. No code is written by this stage.

## 2. Frozen identities and versions

| Identity | Frozen value |
| --- | --- |
| Python package | `xverse.argus` (distribution `xverse-xdl`, unchanged name) |
| Additive console entry point | `xverse-argus = "xverse.argus.cli:main"` (new; `xdl` unchanged) |
| Event record schema | `eventSchemaVersion = "1.0"` |
| Manifest schema | `manifestVersion = "1.0"` |
| Observation projection schema | `projectionVersion = "1.0"`; upstream `upstreamContractVersion = "1.0.0"` |
| Snapshot projection schema | `snapshotVersion = "1.0"` |
| Task/generator token | `ARGUS2` |
| Package version token | `0.1.0` (reported as `argusVersion`, distinct from `xverse-xdl`) |

Version-parsing rule (applies to `eventSchemaVersion`, `manifestVersion`, `projectionVersion`,
`snapshotVersion`): the value must be a string `<major>.<minor>` with decimal integers. An unknown
`major` (not `1`) is rejected with `ARGUS2-SCHEMA-MAJOR-UNSUPPORTED`. A `major` of `1` with any
`minor` is accepted because additive minor evolution only relaxes nothing; unknown **fields** are
handled by §3.5, never silently ignored.

## 3. Event record schema (evidence stream, JSONL, frozen v1.0)

The evidence stream is append-only JSONL: exactly one JSON object per line, each line terminated by a
single `\n`, UTF-8 without BOM, no blank lines, no trailing content after the final newline. Keys are
emitted with `sort_keys=True` and compact separators `(",", ":")`; `allow_nan=False`. The writer assigns
`ingestionOrdinal`.

### 3.1 Fields

| Field | Type | Required | Frozen rule |
| --- | --- | --- | --- |
| `schemaVersion` | string | yes | `"1.0"` (§2). |
| `runId` | string | yes | Equals the run identity supplied at open; pattern `^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$`. |
| `eventId` | string | yes | Caller-supplied, unique within the run; pattern `^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$`. |
| `producerId` | string | yes | Caller-supplied producer identity; pattern as `eventId`, non-empty. |
| `ingestionOrdinal` | integer | yes | Writer-assigned; strictly increasing from `1` in append order; never presented as temporal or causal order. |
| `eventKind` | string | yes | Closed set `run-opened`, `run-closed`, `run-failed`, `observation`, `snapshot`, `annotation`. |
| `producerSequence` | integer \| absent | no | Present only when the producer declares one; non-negative; preserved exactly. Never used for ordering. |
| `correlationId` | string \| absent | no | Explicit reference, preserved exactly. |
| `causationId` | string \| absent | no | Explicit reference, preserved exactly. |
| `clocks` | object \| absent | conditional | Required for `observation`/`snapshot` events; explicit per §6. Absent means "not declared", never inferred. |
| `observation` | object \| absent | conditional | Exactly one of `observation`/`snapshot` for those kinds; frozen projection in §5. |
| `snapshot` | object \| absent | conditional | Frozen snapshot projection in §5.4. |
| `annotation` | object \| absent | no | Free-form caller note `{"text": <string ≤ max_text_length>}`; no semantics are inferred. |
| `extensions` | object \| absent | no | Additive namespace map per §3.5. |

### 3.2 Kind-specific requirements

* `run-opened`, `run-closed`, `run-failed` are writer-emitted, carry no `observation`/`snapshot`, and are
  the only kinds the caller may not append directly.
* An `observation` kind requires `observation` and `observationContract` provenance; a `snapshot` kind
  requires `snapshot`.
* An event that fails any rule is rejected with a categorized diagnostic and **no** JSONL line is
  written; the writer's state and stream bytes are unchanged by a rejected append.

### 3.3 Encoding of payload bytes

Visible payload bytes are carried as lowercase hexadecimal text in `observation.payload.visibleBytesHex`
with an explicit `visibleByteCount`; the encoding is fixed (no base64) so the byte length is
unambiguous and the projection is text-only. `sourcePayloadSize` is the complete source byte count
even when content is withheld.

### 3.4 Null, empty and absence

`null` is never a valid substitute for an absent optional field: an optional field is either present
with a valid value or absent from the object. `[]`/`{}` are valid only where a collection is declared.
"Unavailable" is represented in the projection schema (§5) by an explicit
`{"available": false, "reason": <code>}` marker, never by a fabricated value.

### 3.5 Additive unknown-field rule (explicit, not silent)

Within a frozen record object every key is closed: an unknown top-level or nested key (outside
`extensions`) is rejected with `ARGUS2-SCHEMA-UNKNOWN-FIELD`. Forward-compatible additive data must be
placed in the record's `extensions` object as `{ "<namespace>": <JSON value> }` where `<namespace>`
matches `^[a-z][a-z0-9._-]{0,63}$`. Unknown `extensions` namespaces are **preserved verbatim** on append
and echoed verbatim on read/export, but are never interpreted, validated beyond JSON-encodability, or
allowed to affect status, ordering or obligations. This makes additive behaviour explicit rather than
silently accepted or silently discarded.

## 4. Manifest schema (atomic JSON, frozen v1.0)

The manifest is a single JSON object written by temporary-file + `flush` + `fsync` + atomic rename inside
the run root. It is replaced on open, on finalize and (best-effort) on failure. It is never appended.

| Field | Type | Frozen rule |
| --- | --- | --- |
| `schemaVersion` | string | `"1.0"`. |
| `manifestVersion` | string | `"1.0"`. |
| `runId` | string | The run identity. |
| `plan` | object | `{"apiVersion", "profileVersion", "planVersion", "semanticDigest": {"algorithm":"sha256","value":<hex>}}` — the verified accepted plan identity (§7). |
| `sourceByteProvenance` | object | Map of caller-declared source name → `{"algorithm":"sha256","value":<hex>}`; kept strictly separate from `plan.semanticDigest`. |
| `writerState` | string | Closed set `open`, `closed`, `failed`. |
| `openedAt` | object \| absent | Caller-declared clock value (§6) or absent; never an ambient wall clock. |
| `finalizedAt` | object \| absent | Caller-declared clock value or absent. |
| `eventCount` | integer | Number of accepted JSONL event lines at publication time. |
| `eventStream` | object | `{"path":"events.jsonl","mediaType":"application/x-ndjson","schemaVersion":"1.0","bytes":<int>,"sha256":<hex>}`. |
| `artifacts` | array | Frozen artifact index (§4.1), each entry unique by `path`. |
| `obligations` | array | Caller-declared obligations (§4.2), each unique by `obligationId`. |
| `evidenceStatus` | string | Closed set `unassessed`, `complete`, `incomplete`. |
| `evidenceReasons` | array of string | Closed reason codes (§4.3); empty iff `evidenceStatus == "complete"`. |
| `limits` | object | Echo of the effective caller limits (§10) so the reader verifies under the same bounds. |
| `extensions` | object \| absent | Additive namespace map per §3.5. |

### 4.1 Artifact index entry

`{"path": <run-relative POSIX path>, "mediaType": <string>, "schemaVersion": <string>, "bytes": <int>,
"sha256": <hex>, "role": <string>}`. The reader verifies `bytes` and `sha256` against the confined file
and rejects a mismatch with `ARGUS2-CORRUPT-ARTIFACT-HASH` / `ARGUS2-CORRUPT-ARTIFACT-SIZE`; a missing
file yields `ARGUS2-MISSING-ARTIFACT`.

### 4.2 Obligations

`{"obligationId": <string>, "kind": <closed kind>, "required": <bool>, "detail": <object|absent>}`.
Closed kinds and their deterministic evaluation (no inference, no defaults):

| Kind | Satisfied iff |
| --- | --- |
| `causal-closure` | Every `causationId`/`correlationId` referenced by an accepted event resolves to an accepted event in the same run. |
| `interval-closure` | Every imported snapshot declares `intervalProvenance.closure == "closed"`. |
| `no-known-loss` | No accepted observation carries `observation.counters.dropped > 0` or `coalesced > 0`, and no imported snapshot declares `dropped > 0`, `coalesced > 0`, `validityState != "valid"` or `experimentValidityDegraded == true`. |
| `min-observations` | `eventCount`-based count of accepted `observation` events ≥ `detail.minimum`. |

Only these four kinds exist. A `required` obligation that is not satisfied forces
`evidenceStatus = "incomplete"` with reason `ARGUS2-REASON-UNMET-OBLIGATION`; an unsatisfied
non-required obligation is recorded as a finding but does not by itself force incompleteness.

### 4.3 Closed evidence reason codes

`ARGUS2-REASON-TRUNCATED-STREAM`, `ARGUS2-REASON-MISSING-ARTIFACT`, `ARGUS2-REASON-MUTATED-ARTIFACT`,
`ARGUS2-REASON-UNMET-OBLIGATION`, `ARGUS2-REASON-KNOWN-LOSS`, `ARGUS2-REASON-DEGRADED-INTERVAL`,
`ARGUS2-REASON-INVALID-INTERVAL`, `ARGUS2-REASON-UNRESOLVED-CAUSATION`,
`ARGUS2-REASON-UNCLOSED-INTERVAL`, `ARGUS2-REASON-UNSUPPORTED-SCHEMA`, `ARGUS2-REASON-WRITER-STATE`,
`ARGUS2-REASON-CORRUPT-MANIFEST`, `ARGUS2-REASON-CORRUPT-EVENT` (the last two are assigned only to the
reader's *assessed* reasons, §11.1; they are never written into a manifest by the writer).

### 4.4 Manifest publication byte bound at every publication (`AR-F04`, `ARGUS2-ADV-06`)

Manifest content grows after the open manifest is published: the artifact index, declared obligations,
`finalizedAt`, the closed `evidenceStatus`/`evidenceReasons` and the recomputed stream identity all
appear only at finalize/abort. The bound therefore cannot be enforced only on the open publication.

**Frozen rule.** There is exactly one publication chokepoint, `_publish(candidate)`, and it enforces the
bound itself:

1. Serialize the complete candidate manifest with the canonical encoder and measure
   `byte_length = len(canonical_bytes(candidate))`.
2. If `byte_length > limits.max_manifest_bytes` (or, when comparing the on-disk form, the encoded form
   including its single trailing `\n`), raise `ARGUS2-BOUND-EXCEEDED` naming `max_manifest_bytes`.
   **No temporary file is created and no `os.replace` occurs**, so the prior manifest bytes remain
   exactly as they were.
3. Otherwise write the temporary file, `flush`, `os.fsync`, `os.replace` atomically, then `fsync` the
   run-root directory (best-effort). An `OSError` raises `ARGUS2-IO-FAILURE`; the prior manifest bytes
   again remain, because the replace did not complete.
4. Open, finalize-success, finalize-failure and abort all publish through this one chokepoint, so
   growth from artifacts, obligations or finalized metadata is always measured.

**State/honesty rule.** A publication that fails the bound or I/O leaves the writer's state and the
on-disk manifest unchanged. The writer must not report `closed` or `complete`, must not append a
`run-closed` event that claims success for a failed finalize publication, and must surface the stable
diagnostic to the caller. If a caller retries finalize, the same actual-byte check applies again (no
cached or previously computed size is trusted).

## 5. Observation and snapshot projection (frozen v1.0)

The projection maps the owned C++ `ObservationRecord` accessors (`observation.hpp`, contract
`1.0.0`) by value. It is produced by a real owned producer fixture that serializes these values; no
callback, hub handle, provider handle or delivery authority enters Argus.

### 5.1 Projection envelope

```json
{
  "projectionVersion": "1.0",
  "upstreamContractVersion": "1.0.0",
  "exporter": {"task": "<string>", "toolVersion": "<string>", "provenance": {"available": true, "note": "<string>"}},
  "records": [ <observation projection>, ... ]
}
```

### 5.2 Observation projection field mapping

| Owned C++ accessor | Projection field | Rule |
| --- | --- | --- |
| `contract_id()` | `contractId` | Identity text, preserved exactly. |
| `contract_version()` | `contractVersion` | Canonical `major.minor.patch`. |
| `interface_id()` / `endpoint_id()` | `interfaceId` / `endpointId` | Preserved exactly. |
| `schema_id()` / `schema_version()` | `schemaId` / `schemaVersion` | Preserved exactly. |
| `interaction_kind()` | `interactionKind` | Closed set `signal_state_update`, `message_event`, `service_request`, `service_response`. |
| `origin()` | `origin` | Closed set `component`, `validation_tool`, `replay`, `provider_generated`. |
| `source_timestamp()` / `source_clock_domain()` | `sourceClock` | Clock value object (§6) with `nanoseconds` and the domain identity. |
| `observation_timestamp()` / `observation_clock_domain()` | `observationClock` | Clock value object (§6). |
| `sequence()` | `sequence` | Present (non-negative integer) only when declared; otherwise absent. |
| `correlation_id()` / `causation_id()` | `correlationId` / `causationId` | Preserved exactly; used only for explicit causal references. |
| `route_id()` / `provider_id()` | `routeId` / `providerId` | Preserved exactly. |
| `source_payload_size()` | `sourcePayloadSize` | Integer ≥ 0; the complete source size even when bytes are withheld. |
| `provider_outcome()` | `providerOutcome` | Closed set `not_attempted`, `accepted`, `rejected`; never promoted to an experiment-validity claim. |
| `payload_view_state()` | `payloadViewState` | Closed set `omitted`, `complete`, `truncated`, `redacted`. |
| `payload_schema_state()` | `payloadSchemaState` | `undecoded` (this slice never claims decoder success). |
| `payload_bytes()` | `visibleBytesHex` + `visibleByteCount` | Lowercase hex of the visible bytes; `visibleByteCount == sourcePayloadSize` iff `complete`; empty for `omitted`/`redacted`. |
| `tap_id()` | `tapId` | Declared producing-tap identity, preserved exactly. |
| `counters()` | `counters` | `{"queued","accepted","dropped","coalesced"}`; retention-time projection only (§8). |

### 5.3 Visibility invariants (fail-closed)

* `payloadViewState == "omitted"` or `"redacted"` ⇒ `visibleByteCount == 0` and `visibleBytesHex == ""`.
* `payloadViewState == "complete"` ⇒ `visibleByteCount == sourcePayloadSize`.
* `payloadViewState == "truncated"` ⇒ `0 < visibleByteCount < sourcePayloadSize`.
* `payloadSchemaState == "undecoded"` always; any other value is rejected with
  `ARGUS2-SCHEMA-UNKNOWN-FIELD`-class rejection.
* A projection whose encoded visible bytes decode to a byte count other than `visibleByteCount` is
  rejected (`ARGUS2-INPUT-PAYLOAD-LENGTH`); bytes are never synthesized or padded.

### 5.4 Snapshot projection

```json
{
  "snapshotVersion": "1.0",
  "handle": {"hubInstanceId": <int>, "tapId": <int>, "generation": <int>},
  "queued": <int>, "accepted": <int>, "dropped": <int>, "coalesced": <int>,
  "backpressureRejections": <int>,
  "experimentValidityDegraded": <bool>,
  "declaredTapId": "<string>",
  "validityEffect": "none|degrade_on_loss|invalidate_on_loss",
  "validityState": "valid|degraded|invalid",
  "intervalProvenance": {
    "streamId": "<string>",
    "intervalId": "<string>",
    "closure": "closed|unclosed|unavailable",
    "start": <clock value|absent>,
    "end": <clock value|absent>,
    "provenance": "<string>"
  }
}
```

The owned C++ `ObservationSnapshot` carries no interval window; `intervalProvenance` is therefore
**caller-supplied** metadata imported with the snapshot, never inferred from the counters. A snapshot
whose `closure` is `closed` but with `start`/`end` absent is rejected
(`ARGUS2-INPUT-INTERVAL-INCOMPLETE`); an `unclosed`/`unavailable` closure is accepted and recorded as
an unresolved interval, forcing the relevant obligation (and any dependent status) to remain
incomplete.

## 6. Clock representation and causation

A clock value is `{"domain": <string ≤ max_text_length>, "unit": <string ≤ max_text_length>,
"value": <finite JSON number>}`. Rules:

* `domain` and `unit` are caller-supplied and preserved verbatim; `unit` has no closed vocabulary (the
  caller declares representation), and no unit is inferred.
* `value` must be finite (`allow_nan=False`); a non-finite or missing value is rejected with
  `ARGUS2-INPUT-NONFINITE` / `ARGUS2-INPUT-CLOCK-MISSING`.
* For observation projections the projected nanosecond magnitude is emitted as an integer-valued
  `value` with the caller-declared `unit`; Argus never rescales between source and observation domains.
* Argus performs **no** cross-clock-domain comparison, subtraction, sorting or conversion. The
  ingestion ordinal, producer sequence and any causal reference are recorded as declared; a causal link
  is explicit evidence, not proof of synchronisation.
* Causation index: `causationId`/`correlationId` targets are indexed by `eventId`; an unresolved target
  remains visible and is reported as `ARGUS2-REASON-UNRESOLVED-CAUSATION`, never repaired or invented.

## 7. XDL digest reuse and plan binding

Argus does not reimplement or reparse plan identity. It imports the accepted public API:

* `xverse_xdl.experiment_plan.plan_matches_digest(plan)` must return `True` for the supplied resolved
  plan (`compute_plan_digest` is the accepted body-digest function; the API and Profile versions are
  `xverse.io/xdl/v1alpha1` and `io.xverse.experiment`, plan version `"1"`).
* The manifest `plan.semanticDigest` is the accepted `plan["digest"]` value; `plan.apiVersion`,
  `plan.profileVersion` (Profile metadata version) and `plan.planVersion` are recorded from the plan.
* `sourceByteProvenance` is a separate map of caller-declared source names to SHA-256 digests (from the
  accepted loader/compiler envelope `sourceByteDigests` when available) and is **never** used as the
  plan identity.
* Rejections: digest mismatch → `ARGUS2-PLAN-DIGEST-MISMATCH`; unsupported API/Profile/plan major →
  `ARGUS2-PLAN-VERSION-UNSUPPORTED`; envelope `runId` differing from the declared run identity →
  `ARGUS2-PLAN-ENVELOPE-CONFLICT`; existing run root → `ARGUS2-STATE-RUN-EXISTS`. No run is opened and
  nothing is overwritten on any rejection.

## 8. Single-writer state, durability and recovery

### 8.1 State machine

`new → open → closed`, or `open → failed`. `new` is the pre-open state; `open` is published in the
manifest as soon as the run root exists; `closed` is published only by a completed finalize; `failed` is
published by an aborted or interrupted finalize. Any transition other than these is rejected with
`ARGUS2-STATE-ILLEGAL-TRANSITION`.

### 8.2 Exclusivity and reuse

One owning writer per run. The run root is created with exclusive semantics (`os.mkdir`, or `os.open`
with `O_CREAT|O_EXCL` for the run-root marker) and an already-existing run root is rejected
(`ARGUS2-STATE-RUN-EXISTS`) before any file is created or overwritten. A second in-process writer for
the same run root is rejected (`ARGUS2-STATE-WRITER-CONFLICT`). Reopen for writing is refused; the reader
opens evidence read-only.

### 8.3 Documented durability steps

1. **Open:** create run root exclusively; write `manifest.json` to `manifest.json.tmp-<n>`, `flush`,
   `os.fsync`, then `os.replace(tmp, manifest.json)`; `os.fsync` the run-root directory.
2. **Append:** serialize the event canonically, write one line to the open `events.jsonl` handle, then
   `flush`. `flush_buffer()` performs `flush` + `os.fsync` explicitly and is the only durability point
   for appended lines; `finalize()` calls it before hashing.
3. **Finalize:** `flush_buffer()`; recompute `eventCount`/`bytes`/`sha256`; verify every artifact; write
   the closed manifest via the same temp+fsync+replace+dir-fsync sequence; publish `evidenceStatus`.
4. **Failure/abort:** best-effort `run-failed` append (skipped if the stream is unusable) and a `failed`
   manifest via the same atomic sequence; a failure during finalize leaves the prior open manifest bytes
   unless the atomic replace completed.

**Claim scope:** this is a bounded local filesystem guarantee (flush/fsync/atomic-rename on the local
run root). It is **not** a power-loss, hardware, distributed, or network-filesystem guarantee; no such
claim is made or verified.

### 8.4 Partial writes and non-mutating recovery

Recovery reads a bounded prefix and never writes. A final line without a terminating `\n`, or a line
that is not valid canonical JSON, is a truncated record and is reported as
`ARGUS2-CORRUPT-STREAM-TRUNCATED`; accepted bytes are never rewritten, upgraded or deleted, and the
original run root files are left byte-identical after recovery. A truncated record is never counted as
an accepted event, and its apparent content is never repaired.

### 8.5 Pre-I/O confinement and bounded streaming reads (`AR-F01`, `ARGUS2-ADV-01`, `ARGUS2-ADV-02`)

Confined-path checks and bounds are enforced **before** bytes are consumed; recovering a bounded
prefix must never require loading an unbounded file.

**Pre-I/O path checks (before any open/parse).** For each of `manifest.json`, the `eventStream.path`
and every indexed artifact path, the reader:

1. Rejects an absolute path, a `\`, a NUL, a drive-like prefix, an empty/`.`/`..` segment and any
   non-matching name (`ARGUS2-PATH-ESCAPE`) — validated on the **recorded text**, never on a
   caller-supplied string.
2. Computes the confined real path from the resolved run-root and applies `os.lstat` to the parent and
   the final component **before** opening. A symlink anywhere on the confined path (including one that
   resolves inside the run root) is rejected with `ARGUS2-PATH-SYMLINK`; a non-regular file (directory,
   FIFO, device, socket) is rejected with `ARGUS2-PATH-NOT-REGULAR`; a path resolving outside the run
   root is rejected with `ARGUS2-PATH-ESCAPE`.
3. Opens the confined regular file with `os.open(..., O_RDONLY | O_NOFOLLOW)` and keeps the
   `os.fstat` result; if the opened descriptor is not a regular file or its device/inode differs from
   the `lstat` result, the read is rejected (`ARGUS2-PATH-NOT-REGULAR`), defeating a TOCTOU swap.

**Bounded reads before parsing.**

* The manifest is read through a capped reader that accepts at most `limits.max_manifest_bytes` bytes;
  reaching the cap without EOF is `ARGUS2-BOUND-EXCEEDED` naming `max_manifest_bytes`, and the partial
  bytes are **not** parsed.
* The stream is read line-by-line through the same descriptor without materializing the whole file. A
  line longer than `limits.max_event_bytes` is `ARGUS2-BOUND-EXCEEDED` naming `max_event_bytes`; a
  stream whose byte length exceeds `max_events * max_event_bytes` (the derived total stream bound) is
  `ARGUS2-BOUND-EXCEEDED` naming `max_events`; the number of accepted records is capped by
  `max_read_records`.
* Streamed bytes are hashed incrementally so `eventStream.bytes`/`sha256` can still be compared, but
  the hash comparison is only attempted after the confined regular-file checks succeed.
* Diagnostics are capped by `limits.max_diagnostic_count`; reaching the cap stops further emission and
  records a single bounded `ARGUS2-BOUND-EXCEEDED` naming `max_diagnostic_count`, so damaged input
  cannot amplify diagnostics without limit.
* `recovery.read_bytes` (and any equivalent helper) takes an explicit `max_bytes` and a `NOFOLLOW`
  descriptor; there is no unbounded `read_bytes()`/`read()` on manifest or stream paths anywhere in the
  read or recovery path. The writer's own finalize/abort stream read uses the same bounded helper.

**Limits authority.** The `limits` value passed to the read operation is authoritative. The manifest
`limits` echo is recorded data only: it may be parsed and recorded, but it must never relax a caller
bound, and an unparseable or oversized echo is a diagnostic, not a new limit set. If both are used, the
effective bound is the stricter of the two.

## 9. Confined artifact paths

* Artifact paths are run-relative POSIX paths: must be non-empty, not absolute, contain no `\`, no NUL,
  no empty/`.`/`..` segment, and match `^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$`.
* The confined path is computed from the run-root real path plus the relative path; the parent and the
  final component are verified with `os.lstat` (not the caller's text). A symlink (including one that
  resolves inside the run root) is rejected (`ARGUS2-PATH-SYMLINK`); a path that resolves outside the
  run root is rejected (`ARGUS2-PATH-ESCAPE`); a non-regular file is rejected
  (`ARGUS2-PATH-NOT-REGULAR`).
* Writes are performed only through the confined path; no write outside the run root is possible by
  design, and the implementation must reject rather than follow an escaping path.

## 10. Caller-configured finite bounds

`EvidenceLimits` (frozen dataclass; every field a positive integer, caller-supplied, echoed into the
manifest as *recorded* data so a reader may cross-check, while the caller-supplied `limits` argument
remains authoritative — §8.5):

| Field | Meaning |
| --- | --- |
| `max_event_bytes` | Maximum canonical bytes of one JSONL event line. |
| `max_events` | Maximum accepted events per run. |
| `max_id_length` | Maximum length of `runId`/`eventId`/`producerId`/identities. |
| `max_text_length` | Maximum length of clock domains/units and annotation text. |
| `max_payload_bytes` | Maximum visible payload bytes stored per observation. |
| `max_artifacts` | Maximum entries in the artifact index. |
| `max_obligations` | Maximum declared obligations. |
| `max_diagnostic_count` | Maximum diagnostics returned/retained per operation. |
| `max_manifest_bytes` | Maximum canonical bytes of the manifest. |
| `max_causal_index_entries` | Maximum causal-index entries. |
| `max_read_records` | Maximum records returned by one bounded read/export. |

Any exceeded bound rejects with `ARGUS2-BOUND-EXCEEDED` naming the field; no diagnostic is produced
without an actual violation. Bounds are implementation limits, **not** scientific, safety or performance
thresholds. Every field must have at least one independent negative case (frozen by the
verification-design stage). Additional derived limits are frozen here: the stream may not exceed
`max_events * max_event_bytes` and `max_manifest_bytes` is measured on the actual serialized manifest at
**every** publication (§4.4). No bound is ever sourced from a damaged input's echoed `limits`.

## 11. Incomplete classification

`evidenceStatus` is independent of `writerState`:

* While `writerState == "open"`, `evidenceStatus == "unassessed"`.
* On finalize, `evidenceStatus == "complete"` **iff** `writerState == "closed"`, the stream parses with
  no truncated line, every indexed artifact verifies, every `required` obligation is satisfied, and
  `evidenceReasons` would be empty.
* Otherwise `evidenceStatus == "incomplete"` with the applicable closed reasons from §4.3. Known loss,
  degraded/invalid intervals, unresolved causation and unclosed/unavailable interval closure remain
  visible and can never be upgraded to `complete` by finalization alone. A closed manifest with an
  unknown/absent status field is treated as `incomplete` (`ARGUS2-REASON-WRITER-STATE`).

### 11.1 Reader-assessed status vs recorded manifest facts (`AR-F02`, `ARGUS2-ADV-03`)

A manifest is itself untrusted input: a damaged or partially written manifest can claim a status that
the bytes do not support. The reader therefore computes and exposes two separate facts.

* **Recorded facts** — `recordedEvidenceStatus` and `recordedEvidenceReasons` are the manifest's
  `evidenceStatus`/`evidenceReasons` echoed verbatim, labelled as recorded, plus the recorded
  `writerState`. They are never presented as the reader's own conclusion.
* **Assessed facts** — `assessedEvidenceStatus` and `assessedEvidenceReasons` are computed by the reader
  from what it actually verified: manifest shape and version, confined path/type checks, bounded stream
  parse, per-event full-schema/identity/ordinal/finiteness checks, event-stream byte/hash agreement,
  artifact size/hash verification and re-evaluation of the declared obligations where the required
  inputs were readable.
* The reader's assessed status is `complete` **iff** every one of those checks succeeded and no
  obligation evaluated as unmet. Any detected corruption, truncation, blank/non-canonical line,
  missing/mutated artifact, unsupported schema major, malformed shape, run-ID mismatch, duplicate or
  non-monotonic record, or required-input-unreadable obligation forces `assessedEvidenceStatus =
  "incomplete"` with the applicable closed reasons, including `ARGUS2-REASON-CORRUPT-MANIFEST` /
  `ARGUS2-REASON-CORRUPT-EVENT` where a container or record is structurally invalid.
* Exported/reported completeness is the **assessed** value as the primary status; the recorded value is
  carried alongside in a clearly named field. A reader must never emit primary `complete`, or a
  `verify` exit code of `0`, when `assessedEvidenceStatus != "complete"` — including when the manifest
  recorded `complete` but verification failed.
* If the manifest cannot be read or parsed at all, the reader returns an assessed `incomplete` result
  with no records and a bounded stable diagnostic; it never synthesizes a manifest, never rewrites the
  original and never falls back to recorded claims.

## 12. Read-only replay and export

* `read_evidence(root, *, limits)` opens the run read-only, validates the manifest, verifies the event
  stream hash/size and every artifact, and returns records **in `ingestionOrdinal` order**, followed by
  diagnostics and declared metric-input links.
* `export_json()` emits one canonical JSON document; `export_jsonl()` emits the event records as
  canonical JSONL. Repeated reads of unchanged inputs produce byte-equal output.
* A corrupt artifact, a hash/size mismatch, or an exceeded reader bound yields a stable categorized
  diagnostic plus a bounded partial result (records read so far, bounded by `max_read_records`); it
  never silently truncates, never invents data and never writes to the run.
* Replay is evidence reconstruction only: it invokes no component, fault, lifecycle action, metric
  computation or evaluation oracle, and produces no control or actuation output.

### 12.1 Strict reader schema, identity and ordinal validation (`AR-F03`, `ARGUS2-ADV-04`, `ARGUS2-ADV-05`)

Reading re-applies the **complete** frozen schema, not a subset, and never performs an unchecked
operation on attacker-controlled structure.

* **Container shapes.** The manifest must be a JSON object and the `artifacts`, `obligations`,
  `metricInputs` and `eventStream` members must have their frozen JSON types; every event line must
  parse to a JSON object. A JSON array/scalar/string/null where an object is required, or a wrong-typed
  member, is `ARGUS2-CORRUPT-MANIFEST-SHAPE` (manifest) or `ARGUS2-CORRUPT-EVENT` (record) and stops
  trusted use of that container — it is never coerced, iterated or indexed assuming the wrong type.
* **Closed nested keys.** Every event key and every nested key of `clocks`, `observation` (all
  sub-objects), `snapshot`, `intervalProvenance`, artifact entries, obligation entries and metric-input
  entries is validated against the frozen closed sets exactly as on write; an unknown nested key outside
  `extensions` is a stable `ARGUS2-SCHEMA-UNKNOWN-FIELD` diagnostic. Verification reuses the same
  validators as the writer so write and read cannot drift.
* **Required identity.** `runId`, `eventId` and `producerId` are required on every event and are
  non-empty strings within `max_id_length`; a missing identity is `ARGUS2-INPUT-IDENTITY-MISSING` (event
  read) and a non-string is a stable type diagnostic. Absent/`null` optional fields are treated as
  absent, never as an empty or fabricated value.
* **Run-ID consistency.** Every accepted event's `runId` must equal the manifest `runId`
  (`ARGUS2-CORRUPT-RUN-ID-MISMATCH`); a mismatch excludes that record from the trusted result and marks
  the run assessed `incomplete`.
* **Per-run uniqueness.** Within a run, `eventId` must be unique; a duplicate (including one appearing
  after a truncated/recovered line) is `ARGUS2-CORRUPT-DUPLICATE-EVENT` and excludes the duplicate from
  the trusted result. Duplicate tracking is bounded by `max_events`.
* **Monotonic ingestion ordinals.** Accepted events must carry strictly increasing `ingestionOrdinal`
  starting at `1` with no gaps (`ARGUS2-CORRUPT-ORDINAL` otherwise). The ordinal is still never
  presented as temporal or causal order.
* **Finite values.** Every clock `value` and every numeric field must be finite (`allow_nan=False`);
  a non-finite/NaN/Infinity value or a non-numeric clock is `ARGUS2-INPUT-NONFINITE` /
  `ARGUS2-CLOCK-UNRESOLVED` as applicable. Non-finite values never enter the result.
* **No uncaught parse/I/O exception.** Every container-type, value-type, version, decode, bound and I/O
  condition is caught and converted to a bounded stable categorized diagnostic. `TypeError`,
  `KeyError`, `ValueError`, `UnicodeDecodeError`, `json.JSONDecodeError`, and `OSError` must not escape
  the reader or the CLI; malformed input returns an assessed-`incomplete`, bounded partial result.

### 12.2 Immutable returned views (`AR-F05`, `ARGUS2-ADV-07`)

`records()`, `metric_inputs()`, `manifest` and the CLI/export outputs return independent defensive
copies or immutable structures. Mutating any returned list/dict (or any nested object reachable from a
returned view) cannot change an internal admission fact, an indexed artifact size/hash, a writer state
or a subsequent read's result. Export output is derived from the internal immutable snapshot, so a
caller that holds a returned object and mutates it cannot make two exports of unchanged on-disk inputs
differ.

## 13. Metric-input links (no computation)

The manifest/reader expose `metricInputs`: a list derived from the accepted plan's `metrics` entries
(where present in the plan body), each entry `{"metricId","observerIds","calculationRef","unitSemantics",
"timeDomainIds","selection": [<artifact path or eventId>, ...]}` linking the declared metric/observer
references to captured artifacts/events. Argus computes **no** metric value and invokes no oracle; the
selection is a declared reference only, and an incomplete selection is reported, never filled in.

## 14. Public Python API and CLI (frozen signatures)

Public surface exported from `xverse.argus`:

```python
class EvidenceDiagnostic: ...        # code, category, severity, message, pointer, path, eventId, remediation
class EvidenceError(Exception): ...  # .diagnostics: tuple[EvidenceDiagnostic, ...]

@dataclass(frozen=True)
class EvidenceLimits: ...            # §10 fields

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
    def flush_buffer(self) -> None: ...
    def finalize(self, *, finalized_at=None) -> "EvidenceManifest": ...
    def abort(self, *, reason=None) -> None: ...

class EvidenceReader:
    diagnostics: tuple[EvidenceDiagnostic, ...]
    def records(self): ...
    def metric_inputs(self): ...
    def export_json(self) -> str: ...
    def export_jsonl(self) -> str: ...
```

CLI (`xverse-argus`, read-only): `verify <run-root>` prints the manifest/verification summary as JSON;
`export <run-root> [--format json|jsonl]` writes the canonical export to stdout. Writing is programmatic
only through `EvidenceStore.open_run`. `main(argv=None) -> int` returns `0` on success, `1` on a failed
verification (assessed `incomplete`/corrupt, including when the manifest recorded `complete`), `2` on
usage/input error. `verify` output carries both the recorded and assessed status/reasons (§11.1); exit
code `0` requires `assessedEvidenceStatus == "complete"`.

### 14.1 Deep snapshot of admitted caller objects (`AR-F05`, `ARGUS2-ADV-07`)

Admission is a boundary: the writer must not retain a reference to any caller-owned mutable object.

* **Obligations.** Each admitted obligation is deep-snapshotted, including the nested `detail` object
  (e.g. `min-observations.detail.minimum`). Snapshotting is a canonical JSON round-trip
  (`json.loads(canonical_json(value))`) followed by storing the reconstructed value; non-JSON-encodable
  or non-finite content is rejected at admission with a stable `ARGUS2-INPUT-FIELD-INVALID` diagnostic.
  If the caller later mutates its own list/dict/nested `detail`, the evaluated obligation set is
  unchanged.
* **Envelope, digests, clocks, extensions, annotation.** The run envelope, `source_byte_digests`,
  caller clock declarations, annotation text and `extensions` values are deep-copied/round-tripped at
  admission for the same reason; the manifest records the snapshot, not an alias.
* **Artifact identity.** `record_artifact` computes size and SHA-256 from the confined regular file at
  record time and stores its own immutable entry. The returned artifact view is an independent copy: a
  caller that mutates the returned dict cannot rewrite the indexed `bytes`/`sha256`, and a later
  mutation of the file on disk is detected on read as `ARGUS2-CORRUPT-ARTIFACT-*` rather than masked.
* **Returned views.** Every public accessor returns a deep copy or immutable structure (§12.2); internal
  admission facts are never exposed by reference.

## 15. Additive namespace and wheel packaging

* New files: `src/xverse/__init__.py` (a plain package marker with `__all__ = []` and **no** import of
  `xcom`) and `src/xverse/argus/**`. The C++ `src/xverse/xcom/**` tree is never packaged and never
  modified.
* `pyproject.toml` stays additive: `[project.scripts]` gains `xverse-argus = "xverse.argus.cli:main"`
  and the existing `xdl` entry is unchanged; `name = "xverse-xdl"` is unchanged; the wheel gains the
  `xverse` package. The frozen selection keeps `packages = ["src/xverse_xdl"]` and adds
  `force-include` entries mapping `src/xverse/argus` → `xverse/argus` and `src/xverse/__init__.py` →
  `xverse/__init__.py`, so only the Argus package (never `xcom`) enters the wheel. The implementation
  stage may switch to an equivalent `only-include`/`sources` selection only if it preserves this exact
  wheel content, and must verify it from the built artifact.
* Compatibility: installed `xverse_xdl.experiment_plan` imports, the `xdl` CLI, and the accepted C++
  contracts remain intact; `xverse.argus` and `xverse_xdl` both import from the installed wheel outside
  the source tree with an empty `PYTHONPATH`.

## 16. Diagnostic catalogue (categorized, stable)

Every diagnostic carries `{code, category, severity, message, pointer?, path?, eventId?, remediation}`.
Categories distinguish the required classes: `input-rejection` (`ARGUS2-INPUT-*`), `io-failure`
(`ARGUS2-IO-*`), `unsupported-schema` (`ARGUS2-SCHEMA-*`), `corrupt-artifact` (`ARGUS2-CORRUPT-*`),
`missing-evidence` (`ARGUS2-MISSING-*`) and `known-observation-loss` (`ARGUS2-LOSS-*`), plus the
auxiliary `ARGUS2-BOUND-*`, `ARGUS2-PATH-*`, `ARGUS2-STATE-*`, `ARGUS2-CLOCK-*`, `ARGUS2-CAUSAL-*` and
`ARGUS2-PLAN-*` families. The closed code list is enumerated in the unit-specification stage; the
category mapping above is frozen and no diagnostic is emitted without a real violation.

### 16.1 Repair-specific codes (frozen here; bound to adversarial cases)

The following codes are added by the terminal-review repair and are stable, categorized and emitted
only on a real violation. Each is bound to the adversarial case that must exercise it.

| Code | Category | Raised when | Adversarial case |
| --- | --- | --- | --- |
| `ARGUS2-PATH-ESCAPE` | `path` | absolute/`\`/NUL/drive/`.`/`..`/non-matching recorded path, or a resolved path outside the run root | `ARGUS2-ADV-01` |
| `ARGUS2-PATH-SYMLINK` | `path` | a symlink on the confined manifest/stream/artifact path (even one resolving inside the run root), or `O_NOFOLLOW` refuses | `ARGUS2-ADV-01` |
| `ARGUS2-PATH-NOT-REGULAR` | `path` | `lstat`/`fstat` shows a non-regular file, or device/inode differs (TOCTOU) | `ARGUS2-ADV-01` |
| `ARGUS2-BOUND-EXCEEDED` | `bound` | an actual `max_manifest_bytes`/`max_event_bytes`/`max_events`/`max_read_records`/`max_diagnostic_count` violation (read or publication) | `ARGUS2-ADV-02`, `ARGUS2-ADV-06` |
| `ARGUS2-CORRUPT-MANIFEST-SHAPE` | `corrupt-artifact` | manifest or a frozen manifest member has the wrong container/type | `ARGUS2-ADV-05` |
| `ARGUS2-CORRUPT-RECORD-SHAPE` / `ARGUS2-CORRUPT-EVENT` | `corrupt-artifact` | an event line is not a JSON object or a frozen nested member has the wrong type/key set | `ARGUS2-ADV-05` |
| `ARGUS2-CORRUPT-RUN-ID-MISMATCH` | `corrupt-artifact` | an event `runId` differs from the manifest `runId` | `ARGUS2-ADV-04` |
| `ARGUS2-CORRUPT-DUPLICATE-EVENT` | `corrupt-artifact` | a duplicate `eventId` within one run | `ARGUS2-ADV-04` |
| `ARGUS2-CORRUPT-ORDINAL` | `corrupt-artifact` | `ingestionOrdinal` not strictly increasing from `1` / has a gap | `ARGUS2-ADV-04` |
| `ARGUS2-INPUT-IDENTITY-MISSING` | `input-rejection` | a required event identity is absent/empty on read or admission | `ARGUS2-ADV-04` |
| `ARGUS2-INPUT-NONFINITE` | `input-rejection` | a clock/numeric value is NaN/Infinity/non-finite | `ARGUS2-ADV-04` |
| `ARGUS2-IO-FAILURE` | `io-failure` | atomic manifest replace or a confined read/write fails | `ARGUS2-ADV-06` |
| `ARGUS2-INPUT-FIELD-INVALID` | `input-rejection` | admitted obligation/detail is non-JSON-encodable or non-finite at snapshot time | `ARGUS2-ADV-07` |
| `ARGUS2-REASON-CORRUPT-MANIFEST` / `ARGUS2-REASON-CORRUPT-EVENT` | assessed reason | reader-assessed status when a container/record is structurally invalid (never writer-emitted) | `ARGUS2-ADV-03`, `ARGUS2-ADV-05` |

## 17. Constitution check (repeated before code)

The constitution check of `architecture.md` §9 is repeated here and holds for this design: production
safety, domain neutrality, XDL centrality, standards interoperability, logical/physical separation,
physical-hardware accounting, foundations-before-compatibility, repository boundaries, explicit
fidelity/maturity, reproducibility/traceability and the capability-acceptance gates are all preserved.
Scientific values remain caller inputs; no existing ADR, source requirement or accepted artifact is
rewritten; no runtime, interoperability, compatibility, parity, readiness or delivery claim is created
by this design.

## 18. Cross-stage hand-off

The unit-specification stage must decompose each `ARGUS2-SR-###-CMP` into units (with `decomposes_to`
links) and freeze exact pytest-discoverable test identifiers, including duplicate IDs, unknown versions,
partial writes/recovery, exceeded bounds, source digest mutation, missing causal/interval closure,
payload visibility/loss, unsafe paths/symlinks and installed-wheel consumer compatibility. The
verification-design stage must bind the four ARGUS2 measures (`ARGUS2-UNIT`, `ARGUS2-STATIC`,
`ARGUS2-INTEGRATION`, `ARGUS2-VALIDATION`) to exact test identifiers and freeze the real C++ owned-record
fixture and XDL/compiler consumer cases. No code may be written until all four design stages complete and
the precode gate passes.

**Terminal-review repair hand-off (binding).** The frozen adversarial cases `ARGUS2-ADV-01`–`ARGUS2-ADV-07`
(`architecture.md` §11.1, detailed in §4.4, §8.5, §11.1, §12.1, §12.2 and §14.1) must each be bound to at
least one exact pytest-discoverable identifier across the unit and validation measures, and the existing
passing regression cases must be preserved (no deletion, no assertion weakening). The unit-specification
stage freezes the exact identifiers before code; the verification-design stage ensures every declared
identifier appears in the relevant actual logs. Implementation, integration and validation must repair
against these frozen contracts; a design change requires a reviewed successor candidate and stops the run.
