# AFFA17 separate read-only findings

18 October 2026. Same-agent component review, not independent full-candidate review.
Record findings before subsequent repairs. Parent is temporarily6083439; exact
recovery16 integration/freeze is still pending. No M1 execution claim.

1. MINOR bounded-value inspection before repair: make the inert AuthorityFrame
   dataclass use slots. Its exact-type/byte validation is already present; slots
   additionally prevents arbitrary per-instance method/attribute injection and
   reduces mutable instance surface. It remains a value, never a capability.
2. The receiver/client must compare every parsed reply with the exact original
   request, peer and live registry. Shape validation by itself is not a native
   acknowledgement, clock check, ticket validation or C1 ownership proof. This is
   an integration obligation, not a reason to promote the codec to authority.
3. Native config/recipe and ancillary-rights contracts, actual authority state
   machine, supervisor/controller integration, AF01–AF22 and all runtime cases
   remain unfinished. Twenty-three pure protocol checks cannot close those gates.
