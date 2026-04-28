#!/usr/bin/env bash
# scripts/setup-venv.sh — set up the Python development environment.
#
# Default behaviour: create tooling/.venv via the stdlib `python -m venv`
# and install dev dependencies via pip in editable mode. Idempotent: if
# the venv already exists, only the install step runs.
#
# Override knobs (environment variables):
#
#   PYTHON      Python interpreter to seed the venv with.
#               Default: python3 (must be >= 3.11).
#               Examples: PYTHON=python3.12, PYTHON=python3.13
#
#   VENV_DIR    Where to create the venv.
#               Default: tooling/.venv (where pre-commit hook + CI look).
#               If you set this to anything else, the script will warn
#               and suggest a symlink.
#
#   VENV_TOOL   How to make the venv:
#                 stdlib      python -m venv (default; no extras)
#                 virtualenv  virtualenv (older alternative)
#                 uv          uv venv (Astral; very fast; needs uv)
#
#   INSTALLER   How to install dev deps after the venv exists:
#                 pip         pip install -e ".[dev]"  (default)
#                 uv          uv pip install -e ".[dev]"  (faster)
#
# Examples:
#   ./scripts/setup-venv.sh
#   PYTHON=python3.13 ./scripts/setup-venv.sh
#   VENV_TOOL=uv INSTALLER=uv ./scripts/setup-venv.sh
#   VENV_DIR=$HOME/.virtualenvs/ai-isa ./scripts/setup-venv.sh
#
# After it finishes, activate with:
#   source tooling/.venv/bin/activate
# (or whatever VENV_DIR you chose).

set -euo pipefail

PYTHON="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-tooling/.venv}"
VENV_TOOL="${VENV_TOOL:-stdlib}"
INSTALLER="${INSTALLER:-pip}"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# ---- Create venv if missing --------------------------------------------

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "==> Creating venv in $VENV_DIR (tool=$VENV_TOOL)..."
    case "$VENV_TOOL" in
        stdlib)
            "$PYTHON" -m venv "$VENV_DIR"
            ;;
        virtualenv)
            command -v virtualenv >/dev/null \
                || { echo "virtualenv not on PATH; install via pip first." >&2; exit 1; }
            virtualenv -p "$PYTHON" "$VENV_DIR"
            ;;
        uv)
            command -v uv >/dev/null \
                || { echo "uv not on PATH; see https://docs.astral.sh/uv/" >&2; exit 1; }
            uv venv --python "$PYTHON" "$VENV_DIR"
            ;;
        *)
            echo "Unknown VENV_TOOL: $VENV_TOOL" >&2
            echo "Valid: stdlib | virtualenv | uv" >&2
            exit 1
            ;;
    esac
else
    echo "==> Venv already exists at $VENV_DIR; skipping creation."
fi

# ---- Install dev deps in editable mode ---------------------------------

echo "==> Installing dev dependencies via $INSTALLER..."
case "$INSTALLER" in
    pip)
        "$VENV_DIR/bin/python" -m pip install --upgrade pip
        "$VENV_DIR/bin/pip" install -e ".[dev]"
        ;;
    uv)
        command -v uv >/dev/null \
            || { echo "uv not on PATH; see https://docs.astral.sh/uv/" >&2; exit 1; }
        uv pip install --python "$VENV_DIR/bin/python" -e ".[dev]"
        ;;
    *)
        echo "Unknown INSTALLER: $INSTALLER" >&2
        echo "Valid: pip | uv" >&2
        exit 1
        ;;
esac

# ---- Warn if venv is not where the hook + CI expect --------------------

if [[ "$VENV_DIR" != "tooling/.venv" ]]; then
    echo ""
    echo "WARNING: VENV_DIR=$VENV_DIR is NOT tooling/.venv."
    echo "  The pre-commit hook and the CI workflow both look at"
    echo "  tooling/.venv. To make local hooks work, symlink it:"
    echo "      ln -s '$VENV_DIR' tooling/.venv"
fi

echo ""
echo "==> Done. Activate with:  source $VENV_DIR/bin/activate"
