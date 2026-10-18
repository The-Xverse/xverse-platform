# Supplemental collector review — before repair

The first collector attempted Maestro payload validation on every accepted Argus
record after fixture teardown. Argus legitimately appends its own abort record,
which has no Maestro extension; the resulting KeyError rejects that collector
attempt. Validate the custom schema only on Maestro annotation records and retain
Argus internal records as reader observations. This is an artifact-only correction;
product and source/installed regression inputs are unchanged. No suite attribution
or complete lifecycle claim is inferred for supplemental retained fixture bytes.
