# SWE.3 Unit specifications (EARS)

## XCOM-BLD-UNIT-004 — VerificationPolicy [ubiquitous]

The host verification evidence shall identify whether network access was allowed and the isolation mechanism used for each required measure.

Source: XCOM-BLD-003.

Verification intent: Inspect the five revision-bound environment manifests and require allow_network=false with bubblewrap-unshare-net.
