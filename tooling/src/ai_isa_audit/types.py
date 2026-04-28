"""Shared types for the audit tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class ParsedRef:
    """Structured form of a `path[#fragment][:symbol]` ref string."""

    path: str
    fragment: str | None
    symbol: str | None


class Resolution(Enum):
    """How a ref resolved against the repo (v1 outcomes)."""

    # All checked aspects passed. (v1: file existence + markdown
    # fragment when applicable. Symbol presence is recorded but not
    # verified — that lands with D011.)
    OK = "ok"
    # The file path didn't resolve to anything in the repo.
    FILE_MISSING = "file_missing"
    # The file resolved but the #anchor doesn't appear in the
    # markdown headings or as an explicit HTML <a id="..."> tag.
    FRAGMENT_MISSING = "fragment_missing"


@dataclass(frozen=True)
class ResolvedRef:
    """A ref plus its resolution outcome.

    `original` is the input ref string (for display in reports);
    `parsed` is its structured form; `resolution` is the verdict.
    `detail` carries a short human-readable explanation when the
    resolution is not `OK` (and is empty otherwise).
    """

    original: str
    parsed: ParsedRef
    resolution: Resolution
    detail: str


@dataclass
class ConstraintReport:
    """One row in the audit matrix — one ontology entry's findings."""

    kind: str            # "decision" | "design_principle" | ...
    id: str
    name: str
    status: str
    refs: list[ResolvedRef]
    consistency_violations: list[str]

    @property
    def has_gap(self) -> bool:
        """True if any ref didn't resolve OR any consistency rule fired."""
        if self.consistency_violations:
            return True
        return any(r.resolution is not Resolution.OK for r in self.refs)


@dataclass
class Summary:
    """Aggregate counts across the report."""

    total_rows: int = 0
    rows_with_gap: int = 0
    refs_total: int = 0
    refs_file_missing: int = 0
    refs_fragment_missing: int = 0
    consistency_violations: int = 0


@dataclass
class AuditReport:
    """Full audit output: per-entry rows plus aggregate Summary."""

    rows: list[ConstraintReport] = field(default_factory=list)
    summary: Summary = field(default_factory=Summary)

    @property
    def has_any_gap(self) -> bool:
        """True if any row has a gap. Drives CI exit code."""
        return self.summary.rows_with_gap > 0
