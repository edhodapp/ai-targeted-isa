"""Audit tool for the ai-targeted-isa ontology (D010).

Resolves every ref in the built ontology JSON against the actual
repo, applies consistency rules, and emits a report. CI and local
hooks call this as the verification substrate that closes the
D007 / D009 design loop.

v1 modules (this commit):
  - types     : ParsedRef, Resolution, ResolvedRef
  - parser    : parse_ref(str) -> ParsedRef
  - resolver  : resolve_ref(parsed, repo_root) -> ResolvedRef

Coming in the second D010 commit:
  - consistency, audit, formatter, cli  (orchestrator + CLI + CI wiring)
"""

from ai_isa_audit.audit import load_ontology, run_audit
from ai_isa_audit.formatter import render_json, render_text
from ai_isa_audit.parser import parse_ref
from ai_isa_audit.resolver import resolve_ref
from ai_isa_audit.types import (
    AuditReport,
    ConstraintReport,
    ParsedRef,
    Resolution,
    ResolvedRef,
    Summary,
)

__all__ = [
    "AuditReport",
    "ConstraintReport",
    "ParsedRef",
    "Resolution",
    "ResolvedRef",
    "Summary",
    "load_ontology",
    "parse_ref",
    "render_json",
    "render_text",
    "resolve_ref",
    "run_audit",
]
