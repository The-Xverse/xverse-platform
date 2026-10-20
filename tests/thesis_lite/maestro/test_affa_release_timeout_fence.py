"""F-01 (helper-bytes review, finding 381): release timeout is fenced by the Python-side cleanup.

The native authority skips its refreeze once the request deadline has elapsed (run_authority.c
freeze_all/close_authority), so after a RELEASE that times out before the workload exec completes
the unit boundary can be left thawed. The documented increment17 precondition is that the owner
treats a REJECTED or uncertain Release as cancellation and the supervisor's cleanup-only authority
terminates the boundary before anything else can thaw it. This control reproduces the timeout
deterministically by freezing the boundary parent (an ancestor freeze keeps the unit frozen while
the authority thaws it), observes the authority's reply, applies the cleanup-only fence while the
ancestor is still frozen, then thaws the ancestor and proves that no workload instruction ever ran.
Observation only for the helper: no helper byte changes; the native strengthening is queued as a
change-spec item (finding 382).
"""
import hashlib
import json
import os
from pathlib import Path
import time

from xverse.maestro.affa_protocol import AuthorityKind as K
from .test_affa_native import authority as authority, authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries

SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _freeze_parent(root_fd, value):
    fd = os.open("cgroup.freeze", os.O_WRONLY | os.O_CLOEXEC, dir_fd=root_fd)
    try:
        os.write(fd, value)
    finally:
        os.close(fd)


def test_release_timeout_under_frozen_ancestor_is_fenced_before_thaw(authority):
    h, work = authority
    h.stage(0)
    ticket_armed_ns = time.monotonic_ns()
    h.arm(0)
    descriptor = h.units[0]["descriptor"]
    root = h.manager._root_fd
    _freeze_parent(root, b"1")
    observations = dict(frozen_parent_at=time.monotonic())
    try:
        began = time.monotonic()
        reply = h.release(0)
        observations.update(reply_kind=reply.kind.name, reply_state=reply.state, reply_reason=reply.reason,
                            reply_epoch=reply.epoch, reply_seconds=round(time.monotonic() - began, 3),
                            marker_before_fence=(work / "u0.marker").exists(),
                            members_before_fence=list(h.manager.residual_membership(descriptor)))
        # Release-timeout discriminators (independent review B-02): REJECTED with the PROTOCOL
        # reason after the ticket window elapsed, no workload instruction yet, and the pre-exec
        # child still a boundary member when the fence is applied.
        ticket_seconds = (h.units[0]["ticket_end"] - ticket_armed_ns) / 1e9
        assert reply.kind is K.REJECTED and reply.reason == 4, (reply.kind, reply.reason)
        assert observations["reply_seconds"] >= ticket_seconds - 0.25, (observations["reply_seconds"], ticket_seconds)
        assert not observations["marker_before_fence"]
        assert observations["members_before_fence"], "pre-exec child was not a member before the fence"
        # Python-side precondition: a REJECTED/uncertain Release is cancellation; cleanup-only
        # authority terminates the boundary while nothing has thawed it yet.
        fenced = h.manager.force_cleanup(descriptor)
        observations.update(boundary_released=fenced.boundary_released, termination_observed=fenced.termination_observed,
                            fenced_at=time.monotonic())
    finally:
        _freeze_parent(root, b"0")
    time.sleep(0.2)  # any surviving pre-exec child would run now; none may
    observations.update(marker_after_thaw=(work / "u0.marker").exists(),
                        members_after_thaw=list(h.manager.residual_membership(descriptor)) if not observations.get("boundary_released") else [])
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        target = Path(output)
        target.mkdir(parents=True, exist_ok=True)
        (target / ("release-timeout-fence-" + Path(work).name + ".json")).write_text(json.dumps(dict(
            observations=dict(observations, ticket_seconds=round(ticket_seconds, 3)), source_sha256=SOURCE_SHA256, helper_finding="F-01", helper_bytes_changed=False,
            precondition="REJECTED release -> cleanup-only termination before any thaw", accepted=False), indent=2))
    assert fenced.boundary_released and fenced.termination_observed
    assert not (work / "u0.marker").exists(), "workload instruction reached the child after a REJECTED release"
    assert not observations["marker_before_fence"]
    # The authority process itself is retired by the fixture teardown; its exit is not part of the fence.
