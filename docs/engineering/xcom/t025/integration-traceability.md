# T025 protected integration trace disposition

This host-side allocation reviews the immutable Fabro candidate against the authoritative
[capability 007 specification](../../../../specs/007-xcom-core/spec.md). The worker's
`engineering/trace.md` preserved the FR IDs but explicitly left their allocation unverified because
the predecessor text was unavailable in its sanitized workspace. That allocation is not accepted as
the protected trace. The complete worker trace and link matrix remain unchanged in the copied run.

| Capability 007 anchor | T025 disposition and link | Remaining work |
| --- | --- | --- |
| FR-015 common stimulation boundary | Deferred. T025 only supplies time, permit, and session primitives. | T027 signal/message injection, service invocation, emulation. |
| FR-016 disabled-by-default, exact single-session permit | Partial: T025-SR-007 through SR-010, SR-013 through SR-015; `validation_session.hpp/.cpp`, unit/integration/validation tests. | T028 enforce permit at every emission path. |
| FR-017 visible synthetic/tool provenance | Deferred. T025 emits zero normal-route items (SR-018), so no provenance propagation is exercised. | T029 routed-item provenance tests. |
| FR-018 item validation before route entry | Partial: permit/session envelope validation in SR-007, SR-008, SR-013, SR-015. | T028 schema, direction, target, quota and route-entry checks. |
| FR-019 loop and emulation conflict handling | Deferred. No injection or emulation exists in T025. | T027–T029. |
| FR-020 scheduled semantics and clock domain | Partial: time authority and mapping in SR-001 through SR-006. | T027–T029 ordering, late-item policy, immediate labeling and reproducibility limits. |
| FR-033 explicit time authority and unmapped-clock policy | Partial: SR-001 through SR-006, `validation_session.hpp/.cpp`, unit/validation tests. | T028 rejection or invalid-before-emission policy at the stimulation boundary. |

`SR` identifiers above are the preserved `T025-SR-*` records in the run's
`worker-capture/engineering/requirements/` directory. The worker's machine-readable
`worker-capture/engineering/trace/links.json` retains the detailed requirements-to-design-to-code-to-test
links for the bounded standalone implementation. This host disposition corrects the protected FR
allocation and does not rewrite historical worker evidence.
