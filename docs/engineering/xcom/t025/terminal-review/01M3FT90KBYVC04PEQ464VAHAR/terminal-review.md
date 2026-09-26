# T025 independent terminal re-review

Date: 2026-09-26T22:20:28.607966+00:00. Run: `01M3FT90KBYVC04PEQ464VAHAR`. Candidate: `7ec9a5ab85bc6d805c78a938514dc647b710551fb18cb42f5644a58f76fe0e9d`.

**Verdict: R6 and R5 fixed for the focused standalone scope.** This is a reviewed candidate, not protected integration or external delivery acceptance.

## R6 — fixed in candidate

`TimeAuthority::declare_clock` now assigns each declaration a generation. `now_impl` and the mapped destination read capture that generation with the observation under the authority mutex; `advance_baseline` accepts the deferred commit only if the same declaration still owns the domain. A re-declaration between peek and commit therefore leaves the replacement baseline untouched. The deterministic `BUG_R6_ConcurrentRedeclaration` and `BUG_R6_MappedRedeclaration` cases place replacement at that exact point; `BUG_R6_PublicReadAfterRedeclare` checks ordinary reads. The existing rejection-side-effect case remains in the suite. A fresh build of the exact captured source in the pinned, network-blocked image passed **144/144 CTest cases** ([log](fresh-ctest.log), SHA-256 `f9c00bf8f19cbfa6856ea4d16eecfb9291c91c3d7488e68ae598dd773533e5dc`).

## R5 — fixed in collector and observed handoff

The pinned [collector](../../collect_terminal.py) derives the ultra-light minimum candidate and evidence path set from the host dispatch receipt, independently of the worker manifest. The isolated [probe](collector-probe.log) rejects a missing manifest, a listed but missing source, source omitted from the manifest, and evidence omitted from the manifest. Its SHA-256 is `e49814c72c065f3139922f83712bf9c0805c9845aa917e22cb3de57390a70fe9`. The exact pinned collector hash matches the [dispatch receipt](../../runs/01M3FT90KBYVC04PEQ464VAHAR/dispatch-ultra-light.json) and worker check report. This run's [terminal index](../../runs/01M3FT90KBYVC04PEQ464VAHAR/morning-review-index.json) has no collection errors; all **833** indexed files and **12** worker-manifest artifacts matched hashes, and the candidate identity recomputed correctly.

## Limits

Protected predecessor integration, sanitizers, CodeQL, and external acceptance were not performed in this focused review. The dirty `/home/jefferson/xverse-platform` checkout was not changed.
