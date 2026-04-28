"""Top-level audit orchestrator.

Walks every ontology entry, resolves its refs, applies the
consistency rules, and aggregates the output into an AuditReport.
The CLI loads the ontology JSON, calls this, and renders the
report.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_isa_audit.consistency import (
    check_principle_xrefs,
    check_provable_lie,
    check_stage_xrefs,
    check_supersession_for,
    collect_supersession_index,
)
from ai_isa_audit.parser import parse_ref
from ai_isa_audit.resolver import resolve_ref
from ai_isa_audit.types import (
    AuditReport,
    ConstraintReport,
    Resolution,
    ResolvedRef,
    Summary,
)
from ai_targeted_isa_ontology.models import (
    Decision,
    Ontology,
)


def load_ontology(json_path: Path) -> Ontology:
    """Read the built JSON snapshot and validate it back into Ontology."""
    text = json_path.read_text(encoding="utf-8")
    return Ontology.model_validate(json.loads(text))


def run_audit(ontology: Ontology, repo_root: Path) -> AuditReport:
    """Apply ref resolution + consistency rules across the ontology."""
    report = AuditReport()
    decision_index = collect_supersession_index(ontology)
    decision_ids = set(decision_index.keys())
    artifact_ids = {a.id for a in ontology.artifact_types}
    _audit_decisions(ontology, repo_root, decision_index, report)
    _audit_principles(ontology, repo_root, decision_ids, report)
    _audit_features(ontology, repo_root, report)
    _audit_memory_mechanisms(ontology, repo_root, report)
    _audit_pipeline_stages(ontology, repo_root, artifact_ids, report)
    _audit_artifact_types(ontology, repo_root, report)
    return report


def _audit_decisions(
    ontology: Ontology,
    repo_root: Path,
    decision_index: dict[str, Decision],
    report: AuditReport,
) -> None:
    for d in ontology.decisions:
        refs = _resolve_refs([d.rationale_ref], repo_root)
        violations = check_supersession_for(d, decision_index)
        _push_row(report, "decision", d.id, d.name, d.status,
                  refs, violations)


def _audit_principles(
    ontology: Ontology,
    repo_root: Path,
    decision_ids: set[str],
    report: AuditReport,
) -> None:
    for p in ontology.design_principles:
        refs = _resolve_refs(
            list(p.implementation_refs) + list(p.verification_refs),
            repo_root,
        )
        violations = check_provable_lie(p, "design_principle")
        violations.extend(check_principle_xrefs(p, decision_ids))
        _push_row(report, "design_principle", p.id, p.name, p.status,
                  refs, violations)


def _audit_features(
    ontology: Ontology,
    repo_root: Path,
    report: AuditReport,
) -> None:
    for f in ontology.isa_features:
        refs = _resolve_refs(
            list(f.implementation_refs) + list(f.verification_refs),
            repo_root,
        )
        violations = check_provable_lie(f, "isa_feature")
        _push_row(report, "isa_feature", f.id, f.name, f.status,
                  refs, violations)


def _audit_memory_mechanisms(
    ontology: Ontology,
    repo_root: Path,
    report: AuditReport,
) -> None:
    for m in ontology.memory_mechanisms:
        refs = _resolve_refs(
            list(m.implementation_refs) + list(m.verification_refs),
            repo_root,
        )
        violations = check_provable_lie(m, "memory_mechanism")
        _push_row(report, "memory_mechanism", m.id, m.name, m.status,
                  refs, violations)


def _audit_pipeline_stages(
    ontology: Ontology,
    repo_root: Path,
    artifact_ids: set[str],
    report: AuditReport,
) -> None:
    for s in ontology.pipeline_stages:
        refs = _resolve_refs(
            list(s.implementation_refs) + list(s.verification_refs),
            repo_root,
        )
        violations = check_provable_lie(s, "pipeline_stage")
        violations.extend(check_stage_xrefs(s, artifact_ids))
        _push_row(report, "pipeline_stage", s.id, s.name, s.status,
                  refs, violations)


def _audit_artifact_types(
    ontology: Ontology,
    repo_root: Path,
    report: AuditReport,
) -> None:
    for a in ontology.artifact_types:
        refs = _resolve_refs(
            list(a.implementation_refs) + list(a.verification_refs),
            repo_root,
        )
        violations = check_provable_lie(a, "artifact_type")
        _push_row(report, "artifact_type", a.id, a.name, a.status,
                  refs, violations)


def _resolve_refs(
    ref_strings: list[str],
    repo_root: Path,
) -> list[ResolvedRef]:
    return [resolve_ref(parse_ref(r), repo_root) for r in ref_strings]


def _push_row(
    report: AuditReport,
    kind: str,
    entry_id: str,
    name: str,
    status: str,
    refs: list[ResolvedRef],
    violations: list[str],
) -> None:
    row = ConstraintReport(
        kind=kind,
        id=entry_id,
        name=name,
        status=status,
        refs=refs,
        consistency_violations=violations,
    )
    report.rows.append(row)
    _update_summary(report.summary, row)


def _update_summary(summary: Summary, row: ConstraintReport) -> None:
    summary.total_rows += 1
    if row.has_gap:
        summary.rows_with_gap += 1
    summary.consistency_violations += len(row.consistency_violations)
    for r in row.refs:
        summary.refs_total += 1
        if r.resolution is Resolution.FILE_MISSING:
            summary.refs_file_missing += 1
        elif r.resolution is Resolution.FRAGMENT_MISSING:
            summary.refs_fragment_missing += 1
