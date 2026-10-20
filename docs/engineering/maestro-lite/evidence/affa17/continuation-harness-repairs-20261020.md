# Harness and fixture repairs verified; runtime lane integrated; run f live

2026-10-20 (UTC). Goal ACTIVE. Supersedes continuation-platform-regression-20261019b.md.
Author instruction 2026-10-20: "fix all those issues first, after that continue the
implementation of the remaining tasks". Work by Claude in the isolated candidate.
Stable parent 46e0ebfd332dd833322d764191a7cfe1e008bec1; increment17 remains dirty; no commit.

## Runs a–e, each retained unchanged (findings 357–365)

| Run | Variation | Outer result | Nested child |
| --- | --- | --- | --- |
| a (19a) | original environment, no build tools | 17 failed/2063 passed | 12 failed/14 errors |
| b (19b) | build-capable environment | 3 failed/2077 passed | 0 failed/14 errors |
| c (20c) | + receipt-namespace plugin by name (child gets per-module dirs) | 4 failed/2076 passed | 1 failed/0 errors |
| d (20d) | + fixture window repair (over-reached onto literal 20 s windows) | 25 failed/2055 passed | 24 failed |
| e (20e) | narrowed repair + private basetemp on tmpfs | **1 failed/2079 passed** (only the nested case) | 2 failed (child still on ext4) |

Fixed with local evidence: missing build tooling (357); nested-child receipt collisions
(359-CHILD); the CAPA-222 squeeze (362/364: the 4.8 s fixture window reserves restart/recovery
budgets, 5.8 s for test_active_restart; literal 20 s windows unchanged). Refuted: collector
pauses (max 0.068 s). Supported, not proven: fsync stalls on the 90%-full shared ext4 root
(9 spikes/55 min, worst 1.11 s; one 1.04 s spike overlapped a 0.74 s init stall; tmpfs
outer session clean while its ext4 child expired twice). Harness mitigation tracked as
ML-CAPA-364 with declared fidelity change; product budgets and durability logic unchanged.

CAPA successor `capa-20261020-harness-repairs/register.json` SHA256
bfe07733e1e9842180e9915d68690ee3285423ab8618398042a8623742298d38, **44 records/275
bindings**, parent capa-20261019-platform-regression (43/245) fully preserved. States:
222, 357, 359-CHILD, 364 FIX_CANDIDATE/HYPOTHESIS; 359 UNRESOLVED/UNKNOWN; ten unknown
causes remain (135, 286, 287, 318, 324, 330, 331, 332, 337, 359). All effectiveness
NOT_DEMONSTRATED. Manual OBSERVE_ONLY; no automatic CAPA, no 025 integration.

Harness tools retained in this directory: `maestro_receipt_namespace.py` (v2),
`maestro_receipt_namespace_v3.py` (GC log), environment builders c/d, drivers c–f,
`triage-platform-regression-20261019a.py`, `correlate-stalls-fsync-20261020.py`,
`build-capa-20261020-harness-repairs.py`, `build-runtime-lane-traceability-20261020.py`.
Known harness defects, documented and superseded: driver d probe quoting; driver e probe
without summary on termination; driver start message prints a literal count.

## Runtime lane (finding 365)

`tests/thesis_lite/maestro/test_runtime_actual.py` (SHA
00abcd8db4dd7934d5f9938db744c2e0d7206ee2cdbb84335ed35797412cbbd9) implements seven of
the nine `RUNTIME_CASES` identifiers against the current composition with real children,
the unrelated heartbeat sentinel and JSON receipts; `test_atomic_release_cancel_stage`
and `test_pre_handle_crash_survival` remain in test_composed_authority_interruptions.
Bounded evidence `runtime-lane-20261020a/`: source 17 passed, installed wheel 17 passed,
seven receipts per phase (receipt 1985355134306cc08c9e24bda62591e6282296630402922417651b81e6f78e80).
Partial trace `runtime-lane-partial-traceability.json`
(cb8f6eba9afe3ba90aa072346a2142d1545feb45d7c3417c17e486bb1bec1178) binds the nine
identifiers to ML-SR-009/010/011/012/013/024. See ../../runtime-lane.md. Not met: IR-ML3-04
activation prerequisites, M1 admission, crash-point matrices, acceptance.

## Run f terminal; crash-point controls integrated; run g live (finding 366)

Run f (whole session under TMPDIR on tmpfs, 2088 collected): **1 failed/2087 passed**, the
lane's 8 cases passing inside the full suite; the only failure is the nested case whose
child reports 1 failed/1803 passed (transitive cohort, run-terminal 0.300 s budget
expired). Diagnosis: the transitive fixture's `operation_seconds=.3` is a third fixture
margin mechanism (terminal statements take ~0.13 s, p99 0.22 s, usage p99 0.74); repaired
to 0.5 s like the other fixtures and verified in run g. Probe files of e/f are empty
because pytest recreates the basetemp (zero spikes on tmpfs; summary lost at unlink);
driver g keeps the probe outside the basetemp. CAPA successor
`capa-20261020-run-f/register.json` 07e1051c606dee6667bdb16282ee28590d88b817cd2b0230bfb9912c3199ac23
(44 records/284 bindings, parent 44/275 preserved) adds run f as a prevention observation.

Crash-point matrix: `tests/thesis_lite/maestro/test_composed_post_release_loss.py`
(0aa29d007bedb9b14f5299a199a894281f556ac4c5360d26d15ad464972c5dee) closes the two gaps
(post-Release authority/storage loss; spawn-time storage loss) with hand-authored
expectations; bounded evidence `crash-matrix-20261020a/` source 15 passed, wheel 15 passed
(receipt 0a454ac42423b54b939e9f0aa817f773e07effb1d16a66812fcdf9db4962efdf). See
../../crash-point-matrix.md for the remaining items. Endpoint reconciliation gap recorded in
../../endpoint-reconciliation-gap.md (7 of 62 declared endpoints resolve; author-gated
successor required).

## Run g terminal: transitive budget repair REJECTED at admission (finding 367)

Run g (2094 collected, transitive `operation_seconds .3 -> .5`): 25 failed/2069 passed; all
24 transitive cases fail at `admit_schedule` with ML-SCHEDULE-HEALTH-CAPACITY because
period = cadence - n*op - (service_calls+1)*op must exceed n*op (holds at 0.3 s, fails at
0.5 s with 4 units and a 5 s cadence). The 0.3 s budget is forced by the cadence; a margin
change needs a cadence/scan redesign and is recorded as a proposal only. The edit is
reverted (test_shared_dispatcher.py SHA 8acc16222c2a5c3e478357054dab4f06e1b1d1c96c2055a838534eb58ce2fde8).
The six crash-point controls passed inside the full suite; the probe is fixed (7879
samples, 0 spikes on tmpfs). CAPA successor `capa-20261020-run-g/register.json`
d628a13c29433b55b881bc974e98a1b3a89e13644156dcc0cb6fae385804d37d (45 records/293
bindings, parent 44/284 preserved) adds ML-CAPA-366 as REJECTED with run g retained.

## Run h terminal: the baseline (finding 368)

Run h (reverted baseline, 2094 collected, TMPDIR on tmpfs): **1 failed/2093 passed**, zero
outer Maestro expiries for the third consecutive tmpfs run; lane and crash-point controls
pass inside the full suite. The only failure is the nested case: child 1 failed/1809
passed (test_schedule_worker native gate renewal, first occurrence, operation_seconds 0.1
fixture, tail only, UNKNOWN under 359). Probe terminal: 9898 samples, 0 spikes. CAPA
successor `capa-20261020-run-h/register.json` f563f188df02e10a1fd7a6a423dc6533a28327e836459e35f3913fcc44419a10 (45 records, parent run-g preserved).
No run is live at this handoff. Baseline configuration: environment d (build tools, plugin
v3), drivers f–h (TMPDIR on tmpfs, probe outside basetemp), fixture repairs 362/364
narrowed, transitive budget 0.3 s (forced by cadence), lane and crash-point modules.
Superseded live-run section for f follows for history.

## Run f (historical live section)

Driver `verify-platform-regression-20261020f.py`, pytest PID **421617**, environment d,
whole session under TMPDIR on tmpfs (child included), probe summary on SIGTERM, 2088
collected (2080 + the lane module), private basetemp
/dev/shm/maestro-platform-20261020f-private-8qclus68. Expected ~45 min. Terminal receipt:
`platform-regression-20261020f/source-receipt.json`. Then run the triage tool, correlate,
record finding 366, and extend the CAPA successor with f as a further prevention
observation (never overwrite the 44-record register).

## Remaining 024 scope and gates

Open: crash-point matrices from the unit specification (constructor/startup/active/crash),
complete 24/18/30/90 trace closure, IR-ML3-04 lane admission, whole-platform clean run on
persistent media (tmpfs is a declared harness choice, not a product property), separate
complete independent review, stable increment17 commit, author acceptance, main merge.
Source-parent projection v2 approval remains pending; no canonical-note edit, factory run,
scientific claim, acceptance or merge is implied. New factory runs only through
/home/jefferson/x-verse_fabric/automation/factory_start.py.

Thesis: /home/jefferson/distributed_safety_critical_thesis, branch
agent/synchronize-thesis-obsidian-notes, HEAD d97fdd1, note SHA
01fcce48696c30d8e8cf46fa60fcf28eae9f45c19a8885df86528832e18b4abb unchanged.
