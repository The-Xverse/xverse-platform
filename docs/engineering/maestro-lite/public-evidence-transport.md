# Original public evidence transport contract

DRAFT before code; ADR-ML3-EVIDENCE-0001; complete increment17 remains open.

Optional BrokerArtifact admission is derived only from the original externally
pinned CoverageAdmission's brokerPath and required artifact byte cap (at most1MiB).
The encoder/worker independently rederive the exact declaration and original digest
before journal/writer effects. Optional sealed configuration v5 carries it; absent
admission preserves v1–v4. Reserve one original publication RPC in any schedule.
The worker pins its original writer root even without v3 export declarations.

Request frame keeps version1 and the closed existing envelope. New kind public-blob
has body {purpose:broker-projection, bytes:positive integer, sha256:64 lowercase hex}.
Only admitted v5 worker requests accept exactly one SCM_RIGHTS descriptor with the
original SO_PEERCRED/SCM_CREDENTIALS identity. Other frames accept no rights. Require
a regular descriptor with write/grow/shrink/seal seals, exact size within the admitted
cap, original frame end within5s and the original generation end. Read in bounded
chunks/checkpoints, verify actual identity/size/hash, and close descriptors before
returning inert bytes to dispatch. Truncation/extra rights always reject and dispose.

The public broker payload is canonical closed JSON: original schema/run/lifecycle/
host session, full admitted unit and inert future context inventory, every registered
generation (including known never-attempted/unknown), original epoch/cancellation
facts, retained Release/Stop brackets and independent native/C1 observations. No
private descriptor, PID, nonce, raw handle or arbitrary artifact path is accepted.
The parent supplies only actual original broker projections. Worker admission checks
are additional data checks, never a claim that public metadata authenticates an issuer.

Write once at the original brokerPath, using no-follow confined directory descriptors,
exclusive creation, bounded writes, fsync and actual byte/identity verification.
Return the actual public record_artifact entry, original run/lifecycle/admission,
snapshot digest and original observation timestamp. The parent checks exact shape,
types, values and index entry before retaining a receipt. Matching repeats cache the
original snapshot and do no I/O; copying/replacing the original broker/admission or
malformed/lost ACK cannot publish a new receipt. Cancellation does not reopen starts
but permits evidence publication while the original writer is still open.

Controls authored before implementation:
PE01 default v1–v4 exact bytes/no descriptor acceptance; v5 rederived before sinks.
PE02 real original worker writes/indexes actual broker bytes before/after real owned
native teardown, with actual original event/source references and closed-reader bytes.
PE03 complete metadata inventory larger than one packet traverses a real sealed
descriptor unchanged; no rows are dropped and no productive authority is inferred.
PE04 bad digest/size/seals/regular type/frame/peer/missing/extra/truncated rights
reject and close all delivered descriptors, including failures after receipt.
PE05 wrong run/lifecycle/session/context/generation/capacity/shape/epoch/clock data
reject; malformed JSON or duplicate keys cannot produce an index ACK.
PE06 existing/symlink/changed parent/root/partial write/index failure preserves the
original failure, cannot overwrite or return a successful receipt.
PE07 actual copied original admission/broker, malformed/lost ACK and RPC conflict
reject with no adoption/replay; original helpers remain cleanup-owned.
PE08 matching repeat is original immutable receipt; starts remain cancelled and
publication does not append intents, launch or invent cleanup/normal outcomes.
PE09 required report/collection/dispositions/terminal/closure still missing means
incomplete U7/U8; pure consumer and independent accepted-reader checks remain.
