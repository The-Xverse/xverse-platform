"""Thesis Lite Phase 5: deterministic fault injection over compiled XDL fault schedules.

Public surface: the closed vocabulary (``VOCABULARY``), ``resolve_schedule`` (pure resolution of a
compiled plan against Maestro's planned ticks), the boundary protocol with the owned relays, the
tick-driven ``FaultScheduler`` and the Argus evidence helpers. Nothing here starts a process,
opens a socket or touches a resource it does not hold an exact handle for.
"""

from .resolve import ResolvedEntry, effective_tick, resolve_entry, resolve_schedule
from .vocabulary import (
    APPLY_FAILURE_POLICIES,
    ARBITRATIONS,
    COLLECTION_BOUNDARY,
    UNEXECUTED,
    VOCABULARY,
    FaultError,
    FaultParameters,
    KindSpec,
    kind_spec,
    validate_parameters,
)

__all__ = [
    "APPLY_FAILURE_POLICIES",
    "ARBITRATIONS",
    "COLLECTION_BOUNDARY",
    "UNEXECUTED",
    "VOCABULARY",
    "FaultError",
    "FaultParameters",
    "KindSpec",
    "ResolvedEntry",
    "effective_tick",
    "kind_spec",
    "resolve_entry",
    "resolve_schedule",
    "validate_parameters",
]
