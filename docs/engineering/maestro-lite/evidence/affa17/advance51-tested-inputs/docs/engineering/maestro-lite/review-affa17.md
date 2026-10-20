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

4. MAJOR completeness finding before native implementation: the first AC17/AF17
   draft pins one generation per unit and has no explicit advance operation. It
   therefore cannot yet express selective restart while unrelated units remain
   active. Do not substitute a replacement broker, whole-run restart or weaker
   cooperative epoch check. Before native code, specify same-original-authority
   generation advance: actual prior boundary release, fresh execution/permit/intent/
   mirror, new original pre-Stage C1 descriptor, shared epoch advance/burned unused
   tickets, fresh prerequisite observations, bounded retained old-generation facts
   and explicit restart-budget admission. Old C1 cleanup and matching cached outcomes
   stay scoped to their original generations. AF17v1's codec checks do not close
   this requirement; record a successor protocol and expected controls first.

5. MINOR successor fixture inspection before correction: the v2 literal unit
   fixture supplies six uint64 fields but still spells five Q fields/24 reserved
   bytes in struct.pack. Correct it to six Q fields/16 reserved bytes, matching
   the independently recorded160-byte v2 layout. Retain the first red run and
   repeat the corrected red controls before product changes.

Read-only successor pass after generation-expression repair: inspected the v2
fixed offsets, explicit initial/maximum and joint generation bounds, ADVANCE/
ADVANCED no-handle/no-ticket shapes and aggregate recipe byte cap. The corrected
red controls fail before code;51 pure controls pass afterward. No additional codec
finding in this pass. Finding4's native/broker/selective-restart behavior remains
open: the codec now expresses it, but does not execute or authenticate it. Old23
and48 tested inputs are retained with exact pre-recorded hash matches.
