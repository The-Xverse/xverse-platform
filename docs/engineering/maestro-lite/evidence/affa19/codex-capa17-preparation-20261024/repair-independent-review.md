# Independent CAPA17 guard repair review (2026-10-24)

**Verdict: PASS for the staged source repair; no remaining source blocker found for R17p-1/R17p-2.**
This is not an executed builder, verified CAPA register, actual DV12 decision, acceptance or merge. The actual
official-DV12 wrapper/receipt and byte-identical final installation remain to be checked in the authorized workflow.
Sol at high reasoning is recommended for that final evidence/installation review; no model switch is claimed.

Reviewed only the prospective files beside this review, before installation into affa19:

- `repair-design.md`, SHA256 `15f3f7b7e0cfb3760ac016c5cae572dada4ced8da1dbed95e2233ac34b30c3b1`.
- `build-capa-20261024-simtime-step17.py`, SHA256
  `407a4fabb65c41235e816f0053fae977c06e86e1eb963f04d629eb7239a4b645`.

The intended final path remains `<candidate>/docs/engineering/maestro-lite/evidence/affa19/`, where
`BASE.parents[4]` identifies the relocated candidate root. The staging directory is deliberately not an execution
location and was not used as one. No original platform/thesis files or Git state were written. All new data and
TMPDIR remained on loop10 under the coordinator's current storage constraint.

## R17p-1: current status and historical preservation, resolved in source

The builder deepcopies the exact parent, explicitly resets only the current child's root accepted/merged to false
and asserts both false before register serialization. The new increment metadata and printed summary also remain
false. Historical nested approvals remain in the parent copy; old records, action plans and evidence bindings are
still checked for exact preservation. This removes the contradictory inherited root-status claim without erasing
past approvals or creating a new one. Parent SHA/count guards and observe-only limits remain unchanged.

## R17p-2: exact candidate/run and genuine execution association, resolved in source

The new guards go beyond the prior free-standing true flag:

- Wheel, configuration, gate candidate/run_head and collected count must agree with exact tested 4bed/3039.
  Configuration must state installed-equals-frozen-src and wheel verification; archive fields agree, and the actual
  log digest must match the receipt. Gate blockers must be empty and its mode must be code.
- The actual official validator's current bytes must equal its tested Git blob. Its own source helpers are used
  for code identity and terminal summary counts. Both scope code digests must equal that tested identity, and
  actual summary/gate counts must be 3038 passed/1 skipped. The existing unrelated accepted attempt-h verdict has
  a different candidate/run_head and 2958 collection count and is now refused by those exact guards.
- A separate execution receipt is required: exact integer return code 0, tested candidate/scope, resolved repo/run,
  matching input hashes before and after, exact gate-output hash and exact official command. The inputs include
  configuration, wheel receipt/log, G4, allowlist and validator. This supplies an auditable association to the actual
  run bytes when genuinely captured; the builder does not invent that receipt merely because a gate says true.
  Its absent receipt remains an execution gate.
- New configuration/execution/validator evidence bindings retain that association. Current bound source/test/script/
  ADR bytes are additionally compared with fixed tested Git blobs, while review/evidence-only additions retain
  separate identities. The three-file collection patch still comes from the specified fixed base→tested Git diff.

The validator is loaded only in the future builder execution to obtain its pure helpers; this reviewer did not
import/run that validator, invoke its gate/checker, compute its code/archive digest or execute any builder body.
The future official command is expected to perform the authoritative archive/log/skip/G4 checks. The new execution
receipt is a trusted engineering observation, not cryptographic attestation; actual capture must be inspected.

## Narrow controls and current evidence state

AST parsing passed. Six small in-memory guard-control groups exercised only extracted pure assertion expressions:
matching candidate/count, the real unrelated accepted gate's rejection, matching input association and changed
before/after hashes; explicit root-false assignments were also checked. These were not a synthetic full-builder or
DV12 execution. No CAPA output directory/register was generated.

Read-only inspection of actual attempt-j configuration/receipt confirms the expected fields exist: both name
4bedba9efd21c750b84322e5fc265eb6adf86cc9 and collected 3039, agree on archive
0bc48cd094e0c98d8a300845afe94528f5978e1c34ecbbd9aece23eeede87382, and the wheel receipt declares return code 0,
passed_exit_status=true, outer_timeout=false and descendant_cleanup_unknown=false. Reading only the final 2048 log
bytes shows the expected terminal summary: 3038 passed, 1 skipped, 39 subtests passed. This is field/tail inspection,
not independent full-log hashing or official acceptance of that result. At this review, both
`dv12-gate-verdict.json` and `dv12-execution-receipt.json` remain absent, so no actual DV12 success is claimed.

The summary guard uses the log's literal last split line whereas the official checker filters blank lines; the
actual attempt-j tail has the terminal summary at that literal position, so no current mismatch/blocker exists.
The exact receipt command uses resolved physical candidate/run/input paths; the forthcoming wrapper must capture
those same command strings rather than silently using a different logical alias or interpreter. The wrapper and
actual receipt have not yet been reviewed or executed by this reviewer.

## Remaining gates and preserved observation boundary

Install only the reviewed bytes at the documented final affa19 location and check their installed hash. Obtain
the actual official DV12 command/result and genuinely captured input/output receipt through the coordinator's
authorized serialized workflow; inspect that association before CAPA generation. A source-review pass does not
replace missing actual execution evidence, and a prepared receipt schema is not an execution result.

The new observation remains TRIAGED/HYPOTHESIS, reproducer confirmation pending, null observation-window end,
NOT_DEMONSTRATED effectiveness and no historical cause/effectiveness closure. The source-inspected shared
collection-continuity limitation is still distinguished from defects repaired within the unaccepted simulator-
time candidate and from attempt-i's unrelated socket-test path failure. No additional claim is introduced here.
After eventual generation, inspect the new row and exact preserved content, then run the official schema/evidence
verifier and parent-preservation checker when the slot is available. Acceptance and isolated main delivery remain
separate explicit delegated steps.

**Not performed:** no Git command, original platform/thesis write, all-757 evidence hash pass, checker/verifier,
builder/CAPA generation, framework, test runner or heavy workload. Only the two staged preparation files, small
existing metadata/validator source and a 2048-byte log tail were read; this adjacent review is the only new artifact.
