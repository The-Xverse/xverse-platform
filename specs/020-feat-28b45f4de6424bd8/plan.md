# Design and verification plan

Introduce explicit finite later-capability allowlists at each predecessor validator ownership boundary. The validators continue to execute their original checks on owned code, tests, documentation, traceability, dependencies, and behavior. The observation validator creates a private exact-candidate clone and invokes all three unchanged command contracts there. No production unit or public interface changes.

- XCOM-VAL-PREDECESSORS: Adapt the three predecessor validator ownership/layout boundaries with finite explicit later-capability catalogs while preserving every original check, mode, diagnostic, and exact-candidate binding. Do not edit production code, tests, build files, observation validation, or documentation.; checks: VM-XCOM-VAL-CORE, VM-XCOM-VAL-LIFECYCLE, VM-XCOM-VAL-PROVIDER
- XCOM-VAL-OBSERVATION: Restore exact-candidate predecessor --all execution in the observation validator and correct the public observation evidence text. Preserve all current candidate checks and do not edit predecessor validators, production code, tests, or build files.; checks: VM-XCOM-VAL-OBSERVATION
