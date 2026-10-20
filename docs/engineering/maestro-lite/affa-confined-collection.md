# Confined collection — engineering continuation

DRAFT implementation design for U8, ML-SR-016–024 and the original 24-requirement
universe; thesis ML-DESIGN-2026-10-03-v2 D8 remains authoritative. No scientific
threshold or provider/root authority is introduced. The full increment17 remains
M1/controller/generation/evidence/runtime composition, not this component alone.

A collection admission pins two existing distinct directory roots before collection
using no-follow descriptor traversal, plus ordered declarations and the original
positive host deadline (at most10 seconds). Each declaration binds unit/generation,
source path, destination path, required flag and media type. Bounds:16 logical units,
8 artifacts per unit,128 declarations,1 MiB each and16 MiB total. These are engineering
caps, not measured safety or protocol parameters. Reject duplicate destinations,
traversal, symlinks, nonregular files and substitutions; undeclared filesystem entries
are never traversed/read/copied and any extra requested declaration is not admitted.

Read by pinned directory-relative descriptors, nonblocking/no-follow; compare actual
root identity at use and file identity/size/mtime/ctime before and after each read.
Check original same-session deadline between bounded chunks. Hash only a completely
accepted immutable bytes value. Exclusive confined destination creation prevents any
existing target overwrite; verify destination descriptor identity and actual copied
bytes/hash before returning. Partial failed copies are removed only after checking
that the target still names the exact newly created inode. The pre-existing target
is never removed. Preserve explicit missing/error dispositions and count/time limits.

CollectionResult is immutable and retains bounded accepted bytes for provisional
coverage. It grants no cleanup, ownership, execution, readiness or evidence-complete
credit. Indexing uses only the accepted public record_artifact method, compares its
whole returned entry to actual copied bytes, and returns immutable index receipts.
It must not inspect private Argus state or claim an open reader sees the live index.
Runtime must call collection after factual teardown and independently account for
unresolved/live unit trust. Offline U7 will independently read closed indexed bytes.

Controls authored before code:

- AC01 real nested declared file, accepted bytes/hash/index and unchanged repeat.
- AC02 traversal, absolute paths, source/destination symlinks and nonregular files
  reject without outside reads/writes or replacement of an existing target.
- AC03 root substitution and source mutation during read produce explicit errors,
  never a stable fabricated hash.
- AC04 declaration cardinality, size and total read bounds reject/expose overflow.
- AC05 same-session original deadline is required; expiry stops further collection
  and preserves prior actual accepted facts without deadline extension.
- AC06 missing required vs optional file dispositions remain distinguishable.
- AC07 mismatched actual public index ACK never certifies an indexed artifact.
- AC08 copied receipt/result/admission metadata creates no root or writer authority;
  a result is accepted for indexing only by its original admission identity.
