# Combined Maestro regression — original attempt terminal

Status: failed regression, unfinished increment17. Original session53866 exited1.
Both phases used the same271 frozen inputs and81 packaged Python/C files. No
runtime source,test,plugin,deadline or installed environment changed during the
attempt. There was no unchanged native retry. This is Maestro-only verification,
not a passing whole-platform regression or actual M1 admission.

| Original phase | Passed | Failed | Pytest elapsed |
| --- | ---: | ---: | ---: |
| Source |1493|2|1310.39s|
| Installed wheel |1492|3|1400.11s|
| Total executions |2985|5| |

The [combined inventory](evidence/affa17/integrated-maestro-20261019a/combined-terminal-inventory.json)
binds exact original logs,receipts,audits and all five failed cases. Neither phase
had an outer timeout. Source and wheel failures differ; an opposite-phase pass
does not erase a failure, establish a cause or prove effectiveness.

| Finding | Failure boundary | Credit withheld |
| --- | --- | --- |
|318 source|prepare-unrelated schedule/step-complete timeout at original1s end|The rejected restart control was not reached|
|324 source|collect/action=finish receive timeout|No returned collection result or subsequent closed-reader control|
|330 wheel|shared-schedule execution reports ML-PERSIST-TIMEOUT; first RPC context unavailable|Subsequent validation/tick/export assertions not reached|
|331 wheel|sink-generation1 probe timeout with approximately40.7ms remaining at original call entry; terminal result absent|Intended lost-report-ACK control not demonstrated|
|332 wheel|source-generation1 commit timeout; post-collection observations empty|Intended post-collection storage-stall injection not reached|

All causes and same-cause relations remain UNKNOWN. No deadline extension or
candidate correction is inferred from these localizations. In particular, missing
terminal data and an unreached fault boundary do not prove defects at the intended
injection stage. Reviews318/324/330–333 preserve that distinction.

Both separate terminal-phase audits exit0. They check frozen/package identities,
inventory5862 retained files,find all1706 recorded owned cgroup reservations absent,
and retain662 public projections with13508 verified M3 reference links.423 reader/
reference gaps are unclassified observations across adverse controls. Reservation
absence and recorded reaping do not prove every direct workload wait,complete
runtime-case coverage or a passing regression. Original unknowns remain unknown.

Latest [CAPA register](evidence/affa17/capa-20261019-integrated-terminal/register.json)
validates32 records/170 evidence bindings:23 local FIX_CANDIDATE/HYPOTHESIS and
nine UNRESOLVED/UNKNOWN135/222/286/287/318/324/330/331/332. Every effectiveness
remains NOT_DEMONSTRATED. This remains manual OBSERVE_ONLY work, with no independent
causal confirmation,defined observation window,automatic engine or025 integration.

The [source checkpoint and trace review](integrated-regression-source-20261019.md)
preserve26 historical trace snapshots/24 requirement rows/737 unique references.
Nine shorthand references retain multiple current definition candidates. Exact
definitions,support fixtures and historical file identities remain separate from
semantic requirement closure. The corrected class classifier has51 same-input AST
controls; its original output/correction are CAPA328, not a product runtime repair.

Next: review whole-entry issuer-loss/crash coverage against the original expected
tables and existing direct broker/dispatcher controls,then implement only concrete
missing lifecycle scope or a reviewed defect. Preserve these timing incidents and
do not rerun the unchanged full directory for green. All24 requirements,18 source
semantics,30 pairs/90 endpoints,nine complete runtime cases,seven P3 tasks,M1/
environment,whole-platform regression and separate complete review remain open.
Approved public-safe REF-002 definitions are still a pending author input; dependent
source/M1 work remains gated. Actual admitted RuntimeService/M1 executions remain0.
No stable17 commit,acceptance,merge,publication,scientific claim or canonical-note
edit follows. Sol/high is recommended for the next original lifecycle coverage
review. See the [continuation](evidence/affa17/continuation-integrated-terminal-20261019.md).
