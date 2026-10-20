"""Revalidation must use current actual durable intent evidence."""

import pytest
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def test_actual_intent_mirror_loss_prevents_revalidation(boot_stack):
    session, _, _, config, work, boundary, _, clients, _ = boot_stack
    storage = session.persistence(config, boundary("storage"), deadline(2))
    clients.append(storage)
    unit = config.prepared.units[0].unit_id
    receipt = storage.commit_intent(unit, deadline(2))
    events = work.parent / "argus" / "events.jsonl"
    assert events.is_file()
    events.rename(events.with_name("saved-events.jsonl"))
    with pytest.raises(ValueError):
        storage.revalidate_intent(receipt, deadline(1))
