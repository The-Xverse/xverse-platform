"""Single-writer evidence persistence, manifest publication and honest completeness.

Owns the ``new -> open -> closed`` / ``open -> failed`` writer machine, append-only canonical JSONL
persistence, the atomic JSON manifest (temporary file -> flush -> ``os.fsync`` -> ``os.replace`` +
directory fsync), the caller-declared finite bounds, confined artifact indexing and the evaluation
of declared evidence obligations. Stream closure and evidence completeness are separate facts
(``detailed-design.md`` sections 4, 8 and 11, invariants ``ARGUS2-INV-01``/``06``/``09``/``14``).
"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .artifacts import build_index_entry, sha256_file, verify_index_entry
from .causation import CausalIndex, index_references
from .clocks import validate_clocks
from .diagnostics import (
    EvidenceDiagnostic,
    EvidenceError,
    bound_diagnostics,
    diagnostic,
)
from .limits import EvidenceLimits
from .observation import validate_projection
from .schema import (
    ANNOTATION_KEYS,
    EVENT_KINDS,
    EVENT_SCHEMA_VERSION,
    MANIFEST_VERSION,
    WRITER_EMITTED_KINDS,
    canonical_bytes,
    json_depth_exceeded,
    reject_unknown_keys,
    validate_extensions,
)
from .snapshot import validate_snapshot

__all__ = [
    "MANIFEST_NAME",
    "STREAM_NAME",
    "EvidenceManifest",
    "EvidenceRun",
    "evaluate_evidence",
    "manifest_data",
    "preview_open_manifest",
]

MANIFEST_NAME = "manifest.json"
STREAM_NAME = "events.jsonl"
_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
_ID_PATTERN = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_RUN_ID_PATTERN = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


@dataclass(frozen=True)
class EvidenceManifest:
    """A published manifest, with the stable categorized diagnostics observed while publishing."""

    data: dict[str, Any]
    diagnostics: tuple[EvidenceDiagnostic, ...] = field(default_factory=tuple)

    @property
    def writer_state(self) -> str:
        return self.data.get("writerState")

    @property
    def evidence_status(self) -> str:
        return self.data.get("evidenceStatus")

    @property
    def evidence_reasons(self) -> list[str]:
        return copy.deepcopy(list(self.data.get("evidenceReasons", [])))

    @property
    def event_count(self) -> int:
        return self.data.get("eventCount", 0)

    @property
    def plan(self) -> dict[str, Any]:
        return copy.deepcopy(self.data.get("plan", {}))

    @property
    def artifacts(self) -> list[dict[str, Any]]:
        return copy.deepcopy(list(self.data.get("artifacts", [])))

    @property
    def obligations(self) -> list[dict[str, Any]]:
        return copy.deepcopy(list(self.data.get("obligations", [])))

    @property
    def limits(self) -> dict[str, Any]:
        return copy.deepcopy(self.data.get("limits", {}))

    # Frozen external field-name aliases.
    @property
    def writerState(self) -> str:
        return self.writer_state

    @property
    def evidenceStatus(self) -> str:
        return self.evidence_status

    @property
    def evidenceReasons(self) -> list[str]:
        return self.evidence_reasons

    @property
    def eventCount(self) -> int:
        return self.event_count


# --------------------------------------------------------------------------------------
# Obligation and completeness evaluation (shared by the writer and the reader)
# --------------------------------------------------------------------------------------


def _is_true(value: Any) -> bool:
    return value is True


def _admission_snapshot(value: Any, *, pointer: str, diagnostics: list[EvidenceDiagnostic]) -> Any:
    """Return a canonical-round-tripped snapshot of one admitted caller value, or ``None``.

    Deep-copying alone would retain a non-finite or non-JSON-encodable value that later fails during
    serialization; the round-trip rejects it at admission with a stable diagnostic so no caller-owned
    reference is retained and no raw ``TypeError``/``ValueError`` escapes (``AR-F05``).
    """

    try:
        return json.loads(canonical_bytes(value))
    except (TypeError, ValueError, RecursionError):
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                f"admitted value at {pointer} is not JSON-encodable or contains a non-finite value",
                pointer=pointer,
                remediation="Supply finite JSON-encodable content; no caller reference is retained.",
            )
        )
        return None


def evaluate_evidence(
    records: list[dict[str, Any]],
    *,
    obligations: list[dict[str, Any]],
    artifact_entries: list[dict[str, Any]],
    artifact_diagnostics: tuple[EvidenceDiagnostic, ...],
    recovery_diagnostics: tuple[EvidenceDiagnostic, ...],
    truncated: bool,
    writer_state: str,
    limits: EvidenceLimits,
) -> tuple[str, list[str], tuple[EvidenceDiagnostic, ...]]:
    """Evaluate obligations and integrity, returning status, reasons and diagnostics."""

    reasons: list[str] = []
    diagnostics: list[EvidenceDiagnostic] = list(recovery_diagnostics)

    if truncated or any(item.code == "ARGUS2-CORRUPT-STREAM-TRUNCATED" for item in recovery_diagnostics):
        reasons.append("ARGUS2-REASON-TRUNCATED-STREAM")
    if any(item.code == "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED" for item in recovery_diagnostics):
        reasons.append("ARGUS2-REASON-UNSUPPORTED-SCHEMA")

    artifact_codes = {item.code for item in artifact_diagnostics}
    diagnostics.extend(artifact_diagnostics)
    if "ARGUS2-CORRUPT-ARTIFACT-HASH" in artifact_codes or "ARGUS2-CORRUPT-ARTIFACT-SIZE" in artifact_codes:
        reasons.append("ARGUS2-REASON-MUTATED-ARTIFACT")
    if "ARGUS2-MISSING-ARTIFACT" in artifact_codes:
        reasons.append("ARGUS2-REASON-MISSING-ARTIFACT")

    causal_index, causal_diagnostics = index_references(records, maximum=limits.max_causal_index_entries)
    unresolved = causal_index.unresolved()
    if unresolved:
        reasons.append("ARGUS2-REASON-UNRESOLVED-CAUSATION")
        diagnostics.append(
            diagnostic(
                "ARGUS2-CAUSAL-UNRESOLVED",
                f"declared causal references resolve to no accepted event: {', '.join(unresolved)}",
                remediation="The missing predecessor is never repaired or invented.",
            )
        )
    diagnostics.extend(causal_diagnostics)

    observations = [item for item in records if item.get("eventKind") == "observation"]
    snapshots = [item for item in records if item.get("eventKind") == "snapshot"]

    known_loss = False
    for event in observations:
        counters = event.get("observation", {}).get("counters", {})
        if not isinstance(counters, dict):
            continue
        if int(counters.get("dropped", 0)) > 0 or int(counters.get("coalesced", 0)) > 0:
            known_loss = True
            diagnostics.append(
                diagnostic(
                    "ARGUS2-LOSS-KNOWN-DROP",
                    "an accepted observation declares a known drop or coalescing",
                    event_id=event.get("eventId"),
                    remediation="Known loss stays visible and cannot be upgraded to complete.",
                )
            )
            break
    unclosed = False
    degraded = False
    invalid = False
    for event in snapshots:
        snapshot = event.get("snapshot", {})
        interval = snapshot.get("intervalProvenance", {}) if isinstance(snapshot, dict) else {}
        if isinstance(interval, dict) and interval.get("closure") != "closed":
            unclosed = True
        if not isinstance(snapshot, dict):
            continue
        if int(snapshot.get("dropped", 0)) > 0 or int(snapshot.get("coalesced", 0)) > 0:
            known_loss = True
        state = snapshot.get("validityState")
        if state == "degraded":
            degraded = True
            diagnostics.append(
                diagnostic(
                    "ARGUS2-LOSS-DEGRADED-INTERVAL",
                    "a snapshot declares a degraded validity state",
                    event_id=event.get("eventId"),
                    remediation="A degraded interval is never acknowledged away by finalization.",
                )
            )
        elif state == "invalid":
            invalid = True
            diagnostics.append(
                diagnostic(
                    "ARGUS2-LOSS-INVALID-INTERVAL",
                    "a snapshot declares an invalid validity state",
                    event_id=event.get("eventId"),
                    remediation="An invalid interval stays visible.",
                )
            )
        if _is_true(snapshot.get("experimentValidityDegraded")):
            known_loss = True
    if known_loss:
        reasons.append("ARGUS2-REASON-KNOWN-LOSS")
    if degraded:
        reasons.append("ARGUS2-REASON-DEGRADED-INTERVAL")
    if invalid:
        reasons.append("ARGUS2-REASON-INVALID-INTERVAL")
    if unclosed:
        reasons.append("ARGUS2-REASON-UNCLOSED-INTERVAL")

    unmet_required = False
    for obligation in obligations:
        if not isinstance(obligation, dict):
            continue
        kind = obligation.get("kind")
        required = _is_true(obligation.get("required"))
        detail = obligation.get("detail") if isinstance(obligation.get("detail"), dict) else {}
        if kind == "causal-closure":
            satisfied = not unresolved
        elif kind == "interval-closure":
            satisfied = bool(snapshots) and not unclosed
        elif kind == "no-known-loss":
            satisfied = not known_loss and not degraded and not invalid
        elif kind == "min-observations":
            minimum = detail.get("minimum")
            satisfied = isinstance(minimum, int) and not isinstance(minimum, bool) and len(observations) >= minimum
        else:
            satisfied = False
        if required and not satisfied:
            unmet_required = True
        if not satisfied:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-MISSING-ARTIFACT",
                    f"declared obligation {obligation.get('obligationId')!r} of kind {kind!r} is unsatisfied",
                    remediation="Unsatisfied obligations are reported, never filled in.",
                )
            )
    if unmet_required:
        reasons.append("ARGUS2-REASON-UNMET-OBLIGATION")

    if writer_state != "closed" and "ARGUS2-REASON-WRITER-STATE" not in reasons:
        reasons.append("ARGUS2-REASON-WRITER-STATE")

    ordered = sorted(set(reasons))
    status = "complete" if (writer_state == "closed" and not ordered) else "incomplete"
    bounded = bound_diagnostics(diagnostics, limits.max_diagnostic_count)
    return status, ordered, bounded


def manifest_data(
    *,
    run_id: str,
    plan_block: dict[str, Any],
    source_byte_provenance: dict[str, Any],
    obligations: list[dict[str, Any]],
    limits: EvidenceLimits,
    opened_at: dict[str, Any] | None,
    state: str,
    evidence_status: str,
    reasons: list[str],
    event_count: int,
    finalized_at: Any,
    stream_bytes: int,
    stream_sha: str,
    artifacts: list[dict[str, Any]] | None = None,
    metric_inputs: list[dict[str, Any]] | None = None,
    clock_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Build one frozen manifest object (no I/O)."""

    manifest: dict[str, Any] = {
        "schemaVersion": EVENT_SCHEMA_VERSION,
        "manifestVersion": MANIFEST_VERSION,
        "runId": run_id,
        "plan": plan_block,
        "sourceByteProvenance": source_byte_provenance,
        "writerState": state,
        "eventCount": event_count,
        "eventStream": {
            "path": STREAM_NAME,
            "mediaType": "application/x-ndjson",
            "schemaVersion": EVENT_SCHEMA_VERSION,
            "bytes": stream_bytes,
            "sha256": stream_sha or _EMPTY_SHA256,
        },
        "artifacts": list(artifacts or []),
        "obligations": list(obligations),
        "evidenceStatus": evidence_status,
        "evidenceReasons": list(reasons),
        "limits": limits.to_data(),
        "metricInputs": list(metric_inputs or []),
        "clockDomains": sorted(clock_domains or []),
    }
    if opened_at is not None:
        manifest["openedAt"] = opened_at
    if finalized_at is not None:
        manifest["finalizedAt"] = finalized_at
    return manifest


def preview_open_manifest(
    *,
    run_id: str,
    plan_block: dict[str, Any],
    source_byte_provenance: dict[str, Any],
    obligations: list[dict[str, Any]],
    limits: EvidenceLimits,
    opened_at: dict[str, Any] | None,
    metric_inputs: list[dict[str, Any]] | None = None,
    clock_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Build the exact open manifest the writer would publish, before any file is created."""

    return manifest_data(
        run_id=run_id,
        plan_block=plan_block,
        source_byte_provenance=source_byte_provenance,
        obligations=obligations,
        limits=limits,
        opened_at=opened_at,
        state="open",
        evidence_status="unassessed",
        reasons=[],
        event_count=0,
        finalized_at=None,
        stream_bytes=0,
        stream_sha=_EMPTY_SHA256,
        metric_inputs=metric_inputs,
        clock_domains=clock_domains,
    )


# --------------------------------------------------------------------------------------
# Writer
# --------------------------------------------------------------------------------------


class EvidenceRun:
    """Exactly one owning writer for one fresh run root."""

    def __init__(
        self,
        *,
        root: Path,
        run_id: str,
        plan_block: dict[str, Any],
        source_byte_provenance: dict[str, Any],
        obligations: list[dict[str, Any]],
        limits: EvidenceLimits,
        declared_domains: frozenset[str],
        opened_at: dict[str, Any] | None,
        registry_key: str,
        unregister,
        metric_inputs: list[dict[str, Any]] | None = None,
        clock_domains: list[str] | None = None,
    ) -> None:
        self._root = Path(root)
        self._run_id = run_id
        self._plan_block = plan_block
        self._source_byte_provenance = source_byte_provenance
        self._obligations = obligations
        self._limits = limits
        self._declared_domains = declared_domains
        self._opened_at = opened_at
        self._metric_inputs = list(metric_inputs or [])
        self._clock_domains = sorted(clock_domains or [])
        self._registry_key = registry_key
        self._unregister = unregister
        self._writer_state = "open"
        self._ordinal = 0
        self._event_ids: set[str] = set()
        self._causal = CausalIndex(limits.max_causal_index_entries)
        self._artifact_entries: list[dict[str, Any]] = []
        self._artifacts_by_path: dict[str, dict[str, Any]] = {}
        self._tmp_counter = 0
        self._stream = (self._root / STREAM_NAME).open("w", encoding="utf-8", newline="\n")
        self._publish_manifest(state="open", evidence_status="unassessed", reasons=[], event_count=0, finalized_at=None)

    # -- public surface -----------------------------------------------------------------

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def writer_state(self) -> str:
        return self._writer_state

    @property
    def declared_domains(self) -> frozenset[str]:
        return self._declared_domains

    def append_event(
        self,
        *,
        event_id: str,
        producer_id: str,
        event_kind: str,
        producer_sequence: int | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        clocks: Any = None,
        annotation: Any = None,
        extensions: Any = None,
        observation: Any = None,
        snapshot: Any = None,
    ) -> int:
        """Append one caller-supplied event; return its ingestion ordinal."""

        return self._append(
            event_id=event_id,
            producer_id=producer_id,
            event_kind=event_kind,
            producer_sequence=producer_sequence,
            correlation_id=correlation_id,
            causation_id=causation_id,
            clocks=clocks,
            annotation=annotation,
            extensions=extensions,
            observation=observation,
            snapshot=snapshot,
            internal=False,
        )

    def import_observation(self, projection: Any) -> tuple[int, ...]:
        """Import a versioned owned-observation projection envelope; return ingestion ordinals."""

        self._require_open()
        envelope, diagnostics = validate_projection(projection, limits=self._limits)
        if diagnostics or envelope is None:
            raise EvidenceError(bound_diagnostics(diagnostics, self._limits.max_diagnostic_count))
        ordinals: list[int] = []
        for record in envelope["records"]:
            clocks = {
                "source": record["sourceClock"],
                "observation": record["observationClock"],
            }
            event_id = self._derived_event_id("obs", record.get("tapId"))
            ordinal = self._append(
                event_id=event_id,
                producer_id=str(record.get("tapId") or "xcom-projection"),
                event_kind="observation",
                producer_sequence=record.get("sequence"),
                correlation_id=record.get("correlationId"),
                causation_id=record.get("causationId"),
                clocks=clocks,
                annotation=None,
                extensions=None,
                observation=record,
                snapshot=None,
                internal=True,
            )
            ordinals.append(ordinal)
        return tuple(ordinals)

    def import_snapshot(self, snapshot: Any, *, event_id: str | None = None) -> int:
        """Import one separately supplied tap snapshot; return its ingestion ordinal."""

        self._require_open()
        validated, diagnostics = validate_snapshot(snapshot, limits=self._limits)
        if diagnostics or validated is None:
            raise EvidenceError(bound_diagnostics(diagnostics, self._limits.max_diagnostic_count))
        interval = validated.get("intervalProvenance", {})
        clocks = None
        if isinstance(interval, dict):
            possible = {
                key: interval[key]
                for key in ("start", "end")
                if isinstance(interval.get(key), dict)
            }
            if possible:
                clocks = possible
        return self._append(
            event_id=event_id or self._derived_event_id("snap", validated.get("declaredTapId")),
            producer_id=str(validated.get("declaredTapId") or "xcom-snapshot"),
            event_kind="snapshot",
            producer_sequence=None,
            correlation_id=None,
            causation_id=None,
            clocks=clocks,
            annotation=None,
            extensions=None,
            observation=None,
            snapshot=validated,
            internal=True,
        )

    def record_artifact(
        self,
        relative_path: str,
        *,
        media_type: str = "application/json",
        schema_version: str = "1.0",
        role: str = "evidence",
    ) -> dict[str, Any]:
        """Index one confined regular file already present inside the run root."""

        self._require_open()
        if len(self._artifact_entries) + 1 > self._limits.max_artifacts and relative_path not in self._artifacts_by_path:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"artifact index would exceed max_artifacts {self._limits.max_artifacts}",
                    path=relative_path,
                    remediation="Reduce the number of indexed artifacts.",
                )
            )
        entry = build_index_entry(
            self._root,
            relative_path,
            media_type=media_type,
            schema_version=schema_version,
            role=role,
            limits=self._limits,
        )
        if entry is None:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-MISSING-ARTIFACT",
                    f"artifact does not exist inside the run root: {relative_path!r}",
                    path=relative_path,
                    remediation="Restore the artifact; it is never created by the writer.",
                )
            )
        if relative_path not in self._artifacts_by_path:
            self._artifact_entries.append(entry)
        else:
            index = self._artifact_entries.index(self._artifacts_by_path[relative_path])
            self._artifact_entries[index] = entry
        self._artifacts_by_path[relative_path] = entry
        return copy.deepcopy(entry)

    def flush_buffer(self) -> None:
        """Flush and fsync the appended-line buffer: the only appended-line durability point."""

        self._require_open()
        self._stream.flush()
        os.fsync(self._stream.fileno())

    def finalize(self, *, finalized_at: Any = None) -> EvidenceManifest:
        """Close the stream, verify every artifact and obligation, and publish the closed manifest."""

        self._require_open()
        self.flush_buffer()
        self._stream.flush()
        self._stream.close()
        manifest: dict[str, Any] | None = None
        try:
            from .recovery import recover_stream

            recovery = recover_stream(self._root, limits=self._limits, manifest_run_id=self._run_id)
            records = list(recovery.records)
            artifact_diagnostics: list[EvidenceDiagnostic] = []
            for entry in self._artifact_entries:
                artifact_diagnostics.extend(verify_index_entry(self._root, entry))
            status, reasons, diagnostics = evaluate_evidence(
                records,
                obligations=self._obligations,
                artifact_entries=self._artifact_entries,
                artifact_diagnostics=tuple(artifact_diagnostics),
                recovery_diagnostics=tuple(recovery.diagnostics),
                truncated=recovery.truncated,
                writer_state="closed",
                limits=self._limits,
            )
            manifest = self._manifest(
                state="closed",
                evidence_status=status,
                reasons=reasons,
                event_count=len(records),
                finalized_at=finalized_at,
                stream_bytes=recovery.byte_count,
                stream_sha=recovery.sha256,
            )
            # The one publication chokepoint enforces the actual serialized byte bound. The writer
            # state is only advanced to 'closed' after the publication succeeds, so a bound or I/O
            # failure preserves the prior manifest bytes and never reports closed/complete.
            self._publish(manifest)
            self._writer_state = "closed"
        except BaseException:
            self._writer_state = "failed"
            raise
        finally:
            self._unregister(self._registry_key)
        return EvidenceManifest(data=manifest, diagnostics=diagnostics)

    def abort(self, *, reason: str | None = None) -> None:
        """Abort an open run: best-effort failure event and a failed manifest."""

        if self._writer_state != "open":
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-STATE-ILLEGAL-TRANSITION",
                    f"cannot abort a run in state {self._writer_state!r}",
                    remediation="A closed or failed run is never reopened for writing.",
                )
            )
        try:
            self._append(
                event_id="run-failed",
                producer_id="argus-writer",
                event_kind="run-failed",
                annotation={"text": reason} if isinstance(reason, str) else None,
                internal=True,
            )
        except EvidenceError:
            pass
        try:
            self._stream.flush()
            os.fsync(self._stream.fileno())
        except (OSError, ValueError):
            pass
        self._stream.close()
        self._writer_state = "failed"
        try:
            from .recovery import recover_stream

            recovery = recover_stream(self._root, limits=self._limits, manifest_run_id=self._run_id)
            status, reasons, _diagnostics = evaluate_evidence(
                list(recovery.records),
                obligations=self._obligations,
                artifact_entries=self._artifact_entries,
                artifact_diagnostics=(),
                recovery_diagnostics=tuple(recovery.diagnostics),
                truncated=recovery.truncated,
                writer_state="failed",
                limits=self._limits,
            )
            manifest = self._manifest(
                state="failed",
                evidence_status=status,
                reasons=reasons,
                event_count=len(recovery.records),
                finalized_at=None,
                stream_bytes=recovery.byte_count,
                stream_sha=recovery.sha256,
            )
            self._publish(manifest)
        finally:
            self._unregister(self._registry_key)

    # -- internals ----------------------------------------------------------------------

    def _require_open(self) -> None:
        if self._writer_state != "open":
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-STATE-ILLEGAL-TRANSITION",
                    f"writer state {self._writer_state!r} does not permit this operation",
                    remediation="Only an open run accepts writes; finalize and abort are mutually exclusive.",
                )
            )

    def _derived_event_id(self, prefix: str, identity: Any) -> str:
        ordinal = self._ordinal + 1
        base = f"{prefix}.{ordinal}"
        if isinstance(identity, str) and identity:
            candidate = f"{prefix}.{identity}"
            if candidate not in self._event_ids and len(candidate) <= self._limits.max_id_length:
                return candidate
        return base

    def _validate_id(self, value: Any, *, field: str, pattern) -> list[EvidenceDiagnostic]:
        if not isinstance(value, str) or value == "":
            return [
                diagnostic(
                    "ARGUS2-INPUT-IDENTITY-MISSING",
                    f"required identity field {field!r} is absent or empty",
                    pointer=f"/event/{field}",
                    remediation="Supply the caller's identity; no identity is generated.",
                )
            ]
        if pattern.match(value) is None:
            return [
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"{field} fails the frozen identity pattern",
                    pointer=f"/event/{field}",
                    remediation="Use a safe caller-supplied identity.",
                )
            ]
        if len(value) > self._limits.max_id_length:
            return [
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"{field} exceeds max_id_length {self._limits.max_id_length}",
                    pointer=f"/event/{field}",
                    remediation="Shorten the declared identity.",
                )
            ]
        return []

    def _append(
        self,
        *,
        event_id: Any,
        producer_id: Any,
        event_kind: Any,
        producer_sequence: Any = None,
        correlation_id: Any = None,
        causation_id: Any = None,
        clocks: Any = None,
        annotation: Any = None,
        extensions: Any = None,
        observation: Any = None,
        snapshot: Any = None,
        internal: bool,
    ) -> int:
        self._require_open()
        diagnostics: list[EvidenceDiagnostic] = []
        # Reject an adversarially deep caller value *before* any recursive validation, deep copy or
        # serialization, so open_run obligations and append_event annotation/extensions/observation/
        # snapshot can never raise an uncaught ``RecursionError`` (``AR-RVW-001``). The check is
        # iterative and bounded, and the rejected value is never written.
        for pointer, member in (
            ("/event/clocks", clocks),
            ("/event/annotation", annotation),
            ("/event/extensions", extensions),
            ("/event/observation", observation),
            ("/event/snapshot", snapshot),
        ):
            if member is not None and json_depth_exceeded(member):
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-FIELD-INVALID",
                        f"admitted value at {pointer} exceeds the bounded JSON nesting depth",
                        pointer=pointer,
                        remediation="Reduce the nesting depth; deeply nested content is rejected before any byte is written.",
                    )
                )
        if internal:
            if not isinstance(event_id, str) or event_id == "":
                diagnostics.extend(self._validate_id(event_id, field="eventId", pattern=_ID_PATTERN))
        else:
            diagnostics.extend(self._validate_id(event_id, field="eventId", pattern=_ID_PATTERN))
        diagnostics.extend(self._validate_id(producer_id, field="producerId", pattern=_ID_PATTERN))
        if event_kind not in EVENT_KINDS:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"event kind {event_kind!r} is outside the closed set",
                    pointer="/event/eventKind",
                    remediation=f"Use one of {', '.join(EVENT_KINDS)}.",
                )
            )
        elif not internal and event_kind in WRITER_EMITTED_KINDS:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"event kind {event_kind!r} is writer-emitted and may not be appended by a caller",
                    pointer="/event/eventKind",
                    remediation="Writer-emitted kinds remain writer-only.",
                )
            )
        if isinstance(event_id, str) and event_id in self._event_ids:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-DUPLICATE-EVENT",
                    f"event id {event_id!r} was already accepted in this run",
                    event_id=event_id,
                    remediation="Event identities must be unique within a run.",
                )
            )
        if producer_sequence is not None and (
            isinstance(producer_sequence, bool) or not isinstance(producer_sequence, int) or producer_sequence < 0
        ):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "producerSequence must be a non-negative integer when declared",
                    pointer="/event/producerSequence",
                    remediation="Preserve the declared sequence exactly.",
                )
            )
        for name, value in (("correlationId", correlation_id), ("causationId", causation_id)):
            if value is not None and (not isinstance(value, str) or value == ""):
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-FIELD-INVALID",
                        f"{name} must be a non-empty string when declared",
                        pointer=f"/event/{name}",
                        remediation="Preserve the declared reference exactly.",
                    )
                )
        preserved_annotation = None
        if annotation is not None:
            diagnostics.extend(reject_unknown_keys(annotation, ANNOTATION_KEYS, pointer="/event/annotation"))
            if isinstance(annotation, dict):
                text = annotation.get("text")
                if not isinstance(text, str):
                    diagnostics.append(
                        diagnostic(
                            "ARGUS2-INPUT-FIELD-INVALID",
                            "annotation text must be a string",
                            pointer="/event/annotation/text",
                            remediation="Supply a caller-supplied note string.",
                        )
                    )
                elif len(text) > self._limits.max_text_length:
                    diagnostics.append(
                        diagnostic(
                            "ARGUS2-BOUND-EXCEEDED",
                            "annotation text exceeds max_text_length",
                            pointer="/event/annotation/text",
                            remediation="Shorten the declared annotation text.",
                        )
                    )
            preserved_annotation = _admission_snapshot(
                annotation, pointer="/event/annotation", diagnostics=diagnostics
            )
        preserved_extensions = None
        if extensions is not None:
            diagnostics.extend(validate_extensions(extensions, pointer="/event/extensions", limits=self._limits))
            preserved_extensions = _admission_snapshot(
                extensions, pointer="/event/extensions", diagnostics=diagnostics
            )

        preserved_clocks = None
        if clocks is not None:
            preserved_clocks, clock_diagnostics = validate_clocks(clocks, pointer="/event/clocks", limits=self._limits)
            diagnostics.extend(clock_diagnostics)
        elif event_kind == "observation":
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-CLOCK-MISSING",
                    "an observation event requires explicit clocks",
                    pointer="/event/clocks",
                    remediation="Absent means not declared and is never inferred.",
                )
            )

        preserved_observation = None
        preserved_snapshot = None
        if event_kind == "observation":
            if not isinstance(observation, dict):
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                        "an observation event requires an observation record",
                        pointer="/event/observation",
                        remediation="Supply the frozen observation record.",
                    )
                )
            else:
                preserved_observation, record_diagnostics = _validate_inline_observation(observation, self._limits)
                diagnostics.extend(record_diagnostics)
        elif observation is not None:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "observation is only valid for an observation-kind event",
                    pointer="/event/observation",
                    remediation="Remove the observation or use the observation kind.",
                )
            )
        if event_kind == "snapshot":
            if not isinstance(snapshot, dict):
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                        "a snapshot event requires a snapshot record",
                        pointer="/event/snapshot",
                        remediation="Supply the frozen snapshot projection.",
                    )
                )
            else:
                preserved_snapshot, snapshot_diagnostics = validate_snapshot(snapshot, limits=self._limits)
                diagnostics.extend(snapshot_diagnostics)
        elif snapshot is not None:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "snapshot is only valid for a snapshot-kind event",
                    pointer="/event/snapshot",
                    remediation="Remove the snapshot or use the snapshot kind.",
                )
            )

        if len(self._event_ids) + 1 > self._limits.max_events and event_kind not in WRITER_EMITTED_KINDS:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"accepted events would exceed max_events {self._limits.max_events}",
                    remediation="Reduce the number of appended events or raise the caller bound.",
                )
            )

        if diagnostics:
            raise EvidenceError(bound_diagnostics(diagnostics, self._limits.max_diagnostic_count))

        # Pre-check the finite causal-index bound before any byte is written, so a rejected append
        # leaves the writer state and stream bytes unchanged.
        new_targets = tuple(
            value
            for value in (causation_id, correlation_id)
            if isinstance(value, str) and value not in self._causal.references
        )
        if len(self._causal.references) + len(new_targets) > self._limits.max_causal_index_entries:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"causal index would exceed max_causal_index_entries {self._limits.max_causal_index_entries}",
                    event_id=str(event_id),
                    remediation="Reduce the number of distinct declared causal references.",
                )
            )

        ordinal = self._ordinal + 1
        record: dict[str, Any] = {
            "schemaVersion": EVENT_SCHEMA_VERSION,
            "runId": self._run_id,
            "eventId": event_id,
            "producerId": producer_id,
            "ingestionOrdinal": ordinal,
            "eventKind": event_kind,
        }
        if producer_sequence is not None:
            record["producerSequence"] = producer_sequence
        if correlation_id is not None:
            record["correlationId"] = correlation_id
        if causation_id is not None:
            record["causationId"] = causation_id
        if preserved_clocks is not None:
            record["clocks"] = copy.deepcopy(preserved_clocks)
        if preserved_observation is not None:
            record["observation"] = copy.deepcopy(preserved_observation)
        if preserved_snapshot is not None:
            record["snapshot"] = copy.deepcopy(preserved_snapshot)
        if preserved_annotation is not None:
            record["annotation"] = copy.deepcopy(preserved_annotation)
        if preserved_extensions is not None:
            record["extensions"] = copy.deepcopy(preserved_extensions)

        try:
            line = canonical_bytes(record)
        except (TypeError, ValueError, RecursionError):
            raise EvidenceError(
                bound_diagnostics(
                    [
                        diagnostic(
                            "ARGUS2-INPUT-FIELD-INVALID",
                            "event record is not canonical JSON; non-finite or non-JSON content is rejected",
                            pointer="/event",
                            event_id=str(event_id),
                            remediation="Admit only finite JSON-encodable content; no byte is written.",
                        )
                    ],
                    self._limits.max_diagnostic_count,
                )
            ) from None
        if len(line) > self._limits.max_event_bytes:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"event exceeds max_event_bytes {self._limits.max_event_bytes}",
                    event_id=str(event_id),
                    remediation="Reduce the event size or raise the caller bound.",
                )
            )
        self._stream.write(line.decode("utf-8"))
        self._stream.write("\n")
        # The appended line is flushed to the OS buffer; flush_buffer() is the explicit
        # flush+fsync durability point documented by the frozen design.
        self._stream.flush()
        self._ordinal = ordinal
        if isinstance(event_id, str):
            self._event_ids.add(event_id)
        self._causal.register_event(str(event_id))
        targets = tuple(
            value for value in (causation_id, correlation_id) if isinstance(value, str)
        )
        if targets:
            self._causal.add_references(event_id=str(event_id), targets=targets)
        return ordinal

    def _manifest(
        self,
        *,
        state: str,
        evidence_status: str,
        reasons: list[str],
        event_count: int,
        finalized_at: Any,
        stream_bytes: int,
        stream_sha: str,
    ) -> dict[str, Any]:
        return manifest_data(
            run_id=self._run_id,
            plan_block=self._plan_block,
            source_byte_provenance=self._source_byte_provenance,
            obligations=self._obligations,
            limits=self._limits,
            opened_at=self._opened_at,
            state=state,
            evidence_status=evidence_status,
            reasons=reasons,
            event_count=event_count,
            finalized_at=finalized_at,
            stream_bytes=stream_bytes,
            stream_sha=stream_sha,
            artifacts=self._artifact_entries,
            metric_inputs=self._metric_inputs,
            clock_domains=self._clock_domains,
        )

    def _stream_identity(self) -> tuple[int, str]:
        """Return the appended-stream byte length and SHA-256 without an unbounded read."""

        stream_path = self._root / STREAM_NAME
        if not stream_path.exists():
            return 0, _EMPTY_SHA256
        size = stream_path.stat().st_size
        if size == 0:
            return 0, _EMPTY_SHA256
        return size, sha256_file(stream_path)

    def _publish_manifest(
        self,
        *,
        state: str,
        evidence_status: str,
        reasons: list[str],
        event_count: int,
        finalized_at: Any,
    ) -> None:
        stream_bytes, stream_sha = self._stream_identity()
        manifest = self._manifest(
            state=state,
            evidence_status=evidence_status,
            reasons=reasons,
            event_count=event_count,
            finalized_at=finalized_at,
            stream_bytes=stream_bytes,
            stream_sha=stream_sha,
        )
        self._publish(manifest)

    def _publish(self, manifest: dict[str, Any]) -> None:
        """The single manifest publication chokepoint (bound, temp file, fsync, atomic replace)."""

        # AR-F03/AR-F04: a manifest member admitted at the standalone nesting bound can exceed the
        # bounded nesting maximum once the manifest object wraps it. Convert that bounded serializer
        # failure into a stable ``EvidenceError`` before any temp file is created, so the prior
        # manifest bytes are preserved and no closed/complete persistence is claimed.
        try:
            encoded = canonical_bytes(manifest)
        except (ValueError, RecursionError):
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "manifest content exceeds the bounded JSON nesting depth during publication",
                    path=MANIFEST_NAME,
                    remediation="The prior manifest bytes are preserved and no closure is claimed.",
                )
            ) from None
        # The on-disk manifest is the canonical encoding plus its single trailing newline. The bound
        # is enforced on the exact bytes that would be written (AR-F04), so a manifest whose content
        # fits but whose final newline would overflow the caller bound is refused before any temp file
        # is created and the prior manifest bytes are preserved.
        if len(encoded) + 1 > self._limits.max_manifest_bytes:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"manifest exceeds max_manifest_bytes {self._limits.max_manifest_bytes}",
                    remediation="The prior manifest bytes are preserved and no closure is claimed.",
                )
            )
        self._tmp_counter += 1
        tmp_path = self._root / f"{MANIFEST_NAME}.tmp-{self._tmp_counter}"
        payload = encoded + b"\n"
        try:
            with tmp_path.open("wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp_path, self._root / MANIFEST_NAME)
        except OSError as error:
            try:
                tmp_path.unlink()
            except OSError:
                pass
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-IO-FAILURE",
                    f"atomic manifest publication failed: {error}",
                    remediation="The previous manifest bytes are preserved.",
                )
            ) from error
        try:
            directory = os.open(self._root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass


def _validate_inline_observation(record: Any, limits: EvidenceLimits):
    from .observation import validate_observation_record

    return validate_observation_record(record, pointer="/event/observation", limits=limits)
