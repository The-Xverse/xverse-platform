# Design and verification plan

Adds a root CMake foundation that can include the future src/xverse/xcom subtree when present, a pinned offline dependency lock, and a deterministic no-network dependency preflight. It adds no runtime, provider, observation, stimulation, or gateway behavior.

- XCOM-BUILD-FOUNDATION: Generate the root CMake C++20/test/warning foundation, explicit offline dependency helpers, deterministic dependency preflight with self-tests and classified failures, and public-safe lock/environment documentation. Read XVERSE_XCOM_TOOLCHAIN and XVERSE_XCOM_PACKAGE_MANIFEST only as explicit inputs. Verify all twelve package hashes from the external package files; record exact versions, licenses, and generated-code provenance. Do not add any X-COM runtime source or fetch/install anything.; checks: VM-BLD-UNIT, VM-BLD-INTEGRATION, VM-BLD-VALIDATION
