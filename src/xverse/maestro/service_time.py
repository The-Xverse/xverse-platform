"""Per-run service-time estimator for load-aware interior budgets (ADR-ML3-BUDGET-0001).

Observation only: it never sends, waits or grants. Estimates are the longest span observed in the
same run per kind (the v2 statistic of findings 438, 453); a kind never seen estimates 0, so the
first span of a kind is sized and decided exactly as before. Outer admitted bounds are applied by
the callers and never by this module.
"""
import math

SIZING_MARGIN = 1.5    # interior deadline sizing (widening only)
DECISION_MARGIN = 1.0  # go/no-go before a mutation; no floor (findings 433, 434)
NORMAL_SHARE = 0.6     # the normal path's share of an admitted teardown window, unchanged
RPC_MAX_SECONDS = 5    # owner._deadline: no single request deadline beyond now + 5 s (hard)
RUN_MAX_SECONDS = 80   # teardown._deadline: no whole-run teardown deadline beyond now + 80 s (hard)
STOP_FORCE_RESERVE_SECONDS = 0.5  # S1b: kept after a TERM grace for the forced STOP and the boundary check


def valid(seconds):
    return type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0


class ServiceTimes:
    def __init__(self):
        self.seen = {}

    def observe(self, kind, seconds):
        """A completed span of `kind`."""
        if type(kind) is str and valid(seconds):
            self.seen[kind] = max(self.est(kind), float(seconds))

    def seed(self, kind, seconds):
        """A stated estimate (tests, the F-09 record setter); rejected unless finite and >= 0."""
        if type(kind) is not str or not valid(seconds):
            raise ValueError("service-time estimate must be a finite number >= 0")
        self.seen[kind] = float(seconds)

    def censor(self, kind, seconds):
        """A failed or refused span: the work took at least `seconds`."""
        self.observe(kind, seconds)

    def est(self, kind):
        """A corrupted entry (written around observe/seed) estimates 0: today's behaviour."""
        value = self.seen.get(kind, 0.0)
        return value if valid(value) else 0.0

    def statement_max(self, limit):
        """Longest observed statement round trip, capped by an admitted per-statement budget."""
        values = [self.est(k) for k in list(self.seen) if ":" not in k and k != "teardown-record"]  # snapshot
        return min(max(values, default=0.0), limit)


def sized(base, now, need, window, cap):
    """ADR-ML3-BUDGET-0001 M2: never earlier than `base`; equals it whenever `need` fits the normal
    share of `window` (base == now + window). `cap` carries every outer bound and later reserve."""
    if need <= NORMAL_SHARE * window:
        return base
    return max(base, min(now + need + (1 - NORMAL_SHARE) * window, cap))
