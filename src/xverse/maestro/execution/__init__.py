"""Public execution capability022, under implementation and not yet admitted.

Static/effective inspection, host-bound lifecycle dispatch and owned Linux child
handling are prototype implementations. Preparation alone never authorizes
execution. Native integration, full verification and acceptance remain separate.
"""
from .inspection import (
    CanonicalSubmission, EffectiveInspection, ExecutionInputError, ExperimentSelection, InspectionHost,
    SchemaPin, TargetBinding, inspect_submission,
)

__all__ = ['CanonicalSubmission','EffectiveInspection','ExecutionInputError',
    'ExperimentSelection','InspectionHost','SchemaPin','TargetBinding','inspect_submission']

from .admission import (
    EffectiveConfiguration, ExecutionProvider, PreparedExecution, PreparedProvider,
    prepare_execution,
)
__all__ += ['EffectiveConfiguration','ExecutionProvider','PreparedExecution',
            'PreparedProvider','prepare_execution']

from .planning import LifecycleGraph, LifecyclePhase, plan_lifecycle
from .permissions import HostExecutionPermit
__all__ += ['LifecycleGraph', 'LifecyclePhase', 'plan_lifecycle', 'HostExecutionPermit']

from .runtime import PhaseReceipt, PublicExecutionService, RuntimeContext, RuntimeProvider
from .process import FixedProcessInstallation, InstallationFile, OwnedChild, ProcessOwnershipError
__all__ += ['PhaseReceipt', 'PublicExecutionService', 'RuntimeContext', 'RuntimeProvider',
            'FixedProcessInstallation', 'InstallationFile', 'OwnedChild', 'ProcessOwnershipError']
