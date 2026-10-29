"""Public, host-permitted retirement of verifiably released predecessor claims.

This module never signals a process or invokes a provider. It records a separate
admission fact; original runtime reads and original evidence are never rewritten.
"""

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time
import uuid

from xverse.argus import EvidenceLimits, EvidenceStore
from .inspection import ExecutionInputError, _DIGEST, _ID, canonical, sha256

MAX_SOURCE = 64 * 1024 * 1024
MAX_RECEIPT = 32768
_ALLOWED_LOSS = {"ARGUS2-LOSS-KNOWN-DROP", "ARGUS2-LOSS-DEGRADED-INTERVAL"}
_KINDS = {
    "run-start-requested",
    "phase-intent",
    "phase-outcome",
    "run-running",
    "runtime-observe-intent",
    "runtime-observation",
    "native-batch-import-intent",
    "native-batch-imported",
    "run-stop-requested",
    "run-cleanup-requested",
    "cleanup-intent",
    "cleanup-outcome",
    "run-terminal",
}


def _error(code):
    raise ExecutionInputError("MRX-" + code)


@dataclass(frozen=True)
class RecoveryProviderBinding:
    """Host-declared installation pin, not an Argus installation attestation."""

    provider_id: str
    installation_digest: str

    def __post_init__(self):
        if (
            type(self.provider_id) is not str
            or not _ID.fullmatch(self.provider_id)
            or type(self.installation_digest) is not str
            or not _DIGEST.fullmatch(self.installation_digest)
        ):
            _error("BINDING-INVALID")


def validate_bindings(bindings, provider_ids):
    if (
        type(bindings) is not tuple
        or len(bindings) > 128
        or any(type(b) is not RecoveryProviderBinding for b in bindings)
        or len({b.provider_id for b in bindings}) != len(bindings)
        or bindings
        and {b.provider_id for b in bindings} != set(provider_ids)
    ):
        _error("BINDING-INVALID")
    return tuple(sorted(bindings, key=lambda b: b.provider_id))


@dataclass(frozen=True)
class RecoveryInspection:
    canonical_bytes: bytes = field(repr=False)

    def to_data(self):
        return json.loads(self.canonical_bytes)

    @property
    def inspection_digest(self):
        return sha256(b"xverse.maestro.recovery-inspection.v1\0" + self.canonical_bytes)


@dataclass(frozen=True)
class RecoveryRetirement:
    canonical_bytes: bytes = field(repr=False)

    def to_data(self):
        return json.loads(self.canonical_bytes)


@dataclass(frozen=True)
class HostRecoveryPermit:
    """In-process trusted-host grant; never construct from imported project data."""

    permit_id: str
    inspection_digest: str
    host_binding_digest: str
    runtime_binding_digest: str
    recovery_binding_digest: str
    environment_id: str
    approval_reference: str
    not_before: float
    expires_at: float
    scope: str = "owned-simulation-recovery"

    def __post_init__(self):
        if (
            any(
                type(v) is not str or not _ID.fullmatch(v)
                for v in (self.permit_id, self.environment_id)
            )
            or any(
                type(v) is not str or not _DIGEST.fullmatch(v)
                for v in (
                    self.inspection_digest,
                    self.host_binding_digest,
                    self.runtime_binding_digest,
                    self.recovery_binding_digest,
                )
            )
            or type(self.approval_reference) is not str
            or not 1 <= len(self.approval_reference) <= 512
            or self.scope != "owned-simulation-recovery"
            or any(
                type(v) not in (int, float) or not math.isfinite(v)
                for v in (self.not_before, self.expires_at)
            )
            or not 0 < self.expires_at - self.not_before <= 300
        ):
            _error("PERMIT-INVALID")

    @property
    def digest(self):
        return sha256(canonical(self.__dict__))

    def validate(self, inspection, service, *, now=None):
        instant = time.time() if now is None else now
        if (
            type(instant) not in (int, float)
            or not math.isfinite(instant)
            or not self.not_before <= instant < self.expires_at
        ):
            _error("PERMIT-TIME")
        data = inspection.to_data()
        if (
            self.inspection_digest != inspection.inspection_digest
            or self.host_binding_digest != service.host.identity()
            or self.runtime_binding_digest != service.runtime_binding_digest
            or self.recovery_binding_digest != data["recoveryBindingDigest"]
            or self.environment_id != service.host.host_id
        ):
            _error("PERMIT-MISMATCH")


def _read(directory_fd, name, limit, *, missing=False):
    try:
        fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
        )
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                _error("SOURCE-SHAPE")
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            _error("SOURCE-LIMIT")
        return raw
    except FileNotFoundError:
        if missing:
            return None
        _error("SOURCE-UNAVAILABLE")
    except OSError:
        _error("SOURCE-UNAVAILABLE")


def _hash_stream(directory_fd, name):
    if type(name) is not str or not _ID.fullmatch(name):
        _error("SOURCE-PATH-UNSUPPORTED")
    total, hasher = 0, hashlib.sha256()
    try:
        fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
        )
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                _error("SOURCE-SHAPE")
            while chunk := stream.read(65536):
                total += len(chunk)
                if total > MAX_SOURCE:
                    _error("SOURCE-LIMIT")
                hasher.update(chunk)
    except OSError:
        _error("SOURCE-UNAVAILABLE")
    return total, "sha256:" + hasher.hexdigest()


def root_claims(service):
    service._check_root()
    names = []
    with os.scandir(service._root_fd) as entries:
        for count, entry in enumerate(entries, 1):
            if count > 1024:
                _error("ROOT-LIMIT")
            if entry.name.endswith(".claim.json"):
                run_id = entry.name[:-11]
                if not _ID.fullmatch(run_id):
                    _error("CLAIM-INVALID")
                names.append(run_id)
                if len(names) > 128:
                    _error("ROOT-LIMIT")
    return tuple(sorted(names))


def binding_digest(service):
    if not service._recovery_bindings:
        _error("BINDING-REQUIRED")
    return sha256(
        canonical(
            {
                "host": service.host.identity(),
                "runtime": service.runtime_binding_digest,
                "providers": [
                    (b.provider_id, b.installation_digest)
                    for b in service._recovery_bindings
                ],
            }
        )
    )


def _lifecycle(records, claim):
    events = []
    for record in records:
        event = record.get("extensions", {}).get("io.xverse.maestro.execution")
        if event is not None:
            if (
                type(event) is not dict
                or record.get("producerId") != "maestro-public-execution"
            ):
                _error("LIFECYCLE-SHAPE")
            events.append((record, event))
        elif record.get("producerId") == "maestro-public-execution":
            _error("LIFECYCLE-SHAPE")
    if not events:
        _error("LIFECYCLE-MISSING")
    phases, outcomes, cleanup_intents, cleanup_outcomes = {}, {}, {}, {}
    acquiring = []
    stop = None
    starts = []
    terminals = []
    preparation = None
    sources = None
    running = False
    active_cleanup = None
    terminal_event = None
    for index, (record, event) in enumerate(events, 1):
        kind = event.get("kind")
        if (
            type(record.get("producerSequence")) is not int
            or record.get("producerSequence") != index
            or record.get("eventKind") != "annotation"
            or record.get("schemaVersion") != "1.0"
            or set(event)
            != {
                "schemaVersion",
                "kind",
                "operationId",
                "runId",
                "planDigest",
                "inputSemanticDigest",
                "preparationDigest",
                "sourceDigests",
                "phaseId",
                "logicalId",
                "providerId",
                "operation",
                "outcome",
                "readinessKind",
                "resources",
                "observation",
            }
            or event.get("schemaVersion") != "1.0"
            or kind not in _KINDS
            or any(
                event.get(k) != claim[k]
                for k in ("runId", "planDigest", "inputSemanticDigest")
            )
            or record.get("runId") != claim["runId"]
        ):
            _error("LIFECYCLE-IDENTITY")
        phase_kind = kind in (
            "phase-intent",
            "phase-outcome",
            "cleanup-intent",
            "cleanup-outcome",
        )
        resources = event.get("resources")
        if (
            type(resources) is not list
            or len(resources) > 32
            or any(type(r) is not str or not _ID.fullmatch(r) for r in resources)
            or (kind != "phase-outcome" and resources)
            or (
                event.get("observation") is not None
                and type(event["observation"]) is not dict
            )
            or (kind != "phase-outcome" and event.get("readinessKind") is not None)
            or (
                not phase_kind
                and any(
                    event.get(k) is not None
                    for k in ("phaseId", "logicalId", "providerId", "operation")
                )
            )
        ):
            _error("LIFECYCLE-SHAPE")
        if index == 1:
            preparation = event.get("preparationDigest")
            sources = event.get("sourceDigests")
        if (
            type(preparation) is not str
            or not _DIGEST.fullmatch(preparation)
            or type(sources) is not dict
            or not sources
            or len(sources) > 128
            or any(
                type(v) is not str or not _DIGEST.fullmatch(v) for v in sources.values()
            )
            or event.get("preparationDigest") != preparation
            or event.get("sourceDigests") != sources
        ):
            _error("LIFECYCLE-IDENTITY")
        if kind == "run-start-requested":
            if (
                index != 1
                or record["eventId"] != claim["correlationId"]
                or event.get("operationId") != claim["operationId"]
            ):
                _error("LIFECYCLE-IDENTITY")
            starts.append(record["eventId"])
        elif record.get("correlationId") != claim["correlationId"]:
            _error("LIFECYCLE-IDENTITY")
        if kind in ("run-stop-requested", "run-cleanup-requested"):
            if stop is not None:
                _error("LIFECYCLE-ORDER")
            stop = event.get("operationId")
            if type(stop) is not str or not _ID.fullmatch(stop):
                _error("LIFECYCLE-SHAPE")
        elif kind.startswith("cleanup-") or kind == "run-terminal":
            if stop is None or event.get("operationId") != stop:
                _error("LIFECYCLE-ORDER")
        elif event.get("operationId") != claim["operationId"] or stop is not None:
            _error("LIFECYCLE-ORDER")
        phase = event.get("phaseId")
        if kind == "run-running":
            if running or len(outcomes) != len(phases):
                _error("LIFECYCLE-ORDER")
            running = True
        if kind == "phase-intent":
            if running or len(outcomes) != len(phases):
                _error("LIFECYCLE-ORDER")
            if (
                type(phase) is not str
                or not _ID.fullmatch(phase)
                or phase in phases
                or event.get("operation") not in ("prepare", "start", "ready")
                or type(event.get("logicalId")) is not str
                or not event["logicalId"].startswith("xdl://")
                or type(event.get("providerId")) is not str
                or not _ID.fullmatch(event["providerId"])
            ):
                _error("LIFECYCLE-SHAPE")
            phases[phase] = (record, event)
            if event["operation"] != "ready":
                acquiring.append(phase)
        elif kind in ("phase-outcome", "cleanup-intent", "cleanup-outcome"):
            if phase not in phases:
                _error("LIFECYCLE-MISSING")
            original, intent = phases[phase]
            if any(
                event.get(k) != intent.get(k)
                for k in ("phaseId", "logicalId", "providerId", "operation")
            ):
                _error("LIFECYCLE-IDENTITY")
            if kind == "phase-outcome":
                if (
                    phase in outcomes
                    or record.get("causationId") != original["eventId"]
                ):
                    _error("LIFECYCLE-ORDER")
                if (
                    event.get("outcome")
                    != {"prepare": "prepared", "start": "started", "ready": "ready"}[
                        intent["operation"]
                    ]
                ):
                    _error("LIFECYCLE-OUTCOME")
                if (
                    intent["operation"] == "ready"
                    and event.get("readinessKind")
                    not in ("liveness", "interface", "functional")
                ) or (
                    intent["operation"] != "ready"
                    and event.get("readinessKind") is not None
                ):
                    _error("LIFECYCLE-SHAPE")
                outcomes[phase] = record["eventId"]
            elif kind == "cleanup-intent":
                if (
                    active_cleanup is not None
                    or phase not in acquiring
                    or phase in cleanup_intents
                    or len(cleanup_intents) >= len(acquiring)
                ):
                    _error("LIFECYCLE-ORDER")
                if phase != acquiring[-1 - len(cleanup_intents)]:
                    _error("LIFECYCLE-ORDER")
                cleanup_intents[phase] = record["eventId"]
                active_cleanup = phase
            else:
                if (
                    active_cleanup != phase
                    or phase not in cleanup_intents
                    or phase in cleanup_outcomes
                    or record.get("causationId") != cleanup_intents[phase]
                    or event.get("outcome") != "released"
                ):
                    _error("CLEANUP-UNVERIFIED")
                cleanup_outcomes[phase] = record["eventId"]
                active_cleanup = None
        elif kind == "run-terminal":
            observation = event.get("observation")
            if (
                index != len(events)
                or event.get("outcome") not in ("stopped", "failed")
                or type(observation) is not dict
                or observation.get("cleanup") != "released"
            ):
                _error("CLEANUP-UNVERIFIED")
            if (
                set(observation)
                != {"failureCode", "cleanup", "observationTransportGaps"}
                or type(observation["observationTransportGaps"]) is not int
                or observation["observationTransportGaps"] < 0
                or (
                    observation["failureCode"] is not None
                    and (
                        type(observation["failureCode"]) is not str
                        or not _ID.fullmatch(observation["failureCode"])
                    )
                )
                or (event["outcome"] == "failed" and observation["failureCode"] is None)
            ):
                _error("LIFECYCLE-SHAPE")
            terminals.append(record["eventId"])
            terminal_event = event
    missing = [p for p in phases if p not in outcomes]
    failed_terminal = terminal_event and terminal_event["outcome"] == "failed"
    if (
        len(starts) != 1
        or len(terminals) != 1
        or active_cleanup is not None
        or set(cleanup_outcomes) != set(acquiring)
        or (
            missing
            and (
                not failed_terminal
                or len(missing) != 1
                or missing[0] != next(reversed(phases))
            )
        )
        or (terminal_event and terminal_event["outcome"] == "stopped" and not running)
    ):
        _error("LIFECYCLE-MISSING")
    return {
        "terminalEventId": terminals[0],
        "cleanupEventIds": list(cleanup_outcomes.values()),
        "acquiringPhaseCount": len(acquiring),
        "lifecycleRecordCount": len(events),
    }


def inspect(service, run_id):
    service._check_root()
    service._claim_path(run_id)
    recovery_binding = binding_digest(service)
    if run_id in service._runs or any(
        r.state not in ("stopped", "failed") or r.cleanup_state != "released"
        for r in service._runs.values()
    ):
        _error("OWNER-PRESENT")
    claim_raw = _read(service._root_fd, run_id + ".claim.json", 8192)
    claim = service._read_claim(run_id)
    if claim is not None and set(claim) != {
        "runId",
        "requestDigest",
        "operationId",
        "correlationId",
        "planDigest",
        "inputSemanticDigest",
    }:
        _error("CLAIM-INVALID")
    if claim is None or canonical(json.loads(claim_raw)) != canonical(claim):
        _error("SOURCE-CHANGED")
    fd = None
    try:
        fd = os.open(
            run_id + ".argus",
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=service._root_fd,
        )
        identity = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
        manifest_raw = _read(fd, "manifest.json", 1024 * 1024)
        manifest = json.loads(manifest_raw)
        if type(manifest) is not dict or manifest.get("artifacts") not in ([], None):
            _error("SOURCE-FORMAT-UNSUPPORTED")
        stream = manifest.get("eventStream") or {}
        size, stream_digest = _hash_stream(fd, stream.get("path"))
        source_root = Path("/proc/self/fd") / str(fd)
        reader = EvidenceStore.read_run(
            source_root,
            limits=EvidenceLimits(
                max_event_bytes=16384,
                max_events=4096,
                max_read_records=4096,
                max_causal_index_entries=4096,
                max_manifest_bytes=1024 * 1024,
                max_artifacts=64,
                max_text_length=2048,
                max_payload_bytes=4096,
            ),
        )
        if (
            reader.manifest.get("runId") != run_id
            or manifest.get("runId") != run_id
            or manifest.get("writerState") not in ("closed", "failed")
        ):
            _error("WRITER-UNVERIFIED")
        plan = (manifest.get("plan") or {}).get("semanticDigest") or {}
        if plan != {"algorithm": "sha256", "value": claim["planDigest"][7:]}:
            _error("PLAN-IDENTITY")
        records = reader.records()
        bad = [d.code for d in reader.diagnostics if d.code not in _ALLOWED_LOSS]
        if bad:
            _error("EVIDENCE-UNVERIFIED")
        lifecycle = _lifecycle(records, claim)
        if (
            _read(fd, "manifest.json", 1024 * 1024) != manifest_raw
            or _hash_stream(fd, stream.get("path")) != (size, stream_digest)
            or _read(service._root_fd, run_id + ".claim.json", 8192) != claim_raw
            or (
                os.stat(
                    run_id + ".argus", dir_fd=service._root_fd, follow_symlinks=False
                ).st_dev,
                os.stat(
                    run_id + ".argus", dir_fd=service._root_fd, follow_symlinks=False
                ).st_ino,
            )
            != identity
        ):
            _error("SOURCE-CHANGED")
        service._check_root()
        data = {
            "contractVersion": "1.0",
            "runId": run_id,
            "eligible": True,
            "reasons": [],
            "identity": claim,
            "claimDigest": sha256(claim_raw),
            "sourceWitness": sha256(
                canonical(
                    {
                        "manifestBytes": sha256(manifest_raw),
                        "streamBytes": size,
                        "streamDigest": stream_digest,
                        "records": records,
                        "argusIdentity": identity,
                    }
                )
            ),
            "hostBindingDigest": service.host.identity(),
            "runtimeBindingDigest": service.runtime_binding_digest,
            "recoveryBindingDigest": recovery_binding,
            "installationBinding": "host-declared; not Argus-attested",
            "writerState": manifest["writerState"],
            "recordedEvidenceStatus": reader.recorded_evidence_status,
            "assessedEvidenceStatus": reader.assessed_evidence_status,
            "diagnostics": [
                {"code": d.code, "category": d.category, "severity": d.severity}
                for d in reader.diagnostics
            ],
            "recordCount": len(records),
            **lifecycle,
        }
        raw = canonical(data)
        if len(raw) > MAX_RECEIPT:
            _error("SOURCE-LIMIT")
        return RecoveryInspection(raw)
    except ExecutionInputError:
        raise
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        _error("SOURCE-UNAVAILABLE")
    finally:
        if fd is not None:
            os.close(fd)


def _receipt_name(service, run_id):
    return run_id + "." + binding_digest(service)[7:] + ".retired.json"


def _load_receipt(service, run_id):
    raw = _read(
        service._root_fd, _receipt_name(service, run_id), MAX_RECEIPT, missing=True
    )
    if raw is None:
        return None
    try:
        value = json.loads(raw)
        if (
            type(value) is not dict
            or set(value)
            != {
                "contractVersion",
                "runId",
                "inspectionDigest",
                "inspection",
                "permitDigest",
                "authorization",
                "recoveryBindingDigest",
                "retiredAt",
                "receiptDigest",
            }
            or value.get("contractVersion") != "1.0"
            or value.get("runId") != run_id
            or canonical(value) != raw
            or not _DIGEST.fullmatch(value["permitDigest"])
            or not _DIGEST.fullmatch(value["inspectionDigest"])
            or value.get("receiptDigest")
            != sha256(
                canonical({k: v for k, v in value.items() if k != "receiptDigest"})
            )
        ):
            raise ValueError()
        authorization = HostRecoveryPermit(**value["authorization"])
        if authorization.digest != value["permitDigest"]:
            raise ValueError()
        authorization.validate(
            RecoveryInspection(canonical(value["inspection"])),
            service,
            now=value["retiredAt"],
        )
    except (ValueError, KeyError, TypeError, RecursionError):
        _error("RETIREMENT-INVALID")
    return value


def verified(service, run_id):
    if not service._recovery_bindings:
        return False
    value = _load_receipt(service, run_id)
    if value is None:
        return False
    current = inspect(service, run_id)
    data = current.to_data()
    if (
        value.get("inspectionDigest") != current.inspection_digest
        or value.get("inspection") != data
        or value.get("recoveryBindingDigest") != binding_digest(service)
    ):
        _error("RETIREMENT-STALE")
    return True


def retire(service, inspection, permit):
    if (
        type(inspection) is not RecoveryInspection
        or type(permit) is not HostRecoveryPermit
        or type(inspection.canonical_bytes) is not bytes
        or len(inspection.canonical_bytes) > MAX_RECEIPT
    ):
        _error("INPUT-INVALID")
    try:
        supplied = inspection.to_data()
        current = inspect(service, supplied["runId"])
    except ExecutionInputError:
        raise
    except (ValueError, KeyError, TypeError, RecursionError):
        _error("INPUT-INVALID")
    if current != inspection:
        _error("INSPECTION-STALE")
    permit.validate(current, service)
    old = _load_receipt(service, supplied["runId"])
    if old is not None:
        if (
            old.get("inspectionDigest") != current.inspection_digest
            or old.get("inspection") != current.to_data()
        ):
            _error("RETIREMENT-CONFLICT")
        try:
            os.fsync(service._root_fd)
        except OSError:
            _error("RETIREMENT-WRITE-FAILED")
        return RecoveryRetirement(canonical(old))
    root_claims(service)
    with os.scandir(service._root_fd) as entries_iterator:
        entries = [e.name for e in entries_iterator if e.name.endswith(".retired.json")]
    if (
        len(entries) >= 256
        or sum(n.startswith(supplied["runId"] + ".") for n in entries) >= 8
    ):
        _error("RETIREMENT-LIMIT")
    value = {
        "contractVersion": "1.0",
        "runId": supplied["runId"],
        "inspectionDigest": current.inspection_digest,
        "inspection": current.to_data(),
        "permitDigest": permit.digest,
        "authorization": dict(permit.__dict__),
        "recoveryBindingDigest": binding_digest(service),
        "retiredAt": time.time(),
    }
    value["receiptDigest"] = sha256(canonical(value))
    raw = canonical(value)
    if len(raw) > MAX_RECEIPT:
        _error("SOURCE-LIMIT")
    temporary = ".recovery-" + uuid.uuid4().hex + ".tmp"
    try:
        fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=service._root_fd,
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # Recheck exact source and permit after serialization and before publish.
        if inspect(service, supplied["runId"]) != current:
            _error("SOURCE-CHANGED")
        permit.validate(current, service)
        os.link(
            temporary,
            _receipt_name(service, supplied["runId"]),
            src_dir_fd=service._root_fd,
            dst_dir_fd=service._root_fd,
            follow_symlinks=False,
        )
        os.fsync(service._root_fd)
        service._check_root()
        return RecoveryRetirement(raw)
    except OSError:
        _error("RETIREMENT-WRITE-FAILED")
    finally:
        try:
            os.unlink(temporary, dir_fd=service._root_fd)
        except FileNotFoundError:
            pass
