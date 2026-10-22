"""Python mirror of the C++ X-COM route rules for the loopback provider (D6-7; design §4).

The mirror reproduces ``declared_delivery_claim`` / ``declared_ordering_claim`` and the
``prepare_route`` refusals (``unsupported_policy`` = ``XCOM-PROV-E030``, queue and route limits)
for the one implemented provider, ``LoopbackProvider``. It opens no X-COM route. ``MIRROR_SHA256``
binds the mirror to the C++ sources it was written from; ``mirror_digest`` recomputes it so a test
fails on any drift until the mirror is re-reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

MIRRORED_FILES = (
    "src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp",
    "src/xverse/xcom/include/xverse/xcom/provider.hpp",
    "src/xverse/xcom/src/loopback_provider.cpp",
    "src/xverse/xcom/src/provider.cpp",
)
#: Digest of ``MIRRORED_FILES`` at platform main ``2d556ff24`` (path, NUL, length, NUL, bytes).
MIRROR_SHA256 = "0e38ed80fc4c9a752a564b88b69a55315bb230d548c23e10741d4f68a70475d6"

DELIVERY_CLAIMS = {"best-effort": "best_effort", "at-least-once": "reliable"}
ORDERING_CLAIMS = {"unordered": "unordered", "fifo": "per_route_fifo"}


@dataclass(frozen=True)
class ProviderModel:
    """Mirrored provider descriptor: capability masks and limits."""

    delivery_mask: frozenset[str]
    ordering_mask: frozenset[str]
    max_queue_items: int
    max_routes: int


#: ``LoopbackProvider::descriptor_compatible`` (loopback_provider.cpp 30-38; kMaximum* in the .hpp).
LOOPBACK = ProviderModel(frozenset({"best_effort"}), frozenset({"per_route_fifo"}), 8, 4)


def claims(reliability: str, ordering: str) -> tuple[str, str] | str:
    """Return ``(delivery, ordering)`` claim names, or the C++ outcome name of the refusal."""

    if reliability not in DELIVERY_CLAIMS:
        return "unsupported_delivery"
    if ordering not in ORDERING_CLAIMS:
        return "unsupported_ordering"
    return DELIVERY_CLAIMS[reliability], ORDERING_CLAIMS[ordering]


def mirror_digest(root: str | Path) -> str:
    """Recompute the mirror digest over ``MIRRORED_FILES`` under ``root``."""

    digest = hashlib.sha256()
    for path in sorted(MIRRORED_FILES):
        data = (Path(root) / path).read_bytes()
        digest.update(path.encode() + b"\0" + str(len(data)).encode() + b"\0" + data)
    return digest.hexdigest()
