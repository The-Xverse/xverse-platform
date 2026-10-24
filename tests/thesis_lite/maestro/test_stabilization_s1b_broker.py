"""S1b broker, teardown and schedule (FR-009, FR-010): the two-step TERM, stderr admission and budgets.

Real BS17/AF17 broker stacks (``test_run_broker.broker_stack``) with S1b controls declared in the actual
v0.2 catalog payload. Design: ``design-stabilization-s1b.md``.
"""

from dataclasses import replace
import os
from pathlib import Path
import time

import pytest
from xverse.maestro.affa_protocol import AuthorityRecipe
from xverse.maestro.owner import OwnerError
from xverse.maestro.run_broker import UnitAdmission
from xverse.maestro.teardown import ReverseTeardown
from xverse_xdl.catalog import ProcessControls
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline

NS = "io.xverse.runtime.compatibility"


def declare(monkeypatch, controls, *, stderr=None, maximum_generation=3):
    """Declare S1b controls per binding id in the actual v0.2 catalog payload (before broker_stack runs).

    controls: {binding_id: dict(stop=seconds, stderr=bytes, condition=..., mode=..., cwd=name,
    stale=True|"aside"|"link", observe_timeout=seconds)}.
    stderr: {unit binding_id: directory path} for UnitAdmission.stderr_directory.
    """
    from . import test_launcher, test_run_broker

    original = test_launcher.compiled

    def compiled(docs):
        profile = docs["runtime-profile.json"]
        profile["metadata"]["version"] = "0.2.0"
        profile["spec"]["schemaRef"] = "https://xverse.io/profiles/runtime-compatibility/v0.2/schema.json"
        for binding in docs["deployment.json"]["spec"]["bindings"]:
            payload = binding["extensions"][NS]
            payload["schemaVersion"] = "0.2.0"
            wanted = controls.get(binding["id"], {})
            process = payload["process"]
            if "stop" in wanted:
                process["stop"] = {"graceSeconds": wanted["stop"]}
            if "stderr" in wanted:
                process["stderr"] = {"capture": "run-scoped-private", "maximumBytes": wanted["stderr"]}
            if "mode" in wanted:
                process["arguments"][1] = wanted["mode"]
            if "cwd" in wanted:  # a name inside the shared work directory, or an absolute path
                cwd = Path(process["workingDirectory"]) / wanted["cwd"]
                cwd.mkdir(mode=0o700, exist_ok=True)
                process["workingDirectory"] = str(cwd)
                stale = wanted.get("stale")
                if stale is True:
                    (cwd / ".xverse-ready").mkdir(mode=0o700)
                elif stale == "aside":
                    (cwd / ".xverse-ready.g1").mkdir(mode=0o700)
                elif stale == "link":
                    os.symlink(cwd / "absent-target", cwd / ".xverse-ready.g7")
            observe = next(a for a in payload["actions"] if a["phase"] == "observe")
            if "condition" in wanted:
                observe["condition"] = wanted["condition"]
            if "observe_timeout" in wanted:
                observe["timeoutSeconds"] = wanted["observe_timeout"]
        return original(docs)

    monkeypatch.setattr(test_launcher, "compiled", compiled)

    def admission(descriptor, environment, maximum):
        binding = descriptor.unit_id.rsplit("#", 1)[-1].replace("componentInstances/", "").replace(
            "-instance", "-binding")
        return UnitAdmission(descriptor, environment, maximum_generation,
                             stderr_directory=(stderr or {}).get(binding))

    monkeypatch.setattr(test_run_broker, "UnitAdmission", admission)


def private(tmp_path, name, mode=0o700):
    path = tmp_path / name
    path.mkdir(mode=mode)
    path.chmod(mode)
    return path


def started(stack):
    broker, facade, _, _ = stack
    end = stage_all(stack)
    for unit in broker.owner._prepared.resource_order:
        issuer = broker.issuer(unit)
        assert facade.start(unit, issuer.recipe.descriptor, broker.connection, end).ready
    return broker.owner._prepared.resource_order


def marker(work, binding, contents, seconds=1.5):
    path = work / (binding + ".marker")
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if path.exists() and path.read_bytes() == contents:
            return
        time.sleep(0.005)
    raise AssertionError((path, path.read_bytes() if path.exists() else None))


def recipe_bytes(issuer):
    return os.pread(issuer._image.recipe_fd, 65536, 0)


def test_undeclared_units_keep_ar17_version_1_and_a_forced_stop(broker_stack):
    broker, facade, _, work = broker_stack
    for issuer in broker.issuers:
        raw = recipe_bytes(issuer)
        assert raw[4:8] == (1).to_bytes(4, "big") and AuthorityRecipe.decode(raw).version == 1
        assert issuer.stop_grace_seconds == 0 and issuer.readiness_probe == "running"
        assert issuer._image.stderr_fd is None
    started(broker_stack)
    result = ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))
    assert result.unit_cleanup_complete
    for issuer in broker.issuers:
        assert issuer._term_ack is None and issuer._closure_fact().stop_mode == "forced"


def test_declared_grace_term_is_honoured_by_a_scenario_stop(request, monkeypatch):
    declare(monkeypatch, {"sink-binding": dict(stop=1.5, mode="term")})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, _, work = stack
    source, sink = started(stack)
    issuer = broker.issuer(sink)
    raw = recipe_bytes(issuer)
    assert AuthorityRecipe.decode(raw).grace_ms == 1500 and raw[4:8] == (2).to_bytes(4, "big")
    assert AuthorityRecipe.decode(recipe_bytes(broker.issuer(source))).version == 1
    marker(work, "sink-binding", b"EXEC\n")
    controller = ReverseTeardown(facade, per_unit_seconds=4)
    began = time.monotonic()
    stopped = controller.phase(sink, "stop", deadline(4.5))
    assert not stopped.emergency and stopped.leader_reaped and time.monotonic() - began < 1.5
    assert issuer._term_ack.state & 512 and issuer._stop_ack.state & (512 | 1024) == 512 | 1024
    assert issuer._closure_fact().stop_mode == "exited-on-term"
    marker(work, "sink-binding", b"EXEC\nTERM\n")
    assert controller.phase(sink, "cleanup", deadline(2)).unit_cleanup_complete
    assert broker.connection.epoch == 0 and not broker.owner.latch.cancelled
    result = controller.run(deadline(3))
    assert result.unit_cleanup_complete
    assert broker.issuer(source)._term_ack is None
    assert broker.issuer(source)._closure_fact().stop_mode == "forced"


def test_term_ignored_is_forced_at_the_end_of_the_grace(request, monkeypatch):
    declare(monkeypatch, {"sink-binding": dict(stop=0.3, mode="ignore-term")})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, _, work = stack
    _, sink = started(stack)
    issuer = broker.issuer(sink)
    marker(work, "sink-binding", b"EXEC\n")
    began = time.monotonic()
    stopped = ReverseTeardown(facade, per_unit_seconds=4).phase(sink, "stop", deadline(4.5))
    elapsed = time.monotonic() - began
    assert not stopped.emergency and stopped.leader_reaped and 0.3 <= elapsed < 2
    assert issuer._term_ack.state & 512 and not issuer._stop_ack.state & 1024
    assert issuer._closure_fact().stop_mode == "forced"


def test_terminal_fence_stop_after_cancel_is_forced_without_term(request, monkeypatch):
    declare(monkeypatch, {"sink-binding": dict(stop=1.5, mode="term")})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, _, work = stack
    _, sink = started(stack)
    marker(work, "sink-binding", b"EXEC\n")
    issuer = broker.issuer(sink)
    assert broker.cancel("dispatcher-terminal-fence").native_epoch_confirmed
    assert issuer.stop_owned(issuer._handle, deadline(1), grace_until=time.monotonic() + 1).leader_reaped
    assert issuer._term_ack is None and not issuer._stop_ack.state & (512 | 1024)
    assert issuer._closure_fact().stop_mode == "forced"
    assert (work / "sink-binding.marker").read_bytes() == b"EXEC\n"


def test_emergency_stop_passes_no_grace(request, monkeypatch):
    declare(monkeypatch, {"sink-binding": dict(stop=1.5, mode="term")})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, _, work = stack
    _, sink = started(stack)
    issuer = broker.issuer(sink)
    calls = []
    original = type(issuer).stop_owned

    def recorded(self, handle, deadline, *, grace_until=None):
        calls.append(grace_until)
        return original(self, handle, deadline, grace_until=grace_until)

    monkeypatch.setattr(type(issuer), "stop_owned", recorded)
    controller = ReverseTeardown(facade, per_unit_seconds=4)
    job = next(j for j in controller._jobs(deadline(2)) if j[0] == sink)
    result = controller._emergency(job, deadline(2), "ML-TEARDOWN-NORMAL-INCOMPLETE")
    assert result.emergency and calls == [None] and issuer._term_ack is None


def test_stop_owned_rejects_a_non_finite_grace_end(request, monkeypatch):
    declare(monkeypatch, {"sink-binding": dict(stop=1.5, mode="term")})
    stack = request.getfixturevalue("broker_stack")
    broker, _, _, _ = stack
    _, sink = started(stack)
    issuer = broker.issuer(sink)
    with pytest.raises(OwnerError, match="ML-RUN-STOP-GRACE"):
        issuer.stop_owned(issuer._handle, deadline(1), grace_until=float("nan"))
    assert issuer._stop_ack is None and issuer._term_ack is None


def test_teardown_need_carries_the_grace_and_its_reserve(request, monkeypatch):
    declare(monkeypatch, {"sink-binding": dict(stop=1.5, mode="term")})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, _, _ = stack
    source, sink = started(stack)
    controller = ReverseTeardown(facade, per_unit_seconds=4)
    assert controller._need(sink, "stop") == 2.0 and controller._need(source, "stop") == 0
    controller._times.seed("phase:stop", 2)
    controller._times.seed("phase:cleanup", 0.2)
    assert controller._need(sink, "cleanup") == pytest.approx(3.3)
    assert controller._need(source, "cleanup") == pytest.approx(3.3)
    controller._times.seed("phase:stop", 0.1)
    assert controller._need(sink, "cleanup") == pytest.approx(2.3)
    assert controller._need(source, "cleanup") == pytest.approx(0.45)
    controller.run(deadline(4))


def test_declared_stderr_is_private_capped_and_registered_with_five_fds(request, monkeypatch, tmp_path):
    errors = private(tmp_path, "stderr-sink")
    declare(monkeypatch, {"sink-binding": dict(stderr=1000, mode="stderr-flood")}, stderr={"sink-binding": str(errors)})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, _, work = stack
    _, sink = started(stack)
    issuer = broker.issuer(sink)
    raw = AuthorityRecipe.decode(recipe_bytes(issuer))
    info = os.stat(errors)
    assert (raw.stderr_max, raw.stderr_device, raw.stderr_inode) == (1000, info.st_dev, info.st_ino)
    path = errors / "stderr-g1"
    end = time.monotonic() + 1.5
    while not (path.exists() and path.stat().st_size == 16384):
        assert time.monotonic() < end
        time.sleep(0.005)
    ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))
    assert issuer._stop_ack.state & 4096 and path.stat().st_size == 1000
    assert oct(path.stat().st_mode & 0o777) == "0o600" and sorted(os.listdir(errors)) == ["stderr-g1"]


@pytest.mark.parametrize("mode", ["undeclared-directory", "missing-directory", "group-readable", "not-empty",
                                  "symlink-component", "absent", "shared", "is-cwd", "budget"])
def test_stderr_admission_fails_closed(request, monkeypatch, tmp_path, mode):
    errors = private(tmp_path, "stderr-a", 0o750 if mode == "group-readable" else 0o700)
    controls = {"sink-binding": dict(stderr=1 << 20)}
    directories = {"sink-binding": str(errors)}
    maximum = 3
    code = "ML-RUN-STDERR-DIRECTORY"
    if mode == "undeclared-directory":
        controls, code = {}, "ML-RUN-STDERR-ADMISSION"
    elif mode == "missing-directory":
        directories, code = {}, "ML-RUN-STDERR-ADMISSION"
    elif mode == "not-empty":
        (errors / "old").write_bytes(b"x")
    elif mode == "symlink-component":
        os.symlink(tmp_path, tmp_path / "link")
        directories = {"sink-binding": str(tmp_path / "link" / "stderr-a")}
    elif mode == "absent":
        directories = {"sink-binding": str(tmp_path / "absent")}
    elif mode == "shared":
        controls["source-binding"] = dict(stderr=10)
        directories["source-binding"] = str(errors)
        code = "ML-RUN-STDERR-SHARED"
    elif mode == "is-cwd":
        directories, code = {"sink-binding": str(tmp_path / "work")}, "ML-RUN-STDERR-SHARED"
    elif mode == "budget":
        controls["source-binding"] = dict(stderr=1 << 20)
        directories["source-binding"] = str(private(tmp_path, "stderr-b"))
        maximum, code = 9, "ML-RUN-STDERR-BUDGET"  # 2 units x 9 generations x 1 MiB > 16 MiB
    declare(monkeypatch, controls, stderr=directories, maximum_generation=maximum)
    if mode == "is-cwd":
        from . import test_launcher
        original = test_launcher.compiled

        def compiled(docs):
            Path(docs["deployment.json"]["spec"]["bindings"][0]["extensions"][NS]["process"]["workingDirectory"]).chmod(0o700)
            return original(docs)

        monkeypatch.setattr(test_launcher, "compiled", compiled)
    with pytest.raises(OwnerError, match=code):
        request.getfixturevalue("broker_stack")


def test_stderr_directory_inside_the_collection_source_root_is_refused(request, monkeypatch, tmp_path):
    from .test_collection_runtime import configure

    configure(monkeypatch)
    from . import test_launcher
    declare(monkeypatch, {"sink-binding": dict(stderr=1000)}, stderr={"sink-binding": str(tmp_path / "work" / "err")})
    original = test_launcher.compiled

    def compiled(docs):
        (tmp_path / "work" / "err").mkdir(mode=0o700)
        return original(docs)

    monkeypatch.setattr(test_launcher, "compiled", compiled)
    with pytest.raises(OwnerError, match="ML-RUN-STDERR-ROOT"):
        request.getfixturevalue("broker_stack")


def test_schedule_rejects_a_grace_outside_the_normal_teardown_share():
    from xverse.maestro.providers import ProbePolicy
    from xverse.maestro.schedule_plan import ScheduleError, admit_schedule
    from .test_preparation import prepared

    value = prepared()
    unit = value.units[0]
    graced = replace(value, units=(replace(unit, plan=replace(unit.plan, process_controls=ProcessControls(2.5))),)
                     + value.units[1:])
    options = dict(policies=tuple(ProbePolicy(u.unit_id, 2, 1, 0.1) for u in value.units),
                   ticks=(0, 0, value.clock.horizon_ticks), active_seconds=1, operation_seconds=0.1)
    plain = admit_schedule(value, per_unit_seconds=1, **options)
    with pytest.raises(ScheduleError, match="ML-SCHEDULE-STOP-GRACE"):
        admit_schedule(graced, per_unit_seconds=4, **options)  # 2.5 + 0.5 > 0.6 x 4
    accepted = admit_schedule(graced, per_unit_seconds=5, **options)  # 3.0 <= 0.6 x 5
    assert accepted.per_unit_seconds == 5
    assert admit_schedule(value, per_unit_seconds=1, **options).digest == plain.digest


def grace_cancel(request, monkeypatch, *, hold=0.0):
    """A scenario stop of an ignore-term unit (grace 2 s), with an external cancel 0.4 s into the grace.
    `hold` keeps the CANCEL exchange busy that long after its send (under the connection lock)."""
    import threading
    from xverse.maestro.affa_client import AuthorityConnection

    declare(monkeypatch, {"sink-binding": dict(stop=2.0, mode="ignore-term")})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, _, work = stack
    _, sink = started(stack)
    issuer = broker.issuer(sink)
    marker(work, "sink-binding", b"EXEC\n")
    out, errors, cancelling = {}, [], threading.Event()
    receive = AuthorityConnection._receive

    def held(self, until):
        if cancelling.is_set() and threading.current_thread() is not threading.main_thread():
            time.sleep(hold)
        return receive(self, until)

    if hold:
        monkeypatch.setattr(AuthorityConnection, "_receive", held)

    def cancel():
        time.sleep(0.4)
        began = time.monotonic()
        cancelling.set()
        out["cancel"] = broker.cancel("external-during-grace")
        out["seconds"] = time.monotonic() - began

    original = ReverseTeardown._diagnostic

    def diagnostic(self, error):
        errors.append(error)
        return original(self, error)

    monkeypatch.setattr(ReverseTeardown, "_diagnostic", diagnostic)
    controller = ReverseTeardown(facade, per_unit_seconds=5)
    thread = threading.Thread(target=cancel)
    thread.start()
    began = time.monotonic()
    result = controller.phase(sink, "stop", deadline(4.9))
    elapsed = time.monotonic() - began
    thread.join(3)
    assert not thread.is_alive()
    # Common to both observed paths: the cancel is confirmed natively, never revoked, within a short bound
    # (the exchange lock is free during the grace, D-4); the grace ends at the cancel; the forced STOP succeeds
    # with no exit on TERM; the phase returns the existing emergency result with a complete forced cleanup.
    assert out["cancel"].native_epoch_confirmed and out["cancel"].diagnostic is None and out["seconds"] < 1.0
    assert not broker.connection._revoked and elapsed < 2.0
    assert issuer._term_ack.state & 512
    assert issuer._stop_ack.state & 8 and not issuer._stop_ack.state & (4 | 1024)
    assert issuer._closure_fact().stop_mode == "forced"
    assert result.emergency and result.diagnostic == "ML-TEARDOWN-NORMAL-INCOMPLETE"
    assert result.leader_reaped and result.boundary_empty and result.boundary_released
    return [(type(e).__name__, str(e)) for e in errors]


def test_cancel_during_the_term_grace_is_confirmed_and_the_stop_is_an_emergency_result(request, monkeypatch):
    """S1b review LOW-2 (expected, fail-safe behaviour). The usual path: the STOP follows the completed CANCEL
    and the normal outcome record is refused (ML-TEARDOWN-TERMINAL-SCOPE). Less often (1 of 8 local runs), the
    grace wait sees the cancelled latch while the CANCEL exchange still holds the connection, and the STOP is
    refused before send (ML-AFFA-CONFLICT, no revoke); the emergency path then makes the forced STOP."""
    assert grace_cancel(request, monkeypatch) in (
        [("PersistenceError", "ML-TEARDOWN-TERMINAL-SCOPE")], [("BootstrapError", "ML-AFFA-CONFLICT")])


def test_stop_colliding_with_an_in_flight_cancel_is_finished_by_the_emergency_path(request, monkeypatch):
    """S1b review LOW-2, the less frequent path made deterministic: the CANCEL exchange is held 0.15 s."""
    assert grace_cancel(request, monkeypatch, hold=0.15) == [("BootstrapError", "ML-AFFA-CONFLICT")]


@pytest.mark.parametrize("bit", [512, 1024, 2048, 4096])
def test_a_reply_bit_of_an_undeclared_control_fails_closed(broker_stack, monkeypatch, bit):
    """S1b review LOW-4: a crafted native reply carrying an undeclared control's bit is never accepted."""
    from xverse.maestro.affa_client import AuthorityConnection

    broker, facade, _, work = broker_stack
    source, sink = started(broker_stack)
    issuer = broker.issuer(sink)
    exchange = AuthorityConnection._exchange

    def crafted(self, request, *, fds=()):
        reply = exchange(self, request, fds=fds)
        return replace(reply, state=reply.state | bit)

    monkeypatch.setattr(AuthorityConnection, "_exchange", crafted)
    with pytest.raises(OwnerError, match="ML-RUN-STATE-UNDECLARED"):
        issuer.observe(issuer._handle, deadline(1))


def test_declared_control_bits_are_accepted(request, monkeypatch, tmp_path):
    """S1b review LOW-4: the bits of declared controls pass; the marker bit of a non-marker unit does not."""
    from xverse.maestro.affa_client import AuthorityConnection

    errors = private(tmp_path, "stderr-declared")
    declare(monkeypatch, {"sink-binding": dict(stop=1, stderr=100)}, stderr={"sink-binding": str(errors)})
    stack = request.getfixturevalue("broker_stack")
    broker, _, _, _ = stack
    _, sink = started(stack)
    issuer = broker.issuer(sink)
    exchange = AuthorityConnection._exchange
    added = {"bits": 512 | 1024 | 4096}

    def crafted(self, request, *, fds=()):
        reply = exchange(self, request, fds=fds)
        return replace(reply, state=reply.state | added["bits"])

    monkeypatch.setattr(AuthorityConnection, "_exchange", crafted)
    assert issuer.observe(issuer._handle, deadline(1)).leader_alive
    added["bits"] = 2048
    with pytest.raises(OwnerError, match="ML-RUN-STATE-UNDECLARED"):
        issuer.observe(issuer._handle, deadline(1))
