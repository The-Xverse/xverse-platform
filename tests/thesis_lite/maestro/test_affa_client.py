"""Original typed transport over real BS17/AFFA; no M3 admission claim."""

from dataclasses import replace
import copy
import os
import signal
import threading

import pytest
from xverse.maestro.affa_client import AuthorityConnection
from xverse.maestro.affa_protocol import AuthorityFrame, AuthorityKind as K
from .test_run_bootstrap import (
    run_stack as run_stack,
    run_bootstrap_binary as run_bootstrap_binary,
)
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def connect(stack, monkeypatch, *, maximum_generation=None):
    session, manager, h, helper, _, _, _ = stack
    for unit in h.units:
        session.watch(unit["descriptor"], deadline(2))
    config = replace(
        h.config,
        scope=session.authority_scope,
        supervisor_session=session.authority_supervisor,
        units=tuple(
            replace(u, max_generation=maximum_generation) for u in h.config.units
        )
        if maximum_generation is not None
        else h.config.units,
    )
    client = session.authority(config, helper, deadline(2))
    assert type(client) is AuthorityConnection
    h.config = config

    def exchange(frame, fds=()):
        from .test_affa_native import WATCH_PLACEHOLDER
        if frame.kind is K.ADVANCE and fds and frame.ticket == WATCH_PLACEHOLDER:
            frame = replace(frame, ticket=client.watch_token(fds[0]))  # F-02: real supervisor token
        until = h.end()
        if frame.kind is K.RELEASE:
            until = min(until, h.units[frame.slot - 1]["ticket_end"])
        response = client._exchange(
            replace(
                frame,
                sequence=client.sequence + 1,
                deadline_ns=until,
                epoch=client.epoch,
            ),
            fds=fds,
        )
        if response.kind is K.CANCELLED:
            h.closed = True
        return response

    h.rpc = exchange
    for i, unit in enumerate(h.units):
        record = config.units[i]
        frame = AuthorityFrame(
            K.REGISTER,
            1,
            h.end(),
            config.scope,
            i + 1,
            config.epoch,
            1,
            first=record.binding,
            second=record.image,
            third=record.recipe,
            fourth=unit["boundary"],
        )
        assert (
            exchange(
                frame, (unit["cg"], h.image.descriptor, h.cwd, unit["recipe"])
            ).kind
            is K.REGISTERED
        )
    for i in range(2):
        assert exchange(h.frame(K.INTENT, i)).kind is K.INTENT_RECORDED
    return client


def test_typed_original_two_unit_lifecycle(run_stack, monkeypatch):
    client = connect(run_stack, monkeypatch)
    _, _, h, _, _, _, _ = run_stack
    for i in range(2):
        h.stage(i)
        h.arm(i)
        assert h.release(i).kind is K.RELEASED
    h.cancel()
    for i in range(2):
        h.stop_retire(i)
    assert client.epoch == 1 and len(client._pidfds) == 2


def test_client_refuses_a_copied_or_forked_holder(run_stack, monkeypatch):
    client = connect(run_stack, monkeypatch)
    with pytest.raises(TypeError):
        copy.copy(client)
    pid = os.fork()
    if pid == 0:
        try:
            with pytest.raises(ValueError):
                client._holder()
        except BaseException:
            os._exit(1)
        os._exit(0)
    assert os.waitpid(pid, 0)[1] == 0


def test_release_cannot_extend_original_arm_end(run_stack, monkeypatch):
    client = connect(run_stack, monkeypatch)
    _, _, h, _, _, _, _ = run_stack
    h.stage(0)
    h.arm(0)
    frame = replace(
        h.frame(K.RELEASE, 0),
        sequence=client.sequence + 1,
        deadline_ns=h.units[0]["ticket_end"] + 1,
        ticket=h.units[0]["ticket"],
    )
    before = client.sequence
    with pytest.raises(ValueError, match="TICKET-END"):
        client._exchange(frame)
    assert client.sequence == before


def test_independent_revocation_during_stopped_native_exchange(run_stack, monkeypatch):
    client = connect(run_stack, monkeypatch)
    session, _, h, _, _, _, _ = run_stack
    h.stage(0)
    child = client.child
    signal.pidfd_send_signal(child._capability.fileno(), signal.SIGSTOP)
    entered = threading.Event()
    original = client._receive
    errors = []

    def receive(*args, **kwargs):
        entered.set()
        return original(*args, **kwargs)

    monkeypatch.setattr(client, "_receive", receive)

    def query():
        try:
            h.rpc(h.frame(K.QUERY, 0))
        except ValueError as error:
            errors.append(str(error))

    thread = threading.Thread(target=query)
    thread.start()
    try:
        assert entered.wait(1)
        result = client.revoke(deadline(1))
        assert result.issuer_reaped and result.issuer_dead
        assert not result.workload_waits_known and not result.boundaries_released
    finally:
        thread.join(2)
    assert not thread.is_alive() and errors and session.latch.cancelled


@pytest.mark.parametrize(
    "change",
    [
        dict(sequence=99),
        dict(deadline_ns=1),
        dict(scope=b"x" * 32),
        dict(slot=2),
        dict(epoch=1),
        dict(generation=2),
        dict(operation=b"x" * 16),
        dict(first=b"x" * 32),
        dict(second=b"x" * 32),
        dict(third=b"x" * 32),
        dict(fourth=b"x" * 32),
        dict(handle=b"x" * 32),
        dict(state=512),
    ],
)
def test_uncorrelated_real_reply_revokes_original_issuer(
    run_stack, monkeypatch, change
):
    client = connect(run_stack, monkeypatch)
    _, _, h, _, _, _, _ = run_stack
    h.stage(0)
    original = client._receive

    def altered(until):
        response, fds = original(until)
        return replace(response, **change), fds

    monkeypatch.setattr(client, "_receive", altered)
    with pytest.raises(ValueError):
        h.rpc(h.frame(K.QUERY, 0))
    assert client._revoked and client.child._result is not None


def test_extra_reply_right_is_closed_and_issuer_revoked(run_stack, monkeypatch):
    client = connect(run_stack, monkeypatch)
    _, _, h, _, _, _, _ = run_stack
    h.stage(0)
    original = client._receive
    transferred = []

    def altered(until):
        response, fds = original(until)
        extra = os.dup(h.units[0]["cg"])
        transferred.append(extra)
        return response, fds + [extra]

    monkeypatch.setattr(client, "_receive", altered)
    with pytest.raises(ValueError, match="ACK-RIGHTS"):
        h.rpc(h.frame(K.QUERY, 0))
    assert client.child._result is not None
    with pytest.raises(OSError):
        os.fstat(transferred[0])


def test_advance_requires_actual_original_watched_C1_before_send(
    run_stack, monkeypatch
):
    client = connect(run_stack, monkeypatch)
    _, manager, h, helper, _, _, _ = run_stack
    frame = replace(
        h.frame(K.INTENT, 0),
        kind=K.ADVANCE,
        generation=2,
        sequence=client.sequence + 1,
        deadline_ns=h.end(),
        ticket=b"\x01" * 32,  # F-02: an ADVANCE carries a WATCH token; the UNWATCHED check still precedes it
    )
    before = client.sequence
    with pytest.raises(ValueError, match="UNWATCHED"):
        client._exchange(frame, fds=(manager._entry(helper).fd,))
    assert client.sequence == before and not client._revoked


def test_query_issued_retains_one_exact_original_pidfd(run_stack, monkeypatch):
    client = connect(run_stack, monkeypatch)
    _, _, h, _, _, _, _ = run_stack
    h.stage(0)
    token = h.units[0]["handle"]
    for _ in range(3):
        frame = replace(h.frame(K.QUERY, 0), kind=K.QUERY_ISSUED, handle=bytes(32))
        assert h.rpc(frame).handle == token
    assert len(client._pidfds) == 1


def test_expired_original_revoke_end_still_attempts_kill(run_stack, monkeypatch):
    import time
    from xverse.maestro.time import HostDeadline

    client = connect(run_stack, monkeypatch)
    signal.pidfd_send_signal(client.child._capability.fileno(), signal.SIGSTOP)
    result = client.revoke(
        HostDeadline(client.child._root.session, time.monotonic() - 0.01)
    )
    assert not result.issuer_reaped and result.diagnostic == "ML-AFFA-WAIT-UNRESOLVED"
    import select

    assert select.select([client.child._capability.fileno()], [], [], 1)[0]
