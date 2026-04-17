#!/usr/bin/env bash
# scripts/check-workflow-lock-sync.sh
#
# Validates that each .github/workflows/*.md source file is in sync with its
# compiled .lock.yml counterpart.
#
# Strategy
# --------
# 1. Prefer 'gh aw compile --check-only' when the installed gh-aw version
#    supports it. This path is read-only, version-agnostic, and has no side
#    effects. Chosen because it relies directly on the tool that owns the hash
#    format rather than reimplementing it.
#
# 2. Fallback: run 'gh aw compile' in the working tree and use 'git diff' to
#    detect which lock files changed. Does not commit or push anything. In CI
#    the checkout is ephemeral. Locally, run:
#      git restore .github/workflows/*.lock.yml
#    to undo the side-effects of the compilation step.
#    Chosen as fallback because it reuses the same hash logic that generated
#    the checked-in files; no reimplementation needed.
#
# Exit codes
# ----------
# 0  All workflow lock files are in sync.
# 1  One or more lock files are stale. See output for repair commands.
# 2  gh CLI or gh-aw extension is not installed.
#
# Refs: pskoett/measuring-ai-proficiency#95

set -euo pipefail

WORKFLOWS_DIR=".github/workflows"
ISSUE_REF="pskoett/measuring-ai-proficiency#95"

die() { echo "ERROR: $*" >&2; exit 1; }

# Run from the repo root so all relative paths are consistent.
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) \
  || die "'git rev-parse' failed. Run this script from inside the repository."
cd "$REPO_ROOT"

# ── verify tooling ────────────────────────────────────────────────────────────

if ! command -v gh &>/dev/null; then
  die "'gh' CLI is not installed. See https://cli.github.com/ then run: gh extension install github/gh-aw"
fi

if ! gh aw --version &>/dev/null; then
  die "'gh aw' extension is not installed. Run: gh extension install github/gh-aw"
fi

# ── count workflow pairs ──────────────────────────────────────────────────────

PAIR_COUNT=0
for md in "${WORKFLOWS_DIR}"/*.md; do
  [ -f "$md" ] || continue
  lock="${md%.md}.lock.yml"
  [ -f "$lock" ] && PAIR_COUNT=$((PAIR_COUNT + 1))
done

if [ "$PAIR_COUNT" -eq 0 ]; then
  echo "No .md/.lock.yml pairs found in ${WORKFLOWS_DIR}/. Nothing to check."
  exit 0
fi

echo "Checking ${PAIR_COUNT} workflow pair(s) in ${WORKFLOWS_DIR}/..."
echo ""

# ── strategy 1: native --check-only ──────────────────────────────────────────
#
# Detect support by consulting the help text. This is more reliable than
# parsing error messages, which vary across versions and locales. If the flag
# is listed in help, run it and forward the result. If the flag is not in help,
# fall through to the compile-and-diff fallback.

if gh aw compile --help | grep -q -- "--check-only"; then
  echo "Strategy: native 'gh aw compile --check-only' (read-only, no side effects)"
  echo ""
  CHECK_ONLY_OUT=$(gh aw compile --check-only 2>&1) || CHECK_ONLY_RC=$?
  CHECK_ONLY_RC=${CHECK_ONLY_RC:-0}
  echo "$CHECK_ONLY_OUT"
  if [ "$CHECK_ONLY_RC" -eq 0 ]; then
    echo ""
    echo "All workflow lock files are in sync."
    exit 0
  else
    echo ""
    echo "One or more workflow lock files are out of sync. Run the repair commands above."
    echo "Refs ${ISSUE_REF}"
    exit 1
  fi
else
  echo "Note: 'gh aw compile --check-only' is not listed in 'gh aw compile --help'."
  echo "  Switching to compile-and-diff fallback."
  echo ""
fi

# ── strategy 2: compile-and-diff fallback ────────────────────────────────────

echo "Strategy: fallback (compile + git diff)"
echo "  Running 'gh aw compile' and checking for changes to .lock.yml files."
echo "  In CI the checkout is ephemeral. Locally, restore modified files with:"
echo "    git restore .github/workflows/*.lock.yml"
echo ""

# Run compile. Capture output for diagnostics on failure.
if ! COMPILE_OUT=$(gh aw compile 2>&1); then
  echo "ERROR: 'gh aw compile' failed:"
  echo "$COMPILE_OUT" | sed 's/^/  /'
  exit 1
fi

# Detect lock files that were modified by the compile step.
STALE_FILES=()
while IFS= read -r f; do
  [ -n "$f" ] && STALE_FILES+=("$f")
done < <(git diff --name-only -- "${WORKFLOWS_DIR}"/*.lock.yml 2>/dev/null || true)

if [ "${#STALE_FILES[@]}" -eq 0 ]; then
  echo "All workflow lock files are in sync."
  exit 0
fi

echo "ERROR: ${#STALE_FILES[@]} workflow lock file(s) are out of sync:"
echo ""

for lock_file in "${STALE_FILES[@]}"; do
  md_file="${lock_file%.lock.yml}.md"
  workflow_name=$(basename "${lock_file%.lock.yml}")
  echo "  Stale pair:"
  echo "    Source : ${md_file}"
  echo "    Lock   : ${lock_file}"
  echo "    Repair : gh aw compile ${workflow_name}"
  echo ""
done

echo "To repair all stale files at once:"
echo "  gh aw compile"
echo "  git add .github/workflows/*.lock.yml"
echo "  git commit -m 'chore: recompile workflow lock files'"
echo ""
echo "Refs ${ISSUE_REF}"
exit 1
