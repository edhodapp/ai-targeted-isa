"""Shared types for the audit tool."""

from __future__ import annotations

from dataclasses import dataclass
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
