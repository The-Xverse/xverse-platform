"""Bounded read-only replay, verification and JSON/JSONL export.

The reader opens a run read-only, resolves and confines every recorded path **before** any I/O,
streams the manifest and evidence stream under the caller finite bounds, verifies the event stream,
every artifact and the declared obligations, and returns records in ingestion-ordinal order followed
by diagnostics and declared metric-input links. It never writes, never repairs, never invokes a
component, fault, lifecycle action, metric computation or evaluation oracle.

Two facts are kept separate: the *recorded* manifest claims and the reader's own *assessed*
completeness. Corrupt/truncated/loss evidence is exported as assessed ``incomplete`` and never as a
primary ``complete`` (``detailed-design.md`` sections 11.1, 12, 12.1 and 12.2).
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from xverse_xdl.experiment_plan import API_VERSION, PLAN_VERSION

from .artifacts import verify_index_entry
from .clocks import validate_clock
from .diagnostics import EvidenceDiagnostic, diagnostic
from .limits import EvidenceLimits
from .recovery import (
    EVENT_STREAM_NAME,
    read_confined_bytes,
    recorded_path_diagnostics,
    recover_stream,
)
from .schema import (
    MAX_JSON_NESTING,
    canonical_json,
    find_nonfinite,
    json_depth_exceeded,
    parse_json_bounded,
    parse_major,
    validate_extensions,
)
from .writer import evaluate_evidence

__all__ = ["MANIFEST_NAME", "EvidenceReader"]

MANIFEST_NAME = "manifest.json"

# Enclosing depth added by the read-only JSON export document around each admitted record: the root
# object plus the ``records`` array. A record admitted by the input parse bound can still exceed the
# bounded nesting maximum once wrapped here, so the export must account for this margin (``AR-F03``).
_EXPORT_WRAP_DEPTH = 2

# Closed mapping from a reader diagnostic to the assessed evidence reason it implies.
_REASON_BY_CODE: dict[str, str] = {
    "ARGUS2-CORRUPT-STREAM-TRUNCATED": "ARGUS2-REASON-TRUNCATED-STREAM",
    "ARGUS2-CORRUPT-ARTIFACT-HASH": "ARGUS2-REASON-MUTATED-ARTIFACT",
    "ARGUS2-CORRUPT-ARTIFACT-SIZE": "ARGUS2-REASON-MUTATED-ARTIFACT",
    "ARGUS2-MISSING-ARTIFACT": "ARGUS2-REASON-MISSING-ARTIFACT",
    "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED": "ARGUS2-REASON-UNSUPPORTED-SCHEMA",
    "ARGUS2-CORRUPT-MANIFEST-SHAPE": "ARGUS2-REASON-CORRUPT-MANIFEST",
    "ARGUS2-CORRUPT-EVENT": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-CORRUPT-RECORD-SHAPE": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-CORRUPT-RUN-ID-MISMATCH": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-CORRUPT-DUPLICATE-EVENT": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-CORRUPT-ORDINAL": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-SCHEMA-UNKNOWN-FIELD": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-INPUT-IDENTITY-MISSING": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-INPUT-NONFINITE": "ARGUS2-REASON-CORRUPT-EVENT",
    "ARGUS2-CLOCK-UNRESOLVED": "ARGUS2-REASON-CORRUPT-EVENT",
}


def _string_list(value: Any) -> list[str]:
    """Return the string members of a declared list, tolerating a malformed container.

    A damaged manifest may carry a scalar, object or ``null`` where the frozen schema declares an
    array; iterating it blindly would raise ``TypeError``. Malformed containers are treated as empty
    here so the reader keeps emitting only bounded stable diagnostics (``AR-F03``).
    """

    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


class EvidenceReader:
    """A read-only, immutable-snapshot view over one run root."""

    def __init__(
        self,
        *,
        root: Path,
        manifest: dict[str, Any] | None,
        records: list[dict[str, Any]],
        diagnostics: tuple[EvidenceDiagnostic, ...],
        limits: EvidenceLimits,
        assessed_status: str,
        assessed_reasons: list[str],
        recorded_status: str | None,
        recorded_reasons: list[str],
    ) -> None:
        self._root = Path(root)
        self._manifest = copy.deepcopy(manifest) if isinstance(manifest, dict) else {}
        self._records = copy.deepcopy(records)
        self._diagnostics = tuple(diagnostics)
        self._limits = limits
        self._assessed_status = assessed_status
        self._assessed_reasons = list(assessed_reasons)
        self._recorded_status = recorded_status
        self._recorded_reasons = list(recorded_reasons)

    @property
    def diagnostics(self) -> tuple[EvidenceDiagnostic, ...]:
        return self._diagnostics

    @property
    def manifest(self) -> dict[str, Any]:
        return copy.deepcopy(self._manifest)

    @property
    def recorded_evidence_status(self) -> str | None:
        return self._recorded_status

    @property
    def recorded_evidence_reasons(self) -> list[str]:
        return list(self._recorded_reasons)

    @property
    def assessed_evidence_status(self) -> str:
        return self._assessed_status

    @property
    def assessed_evidence_reasons(self) -> list[str]:
        return list(self._assessed_reasons)

    # Frozen external field-name aliases.
    @property
    def recordedEvidenceStatus(self) -> str | None:
        return self._recorded_status

    @property
    def recordedEvidenceReasons(self) -> list[str]:
        return list(self._recorded_reasons)

    @property
    def assessedEvidenceStatus(self) -> str:
        return self._assessed_status

    @property
    def assessedEvidenceReasons(self) -> list[str]:
        return list(self._assessed_reasons)

    def records(self) -> list[dict[str, Any]]:
        """Return accepted event records in ingestion-ordinal order (independent copies)."""

        return copy.deepcopy(self._records)

    def metric_inputs(self) -> list[dict[str, Any]]:
        """Return declared metric-input links; no metric value is computed."""

        declarations = self._manifest.get("metricInputs")
        if not isinstance(declarations, list):
            return []
        artifacts = self._manifest.get("artifacts")
        if not isinstance(artifacts, list):
            artifacts = []
        captured_artifacts = {
            entry.get("path")
            for entry in artifacts
            if isinstance(entry, dict) and isinstance(entry.get("path"), str)
        }
        captured_events = {
            record.get("eventId")
            for record in self._records
            if isinstance(record.get("eventId"), str)
        }
        results: list[dict[str, Any]] = []
        for declaration in declarations:
            if not isinstance(declaration, dict):
                continue
            sink_refs = [
                value
                for value in _string_list(declaration.get("evidenceSinkRefs", []))
                if value
            ]
            selection: list[str] = []
            for reference in sink_refs:
                if (reference in captured_artifacts or reference in captured_events) and reference not in selection:
                    selection.append(reference)
            complete = bool(sink_refs) and len(selection) == len(sink_refs)
            results.append(
                {
                    "metricId": declaration.get("metricId"),
                    "observerIds": _string_list(declaration.get("observerIds", [])),
                    "calculationRef": declaration.get("calculationRef"),
                    "unitSemantics": declaration.get("unitSemantics"),
                    "timeDomainIds": _string_list(declaration.get("timeDomainIds", [])),
                    "selection": sorted(selection),
                    "selectionStatus": "complete" if complete else "incomplete",
                }
            )
        results.sort(key=lambda item: str(item.get("metricId")))
        return results

    def _recorded_stream_relative(self) -> str:
        """Return the manifest-recorded event-stream path, or the canonical default.

        A manifest defect (non-object ``eventStream``) or a missing/non-string ``path`` falls back to
        the canonical name so an export diagnostic still names a bounded, stable path.
        """

        entry = self._manifest.get("eventStream")
        if isinstance(entry, dict):
            candidate = entry.get("path")
            if isinstance(candidate, str) and candidate:
                return candidate
        return EVENT_STREAM_NAME

    def export_json(self) -> str:
        """Return one canonical JSON document of the reconstructed evidence.

        A record admitted by the input parse bound can exceed the bounded nesting maximum once this
        export document wraps it (root object -> ``records`` array -> record). Such a record is
        withheld from the wrapped document and reported with a stable bounded diagnostic instead of
        raising an uncaught ``ValueError``/``RecursionError``, and the exported primary status is never
        ``complete`` (``AR-F02``, ``AR-F03``). Records that fit the wrapped document are preserved.
        """

        document = {
            "schemaVersion": "1.0",
            "runId": self._manifest.get("runId"),
            "writerState": self._manifest.get("writerState"),
            "evidenceStatus": self._assessed_status,
            "evidenceReasons": list(self._assessed_reasons),
            "recordedEvidenceStatus": self._recorded_status,
            "recordedEvidenceReasons": list(self._recorded_reasons),
            "assessedEvidenceStatus": self._assessed_status,
            "assessedEvidenceReasons": list(self._assessed_reasons),
            "records": copy.deepcopy(self._records),
            "metricInputs": self.metric_inputs(),
            "diagnostics": [item.to_data() for item in self._diagnostics],
        }
        if json_depth_exceeded(document):
            document["records"] = [
                record
                for record in self._records
                if not json_depth_exceeded(record, maximum=MAX_JSON_NESTING - _EXPORT_WRAP_DEPTH)
            ]
            document["evidenceStatus"] = "incomplete"
            document["assessedEvidenceStatus"] = "incomplete"
            if not any(
                isinstance(item, dict) and item.get("code") == "ARGUS2-BOUND-EXCEEDED"
                for item in document["diagnostics"]
            ):
                document["diagnostics"] = list(document["diagnostics"]) + [
                    diagnostic(
                        "ARGUS2-BOUND-EXCEEDED",
                        "an admitted event record exceeds the bounded JSON nesting depth once the export document wraps it",
                        path=self._recorded_stream_relative(),
                        remediation="The over-deep record is withheld from the wrapped export and reported as bounded incomplete evidence.",
                    ).to_data()
                ]
            document["assessedEvidenceReasons"] = sorted(
                set(document["assessedEvidenceReasons"]) | {"ARGUS2-REASON-CORRUPT-EVENT"}
            )
            document["evidenceReasons"] = list(document["assessedEvidenceReasons"])
        if json_depth_exceeded(document):
            # Last-resort bounded representation: a non-record member (e.g. a hostile declaration)
            # could still exceed the wrapping bound. Never raise from a read-only export.
            document["records"] = []
            document["evidenceStatus"] = "incomplete"
            document["assessedEvidenceStatus"] = "incomplete"
        return canonical_json(document)

    def export_jsonl(self) -> str:
        """Return the accepted event records as canonical JSONL."""

        if not self._records:
            return ""
        return "".join(f"{canonical_json(record)}\n" for record in self._records)


def _reader(
    *,
    root: Path,
    manifest: dict[str, Any] | None,
    records: list[dict[str, Any]],
    diagnostics: list[EvidenceDiagnostic],
    limits: EvidenceLimits,
    assessed_reasons: list[str],
    recorded_status: str | None = None,
    recorded_reasons: list[str] | None = None,
) -> EvidenceReader:
    reasons = sorted(set(assessed_reasons))
    status = "complete" if not reasons and not diagnostics else "incomplete"
    return EvidenceReader(
        root=root,
        manifest=manifest,
        records=records,
        diagnostics=tuple(_cap_diagnostics(diagnostics, limits.max_diagnostic_count)),
        limits=limits,
        assessed_status=status,
        assessed_reasons=reasons,
        recorded_status=recorded_status,
        recorded_reasons=list(recorded_reasons or []),
    )


def _stricter(left: EvidenceLimits, right: EvidenceLimits) -> EvidenceLimits:
    """Return the stricter (per-field minimum) of two limit sets."""

    fields = EvidenceLimits().to_data().keys()
    values = {field: min(getattr(left, field), getattr(right, field)) for field in fields}
    return EvidenceLimits(**values)


def _effective_limits(caller: EvidenceLimits | None, manifest: dict[str, Any]) -> tuple[EvidenceLimits, list[EvidenceDiagnostic]]:
    """Return the effective read limits and any echo diagnostics (caller stays authoritative)."""

    diagnostics: list[EvidenceDiagnostic] = []
    base = caller if caller is not None else EvidenceLimits()
    echo = manifest.get("limits")
    echo_limits: EvidenceLimits | None = None
    if echo is not None:
        if not isinstance(echo, dict):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-CORRUPT-MANIFEST-SHAPE",
                    "manifest limits echo is not an object",
                    path=MANIFEST_NAME,
                    remediation="The echo is recorded data only and never a new limit set.",
                )
            )
        else:
            try:
                echo_limits = EvidenceLimits.from_data(echo)
            except ValueError:
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-FIELD-INVALID",
                        "manifest limits echo is malformed and is not adopted",
                        path=MANIFEST_NAME,
                        remediation="The echo is recorded data only and never relaxes a caller bound.",
                    )
                )
    if echo_limits is None:
        return base, diagnostics
    return _stricter(base, echo_limits), diagnostics


def _cap_diagnostics(diagnostics: list[EvidenceDiagnostic], maximum: int) -> list[EvidenceDiagnostic]:
    if maximum is None or maximum <= 0:
        return []
    if len(diagnostics) <= maximum:
        return list(diagnostics)
    capped = list(diagnostics[: max(0, maximum - 1)])
    capped.append(
        diagnostic(
            "ARGUS2-BOUND-EXCEEDED",
            f"returned diagnostics are capped by max_diagnostic_count {maximum}",
            remediation="Damaged input cannot amplify diagnostics without limit.",
        )
    )
    return capped


def _dedupe(diagnostics: list[EvidenceDiagnostic]) -> list[EvidenceDiagnostic]:
    seen: set[tuple[str, str | None, str | None]] = set()
    result: list[EvidenceDiagnostic] = []
    for item in diagnostics:
        key = (item.code, item.path, item.eventId)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _manifest_metadata_diagnostics(manifest: dict[str, Any], limits: EvidenceLimits) -> list[EvidenceDiagnostic]:
    """Validate nested recorded metadata without coercing it or inferring absent declarations."""
    allowed = {
        "schemaVersion", "manifestVersion", "runId", "plan", "sourceByteProvenance", "writerState",
        "openedAt", "finalizedAt", "eventCount", "eventStream", "artifacts", "obligations",
        "evidenceStatus", "evidenceReasons", "limits", "extensions", "metricInputs", "clockDomains",
    }
    defect = bool(set(manifest) - allowed)

    def digest_valid(value: Any) -> bool:
        return (
            isinstance(value, dict)
            and set(value) == {"algorithm", "value"}
            and value.get("algorithm") == "sha256"
            and isinstance(value.get("value"), str)
            and re.fullmatch(r"[0-9a-f]{64}", value["value"]) is not None
        )

    plan = manifest["plan"]
    if (
        set(plan) != {"apiVersion", "profileVersion", "planVersion", "semanticDigest"}
        or plan.get("apiVersion") != API_VERSION
        or plan.get("planVersion") != PLAN_VERSION
        or not isinstance(plan.get("profileVersion"), str)
        or not plan["profileVersion"]
        or not digest_valid(plan.get("semanticDigest"))
    ):
        defect = True
    for source, digest in manifest["sourceByteProvenance"].items():
        if not source or not digest_valid(digest):
            defect = True

    paths = [entry.get("path") for entry in manifest["artifacts"] if isinstance(entry.get("path"), str)]
    if len(paths) != len(set(paths)):
        defect = True

    reason_codes = {
        "ARGUS2-REASON-" + suffix for suffix in (
            "TRUNCATED-STREAM", "MISSING-ARTIFACT", "MUTATED-ARTIFACT", "UNMET-OBLIGATION", "KNOWN-LOSS",
            "DEGRADED-INTERVAL", "INVALID-INTERVAL", "UNRESOLVED-CAUSATION", "UNCLOSED-INTERVAL",
            "UNSUPPORTED-SCHEMA", "WRITER-STATE", "CORRUPT-MANIFEST", "CORRUPT-EVENT",
        )
    }
    if set(manifest["evidenceReasons"]) - reason_codes or (
        manifest["evidenceStatus"] == "complete" and manifest["evidenceReasons"]
    ):
        defect = True

    metric_fields = {"metricId", "observerIds", "calculationRef", "unitSemantics", "timeDomainIds", "evidenceSinkRefs"}
    for metric in manifest.get("metricInputs", []):
        if not isinstance(metric, dict) or set(metric) != metric_fields:
            defect = True
            continue
        if any(not isinstance(metric[field], str) or not metric[field]
               for field in ("metricId", "calculationRef", "unitSemantics")):
            defect = True
        if any(not isinstance(metric[field], list)
               or any(not isinstance(value, str) or not value for value in metric[field])
               for field in ("observerIds", "timeDomainIds", "evidenceSinkRefs")):
            defect = True

    diagnostics: list[EvidenceDiagnostic] = []
    for field in ("openedAt", "finalizedAt"):
        if field in manifest:
            _, issues = validate_clock(manifest[field], pointer=f"/{field}", limits=limits)
            diagnostics.extend(issues)
    if "extensions" in manifest:
        if manifest["extensions"] is None:
            defect = True
        diagnostics.extend(validate_extensions(manifest["extensions"], pointer="/extensions", limits=limits))
    if defect:
        diagnostics.append(diagnostic(
            "ARGUS2-CORRUPT-MANIFEST-SHAPE", "nested manifest metadata violates the frozen contract",
            path=MANIFEST_NAME, remediation="Preserve complete, unique recorded identities and valid declarations.",
        ))
    return diagnostics


def read_run(root: Any, *, limits: EvidenceLimits | None = None) -> EvidenceReader:
    """Open one run read-only, verify manifest/stream/artifacts, and return a bounded view."""

    root_path = Path(root)
    caller = limits
    base = caller if caller is not None else EvidenceLimits()

    manifest_bytes, manifest_diagnostics = read_confined_bytes(
        root_path,
        MANIFEST_NAME,
        max_bytes=base.max_manifest_bytes,
        bound_field="max_manifest_bytes",
    )
    if manifest_diagnostics:
        reasons = [_REASON_BY_CODE.get(item.code, "ARGUS2-REASON-CORRUPT-MANIFEST") for item in manifest_diagnostics]
        return _reader(
            root=root_path,
            manifest=None,
            records=[],
            diagnostics=manifest_diagnostics,
            limits=base,
            assessed_reasons=reasons,
        )
    assert manifest_bytes is not None
    try:
        # ``parse_json_bounded`` rejects an adversarially deep document with a bounded ``ValueError``
        # before the recursive decoder runs, so a small deeply nested manifest can never raise an
        # uncaught ``RecursionError`` here (``AR-RVW-001``).
        manifest = parse_json_bounded(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return _reader(
            root=root_path,
            manifest=None,
            records=[],
            diagnostics=[
                diagnostic(
                    "ARGUS2-CORRUPT-MANIFEST-SHAPE",
                    "run manifest is not valid canonical JSON",
                    path=MANIFEST_NAME,
                    remediation="Damaged manifests are never repaired.",
                )
            ],
            limits=base,
            assessed_reasons=["ARGUS2-REASON-CORRUPT-MANIFEST"],
        )
    if not isinstance(manifest, dict):
        return _reader(
            root=root_path,
            manifest=None,
            records=[],
            diagnostics=[
                diagnostic(
                    "ARGUS2-CORRUPT-MANIFEST-SHAPE",
                    "run manifest is not a JSON object",
                    path=MANIFEST_NAME,
                    remediation="A wrong-typed manifest container is never trusted.",
                )
            ],
            limits=base,
            assessed_reasons=["ARGUS2-REASON-CORRUPT-MANIFEST"],
        )

    # AR-F01/AR-F03: json.loads accepts NaN/Infinity (and 1e400 parses to inf), so a damaged manifest
    # can carry a non-finite value at any depth. Reject it with a bounded stable diagnostic *before*
    # any assessment, limit handling or export, so no non-finite value can reach an allow_nan=False
    # serialization or be presented as assessable evidence. The recorded manifest facts are still
    # preserved separately.
    nonfinite = find_nonfinite(manifest, max_reports=1)
    if nonfinite:
        recorded_status = manifest.get("evidenceStatus")
        raw_reasons = manifest.get("evidenceReasons")
        if not isinstance(raw_reasons, list):
            raw_reasons = []
        return _reader(
            root=root_path,
            manifest=None,
            records=[],
            diagnostics=nonfinite,
            limits=base,
            assessed_reasons=["ARGUS2-REASON-CORRUPT-MANIFEST"],
            recorded_status=recorded_status if isinstance(recorded_status, str) else None,
            recorded_reasons=[value for value in raw_reasons if isinstance(value, str)],
        )

    recorded_status = manifest.get("evidenceStatus")
    recorded_reasons = manifest.get("evidenceReasons")
    if not isinstance(recorded_reasons, list):
        recorded_reasons = []
    recorded_reasons = [value for value in recorded_reasons if isinstance(value, str)]

    if parse_major(manifest.get("schemaVersion")) != 1:
        return _reader(
            root=root_path,
            manifest=manifest,
            records=[],
            diagnostics=[
                diagnostic(
                    "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED",
                    "manifest schemaVersion major is not supported",
                    path=MANIFEST_NAME,
                    remediation="Unsupported manifests are reported with a bounded partial result.",
                )
            ],
            limits=base,
            assessed_reasons=["ARGUS2-REASON-UNSUPPORTED-SCHEMA"],
            recorded_status=recorded_status if isinstance(recorded_status, str) else None,
            recorded_reasons=recorded_reasons,
        )

    effective, echo_diagnostics = _effective_limits(caller, manifest)
    diagnostics: list[EvidenceDiagnostic] = list(echo_diagnostics)
    assessed_reasons: list[str] = [
        _REASON_BY_CODE.get(item.code, "ARGUS2-REASON-CORRUPT-MANIFEST") for item in echo_diagnostics
    ]

    # Frozen manifest member shapes.
    shape_defect = False
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or any(not isinstance(entry, dict) for entry in artifacts):
        shape_defect = True
    obligations = manifest.get("obligations")
    if not isinstance(obligations, list):
        shape_defect = True
    metric_inputs = manifest.get("metricInputs")
    if "metricInputs" in manifest and not isinstance(metric_inputs, list):
        shape_defect = True
    stream_entry = manifest.get("eventStream")
    if not isinstance(stream_entry, dict):
        shape_defect = True
    else:
        stream_bytes = stream_entry.get("bytes")
        stream_sha = stream_entry.get("sha256")
        if (
            set(stream_entry) != {"path", "mediaType", "schemaVersion", "bytes", "sha256"}
            or not isinstance(stream_entry.get("path"), str)
            or not stream_entry["path"]
            or stream_entry.get("mediaType") != "application/x-ndjson"
            or parse_major(stream_entry.get("schemaVersion")) != 1
            or isinstance(stream_bytes, bool)
            or not isinstance(stream_bytes, int)
            or stream_bytes < 0
            or not isinstance(stream_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", stream_sha) is None
        ):
            shape_defect = True
    clock_domains = manifest.get("clockDomains")
    if "clockDomains" in manifest and (not isinstance(clock_domains, list)
            or any(not isinstance(value, str) or not value for value in clock_domains)):
        shape_defect = True
    for field in ("limits", "plan", "sourceByteProvenance"):
        if not isinstance(manifest.get(field), dict):
            shape_defect = True
    raw_reasons = manifest.get("evidenceReasons")
    if not isinstance(raw_reasons, list) or any(not isinstance(value, str) for value in raw_reasons):
        shape_defect = True
    run_id = manifest.get("runId")
    if not isinstance(run_id, str) or not run_id or len(run_id) > effective.max_id_length:
        shape_defect = True
    event_count = manifest.get("eventCount")
    if isinstance(event_count, bool) or not isinstance(event_count, int) or event_count < 0:
        shape_defect = True
    if manifest.get("evidenceStatus") not in ("unassessed", "complete", "incomplete"):
        shape_defect = True
    if parse_major(manifest.get("manifestVersion")) != 1:
        shape_defect = True
    if shape_defect:
        diagnostics.append(
            diagnostic(
                "ARGUS2-CORRUPT-MANIFEST-SHAPE",
                "a frozen manifest member has the wrong container type",
                path=MANIFEST_NAME,
                remediation="The container is never coerced, iterated or indexed assuming the wrong type.",
            )
        )
        return _reader(
            root=root_path,
            manifest=manifest,
            records=[],
            diagnostics=_dedupe(diagnostics),
            limits=effective,
            assessed_reasons=sorted(set(assessed_reasons) | {"ARGUS2-REASON-CORRUPT-MANIFEST"}),
            recorded_status=recorded_status if isinstance(recorded_status, str) else None,
            recorded_reasons=recorded_reasons,
        )

    # Reject excessive collections before invoking filesystem verification or nested validators.
    if len(artifacts) > effective.max_artifacts or len(obligations) > effective.max_obligations:
        return _reader(root=root_path, manifest=manifest, records=[], limits=effective,
            diagnostics=[diagnostic("ARGUS2-BOUND-EXCEEDED", "manifest collection exceeds caller bounds",
                path=MANIFEST_NAME, remediation="Reduce the collection or supply explicit finite bounds.")],
            assessed_reasons=["ARGUS2-REASON-CORRUPT-MANIFEST"],
            recorded_status=recorded_status, recorded_reasons=recorded_reasons)

    # Apply the same obligation contract on admission and read; damaged obligations are never dropped.
    from .api import _validate_obligations, _validate_run_id

    metadata_diagnostics = _manifest_metadata_diagnostics(manifest, effective)
    metadata_diagnostics.extend(_validate_run_id(run_id, effective))
    diagnostics.extend(metadata_diagnostics[:effective.max_diagnostic_count])
    if metadata_diagnostics:
        assessed_reasons.append("ARGUS2-REASON-CORRUPT-MANIFEST")
    _, obligation_diagnostics = _validate_obligations(obligations, effective)
    diagnostics.extend(obligation_diagnostics[:effective.max_diagnostic_count])
    if obligation_diagnostics:
        assessed_reasons.append("ARGUS2-REASON-CORRUPT-MANIFEST")

    # Confined, bounded evidence stream. The reader confines and opens the exact manifest-recorded
    # ``eventStream.path`` (never a hardcoded default) and compares the recorded size/SHA-256 with
    # that same file, so a missing, wrong, symlinked or noncanonical recorded path is reported
    # incomplete rather than silently read from another file (``AR-F01``).
    records: list[dict[str, Any]] = []
    recovery = None
    effective_stream_relative: str = EVENT_STREAM_NAME
    if isinstance(stream_entry, dict):
        stream_relative = stream_entry.get("path", EVENT_STREAM_NAME)
        if isinstance(stream_relative, str) and stream_relative != "":
            effective_stream_relative = stream_relative
        path_diagnostics = recorded_path_diagnostics(stream_relative)
        if path_diagnostics:
            diagnostics.extend(path_diagnostics)
            assessed_reasons.extend("ARGUS2-REASON-CORRUPT-EVENT" for _ in path_diagnostics)
        else:
            recovery = recover_stream(
                root_path,
                limits=effective,
                manifest_run_id=manifest.get("runId"),
                relative=stream_relative,
            )
            records = list(recovery.records)
            diagnostics.extend(recovery.diagnostics)
            assessed_reasons.extend(
                _REASON_BY_CODE.get(item.code, "ARGUS2-REASON-CORRUPT-EVENT") for item in recovery.diagnostics
            )
            recorded_bytes = stream_entry.get("bytes")
            recorded_sha = stream_entry.get("sha256")
            structural = {
                item.code
                for item in recovery.diagnostics
                if item.code
                in (
                    "ARGUS2-MISSING-ARTIFACT",
                    "ARGUS2-PATH-ESCAPE",
                    "ARGUS2-PATH-SYMLINK",
                    "ARGUS2-PATH-NOT-REGULAR",
                    "ARGUS2-IO-FAILURE",
                )
            }
            if not recovery.over_read_bound and not structural:
                if recorded_bytes != recovery.byte_count:
                    diagnostics.append(
                        diagnostic(
                            "ARGUS2-CORRUPT-ARTIFACT-SIZE",
                            "evidence stream size differs from the recorded value",
                            path=str(stream_relative),
                            remediation="The recorded size is authoritative.",
                        )
                    )
                    assessed_reasons.append("ARGUS2-REASON-MUTATED-ARTIFACT")
                if recorded_sha != recovery.sha256:
                    diagnostics.append(
                        diagnostic(
                            "ARGUS2-CORRUPT-ARTIFACT-HASH",
                            "evidence stream content hash differs from the recorded value",
                            path=str(stream_relative),
                            remediation="The recorded hash is authoritative.",
                        )
                    )
                    assessed_reasons.append("ARGUS2-REASON-MUTATED-ARTIFACT")
    else:
        diagnostics.append(
            diagnostic(
                "ARGUS2-MISSING-ARTIFACT",
                "manifest carries no event stream entry",
                path=MANIFEST_NAME,
                remediation="The stream entry is required.",
            )
        )
        assessed_reasons.append("ARGUS2-REASON-MISSING-ARTIFACT")

    # AR-F03 enclosing depth: a record admitted by the input parse bound can still exceed the bounded
    # nesting maximum once the read-only export document wraps it (root object -> ``records`` array ->
    # record). Flag it here as bounded incomplete evidence -- the admitted record stays in the trusted
    # result, but the wrapped export withholds it with one stable diagnostic instead of raising.
    if recovery is not None and not recovery.over_read_bound and event_count != len(records):
        diagnostics.append(diagnostic("ARGUS2-CORRUPT-MANIFEST-SHAPE",
            "manifest eventCount differs from the verified event count", path=MANIFEST_NAME,
            remediation="The recorded count is preserved; incomplete evidence is reported."))
        assessed_reasons.append("ARGUS2-REASON-CORRUPT-MANIFEST")
    for record in records:
        candidate = record if isinstance(record, dict) else None
        if candidate is not None and json_depth_exceeded(
            candidate, maximum=MAX_JSON_NESTING - _EXPORT_WRAP_DEPTH
        ):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    "an admitted event record exceeds the bounded JSON nesting depth once the export document wraps it",
                    path=effective_stream_relative,
                    event_id=candidate.get("eventId") if isinstance(candidate.get("eventId"), str) else None,
                    remediation="The record is withheld from the wrapped export and reported as bounded incomplete evidence.",
                )
            )
            assessed_reasons.append("ARGUS2-REASON-CORRUPT-EVENT")
            break

    # Declared clock domains remain explicit; an undeclared domain is never inferred.
    declared_domains = {value for value in clock_domains if isinstance(value, str)} if isinstance(
        clock_domains, list
    ) else set()
    if declared_domains:
        for event in records:
            clocks = event.get("clocks")
            if not isinstance(clocks, dict):
                continue
            for clock in clocks.values():
                if (
                    isinstance(clock, dict)
                    and isinstance(clock.get("domain"), str)
                    and clock["domain"] not in declared_domains
                ):
                    diagnostics.append(
                        diagnostic(
                            "ARGUS2-CLOCK-UNRESOLVED",
                            f"clock domain {clock['domain']!r} was not declared by the caller",
                            event_id=event.get("eventId"),
                            remediation="The undeclared relation stays explicit and is never inferred.",
                        )
                    )
                    assessed_reasons.append("ARGUS2-REASON-CORRUPT-EVENT")
                    break

    # Confined, bounded artifact re-verification (pre-I/O symlink/regular checks).
    artifact_diagnostics: list[EvidenceDiagnostic] = []
    for entry in artifacts:
        artifact_diagnostics.extend(verify_index_entry(root_path, entry))
    diagnostics.extend(artifact_diagnostics)
    assessed_reasons.extend(
        _REASON_BY_CODE.get(item.code, "ARGUS2-REASON-MUTATED-ARTIFACT") for item in artifact_diagnostics
    )

    writer_state = manifest.get("writerState")
    if writer_state not in ("open", "closed", "failed"):
        writer_state = "failed"
        diagnostics.append(
            diagnostic(
                "ARGUS2-STATE-ILLEGAL-TRANSITION",
                "manifest writerState is absent or outside the frozen machine",
                path=MANIFEST_NAME,
                remediation="An unknown writer state is treated as incomplete.",
            )
        )
        assessed_reasons.append("ARGUS2-REASON-WRITER-STATE")

    recovery_diagnostics = tuple(recovery.diagnostics) if recovery is not None else ()
    truncated = recovery.truncated if recovery is not None else False
    _status, evaluated_reasons, evaluated_diagnostics = evaluate_evidence(
        records,
        obligations=[item for item in obligations if isinstance(item, dict)],
        artifact_entries=[item for item in artifacts if isinstance(item, dict)],
        artifact_diagnostics=tuple(artifact_diagnostics),
        recovery_diagnostics=recovery_diagnostics,
        truncated=truncated,
        writer_state=writer_state,
        limits=effective,
    )
    diagnostics.extend(evaluated_diagnostics)
    assessed_reasons.extend(evaluated_reasons)

    if writer_state != "closed":
        assessed_reasons.append("ARGUS2-REASON-WRITER-STATE")

    for item in diagnostics:
        mapped = _REASON_BY_CODE.get(item.code)
        if mapped is not None:
            assessed_reasons.append(mapped)
    if any(item.path == effective_stream_relative for item in diagnostics):
        assessed_reasons.append("ARGUS2-REASON-CORRUPT-EVENT")
    if any(item.path == MANIFEST_NAME for item in diagnostics):
        assessed_reasons.append("ARGUS2-REASON-CORRUPT-MANIFEST")

    # Cap the raw diagnostics before de-duplication so damaged input cannot amplify them.
    capped = _cap_diagnostics(diagnostics, effective.max_diagnostic_count)
    deduped = _dedupe(capped)
    if deduped and not assessed_reasons:
        assessed_reasons.append("ARGUS2-REASON-CORRUPT-EVENT")
    return _reader(
        root=root_path,
        manifest=manifest,
        records=records,
        diagnostics=deduped,
        limits=effective,
        assessed_reasons=assessed_reasons,
        recorded_status=recorded_status if isinstance(recorded_status, str) else None,
        recorded_reasons=recorded_reasons,
    )
