"""Bounded, owned concurrent journal-claim exercise; never runs a provider."""

import json
import multiprocessing
import sys
from datetime import datetime, timezone

from xverse_xdl.lifecycle import (
    EvidenceRecord,
    FileEvidenceJournal,
    PermitClaimConflict,
)
from xverse_xdl.models import freeze


def contender(path, serial, barrier, answers):
    journal = FileEvidenceJournal(path)
    record = EvidenceRecord(
        kind="intent",
        sequence=0,
        timestamp=datetime.now(timezone.utc).isoformat(),
        execution_id=f"contender-{serial}",
        action_id="start",
        catalog_identity="test-catalog",
        plan_digest="test-plan",
        permit_id=f"permit-{serial}",
        permit_nonce="shared-nonce",
        status="pending",
        environment_identity="test-owned-fixture",
        resource_revisions=freeze({}),
        artifact_digests=(),
        selection=freeze({}),
    )
    barrier.wait(timeout=10)
    try:
        saved = journal.claim_intent(record)
        answers.put(("claimed", saved.sequence))
    except PermitClaimConflict:
        answers.put(("conflict", None))


def main(path):
    context = multiprocessing.get_context("spawn")
    barrier, answers = context.Barrier(2), context.Queue()
    children = [
        context.Process(target=contender, args=(path, i, barrier, answers))
        for i in range(2)
    ]
    try:
        for child in children:
            child.start()
        result = [answers.get(timeout=15) for _ in children]
        for child in children:
            child.join(timeout=5)
            if child.is_alive() or child.exitcode != 0:
                raise RuntimeError("owned claim child did not terminate successfully")
        print(json.dumps(sorted(result)))
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(timeout=2)
                if child.is_alive():
                    child.kill()
                    child.join(timeout=2)
        answers.close()
        answers.join_thread()


if __name__ == "__main__":
    main(sys.argv[1])
