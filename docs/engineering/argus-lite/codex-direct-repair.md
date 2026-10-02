# Argus Lite direct Codex successor (2026-10-02)

The author requested: "abort it and try to solve it directly with codex". This authorizes
this isolated repair of P2-FINISH and supersedes the factory-only engineering route for this task.
It does not accept the candidate or authorize a main merge. The 63 later DRAFT planning items
remain unstarted. The queue and its watchdog are disabled; the active worker was captured before
cancellation. Accounting and unsuccessful factory evidence are retained.

The candidate is a successor assembled over platform main
`947ac1e58e2b97f2cd6d6cdb33bc1b3c3bdc7f6b`, on
`codex/argus2-direct-repair-20261002`. The originally admitted specifications at
`distributed_safety_critical_thesis/specs/023-argus-lite-evidence/` remain external inputs;
their `c1fd213...` baseline describes planning history, not this assembled target.
The 124 captured in-scope paths were imported without modifying accepted XDL or C++ sources.
The source main checkout's existing untracked author records are preserved.

## Review findings and successor design

A separate read-only pass recorded CDX-01..03 before repairs, followed by a second pass
recording CDX-04..05 and CDX-06 with failing reproductions before their repairs. Both records and the
original worker inventory are retained in the external evidence bundle below.

| Findings | Existing requirements | Repair and regression evidence |
| --- | --- | --- |
| CDX-01, CDX-04, CDX-05, CDX-06 / AR-F03 | ARGUS2-SR-001, 002, 005, 007, 010 | Reader validates required manifest member types, full stream identity, plan/provenance/metric metadata, unique artifact paths, declared clocks and nested obligations. Present-null event members and duplicate JSON object members are rejected. Huge version components return a stable unsupported-schema result. |
| CDX-02 / AR-F01, AR-F02 | ARGUS2-SR-002, 005, 007, 010 | Recorded event count is checked against verified records. Artifact/obligation collections are bounded before verification. Actual stream line count is bounded independently of byte size. |
| CDX-03 / AR-F01, AR-F02 | ARGUS2-SR-003, 005, 006, 010 | Descriptor-relative directory traversal anchors the read to verified parent directories; symlink swaps cannot redirect hashing. Stream and artifact I/O failures yield stable diagnostics and incomplete evidence. Artifact hashing rejects a size mismatch before hashing and stops if the file grows beyond the recorded size. |
| Inherited AR-F04, AR-F05, AR-RVW-001 | ARGUS2-SR-001, 002, 005, 006, 007, 010 | Exact publication byte bounds, admission snapshots, defensive returned copies and iterative nesting guards are retained and repeated by the existing adversarial tests. |

The additive regression file is `tests/thesis_lite/argus/test_argus2_codex_repair_unit.py`
(47 parameterized cases). Existing frozen identifiers and assertions are preserved. Source
changes are in `api.py`, `artifacts.py`, `reader.py`, `recovery.py` and `schema.py`; remaining
Argus source adjustments are import/annotation/lint cleanup. No new runtime dependency is added.
The local descriptor walk uses Linux/POSIX directory descriptors and `O_NOFOLLOW`.

## Exact configuration and delivery evidence

The explicit external evidence bundle is
`/home/jefferson/x-verse_fabric/automation/argus2-codex-direct-20261002/`.
Its `verification.json`, `final-review.json`, `candidate-identity.json`, `assembly.json`,
`trace-audit.json` and `evidence-index.json` bind the candidate commit/tree, input hashes,
commands, environment/tool identity, return codes and log hashes. Until populated and checked,
these locators carry no passing claim. `integration.log` is the actual immutable-image,
network-disabled verification over the isolated pinned target assembly, with the full platform
suite and installed-wheel consumer repetition, including real XDL compiler and owned C++20
X-COM producer fixtures. This is direct Codex verification, not a Fabro gate receipt.

Historical `argus2-*.json` stage records, `internal-review.json`, `implementation.md`,
`integration.md`, `validation.md` and older Argus review-index paragraphs are preserved
as predecessor history only. Their hashes, counts, verdicts and seals do not establish
verification of this successor. This document and the bound external bundle define its current
state. Mutable trace file pins are refreshed to the actual successor bytes, with a retained delta.

## Maintenance and limitations

Use the existing `maintenance.md` API/CLI procedures. When changing parsing or confinement,
repeat malformed-member, finite-bound, I/O failure and directory-swap regressions as well as
full target and installed-wheel checks. Do not remove a failing assertion to obtain a pass.
Retain the original run files; read-only reconstruction neither repairs nor mutates them.

All twelve REF-002 parent allocations retain their bounded partial extent. Evidence completeness
means only that declared capture obligations and integrity checks were satisfied. No safety,
scientific-result, runtime, live-tap, metric computation, oracle, compatibility/parity,
production or power-loss durability claim follows. Acceptance and merge into platform main
remain explicit author gates under AGENTS.md and ADR-0020. No phase 3 or later work is performed.

Model recommendation: Sol/high for the boundary repair and verification (task-based judgment,
no measured cost claim; no session model switch was performed). Next step after the completed
bundle is read-only author acceptance review, then an isolated merge only if explicitly accepted.
