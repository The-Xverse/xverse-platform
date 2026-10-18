# Separate read-only outcome evidence review (before successor repairs)

18 October 2026. Same-agent component review, not independent full-candidate review.
Read v1 lifecycle_evidence.py, persistence client/worker changes and actual tests.

1. MAJOR ACK validation: client checks only a subset of returned event fields. An
   altered original-worker reply could be credited despite wrong action/outcome,
   source identity, clock, handle reference, dependency/causal shape or ordinals.
   Validate the complete closed retained-public receipt against original facade,
   claim, sequence, predecessor receipts and expected phase/action order, with
   substituted-ACK controls before allowing ready.
2. MAJOR history continuity: pre-append checks require only an old prefix and
   original claims. Unexpected extra records or changes between check/append may
   become accepted history. Admit only retained exact history plus genuine new
   claims, then verify one exact append from that snapshot. Never edit M3 internals.
3. MINOR intent mirror continuity: comparing selected payload fields is weaker
   than the already retained original append+flush digest. Compare exact canonical
   [event ID, ingestion ordinal, payload] against the original claim flush digest.
4. ADVISORY scope: actual missing Query/issuer/dead-child failures do not yet have
   normal failure/disposition records, and no automatic scheduler, normal reverse
   stop/cleanup or full U7/U8 coverage is provided. Keep those obligations open.
   The 128 request cap is inherited; full scheduling admission must budget it.
5. ADVISORY verification: demonstrate actual original journal lock after Release,
   source public-record hash/schema correspondence, public sanitization and reader
   reconstruction. Retain partial records after fault; never claim full coverage
   or replace a missing normal record with later cleanup success.

Findings precede repairs. Full regression/installed-wheel and exact-source binding
remain required. No acceptance, main merge, experiment run or full M1 is claimed.

6. MINOR fixture budget after durable evidence integration: the inherited stale-
   reply test gives its successful setup only 10 ms freshness. A correct durable
   append+flush/read-back can exceed that and properly reject initial readiness.
   Use an explicit 500 ms engineering setup window; the injected reply is still
   one second old and must reject. No product freshness relaxation is allowed.
7. MINOR positive fixture discrimination: a real first Query may observe pending
   exec. Accept independently specified failed initial probes before the first
   successful started/probe/ready chain; never assert a fixed event count that
   excludes legitimate bounded pending-exec observations.

8. MINOR receipt sequence precision (read-only successor pass): positive producer
   and ingestion ordinals alone do not prove ordering against other unit receipts.
   Retain the last acknowledged global producer/M3/Argus positions and require
   exact producer increments, increasing M3 sequence, and contiguous intra-reply
   Argus ordinals. Add an altered producer ordinal control.
9. MINOR repair application check: the v2 focused run still uses the inherited
   split-line 10 ms setup budget; the textual replacement did not match. Correct
   the exact fixture literal and verify the diff before repeating checks.

10. MINOR fault-fixture outcome expectation (v3 focused run): a flush failure can
    occur on a legitimate pending-exec probe before any running observation. The
    real normal M3 observation exists, but the test incorrectly requires a start
    outcome in every fault branch. Require a factual post-intent observation or
    outcome, while retaining no-ready and actual worker-reap checks. A failed
    initial probe never becomes an invented successful start outcome.

## Final read-only component pass

Final focused v4 result: 58 passed (23 new outcome cases plus 35 provider cases).
Findings 1–3, 6–10 have successor repairs or discriminating fixture corrections.
Finding 5 verification is exercised by real files/reader and fixed worker faults;
finding 4 remains an explicit full-integration limitation. No independent full
review, acceptance or complete lifecycle coverage is claimed. Record-before-repair
archives and focused failure logs remain retained. The 500 ms stale-reply setup
budget is an engineering fixture value; its injected sample is one second old.
Product freshness limits were not relaxed. Full source/wheel checks remain required.
