# CodeQL result disposition for T025 successor

Source revision `25c650830c865c0ae0170a8eed53da7e8f076d8f`; suite
`codeql/cpp-queries:codeql-suites/cpp-security-and-quality.qls`, pack 1.9.0. The complete
machine result is [`codeql-results.sarif`](codeql-results.sarif). These are the only two results;
both have `problem.severity: recommendation` and `precision: very-high`.

| Result | Location | Disposition |
| --- | --- | --- |
| `cpp/large-parameter` for 72-byte `ManagerConfig` | `src/xverse/xcom/src/validation_session.cpp:806` | Accepted recommendation for this bounded prototype. The constructor is not a per-item path; passing the configuration by value establishes an owned construction boundary and it is copied into the manager's member. This result is a performance opportunity, not evidence of incorrect permit/session behavior. Revisit if a constructor benchmark or target constraint warrants it. |
| `cpp/large-parameter` for 320-byte `SessionContext` | `tests/xcom/validation_session/unit_tests.cpp:991` | Accepted recommendation in a test-only helper. Its by-value argument does not affect production runtime or the tested outcome. A later test-maintenance change may use `const&`; this review does not alter the independently reviewed test cases for that advisory. |

No result is silently suppressed. These dispositions do not claim that CodeQL proves absence of
all defects; they close the two reported recommendations for this exact candidate and query suite.
