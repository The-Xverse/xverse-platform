# Argus Lite Phase 2 — integration record

| Field | Value |
| --- | --- |
| Feature | ARGUS2 (Argus Lite Phase 2 — bounded run evidence persistence, X-COM observation projection import and read-only reconstruction) |
| Stage / role | integration (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 7 (integration re-run against the revision-7 `AR-F01` recorded-`eventStream.path` repaired implementation candidate) |
| Supersedes | Revision 6 (`docs/engineering/argus-lite/integration.md` sha256 `e59ab4b39874515524f787d82731c4677f22f17c0c1d338bb5acc1685a626bb4`, recorded by `engineering/stage-results/argus2-integration.json` sha256 `4b02df9d87c4da1605aba23e734d2a74f0000f488d7d6f5be60a1decdb194119`). That record was bound to the revision-6 candidate (232 owned cases, 527 platform cases) and is stale for this candidate; its bytes are superseded by this revision and its identity is preserved here as predecessor lineage. Revision 5 (`7fb95787…` / `d467b0ff…`) remains the earlier lineage. |
| Date | 2026-10-02 |
| Admitted platform baseline | `c1fd213cd00259b74f8308d8ca58157ea985aaa0` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`ARGUS2-SR-001` … `ARGUS2-SR-012`), sha256 `1b6d30ee…` |
| Design authority | [`architecture.md`](architecture.md) rev 1 rework (`f2a44c73…`), [`detailed-design.md`](detailed-design.md) rev 1 rework (`4f9537d6…`) |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 rework (`ea6fd473…`) |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 2 (`5e36301a…`); frozen integration measure `engineering/verification/measures/ARGUS2-INTEGRATION.json` (`99757b32…`) |
| Implementation authority | [`implementation.md`](implementation.md) sha256 `356295eec3d8063fd920b3093260dcc0082b41ca387bc7ada7e41a7ad02e6a8d` plus the revision-7 repaired candidate bound by `engineering/stage-results/argus2-implementation.json` sha256 `dbebcce96ccebc3c5a34d1bd5c5cfaf485b6a271a48d9f333dc1444c1fdcf6e1` |
| Classification | Public-safe engineering work-product |
| Maturity | **Integration passes in the worker.** The revision-7 candidate satisfies the frozen `ARGUS2-INTEGRATION` measure in-tree and the whole installed-wheel consumer path in a bounded `/tmp` assembly. This is candidate-local, worker-run evidence only; it is **not** trusted target-repository verification, and no compatibility, parity, validation or delivery claim follows. |

## 1. Purpose and boundary

This stage executed the integration continuation of the captured ARGUS2 revision-7 repair checkpoint. It
re-ran the nine frozen `ARGUS2-INTEGRATION` identifiers, the full platform pytest suite, the owned Argus
suite, and the exact installed-wheel consumer command supplied by the host
(`/opt/controls/argus_checks.py`, non-`static` branch), then recorded the honest observed results and
hashes.

It changed **no** source, test, fixture, schema, packaging or historical record in the candidate. It is
a read-and-run stage. The integration opportunity it exercised is the installed-wheel contract: owned
Argus tests must run against the installed wheel with `PYTHONPATH` set only to the installed packages
and `ARGUS_PLATFORM_SOURCE_ROOT` set to the target, with no platform `src` injected into `sys.path`.

The candidate under test is the revision-7 repaired implementation:

* the frozen adversarial cases `ARGUS2-ADV-01`–`ARGUS2-ADV-07` (findings `AR-F01`–`AR-F05`);
* the revision-4 residual repairs (`AR-F03` non-finite manifest rejection via `schema.find_nonfinite`
  and `reader.read_run`; `AR-F04` newline-inclusive exact manifest byte bound in `writer._publish` and
  the `api.open_run` preflight);
* the revision-5 residual repair (`AR-RVW-001`: iterative bounded nesting checks in
  `schema.json_text_depth_exceeded`/`schema.parse_json_bounded`/`schema.json_depth_exceeded`/
  `schema.canonical_json`, in `reader.read_run`, in `recovery.recover_stream` and in
  `writer.EvidenceRun._append`, so small deeply nested JSON yields stable bounded diagnostics instead of
  an uncaught `RecursionError`);
* the two revision-6 `AR-F03` enclosing-depth repairs: (a) `reader._EXPORT_WRAP_DEPTH = 2` so an event
  record admitted at the parse bound is flagged with one bounded `ARGUS2-BOUND-EXCEEDED` diagnostic and
  assessed incomplete when the JSON export document wrap would push it over `MAX_JSON_NESTING`, with
  `export_json` withholding only the over-deep record and never raising, and CLI export returning a
  stable bounded diagnostic without a traceback; and (b) obligation admission, where `api.open_run`
  converts a manifest-preview nesting overflow into a bounded `ARGUS2-INPUT-FIELD-INVALID`
  `EvidenceError` before any run root is created and `writer._publish` applies the same bounded
  conversion before writing any temp file; and
* the revision-7 `AR-F01` recorded-`eventStream.path` repair: `reader`/`recovery` confine and open the
  exact manifest-recorded relative stream path (or reject every non-canonical recorded path with a
  stable diagnostic), and compare the recorded size and SHA-256 against **that** file rather than the
  canonical default, so missing, different, symlinked or nested recorded paths never yield a primary
  complete assessment for the wrong or corrupt file.

The additive adversarial cases live in `tests/thesis_lite/argus/test_argus2_repair_unit.py` (now 26
cases). The frozen integration identifiers and module are unchanged by those repairs.

## 2. Candidate movement carried into this stage

The predecessor integration record was authored against the revision-6 candidate. The revision-7
continuation added five `AR-F01` recorded-stream-path adversarial cases (repair module now 26 cases) and
changed `reader.py` and `recovery.py`. This stage re-verified the whole integration surface against the
revision-7 bytes rather than citing the predecessor numbers.

| Aspect | Predecessor (rev 6 record) | This candidate (rev 7) |
| --- | --- | --- |
| Owned Argus cases | 232 (193 unit + 9 integration + 30 validation) | 237 (198 unit + 9 integration + 30 validation) |
| `ARGUS2-UNIT` frozen cases | 172 (unchanged; all present) | 172 (unchanged; all present) |
| `ARGUS2-VALIDATION` frozen cases | 30 | 30 (unchanged; all present) |
| Additive `test_argus2_repair_unit.py` cases | 21 | 26 (additive; not in any frozen measure) |
| Full platform suite | 527 passed | 532 passed |
| `src/xverse/argus/reader.py` | `1347eda6…` | `cdb6fb1482567af5c0898c38368352dd04dc37cf07220081981dd5ea4abca66b` |
| `src/xverse/argus/recovery.py` | `528c8756…` | `5045c80e6f6f72e3f075631aceb0b431e7d730811e2fc6cc1cdb79533ec77493` |
| `src/xverse/argus/writer.py` | `7f8d816e…` | `7f8d816e6b26aad62bbe885cc7a4d9a9eb5bcefc2d2f90a832351f9e42ca538b` (unchanged) |
| `src/xverse/argus/api.py` | `74858074…` | `748580741a060d2b0af4a5de225e873a29deb8e9a201cc0e5199bc15b4786aef` (unchanged) |
| `src/xverse/argus/schema.py` | `48c0c184…` | `48c0c18477998f33b4997e8480beb92676bfb8c5b8ec8cf47f705b1e560206e2` (unchanged) |

No assertion was weakened, skipped or deleted to obtain these results. The frozen nine identifiers are
identical to `engineering/verification/measures/ARGUS2-INTEGRATION.json`
(sha256 `99757b323c97e6ff65b51523886b54e29a3bec227fcadae476ee5b150a9cbeee`), and each still compiles
the real C++20 producer and drives the real accepted XDL compiler.

## 3. Nine frozen ARGUS2-INTEGRATION cases — actual result

Command (candidate-local, as declared by the measure), run from the candidate checkout:

```
python3 -m pytest -v -p no:cacheprovider tests/thesis_lite/argus/test_argus2_integration.py
```

Result: **exit 0 — `9 passed in 40.42s`.** The discovered passing identifier set equals the frozen set
exactly (9 of 9, no missing, no extra), re-checked programmatically against
`engineering/verification/measures/ARGUS2-INTEGRATION.json`:

* `tests/thesis_lite/argus/test_argus2_integration.py::test_real_accepted_xdl_compiler_output_written_and_reconstructed`
* `…::test_real_owned_cpp_observation_fixture_compiles_and_imports_by_value`
* `…::test_real_owned_cpp_snapshot_fixture_preserves_interval_and_counters`
* `…::test_owned_cpp_projection_roundtrip_with_accepted_xcom_headers`
* `…::test_installed_wheel_imports_xverse_argus_and_xverse_xdl_outside_source_tree`
* `…::test_owned_argus_tests_repeat_against_installed_wheel_with_empty_pythonpath`
* `…::test_existing_platform_pytest_regression_unchanged_in_assembled_target`
* `…::test_existing_xdl_cli_and_public_api_preserved_in_assembled_target`
* `…::test_gateway_protobuf_observation_not_substituted_for_owned_projection`

Real interoperability remains exercised, not simulated: the owned neutral fixtures are compiled by the
real accepted `xverse_xdl.experiment_plan.compile_experiment_files`; the owned C++20 producer fixture
is compiled with `g++ -std=c++20` against the accepted
`src/xverse/xcom/include/xverse/xcom/observation.hpp` and the accepted
`observation.cpp`/`item.cpp`/`contract.cpp`/`value.cpp`/`diagnostic.cpp` translation units under
`/tmp`; the serialized owned projection is imported, finalized, read back and exported by value. No
public C++ source was modified. The narrower tool-gateway protobuf observation remains rejected as the
full owned projection.

Log: `/tmp/argus-int7/integration_nine.log` sha256
`d1f20ae092d59667bfb3d8ed00f4efc9a744a1d7c2a10d459df63f234a1129fb`.

## 4. Full platform and owned suites — actual result

| # | Command (from the candidate checkout) | Exit | Observed result |
| --- | --- | --- | --- |
| 1 | `python3 -m pytest -q -p no:cacheprovider tests/thesis_lite/argus` | 0 | `237 passed in 70.82s` — all owned Argus cases |
| 2 | `python3 -m pytest -q -p no:cacheprovider tests` | 0 | `532 passed in 92.92s` — no regression in the accepted XDL, catalog, lifecycle, CLI, C++ X-COM, thesis-lite or Argus suites |

These are candidate-local worker checks, not trusted measure evidence.

The frozen design is fully realized in the candidate: programmatic set checks over the collected owned
identifiers confirm `ARGUS2-UNIT` 172/172, `ARGUS2-INTEGRATION` 9/9 and `ARGUS2-VALIDATION` 30/30
declared identifiers present, with 0 missing (211 frozen identifiers), plus the 26 additive adversarial
cases in `test_argus2_repair_unit.py` (237 total). The 26 additive cases are additive regression
coverage only; they are not entries in the frozen `ARGUS2-UNIT` measure, which declares exactly 172
pre-frozen identifiers. No frozen identifier was renamed, dropped, skipped or weakened.

Per-module collected counts (this candidate): admission 13, artifacts 14, bounds 15, clocks 8,
consumer 10, diagnostics 4, identity 17, observation 12, offline 11, payload 13, reader 24, recovery 3,
repair 26, stream 16, writer 12, integration 9, validation 30 (total 237).

Logs: `/tmp/argus-int7/owned_argus.log` sha256
`3bf1850301e65e59625777d056796a4f266b79ae631b2078df62ef5262c8813d`;
`/tmp/argus-int7/platform_full.log` sha256
`162c98f4e6e438450f797174613214a49965f8bd7d27cbfca23e13eaab61be0f`.

## 5. Exact installed-wheel consumer command — actual result

`/target` is not mounted in this worker, so the exact trusted command was replicated by replacing **all
three** `/target` path literals with one bounded `/tmp` copy of the candidate checkout and nothing else.
`diff` confirms the replication differs from `/opt/controls/argus_checks.py`
(sha256 `47a5ee269a02b77af17d4954ee6a9ccaf560636115b1b02d396e755faeb0b922`) only in those three path
literals; the replication sha256 is
`d991bbd86e8ba824a78d0655db5c0341f02dc2b6173ea83553bb58de906a308d`. The bounded copy is the full
candidate checkout (2,919 regular files by local `find -type f`; `/tmp` is outside `/workspace`). The
trusted `engineering-checks` shim was not invoked.

```
cd /tmp/argus-target
python3 /tmp/argus-wheel-replica.py integration
```

The script's non-`static` branch ran, in order:

| # | Step | Observed result |
| --- | --- | --- |
| 1 | `python3 -m pytest -v -p no:cacheprovider tests`, `cwd=/tmp/argus-target` | exit 0 — `532 passed in 88.24s` |
| 2 | `python3 -m build --wheel --no-isolation --outdir <tmp>/dist`, `cwd=<target>` | exit 0 — `Successfully built xverse_xdl-0.4.0-py3-none-any.whl` |
| 3 | `python3 -m pip install --no-index --no-deps --target <tmp>/installed <wheel>` | exit 0 — `Successfully installed xverse-xdl-0.4.0` |
| 4 | outside-source-tree import check, `PYTHONPATH=<tmp>/installed` only, `ARGUS_PLATFORM_SOURCE_ROOT=<target>` | exit 0 — `INSTALLED_CONSUMER_IMPORT_PASSED` (`xverse.argus` and `xverse_xdl.experiment_plan` both resolve under `installed`) |
| 5 | copy `<target>/tests/thesis_lite/argus` to `<tmp>/tests` and run `python3 -m pytest -v -p no:cacheprovider <tmp>/tests`, `cwd=<tmp>` | exit 0 — `237 passed in 62.76s` |
| 6 | final marker | `TARGET_AND_INSTALLED_CONSUMER_PASSED`, process exit 0 |

Overall wall time 152 s; log `/tmp/argus-int7/installed_consumer.log` sha256
`734ffcef918b6fd3662377c2e2971aa991e8ae6d835043c038436160be545b51`.

The installed-wheel contract was satisfied as required:

* The `env` for steps 4 and 5 sets `PYTHONPATH` to the installed target **only** and
  `ARGUS_PLATFORM_SOURCE_ROOT` to the target; the platform `src` tree is never placed on
  `PYTHONPATH`, and no owned module injects platform `src` into `sys.path` (the only `sys.path.insert`
  calls add the owned test directory).
* The owned tests therefore resolve `xverse.argus` and the accepted XDL modules from the **installed
  wheel**, and resolve the accepted platform C++ sources and XDL fixtures from
  `ARGUS_PLATFORM_SOURCE_ROOT` (the bounded target copy), exactly as `verification-plan.md` §8 requires.
* The copied owned tests collect all 17 owned modules (including the 9 integration and 30 validation
  identifiers) and pass all 237 cases with no collection error, so the repair-facing cases
  (`ARGUS2-ADV-01`–`ARGUS2-ADV-07`, `AR-F01`–`AR-F05`, the revision-4 `AR-F03`/`AR-F04`
  non-finite/exact-bound repairs, the revision-5 `AR-RVW-001` bounded deep-nesting repairs, the
  revision-6 `AR-F03` enclosing-depth repairs and the revision-7 `AR-F01` recorded-stream-path repair)
  run against the installed wheel, not the source tree.

### 5.1 Explicit installed-resolution check

As direct supporting evidence of the "only installed packages" requirement, an independent check built
the wheel offline from the target copy and installed it into `/tmp/argus-int7/explicit/installed`, then
ran from a neutral working directory with `PYTHONPATH=/tmp/argus-int7/explicit/installed` (installed
target only), `PYTHONDONTWRITEBYTECODE=1` and
`ARGUS_PLATFORM_SOURCE_ROOT=/tmp/argus-target`:

```
sys.path = ['', '/tmp/argus-int7/explicit/installed', <stdlib>, <site-packages>]   # no /workspace, no /workspace/src
xverse.argus              = /tmp/argus-int7/explicit/installed/xverse/argus/__init__.py
xverse_xdl.experiment_plan = /tmp/argus-int7/explicit/installed/xverse_xdl/experiment_plan.py
EXPLICIT_INSTALLED_RESOLUTION_PASSED
```

Logs: `/tmp/argus-int7/explicit/resolution.log` sha256
`3d7be0da24680769fd26845b1b37cb9042d0b03011f4a7cd6a383edfef689f25`;
`/tmp/argus-int7/explicit/build.log` sha256
`cca4621bd7ea650b6ff0d5e7ab75a4def3af79dd9c051f668cc0ecf9e7c43674`.

## 6. Preservation and integrity check

All artifacts bound by the five completed predecessor ARGUS2 stage records were re-verified read-only
with `fabro_engineering.core.validate_stage`; the four precode-gate design records and the revision-7
implementation record were not modified by this stage:

| Stage record | Artifacts | Record sha256 | Result |
| --- | --- | --- | --- |
| `argus2-requirements.json` | 24 | `94e67cbd…` | all match |
| `argus2-architecture.json` | 14 | `a099e7a1…` | all match |
| `argus2-unit_specification.json` | 13 | `1556d7e3…` | all match |
| `argus2-verification_design.json` | 14 | `191b5afd…` | all match |
| `argus2-implementation.json` | 44 | `dbebcce9…` | all match |

110 of 110 bound artifacts match their recorded SHA-256, 0 mismatches. The frozen design documents are
byte-unchanged: `requirements.md` `1b6d30ee…`, `architecture.md` `f2a44c73…`, `detailed-design.md`
`4f9537d6…`, `unit-specifications.md` `ea6fd473…`, `verification-plan.md` `5e36301a…`,
`planned-trace.json` `188c0ee7…`. `engineering/trace/links.json` sha256
`39f3db98d0a346bedb0104736f74a46bd675b4f69d72400be2bff65dbb533002` (968 artifacts, 3,595 links via
`core.validate_trace`, which raises on any missing/duplicate/stale endpoint — the call returned cleanly)
and `engineering/project.json` sha256
`9d5927ebbf13f8141d8b7100c0fc07c764722a577e09f65057506006565df7ad` are unchanged from the values
bound by the implementation stage. No prior stage artifact, historical record, accepted C++/XDL source,
schema, CLI or test was modified by this stage. This stage wrote exactly one owned artifact,
`docs/engineering/argus-lite/integration.md`, plus its own replacement stage record.

The only superseded bytes are this role's own predecessor revision (predecessor `integration.md`
sha256 `e59ab4b3…`, predecessor record sha256 `4b02df9d…`), identified in the header so the lineage is
not lost.

## 7. What this stage does and does not establish

* It establishes, in the worker, that the revision-7 repaired candidate satisfies the frozen
  integration identifiers and the exact installed-wheel consumer command over a bounded `/tmp`
  assembly.
* It does **not** perform trusted target-repository verification. The sealed candidate revision, the
  mounted `/target`, the trusted `run_measure` wrapper and the external assembly policy were not
  available to this worker; the host remains the authority for the recorded `ARGUS2-INTEGRATION`
  measure. Worker checks are not reported as trusted verification.
* It performs no independent review, no merge, no sealing and no acceptance.
* All `/tmp` build, install, log and target-copy paths are temporary and are not shipped; their SHA-256
  values are recorded here for the host evidence bundle.

## 8. Candidate artifact identities

| Artifact | sha256 |
| --- | --- |
| `docs/engineering/argus-lite/implementation.md` (rev 7) | `356295eec3d8063fd920b3093260dcc0082b41ca387bc7ada7e41a7ad02e6a8d` |
| `engineering/stage-results/argus2-implementation.json` (rev 7) | `dbebcce96ccebc3c5a34d1bd5c5cfaf485b6a271a48d9f333dc1444c1fdcf6e1` |
| `docs/engineering/argus-lite/verification-plan.md` | `5e36301a1a120bd718c59a87ff1864fe4b1a8907d1426a5add535d4cb26f5baf` |
| `engineering/verification/measures/ARGUS2-INTEGRATION.json` | `99757b323c97e6ff65b51523886b54e29a3bec227fcadae476ee5b150a9cbeee` |
| `tests/thesis_lite/argus/test_argus2_integration.py` | `264bbbb3b88a151e8cde7ec9d6ff339caeb02a7aee83667cb7087a49cf9f8d5c` |
| `tests/thesis_lite/argus/test_argus2_validation.py` | `098f019de68f02b9175943a148476351d7a449458d76171e1e8fee6ea7c92c26` |
| `tests/thesis_lite/argus/test_argus2_repair_unit.py` (26 additive adversarial) | `4742321e7a93e93880049fcb203ee89f0d7805e05b10f3a2b081d4617905a484` |
| `tests/thesis_lite/argus/test_argus2_stream_unit.py` | `56ee723e9478e46c0e882395fc53ca31996cd62e2ef9322f49c1423690d694fc` |
| `tests/thesis_lite/argus/test_argus2_writer_unit.py` | `8bef93857ee53717c3ce6635c646c9c4947c889df9d28974cfc20555f5d163b9` |
| `tests/thesis_lite/argus/support.py` | `bb4dd92f5dae4f1de03382dc4db517eee3cbe730c2a114c3747ac00d0f0393dd` |
| `tests/thesis_lite/argus/fixtures/argus2_owned_record_producer.cpp` | `014f8eb29c6e9b5b92d923e594e0b9a4333b52a8e871b277a934a7e6b4a0748c` |
| `src/xverse/argus/reader.py` | `cdb6fb1482567af5c0898c38368352dd04dc37cf07220081981dd5ea4abca66b` |
| `src/xverse/argus/recovery.py` | `5045c80e6f6f72e3f075631aceb0b431e7d730811e2fc6cc1cdb79533ec77493` |
| `src/xverse/argus/writer.py` | `7f8d816e6b26aad62bbe885cc7a4d9a9eb5bcefc2d2f90a832351f9e42ca538b` |
| `src/xverse/argus/schema.py` | `48c0c18477998f33b4997e8480beb92676bfb8c5b8ec8cf47f705b1e560206e2` |
| `src/xverse/argus/api.py` | `748580741a060d2b0af4a5de225e873a29deb8e9a201cc0e5199bc15b4786aef` |
| `pyproject.toml` (additive wheel configuration) | `a55f3d0ac062b5c349e920770188c28e2a473c5bf1bfdf6075b0a9f73a2b1320` |
| `engineering/trace/links.json` | `39f3db98d0a346bedb0104736f74a46bd675b4f69d72400be2bff65dbb533002` |
| `engineering/project.json` | `9d5927ebbf13f8141d8b7100c0fc07c764722a577e09f65057506006565df7ad` |

## 9. Limitations

* Trusted whole-system verification, candidate sealing and the external assembly policy remain
  external host gates; this stage replicated the trusted command faithfully but cannot substitute for
  them. The measured counts (237 owned, 532 platform) are worker observations, not trusted evidence.
* Successful finalization of an Argus run means only that caller-declared capture obligations and
  integrity checks were satisfied; it never proves scientific validity, safety, compatibility, parity
  or readiness. Nothing here claims otherwise.
* Inherited limitation: the admitted planning bundle names a required launch-evidence
  `admission/review.md` that is not an admitted input for this run; it remains an external, unverified
  later-gate input and is neither fabricated nor substituted.
* No REF-002 parent disposition is promoted or closed and no new system requirement ID is created.
* The 26 additive adversarial unit cases in `test_argus2_repair_unit.py` are not separate entries in the
  frozen `ARGUS2-UNIT` measure (which declares exactly 172 pre-frozen identifiers); they are additive
  regression coverage only and are reported as such.

## 10. Model and next step

The pinned `deepseek-v4-flash` with **high** reasoning remains the most cost-effective authorized route
for this bounded re-run and verification, and no model switch occurred. For the next step the same
pinned route is still the best expected cost-effectiveness: the frozen contracts are already bound, the
repair is narrow, and the remaining work is a deterministic validation pass over the same candidate.
Escalation would be justified only by a measured, reproducible failure the pinned route cannot resolve;
a cheaper route is not justified because the frozen test identifiers and trust boundaries must be
preserved exactly.

Next step: **validation**. No blocker remains for the integration stage; the frozen integration
identifiers and the exact installed-wheel consumer command both pass in-worker. Validation must exercise
the required failure, uncertainty, retention, recovery, security and metamorphic cases and finalize the
mutable source-endpoint hashes, without weakening any assertion or reporting missing evidence complete.
