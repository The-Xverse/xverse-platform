"""Scheduling policy checks; owned fake clocks/leases give no runtime authority."""
from types import SimpleNamespace
import pytest
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.time import HostDeadline


@pytest.mark.parametrize('health_end,lease_end,expected', [
    (102.6, 101.3, ['heartbeat', 'renew', 'health']),
    (102.6, 104.8, ['health']),
    (None, 101.3, ['heartbeat', 'renew']),
])
def test_due_services_keep_original_scan_budget_and_earliest_deadlines(monkeypatch, health_end, lease_end, expected):
    monkeypatch.setattr('xverse.maestro.dispatcher.time.monotonic', lambda: 100.0)
    actions=[]
    session='owned-service-order'
    gate=SimpleNamespace(lease_ns=int(lease_end*1e9))
    bootstrap=SimpleNamespace(_lease=int(lease_end*1e9), _generation=int(200*1e9))
    facade=SimpleNamespace(next_health_deadline=HostDeadline(session,health_end) if health_end else None)
    def scan(end, *, force):
        assert force and end.session==session
        # The entire admitted scan must fit before either original deadline.
        assert end.monotonic_seconds-100.0>=1.2
        assert end.monotonic_seconds<=health_end
        assert end.monotonic_seconds<=bootstrap._lease/1e9-1.2
        actions.append('health')
        facade.next_health_deadline=HostDeadline(session,105.0)
    facade.check_health=scan
    def heartbeat(unit,phase,end):
        assert unit is None and phase=='heartbeat'
        assert 100<end.monotonic_seconds<=100.3
        assert end.monotonic_seconds<lease_end
        actions.append('heartbeat')
    def renew(target,end):
        assert 100<end.monotonic_seconds<=100.3
        assert target.monotonic_seconds==105.0
        if health_end is not None:
            assert end.monotonic_seconds<=health_end-1.2
        actions.append('renew')
        bootstrap._lease=gate.lease_ns=int(target.monotonic_seconds*1e9)
    driver=SimpleNamespace(owner=SimpleNamespace(latch=SimpleNamespace(cancelled=False),session=session),
        bootstrap=bootstrap,facade=facade,gates={'unit':gate},teardown=SimpleNamespace(_stopped=set()),
        plan=SimpleNamespace(operation_seconds=.3,health_scan_seconds=1.2,health_slots=10),
        _active_end=120.0,_work_end=125.0,_service_calls=4,_native=True,
        _controller=SimpleNamespace(request=heartbeat),_broker=SimpleNamespace(renew=renew),
        health_scans=0,lease_renewals=0)
    driver._renew_service=lambda limit:FiniteDispatcher._renew_service(driver,limit)
    FiniteDispatcher._service(driver)
    assert actions==expected
    assert driver.health_scans==int('health' in expected)
    assert driver.lease_renewals==2*int('renew' in expected)
