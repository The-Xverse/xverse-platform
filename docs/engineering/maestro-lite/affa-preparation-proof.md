# Reusing only the original validated preparation proof

DRAFT detailed design before implementation; partial ML-SR-001/005/006/018/019/023.
The worker diagnostic profile identifies repeated deterministic preparation as a
hotspot; it does not establish the sole cause of the observed storage timeouts.

At original PermitSession admission, retain the full successful XDL/plan/preparation
verification. Pin the exact prepared/result/resource objects and a private immutable
snapshot of all their typed data fields, including mutable compiler plan content,
resource provenance/elements/references/extensions/content/source maps, prepared
units/actions/provider pins/graph/clock/limits/canonical bytes, and result diagnostics.
At each claim and original receipt revalidation, verify the original objects and
compare all current typed fields with this original snapshot. A change rejects
before consumption or permission use, even when public digests remain unchanged.
No changed input is accepted by recomputing its pin. No global cache or public
pin/receipt adoption is introduced. Bound inputs remain those originally admitted.

For identical complete inputs, the pinned package's deterministic compiler has the
same result as its actual original verification. Reuse that proof; do not repeat
full compilation on every original receipt. Keep the initial public validation API
unchanged, including its full verification and first-claim whole-set validity check.
Keep current UTC permit/approval validation, exact receipt identity, original journal
and consumed nonce checks, durable history/mirror checks, independent cancellation
and all operation deadlines. A plan pin never becomes execution permission.

Verify unchanged original use without recompilation, mutated nested compiled plan,
prepared fields, original resource fields and replaced equal input objects. Repeat
permit expiry, journal loss, consumed nonce and mutation/adoption tests, then current
source/wheel lifecycle/scheduling regressions. Preserve all prior failure evidence;
any improvement is bounded engineering evidence, not a hard host timing guarantee,
full M1 completion or experiment fitness. Fresh generation/controller work remains.
