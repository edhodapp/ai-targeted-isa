"""Tests for types.py — the ontology schema's type primitives.

Covers each constrained-string regex / length cap and confirms the
literal type values are exactly the documented set.
"""

from __future__ import annotations

import typing

import pytest
from pydantic import BaseModel, ValidationError

from ai_targeted_isa_ontology import types as t


class _SafeIdHolder(BaseModel):
    value: t.SafeId


class _ShortNameHolder(BaseModel):
    value: t.ShortName


class _DescriptionHolder(BaseModel):
    value: t.Description


# ---- SafeId -------------------------------------------------------------


@pytest.mark.parametrize(
    "good",
    ["a", "Z", "1", "_", "abc", "abc-def", "a_b-c_1", "X9_q-r"],
)
def test_safe_id_accepts_valid(good: str) -> None:
    """Valid IDs survive validation unchanged."""
    assert _SafeIdHolder(value=good).value == good


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "-rf",
        "-leading-dash",
        "has space",
        "has.dot",
        "has/slash",
        "has:colon",
        "x" * 101,
    ],
)
def test_safe_id_rejects_invalid(bad: str) -> None:
    """First-char-alnum-or-underscore rule catches CLI-flag-shaped IDs."""
    with pytest.raises(ValidationError):
        _SafeIdHolder(value=bad)


# ---- ShortName ----------------------------------------------------------


def test_short_name_accepts_up_to_cap() -> None:
    name = "x" * 100
    assert _ShortNameHolder(value=name).value == name


def test_short_name_rejects_over_cap() -> None:
    with pytest.raises(ValidationError):
        _ShortNameHolder(value="x" * 101)


# ---- Description --------------------------------------------------------


def test_description_accepts_up_to_cap() -> None:
    body = "x" * 4000
    assert _DescriptionHolder(value=body).value == body


def test_description_rejects_over_cap() -> None:
    with pytest.raises(ValidationError):
        _DescriptionHolder(value="x" * 4001)


# ---- Literal types ------------------------------------------------------
#
# typing.get_args reflects the literal members at runtime. Locking the
# expected sets here means a future drift in types.py (e.g. silently
# dropping "deviation") fails the test rather than the audit.


def test_requirement_status_values_are_documented_set() -> None:
    expected = {"spec", "tested", "implemented", "deviation", "n_a"}
    assert set(typing.get_args(t.RequirementStatus)) == expected


def test_decision_status_values_are_documented_set() -> None:
    expected = {"live", "superseded", "withdrawn"}
    assert set(typing.get_args(t.DecisionStatus)) == expected


def test_isa_category_values_are_documented_set() -> None:
    expected = {
        "control_flow",
        "data_movement",
        "safety",
        "parallelism",
        "declarative_metadata",
    }
    assert set(typing.get_args(t.IsaCategory)) == expected


def test_memory_tier_values_are_documented_set() -> None:
    expected = {
        "register",
        "scratchpad",
        "l1",
        "l2",
        "l3",
        "dram",
        "nvm",
        "topology",
    }
    assert set(typing.get_args(t.MemoryTier)) == expected
