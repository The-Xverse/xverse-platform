"""Fixed host commands and original-child kernel ownership, native Linux only.

This is a provider building block, not a hostile-code sandbox or process-tree
controller. Each child must own/release its own descendants through separate
reviewed handles. No signal is ever sent to a group, name, or reconstructed PID.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from .inspection import ExecutionInputError, _DIGEST, canonical, sha256


class ProcessOwnershipError(ExecutionInputError):
    """A child started but kernel ownership admission failed; retain this child.

    The trusted provider must keep child for cleanup. Unknown ownership grants
    no signal authority; diagnostics must not serialize the underlying Popen.
    """
    def __init__(self, child):
        self.child = child
        super().__init__('MPX-PROCESS-OWNERSHIP-UNAVAILABLE')


@dataclass(frozen=True)
class InstallationFile:
    """Host-installed binary/script identity, excluded from public summaries."""
    path: Path = field(repr=False)
    digest: str

    def verify(self):
        if type(self.digest) is not str or not _DIGEST.fullmatch(self.digest):
            raise ExecutionInputError('MPX-INSTALLATION-INVALID')
        try:
            if not self.path.is_absolute() or self.path.is_symlink() or not self.path.is_file():
                raise ExecutionInputError('MPX-INSTALLATION-INVALID')
            # Installation bounds are separate from project document bounds.
            size = self.path.stat().st_size
            if size > 256*1024*1024:
                raise ExecutionInputError('MPX-INSTALLATION-LIMIT')
            import hashlib
            digest = hashlib.sha256()
            count = 0
            with self.path.open('rb') as stream:
                while chunk := stream.read(1024*1024):
                    count += len(chunk)
                    if count > 256*1024*1024:
                        raise ExecutionInputError('MPX-INSTALLATION-LIMIT')
                    digest.update(chunk)
            if 'sha256:' + digest.hexdigest() != self.digest:
                raise ExecutionInputError('MPX-INSTALLATION-CHANGED')
        except OSError:
            raise ExecutionInputError('MPX-INSTALLATION-UNAVAILABLE') from None


@dataclass(frozen=True)
class FixedProcessInstallation:
    """All command/environment strings originate in trusted host registration.

    The imported project supplies no executable, argv, cwd or environment. Frozen
    semantic configuration is transferred as bounded data on stdin, never -c or
    shell text. Pins must include the executable and every interpreted script.
    """
    executable: Path = field(repr=False)
    arguments: tuple[str, ...] = field(repr=False)
    working_directory: Path = field(repr=False)
    environment: tuple[tuple[str, str], ...] = field(repr=False)
    files: tuple[InstallationFile, ...] = field(repr=False)

    @property
    def installation_digest(self):
        """Pin actual host command, paths, environment and expected file content.

        The public value is a digest only. verify independently checks current
        file contents; environment/path values themselves never enter a summary.
        """
        return sha256(b'xverse.maestro.fixed-process-installation.v1\0' + canonical({
            'executable': str(self.executable), 'arguments': self.arguments,
            'workingDirectory': str(self.working_directory), 'environment': self.environment,
            'files': [{'path': str(p.path), 'digest': p.digest} for p in self.files]}))

    def verify(self):
        if (sys.platform != 'linux' or not hasattr(os, 'pidfd_open')
                or not hasattr(signal, 'pidfd_send_signal')):
            raise ExecutionInputError('MPX-PROCESS-OWNERSHIP-UNSUPPORTED')
        if (type(self.arguments) is not tuple or len(self.arguments) > 64
                or any(type(v) is not str or len(v) > 4096 or '\0' in v for v in self.arguments)
                or type(self.environment) is not tuple or len(self.environment) > 128
                or any(type(v) is not tuple or len(v) != 2
                    or any(type(s) is not str or len(s) > 4096 or '\0' in s for s in v)
                    or not v[0] or '=' in v[0] for v in self.environment)
                or len(dict(self.environment)) != len(self.environment)
                or type(self.files) is not tuple or not 1 <= len(self.files) <= 128
                or any(type(v) is not InstallationFile for v in self.files)
                or self.executable not in {v.path for v in self.files}
                or not self.working_directory.is_absolute()
                or not self.working_directory.is_dir()):
            raise ExecutionInputError('MPX-INSTALLATION-INVALID')
        for pin in self.files:
            pin.verify()

    def launch(self):
        """Return ownership before data transfer, so partial failures can clean up."""
        self.verify()
        process = subprocess.Popen([str(self.executable), *self.arguments],
            cwd=self.working_directory, env=dict(self.environment), shell=False,
            close_fds=True, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        return OwnedChild(process)


class OwnedChild:
    """Original Popen plus pidfd: no authority can be reconstructed from metadata."""
    def __init__(self, process):
        self.reference = 'child-' + uuid.uuid4().hex
        self._process = process
        self._pidfd = None
        self._birth = None
        self._closed = False
        try:
            # An unreaped original child retains its PID even if it exits here;
            # pidfd_open cannot accidentally bind a reused unrelated process.
            self._pidfd = os.pidfd_open(process.pid, 0)
            self._birth = self._birth_of_child()
        except OSError:
            raise ProcessOwnershipError(self) from None

    def _birth_of_child(self):
        # /proc stat field22 follows the final ')' of comm, which may itself
        # contain spaces/parentheses. This witness supplements the kernel handle.
        value = Path(f'/proc/{self._process.pid}/stat').read_text()
        return value[value.rfind(')') + 2:].split()[19]

    def configure(self, configuration: bytes):
        """Transfer frozen semantic data after the provider retains this handle."""
        if type(configuration) is not bytes or len(configuration) > 4096:
            raise ExecutionInputError('MPX-PROCESS-CONFIG-LIMIT')
        try:
            # The bounded transfer fits Linux PIPE_BUF even before the child
            # reads. Use nonblocking I/O so provider deadlines remain finite.
            descriptor = self._process.stdin.fileno()
            os.set_blocking(descriptor, False)
            if os.write(descriptor, configuration) != len(configuration):
                raise OSError()
            self._process.stdin.close()
        except (OSError, ValueError):
            raise ExecutionInputError('MPX-PROCESS-CONFIG-DELIVERY-FAILED') from None

    def observe(self):
        if self._closed:
            return 'released'
        if self._process.poll() is not None:
            return 'exited'
        if self._pidfd is None or self._birth is None:
            return 'unknown'
        try:
            if self._birth_of_child() != self._birth:
                return 'unknown'
            signal.pidfd_send_signal(self._pidfd, 0)
        except OSError:
            return 'unknown'
        return 'running'

    def stop(self, *, deadline: float):
        """Signal the kernel handle only; timeout/ownership loss stays unknown."""
        if self._closed:
            return 'released'
        state = self.observe()
        if state == 'unknown':
            return 'unknown'
        if state == 'running':
            try:
                signal.pidfd_send_signal(self._pidfd, signal.SIGTERM)
                self._process.wait(timeout=max(0, deadline - time.monotonic()))
            except (OSError, subprocess.TimeoutExpired):
                return 'unknown'
        if self._pidfd is not None:
            os.close(self._pidfd)
        if self._process.stdin is not None and not self._process.stdin.closed:
            self._process.stdin.close()
        self._closed = True
        return 'released'
