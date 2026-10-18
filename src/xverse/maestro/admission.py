"""Exact M3 permit validation and durable intent claims; no launch authority.

Approval facts must be supplied by the trusted admission owner. This library
does not authenticate an operator, invent approval, admit containment or create
a bootstrap permit. Its return values are not capabilities or launch tickets.
"""

from collections.abc import Iterable, Sequence
import copy
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
import hashlib
import json
import os

from xverse_xdl.experiment_plan import ExperimentPlanResult
from xverse_xdl.lifecycle import (
    EvidenceRecord,
    EvidenceWriteError,
    ExecutionPermit,
    FileEvidenceJournal,
    LifecycleError,
    PermitClaimConflict,
)
from xverse_xdl.models import NormalizedResource, freeze

from .projection import PreparedLifecycle, Unit, prepare_lifecycle


class AdmissionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _deny(code: str, message: str) -> None:
    raise AdmissionError(code, message)


def _identifier(value: str) -> None:
    if (
        type(value) is not str
        or not value.strip()
        or len(value) > 200
        or any(ord(c) < 32 for c in value)
    ):
        _deny("ML-PERMIT-IDENTITY", "invalid bounded identifier")


def _aware(now: datetime) -> None:
    if type(now) is not datetime or now.utcoffset() is None:
        _deny(
            "ML-PERMIT-TIME",
            "an explicit timezone-aware UTC validity observation is required",
        )


def permit_digest(permit: ExecutionPermit) -> str:
    """Private exact-content pin; never publish permit/nonce material."""

    _permit_shape(permit)
    body = asdict(permit)
    body["not_before"], body["expires_at"] = (
        permit.not_before.isoformat(),
        permit.expires_at.isoformat(),
    )
    encoded = json.dumps(
        body, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(b"xverse.maestro.private-permit.v1\0" + encoded).hexdigest()


def _permit_shape(permit: ExecutionPermit) -> None:
    if type(permit) is not ExecutionPermit:
        _deny("ML-PERMIT-TYPE", "an accepted M3 ExecutionPermit value is required")
    for name in (
        "permit_id",
        "nonce",
        "plan_digest",
        "catalog_identity",
        "environment_identity",
        "approval_evidence_ref",
        "issuer_label",
        "public_safety_classification",
    ):
        _identifier(getattr(permit, name))
    for name in ("permitted_actions", "operation_classes", "exclusions"):
        values = getattr(permit, name)
        if type(values) is not tuple or any(
            type(value) is not str or not value for value in values
        ):
            _deny(
                "ML-PERMIT-TYPE",
                "permit scope must use immutable tuples of identifiers",
            )
    _aware(permit.not_before)
    _aware(permit.expires_at)


def _approval_shape(approval: "PermitApproval") -> None:
    for name in approval.__dataclass_fields__:
        if name not in {"not_before", "expires_at", "generation", "artifact_digests"}:
            _identifier(getattr(approval, name))
    if type(approval.generation) is not int or approval.generation < 0:
        _deny("ML-PERMIT-APPROVAL", "approval generation must be an integer")
    if type(approval.artifact_digests) is not tuple or any(
        type(value) is not str for value in approval.artifact_digests
    ):
        _deny("ML-PERMIT-APPROVAL", "approval artifact pins must be immutable strings")


@dataclass(frozen=True)
class PermitBinding:
    unit_id: str
    execution_id: str
    generation: int
    permit: ExecutionPermit = field(repr=False)


@dataclass(frozen=True)
class PermitApproval:
    """Private facts supplied by the approval owner, not self-authenticating approval."""

    approval_ref: str
    issuer_label: str
    run_id: str
    unit_id: str
    execution_id: str
    generation: int
    lifecycle_digest: str
    plan_digest: str
    provider_id: str
    provider_kind: str
    provider_artifact_digest: str
    environment_identity: str
    artifact_digests: tuple[str, ...]
    permit_content_digest: str = field(repr=False)
    not_before: datetime
    expires_at: datetime


@dataclass(frozen=True)
class IntentReceipt:
    unit_id: str
    execution_id: str
    m3_sequence: int
    status: str = "intent-durable"

    @property
    def ready_for_execution(self) -> bool:
        return False


def _check_exclusions(permit: ExecutionPermit, unit: Unit) -> None:
    if len(set(permit.exclusions)) != len(permit.exclusions):
        _deny("ML-PERMIT-EXCLUSION", "duplicate exclusions are ambiguous")
    for exclusion in permit.exclusions:
        if exclusion == "legacy-execution":
            if unit.plan.selection.get("externalAssetRef") is not None:
                _deny("ML-PERMIT-EXCLUSION", "legacy artifact is excluded")
            continue
        category, sep, value = exclusion.partition(":")
        choices = {
            "operation": (
                {"validate", "start", "observe", "stop", "cleanup"},
                {a.operation for a in unit.plan.actions},
            ),
            "provider": (
                {"maestro-fixture-v1", "maestro-process-v1"},
                {unit.provider.provider_id},
            ),
            "realization": (
                {"simulated", "virtual", "physical", "hybrid"},
                {unit.plan.selection["realizationClass"]},
            ),
        }
        if not sep or category not in choices or value not in choices[category][0]:
            _deny(
                "ML-PERMIT-EXCLUSION", "unknown exclusion requires an explicit contract"
            )
        if value in choices[category][1]:
            _deny(
                "ML-PERMIT-EXCLUSION", "exclusion conflicts with the selected lifecycle"
            )


def _validate_one(
    prepared: PreparedLifecycle,
    run_id: str,
    unit: Unit,
    binding: PermitBinding,
    approval: PermitApproval,
    now: datetime,
    initial_generation: int = 0,
) -> None:
    _aware(now)
    _identifier(binding.execution_id)
    if type(binding.generation) is not int or binding.generation != initial_generation:
        _deny(
            "ML-PERMIT-GENERATION",
            "binding must match explicit initial generation; restart needs prior release evidence",
        )
    permit = binding.permit
    if type(permit) is not ExecutionPermit:
        _deny("ML-PERMIT-TYPE", "accepted M3 permit required")
    try:
        permit.validate(unit.plan, now)
    except LifecycleError as error:
        raise AdmissionError("ML-PERMIT-M3", error.diagnostic.code) from error
    if set(permit.permitted_actions) != {a.action_id for a in unit.plan.actions}:
        _deny(
            "ML-PERMIT-ACTIONS", "permit actions must equal the exact plan action set"
        )
    if set(permit.operation_classes) != {a.operation for a in unit.plan.actions}:
        _deny(
            "ML-PERMIT-OPERATIONS",
            "permit classes must equal the exact plan operation set",
        )
    _check_exclusions(permit, unit)
    _aware(approval.not_before)
    _aware(approval.expires_at)
    if (
        approval.not_before >= approval.expires_at
        or not approval.not_before <= now < approval.expires_at
    ):
        _deny(
            "ML-PERMIT-APPROVAL", "approval is outside its explicit validity interval"
        )
    expected = (
        permit.approval_evidence_ref,
        permit.issuer_label,
        run_id,
        unit.unit_id,
        binding.execution_id,
        binding.generation,
        prepared.lifecycle_digest,
        unit.plan.digest,
        unit.provider.provider_id,
        unit.provider.kind,
        unit.provider.artifact_digest,
        unit.plan.environment_identity,
        tuple(sorted(unit.plan.artifact_digests)),
        permit_digest(permit),
    )
    actual = (
        approval.approval_ref,
        approval.issuer_label,
        approval.run_id,
        approval.unit_id,
        approval.execution_id,
        approval.generation,
        approval.lifecycle_digest,
        approval.plan_digest,
        approval.provider_id,
        approval.provider_kind,
        approval.provider_artifact_digest,
        approval.environment_identity,
        tuple(sorted(approval.artifact_digests)),
        approval.permit_content_digest,
    )
    if actual != expected:
        _deny(
            "ML-PERMIT-APPROVAL",
            "approval facts do not bind this exact run/unit/permit/provider",
        )


def _verify_prepared(prepared, result, resources) -> None:
    if type(prepared) is not PreparedLifecycle:
        _deny("ML-PERMIT-PLAN", "exact PreparedLifecycle type required")
    pins = tuple({unit.provider for unit in prepared.units})
    recompiled = prepare_lifecycle(
        result, resources, provider_descriptors=pins, limits=prepared.limits
    )
    if recompiled != prepared:
        _deny("ML-PERMIT-PLAN", "prepared structure does not reproduce original XDL")


def _check_unresolved_intents(history, units) -> None:
    pending = {}
    for record in history:
        key = (record.execution_id, record.action_id)
        if record.kind == "intent":
            pending[key] = (record.catalog_identity, record.environment_identity)
        elif record.kind == "outcome":
            pending.pop(key, None)
    scopes = {
        (unit.plan.catalog_identity, unit.plan.environment_identity) for unit in units
    }
    if any(scope in scopes for scope in pending.values()):
        _deny(
            "ML-PERMIT-UNRESOLVED",
            "selected scope has an intent without an outcome; original-owner recovery is required",
        )


def validate_permits(
    prepared: PreparedLifecycle,
    result: ExperimentPlanResult,
    resources: Sequence[NormalizedResource],
    *,
    run_id: str,
    bindings: Iterable[PermitBinding],
    approvals: Iterable[PermitApproval],
    now: datetime,
    initial_generation: int = 0,
) -> tuple[tuple[Unit, PermitBinding, PermitApproval], ...]:
    """Pure whole-set validation; no journal, provider, writer or ticket is invoked."""

    _identifier(run_id)
    if type(initial_generation) is not int or initial_generation not in (0, 1):
        _deny(
            "ML-PERMIT-GENERATION", "only initial generation zero or one is supported"
        )
    _aware(now)
    _verify_prepared(prepared, result, resources)
    bindings, approvals = tuple(bindings), tuple(approvals)
    if any(type(item) is not PermitBinding for item in bindings) or any(
        type(item) is not PermitApproval for item in approvals
    ):
        _deny("ML-PERMIT-TYPE", "only inert binding/approval values are supported")
    for binding in bindings:
        _identifier(binding.unit_id)
        _identifier(binding.execution_id)
        _permit_shape(binding.permit)
    for approval in approvals:
        _approval_shape(approval)
    unit_ids = {u.unit_id for u in prepared.units}
    if (
        len(bindings) != len(unit_ids)
        or {b.unit_id for b in bindings} != unit_ids
        or len(approvals) != len(unit_ids)
        or {a.unit_id for a in approvals} != unit_ids
    ):
        _deny(
            "ML-PERMIT-SET",
            "exactly one permit and approval per declared unit is required",
        )
    if (
        len({b.permit.permit_id for b in bindings}) != len(bindings)
        or len({b.permit.nonce for b in bindings}) != len(bindings)
        or len({b.execution_id for b in bindings}) != len(bindings)
    ):
        _deny(
            "ML-PERMIT-REPLAY",
            "unit permit IDs, nonces and execution IDs must be unique",
        )
    by_unit = {b.unit_id: b for b in bindings}
    approval_by_unit = {a.unit_id: a for a in approvals}
    checked = []
    for unit in prepared.units:
        binding, approval = by_unit[unit.unit_id], approval_by_unit[unit.unit_id]
        _validate_one(
            prepared, run_id, unit, binding, approval, now, initial_generation
        )
        checked.append((unit, binding, approval))
    return tuple(checked)


class PermitSession:
    """Private coordinator-side permit context; durable claims grant no launch rights."""

    def __init__(
        self,
        prepared: PreparedLifecycle,
        result: ExperimentPlanResult,
        resources: Sequence[NormalizedResource],
        *,
        run_id: str,
        bindings: Iterable[PermitBinding],
        approvals: Iterable[PermitApproval],
        now: datetime,
        journal: FileEvidenceJournal,
        initial_generation: int = 0,
    ) -> None:
        if type(journal) is not FileEvidenceJournal:
            _deny("ML-PERMIT-JOURNAL", "actual durable M3 FileEvidenceJournal required")
        checked = validate_permits(
            prepared,
            result,
            resources,
            run_id=run_id,
            bindings=bindings,
            approvals=approvals,
            now=now,
            initial_generation=initial_generation,
        )
        for _, binding, _ in checked:
            if journal.permit_consumed(binding.permit.permit_id, binding.permit.nonce):
                _deny(
                    "ML-PERMIT-REPLAY",
                    "durable M3 history already consumed a unit permit",
                )
        _check_unresolved_intents(journal.records, prepared.units)
        self._prepared = prepared
        self._result = replace(result, plan=copy.deepcopy(result.plan))
        self._resources = tuple(resources)
        self._run_id = run_id
        self._checked = checked
        self._journal = journal
        self._has_claimed = False
        self._claims_closed = False
        self._original = self
        self._pid = os.getpid()
        self._initial_generation = initial_generation
        self._journal_pin = journal
        self._context_pin = (prepared, checked, run_id, initial_generation)
        self._issued: dict[int, tuple] = {}

    def _holder(self) -> None:
        if (
            self._original is not self
            or self._pid != os.getpid()
            or self._journal is not self._journal_pin
        ):
            _deny("ML-PERMIT-HOLDER", "original permit session and journal required")
        prepared, checked, run_id, generation = self._context_pin
        if (
            self._prepared is not prepared
            or self._checked is not checked
            or self._run_id != run_id
            or self._initial_generation != generation
        ):
            _deny("ML-PERMIT-HOLDER", "original permit context required")

    def revalidate_start_intent(self, receipt: IntentReceipt, *, now: datetime) -> None:
        """Revalidate only a genuine original claim; never consumes a fresh permit."""
        self._holder()
        saved = self._issued.get(id(receipt))
        if saved is None or saved[0] is not receipt or self._claims_closed:
            _deny("ML-PERMIT-RECEIPT", "original retained intent receipt required")
        _, stored, unit, binding, approval = saved
        _verify_prepared(self._prepared, self._result, self._resources)
        _validate_one(
            self._prepared,
            self._run_id,
            unit,
            binding,
            approval,
            now,
            self._initial_generation,
        )
        try:
            records = self._journal.records
            if not any(r.sequence == stored.sequence and r == stored for r in records):
                raise EvidenceWriteError("original durable claim no longer exists")
            if any(
                r.kind == "outcome"
                and (r.execution_id, r.action_id)
                == (stored.execution_id, stored.action_id)
                for r in records
            ):
                raise EvidenceWriteError(
                    "original intent already has a terminal outcome"
                )
        except (EvidenceWriteError, OSError) as error:
            self._claims_closed = True
            raise AdmissionError(
                "ML-PERMIT-DURABILITY", "original claim history is unavailable"
            ) from error

    def public_start_intent(self, receipt: IntentReceipt, *, now: datetime) -> dict:
        """Read the genuine journal's redacted projection of this original claim."""
        self.revalidate_start_intent(receipt, now=now)
        stored = self._issued[id(receipt)][1]
        try:
            matches = [
                record
                for record in self._journal.public_records()
                if record["sequence"] == stored.sequence
            ]
            if len(matches) != 1 or any(
                matches[0][key] != expected
                for key, expected in (
                    ("executionId", stored.execution_id),
                    ("actionId", stored.action_id),
                    ("kind", "intent"),
                )
            ):
                raise EvidenceWriteError(
                    "original public intent projection unavailable"
                )
            self.revalidate_start_intent(receipt, now=now)
            return copy.deepcopy(matches[0])
        except (EvidenceWriteError, OSError, KeyError, TypeError) as error:
            self._claims_closed = True
            raise AdmissionError(
                "ML-PERMIT-DURABILITY", "original public intent cannot be verified"
            ) from error

    @property
    def ready_for_execution(self) -> bool:
        return False

    @property
    def claims_closed(self) -> bool:
        return self._claims_closed

    def claim_start_intent(self, unit_id: str, *, now: datetime) -> IntentReceipt:
        """Revalidate at use, atomically persist intent, return only after fsync."""

        self._holder()
        if self._claims_closed:
            _deny(
                "ML-PERMIT-CLOSED",
                "durability failure has permanently closed this session's claims",
            )
        _aware(now)
        _verify_prepared(self._prepared, self._result, self._resources)
        if not self._has_claimed:
            # The first mutation follows a fresh check of all initial permits.
            checked = validate_permits(
                self._prepared,
                self._result,
                self._resources,
                run_id=self._run_id,
                bindings=(b for _, b, _ in self._checked),
                approvals=(a for _, _, a in self._checked),
                now=now,
                initial_generation=self._initial_generation,
            )
            try:
                _check_unresolved_intents(self._journal.records, self._prepared.units)
            except (EvidenceWriteError, OSError) as error:
                self._claims_closed = True
                raise AdmissionError(
                    "ML-PERMIT-DURABILITY", "consumption history cannot be verified"
                ) from error
        else:
            checked = self._checked
        selected = next(
            (entry for entry in checked if entry[0].unit_id == unit_id), None
        )
        if selected is None:
            _deny("ML-PERMIT-SET", "unknown unit requested")
        unit, binding, _ = selected
        _validate_one(
            self._prepared,
            self._run_id,
            unit,
            binding,
            selected[2],
            now,
            self._initial_generation,
        )
        permit, plan = binding.permit, unit.plan
        start = next(action for action in plan.actions if action.phase == "start")
        record = EvidenceRecord(
            kind="intent",
            sequence=0,
            timestamp=now.isoformat(),
            execution_id=binding.execution_id,
            action_id=start.action_id,
            catalog_identity=plan.catalog_identity,
            plan_digest=plan.digest,
            permit_id=permit.permit_id,
            permit_nonce=permit.nonce,
            status="pending",
            environment_identity=plan.environment_identity,
            resource_revisions=plan.resource_revisions,
            artifact_digests=plan.artifact_digests,
            selection=plan.selection,
            permit_issuer_label=permit.issuer_label,
            permit_operation_classes=permit.operation_classes,
            permit_exclusions=permit.exclusions,
            permit_public_safety_classification=permit.public_safety_classification,
            details=freeze(
                {
                    "maestroRunId": self._run_id,
                    "maestroUnitId": unit_id,
                    "generation": binding.generation,
                    "lifecycleDigest": self._prepared.lifecycle_digest,
                }
            ),
        )
        try:
            stored = self._journal.claim_intent(record)
        except PermitClaimConflict as error:
            raise AdmissionError(
                "ML-PERMIT-REPLAY", "M3 rejected the atomic intent claim"
            ) from error
        except EvidenceWriteError as error:
            self._claims_closed = True
            raise AdmissionError(
                "ML-PERMIT-DURABILITY",
                "intent persistence is failed or uncertain; no launch is authorized",
            ) from error
        self._has_claimed = True
        receipt = IntentReceipt(unit_id, binding.execution_id, stored.sequence)
        self._issued[id(receipt)] = (receipt, stored, unit, binding, selected[2])
        return receipt
