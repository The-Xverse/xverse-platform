---
title: Status and roadmap
description: Current bounded implementations, release status, and remaining targets.
---

**Documentation baseline: 2026-10-24.** The current tracked release record identifies **X-Verse Lite 1.0 rc.1**, with final release depending on a pending soak qualification. The Python package version is **0.4.0**.

## Available within their declared scope

| Capability | Current scope |
| --- | --- |
| XDL validation and normalization | Local YAML/JSON resource checks and canonical JSON. |
| XDL Lite experiment compilation | Offline resolved intent, dependencies, provenance, and plan digest. |
| Catalog and lifecycle | XDL-derived catalog, planning, ownership/permit mechanics, and owned fixture paths. |
| Maestro Lite | Bounded lifecycle/orchestration engineering implementation, with explicit admission and host assumptions. |
| Argus Lite | Bounded evidence writer/reader and offline verify/export commands. |
| Faults Lite | Closed fault vocabulary, schedule resolution, and tick-driven owned boundaries. |
| Flow runtime | Bounded Python flow layer mirroring admitted X-COM rules. |
| X-COM | C++ communication, observation, controlled stimulation, and local IPC/gRPC gateway prototype. |

The public API references document selected package exports and C++ headers. Internal runtime modules are not promoted into supported public APIs merely because they exist in the source tree.

## Scope that remains separate

General-purpose orchestration services, a complete operational dashboard, broader providers, production readiness, scientific validity, and safety/fitness-for-purpose claims require their own work and evidence. A successful schema check or documentation build does not establish those outcomes.

The bounded Python flow layer does not activate the C++ core. Argus Lite is an evidence interface, not a live dashboard. Owned fixture results do not establish arbitrary device or legacy compatibility.

## Direction

The architecture separates system intent from realizations and keeps extension boundaries explicit. Future work can expand providers, lifecycle services, evidence presentation, and domain blueprints without changing the logical identities of described systems.

This page is maintained with source and release records. Automatic API generation cannot decide that a milestone is complete. Consult the repository's current release and acceptance records when evaluating an exact revision.

## Release and documentation identities

The [publication manifest](/publication-manifest.json) records the source revision and hashes of documentation inputs. A source revision plus those hashes identifies what was used to build this website; it is not runtime acceptance evidence.
