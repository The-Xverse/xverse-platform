# Pin original supervisor startup resources and retain cleanup after alias loss

Status: DRAFT before fault controls/repair; finding307. Refines original startup
ownership in RUNTIME-0002 and partial ML-SR-010/012/013/024, CP-04/09 and unrelated
sentinel capability controls. No change to eight hash-bound external design inputs.

The original launcher must retain each actual channel, Popen, raw pidfd, private
pidfd capability and successful BootstrapSession immediately when returned.
Ordinary launch/repeat/registration checks require those original identities.
A different genuine capability/session is not authority for this launcher.

Cancellation/drain/disposal and factual outcome inspection use a separate original
cleanup holder, admitted original manager/end/session and retained resource pins.
No lost ordinary alias may select another process/socket/session, replace wait
ownership or block original available cleanup. Native session remains the root wait
owner after registration; failed pre-READY registration uses only the original
launcher private pidfd. Missing original birth/capability remains unknown with no
PID/name/path reconstruction, adoption, second creation or fabricated wait.
Preserve original bounded drain ends, lease/start-window checks and input admission.

Unit specification: stop the actual owned supervisor before READY; separately
replace capability, process, channel, raw pidfd or session alias. Full ordinary use
must reject; cancellation must close the original latch without targeting the
separately owned sentinel, and original wait must remain authoritative. A foreign
signal guard denies/records any attempted sentinel signal without killing it.
Capture primary state before test-only external cleanup; source failure cannot be
hidden by metadata restoration or external descriptor disposal. Late Popen-return
and unknown-birth cases retain their existing conservative contract.

Python owns retained host identities; native bootstrap/AFFA fencing and data paths
are unchanged. No actual M1/service admission, scientific parameter, safety result,
acceptance or historical135/222/286/287 closure. Expected scope comes from the
original crash/capability table, not copied implementation transitions.
