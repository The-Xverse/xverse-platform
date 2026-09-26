Goal: [ultra-light] Fix only Codex-reported T025 bugs R6 and R5; focus verification on their closure

## Completed stages
- **import_gate**: succeeded
  - Script: `python3 /opt/xcom-input/bugfix_check.py import`
  - Output:
    ```
    bug-fix checkpoint imported: 721
    ```


You are the DeepSeek V4 Flash repair worker for the sanitized T025 candidate. Work only in the writable `/workspace`. The `import_gate` has already verified and copied the rejected source snapshot. Read `/opt/xcom-bugfix/terminal-review.json`, its R6 finding and closure criteria, the current time authority and session implementation, the relevant tests, and the nearby design/implementation notes. The admitted packet and bridge are in `/opt/xcom-input`. Do not access restricted predecessor source, credentials, or the network. Do not spawn subagents or alter workflow controls.

Fix the new R6 finding directly. A lifecycle transition must commit an observation only to the same clock declaration that produced it. Serialize declaration with the full transition, or carry and validate a declaration generation through observation and commit. Preserve the guarantee that rejected transitions do not change baselines, session state, quota, or output. Cover same-domain and mapped clocks, concurrent re-declaration, and ordinary public reads. Keep the four existing `BUG_R6_` regressions and add deterministic GoogleTest cases named `BUG_R6_ConcurrentRedeclaration`, `BUG_R6_MappedRedeclaration`, and `BUG_R6_PublicReadAfterRedeclare`; CTest must discover them. Update only the affected source/header, tests, and relevant design/implementation notes. Rewrite `engineering/bugfix-disposition.md` with the exact R6 fix, changed files, test commands/results, and remaining limitations. Existing requirements and unrelated evidence remain historical; do not refresh them or claim protected acceptance.

R5 concerns the host terminal collector. Dispatch has supplied the repaired collector source read-only at `/opt/xcom-input/collect_terminal.py`; it must reject a manifest that omits any independently required candidate or evidence path. Keep the worker package complete. Do not claim end-to-end R5 closure from inside the worker; terminal collection must still succeed with this exact collector.

Run the named R6 tests and the existing suite with no more than four jobs. If a check fails, fix the cause before reporting success. Keep work scoped to R6 and its directly affected tests/documentation. Return `{"outcome":"succeeded","context_updates":{"stage":"repair"}}` only after the repair and focused evidence are present; otherwise return failed with the blocker.


Fabro final-output contract

The following contract is trusted workflow configuration. It applies only to your final response, not to intermediate tool calls.
Return a single JSON object with at least one routing field: preferred_next_label, outcome, failure_reason, suggested_next_ids, context_updates.
The contract is complete. Do not ask the user to provide or choose the output shape.