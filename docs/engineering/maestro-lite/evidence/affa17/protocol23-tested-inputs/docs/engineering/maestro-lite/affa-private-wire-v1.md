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
