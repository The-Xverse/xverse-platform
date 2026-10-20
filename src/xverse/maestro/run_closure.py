"""Finite closure of the original issued inventory; evidence completeness stays separate."""

from dataclasses import dataclass, field
import math
import threading
import time
import signal
import select

from .bootstrap import BootstrapSession
from .affa_client import AuthorityConnection
from .affa_protocol import AuthorityFrame, AuthorityKind as K
from .controller import ControllerSession
from .run_broker import NativeGenerationClosure, RunBroker
from .dispatcher import FiniteDispatcher
from .launcher import CatalogLauncher
from .owner import _Original, OwnerError, GateConnection
from .persistence import PersistenceClient
from .teardown import ReverseTeardown
from .time import HostDeadline
from .writer_closure import WriterClosure, unresolved
from .terminal_runtime import TerminalReceipt


class ClosureError(OwnerError):
    pass


@dataclass(frozen=True)
class IssuedBoundaryClosure:
    unit_id: str
    generation: int
    empty: bool
    released: bool
    diagnostic: str | None


@dataclass(frozen=True)
class HelperClosure:
    slot: int
    role: int
    unit_id: str
    process_reaped: bool
    returncode: int | None
    direct_child_reaped: bool | None
    client_retained: bool


@dataclass(frozen=True)
class RunClosureResult:
    run_id: str
    lifecycle_digest: str
    execution_succeeded: bool | None
    normal_unit_records_complete: bool
    helpers: tuple[HelperClosure, ...]
    boundaries: tuple[IssuedBoundaryClosure, ...]
    writers: tuple[WriterClosure, ...]
    root_reaped: bool
    final_freeze_acknowledged: bool
    unacknowledged_births: int
    inventory_complete: bool
    diagnostics: tuple[str, ...]
    lifecycle_complete: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)
    local_control_disposed: bool = field(default=False, init=False)
    native_units: tuple[NativeGenerationClosure, ...] = ()
    authority_fenced: bool | None = None
    terminal_reports: tuple[TerminalReceipt, ...] = ()

    @property
    def cleanup_complete(self):
        return (
            self.inventory_complete
            and self.root_reaped
            and self.unacknowledged_births == 0
            and all(
                h.process_reaped and (h.role not in (1, 4) or h.direct_child_reaped)
                for h in self.helpers
            )
            and all(b.empty and b.released for b in self.boundaries)
            and (not any(h.role == 4 for h in self.helpers) or self.authority_fenced is True)
        )


class RunClosure(_Original):
    def __init__(
        self,
        bootstrap,
        *,
        dispatcher=None,
        teardown=None,
        broker=None,
        terminal_seconds=0.5,
        drain_seconds=0.75,
        boundary_seconds=0.75,
    ):
        if type(bootstrap) is not BootstrapSession:
            raise ClosureError("ML-CLOSURE-ROOT")
        bootstrap._holder()
        if dispatcher is not None:
            if type(dispatcher) is not FiniteDispatcher or teardown is not None:
                raise ClosureError("ML-CLOSURE-DISPATCHER")
            dispatcher._holder()
            if dispatcher.bootstrap is not bootstrap:
                raise ClosureError("ML-CLOSURE-ISSUER")
            teardown = dispatcher.teardown
        if teardown is not None:
            if type(teardown) is not ReverseTeardown:
                raise ClosureError("ML-CLOSURE-TEARDOWN")
            teardown._holder()
            if (
                teardown.manager is not bootstrap.boundaries
                or getattr(teardown.owner.persistence.process, "_root", None)
                is not bootstrap
            ):
                raise ClosureError("ML-CLOSURE-ISSUER")
        derived = teardown.owner._run_broker_pin if teardown else None
        if broker is not None:
            if type(broker) is not RunBroker or broker.session is not bootstrap:
                raise ClosureError("ML-CLOSURE-BROKER")
            broker._cleanup_context()
            if derived is not None and derived is not broker:
                raise ClosureError("ML-CLOSURE-BROKER")
        self._broker = broker if broker is not None else derived
        for value, maximum in (
            (terminal_seconds, 2),
            (drain_seconds, 2),
            (boundary_seconds, 5),
        ):
            try:
                valid = (
                    type(value) in (int, float)
                    and math.isfinite(value)
                    and 0 < value <= maximum
                )
            except OverflowError:
                valid = False
            if not valid:
                raise ClosureError("ML-CLOSURE-BUDGET")
        self._retain()
        self.bootstrap, self.dispatcher, self.teardown = bootstrap, dispatcher, teardown
        self._budgets = (terminal_seconds, drain_seconds, boundary_seconds)
        self._pins = (
            bootstrap,
            dispatcher,
            teardown,
            bootstrap._issued,
            bootstrap._clients,
            bootstrap._children,
            bootstrap.boundaries._entries,
            self._budgets,
            self._broker,
        )
        self._lock = threading.Lock()
        self._scope = self._result = None

    def _holder(self):
        super()._holder()
        root = self.bootstrap
        if any(
            a is not b
            for a, b in zip(
                (
                    root,
                    self.dispatcher,
                    self.teardown,
                    root._issued,
                    root._clients,
                    root._children,
                    root.boundaries._entries,
                    self._budgets,
                    self._broker,
                ),
                self._pins,
            )
        ):
            raise ClosureError("ML-CLOSURE-REPLACED")

    @staticmethod
    def _fence(connection, end):
        try:
            connection._holder()
            if connection._epoch_history[-1].kind is K.CANCELLED:
                return True
            connection._exchange(AuthorityFrame(K.CANCEL, connection.sequence+1,
                int(end*1e9), connection.config.scope, epoch=connection.epoch))
            return True
        except (ValueError, OSError):
            try:
                result = connection.revoke(HostDeadline(connection.child._root.session, end))
                return result.issuer_dead and result.issuer_reaped
            except (ValueError, OSError):
                return False

    def cancel(self, reason="run-closure-cancel"):
        super()._holder()
        # No normal mutation lock or storage operation precedes cancellation.
        root = self._pins[0]
        root._pins[4].cancel(reason)
        for slot, client in tuple(root._clients.items()):
            if type(client) is AuthorityConnection and root._issued.get(slot, (None,))[0] == 4:
                if not self._fence(client, min(time.monotonic()+0.5, root._generation/1e9)):
                    root.cancel(reason)

    def close(self, deadline, *, reason="run-closure"):
        self._holder()
        root = self.bootstrap
        if type(deadline) is not HostDeadline or deadline.session != root.session:
            raise ClosureError("ML-CLOSURE-SESSION")
        deadline.__post_init__()
        if (
            type(reason) is not str
            or not 0 < len(reason) <= 64
            or any(not (c.isascii() and (c.isalnum() or c in "-_")) for c in reason)
        ):
            raise ClosureError("ML-CLOSURE-REASON")
        scope = (deadline, reason)
        if self._scope is not None and scope != self._scope:
            raise ClosureError("ML-CLOSURE-REPEAT")
        if self._result is not None:
            return self._result
        root._holder()
        end = deadline.monotonic_seconds
        if not 0 < end - time.monotonic() <= 90 or int(end * 1e9) > root._generation:
            raise ClosureError("ML-CLOSURE-DEADLINE")
        locks = []
        reserved = None
        try:
            for lock in (self._lock, root._lock) + (
                (self.dispatcher._lock,) if self.dispatcher else ()
            ):
                if not lock.acquire(False):
                    raise ClosureError("ML-CLOSURE-CONFLICT")
                locks.append(lock)
            invalid_adapters = set()
            for slot, client in root._clients.items():
                role = root._issued[slot][0]
                if (
                    type(client)
                    is not {
                        1: CatalogLauncher,
                        2: GateConnection,
                        3: PersistenceClient,
                        4: AuthorityConnection,
                        5: ControllerSession,
                    }[role]
                ):
                    raise ClosureError("ML-CLOSURE-ISSUER")
                original = (client._process_pin if role == 2 else
                    client._pins[1] if role == 5 else client._pins[0])
                if original is not root._children.get(slot):
                    raise ClosureError("ML-CLOSURE-ISSUER")
                try:
                    client._holder()
                    current = client.child if role == 4 else client.process
                    if current is not original or (
                        role == 2 and client.channel is not client._channel_pin
                    ):
                        raise ClosureError("ML-CLOSURE-ADAPTER-UNRESOLVED")
                except (ValueError, OSError):
                    invalid_adapters.add(slot)
            if self.teardown:
                self.teardown._holder()
                owner = self.teardown.owner
                temporary = []
                try:
                    for lock in (
                        self.teardown._lock,
                        self.teardown.facade._lock,
                        owner._lock,
                        *((owner._run_broker_pin._lock,) if owner._run_broker_pin else ()),
                    ):
                        if not lock.acquire(False):
                            raise ClosureError("ML-CLOSURE-CONFLICT")
                        temporary.append(lock)
                    if owner._dispatch_owner is not None:
                        raise ClosureError("ML-CLOSURE-CONFLICT")
                    owner._dispatch_owner, owner._dispatch_thread = (
                        self,
                        threading.get_ident(),
                    )
                    reserved = owner
                finally:
                    for lock in reversed(temporary):
                        lock.release()
            self._scope = scope
            terminal_budget, drain_budget, boundary_budget = self._budgets
            diagnostics, writers, terminal_reports = [], [], []
            units = self.teardown._result if self.teardown else None
            if self.teardown and units is None:
                unit_end = min(
                    end - terminal_budget - 2 * drain_budget - boundary_budget,
                    time.monotonic() + 80,
                )
                try:
                    units = self.teardown.run(
                        HostDeadline(root.session, unit_end), reason=reason
                    )
                except Exception:
                    diagnostics.append("ML-CLOSURE-UNIT-UNRESOLVED")
            self.cancel(reason)
            native_units = []
            native_inventory_complete = True
            broker = self._broker
            if broker is not None:
                try:
                    broker._cleanup_context()
                    registry = broker._generation_issuer_registry
                    if type(registry) is not dict or tuple(registry.items()) != broker._generation_issuer_log:
                        raise ClosureError("ML-CLOSURE-INVENTORY-UNRESOLVED")
                    generations = tuple(registry.items())
                except (ValueError, OSError, AttributeError, TypeError):
                    generations = ()
                    native_inventory_complete = False
                    diagnostics.append("ML-CLOSURE-INVENTORY-UNRESOLVED")
                for (unit, generation), issuer in generations:
                    try:
                        native_units.append(issuer._closure_fact())
                    except (ValueError, OSError):
                        native_units.append(NativeGenerationClosure(unit, generation, None, None, None))
            if invalid_adapters:
                diagnostics.append("ML-CLOSURE-ADAPTER-UNRESOLVED")
            # Root birth adapters are serialized by root._lock; all inventories
            # are the original retained dictionaries, never caller-supplied lists.
            issued = tuple(sorted(root._issued.items()))
            clients = tuple(sorted(root._clients.items()))
            manager = root.boundaries
            inventory_complete = native_inventory_complete
            descriptors = ()
            try:
                with manager._cleanup_lock(deadline):
                    descriptors = tuple(e.descriptor for e in manager._entries.values())
            except Exception:
                inventory_complete = False
                diagnostics.append("ML-CLOSURE-INVENTORY-UNRESOLVED")
            prepared = None
            for slot, client in clients:
                if slot in invalid_adapters:
                    continue
                if type(client) is PersistenceClient:
                    prepared = client.prepared
                    break
                if type(client) is CatalogLauncher:
                    prepared = client.owner._prepared
            rank = (
                {unit: i for i, unit in enumerate(reversed(prepared.resource_order))}
                if prepared is not None
                else {}
            )
            unit_keys = {
                unit.key for _, (role, helper, unit) in issued if role in (1, 2)
            }
            descriptors = tuple(
                sorted(
                    descriptors,
                    key=lambda d: (
                        (0, rank[d.unit_id])
                        if d.unit_id in rank
                        else ((1 if d.key in unit_keys else 2), d.unit_id, d.generation)
                    ),
                )
            )
            # Close actual shared native starts before any fallback C1 release.
            fenced_slots = set()
            fence_end = min(end-terminal_budget-2*drain_budget-boundary_budget,
                            time.monotonic()+drain_budget)
            for slot, (role, helper, unit) in issued:
                if role != 4:
                    continue
                connection = root._clients.get(slot)
                try:
                    if slot in invalid_adapters or type(connection) is not AuthorityConnection:
                        raise ClosureError("ML-CLOSURE-ADAPTER-UNRESOLVED")
                    if self._fence(connection, fence_end):
                        fenced_slots.add(slot)
                    else:
                        raise ClosureError("ML-CLOSURE-AUTHORITY-UNRESOLVED")
                except (ValueError, OSError):
                    child = root._children.get(slot)
                    if child is not None:
                        try:
                            child._holder()
                            signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL)
                            while time.monotonic() < fence_end:
                                if child._wait(child._capability.fileno(), consume=True) is not None:
                                    fenced_slots.add(slot)
                                    break
                                select.select([child._capability.fileno()], [], [], 0.005)
                        except (ValueError, OSError):
                            pass
            for slot, client in clients:
                if slot in invalid_adapters:
                    continue
                if type(client) is PersistenceClient:
                    if client._terminal_outcome is not None:
                        original, _, outcome, _ = client._terminal_outcome
                        if (type(original) is not RunBroker or original.storage is not client
                            or original.session is not root or self._broker is not None and original is not self._broker):
                            diagnostics.append('ML-CLOSURE-WRITER-UNRESOLVED')
                            continue
                        # _holder validated the original pinned outcome above.
                        # Retain its ACK/unknown facts without an abort-only replay.
                        terminal_reports.append(outcome)
                        facts = outcome.public_data()
                        if (facts['diagnostic'] is not None or facts['writer'] is None
                            or facts['report'] is None or not facts['report']['eligible']
                            or not facts['writer']['evidence_complete']):
                            diagnostics.append('ML-CLOSURE-REPORT-INCOMPLETE')
                        continue
                    until = min(
                        end - 2 * drain_budget - boundary_budget,
                        time.monotonic() + terminal_budget,
                    )
                    try:
                        writers.append(
                            client.close_incomplete(HostDeadline(root.session, until))
                        )
                    except Exception:
                        diagnostics.append("ML-CLOSURE-WRITER-UNRESOLVED")
            for slot, (role, helper, unit) in issued:
                if role == 3 and (
                    slot not in root._clients or slot in invalid_adapters
                ):
                    writers.append(unresolved("unknown"))
            graceful_end = min(
                end - drain_budget - boundary_budget, time.monotonic() + drain_budget
            )
            launcher_facts = {}
            for slot, client in clients:
                if slot in invalid_adapters:
                    continue
                try:
                    if type(client) is CatalogLauncher:
                        client.cancel(reason)
                        launcher_facts[slot] = client.drain(
                            HostDeadline(root.session, graceful_end)
                        )
                    elif type(client) is PersistenceClient:
                        if not (client._failed or client._aborted):
                            client._fail()
                        client.drain(HostDeadline(root.session, graceful_end))
                    elif type(client) is AuthorityConnection:
                        client.revoke(HostDeadline(root.session, graceful_end))
                    elif type(client) is ControllerSession:
                        # Root owns the original helper wait; no live broker channel
                        # is required after the original writer has been closed.
                        pass
                    else:
                        client.cancel(reason)
                except Exception:
                    diagnostics.append("ML-CLOSURE-HELPER-UNRESOLVED")
            root.cancel(reason)
            root_result = None
            try:
                root_result = root.drain(
                    HostDeadline(
                        root.session,
                        min(end - boundary_budget, time.monotonic() + drain_budget),
                    )
                )
            except Exception:
                diagnostics.append("ML-CLOSURE-ROOT-UNRESOLVED")
            helpers = []
            for slot, (role, helper, unit) in issued:
                child = root._children.get(slot)
                reaped, code = False, None
                if child is not None:
                    try:
                        child._holder()
                        reaped = child._result is not None
                        code = child.returncode if reaped else None
                    except Exception:
                        diagnostics.append("ML-CLOSURE-IDENTITY-UNRESOLVED")
                direct = None
                if role == 1:
                    known = bool(
                        units
                        and any(
                            u.unit_id == unit.unit_id and u.leader_reaped
                            for u in units.units
                        )
                    )
                    direct = (
                        known
                        or bool(slot in launcher_facts and launcher_facts[slot].direct_child_reaped)
                        or (reaped and code == 0)
                    )
                elif role == 4:
                    if reaped:
                        fenced_slots.add(slot)
                    direct = bool(native_units) and all(
                        u.issued is False or u.direct_child_reaped is True for u in native_units)
                helpers.append(
                    HelperClosure(
                        slot,
                        role,
                        helper.unit_id,
                        reaped,
                        code,
                        direct,
                        slot in root._clients,
                    )
                )
            boundaries = []
            authority_slots = {slot for slot, (role, _, _) in issued if role == 4}
            authority_fenced = (authority_slots <= fenced_slots) if authority_slots else None
            if root_result and root_result.final_workload_freeze_acknowledged:
                authority_fenced = True if authority_slots else None
            if authority_slots and not authority_fenced:
                diagnostics.append("ML-CLOSURE-AUTHORITY-UNRESOLVED")
            if authority_slots and (not native_units or any(
                u.issued is None or u.issued is True and u.direct_child_reaped is not True
                for u in native_units)):
                diagnostics.append("ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN")
            boundary_end = min(end, time.monotonic() + boundary_budget)
            for descriptor in descriptors:
                record = None
                try:
                    record = manager._entry(descriptor).terminal
                    if record is None:
                        if authority_slots and not authority_fenced:
                            raise ClosureError("ML-CLOSURE-AUTHORITY-UNRESOLVED")
                        record = manager.force_cleanup(
                            descriptor,
                            deadline=HostDeadline(root.session, boundary_end),
                        )
                except Exception:
                    pass
                boundaries.append(
                    IssuedBoundaryClosure(
                        descriptor.unit_id,
                        descriptor.generation,
                        bool(
                            record
                            and record.membership_complete
                            and record.residual_count == 0
                        ),
                        bool(record and record.boundary_released),
                        record.diagnostic
                        if record
                        else "ML-CLOSURE-BOUNDARY-UNRESOLVED",
                    )
                )
            if any(slot not in root._issued for slot in root._children):
                inventory_complete = False
            if any(slot not in root._issued for slot in root._pending):
                inventory_complete = False
            pending = len(root._pending)
            self._result = RunClosureResult(
                root.config.admission.run_id,
                root.config.admission.lifecycle_digest,
                self.dispatcher._result.execution_succeeded
                if self.dispatcher and self.dispatcher._result
                else None,
                bool(units and units.normal_records_complete),
                tuple(helpers),
                tuple(boundaries),
                tuple(writers),
                bool(root_result and root_result.supervisor_reaped),
                bool(root_result and root_result.final_workload_freeze_acknowledged),
                pending,
                inventory_complete,
                tuple(sorted(set(diagnostics))),
                native_units=tuple(native_units),
                authority_fenced=authority_fenced,
                terminal_reports=tuple(terminal_reports),
            )
            return self._result
        finally:
            if reserved is not None:
                reserved._dispatch_owner = reserved._dispatch_thread = None
            for lock in reversed(locks):
                lock.release()
