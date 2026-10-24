"""Thesis Lite Phase 5: deterministic fault injection over compiled XDL fault schedules.

Public surface: the closed vocabulary (``VOCABULARY``), ``resolve_schedule`` (pure resolution of a
compiled plan against Maestro's planned ticks), the boundary protocol with the owned relays, the
tick-driven ``FaultScheduler`` and the Argus evidence helpers. Nothing here starts a process,
opens a socket or touches a resource it does not hold an exact handle for.
"""

from .simtime import HubChannel, SimEntry, SimTimeFaultScheduler, SimulationClock, resolve_simtime, thaw_check
from .resolve import ResolvedEntry, effective_tick, resolve_entry, resolve_schedule, validate_static
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

#: Public capability contract (ADR-ML3-SIMTIME-0001 decision 9): True only because every option A requirement is
#: implemented here: exact simulator-ns onset and duration, the simulator-time horizon check, the remote relay
#: boundary at the clock-source unit and the step-hold freeze handshake (with ST-2: the channel lifetime, the
#: ``resumed`` hold verification, per-entry arming and the arm ``count``/``index``). It claims no measurement and no run.
SIMULATION_TIME_TRIGGERS = True

__all__ = [
    "SIMULATION_TIME_TRIGGERS",
    "HubChannel",
    "SimEntry",
    "SimTimeFaultScheduler",
    "SimulationClock",
    "resolve_simtime",
    "thaw_check",
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
    "validate_static",
]
