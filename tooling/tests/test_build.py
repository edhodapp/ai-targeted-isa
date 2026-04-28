"""Tests for build.py — YAML loading, validation, JSON emission, CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_targeted_isa_ontology import build, models


# ---- load_yaml ---------------------------------------------------------


def test_load_yaml_empty_file_returns_empty_dict(tmp_path: Path) -> None:
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    assert build.load_yaml(p) == {}


def test_load_yaml_only_comments_returns_empty_dict(tmp_path: Path) -> None:
    p = tmp_path / "comments.yaml"
    p.write_text("# nothing here\n", encoding="utf-8")
    assert build.load_yaml(p) == {}


def test_load_yaml_returns_mapping(tmp_path: Path) -> None:
    p = tmp_path / "valid.yaml"
    p.write_text("decisions: []\n", encoding="utf-8")
    assert build.load_yaml(p) == {"decisions": []}


def test_load_yaml_rejects_non_mapping_top_level(tmp_path: Path) -> None:
    p = tmp_path / "list.yaml"
    p.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(TypeError, match="must be a mapping"):
        build.load_yaml(p)


def test_load_yaml_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build.load_yaml(tmp_path / "missing.yaml")


# ---- build_ontology / serialize / write_json --------------------------


def test_build_ontology_empty_dict_yields_empty_ontology() -> None:
    o = build.build_ontology({})
    assert o == models.Ontology()


def test_build_ontology_with_one_decision() -> None:
    o = build.build_ontology(
        {
            "decisions": [
                {
                    "id": "d001",
                    "d_number": 1,
                    "name": "Stub",
                    "date_utc": "2026-04-27 18:50 UTC",
                    "summary": "x",
                    "rationale_ref": "DECISIONS.md#d001",
                    "status": "live",
                },
            ],
        },
    )
    assert len(o.decisions) == 1
    assert o.decisions[0].id == "d001"


def test_serialize_is_deterministic() -> None:
    o = models.Ontology()
    body_a = build.serialize(o)
    body_b = build.serialize(o)
    assert body_a == body_b
    assert body_a.endswith("\n")
    # Round-trip through json must parse back to an equivalent object.
    parsed = json.loads(body_a)
    assert build.build_ontology(parsed) == o


def test_write_json_creates_parent_directory(tmp_path: Path) -> None:
    target = tmp_path / "deep/nested/out.json"
    build.write_json(target, '{"x": 1}\n')
    assert target.read_text(encoding="utf-8") == '{"x": 1}\n'


# ---- summarize ---------------------------------------------------------


def test_summarize_counts_each_section() -> None:
    o = models.Ontology(
        decisions=[
            models.Decision(
                id="d001",
                d_number=1,
                name="x",
                date_utc="2026-04-27 18:50 UTC",
                summary="x",
                rationale_ref="DECISIONS.md#d001",
                status="live",
            ),
        ],
    )
    out = build.summarize(o)
    assert "decisions" in out
    assert "1" in out
    assert "isa_features" in out


# ---- main: success / error paths --------------------------------------


def _write_minimal_yaml(path: Path) -> None:
    path.write_text(
        "decisions: []\n"
        "design_principles: []\n"
        "isa_features: []\n"
        "memory_mechanisms: []\n"
        "pipeline_stages: []\n"
        "artifact_types: []\n",
        encoding="utf-8",
    )


def test_main_success_writes_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "in.yaml"
    json_path = tmp_path / "out.json"
    _write_minimal_yaml(yaml_path)
    rc = build.main(["--yaml", str(yaml_path), "--json", str(json_path)])
    assert rc == 0
    assert json.loads(json_path.read_text(encoding="utf-8")) == {
        "decisions": [],
        "design_principles": [],
        "isa_features": [],
        "memory_mechanisms": [],
        "pipeline_stages": [],
        "artifact_types": [],
    }
    out = capsys.readouterr().out
    assert "wrote" in out
    assert "ontology contents" in out


def test_main_missing_yaml_returns_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = build.main(
        [
            "--yaml", str(tmp_path / "missing.yaml"),
            "--json", str(tmp_path / "out.json"),
        ],
    )
    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_main_validation_error_returns_1(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text(
        "isa_features:\n"
        "  - id: x\n"
        "    name: x\n"
        "    description: x\n"
        "    rationale: x\n"
        "    status: spec\n"
        "    category: bogus\n",
        encoding="utf-8",
    )
    rc = build.main(
        [
            "--yaml", str(yaml_path),
            "--json", str(tmp_path / "out.json"),
        ],
    )
    assert rc == 1
    assert "failed to load" in capsys.readouterr().err


def test_main_non_mapping_yaml_returns_1(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "list.yaml"
    yaml_path.write_text("- a\n", encoding="utf-8")
    rc = build.main(
        [
            "--yaml", str(yaml_path),
            "--json", str(tmp_path / "out.json"),
        ],
    )
    assert rc == 1
    assert "must be a mapping" in capsys.readouterr().err


def test_main_yaml_syntax_error_returns_1(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "syntax.yaml"
    yaml_path.write_text("x: [unclosed\n", encoding="utf-8")
    rc = build.main(
        [
            "--yaml", str(yaml_path),
            "--json", str(tmp_path / "out.json"),
        ],
    )
    assert rc == 1
    assert "failed to load" in capsys.readouterr().err


# ---- main --check / _check_in_sync ------------------------------------


def test_main_check_succeeds_when_in_sync(
    tmp_path: Path,
) -> None:
    yaml_path = tmp_path / "in.yaml"
    json_path = tmp_path / "out.json"
    _write_minimal_yaml(yaml_path)
    # First run writes the JSON.
    assert build.main(
        ["--yaml", str(yaml_path), "--json", str(json_path)],
    ) == 0
    # --check must pass against the just-written JSON.
    rc = build.main(
        ["--yaml", str(yaml_path), "--json", str(json_path), "--check"],
    )
    assert rc == 0


def test_main_check_fails_when_json_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "in.yaml"
    _write_minimal_yaml(yaml_path)
    rc = build.main(
        [
            "--yaml", str(yaml_path),
            "--json", str(tmp_path / "missing.json"),
            "--check",
        ],
    )
    assert rc == 3
    assert "does not exist" in capsys.readouterr().err


def test_main_check_fails_when_json_drifts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "in.yaml"
    json_path = tmp_path / "drift.json"
    _write_minimal_yaml(yaml_path)
    # Write an obviously-wrong JSON to force a mismatch.
    json_path.write_text("{}\n", encoding="utf-8")
    rc = build.main(
        ["--yaml", str(yaml_path), "--json", str(json_path), "--check"],
    )
    assert rc == 4
    assert "out of sync" in capsys.readouterr().err
