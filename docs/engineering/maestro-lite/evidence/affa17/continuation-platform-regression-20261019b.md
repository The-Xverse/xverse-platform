# Broader platform regression triaged; successor b terminal; CAPA43/245

2026-10-20 (UTC). Goal ACTIVE. This checkpoint supersedes the live-run status in
continuation-integrated-terminal-20261019b.md. No production, test, XDL or
environment change in this checkpoint. Stable parent
46e0ebfd332dd833322d764191a7cfe1e008bec1 and dirty increment17 are unchanged.
Work performed by Claude from CLAUDE_HANDOVER_2026-10-19.md in the thesis repository.

## Original run a: terminal, immutable

Original exec33408, driver1667036, pytest1669996, nested child1678188. Terminal
returncode1 after2979.15s: **17 failed/2063 passed/0 errors**, no outer timeout,
all1903 frozen inputs unchanged, descendants gone. Receipt SHA256
b66dd19b49338b2c3a0bd5445d6eecb063f6a674797952a7d263c9b852f06d36; log
2251bb89fefd86e2b6806cbd9235c602f23cfd95769ef0f766172c3fa57ef735; triage
`platform-regression-20261019a/failure-triage.json`
d4ad64d9434c8a9c9d419ce90e4deee30051a837597a144a843006cbeb6a360a (tool
triage-platform-regression-20261019a.py,
4730f4b49fcd11e21894915b70b14941d391242b14cdb41c8018c4842b39feb1).

Failures, each classified individually (finding359):

| Class | Count | Evidence |
| --- | --- | --- |
| Argus packaging/installed-wheel cases with exact `No module named build` traceback | 13 | finding357 confirmed; verification-environment omission |
| Argus nested platform regression case (child12 failed/1770 passed/14 errors) | 1 | only child's last4000 chars retained; errors hypothesised as shared-receipt collisions (260 mechanism) |
| Maestro ML-PERSIST-TIMEOUT (health_scans0, lease_renewals2) | 3 | 222 exact recurrence (active restart leaf), 318 sibling (beyond-active-recovery), W01 stream seeded-flush-persistent |

## Successor run b: terminal, environment-only variation

Driver `verify-platform-regression-20261019b.py` (PID2354172, pytest2355112),
Python /tmp/maestro-lite-platform-regression-target-20261019b (build1.6.1,
hatchling1.32.4, pytest9.0.3, candidate wheel; preparation receipt
0ee24c73d11f73a9e0aa7e33647d1723f4fc04ec8f88c909899b8ff0b979204d bound by
preflight.json). Snapshot byte-identical to run a (1903 files, manifest
3c2d860be3f964a38e03d608a979293deeb09f2e6f396186f5b6ee2fac084198). Outer
deadline7200s, documented. Terminal returncode1 after2886.60s:
**3 failed/2077 passed/0 errors**, no timeout, inputs unchanged. Receipt
c4c628ca0155673a1bdab92284802789d50f910684292c1f21353015503d911b; log
5187cf0d7752991161d30479fb02c499347c3f50c25400209f847d1bdfeba5fc; triage
3f49200acaebc460a6d324e7f35f5a389af8d6efebe769e2eec4a120407264a7.

- All13 build-signature cases pass; no b failure carries that signature.
- Nested case fails again: child1782 passed/0 failed/**14 errors**, identical
  error node IDs to run a (composed_issuer_loss ×6, composed_persistence_termination
  ×6, runtime_issuer_loss ×2). The child's12 run-a failures did not recur.
- Two different Maestro cases fail: transitive cohort[cleaned-leaf]
  (ML-SCHEDULE-TEARDOWN-INCOMPLETE after a teardown ML-PERSIST-TIMEOUT) and
  dispatcher full five-phase (ML-PERSIST-TIMEOUT, lease_renewals0). The three
  run-a Maestro timeouts did not recur. Finding360 retains all of this as UNKNOWN.

Neither run is a whole-platform pass. Run b supplies the required packaging/
installed-wheel evidence that the original environment could not. Both evidence
directories, logs, receipts, harness receipts and archives are retained unchanged.

## CAPA successor: capa-20261019-platform-regression

`register.json` SHA256
cc1cca7748451b6ae3196e3fb40a33122ee16aa4ed5368854dd7c828898cab49,
**43 records/245 bindings**, parent capa-20261019-reviewer-shape (40/216,
c04badb5…b1b3) with all216 parent bindings preserved
(`parent-preservation.json` 68de54b2…35e7; `verification-recheck.json`
99023e78…9526). Builder build-capa-20261019-platform-regression.py
7789d572…ecfaa. Additions:

- ML-CAPA-357 FIX_CANDIDATE/HYPOTHESIS: missing build tooling in driver a's
  environment; correction = separate preflight-bound environment and successor
  driver; prevention = same13 node IDs absent in b. Effectiveness NOT_DEMONSTRATED.
- ML-CAPA-359 UNRESOLVED/UNKNOWN: five nonrecurring Maestro first-RPC deadline
  expiries across runs a/b (three in a, two in b).
- ML-CAPA-359-CHILD UNRESOLVED/UNKNOWN: nested child errors/failures; receipt-
  namespace collision is a hypothesis with local file evidence only.
- ML-CAPA-222 and ML-CAPA-318: additive recurrence references (incident
  review:359), identities unchanged.

Unknown causes now:135,222,286,287,318,324,330,331,332,337,359,359-CHILD. All
effectiveness NOT_DEMONSTRATED. Manual OBSERVE_ONLY; no automatic CAPA, no025
integration, no acceptance, no scientific result.

## Proposed next harness successor (not executed, needs its own finding)

To let the accepted nested case run its child with the same per-module receipt
namespace as the outer session without modifying accepted tests: a successor
receipt plugin would also export a child receipt root
(`MAESTRO_FULL_RECEIPT_ROOT=<harness>/<module>/nested`) and the child would load
the plugin through `PYTEST_PLUGINS`, which pytest9.0.3 honours even with
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` (config/__init__.py consider_env). Constraint
found read-only: the Argus consumer/validation cases spawn pytest with
`PYTHONPATH=<target>` only, so a plugin named in `PYTEST_PLUGINS` must be
importable from site-packages, i.e. a new prepared environment c with the plugin
installed and a new preparation receipt. This changes the verification harness
only; it must be recorded as a finding and a separate run before any claim.
If, after that, the child still reports errors, the hypothesis is refuted.

## Repository boundaries and gates

Thesis:/home/jefferson/distributed_safety_critical_thesis, branch
agent/synchronize-thesis-obsidian-notes, HEAD d97fdd1 (upstream equal; fresh
fetch at session start, no incoming note change, no pull). Canonical note SHA256
01fcce48696c30d8e8cf46fa60fcf28eae9f45c19a8885df86528832e18b4abb unchanged;
no canonical-note edit made or authorized.

Candidate:/home/jefferson/xverse-platform-worktrees/maestro-lite-affa-20261018,
branch candidate/maestro-lite-affa17-20261018, no upstream, HEAD46e0ebfd; main
untouched at c2997c0f. No commit was created: this checkpoint is verification
evidence and documentation over the unfinished, uncommitted increment17 sources,
not a stable increment. Preserve all dirty work. Pending author decisions remain:
source-parent projection v2 approval; no acceptance, M1, merge, factory or
scientific authorization is implied. New factory runs only via
/home/jefferson/x-verse_fabric/automation/factory_start.py; these local pytest
runs are not factory runs.

Next action: author decides whether to pursue the harness successor c for the
nested child before continuing the full024 runtime/evidence/admission matrices;
either way, continue024 scope on the candidate, record findings before repairs,
and commit only a genuinely stable increment17.
