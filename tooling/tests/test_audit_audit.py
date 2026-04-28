"""Tests for ai_isa_audit.audit (orchestrator + JSON loading)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ai_isa_audit import audit
from ai_isa_audit.types import Resolution
from ai_targeted_isa_ontology import models as m


def _decision_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "d001",
        "d_number": 1,
        "name": "Stub",
        "date_utc": "2026-04-27 18:50 UTC",
        "summary": "x",
        "rationale_ref": "DECISIONS.md",
        "status": "live",
    }
    base.update(overrides)
    return base


def _req_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "stub",
        "name": "S",
        "description": "d",
        "rationale": "r",
        "status": "spec",
    }
    base.update(overrides)
    return base


def _make_repo(tmp_path: Path) -> Path:
    """Build a minimal repo tree with files refs can resolve to."""
    (tmp_path / "DECISIONS.md").write_text("# h\n", encoding="utf-8")
    (tmp_path / "doc.md").write_text("# h\n", encoding="utf-8")
    return tmp_path


# ---- load_ontology -----------------------------------------------------


def test_load_ontology_round_trip(tmp_path: Path) -> None:
    o = m.Ontology(
        decisions=[m.Decision(**_decision_kwargs())],
    )
    json_path = tmp_path / "ont.json"
    json_path.write_text(o.model_dump_json(), encoding="utf-8")
    loaded = audit.load_ontology(json_path)
    assert loaded == o


def test_load_ontology_invalid_json_raises(tmp_path: Path) -> None:
    json_path = tmp_path / "bad.json"
    json_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        audit.load_ontology(json_path)


def test_load_ontology_invalid_schema_raises(tmp_path: Path) -> None:
    json_path = tmp_path / "schema.json"
    json_path.write_text(
        json.dumps({"decisions": [{"id": "d001"}]}),  # missing fields
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        audit.load_ontology(json_path)


# ---- run_audit: empty + minimal cases ---------------------------------


def test_audit_empty_ontology(tmp_path: Path) -> None:
    report = audit.run_audit(m.Ontology(), tmp_path)
    assert report.summary.total_rows == 0
    assert report.summary.rows_with_gap == 0
    assert report.has_any_gap is False


def test_audit_decision_with_resolvable_ref(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    o = m.Ontology(
        decisions=[
            m.Decision(**_decision_kwargs(rationale_ref="DECISIONS.md")),
        ],
    )
    report = audit.run_audit(o, repo)
    assert report.summary.total_rows == 1
    assert report.summary.refs_total == 1
    assert report.summary.refs_file_missing == 0
    assert report.has_any_gap is False
    assert report.rows[0].kind == "decision"


def test_audit_decision_with_missing_file(tmp_path: Path) -> None:
    o = m.Ontology(
        decisions=[m.Decision(**_decision_kwargs(rationale_ref="missing.md"))],
    )
    report = audit.run_audit(o, tmp_path)
    assert report.summary.refs_file_missing == 1
    assert report.has_any_gap is True
    assert report.rows[0].refs[0].resolution is Resolution.FILE_MISSING


def test_audit_decision_with_missing_fragment(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    o = m.Ontology(
        decisions=[
            m.Decision(**_decision_kwargs(rationale_ref="DECISIONS.md#nope")),
        ],
    )
    report = audit.run_audit(o, repo)
    assert report.summary.refs_fragment_missing == 1
    assert report.has_any_gap is True


# ---- run_audit: each entity kind --------------------------------------


def test_audit_design_principle_provable_lie(tmp_path: Path) -> None:
    o = m.Ontology(
        design_principles=[
            m.DesignPrinciple(**_req_kwargs(status="tested")),
        ],
    )
    report = audit.run_audit(o, tmp_path)
    assert report.summary.consistency_violations == 1
    assert report.has_any_gap is True
    assert "implementation_refs" in (
        report.rows[0].consistency_violations[0]
    )


def test_audit_design_principle_xref_violation(tmp_path: Path) -> None:
    o = m.Ontology(
        design_principles=[
            m.DesignPrinciple(
                **_req_kwargs(derives_from_decisions=["d999"]),
            ),
        ],
    )
    report = audit.run_audit(o, tmp_path)
    assert any(
        "d999" in v for v in report.rows[0].consistency_violations
    )


def test_audit_isa_feature_provable_lie(tmp_path: Path) -> None:
    o = m.Ontology(
        isa_features=[
            m.ISAFeature(
                **_req_kwargs(status="tested", category="control_flow"),
            ),
        ],
    )
    report = audit.run_audit(o, tmp_path)
    assert report.has_any_gap is True


def test_audit_memory_mechanism_clean(tmp_path: Path) -> None:
    o = m.Ontology(
        memory_mechanisms=[
            m.MemoryMechanism(
                **_req_kwargs(status="spec", tier="dram"),
            ),
        ],
    )
    report = audit.run_audit(o, tmp_path)
    assert report.has_any_gap is False


def test_audit_pipeline_stage_xref_violation(tmp_path: Path) -> None:
    o = m.Ontology(
        pipeline_stages=[
            m.PipelineStage(
                **_req_kwargs(stage_index=0, inputs=["bogus"]),
            ),
        ],
    )
    report = audit.run_audit(o, tmp_path)
    assert any(
        "bogus" in v for v in report.rows[0].consistency_violations
    )


def test_audit_artifact_type_clean(tmp_path: Path) -> None:
    o = m.Ontology(
        artifact_types=[
            m.ArtifactType(**_req_kwargs(file_glob="*.md")),
        ],
    )
    report = audit.run_audit(o, tmp_path)
    assert report.has_any_gap is False


def test_audit_summary_aggregates_correctly(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    o = m.Ontology(
        decisions=[
            m.Decision(**_decision_kwargs(rationale_ref="DECISIONS.md")),
            m.Decision(
                **_decision_kwargs(
                    id="d002", d_number=2, rationale_ref="missing.md",
                ),
            ),
        ],
        design_principles=[
            m.DesignPrinciple(
                **_req_kwargs(status="tested"),  # provable lie
            ),
        ],
    )
    report = audit.run_audit(o, repo)
    assert report.summary.total_rows == 3
    assert report.summary.refs_total == 2
    assert report.summary.refs_file_missing == 1
    assert report.summary.consistency_violations == 1
    assert report.summary.rows_with_gap == 2
