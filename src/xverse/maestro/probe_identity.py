"""S1b admitted readiness probe identities (design-stabilization-s1b.md, ADR-ML3-PROBE-0001 amendment S1b-1).

The identity is the catalog observe ``condition``, already part of the plan digest. ``running`` is sampled
process existence after exec; ``nonce-marker`` additionally requires the unit's ready marker to equal the
per-generation challenge nonce, checked only by the native authority. Periodic health stays ``running``.
"""

from xverse_xdl.catalog import NONCE_MARKER_CONDITION

RUNNING = "running"
NONCE_MARKER = NONCE_MARKER_CONDITION
READINESS_PROBES = (RUNNING, NONCE_MARKER)
HEALTH_PROBE = RUNNING
