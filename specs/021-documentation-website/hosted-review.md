# Hosted publication review

## W-DOC-007 — MAJOR — Hosted C++ reference is isolated from the shared search

Observed before repair on deployment of `1fe5e5638cb5a82118fd2c2fdef8c32ad0235b56`, workflow run `40083090309`.

The local Doxygen 1.9.1 output has no language attribute; the generator inserts `en`. GitHub's Ubuntu runner uses a newer Doxygen that emits `lang="en-US"`. The generator preserves that attribute. Pagefind consequently builds separate English indexes: the Starlight home/search UI selects `en`, so C++ query results are absent there even though the C++ pages exist and pass HTTP/link checks.

Reproduction: public `reference/cpp/classxverse_1_1xcom_1_1validation_1_1StimulationGuard.html` contains `<html ... lang="en-US">` and `data-pagefind-body`; the public docs and Python pages use `en`. The production browser script times out waiting for its cross-language C++ result. Basic HTTP checks and manifest identities pass, but that is insufficient for shared-search acceptance.

Required repair: canonicalize the English Doxygen page language to `en` (the Doxyfile is explicitly English), add coverage for native headers with and without language attributes, and reject a split-language index for this English-only site. Rebuild, review, redeploy, and repeat the public browser acceptance script. The user's acceptance/publication authorization covers this deployment compatibility repair; no runtime capability is changed.

## Repair review and local verification

A separate read-only review found no issues in the repair. Native `<html>` attributes are preserved apart from the intentionally normalized language. Missing/split Pagefind indexes fail publication. Eleven contract tests and both hosting-path builds passed; the local index contains only `en`. Source identities and command records are in `evidence/search-repair/`.

The repair stays within the accepted documentation/publication scope and changes no runtime behavior. Final closure requires the successor hosted workflow and production C++ search check; this is not inferred from the local checks.
