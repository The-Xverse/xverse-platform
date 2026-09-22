# Design and verification plan

No architecture, interface, code, test, or runtime behavior changes. Correct only public evidence provenance and exact-revision language.

- XCOM-FINAL-EVIDENCE-BINDING-REPAIR: Modify only the provider document and traceability JSON to remove the false 90d214a delivery identity and uncommitted-overlay claims. Bind final identity to SESN host feature/evidence/review records and SESN_CANDIDATE_REVISION matched to git rev-parse HEAD, without embedding an impossible self-referential final SHA. Preserve explicitly labeled historical revisions and all other content.; checks: VM-XCOM-PROV-STATIC
