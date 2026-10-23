"""S1b native AF17 controls (FR-009 to FR-011, FR-013): graceful TERM, private capped stderr, nonce marker.

Standalone owned fixture, as in ``test_affa_native``: it plays the supervisor over a real socket and real
frozen cgroups. Not bootstrap or run admission. Design: ``design-stabilization-s1b.md``.
"""

from dataclasses import replace
import os
from pathlib import Path
import select
import signal
import socket
import stat
import struct
import subprocess
import time

import pytest
from xverse.maestro.affa_protocol import (
    AuthorityConfig,
    AuthorityFrame,
    AuthorityKind as K,
    AuthorityRecipe,
    AuthorityUnit,
)
from xverse.maestro.bootstrap import _sealed, seal_helper_image
from xverse.maestro.prbc import BoundaryDescriptor
from .test_affa_native import Harness, WATCH_PLACEHOLDER, authority_binary as authority_binary, digest
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries

TERM_SENT, EXITED, MARKER, TRUNCATED = 512, 1024, 2048, 4096


@pytest.fixture
def s1b(environment, authority_binary, binaries, tmp_path):
    """start(specs) registers one unit per spec and records INTENT; specs are dicts with mode and controls."""
    factory, _, _ = environment
    manager, _ = factory(seconds=40)
    image = seal_helper_image(
        binaries["workload"],
        digest="sha256:" + digest(binaries["workload"].read_bytes()).hex(),
        argv0=str(binaries["workload"]),
    )
    state = dict(h=None, peer=None, parent=None, open=[image.descriptor])

    def start(specs, *, register=True):
        h = Harness(manager, None, image, [])
        state["h"] = h
        records = []
        for i, spec in enumerate(specs):
            work = tmp_path / f"cwd{i}"
            work.mkdir(mode=0o700)
            cwd = os.open(work, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
            state["open"].append(cwd)
            errors = errfd = None
            controls = dict(grace_ms=spec.get("grace_ms", 0), probe=spec.get("probe", 0))
            if spec.get("stderr_max"):
                errors = tmp_path / f"err{i}"
                errors.mkdir(mode=spec.get("stderr_mode", 0o700))
                errors.chmod(spec.get("stderr_mode", 0o700))
                errfd = os.open(errors, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
                state["open"].append(errfd)
                info = os.fstat(errfd)
                controls.update(stderr_max=spec["stderr_max"], stderr_device=info.st_dev, stderr_inode=info.st_ino)
            desc = BoundaryDescriptor("run", f"u{i}", 1, f"s1b-{i}", 0)
            manager.create_frozen(desc)
            cg = manager._entries[desc.key].fd
            recipe = spec.get("raw_recipe") or AuthorityRecipe(
                ("/fixture", "unit.marker", spec["mode"]), ("MAESTRO_VISIBLE=declared",), **controls).encode()
            recipe_fd = _sealed(recipe, "owned-s1b-recipe")
            h.fds.append(recipe_fd)
            st, wst = os.fstat(cg), os.fstat(cwd)
            records.append(AuthorityUnit(digest(bytes([i + 1])), bytes.fromhex(image.digest[7:]), digest(recipe),
                                         st.st_dev, st.st_ino, wst.st_dev, wst.st_ino, 1, 2))
            h.units.append(dict(
                descriptor=desc, cg=cg, recipe=recipe_fd, cwd=cwd, work=work, errors=errors, errfd=errfd,
                generation=1, operation=bytes([i + 1]) * 16, intent=digest(b"intent" + bytes([i])),
                mirror=digest(b"mirror" + bytes([i])), boundary=digest(b"boundary" + bytes([i]))))
        h.lease = time.monotonic_ns() + 4_800_000_000
        h.config = AuthorityConfig(
            int(manager._admission.teardown_deadline.monotonic_seconds * 1e9), h.lease, 0,
            digest(b"owned-AFFA-s1b"), digest(b"original-supervisor"), tuple(records))
        config_fd = _sealed(h.config.encode(), "owned-s1b-config")
        h.watch_key = os.urandom(32)
        key_fd = _sealed(h.watch_key, "owned-s1b-watch-key")
        h.fds += [config_fd, key_fd]
        parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        state["parent"], state["peer"] = parent, peer
        parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        parent.settimeout(3)
        h.channel = parent
        h.process = subprocess.Popen(
            [str(authority_binary), str(peer.fileno()), str(config_fd), str(key_fd)],
            pass_fds=(peer.fileno(), config_fd, key_fd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        peer.close()
        state["peer"] = None
        ready = AuthorityFrame.decode(parent.recvmsg(321, socket.CMSG_SPACE(12))[0])
        assert ready.kind is K.READY and ready.epoch == 0
        if register:
            for i in range(len(specs)):
                assert h.rpc(*registration(h, i)).kind is K.REGISTERED
            for i in range(len(specs)):
                assert h.rpc(h.frame(K.INTENT, i)).kind is K.INTENT_RECORDED
        return h

    yield start
    h = state["h"]
    if state["peer"]:
        state["peer"].close()
    if state["parent"]:
        state["parent"].close()
    if h is not None and h.process:
        try:
            h.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pidfd = os.pidfd_open(h.process.pid)
            try:
                signal.pidfd_send_signal(pidfd, signal.SIGKILL)
            finally:
                os.close(pidfd)
            h.process.wait(timeout=3)
    for fd in (h.childfds + h.fds if h else []) + state["open"]:
        os.close(fd)


def registration(h, i, fds=None):
    u, r = h.units[i], h.config.units[i]
    frame = AuthorityFrame(K.REGISTER, 1, h.end(), h.config.scope, i + 1, 0, 1,
                           first=r.binding, second=r.image, third=r.recipe, fourth=u["boundary"])
    base = (u["cg"], h.image.descriptor, u["cwd"], u["recipe"])
    return frame, (base + ((u["errfd"],) if u["errfd"] is not None else ()) if fds is None else fds)


def run(h, i):
    h.stage(i)
    h.units[i]["pidfd"] = h.childfds[-1]
    h.arm(i)
    assert h.release(i).kind is K.RELEASED
    wait_for(lambda: (h.units[i]["work"] / "unit.marker").exists(), "workload marker")


def wait_for(condition, what, seconds=1.5):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if condition():
            return
        time.sleep(0.005)
    raise AssertionError("expected " + what)


def exited(h, i, seconds):
    return bool(select.select([h.units[i]["pidfd"]], [], [], seconds)[0])


def query(h, i):
    reply = h.rpc(h.frame(K.QUERY, i))
    assert reply.kind is K.OBSERVED
    return reply.state


def stop(h, i):
    stopped = h.rpc(h.frame(K.STOP, i))
    assert stopped.kind is K.STOPPED and stopped.state & 8 and not stopped.state & 4
    return stopped.state


# ---- protocol bytes -------------------------------------------------------------------------------

def test_undeclared_recipe_stays_ar17_version_1_bytes():
    words = (b"/fixture", b"unit.marker", b"single", b"MAESTRO_VISIBLE=declared")
    expected = b"AR17" + struct.pack("!III", 1, 3, 1)
    expected += b"".join(struct.pack("!I", len(w)) + w + b"\0" for w in words)
    recipe = AuthorityRecipe(("/fixture", "unit.marker", "single"), ("MAESTRO_VISIBLE=declared",))
    assert recipe.version == 1 and recipe.encode() == expected
    assert AuthorityRecipe.decode(expected) == recipe


# ---- FR-009 graceful stop -----------------------------------------------------------------------

def test_term_is_honoured_and_the_stop_records_exited_on_term(s1b):
    h = s1b([dict(mode="term", grace_ms=2000)])
    run(h, 0)
    sent = h.rpc(h.frame(K.TERM, 0))
    assert sent.kind is K.TERM_SENT and sent.state & TERM_SENT and not sent.state & EXITED
    assert h.rpc(h.frame(K.TERM, 0)).state & TERM_SENT  # idempotent, no second signal needed
    assert exited(h, 0, 1.5)
    flags = stop(h, 0)
    assert flags & (TERM_SENT | EXITED) == TERM_SENT | EXITED
    assert (h.units[0]["work"] / "unit.marker").read_bytes() == b"EXEC\nTERM\n"
    assert h.rpc(h.frame(K.RETIRE, 0)).state & (128 | TERM_SENT | EXITED) == 128 | TERM_SENT | EXITED


def test_term_ignored_is_forced_after_the_grace(s1b):
    h = s1b([dict(mode="ignore-term", grace_ms=300)])
    run(h, 0)
    assert h.rpc(h.frame(K.TERM, 0)).state & TERM_SENT
    assert not exited(h, 0, 0.3)
    flags = stop(h, 0)
    assert flags & TERM_SENT and not flags & EXITED
    assert h.manager.residual_membership(h.units[0]["descriptor"]) == ()


def test_cancel_then_stop_is_forced_without_term(s1b):
    h = s1b([dict(mode="term", grace_ms=2000)])
    run(h, 0)
    h.cancel()
    refused = h.rpc(h.frame(K.TERM, 0))  # the client refuses it before sending; natively it is a no-op
    assert refused.kind is K.TERM_SENT and not refused.state & TERM_SENT
    flags = stop(h, 0)
    assert not flags & (TERM_SENT | EXITED)
    assert (h.units[0]["work"] / "unit.marker").read_bytes() == b"EXEC\n"


def test_a_frozen_unit_is_not_sent_term(s1b):
    h = s1b([dict(mode="term", grace_ms=2000)])
    run(h, 0)
    assert h.rpc(h.frame(K.FAULT_FREEZE, 0)).kind is K.FAULTED
    refused = h.rpc(h.frame(K.TERM, 0))
    assert refused.kind is K.TERM_SENT and not refused.state & TERM_SENT and refused.state & 32
    assert not stop(h, 0) & (TERM_SENT | EXITED)
    assert (h.units[0]["work"] / "unit.marker").read_bytes() == b"EXEC\n"


def test_term_without_a_declared_grace_is_rejected(s1b):
    h = s1b([dict(mode="term")])
    run(h, 0)
    assert h.rpc(h.frame(K.TERM, 0)).kind is K.REJECTED
    assert not stop(h, 0) & (TERM_SENT | EXITED)
    assert (h.units[0]["work"] / "unit.marker").read_bytes() == b"EXEC\n"


def test_term_before_release_signals_nothing(s1b):
    h = s1b([dict(mode="term", grace_ms=2000)])
    h.stage(0)
    refused = h.rpc(h.frame(K.TERM, 0))
    assert refused.kind is K.TERM_SENT and not refused.state & TERM_SENT
    h.cancel()
    assert not stop(h, 0) & TERM_SENT
    assert not (h.units[0]["work"] / "unit.marker").exists()


# ---- FR-011 nonce marker ------------------------------------------------------------------------

def challenge(h, i):
    path = h.units[i]["work"] / ".xverse-ready" / "challenge"
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o400 and info.st_size == 64
    value = path.read_bytes()
    assert all(c in b"0123456789abcdef" for c in value)
    return value


def test_marker_ready_latches_on_the_exact_nonce(s1b):
    h = s1b([dict(mode="marker", probe=1)])
    run(h, 0)
    directory = os.lstat(h.units[0]["work"] / ".xverse-ready")
    assert stat.S_ISDIR(directory.st_mode) and stat.S_IMODE(directory.st_mode) == 0o700
    nonce = challenge(h, 0)
    wait_for(lambda: (h.units[0]["work"] / ".xverse-ready" / "ready").exists(), "ready marker")
    assert (h.units[0]["work"] / ".xverse-ready" / "ready").read_bytes() == nonce
    assert query(h, 0) & (4 | MARKER) == 4 | MARKER
    (h.units[0]["work"] / ".xverse-ready" / "ready").unlink()
    assert query(h, 0) & MARKER  # latched
    stop(h, 0)


def test_marker_that_never_appears_is_never_ready(s1b):
    h = s1b([dict(mode="marker-never", probe=1)])
    run(h, 0)
    for _ in range(4):
        assert not query(h, 0) & MARKER
        time.sleep(0.05)
    assert query(h, 0) & 4
    stop(h, 0)


def test_marker_late_within_the_bound_is_ready(s1b):
    h = s1b([dict(mode="marker-late", probe=1)])
    run(h, 0)
    began, seen = time.monotonic(), []
    for k in range(3):  # spaced attempts t0 + k * W / A, W = 1.8 s, A = 3; the marker comes after 0.4 s
        time.sleep(max(0, began + k * 0.6 - time.monotonic()))
        seen.append(bool(query(h, 0) & MARKER))
    assert seen[0] is False and seen[-1] is True
    stop(h, 0)


def test_marker_checks_are_capped_at_three_per_generation(s1b):
    h = s1b([dict(mode="marker-late", probe=1)])
    run(h, 0)
    for _ in range(3):
        assert not query(h, 0) & MARKER
    wait_for(lambda: (h.units[0]["work"] / ".xverse-ready" / "ready").exists(), "late ready marker")
    assert not query(h, 0) & MARKER  # the fourth check is never made
    stop(h, 0)


@pytest.mark.parametrize("form", ["wrong-nonce", "symlink", "fifo", "oversized", "directory"])
def test_marker_rejects_wrong_or_hostile_files_without_blocking(s1b, form):
    h = s1b([dict(mode="marker-wrong" if form == "wrong-nonce" else "marker-never", probe=1)])
    run(h, 0)
    ready = h.units[0]["work"] / ".xverse-ready" / "ready"
    if form == "wrong-nonce":
        wait_for(ready.exists, "wrong ready marker")
    elif form == "symlink":
        os.symlink("challenge", ready)  # the target holds exactly the nonce
    elif form == "fifo":
        os.mkfifo(ready, 0o600)
    elif form == "oversized":
        ready.write_bytes(challenge(h, 0) + b"\n")
    else:
        ready.mkdir()
    began = time.monotonic()
    for _ in range(3):
        assert not query(h, 0) & MARKER
    assert time.monotonic() - began < 1
    stop(h, 0)


def test_stale_marker_directory_rejects_stage_and_creates_no_workload(s1b):
    h = s1b([dict(mode="marker", probe=1)])
    (h.units[0]["work"] / ".xverse-ready").mkdir(mode=0o700)
    assert h.rpc(h.frame(K.STAGE, 0)).kind is K.REJECTED
    assert not (h.units[0]["work"] / "unit.marker").exists()
    assert h.manager.residual_membership(h.units[0]["descriptor"]) == ()


def test_marker_directory_symlink_is_never_followed(s1b, tmp_path):
    h = s1b([dict(mode="marker", probe=1)])
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir(mode=0o700)
    os.symlink(elsewhere, h.units[0]["work"] / ".xverse-ready")
    assert h.rpc(h.frame(K.STAGE, 0)).kind is K.REJECTED
    assert list(elsewhere.iterdir()) == []
    assert h.manager.residual_membership(h.units[0]["descriptor"]) == ()


def test_each_generation_gets_a_fresh_challenge_and_the_old_one_moves_aside(s1b):
    h = s1b([dict(mode="marker", probe=1)])
    run(h, 0)
    first = challenge(h, 0)
    wait_for(lambda: (h.units[0]["work"] / ".xverse-ready" / "ready").exists(), "first ready marker")
    assert query(h, 0) & MARKER
    stop(h, 0)
    assert h.rpc(h.frame(K.RETIRE, 0)).state & 128
    assert h.manager.force_cleanup(h.units[0]["descriptor"]).boundary_released
    desc = BoundaryDescriptor("run", "u0", 2, "s1b-next", 0)
    h.manager.create_frozen(desc)
    fd = h.manager._entries[desc.key].fd
    u = h.units[0]
    u.update(generation=2, operation=b"n" * 16, intent=digest(b"new-intent"), mirror=digest(b"new-mirror"),
             boundary=digest(b"new-boundary"))
    u.pop("handle")
    u.pop("ticket")
    assert h.rpc(h.frame(K.ADVANCE, 0), (fd,)).kind is K.ADVANCED
    u["descriptor"], u["cg"] = desc, fd
    (u["work"] / "unit.marker").unlink()
    run(h, 0)
    aside = u["work"] / ".xverse-ready.g1"
    assert (aside / "challenge").read_bytes() == first and (aside / "ready").read_bytes() == first
    second = challenge(h, 0)
    assert second != first
    wait_for(lambda: (u["work"] / ".xverse-ready" / "ready").exists(), "second ready marker")
    assert query(h, 0) & MARKER
    h.cancel()
    stop(h, 0)


def test_occupied_aside_name_rejects_the_next_stage(s1b):
    h = s1b([dict(mode="marker-never", probe=1)])
    run(h, 0)
    stop(h, 0)
    assert h.rpc(h.frame(K.RETIRE, 0)).state & 128
    assert h.manager.force_cleanup(h.units[0]["descriptor"]).boundary_released
    (h.units[0]["work"] / ".xverse-ready.g1").mkdir()
    desc = BoundaryDescriptor("run", "u0", 2, "s1b-occupied", 0)
    h.manager.create_frozen(desc)
    fd = h.manager._entries[desc.key].fd
    u = h.units[0]
    u.update(generation=2, operation=b"o" * 16, intent=digest(b"o-intent"), mirror=digest(b"o-mirror"),
             boundary=digest(b"o-boundary"))
    u.pop("handle")
    u.pop("ticket")
    assert h.rpc(h.frame(K.ADVANCE, 0), (fd,)).kind is K.ADVANCED
    u["descriptor"], u["cg"] = desc, fd
    assert h.rpc(h.frame(K.STAGE, 0)).kind is K.REJECTED
    assert h.manager.residual_membership(desc) == ()


# ---- FR-010 private stderr ----------------------------------------------------------------------

def test_stderr_cap_overflow_is_truncated_at_stop(s1b):
    h = s1b([dict(mode="stderr-flood", stderr_max=1000)])
    run(h, 0)
    path = h.units[0]["errors"] / "stderr-g1"
    wait_for(lambda: path.stat().st_size == 16384, "flooded stderr")
    flags = stop(h, 0)
    info = os.lstat(path)
    assert flags & TRUNCATED and info.st_size == 1000 and stat.S_IMODE(info.st_mode) == 0o600
    assert stat.S_ISREG(info.st_mode) and path.read_bytes() == b"E" * 1000


def test_stderr_under_the_cap_is_kept_whole_and_streams_are_closed(s1b):
    h = s1b([dict(mode="streams", stderr_max=4096), dict(mode="streams")])
    run(h, 0)
    run(h, 1)
    for i in range(2):
        wait_for(lambda i=i: (h.units[i]["work"] / "unit.marker").read_bytes().count(b"STREAMS"), "streams")
    assert (h.units[0]["work"] / "unit.marker").read_bytes() == b"EXEC\nSTREAMS file\n"
    assert (h.units[1]["work"] / "unit.marker").read_bytes() == b"EXEC\nSTREAMS null\n"
    assert not stop(h, 0) & TRUNCATED
    assert (h.units[0]["errors"] / "stderr-g1").read_bytes() == b"diagnostic\n"
    assert not stop(h, 1) & TRUNCATED


def test_existing_stderr_file_or_symlink_rejects_stage(s1b, tmp_path):
    h = s1b([dict(mode="single", stderr_max=1000)])
    target = tmp_path / "victim"
    target.write_bytes(b"keep")
    os.symlink(target, h.units[0]["errors"] / "stderr-g1")
    assert h.rpc(h.frame(K.STAGE, 0)).kind is K.REJECTED
    assert target.read_bytes() == b"keep"
    assert h.manager.residual_membership(h.units[0]["descriptor"]) == ()


def test_existing_stderr_regular_file_rejects_stage(s1b):
    h = s1b([dict(mode="single", stderr_max=1000)])
    (h.units[0]["errors"] / "stderr-g1").write_bytes(b"stale")
    assert h.rpc(h.frame(K.STAGE, 0)).kind is K.REJECTED
    assert (h.units[0]["errors"] / "stderr-g1").read_bytes() == b"stale"


@pytest.mark.parametrize("mode", ["missing-fifth", "extra-fifth", "wrong-directory", "group-readable"])
def test_register_binds_the_exact_private_stderr_directory(s1b, tmp_path, mode):
    spec = dict(mode="single", stderr_max=1000, stderr_mode=0o750 if mode == "group-readable" else 0o700)
    h = s1b([spec if mode != "extra-fifth" else dict(mode="single")], register=False)
    frame, fds = registration(h, 0)
    if mode == "missing-fifth":
        fds = fds[:4]
    elif mode == "extra-fifth":
        fds = fds + (h.units[0]["cwd"],)
    elif mode == "wrong-directory":
        other = tmp_path / "other"
        other.mkdir(mode=0o700)
        fd = os.open(other, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        h.fds.append(fd)
        fds = fds[:4] + (fd,)
    assert h.rpc(frame, fds).kind is K.REJECTED


@pytest.mark.parametrize("controls", ["all-zero", "reserved", "grace", "stderr-max", "probe", "identity"])
def test_native_rejects_invalid_version_2_recipes(s1b, controls):
    header = dict(grace=1000, stderr=0, probe=0, reserved=0, dev=0, ino=0)
    header.update({"all-zero": dict(grace=0), "reserved": dict(reserved=1), "grace": dict(grace=4001),
                   "stderr-max": dict(stderr=1048577, dev=1, ino=1), "probe": dict(probe=2),
                   "identity": dict(stderr=0, dev=1, ino=0)}[controls])
    words = (b"/fixture", b"unit.marker", b"single", b"MAESTRO_VISIBLE=declared")
    raw = b"AR17" + struct.pack("!III", 2, 3, 1) + struct.pack(
        "!IIIIQQ", header["grace"], header["stderr"], header["probe"], header["reserved"], header["dev"], header["ino"])
    raw += b"".join(struct.pack("!I", len(w)) + w + b"\0" for w in words)
    h = s1b([dict(mode="single", raw_recipe=raw)], register=False)
    assert h.rpc(*registration(h, 0)).kind is K.REJECTED
