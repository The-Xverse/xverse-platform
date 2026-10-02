"""Bounded, non-mutating evidence-stream recovery with pre-I/O path confinement.

Recovery resolves the confined real path of the manifest/stream, applies ``os.lstat`` to every
component **before** any open or parse, opens the confined regular file with ``O_NOFOLLOW``,
re-checks the descriptor with ``os.fstat`` (device/inode) and then streams the content under the
caller finite bounds. No unbounded ``read()``/``read_bytes()`` is applied to the manifest or the
evidence stream, and no byte is written: a truncated or non-canonical final line is reported as
``ARGUS2-CORRUPT-STREAM-TRUNCATED`` and is never counted, repaired or deleted
(``detailed-design.md`` sections 8.4, 8.5; invariants ``ARGUS2-INV-14``/``17``/``18``).
"""

from __future__ import annotations

import errno
import hashlib
import os
import re
import stat
from dataclasses import dataclass, field
from typing import Any

from .clocks import validate_clocks
from .diagnostics import EvidenceDiagnostic, diagnostic
from .limits import EvidenceLimits
from .observation import validate_observation_record
from .schema import (
    ANNOTATION_KEYS,
    EVENT_KEYS,
    EVENT_KINDS,
    canonical_bytes,
    parse_json_bounded,
    reject_unknown_keys,
    require_supported_major,
    validate_extensions,
)
from .snapshot import validate_snapshot

__all__ = [
    "EVENT_STREAM_NAME",
    "RecoveryResult",
    "open_confined",
    "read_confined_bytes",
    "recorded_path_diagnostics",
    "recover_stream",
    "validate_event_record",
]

EVENT_STREAM_NAME = "events.jsonl"
_RECORDED_PATH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")


@dataclass(frozen=True)
class RecoveryResult:
    """The bounded, non-mutating result of reading one evidence stream."""

    records: list[dict[str, Any]] = field(default_factory=list)
    diagnostics: tuple[EvidenceDiagnostic, ...] = ()
    truncated: bool = False
    byte_count: int = 0
    sha256: str = ""
    accepted_lines: int = 0
    over_read_bound: bool = False


def recorded_path_diagnostics(relative: Any) -> list[EvidenceDiagnostic]:
    """Validate a recorded run-relative path on its text before any filesystem access."""

    if not isinstance(relative, str) or relative == "":
        return [
            diagnostic(
                "ARGUS2-PATH-UNSAFE",
                "recorded path must be a non-empty run-relative POSIX path",
                path=relative if isinstance(relative, str) else None,
                remediation="Record a run-relative path inside the run root.",
            )
        ]
    if (
        relative.startswith(("/", "\\"))
        or "\\" in relative
        or "\x00" in relative
        or re.match(r"^[A-Za-z]:", relative) is not None
    ):
        return [
            diagnostic(
                "ARGUS2-PATH-ESCAPE",
                f"recorded path is absolute or contains a forbidden character: {relative!r}",
                path=relative,
                remediation="Recorded paths stay run-relative; they are never followed outside.",
            )
        ]
    segments = relative.split("/")
    if any(segment in ("", ".") for segment in segments) or ".." in segments:
        return [
            diagnostic(
                "ARGUS2-PATH-ESCAPE",
                f"recorded path contains a traversal/invalid segment: {relative!r}",
                path=relative,
                remediation="Remove the traversal segment; recorded paths stay confined.",
            )
        ]
    if _RECORDED_PATH_PATTERN.match(relative) is None:
        return [
            diagnostic(
                "ARGUS2-PATH-ESCAPE",
                f"recorded path is outside the frozen name pattern: {relative!r}",
                path=relative,
                remediation="Match ^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$.",
            )
        ]
    return []


def open_confined(root: Any, relative: Any) -> tuple[int | None, list[EvidenceDiagnostic]]:
    """Open a regular file through directory descriptors without following symlinks.

    Each component is inspected and opened relative to its already opened parent. Renaming or
    replacing a pathname during traversal cannot redirect the read through a different directory.
    """
    diagnostics = recorded_path_diagnostics(relative)
    if diagnostics:
        return None, diagnostics
    parent = None
    descriptor = None
    try:
        parent = os.open(os.path.realpath(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        segments = relative.split("/")
        for index, segment in enumerate(segments):
            inspected = os.stat(segment, dir_fd=parent, follow_symlinks=False)
            if stat.S_ISLNK(inspected.st_mode):
                return None, [diagnostic("ARGUS2-PATH-SYMLINK", "recorded path contains a symlink",
                    path=relative, remediation="Use regular files and directories inside the run root.")]
            final = index == len(segments) - 1
            if (final and not stat.S_ISREG(inspected.st_mode)) or (
                not final and not stat.S_ISDIR(inspected.st_mode)
            ):
                return None, [diagnostic("ARGUS2-PATH-NOT-REGULAR", "recorded path has an invalid file type",
                    path=relative, remediation="Read only confined regular files.")]
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if not final:
                flags |= os.O_DIRECTORY
            descriptor = os.open(segment, flags, dir_fd=parent)
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (inspected.st_dev, inspected.st_ino):
                return None, [diagnostic("ARGUS2-PATH-NOT-REGULAR", "recorded path changed during open",
                    path=relative, remediation="Retry only with stable evidence files.")]
            if final:
                result, descriptor = descriptor, None
                return result, []
            os.close(parent)
            parent, descriptor = descriptor, None
    except OSError as error:
        code = "ARGUS2-MISSING-ARTIFACT" if error.errno == errno.ENOENT else (
            "ARGUS2-PATH-SYMLINK" if error.errno == errno.ELOOP else "ARGUS2-IO-FAILURE")
        return None, [diagnostic(code, "recorded file could not be opened safely", path=relative,
            remediation="Resolve the filesystem failure; the evidence is never repaired on read.")]
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if parent is not None:
            os.close(parent)
    return None, [diagnostic("ARGUS2-PATH-UNSAFE", "recorded path has no file", path=relative)]


def read_confined_bytes(
    root: Any,
    relative: Any,
    *,
    max_bytes: int,
    bound_field: str,
) -> tuple[bytes | None, list[EvidenceDiagnostic]]:
    """Read at most ``max_bytes`` bytes of a confined regular file, bounded before parsing."""

    descriptor, diagnostics = open_confined(root, relative)
    if diagnostics:
        return None, diagnostics
    assert descriptor is not None
    chunks: list[bytes] = []
    remaining = max_bytes + 1
    try:
        while remaining > 0:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    except OSError as error:
        return None, [
            diagnostic(
                "ARGUS2-IO-FAILURE",
                f"confined read failed: {error}",
                path=relative,
                remediation="Resolve the filesystem fault.",
            )
        ]
    finally:
        os.close(descriptor)
    data = b"".join(chunks)
    if len(data) > max_bytes:
        return None, [
            diagnostic(
                "ARGUS2-BOUND-EXCEEDED",
                f"recorded file exceeds {bound_field} {max_bytes}",
                path=relative,
                remediation="The partial bytes are never parsed as trusted evidence.",
            )
        ]
    return data, []


def validate_event_record(
    record: Any, *, limits: EvidenceLimits, pointer: str = "/event"
) -> tuple[dict[str, Any] | None, list[EvidenceDiagnostic]]:
    """Validate one accepted event record against the complete closed frozen event schema."""

    diagnostics: list[EvidenceDiagnostic] = []
    if not isinstance(record, dict):
        return None, [
            diagnostic(
                "ARGUS2-CORRUPT-EVENT",
                f"event record at {pointer} is not a JSON object",
                pointer=pointer,
                remediation="Evidence bytes are never repaired.",
            )
        ]
    diagnostics.extend(
        require_supported_major(record.get("schemaVersion"), field="schemaVersion", pointer=f"{pointer}/schemaVersion")
    )
    if record.get("eventKind") not in EVENT_KINDS:
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                f"event kind {record.get('eventKind')!r} is outside the closed set",
                pointer=f"{pointer}/eventKind",
                remediation=f"Use one of {', '.join(EVENT_KINDS)}.",
            )
        )
    diagnostics.extend(reject_unknown_keys(record, EVENT_KEYS, pointer=pointer))
    for field_name in EVENT_KEYS:
        if field_name in record and record[field_name] is None:
            diagnostics.append(diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                f"present field {field_name!r} cannot be null",
                pointer=f"{pointer}/{field_name}",
                remediation="Omit an optional field or supply its valid declared value.",
            ))

    for field_name in ("runId", "eventId", "producerId"):
        value = record.get(field_name)
        if not isinstance(value, str) or value == "":
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-IDENTITY-MISSING",
                    f"required identity field {field_name!r} is missing on read",
                    pointer=f"{pointer}/{field_name}",
                    remediation="Required event identities are never inferred.",
                )
            )
        elif len(value) > limits.max_id_length:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"{field_name} exceeds max_id_length {limits.max_id_length}",
                    pointer=f"{pointer}/{field_name}",
                    remediation="Shorten the recorded identity.",
                )
            )

    ordinal = record.get("ingestionOrdinal")
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "ingestionOrdinal must be a positive integer",
                pointer=f"{pointer}/ingestionOrdinal",
                remediation="The writer assigns the ingestion ordinal.",
            )
        )

    producer_sequence = record.get("producerSequence")
    if producer_sequence is not None and (
        isinstance(producer_sequence, bool) or not isinstance(producer_sequence, int) or producer_sequence < 0
    ):
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "producerSequence must be a non-negative integer when declared",
                pointer=f"{pointer}/producerSequence",
                remediation="Preserve the declared sequence exactly.",
            )
        )
    for reference in ("correlationId", "causationId"):
        value = record.get(reference)
        if value is not None and (not isinstance(value, str) or value == ""):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"{reference} must be a non-empty string when declared",
                    pointer=f"{pointer}/{reference}",
                    remediation="Preserve the declared reference exactly.",
                )
            )

    if "annotation" in record:
        annotation = record.get("annotation")
        diagnostics.extend(reject_unknown_keys(annotation, ANNOTATION_KEYS, pointer=f"{pointer}/annotation"))
        if isinstance(annotation, dict) and not isinstance(annotation.get("text"), str):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "annotation text must be a string",
                    pointer=f"{pointer}/annotation/text",
                    remediation="Supply a caller-supplied note string.",
                )
            )

    diagnostics.extend(validate_extensions(record.get("extensions"), pointer=f"{pointer}/extensions", limits=limits))

    clocks = record.get("clocks")
    if clocks is not None:
        _preserved, clock_diagnostics = validate_clocks(clocks, pointer=f"{pointer}/clocks", limits=limits)
        diagnostics.extend(clock_diagnostics)

    event_kind = record.get("eventKind")
    if event_kind == "observation":
        if clocks is None:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-CLOCK-MISSING",
                    "an observation event requires explicit clocks",
                    pointer=f"{pointer}/clocks",
                    remediation="Absent means not declared and is never inferred.",
                )
            )
        observation = record.get("observation")
        if not isinstance(observation, dict):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-CORRUPT-RECORD-SHAPE",
                    "an observation event must carry an observation object",
                    pointer=f"{pointer}/observation",
                    remediation="A wrong-typed container is never iterated.",
                )
            )
        else:
            _validated, record_diagnostics = validate_observation_record(
                observation, pointer=f"{pointer}/observation", limits=limits
            )
            diagnostics.extend(record_diagnostics)
    elif "observation" in record:
        diagnostics.append(
            diagnostic(
                "ARGUS2-CORRUPT-RECORD-SHAPE",
                "observation is only valid for an observation-kind event",
                pointer=f"{pointer}/observation",
                remediation="A wrong-kind member is never trusted.",
            )
        )

    if event_kind == "snapshot":
        snapshot = record.get("snapshot")
        if not isinstance(snapshot, dict):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-CORRUPT-RECORD-SHAPE",
                    "a snapshot event must carry a snapshot object",
                    pointer=f"{pointer}/snapshot",
                    remediation="A wrong-typed container is never iterated.",
                )
            )
        else:
            _validated, snapshot_diagnostics = validate_snapshot(snapshot, limits=limits)
            diagnostics.extend(snapshot_diagnostics)
    elif "snapshot" in record:
        diagnostics.append(
            diagnostic(
                "ARGUS2-CORRUPT-RECORD-SHAPE",
                "snapshot is only valid for a snapshot-kind event",
                pointer=f"{pointer}/snapshot",
                remediation="A wrong-kind member is never trusted.",
            )
        )

    if diagnostics:
        return None, diagnostics
    return dict(record), []


def _advance_ordinal(record: dict[str, Any], expected: int) -> int:
    ordinal = record.get("ingestionOrdinal")
    if isinstance(ordinal, int) and not isinstance(ordinal, bool) and ordinal >= 1:
        return ordinal + 1
    return expected


def recover_stream(
    root: Any,
    *,
    limits: EvidenceLimits,
    manifest_run_id: str | None = None,
    relative: Any = EVENT_STREAM_NAME,
) -> RecoveryResult:
    """Read one evidence stream read-only under caller bounds; report damage, write nothing.

    ``relative`` is the exact run-relative stream path to confine and open. The reader passes the
    manifest-recorded ``eventStream.path`` so the recorded file -- not a hardcoded default -- is the
    one that is validated, read, hashed and compared; every diagnostic names that same recorded path
    (``AR-F01``, ``detailed-design.md`` section 8.5).
    """

    descriptor, diagnostics = open_confined(root, relative)
    if diagnostics:
        return RecoveryResult(records=[], diagnostics=tuple(diagnostics))
    assert descriptor is not None

    digest = hashlib.sha256()
    total = 0
    records: list[dict[str, Any]] = []
    collected: list[EvidenceDiagnostic] = []
    truncated = False
    over_read_bound = False
    expected_ordinal = 1
    seen_ids: set[str] = set()
    total_cap = limits.max_events * (limits.max_event_bytes + 1)
    line_number = 0
    diagnostics_suppressed = False

    def emit(item: EvidenceDiagnostic) -> None:
        """Emit one diagnostic, stopping at the caller diagnostic bound (``AR-F01``).

        One slot is reserved so a single bounded ``ARGUS2-BOUND-EXCEEDED`` can report the cap;
        damaged input can therefore never amplify diagnostics without limit.
        """

        nonlocal diagnostics_suppressed
        if len(collected) < limits.max_diagnostic_count - 1:
            collected.append(item)
        else:
            diagnostics_suppressed = True

    try:
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = None
            while True:
                raw = handle.readline(limits.max_event_bytes + 1)
                if raw == b"":
                    break
                line_number += 1
                if line_number > limits.max_events:
                    emit(diagnostic("ARGUS2-BOUND-EXCEEDED", "stream exceeds max_events",
                        path=relative, remediation="Read only the caller-bounded prefix."))
                    over_read_bound = True
                    break
                digest.update(raw)
                total += len(raw)
                if total > total_cap:
                    emit(
                        diagnostic(
                            "ARGUS2-BOUND-EXCEEDED",
                            f"evidence stream exceeds max_events {limits.max_events} at the derived total bound",
                            path=relative,
                            remediation="The read stops at the derived total stream bound.",
                        )
                    )
                    truncated = True
                    over_read_bound = True
                    break
                if len(raw) > limits.max_event_bytes and not raw.endswith(b"\n"):
                    emit(
                        diagnostic(
                            "ARGUS2-BOUND-EXCEEDED",
                            f"evidence line exceeds max_event_bytes {limits.max_event_bytes}",
                            path=relative,
                            remediation="The over-long line is never parsed as trusted evidence.",
                        )
                    )
                    truncated = True
                    over_read_bound = True
                    break
                if not raw.endswith(b"\n"):
                    truncated = True
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-STREAM-TRUNCATED",
                            "evidence stream ends in a truncated final record",
                            path=relative,
                            remediation="The truncated record is never counted, repaired or deleted.",
                        )
                    )
                    break

                line = raw[:-1]
                if line == b"":
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-STREAM-TRUNCATED",
                            "evidence stream contains a blank line",
                            path=relative,
                            remediation="Blank lines are never fabricated or dropped silently.",
                        )
                    )
                    continue
                try:
                    # The pre-decoded nesting bound refuses an adversarially deep line with a bounded
                    # ``ValueError`` before the recursive decoder can raise ``RecursionError``.
                    parsed = parse_json_bounded(line.decode("utf-8"))
                except (UnicodeDecodeError, ValueError, RecursionError):
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-STREAM-TRUNCATED",
                            f"evidence line {line_number} is not valid JSON",
                            path=relative,
                            remediation="Damaged lines are never repaired.",
                        )
                    )
                    continue
                if not isinstance(parsed, dict):
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-EVENT",
                            f"evidence line {line_number} is not a JSON object",
                            path=relative,
                            remediation="Non-object records are never trusted.",
                        )
                    )
                    continue

                record, record_diagnostics = validate_event_record(
                    parsed, limits=limits, pointer=f"/events/{line_number}"
                )
                if record_diagnostics:
                    for _diagnostic in record_diagnostics:
                        emit(_diagnostic)
                    expected_ordinal = _advance_ordinal(parsed, expected_ordinal)
                    continue

                try:
                    canonical = canonical_bytes(record)
                except (TypeError, ValueError, RecursionError):
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-STREAM-TRUNCATED",
                            f"evidence line {line_number} is not canonical JSON",
                            path=relative,
                            remediation="Damaged lines are never rewritten.",
                        )
                    )
                    expected_ordinal = _advance_ordinal(parsed, expected_ordinal)
                    continue
                if canonical != line:
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-STREAM-TRUNCATED",
                            f"evidence line {line_number} is not canonical JSON",
                            path=relative,
                            remediation="Damaged lines are never rewritten.",
                        )
                    )
                    expected_ordinal = _advance_ordinal(parsed, expected_ordinal)
                    continue

                if manifest_run_id is not None and record.get("runId") != manifest_run_id:
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-RUN-ID-MISMATCH",
                            f"event runId differs from the manifest runId on line {line_number}",
                            path=relative,
                            remediation="A run-ID mismatch excludes the record from the trusted result.",
                        )
                    )
                    expected_ordinal = _advance_ordinal(parsed, expected_ordinal)
                    continue

                event_id = record.get("eventId")
                if event_id in seen_ids:
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-DUPLICATE-EVENT",
                            f"duplicate eventId {event_id!r} within the run",
                            path=relative,
                            event_id=event_id if isinstance(event_id, str) else None,
                            remediation="A duplicate identity is excluded from the trusted result.",
                        )
                    )
                    expected_ordinal = _advance_ordinal(parsed, expected_ordinal)
                    continue

                ordinal = record.get("ingestionOrdinal")
                if ordinal != expected_ordinal:
                    emit(
                        diagnostic(
                            "ARGUS2-CORRUPT-ORDINAL",
                            f"ingestionOrdinal {ordinal!r} is not the strictly increasing expected value",
                            path=relative,
                            remediation="The ordinal is never presented as temporal or causal order.",
                        )
                    )
                    expected_ordinal = _advance_ordinal(parsed, expected_ordinal)
                    continue

                if isinstance(event_id, str):
                    seen_ids.add(event_id)
                expected_ordinal = ordinal + 1
                records.append(record)

                if len(records) >= limits.max_read_records:
                    extra = handle.readline(limits.max_event_bytes + 1)
                    if extra != b"":
                        emit(
                            diagnostic(
                                "ARGUS2-BOUND-EXCEEDED",
                                f"reader accepted records exceed max_read_records {limits.max_read_records}",
                                path=relative,
                                remediation="Increase max_read_records or read a bounded prefix.",
                            )
                        )
                        over_read_bound = True
                    break
    except OSError:
        emit(diagnostic(
            "ARGUS2-IO-FAILURE", "evidence stream could not be read",
            path=relative, remediation="Resolve the filesystem failure; no completeness is claimed.",
        ))
        over_read_bound = True
    finally:
        if descriptor is not None:
            os.close(descriptor)

    if diagnostics_suppressed:
        collected.append(
            diagnostic(
                "ARGUS2-BOUND-EXCEEDED",
                f"recovery diagnostics reached max_diagnostic_count {limits.max_diagnostic_count}",
                path=relative,
                remediation="Damaged input cannot amplify diagnostics beyond the caller bound.",
            )
        )

    return RecoveryResult(
        records=records,
        diagnostics=tuple(collected),
        truncated=truncated,
        byte_count=total,
        sha256=digest.hexdigest(),
        accepted_lines=len(records),
        over_read_bound=over_read_bound,
    )
