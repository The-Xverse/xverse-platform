# Separate read-only Release gate review

Same-agent component review, 2026-10-18. No independent/full-candidate acceptance.
Exact first source/tests archived in evidence/releasegate6/pre-review-v1.tar.gz;
first real run: 109 checks pass (RG06, codec and default LG05).

Findings recorded before successor repair:

1. MAJOR: Released currently acknowledges a successful unfreeze write, but the unit
   contract promises observed unfreeze. Observe frozen=0 within original ticket TTL
   and current lease, rechecking original owner before the response. Failure/expiry
   burns the ticket and attempts conservative freeze; it cannot return Released.
2. MINOR: the inert codec accepts nonterminal response reasons and nonzero Ready
   sequence. Reject inconsistent response headers; do not infer successful ACKs
   from contradictory bytes. Keep it a codec, not a duplicate lifecycle machine.

Remaining full-scope limitations are explicit: no actual M3/Argus/Stage receipt
truth validation in the native program, no child launcher or full provider handle,
no bounded kernel/scheduler stall or killed-helper lease, no complete original C1/
owner/bootstrap integration, no nine-case runtime proof. Digests/nonce/fields do
not manufacture authority. Kernel removal prevents old-FD revival only after actual
C1-confirmed removal; freeze alone is insufficient. These are open gates, not waived
requirements. All 24 ML-SR and 18 unvalidated REF-002 parents remain in scope.
