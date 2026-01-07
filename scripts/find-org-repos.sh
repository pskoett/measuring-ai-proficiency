#!/bin/bash
set -euo pipefail

# find-org-repos.sh - Find active GitHub org repos with AI context artifacts
#
# Usage: ./scripts/find-org-repos.sh <org-name> [--json]
#
# This script searches a GitHub organization for active repositories (with commits
# in the last 90 days) and identifies which ones have context engineering artifacts
# like CLAUDE.md, AGENTS.md, .cursorrules, or .github/copilot-instructions.md.
#
# Requirements:
#   - GitHub CLI (gh) installed and authenticated
#   - jq for JSON processing
#
# Output:
#   - Summary statistics of active repos with artifacts
#   - List of repo URLs to scan with measure-ai-proficiency
#   - Optional JSON output for programmatic use

# Configuration
INSTRUCTION_FILES=(
    "CLAUDE.md"
    "AGENTS.md"
    ".cursorrules"
    ".github/copilot-instructions.md"
    ".github/copilot-instructions.md"
    "CODEX.md"
)

DAYS_ACTIVE=90
JSON_OUTPUT=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <org-name> [--json]"
    echo ""
    echo "Find active repositories in a GitHub organization that have AI context artifacts."
    echo ""
    echo "Arguments:"
    echo "  org-name    GitHub organization name"
    echo "  --json      Output results in JSON format"
    echo ""
    echo "Example:"
    echo "  $0 anthropics"
    echo "  $0 anthropics --json > results.json"
    exit 1
fi

ORG_NAME="$1"
if [ "${2:-}" = "--json" ]; then
    JSON_OUTPUT=true
fi

# Check dependencies
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed."
    echo "Install it from: https://stedolan.github.io/jq/"
    exit 1
fi

# Verify gh authentication
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

# Calculate date threshold (90 days ago)
if date --version &> /dev/null 2>&1; then
    # GNU date
    DATE_THRESHOLD=$(date -d "$DAYS_ACTIVE days ago" +%Y-%m-%d)
else
    # BSD date (macOS)
    DATE_THRESHOLD=$(date -v-${DAYS_ACTIVE}d +%Y-%m-%d)
fi

if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${BOLD}Searching GitHub organization: ${BLUE}$ORG_NAME${NC}"
    echo -e "${BOLD}Activity threshold: ${NC}Commits in last $DAYS_ACTIVE days (since $DATE_THRESHOLD)"
    echo ""
fi

# Temporary files for processing
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

REPOS_FILE="$TEMP_DIR/repos.json"
ACTIVE_REPOS_FILE="$TEMP_DIR/active_repos.txt"
REPOS_WITH_ARTIFACTS_FILE="$TEMP_DIR/repos_with_artifacts.txt"

# Fetch all repositories in the org
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}Fetching repositories from $ORG_NAME...${NC}"
fi

gh repo list "$ORG_NAME" \
    --limit 1000 \
    --json name,url,pushedAt,isArchived,isFork \
    > "$REPOS_FILE"

TOTAL_REPOS=$(jq 'length' "$REPOS_FILE")

if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${GREEN}Found $TOTAL_REPOS repositories${NC}"
    echo ""
fi

# Filter for active repos (not archived, with recent pushes)
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}Filtering for active repositories...${NC}"
fi

jq -r --arg date "$DATE_THRESHOLD" \
    '.[] | select(.isArchived == false and .pushedAt >= $date) | .name' \
    "$REPOS_FILE" > "$ACTIVE_REPOS_FILE"

ACTIVE_COUNT=$(wc -l < "$ACTIVE_REPOS_FILE" | tr -d ' ')

if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${GREEN}Found $ACTIVE_COUNT active repositories (commits since $DATE_THRESHOLD)${NC}"
    echo ""
fi

if [ "$ACTIVE_COUNT" -eq 0 ]; then
    if [ "$JSON_OUTPUT" = true ]; then
        echo '{"org":"'$ORG_NAME'","total_repos":'$TOTAL_REPOS',"active_repos":0,"repos_with_artifacts":0,"percentage":0,"repositories":[]}'
    else
        echo -e "${RED}No active repositories found.${NC}"
    fi
    exit 0
fi

# Check each active repo for instruction files
if [ "$JSON_OUTPUT" = false ]; then
    echo -e "${YELLOW}Checking for AI context artifacts...${NC}"
    echo -e "${YELLOW}Looking for: ${NC}${INSTRUCTION_FILES[*]}"
    echo ""
fi

> "$REPOS_WITH_ARTIFACTS_FILE"  # Clear file

repo_count=0
while IFS= read -r repo_name; do
    ((repo_count++))

    if [ "$JSON_OUTPUT" = false ]; then
        echo -ne "\rProgress: [$repo_count/$ACTIVE_COUNT] Checking: $repo_name..." | cut -c1-80
    fi

    has_artifact=false
    found_files=()

    # Check each instruction file
    for file in "${INSTRUCTION_FILES[@]}"; do
        # Use gh api to check if file exists (faster than cloning)
        if gh api "repos/$ORG_NAME/$repo_name/contents/$file" --silent 2>/dev/null; then
            has_artifact=true
            found_files+=("$file")
        fi
    done

    if [ "$has_artifact" = true ]; then
        repo_url=$(jq -r --arg name "$repo_name" '.[] | select(.name == $name) | .url' "$REPOS_FILE")
        echo "$repo_name|$repo_url|${found_files[*]}" >> "$REPOS_WITH_ARTIFACTS_FILE"
    fi
done < "$ACTIVE_REPOS_FILE"

if [ "$JSON_OUTPUT" = false ]; then
    echo -e "\r\033[K"  # Clear progress line
fi

ARTIFACTS_COUNT=$(wc -l < "$REPOS_WITH_ARTIFACTS_FILE" | tr -d ' ')

# Calculate percentage
if [ "$ACTIVE_COUNT" -gt 0 ]; then
    PERCENTAGE=$(awk "BEGIN {printf \"%.1f\", ($ARTIFACTS_COUNT / $ACTIVE_COUNT) * 100}")
else
    PERCENTAGE=0
fi

# Output results
if [ "$JSON_OUTPUT" = true ]; then
    # JSON output
    echo "{"
    echo "  \"org\": \"$ORG_NAME\","
    echo "  \"scan_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"days_active\": $DAYS_ACTIVE,"
    echo "  \"total_repos\": $TOTAL_REPOS,"
    echo "  \"active_repos\": $ACTIVE_COUNT,"
    echo "  \"repos_with_artifacts\": $ARTIFACTS_COUNT,"
    echo "  \"percentage\": $PERCENTAGE,"
    echo "  \"repositories\": ["

    first=true
    while IFS='|' read -r name url files; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        echo -n "    {\"name\": \"$name\", \"url\": \"$url\", \"artifacts\": ["
        IFS=' ' read -ra file_array <<< "$files"
        file_first=true
        for f in "${file_array[@]}"; do
            if [ "$file_first" = true ]; then
                file_first=false
            else
                echo -n ", "
            fi
            echo -n "\"$f\""
        done
        echo -n "]}"
    done < "$REPOS_WITH_ARTIFACTS_FILE"

    echo ""
    echo "  ]"
    echo "}"
else
    # Human-readable output
    echo -e "${BOLD}=== Results ===${NC}"
    echo ""
    echo -e "${BOLD}Organization:${NC} $ORG_NAME"
    echo -e "${BOLD}Total repositories:${NC} $TOTAL_REPOS"
    echo -e "${BOLD}Active repositories:${NC} $ACTIVE_COUNT (commits in last $DAYS_ACTIVE days)"
    echo -e "${BOLD}Repos with AI context artifacts:${NC} $ARTIFACTS_COUNT"
    echo ""

    if [ "$ARTIFACTS_COUNT" -gt 0 ]; then
        echo -e "${GREEN}${BOLD}✓ ${PERCENTAGE}% of active repositories have context engineering artifacts${NC}"
    else
        echo -e "${RED}${BOLD}✗ 0% of active repositories have context engineering artifacts${NC}"
    fi

    echo ""
    echo -e "${BOLD}=== Repositories to Scan ===${NC}"
    echo ""

    if [ "$ARTIFACTS_COUNT" -gt 0 ]; then
        while IFS='|' read -r name url files; do
            echo -e "${BLUE}$name${NC}"
            echo -e "  URL: $url"
            echo -e "  Artifacts: ${GREEN}$files${NC}"
            echo ""
        done < "$REPOS_WITH_ARTIFACTS_FILE"

        echo -e "${BOLD}To scan these repositories:${NC}"
        echo ""
        echo -e "  # Clone and scan individual repo:"
        echo -e "  git clone <repo-url>"
        echo -e "  cd <repo-name>"
        echo -e "  measure-ai-proficiency ."
        echo ""
        echo -e "  # Or scan all at once (requires repos to be cloned):"
        while IFS='|' read -r name url files; do
            echo "  # git clone $url"
        done < "$REPOS_WITH_ARTIFACTS_FILE"
        echo "  measure-ai-proficiency */"
    else
        echo -e "${YELLOW}No repositories found with AI context artifacts.${NC}"
        echo ""
        echo -e "Consider creating context engineering files in your active repositories:"
        echo -e "  - ${BOLD}CLAUDE.md${NC} - Instructions for Claude Code"
        echo -e "  - ${BOLD}AGENTS.md${NC} - Generic AI agent instructions"
        echo -e "  - ${BOLD}.cursorrules${NC} - Instructions for Cursor"
        echo -e "  - ${BOLD}.github/copilot-instructions.md${NC} - Instructions for GitHub Copilot"
    fi
fi
