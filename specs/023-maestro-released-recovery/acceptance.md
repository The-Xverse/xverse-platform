# Acceptance cases

- MRX-AC-01: actual stopped child / original Argus / predecessor inspect+retire / distinct new run.
- MRX-AC-02: failed and cancelled acquiring phase explicitly compensated, failed writer preserved.
- MRX-AC-03: wrong identities/pins/root/source/inspection/permit; zero effects.
- MRX-AC-04: missing/duplicate/reordered lifecycle, corruption, unknown cleanup, open writer, source races.
- MRX-AC-05: busy owner/concurrent lock, durable/idempotent retry, interrupted persistence, stale receipt on Start.
- MRX-AC-06: existing public SDK/native regression, separate review, explicit acceptance and assembled integration.

Owned fixtures do not complete the actual Studio/Autoverse goal.
