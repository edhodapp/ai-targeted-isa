"""Type primitives for the ai-targeted-isa ontology schema.

Mirrors iomoments / fireasmserver where the constraint is generic, so
that a future cross-project audit tool can unify all three projects'
ontologies without per-project type adapters (D007 cross-project goal).
Project-specific literals (`IsaCategory`, `MemoryTier`) are added here
because v1 needs them; a later refactor can split them out if other
projects gain similar concepts.
"""

from typing import Annotated, Literal

from pydantic import StringConstraints

# ---- Constrained string types ------------------------------------------

# First char must be alnum or underscore — prevents IDs like "-rf" from
# being mistaken for CLI flags downstream. Same regex as iomoments'
# SafeId so cross-project audit tooling stays viable.
SafeId = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-zA-Z0-9_][a-zA-Z0-9_-]*$",
        max_length=100,
    ),
]

# Short human-readable name. Matches iomoments cap.
ShortName = Annotated[
    str,
    StringConstraints(max_length=100),
]

# 4000-char cap matches iomoments / fireasmserver so snapshot YAML/JSON
# can cross-round-trip.
Description = Annotated[
    str,
    StringConstraints(max_length=4000),
]

# ---- Lifecycle literals ------------------------------------------------

# Status for any "requirement-shaped" entity (design principles, ISA
# features, memory mechanisms, pipeline stages, artifact types). Same
# values as iomoments' RequirementStatus so cross-project audit
# tooling can interpret them uniformly.
#
#   spec         - written down but no enforcement code or test yet.
#                  Honest default for the current markdown-only state.
#   tested       - a test exists and passes; enforcement code may be
#                  present but hasn't been cross-verified by mutation.
#   implemented  - enforcement code + test + (where applicable) the
#                  measured value meets the stated budget/invariant.
#   deviation    - the system does NOT satisfy the requirement as
#                  written; the rationale field explains why; the
#                  audit tool flags this row for human review.
#   n_a          - not applicable to the current build / target
#                  profile; retained for traceability against the
#                  originating decision.
RequirementStatus = Literal[
    "spec",
    "tested",
    "implemented",
    "deviation",
    "n_a",
]

# Decisions have their own immutability/supersession discipline that
# does not map to spec/tested/implemented.
#
#   live        - current; nothing has superseded it.
#   superseded  - a later decision-log entry replaced this one;
#                 superseded_by must be populated.
#   withdrawn   - removed from the active corpus; the node persists
#                 for traceability but the decision no longer applies.
DecisionStatus = Literal[
    "live",
    "superseded",
    "withdrawn",
]

# ---- ai-targeted-isa-specific literals ---------------------------------

# Coarse classification of ISA features. Used for grouping in audit
# reports and for filtering in queries. Values are deliberately broad
# in v1; finer categories can come once enough features land that the
# coarse grouping is unhelpful.
IsaCategory = Literal[
    "control_flow",
    "data_movement",
    "safety",
    "parallelism",
    "declarative_metadata",
]

# Memory hierarchy tier the mechanism primarily affects.
MemoryTier = Literal[
    "register",
    "scratchpad",
    "l1",
    "l2",
    "l3",
    "dram",
    "nvm",
    "topology",
]
