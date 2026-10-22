"""Thesis Lite Phase 6: flow runtime over the accepted X-COM contracts.

Public surface: ``bind`` (flows to routes with explicit per-route policies, refusals collected),
the closed time grammar, the receiver with its verdicts, Argus evidence helpers and the
tick-driven ``FlowRunHarness``. The Python route layer mirrors the C++ loopback provider and opens
no X-COM route (D6-7); the Maestro dispatcher is not involved (D6-11).
"""

from .binding import FlowBinding, FlowBindingRecord, FlowPolicy, bind, flow_hash
from .clock import ReceiverClock, TickClock
from .codes import FlowError
from .evidence import FlowEvidence, reconstruct_flows
from .provider import LOOPBACK, MIRROR_SHA256, MIRRORED_FILES, claims, mirror_digest
from .receiver import FlowItem, FlowReceiver, ItemVerdict
from .run import FlowRunHarness, HarnessResult
from .timebase import TimeMapping, parse_mapping, parse_quantity_ns, seconds_to_ns

__all__ = [
    "LOOPBACK", "MIRROR_SHA256", "MIRRORED_FILES", "FlowBinding", "FlowBindingRecord", "FlowError", "FlowEvidence",
    "FlowItem", "FlowPolicy", "FlowReceiver", "FlowRunHarness", "HarnessResult", "ItemVerdict", "ReceiverClock",
    "TickClock", "TimeMapping", "bind", "claims", "flow_hash", "mirror_digest", "parse_mapping", "parse_quantity_ns",
    "reconstruct_flows", "seconds_to_ns",
]
