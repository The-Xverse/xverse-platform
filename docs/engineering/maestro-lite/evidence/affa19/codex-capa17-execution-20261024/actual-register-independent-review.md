# Independent review of actual CAPA17 and DV12 — 2026-10-24

**Verdict: PASS for the actual generated evidence package within the inspected source/JSON scope. No blocking finding.** This is an independent review, not CAPA effectiveness confirmation, delegated implementation acceptance or permission to merge.

Inspected physical repository: `/media/jefferson/11c42dee-73a3-4c2b-ab42-a0440011d9e0/.x-verse-build/codex-20261024/worktrees/xverse-platform/stabilization-s1a3-20261023`, HEAD `7b7126ca392800c8bca7c89791b85c98a676e555`. The installed-wheel tested candidate remains `4bedba9efd21c750b84322e5fc265eb6adf86cc9`. HEAD did not move during these checks. The generated CAPA directory was untracked; other generated run/check outputs remain under root's final bundle-retention workflow. No platform, thesis or Git files were changed by this review. Only this external review and independent scratch controls were written.

## Actual identities inspected

Paths below are relative to `docs/engineering/maestro-lite/evidence/affa19/` unless indicated.

| Artifact | SHA-256 |
| --- | --- |
| Parent `capa-20261024-c1-config-bound-step16/register.json` | `bf39b0875a3f1606a2027718c570f5b17846065bf70b2d9aead382c408ae2ad8` |
| Child `capa-20261024-simtime-faults-step17/register.json` | `0d6f40f28635ccb1c801fa00552f0fe8e0b3f04008c91c65338d5324b1da3b07` |
| Actual run `platform-regression-20261024j-codex-1/dv12-gate-verdict.json`, under `stabilization-s1a3/` | `9705d8471ea415b01b1d06c98dbc69a3d63ea544126b194a007f740a4ba33c6c` |
| Same run `dv12-execution-receipt.json` | `3e8d806ce8602850758629b608deea9e8b75f04b94945cae0886144659cfbef6` |
| Original reviewed and actually invoked `capture-dv12-20261024.py` | `e388ee9a468bc73375a03def17fc28c708856971d66afee234e6200af02b09d4` |
| Actually invoked `build-capa-20261024-simtime-step17.py` | `1e2d6f3412e217d61b0bd4f308f230b784f28e00c3617e28e4b704871bb28bf5` |

## Parent preservation and honest observation status

The parent file's actual bytes reproduce its recorded SHA. Independent comparison of all56 prior rows, all56 action plans and all757 prior evidence bindings finds exact canonical JSON-byte equality, preserving typed values as well as ordinary equality. The child's original rows retain their original order. The parent pointer binds that exact existing file/hash. Every other historical root member is unchanged except the designed current root flags and parent pointer; `simTimeFaults` is the sole added root member. Historical nested approvals remain historical, while child root `accepted`, `merged`, `scientific_result` and current `simTimeFaults.accepted/merged` are false.

The child has57 records and784 bindings, adding one observation and27 new evidence bindings. All27 new bound files reproduce their recorded hashes. Current source/test/validator/ADR bindings also equal their exact tested4bed Git blobs. The collection patch equals the actual three-file diff from `b40acce49d181058ac61cd651650d18779af8027` to4bed and reproduces recorded hash `28f9bf55fbfa460d38625fa2f16df655d0f2151ac8540dcc3436a7fc81d5a42c`.

New `ML-CAPA-SIMTIME-COLLECTION-20261024` remains **TRIAGED**, with **HYPOTHESIS** cause status, null reproducer and observation-window end, no lesson promotion, and **NOT_DEMONSTRATED** effectiveness with no observation plan or independent confirmation. It traces finding8's composed collection-continuity observation to the source/patch and names actual composed coverage. The summary and affected-version qualifier explicitly limit historical runtime occurrence and independent cause verification. Correction/prevention remain candidate statuses. Findings8–11 distinguish that shared-path observation from candidate-only repairs and retain the genuine earlier full-run failure. A clean regression is not presented as cause verification or sustained effectiveness.

## Actual run, capture and tested-source association

The actual official DV12 command is exactly `/usr/bin/python3 -I <tested validator> <actual j run> --candidate 4bed... --g4 <actual G4> --allowlist <actual allowlist> --scope code --repo <physical repository>`. Candidate, run_head, configuration git_head and wheel receipt git_head all equal4bed. The validator's actual bytes equal the tested Git blob. The actual capture identifies the original independently reviewed wrapper hash above, at its installed physical path.

Execution records actual exit0, `timed_out=false`, `failure=null`, `capture_passed=true`, complete cleanup, no TERM/KILL and no cleanup errors. Before/after maps contain exactly the six reviewed input hashes and are identical. Five small input files were independently rehashed; the wheel-log hash agrees across both capture maps, the actual wheel receipt and run SHA256SUMS. Gate and empty stderr hashes independently match the actual files and SHA256SUMS. Capture `accepted/merged` remain false.

The actual gate has `accepted_as_evidence=true`, no blockers,3039 collected,3038 passed and1 skipped. Its code scope digest `45a5960c8b30c4655be4e4a526c1b41ec5da48573817e0c334da1daac53d5268` was independently recomputed from the filtered Git ls-tree listings for both tested4bed and current7b7126c; both equal the gate's run/candidate digests. Thus the later evidence-guard commit does not change tested code scope.

Configuration and actual wheel receipt agree on archive `0bc48cd094e0c98d8a300845afe94528f5978e1c34ecbbd9aece23eeede87382`, collection count, successful installed-wheel verification and installed-versus-frozen source equality. Wheel exit0, no outer timeout and no unknown descendant cleanup are explicit. A bounded final4096-byte log read matches the receipt's exact summary:3038 passed,1 skipped,39 subtests passed in3086.69s. The single skip is the explicitly separate lane-admission driver (`MAESTRO_LANE_PROPOSAL` absent), not a hidden full-suite failure. No prior gate's success flag was merely inherited: actual command/input/gate/capture/count/code associations identify this j run.

## Actual official-check receipts and limits of this review

Inspected `codex-capa17-execution-20261024/` generation, schema-evidence and parent-preservation receipts, complete stdout/stderr files and verdict JSON. Actual tool hashes, output hashes, commands and physical cwd match their receipts; all actual returncodes are0. The schema/evidence verdict binds the exact child register and reports57 records/784 bindings. The preservation verdict binds the exact child and parent,757 old bindings, no changed/lost identities or references, and unchanged schema/policy. Both preserve no-effectiveness/no-cause-confirmation boundaries. The generation receipt identifies the reviewed builder hash above. These terminal receipts are actual execution evidence, unlike the earlier unexecuted preparation review.

Independent stdlib source/JSON controls and their complete result are retained outside the repository at `codex-20261024/scratch/review_wp15/capa17-actual-review-controls.py` and `.json`. JSON reads reject duplicate keys. No official checker/builder/validator, pytest, framework or live simulator was rerun. This review did not independently rehash all757 historical evidence files, the entire wheel log or Git archive: their actual official checks remain associated through the inspected receipts and gate, while parent binding preservation and all27 additions were independently checked. This scope is not a second full schema/evidence verification or a scientific result.

Root still owns final bundle retention, any delegated implementation acceptance and any separately authorized commit/merge/delivery. This PASS does not promote the CAPA observation, close carried residuals, or authorize live execution.
