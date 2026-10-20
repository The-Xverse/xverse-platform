"""Actual reads of SYNTHETIC INERT files: no M1 permission or execution."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess

import pytest
from xverse.maestro.bootstrap import encode_bootstrap
from xverse.maestro.prbc import BoundaryAdmission, BoundaryLimits, ProcessBoundaryOps
from xverse.maestro.runtime_admission import admission_digest
from xverse.maestro.runtime_evidence import RuntimeEvidenceFiles, verify_runtime_evidence, MAX_EVIDENCE_FILE
from xverse.maestro.supervisor import CancellationLatch
from .test_runtime_admission import inputs as inputs, pin
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


@pytest.fixture
def evidence(inputs,tmp_path):
    persistence,boot,authorization,facility,pins=inputs
    manager=ProcessBoundaryOps(boot.admission.boundary_parent,BoundaryAdmission(
        persistence.run_id,'supervisor','affa','bootstrap-approval','cleanup-approval',
        'reservation-approval',boot.admission.generation,0),CancellationLatch(),BoundaryLimits(2))
    boot=encode_bootstrap(replace(boot.admission,approval_ref='bootstrap-approval',boundary_parent=manager._root_fd))
    facility=replace(facility,kernel_identity=os.uname().release)
    authorization=replace(authorization,approval_ref='bootstrap-approval',bootstrap_digest=pin(boot.private_bytes),facility_digest=admission_digest(facility))
    pins={k:v for k,v in pins.items() if k.startswith('expected_')}
    pins.update(expected_authorization_digest=admission_digest(authorization),expected_facility_digest=admission_digest(facility))
    paths={};fds=[]
    blobs={'authorization':authorization.canonical_bytes(),'facility':facility.canonical_bytes(),
           **{name:('SYNTHETIC-NOT-EXECUTED:'+name).encode() for name,_ in facility.runtime_case_receipts}}
    for name,blob in blobs.items():
        path=tmp_path/(name+'.receipt');path.write_bytes(blob);paths[name]=path
        fds.append(os.open(path,os.O_RDONLY|os.O_CLOEXEC))
    files=RuntimeEvidenceFiles(fds[0],fds[1],tuple((name,fd) for (name,_),fd in zip(facility.runtime_case_receipts,fds[2:])))
    try:yield persistence,boot,authorization,facility,files,manager,pins,paths
    finally:
        for fd in fds:os.close(fd)
        manager.close()


def checked(evidence,**kw):
    persistence,boot,authorization,facility,files,manager,pins,_=evidence
    return verify_runtime_evidence(persistence,boot,authorization,facility,files,manager,deadline=deadline(2),**dict(pins,**kw))


def test_actual_file_reads_and_current_original_host_checks_are_inert(evidence,monkeypatch):
    from xverse.argus import EvidenceStore
    from xverse_xdl.lifecycle import FileEvidenceJournal
    manager=evidence[5];files=evidence[4]
    def forbidden(*a,**kw):pytest.fail('evidence read attempted lifecycle mutation')
    for fd in (files.authorization,files.facility,*(fd for _,fd in files.runtime_cases)):os.lseek(fd,1,os.SEEK_SET)
    with monkeypatch.context() as patch:
        patch.setattr(subprocess,'Popen',forbidden);patch.setattr(ProcessBoundaryOps,'create_frozen',forbidden)
        patch.setattr(EvidenceStore,'open_run',forbidden);patch.setattr(FileEvidenceJournal,'__init__',forbidden)
        result=checked(evidence)
    assert not result.ready_for_execution and not result.admission.ready_for_execution
    assert result.receipt_digests==evidence[3].runtime_case_receipts
    assert result.parent_identity==manager._root_identity and result.kernel_identity==os.uname().release
    assert not manager._entries and not manager._latch.cancelled
    assert all(os.lseek(fd,0,os.SEEK_CUR)==1 for fd in (files.authorization,files.facility,*(fd for _,fd in files.runtime_cases)))
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out)/'inert-evidence-files.json').write_text(json.dumps(dict(
            synthetic_receipt_bytes_read=True,actual_M1_admissions=0,actual_runtime_helpers=0,
            actual_kernel_checked=result.kernel_identity,current_self_pidfd_KCMP_checked=True,
            ready_for_execution=False),indent=2)+'\n')


@pytest.mark.parametrize('name',['authorization','facility','test_affa','test_unrelated_sentinel'])
def test_changed_original_files_reject_without_trusting_metadata_alone(evidence,name):
    evidence[-1][name].write_bytes(b'changed')
    with pytest.raises(ValueError,match='ML-RUNTIME-EVIDENCE'):checked(evidence)


@pytest.mark.parametrize('fault',['empty','oversized','directory','missing-fd','swapped','missing-case','mutable-set'])
def test_bounded_actual_receipt_inputs_reject(evidence,fault,tmp_path):
    files=evidence[4];cases=files.runtime_cases
    opened=None
    if fault in ('empty','oversized'):
        path=evidence[-1][cases[0][0]]
        with path.open('wb') as f:f.truncate(0 if fault=='empty' else MAX_EVIDENCE_FILE+1)
    elif fault=='directory':
        opened=os.open(tmp_path,os.O_RDONLY|os.O_DIRECTORY);cases=((cases[0][0],opened),*cases[1:])
    elif fault=='missing-fd':cases=((cases[0][0],-1),*cases[1:])
    elif fault=='swapped':cases=((cases[0][0],cases[1][1]),(cases[1][0],cases[0][1]),*cases[2:])
    elif fault=='missing-case':cases=cases[:-1]
    else:cases=list(cases)
    changed=(*evidence[:4],replace(files,runtime_cases=cases),*evidence[5:])
    try:
        with pytest.raises(ValueError,match='ML-RUNTIME-EVIDENCE'):checked(changed)
    finally:
        if opened is not None:os.close(opened)


def test_change_during_actual_pread_rejects(evidence,monkeypatch):
    path=evidence[-1]['test_affa'];inode=path.stat().st_ino
    pread=os.pread;changed=[]
    def read(fd,size,offset):
        data=pread(fd,size,offset)
        if os.fstat(fd).st_ino==inode and not changed:
            with path.open('ab') as stream:stream.write(b'X')
            changed.append(True)
        return data
    with monkeypatch.context() as patch:
        patch.setattr(os,'pread',read)
        with pytest.raises(ValueError,match='EVIDENCE-CHANGED'):checked(evidence)
    assert changed


@pytest.mark.parametrize('fault',['kernel','pidfd','cancelled','foreign-empty-child'])
def test_current_host_and_original_parent_are_required(evidence,monkeypatch,fault):
    manager=evidence[5];made=False
    with monkeypatch.context() as patch:
        if fault=='kernel':
            original=os.uname()
            patch.setattr(os,'uname',lambda:os.uname_result((original.sysname,original.nodename,'changed',original.version,original.machine)))
        elif fault=='pidfd':patch.setattr(os,'pidfd_open',lambda *a:(_ for _ in ()).throw(OSError('owned unavailable pidfd')))
        elif fault=='cancelled':manager._latch.cancel('owned-pre-cancel')
        else:os.mkdir('owned-empty-child',dir_fd=manager._root_fd);made=True
        try:
            with pytest.raises(ValueError,match='ML-RUNTIME-EVIDENCE'):checked(evidence)
        finally:
            if made:os.rmdir('owned-empty-child',dir_fd=manager._root_fd)


def test_caller_clock_override_cannot_supply_current_start_validity(evidence):
    with pytest.raises(TypeError):checked(evidence,now=evidence[2].not_before)
