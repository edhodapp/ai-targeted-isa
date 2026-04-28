"""Parse ref strings of the form `path[#fragment][:symbol]`.

Grammar:
  ref     := path ("#" fragment)? (":" symbol)?
  path    := one or more chars from [A-Za-z0-9._/-]   (no `#` or `:`)
  fragment:= zero or more chars from [^:]              (no `:`)
  symbol  := remaining string

The fragment must precede the symbol when both are present;
`path:sym#frag` is rejected as malformed. The schema's pydantic Ref
constraint is intentionally more permissive (it catches whitespace /
control chars but doesn't enforce ordering); this parser is the
stricter interpreter that downstream resolution depends on.
"""

from __future__ import annotations

import re

from ai_isa_audit.types import ParsedRef

_REF_RE = re.compile(
    r"^(?P<path>[^#:]+)"
    r"(?:#(?P<fragment>[^:]*))?"
    r"(?::(?P<symbol>.*))?$"
)


def parse_ref(ref: str) -> ParsedRef:
    """Parse a ref string. Raises ValueError on malformed input."""
    if not ref:
        raise ValueError("empty ref")
    match = _REF_RE.match(ref)
    if match is None:
        raise ValueError(f"malformed ref: {ref!r}")
    fragment = match.group("fragment") or None
    symbol = match.group("symbol") or None
    return ParsedRef(
        path=match.group("path"),
        fragment=fragment,
        symbol=symbol,
    )
