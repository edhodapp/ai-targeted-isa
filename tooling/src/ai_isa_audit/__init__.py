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

from ai_isa_audit.parser import parse_ref
from ai_isa_audit.resolver import resolve_ref
from ai_isa_audit.types import ParsedRef, Resolution, ResolvedRef

__all__ = [
    "ParsedRef",
    "Resolution",
    "ResolvedRef",
    "parse_ref",
    "resolve_ref",
]
