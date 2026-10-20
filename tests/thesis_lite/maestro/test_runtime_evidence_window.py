"""Actual UTC expiry during bounded inert receipt I/O, no execution permission."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import os
import time

import pytest
from xverse.maestro.runtime_admission import admission_digest
from .test_runtime_evidence import evidence as evidence, checked
from .test_runtime_admission import inputs as inputs
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


def test_actual_start_window_expiring_during_receipt_read_rejects(evidence,monkeypatch):
    values=list(evidence);now=datetime.now(timezone.utc)
    authorization=replace(values[2],not_before=now-timedelta(seconds=1),expires_at=now+timedelta(seconds=1))
    values[2]=authorization
    values[6]=dict(values[6],expected_authorization_digest=admission_digest(authorization))
    path=values[-1]['authorization'];path.write_bytes(authorization.canonical_bytes())
    inode=path.stat().st_ino;pread=os.pread;observed=[]
    def read(fd,size,offset):
        data=pread(fd,size,offset)
        if os.fstat(fd).st_ino==inode and not observed:
            observed.append(datetime.now(timezone.utc))
            time.sleep(1.1)
        return data
    with monkeypatch.context() as patch:
        patch.setattr(os,'pread',read)
        with pytest.raises(ValueError,match='ML-RUNTIME-START-WINDOW'):
            checked(tuple(values))
    assert len(observed)==1 and observed[0]<authorization.expires_at
    assert datetime.now(timezone.utc)>=authorization.expires_at
