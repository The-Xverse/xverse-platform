"""Single original persistence process; CLI accepts only private socket/config FDs."""

from datetime import datetime, timezone
from importlib.resources import files
import ctypes
import hashlib
import os
import select
import signal
import socket
import struct
import sys
import time

from xverse.argus import EvidenceStore
from xverse_xdl.experiment_plan import compile_experiment_plan
from xverse_xdl.lifecycle import ExecutionPermit, FileEvidenceJournal
from xverse_xdl.validate import validate_mappings
from .admission import PermitApproval, PermitBinding, PermitSession, validate_permits
from .owner import _persist_intent
from .persistence import (
    PersistenceError,
    _frame,
    _read_input,
    _receive,
    _send,
    _strict_json,
)
from .projection import Limits, ProviderDescriptor, prepare_lifecycle
from .time import HostDeadline


CONFIG_KEYS = {
    "version",
    "resources",
    "providers",
    "limits",
    "experiment_digest",
    "lifecycle_digest",
    "run_id",
    "session",
    "generation_ns",
    "journal_path",
    "evidence_root",
    "bindings",
    "approvals",
}


def _load(config, checkpoint):
    """Original objects are constructed here only, after authenticated Init."""
    checkpoint()
    schemas = tuple(
        p
        for p in files("xverse_xdl").joinpath("profiles").iterdir()
        if p.name.endswith(".schema.json")
    )
    checkpoint()
    validation = validate_mappings(
        tuple(config["resources"]), profile_schema_paths=schemas
    )
    if not validation.is_valid:
        raise PersistenceError("ML-PERSIST-XDL")
    checkpoint()
    result = compile_experiment_plan(validation.resources)
    prepared = prepare_lifecycle(
        result,
        validation.resources,
        provider_descriptors=tuple(
            ProviderDescriptor(**d) for d in config["providers"]
        ),
        limits=Limits(**config["limits"]),
    )
    if (
        prepared.experiment_digest != config["experiment_digest"]
        or prepared.lifecycle_digest != config["lifecycle_digest"]
    ):
        raise PersistenceError("ML-PERSIST-PREPARATION")
    bindings = []
    for row in config["bindings"]:
        row = dict(row)
        permit = dict(row.pop("permit"))
        for name in ("not_before", "expires_at"):
            permit[name] = datetime.fromisoformat(permit[name])
        for name in ("permitted_actions", "operation_classes", "exclusions"):
            permit[name] = tuple(permit[name])
        bindings.append(PermitBinding(**row, permit=ExecutionPermit(**permit)))
    approvals = []
    for row in config["approvals"]:
        row = dict(row)
        for name in ("not_before", "expires_at"):
            row[name] = datetime.fromisoformat(row[name])
        row["artifact_digests"] = tuple(row["artifact_digests"])
        approvals.append(PermitApproval(**row))
    checkpoint()
    now = datetime.now(timezone.utc)
    validate_permits(
        prepared,
        result,
        validation.resources,
        run_id=config["run_id"],
        bindings=bindings,
        approvals=approvals,
        now=now,
        initial_generation=1,
    )
    checkpoint()
    journal = FileEvidenceJournal(config["journal_path"])
    checkpoint()
    permits = PermitSession(
        prepared,
        result,
        validation.resources,
        run_id=config["run_id"],
        bindings=bindings,
        approvals=approvals,
        now=now,
        initial_generation=1,
        journal=journal,
    )
    checkpoint()
    session = config["session"]
    writer = EvidenceStore.open_run(
        config["evidence_root"],
        run_id=config["run_id"],
        plan=result.plan,
        clocks={
            "host": {
                "domain": "host:" + session,
                "unit": "s",
                "value": time.monotonic(),
            },
            "utc": {"domain": "utc:" + session, "unit": "s", "value": now.timestamp()},
        },
    )
    checkpoint()
    return permits, writer


def serve(channel, input_fd):
    """Trusted bootstrap calls in the new process; never fork-copy active owners."""
    if (
        channel.family != socket.AF_UNIX
        or channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
        != socket.SOCK_SEQPACKET
    ):
        raise PersistenceError("ML-PERSIST-SOCKET")
    peer = struct.unpack(
        "3i", channel.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
    )
    if peer != (os.getppid(), os.getuid(), os.getgid()) or peer[0] <= 1:
        raise PersistenceError("ML-PERSIST-PARENT")
    parent_fd = os.pidfd_open(peer[0], 0)
    try:
        # The bootstrap must keep the creating parent thread alive; not a hard
        # kernel bound or protection during interpreter/bootstrap initialization.
        libc = ctypes.CDLL(None, use_errno=True)
        libc.prctl.argtypes = (
            ctypes.c_int,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
        )
        libc.prctl.restype = ctypes.c_int
        if (
            libc.prctl(1, signal.SIGKILL, 0, 0, 0)
            or libc.prctl(4, 0, 0, 0, 0)
            or libc.prctl(38, 1, 0, 0, 0)
            or os.getppid() != peer[0]
        ):
            raise PersistenceError("ML-PERSIST-PARENT-GUARD")
        channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        channel.setblocking(False)
        private = _read_input(input_fd)
        config = _strict_json(private)
        if (
            type(config) is not dict
            or set(config) != CONFIG_KEYS
            or type(config["version"]) is not int
            or config["version"] != 1
            or type(config["generation_ns"]) is not int
            or not 0 < config["generation_ns"] - time.monotonic_ns() <= 394_000_000_000
            or any(
                type(config[k]) is not list or not 0 < len(config[k]) <= cap
                for k, cap in (
                    ("resources", 128),
                    ("providers", 16),
                    ("bindings", 16),
                    ("approvals", 16),
                )
            )
        ):
            raise PersistenceError("ML-PERSIST-CONFIG")
        session, end = config["session"], config["generation_ns"]
        HostDeadline(session, end / 1e9).__post_init__()
        scope = hashlib.sha256(private).hexdigest()
        sequence, permits, writer, claims, attempted = 0, None, None, {}, set()

        def alive():
            if (
                select.select([parent_fd], [], [], 0)[0]
                or os.getppid() != peer[0]
                or time.monotonic_ns() >= end
            ):
                raise PersistenceError("ML-PERSIST-PARENT-CLOSED")

        def check(deadline):
            alive()
            if type(deadline) is not HostDeadline or deadline.session != session:
                raise PersistenceError("ML-PERSIST-HOST-SESSION")
            deadline.__post_init__()
            until = request["deadline"]
            if deadline.monotonic_seconds != until / 1e9:
                raise PersistenceError("ML-PERSIST-DEADLINE")
            if not 0 < until - time.monotonic_ns() <= 5_000_000_000 or until > end:
                raise PersistenceError("ML-PERSIST-DEADLINE")
            return until

        _send(channel, _frame("hello", 0, "", 0, scope, {}))
        while True:
            request = _receive(channel, peer, end, alive)
            sequence += 1
            if (
                sequence > 128
                or request["sequence"] != sequence
                or request["scope"] != scope
                or request["kind"] not in {"init", "commit", "revalidate", "abort"}
                or not request["operation"].startswith("ml-")
                or len(request["operation"]) != 35
            ):
                raise PersistenceError("ML-PERSIST-REQUEST")
            deadline = HostDeadline(session, request["deadline"] / 1e9)
            check(deadline)
            kind, body = request["kind"], request["body"]
            try:
                if kind == "init":
                    if permits is not None or body != {}:
                        raise PersistenceError("ML-PERSIST-INIT")
                    permits, writer = _load(config, lambda: check(deadline))
                    response = {
                        "run_id": config["run_id"],
                        "lifecycle_digest": permits._prepared.lifecycle_digest,
                        "session": session,
                        "generation_ns": end,
                    }
                elif permits is None or writer.writer_state != "open":
                    raise PersistenceError("ML-PERSIST-NOT-OPEN")
                elif kind == "commit":
                    if (
                        set(body) != {"unit", "generation"}
                        or type(body["generation"]) is not int
                        or body["generation"] != 1
                        or body["unit"] in attempted
                    ):
                        raise PersistenceError("ML-PERSIST-CLAIM")
                    attempted.add(body["unit"])
                    claim = _persist_intent(
                        permits,
                        writer,
                        session,
                        body["unit"],
                        deadline,
                        check,
                        request["operation"],
                    )
                    claims[body["unit"]] = claim
                    response = {
                        "event": claim.event_id,
                        "intent": "sha256:" + claim.intent_digest.hex(),
                        "flush": "sha256:" + claim.flush_digest.hex(),
                    }
                elif kind == "revalidate":
                    if set(body) != {"unit", "claim"}:
                        raise PersistenceError("ML-PERSIST-CLAIM")
                    claim = claims.get(body["unit"])
                    if (
                        claim is None
                        or body["claim"] != claim.operation
                        or check(deadline) > claim.deadline_ns
                    ):
                        raise PersistenceError("ML-PERSIST-CLAIM")
                    permits.revalidate_start_intent(
                        claim.receipt, now=datetime.now(timezone.utc)
                    )
                    response = {}
                else:
                    if body != {}:
                        raise PersistenceError("ML-PERSIST-ABORT")
                    writer.abort(
                        reason="Maestro persistence owner abort; lifecycle evidence remains incomplete"
                    )
                    response = {"writer_state": writer.writer_state}
                check(deadline)
                reply = dict(request, kind="ok", body=response)
                _send(channel, reply)
                if kind == "abort":
                    return
            except Exception:
                # No exception text/private path/permit material is serialized.
                try:
                    _send(
                        channel,
                        dict(
                            request,
                            kind="error",
                            body={"diagnostic": "ML-PERSIST-WORKER-FAILED"},
                        ),
                    )
                except Exception:
                    pass
                raise
    finally:
        os.close(parent_fd)


def main():
    try:
        if len(sys.argv) != 3:
            raise PersistenceError("ML-PERSIST-ARGUMENTS")
        channel_fd, input_fd = (int(v) for v in sys.argv[1:])
        if min(channel_fd, input_fd) < 3 or channel_fd == input_fd:
            raise PersistenceError("ML-PERSIST-ARGUMENTS")
        channel = socket.socket(fileno=channel_fd)
        serve(channel, input_fd)
        return 0
    except Exception:
        return 70


if __name__ == "__main__":
    os._exit(main())
