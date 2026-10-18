"""Actual M3 permit/journal consumers, independent of provider launch and Argus."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest

from xverse.maestro.admission import (
    AdmissionError,
    PermitApproval,
    PermitBinding,
    PermitSession,
    permit_digest,
    validate_permits,
)
from xverse.maestro.projection import prepare_lifecycle
from xverse_xdl.lifecycle import (
    EvidenceRecord,
    EvidenceWriteError,
    ExecutionPermit,
    FileEvidenceJournal,
    InMemoryEvidenceJournal,
    PermitClaimConflict,
)
from xverse_xdl.models import freeze

from .test_preparation import compiled, PIN

NOW = datetime(2026, 10, 18, 9, tzinfo=timezone.utc)


def context():
    result, resources = compiled()
    prepared = prepare_lifecycle(result, resources, provider_descriptors=(PIN,))
    bindings, approvals = [], []
    for index, unit in enumerate(prepared.units):
        plan = unit.plan
        permit = ExecutionPermit(
            permit_id=f"fixture-permit-{index}",
            nonce=f"private-test-nonce-{index}",
            plan_digest=plan.digest,
            catalog_identity=plan.catalog_identity,
            environment_identity=plan.environment_identity,
            permitted_actions=tuple(a.action_id for a in plan.actions),
            approval_evidence_ref=f"urn:xverse:test:approval:{index}",
            issuer_label="test-approval-owner",
            operation_classes=tuple(sorted({a.operation for a in plan.actions})),
            exclusions=("legacy-execution",),
            public_safety_classification="public-safe",
            not_before=NOW - timedelta(seconds=10),
            expires_at=NOW + timedelta(seconds=60),
        )
        binding = PermitBinding(unit.unit_id, f"fixture-execution-{index}", 0, permit)
        approval = PermitApproval(
            permit.approval_evidence_ref,
            permit.issuer_label,
            "fixture-run",
            unit.unit_id,
            binding.execution_id,
            0,
            prepared.lifecycle_digest,
            plan.digest,
            unit.provider.provider_id,
            unit.provider.kind,
            unit.provider.artifact_digest,
            plan.environment_identity,
            plan.artifact_digests,
            permit_digest(permit),
            NOW - timedelta(seconds=5),
            NOW + timedelta(seconds=30),
        )
        bindings.append(binding)
        approvals.append(approval)
    return prepared, result, resources, tuple(bindings), tuple(approvals)


def validate(
    ctx, *, bindings=None, approvals=None, now=NOW, run_id="fixture-run", prepared=None
):
    prepared0, result, resources, b, a = ctx
    return validate_permits(
        prepared or prepared0,
        result,
        resources,
        run_id=run_id,
        bindings=b if bindings is None else bindings,
        approvals=a if approvals is None else approvals,
        now=now,
    )


def session(ctx, path, *, now=NOW):
    prepared, result, resources, bindings, approvals = ctx
    return PermitSession(
        prepared,
        result,
        resources,
        run_id="fixture-run",
        bindings=bindings,
        approvals=approvals,
        now=now,
        journal=FileEvidenceJournal(path),
    )


def claim_record(*, execution="execution", permit="permit", nonce="nonce"):
    return EvidenceRecord(
        kind="intent",
        sequence=0,
        timestamp=NOW.isoformat(),
        execution_id=execution,
        action_id="start",
        catalog_identity="test-catalog",
        plan_digest="test-plan",
        permit_id=permit,
        permit_nonce=nonce,
        status="pending",
        environment_identity="test-fixture",
        resource_revisions=freeze({}),
        artifact_digests=(),
        selection=freeze({}),
    )


def test_all_exact_m3_permits_validate_without_effects(monkeypatch):
    import builtins
    import socket
    import threading

    ctx = context()

    def denied(*args, **kwargs):
        raise AssertionError("permit validation attempted an external effect")

    for owner, member in (
        (builtins, "open"),
        (Path, "open"),
        (socket, "socket"),
        (threading, "Lock"),
        (subprocess, "Popen"),
    ):
        monkeypatch.setattr(owner, member, denied)
    checked = validate(ctx)
    assert [row[0].unit_id for row in checked] == list(ctx[0].resource_order)


@pytest.mark.parametrize(
    "field,value,code",
    [
        (
            "permitted_actions",
            ("prepare", "start", "observe", "stop", "cleanup", "extra"),
            "ML-PERMIT-ACTIONS",
        ),
        (
            "operation_classes",
            ("validate", "start", "observe", "stop", "cleanup", "force"),
            "ML-PERMIT-OPERATIONS",
        ),
        ("environment_identity", "other", "ML-PERMIT-M3"),
        ("plan_digest", "other", "ML-PERMIT-M3"),
        ("catalog_identity", "other", "ML-PERMIT-M3"),
    ],
)
def test_surplus_scope_and_changed_m3_identity_reject(field, value, code):
    ctx = context()
    b = ctx[3]
    changed = replace(b[0], permit=replace(b[0].permit, **{field: value}))
    with pytest.raises(AdmissionError, match=code):
        validate(ctx, bindings=(changed, b[1]))


@pytest.mark.parametrize(
    "exclusions",
    [
        ("operation:start",),
        ("provider:maestro-fixture-v1",),
        ("realization:simulated",),
        ("unknown-expression",),
        ("legacy-execution", "legacy-execution"),
    ],
)
def test_conflicting_unknown_and_duplicate_exclusions_reject(exclusions):
    ctx = context()
    b = ctx[3]
    changed = replace(b[0], permit=replace(b[0].permit, exclusions=exclusions))
    with pytest.raises(AdmissionError, match="ML-PERMIT-EXCLUSION"):
        validate(ctx, bindings=(changed, b[1]))


@pytest.mark.parametrize(
    "exclusion", ["provider:maestro-process-v1", "realization:physical"]
)
def test_recognized_nonconflicting_exclusion_preserves_a_valid_fixture_permit(
    exclusion,
):
    ctx = context()
    bindings, approvals = ctx[3], ctx[4]
    permit = replace(bindings[0].permit, exclusions=("legacy-execution", exclusion))
    approval = replace(approvals[0], permit_content_digest=permit_digest(permit))
    checked = validate(
        ctx,
        bindings=(replace(bindings[0], permit=permit), bindings[1]),
        approvals=(approval, approvals[1]),
    )
    assert len(checked) == 2


@pytest.mark.parametrize("field", ["permit_id", "nonce"])
def test_duplicate_unit_permit_id_or_nonce_rejects(field):
    ctx = context()
    b = ctx[3]
    changed = replace(
        b[1], permit=replace(b[1].permit, **{field: getattr(b[0].permit, field)})
    )
    with pytest.raises(AdmissionError, match="ML-PERMIT-REPLAY"):
        validate(ctx, bindings=(b[0], changed))


def test_duplicate_execution_and_missing_unit_scope_reject():
    ctx = context()
    b = ctx[3]
    with pytest.raises(AdmissionError, match="ML-PERMIT-REPLAY"):
        validate(ctx, bindings=(b[0], replace(b[1], execution_id=b[0].execution_id)))
    with pytest.raises(AdmissionError, match="ML-PERMIT-SET"):
        validate(ctx, bindings=b[:1])
    with pytest.raises(AdmissionError, match="ML-PERMIT-SET"):
        validate(ctx, approvals=ctx[4][:1])


@pytest.mark.parametrize(
    "offset,code",
    [(-11, "ML-PERMIT-M3"), (60, "ML-PERMIT-M3"), (30, "ML-PERMIT-APPROVAL")],
)
def test_future_expired_permits_and_expired_approval_reject(offset, code):
    with pytest.raises(AdmissionError, match=code):
        validate(context(), now=NOW + timedelta(seconds=offset))


def test_naive_validity_time_rejects():
    with pytest.raises(AdmissionError, match="ML-PERMIT-TIME"):
        validate(context(), now=NOW.replace(tzinfo=None))


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", "other-run"),
        ("execution_id", "other-execution"),
        ("generation", 1),
        ("lifecycle_digest", "other"),
        ("plan_digest", "other"),
        ("provider_id", "maestro-process-v1"),
        ("provider_kind", "process"),
        ("provider_artifact_digest", "sha256:" + "2" * 64),
        ("environment_identity", "other"),
        ("artifact_digests", ("sha256:" + "3" * 64,)),
        ("approval_ref", "other-ref"),
        ("issuer_label", "other-issuer"),
        ("permit_content_digest", "other"),
    ],
)
def test_changed_owner_approval_facts_reject(field, value):
    ctx = context()
    approvals = ctx[4]
    with pytest.raises(AdmissionError, match="ML-PERMIT-APPROVAL"):
        validate(ctx, approvals=(replace(approvals[0], **{field: value}), approvals[1]))


def test_forged_prepared_plan_rejects_even_with_unchanged_public_digest():
    ctx = context()
    unit = ctx[0].units[0]
    forged = replace(
        ctx[0],
        units=(
            replace(unit, plan=replace(unit.plan, provider_id="forged")),
            ctx[0].units[1],
        ),
    )
    with pytest.raises(AdmissionError, match="ML-PERMIT-PLAN"):
        validate(ctx, prepared=forged)


def test_durable_claims_recheck_at_use_and_do_not_issue_launch_authority(tmp_path):
    ctx = context()
    path = tmp_path / "m3.jsonl"
    holder = session(ctx, path)
    assert holder.ready_for_execution is False
    receipt = holder.claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    assert receipt.status == "intent-durable" and receipt.m3_sequence == 1
    assert receipt.ready_for_execution is False
    saved = FileEvidenceJournal(path).records
    assert (
        len(saved) == 1 and saved[0].kind == "intent" and saved[0].status == "pending"
    )
    assert saved[0].handle_id is None
    with pytest.raises(AdmissionError, match="ML-PERMIT-REPLAY"):
        holder.claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    with pytest.raises(AdmissionError, match="ML-PERMIT-APPROVAL"):
        holder.claim_start_intent(
            ctx[0].units[1].unit_id, now=NOW + timedelta(seconds=30)
        )
    assert len(FileEvidenceJournal(path).records) == 1


def test_existing_intent_without_outcome_blocks_reopen_and_new_session(tmp_path):
    ctx = context()
    path = tmp_path / "m3.jsonl"
    session(ctx, path).claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    with pytest.raises(AdmissionError, match="ML-PERMIT-REPLAY"):
        session(ctx, path)


def test_failed_fsync_returns_no_receipt_and_surviving_intent_prevents_replay(
    tmp_path, monkeypatch
):
    import os

    ctx = context()
    path = tmp_path / "m3.jsonl"
    holder = session(ctx, path)
    original = os.fsync

    def failed(descriptor):
        if path.exists() and os.fstat(descriptor).st_ino == path.stat().st_ino:
            raise OSError("fixture intent fsync failure")
        return original(descriptor)

    monkeypatch.setattr(os, "fsync", failed)
    with pytest.raises(AdmissionError, match="ML-PERMIT-DURABILITY"):
        holder.claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    monkeypatch.setattr(os, "fsync", original)
    assert holder.claims_closed is True
    before = path.read_bytes()
    with pytest.raises(AdmissionError, match="ML-PERMIT-CLOSED"):
        holder.claim_start_intent(ctx[0].units[1].unit_id, now=NOW)
    assert path.read_bytes() == before
    assert FileEvidenceJournal(path).permit_consumed(
        ctx[3][0].permit.permit_id, ctx[3][0].permit.nonce
    )
    with pytest.raises(AdmissionError, match="ML-PERMIT-REPLAY"):
        session(ctx, path)


def test_public_m3_projection_and_receipt_withhold_nonce(tmp_path):
    from dataclasses import asdict

    ctx = context()
    path = tmp_path / "m3.jsonl"
    receipt = session(ctx, path).claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    public = json.dumps([asdict(receipt), FileEvidenceJournal(path).public_records()])
    assert ctx[3][0].permit.nonce not in public
    assert FileEvidenceJournal(path).public_records()[0]["permitNonce"] == "withheld"


@pytest.mark.parametrize("factory", [InMemoryEvidenceJournal, lambda: None])
def test_atomic_claim_conflicts_and_unknown_history_are_conservative(factory, tmp_path):
    journal = (
        factory()
        if factory is InMemoryEvidenceJournal
        else FileEvidenceJournal(tmp_path / "journal.jsonl")
    )
    record = claim_record()
    assert journal.claim_intent(record).sequence == 1
    for changed in (
        replace(record, execution_id="two"),
        replace(record, execution_id="two", permit_id="two"),
        replace(record, permit_id="two", permit_nonce="two"),
    ):
        with pytest.raises(PermitClaimConflict):
            journal.claim_intent(changed)
    assert len(journal.records) == 1
    journal.append(
        replace(record, permit_id="unknown", permit_nonce=None, execution_id="unknown")
    )
    with pytest.raises(EvidenceWriteError, match="unresolved nonce"):
        journal.claim_intent(claim_record(execution="new", permit="new", nonce="new"))


def test_actual_two_process_claims_have_one_fsynced_winner(tmp_path):
    path = tmp_path / "race.jsonl"
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("claim_worker.py")), str(path)],
        text=True,
        capture_output=True,
        timeout=25,
        check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert json.loads(result.stdout) == [["claimed", 1], ["conflict", None]]
    assert len(FileEvidenceJournal(path).records) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "outcome"},
        {"status": "started"},
        {"permit_nonce": None},
        {"execution_id": ""},
        {"handle_id": "fabricated"},
        {"timestamp": "2026-10-18T09:00:00"},
        {"sequence": False},
        {"sequence": 1.0},
    ],
)
def test_invalid_atomic_claims_never_consume(changes):
    journal = InMemoryEvidenceJournal()
    with pytest.raises(EvidenceWriteError):
        journal.claim_intent(replace(claim_record(), **changes))
    assert journal.records == ()


def test_boolean_approval_generation_and_mutable_scope_reject():
    ctx = context()
    with pytest.raises(AdmissionError, match="ML-PERMIT-APPROVAL"):
        validate(ctx, approvals=(replace(ctx[4][0], generation=False), ctx[4][1]))
    changed = replace(
        ctx[3][0].permit, permitted_actions=list(ctx[3][0].permit.permitted_actions)
    )
    with pytest.raises(AdmissionError, match="ML-PERMIT-TYPE"):
        validate(ctx, bindings=(replace(ctx[3][0], permit=changed), ctx[3][1]))
    with pytest.raises(AdmissionError, match="ML-PERMIT-TYPE"):
        validate(ctx, bindings=(replace(ctx[3][0], permit=None), ctx[3][1]))


def test_claim_rejects_malformed_durable_identity_without_new_bytes(tmp_path):
    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    journal.append(claim_record())
    data = json.loads(path.read_text())
    data["permitNonce"] = 42
    path.write_text(json.dumps(data) + "\n")
    before = path.read_bytes()
    with pytest.raises(EvidenceWriteError, match="invalid consumption nonce"):
        journal.claim_intent(claim_record(execution="new", permit="new", nonce="new"))
    assert path.read_bytes() == before


def test_claim_rejects_duplicate_json_keys_without_new_bytes(tmp_path):
    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    journal.append(claim_record())
    data = path.read_text().replace(
        '"kind":"intent"', '"kind":"intent","kind":"observation"'
    )
    assert data != path.read_text()
    path.write_text(data)
    before = path.read_bytes()
    with pytest.raises(EvidenceWriteError, match="duplicate evidence field"):
        journal.claim_intent(claim_record(execution="new", permit="new", nonce="new"))
    assert path.read_bytes() == before


@pytest.mark.parametrize("mutation", ["delete", "replace", "truncate", "change-prefix"])
def test_consumption_history_loss_or_replacement_never_resets_claims(
    tmp_path, mutation
):
    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    journal.claim_intent(claim_record())
    if mutation == "delete":
        path.unlink()
    elif mutation == "replace":
        path.rename(tmp_path / "original.jsonl")
        path.write_text("")
    elif mutation == "truncate":
        path.write_text("")
    else:
        path.write_text(path.read_text().replace('"permit"', '"forged"'))
    before = path.read_bytes() if path.exists() else None
    for holder in (journal, FileEvidenceJournal(path)):
        with pytest.raises(EvidenceWriteError):
            holder.claim_intent(
                claim_record(execution="new", permit="new", nonce="new")
            )
    assert (path.read_bytes() if path.exists() else None) == before


def test_claim_store_marker_cannot_be_silently_reinitialized(tmp_path):
    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    journal.claim_intent(claim_record())
    journal.lock_path.write_bytes(b"xverse-m3-claim-store-v1\n{partial")
    before = path.read_bytes()
    with pytest.raises(EvidenceWriteError, match="unresolved"):
        FileEvidenceJournal(path).claim_intent(
            claim_record(execution="new", permit="new", nonce="new")
        )
    assert path.read_bytes() == before


def test_claim_store_attribute_substitution_rejects(tmp_path):
    journal = FileEvidenceJournal(tmp_path / "original.jsonl")
    journal.path = tmp_path / "substitute.jsonl"
    with pytest.raises(EvidenceWriteError, match="path changed"):
        journal.claim_intent(claim_record())
    assert not journal.path.exists()


def test_partial_first_store_marker_blocks_without_consuming(tmp_path, monkeypatch):
    import os

    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    original = os.pwrite

    def partial(descriptor, data, offset):
        return original(descriptor, data[:9], offset)

    monkeypatch.setattr(os, "pwrite", partial)
    with pytest.raises(EvidenceWriteError, match="publication is uncertain"):
        journal.claim_intent(claim_record())
    monkeypatch.setattr(os, "pwrite", original)
    assert journal.records == ()
    with pytest.raises(EvidenceWriteError, match="unresolved"):
        FileEvidenceJournal(path).claim_intent(claim_record())


def test_post_intent_store_publication_failure_never_returns_a_success_receipt(
    tmp_path, monkeypatch
):
    import os

    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    original = os.pwrite
    count = 0

    def failed_second(descriptor, data, offset):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("fixture post-intent marker failure")
        return original(descriptor, data, offset)

    monkeypatch.setattr(os, "pwrite", failed_second)
    with pytest.raises(EvidenceWriteError, match="publication is uncertain"):
        journal.claim_intent(claim_record())
    monkeypatch.setattr(os, "pwrite", original)
    assert len(FileEvidenceJournal(path).records) == 1
    with pytest.raises(PermitClaimConflict):
        FileEvidenceJournal(path).claim_intent(claim_record())


def test_expiry_of_already_used_start_permission_does_not_block_a_fresh_unit(tmp_path):
    ctx = context()
    bindings, approvals = list(ctx[3]), list(ctx[4])
    permit = replace(bindings[0].permit, expires_at=NOW + timedelta(seconds=5))
    bindings[0] = replace(bindings[0], permit=permit)
    approvals[0] = replace(
        approvals[0],
        expires_at=NOW + timedelta(seconds=5),
        permit_content_digest=permit_digest(permit),
    )
    ctx = (*ctx[:3], tuple(bindings), tuple(approvals))
    path = tmp_path / "m3.jsonl"
    holder = session(ctx, path)
    holder.claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    journal = FileEvidenceJournal(path)
    # A fixture outcome resolves the first intent; no provider executes here.
    journal.append(
        replace(
            journal.records[0],
            kind="outcome",
            sequence=0,
            status="running",
            permit_nonce=None,
        )
    )
    receipt = holder.claim_start_intent(
        ctx[0].units[1].unit_id, now=NOW + timedelta(seconds=6)
    )
    assert receipt.m3_sequence == 3 and receipt.ready_for_execution is False


def test_first_claim_rechecks_all_initial_permits_at_the_actual_use_time(tmp_path):
    ctx = context()
    bindings, approvals = list(ctx[3]), list(ctx[4])
    permit = replace(bindings[1].permit, expires_at=NOW + timedelta(seconds=5))
    bindings[1] = replace(bindings[1], permit=permit)
    approvals[1] = replace(approvals[1], permit_content_digest=permit_digest(permit))
    ctx = (*ctx[:3], tuple(bindings), tuple(approvals))
    path = tmp_path / "m3.jsonl"
    holder = session(ctx, path)
    with pytest.raises(AdmissionError, match="ML-PERMIT-M3"):
        holder.claim_start_intent(
            ctx[0].units[0].unit_id, now=NOW + timedelta(seconds=6)
        )
    assert FileEvidenceJournal(path).records == ()


def test_fresh_permit_identities_do_not_adopt_an_unresolved_prior_scope(tmp_path):
    ctx = context()
    path = tmp_path / "m3.jsonl"
    session(ctx, path).claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    bindings, approvals = [], []
    for binding, approval in zip(ctx[3], ctx[4]):
        permit = replace(
            binding.permit,
            permit_id="new-" + binding.permit.permit_id,
            nonce="new-" + binding.permit.nonce,
        )
        binding = replace(
            binding, execution_id="new-" + binding.execution_id, permit=permit
        )
        bindings.append(binding)
        approvals.append(
            replace(
                approval,
                execution_id=binding.execution_id,
                permit_content_digest=permit_digest(permit),
            )
        )
    ctx = (*ctx[:3], tuple(bindings), tuple(approvals))
    before = path.read_bytes()
    with pytest.raises(AdmissionError, match="ML-PERMIT-UNRESOLVED"):
        session(ctx, path)
    assert path.read_bytes() == before


def test_consumption_read_failure_latches_the_original_session_closed(
    tmp_path, monkeypatch
):
    ctx = context()
    path = tmp_path / "m3.jsonl"
    holder = session(ctx, path)
    original = FileEvidenceJournal.records

    def failed(_):
        raise EvidenceWriteError("fixture read failure")

    monkeypatch.setattr(FileEvidenceJournal, "records", property(failed))
    with pytest.raises(AdmissionError, match="ML-PERMIT-DURABILITY"):
        holder.claim_start_intent(ctx[0].units[0].unit_id, now=NOW)
    monkeypatch.setattr(FileEvidenceJournal, "records", original)
    assert holder.claims_closed is True
    with pytest.raises(AdmissionError, match="ML-PERMIT-CLOSED"):
        holder.claim_start_intent(ctx[0].units[1].unit_id, now=NOW)
    assert FileEvidenceJournal(path).records == ()
