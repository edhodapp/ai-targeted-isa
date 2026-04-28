"""Tests for ai_isa_audit.consistency."""

from __future__ import annotations

from typing import Any

from ai_isa_audit import consistency as c
from ai_targeted_isa_ontology import models as m


def _decision(**overrides: Any) -> m.Decision:
    base: dict[str, Any] = {
        "id": "d001",
        "d_number": 1,
        "name": "Stub",
        "date_utc": "2026-04-27 18:50 UTC",
        "summary": "x",
        "rationale_ref": "DECISIONS.md#d001",
        "status": "live",
    }
    base.update(overrides)
    return m.Decision(**base)


def _principle(**overrides: Any) -> m.DesignPrinciple:
    base: dict[str, Any] = {
        "id": "p1",
        "name": "P1",
        "description": "desc",
        "rationale": "why",
        "status": "spec",
    }
    base.update(overrides)
    return m.DesignPrinciple(**base)


def _stage(**overrides: Any) -> m.PipelineStage:
    base: dict[str, Any] = {
        "id": "s1",
        "name": "S1",
        "description": "desc",
        "rationale": "why",
        "status": "spec",
        "stage_index": 0,
    }
    base.update(overrides)
    return m.PipelineStage(**base)


# ---- check_provable_lie -----------------------------------------------


def test_provable_lie_spec_with_empty_refs_no_violation() -> None:
    p = _principle(status="spec", implementation_refs=[])
    assert not c.check_provable_lie(p, "design_principle")


def test_provable_lie_n_a_with_empty_refs_no_violation() -> None:
    p = _principle(status="n_a", implementation_refs=[])
    assert not c.check_provable_lie(p, "design_principle")


def test_provable_lie_tested_with_empty_refs_is_violation() -> None:
    p = _principle(status="tested", implementation_refs=[])
    issues = c.check_provable_lie(p, "design_principle")
    assert len(issues) == 1
    assert "tested" in issues[0]
    assert "implementation_refs" in issues[0]


def test_provable_lie_implemented_with_empty_refs_is_violation() -> None:
    p = _principle(status="implemented", implementation_refs=[])
    assert c.check_provable_lie(p, "design_principle")


def test_provable_lie_deviation_with_empty_refs_is_violation() -> None:
    p = _principle(status="deviation", implementation_refs=[])
    assert c.check_provable_lie(p, "design_principle")


def test_provable_lie_tested_with_refs_no_violation() -> None:
    p = _principle(status="tested", implementation_refs=["x.md"])
    assert not c.check_provable_lie(p, "design_principle")


# ---- supersession integrity -------------------------------------------


def test_no_superseded_by_no_supersedes_clean() -> None:
    d = _decision()
    by_id = {d.id: d}
    assert not c.check_supersession_for(d, by_id)


def test_superseded_by_target_missing_violation() -> None:
    d = _decision(status="superseded", superseded_by="d999")
    by_id = {d.id: d}
    issues = c.check_supersession_for(d, by_id)
    assert any("no such decision exists" in i for i in issues)


def test_superseded_by_target_does_not_reciprocate() -> None:
    d = _decision(id="d001", status="superseded", superseded_by="d002")
    target = _decision(id="d002", d_number=2, supersedes=[])
    by_id = {d.id: d, target.id: target}
    issues = c.check_supersession_for(d, by_id)
    assert any("does not include" in i for i in issues)


def test_superseded_by_target_reciprocates_clean() -> None:
    d = _decision(id="d001", status="superseded", superseded_by="d002")
    target = _decision(id="d002", d_number=2, supersedes=["d001"])
    by_id = {d.id: d, target.id: target}
    assert not c.check_supersession_for(d, by_id)


def test_supersedes_target_missing_violation() -> None:
    d = _decision(id="d002", d_number=2, supersedes=["d001"])
    by_id = {d.id: d}
    issues = c.check_supersession_for(d, by_id)
    assert any("supersedes 'd001'" in i and "no such decision" in i
               for i in issues)


def test_supersedes_target_does_not_point_back() -> None:
    d = _decision(id="d002", d_number=2, supersedes=["d001"])
    other = _decision(id="d001", superseded_by=None)
    by_id = {d.id: d, other.id: other}
    issues = c.check_supersession_for(d, by_id)
    assert any("superseded_by" in i for i in issues)


def test_supersedes_target_points_back_clean() -> None:
    d = _decision(id="d002", d_number=2, supersedes=["d001"])
    other = _decision(
        id="d001", status="superseded", superseded_by="d002",
    )
    by_id = {d.id: d, other.id: other}
    assert not c.check_supersession_for(d, by_id)


# ---- principle / stage xrefs ------------------------------------------


def test_principle_xrefs_empty_clean() -> None:
    p = _principle(derives_from_decisions=[])
    assert not c.check_principle_xrefs(p, set())


def test_principle_xrefs_known_decision_clean() -> None:
    p = _principle(derives_from_decisions=["d001"])
    assert not c.check_principle_xrefs(p, {"d001"})


def test_principle_xrefs_unknown_decision_violation() -> None:
    p = _principle(derives_from_decisions=["d999"])
    issues = c.check_principle_xrefs(p, {"d001"})
    assert any("d999" in i for i in issues)


def test_stage_xrefs_known_artifacts_clean() -> None:
    s = _stage(inputs=["markdown"], outputs=["python"])
    assert not c.check_stage_xrefs(s, {"markdown", "python"})


def test_stage_xrefs_unknown_input_violation() -> None:
    s = _stage(inputs=["bogus"], outputs=[])
    issues = c.check_stage_xrefs(s, {"markdown"})
    assert any("input='bogus'" in i for i in issues)


def test_stage_xrefs_unknown_output_violation() -> None:
    s = _stage(inputs=[], outputs=["bogus"])
    issues = c.check_stage_xrefs(s, {"markdown"})
    assert any("output='bogus'" in i for i in issues)


def test_collect_supersession_index_builds_map() -> None:
    d1 = _decision(id="d001")
    d2 = _decision(id="d002", d_number=2)
    o = m.Ontology(decisions=[d1, d2])
    by_id = c.collect_supersession_index(o)
    assert by_id == {"d001": d1, "d002": d2}
