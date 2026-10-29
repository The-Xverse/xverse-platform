"""Host-bound public lifecycle service, prototype owned-simulation scope.

Providers are reviewed host code with cooperative finite operation deadlines.
This service does not import private runtime types or issue any host permission.
"""
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import sys
import stat
import threading
import time
from typing import Protocol
import uuid

from .admission import EffectiveConfiguration, ExecutionProvider, PreparedExecution, prepare_execution
from .evidence import LifecycleEvidence
from .inspection import ExecutionInputError, InspectionHost, _DIGEST, _ID, canonical, sha256
from .permissions import HostExecutionPermit
from .planning import LifecycleGraph, LifecyclePhase, plan_lifecycle
from .observations import NativeObservationBatch


def _failure_code(error, fallback):
    code = getattr(error, 'code', None)
    return code if isinstance(error, ExecutionInputError) and type(code) is str and _ID.fullmatch(code) else fallback


@dataclass(frozen=True)
class RuntimeContext:
    run_id: str
    operation_id: str
    correlation_id: str
    intent_event_id: str
    deadline: float


@dataclass(frozen=True)
class PhaseReceipt:
    """Provider observation; resource references are opaque, never host paths."""
    outcome: str
    resource_references: tuple[str, ...] = ()
    readiness_kind: str | None = None
    observation_bytes: bytes = field(default=b'{}', repr=False)

    def __post_init__(self):
        if (self.outcome not in ('prepared', 'started', 'ready')
                or type(self.resource_references) is not tuple
                or len(self.resource_references) > 32
                or any(type(r) is not str or not _ID.fullmatch(r) for r in self.resource_references)
                or self.readiness_kind not in (None, 'liveness', 'interface', 'functional')
                or (self.outcome == 'ready') != (self.readiness_kind is not None)
                or type(self.observation_bytes) is not bytes or len(self.observation_bytes) > 4096):
            raise ExecutionInputError('MPX-PHASE-RECEIPT-INVALID')
        try:
            value = json.loads(self.observation_bytes)
            if type(value) is not dict:
                raise ValueError()
            canonical(value)  # Reject nonfinite/deep invalid JSON before persistence.
        except (ValueError, TypeError, RecursionError):
            raise ExecutionInputError('MPX-PHASE-RECEIPT-INVALID') from None


class RuntimeProvider(ExecutionProvider, Protocol):
    """Installed host implementation, with pure admission and bounded effects.

    Expansion and validate_runtime are side-effect-free. They must reject every
    unsupported input semantic and verify current installation/permissions. Cleanup
    covers partially failed dispatches using provider-retained exact ownership.
    """
    @property
    def installation_digest(self) -> str:
        """Actual current host installation identity, separate from provider code."""
        ...
    def lifecycle_phases(self, configuration: EffectiveConfiguration,
                         prepared: PreparedExecution) -> tuple[LifecyclePhase, ...]: ...
    def validate_runtime(self, configuration: EffectiveConfiguration,
                         prepared: PreparedExecution) -> None: ...
    def dispatch(self, phase: LifecyclePhase, configuration: EffectiveConfiguration,
                 context: RuntimeContext) -> PhaseReceipt: ...
    def cleanup(self, phase: LifecyclePhase, configuration: EffectiveConfiguration,
                context: RuntimeContext) -> str:
        """Return released, failed or unknown; never signal an unknown resource."""
        ...
    def observe_runtime(self, configuration: EffectiveConfiguration,
                        context: RuntimeContext) -> str:
        """Boundedly observe exact resources: running, exited or unknown; no activation."""
        ...


@dataclass
class _Run:
    prepared: PreparedExecution
    graph: LifecycleGraph
    request_digest: str
    operation_id: str
    correlation_id: str
    state: str = 'preparing'
    version: int = 1
    evidence: object = field(default=None, repr=False)
    evidence_state: str = 'unavailable'
    attempted: list = field(default_factory=list)
    observations: list = field(default_factory=list)
    cleanup_state: str = 'not_requested'
    failure_code: str | None = None
    deadline: float = 0
    timer: object = field(default=None, repr=False)
    native_sources: dict = field(default_factory=dict)
    native_gap_count: int = 0
    stop_request_version: int | None = None
    stop_operation_id: str | None = None
    cancel: threading.Event = field(default_factory=threading.Event, repr=False)


class PublicExecutionService:
    """Single host-root owner; durable claims prohibit dispatch replay after restart.

    Native Linux prototype. Reader snapshots expose metadata and original event
    references; Argus verdicts must be obtained from the actual public reader.
    Closing a service with an active run is rejected. Lost service handles never
    confer process ownership, even if an old journal names a PID or resource.
    """
    def __init__(self, root: Path, host: InspectionHost,
                 providers: tuple[RuntimeProvider, ...], *, max_runtime_seconds: float = 600,
                 cleanup_budget_seconds: float = 30, recovery_bindings: tuple = ()):
        from .recovery import validate_bindings
        if sys.platform != 'linux':
            raise ExecutionInputError('MPX-RUNTIME-OS-UNSUPPORTED')
        import fcntl
        if (type(max_runtime_seconds) not in (int, float) or not math.isfinite(max_runtime_seconds)
                or not 1 <= max_runtime_seconds <= 3600
                or type(cleanup_budget_seconds) not in (int, float) or not math.isfinite(cleanup_budget_seconds)
                or not 0 < cleanup_budget_seconds <= 60):
            raise ExecutionInputError('MPX-RUNTIME-LIMIT-INVALID')
        self.max_runtime_seconds = max_runtime_seconds
        self.cleanup_budget_seconds = cleanup_budget_seconds
        if (type(host) is not InspectionHost or type(providers) is not tuple
                or len(providers) > 128):
            raise ExecutionInputError('MPX-PROVIDER-REGISTRY-INVALID')
        expected = {t.provider_id: t.implementation_digest for t in host.targets}
        actual = {}
        for provider in providers:
            identity = getattr(provider, 'provider_id', None)
            if (type(identity) is not str or identity not in expected or identity in actual
                    or getattr(provider, 'implementation_digest', None) != expected[identity]
                    or any(not callable(getattr(provider, method, None)) for method in
                        ('prepare_effective_configuration', 'validate_runtime', 'lifecycle_phases',
                         'dispatch', 'cleanup', 'observe_runtime'))):
                raise ExecutionInputError('MPX-PROVIDER-REGISTRY-INVALID')
            actual[identity] = provider
        self._recovery_bindings = validate_bindings(recovery_bindings, actual)
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if (self.root.is_symlink() or self.root.absolute() != self.root.resolve()
                or self.root.stat().st_mode & (stat.S_IWGRP | stat.S_IWOTH)):
            raise ExecutionInputError('MPX-RUNTIME-ROOT-INVALID')
        self._root_identity = (self.root.stat().st_dev, self.root.stat().st_ino)
        self.host = host
        self.providers = providers
        self._providers = actual
        self._lock_fd = os.open(self.root / '.owner.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self._lock_fd)
            raise ExecutionInputError('MPX-RUNTIME-ROOT-BUSY') from None
        try:
            self._root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            self._writer_root = Path('/proc/self/fd') / str(self._root_fd)
        except OSError:
            os.close(self._lock_fd)
            raise ExecutionInputError('MPX-RUNTIME-ROOT-INVALID') from None
        self._closed = False
        self._runs = {}
        self._operations = threading.Lock()
        self._state = threading.RLock()
        self._clock_domain = 'host-monotonic-' + uuid.uuid4().hex

    @property
    def runtime_binding_digest(self):
        """Actual service environment/root and host limits, no public paths."""
        return sha256(b'xverse.maestro.public-runtime-binding.v1\0' + canonical({
            'hostBindingDigest': self.host.identity(), 'platform': sys.platform,
            'kernel': os.uname().release, 'uid': os.getuid(),
            'rootIdentity': self._root_identity, 'rootPath': str(self.root),
            'maxRuntimeSeconds': self.max_runtime_seconds,
            'cleanupBudgetSeconds': self.cleanup_budget_seconds}))

    def _verify_installation(self, binding):
        actual = getattr(self._providers[binding.provider_id], 'installation_digest', None)
        if binding.configuration.installation_digest is None or actual != binding.configuration.installation_digest:
            raise ExecutionInputError('MPX-INSTALLATION-MISMATCH')

    def _check_root(self):
        try:
            valid = (not self._closed and not self.root.is_symlink()
                and (self.root.stat().st_dev, self.root.stat().st_ino) == self._root_identity)
        except OSError:
            valid = False
        if not valid:
            raise ExecutionInputError('MPX-RUNTIME-ROOT-CHANGED')

    def _claim_path(self, run_id):
        if type(run_id) is not str or not _ID.fullmatch(run_id):
            raise ExecutionInputError('MPX-RUN-ID-INVALID')
        self._check_root()
        return self.root / (run_id + '.claim.json')

    def _read_claim(self, run_id):
        path = self._claim_path(run_id)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        except OSError:
            raise ExecutionInputError('MPX-CLAIM-UNAVAILABLE') from None
        try:
            with os.fdopen(descriptor, 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError()
                raw = stream.read(8193)
            if len(raw) > 8192:
                raise ValueError()
            value = json.loads(raw)
            if (type(value) is not dict or value.get('runId') != run_id
                    or any(type(value.get(k)) is not str or not _ID.fullmatch(value[k])
                        for k in ('operationId', 'correlationId'))
                    or any(type(value.get(k)) is not str or not _DIGEST.fullmatch(value[k])
                        for k in ('requestDigest', 'planDigest', 'inputSemanticDigest'))):
                raise ValueError()
            return value
        except (ValueError, KeyError, TypeError):
            raise ExecutionInputError('MPX-CLAIM-INVALID') from None

    def _claim(self, prepared, request_digest, operation_id, correlation_id):
        if len(tuple(self.root.glob('*.claim.json'))) >= 128:
            raise ExecutionInputError('MPX-RUN-LIMIT')
        payload = canonical({'runId': prepared.submission.run_id, 'requestDigest': request_digest,
            'operationId': operation_id, 'correlationId': correlation_id,
            'planDigest': prepared.submission.expected_plan_digest,
            'inputSemanticDigest': prepared.submission.expected_input_semantic_digest})
        try:
            descriptor = os.open(self._claim_path(prepared.submission.run_id),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            raise ExecutionInputError('MPX-START-CONFLICT') from None
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def _snapshot(self, run):
        return {'runId': run.prepared.submission.run_id,
            'planDigest': run.prepared.submission.expected_plan_digest,
            'inputSemanticDigest': run.prepared.submission.expected_input_semantic_digest,
            'preparationDigest': run.prepared.digest, 'lifecycleDigest': run.graph.digest,
            'operationId': run.operation_id, 'correlationId': run.correlation_id,
            'stopOperationId': run.stop_operation_id,
            'state': run.state, 'stateVersion': run.version,
            'cleanup': run.cleanup_state, 'evidenceWriter': run.evidence_state,
            'failureCode': run.failure_code,
            'nativeSources': json.loads(canonical(run.native_sources)),
            'observationTransportGaps': run.native_gap_count,
            'observations': json.loads(canonical(run.observations))}

    def read(self, run_id):
        """Observe only; recovery without original ownership is always unknown."""
        with self._state:
            self._check_root()
            self._claim_path(run_id)
            if run_id in self._runs:
                return self._snapshot(self._runs[run_id])
            claim = self._read_claim(run_id)
            if claim is None:
                raise ExecutionInputError('MPX-RUN-NOT-FOUND')
            return {k: claim[k] for k in ('runId', 'planDigest', 'inputSemanticDigest',
                    'operationId', 'correlationId')} | {
                'state': 'unknown', 'stateVersion': 0, 'cleanup': 'unknown',
                'evidenceWriter': 'unknown', 'observations': [],
                'diagnostic': 'MPX-ORIGINAL-OWNERSHIP-UNAVAILABLE'}

    def _record(self, run, *, kind, phase=None, outcome=None,
                causation_id=None, readiness_kind=None, resources=(), observation=None,
                operation_id=None):
        try:
            event, clock = run.evidence.append(operation_id=operation_id or run.operation_id,
                correlation_id=run.correlation_id, kind=kind, phase=phase, outcome=outcome,
                causation_id=causation_id, readiness_kind=readiness_kind, resources=resources,
                observation=observation)
        except Exception:
            run.evidence_state = 'failed'
            raise ExecutionInputError('MPX-EVIDENCE-WRITE-FAILED') from None
        with self._state:
            run.observations.append({'eventId': event, 'kind': kind,
                'phaseId': phase.phase_id if phase else None,
                'logicalId': phase.logical_id if phase else None,
                'outcome': outcome, 'causationId': causation_id,
                'operationId': operation_id or run.operation_id,
                'readinessKind': readiness_kind, 'hostClock': clock})
            run.version += 1
        return event

    def start(self, prepared: PreparedExecution, graph: LifecycleGraph,
              permit: HostExecutionPermit, *, idempotency_key: str):
        """Start only the exact current host-bound configuration, once durably."""
        if type(idempotency_key) is not str or not _ID.fullmatch(idempotency_key):
            raise ExecutionInputError('MPX-IDEMPOTENCY-INVALID')
        if (type(prepared) is not PreparedExecution or type(graph) is not LifecycleGraph
                or type(permit) is not HostExecutionPermit):
            raise ExecutionInputError('MPX-START-INPUT-INVALID')
        request_digest = sha256(canonical({'preparation': prepared.digest,
            'lifecycle': graph.digest, 'permit': permit.digest, 'key': idempotency_key}))
        run_id = prepared.submission.run_id
        with self._operations:
            self._check_root()
            claim = self._read_claim(run_id)
            if claim is not None:
                if claim['requestDigest'] != request_digest:
                    raise ExecutionInputError('MPX-START-CONFLICT')
                return self.read(run_id)
            if any(r.state not in ('stopped', 'failed') or r.cleanup_state != 'released'
                   for r in self._runs.values()):
                raise ExecutionInputError('MPX-ACTIVE-RUN-CONFLICT')
            # A predecessor process's claim does not carry its original resource
            # handles. Do not grant new activation while any such run is unknown.
            known_claims = {self._claim_path(key) for key in self._runs}
            from .recovery import root_claims, verified
            foreign = [key for key in root_claims(self) if self._claim_path(key) not in known_claims]
            if foreign and self._recovery_bindings:
                pins = {b.provider_id:b.installation_digest for b in self._recovery_bindings}
                if any(p.configuration.installation_digest != pins[p.provider_id] for p in prepared.providers):
                    raise ExecutionInputError('MRX-CURRENT-INSTALLATION-MISMATCH')
            if any(not verified(self, key) for key in foreign):
                raise ExecutionInputError('MPX-ORIGINAL-OWNERSHIP-UNAVAILABLE')
            fresh = prepare_execution(prepared.submission, self.host, self.providers)
            if fresh != prepared:
                raise ExecutionInputError('MPX-PREPARATION-STALE')
            phases = []
            for binding in prepared.providers:
                provider = self._providers[binding.provider_id]
                try:
                    self._verify_installation(binding)
                    provider.validate_runtime(binding.configuration, prepared)
                    expansion = provider.lifecycle_phases(binding.configuration, prepared)
                except ExecutionInputError:
                    raise
                except Exception:
                    raise ExecutionInputError('MPX-PROVIDER-ADMISSION-FAILED') from None
                if type(expansion) is not tuple or any(p.provider_id != binding.provider_id for p in expansion):
                    raise ExecutionInputError('MPX-PHASE-OWNERSHIP')
                phases.extend(expansion)
            if plan_lifecycle(prepared, tuple(phases)) != graph:
                raise ExecutionInputError('MPX-PREPARATION-STALE')
            permit.validate(prepared, self.host, graph, runtime_binding_digest=self.runtime_binding_digest)
            run = _Run(prepared, graph, request_digest, 'op-' + uuid.uuid4().hex,
                'corr-' + uuid.uuid4().hex)
            self._claim(prepared, request_digest, run.operation_id, run.correlation_id)
            with self._state:
                self._runs[run_id] = run
            try:
                source_clocks = {}
                for binding in prepared.providers:
                    declaration = getattr(self._providers[binding.provider_id], 'observation_clock_declarations', None)
                    if not callable(declaration):
                        continue
                    declared = declaration(binding.configuration, run_id, run.operation_id)
                    if type(declared) is not dict or len(declared) > 32:
                        raise ExecutionInputError('MPX-NATIVE-CLOCK-DECLARATION-INVALID')
                    for key, value in declared.items():
                        name = binding.provider_id + '.' + key if type(key) is str and _ID.fullmatch(key) else None
                        if name is None or name in source_clocks or name == 'host':
                            raise ExecutionInputError('MPX-NATIVE-CLOCK-DECLARATION-INVALID')
                        source_clocks[name] = value
                    if len(source_clocks) > 32:
                        raise ExecutionInputError('MPX-NATIVE-CLOCK-DECLARATION-INVALID')
                run.evidence = LifecycleEvidence(self._writer_root / (run_id + '.argus'), prepared,
                    clock_domain=self._clock_domain, source_clocks=source_clocks)
                run.evidence_state = 'open'
                self._record(run, kind='run-start-requested')
                duration = min(self.max_runtime_seconds, max(0, permit.expires_at - time.time()))
                run.deadline = time.monotonic() + duration
                run.timer = threading.Timer(duration, self._expire, args=(run,))
                run.timer.daemon = True
                run.timer.start()
                configurations = {p.provider_id: p.configuration for p in prepared.providers}
                for phase in graph.phases:
                    if run.cancel.is_set():
                        raise ExecutionInputError('MPX-START-CANCELLED')
                    permit.validate(prepared, self.host, graph, runtime_binding_digest=self.runtime_binding_digest)
                    for binding in prepared.providers:
                        self._verify_installation(binding)
                    self._check_root()
                    intent = self._record(run, kind='phase-intent', phase=phase)
                    context = RuntimeContext(run_id, run.operation_id, run.correlation_id,
                        intent, min(run.deadline, time.monotonic() + phase.timeout_seconds))
                    # Retain attempts before dispatch: callbacks can acquire a
                    # resource and then fail before returning a receipt.
                    if phase.operation != 'ready':
                        run.attempted.append((phase, configurations[phase.provider_id], context))
                    receipt = self._providers[phase.provider_id].dispatch(
                        phase, configurations[phase.provider_id], context)
                    expected = {'prepare': 'prepared', 'start': 'started', 'ready': 'ready'}[phase.operation]
                    if (type(receipt) is not PhaseReceipt or receipt.outcome != expected
                            or time.monotonic() > context.deadline):
                        raise ExecutionInputError('MPX-PHASE-FAILED')
                    self._record(run, kind='phase-outcome', phase=phase,
                        outcome=receipt.outcome, causation_id=intent,
                        readiness_kind=receipt.readiness_kind, resources=receipt.resource_references,
                        observation=json.loads(receipt.observation_bytes))
                if run.cancel.is_set() or time.monotonic() >= run.deadline:
                    raise ExecutionInputError('MPX-START-CANCELLED')
                with self._state:
                    run.state = 'running'
                    run.version += 1
                self._record(run, kind='run-running', outcome='running')
            except BaseException as error:
                run.failure_code = _failure_code(error, 'MPX-PROVIDER-FAILED')
                self._cleanup(run, failed=True)
                if not isinstance(error, Exception):
                    raise
            return self.read(run_id)

    def _expire(self, run):
        run.cancel.set()
        with self._operations:
            if run.state not in ('stopped', 'failed', 'unknown'):
                run.failure_code = 'MPX-RUN-DEADLINE'
                run.stop_operation_id = run.stop_operation_id or 'stop-' + uuid.uuid4().hex
                self._cleanup(run, failed=True)

    def observe(self, run_id, *, expected_version: int):
        """Reconcile actual liveness without activation; ordinary read stays inert.

        Startup readiness is historical. Runtime observations retain their own
        original monotonic timestamp and never assert current functional fitness.
        Each explicit observation consumes bounded evidence capacity; exhaustion
        is a writer failure and still triggers cleanup of known resources.
        """
        with self._operations:
            snapshot = self.read(run_id)
            if type(expected_version) is not int or snapshot['stateVersion'] != expected_version:
                raise ExecutionInputError('MPX-STATE-VERSION-CONFLICT')
            run = self._runs.get(run_id)
            if run is None or run.state != 'running':
                return snapshot
            try:
                for binding in run.prepared.providers:
                    intent = self._record(run, kind='runtime-observe-intent', outcome=binding.provider_id)
                    context = RuntimeContext(run_id, run.operation_id, run.correlation_id,
                        intent, time.monotonic() + 3)
                    result = self._providers[binding.provider_id].observe_runtime(binding.configuration, context)
                    if result not in ('running', 'exited', 'unknown') or time.monotonic() > context.deadline:
                        result = 'unknown'
                    self._record(run, kind='runtime-observation', outcome=result, causation_id=intent)
                    if result != 'running':
                        raise ExecutionInputError('MPX-RUNTIME-' + result.upper())
            except Exception as error:
                run.failure_code = _failure_code(error, 'MPX-PROVIDER-OBSERVATION-FAILED')
                self._cleanup(run, failed=True)
            return self.read(run_id)

    def _cleanup(self, run, *, failed):
        if run.timer is not None:
            run.timer.cancel()
        with self._state:
            run.state = 'stopping'
            run.cleanup_state = 'in_progress'
            run.version += 1
        uncertain = False
        cleanup_deadline = time.monotonic() + self.cleanup_budget_seconds
        operation_id = run.stop_operation_id or run.operation_id
        try:
            self._record(run, kind='run-stop-requested' if run.stop_operation_id else 'run-cleanup-requested',
                operation_id=operation_id,
                observation={'failureCode': run.failure_code, 'expectedVersion': run.stop_request_version})
        except Exception:
            run.evidence_state = 'failed'
        for phase, configuration, original in reversed(run.attempted):
            intent = None
            try:
                intent = self._record(run, kind='cleanup-intent', phase=phase, operation_id=operation_id)
            except Exception:
                run.evidence_state = 'failed'
            context = RuntimeContext(original.run_id, operation_id, run.correlation_id,
                intent or original.intent_event_id,
                min(cleanup_deadline, time.monotonic() + phase.timeout_seconds))
            try:
                outcome = ('unknown' if time.monotonic() >= cleanup_deadline else
                    self._providers[phase.provider_id].cleanup(phase, configuration, context))
                if outcome not in ('released', 'failed', 'unknown') or time.monotonic() > context.deadline:
                    outcome = 'unknown'
            except Exception:
                outcome = 'unknown'
            uncertain |= outcome != 'released'
            try:
                self._record(run, kind='cleanup-outcome', phase=phase,
                    outcome=outcome, causation_id=intent, operation_id=operation_id)
            except Exception:
                run.evidence_state = 'failed'
        with self._state:
            run.cleanup_state = 'unknown' if uncertain else 'released'
            run.state = 'unknown' if uncertain else ('failed' if failed else 'stopped')
            run.version += 1
        try:
            self._record(run, kind='run-terminal', outcome=run.state, operation_id=operation_id,
                observation={'failureCode': run.failure_code, 'cleanup': run.cleanup_state,
                    'observationTransportGaps': run.native_gap_count})
            run.evidence.close(failed=failed or uncertain or run.evidence_state == 'failed'
                or run.native_gap_count > 0,
                reason='Known native observation transport gap; evidence is incomplete'
                    if run.native_gap_count else None)
            if run.evidence_state != 'failed':
                run.evidence_state = run.evidence.writer.writer_state
        except Exception:
            run.evidence_state = 'failed'

    def collect_native_observations(self, run_id, *, expected_version: int):
        """Pull original batches from installed providers; callers supply no data.

        This observes only. No missing interface or host-supplied enum proves a
        native source: concrete native providers require actual verification.
        """
        with self._operations:
            snapshot = self.read(run_id)
            if type(expected_version) is not int or snapshot['stateVersion'] != expected_version:
                raise ExecutionInputError('MPX-STATE-VERSION-CONFLICT')
            run = self._runs.get(run_id)
            if run is None or run.state != 'running':
                return snapshot
            try:
                for binding in run.prepared.providers:
                    provider = self._providers[binding.provider_id]
                    pull = getattr(provider, 'read_observation_batch', None)
                    if not callable(pull):
                        with self._state:
                            if binding.provider_id not in run.native_sources:
                                run.native_sources[binding.provider_id] = {'state': 'unsupported'}
                                run.version += 1
                        continue
                    self._verify_installation(binding)
                    context = RuntimeContext(run_id, run.operation_id, run.correlation_id,
                        run.correlation_id, time.monotonic() + 3)
                    batch = pull(binding.configuration, context)
                    if time.monotonic() > context.deadline:
                        raise ExecutionInputError('MPX-NATIVE-SOURCE-TIMEOUT')
                    if batch is None:
                        continue
                    if type(batch) is not NativeObservationBatch:
                        raise ExecutionInputError('MPX-NATIVE-BATCH-INVALID')
                    projection = batch.validate_identity(run.prepared, binding)
                    previous = run.native_sources.get(binding.provider_id, {})
                    prior_sequence = previous.get('batchSequence', 0)
                    if batch.sequence <= prior_sequence:
                        if batch.sequence == prior_sequence and batch.digest == previous['batchDigest']:
                            continue
                        raise ExecutionInputError('MPX-NATIVE-SEQUENCE-CONFLICT')
                    gap = batch.sequence - prior_sequence - 1
                    metadata = {k: v for k, v in projection.items() if k != 'records'}
                    intent = self._record(run, kind='native-batch-import-intent',
                        observation={'providerId': binding.provider_id, 'batchSequence': batch.sequence,
                            'batchDigest': batch.digest, 'originalEnvelope': metadata,
                            'missingSourceBatches': gap})
                    try:
                        ordinals, snapshot_ordinals, input_ordinals = run.evidence.import_observations(projection)
                    except Exception as error:
                        run.evidence_state = 'failed'
                        raise ExecutionInputError(_failure_code(error, 'MPX-NATIVE-EVIDENCE-IMPORT-FAILED')) from None
                    with self._state:
                        run.native_gap_count += gap
                        run.native_sources[binding.provider_id] = {'state': 'available',
                            'batchSequence': batch.sequence, 'batchDigest': batch.digest,
                            'missingSourceBatches': previous.get('missingSourceBatches', 0) + gap,
                            'lastArgusOrdinals': list(ordinals),
                            'lastSnapshotArgusOrdinals': list(snapshot_ordinals),
                            'lastInputArgusOrdinals': list(input_ordinals),
                            'importedRecords': previous.get('importedRecords', 0) + len(ordinals)}
                        run.version += 1
                    self._record(run, kind='native-batch-imported',
                        outcome='partial' if gap else 'accepted', causation_id=intent,
                        observation={'providerId': binding.provider_id,
                            'argusOrdinals': list(ordinals), 'missingSourceBatches': gap})
            except Exception as error:
                run.failure_code = _failure_code(error, 'MPX-NATIVE-SOURCE-FAILED')
                self._cleanup(run, failed=True)
            return self.read(run_id)

    def stop(self, run_id, *, expected_version: int):
        """Request cancellation then bounded reverse cleanup, without replay."""
        with self._state:
            snapshot = self.read(run_id)
            run = self._runs.get(run_id)
            repeated = run is not None and run.stop_request_version == expected_version
            if type(expected_version) is not int or not repeated and snapshot['stateVersion'] != expected_version:
                raise ExecutionInputError('MPX-STATE-VERSION-CONFLICT')
            if run is None:
                return snapshot
            if run.state in ('stopped', 'failed', 'unknown'):
                return snapshot
            if not repeated:
                run.stop_request_version = expected_version
                run.stop_operation_id = 'stop-' + uuid.uuid4().hex
                run.version += 1
            run.cancel.set()
        with self._operations:
            if run.state not in ('stopped', 'failed', 'unknown'):
                self._cleanup(run, failed=False)
            return self.read(run_id)

    def inspect_recovery(self, run_id):
        """Read-only eligibility; no provider calls or restored resource handles."""
        from .recovery import RecoveryInspection, binding_digest, inspect
        if not self._operations.acquire(blocking=False):
            raise ExecutionInputError('MRX-REGISTRATION-BUSY')
        try:
            self._claim_path(run_id)
            binding = binding_digest(self)
            try:
                return inspect(self, run_id)
            except ExecutionInputError as error:
                return RecoveryInspection(canonical({'contractVersion':'1.0','runId':run_id,
                    'eligible':False,'reasons':[error.code], 'sourceWitness':None,
                    'hostBindingDigest':self.host.identity(),
                    'runtimeBindingDigest':self.runtime_binding_digest,'recoveryBindingDigest':binding}))
        finally:
            self._operations.release()

    def retire_released(self, inspection, permit):
        """Publish a separate host-permitted retirement; original bytes stay intact."""
        from .recovery import retire
        if not self._operations.acquire(blocking=False):
            raise ExecutionInputError('MRX-REGISTRATION-BUSY')
        try:
            return retire(self, inspection, permit)
        finally:
            self._operations.release()

    def recovery_status(self, run_id):
        """Separate retirement status; never change read(run_id)'s ownership state."""
        from .recovery import verified
        if not self._operations.acquire(blocking=False):
            raise ExecutionInputError('MRX-REGISTRATION-BUSY')
        try:
            self._claim_path(run_id)
            if not self._recovery_bindings:
                return {'runId':run_id,'retirement':'unavailable','reason':'MRX-BINDING-REQUIRED'}
            try:
                valid = verified(self, run_id)
                return {'runId':run_id,'retirement':'verified' if valid else 'absent'}
            except ExecutionInputError as error:
                return {'runId':run_id,'retirement':'unverified','reason':error.code}
        finally:
            self._operations.release()

    def close(self):
        """Release the host-root lock only after every known run is terminal."""
        with self._operations, self._state:
            if any(run.state not in ('stopped', 'failed', 'unknown') for run in self._runs.values()):
                raise ExecutionInputError('MPX-ACTIVE-RUNS')
            if not self._closed:
                os.close(self._root_fd)
                os.close(self._lock_fd)
                self._closed = True
