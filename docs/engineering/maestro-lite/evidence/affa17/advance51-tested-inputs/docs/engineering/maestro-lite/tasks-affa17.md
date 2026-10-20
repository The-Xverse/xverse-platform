# Run-wide AFFA / surviving supervisor implementation tasks

DRAFT. Parent must advance to verified recovery16 before integration/freeze. Isolated
new protocol/native unit work may proceed on the pinned initial parent. Full phase3 remains
open. These engineering tasks do not replace any capability024 requirement.

- [x] Record the single-authority problem, native/Python allocation and unit contract before code.
- [ ] Freeze independently authored exact wire, crash and two-unit ordering expectations (AF01–AF22 authored; exact wire still pending).
- [ ] Implement the original run-wide native authority and strict private bounded client.
- [ ] Integrate all Stage/Release/Cancel/lease operations with its shared epoch and ticket table.
- [ ] Preserve original pre-Stage C1 ownership and fence all late authority before fallback release.
- [ ] Compose the surviving original supervisor/broker and replaceable admitted controller worker.
- [ ] Integrate fresh-session durable reconciliation and explicit fresh-generation restart.
- [ ] Export original public-safe issuance/epoch facts for U7/U8 without authority material.
- [ ] Record separate read-only findings before repairs and verify exact source/wheel/native assembly.
- [ ] Commit verified stable source and thesis checkpoint; retain all full runtime/acceptance gates.

Current parent: `46e0ebfd332dd833322d764191a7cfe1e008bec1`; recovery16 thesis checkpoint28f8f74.
Private ABI values now express same-authority selective advance with explicit
generation bounds;51 pure checks pass. Native enforcement and all actual behavioral
controls remain open. No codec-only stable increment or acceptance is claimed.
