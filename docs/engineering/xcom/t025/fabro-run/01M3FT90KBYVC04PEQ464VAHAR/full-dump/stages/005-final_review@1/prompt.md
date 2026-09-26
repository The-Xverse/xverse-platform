Goal: [ultra-light] Fix only Codex-reported T025 bugs R6 and R5; focus verification on their closure

## Completed stages
- **import_gate**: succeeded
  - Script: `python3 /opt/xcom-input/bugfix_check.py import`
  - Output:
    ```
    bug-fix checkpoint imported: 721
    ```
- **repair**: succeeded
  - Model: deepseek-v4-flash
  - Files: /workspace/engineering/bugfix-disposition.md, /workspace/engineering/design.md, /workspace/engineering/implementation-notes.md, /workspace/src/xverse/xcom/include/xverse/xcom/validation_session.hpp, /workspace/src/xverse/xcom/src/validation_session.cpp, /workspace/tests/validation_session_tests.cpp
- **focused_checks**: succeeded
  - Script: `python3 /opt/xcom-input/bugfix_check.py verify`
  - Output:
    ```
    focused R6 checks and full CTest passed: 144
    ```

## Context
- stage: repair


You are the sole DeepSeek V4 Pro reviewer in this ultra-light T025 bug-fix workflow. Review **only the reported blocking bugs R6 and R5** in `/opt/xcom-bugfix/terminal-review.json`; do not rerun requirements, architecture, unit-specification, validation-authoring, or general phase inspections. Work only in `/workspace`. No subagents, restricted source, credentials, or network.

Read `reports/bugfix-check.json`, `engineering/bugfix-disposition.md`, the changed source/tests/design notes, and the exact baseline files under `/opt/xcom-bugfix/files`. For R6, independently check the actual delta and tests: an observation cannot be committed to a replacement clock declaration after concurrent re-declaration; rejected transitions leave baselines and session state unchanged; same-domain and mapped cases and ordinary public reads are covered. Look for a deterministic race test, not only a probabilistic stress loop. A passing CTest log by itself is insufficient. If any closure criterion is unproven, mark R6 `fail` and give a concrete finding.

For R5, inspect the read-only host collector source at `/opt/xcom-input/collect_terminal.py` and its hash from `reports/bugfix-check.json`. Check that it captures the stopped worker and independently requires the candidate header/source, tests, review, and evidence inventory in the worker manifest. Verify that omitted entries, physically missing files, and hash mismatches produce collection errors. Mark R5 `pending_terminal` if that contract is present: actual end-to-end closure still depends on the model-free collector after this run terminates. Mark `fail` if the contract is absent or mismatched. Do not assert that a future collection already succeeded.

Write `reports/bugfix-pro-review.json` with `schema_version: 1`, `reviewer_model: "deepseek-v4-pro"`, `source_review_sha256`, `candidate_material_sha256`, and exactly two objects in `issues`: `{ "id": "R6", "status": "fixed"|"fail", "evidence": [specific paths], "finding": null|string }` and `{ "id": "R5", "status": "pending_terminal"|"fail", "evidence": [specific paths], "finding": null|string }`. `source_review_sha256` and `candidate_material_sha256` must equal the values in `reports/bugfix-check.json`. Use `fixed` for R6 only when independently supported. Return `{"outcome":"succeeded","context_updates":{"stage":"final_review"}}` only if R6 is fixed and the R5 collector contract is present; otherwise return failed after writing the findings. Keep the response short.


Fabro final-output contract

The following contract is trusted workflow configuration. It applies only to your final response, not to intermediate tool calls.
Return a single JSON object with at least one routing field: preferred_next_label, outcome, failure_reason, suggested_next_ids, context_updates.
The contract is complete. Do not ask the user to provide or choose the output shape.