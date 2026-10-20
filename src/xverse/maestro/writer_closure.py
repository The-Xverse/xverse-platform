"""Public writer/reader observations for one incomplete closure attempt."""

from dataclasses import asdict, dataclass
import hashlib
import re
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes


@dataclass(frozen=True)
class WriterClosure:
    acknowledged: bool
    last_acknowledged_state: str
    before_state: str | None
    after_state: str | None
    abort_usability: str
    after_usability: str
    abort_attempted: bool
    abort_completed: bool
    stage: str
    manifest_sha256: str | None
    durable_writer_state: str | None
    durable_recorded_status: str | None
    durable_assessed_status: str | None
    reader_diagnostics: tuple[str, ...]


def unresolved(last_acknowledged_state):
    return WriterClosure(
        acknowledged=False,
        last_acknowledged_state=last_acknowledged_state,
        before_state=None,
        after_state=None,
        abort_usability="unknown",
        after_usability="unknown",
        abort_attempted=False,
        abort_completed=False,
        stage="rpc-unresolved",
        manifest_sha256=None,
        durable_writer_state=None,
        durable_recorded_status=None,
        durable_assessed_status=None,
        reader_diagnostics=(),
    )


def close_writer(writer, root, check):
    """Runs only in the disposable original I/O owner; never inspects stream internals."""
    check()
    before = writer.writer_state
    attempted = completed = False
    usability = "unknown"
    stage = "not-open"
    if before == "open":
        try:
            writer.flush_buffer()
            check()
        except Exception:
            stage = "flush-error"
        else:
            usability, attempted = "usable", True
            try:
                writer.abort(
                    reason="Maestro run closure; lifecycle evidence remains incomplete"
                )
                check()
                completed, stage = True, "abort-completed"
            except Exception:
                stage = "abort-error"
    after = writer.writer_state
    manifest_sha = durable_state = recorded = assessed = None
    codes = ()
    try:
        check()
        reader = EvidenceStore.read_run(root)
        check()
        manifest = reader.manifest
        if manifest:
            manifest_sha = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
            state = manifest.get("writerState")
            durable_state = state if state in ("open", "closed", "failed") else None
        recorded = reader.recorded_evidence_status
        assessed = reader.assessed_evidence_status
        codes = tuple(d.code for d in reader.diagnostics)
    except Exception:
        codes = ("ML-CLOSURE-READER-UNRESOLVED",)
    check()
    return asdict(
        WriterClosure(
            acknowledged=True,
            last_acknowledged_state="unknown",
            before_state=before,
            after_state=after,
            abort_usability=usability,
            after_usability={"failed": "unusable", "closed": "not-applicable"}.get(
                after, "unknown"
            ),
            abort_attempted=attempted,
            abort_completed=completed,
            stage=stage,
            manifest_sha256=manifest_sha,
            durable_writer_state=durable_state,
            durable_recorded_status=recorded,
            durable_assessed_status=assessed,
            reader_diagnostics=codes,
        )
    )


def decode_closure(body, last_acknowledged_state):
    """Validate all fields before publishing any client-side factual state."""
    if type(body) is not dict or set(body) != set(WriterClosure.__dataclass_fields__):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    for name in ("before_state", "after_state"):
        if type(body[name]) is not str or body[name] not in (
            "open",
            "closed",
            "failed",
        ):
            raise ValueError("ML-CLOSURE-WRITER-ACK")
    if (
        body["acknowledged"] is not True
        or body["last_acknowledged_state"] != "unknown"
        or type(body["abort_attempted"]) is not bool
        or type(body["abort_completed"]) is not bool
        or body["abort_usability"] not in ("usable", "unknown")
        or body["stage"]
        not in ("not-open", "flush-error", "abort-error", "abort-completed")
        or body["abort_attempted"] != (body["abort_usability"] == "usable")
        or body["abort_completed"] != (body["stage"] == "abort-completed")
        or (body["abort_attempted"] and body["before_state"] != "open")
        or (body["abort_completed"] and body["after_state"] != "failed")
        or (body["stage"] == "flush-error" and body["abort_attempted"])
        or (body["stage"] == "not-open" and body["before_state"] == "open")
        or (
            body["stage"] in ("abort-error", "abort-completed")
            and not body["abort_attempted"]
        )
    ):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    expected_usability = {
        "failed": "unusable",
        "closed": "not-applicable",
        "open": "unknown",
    }[body["after_state"]]
    if body["after_usability"] != expected_usability:
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    digest = body["manifest_sha256"]
    if digest is not None and (
        type(digest) is not str or re.fullmatch("[a-f0-9]{64}", digest) is None
    ):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    if body["durable_writer_state"] not in (None, "open", "closed", "failed"):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    if body["durable_recorded_status"] not in (
        None,
        "complete",
        "incomplete",
        "unassessed",
    ):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    if body["durable_assessed_status"] not in (None, "complete", "incomplete"):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    if digest is None and (
        body["durable_writer_state"] is not None
        or body["durable_recorded_status"] is not None
    ):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    codes = body["reader_diagnostics"]
    if (
        type(codes) not in (tuple, list)
        or len(codes) > 128
        or any(
            type(c) is not str or re.fullmatch("[A-Z0-9-]{1,128}", c) is None
            for c in codes
        )
    ):
        raise ValueError("ML-CLOSURE-WRITER-ACK")
    return WriterClosure(
        **dict(
            body,
            last_acknowledged_state=last_acknowledged_state,
            reader_diagnostics=tuple(codes),
        )
    )
