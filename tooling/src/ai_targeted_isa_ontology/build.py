"""Build tool: YAML source → validated JSON snapshot.

Reads `ontology/ai-targeted-isa.yaml`, parses it via the pydantic
schema in `models.py`, and writes the canonical JSON form to
`ontology/ai-targeted-isa.json`. Per D009 the JSON is committed to
git; git history is the version history.

CLI:
    python -m ai_targeted_isa_ontology
    python -m ai_targeted_isa_ontology --yaml=path --json=path
    build-ai-isa-ontology  (console script)

Exits 0 on success; non-zero on parse or validation error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ai_targeted_isa_ontology.models import Ontology

DEFAULT_YAML_PATH = Path("ontology/ai-targeted-isa.yaml")
DEFAULT_JSON_PATH = Path("ontology/ai-targeted-isa.json")


def load_yaml(path: Path) -> dict[str, Any]:
    """Read YAML from path; treat empty/missing-content as empty dict.

    Raises FileNotFoundError if the path doesn't exist (caller decides
    whether that's fatal or means "first build").
    """
    text = path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(text)
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise TypeError(
            f"{path}: top-level YAML must be a mapping, got "
            f"{type(parsed).__name__}"
        )
    return parsed


def build_ontology(data: dict[str, Any]) -> Ontology:
    """Validate raw dict against the schema."""
    return Ontology.model_validate(data)


def serialize(ontology: Ontology) -> str:
    """Return the canonical JSON form (deterministic, indent=2)."""
    payload = ontology.model_dump(mode="json")
    body = json.dumps(payload, indent=2, sort_keys=True)
    return body + "\n"


def write_json(path: Path, body: str) -> None:
    """Create parent dir if needed and write atomically-ish."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def summarize(ontology: Ontology) -> str:
    """Human-readable counts for the build's stdout report."""
    pairs = [
        ("decisions", len(ontology.decisions)),
        ("design_principles", len(ontology.design_principles)),
        ("isa_features", len(ontology.isa_features)),
        ("memory_mechanisms", len(ontology.memory_mechanisms)),
        ("pipeline_stages", len(ontology.pipeline_stages)),
        ("artifact_types", len(ontology.artifact_types)),
    ]
    rows = [f"  {name:<20} {count:>4}" for name, count in pairs]
    return "\n".join(["ontology contents:", *rows])


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build-ai-isa-ontology",
        description=(
            "Validate the ai-targeted-isa ontology YAML and write "
            "the canonical JSON snapshot."
        ),
    )
    parser.add_argument(
        "--yaml",
        type=Path,
        default=DEFAULT_YAML_PATH,
        help=f"YAML source path (default: {DEFAULT_YAML_PATH})",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help=f"JSON output path (default: {DEFAULT_JSON_PATH})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Validate only; do not write. Exits non-zero if the "
            "existing JSON differs from a freshly built one."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry. Returns 0 on success, non-zero on failure."""
    args = _parse_args(argv)
    try:
        ontology = build_ontology(load_yaml(args.yaml))
    except FileNotFoundError:
        print(f"error: YAML source not found: {args.yaml}", file=sys.stderr)
        return 2
    except (ValidationError, TypeError, yaml.YAMLError) as exc:
        print(f"error: failed to load {args.yaml}:\n{exc}", file=sys.stderr)
        return 1
    body = serialize(ontology)
    if args.check:
        return _check_in_sync(args.json, body)
    write_json(args.json, body)
    print(summarize(ontology))
    print(f"wrote {args.json}")
    return 0


def _check_in_sync(json_path: Path, fresh_body: str) -> int:
    """Compare an existing JSON file with a freshly built body."""
    if not json_path.exists():
        print(
            f"error: --check given but {json_path} does not exist; "
            "run without --check to create it.",
            file=sys.stderr,
        )
        return 3
    on_disk = json_path.read_text(encoding="utf-8")
    if on_disk != fresh_body:
        print(
            f"error: {json_path} is out of sync with the YAML source; "
            "run the build tool without --check to refresh it.",
            file=sys.stderr,
        )
        return 4
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
