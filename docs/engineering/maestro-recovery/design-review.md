# Initial read-only specification review

Baseline ce2d5558, authorized ADR-0035 scope. No code acceptance implied.
Requirements/design identify all narrow scope items, finite resource/permit bounds,
original identity/source witnesses, separate original evidence verdicts and retirement,
no callback/signal authority, and explicit downstream live acceptance. Constitution
and dependency direction pass. Python control-plane allocation reuses actual public
Argus/XDL; C++ data-plane and legacy sources remain unchanged. Applicable REF-002
allocations are explicit in feature traceability without normative conformance claims.

Design findings: a failed writer from public abort is not evidence corruption by
itself; allow only verified explicit compensation and preserve incomplete status.
Interrupted acquisition may lack success but still needs an original causal released
cleanup pair. Mutable caller receipts require full recapture, not digest trust alone.
Root/installation changes invalidate retirement; old read stays unknown. These are
included in the contract before implementation. No blocking specification inconsistency
remains. Final software read-only review follows actual verification and records its
findings separately before repairs. Review is primary-agent, not independent acceptance.
