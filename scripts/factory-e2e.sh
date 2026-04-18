#!/usr/bin/env bash
#
# factory-e2e.sh — files a canary issue and watches it through the factory
# chain. Reports which stages the factory completed within the time budget.
# Cleans up by closing the issue + any spawned PRs at the end.
#
# Usage:
#   scripts/factory-e2e.sh [--stage STAGE] [--keep]
#
# Flags:
#   --stage STAGE   stop after this stage (triage|spec|plan|impl|full, default: plan)
#   --keep          don't clean up at the end (leave issue + PRs open for inspection)
#
# What the stages cover:
#   triage    issue-triage fires, labels are applied
#   spec      add needs-spec, watch spec-refiner produce plan PR or direct route
#   plan      merge plan PR, watch plan-merged-dispatcher write checklist
#   impl      watch implementer-dispatcher assign Copilot
#   full      watch Copilot open an impl PR (long — 20+ min, may not complete)
#
# Default stop is `plan` because that's the last step the test can drive
# without involving a real Copilot coding run.
#
# Requires:
#   - gh CLI authenticated
#   - GH_AW_REPO env var or default derived from origin
#
# Exit 0 if every attempted stage transition happened within its timeout.
# Exit 1 otherwise.

set -euo pipefail

REPO="${GH_AW_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
STAGE="plan"
KEEP=false

while [ $# -gt 0 ]; do
  case "$1" in
    --stage) STAGE="$2"; shift 2 ;;
    --keep)  KEEP=true; shift ;;
    -h|--help) sed -n '2,/^$/p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

CANARY_ID="smoke-$(date -u +%Y%m%dT%H%M%SZ)"
ISSUE_TITLE="[smoke-test] factory e2e $CANARY_ID"
ISSUE_BODY="Factory e2e test. The harness closes the issue and sweeps any spawned PR on exit.

**Canary ID**: \`$CANARY_ID\`
**Proposed change**: add the line \`<!-- factory-smoke-$CANARY_ID -->\` to the end of \`docs/plans/README.md\`. One-line append, no other edits.

Run by: \`scripts/factory-e2e.sh\`"

ISSUE_NUM=""
PR_NUM=""
exit_code=0

cleanup() {
  echo ""
  if [ "$KEEP" = true ]; then
    echo "--keep set; leaving issue #${ISSUE_NUM:-?} and PR #${PR_NUM:-?} open for inspection."
    return
  fi
  if [ -n "$PR_NUM" ]; then
    echo "Closing PR #$PR_NUM..."
    gh pr close "$PR_NUM" --repo "$REPO" --comment "factory-e2e cleanup: closing canary PR." >/dev/null 2>&1 || true
  fi
  if [ -n "$ISSUE_NUM" ]; then
    echo "Closing issue #$ISSUE_NUM..."
    gh issue close "$ISSUE_NUM" --repo "$REPO" --reason "not planned" \
      --comment "factory-e2e cleanup: canary $CANARY_ID completed." >/dev/null 2>&1 || true
  fi
  # Belt-and-suspenders sweep: Copilot may open a PR after we close the
  # issue (race condition observed on 2026-04-18). Find and close any PR
  # whose body references our canary ID and delete its branch.
  if [ -n "$CANARY_ID" ]; then
    echo "Sweeping for late Copilot PRs matching canary $CANARY_ID..."
    for lingering_pr in $(gh pr list --repo "$REPO" --state open \
      --json number,body,headRefName \
      --jq ".[] | select(.body | test(\"$CANARY_ID\")) | .number" 2>/dev/null); do
      echo "  closing late PR #$lingering_pr"
      gh pr close "$lingering_pr" --repo "$REPO" --delete-branch \
        --comment "factory-e2e cleanup: canary $CANARY_ID post-exit sweep." >/dev/null 2>&1 || true
    done
  fi
}
trap cleanup EXIT

# Poll helper: wait up to $2 seconds for a predicate command to return 0.
# Returns the elapsed seconds on success, or the timeout value on failure.
wait_for() {
  local label="$1"
  local timeout="$2"
  local cmd="$3"
  local waited=0
  local start_ts
  start_ts=$(date +%s)

  while [ "$waited" -lt "$timeout" ]; do
    if bash -c "$cmd" >/dev/null 2>&1; then
      local elapsed=$(( $(date +%s) - start_ts ))
      printf '  %-40s PASS (%ds)\n' "$label" "$elapsed"
      return 0
    fi
    sleep 10
    waited=$((waited + 10))
  done

  printf '  %-40s TIMEOUT (%ds)\n' "$label" "$timeout"
  return 1
}

stage_at_least() {
  case "$STAGE" in
    triage) return 1 ;;
    spec)   [ "$1" = "triage" ] ;;
    plan)   [ "$1" = "triage" ] || [ "$1" = "spec" ] ;;
    impl)   [ "$1" = "triage" ] || [ "$1" = "spec" ] || [ "$1" = "plan" ] ;;
    full)   return 0 ;;
    *)      echo "unknown stage: $STAGE" >&2; exit 2 ;;
  esac
}

echo "=== factory-e2e: $CANARY_ID ==="
echo "Repo:  $REPO"
echo "Stage: $STAGE"
echo ""

# --- Stage 1: file issue ---------------------------------------------------
echo "Filing canary issue..."
ISSUE_URL=$(gh issue create --repo "$REPO" --title "$ISSUE_TITLE" --body "$ISSUE_BODY" 2>&1 | tail -1)
ISSUE_NUM=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')
if [ -z "$ISSUE_NUM" ]; then
  echo "Failed to create issue. Output: $ISSUE_URL" >&2
  exit 1
fi
echo "Filed #$ISSUE_NUM: $ISSUE_URL"
echo ""

# --- Stage triage ----------------------------------------------------------
# Success signal is that issue-triage RAN and posted its analysis comment.
# Labels are not required — triage may legitimately noop for canary issues
# (it reads the body and classifies as automated test, chooses not to
# apply a category label). That's correct behaviour, not a failure.
echo "--- Stage: triage ---"
wait_for "issue-triage posted analysis comment" 180 \
  "gh issue view $ISSUE_NUM --repo $REPO --json comments --jq '[.comments[] | select(.author.login == \"github-actions\")] | length > 0' | grep -q true" \
  || exit_code=1

if ! stage_at_least "triage"; then
  echo ""; echo "Stopped at stage: triage"; exit $exit_code
fi

# --- Stage spec ------------------------------------------------------------
echo ""
echo "--- Stage: spec ---"
gh issue edit "$ISSUE_NUM" --repo "$REPO" --add-label "needs-spec" >/dev/null 2>&1
wait_for "needs-spec removed (spec-refiner fired)" 300 \
  "! gh issue view $ISSUE_NUM --repo $REPO --json labels --jq '[.labels[].name]' | grep -q needs-spec" \
  || exit_code=1

# spec-refiner either:
#   (a) plan-worthy: labels needs-plan + impl:copilot, opens a plan PR
#   (b) direct-route: labels impl:copilot + ready-for-implementation
#   (c) blocked: labels blocked-on-human
post_spec_labels=$(gh issue view "$ISSUE_NUM" --repo "$REPO" --json labels --jq '[.labels[].name] | join(",")')
echo "  post-spec labels: $post_spec_labels"

if echo "$post_spec_labels" | grep -q "blocked-on-human"; then
  echo "  spec-refiner classified as blocked. Stopping here."
  if ! stage_at_least "spec"; then exit $exit_code; fi
  exit 0
fi

if ! stage_at_least "spec"; then
  echo ""; echo "Stopped at stage: spec"; exit $exit_code
fi

# --- Stage plan ------------------------------------------------------------
echo ""
echo "--- Stage: plan ---"
if echo "$post_spec_labels" | grep -q "ready-for-implementation"; then
  echo "  direct-route: skipping plan merge (no plan PR produced)."
elif echo "$post_spec_labels" | grep -q "needs-plan"; then
  # Find plan PR referencing this issue
  wait_for "spec-refiner opened plan PR" 120 \
    "gh pr list --repo $REPO --state open --json number,body --jq '.[] | select(.body | test(\"#$ISSUE_NUM\\\\b\")) | .number' | head -1 | grep -qE '^[0-9]+\$'" \
    || exit_code=1

  PR_NUM=$(gh pr list --repo "$REPO" --state open --json number,body \
    --jq ".[] | select(.body | test(\"#$ISSUE_NUM\\\\b\")) | .number" | head -1)
  echo "  plan PR: #$PR_NUM"

  # Merge the plan PR (the harness has to do this — no human gate in a test)
  echo "  merging plan PR #$PR_NUM..."
  gh pr merge "$PR_NUM" --repo "$REPO" --squash --admin >/dev/null 2>&1 || {
    echo "  merge failed. Leaving PR open."
    exit_code=1
  }

  wait_for "plan-merged-dispatcher added ready-for-implementation" 180 \
    "gh issue view $ISSUE_NUM --repo $REPO --json labels --jq '[.labels[].name]' | grep -q ready-for-implementation" \
    || exit_code=1
fi

if ! stage_at_least "plan"; then
  echo ""; echo "Stopped at stage: plan"; exit $exit_code
fi

# --- Stage impl ------------------------------------------------------------
echo ""
echo "--- Stage: impl ---"
wait_for "implementer-dispatcher assigned Copilot" 180 \
  "gh issue view $ISSUE_NUM --repo $REPO --json labels --jq '[.labels[].name]' | grep -q assigned-to-agent" \
  || exit_code=1

if ! stage_at_least "impl"; then
  echo ""; echo "Stopped at stage: impl"; exit $exit_code
fi

# --- Stage full ------------------------------------------------------------
echo ""
echo "--- Stage: full ---"
echo "  Waiting for Copilot to open impl PR (up to 20 min)..."
wait_for "Copilot opened impl PR" 1200 \
  "gh pr list --repo $REPO --state open --json number,body,headRefName --jq '.[] | select((.body | test(\"#$ISSUE_NUM\\\\b\")) and (.headRefName | test(\"copilot/\"))) | .number' | head -1 | grep -qE '^[0-9]+\$'" \
  || exit_code=1

echo ""
echo "=== factory-e2e complete ==="
exit $exit_code
