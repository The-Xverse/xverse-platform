"""Bounded host-provider lifecycle expansion, with no runtime effects.

These operations realize existing compiler bindings. They are not an authored
System, an execution permit, or a substitute for interpreting scenario semantics.
"""
from dataclasses import dataclass
import math

from .admission import PreparedExecution
from .inspection import ExecutionInputError, _ID, canonical, sha256


@dataclass(frozen=True)
class LifecyclePhase:
    """A trusted provider's phase for one selected logical element.

    needs names other phase IDs, including phases of other admitted providers.
    start/prepare may acquire owned resources; ready only observes them. Cleanup
    must subsequently visit every attempted mutating phase in reverse order.
    """
    phase_id: str
    logical_id: str
    provider_id: str
    operation: str
    needs: tuple[str, ...] = ()
    timeout_seconds: float = 30.0

    def __post_init__(self):
        if (any(type(v) is not str or not _ID.fullmatch(v)
                for v in (self.phase_id, self.provider_id))
                or type(self.logical_id) is not str or len(self.logical_id) > 1024
                or self.operation not in ('prepare', 'start', 'ready')
                or type(self.needs) is not tuple or len(self.needs) > 128
                or any(type(v) is not str or not _ID.fullmatch(v) for v in self.needs)
                or len(set(self.needs)) != len(self.needs)
                or type(self.timeout_seconds) not in (int, float)
                or not math.isfinite(self.timeout_seconds)
                or not 0 < self.timeout_seconds <= 300):
            raise ExecutionInputError('MPX-PHASE-INVALID')

    def to_data(self):
        return {'phaseId': self.phase_id, 'logicalId': self.logical_id,
                'providerId': self.provider_id, 'operation': self.operation,
                'needs': list(self.needs), 'timeoutSeconds': self.timeout_seconds}


@dataclass(frozen=True)
class LifecycleGraph:
    """Validated derived expansion; no provider callback or runtime authority."""
    preparation_digest: str
    phases: tuple[LifecyclePhase, ...]
    digest: str


def plan_lifecycle(prepared: PreparedExecution,
                   phases: tuple[LifecyclePhase, ...]) -> LifecycleGraph:
    """Check complete logical coverage, ownership, dependencies and phase order.

    Providers must separately reject unsupported plan semantics during effective
    preparation. This validator neither executes nor silently interprets them.
    The deterministic topological order uses phase identity only to break ties;
    it does not invent a causal relationship between independent phases.
    """
    if (type(prepared) is not PreparedExecution or type(phases) is not tuple
            or not 1 <= len(phases) <= 512
            or any(type(p) is not LifecyclePhase for p in phases)):
        raise ExecutionInputError('MPX-PHASE-GRAPH-INVALID')
    units = {u['logicalId']: u['providerId'] for u in prepared.inspection.to_data()['units']}
    by_id = {p.phase_id: p for p in phases}
    if len(by_id) != len(phases):
        raise ExecutionInputError('MPX-PHASE-DUPLICATE')
    for phase in phases:
        if units.get(phase.logical_id) != phase.provider_id:
            raise ExecutionInputError('MPX-PHASE-OWNERSHIP')
        if not set(phase.needs) <= by_id.keys():
            raise ExecutionInputError('MPX-PHASE-DEPENDENCY-MISSING')
    # Kahn traversal, bounded by the admitted graph size. Retain ancestors to
    # require actual prepare -> start -> ready dependencies, not list ordering.
    pending = dict(by_id)
    ancestors = {}
    ordered = []
    while pending:
        eligible = sorted(k for k, p in pending.items() if set(p.needs) <= ancestors.keys())
        if not eligible:
            raise ExecutionInputError('MPX-PHASE-CYCLE')
        for key in eligible:
            phase = pending.pop(key)
            ancestors[key] = set(phase.needs)
            for need in phase.needs:
                ancestors[key].update(ancestors[need])
            ordered.append(phase)
    for logical_id in units:
        own = [p for p in phases if p.logical_id == logical_id]
        for operation in ('prepare', 'start', 'ready'):
            if not any(p.operation == operation for p in own):
                raise ExecutionInputError('MPX-PHASE-COVERAGE')
        for phase in own:
            if phase.operation == 'prepare':
                continue
            required = 'prepare' if phase.operation == 'start' else 'start'
            if not any(p.operation == required and p.phase_id in ancestors[phase.phase_id] for p in own):
                raise ExecutionInputError('MPX-PHASE-ORDER')
        # Every acquisition must feed a readiness observation, including support
        # resources created in additional prepare/start phases.
        ready = [p for p in own if p.operation == 'ready']
        if any(not any(p.phase_id in ancestors[r.phase_id] for r in ready)
               for p in own if p.operation != 'ready'):
            raise ExecutionInputError('MPX-PHASE-UNOBSERVED')
    ordered = tuple(ordered)
    digest = sha256(b'xverse.maestro.lifecycle-graph.v1\0' + canonical({
        'preparationDigest': prepared.digest, 'phases': [p.to_data() for p in ordered]}))
    return LifecycleGraph(prepared.digest, ordered, digest)
