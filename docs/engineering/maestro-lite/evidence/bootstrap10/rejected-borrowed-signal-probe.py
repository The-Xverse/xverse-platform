import os
import select
import pytest
from tests.thesis_lite.maestro.test_bootstrap import (
    boot_stack as boot_stack, environment as environment, binaries as binaries,
    supervisor_binary as supervisor_binary, native as native, deadline,
)


def test_failure_signal_cannot_follow_borrowed_foreign_pidfd(boot_stack, environment, native):
    session,manager,latch,config,work,boundary,start,clients,owners=boot_stack
    owner,storage,*_=start()
    _,spawn,_=environment
    sentinel_descriptor=boundary('signal-sentinel')
    sentinel,_,line=spawn(native,manager,sentinel_descriptor)
    saved=os.dup(storage._pidfd)
    foreign=os.pidfd_open(sentinel.pid,0)
    try:
        os.dup2(foreign,storage._pidfd)
        with pytest.raises((ValueError,OSError)):
            storage.commit_intent(config.prepared.units[1].unit_id,deadline(1))
        assert not select.select([foreign],[],[],0.2)[0], 'foreign sentinel was signalled'
    finally:
        os.dup2(saved,storage._pidfd)
        os.close(saved)
        os.close(foreign)
