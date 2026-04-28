"""Tests for ai_isa_audit.formatter and ai_isa_audit.cli."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_isa_audit import cli, formatter
from ai_isa_audit.types import (
    AuditReport,
    ConstraintReport,
    ParsedRef,
    Resolution,
    ResolvedRef,
    Summary,
)


def _ok_ref(path: str = "x.md") -> ResolvedRef:
    return ResolvedRef(
        original=path,
        parsed=ParsedRef(path=path, fragment=None, symbol=None),
        resolution=Resolution.OK,
        detail="",
    )


def _bad_ref(path: str = "missing.md") -> ResolvedRef:
    return ResolvedRef(
        original=path,
        parsed=ParsedRef(path=path, fragment=None, symbol=None),
        resolution=Resolution.FILE_MISSING,
        detail=f"path does not exist: {path}",
    )


# ---- formatter.render_text --------------------------------------------


def test_text_empty_report_says_no_gaps() -> None:
    rep = AuditReport()
    text = formatter.render_text(rep)
    assert "no gaps" in text
    assert "rows                    0" in text


def test_text_lists_rows_with_gaps() -> None:
    bad = ConstraintReport(
        kind="decision", id="d001", name="Stub", status="live",
        refs=[_bad_ref()], consistency_violations=[],
    )
    summary = Summary(
        total_rows=1, rows_with_gap=1, refs_total=1, refs_file_missing=1,
    )
    rep = AuditReport(rows=[bad], summary=summary)
    text = formatter.render_text(rep)
    assert "decision 'd001'" in text
    assert "file_missing" in text
    assert "missing.md" in text


def test_text_skips_ok_refs_within_a_failed_row() -> None:
    """Inside a row with mixed refs, only the failed ones are listed."""
    row = ConstraintReport(
        kind="decision", id="d001", name="Stub", status="live",
        refs=[_ok_ref("ok.md"), _bad_ref("fail.md")],
        consistency_violations=[],
    )
    summary = Summary(
        total_rows=1, rows_with_gap=1, refs_total=2, refs_file_missing=1,
    )
    text = formatter.render_text(AuditReport(rows=[row], summary=summary))
    assert "fail.md" in text
    assert "ok.md" not in text


def test_text_renders_failed_ref_with_empty_detail() -> None:
    """Branch where a non-OK ref has detail='' (rare but allowed)."""
    bare_failure = ResolvedRef(
        original="x.md",
        parsed=ParsedRef(path="x.md", fragment=None, symbol=None),
        resolution=Resolution.FILE_MISSING,
        detail="",  # empty: the (detail) line should NOT be emitted.
    )
    row = ConstraintReport(
        kind="decision", id="d001", name="Stub", status="live",
        refs=[bare_failure], consistency_violations=[],
    )
    summary = Summary(
        total_rows=1, rows_with_gap=1, refs_total=1, refs_file_missing=1,
    )
    text = formatter.render_text(AuditReport(rows=[row], summary=summary))
    # The ref is reported but the detail line is suppressed.
    assert "file_missing: x.md" in text
    assert "(\n" not in text
    assert "()" not in text


def test_text_lists_consistency_violations() -> None:
    row = ConstraintReport(
        kind="design_principle", id="p1", name="P", status="tested",
        refs=[],
        consistency_violations=["bogus violation"],
    )
    summary = Summary(
        total_rows=1, rows_with_gap=1, consistency_violations=1,
    )
    rep = AuditReport(rows=[row], summary=summary)
    text = formatter.render_text(rep)
    assert "bogus violation" in text


def test_text_omits_clean_rows_from_per_row_list() -> None:
    clean = ConstraintReport(
        kind="decision", id="d001", name="Stub", status="live",
        refs=[_ok_ref()], consistency_violations=[],
    )
    bad = ConstraintReport(
        kind="decision", id="d002", name="Stub2", status="live",
        refs=[_bad_ref()], consistency_violations=[],
    )
    summary = Summary(
        total_rows=2, rows_with_gap=1, refs_total=2, refs_file_missing=1,
    )
    rep = AuditReport(rows=[clean, bad], summary=summary)
    text = formatter.render_text(rep)
    assert "d001" not in text  # clean row hidden
    assert "d002" in text


# ---- formatter.render_json --------------------------------------------


def test_json_round_trips() -> None:
    row = ConstraintReport(
        kind="decision", id="d001", name="Stub", status="live",
        refs=[_ok_ref(), _bad_ref()],
        consistency_violations=["bogus"],
    )
    summary = Summary(
        total_rows=1, rows_with_gap=1, refs_total=2,
        refs_file_missing=1, consistency_violations=1,
    )
    rep = AuditReport(rows=[row], summary=summary)
    payload = json.loads(formatter.render_json(rep))
    assert payload["summary"]["total_rows"] == 1
    assert payload["rows"][0]["id"] == "d001"
    assert payload["rows"][0]["has_gap"] is True
    assert payload["rows"][0]["consistency_violations"] == ["bogus"]
    assert len(payload["rows"][0]["refs"]) == 2


# ---- cli.main: success / violations / load failure --------------------


def _build_repo_and_ontology(
    tmp_path: Path,
    *,
    extra_refs: list[str] | None = None,
) -> Path:
    """Create a repo with DECISIONS.md and an ontology JSON."""
    (tmp_path / "DECISIONS.md").write_text("# h\n", encoding="utf-8")
    decision: dict[str, Any] = {
        "id": "d001",
        "d_number": 1,
        "name": "Stub",
        "date_utc": "2026-04-27 18:50 UTC",
        "summary": "x",
        "rationale_ref": "DECISIONS.md",
        "status": "live",
        "supersedes": [],
        "superseded_by": None,
    }
    extras: list[dict[str, Any]] = []
    if extra_refs is not None:
        extras = [
            {
                "id": "p1",
                "name": "P",
                "description": "d",
                "rationale": "r",
                "status": "tested",
                "implementation_refs": extra_refs,
                "verification_refs": [],
                "derives_from_decisions": [],
            },
        ]
    payload = {
        "decisions": [decision],
        "design_principles": extras,
        "isa_features": [],
        "memory_mechanisms": [],
        "pipeline_stages": [],
        "artifact_types": [],
    }
    json_path = tmp_path / "ont.json"
    json_path.write_text(
        json.dumps(payload), encoding="utf-8",
    )
    return json_path


def test_cli_clean_returns_0(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path = _build_repo_and_ontology(tmp_path)
    rc = cli.main(
        ["--ontology", str(json_path), "--repo-root", str(tmp_path)],
    )
    assert rc == 0
    assert "no gaps" in capsys.readouterr().out


def test_cli_violation_returns_1(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path = _build_repo_and_ontology(
        tmp_path, extra_refs=[],  # provable-lie violation
    )
    rc = cli.main(
        ["--ontology", str(json_path), "--repo-root", str(tmp_path)],
    )
    assert rc == 1
    assert "implementation_refs" in capsys.readouterr().out


def test_cli_missing_ontology_returns_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = cli.main(
        [
            "--ontology", str(tmp_path / "missing.json"),
            "--repo-root", str(tmp_path),
        ],
    )
    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_cli_invalid_json_returns_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not json", encoding="utf-8")
    rc = cli.main(
        [
            "--ontology", str(bad_path),
            "--repo-root", str(tmp_path),
        ],
    )
    assert rc == 2
    assert "failed to load" in capsys.readouterr().err


def test_cli_invalid_schema_returns_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(
        json.dumps({"decisions": [{"id": "x"}]}), encoding="utf-8",
    )
    rc = cli.main(
        [
            "--ontology", str(bad_path),
            "--repo-root", str(tmp_path),
        ],
    )
    assert rc == 2
    assert "failed to load" in capsys.readouterr().err


def test_cli_json_format(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path = _build_repo_and_ontology(tmp_path)
    rc = cli.main(
        [
            "--ontology", str(json_path),
            "--repo-root", str(tmp_path),
            "--format", "json",
        ],
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "summary" in payload
    assert "rows" in payload
