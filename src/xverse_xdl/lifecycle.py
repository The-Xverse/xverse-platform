"""Owned M3 fixture lifecycle with durable evidence and explicit execution permits."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import signal
import subprocess
import threading
import time
import uuid
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .catalog import LifecyclePlan, ProcessAction
from .models import FrozenMap, freeze

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platforms
    fcntl = None

_SENSITIVE_KEY = re.compile(r"password|passwd|secret|token|credential|address|path|directory|asset", re.I)
_MUTATION_LOCKS: dict[tuple[str, str], threading.Lock] = {}
_MUTATION_LOCKS_GUARD = threading.Lock()


class EvidenceWriteError(RuntimeError):
    """Report a durable evidence read, ordering, locking, or write failure."""

    pass


@dataclass(frozen=True)
class LifecycleDiagnostic:
    """Stable lifecycle failure data suitable for operator-facing reporting."""

    code: str
    severity: str
    phase: str
    selected_identity: str
    message: str
    correction: str


class LifecycleError(RuntimeError):
    """Lifecycle exception carrying a structured stable diagnostic."""

    def __init__(self, diagnostic: LifecycleDiagnostic) -> None:
        """Initialize the exception from a structured diagnostic."""

        super().__init__(f"{diagnostic.code}: {diagnostic.message}")
        self.diagnostic = diagnostic


def _lifecycle_error(
    code: str, phase: str, plan: LifecyclePlan, message: str, correction: str,
) -> LifecycleError:
    """Create a lifecycle failure anchored to the selected catalog identity."""

    return LifecycleError(LifecycleDiagnostic(
        code, "error", phase, plan.catalog_identity, message, correction,
    ))


@dataclass(frozen=True)
class ExecutionPermit:
    """Time-bounded single-use authorization bound to one exact lifecycle plan."""

    permit_id: str
    nonce: str
    plan_digest: str
    catalog_identity: str
    environment_identity: str
    permitted_actions: tuple[str, ...]
    approval_evidence_ref: str
    issuer_label: str
    operation_classes: tuple[str, ...]
    exclusions: tuple[str, ...]
    public_safety_classification: str
    not_before: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        """Reject incomplete, ambiguous, or invalid permit declarations."""

        required = (
            self.permit_id, self.nonce, self.plan_digest, self.catalog_identity,
            self.environment_identity, self.approval_evidence_ref, self.issuer_label,
        )
        if any(not value.strip() for value in required):
            raise ValueError("execution permit identifiers and approval evidence must be non-empty")
        if not self.permitted_actions or len(set(self.permitted_actions)) != len(self.permitted_actions):
            raise ValueError("execution permit actions must be non-empty and unique")
        if not self.operation_classes or len(set(self.operation_classes)) != len(self.operation_classes):
            raise ValueError("execution permit operation classes must be non-empty and unique")
        if self.public_safety_classification not in {"public-safe", "restricted-local"}:
            raise ValueError("execution permit public-safety classification is invalid")
        if self.not_before.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("execution permit times must be timezone-aware")
        if self.not_before >= self.expires_at:
            raise ValueError("execution permit validity interval is empty")

    def validate(self, plan: LifecyclePlan, now: datetime) -> None:
        """Validate temporal, identity, action, and operation bindings.

        @raises LifecycleError If the permit does not authorize the exact plan at *now*.
        """

        if self.not_before.tzinfo is None or self.expires_at.tzinfo is None or now.tzinfo is None:
            raise _lifecycle_error("XVERSE-PERMIT-TIME", "authorization", plan, "permit times must be timezone-aware", "Use UTC-aware validity bounds.")
        if now < self.not_before:
            raise _lifecycle_error("XVERSE-PERMIT-NOT-YET-VALID", "authorization", plan, "execution permit is not yet valid", "Wait for notBefore or issue a correct permit.")
        if now >= self.expires_at:
            raise _lifecycle_error("XVERSE-PERMIT-EXPIRED", "authorization", plan, "execution permit is expired", "Issue a new single-use permit.")
        expected = {
            "plan digest": (self.plan_digest, plan.digest),
            "catalog identity": (self.catalog_identity, plan.catalog_identity),
            "environment identity": (self.environment_identity, plan.environment_identity),
        }
        mismatch = next((label for label, values in expected.items() if values[0] != values[1]), None)
        if mismatch:
            raise _lifecycle_error("XVERSE-PERMIT-MISMATCH", "authorization", plan, f"execution permit {mismatch} mismatch", "Bind the permit to this exact plan and environment.")
        action_ids = {item.action_id for item in plan.actions}
        if not action_ids.issubset(set(self.permitted_actions)):
            raise _lifecycle_error("XVERSE-PERMIT-ACTIONS", "authorization", plan, "execution permit action set mismatch", "Permit every action in the exact plan.")
        operation_classes = {item.operation for item in plan.actions}
        if not operation_classes.issubset(set(self.operation_classes)):
            raise _lifecycle_error("XVERSE-PERMIT-OPERATIONS", "authorization", plan, "execution permit operation classes mismatch", "Permit every operation class in the exact plan.")


@dataclass(frozen=True)
class IsolationAttestation:
    """Explicit trust input describing the caller-provided execution boundary."""

    attestation_id: str
    execution_root: str
    filesystem_boundary: str
    legacy_checkout_immutable: bool
    network_boundary: str

    def __post_init__(self) -> None:
        """Require an absolute isolated root and immutable legacy checkout declaration."""

        if not self.attestation_id.strip() or not Path(self.execution_root).is_absolute():
            raise ValueError("isolation attestation identity and execution root are required")
        if self.filesystem_boundary != "isolated" or not self.legacy_checkout_immutable:
            raise ValueError("process execution requires an isolated filesystem and immutable legacy checkout")


@dataclass(frozen=True)
class OwnedResourceHandle:
    """Opaque provider-issued authority over one exact started resource."""

    opaque_id: str
    execution_id: str
    action_id: str
    provider_id: str
    provider_kind: str
    resource_identity: str = field(repr=False)


@dataclass(frozen=True)
class EvidenceRecord:
    """Append-only intent, outcome, or observation record for one lifecycle action."""

    kind: str
    sequence: int
    timestamp: str
    execution_id: str
    action_id: str
    catalog_identity: str
    plan_digest: str
    permit_id: str | None
    permit_nonce: str | None
    status: str
    environment_identity: str
    resource_revisions: FrozenMap
    artifact_digests: tuple[str, ...]
    selection: FrozenMap
    permit_issuer_label: str | None = None
    permit_operation_classes: tuple[str, ...] = ()
    permit_exclusions: tuple[str, ...] = ()
    permit_public_safety_classification: str | None = None
    handle_id: str | None = None
    handle_action_id: str | None = None
    handle_provider_id: str | None = None
    handle_provider_kind: str | None = None
    handle_resource_identity: str | None = field(default=None, repr=False)
    details: FrozenMap = field(default_factory=FrozenMap)


@dataclass(frozen=True)
class LifecycleResult:
    """Current lifecycle status and its exact owned handle when available."""

    execution_id: str
    status: str
    handle: OwnedResourceHandle | None


class EvidenceJournal(Protocol):
    """Storage contract for ordered evidence and single-use permit checks."""

    @property
    def records(self) -> tuple[EvidenceRecord, ...]:
        """Return a consistent ordered evidence snapshot."""

        ...

    def append(self, record: EvidenceRecord) -> None:
        """Append one record while preserving contiguous sequence numbers."""

        ...

    def permit_consumed(self, permit_id: str, nonce: str | None = None) -> bool:
        """Return whether an intent consumed the permit ID or optional nonce."""

        ...

    def public_records(self) -> tuple[dict[str, Any], ...]:
        """Return redacted evidence records safe for public reporting."""

        ...


def _record_data(record: EvidenceRecord, *, public: bool = False) -> dict[str, Any]:
    """Serialize an evidence record, optionally applying public redaction."""

    details = _public_value(record.details) if public else _plain(record.details)
    return {
        "actionId": record.action_id,
        "catalogIdentity": record.catalog_identity,
        "details": details,
        "executionId": record.execution_id,
        "handleId": "withheld" if public and record.handle_id else record.handle_id,
        "handleActionId": record.handle_action_id,
        "handleProviderId": record.handle_provider_id,
        "handleProviderKind": record.handle_provider_kind,
        "handleResourceIdentity": (
            "withheld" if public and record.handle_resource_identity else record.handle_resource_identity
        ),
        "kind": record.kind,
        "permitId": record.permit_id,
        "permitNonce": "withheld" if public and record.permit_nonce else record.permit_nonce,
        "planDigest": record.plan_digest,
        "environmentIdentity": record.environment_identity,
        "resourceRevisions": _plain(record.resource_revisions),
        "artifactDigests": list(record.artifact_digests),
        "selection": _public_value(record.selection) if public else _plain(record.selection),
        "permitIssuerLabel": record.permit_issuer_label,
        "permitOperationClasses": list(record.permit_operation_classes),
        "permitExclusions": _public_value(record.permit_exclusions, "exclusions") if public else list(record.permit_exclusions),
        "permitPublicSafetyClassification": record.permit_public_safety_classification,
        "sequence": record.sequence,
        "status": record.status,
        "timestamp": record.timestamp,
    }


def _plain(value: Any) -> Any:
    """Recursively convert immutable mappings and sequences to plain data."""

    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_plain(child) for child in value]
    return value


def _public_value(value: Any, key: str = "") -> Any:
    """Recursively redact sensitive keys, paths, and private network addresses."""

    if _SENSITIVE_KEY.search(key):
        return "withheld"
    if isinstance(value, Mapping):
        return {str(child_key): _public_value(child, str(child_key)) for child_key, child in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_public_value(child, key) for child in value]
    if isinstance(value, str):
        if value.startswith("/"):
            return "withheld"
        try:
            address = ipaddress.ip_address(value)
            if address.is_private or address.is_loopback or address.is_link_local:
                return "withheld"
        except ValueError:
            pass
    return value


def _record_from_data(value: Mapping[str, Any]) -> EvidenceRecord:
    """Reconstruct a typed evidence record from durable JSON data."""

    return EvidenceRecord(
        kind=str(value["kind"]), sequence=int(value["sequence"]), timestamp=str(value["timestamp"]),
        execution_id=str(value["executionId"]), action_id=str(value["actionId"]),
        catalog_identity=str(value["catalogIdentity"]), plan_digest=str(value["planDigest"]),
        permit_id=str(value["permitId"]) if value.get("permitId") is not None else None,
        permit_nonce=str(value["permitNonce"]) if value.get("permitNonce") is not None else None,
        status=str(value["status"]), handle_id=str(value["handleId"]) if value.get("handleId") is not None else None,
        handle_action_id=str(value["handleActionId"]) if value.get("handleActionId") is not None else None,
        handle_provider_id=str(value["handleProviderId"]) if value.get("handleProviderId") is not None else None,
        handle_provider_kind=(
            str(value["handleProviderKind"]) if value.get("handleProviderKind") is not None else None
        ),
        handle_resource_identity=(
            str(value["handleResourceIdentity"]) if value.get("handleResourceIdentity") is not None else None
        ),
        environment_identity=str(value["environmentIdentity"]),
        resource_revisions=freeze(value.get("resourceRevisions", {})),
        artifact_digests=tuple(str(item) for item in value.get("artifactDigests", ())),
        selection=freeze(value.get("selection", {})),
        permit_issuer_label=(str(value["permitIssuerLabel"]) if value.get("permitIssuerLabel") is not None else None),
        permit_operation_classes=tuple(str(item) for item in value.get("permitOperationClasses", ())),
        permit_exclusions=tuple(str(item) for item in value.get("permitExclusions", ())),
        permit_public_safety_classification=(
            str(value["permitPublicSafetyClassification"])
            if value.get("permitPublicSafetyClassification") is not None else None
        ),
        details=freeze(value.get("details", {})),
    )


class InMemoryEvidenceJournal:
    """Thread-safe ordered evidence journal for isolated tests and fixtures."""

    def __init__(self) -> None:
        """Initialize an empty journal and its synchronization lock."""

        self._records: list[EvidenceRecord] = []
        self._lock = threading.Lock()

    @property
    def records(self) -> tuple[EvidenceRecord, ...]:
        """Return an immutable snapshot of all records."""

        with self._lock:
            return tuple(self._records)

    def append(self, record: EvidenceRecord) -> None:
        """Append a record with the next contiguous sequence number."""

        with self._lock:
            expected = len(self._records) + 1
            if record.sequence not in (0, expected):
                raise EvidenceWriteError("evidence sequence is not contiguous")
            self._records.append(replace(record, sequence=expected))

    def permit_consumed(self, permit_id: str, nonce: str | None = None) -> bool:
        """Return whether an intent already used the permit ID or nonce."""

        return any(
            item.kind == "intent" and (item.permit_id == permit_id or (nonce is not None and item.permit_nonce == nonce))
            for item in self.records
        )

    def public_records(self) -> tuple[dict[str, Any], ...]:
        """Return all evidence using the public-safe projection."""

        return tuple(_record_data(item, public=True) for item in self.records)


class FileEvidenceJournal(InMemoryEvidenceJournal):
    """Append-only JSON Lines evidence journal with POSIX process locking."""

    def __init__(self, path: str | Path) -> None:
        """Open or create a non-symlink journal and validate stored records."""

        super().__init__()
        self.path = Path(path)
        self.lock_path = self.path.with_name(self.path.name + ".lock")
        if self.path.is_symlink():
            raise EvidenceWriteError("evidence journal must not be a symbolic link")
        with self._file_lock():
            self._reload()

    @contextmanager
    def _file_lock(self):
        """Hold an exclusive advisory lock on a private sibling lock file."""

        if fcntl is None:
            raise EvidenceWriteError("file evidence locking is unavailable on this platform")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(self.lock_path, flags, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _reload(self) -> None:
        """Reload and validate the complete contiguous on-disk journal."""

        if not self.path.exists():
            self._records = []
            return
        if self.path.is_symlink():
            raise EvidenceWriteError("evidence journal must not be a symbolic link")
        try:
            records = [_record_from_data(json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines() if line]
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise EvidenceWriteError(f"cannot load evidence journal: {error}") from error
        if [item.sequence for item in records] != list(range(1, len(records) + 1)):
            raise EvidenceWriteError("evidence journal sequence is invalid")
        self._records = records

    @property
    def records(self) -> tuple[EvidenceRecord, ...]:
        """Reload under thread and process locks and return a consistent snapshot."""

        with self._lock, self._file_lock():
            self._reload()
            return tuple(self._records)

    def append(self, record: EvidenceRecord) -> None:
        """Durably append, flush, and fsync one contiguously numbered record."""

        with self._lock:
            with self._file_lock():
                self._reload()
                expected = len(self._records) + 1
                if record.sequence not in (0, expected):
                    raise EvidenceWriteError("evidence sequence is not contiguous")
                stored = replace(record, sequence=expected)
                encoded = json.dumps(_record_data(stored), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
                try:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
                    flags |= getattr(os, "O_NOFOLLOW", 0)
                    descriptor = os.open(self.path, flags, 0o600)
                    os.fchmod(descriptor, 0o600)
                    with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
                        stream.write(encoded)
                        stream.flush()
                        os.fsync(stream.fileno())
                    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    directory = os.open(self.path.parent, directory_flags)
                    try:
                        os.fsync(directory)
                    finally:
                        os.close(directory)
                except OSError as error:
                    raise EvidenceWriteError(f"cannot persist evidence: {error}") from error
                self._records.append(stored)


class LifecycleProvider(Protocol):
    """Provider contract constrained to exact handles issued by ``start``."""

    provider_id: str
    provider_kind: str
    def start(self, action: ProcessAction | None, execution_id: str, action_id: str, timeout_seconds: float) -> OwnedResourceHandle:
        """Start the selected resource and return provider-owned authority."""

        ...

    def observe(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Observe only the exact resource identified by *handle*."""

        ...

    def stop(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Stop only the exact resource identified by *handle*."""

        ...

    def cleanup(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Clean only the stopped resource identified by *handle*."""

        ...

    def revalidate(self, handle: OwnedResourceHandle) -> bool:
        """Confirm after restart that the provider still owns *handle*."""

        ...


class FixtureProvider:
    """Deterministic in-memory provider proving owned lifecycle mechanics."""

    provider_id = "fixture-provider"
    provider_kind = "fixture"

    def __init__(self, *, start_barrier: threading.Barrier | None = None) -> None:
        """Initialize fixture state with an optional concurrency-test barrier."""

        self._handles: dict[str, tuple[OwnedResourceHandle, str]] = {}
        self._counter = 0
        self._lock = threading.Lock()
        self._starting = threading.Event()
        self._start_barrier = start_barrier
        self.start_count = 0
        self.stop_count = 0

    def wait_until_starting(self) -> None:
        """Wait until a concurrent fixture start reaches its synchronization point."""

        if not self._starting.wait(timeout=2):
            raise RuntimeError("fixture did not enter start")

    def release_start(self) -> None:
        """Release a configured start barrier from the coordinating thread."""

        if self._start_barrier is not None:
            self._start_barrier.wait(timeout=2)

    def start(self, action: ProcessAction | None, execution_id: str, action_id: str, timeout_seconds: float) -> OwnedResourceHandle:
        """Create one in-memory resource and issue its exact ownership handle."""

        self._starting.set()
        if self._start_barrier is not None:
            self._start_barrier.wait(timeout=2)
        with self._lock:
            self._counter += 1
            self.start_count += 1
            opaque = f"fixture-{self._counter:04d}"
            handle = OwnedResourceHandle(
                opaque, execution_id, action_id, self.provider_id, self.provider_kind, opaque,
            )
            self._handles[opaque] = (handle, "running")
            return handle

    def _validate(self, handle: OwnedResourceHandle) -> None:
        """Reject unknown, forged, or altered ownership handles."""

        stored = self._handles.get(handle.opaque_id)
        if stored is None or stored[0] != handle:
            raise PermissionError("provider does not own this resource handle")

    def observe(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Return the state of an exactly owned fixture resource."""

        self._validate(handle)
        return self._handles[handle.opaque_id][1]

    def stop(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Idempotently stop an exactly owned fixture resource."""

        self._validate(handle)
        with self._lock:
            stored, status = self._handles[handle.opaque_id]
            if status != "stopped":
                self._handles[handle.opaque_id] = (stored, "stopped")
                self.stop_count += 1
        return "stopped"

    def cleanup(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Confirm cleanup only after the exact fixture resource is stopped."""

        self._validate(handle)
        if self._handles[handle.opaque_id][1] != "stopped":
            raise RuntimeError("fixture must be stopped before cleanup")
        return "cleaned"

    def revalidate(self, handle: OwnedResourceHandle) -> bool:
        """Return whether an exact fixture handle is still owned."""

        stored = self._handles.get(handle.opaque_id)
        return stored is not None and stored[0] == handle


class ProcessProvider:
    """Constrained local process provider for explicitly attested isolated roots.

    The attestation is a fail-closed trust input; this class does not create an
    operating-system sandbox and does not authorize legacy execution.
    """

    provider_id = "process-provider"
    provider_kind = "process"

    def __init__(
        self, execution_root: str | Path, *, allowed_executables: Sequence[str | Path],
        explicit_environment: Mapping[str, str], isolation_attestation: IsolationAttestation,
    ) -> None:
        """Bind the provider to an existing root, allowlist, environment, and attestation."""

        self.execution_root = Path(execution_root).resolve(strict=True)
        self.allowed_executables = frozenset(Path(value).resolve(strict=True) for value in allowed_executables)
        if Path(isolation_attestation.execution_root).resolve(strict=True) != self.execution_root:
            raise ValueError("isolation attestation does not match the execution root")
        self.isolation_attestation = isolation_attestation
        self.explicit_environment = dict(explicit_environment)
        self._processes: dict[str, tuple[OwnedResourceHandle, subprocess.Popen[bytes]]] = {}
        self._lock = threading.Lock()

    def start(self, action: ProcessAction | None, execution_id: str, action_id: str, timeout_seconds: float = 1) -> OwnedResourceHandle:
        """Start one allowlisted executable without a shell or inherited handles."""

        if action is None:
            raise ValueError("process provider requires a process action")
        cwd = Path(action.working_directory).resolve(strict=True)
        executable = Path(action.executable).resolve(strict=True)
        if executable not in self.allowed_executables:
            raise ValueError("process executable is not explicitly allowed")
        try:
            cwd.relative_to(self.execution_root)
        except ValueError as error:
            raise ValueError("process working directory is outside the isolated execution root") from error
        missing = tuple(name for name in action.environment_names if name not in self.explicit_environment)
        if missing:
            raise ValueError(f"explicit environment is missing: {', '.join(missing)}")
        environment = {name: self.explicit_environment[name] for name in action.environment_names}
        process = subprocess.Popen(
            [str(executable), *action.arguments], cwd=cwd, env=environment, shell=False,
            close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )
        opaque = uuid.uuid4().hex
        handle = OwnedResourceHandle(
            opaque, execution_id, action_id, self.provider_id, self.provider_kind,
            f"process-group:{process.pid}",
        )
        with self._lock:
            self._processes[opaque] = (handle, process)
        return handle

    def _owned(self, handle: OwnedResourceHandle) -> subprocess.Popen[bytes]:
        """Resolve an exact issued handle to its owned child process."""

        if (handle.provider_id, handle.provider_kind) != (self.provider_id, self.provider_kind):
            raise PermissionError("provider does not own this resource handle")
        stored = self._processes.get(handle.opaque_id)
        if stored is None or stored[0] != handle:
            raise PermissionError("provider does not own this resource handle")
        return stored[1]

    def observe(self, handle: OwnedResourceHandle, timeout_seconds: float = 1) -> str:
        """Report whether the exactly owned child is running or exited."""

        return "running" if self._owned(handle).poll() is None else "exited"

    def stop(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Terminate the exact owned process group within the declared timeout."""

        process = self._owned(handle)
        if process.poll() is not None:
            return "stopped"
        if hasattr(os, "killpg"):
            os.killpg(process.pid, signal.SIGTERM)
        else:  # pragma: no cover - platform fallback
            process.terminate()
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("owned process did not stop within its declared timeout") from error
        return "stopped"

    def cleanup(self, handle: OwnedResourceHandle, timeout_seconds: float) -> str:
        """Confirm cleanup only after the exact owned process has exited."""

        process = self._owned(handle)
        if process.poll() is None:
            raise RuntimeError("owned process must be stopped before cleanup")
        return "cleaned"

    def revalidate(self, handle: OwnedResourceHandle) -> bool:
        """Return whether this provider still owns the exact process handle."""

        stored = self._processes.get(handle.opaque_id)
        return stored is not None and stored[0] == handle


@dataclass
class _Execution:
    """Controller-local state for one activated or reconciled execution."""

    plan: LifecyclePlan
    permit_id: str
    handle: OwnedResourceHandle
    status: str
    reconciled: bool = True


class LifecycleController:
    """Coordinate permitted lifecycle mutations with ownership and durable evidence."""

    def __init__(self, journal: EvidenceJournal) -> None:
        """Initialize from journal evidence and block starts with incomplete outcomes."""

        self.journal = journal
        self._executions: dict[str, _Execution] = {}
        pending: dict[tuple[str, str], tuple[str, str]] = {}
        for record in journal.records:
            key = (record.execution_id, record.action_id)
            if record.kind == "intent":
                pending[key] = (record.catalog_identity, record.environment_identity)
            elif record.kind == "outcome":
                pending.pop(key, None)
        self._blocked_starts: set[tuple[str, str]] = set(pending.values())

    def _mutation_lock(self, plan: LifecyclePlan) -> threading.Lock:
        """Return the process-local mutation lock for a catalog/environment pair."""

        key = (plan.catalog_identity, plan.environment_identity)
        with _MUTATION_LOCKS_GUARD:
            return _MUTATION_LOCKS.setdefault(key, threading.Lock())

    def _execution(self, execution_id: str, phase: str) -> _Execution:
        """Resolve active execution state or raise a stable unknown-execution error."""

        execution = self._executions.get(execution_id)
        if execution is None:
            empty_plan = LifecyclePlan(
                catalog_identity="unselected", environment_identity="unselected",
                provider_id="unselected", provider_kind="unselected", selection=FrozenMap(),
                resource_revisions=FrozenMap(), artifact_digests=(), actions=(),
                process_action=None, blockers=(), digest="unselected",
            )
            raise _lifecycle_error(
                "XVERSE-RUNTIME-EXECUTION-UNKNOWN", phase, empty_plan,
                f"execution {execution_id!r} is unknown", "Use an activated or reconciled execution ID.",
            )
        return execution

    @staticmethod
    def _check_provider(execution: _Execution, provider: LifecycleProvider, phase: str) -> None:
        """Ensure the provider identity matches the provider-issued handle."""

        if (provider.provider_id, provider.provider_kind) != (
            execution.handle.provider_id, execution.handle.provider_kind,
        ):
            raise _lifecycle_error(
                "XVERSE-RUNTIME-PROVIDER", phase, execution.plan,
                "provider identity does not match the owned handle", "Use the provider that issued the handle.",
            )

    def _record(
        self, kind: str, execution_id: str, action_id: str, plan: LifecyclePlan,
        permit_id: str | None, status: str, handle: OwnedResourceHandle | None = None,
        permit_nonce: str | None = None,
        permit_context: ExecutionPermit | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """Construct and append one complete evidence record."""

        record = EvidenceRecord(
            kind=kind, sequence=0,
            timestamp=datetime.now(timezone.utc).isoformat(), execution_id=execution_id,
            action_id=action_id, catalog_identity=plan.catalog_identity, plan_digest=plan.digest,
            permit_id=permit_id, permit_nonce=permit_nonce, status=status,
            environment_identity=plan.environment_identity,
            resource_revisions=plan.resource_revisions, artifact_digests=plan.artifact_digests,
            selection=plan.selection,
            permit_issuer_label=permit_context.issuer_label if permit_context else None,
            permit_operation_classes=permit_context.operation_classes if permit_context else (),
            permit_exclusions=permit_context.exclusions if permit_context else (),
            permit_public_safety_classification=(permit_context.public_safety_classification if permit_context else None),
            handle_id=handle.opaque_id if handle else None,
            handle_action_id=handle.action_id if handle else None,
            handle_provider_id=handle.provider_id if handle else None,
            handle_provider_kind=handle.provider_kind if handle else None,
            handle_resource_identity=handle.resource_identity if handle else None,
            details=freeze(details or {}),
        )
        self.journal.append(record)

    def start(
        self, plan: LifecyclePlan, permit: ExecutionPermit, provider: LifecycleProvider, *, execution_id: str,
    ) -> LifecycleResult:
        """Consume a matching permit and activate a plan exactly once.

        Durable intent is written before provider mutation. Repeated matching calls
        are idempotent; mismatches and concurrent mutations fail closed.
        """

        existing = self._executions.get(execution_id)
        if existing is not None:
            if existing.plan.digest != plan.digest:
                raise _lifecycle_error("XVERSE-RUNTIME-EXECUTION-ID", "start", plan, "execution ID is bound to another plan", "Use the original plan or a new execution ID.")
            if (
                existing.permit_id != permit.permit_id
                or (provider.provider_id, provider.provider_kind)
                != (plan.provider_id, plan.provider_kind)
            ):
                raise _lifecycle_error("XVERSE-RUNTIME-IDEMPOTENCY", "start", plan, "idempotent start does not match the activated execution", "Use the original permit and provider.")
            return LifecycleResult(execution_id, existing.status, existing.handle)
        key = (plan.catalog_identity, plan.environment_identity)
        if key in self._blocked_starts:
            raise _lifecycle_error("XVERSE-RUNTIME-EVIDENCE-INCOMPLETE", "start", plan, "new starts are blocked by incomplete evidence", "Resolve the incomplete journal before starting again.")
        if plan.blockers:
            raise _lifecycle_error("XVERSE-RUNTIME-PLAN-BLOCKED", "start", plan, f"plan is blocked: {', '.join(plan.blockers)}", "Resolve every planning blocker.")
        if (provider.provider_id, provider.provider_kind) != (plan.provider_id, plan.provider_kind):
            raise _lifecycle_error("XVERSE-RUNTIME-PROVIDER", "start", plan, "provider identity does not match the plan", "Use the exact selected provider.")
        permit.validate(plan, datetime.now(timezone.utc))
        mutation_lock = self._mutation_lock(plan)
        if not mutation_lock.acquire(blocking=False):
            raise _lifecycle_error("XVERSE-RUNTIME-CONCURRENT-MUTATION", "start", plan, "concurrent mutation is not allowed", "Wait for the active mutation to finish.")
        try:
            if execution_id in self._executions:
                execution = self._executions[execution_id]
                return LifecycleResult(execution_id, execution.status, execution.handle)
            if self.journal.permit_consumed(permit.permit_id, permit.nonce):
                raise _lifecycle_error("XVERSE-PERMIT-CONSUMED", "authorization", plan, "execution permit is already consumed", "Issue a new single-use permit.")
            prepare_action = next(item for item in plan.actions if item.phase == "prepare")
            start_action = next(item for item in plan.actions if item.phase == "start")
            try:
                self._record(
                    "observation", execution_id, prepare_action.action_id, plan, permit.permit_id,
                    "prepared", permit_nonce=permit.nonce,
                )
                self._record(
                    "intent", execution_id, start_action.action_id, plan, permit.permit_id,
                    "pending", permit_nonce=permit.nonce, permit_context=permit,
                )
            except EvidenceWriteError as error:
                raise _lifecycle_error(
                    "XVERSE-RUNTIME-EVIDENCE-INTENT", "start", plan,
                    "durable intent evidence could not be stored", "Repair the journal before retrying.",
                ) from error
            handle: OwnedResourceHandle | None = None
            try:
                started_at = time.monotonic()
                handle = provider.start(plan.process_action, execution_id, start_action.action_id, start_action.timeout_seconds)
                if (
                    handle.execution_id != execution_id
                    or handle.action_id != start_action.action_id
                    or (handle.provider_id, handle.provider_kind)
                    != (plan.provider_id, plan.provider_kind)
                ):
                    raise PermissionError("provider returned a mismatched ownership handle")
                if time.monotonic() - started_at > start_action.timeout_seconds:
                    raise TimeoutError("provider exceeded the declared start timeout")
            except Exception as error:
                if handle is not None:
                    stop_action = next(item for item in plan.actions if item.phase == "stop")
                    try:
                        provider.stop(handle, stop_action.timeout_seconds)
                    except Exception:
                        pass
                try:
                    self._record(
                        "outcome", execution_id, start_action.action_id, plan, permit.permit_id,
                        "failed", details={"errorType": type(error).__name__},
                    )
                except EvidenceWriteError:
                    self._blocked_starts.add(key)
                raise _lifecycle_error(
                    "XVERSE-RUNTIME-PROVIDER-START", "start", plan,
                    f"provider start failed: {type(error).__name__}",
                    "Inspect provider evidence and correct the declared action or timeout.",
                ) from error
            assert handle is not None
            execution = _Execution(plan, permit.permit_id, handle, "running")
            self._executions[execution_id] = execution
            try:
                self._record(
                    "outcome", execution_id, start_action.action_id, plan,
                    permit.permit_id, "running", handle,
                )
            except EvidenceWriteError:
                execution.status = "evidence-incomplete"
                self._blocked_starts.add(key)
            return LifecycleResult(execution_id, execution.status, handle)
        finally:
            mutation_lock.release()

    def observe(self, execution_id: str, provider: LifecycleProvider) -> LifecycleResult:
        """Evaluate the declared readiness condition for an owned execution."""

        execution = self._execution(execution_id, "observe")
        self._check_provider(execution, provider, "observe")
        if not execution.reconciled:
            raise PermissionError("ownership handle has not been revalidated")
        action = next(item for item in execution.plan.actions if item.phase == "observe")
        observed_at = time.monotonic()
        try:
            status = provider.observe(execution.handle, action.timeout_seconds)
        except Exception as error:
            try:
                self._record("observation", execution_id, action.action_id, execution.plan, execution.permit_id, "failed", execution.handle, details={"errorType": type(error).__name__})
            except EvidenceWriteError:
                execution.status = "evidence-incomplete"
            raise _lifecycle_error("XVERSE-RUNTIME-PROVIDER-OBSERVE", "observe", execution.plan, f"provider observation failed: {type(error).__name__}", "Inspect provider evidence and the declared observation.") from error
        if time.monotonic() - observed_at > action.timeout_seconds:
            status = "timeout"
        elif action.condition and status != action.condition:
            status = "unavailable" if status == "unavailable" else "not-ready"
        try:
            self._record(
                "observation", execution_id, action.action_id, execution.plan,
                execution.permit_id, status, execution.handle,
            )
        except EvidenceWriteError:
            execution.status = "evidence-incomplete"
            self._blocked_starts.add((execution.plan.catalog_identity, execution.plan.environment_identity))
            return LifecycleResult(execution_id, execution.status, execution.handle)
        if execution.status != "evidence-incomplete":
            execution.status = status
        return LifecycleResult(execution_id, execution.status, execution.handle)

    def stop(self, execution_id: str, provider: LifecycleProvider) -> LifecycleResult:
        """Durably record intent and stop only the exactly owned resource."""

        execution = self._execution(execution_id, "stop")
        self._check_provider(execution, provider, "stop")
        if execution.status == "stopped":
            return LifecycleResult(execution_id, "stopped", execution.handle)
        if not execution.reconciled:
            raise PermissionError("ownership handle has not been revalidated")
        action = next(item for item in execution.plan.actions if item.phase == "stop")
        lock = self._mutation_lock(execution.plan)
        if not lock.acquire(blocking=False):
            raise _lifecycle_error("XVERSE-RUNTIME-CONCURRENT-MUTATION", "stop", execution.plan, "concurrent mutation is not allowed", "Wait for the active mutation to finish.")
        try:
            try:
                self._record("intent", execution_id, action.action_id, execution.plan, execution.permit_id, "pending", execution.handle)
            except EvidenceWriteError as error:
                raise _lifecycle_error("XVERSE-RUNTIME-EVIDENCE-INTENT", "stop", execution.plan, "durable stop intent could not be stored", "Repair the journal before retrying.") from error
            try:
                status = provider.stop(execution.handle, action.timeout_seconds)
            except Exception as error:
                try:
                    self._record("outcome", execution_id, action.action_id, execution.plan, execution.permit_id, "failed", execution.handle, details={"errorType": type(error).__name__})
                except EvidenceWriteError:
                    execution.status = "evidence-incomplete"
                raise _lifecycle_error("XVERSE-RUNTIME-PROVIDER-STOP", "stop", execution.plan, f"provider stop failed: {type(error).__name__}", "Escalate the still-owned resource without broad cleanup.") from error
            prior_incomplete = execution.status == "evidence-incomplete"
            try:
                self._record("outcome", execution_id, action.action_id, execution.plan, execution.permit_id, status, execution.handle)
                execution.status = "evidence-incomplete" if prior_incomplete else status
            except EvidenceWriteError:
                execution.status = "evidence-incomplete"
                self._blocked_starts.add((execution.plan.catalog_identity, execution.plan.environment_identity))
            return LifecycleResult(execution_id, execution.status, execution.handle)
        finally:
            lock.release()

    def cleanup(self, execution_id: str, provider: LifecycleProvider) -> LifecycleResult:
        """Durably record intent and clean only the exactly owned stopped resource."""

        execution = self._execution(execution_id, "cleanup")
        self._check_provider(execution, provider, "cleanup")
        if not execution.reconciled:
            raise PermissionError("ownership handle has not been revalidated")
        action = next(item for item in execution.plan.actions if item.phase == "cleanup")
        lock = self._mutation_lock(execution.plan)
        if not lock.acquire(blocking=False):
            raise _lifecycle_error("XVERSE-RUNTIME-CONCURRENT-MUTATION", "cleanup", execution.plan, "concurrent mutation is not allowed", "Wait for the active mutation to finish.")
        try:
            try:
                self._record("intent", execution_id, action.action_id, execution.plan, execution.permit_id, "pending", execution.handle)
            except EvidenceWriteError as error:
                raise _lifecycle_error("XVERSE-RUNTIME-EVIDENCE-INTENT", "cleanup", execution.plan, "durable cleanup intent could not be stored", "Repair the journal before retrying.") from error
            try:
                status = provider.cleanup(execution.handle, action.timeout_seconds)
            except Exception as error:
                try:
                    self._record("outcome", execution_id, action.action_id, execution.plan, execution.permit_id, "failed", execution.handle, details={"errorType": type(error).__name__})
                except EvidenceWriteError:
                    execution.status = "evidence-incomplete"
                raise _lifecycle_error("XVERSE-RUNTIME-PROVIDER-CLEANUP", "cleanup", execution.plan, f"provider cleanup failed: {type(error).__name__}", "Escalate the owned resource without inferred cleanup.") from error
            try:
                self._record("outcome", execution_id, action.action_id, execution.plan, execution.permit_id, status, execution.handle)
                if execution.status != "evidence-incomplete":
                    execution.status = status
            except EvidenceWriteError:
                execution.status = "evidence-incomplete"
            return LifecycleResult(execution_id, execution.status, execution.handle)
        finally:
            lock.release()

    def reconcile(self, plan: LifecyclePlan, execution_id: str, provider: LifecycleProvider) -> bool:
        """Restore controller state only after exact handle evidence revalidation."""

        evidence = next(
            (item for item in reversed(self.journal.records)
             if item.execution_id == execution_id and item.plan_digest == plan.digest
             and item.catalog_identity == plan.catalog_identity and item.handle_id
             and item.handle_action_id and item.handle_provider_id and item.handle_provider_kind
             and item.handle_resource_identity),
            None,
        )
        if evidence is None:
            return False
        handle = OwnedResourceHandle(
            evidence.handle_id, execution_id, evidence.handle_action_id,
            evidence.handle_provider_id, evidence.handle_provider_kind,
            evidence.handle_resource_identity,
        )
        if (
            (provider.provider_id, provider.provider_kind)
            != (plan.provider_id, plan.provider_kind)
            or (handle.provider_id, handle.provider_kind)
            != (plan.provider_id, plan.provider_kind)
        ):
            return False
        if not provider.revalidate(handle):
            return False
        self._executions[execution_id] = _Execution(
            plan=plan, permit_id=evidence.permit_id or "", handle=handle,
            status="reconciled", reconciled=True,
        )
        return True


__all__ = [
    "EvidenceRecord", "EvidenceWriteError", "ExecutionPermit", "FileEvidenceJournal",
    "FixtureProvider", "InMemoryEvidenceJournal", "IsolationAttestation", "LifecycleController",
    "LifecycleDiagnostic", "LifecycleError", "LifecycleResult", "OwnedResourceHandle",
    "ProcessAction", "ProcessProvider",
]
