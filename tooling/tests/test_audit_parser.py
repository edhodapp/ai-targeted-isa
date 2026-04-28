"""Tests for ai_isa_audit.parser.parse_ref."""

from __future__ import annotations

import pytest

from ai_isa_audit.parser import parse_ref


def test_path_only() -> None:
    p = parse_ref("DECISIONS.md")
    assert p.path == "DECISIONS.md"
    assert p.fragment is None
    assert p.symbol is None


def test_path_with_fragment() -> None:
    p = parse_ref("DECISIONS.md#d001")
    assert p.path == "DECISIONS.md"
    assert p.fragment == "d001"
    assert p.symbol is None


def test_path_with_symbol() -> None:
    p = parse_ref("tooling/src/foo.py:bar")
    assert p.path == "tooling/src/foo.py"
    assert p.fragment is None
    assert p.symbol == "bar"


def test_path_with_fragment_and_symbol() -> None:
    p = parse_ref("doc.md#section:func")
    assert p.path == "doc.md"
    assert p.fragment == "section"
    assert p.symbol == "func"


def test_empty_ref_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_ref("")


def test_ref_starting_with_hash_raises() -> None:
    """A path is required; `#frag` alone is malformed."""
    with pytest.raises(ValueError, match="malformed"):
        parse_ref("#frag")


def test_ref_starting_with_colon_raises() -> None:
    with pytest.raises(ValueError, match="malformed"):
        parse_ref(":sym")


def test_empty_fragment_treated_as_none() -> None:
    """`path#` parses with fragment=None (regex group is empty str)."""
    p = parse_ref("doc.md#")
    assert p.fragment is None


def test_empty_symbol_treated_as_none() -> None:
    """`path:` parses with symbol=None."""
    p = parse_ref("file.py:")
    assert p.symbol is None
