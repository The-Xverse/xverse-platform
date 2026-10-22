#!/bin/bash
# Increment19 finding 467: rerun, once, the 12 tests that failed inside run v's nested Argus suite,
# from run v's frozen tree and installed venv (no PYTHONPATH except the observation-only guard trace
# plugin), on the naturally loaded host (llama-server of another project). Observation only; no retry
# loop; nothing outside the output directory and /dev/shm is written.
set -u
HERE=$(dirname "$(realpath "$0")")
W=/dev/shm/maestro-platform-20261021t-pjnlpns7
OUT=$(realpath "$1"); mkdir -p "$OUT"
BT=$(mktemp -d /dev/shm/affa19-v-rerun-XXXX)
cat /proc/loadavg > "$OUT/load-at-launch.txt"
cd "$W/tree"
env -u PYTEST_ADDOPTS PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_PLUGINS=maestro_receipt_namespace,guard_trace_plugin PYTHONPATH="$HERE/guard-trace" \
  GUARD_TRACE_OUT="$OUT/guard-trace.jsonl" TMPDIR="$BT" MAESTRO_FULL_RECEIPT_ROOT="$BT/receipts" MAESTRO_BOUNDARY_RECEIPTS="$BT/receipts" \
  "$W/venv/bin/python" -m pytest -q -ra -p no:cacheprovider --basetemp "$BT/basetemp" \
  "tests/thesis_lite/maestro/test_active_transitive_restart.py::test_original_transitive_cohort_retains_unrelated_and_all_generations[cleaned-leaf]" \
  "tests/thesis_lite/maestro/test_composed_persistence_termination.py::test_original_intent_frontier_loader_and_loss[disabled]" \
  "tests/thesis_lite/maestro/test_launcher_composition.py::test_actual_original_startup_through_terminal_and_helper_closure[closed]" \
  "tests/thesis_lite/maestro/test_launcher_composition.py::test_actual_original_startup_through_terminal_and_helper_closure[lost-close-ack]" \
  "tests/thesis_lite/maestro/test_lazy_dispatcher.py::test_actual_lazy_nominal_stages_only_at_eligible_start_then_collects_before_terminal" \
  "tests/thesis_lite/maestro/test_lazy_dispatcher.py::test_actual_worker_rejects_handle_free_productive_completion_or_observe[step-complete]" \
  "tests/thesis_lite/maestro/test_native_writer_stream_faults.py::test_native_stream_fault_preserves_public_writer_and_original_cleanup[loader-only]" \
  "tests/thesis_lite/maestro/test_native_writer_stream_faults.py::test_native_stream_fault_preserves_public_writer_and_original_cleanup[seeded-flush-once]" \
  "tests/thesis_lite/maestro/test_native_writer_stream_faults.py::test_native_stream_fault_preserves_public_writer_and_original_cleanup[seeded-flush-persistent]" \
  "tests/thesis_lite/maestro/test_shared_dispatcher.py::test_paused_shared_ticks_renew_both_original_leases_and_observe_health" \
  "tests/thesis_lite/maestro/test_terminal_controller_inventory.py::test_original_terminal_report_keeps_retired_current_controllers_and_future_universe[successor-live]" \
  "tests/thesis_lite/maestro/test_terminal_controller_inventory.py::test_original_terminal_report_keeps_retired_current_controllers_and_future_universe[successor-dead]" \
  > "$OUT/rerun.log" 2>&1
echo "returncode=$?" >> "$OUT/rerun.log"
cat /proc/loadavg > "$OUT/load-at-end.txt"
ps -eo pid,etimes,pcpu,rss,comm --sort=-pcpu | head -8 >> "$OUT/load-at-end.txt"
rm -rf "$BT"
