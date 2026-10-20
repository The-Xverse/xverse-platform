# Separate read-only catalog launcher review

Same-agent component pass, 18 October 2026. Exact first source/test is archived in
pre-review-v1. The initial chain reached native catalog exec, exact argv/environment/
closed control FDs, probe and cleanup. Its final assertion wrongly demanded C1 itself
perform the kill, although the original native issuer had already killed/reaped.
No independent/full-candidate review, runtime admission or acceptance is claimed.

Findings recorded before repairs:

1. MINOR test: check C1 empty/released independently from actual native direct-child
   reap. Native cancellation can win the race; an empty C1 does not fabricate its
   own termination observation. Combine only the actual distinct observations.
2. MAJOR: reserve/serialize the entire Stage operation before M3/RPC work. A second
   request must not dispatch after the first RPC returns but before handle insertion,
   kill an already-issued child or manufacture a second attempt. Cancel stays independent.
3. MAJOR: recompute the recipe from original owner/catalog/claim facts before accepting
   a caller's LaunchRecipe. Equality of caller-supplied metadata is not executable
   authority. Bind exact native-loaded configuration bytes with a digest computed by
   the helper, not a context hash merely copied from the input header.
4. MAJOR: retain/check original socket device/inode as well as Python object identity;
   a dup2 replacement of its underlying FD is not the originally registered channel.
5. MAJOR: reject a negative F_GET_SEALS result before bit tests. -1 contains all bits
   and cannot prove that an ordinary mutable file is sealed. Verify the full private
   input digest before READY so a different sealed input cannot echo the same context.

Expanded-source read-only pass (pre-repair-expanded-v1 archive; 11 passed, one failed):

6. MAJOR: native receive must return immediately after a non-retry recvmsg error.
   Ancillary storage has no received-message validity after that error; parsing it
   can inspect uninitialized control bytes. A retry remains non-authoritative.
7. MINOR test: C1 residual_membership requires an observed frozen boundary. The
   descendant test queried it after Release while unfrozen. Freeze through the
   original retained C1 authority, then check membership and cleanup independently.

Bootstrap/helper/environment authentication, whole caller/kernel bounds, full M1,
normal provider facade/readiness/evidence and all nine runtime cases remain open.
