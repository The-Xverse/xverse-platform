# AF17 private native wire v1 — before implementation

DRAFT. Internal control ABI, never XDL, public evidence or operator approval.
Codec values confer no ownership. Exact original peer, supervisor/issuer registry,
C1 descriptors and durable M3/Argus facts remain separate required admission checks.
All integers are unsigned network byte order; bool is never an integer input.

Every datagram is exactly320 bytes. No trailing bytes, unknown enum, nonzero reserved
byte, extra descriptor or duplicate ancillary item is accepted. Admission caps at16
units and8192 requests; the native receiver independently checks current original
clock/lease, exact peer credentials, operation scope and expected descriptor count.

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 4 | literal AF17 |
| 4 | 4 | kind |
| 8 | 8 | request sequence |
| 16 | 8 | original broker absolute operation end, monotonic ns |
| 24 | 32 | exact run admission scope digest |
| 56 | 8 | unit slot1–16;0 only for run-scoped operations |
| 64 | 8 | run release epoch |
| 72 | 8 | original resource generation;0 for run scope |
| 80 | 16 | original operation identity |
| 96 | 32 | first digest |
| 128 | 32 | second digest |
| 160 | 32 | third digest |
| 192 | 32 | fourth digest |
| 224 | 32 | private one-use ticket |
| 256 | 32 | private original issued-handle token |
| 288 | 8 | observed state flags;0 in requests |
| 296 | 8 | reason;0 in requests |
| 304 | 8 | requested/acknowledged run lease end;0 except renewal/readiness |
| 312 | 8 | reserved zero |

Requests: REGISTER1, INTENT2, STAGE3, ARM4, RELEASE5, QUERY6, STOP7,
RETIRE8, RENEW9, CANCEL10, QUERY_ISSUED11. Responses: READY16,
REGISTERED17, INTENT_RECORDED18, STAGED19, ARMED20, RELEASED21,
OBSERVED22, STOPPED23, RETIRED24, RENEWED25, CANCELLED26, REJECTED27.
READY alone has sequence0; all other frames have sequence1–8192. The run scope
and operation end are nonzero. Epoch permits0 and must fit uint64; the authority
rejects an admission without room for its required next epoch.

REGISTER uses the four digests for exact unit admission binding, immutable ELF image,
sealed recipe and original C1 boundary respectively. Its operation, ticket and
handle are zero. Exactly four private file descriptions accompany it: boundary,
sealed image, cwd directory, sealed recipe. Their identities/hashes must match the
original admission and C1 inventory; the codec does not perform that I/O.

INTENT binds the original nonzero operation identity plus four nonzero digests:
exact start action, durable M3 intent, actual durable Argus mirror/flush receipt and
original C1 boundary. STAGE repeats that exact identity; neither takes a ticket or
handle. ARM supplies the issued handle; RELEASE supplies issued handle and genuine
one-use ticket. QUERY/STOP/RETIRE supply the full original handle and identity;
QUERY_ISSUED repeats the original intent identity without inventing a handle after
a lost ACK. No rights accompany those requests. A genuine STAGED response may return
exactly one original pidfd; ordinary metadata cannot replace that description.

RENEW/CANCEL use slot0, generation0 and zero operation/digest/ticket/handle fields.
RENEW alone has a positive new lease; CANCEL has lease0. State/reason are zero in
all requests. Replies are data to be compared to the exact original request and
live registry; parsing a reply never acknowledges a transition by itself. Native
state flags are bounded to16 bits; reasons are closed values0–7. READY is run scoped,
all private identity fields are zero, and its positive lease equals its operation end.

All private byte fields are exact immutable bytes, not strings/bytearrays or
callbacks. Bounded value validation is pure: no I/O, provider, process, callback,
scenario or oracle. The original transport closes every received FD on any error.
No raw frame or secret field is emitted by dataclass repr or public diagnostics.

Before native code, manually authored offset fixtures must prove exact encoding,
closed request shapes and rejection of malformed length/magic/reserved/kind/range/
identity fields. Native tests must independently consume the same frozen ABI. These
checks are protocol evidence only; AF01–AF22 and the full runtime cases remain open.

## Sealed original admission and recipe ABI — before native/config code

The sealed AC17 configuration has a128-byte header: magic AC17 at0, u32 version1
at4, u64 original generation end at8, u64 initial lease end at16, u64 initial epoch
at24, u64 unit count1–16 at32, scope digest32 bytes at40, original supervisor
session32 bytes at72,24 reserved zero bytes at104. Initial epoch must leave room
for cancellation. The original lease ends at least2 seconds before generation end.
The native receiver additionally checks its own clock, lease≤5s and generation≤394s.

Each unit then has exactly160 bytes in slot order: admission binding digest32 at0,
sealed ELF SHA-256 at32, sealed recipe SHA-256 at64; u64 boundary device/inode at96/
104; u64 cwd device/inode at112/120; u64 generation≥1 at128;24 reserved zero bytes
at136. Unit admission bindings and boundary identities are unique; image/recipe/cwd
may be shared. Device values are unsigned; inode values are positive. The native
receiver compares all actual original descriptors and hashes before retaining them.
A shape-valid config does not establish bootstrap approval, C1 ownership or host
support. Configs cannot be supplied by a disposable controller.

Sealed AR17 recipe: magic AR17, u32 version1, u32 argc1–32, u32 envc0–64 (16-byte
header). Each ordered argv then env string is u32 UTF-8 byte length, exact bytes and
one zero terminator. Strings contain no embedded NUL and are at most4096 bytes;
argv0 is nonempty. Environment keys match [A-Za-z_][A-Za-z0-9_]*, followed by '=';
duplicate keys reject. Total recipe size≤65536 bytes; no suffix accepted. The native
receiver independently validates UTF-8, lengths, keys and exact sealed bytes.
Catalog argv/environment, file/CWD identities and explicit approvals remain original
admission responsibilities; the codec never discovers paths, runs a shell or execs.

## Open full-scope integration obligation

This initial wire/config draft does not yet encode selective fresh-generation
restart. Review finding4 requires an explicit same-authority advance contract and
independently authored controls before native implementation. Do not interpret a
new run or replacement authority as satisfying that missing operation. The complete
ML-SR-006/014 and explicit-restart design remain binding; current codec checks only
validate the exact draft bytes described above.
