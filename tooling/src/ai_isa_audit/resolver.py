"""Resolve ParsedRef instances against the actual repository.

v1 scope:
  - file existence (any ref)
  - markdown anchor existence (when path ends in .md and a fragment
    is present) — anchors come from heading slugification AND
    explicit `<a id="...">` / `<a name="...">` tags.

Out of scope (D011 future):
  - symbol resolution inside source files.
  - cross-language symbol grammar (Python vs C vs assembly).
"""

from __future__ import annotations

import re
from pathlib import Path

from ai_isa_audit.types import ParsedRef, ResolvedRef, Resolution

# Match `<a id="..."></a>` and `<a name="..."></a>` in markdown.
# The audit tool relies on these for stable, drift-resistant
# anchors (heading text changes don't break refs).
_HTML_ANCHOR_RE = re.compile(
    r"<a\s+(?:id|name)\s*=\s*[\"'](?P<name>[^\"']+)[\"']",
    re.IGNORECASE,
)


def resolve_ref(parsed: ParsedRef, repo_root: Path) -> ResolvedRef:
    """Resolve one ref under repo_root. v1: file + md fragment only."""
    original = _render(parsed)
    full_path = repo_root / parsed.path
    if not full_path.exists():
        return _ref(parsed, original, Resolution.FILE_MISSING,
                    f"path does not exist: {parsed.path}")
    if _should_check_fragment(parsed, full_path):
        anchors = _markdown_anchors(full_path)
        # mypy: parsed.fragment is non-None here (gated by the helper
        # above), but that helper can't narrow across calls. Local var
        # makes the narrowing explicit.
        fragment = parsed.fragment
        assert fragment is not None
        if fragment not in anchors:
            return _ref(parsed, original, Resolution.FRAGMENT_MISSING,
                        f"#{fragment} not in {parsed.path}")
    return _ref(parsed, original, Resolution.OK, "")


def _should_check_fragment(parsed: ParsedRef, path: Path) -> bool:
    """We check fragments only for markdown files (.md)."""
    return parsed.fragment is not None and path.suffix == ".md"


def _ref(
    parsed: ParsedRef,
    original: str,
    resolution: Resolution,
    detail: str,
) -> ResolvedRef:
    """Construct a ResolvedRef (small helper for readability)."""
    return ResolvedRef(
        original=original,
        parsed=parsed,
        resolution=resolution,
        detail=detail,
    )


def _render(parsed: ParsedRef) -> str:
    """Reconstruct the original ref string from a ParsedRef."""
    out = parsed.path
    if parsed.fragment is not None:
        out += f"#{parsed.fragment}"
    if parsed.symbol is not None:
        out += f":{parsed.symbol}"
    return out


def _markdown_anchors(path: Path) -> set[str]:
    """All anchor names available in a markdown file."""
    text = path.read_text(encoding="utf-8")
    anchors: set[str] = set()
    _add_heading_anchors(text, anchors)
    _add_html_anchors(text, anchors)
    return anchors


def _add_heading_anchors(text: str, anchors: set[str]) -> None:
    """Slugify every ATX heading and add to the anchors set."""
    for line in text.splitlines():
        if line.startswith("#"):
            anchors.add(_github_slug(line))


def _add_html_anchors(text: str, anchors: set[str]) -> None:
    """Add explicit <a id="..."> / <a name="..."> tag values.

    Known v1 limitation: this regex matches occurrences inside code
    spans / code blocks too. A heading with ``<a id="x">`` written as
    a code-span example will produce a spurious 'x' anchor that the
    rendered markdown does NOT actually expose. Real anchors override
    spurious code-span matches in practice (set union), so the
    workaround is "add the real anchor." Proper fix wants a
    markdown-aware tokenizer; out of scope for D010 v1.
    """
    for match in _HTML_ANCHOR_RE.finditer(text):
        anchors.add(match.group("name"))


def _github_slug(heading: str) -> str:
    """GitHub-style anchor slug for an ATX heading line."""
    # Strip leading hash marks and surrounding whitespace.
    text = re.sub(r"^#+\s*", "", heading).lower()
    # Strip inline code backticks (keep the content inside).
    text = text.replace("`", "")
    # Whitespace -> hyphen.
    text = re.sub(r"\s+", "-", text)
    # Drop everything except [a-z0-9_-].
    return re.sub(r"[^a-z0-9_-]", "", text)
