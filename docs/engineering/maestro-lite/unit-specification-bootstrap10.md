# Bootstrap supervisor unit contract

ML3-BOOTSTRAP10-2026-10-18-v4, partial candidate; no readiness or acceptance.

BC10 sealed input: magic/version, fixed generation, initial lease, original admission
context digest, and three role entries (sealed image FD, SHA-256, explicit argv0).
Maximum private input 64 KiB, image 32 MiB, argv0 4096 UTF-8 bytes. Native hashes the
full input and each sealed ELF independently. No path lookup of helper images.

BS10 private packets are 128 bytes: magic4/kind4/sequence8/deadline8/scope32/slot8/
child-pid8/token32/state8/reason8/reserved8. Birth1, Activate2, Renew3; Ready16,
Born17, Activated18, Renewed19. Closed/invalid/late requests terminate insertion.
Each message requires original kernel SCM_CREDENTIALS. Birth carries exactly four
SCM_RIGHTS FDs: helper C1, workload freeze-only C1 (same as helper for persistence),
helper private seqpacket peer and sealed role input. Other requests carry no FDs;
only Born returns one actual child pidfd. Slot is one-use, 1..64; state selects the
role on Birth and new lease on Renew. Other identities must match exactly.

Helper input is unchanged LC09 sealed recipe or persistence configuration; gate
input is exactly generation/lease/heartbeat/epoch/scope (64 bytes). Native constructs
fixed role argv and clears CLOEXEC only on the explicitly needed helper FDs; no
ambient environment/control channel crosses exec. Generation <=394 s, request <=5 s,
lease <=5 s, drain <=2 s. These are engineering bounds, not measured/AEB thresholds.

Separate Birth and Activate share the original request deadline. Parent registry,
actual pidfd and original direct-child wait authority precede activation. A failed
constructor remains in the original bootstrap registry for exact drain. Cancel is
independent of normal RPC locks. Shared wait facts cannot be forged by public fields.
Issuer death, copied/forked registries, replaced socket/FD/PID, stale handles and
replayed slots cannot retain ordinary authority. Uncertain late births never activate.

Verify all three real helper roles without coordinator-side Popen, composing real
M3/Argus intent -> native catalog Stage -> actual C1-bound Release -> executable
observation -> helper pidfd reaping and separate C1 tree cleanup. Test pre-activation
silence, image/input tamper, unsupported seals, deadline/cancellation during birth,
late ACK cleanup, removed helper C1, issuer loss, duplicate activation, lease expiry/
renewal, forged/copied/forked/replaced authority and exact unrelated sentinel safety.
Retain commands, native tool/link identities, source/wheel identity, all root/helper
receipts, partial trace and separate read-only findings before successor repair.
Repeat full source and copied installed regressions for each repaired product.

The v3 repair requires an admitted own-process KCMP_FILE capability. Private
original pidfd duplicates are the signal/wait authority. Borrowed aliases are
compared by exact open file description; anonymous inode/PID equality is insufficient.
Verify root/child/wait-FD replacement and denied comparison, plus cancellation while
an unrelated sentinel pidfd is substituted. The sentinel must remain alive; alias
replacement cannot acquire wait/kill authority. Every private duplicate is closed
on successful disposal or explicitly counted in external unresolved-case disposal.

The v4 persistence failure control substitutes an unrelated sentinel pidfd into
its borrowed client alias. Exact wait validation must reject, failure closes starts,
and TERM/KILL must still target only the originally issued persistence child. The
sentinel remains alive and its C1 membership unchanged. No ready/normal completion
credit follows factual emergency cleanup.
