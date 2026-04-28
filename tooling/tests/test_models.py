"""Tests for models.py — the ontology entity types.

Exercises each cross-validator branch, the Ref / UtcTimestamp regex
constraints, the per-section ID-uniqueness check, and the immutability
contract of all entity types.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from ai_targeted_isa_ontology import models as m


class _RefHolder(BaseModel):
    value: m.Ref


class _UtcHolder(BaseModel):
    value: m.UtcTimestamp


# ---- Ref grammar --------------------------------------------------------


@pytest.mark.parametrize(
    "good",
    [
        "DECISIONS.md",
        "DECISIONS.md#d002",
        "pipeline_design.md#stages",
        "tooling/src/pkg/models.py:ISAFeature",
        "tests/file.py:test_x",
        "a/b/c.md#anchor:symbol",
    ],
)
def test_ref_accepts_valid_shapes(good: str) -> None:
    assert _RefHolder(value=good).value == good


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "has space",
        "has\ttab",
        "has\nnewline",
        "x" * 513,
    ],
)
def test_ref_rejects_invalid(bad: str) -> None:
    with pytest.raises(ValidationError):
        _RefHolder(value=bad)


# ---- UtcTimestamp -------------------------------------------------------


def test_utc_timestamp_accepts_decisions_md_format() -> None:
    good = "2026-04-28 05:13 UTC"
    assert _UtcHolder(value=good).value == good


@pytest.mark.parametrize(
    "bad",
    [
        "2026-04-28T05:13Z",
        "2026-04-28 05:13:00 UTC",
        "2026-04-28 05:13",
        "April 28 2026",
        "",
    ],
)
def test_utc_timestamp_rejects_other_formats(bad: str) -> None:
    with pytest.raises(ValidationError):
        _UtcHolder(value=bad)


# ---- Decision: supersession consistency --------------------------------


def _decision_kwargs(**overrides: Any) -> dict[str, Any]:
    """Minimal valid Decision kwargs; tests override one field."""
    base: dict[str, Any] = {
        "id": "d001",
        "d_number": 1,
        "name": "Stub decision",
        "date_utc": "2026-04-27 18:50 UTC",
        "summary": "A stub for testing.",
        "rationale_ref": "DECISIONS.md#d001",
        "status": "live",
    }
    base.update(overrides)
    return base


def test_decision_live_with_no_superseded_by_is_valid() -> None:
    d = m.Decision(**_decision_kwargs())
    assert d.status == "live"
    assert d.superseded_by is None


def test_decision_superseded_with_superseded_by_is_valid() -> None:
    d = m.Decision(
        **_decision_kwargs(status="superseded", superseded_by="d042"),
    )
    assert d.status == "superseded"
    assert d.superseded_by == "d042"


def test_decision_superseded_without_superseded_by_raises() -> None:
    with pytest.raises(ValidationError, match="superseded_by"):
        m.Decision(**_decision_kwargs(status="superseded"))


def test_decision_live_with_superseded_by_raises() -> None:
    with pytest.raises(ValidationError, match="forbids superseded_by"):
        m.Decision(
            **_decision_kwargs(superseded_by="d042"),
        )


def test_decision_withdrawn_status_skips_supersession_checks() -> None:
    """Withdrawn decisions don't require either field; both branches OK."""
    d_no_link = m.Decision(**_decision_kwargs(status="withdrawn"))
    d_with_link = m.Decision(
        **_decision_kwargs(status="withdrawn", superseded_by="d999"),
    )
    assert d_no_link.status == "withdrawn"
    assert d_with_link.superseded_by == "d999"


def test_decision_d_number_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        m.Decision(**_decision_kwargs(d_number=0))


# ---- Requirement-shaped entities ---------------------------------------


def _req_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "stub",
        "name": "Stub",
        "description": "Description.",
        "rationale": "Why.",
        "status": "spec",
    }
    base.update(overrides)
    return base


def test_design_principle_round_trips() -> None:
    p = m.DesignPrinciple(
        **_req_kwargs(id="p1", derives_from_decisions=["d002"]),
    )
    assert p.derives_from_decisions == ["d002"]


def test_isa_feature_requires_category() -> None:
    f = m.ISAFeature(**_req_kwargs(id="predication", category="control_flow"))
    assert f.category == "control_flow"


def test_isa_feature_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        m.ISAFeature(**_req_kwargs(id="x", category="bogus"))


def test_memory_mechanism_requires_tier() -> None:
    mm = m.MemoryMechanism(**_req_kwargs(id="scratch", tier="scratchpad"))
    assert mm.tier == "scratchpad"


def test_pipeline_stage_stage_index_must_be_nonneg() -> None:
    with pytest.raises(ValidationError):
        m.PipelineStage(**_req_kwargs(id="s", stage_index=-1))


def test_pipeline_stage_round_trips() -> None:
    s = m.PipelineStage(
        **_req_kwargs(
            id="markdown_synth",
            stage_index=2,
            inputs=["intent"],
            outputs=["markdown"],
            gates=["lab-notebook stance"],
        ),
    )
    assert s.stage_index == 2
    assert s.inputs == ["intent"]


def test_artifact_type_round_trips() -> None:
    a = m.ArtifactType(
        **_req_kwargs(
            id="markdown",
            file_glob="**/*.md",
            gate_tools=["markdownlint-cli2", "lychee"],
        ),
    )
    assert a.file_glob == "**/*.md"
    assert a.gate_tools == ["markdownlint-cli2", "lychee"]


# ---- Ontology root: per-section ID uniqueness --------------------------


def test_empty_ontology_is_valid() -> None:
    o = m.Ontology()
    assert o.decisions == []
    assert o.isa_features == []


def test_ontology_with_unique_ids_is_valid() -> None:
    o = m.Ontology(
        decisions=[
            m.Decision(**_decision_kwargs()),
            m.Decision(**_decision_kwargs(id="d002", d_number=2)),
        ],
    )
    assert len(o.decisions) == 2


@pytest.mark.parametrize(
    ("section", "make_pair"),
    [
        (
            "decisions",
            lambda: {
                "decisions": [
                    m.Decision(**_decision_kwargs()),
                    m.Decision(**_decision_kwargs(d_number=2)),
                ],
            },
        ),
        (
            "design_principles",
            lambda: {
                "design_principles": [
                    m.DesignPrinciple(**_req_kwargs(id="p")),
                    m.DesignPrinciple(**_req_kwargs(id="p")),
                ],
            },
        ),
        (
            "isa_features",
            lambda: {
                "isa_features": [
                    m.ISAFeature(
                        **_req_kwargs(id="f", category="control_flow"),
                    ),
                    m.ISAFeature(
                        **_req_kwargs(id="f", category="safety"),
                    ),
                ],
            },
        ),
        (
            "memory_mechanisms",
            lambda: {
                "memory_mechanisms": [
                    m.MemoryMechanism(
                        **_req_kwargs(id="mm", tier="scratchpad"),
                    ),
                    m.MemoryMechanism(
                        **_req_kwargs(id="mm", tier="dram"),
                    ),
                ],
            },
        ),
        (
            "pipeline_stages",
            lambda: {
                "pipeline_stages": [
                    m.PipelineStage(
                        **_req_kwargs(id="s", stage_index=0),
                    ),
                    m.PipelineStage(
                        **_req_kwargs(id="s", stage_index=1),
                    ),
                ],
            },
        ),
        (
            "artifact_types",
            lambda: {
                "artifact_types": [
                    m.ArtifactType(
                        **_req_kwargs(id="a", file_glob="*.md"),
                    ),
                    m.ArtifactType(
                        **_req_kwargs(id="a", file_glob="*.py"),
                    ),
                ],
            },
        ),
    ],
)
def test_ontology_rejects_duplicate_ids_per_section(
    section: str, make_pair: Any,
) -> None:
    with pytest.raises(ValidationError, match=f"'{section}'"):
        m.Ontology(**make_pair())


# ---- Frozen / extra=forbid contract ------------------------------------


def test_decision_is_frozen() -> None:
    d = m.Decision(**_decision_kwargs())
    with pytest.raises(ValidationError):
        d.status = "withdrawn"


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        m.Decision(**_decision_kwargs(extra_garbage="no"))
