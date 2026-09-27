# T010 Implementation Record — Unit-Design Model, Projection, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T010 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | implementation → implementation record |
| Revision | 4 (revision 1 closed `T010-IR-01`..`IR-04`; revision 2 closed `T010-IR-05`/`IR-06`; revision 4 closes the mandatory-scalar and artifact/planned-evidence enforcement gaps `T010-IR-07`/`IR-08`) |
| Internal review | [`internal-review.json`](internal-review.json) returned `fail` with `T010-IR-07` (the mandatory per-unit scalars `family`/`kind`/`language`/`scope`/`maturity` are not rejected when absent) and `T010-IR-08` (`artifact_paths` entries without a `path` and an empty/deleted `planned_evidence` are unenforced); this record and the artifacts it covers are the revision-4 successor candidate that closes both |
| Authorized baseline | `abb81681e0d844edaecbaf2843f1c2a7deb1e40f` |
| Candidate state | working tree over the authorized baseline (candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), [`unit-design.json`](unit-design.json), [`design-units.md`](design-units.md), this record |
| Authorization | ACC001–ACC015, ADR-0016, ADR-0018, ADR-0019, ADR-0020; `specs/007-xcom-core/tasks.md` T010 |
| Maturity | Governance/planning work product implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T010 implements the bounded unit-design work-product slice required by the T010 task entry: one canonical,
schema-versioned unit-design model, its deterministic Markdown projection, and an offline validator with a
controlled self-test. It is a **documentation-and-governance** change plus one offline script under
`scripts/`. The candidate changes **no** path under `src/`, `tests/`, or `xdl/`, adds no `proto/` definition,
changes no `Doxyfile`/CMake/build file, adds no CMake target or runtime artifact, and accepts, completes, or
integrates no other task or software candidate.

The model elaborates — it does not replace — the accepted capability-007 design and the accepted T009
architecture model. It declares **30 design units** (`XCOM-DU-001`–`030` across the `CORE`, `XDL`, `OBS`,
`STIM`, `GW`, `INTG`, and `ENB` families), each with a closed ownership/lifetime model, an explicit
thread-safety model with its shared state and synchronization or message-passing boundary, at least one finite
resource bound with a configuring source and declared overflow policy, a classified condition-to-outcome
failure map, a Doxygen obligation, and T008/T009 trace links; plus **14 invariants** (`XCOM-UDI-01`–`14`) and
a Doxygen plan (`DOX-01`) with three recorded, non-closed gaps. It records
`ref002.disposition = "unchanged"` with an empty promoted set. Every unit is anchored to real
(`established`) or explicitly planned product paths; `established` paths are verified present and `planned`
paths verified absent by `_check_paths`.

The model covers all 11 first-proof T009 components (`XCOM-CMP-001`–`011`) and all 37 `XCOM-SW-*` software
requirements in the T008 register; `XCOM-CMP-012`/`013` are `later`-scope and are neither required nor
exempted. No requirement or component exemption is declared.

### 2.1 Design-detail resolutions

Ten detail decisions were resolved across the four revisions (items 1–4 during the initial
implementation; items 5–7 during the revision-2 repair; items 8–9 during the revision-3 repair of the
internal-review findings; item 10 during the revision-4 repair). They do not change
any accepted requirement, check, contract, or boundary; they reconcile words in the T010 plan package so the
model, validator, projection, and verification plan agree, and each is a successor-candidate change bound to
this revision.

1. **Unknown-token exit class (NEG-10, NEG-11).** `unit-specifications.md` §`U-THREAD`/`U-FAIL` describe an
   unknown thread-safety model token as `THREAD_INVALID` (5) and an unknown outcome token as
   `FAILURE_INVALID` (7). `detailed-design.md` §12.1 (the authoritative exit-class table), `requirements.md`
   §2.4 ("unknown vocabulary token (NEG-07, NEG-10, NEG-11)"), and `verification-plan.md` §4 (NEG-10/11 → 3)
   all classify both as `IDENTITY_INVALID` (3). The validator implements the explicit tables: an unknown
   thread-safety or outcome token is `IDENTITY_INVALID` (3); a *missing* thread-safety model is
   `THREAD_INVALID` (5) and missing failure semantics is `FAILURE_INVALID` (7), which keeps NEG-17 and NEG-25
   at their declared classes.
2. **`XCOM-DU-021` overflow policy.** `detailed-design.md` §8 lists `["reject"]` for the synthetic tool
   client, whose bounds are `deadline`/`timeout`/`bytes`. `detailed-design.md` §3.2 (and the enforced rule)
   requires the overflow policy set to be exactly `["n/a"]` when no capacity/quota/depth/rate bound exists.
   The model therefore records `["n/a"]`, preserving the finite-bound rule and avoiding a self-inconsistent
   declaration; the deferred/rejection semantics remain in the failure map. Revision 2 also corrects the
   `detailed-design.md` §8 row to `["n/a"]` so the authoritative catalogue agrees with §3.2 and the model
   (`T010-IR-01` evidence, `CHK-13`).
3. **Self-referential artifact paths.** `detailed-design.md` §5 records `XCOM-DU-028`'s own artifacts as
   `(p) planned`, but those files (this model, its projection, and the validator) exist at candidate
   verification time, so `planned` would fail the tree-status check. They are recorded `established`: the
   status is a present/absent tree fact, not a baseline-versus-candidate fact.
4. **Additional isolating fixtures.** The plan's declared set is NEG-01..NEG-46. Four extra fixtures isolate
   declared sub-cases without renumbering the declared set: NEG-05b (dict id, alongside the list id of
   NEG-05), NEG-24b (non-zero retry, alongside the `["n/a"]`-with-capacity case of NEG-24), NEG-33b
   (`implemented` without an accepted revision, alongside the partial-without-reason case of NEG-33), and
   NEG-34b (reverse dependency on an upstream component, alongside the core domain-primitive case of
   NEG-34). Each extra fixture exercises a distinct check path already implied by the declared case.
5. **Invariant enforcing-check alignment and pinned-invariant failure class (`T010-IR-01`).** The model's
   `enforcing_check` values for `XCOM-UDI-05`..`08` and `-13` carried the same four-check string, which did
   not match `detailed-design.md` §11. They now name the single authoritative catalogue check per invariant
   (`-05`/`-06` → CHK-06, `-07` → CHK-07, `-08` → CHK-08, `-13` → CHK-11), and §11 now states that a
   weakened pinned invariant is a `GOVERNANCE_INVALID` (9) failure — the only class the pinned-invariant
   branch of `_check_governance` reports. `design-units.md` was re-projected.
6. **`XCOM-DU-013` saturation classification (`T010-IR-02`).** The failure map's saturation condition is
   scoped to the one rejecting tap policy (`drop-newest` → `rejected`) and `detailed-design.md` §9 now states
   the classification for all three declared policies: `drop-newest` rejects the offered record, `coalesce`
   merges it, and `lossless-backpressure` backpressures the producer before any record is lost, the selected
   policy and counter being surfaced. This keeps the single closed-vocabulary outcome (`rejected`) that maps
   to the only rejection case and removes the contradiction with the §8 overflow-policy set.
7. **Stored-model canonicality and the U-VALIDATE check list (`T010-IR-03`, `T010-IR-04`).** The validator now
   compares the **on-disk** `unit-design.json` bytes against the canonical serialization (previously
   `--verify`/`--check-human` compared the parse result with itself, so the check was unreachable), and
   `unit-specifications.md` §`U-VALIDATE` now names the sixteen check functions actually defined. Closure
   evidence is in §5.1.
8. **Thread-safety consistency rule is now enforced (`T010-IR-05`).** `detailed-design.md` §3.1 declared as an
   "all enforced" rule that a unit with non-empty `shared_state` must use an
   `internally-synchronized`/`externally-synchronized`/`message-passing` model, but `_check_thread_safety`
   only rejected shared state for `immutable-value`/`read-only-static`/`offline-single-threaded`, so a
   `single-thread-owner` unit slipped through, and the reverse direction (a non-null `synchronization` on a
   non-synchronizing model) was unenforced. `XCOM-DU-008` declared `shared_state = ["per-route in-flight queue"]`
   under `single-thread-owner` with a null `synchronization`, contradicting `XCOM-UDI-04`/CHK-05 while `--verify`
   still passed. The validator now defines `SYNCHRONIZING_THREAD_MODELS`
   (`internally-synchronized`/`externally-synchronized`/`message-passing`), treats every other model as owning no
   shared mutable state (`UNSYNCHRONIZED_THREAD_MODELS = {immutable-value, read-only-static, single-thread-owner,
   offline-single-threaded, process-isolated}`), rejects non-empty `shared_state` on any non-synchronizing model,
   and requires `synchronization = null` exactly for the non-synchronizing models. `XCOM-DU-008`'s per-route
   in-flight queue is corrected to declared owner-private state (`shared_state = []`) with the rationale stating
   exclusive ownership, and `detailed-design.md` §3.1/§7, `verification-plan.md` CHK-05, and the
   `unit-specifications.md` `U-THREAD`/cross-cutting rows now state the enforced predicate. Two isolating
   fixtures, **NEG-18b** (`single-thread-owner` with non-empty `shared_state`) and **NEG-19b**
   (`immutable-value` with non-null `synchronization`), reject as `THREAD_INVALID` (5). Closure evidence is in
   §5.2; no accepted requirement, invariant, or check is weakened — `XCOM-UDI-04` is strengthened.
9. **Untracked-set evidence corrected (`T010-IR-06`).** Command 19 previously recorded the untracked set as
   `internal-review.json` **plus** `reports/xcom-queue/t010-package.json`, but that manifest did not exist at the
   reviewed revision (only `t007`/`t008`/`t009` manifests are present and tracked). The record now states the
   observed untracked set (`docs/engineering/xcom/t010/internal-review.json` only) and attributes
   `reports/xcom-queue/t010-package.json` to the later package stage, so it cannot be read as a stale claim
   (`T010-IR-06`, closure evidence in §5.2).
10. **Mandatory scalars and artifact/planned-evidence presence are now enforced (`T010-IR-07`, `T010-IR-08`).**
    `_check_identity` guarded each mandatory per-unit scalar with `if value is not None`, so an omitted
    `family`, `kind`, `language`, `scope`, or `maturity` skipped the vocabulary check and `--verify` still
    passed; only `name`/`responsibility` were separately required, and only `maturity` was incidentally caught
    by the governance check. The loop now requires each of the five scalars to be present and a member of its
    closed set, reporting an absent or null value as `IDENTITY_INVALID` (3) with a message naming the field.
    The same function now requires every `artifact_paths` entry to carry a non-empty string `path`
    (`detailed-design.md` §3 line 84) and every unit's `planned_evidence` to be a non-empty string array
    (line 100), both `IDENTITY_INVALID` (3); previously a status-only artifact entry and an empty or deleted
    `planned_evidence` passed. Thirteen isolating fixtures (**NEG-08b..NEG-08f** on the non-`cpp`
    `XCOM-DU-026`, **NEG-08g..NEG-08k** on the `cpp` `XCOM-DU-006`, **NEG-08l**/`m` and **NEG-09b**) cover
    every path, and `verification-plan.md` NEG-08/CHK-03 are reconciled to the enforced contract. Closure
    evidence is in §5.3; no accepted requirement, check, or boundary is weakened.

## 3. Changed artifacts and symbols

| Artifact | Change | Symbols / structure |
| --- | --- | --- |
| `docs/engineering/xcom/t010/unit-design.json` | new | Canonical model, `schema_version = 1`: 13 closed vocabularies, `authorization_records`, `ref002`, `dependencies`, `coverage`, `doxygen_plan`, `counts`, `units` (30), `invariants` (14). |
| `docs/engineering/xcom/t010/design-units.md` | new | Deterministic projection of the model (identity, vocabularies, counts, REF-002, coverage, Doxygen plan, per-unit catalogues, invariants). |
| `scripts/validate_xcom_unit_design.py` | new; revision 2 loads the on-disk model bytes for the determinism check; revision 3 enforces the full thread-safety consistency predicate; revision 4 enforces every mandatory per-unit scalar and the artifact-path/`planned_evidence` presence rules | `Findings`, `serialize`, `project_markdown`, `_check_model_schema`, `_check_counts`, `_check_ordering`, `_check_identity`, `_check_ownership`, `_check_thread_safety`, `_check_bounds`, `_check_failure`, `_check_doxygen`, `_check_coverage`, `_check_governance`, `_check_dependencies`, `_check_binding`, `_check_paths`, `_check_determinism`, `_scan_public_safety`, `_parse_json`, `_load_json`, `run_checks`, `_negative_fixtures`, `_self_test`; `SYNCHRONIZING_THREAD_MODELS`/`UNSYNCHRONIZED_THREAD_MODELS`; CLI `--verify`, `--check-human`, `--self-test`. |
| `docs/engineering/xcom/task-ownership.json` | modified | Added `scripts/validate_xcom_unit_design.py` to `T-ENABLER` `paths_exclusive`; no other slice or field changed. |
| `docs/engineering/xcom/task-ownership.md` | modified | Deterministic projection regenerated from the updated JSON model. |
| `specs/007-xcom-core/tasks.md` | modified | T010 checkbox marked complete; no other task line changed. |
| `docs/engineering/xcom/t010/implementation.md` | new | This record. |

No production source, test, XDL asset, `proto/` definition, accepted ADR, accepted requirement, or accepted
contract was changed. The T010 candidate's affected product source paths are none; the product paths it
anchors are declared `established` only where baseline source already exists (or where the candidate itself
creates them) and `planned` otherwise.

## 4. Model content summary

- **Units (30).** 8 `CORE` (`XCOM-DU-001`–`008`), 3 `XDL` (`009`–`011`), 2 `OBS` (`012`–`013`), 5 `STIM`
  (`014`–`018`), 3 `GW` (`019`–`021`), 4 `INTG` (`022`–`025`), 5 `ENB` (`026`–`030`). `XCOM-DU-014`/`015`
  (time authority, permit/session lifecycle) are the only `implemented` units, bound to the accepted T025
  merge `4b01586b438a8587d231ee8828d896c206c06a96`; the remaining 17 `partial` units carry a reconciliation
  reason and 11 `allocated` units carry no revision.
- **Ownership/lifetime.** Six closed ownership models and eight closed lifetime models are used; only the
  exact issued handle mutates, closes, or replaces an active resource (`XCOM-DU-006`–`008`, `015`, `017`,
  `018`, `020`, `021`); `XCOM-DU-001`/`003`/`005`/`012` expose a bounded `view_lifetime`.
- **Thread-safety.** Every unit declares a closed model: `immutable-value` (7), `read-only-static` (2),
  `single-thread-owner` (1), `externally-synchronized` (3), `internally-synchronized` (6),
  `message-passing` (1), `offline-single-threaded` (10). Non-empty `shared_state` appears only on
  `internally-synchronized`/`externally-synchronized`/`message-passing` units; every other unit declares
  `shared_state = []` with `synchronization = null` (for example `XCOM-DU-008`'s per-route in-flight queue is
  owner-private state, not shared).
- **Bounds.** Every unit declares at least one finite bound (`configured = true`); only the bounded,
  non-production values `retry = 0` and `thread-count = 1` are fixed. The overflow policy set is exactly
  `["n/a"]` for units without a capacity/quota/depth/rate bound and a non-`n/a` policy set otherwise.
- **Failure semantics.** Every unit maps at least one classified condition to a closed outcome; unknown or
  indeterminate conditions never map to `accepted`/`delivered`; the durable journal unit declares
  `evidence-incomplete`.
- **Doxygen plan.** `DOX-01` records the admitted `Doxyfile`, the warning-as-error gate, the mandatory file
  block (`file`, `brief`, `ingroup`), the mandatory public aliases (`brief`, `ownership`, `lifetime`,
  `thread_safety`, `failure`), one group per family, the coverage rule, and gaps `DOX-GAP-01`–`03` with their
  owning tasks. All 19 `cpp` units declare `required = true` with equal public/documented element counts; the
  11 non-`cpp` units declare `required = false` with a reason.
- **Invariants (14).** `XCOM-UDI-01`–`14`; the pinned safety/contract invariants `XCOM-UDI-05`–`08` and
  `XCOM-UDI-13` are present with their exact `(kind, statement)` text so weakening one is a
  `GOVERNANCE_INVALID` failure.

## 5. Commands, results, and evidence

Environment: Python 3.13.13; repository checkout at baseline
`abb81681e0d844edaecbaf2843f1c2a7deb1e40f`.

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `python3 -m py_compile scripts/validate_xcom_unit_design.py` | 0 | Validator compiles. |
| 2 | `python3 scripts/validate_xcom_unit_design.py --verify` | 0 | `X-COM unit-design validation passed` (CHK-01..CHK-15). |
| 3 | `python3 scripts/validate_xcom_unit_design.py --check-human` | 0 | `design-units.md` is the exact deterministic projection (CHK-16). |
| 4 | `python3 scripts/validate_xcom_unit_design.py --self-test` | 0 | Positive fixture passes; NEG-01..NEG-46 (plus NEG-05b/18b/19b/24b/33b/34b, NEG-08b..NEG-08m, NEG-09b) and NEG-38/40 reject with their declared classes (CHK-17). |
| 5 | two `--verify` runs, stdout piped to `sha256sum` | 0 | Byte-identical stdout `f1426a71c0a714a3b5f305e22d77e0c9726c86066f3cf395dfe7167e13d978ce` (DET-01). |
| 6 | `python3 scripts/validate_xcom_task_ownership.py --verify` | 0 | T007 register valid with the added `T-ENABLER` path (CHK-18). |
| 7 | `python3 scripts/validate_xcom_task_ownership.py --check-human` | 0 | Ownership projection matches the updated JSON model. |
| 8 | `python3 scripts/validate_xcom_task_ownership.py --self-test` | 0 | T007 self-test still passes; no fixture weakened. |
| 9 | `git rev-parse abb8168…` | 0 | Prints the baseline SHA (BND-02). |
| 10 | `git diff --name-only abb8168… --` (after staging) | 0 | The 12-path candidate diff; no `src/`, `tests/`, `xdl/`, or `proto/` path (BND-01). |
| 11 | `git diff --check abb8168… --` | 0 | Clean (BND-06). |
| 12 | `git diff --name-only abb8168… -- Doxyfile scripts/check_doxygen.py` | 0 | Empty; T010 plans, it does not execute (BND-07). |
| 13 | validator `--verify` wall clock | 0 | Wall clock ≈ 0.12 s (BND-05, ≤ 60 s). |
| 14 | DET-04 probe: neutralise each of the sixteen check functions, run `--self-test` | nonzero (exit 9) for every probe | Every check is load-bearing; no check is decorative. |
| 15 | DET-03 probe: inject two defects (`XCOM-DU-002` unknown family + promoted REF-002 id), run twice | 3, 3 | Identical exit and byte-identical diagnostics (DET-03). |
| 16 | BND-03 probe: `_read_bounded` on a >1 MiB file | 14 | `IO_ERROR` over bound (BND-03). |
| 17 | ORD-01 probe: mechanically extract the declared ordering contract from `detailed-design.md` §3.5 and compare with the enforced sets | match | Both top-level id-sorted arrays and both stored-sorted nested-array sets are equal (ORD-01). |
| 18 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T010 abb8168…` | 0 | `{"ok": true, "task_id": "T010", "changed_paths": 12, "checks": []}` — the deterministic gate accepts the staged candidate (T010-SR-012). |
| 19 | `git ls-files --others --exclude-standard` | 0 | Untracked set at the reviewed candidate revision is exactly `docs/engineering/xcom/t010/internal-review.json`; the 12 candidate work products are tracked. `reports/xcom-queue/t010-package.json` is produced by the later package stage and was absent at review time, so it is not part of this observation. |

Self-test detail (command 4, condensed):

```
positive fixture: passed
NEG-01..NEG-05, NEG-05b: SCHEMA_INVALID (exit 2)
NEG-06..NEG-11, NEG-08b..NEG-08m, NEG-09b: IDENTITY_INVALID (exit 3)
NEG-12..NEG-16, NEG-20: OWNERSHIP_INVALID (exit 4)
NEG-17..NEG-19, NEG-18b, NEG-19b: THREAD_INVALID (exit 5)
NEG-21..NEG-24, NEG-24b: BOUNDS_INVALID (exit 6)
NEG-25..NEG-27: FAILURE_INVALID (exit 7)
NEG-28..NEG-30: DOXYGEN_INVALID (exit 8)
NEG-31..NEG-34, NEG-33b, NEG-34b: GOVERNANCE_INVALID (exit 9)
NEG-35..NEG-37, NEG-39, NEG-44..NEG-46: BINDING_INVALID (exit 10)
NEG-38: withheld dependency rejected with BINDING_INVALID (exit 10)
NEG-41: PUBLIC_SAFETY_INVALID (exit 12)
NEG-42, NEG-43: PATH_INVALID (exit 13)
NEG-40: tampered projection rejected with DETERMINISM_INVALID (exit 11)
X-COM unit-design self-test passed
```

DET-04 mutation probes (command 14): neutralising any one of `_check_model_schema`, `_check_counts`,
`_check_ordering`, `_check_identity`, `_check_ownership`, `_check_thread_safety`, `_check_bounds`,
`_check_failure`, `_check_doxygen`, `_check_coverage`, `_check_governance`, `_check_binding`,
`_check_dependencies`, `_check_paths`, `_check_determinism`, or `_scan_public_safety` makes the self-test
exit nonzero (exit 9), so each of the sixteen checks is load-bearing.

Artifact identity at this candidate state:

| Artifact | sha256 | Bytes |
| --- | --- | ---: |
| `docs/engineering/xcom/t010/requirements.md` | `bf0fad94d4041f47a7ec8eb188b9264747175c38da4cd3e00e0337b238c979a9` | — |
| `docs/engineering/xcom/t010/architecture.md` | `315d0f20e7dc15d8bb475c88c15acfb01ebb0874df65c923e658e9ea806d9bfe` | — |
| `docs/engineering/xcom/t010/detailed-design.md` | `7b09102513c3294caf551a1287e6890c510eb63a7fd35bb438a85e54b44a7113` | — |
| `docs/engineering/xcom/t010/unit-specifications.md` | `935ae0460a1da8da6233c122aab0defab51cb3dc4167f9ca15235862478eebc6` | — |
| `docs/engineering/xcom/t010/verification-plan.md` | `8677231a314dbbdaf0537f72f14fb711f9e32d890955bdb36986f4e47859a14b` | — |
| `docs/engineering/xcom/t010/unit-design.json` | `0b5e446c8cb8f3933130fbc58b43c4b0493177bd5941f9af42a6fbd94d1e88f3` | 106655 |
| `docs/engineering/xcom/t010/design-units.md` | `afb49dd8473b53c56ae3108cca2a61320e29badb9e4d38b0a5907fdf4ff4bca4` | 68839 |
| `scripts/validate_xcom_unit_design.py` | `4342ce2cc35e2b7ab73dfa2479d62b8a30dd59505acc7375fe1789e3a84025ae` | — |
| `docs/engineering/xcom/task-ownership.json` | `65797ca1364ceb4ee1af4aef4b115d37f24b5435c8db0d58137793e87bde1ebe` | — |
| `docs/engineering/xcom/task-ownership.md` | `c11a6b2760deec24e1654845a22a8320ff5fc4d7d553869f630566d12cf3b7e7` | — |
| `specs/007-xcom-core/tasks.md` | `8629abe2e16e24d7080987bbbad3f5dd19e68e642c4985cf1122426a04b22b58` | — |

Hashes are bound to this candidate state; the deterministic gate re-runs after the checkbox update and its
output is retained by the workflow. A successor candidate (for example a repair) must record its own exact
revision and repeat the affected checks.

### 5.1 Revision-2 repair closure evidence

The four internal-review findings were closed in this revision. Every affected check was repeated on the
repaired candidate; the commands and observed results are recorded here and bound to the revision-2 hashes.

| # | Finding | Command / inspection | Observed |
| ---: | --- | --- | --- |
| 20 | — (candidate) | `python3 -m py_compile scripts/validate_xcom_unit_design.py` | exit 0 |
| 21 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --verify` | exit 0, `X-COM unit-design validation passed` |
| 22 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --check-human` | exit 0, `X-COM unit-design validation passed` |
| 23 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --self-test` | exit 0; positive fixture and NEG-01..NEG-46 (plus NEG-05b/24b/33b/34b, NEG-38, NEG-40) at their declared classes |
| 24 | — (candidate) | two `--verify` runs piped to `sha256sum` | byte-identical `f1426a71c0a714a3b5f305e22d77e0c9726c86066f3cf395dfe7167e13d978ce` (DET-01) |
| 25 | `T010-IR-01` | parse `enforcing_check` for `XCOM-UDI-05`/`06`/`07`/`08`/`13` from `unit-design.json` and diff against the `detailed-design.md` §11 rows | equal: `CHK-06`, `CHK-06`, `CHK-07`, `CHK-08`, `CHK-11`; §11 names only `GOVERNANCE_INVALID` (9) for a weakened pinned invariant |
| 26 | `T010-IR-02` | compare the `XCOM-DU-013` saturation entry with `detailed-design.md` §8–§9 | the entry is `drop-newest` → `rejected`; §9 states the `coalesce` (merged) and `lossless-backpressure` (producer backpressure) outcomes explicitly, so model and catalogue agree |
| 27 | `T010-IR-03` | extract the check-function names from `unit-specifications.md` §`U-VALIDATE` and confirm each is defined by `grep -n '^def _check' scripts/validate_xcom_unit_design.py` | no named-but-undefined function; the list now names `_check_counts` and `_check_ownership` and no longer names `_check_maturity` |
| 28 | `T010-IR-04` | replace the on-disk `unit-design.json` with a whitespace-altered copy, run `--verify` and `--check-human`, then restore | both exit 11 `DETERMINISM_INVALID`; the restored canonical model exits 0 |
| 29 | — (regression) | `python3 scripts/validate_xcom_task_ownership.py --verify`, `--check-human`, `--self-test` | exit 0 each; the T007 register and projection are unchanged |
| 30 | — (candidate) | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T010 abb8168…` | `{"ok": true, "task_id": "T010", "changed_paths": 12, "checks": []}` |

No accepted requirement, check, contract, test, or boundary was weakened: the repairs only make the model,
projection, design catalogue, unit specification, and validator agree, and they make an already-declared
determinism check reachable. The `T010-IR-01`..`IR-04` findings from revision 1 are closed and the successor
review is recorded separately in a revision-2 `internal-review.json`.

### 5.2 Revision-3 repair closure evidence

The two internal-review findings (`T010-IR-05`, `T010-IR-06`) were closed in this revision. Every affected
check was repeated on the repaired candidate and the hashes above are the revision-3 values. The commands
and observed results are recorded here.

| # | Finding | Command / inspection | Observed |
| ---: | --- | --- | --- |
| 31 | — (candidate) | `python3 -m py_compile scripts/validate_xcom_unit_design.py` | exit 0 |
| 32 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --verify` | exit 0, `X-COM unit-design validation passed` |
| 33 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --check-human` | exit 0, `X-COM unit-design validation passed` (the projection was regenerated from the corrected model) |
| 34 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --self-test` | exit 0; positive fixture and NEG-01..NEG-46 (plus NEG-05b/18b/19b/24b/33b/34b, NEG-38, NEG-40) at their declared classes |
| 35 | — (candidate) | two `--verify` runs piped to `sha256sum` | byte-identical `f1426a71c0a714a3b5f305e22d77e0c9726c86066f3cf395dfe7167e13d978ce` (DET-01) |
| 36 | `T010-IR-05` | in-memory model copy: `XCOM-DU-008` `single-thread-owner` with `shared_state = ["per-route in-flight queue"]`, run `run_checks` | `THREAD_INVALID` (5): `XCOM-DU-008: model single-thread-owner cannot declare shared mutable state` |
| 37 | `T010-IR-05` | in-memory model copy: `XCOM-DU-001` `immutable-value` with a non-null `synchronization`, run `run_checks` | `THREAD_INVALID` (5): `XCOM-DU-001: model immutable-value must declare synchronization = null` |
| 38 | `T010-IR-05` | DET-04 probe: neutralise `_check_thread_safety`, run the self-test | self-test exits nonzero (9); the new predicate is load-bearing |
| 39 | `T010-IR-05` | parse `XCOM-DU-008` from `unit-design.json` and diff against `detailed-design.md` §3.1/§7, `verification-plan.md` CHK-05, and `unit-specifications.md` §`U-THREAD`/§6 | model declares `single-thread-owner`, `shared_state = []`, `synchronization = null`; every catalogue states the enforced predicate; `XCOM-UDI-04` is strengthened, not weakened |
| 40 | `T010-IR-06` | `git ls-files --others --exclude-standard` at the candidate revision | exactly `docs/engineering/xcom/t010/internal-review.json`; `reports/xcom-queue/t010-package.json` absent (produced by the later package stage) — matches the corrected command 19 |
| 41 | — (regression) | `python3 scripts/validate_xcom_task_ownership.py --verify`, `--check-human`, `--self-test` | exit 0 each; the T007 register and projection are unchanged |
| 42 | — (candidate) | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T010 abb8168…` | `{"ok": true, "task_id": "T010", "changed_paths": 12, "checks": []}` |

No accepted requirement, check, contract, test, or boundary was weakened: `XCOM-UDI-04` and CHK-05 are
strengthened (a previously unenforced direction is now enforced and a unit that contradicted the rule is
corrected), two isolating negative fixtures were added, and the stale untracked-set claim is corrected to the
observed state. The `T010-IR-05`..`IR-06` findings are closed and the successor review is recorded separately
in the successor `internal-review.json`.

### 5.3 Revision-4 repair closure evidence

The two internal-review findings (`T010-IR-07`, `T010-IR-08`) were closed in this revision. Every affected
check was repeated on the repaired candidate; the `verification-plan.md` and validator hashes above are the
revision-4 values. The commands and observed results are recorded here.

| # | Finding | Command / inspection | Observed |
| ---: | --- | --- | --- |
| 43 | — (candidate) | `python3 -m py_compile scripts/validate_xcom_unit_design.py` | exit 0 |
| 44 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --verify` | exit 0, `X-COM unit-design validation passed` |
| 45 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --check-human` | exit 0, `X-COM unit-design validation passed` |
| 46 | — (candidate) | `python3 scripts/validate_xcom_unit_design.py --self-test` | exit 0; positive fixture, the original NEG-01..NEG-46 set, and the new NEG-08b..NEG-08m/09b fixtures reject at their declared classes |
| 47 | — (candidate) | two `--verify` runs piped to `sha256sum` | byte-identical `f1426a71c0a714a3b5f305e22d77e0c9726c86066f3cf395dfe7167e13d978ce` (DET-01) |
| 48 | `T010-IR-07` | for each of family/kind/language/scope/maturity, delete the field from `XCOM-DU-026` (non-`cpp`) and `XCOM-DU-006` (`cpp`) and run `run_checks` | each returns `IDENTITY_INVALID` (3) with a message naming the missing field, e.g. `XCOM-DU-026: missing mandatory field kind` and `XCOM-DU-006: missing mandatory field scope`; fixtures NEG-08b..NEG-08k |
| 49 | `T010-IR-08` | in-memory copy: `XCOM-DU-002` `planned_evidence = []`, then `del planned_evidence`, run `run_checks` | each returns `IDENTITY_INVALID` (3): `XCOM-DU-002: planned_evidence must be a non-empty string array`; fixtures NEG-08l/NEG-08m |
| 50 | `T010-IR-08` | in-memory copy: `XCOM-DU-002` `artifact_paths = [{"status": "established"}]`, run `run_checks` | `IDENTITY_INVALID` (3): `XCOM-DU-002: every artifact path entry must carry a non-empty string path`; fixture NEG-09b |
| 51 | `T010-IR-07`/`IR-08` | DET-04 probe: neutralise `_check_identity`, run the self-test | self-test exits nonzero (9); the strengthened predicate is load-bearing |
| 52 | `T010-IR-07`/`IR-08` | compare `verification-plan.md` NEG-08/CHK-03 and `detailed-design.md` §3 line 84/line 100/§12.1 with the enforced checks | the declared class is `IDENTITY_INVALID` (3); NEG-08b..NEG-08m and NEG-09b exercise exactly those paths |
| 53 | — (regression) | `python3 scripts/validate_xcom_task_ownership.py --verify`, `--check-human`, `--self-test` | exit 0 each; the T007 register and projection are unchanged |
| 54 | — (candidate) | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T010 abb8168…` | `{"ok": true, "task_id": "T010", "changed_paths": 12, "checks": []}` |

No accepted requirement, check, contract, test, or boundary was weakened: `T010-SR-002`/CHK-03 are
strengthened (a previously skipped mandatory-field branch and two unenforced presence rules are now enforced),
thirteen isolating negative fixtures were added, and `verification-plan.md` NEG-08/CHK-03 are reconciled to the
enforced contract. The `T010-IR-07`..`IR-08` findings are closed and the successor review is recorded
separately in the successor `internal-review.json`.

## 6. Requirement-to-evidence trace

| Requirement | Checks / evidence |
| --- | --- |
| T010-SR-001 | CHK-01, CHK-02, CHK-16, ORD-01, DET-01, DET-02 (commands 2, 3, 5, 17, and `--check-human`) |
| T010-SR-002 | CHK-03, CHK-11, CHK-15, NEG-06..NEG-09 (incl. NEG-08b..NEG-08m, NEG-09b), NEG-42, NEG-43 (commands 2, 4) |
| T010-SR-003 | CHK-04, NEG-12..NEG-16, NEG-20 (commands 2, 4) |
| T010-SR-004 | CHK-05, NEG-10, NEG-17..NEG-19, NEG-18b, NEG-19b (commands 2, 4) |
| T010-SR-005 | CHK-06, NEG-21..NEG-24, NEG-24b (commands 2, 4) |
| T010-SR-006 | CHK-07, NEG-11, NEG-25..NEG-27 (commands 2, 4) |
| T010-SR-007 | CHK-08, NEG-28..NEG-30 (commands 2, 4) |
| T010-SR-008 | CHK-09, CHK-10, NEG-44, NEG-46 (commands 2, 4) |
| T010-SR-009 | CHK-10, NEG-37, NEG-39, NEG-45, NEG-46 (commands 2, 4) |
| T010-SR-010 | CHK-11, NEG-31..NEG-34, NEG-33b, NEG-34b (commands 2, 4) |
| T010-SR-011 | CHK-12, CHK-13, CHK-15, NEG-35, NEG-36, NEG-38, NEG-42, NEG-43 (commands 2, 4, 9) |
| T010-SR-012 | CHK-18, BND-01, BND-06, BND-07, deterministic gate (commands 10, 11, 12, 18) |
| T010-SR-013 | CHK-14, NEG-41 (commands 2, 4) |
| T010-SR-014 | CHK-02, CHK-16, CHK-17, DET-01..DET-04, BND-03..BND-05, `--self-test` (commands 1, 3, 4, 5, 13, 14, 15, 16) |

REF-002: no direct communication requirement `XVE-SYS-0139`–`0158` is implemented, promoted, or unlinked.
`ref002.disposition = "unchanged"` with an empty promoted set; the authoritative table remains
`specs/007-xcom-core/reference-traceability.md`.

## 7. Limitations and honesty notes

1. **No acceptance or integration claim.** T010 implements and locally verifies only its own bounded work
   products. It does not accept or integrate any candidate, including itself, and it claims no external
   review or user acceptance. The internal review is a separate read-only stage; external Codex review is
   deferred until the `xcom-t007-t010-t017-t020` backlog completes.
2. **Reconciliation is recorded, not resolved.** `T012`–`T016` and `T021`–`T024` coverage stays
   `partial`/`unreconciled`; the accepted `T025` slice is the only coverage bound to an accepted exact
   revision. `T007`–`T009` and `T011` stay `partial` until user acceptance.
3. **Planned anchors.** Every product path the model anchors other than baseline-present (or
   candidate-created) artifacts is declared `planned`; a planned path is a traceability intent, not
   implementation evidence.
4. **Doxygen is planned, not executed.** T010 declares the Doxygen plan, the mandatory tags, and the strict
   configuration gap `DOX-GAP-01`; it changes no `Doxyfile`, runs no generator, and asserts no warning-free
   result. The declared public/documented element counts are a structural consistency claim, not proof that
   documentation exists.
5. **Public-safety scan scope.** The validator mechanically detects absolute host paths, private IPv4
   ranges, credential assignment tokens, private-key markers, and unbounded base64-like tokens. The
   non-mechanical classes (proprietary source excerpts, unrestricted payloads) are assessed by the review
   stage; inspection finds none in the model, projection, or output.
6. **No runtime evidence.** T010 has no runtime artifact, so no performance, availability, or concurrency
   claim is made; the validator is offline, single-threaded, and bounded (≤ 1 MiB per file, ≤ 4 MiB total,
   no network or subprocess, wall clock well under 60 s). The designed units' concurrency and bounds are
   design content verified structurally by CHK-05/CHK-06, not measured.
7. **No production numeric bound is fixed.** Every bound is `configured = true`; only the bounded
   non-production values `retry = 0` and `thread-count = 1` are fixed. Capacity, rate, quota, depth, byte,
   deadline, and timeout values come from the activation plan or unit configuration at runtime (FR-007).
8. **Environment identity is recorded, not pinned by T010.** Compiler/dependency admission with hashes and
   licenses is T011's deliverable; this record names only the Python interpreter used.
9. **Work-product boundary.** The candidate diff contains no `src/`, `tests/`, `xdl/`, or `proto/` path and
   changes no `Doxyfile`/CMake/build file, accepted ADR, accepted contract, accepted requirement, or existing
   test.
