# Separate read-only lease guard review

2026-10-18; same-agent review, not independent full-candidate review. Partial U3/U4.
V1 source is retained exactly in evidence/leaseguard5/pre-review-v1/lease_guard.c.
Findings recorded before successor repair:

1. MAJOR: receive errors other than EAGAIN leave msghdr ancillary storage invalid;
   return immediately without interpreting any control buffer when recvmsg fails.
2. MAJOR: after packet parsing, recheck the original current lease and supervisor
   before committing a renewal. No check can make user-space kernel I/O atomic;
   preserve the explicit stopped-helper/unbounded-I/O limitation.

All full M1, C1/launcher integration, helper-loss fence, authenticated bootstrap,
whole-project trace and independent review gates stay open. This pass does not
approve a source parent or change runtime admission.

Second separate read-only pass after the first real tests (36 pass, 1 fail):

3. MINOR (test/contract): an unread queued request can cause Unix socket reset on
   helper exit, dropping the terminal packet despite a successful send. The late
   heartbeat test assumed reliable final telemetry. Verify native exit AND actual
   frozen kernel state; parse the terminal response if delivered. Preserve lost
   acknowledgement as unavailable, not a fabricated response. The wire contract
   must state that successful local send is not a receiver acknowledgement.

V1 compiler and first kernel failure log are retained. No boundary root leaked;
all test fixtures completed their independent outer cleanup.

Additional read-only native static-analysis pass:

4. MINOR: stricter -Wconversion flags reject an implicit signed-to-unsigned digit
   promotion in overflow checking. Input was range checked first, so no observed
   runtime fault; spell out the unsigned digit and retain the failed diagnostic.

Post-findings 1/2 source (the first real kernel-test candidate) is pinned in
pre-review-v2/lease_guard.c; the second kernel pass has 37 passes. The original
pre-review-v1 C archive predates these repairs and was only compiled/read, not
executed by those kernel tests. Test formatting changed afterwards; final pins
and regressions will bind the final successor exactly.

Final pre-verification read-only pass:

5. MINOR (test): the ordinary-directory rejection check reused pytest's directory
   used by the receipt fixture. Use a separate empty subdirectory so receipt files
   cannot be mistaken for helper side effects.

Findings 1–4 repaired in the successor; strict GCC -Wconversion/-Wshadow/-fanalyzer
now passes. This remains a same-agent component review, with no independent or
full-candidate acceptance claimed. The final manifest binds exact repaired bytes.
