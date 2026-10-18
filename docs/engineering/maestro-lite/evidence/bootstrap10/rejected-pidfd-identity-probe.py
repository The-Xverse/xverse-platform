import os
import pytest
from tests.thesis_lite.maestro.test_bootstrap import (
    boot_stack as boot_stack, environment as environment,
    binaries as binaries, supervisor_binary as supervisor_binary, raw_storage,
)


def test_foreign_pidfd_replacement_must_not_retain_supervisor_liveness(boot_stack):
    session, *_ = boot_stack
    child, channel, _, _ = raw_storage(boot_stack)
    original = os.dup(session._pidfd)
    try:
        root_info, child_info = os.fstat(session._pidfd), os.fstat(child._fd)
        assert (root_info.st_dev, root_info.st_ino) == (child_info.st_dev, child_info.st_ino)
        os.dup2(child._fd, session._pidfd)
        with pytest.raises(ValueError):
            session._live()
    finally:
        os.dup2(original, session._pidfd)
        os.close(original)
        channel.close()
