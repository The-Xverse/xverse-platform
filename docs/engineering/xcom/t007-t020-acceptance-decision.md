# T007–T010 and T017–T020 software acceptance

**Decision:** Accepted and closed by the user on 2026-09-27 (Europe/Lisbon).

The user explicitly accepted the successor candidate presented after Codex repaired terminal-review findings R-01–R-05. The accepted, tested source revision is `d923975c43bfc1b4259d929cf38ca0e01cc2c1b2` on `codex/t007-t020-r01-r05-repair-20260927`, derived from the collected T020 revision `17f5dff67af1a7062d74b99c210c643633aef340`. The candidate patch SHA-256 is `7351ced49fcd0cedeb846ada66ec350e7255d090a63ebf184f1b6f3a918a6ce0`.

This decision closes exactly **T007, T008, T009, T010, T017, T018, T019, and T020** in `specs/007-xcom-core/tasks.md`. The task list already marks their implementation items complete; this record closes the separate external acceptance gate. It does not accept T011–T016, T021–T024, T026 onward, the whole capability 007, a production runtime, a legacy adapter, or deployment.

The reviewed [repair report](../../../../x-verse_fabric/docs/reviews/t007-t020-codex-repair-2026-09-27.md) is held in the workflow repository; its [verification record](../../../../x-verse_fabric/automation/reviews/t007-t020-codex-repair-2026-09-27/verification.json) binds the exact patch to target-repository integration: 247/247 CTest cases, 140 pytest cases plus 24 subtests, and 15 passing retained validator modes. These links are external to this repository and may be unavailable in a standalone clone; the accepted revision and patch hash above identify the decision without them.

This acceptance record is documentation only. It does not alter the tested source or test bytes and does not merge the branch into another checkout.
