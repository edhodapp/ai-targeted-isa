"""Tests for ai_isa_audit.resolver.resolve_ref."""

from __future__ import annotations

from pathlib import Path

from ai_isa_audit.resolver import resolve_ref
from ai_isa_audit.types import ParsedRef, Resolution


def _ref(
    path: str,
    fragment: str | None = None,
    symbol: str | None = None,
) -> ParsedRef:
    return ParsedRef(path=path, fragment=fragment, symbol=symbol)


# ---- file existence ----------------------------------------------------


def test_missing_file_returns_file_missing(tmp_path: Path) -> None:
    res = resolve_ref(_ref("nope.md"), tmp_path)
    assert res.resolution is Resolution.FILE_MISSING
    assert "does not exist" in res.detail
    assert res.original == "nope.md"


def test_existing_file_no_fragment_no_symbol_is_ok(tmp_path: Path) -> None:
    (tmp_path / "exists.md").write_text("# h\n", encoding="utf-8")
    res = resolve_ref(_ref("exists.md"), tmp_path)
    assert res.resolution is Resolution.OK
    assert res.detail == ""


def test_existing_directory_resolves_ok(tmp_path: Path) -> None:
    (tmp_path / "subdir").mkdir()
    res = resolve_ref(_ref("subdir"), tmp_path)
    assert res.resolution is Resolution.OK


# ---- markdown fragment resolution --------------------------------------


def test_md_fragment_present_via_heading(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text(
        "# Top heading\n\n## Second one\n", encoding="utf-8",
    )
    res = resolve_ref(_ref("doc.md", fragment="second-one"), tmp_path)
    assert res.resolution is Resolution.OK


def test_md_fragment_present_via_html_id(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text(
        '## Long heading text here\n<a id="d001"></a>\n',
        encoding="utf-8",
    )
    res = resolve_ref(_ref("doc.md", fragment="d001"), tmp_path)
    assert res.resolution is Resolution.OK


def test_md_fragment_present_via_html_name_attr(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text(
        '<a name="legacy"></a>\n',
        encoding="utf-8",
    )
    res = resolve_ref(_ref("doc.md", fragment="legacy"), tmp_path)
    assert res.resolution is Resolution.OK


def test_md_fragment_missing(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text("# Just the top\n", encoding="utf-8")
    res = resolve_ref(_ref("doc.md", fragment="nope"), tmp_path)
    assert res.resolution is Resolution.FRAGMENT_MISSING
    assert "#nope" in res.detail
    assert "doc.md" in res.detail


def test_non_md_with_fragment_skipped_and_ok(tmp_path: Path) -> None:
    """Fragments on non-markdown files are not checked in v1."""
    (tmp_path / "config.toml").write_text("[a]\nx = 1\n", encoding="utf-8")
    res = resolve_ref(
        _ref("config.toml", fragment="anything"),
        tmp_path,
    )
    assert res.resolution is Resolution.OK


# ---- symbol is recorded but unchecked in v1 ---------------------------


def test_symbol_present_does_not_block_resolution(tmp_path: Path) -> None:
    (tmp_path / "code.py").write_text("def foo(): ...\n", encoding="utf-8")
    res = resolve_ref(_ref("code.py", symbol="anything"), tmp_path)
    assert res.resolution is Resolution.OK
    assert res.original == "code.py:anything"


# ---- _github_slug tested through resolve_ref --------------------------
#
# These exercise the slugifier branches indirectly: code stripping,
# special-char stripping, whitespace folding.


def test_github_slug_strips_inline_code(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text(
        "## D001 — Treat `~/hwdesign/cpu` as exploratory\n",
        encoding="utf-8",
    )
    expected_slug = "d001--treat-hwdesigncpu-as-exploratory"
    res = resolve_ref(_ref("doc.md", fragment=expected_slug), tmp_path)
    assert res.resolution is Resolution.OK


def test_github_slug_strips_punctuation(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text(
        "## A, B; and C!\n", encoding="utf-8",
    )
    res = resolve_ref(_ref("doc.md", fragment="a-b-and-c"), tmp_path)
    assert res.resolution is Resolution.OK


def test_github_slug_collapses_no_whitespace(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text(
        "## hello   world\n", encoding="utf-8",
    )
    # Multiple spaces collapse to single hyphen via \s+ → -.
    res = resolve_ref(_ref("doc.md", fragment="hello-world"), tmp_path)
    assert res.resolution is Resolution.OK


# ---- detail field populated only on failure ---------------------------


def test_ok_resolution_has_empty_detail(tmp_path: Path) -> None:
    (tmp_path / "x.md").write_text("# h\n", encoding="utf-8")
    res = resolve_ref(_ref("x.md", fragment="h"), tmp_path)
    assert res.detail == ""


def test_render_includes_fragment_and_symbol(tmp_path: Path) -> None:
    (tmp_path / "x.md").write_text("# h\n", encoding="utf-8")
    res = resolve_ref(
        _ref("x.md", fragment="h", symbol="sym"),
        tmp_path,
    )
    assert res.original == "x.md#h:sym"
