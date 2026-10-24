"""Private trusted-bootstrap whole lifecycle; public admitted start remains gated.

This component creates effects only within its caller's separately approved
original bootstrap/permit scope. RuntimeEvidencePins are never accepted as an
execution capability. No public top-level start is exported here.
"""
from dataclasses import dataclass, field
import re
import threading
import time

from .bootstrap_launcher import OriginalBootstrapLauncher
from .dispatcher import FiniteDispatcher
from .owner import _Original, _deadline, OwnerError
from .persistence import PersistenceInput, PersistenceRPCFailure
from .prbc import BoundaryDescriptor
from .providers import ProcessReadiness
from .run_broker import RunBroker, UnitAdmission
from .run_closure import RunClosure
from .time import HostDeadline


@dataclass(frozen=True)
class RuntimeScope:
    startup: HostDeadline
    active: HostDeadline
    terminal: HostDeadline
    closure: HostDeadline


@dataclass(frozen=True)
class RuntimeResult:
    run_id: str
    dispatch: object
    closure: object
    startup: object
    diagnostics: tuple[str,...]
    persistence_failure: PersistenceRPCFailure | None = None
    lifecycle_complete: bool = field(default=False,init=False)
    ready_for_execution: bool = field(default=False,init=False)

    @property
    def execution_succeeded(self):
        return self.dispatch.execution_succeeded if self.dispatch is not None else None

    @property
    def cleanup_complete(self):
        return self.closure.cleanup_complete if self.closure is not None else False


class _OriginalRuntimeRun(_Original):
    """Original internal composition, never constructed from public run metadata."""
    def __init__(self,persistence,launcher,units,*,controller_sessions=1,allow_restarts=False,allow_controller_recovery=False,
                 fault_clock_channel=None):
        from xverse.faults.simtime import HubChannel
        if fault_clock_channel is not None and type(fault_clock_channel) is not HubChannel:
            raise OwnerError('ML-RUNTIME-ENTRY-INPUT')
        if (type(persistence) is not PersistenceInput or type(launcher) is not OriginalBootstrapLauncher
            or type(units) is not tuple or any(type(u) is not UnitAdmission for u in units)
            or type(controller_sessions) is not int or not 1<=controller_sessions<=16
            or type(allow_restarts) is not bool or type(allow_controller_recovery) is not bool):
            raise OwnerError('ML-RUNTIME-ENTRY-INPUT')
        launcher._holder()
        if (persistence.schedule is None or persistence.collection is None or persistence.coverage is None
            or persistence.run_id!=launcher.config.admission.run_id
            or persistence.prepared.lifecycle_digest!=launcher.config.admission.lifecycle_digest
            or persistence.generation_ns!=int(launcher.config.admission.generation.monotonic_seconds*1e9)
            or persistence.session!=launcher.config.admission.generation.session
            or launcher.boundaries._entries
            or sum(u.maximum_generation for u in units)+2+controller_sessions>launcher.boundaries._limits.max_boundaries
            or tuple(u.descriptor.unit_id for u in units)!=tuple(u.unit_id for u in persistence.prepared.units)
            or len({u.descriptor.boundary_id for u in units})!=len(units)
            or any(u.descriptor.run_id!=persistence.run_id or u.descriptor.generation!=1
                or u.descriptor.creation_epoch!=launcher.boundaries.release_epoch for u in units)):
            raise OwnerError('ML-RUNTIME-ENTRY-SCOPE')
        for u in units:u.__post_init__()
        self._retain()
        self._persistence,self._launcher,self._units=persistence,launcher,units
        self._fault_channel=fault_clock_channel  # ADR-ML3-SIMTIME-0001: trusted channel to the clock-source unit
        self._pins=(persistence,launcher,units,persistence.private_bytes,controller_sessions,allow_restarts,allow_controller_recovery)
        self._lock=threading.Lock()
        self._stop_lock=threading.Lock()
        self._scope=self._result=self._driver=self._broker=self._storage=self._session=None
        self._stop_scope=None
        self._disposed=False
        self._runtime_pins=(None,None,None,None)
        self._registry_owner=self._registry_pin=None

    def _holder(self):
        super()._holder()
        if (any(a is not b for a,b in zip((self._persistence,self._launcher,self._units),self._pins))
            or self._persistence.private_bytes!=self._pins[3]
            or self._registry_owner is not self._registry_pin
            or any(a is not b for a,b in zip((self._session,self._storage,self._broker,self._driver),self._runtime_pins))):
            raise OwnerError('ML-RUNTIME-ENTRY-REPLACED')
        if self._registry_owner is not None:
            self._registry_owner._holder()
            if self._registry_owner._entries.get(self._pins[0].run_id) is not self:
                raise OwnerError('ML-RUNTIME-ENTRY-REGISTRY')
        self._launcher._holder()

    def _validate_scope(self,scope):
        if type(scope) is not RuntimeScope:raise OwnerError('ML-RUNTIME-ENTRY-END')
        session=self._persistence.session
        for end in (scope.startup,scope.active,scope.terminal,scope.closure):
            if type(end) is not HostDeadline or end.session!=session:
                raise OwnerError('ML-RUNTIME-ENTRY-END')
            end.__post_init__()
        _deadline(scope.startup,session)
        now=time.monotonic();config=self._persistence;plan=config.collection
        reserve=config.schedule.terminal_reserve_seconds+plan.collection_seconds+plan.terminal_seconds
        if (not now<scope.startup.monotonic_seconds<scope.active.monotonic_seconds<scope.terminal.monotonic_seconds<=scope.closure.monotonic_seconds
            or scope.startup.monotonic_seconds>self._launcher.config.admission.lease.monotonic_seconds
            or scope.active.monotonic_seconds>config.coverage.data(config.coverage.digest)['end']
            or scope.terminal.monotonic_seconds<scope.active.monotonic_seconds+reserve
            or scope.closure.monotonic_seconds>config.generation_ns/1e9
            or scope.closure.monotonic_seconds-now>90):
            raise OwnerError('ML-RUNTIME-ENTRY-END')

    def _startup_end(self):
        _deadline(self._scope.startup,self._persistence.session)
        self._pins[1].check_start_authorization()
        return self._scope.startup

    def start(self,scope):
        self._holder()
        if self._disposed:raise OwnerError('ML-RUNTIME-ENTRY-DISPOSED')
        if not self._lock.acquire(False):raise OwnerError('ML-RUNTIME-ENTRY-CONFLICT')
        try:
            if self._scope is not None:
                if scope!=self._scope:raise OwnerError('ML-RUNTIME-ENTRY-REPEAT')
                if self._result is not None:return self._result
                raise OwnerError('ML-RUNTIME-ENTRY-RETAINED')
            self._validate_scope(scope)
            if self._launcher.boundaries._latch.cancelled:raise OwnerError('ML-RUNTIME-ENTRY-CANCELLED')
            self._scope=scope
            dispatch=closure=None;diagnostics=[];fatal=None;persistence_failure=None
            try:
                self._session=self._launcher.launch(self._startup_end())
                self._runtime_pins=(self._session,None,None,None)
                manager=self._launcher.boundaries;config=self._persistence
                def boundary(name,unit):
                    end=self._startup_end()
                    desc=BoundaryDescriptor(config.run_id,unit,1,name,manager.release_epoch)
                    manager.create_frozen(desc,deadline=end)
                    return desc
                self._storage=self._session.persistence(config,boundary('runtime-storage','helper:storage'),self._startup_end())
                self._runtime_pins=(self._session,self._storage,None,None)
                for setup in self._units:
                    manager.create_frozen(setup.descriptor,deadline=self._startup_end())
                self._broker=RunBroker.admit(self._session,self._storage,self._units,
                    boundary('runtime-authority','helper:authority'),deadline=self._startup_end(),controller_sessions=self._pins[4])
                self._runtime_pins=(self._session,self._storage,self._broker,None)
                facade=ProcessReadiness(self._broker.owner,policies=config.schedule.policies)
                controller=self._broker.admit_controller('runtime-controller',self._startup_end())
                self._driver=FiniteDispatcher(facade,self._session,
                    gates=tuple((u.unit_id,self._broker.connection) for u in config.prepared.units),controller=controller,
                    allow_restarts=self._pins[5],allow_controller_recovery=self._pins[6],
                    fault_clock_channel=self._fault_channel)
                self._runtime_pins=(self._session,self._storage,self._broker,self._driver)
                dispatch=self._driver.run(scope.active,scope.terminal)
            except BaseException as error:
                code=str(error);diagnostics.append(code if re.fullmatch(r'ML-[A-Z0-9-]+',code) else 'ML-RUNTIME-ENTRY-FAILED')
                failure=getattr(error,'rpc_failure',None)
                if type(failure) is PersistenceRPCFailure:persistence_failure=failure
                if not isinstance(error,Exception):fatal=error
            finally:
                try:
                    session,storage,broker,driver=self._runtime_pins
                    launcher=self._pins[1]
                    if session is not None:
                        closer=RunClosure(session,dispatcher=driver,broker=broker)
                        closure=closer.close(scope.closure)
                    elif launcher._birth_attempted:
                        end=min(scope.closure.monotonic_seconds,time.monotonic()+1.8)
                        launcher.drain(HostDeadline(self._pins[0].session,end))
                except (ValueError,OSError):diagnostics.append('ML-RUNTIME-ENTRY-CLOSURE-UNRESOLVED')
            original_storage=self._runtime_pins[1]
            if original_storage is not None:
                try:persistence_failure=original_storage.rpc_failure
                except Exception:
                    persistence_failure=None
                    diagnostics.append('ML-RUNTIME-RPC-CONTEXT-UNRESOLVED')
            self._result=RuntimeResult(self._pins[0].run_id,dispatch,closure,self._pins[1].outcome,tuple(diagnostics),persistence_failure)
            if fatal is not None:raise fatal
            return self._result
        finally:self._lock.release()

    def stop(self,run_id,*,reason='runtime-stop'):
        _Original._holder(self)
        if run_id!=self._pins[0].run_id:raise OwnerError('ML-RUNTIME-ENTRY-IDENTITY')
        if not self._stop_lock.acquire(False):raise OwnerError('ML-RUNTIME-ENTRY-CONFLICT')
        try:
            if self._stop_scope is not None and reason!=self._stop_scope:raise OwnerError('ML-RUNTIME-ENTRY-REPEAT')
            if self._stop_scope is not None:return 1  # original monotonic latch epoch, no repeated signal/RPC
            launcher=self._pins[1]
            epoch=launcher.boundaries._latch.cancel(reason)
            self._stop_scope=reason
            driver=self._runtime_pins[3]
            if driver is not None:driver.cancel(reason)
            else:launcher.cancel(reason)
            return epoch
        finally:self._stop_lock.release()

    def collect(self,run_id):
        self._holder()
        if run_id!=self._persistence.run_id:raise OwnerError('ML-RUNTIME-ENTRY-IDENTITY')
        if self._lock.locked() or self._result is None:raise OwnerError('ML-RUNTIME-ENTRY-CONFLICT')
        return self._result.dispatch.collection if self._result.dispatch is not None else None

    def restart(self,run_id,unit_id,*,permit,generation,deadline):
        self._holder()
        if self._driver is None:raise OwnerError('ML-RUNTIME-ENTRY-NOT-ACTIVE')
        return self._driver.restart(run_id,unit_id,permit=permit,generation=generation,deadline=deadline)

    def restart_result(self,ticket):
        self._holder()
        if self._driver is None:raise OwnerError('ML-RUNTIME-ENTRY-NOT-ACTIVE')
        return self._driver.restart_result(ticket)

    def restart_many(self,run_id,requests,*,deadline):
        self._holder()
        if self._driver is None:raise OwnerError('ML-RUNTIME-ENTRY-NOT-ACTIVE')
        return self._driver.restart_many(run_id,requests,deadline=deadline)

    def replace_controller(self,run_id,*,session_id,deadline):
        self._holder()
        if self._driver is None:raise OwnerError('ML-RUNTIME-ENTRY-NOT-ACTIVE')
        return self._driver.replace_controller(run_id,session_id=session_id,deadline=deadline)

    def controller_recovery_result(self,ticket):
        self._holder()
        if self._driver is None:raise OwnerError('ML-RUNTIME-ENTRY-NOT-ACTIVE')
        return self._driver.controller_recovery_result(ticket)

    def dispose(self):
        self._holder()
        if self._disposed:return
        if not self._lock.acquire(False):raise OwnerError('ML-RUNTIME-ENTRY-CONFLICT')
        try:
            if self._result is None:raise OwnerError('ML-RUNTIME-ENTRY-RETAINED')
            observed=self._launcher.outcome
            if (not observed.supervisor_reaped or observed.registered and (
                not observed.registered_helpers_reaped or observed.unacknowledged_births)):
                raise OwnerError('ML-RUNTIME-ENTRY-RETAINED')
            if self._broker is not None:self._broker.dispose()
            self._launcher.dispose()
            self._disposed=True
        finally:self._lock.release()


class _OriginalRuntimeRegistry(_Original):
    """Private trusted-bootstrap run/control ownership, not approval authentication."""
    def __init__(self,maximum_runs):
        if type(maximum_runs) is not int or not 1<=maximum_runs<=128:
            raise OwnerError('ML-RUNTIME-REGISTRY-CAPACITY')
        self._retain()
        self._maximum=self._maximum_pin=maximum_runs
        self._entries=self._entries_pin={}
        self._log=self._log_pin=()
        self._cleanup_log=self._cleanup_pin=()
        self._lock=threading.Lock()

    def _holder(self):
        super()._holder()
        if self._cleanup_log is not self._cleanup_pin:
            raise OwnerError('ML-RUNTIME-REGISTRY-CLEANUP-LOST')
        if (self._entries is not self._entries_pin or self._log is not self._log_pin
            or tuple(self._entries.items())!=self._log or self._maximum!=self._maximum_pin):
            raise OwnerError('ML-RUNTIME-REGISTRY-REPLACED')

    def reserve(self,run,*,start_window=None):
        self._holder()
        if type(run) is not _OriginalRuntimeRun:raise OwnerError('ML-RUNTIME-REGISTRY-INPUT')
        if not self._lock.acquire(False):raise OwnerError('ML-RUNTIME-REGISTRY-CONFLICT')
        held=False
        try:
            run._holder();key=run._pins[0].run_id
            original=self._entries.get(key)
            if original is not None:
                if original is not run:raise OwnerError('ML-RUNTIME-REGISTRY-REPEAT')
                if start_window is not None and run._pins[1]._start_window is not start_window:
                    raise OwnerError('ML-RUNTIME-REGISTRY-REPEAT')
                return original
            if not run._lock.acquire(False):raise OwnerError('ML-RUNTIME-REGISTRY-CONFLICT')
            held=True
            if (run._registry_owner is not None or run._scope is not None
                or run._pins[1]._birth_attempted or run._pins[1]._disposed):
                raise OwnerError('ML-RUNTIME-REGISTRY-ORIGINAL')
            if len(self._entries)>=self._maximum:raise OwnerError('ML-RUNTIME-REGISTRY-FULL')
            if start_window is not None:run._pins[1].bind_start_authorization(start_window)
            run._registry_owner=run._registry_pin=self
            self._entries[key]=run
            self._log=self._log_pin=tuple(self._entries.items())
            self._cleanup_log=self._cleanup_pin=(*self._cleanup_log,(key,run))
            return run
        finally:
            if held:run._lock.release()
            self._lock.release()

    def _run(self,run_id):
        self._holder()
        if type(run_id) is not str:raise OwnerError('ML-RUNTIME-REGISTRY-IDENTITY')
        original=self._entries.get(run_id)
        if original is None:raise OwnerError('ML-RUNTIME-REGISTRY-UNKNOWN')
        original._holder()
        return original

    def start(self,run_id,scope):
        return self._run(run_id).start(scope)

    def collect(self,run_id):
        return self._run(run_id).collect(run_id)

    def stop(self,run_id,*,reason='runtime-stop'):
        _Original._holder(self)
        if self._cleanup_log is not self._cleanup_pin:
            raise OwnerError('ML-RUNTIME-REGISTRY-CLEANUP-LOST')
        if type(run_id) is not str:raise OwnerError('ML-RUNTIME-REGISTRY-IDENTITY')
        for key,original in self._cleanup_log:
            if key==run_id:return original.stop(run_id,reason=reason)
        raise OwnerError('ML-RUNTIME-REGISTRY-UNKNOWN')

    def restart(self,run_id,unit_id,*,permit,generation,deadline):
        return self._run(run_id).restart(run_id,unit_id,permit=permit,generation=generation,deadline=deadline)

    def restart_many(self,run_id,requests,*,deadline):
        return self._run(run_id).restart_many(run_id,requests,deadline=deadline)

    def restart_result(self,run_id,ticket):
        return self._run(run_id).restart_result(ticket)

    def replace_controller(self,run_id,*,session_id,deadline):
        return self._run(run_id).replace_controller(run_id,session_id=session_id,deadline=deadline)

    def controller_recovery_result(self,run_id,ticket):
        return self._run(run_id).controller_recovery_result(ticket)
