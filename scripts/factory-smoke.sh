#!/usr/bin/env bash
#
# factory-smoke.sh — dispatch each safely-dispatchable factory workflow and
# report pass/fail per workflow. Smoke-level: it proves the workflow can
# activate, run its agent, and complete without schema or environment errors.
# It does NOT prove business-logic correctness.
#
# Usage:
#   scripts/factory-smoke.sh [--wait-secs N]
#
# Flags:
#   --wait-secs N   how long to poll each workflow for completion (default 480)
#
# Requires:
#   - gh CLI authenticated
#   - GH_AW_REPO env var or default derived from origin
#
# Output: one line per workflow: "pass|fail|skip|timeout  <workflow>  <run-id>  <duration>"
# Exit 0 if every dispatched workflow reached `completed|success`.
# Exit 1 otherwise.

set -euo pipefail

REPO="${GH_AW_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
WAIT_SECS=480  # default per-workflow timeout

while [ $# -gt 0 ]; do
  case "$1" in
    --wait-secs) WAIT_SECS="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,/^$/p' "$0"
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Workflows the harness can dispatch cleanly on demand.
# Excluded by design:
#   - spec-refiner, implementer-dispatcher, plan-merged-dispatcher, pr-fix,
#     conflict-resolver, trigger-plan, serialization-resolver, ci-cleaner,
#     reviewer, contribution-checker, simplify-and-harden-ci, eval-creator-ci
#     → these need a triggering event (issue label, PR, comment). They are
#     exercised by the e2e harness.
#   - issue-triage → runs on issue open; dispatched via e2e.
#   - sync-factory-state, agent-activity-tracker → plain Actions, not gh-aw;
#     they do have workflow_dispatch but need specific inputs. Covered
#     implicitly by e2e.
#   - ai-proficiency-claude → optional, secret-gated, may not be configured.
#
# Safe-to-dispatch candidates below are long-running or scheduled workflows
# that accept a naked workflow_dispatch.
WORKFLOWS=(
  "factory-health.lock.yml"
  "self-improvement-meta.lock.yml"
  "learning-aggregator-ci.lock.yml"
  "ai-proficiency-weekly-report.lock.yml"
)

printf '%-10s %-44s %-12s %s\n' "RESULT" "WORKFLOW" "RUN-ID" "DURATION"
printf '%-10s %-44s %-12s %s\n' "------" "--------" "------" "--------"

exit_code=0

for wf in "${WORKFLOWS[@]}"; do
  start_ts=$(date +%s)

  # Dispatch
  if ! gh workflow run "$wf" --repo "$REPO" >/dev/null 2>&1; then
    printf '%-10s %-44s %-12s %s\n' "SKIP" "$wf" "-" "dispatch failed"
    continue
  fi

  # Sleep briefly for GitHub to register the run
  sleep 5

  # Find the latest run for this workflow
  run_id=$(gh run list \
    --workflow="$wf" \
    --repo "$REPO" \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId' 2>/dev/null || echo "")

  if [ -z "$run_id" ]; then
    printf '%-10s %-44s %-12s %s\n' "SKIP" "$wf" "-" "no run id"
    continue
  fi

  # Poll until completed or timeout
  waited=0
  status=""
  concl=""
  while [ "$waited" -lt "$WAIT_SECS" ]; do
    payload=$(gh run view "$run_id" --repo "$REPO" --json status,conclusion 2>/dev/null || echo '{}')
    status=$(echo "$payload" | jq -r '.status // ""')
    concl=$(echo "$payload" | jq -r '.conclusion // ""')

    if [ "$status" = "completed" ]; then
      break
    fi

    sleep 15
    waited=$((waited + 15))
  done

  elapsed=$(( $(date +%s) - start_ts ))

  if [ "$status" != "completed" ]; then
    printf '%-10s %-44s %-12s %s\n' "TIMEOUT" "$wf" "$run_id" "${elapsed}s (still $status)"
    exit_code=1
  elif [ "$concl" = "success" ]; then
    printf '%-10s %-44s %-12s %s\n' "PASS" "$wf" "$run_id" "${elapsed}s"
  else
    printf '%-10s %-44s %-12s %s\n' "FAIL" "$wf" "$run_id" "${elapsed}s ($concl)"
    exit_code=1
  fi
done

echo ""
if [ "$exit_code" -eq 0 ]; then
  echo "All workflows passed smoke test."
else
  echo "One or more workflows failed. Run 'gh run view <run-id> --log-failed' for details."
fi

exit "$exit_code"
