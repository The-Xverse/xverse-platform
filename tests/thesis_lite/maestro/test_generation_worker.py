"""Original BS17/storage/AFFA admission of future contexts, without restart claims."""

from dataclasses import asdict, replace
import json

import pytest
from xverse.argus.schema import canonical_bytes
from xverse.maestro.admission import GenerationContext, permit_digest
from xverse.maestro.persistence import _plain
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def successor(binding, approval, generation):
    suffix = "-future-" + str(generation)
    permit = replace(
        binding.permit,
        permit_id=binding.permit.permit_id + suffix,
        nonce=binding.permit.nonce + suffix,
        approval_evidence_ref=binding.permit.approval_evidence_ref + suffix,
    )
    binding = replace(
        binding,
        execution_id=binding.execution_id + suffix,
        generation=generation,
        permit=permit,
    )
    approval = replace(
        approval,
        execution_id=binding.execution_id,
        generation=generation,
        approval_ref=permit.approval_evidence_ref,
        permit_content_digest=permit_digest(permit),
    )
    return GenerationContext(binding, approval)


def prepare(request, monkeypatch, mode="valid"):
    from . import test_launcher

    encode = test_launcher.encode_configuration
    retained = {}

    def configured(*args, **kwargs):
        if mode == "default":
            original = encode(*args, **kwargs)
            explicit = encode(*args, **kwargs, future_contexts=())
            assert original.private_bytes == explicit.private_bytes
            retained["config"] = explicit
            return explicit
        futures = tuple(
            successor(b, a, g)
            for b, a in zip(kwargs["bindings"], kwargs["approvals"])
            for g in (2, 3)
        )
        config = encode(*args, **kwargs, future_contexts=futures)
        data = json.loads(config.private_bytes)
        if mode == "approval":
            first = replace(
                config.future_contexts[0],
                approval=replace(
                    config.future_contexts[0].approval,
                    provider_artifact_digest="sha256:" + "8" * 64,
                ),
            )
            config = replace(
                config, future_contexts=(first, *config.future_contexts[1:])
            )
            data["future_contexts"][0]["approval"] = _plain(asdict(first.approval))
        elif mode == "extra":
            data["future_contexts"][0]["extra"] = "forbidden"
        elif mode == "empty":
            data["future_contexts"] = []
            config = replace(config, future_contexts=())
        elif mode == "v1-future":
            data["version"] = 1
        elif mode == "v2-missing":
            data.pop("future_contexts")
            config = replace(config, future_contexts=())
        config = replace(config, private_bytes=canonical_bytes(data))
        retained["config"] = config
        return config

    monkeypatch.setattr(test_launcher, "encode_configuration", configured)
    return retained


def test_actual_original_worker_retains_future_contexts_without_consuming_them(
    request, monkeypatch
):
    retained = prepare(request, monkeypatch)
    stack = request.getfixturevalue("broker_stack")
    broker, facade, client, work = stack
    config = retained["config"]
    assert json.loads(config.private_bytes)["version"] == 2
    assert (
        len(client._future_contexts) == 4
        and client._future_contexts is config.future_contexts
    )
    original_process = client.process
    end = stage_all(stack)
    for unit in broker.owner._prepared.resource_order:
        issuer = broker.issuer(unit)
        assert facade.start(
            unit, issuer.recipe.descriptor, broker.connection, end
        ).ready
    journal = FileEvidenceJournal(work.parent / "m3.jsonl")
    assert {r.details["generation"] for r in journal.records} == {1}
    for context in config.future_contexts:
        permit = context.binding.permit
        assert not journal.permit_consumed(permit.permit_id, permit.nonce)
    assert client.process is original_process and not client._failed


def test_future_permit_cannot_be_consumed_through_initial_commit_rpc(
    request, monkeypatch
):
    retained = prepare(request, monkeypatch)
    broker, _, client, work = request.getfixturevalue("broker_stack")
    context = retained["config"].future_contexts[0]
    before = FileEvidenceJournal(work.parent / "m3.jsonl").records
    with pytest.raises(ValueError):
        client._rpc(
            "commit", {"unit": context.binding.unit_id, "generation": 2}, deadline(0.5)
        )
    journal = FileEvidenceJournal(work.parent / "m3.jsonl")
    assert journal.records == before
    assert not journal.permit_consumed(
        context.binding.permit.permit_id, context.binding.permit.nonce
    )


@pytest.mark.parametrize(
    "mode", ["approval", "extra", "empty", "v1-future", "v2-missing"]
)
def test_malformed_sealed_future_context_never_opens_journal_or_writer(
    request, monkeypatch, mode
):
    retained = prepare(request, monkeypatch, mode)
    with pytest.raises(ValueError):
        request.getfixturevalue("broker_stack")
    data = json.loads(retained["config"].private_bytes)
    from pathlib import Path

    assert not Path(data["journal_path"]).exists()
    assert not Path(data["evidence_root"]).exists()


def test_default_empty_future_context_preserves_original_version1_bytes(
    request, monkeypatch
):
    retained = prepare(request, monkeypatch, "default")
    _, _, client, _ = request.getfixturevalue("broker_stack")
    data = json.loads(retained["config"].private_bytes)
    assert data["version"] == 1 and "future_contexts" not in data
    assert client._future_contexts == ()
