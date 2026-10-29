# Public recovery contract 1.0

PublicExecutionService(..., recovery_bindings=tuple[RecoveryProviderBinding,...])
registers optional host-declared current installation pins for all its providers.
inspect_recovery(run_id) returns RecoveryInspection without provider/resource calls.
retire_released(inspection, HostRecoveryPermit) recaptures current original source
and validates exact equality and permission before atomic receipt publication.
recovery_status(run_id) reports separate verified retirement state without rewriting
read(run_id). Initial public method names are frozen by this capability's design.

Known original in-memory runs are not predecessor claims and cannot be retired.
Operations refuse busy public lifecycle locks; the actual root flock excludes other
owners. Source root/claim/manifest/stream bytes and reader results bind the witness.
Every original Maestro event must match identity and contiguous producer sequence.
The start-request must own the original correlation ID, and exactly one terminal
record must show stopped/failed plus released cleanup. Each acquiring prepare/start
intent has one causal released cleanup pair, in reverse acquisition order. A successful readiness
outcome is never inferred. At most the last phase intent may lack its outcome, only
with an original terminal failure; every acquiring intent still needs explicit
released compensation. No events after the
terminal lifecycle fact are accepted as further lifecycle; original Argus abort
records are separate. Native loss cannot manufacture a lifecycle gap or cause.

Terminal writer closed or failed may be inspected. Failed/incomplete remains such;
reader integrity errors or unsupported diagnostic categories cannot be bypassed by
a nominal released field. Original argument/source shapes and all refs are checked.

Receipt identity combines original run and current recovery binding. Different host
bindings create separate immutable receipts within declared caps. Exact retry returns
the first receipt; conflicting inspection/source does not overwrite it. Persistence
uses exclusive temporary creation, fsync, atomic no-overwrite publication and root
fsync. Partial writes leave no valid retirement; original source remains unchanged.
Start recaptures each predecessor source and rejects any stale or invalid receipt.
Selected prepared installations must match configured recovery pins. Ordinary XDL,
provider runtime, permit and lifecycle admission still run afterward.

Version1 recovery supports original public lifecycle roots with one regular event
stream and no external artifacts. Unrecognized source formats are refused; source
paths are not caller selectors. Provider installation pins are declared by the host
and do not independently attest a physical installation.
