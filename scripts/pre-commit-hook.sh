#!/usr/bin/env bash
# Pre-commit hook for ai-targeted-isa.
#
# Runs markdownlint-cli2 on staged markdown files and blocks the commit
# on any lint failure. Mirrors the GitHub Actions check in
# .github/workflows/lint.yml so failures surface locally instead of in CI.
#
# Install (from repo root):
#     ln -sf ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit
#
# Requires markdownlint-cli2 on PATH:
#     sudo npm install -g markdownlint-cli2

set -euo pipefail

# Collect staged markdown files: added, copied, modified, renamed.
# Renames return the new path, which is what we want.
mapfile -t STAGED_MD < <(git diff --cached --name-only --diff-filter=ACMR -- '*.md')

if [[ ${#STAGED_MD[@]} -eq 0 ]]; then
    exit 0
fi

if ! command -v markdownlint-cli2 >/dev/null 2>&1; then
    echo "pre-commit: markdownlint-cli2 not installed." >&2
    echo "  Install: sudo npm install -g markdownlint-cli2" >&2
    exit 1
fi

echo "pre-commit: linting ${#STAGED_MD[@]} staged markdown file(s)..."
markdownlint-cli2 "${STAGED_MD[@]}"
