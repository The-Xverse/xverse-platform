"""Actual owned-child/Argus recovery; no real integration or physical effects claimed."""
# ruff: noqa: F811 -- pytest fixture imports are intentionally shadowed by arguments.

from dataclasses import replace
import hashlib
import json
import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.execution import (
    ExecutionInputError,
    HostRecoveryPermit,
    PublicExecutionService,
    RecoveryInspection,
    RecoveryProviderBinding,
    plan_lifecycle,
    prepare_execution,
)
from test_inspection import inputs  # noqa: F401
from test_runtime import runtime, start  # noqa: F401, F811
from test_planning import permit_for
from test_native_exchange import native, collect  # noqa: F401


def hashes(service, rid):
    paths = [
        service.root / (rid + ".claim.json"),
        *(service.root / (rid + ".argus")).rglob("*"),
    ]
    return {
        str(p.relative_to(service.root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
        if p.is_file()
    }


def successor(service, provider):
    return PublicExecutionService(
        service.root,
        service.host,
        (provider,),
        recovery_bindings=(
            RecoveryProviderBinding(provider.provider_id, provider.installation_digest),
        ),
    )


def grant(service, inspection, **changes):
    data = inspection.to_data()
    now = time.time()
    return replace(
        HostRecoveryPermit(
            "recovery-permit",
            inspection.inspection_digest,
            service.host.identity(),
            service.runtime_binding_digest,
            data["recoveryBindingDigest"],
            service.host.host_id,
            "explicit-owned-recovery-test",
            now - 1,
            now + 60,
        ),
        **changes,
    )


@pytest.fixture
def released(runtime):
    service, prepared, graph, permit, provider = runtime
    running = start(runtime)
    stopped = service.stop(
        prepared.submission.run_id, expected_version=running["stateVersion"]
    )
    assert stopped["cleanup"] == "released" and provider.child.observe() == "released"
    service.close()
    recovery = successor(service, provider)
    yield recovery, prepared, provider
    for run_id in list(
        recovery._runs
    ):  # failure-only disposal of original fixture handles
        value = recovery.read(run_id)
        if value["state"] not in ("stopped", "failed", "unknown"):
            recovery.stop(run_id, expected_version=value["stateVersion"])
    recovery.close()


def test_actual_released_predecessor_retirement_preserves_source_and_allows_distinct_new_run(
    released,
):
    service, prepared, provider = released
    rid = prepared.submission.run_id
    original = hashes(service, rid)
    calls = list(provider.calls)
    assert service.read(rid)["state"] == "unknown"
    inspection = service.inspect_recovery(rid)
    assert inspection.to_data()["eligible"], inspection.to_data()
    assert provider.calls == calls and hashes(service, rid) == original
    assert service.recovery_status(rid)["retirement"] == "absent"
    receipt = service.retire_released(inspection, grant(service, inspection))
    assert receipt.to_data()["inspection"]["identity"]["runId"] == rid
    assert hashes(service, rid) == original and provider.calls == calls
    assert service.retire_released(inspection, grant(service, inspection)) == receipt
    assert service.read(rid)["state"] == "unknown"
    assert service.recovery_status(rid)["retirement"] == "verified"
    new = prepare_execution(
        replace(prepared.submission, run_id="new-run-after-recovery"),
        service.host,
        (provider,),
    )
    graph = plan_lifecycle(
        new, provider.lifecycle_phases(new.providers[0].configuration, new)
    )
    running = service.start(
        new,
        graph,
        permit_for(new, service.host, graph, service),
        idempotency_key="distinct-start",
    )
    assert running["state"] == "running", running
    assert running["operationId"] != inspection.to_data()["identity"]["operationId"]
    stopped = service.stop(
        "new-run-after-recovery", expected_version=running["stateVersion"]
    )
    assert stopped["cleanup"] == "released" and hashes(service, rid) == original


@pytest.mark.parametrize("failure", ["fail_ready", "fail_after_launch"])
def test_actual_failed_start_and_failed_writer_are_eligible_only_after_compensation(
    runtime, failure
):
    old, prepared, _, _, provider = runtime
    setattr(provider, failure, True)
    result = start(runtime)
    assert result["state"] == "failed" and result["cleanup"] == "released"
    old.close()
    service = successor(old, provider)
    try:
        inspection = service.inspect_recovery(prepared.submission.run_id)
        data = inspection.to_data()
        assert data["eligible"], data
        assert (
            data["writerState"] == "failed"
            and data["recordedEvidenceStatus"] == "incomplete"
        )
        service.retire_released(inspection, grant(service, inspection))
        assert (
            service.recovery_status(prepared.submission.run_id)["retirement"]
            == "verified"
        )
    finally:
        service.close()


def test_unknown_cleanup_cannot_be_retired(runtime):
    old, prepared, _, _, provider = runtime
    running = start(runtime)
    provider.unknown_cleanup = True
    result = old.stop(
        prepared.submission.run_id, expected_version=running["stateVersion"]
    )
    assert result["cleanup"] == "unknown"
    old.close()
    service = successor(old, provider)
    try:
        inspection = service.inspect_recovery(prepared.submission.run_id)
        assert inspection.to_data()["eligible"] is False
        with pytest.raises(ExecutionInputError):
            service.retire_released(inspection, grant(service, inspection))
        assert not list(service.root.glob("*.retired.json"))
    finally:
        service.close()
        provider.unknown_cleanup = False


@pytest.mark.parametrize(
    "field,value",
    [
        ("inspection_digest", "sha256:" + "f" * 64),
        ("host_binding_digest", "sha256:" + "f" * 64),
        ("runtime_binding_digest", "sha256:" + "f" * 64),
        ("recovery_binding_digest", "sha256:" + "f" * 64),
        ("environment_id", "another-environment"),
        ("expires_at", 0),
    ],
)
def test_wrong_or_expired_permit_has_zero_effects(released, field, value):
    service, prepared, provider = released
    rid = prepared.submission.run_id
    before = hashes(service, rid)
    calls = list(provider.calls)
    inspection = service.inspect_recovery(rid)
    if field == "expires_at":
        permit = grant(
            service, inspection, not_before=time.time() - 60, expires_at=time.time() - 1
        )
    else:
        permit = grant(service, inspection, **{field: value})
    with pytest.raises(ExecutionInputError):
        service.retire_released(inspection, permit)
    assert hashes(service, rid) == before and provider.calls == calls
    assert not list(service.root.glob("*.retired.json"))


def test_forged_inspection_and_changed_source_fail_before_receipt(released):
    service, prepared, _ = released
    rid = prepared.submission.run_id
    inspection = service.inspect_recovery(rid)
    data = inspection.to_data()
    data["sourceWitness"] = "sha256:" + "f" * 64
    forged = RecoveryInspection(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    )
    with pytest.raises(ExecutionInputError, match="STALE"):
        service.retire_released(forged, grant(service, forged))
    claim = service.root / (rid + ".claim.json")
    claim.write_bytes(claim.read_bytes() + b" ")
    with pytest.raises(ExecutionInputError, match="STALE"):
        service.retire_released(inspection, grant(service, inspection))


def test_changed_evidence_invalidates_retirement_and_start(released):
    service, prepared, provider = released
    rid = prepared.submission.run_id
    inspection = service.inspect_recovery(rid)
    service.retire_released(inspection, grant(service, inspection))
    path = service.root / (rid + ".argus") / "manifest.json"
    path.write_bytes(path.read_bytes() + b" ")
    assert service.recovery_status(rid)["retirement"] == "unverified"
    new = prepare_execution(
        replace(prepared.submission, run_id="blocked-new-run"),
        service.host,
        (provider,),
    )
    graph = plan_lifecycle(
        new, provider.lifecycle_phases(new.providers[0].configuration, new)
    )
    calls = list(provider.calls)
    with pytest.raises(ExecutionInputError):
        service.start(
            new,
            graph,
            permit_for(new, service.host, graph, service),
            idempotency_key="new",
        )
    assert provider.calls == calls


def test_live_owner_and_busy_operations_do_not_produce_retirement(runtime):
    service, prepared, _, _, provider = runtime
    running = start(runtime)
    # Original live owner is present even when root inspection uses the same instance.
    service._recovery_bindings = (
        RecoveryProviderBinding(provider.provider_id, provider.installation_digest),
    )
    inspection = service.inspect_recovery(prepared.submission.run_id)
    assert inspection.to_data()["eligible"] is False
    service._operations.acquire()
    try:
        with pytest.raises(ExecutionInputError, match="BUSY"):
            service.inspect_recovery(prepared.submission.run_id)
    finally:
        service._operations.release()
    service.stop(prepared.submission.run_id, expected_version=running["stateVersion"])


def test_actual_concurrent_root_owner_cannot_be_opened(runtime):
    service, _, _, _, provider = runtime
    with pytest.raises(ExecutionInputError, match="ROOT-BUSY"):
        successor(service, provider)


def test_unconfigured_recovery_does_not_weaken_default_fence(released):
    configured, prepared, provider = released
    configured.close()
    default = PublicExecutionService(configured.root, configured.host, (provider,))
    try:
        with pytest.raises(ExecutionInputError, match="BINDING-REQUIRED"):
            default.inspect_recovery(prepared.submission.run_id)
        new = prepare_execution(
            replace(prepared.submission, run_id="default-blocked"),
            default.host,
            (provider,),
        )
        graph = plan_lifecycle(
            new, provider.lifecycle_phases(new.providers[0].configuration, new)
        )
        with pytest.raises(ExecutionInputError, match="OWNERSHIP-UNAVAILABLE"):
            default.start(
                new,
                graph,
                permit_for(new, default.host, graph, default),
                idempotency_key="default",
            )
    finally:
        default.close()


def rewrite_lifecycle(service, prepared, change):
    """Construct adversarial owned source with public Argus, not fabricated HTTP data."""
    root = service.root / (prepared.submission.run_id + ".argus")
    records = EvidenceStore.read_run(root).records()
    archived = root.with_suffix(".original")
    root.rename(archived)
    events = [
        r for r in records if "io.xverse.maestro.execution" in r.get("extensions", {})
    ]
    events = change(events)
    clock = events[0]["clocks"]["host"]
    writer = EvidenceStore.open_run(
        root,
        run_id=prepared.submission.run_id,
        plan=prepared.inspection.to_data()["plan"],
        clocks={"host": clock},
    )
    try:
        for index, row in enumerate(events, 1):
            writer.append_event(
                event_id=row["eventId"],
                producer_id=row["producerId"],
                producer_sequence=index,
                event_kind=row["eventKind"],
                correlation_id=row.get("correlationId"),
                causation_id=row.get("causationId"),
                clocks=row["clocks"],
                extensions=row["extensions"],
            )
        writer.finalize()
    except BaseException:
        writer.abort()
        raise


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-cleanup",
        "unknown-cleanup",
        "wrong-cause",
        "wrong-input",
        "missing-terminal",
        "duplicate-phase",
        "reordered-cleanup",
        "false-stopped",
        "unknown-extension",
        "false-failure",
        "missing-readiness",
    ],
)
def test_structurally_valid_argus_cannot_hide_bad_lifecycle_compensation(
    released, mutation
):
    from copy import deepcopy

    service, prepared, provider = released

    def change(rows):
        rows = deepcopy(rows)

        def selected(kind):
            return [
                r
                for r in rows
                if r["extensions"]["io.xverse.maestro.execution"]["kind"] == kind
            ]

        if mutation == "missing-cleanup":
            rows.remove(selected("cleanup-outcome")[0])
        elif mutation == "unknown-cleanup":
            selected("cleanup-outcome")[0]["extensions"]["io.xverse.maestro.execution"][
                "outcome"
            ] = "unknown"
        elif mutation == "wrong-cause":
            selected("cleanup-outcome")[0]["causationId"] = rows[0]["eventId"]
        elif mutation == "wrong-input":
            selected("phase-intent")[0]["extensions"]["io.xverse.maestro.execution"][
                "inputSemanticDigest"
            ] = "sha256:" + "f" * 64
        elif mutation == "missing-terminal":
            rows.remove(selected("run-terminal")[0])
        elif mutation == "duplicate-phase":
            selected("phase-intent")[1]["extensions"]["io.xverse.maestro.execution"][
                "phaseId"
            ] = selected("phase-intent")[0]["extensions"][
                "io.xverse.maestro.execution"
            ]["phaseId"]
        elif mutation == "reordered-cleanup":
            a, b = selected("cleanup-intent")[:2]
            i, j = rows.index(a), rows.index(b)
            rows[i], rows[j] = rows[j], rows[i]
        elif mutation == "false-stopped":
            rows.remove(selected("run-running")[0])
        elif mutation == "unknown-extension":
            selected("phase-intent")[0]["extensions"]["io.xverse.maestro.execution"][
                "unknownExecutableSemantics"
            ] = True
        elif mutation == "false-failure":
            selected("run-terminal")[0]["extensions"]["io.xverse.maestro.execution"][
                "outcome"
            ] = "failed"
        elif mutation == "missing-readiness":
            next(
                r
                for r in selected("phase-outcome")
                if r["extensions"]["io.xverse.maestro.execution"]["operation"]
                == "ready"
            )["extensions"]["io.xverse.maestro.execution"]["readinessKind"] = None
        return rows

    rewrite_lifecycle(service, prepared, change)
    reader = EvidenceStore.read_run(
        service.root / (prepared.submission.run_id + ".argus")
    )
    assert not reader.diagnostics, [(d.code, d.message) for d in reader.diagnostics]
    calls = list(provider.calls)
    inspection = service.inspect_recovery(prepared.submission.run_id)
    assert inspection.to_data()["eligible"] is False
    with pytest.raises(ExecutionInputError):
        service.retire_released(inspection, grant(service, inspection))
    assert provider.calls == calls and not list(service.root.glob("*.retired.json"))


def test_actual_cancel_during_acquisition_keeps_failed_writer_and_explicit_release(
    runtime,
):
    old, prepared, _, _, provider = runtime
    original = provider.dispatch
    entered = threading.Event()
    release = threading.Event()
    results = []

    def dispatch(phase, effective, context):
        result = original(phase, effective, context)
        if phase.operation == "start":
            entered.set()
            assert release.wait(3)
            raise ExecutionInputError("MPX-START-CANCELLED")
        return result

    provider.dispatch = dispatch
    starter = threading.Thread(target=lambda: results.append(start(runtime)))
    starter.start()
    assert entered.wait(5)
    snapshot = old.read(prepared.submission.run_id)
    stopper = threading.Thread(
        target=lambda: old.stop(
            prepared.submission.run_id, expected_version=snapshot["stateVersion"]
        )
    )
    stopper.start()
    deadline = time.monotonic() + 2
    while (
        old.read(prepared.submission.run_id)["stopOperationId"] is None
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    release.set()
    starter.join(5)
    stopper.join(5)
    assert not starter.is_alive() and not stopper.is_alive()
    assert (
        results[0]["cleanup"] == "released"
        and results[0]["failureCode"] == "MPX-START-CANCELLED"
    )
    old.close()
    service = successor(old, provider)
    try:
        inspection = service.inspect_recovery(prepared.submission.run_id)
        assert inspection.to_data()["eligible"], inspection.to_data()
        service.retire_released(inspection, grant(service, inspection))
    finally:
        service.close()


def test_interrupted_publication_leaves_no_receipt_and_retry_is_safe(
    released, monkeypatch
):
    import xverse.maestro.execution.recovery as recovery

    service, prepared, provider = released
    rid = prepared.submission.run_id
    inspection = service.inspect_recovery(rid)
    before = hashes(service, rid)
    calls = list(provider.calls)

    def fail(*args, **kwargs):
        raise PermissionError("private filesystem message must not leak")

    with monkeypatch.context() as patch:
        patch.setattr(recovery.os, "link", fail)
        with pytest.raises(ExecutionInputError, match="WRITE-FAILED"):
            service.retire_released(inspection, grant(service, inspection))
    assert not list(service.root.glob("*.retired.json"))
    assert not list(service.root.glob(".recovery-*.tmp"))
    assert hashes(service, rid) == before and provider.calls == calls
    service.retire_released(inspection, grant(service, inspection))
    assert service.recovery_status(rid)["retirement"] == "verified"


def test_receipt_corruption_cannot_authorize_new_start(released):
    service, prepared, _ = released
    inspection = service.inspect_recovery(prepared.submission.run_id)
    service.retire_released(inspection, grant(service, inspection))
    path = next(service.root.glob("*.retired.json"))
    data = json.loads(path.read_bytes())
    data["retiredAt"] += 1
    path.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())
    assert (
        service.recovery_status(prepared.submission.run_id)["retirement"]
        == "unverified"
    )


def test_declared_installation_change_does_not_reuse_existing_receipt(released):
    service, prepared, provider = released
    inspection = service.inspect_recovery(prepared.submission.run_id)
    service.retire_released(inspection, grant(service, inspection))
    service._recovery_bindings = (
        RecoveryProviderBinding(provider.provider_id, "sha256:" + "e" * 64),
    )
    assert service.recovery_status(prepared.submission.run_id)["retirement"] == "absent"
    new = prepare_execution(
        replace(prepared.submission, run_id="pin-mismatch-run"),
        service.host,
        (provider,),
    )
    graph = plan_lifecycle(
        new, provider.lifecycle_phases(new.providers[0].configuration, new)
    )
    with pytest.raises(ExecutionInputError, match="INSTALLATION-MISMATCH"):
        service.start(
            new,
            graph,
            permit_for(new, service.host, graph, service),
            idempotency_key="pin-mismatch",
        )


def test_failed_root_fsync_retry_repeats_durability_step(released, monkeypatch):
    import xverse.maestro.execution.recovery as recovery

    service, prepared, _ = released
    inspection = service.inspect_recovery(prepared.submission.run_id)
    original = recovery.os.fsync

    def failed(fd):
        if fd == service._root_fd:
            raise OSError("interrupted root synchronization")
        return original(fd)

    with monkeypatch.context() as patch:
        patch.setattr(recovery.os, "fsync", failed)
        with pytest.raises(ExecutionInputError, match="WRITE-FAILED"):
            service.retire_released(inspection, grant(service, inspection))
    assert len(list(service.root.glob("*.retired.json"))) == 1
    calls = []

    def synced(fd):
        calls.append(fd)
        return original(fd)

    with monkeypatch.context() as patch:
        patch.setattr(recovery.os, "fsync", synced)
        receipt = service.retire_released(inspection, grant(service, inspection))
    assert service._root_fd in calls
    assert receipt.to_data()["authorization"]["scope"] == "owned-simulation-recovery"


def test_altered_persisted_grant_is_rejected_even_with_recomputed_receipt_digest(
    released,
):
    from xverse.maestro.execution.inspection import canonical, sha256

    service, prepared, _ = released
    inspection = service.inspect_recovery(prepared.submission.run_id)
    service.retire_released(inspection, grant(service, inspection))
    path = next(service.root.glob("*.retired.json"))
    value = json.loads(path.read_bytes())
    value["authorization"]["inspection_digest"] = "sha256:" + "f" * 64
    value["receiptDigest"] = sha256(
        canonical({k: v for k, v in value.items() if k != "receiptDigest"})
    )
    path.write_bytes(canonical(value))
    assert (
        service.recovery_status(prepared.submission.run_id)["retirement"]
        == "unverified"
    )


def test_unknown_claim_fields_do_not_become_recovery_authority(released):
    service, prepared, _ = released
    path = service.root / (prepared.submission.run_id + ".claim.json")
    value = json.loads(path.read_bytes())
    value["unknownOwnershipSemantics"] = True
    path.write_text(json.dumps(value))
    assert (
        service.inspect_recovery(prepared.submission.run_id).to_data()["eligible"]
        is False
    )


@pytest.mark.parametrize(
    "native",
    [{"native-observer-capacity": 1, "native-observer-deferred": True}],
    indirect=True,
)
def test_actual_cpp_observer_loss_does_not_replace_released_lifecycle_evidence(native):
    old, prepared, provider, started = native
    collected = collect(native)
    terminal = old.stop(started["runId"], expected_version=collected["stateVersion"])
    assert terminal["cleanup"] == "released"
    old.close()
    service = successor(old, provider)
    try:
        inspection = service.inspect_recovery(started["runId"])
        data = inspection.to_data()
        assert data["eligible"], data
        assert (
            data["recordedEvidenceStatus"]
            == data["assessedEvidenceStatus"]
            == "incomplete"
        )
        assert data["diagnostics"]
        service.retire_released(inspection, grant(service, inspection))
        assert service.read(started["runId"])["state"] == "unknown"
    finally:
        service.close()


@pytest.mark.parametrize(
    "changes",
    [
        {"scope": "physical"},
        {"permit_id": "../escape"},
        {"approval_reference": ""},
        {"not_before": float("nan")},
        {"expires_at": float("inf")},
    ],
)
def test_invalid_host_grants_cannot_create_a_retirement(released, changes):
    service, prepared, _ = released
    inspection = service.inspect_recovery(prepared.submission.run_id)
    with pytest.raises(ExecutionInputError, match="PERMIT-INVALID"):
        grant(service, inspection, **changes)
    assert not list(service.root.glob("*.retired.json"))


@pytest.mark.parametrize("fault", ["truncated-stream", "open-writer"])
def test_corrupt_or_open_original_source_is_not_eligible(released, fault):
    service, prepared, _ = released
    root = service.root / (prepared.submission.run_id + ".argus")
    if fault == "truncated-stream":
        path = root / "events.jsonl"
        path.write_bytes(path.read_bytes()[:-7])
    else:
        path = root / "manifest.json"
        value = json.loads(path.read_bytes())
        value["writerState"] = "open"
        path.write_text(json.dumps(value))
    inspection = service.inspect_recovery(prepared.submission.run_id)
    assert inspection.to_data()["eligible"] is False
    with pytest.raises(ExecutionInputError):
        service.retire_released(inspection, grant(service, inspection))
    assert not list(service.root.glob("*.retired.json"))


def test_source_change_during_publication_is_not_accepted(released, monkeypatch):
    import xverse.maestro.execution.recovery as recovery

    service, prepared, _ = released
    rid = prepared.submission.run_id
    inspection = service.inspect_recovery(rid)
    original = recovery.inspect
    count = [0]

    def changed(*args):
        count[0] += 1
        if count[0] == 2:
            path = service.root / (rid + ".claim.json")
            path.write_bytes(path.read_bytes() + b" ")
        return original(*args)

    monkeypatch.setattr(recovery, "inspect", changed)
    with pytest.raises(ExecutionInputError, match="SOURCE-CHANGED"):
        service.retire_released(inspection, grant(service, inspection))
    assert not list(service.root.glob("*.retired.json"))
    assert not list(service.root.glob(".recovery-*.tmp"))


def test_reader_budget_is_enforced_before_public_reader(released, monkeypatch):
    import xverse.maestro.execution.recovery as recovery

    service, prepared, _ = released
    monkeypatch.setattr(recovery, "MAX_SOURCE", 1)
    monkeypatch.setattr(
        recovery.EvidenceStore,
        "read_run",
        lambda *args, **kwargs: pytest.fail("Oversized source reached reader"),
    )
    assert service.inspect_recovery(prepared.submission.run_id).to_data()[
        "reasons"
    ] == ["MRX-SOURCE-LIMIT"]
