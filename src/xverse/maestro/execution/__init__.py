"""Public execution capability022, under implementation and not yet admitted.

Static inspection is implemented first; lifecycle dispatch/admission remains a
separate unfinished layer. Preparation alone never authorizes execution.
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
