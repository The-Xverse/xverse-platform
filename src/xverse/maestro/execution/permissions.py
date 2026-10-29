"""Trusted-host, exact-configuration runtime authorization.

This is an in-process host trust input, not a browser credential or an approval
issuer. Applications must never construct it from imported XDL or request bodies.
Existing private-runtime, physical-device and containment approvals are separate.
"""
from dataclasses import dataclass
import math
import time

from .admission import PreparedExecution
from .inspection import ExecutionInputError, InspectionHost, _DIGEST, _ID, canonical, sha256
from .planning import LifecycleGraph, plan_lifecycle


@dataclass(frozen=True)
class HostExecutionPermit:
    """Host-supplied single-run grant; never permits physical resources."""
    permit_id: str
    host_binding_digest: str
    preparation_digest: str
    lifecycle_digest: str
    environment_id: str
    approval_reference: str
    not_before: float
    expires_at: float
    scope: str = 'owned-simulation'
    runtime_binding_digest: str | None = None

    def __post_init__(self):
        if (any(type(v) is not str or not _ID.fullmatch(v)
                for v in (self.permit_id, self.environment_id))
                or any(type(v) is not str or not _DIGEST.fullmatch(v) for v in
                       (self.host_binding_digest, self.preparation_digest, self.lifecycle_digest))
                or type(self.approval_reference) is not str
                or not 1 <= len(self.approval_reference) <= 512
                or self.scope != 'owned-simulation'
                or self.runtime_binding_digest is not None and
                (type(self.runtime_binding_digest) is not str or not _DIGEST.fullmatch(self.runtime_binding_digest))
                or any(type(v) not in (int, float) or not math.isfinite(v)
                       for v in (self.not_before, self.expires_at))
                or not 0 < self.expires_at - self.not_before <= 3600):
            raise ExecutionInputError('MPX-PERMIT-INVALID')

    @property
    def digest(self):
        return sha256(canonical(self.__dict__))

    def validate(self, prepared: PreparedExecution, host: InspectionHost,
                 graph: LifecycleGraph, *, now: float | None = None,
                 runtime_binding_digest: str | None = None):
        """Check exact bindings and time before effects; expiry never bars cleanup."""
        instant = time.time() if now is None else now
        if (type(instant) not in (int, float) or not math.isfinite(instant)
                or not self.not_before <= instant < self.expires_at):
            raise ExecutionInputError('MPX-PERMIT-TIME')
        if (self.host_binding_digest != host.identity()
                or self.preparation_digest != prepared.digest
                or self.lifecycle_digest != graph.digest
                or graph.preparation_digest != prepared.digest
                or self.environment_id != host.host_id):
            raise ExecutionInputError('MPX-PERMIT-MISMATCH')
        if runtime_binding_digest is not None and self.runtime_binding_digest != runtime_binding_digest:
            raise ExecutionInputError('MPX-RUNTIME-BINDING-MISMATCH')
        # Revalidate a supplied graph instead of trusting a directly constructed
        # dataclass receipt. This performs no provider calls or resource effects.
        if plan_lifecycle(prepared, graph.phases) != graph:
            raise ExecutionInputError('MPX-PHASE-GRAPH-INVALID')
        if any(b['realizationClass'] not in ('simulated', 'virtual')
               for b in prepared.inspection.to_data()['plan']['bindings']):
            raise ExecutionInputError('MPX-PERMIT-SCOPE')
