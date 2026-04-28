"""Render an AuditReport as text or JSON.

Text format is for humans reading CI logs and local terminal output;
JSON format is for downstream tooling (a future audit dashboard,
cross-project audit aggregator, etc.).
"""

from __future__ import annotations

import json
from dataclasses import asdict

from ai_isa_audit.types import AuditReport, ConstraintReport, Resolution


def render_text(report: AuditReport) -> str:
    """Human-readable summary plus per-row gap details."""
    lines: list[str] = []
    lines.append("=== ai-targeted-isa audit ===")
    lines.append("")
    lines.extend(_format_summary(report))
    lines.append("")
    rows_with_gaps = [r for r in report.rows if r.has_gap]
    if not rows_with_gaps:
        lines.append("no gaps; ontology is in sync with the repo.")
        return "\n".join(lines) + "\n"
    lines.append(f"gaps in {len(rows_with_gaps)} row(s):")
    lines.append("")
    for row in rows_with_gaps:
        lines.extend(_format_row(row))
        lines.append("")
    return "\n".join(lines) + "\n"


def render_json(report: AuditReport) -> str:
    """Machine-readable JSON dump of the full report."""
    payload = {
        "summary": asdict(report.summary),
        "rows": [_row_to_json(r) for r in report.rows],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _format_summary(report: AuditReport) -> list[str]:
    s = report.summary
    return [
        f"  rows                    {s.total_rows}",
        f"  rows with gaps          {s.rows_with_gap}",
        f"  refs total              {s.refs_total}",
        f"  refs file missing       {s.refs_file_missing}",
        f"  refs fragment missing   {s.refs_fragment_missing}",
        f"  consistency violations  {s.consistency_violations}",
    ]


def _format_row(row: ConstraintReport) -> list[str]:
    out: list[str] = []
    out.append(
        f"  {row.kind} '{row.id}' (status={row.status}) — {row.name}"
    )
    for v in row.consistency_violations:
        out.append(f"    ! {v}")
    for ref in row.refs:
        if ref.resolution is Resolution.OK:
            continue
        out.append(
            f"    ! {ref.resolution.value}: {ref.original}"
        )
        if ref.detail:
            out.append(f"      ({ref.detail})")
    return out


def _row_to_json(row: ConstraintReport) -> dict[str, object]:
    return {
        "kind": row.kind,
        "id": row.id,
        "name": row.name,
        "status": row.status,
        "has_gap": row.has_gap,
        "refs": [
            {
                "original": r.original,
                "resolution": r.resolution.value,
                "detail": r.detail,
            }
            for r in row.refs
        ],
        "consistency_violations": list(row.consistency_violations),
    }
