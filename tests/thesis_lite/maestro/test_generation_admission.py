"""Exact owner-supplied future contexts; admission never grants launch/consumption."""

from dataclasses import replace
from datetime import timedelta

import pytest
from xverse.maestro.admission import AdmissionError, permit_digest, validate_permits
from .test_admission import context, NOW


def initial():
    p, result, resources, bindings, approvals = context()
    return (
        p,
        result,
        resources,
        tuple(replace(b, generation=1) for b in bindings),
        tuple(replace(a, generation=1) for a in approvals),
    )


def future(ctx, index, generation):
    from xverse.maestro.admission import GenerationContext

    binding, approval = ctx[3][index], ctx[4][index]
    suffix = "-generation-" + str(generation)
    permit = replace(
        binding.permit,
        permit_id=binding.permit.permit_id + suffix,
        nonce=binding.permit.nonce + suffix,
    )
    binding = replace(
        binding,
        generation=generation,
        execution_id=binding.execution_id + suffix,
        permit=permit,
    )
    approval = replace(
        approval,
        generation=generation,
        execution_id=binding.execution_id,
        approval_ref=permit.approval_evidence_ref,
        permit_content_digest=permit_digest(permit),
    )
    return GenerationContext(binding, approval)


def checked(ctx, contexts, now=NOW):
    from xverse.maestro.admission import validate_generation_contexts

    return validate_generation_contexts(
        ctx[0],
        ctx[1],
        ctx[2],
        run_id="fixture-run",
        bindings=ctx[3],
        approvals=ctx[4],
        future_contexts=contexts,
        now=now,
    )


def test_future_contexts_are_pure_exact_consecutive_and_canonical(monkeypatch):
    import builtins
    import os
    import subprocess

    ctx = initial()
    a2 = future(ctx, 0, 2)
    a3 = future(ctx, 0, 3)
    b2 = future(ctx, 1, 2)

    def forbidden(*args, **kwargs):
        raise AssertionError("pure admission attempted an effect")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", forbidden)
        patch.setattr(os, "open", forbidden)
        patch.setattr(subprocess, "Popen", forbidden)
        result = checked(ctx, (a3, b2, a2))
    assert result == (a2, a3, b2)
    assert all(not c.ready_for_execution for c in result)


@pytest.mark.parametrize("kind", ["permit-id", "nonce", "execution"])
def test_future_identity_cannot_reuse_initial_or_other_future(kind):
    ctx = initial()
    value = future(ctx, 0, 2)
    binding = value.binding
    permit = binding.permit
    if kind == "execution":
        binding = replace(binding, execution_id=ctx[3][0].execution_id)
    else:
        permit = replace(
            permit,
            **{
                ("permit_id" if kind == "permit-id" else "nonce"): getattr(
                    ctx[3][0].permit, "permit_id" if kind == "permit-id" else "nonce"
                )
            },
        )
        binding = replace(binding, permit=permit)
    value = replace(
        value,
        binding=binding,
        approval=replace(
            value.approval,
            execution_id=binding.execution_id,
            permit_content_digest=permit_digest(binding.permit),
        ),
    )
    with pytest.raises(AdmissionError, match="REPLAY"):
        checked(ctx, (value,))


@pytest.mark.parametrize(
    "kind",
    ["gap", "duplicate", "unknown-unit", "boolean-generation", "initial-generation"],
)
def test_future_contexts_reject_wrong_unit_or_generation(kind):
    ctx = initial()
    value = future(ctx, 0, 2)
    if kind == "gap":
        values = (future(ctx, 0, 3),)
    elif kind == "duplicate":
        values = (value, value)
    else:
        value = replace(
            value,
            binding=replace(
                value.binding,
                **(
                    {"unit_id": "unknown"}
                    if kind == "unknown-unit"
                    else {"generation": True if kind == "boolean-generation" else 1}
                ),
            ),
        )
        values = (value,)
    with pytest.raises(AdmissionError):
        checked(ctx, values)


@pytest.mark.parametrize(
    "field",
    [
        "run_id",
        "execution_id",
        "generation",
        "lifecycle_digest",
        "plan_digest",
        "provider_id",
        "provider_kind",
        "provider_artifact_digest",
        "environment_identity",
        "permit_content_digest",
        "approval_ref",
        "issuer_label",
        "unit_id",
        "artifact_digests",
    ],
)
def test_future_approval_must_match_every_exact_original_pin(field):
    ctx = initial()
    value = future(ctx, 0, 2)
    bad = (
        3
        if field == "generation"
        else ("sha256:" + "9" * 64,)
        if field == "artifact_digests"
        else "forged"
    )
    value = replace(value, approval=replace(value.approval, **{field: bad}))
    with pytest.raises(AdmissionError):
        checked(ctx, (value,))


def test_future_expiry_is_revalidated_without_rewriting_initial_api():
    ctx = initial()
    value = future(ctx, 0, 2)
    value = replace(
        value, approval=replace(value.approval, expires_at=NOW + timedelta(seconds=1))
    )
    assert checked(ctx, (value,)) == (value,)
    with pytest.raises(AdmissionError, match="APPROVAL"):
        checked(ctx, (value,), now=NOW + timedelta(seconds=2))
    with pytest.raises(AdmissionError, match="GENERATION"):
        validate_permits(
            ctx[0],
            ctx[1],
            ctx[2],
            run_id="fixture-run",
            bindings=ctx[3],
            approvals=ctx[4],
            now=NOW,
            initial_generation=2,
        )


def test_joint_generation_capacity_is_not_a_new_permission():
    ctx = initial()
    values = tuple(future(ctx, 0, g) for g in range(2, 128))
    assert len(checked(ctx, values)) == 126
    with pytest.raises(AdmissionError, match="CAPACITY"):
        checked(ctx, values + (future(ctx, 0, 128),))
