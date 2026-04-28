"""CLI entry: ``audit-ai-isa-ontology``.

Loads the ontology JSON, runs the audit, renders the report, and
exits with a code suitable for CI: 0 clean, 1 violations found,
2 ontology load failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ai_isa_audit.audit import load_ontology, run_audit
from ai_isa_audit.formatter import render_json, render_text
from ai_isa_audit.types import AuditReport

DEFAULT_ONTOLOGY_PATH = Path("ontology/ai-targeted-isa.json")


def main(argv: list[str] | None = None) -> int:
    """CLI entry. 0 = clean; 1 = violations; 2 = load failure."""
    args = _parse_args(argv)
    try:
        ontology = load_ontology(args.ontology)
    except FileNotFoundError:
        print(
            f"error: ontology JSON not found: {args.ontology}",
            file=sys.stderr,
        )
        return 2
    except (ValidationError, json.JSONDecodeError) as exc:
        print(
            f"error: failed to load {args.ontology}:\n{exc}",
            file=sys.stderr,
        )
        return 2
    report = run_audit(ontology, args.repo_root)
    sys.stdout.write(_render(report, args.format))
    return 1 if report.has_any_gap else 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="audit-ai-isa-ontology",
        description=(
            "Audit the ai-targeted-isa ontology JSON against the repo: "
            "resolve every ref, check consistency rules, exit non-zero "
            "on any gap."
        ),
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        default=DEFAULT_ONTOLOGY_PATH,
        help=f"Built JSON path (default: {DEFAULT_ONTOLOGY_PATH})",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repo root that refs resolve against (default: cwd)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format (default: text)",
    )
    return parser.parse_args(argv)


def _render(report: AuditReport, fmt: str) -> str:
    if fmt == "json":
        return render_json(report)
    return render_text(report)
