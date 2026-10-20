"""Original M3/Argus-to-AFFA broker; full controller/restart admission is pending."""

from dataclasses import dataclass, field, asdict, replace
import hashlib
import os
from pathlib import Path
import select
import threading
import time

from xverse_xdl.lifecycle import OwnedResourceHandle
from .affa_client import AuthorityConnection
from .affa_protocol import (
    AuthorityConfig,
    AuthorityFrame,
    AuthorityKind as K,
    AuthorityRecipe,
    AuthorityUnit,
)
from .bootstrap import BootstrapSession, BootstrapChild, _sealed, seal_helper_image
from .launcher import ProcessObservation
from .owner import (
    _Original,
    _hash,
    _pin,
    _deadline,
    ReleaseOwner,
    StageSupervisor,
    ReleaseObservation,
    OwnerError,
    _Claim,
)
from .persistence import PersistenceClient
from .prbc import BoundaryDescriptor
from .time import HostDeadline

_CREATE = object()


@dataclass(frozen=True, slots=True)
class UnitAdmission:
    descriptor: BoundaryDescriptor
    environment: tuple[tuple[str, str], ...] = field(repr=False)
    maximum_generation: int

    def __post_init__(self):
        if (
            type(self.descriptor) is not BoundaryDescriptor
            or type(self.environment) is not tuple
        ):
            raise OwnerError("ML-RUN-UNIT-ADMISSION")
        if (
            type(self.maximum_generation) is not int
            or not self.descriptor.generation
            <= self.maximum_generation
            <= self.descriptor.generation + 127
        ):
            raise OwnerError("ML-RUN-GENERATION-BUDGET")
        if any(
            type(v) is not tuple or len(v) != 2 or any(type(s) is not str for s in v)
            for v in self.environment
        ):
            raise OwnerError("ML-RUN-ENVIRONMENT")
        if len(dict(self.environment)) != len(self.environment):
            raise OwnerError("ML-RUN-ENVIRONMENT")


@dataclass(frozen=True, slots=True)
class _Image:
    admission: UnitAdmission
    descriptor_fd: int = field(repr=False)
    image_fd: int = field(repr=False)
    cwd_fd: int = field(repr=False)
    recipe_fd: int = field(repr=False)
    native: AuthorityUnit = field(repr=False)
    action: bytes = field(repr=False)
    c1: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class RunRecipe:
    unit_id: str
    descriptor: BoundaryDescriptor
    execution_id: str
    action_id: str
    generation_ns: int
    operation_deadline_ns: int
    scope: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class RunCancellation:
    native_epoch_confirmed: bool
    epoch: int | None
    frozen_units: int
    issuer_dead: bool
    issuer_reaped: bool
    diagnostic: str | None
    cleanup_complete: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class RunRenewal:
    bootstrap_lease_ns: int
    authority_lease_ns: int
    epoch: int
    ready_for_execution: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class NativeGenerationClosure:
    unit_id: str
    generation: int
    issued: bool | None
    direct_child_reaped: bool | None
    native_retired: bool | None


@dataclass(frozen=True)
class _GenerationStatement:
    issuer: object
    controller: object
    descriptor: BoundaryDescriptor
    prior: object
    cleanup: object
    deadline_ns: int

    def __reduce_ex__(self, protocol):
        raise TypeError("original active generation statement cannot be copied")


class PreparedGeneration(_Original):
    def __init__(self, key, broker, statement, receipt):
        if key is not _CREATE:
            raise OwnerError("ML-GENERATION-ORIGINAL")
        self._retain()
        self.broker, self.statement, self.receipt = broker, statement, receipt
        self._pins = broker, statement, receipt

    def _holder(self):
        super()._holder()
        broker, statement, receipt = self._pins
        broker._holder()
        if (
            self.broker is not broker
            or self.statement is not statement
            or self.receipt is not receipt
            or broker._pending_generations.get(statement.descriptor.key) is not self
        ):
            raise OwnerError("ML-GENERATION-ORIGINAL")

    @property
    def ready_for_execution(self):
        return False


def _admit_image(session, storage, setup):
    """Explicit original admission I/O; never a bounded Stage/Release lookup."""
    setup.__post_init__()
    descriptor = setup.descriptor
    unit = next(
        (u for u in storage.prepared.units if u.unit_id == descriptor.unit_id), None
    )
    if (
        unit is None
        or descriptor.run_id != storage.run_id
        or descriptor.generation != 1
        or unit.provider.kind != "process"
        or unit.provider.artifact_digest
        != session.config.admission.authority_image.digest
        or unit.plan.process_action is None
    ):
        raise OwnerError("ML-RUN-CATALOG-ADMISSION")
    action = unit.plan.process_action
    action.__post_init__()
    environment = dict(setup.environment)
    if set(environment) != set(action.environment_names):
        raise OwnerError("ML-RUN-ENVIRONMENT")
    deployment = next(
        (
            r
            for r in storage._resources
            if r.identity.uri == unit.plan.selection["deployment"]
        ),
        None,
    )
    binding = (
        next(
            (b for b in deployment.content["bindings"] if b["id"] == unit.binding_id),
            None,
        )
        if deployment
        else None
    )
    candidates = (
        [
            a
            for a in deployment.content.get("artifacts", ())
            if binding is not None
            and a["id"] in binding["artifactIds"]
            and a["sourceRef"] == Path(action.executable).as_uri()
            and a.get("digest") in unit.plan.artifact_digests
        ]
        if deployment
        else []
    )
    if len(candidates) != 1:
        raise OwnerError("ML-RUN-CATALOG-ARTIFACT")
    manager = session.boundaries
    entry = manager._entry(descriptor)
    manager._authority(entry)
    manager._verify(entry)
    if (
        manager.residual_membership(descriptor)
        or manager.record(descriptor).state != "frozen"
    ):
        raise OwnerError("ML-RUN-C1-NOT-EMPTY")
    image = cwd = recipe_fd = None
    try:
        image = seal_helper_image(
            action.executable, digest=candidates[0]["digest"], argv0=action.executable
        )
        cwd = os.open(
            action.working_directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
        )
        recipe = AuthorityRecipe(
            (action.executable, *action.arguments),
            tuple(k + "=" + environment[k] for k in sorted(environment)),
        ).encode()
        recipe_fd = _sealed(recipe, "maestro-original-run-recipe")
        info, work = os.fstat(entry.fd), os.fstat(cwd)
        native = AuthorityUnit(
            _hash(
                [
                    "AF17-binding",
                    storage.prepared.lifecycle_digest,
                    unit.unit_id,
                    unit.binding_id,
                ]
            ),
            _pin(candidates[0]["digest"]),
            hashlib.sha256(recipe).digest(),
            info.st_dev,
            info.st_ino,
            work.st_dev,
            work.st_ino,
            descriptor.generation,
            setup.maximum_generation,
        )
        action_pin = _hash(
            [
                "AF17-action",
                storage.prepared.lifecycle_digest,
                unit.unit_id,
                unit.plan.digest,
                asdict(action),
                native.image.hex(),
                native.recipe.hex(),
            ]
        )
        c1 = _hash(
            [
                "AF17-C1",
                session.config.scope.hex(),
                list(descriptor.key),
                info.st_dev,
                info.st_ino,
                manager._admission.bootstrap_approval_ref,
                manager._admission.cleanup_approval_ref,
            ]
        )
        return _Image(
            setup, entry.fd, image.descriptor, cwd, recipe_fd, native, action_pin, c1
        )
    except Exception:
        for fd in (image.descriptor if image else None, cwd, recipe_fd):
            if fd is not None:
                os.close(fd)
        raise


class RunBroker(_Original):
    @classmethod
    def admit(cls, session, storage, units, helper, *, deadline, controller_sessions=0):
        if (
            cls is not RunBroker
            or type(session) is not BootstrapSession
            or type(storage) is not PersistenceClient
            or type(units) is not tuple
            or any(type(u) is not UnitAdmission for u in units)
            or type(controller_sessions) is not int
            or not 0 <= controller_sessions <= 16
        ):
            raise OwnerError("ML-RUN-ADMISSION")
        session._live()
        storage._available()
        if (
            session.config.version != 2
            or type(storage.process) is not BootstrapChild
            or storage.process._root is not session
            or session._clients.get(storage.process._slot) is not storage
            or storage.latch is not session.latch
            or storage.run_id != session.config.admission.run_id
            or storage.prepared.lifecycle_digest
            != session.config.admission.lifecycle_digest
            or storage.generation_ns != session._generation
            or storage.session != session.session
            or len(units) != len(storage.prepared.units)
            or {u.descriptor.unit_id for u in units}
            != {u.unit_id for u in storage.prepared.units}
        ):
            raise OwnerError("ML-RUN-ORIGINAL-STORAGE")
        by_unit = {u.descriptor.unit_id: u for u in units}
        if storage.schedule is not None:
            plan = storage.schedule
            extra = (2*len(units) + len(storage._public_exports)
                     + (plan.health_slots if plan.service_operation_count is None else 0))
            if (plan.required_requests+extra > storage._request_limit
                or plan.required_events+len(units)>plan.event_limit):
                raise OwnerError("ML-RUN-EVIDENCE-CAPACITY")
        if controller_sessions and (
            sum(u.maximum_generation - u.descriptor.generation + 1 for u in units)
            + 2 + controller_sessions > session.boundaries._limits.max_boundaries
        ):
            raise OwnerError("ML-RUN-CONTROLLER-CAPACITY")
        images, connection = [], None
        try:
            for unit in storage.prepared.units:
                images.append(_admit_image(session, storage, by_unit[unit.unit_id]))
            for image in images:
                session.watch(image.admission.descriptor, deadline)
            config = AuthorityConfig(
                session._generation,
                session._lease,
                session.boundaries.release_epoch,
                session.authority_scope,
                session.authority_supervisor,
                tuple(i.native for i in images),
            )
            connection = session.authority(config, helper, deadline)
            owner = ReleaseOwner.from_persistence(
                storage,
                StageSupervisor(session.boundaries, session.latch),
                session.latch,
            )
            value = cls.__new__(cls)
            value._retain()
            value.session, value.storage, value.connection, value.owner = (
                session,
                storage,
                connection,
                owner,
            )
            value._pins = session, storage, connection, owner, tuple(images)
            value._disposal = value._disposal_pin = (
                value._pins,
                threading.Lock(),
                [fd for image in images
                 for fd in (image.image_fd, image.cwd_fd, image.recipe_fd)],
                [],
            )
            value._lock = threading.Lock()
            value._cancel_result = None
            value._issuers = {}
            value._issuer_registry = value._issuers
            value._issuer_log = ()
            value._generation_issuers = {}
            value._generation_issuer_registry = value._generation_issuers
            value._generation_issuer_log = ()
            value._active_generation = None
            value._pending_generations = {}
            value._pending_generation_registry = value._pending_generations
            value._controller_budget = value._controller_budget_pin = controller_sessions
            value._controllers = value._controller_log = ()
            value._current_controller = None
            owner._run_broker = owner._run_broker_pin = value
            for slot, image in enumerate(images, 1):
                issuer = RunUnitIssuer(_CREATE, value, slot, image)
                value._issuers[issuer.unit_id] = issuer
                value._generation_issuers[
                    issuer.unit_id, image.admission.descriptor.generation
                ] = issuer
                value._generation_issuer_log = tuple(value._generation_issuers.items())
                value._issuer_log = tuple(value._issuers.items())
                owner._register_launcher(issuer)
            for slot, image in enumerate(images, 1):
                frame = AuthorityFrame(
                    K.REGISTER,
                    connection.sequence + 1,
                    value._until(deadline),
                    config.scope,
                    slot,
                    connection.epoch,
                    image.admission.descriptor.generation,
                    first=image.native.binding,
                    second=image.native.image,
                    third=image.native.recipe,
                    fourth=image.c1,
                )
                connection._exchange(
                    frame,
                    fds=(
                        image.descriptor_fd,
                        image.image_fd,
                        image.cwd_fd,
                        image.recipe_fd,
                    ),
                )
            return value
        except Exception:
            if connection:
                connection.revoke(
                    HostDeadline(
                        session.session,
                        min(time.monotonic() + 1, session._generation / 1e9),
                    )
                )
            for image in images:
                for fd in (image.image_fd, image.cwd_fd, image.recipe_fd):
                    os.close(fd)
            raise

    def _cleanup_context(self):
        """Original fencing context, without ordinary issuer/adoption rights."""
        super()._holder()
        session, storage, connection, owner, images = self._pins
        if (
            self.session is not session
            or self.storage is not storage
            or self.connection is not connection
            or self.owner is not owner
            or owner._run_broker is not self
            or owner._run_broker_pin is not self
        ):
            raise OwnerError("ML-RUN-REPLACED")
        session._holder()
        storage._holder()
        connection._holder()
        owner._holder()

    def _holder(self):
        self._cleanup_context()
        if (
            self._issuers is not self._issuer_registry
            or self._generation_issuers is not self._generation_issuer_registry
            or tuple(self._generation_issuers.items()) != self._generation_issuer_log
            or tuple(self._issuers.items()) != self._issuer_log
            or self._pending_generations is not self._pending_generation_registry
            or self._controller_budget != self._controller_budget_pin
            or self._controllers is not self._controller_log
            or self._current_controller is not (
                self._controllers[-1] if self._controllers else None
            )
        ):
            raise OwnerError("ML-RUN-REPLACED")

    def _until(self, deadline, *, claim=None, cleanup=False):
        until = _deadline(deadline, self.session.session)
        if (
            until > self.connection._lease
            and not (cleanup and self.connection._starts_closed)
            or until > self.session._generation - 2_000_000_000
            or claim
            and until > claim.deadline_ns
        ):
            raise OwnerError("ML-RUN-ORIGINAL-END")
        return until

    def admit_controller(self, session_id, deadline):
        from .controller import admit_controller

        return admit_controller(self, session_id, deadline)

    def public_projection(self, deadline):
        from .evidence import broker_projection
        self._holder()
        until = _deadline(deadline, self.owner.session)
        if until > self.session._generation:
            raise OwnerError('ML-EVIDENCE-BROKER-DEADLINE')
        if not self._lock.acquire(False):
            raise OwnerError('ML-RUN-CONFLICT')
        try:
            return broker_projection(self, until)
        finally:
            self._lock.release()

    @property
    def issuers(self):
        self._holder()
        return tuple(self.issuer(unit.unit_id) for unit in self.owner._prepared.units)

    def issuer(self, unit_id):
        self._holder()
        choices = [
            (g, issuer)
            for (unit, g), issuer in self._generation_issuers.items()
            if unit == unit_id
        ]
        if not choices:
            raise OwnerError("ML-RUN-UNIT")
        current = max(choices, key=lambda pair: pair[0])[1]
        if self.owner._launchers.get(unit_id) is not current:
            raise OwnerError("ML-RUN-CURRENT-ISSUER")
        return current

    def release(self, unit_id, descriptor, gate, deadline, *, readiness_guard=None):
        self._holder()
        self.owner._start_access()
        self.owner._check(deadline)
        from .providers import DependencyGuard
        from .lifecycle_evidence import _parents

        if (
            readiness_guard is not None
            and type(readiness_guard) is not DependencyGuard
            or _parents(self.owner._prepared, unit_id)
            and readiness_guard is None
        ):
            raise OwnerError("ML-RUN-DEPENDENCY-GUARD")
        if gate is not self.connection or type(gate) is not AuthorityConnection:
            raise OwnerError("ML-RUN-ORIGINAL-AUTHORITY")
        if not self._lock.acquire(False):
            raise OwnerError("ML-RUN-CONFLICT")
        try:
            issuer = self.issuer(unit_id)
            if issuer.recipe.descriptor != descriptor:
                raise OwnerError("ML-RUN-ORIGINAL-C1")
            issuer._issued(issuer._handle)
            claim = self.owner._claims[unit_id]
            if claim.attempted:
                raise OwnerError("ML-RUN-RELEASE-REPLAY")
            self._until(deadline, claim=claim)
            claim.attempted = True
            self.storage.revalidate_intent(claim.receipt, deadline, issuance=issuer._issuance_proof[1])
            issuer._boundary()
            ticket = issuer._native(K.ARM, deadline)
            self.owner._check(deadline)
            self.storage.revalidate_intent(claim.receipt, deadline, issuance=issuer._issuance_proof[1])
            issuer._boundary()
            if readiness_guard is not None:
                readiness_guard.check(self.owner, unit_id, deadline)
            issuer._release_bracket = issuer._release_bracket_pin = (time.monotonic(), None)
            released = issuer._native(
                K.RELEASE,
                deadline,
                ticket=ticket.ticket,
                original_end=ticket.deadline_ns,
            )
            issuer._release_ack = issuer._release_ack_pin = released
            issuer._release_bracket = issuer._release_bracket_pin = (
                issuer._release_bracket[0], time.monotonic())
            self.owner._check(deadline)
            return ReleaseObservation(
                unit_id, descriptor.generation, True, claim.event_id
            )
        except Exception:
            self.owner._closed = True
            self.cancel("run-release-uncertain")
            raise
        finally:
            self._lock.release()

    def _prepare_generation(self, controller, unit_id, descriptor, deadline):
        """Original successor intent only; native ADVANCE/Stage still required."""
        from .teardown import ReverseTeardown
        from .lifecycle_evidence import _parents

        self._holder()
        self.owner._start_access()
        if (
            type(controller) is not ReverseTeardown
            or controller.owner is not self.owner
        ):
            raise OwnerError("ML-GENERATION-CONTROLLER")
        controller._holder()
        until = self._until(deadline)
        locks = []
        mutated = False
        try:
            for lock in (
                controller._lock,
                controller.facade._lock,
                self.owner._lock,
                self._lock,
            ):
                if not lock.acquire(False):
                    raise OwnerError("ML-GENERATION-CONFLICT")
                locks.append(lock)
            issuer = self.issuer(unit_id)
            issuer.revalidate_issued(issuer._handle)
            old = issuer.recipe.descriptor
            if (
                type(descriptor) is not BoundaryDescriptor
                or descriptor.run_id != old.run_id
                or descriptor.unit_id != unit_id
                or descriptor.generation != old.generation + 1
                or descriptor.generation > issuer._image.admission.maximum_generation
                or descriptor.key in self._pending_generations
            ):
                raise OwnerError("ML-GENERATION-DESCRIPTOR")
            if not any(
                c.binding.unit_id == unit_id
                and c.binding.generation == descriptor.generation
                for c in self.storage._future_contexts
            ):
                raise OwnerError("ML-GENERATION-NOT-ADMITTED")
            cleaned = controller._cleaned.get(unit_id)
            cleanup = self.storage._teardown_receipts.get(unit_id)
            if (
                cleaned is None
                or cleaned.generation != old.generation
                or not cleaned.unit_cleanup_complete
                or not cleaned.normal_records_complete
                or issuer._stop_ack is None
                or not issuer._stop_ack.state & 8
                or issuer._retire_ack is None
                or not issuer._retire_ack.state & 128
                or cleanup is None
                or cleanup.phase != "cleanup"
                or cleanup.stage != "outcome"
                or not any(cleanup is r for r in controller._receipts.values())
                or not self.session.boundaries.record(
                    old, deadline=deadline
                ).boundary_released
            ):
                raise OwnerError("ML-GENERATION-PRIOR-RELEASE")
            self._check_dependents_released(controller, unit_id, deadline)
            manager = self.session.boundaries
            entry = manager._entry(descriptor)
            manager._authority(entry)
            manager._verify(entry)
            if (
                manager.residual_membership(descriptor)
                or manager.record(descriptor, deadline=deadline).state != "frozen"
            ):
                raise OwnerError("ML-GENERATION-FROZEN")
            self.connection.child._ordinary()
            mutated = True
            self.session.watch(descriptor, deadline)
            statement = _GenerationStatement(
                issuer,
                controller,
                descriptor,
                self.owner._claims[unit_id].receipt,
                cleanup,
                until,
            )
            self._active_generation = statement
            receipt = self.storage.prepare_generation(self, statement, deadline)
            prepared = PreparedGeneration(_CREATE, self, statement, receipt)
            self._pending_generations[descriptor.key] = prepared
            return prepared
        except Exception:
            if mutated:
                self.cancel("generation-intent-uncertain", deadline=deadline)
            raise
        finally:
            self._active_generation = None
            for lock in reversed(locks):
                lock.release()

    def _check_dependents_released(self, controller, unit_id, deadline):
        from .lifecycle_evidence import _parents

        if any(
            unit_id in _parents(self.owner._prepared, other)
            and not controller._released_current(other, deadline)
            for other in self.owner._claims
            if other != unit_id
        ):
            raise OwnerError("ML-GENERATION-DEPENDENTS")

    def advance_generation(self, prepared, deadline):
        """Actual original native ADVANCE; replacement still requires Stage/probes."""
        if type(prepared) is not PreparedGeneration or prepared.broker is not self:
            raise OwnerError("ML-GENERATION-ORIGINAL")
        prepared._holder()
        statement = prepared.statement
        descriptor = statement.descriptor
        origin = statement.issuer
        until = self._until(deadline)
        if until > prepared.receipt.deadline_ns or until > statement.deadline_ns:
            raise OwnerError("ML-GENERATION-ORIGINAL-END")
        existing = self._generation_issuers.get(
            (descriptor.unit_id, descriptor.generation)
        )
        if existing is not None:
            if existing._generation_origin is not prepared:
                raise OwnerError("ML-GENERATION-ORIGINAL")
            return existing
        locks = []
        mutated = False
        try:
            for lock in (
                statement.controller._lock,
                statement.controller.facade._lock,
                self.owner._lock,
                self._lock,
            ):
                if not lock.acquire(False):
                    raise OwnerError("ML-GENERATION-CONFLICT")
                locks.append(lock)
            # Preparation already consumed the fresh permit. Any failure after
            # entering this transition must close the original native authority,
            # including loss of storage before ADVANCE reaches the wire.
            mutated = True
            self.owner._check(deadline)
            if self.issuer(descriptor.unit_id) is not origin:
                raise OwnerError("ML-GENERATION-ORIGINAL")
            self._check_dependents_released(
                statement.controller, descriptor.unit_id, deadline
            )
            self.storage.revalidate_intent(prepared.receipt, deadline)
            manager = self.session.boundaries
            entry = manager._entry(descriptor)
            manager._authority(entry)
            manager._verify(entry)
            if (
                manager.residual_membership(descriptor)
                or manager.record(descriptor, deadline=deadline).state != "frozen"
            ):
                raise OwnerError("ML-GENERATION-FROZEN")
            info = os.fstat(entry.fd)
            c1 = _hash(
                [
                    "AF17-C1",
                    self.session.config.scope.hex(),
                    list(descriptor.key),
                    info.st_dev,
                    info.st_ino,
                    manager._admission.bootstrap_approval_ref,
                    manager._admission.cleanup_approval_ref,
                ]
            )
            image = replace(
                origin._image,
                admission=replace(origin._image.admission, descriptor=descriptor),
                descriptor_fd=entry.fd,
                native=replace(
                    origin._image.native,
                    boundary_device=info.st_dev,
                    boundary_inode=info.st_ino,
                    generation=descriptor.generation,
                ),
                c1=c1,
            )
            frame = AuthorityFrame(
                K.ADVANCE,
                self.connection.sequence + 1,
                until,
                self.connection.config.scope,
                origin.slot,
                self.connection.epoch,
                descriptor.generation,
                bytes.fromhex(prepared.receipt.operation[3:]),
                image.action,
                prepared.receipt.intent_digest,
                prepared.receipt.flush_digest,
                c1,
                ticket=self.connection.watch_token(entry.fd),  # F-02: supervisor WATCH token
            )
            self.connection._exchange(frame, fds=(entry.fd,))
            advance = self.connection._advance_receipts[-1]
            connection, request, _, actual_descriptor = advance._holder()
            if (
                connection is not self.connection
                or request is not frame
                or actual_descriptor != descriptor
            ):
                raise OwnerError("ML-GENERATION-NATIVE-ACK")
            self.owner._check(deadline)
            fresh = RunUnitIssuer(
                _CREATE,
                self,
                origin.slot,
                image,
                generation_origin=prepared,
                advance_receipt=advance,
            )
            receipt = prepared.receipt
            self.owner._claims[descriptor.unit_id] = _Claim(
                receipt,
                receipt.operation,
                receipt.intent_digest,
                receipt.flush_digest,
                receipt.event_id,
                receipt.deadline_ns,
            )
            self.owner._launchers[descriptor.unit_id] = fresh
            self._generation_issuers[descriptor.unit_id, descriptor.generation] = fresh
            self._generation_issuer_log = tuple(self._generation_issuers.items())
            facade = statement.controller.facade
            facade._bindings.pop(descriptor.unit_id, None)
            facade._observations.pop(descriptor.unit_id, None)
            facade._released.discard(descriptor.unit_id)
            facade._attempted.discard(descriptor.unit_id)
            return fresh
        except Exception:
            if mutated:
                self.cancel("generation-advance-uncertain", deadline=deadline)
            raise
        finally:
            for lock in reversed(locks):
                lock.release()

    def renew(self, lease, deadline):
        """Renew the same original bootstrap and shared native authority leases."""
        self._holder()
        self.owner._check(deadline)
        until = self._until(deadline)
        target = _deadline(lease, self.session.session)
        if (
            until > self.session._lease
            or target <= max(self.session._lease, self.connection._lease)
            or target > min(
                self.session._generation, self.connection.config.generation_ns
            ) - 2_000_000_000
        ):
            raise OwnerError("ML-RUN-RENEW-END")
        locks = []
        entered = False
        try:
            for lock in (self.owner._lock, self._lock):
                if not lock.acquire(False):
                    raise OwnerError("ML-RUN-CONFLICT")
                locks.append(lock)
            entered = True
            self.owner._check(deadline)
            self.storage.revalidate_run(self, deadline)
            self.session.renew(lease, deadline)
            reply = self.connection._exchange(
                AuthorityFrame(
                    K.RENEW,
                    self.connection.sequence + 1,
                    until,
                    self.connection.config.scope,
                    epoch=self.connection.epoch,
                    lease_ns=target,
                )
            )
            self.owner._check(deadline)
            return RunRenewal(self.session._lease, reply.lease_ns, reply.epoch)
        except Exception:
            if entered:
                self.cancel("run-renew-uncertain", deadline=deadline)
            raise
        finally:
            for lock in reversed(locks):
                lock.release()

    def service_terminal(self, deadline):
        """Keep only the original fenced bootstrap/writer alive for terminal work."""
        self._holder()
        if self._cancel_result is None or not self.owner.latch.cancelled or not self.owner._closed:
            raise OwnerError("ML-RUN-TERMINAL-STATE")
        # A still productive issuer could thaw after a root freeze. Require the
        # original connection's pinned native cancellation receipt or its actual
        # consumed original-parent wait, never just a local cancellation flag.
        confirmed = any(reply.kind is K.CANCELLED for reply in self.connection._epoch_history)
        child = self.connection.child
        reaped = child._result is not None and bool(select.select(
            [child._capability.fileno()], [], [], 0)[0])
        if not confirmed and not reaped:
            raise OwnerError("ML-RUN-TERMINAL-FENCE")
        if not self._lock.acquire(False):
            raise OwnerError("ML-RUN-CONFLICT")
        try:
            return self.session._service_terminal(deadline, authority=self.connection)
        finally:
            self._lock.release()

    def cancel(self, reason="run-cancel", *, deadline=None):
        self._cleanup_context()
        if self._cancel_result is not None:
            return self._cancel_result
        if deadline is not None:
            if (
                type(deadline) is not HostDeadline
                or deadline.session != self.session.session
            ):
                raise OwnerError("ML-RUN-CANCEL-SESSION")
            deadline.__post_init__()
        limit = deadline.monotonic_seconds if deadline is not None else float("inf")
        self.owner._closed = True
        self.owner.latch.cancel(reason)
        end = min(time.monotonic() + 1, self.session._generation / 1e9 - 2, limit)
        try:
            request = AuthorityFrame(
                K.CANCEL,
                self.connection.sequence + 1,
                int(end * 1e9),
                self.connection.config.scope,
                epoch=self.connection.epoch,
            )
            reply = self.connection._exchange(request)
            result = RunCancellation(
                True,
                reply.epoch,
                reply.state,
                False,
                False,
                None if reply.reason == 5 else "ML-RUN-FREEZE-UNRESOLVED",
            )
        except (ValueError, OSError):
            observed = self.connection.revoke(
                HostDeadline(
                    self.session.session,
                    min(time.monotonic() + 1, self.session._generation / 1e9, limit),
                )
            )
            result = RunCancellation(
                False,
                None,
                0,
                observed.issuer_dead,
                observed.issuer_reaped,
                observed.diagnostic,
            )
        self._cancel_result = result
        return result

    def dispose(self):
        # Matching replay cannot require transports already closed by the launcher.
        super()._holder()
        if self._disposal is not self._disposal_pin or self._disposal[0] is not self._pins:
            raise OwnerError("ML-RUN-REPLACED")
        pins, lock, pending, failures = self._disposal
        if not lock.acquire(False):
            raise OwnerError("ML-RUN-DISPOSE-CONFLICT")
        try:
            if failures:
                raise OwnerError("ML-RUN-DISPOSE-UNRESOLVED") from failures[0]
            if not pending:
                return
            self._cleanup_context()
            if pins[2].child._result is None:
                raise OwnerError("ML-RUN-RETAINED")
            while pending:
                fd = pending.pop()  # consume before close, including ambiguous errors
                try:
                    os.close(fd)
                except OSError as error:
                    failures.append(error)
            if failures:
                raise OwnerError("ML-RUN-DISPOSE-UNRESOLVED") from failures[0]
        finally:
            lock.release()


class RunUnitIssuer(_Original):
    def __init__(
        self, key, broker, slot, image, *, generation_origin=None, advance_receipt=None
    ):
        if key is not _CREATE:
            raise OwnerError("ML-RUN-ISSUER")
        self._retain()
        self.broker, self.slot, self._image = broker, slot, image
        self.owner, self.unit_id = broker.owner, image.admission.descriptor.unit_id
        self.process = broker.connection.child
        self.recipe = self._handle = self._proof = None
        self._attempted = False
        self._stop_ack = self._stop_ack_pin = None
        self._stop_bracket = self._stop_bracket_pin = None
        self._retire_ack = self._retire_ack_pin = None
        self._issued_pin = None
        self._issuance_proof = None
        self._active_issuance = None
        self._release_ack = self._release_ack_pin = None
        self._release_bracket = self._release_bracket_pin = None
        self._generation_origin = generation_origin
        self._advance_receipt = advance_receipt
        self._generation_pins = generation_origin, advance_receipt
        self._pins = broker, slot, image, self.owner, self.unit_id, self.process

    def _holder(self):
        super()._holder()
        broker, slot, image, owner, unit, process = self._pins
        broker._holder()
        self._identity()

    def _identity(self):
        broker, slot, image, owner, unit, process = self._pins
        if (
            self.broker is not broker
            or self.slot != slot
            or self._image is not image
            or self.owner is not owner
            or self.unit_id != unit
            or self.process is not process
            or self._stop_ack is not self._stop_ack_pin
            or self._stop_bracket is not self._stop_bracket_pin
            or self._retire_ack is not self._retire_ack_pin
            or self._release_ack is not self._release_ack_pin
            or self._release_bracket is not self._release_bracket_pin
            or broker._generation_issuers.get(
                (unit, image.admission.descriptor.generation)
            )
            is not self
            or (self._generation_origin, self._advance_receipt) != self._generation_pins
            or max(g for (u, g) in broker._generation_issuers if u == unit)
            == image.admission.descriptor.generation
            and owner._launchers.get(unit) is not self
        ):
            raise OwnerError("ML-RUN-ISSUER-REPLACED")
        if self._issued_pin is not None and (
            self.recipe is not self._issued_pin[0]
            or self._handle is not self._issued_pin[1]
            or self._proof is not self._issued_pin[2]
        ):
            raise OwnerError("ML-RUN-ISSUED-REPLACED")

    def _closure_fact(self):
        """Original cached native facts, independent of a failed storage channel."""
        _Original._holder(self)
        broker, slot, image, owner, unit, process = self._pins
        _Original._holder(broker)
        connection = broker._pins[2]
        connection._holder()
        if (broker._generation_issuers is not broker._generation_issuer_registry
            or broker.owner is not owner or connection.child is not process
            or process._root is not broker._pins[0]):
            raise OwnerError("ML-RUN-ISSUER-REPLACED")
        self._identity()
        generation = image.admission.descriptor.generation
        if self._handle is None:
            return NativeGenerationClosure(unit, generation,
                False if self._attempted is False else None, None, None)
        if self._issued_pin is None:
            raise OwnerError("ML-RUN-ISSUED-REPLACED")
        stopped, retired = self._stop_ack, self._retire_ack
        token = bytes.fromhex(self._handle.opaque_id)
        def actual(frame, kind, flag):
            return bool(frame is not None and frame.kind is kind
                and frame.slot == slot and frame.generation == generation
                and frame.handle == token and frame.state & flag)
        return NativeGenerationClosure(unit, generation, True,
            True if actual(stopped, K.STOPPED, 8) else None,
            True if actual(retired, K.RETIRED, 128) else None)

    def _boundary(self, *, empty=False):
        self._holder()
        manager = self.broker.session.boundaries
        entry = manager._entry(self._image.admission.descriptor)
        manager._authority(entry)
        manager._verify(entry)
        if os.fstat(entry.fd).st_ino != self._image.native.boundary_inode:
            raise OwnerError("ML-RUN-C1-IDENTITY")
        if empty and manager.residual_membership(entry.descriptor):
            raise OwnerError("ML-RUN-C1-NOT-EMPTY")
        if "frozen 1" not in manager._read(entry, "cgroup.events").splitlines():
            raise OwnerError("ML-RUN-C1-NOT-FROZEN")

    def _native(
        self, kind, deadline, *, ticket=bytes(32), original_end=None, cleanup=False
    ):
        self._holder()
        if self._proof is None:
            raise OwnerError("ML-RUN-INTENT")
        until = self.broker._until(deadline, cleanup=cleanup)
        if kind in (K.ARM, K.RELEASE) and until > self.recipe.operation_deadline_ns:
            raise OwnerError("ML-RUN-ORIGINAL-END")
        if original_end is not None and until > original_end:
            raise OwnerError("ML-RUN-TICKET-END")
        request = replace(
            self._proof,
            kind=kind,
            sequence=self.broker.connection.sequence + 1,
            deadline_ns=until,
            epoch=self.broker.connection.epoch,
            handle=self._handle.opaque_id and bytes.fromhex(self._handle.opaque_id)
            if self._handle
            else bytes(32),
            ticket=ticket,
        )
        return self.broker.connection._exchange(request)

    def stage(self, deadline):
        self._holder()
        if not self.broker._lock.acquire(False):
            raise OwnerError("ML-RUN-CONFLICT")
        try:
            if self._attempted:
                raise OwnerError("ML-RUN-STAGE-REPLAY")
            self._attempted = True
            claim = self.owner._stage_claim(self.unit_id, deadline)
            until = self.broker._until(deadline, claim=claim)
            self._boundary(empty=True)
            self._proof = AuthorityFrame(
                K.INTENT,
                self.broker.connection.sequence + 1,
                until,
                self.broker.connection.config.scope,
                self.slot,
                self.broker.connection.epoch,
                self._image.admission.descriptor.generation,
                bytes.fromhex(claim.operation[3:]),
                self._image.action,
                claim.intent_digest,
                claim.flush_digest,
                self._image.c1,
            )
            if self._advance_receipt is None:
                self.broker.connection._exchange(self._proof)
            else:
                self._generation_origin._holder()
                connection, request, reply, descriptor = self._advance_receipt._holder()
                if (
                    connection is not self.broker.connection
                    or descriptor != self._image.admission.descriptor
                    or reply.epoch != connection.epoch
                    or until > request.deadline_ns
                    or request.operation != self._proof.operation
                    or request.generation != self._proof.generation
                    or (request.first, request.second, request.third, request.fourth)
                    != (
                        self._proof.first,
                        self._proof.second,
                        self._proof.third,
                        self._proof.fourth,
                    )
                ):
                    raise OwnerError("ML-GENERATION-ORIGINAL-NATIVE-INTENT")
            self.owner._check(deadline)
            self.owner._revalidate(claim, deadline)
            self._boundary(empty=True)
            reply = self._native(K.STAGE, deadline)
            if reply.state != 37:
                raise OwnerError("ML-RUN-STAGE-ACK")
            execution = self.owner.persistence._claim_execution_id(claim.receipt)
            action = next(
                a.action_id
                for a in self.owner._unit(self.unit_id).plan.actions
                if a.phase == "start"
            )
            scope = _hash(
                [
                    "AF17-resource",
                    self.broker.connection.config.scope.hex(),
                    list(self._image.admission.descriptor.key),
                    self._image.c1.hex(),
                    execution,
                    claim.operation,
                ]
            )
            self.recipe = RunRecipe(
                self.unit_id,
                self._image.admission.descriptor,
                execution,
                action,
                self.broker.session._generation,
                min(claim.deadline_ns, self._advance_receipt._pins[1].deadline_ns)
                if self._advance_receipt
                else claim.deadline_ns,
                scope,
            )
            self._handle = OwnedResourceHandle(
                reply.handle.hex(),
                execution,
                action,
                self.owner._unit(self.unit_id).provider.provider_id,
                "process",
                "maestro-boundary:" + scope.hex(),
            )
            self._issued_pin = self.recipe, self._handle, self._proof
            self._issuance_proof = reply, None
            from .issuance_evidence import IssuanceStatement

            statement = IssuanceStatement(self,claim.receipt,self._handle,reply,time.monotonic(),until)
            self._active_issuance = statement
            try:
                receipt = self.owner.persistence.record_issued(self,statement,deadline)
                self._issuance_proof = reply, receipt
            finally:
                self._active_issuance = None
            self.owner._check(deadline)
            return self._handle
        except Exception:
            self.owner._closed = True
            self.broker.cancel("run-stage-uncertain")
            raise
        finally:
            self.broker._lock.release()

    def _issued(self, handle):
        self.revalidate_issued(handle)
        key = self.unit_id,self.recipe.descriptor.generation
        if (self._issuance_proof is None or self._issuance_proof[1] is None
            or self.owner.persistence._issued_receipts.get(key) is not self._issuance_proof[1]):
            raise OwnerError("ML-ISSUED-NORMAL-RECEIPT")
        self.broker.connection.child._ordinary()
        self.owner.persistence._available()
        if self.owner._closed or self.owner.latch.cancelled:
            raise OwnerError("ML-RUN-CLOSED")
        capability = self.broker.connection._handles[
            (self.slot, self.recipe.descriptor.generation)
        ][1]
        if select.select([capability.fileno()], [], [], 0)[0]:
            raise OwnerError("ML-RUN-CHILD-EXIT")

    def revalidate_issued(self, handle):
        self._holder()
        if (
            type(handle) is not OwnedResourceHandle
            or self._handle is None
            or handle is not self._handle
        ):
            raise OwnerError("ML-RUN-ORIGINAL-HANDLE")
        if self.broker.connection._handles.get(
            (self.slot, self.recipe.descriptor.generation), (None,)
        )[0] != bytes.fromhex(handle.opaque_id):
            raise OwnerError("ML-RUN-ISSUED-HANDLE")
        return True

    def observe(self, handle, deadline):
        self._issued(handle)
        self.owner._check(deadline)
        reply = self._native(K.QUERY, deadline)
        flags = reply.state
        return ProcessObservation(
            handle,
            self.owner.session,
            time.monotonic(),
            bool(flags & 2),
            bool(flags & 4),
            bool(flags & 8),
            bool(flags & 16),
            None,
        )

    def stop_owned(self, handle, deadline):
        self.revalidate_issued(handle)
        if self._stop_ack is None:
            if self._stop_bracket is None:
                self._stop_bracket = self._stop_bracket_pin = (time.monotonic(), None)
            reply = self._native(K.STOP, deadline, cleanup=True)
            if not reply.state & 8 or reply.state & 4:
                raise OwnerError("ML-RUN-STOP-ACK")
            self._stop_ack = self._stop_ack_pin = reply
            self._stop_bracket = self._stop_bracket_pin = (
                self._stop_bracket[0], time.monotonic())
        flags = self._stop_ack.state
        return ProcessObservation(
            handle,
            self.owner.session,
            time.monotonic(),
            bool(flags & 2),
            bool(flags & 4),
            bool(flags & 8),
            bool(flags & 16),
            None,
        )

    def retire_owned(self, handle, deadline):
        self.revalidate_issued(handle)
        if self._retire_ack is None:
            reply = self._native(K.RETIRE, deadline, cleanup=True)
            if reply.state & (8 | 32 | 64 | 128) != (8 | 32 | 64 | 128):
                raise OwnerError("ML-RUN-RETIRE-ACK")
            self._retire_ack = self._retire_ack_pin = reply
        return self._retire_ack

    def cancel(self, reason="run-issuer-cancel"):
        super()._holder()
        broker, slot, image, owner, unit, process = self._pins
        if (self.broker is not broker or self.slot != slot or self._image is not image
            or self.owner is not owner or self.unit_id != unit or self.process is not process):
            raise OwnerError("ML-RUN-ISSUER-REPLACED")
        return broker.cancel(reason)
