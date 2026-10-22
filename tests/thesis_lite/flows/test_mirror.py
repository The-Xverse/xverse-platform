"""V10: mirror drift guard, claim mapping and the FR-024 core headers unchanged."""

from __future__ import annotations

import hashlib
from pathlib import Path

from xverse.flows import LOOPBACK, MIRROR_SHA256, claims, mirror_digest

ROOT = Path(__file__).resolve().parents[3]
CORE_HEADERS = ("value.hpp", "contract.hpp", "item.hpp", "diagnostic.hpp", "result.hpp", "core_types.hpp",
                "endpoint_route_lifecycle.hpp", "provider.hpp", "loopback_provider.hpp", "observation.hpp")
#: Digest of the 10 FR-024 core headers at platform main 2d556ff24 (name, NUL, length, NUL, bytes).
CORE_HEADERS_SHA256 = "67dd25ce73c46fd52b2362f0f525b3448f1d0f029f26774bb8807e8a43801904"


def test_v10_mirror_matches_the_cpp_sources_it_was_written_from():
    assert mirror_digest(ROOT) == MIRROR_SHA256


def test_v10_core_headers_byte_identical_to_the_phase_6_base():
    digest = hashlib.sha256()
    for name in sorted(CORE_HEADERS):
        data = (ROOT / "src/xverse/xcom/include/xverse/xcom" / name).read_bytes()
        digest.update(name.encode() + b"\0" + str(len(data)).encode() + b"\0" + data)
    assert digest.hexdigest() == CORE_HEADERS_SHA256


def test_v10_claim_mapping_and_loopback_masks():
    assert claims("best-effort", "fifo") == ("best_effort", "per_route_fifo")
    assert claims("at-least-once", "unordered") == ("reliable", "unordered")
    assert claims("exactly-once", "fifo") == "unsupported_delivery" and claims("best-effort", "priority") == "unsupported_ordering"
    assert (LOOPBACK.delivery_mask, LOOPBACK.ordering_mask, LOOPBACK.max_queue_items, LOOPBACK.max_routes) == (
        frozenset({"best_effort"}), frozenset({"per_route_fifo"}), 8, 4)
