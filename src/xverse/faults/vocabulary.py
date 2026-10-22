"""Closed fault vocabulary for Thesis Lite Phase 5 (FR-001).

Eight executable kinds act through owned boundaries (``duplicate`` and ``reorder`` since Phase 6
amendment A1); declared-only kinds are validated and never applied (their owning phase implements
the boundary). Parameters arrive as the compiled Phase 1
typed parameter list; two ids are reserved for the scheduler: ``arbitration`` and
``on-apply-failure``. Everything outside this module's tables is rejected.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Any

PROCESS, MESSAGE, OBSERVATION, ASSURANCE = "process", "message", "observation", "assurance"
ARBITRATION, ON_APPLY_FAILURE = "arbitration", "on-apply-failure"
ARBITRATIONS = ("reject", "serialize", "supersede")
APPLY_FAILURE_POLICIES = ("continue", "stop-run")
UNEXECUTED = "declared-not-executed"


class FaultError(RuntimeError):
    """Stable, public-safe failure raised by the fault vocabulary and resolution."""

    def __init__(self, code: str, message: str) -> None:
        """Create a classified failure.

        @param code Stable code of the form ``XVERSE-FAULT-<REASON>``.
        @param message Public-safe explanation.
        """

        super().__init__(f"{code}: {message}")
        self.code = code


MAX_INTEGER_PARAMETER = 1_000_000


def _positive_int(value: Any) -> bool:
    """Return whether ``value`` is an integer (not bool) in [1, MAX_INTEGER_PARAMETER]."""

    return type(value) is int and 1 <= value <= MAX_INTEGER_PARAMETER


def _unit_ratio(value: Any) -> bool:
    """Return whether ``value`` is a finite number in (0, 1]."""

    return type(value) in (int, float) and math.isfinite(value) and 0 < value <= 1


@dataclass(frozen=True)
class KindSpec:
    """How one fault kind is applied: boundary class, executability and parameter validators."""

    kind: str
    boundary_class: str
    executable: bool
    parameters: Mapping[str, Callable[[Any], bool]]
    required: tuple[str, ...] = ()
    exactly_one_of: tuple[str, ...] = ()


VOCABULARY: Mapping[str, KindSpec] = {
    "delay": KindSpec("delay", MESSAGE, True, {"delay-ticks": _positive_int}, required=("delay-ticks",)),
    "loss": KindSpec("loss", MESSAGE, True, {"loss-ratio": _unit_ratio, "every": _positive_int}, exactly_one_of=("loss-ratio", "every")),
    "stale": KindSpec("stale", MESSAGE, True, {}),
    "crash": KindSpec("crash", PROCESS, True, {}),
    "freeze": KindSpec("freeze", PROCESS, True, {}),
    "sensorDropout": KindSpec("sensorDropout", OBSERVATION, True, {}),
    "duplicate": KindSpec("duplicate", MESSAGE, True, {"copies": _positive_int}, required=("copies",)),  # Phase 6 amendment A1
    "reorder": KindSpec("reorder", MESSAGE, True, {"window": _positive_int}, required=("window",)),  # Phase 6 amendment A1
    "assurance.proposal-unsafe": KindSpec("assurance.proposal-unsafe", ASSURANCE, False, {}),
    "assurance.proposal-mistimed": KindSpec("assurance.proposal-mistimed", ASSURANCE, False, {}),
    "assurance.evidence-loss": KindSpec("assurance.evidence-loss", ASSURANCE, False, {}),
}

#: Target collection of the System resource → boundary class a fault on it may use.
COLLECTION_BOUNDARY: Mapping[str, str] = {
    "componentInstances": PROCESS,
    "flows": MESSAGE,
    "sensors": OBSERVATION,
}


@dataclass(frozen=True)
class FaultParameters:
    """Validated parameters of one entry: kind-specific values plus the reserved scheduler ids."""

    values: Mapping[str, Any]
    arbitration: str | None
    on_apply_failure: str


def kind_spec(kind: Any) -> KindSpec:
    """Return the spec of ``kind`` or fail with ``XVERSE-FAULT-KIND``."""

    if not isinstance(kind, str) or kind not in VOCABULARY:
        raise FaultError("XVERSE-FAULT-KIND", f"fault kind {kind!r} is outside the Phase 5 vocabulary")
    return VOCABULARY[kind]


def validate_parameters(spec: KindSpec, parameters: Sequence[Mapping[str, Any]], fault_id: str) -> FaultParameters:
    """Validate the compiled typed parameter list of one entry against its kind.

    @param spec Kind specification.
    @param parameters Compiled Phase 1 parameter projections (``id``, ``value`` at least).
    @param fault_id Entry id for diagnostics.
    @return Validated values and the reserved scheduler parameters.
    @raises FaultError ``XVERSE-FAULT-PARAMETER`` on an unknown, missing, duplicated or invalid parameter.
    """

    code = "XVERSE-FAULT-PARAMETER"
    values: dict[str, Any] = {}
    for item in parameters:
        if not isinstance(item, Mapping) or not isinstance(item.get("id"), str):
            raise FaultError(code, f"fault {fault_id!r} carries a malformed parameter")
        name, value = item["id"], item.get("value")
        if name in values:
            raise FaultError(code, f"fault {fault_id!r} repeats parameter {name!r}")
        if name in (ARBITRATION, ON_APPLY_FAILURE):
            allowed = ARBITRATIONS if name == ARBITRATION else APPLY_FAILURE_POLICIES
            if value not in allowed:
                raise FaultError(code, f"fault {fault_id!r} parameter {name!r} must be one of {allowed}")
        elif name not in spec.parameters:
            raise FaultError(code, f"fault {fault_id!r} parameter {name!r} is not declared for kind {spec.kind!r}")
        elif not spec.parameters[name](value):
            raise FaultError(code, f"fault {fault_id!r} parameter {name!r} has an invalid value")
        values[name] = value
    for name in spec.required:
        if name not in values:
            raise FaultError(code, f"fault {fault_id!r} lacks required parameter {name!r}")
    if spec.exactly_one_of and sum(1 for name in spec.exactly_one_of if name in values) != 1:
        raise FaultError(code, f"fault {fault_id!r} must declare exactly one of {spec.exactly_one_of}")
    arbitration = values.pop(ARBITRATION, None)
    policy = values.pop(ON_APPLY_FAILURE, "stop-run")
    return FaultParameters(values=dict(values), arbitration=arbitration, on_apply_failure=str(policy))
