# Applies the F-08/F-09 v2 candidate (finding 438) to src/ of the increment19 worktree.
from pathlib import Path
import sys
root = Path(sys.argv[1])
def sub(path, a, b):
    p = root / path; s = p.read_text(); assert s.count(a) == 1, (path, a); p.write_text(s.replace(a, b))
sub('src/xverse/maestro/dispatcher.py', '''    def _send(self, kind, deadline, **values):
        body = dict(values)
        if kind != "tick":
            body.update(kind=kind, observed_at=time.monotonic())
        statement = _Statement(
            "tick" if kind == "tick" else "schedule", canonical_bytes(body)
        )
        self._active = statement
        try:
            return self.client.schedule_call(self, statement, deadline)
        finally:
            self._active = None
''', '''    def _send(self, kind, deadline, **values):
        body = dict(values)
        if kind != "tick":
            body.update(kind=kind, observed_at=time.monotonic())
        statement = _Statement(
            "tick" if kind == "tick" else "schedule", canonical_bytes(body)
        )
        # F-08 (finding 438): a statement is not sent with less time left than the longest round
        # trip this run has already observed for its kind; it is refused before the send, so the
        # channel stays usable for the terminal records instead of timing out and failing.
        began = time.monotonic()
        if deadline.monotonic_seconds - began < self._service_seen.get(kind, 0.0):
            raise OwnerError("ML-SCHEDULE-SERVICE-DEADLINE")
        self._active = statement
        try:
            reply = self.client.schedule_call(self, statement, deadline)
        finally:
            self._active = None
        self._service_seen[kind] = max(self._service_seen.get(kind, 0.0), time.monotonic() - began)
        return reply
''')
sub('src/xverse/maestro/dispatcher.py', '''        self._active = None
        self._result = None
''', '''        self._active = None
        self._service_seen = {}  # statement kind -> longest observed round trip (F-08)
        self._result = None
''')
sub('src/xverse/maestro/teardown.py', '''        self._active = step
        receipt = self.owner.persistence.record_teardown(self, step, deadline)
''', '''        # F-09 (finding 438): the same rule for teardown records, so a phase deadline shared
        # through a sequence never hands its last record less than an observed record round trip.
        began = time.monotonic()
        if deadline.monotonic_seconds - began < self._record_seen:
            raise TeardownError("ML-TEARDOWN-RECORD-BUDGET")
        self._active = step
        receipt = self.owner.persistence.record_teardown(self, step, deadline)
        self._record_seen = max(self._record_seen, time.monotonic() - began)
''')
sub('src/xverse/maestro/teardown.py', '''        self._receipts = {}
''', '''        self._receipts = {}
        self._record_seen = 0.0  # longest observed teardown record round trip (F-09)
''')
print('applied')
