"""Consistency rules applied to the ontology (D010 v1).

Three rule families:
  - provable-lie: status not in {spec, n_a} requires non-empty
    implementation_refs (per D007 / D009).
  - supersession integrity: Decision.superseded_by and
    Decision.supersedes must form symmetric, resolvable links.
  - cross-references: DesignPrinciple.derives_from_decisions and
    PipelineStage.inputs/outputs must point at existing entries.

Each rule returns a list of human-readable violation strings (empty
if the rule passes). The audit orchestrator aggregates these into
the per-entry ConstraintReport.consistency_violations field.
"""

from __future__ import annotations

from typing import Union

from ai_targeted_isa_ontology.models import (
    ArtifactType,
    Decision,
    DesignPrinciple,
    ISAFeature,
    MemoryMechanism,
    Ontology,
    PipelineStage,
)

# Union of all requirement-shaped entities (everything except Decision).
# These all share the id / status / implementation_refs fields the
# provable-lie rule needs.
_Requirement = Union[
    DesignPrinciple,
    ISAFeature,
    MemoryMechanism,
    PipelineStage,
    ArtifactType,
]


def check_provable_lie(entry: _Requirement, kind: str) -> list[str]:
    """status not in {spec, n_a} requires non-empty implementation_refs."""
    if entry.status in ("spec", "n_a"):
        return []
    if entry.implementation_refs:
        return []
    return [
        f"{kind} '{entry.id}' has status='{entry.status}' but no "
        "implementation_refs (provable-lie per D007)"
    ]


def check_supersession_for(
    decision: Decision,
    by_id: dict[str, Decision],
) -> list[str]:
    """Both directions of decision.supersedes / decision.superseded_by."""
    out: list[str] = []
    out.extend(_check_superseded_by(decision, by_id))
    out.extend(_check_supersedes(decision, by_id))
    return out


def _check_superseded_by(
    decision: Decision,
    by_id: dict[str, Decision],
) -> list[str]:
    """If decision.superseded_by is set, the target must reciprocate."""
    if decision.superseded_by is None:
        return []
    target = by_id.get(decision.superseded_by)
    if target is None:
        return [
            f"decision '{decision.id}' has superseded_by="
            f"'{decision.superseded_by}' but no such decision exists"
        ]
    if decision.id not in target.supersedes:
        return [
            f"decision '{decision.id}' has superseded_by="
            f"'{decision.superseded_by}' but '{decision.superseded_by}'"
            f".supersedes does not include '{decision.id}'"
        ]
    return []


def _check_supersedes(
    decision: Decision,
    by_id: dict[str, Decision],
) -> list[str]:
    """Each entry in decision.supersedes must point back via superseded_by."""
    out: list[str] = []
    for sup_id in decision.supersedes:
        out.extend(_check_one_supersedes(decision, sup_id, by_id))
    return out


def _check_one_supersedes(
    decision: Decision,
    sup_id: str,
    by_id: dict[str, Decision],
) -> list[str]:
    target = by_id.get(sup_id)
    if target is None:
        return [
            f"decision '{decision.id}' supersedes '{sup_id}' but no "
            "such decision exists"
        ]
    if target.superseded_by != decision.id:
        return [
            f"decision '{decision.id}' supersedes '{sup_id}' but "
            f"'{sup_id}'.superseded_by != '{decision.id}'"
        ]
    return []


def check_principle_xrefs(
    principle: DesignPrinciple,
    decision_ids: set[str],
) -> list[str]:
    """derives_from_decisions must list existing decision ids."""
    out: list[str] = []
    for d_id in principle.derives_from_decisions:
        if d_id not in decision_ids:
            out.append(
                f"design_principle '{principle.id}' "
                f"derives_from_decisions='{d_id}' but no such "
                "decision exists"
            )
    return out


def check_stage_xrefs(
    stage: PipelineStage,
    artifact_ids: set[str],
) -> list[str]:
    """inputs and outputs must list existing artifact_type ids."""
    out: list[str] = []
    for input_id in stage.inputs:
        if input_id not in artifact_ids:
            out.append(
                f"pipeline_stage '{stage.id}' input='{input_id}' but "
                "no such artifact_type exists"
            )
    for output_id in stage.outputs:
        if output_id not in artifact_ids:
            out.append(
                f"pipeline_stage '{stage.id}' output='{output_id}' but "
                "no such artifact_type exists"
            )
    return out


def collect_supersession_index(
    ontology: Ontology,
) -> dict[str, Decision]:
    """Map id -> Decision for all decisions in the ontology."""
    return {d.id: d for d in ontology.decisions}
