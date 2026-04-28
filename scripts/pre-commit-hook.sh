#!/usr/bin/env bash
# Pre-commit hook for ai-targeted-isa.
#
# Runs lint and quality gates on staged files and blocks the commit on
# any failure. Two artifact types covered today:
#   - markdown: markdownlint-cli2
#   - python:   flake8 + pylint + mypy + pytest (in tooling/.venv/)
#
# Mirrors the GitHub Actions checks in .github/workflows/lint.yml so
# failures surface locally instead of in CI.
#
# Install (from repo root):
#     ln -sf ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit
#
# Setup (one-time per clone):
#     # Markdown:
#     sudo npm install -g markdownlint-cli2
#     # Python:
#     python3 -m venv tooling/.venv
#     tooling/.venv/bin/pip install -e ".[dev]"

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ---- Markdown gate ------------------------------------------------------

mapfile -t STAGED_MD < <(
    git diff --cached --name-only --diff-filter=ACMR -- '*.md'
)

if [[ ${#STAGED_MD[@]} -gt 0 ]]; then
    if ! command -v markdownlint-cli2 >/dev/null 2>&1; then
        echo "pre-commit: markdownlint-cli2 not installed." >&2
        echo "  Install: sudo npm install -g markdownlint-cli2" >&2
        exit 1
    fi
    echo "pre-commit: linting ${#STAGED_MD[@]} staged markdown file(s)..."
    markdownlint-cli2 "${STAGED_MD[@]}"
fi

# ---- Python gate --------------------------------------------------------

mapfile -t STAGED_PY < <(
    git diff --cached --name-only --diff-filter=ACMR -- '*.py'
)

if [[ ${#STAGED_PY[@]} -gt 0 ]]; then
    VENV="tooling/.venv"
    if [[ ! -x "$VENV/bin/python" ]]; then
        echo "pre-commit: Python venv not found at $VENV/." >&2
        echo "  Setup: python3 -m venv $VENV \\" >&2
        echo "      && $VENV/bin/pip install -e '.[dev]'" >&2
        exit 1
    fi

    echo "pre-commit: ${#STAGED_PY[@]} staged Python file(s); running gates..."

    # flake8: cheap, runs on the configured path; OK if the path has no
    # .py yet (it just exits 0 with no findings).
    # Scope explicitly to tooling/src and tooling/tests so the gates
    # never walk into tooling/.venv (third-party packages would
    # otherwise get linted).
    echo "  flake8..."
    "$VENV/bin/flake8" tooling/src tooling/tests

    # Dynamically build the dir list from those that actually have .py
    # files so pylint and mypy don't error on empty directories.
    PY_DIRS=()
    for d in tooling/src tooling/tests; do
        if [[ -n "$(find "$d" -type f -name '*.py' 2>/dev/null)" ]]; then
            PY_DIRS+=("$d")
        fi
    done
    if [[ ${#PY_DIRS[@]} -gt 0 ]]; then
        echo "  pylint..."
        "$VENV/bin/pylint" --rcfile=pylintrc "${PY_DIRS[@]}"

        echo "  mypy --strict..."
        "$VENV/bin/mypy" "${PY_DIRS[@]}"
    fi

    # pytest: skip cleanly when no tests are present (exit code 5).
    TEST_COUNT=$(
        find tooling/tests -type f -name 'test_*.py' 2>/dev/null | wc -l
    )
    if [[ "$TEST_COUNT" -gt 0 ]]; then
        echo "  pytest..."
        "$VENV/bin/pytest"
    fi
fi

exit 0
