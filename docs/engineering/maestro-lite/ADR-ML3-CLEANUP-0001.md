# Original cleanup context survives ordinary registry loss

Status: DRAFT implementation refinement of capability024, before repair.
Findings258–259 and original issuer-loss-a69274 reproduce the problem.
Existing ML-SR-009–013/019 and the original crash-table ownership boundary govern.

Ordinary lookup, observation, mutation and reconciliation continue requiring the
original issuer registry identity and membership. Cancellation must instead use
the original pinned bootstrap/storage/authority/owner context, validating those
objects while granting no ordinary operation. The shared epoch is still changed
only by the actual original native authority, or fenced by its original pidfd
revocation/wait. A local latch is not proof of that transition. No replacement
registry, handle, process, configuration, permit or writer is admitted.

RunBroker factors its existing context checks into a private cleanup accessor;
ordinary _holder adds all existing registry/controller checks. cancel uses only
the former and retains exact cached outcome/end semantics. Context damage still
rejects; the original root retains its independent cleanup-only path.

RunClosure snapshots the retained original generation-registry object, with its
original membership log check, instead of dereferencing a replacement ordinary
registry. Original issuer objects may supply cached factual native observations
only when their existing identity checks pass. Otherwise the original known
unit/generation is unknown. Missing original inventory is explicitly unresolved
and cannot stop visits to original helper/C1 cleanup or satisfy cleanup_complete.
This does not reconstruct an ordinary issuer or permit adoption/restart.

Python remains allocated to bounded host control and evidence; native BS17/AFFA
continue owning workload containment, tickets, epochs and direct waits. The
private additive accessor changes no public XDL, Argus or CLI schema. Exact
source/wheel/native regression and separate review are required after repair.
Independent root cause, CAPA effectiveness, full M1/stable17 and author acceptance
remain separate gates. Preserve original failures and unknown workload waits.

Refinement after finding260: the original per-unit issuer cancel entry point
must validate its fixed metadata against its original private pins and delegate
only to that original broker's cleanup context. It must not call the ordinary
registry validator before cancellation. This grants only run-wide fencing, no
ordinary use, even if its public ordinary registry is unavailable. Keep the
complete ReleaseOwner cancellation traversal bounded and the strict ordinary
observation/start paths unchanged.
