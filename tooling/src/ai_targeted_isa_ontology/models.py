"""Pydantic models for the ai-targeted-isa ontology (D009 v1).

Six top-level entity collections:
  - decisions          : formal D-numbered DECISIONS.md entries
  - design_principles  : load-bearing axioms
  - isa_features       : ISA mechanisms
  - memory_mechanisms  : memory-hierarchy primitives
  - pipeline_stages    : AI-compiler pipeline stages
  - artifact_types     : artifact types the pipeline emits

All five non-decision entities share standard fields (id, name,
description, rationale, status, implementation_refs, verification_refs)
plus type-specific extensions. Decisions have their own field shape
because they obey a different lifecycle (live / superseded / withdrawn
rather than spec / tested / implemented).
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from ai_targeted_isa_ontology.types import (
    DecisionStatus,
    Description,
    IsaCategory,
    MemoryTier,
    RequirementStatus,
    SafeId,
    ShortName,
)

# A Ref is a string of the form `path[#fragment][:symbol]`. The
# regex catches obviously-broken refs (whitespace, control chars);
# the audit tool (D010) will check that each ref actually resolves
# against the repo.
Ref = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Za-z0-9._/#:-]+$",
        max_length=512,
    ),
]

# An ISO-8601-like UTC timestamp (e.g. "2026-04-28 05:13 UTC"). Same
# shape as the timestamps in DECISIONS.md so transcribing entries is
# straightforward; not a full RFC 3339 validator.
UtcTimestamp = Annotated[
    str,
    StringConstraints(
        pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC$",
        max_length=32,
    ),
]


class _Frozen(BaseModel):
    """Base model that disallows mutation after construction.

    Ontology entities are immutable values; mutation would break
    content-hash comparisons and the reproducibility the build tool
    promises.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class Decision(_Frozen):
    """One formal entry from DECISIONS.md."""

    id: SafeId
    d_number: int = Field(ge=1)
    name: ShortName
    date_utc: UtcTimestamp
    summary: Description
    rationale_ref: Ref
    status: DecisionStatus
    supersedes: list[SafeId] = Field(default_factory=list)
    superseded_by: SafeId | None = None

    @model_validator(mode="after")
    def _check_supersession_consistency(self) -> Self:
        """status=superseded iff superseded_by is populated."""
        if self.status == "superseded" and self.superseded_by is None:
            raise ValueError(
                f"decision {self.id}: status=superseded requires "
                "superseded_by"
            )
        if self.status == "live" and self.superseded_by is not None:
            raise ValueError(
                f"decision {self.id}: status=live forbids superseded_by"
            )
        return self


class _RequirementBase(_Frozen):
    """Common fields for all requirement-shaped entities.

    The status lifecycle and refs discipline are described in
    types.RequirementStatus and in D007 / D009.
    """

    id: SafeId
    name: ShortName
    description: Description
    rationale: Description
    status: RequirementStatus
    implementation_refs: list[Ref] = Field(default_factory=list)
    verification_refs: list[Ref] = Field(default_factory=list)


class DesignPrinciple(_RequirementBase):
    """A load-bearing axiom of the project."""

    derives_from_decisions: list[SafeId] = Field(default_factory=list)


class ISAFeature(_RequirementBase):
    """A specific ISA mechanism under design."""

    category: IsaCategory


class MemoryMechanism(_RequirementBase):
    """A memory-hierarchy primitive under design."""

    tier: MemoryTier


class PipelineStage(_RequirementBase):
    """One stage of the AI-compiler pipeline."""

    stage_index: int = Field(ge=0)
    inputs: list[SafeId] = Field(default_factory=list)
    outputs: list[SafeId] = Field(default_factory=list)
    gates: list[ShortName] = Field(default_factory=list)


class ArtifactType(_RequirementBase):
    """An artifact type the pipeline emits."""

    file_glob: ShortName
    gate_tools: list[ShortName] = Field(default_factory=list)


class Ontology(_Frozen):
    """Root container for the validated ontology."""

    decisions: list[Decision] = Field(default_factory=list)
    design_principles: list[DesignPrinciple] = Field(default_factory=list)
    isa_features: list[ISAFeature] = Field(default_factory=list)
    memory_mechanisms: list[MemoryMechanism] = Field(default_factory=list)
    pipeline_stages: list[PipelineStage] = Field(default_factory=list)
    artifact_types: list[ArtifactType] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_unique_ids(self) -> Self:
        """Each section's ids must be locally unique."""
        _assert_unique("decisions", [d.id for d in self.decisions])
        _assert_unique(
            "design_principles",
            [p.id for p in self.design_principles],
        )
        _assert_unique(
            "isa_features", [f.id for f in self.isa_features],
        )
        _assert_unique(
            "memory_mechanisms",
            [m.id for m in self.memory_mechanisms],
        )
        _assert_unique(
            "pipeline_stages",
            [s.id for s in self.pipeline_stages],
        )
        _assert_unique(
            "artifact_types",
            [a.id for a in self.artifact_types],
        )
        return self


def _assert_unique(section: str, ids: list[str]) -> None:
    """Raise if any id repeats within a section."""
    seen: set[str] = set()
    for ident in ids:
        if ident in seen:
            raise ValueError(
                f"section '{section}' has duplicate id: {ident}"
            )
        seen.add(ident)
