# Implementation tasks

- [x] MRX-T01: specification, requirements, design and read-only consistency. Depends on: none.
- [x] MRX-T02: public recovery types, source inspection and verifier. Depends on: MRX-T01.
- [x] MRX-T03: host permits, durable retirement and Start fences. Depends on: MRX-T02.
- [x] MRX-T04: actual owned-process and adverse verification. Depends on: MRX-T03.
- [x] MRX-T05: separate review, repair and exact repeated checks. Depends on: MRX-T04.
- [ ] MRX-T06: explicit user acceptance, exact main and assembled verification. Depends on: MRX-T05.
- [ ] MRX-T07: Studio admitted dependency and original-root complete live workflow. Depends on: MRX-T06.

T02–T05 are under successor verification after recorded reviews. Acceptance/main
integration and complete downstream Studio live acceptance remain pending.

Final candidate99dc5994c passes236 source/46 installed recovery checks and3selected
native CTests. All recorded review findings repaired; final read-only review has no
blocking findings. T06 explicit user acceptance/main assembly and T07 full Studio
live acceptance remain pending. Evidence: docs/engineering/maestro-recovery/evidence/verification.json.

The user accepted exact8c2307fa9 on2026-10-29. T06 isolated main integration/assembled
verification is in progress; T07 full Studio live acceptance remains open.
