"""Public Argus evidence API: run admission and read-only reconstruction.

``EvidenceStore.open_run`` admits exactly one fresh bounded run after verifying the accepted plan
identity through the accepted public API, records separate source-byte provenance, echoes the
caller bounds/obligations verbatim and publishes the open manifest atomically.
``EvidenceStore.read_run`` returns a bounded read-only reader. Identities, clocks, units, limits and
obligations are caller inputs only; no ambient wall clock, random identity, remote lookup or
cross-clock conversion is used (``detailed-design.md`` sections 7, 10, 12 and 14).
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from .clocks import validate_clock, validate_clocks
from .diagnostics import (
    EvidenceDiagnostic,
    EvidenceError,
    bound_diagnostics,
    diagnostic,
)
from .limits import EvidenceLimits
from .planbinding import envelope_run_id, plan_identity
from .reader import EvidenceReader, read_run
from .schema import (
    OBLIGATION_KEYS,
    OBLIGATION_KINDS,
    canonical_bytes,
)
from .writer import EvidenceRun, preview_open_manifest

__all__ = ["EvidenceStore"]

_RUN_ID_PATTERN = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

_ACTIVE: set[str] = set()
_ACTIVE_LOCK = threading.Lock()


def _validate_run_id(run_id: Any, limits: EvidenceLimits) -> list[EvidenceDiagnostic]:
    if run_id is None or run_id == "":
        return [
            diagnostic(
                "ARGUS2-INPUT-AUTHORITY-MISSING",
                "a caller-supplied run identity is required",
                pointer="/runId",
                remediation="No identity is generated; supply the caller's run identity.",
            )
        ]
    if not isinstance(run_id, str) or _RUN_ID_PATTERN.match(run_id) is None:
        return [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "run identity fails the frozen identity pattern",
                pointer="/runId",
                remediation="Use a safe caller-supplied run identity.",
            )
        ]
    if len(run_id) > limits.max_id_length:
        return [
            diagnostic(
                "ARGUS2-BOUND-EXCEEDED",
                f"run identity exceeds max_id_length {limits.max_id_length}",
                pointer="/runId",
                remediation="Shorten the declared run identity.",
            )
        ]
    return []


def _validate_obligations(obligations: Any, limits: EvidenceLimits) -> tuple[list[dict[str, Any]], list[EvidenceDiagnostic]]:
    if obligations is None:
        obligations = ()
    if not isinstance(obligations, (list, tuple)):
        return [], [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "obligations must be an array",
                pointer="/obligations",
                remediation="Supply an array of declared obligations.",
            )
        ]
    diagnostics: list[EvidenceDiagnostic] = []
    if len(obligations) > limits.max_obligations:
        diagnostics.append(
            diagnostic(
                "ARGUS2-BOUND-EXCEEDED",
                f"obligation count exceeds max_obligations {limits.max_obligations}",
                pointer="/obligations",
                remediation="Reduce the declared obligations.",
            )
        )
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, obligation in enumerate(obligations):
        pointer = f"/obligations/{index}"
        if not isinstance(obligation, dict):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "obligation must be an object",
                    pointer=pointer,
                    remediation="Supply a frozen obligation object.",
                )
            )
            continue
        unknown = [key for key in obligation if key not in OBLIGATION_KEYS]
        if unknown:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"obligation carries unknown fields: {sorted(unknown)}",
                    pointer=pointer,
                    remediation="Use only the frozen obligation fields.",
                )
            )
        obligation_id = obligation.get("obligationId")
        if not isinstance(obligation_id, str) or obligation_id == "":
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-IDENTITY-MISSING",
                    "obligationId is required",
                    pointer=f"{pointer}/obligationId",
                    remediation="Supply a unique obligation identity.",
                )
            )
        elif obligation_id in seen:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "duplicate obligationId",
                    pointer=f"{pointer}/obligationId",
                    remediation="Obligation identities must be unique.",
                )
            )
        else:
            seen.add(obligation_id)
        kind = obligation.get("kind")
        if kind not in OBLIGATION_KINDS:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"obligation kind {kind!r} is outside the closed set",
                    pointer=f"{pointer}/kind",
                    remediation=f"Use one of {', '.join(OBLIGATION_KINDS)}.",
                )
            )
        if not isinstance(obligation.get("required"), bool):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "obligation required must be a boolean",
                    pointer=f"{pointer}/required",
                    remediation="Declare the required flag explicitly.",
                )
            )
        detail = obligation.get("detail")
        if "detail" in obligation and not isinstance(detail, dict):
            diagnostics.append(diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID", "obligation detail must be an object when present",
                pointer=f"{pointer}/detail", remediation="Omit optional detail or supply an object.",
            ))
        if kind == "min-observations":
            minimum = detail.get("minimum") if isinstance(detail, dict) else None
            if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum <= 0:
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-FIELD-INVALID",
                        "min-observations requires a positive integer detail.minimum",
                        pointer=f"{pointer}/detail/minimum",
                        remediation="Declare the caller's minimum observation count.",
                    )
                )
        snapshot = _admission_snapshot(obligation, pointer=pointer, diagnostics=diagnostics)
        if snapshot is not None:
            result.append(snapshot)
    return result, diagnostics


def _admission_snapshot(value: Any, *, pointer: str, diagnostics: list[EvidenceDiagnostic]) -> Any:
    """Return a deep, canonical-round-tripped snapshot of an admitted caller object.

    Non-JSON-encodable or non-finite content is rejected at admission; no caller-owned mutable
    reference is retained (``detailed-design.md`` section 14.1, ``ARGUS2-ADV-07``).
    """

    try:
        return json.loads(canonical_bytes(value))
    except (TypeError, ValueError, RecursionError):
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "admitted object is not JSON-encodable or contains a non-finite value",
                pointer=pointer,
                remediation="Supply a finite JSON-encodable value; no caller reference is retained.",
            )
        )
        return None


def _source_provenance(source_byte_digests: Any) -> tuple[dict[str, Any], list[EvidenceDiagnostic]]:
    if source_byte_digests is None:
        return {}, []
    if not isinstance(source_byte_digests, dict):
        return {}, [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "source_byte_digests must be an object map",
                pointer="/sourceByteProvenance",
                remediation="Supply name -> sha256 digest entries.",
            )
        ]
    result: dict[str, Any] = {}
    for name, value in source_byte_digests.items():
        if isinstance(value, str):
            result[str(name)] = {"algorithm": "sha256", "value": value}
        elif isinstance(value, dict) and value.get("algorithm") == "sha256" and isinstance(value.get("value"), str):
            result[str(name)] = {"algorithm": "sha256", "value": value["value"]}
        else:
            return {}, [
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"source-byte digest for {name!r} is malformed",
                    pointer="/sourceByteProvenance",
                    remediation="Supply a lowercase sha256 hex value or digest object.",
                )
            ]
    return result, []


def _metric_inputs(plan: dict[str, Any]) -> list[dict[str, Any]]:
    observers = {
        item.get("observerId"): item
        for item in plan.get("observers", [])
        if isinstance(item, dict) and isinstance(item.get("observerId"), str)
    }
    results: list[dict[str, Any]] = []
    for metric in plan.get("metrics", []):
        if not isinstance(metric, dict):
            continue
        observer_ids = [value for value in metric.get("observerIds", []) if isinstance(value, str)]
        sink_refs = [
            observers[observer_id].get("evidenceSinkRef")
            for observer_id in observer_ids
            if observer_id in observers and isinstance(observers[observer_id].get("evidenceSinkRef"), str)
        ]
        results.append(
            {
                "metricId": metric.get("metricId"),
                "observerIds": sorted(observer_ids),
                "calculationRef": metric.get("calculationRef"),
                "unitSemantics": metric.get("unitSemantics"),
                "timeDomainIds": list(metric.get("timeDomainIds", [])),
                "evidenceSinkRefs": sink_refs,
            }
        )
    results.sort(key=lambda item: str(item.get("metricId")))
    return results


class EvidenceStore:
    """Admission and read-only reconstruction entry points for bounded run evidence."""

    @classmethod
    def open_run(
        cls,
        root: Any,
        *,
        run_id: Any,
        plan: Any,
        run_envelope: Any = None,
        source_byte_digests: Any = None,
        limits: EvidenceLimits | None = None,
        obligations: Any = (),
        clocks: Any = None,
    ) -> EvidenceRun:
        """Open exactly one fresh run, or reject with stable diagnostics and no partial state."""

        effective = limits if limits is not None else EvidenceLimits()
        diagnostics: list[EvidenceDiagnostic] = []

        diagnostics.extend(_validate_run_id(run_id, effective))
        validated_obligations, obligation_diagnostics = _validate_obligations(obligations, effective)
        diagnostics.extend(obligation_diagnostics)

        plan_block = None
        if diagnostics:
            # Identity/obligation defects are reported without touching the plan or the filesystem.
            raise EvidenceError(bound_diagnostics(diagnostics, effective.max_diagnostic_count))

        plan_block, plan_diagnostics = plan_identity(plan)
        diagnostics.extend(plan_diagnostics)
        if diagnostics or plan_block is None:
            raise EvidenceError(bound_diagnostics(diagnostics, effective.max_diagnostic_count))

        declared_envelope_id = envelope_run_id(run_envelope)
        if declared_envelope_id is not None and declared_envelope_id != run_id:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-PLAN-ENVELOPE-CONFLICT",
                    "envelope run identity conflicts with the declared run identity",
                    pointer="/runEnvelope/runId",
                    remediation="Supply one consistent run identity; nothing is overwritten.",
                )
            )

        provenance, provenance_diagnostics = _source_provenance(source_byte_digests)
        if provenance_diagnostics:
            raise EvidenceError(bound_diagnostics(provenance_diagnostics, effective.max_diagnostic_count))

        declared_domains: frozenset[str] = frozenset()
        if clocks is not None:
            preserved_clocks, clock_diagnostics = validate_clocks(clocks, pointer="/clocks", limits=effective)
            if clock_diagnostics or preserved_clocks is None:
                raise EvidenceError(bound_diagnostics(clock_diagnostics, effective.max_diagnostic_count))
            declared_domains = frozenset(
                value["domain"] for value in preserved_clocks.values()
            )

        opened_at = None
        if isinstance(run_envelope, dict):
            candidate = run_envelope.get("openedAt")
            if isinstance(candidate, dict):
                validated_clock, clock_diagnostics = validate_clock(candidate, pointer="/runEnvelope/openedAt", limits=effective)
                if clock_diagnostics:
                    raise EvidenceError(bound_diagnostics(clock_diagnostics, effective.max_diagnostic_count))
                opened_at = validated_clock

        root_path = Path(root)
        registry_key = os.path.realpath(root_path)
        with _ACTIVE_LOCK:
            if registry_key in _ACTIVE:
                raise EvidenceError(
                    diagnostic(
                        "ARGUS2-STATE-WRITER-CONFLICT",
                        "a second owning writer was requested for the same run",
                        remediation="Exactly one owning writer may hold a run.",
                    )
                )
        if root_path.exists():
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-STATE-RUN-EXISTS",
                    "the run root already exists",
                    path=str(root_path),
                    remediation="An existing run root is never reused, reopened or overwritten.",
                )
            )

        metric_inputs = _metric_inputs(plan)
        preview = preview_open_manifest(
            run_id=run_id,
            plan_block=plan_block,
            source_byte_provenance=provenance,
            obligations=validated_obligations,
            limits=effective,
            opened_at=opened_at,
            metric_inputs=metric_inputs,
            clock_domains=sorted(declared_domains),
        )
        # AR-F03 enclosing depth: an obligation admitted at the standalone parse bound can exceed the
        # bounded nesting maximum once the manifest preview wraps it inside the manifest object and its
        # ``obligations`` array. Convert that bounded serializer failure into a stable ``EvidenceError``
        # (never an uncaught ``ValueError``/``RecursionError``) before any run root is created.
        try:
            preview_bytes = canonical_bytes(preview)
        except (ValueError, RecursionError):
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "admitted obligation nesting exceeds the bounded JSON nesting depth for the manifest preview",
                    pointer="/obligations",
                    remediation="Reduce the nesting depth; no run root is created and no state is claimed.",
                )
            ) from None
        # Preflight the same actual-byte bound as the publication chokepoint, including the manifest's
        # single trailing newline, so an over-bound open is refused before any run root is created.
        if len(preview_bytes) + 1 > effective.max_manifest_bytes:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-BOUND-EXCEEDED",
                    f"manifest would exceed max_manifest_bytes {effective.max_manifest_bytes}",
                    remediation="Reduce the manifest content or raise the caller bound.",
                )
            )

        try:
            os.mkdir(root_path, 0o777)
        except FileExistsError:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-STATE-RUN-EXISTS",
                    "the run root already exists",
                    path=str(root_path),
                    remediation="An existing run root is never reused.",
                )
            ) from None
        except OSError as error:
            raise EvidenceError(
                diagnostic(
                    "ARGUS2-IO-FAILURE",
                    f"run root could not be created: {error}",
                    path=str(root_path),
                    remediation="Resolve the filesystem failure.",
                )
            ) from error

        with _ACTIVE_LOCK:
            _ACTIVE.add(registry_key)

        try:
            run = EvidenceRun(
                root=root_path,
                run_id=run_id,
                plan_block=plan_block,
                source_byte_provenance=provenance,
                obligations=validated_obligations,
                limits=effective,
                declared_domains=declared_domains,
                opened_at=opened_at,
                registry_key=registry_key,
                unregister=_unregister,
                metric_inputs=metric_inputs,
                clock_domains=sorted(declared_domains),
            )
            return run
        except BaseException:
            _unregister(registry_key)
            raise

    @classmethod
    def read_run(cls, root: Any, *, limits: EvidenceLimits | None = None) -> EvidenceReader:
        """Return a bounded read-only reader for one run root."""

        return read_run(root, limits=limits)


def _unregister(registry_key: str) -> None:
    with _ACTIVE_LOCK:
        _ACTIVE.discard(registry_key)
