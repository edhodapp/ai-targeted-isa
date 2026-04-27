# Pipeline Design — From Intent to Audited Artifact

This document is the project's first pass at the meta-design that frames
all subsequent work: the pipeline by which design intent becomes audited
artifacts. Per [`DECISIONS.md`](DECISIONS.md) **D006**, this pipeline
*is* the project's CD pipeline. Today its only artifact type is markdown
design notes. Eventually it produces ISA-targeted assembly. The shape is
the same at every scope.

This is task #1 from the working task list and a co-equal design artifact
to the ISA itself ([D003](DECISIONS.md)).

## The pipeline at a glance

```text
+-----------+     +-----------------+     +-------+     +---------+
|  intent   | --> | transformation  | --> | gates | --> | promote |
+-----------+     +-----------------+     +-------+     +---------+
                                                              |
                                                              v
                                                    +-------------------+
                                                    | audited artifact  |
                                                    | (DAG node + facts)|
                                                    +-------------------+
```

Every stage takes one or more artifacts as input, runs a transformation,
gates the output, and on success promotes the result into the project's
audited corpus. The audit DAG records what was done, by what, with what
inputs, and which gates were passed.

The pipeline is recursive: a "transformation" may itself be a sub-pipeline
with its own gates and DAG nodes. Today the recursion has depth 1
(markdown intent → markdown artifact); when code lands, recursion deepens.

## Stages, in their current and projected forms

The current pipeline is small. The future pipeline is large. Both are
listed so the trajectory is visible.

### Today (markdown-only artifact type)

| Stage | Input | Transformation | Gates | Output |
| --- | --- | --- | --- | --- |
| 1. Intent capture | Conversation between Ed and an AI assistant | Synthesis into a design statement, prior-art question, or decision proposal | Honest-claim discipline (`CLAUDE.md`); reference to the relevant decision in `DECISIONS.md` | Reviewable intent statement (in conversation, in an issue, or in a draft markdown section) |
| 2. Markdown synthesis | Intent statement + prior-art doc + decision log | Drafting markdown — design notes, prior-art entries, decision-log entries, task-list updates | Lab-notebook stance; cross-references as proper links; observations marked as observations | Draft markdown file or section |
| 3. Local gates | Draft markdown | `markdownlint-cli2` run via the `scripts/pre-commit-hook.sh` symlinked into `.git/hooks/pre-commit` | MD004/dash, MD022, MD032, MD034, MD041, MD046; configured in `.markdownlint.json` | Lint-clean markdown |
| 4. CI gates | Pushed commit | `markdownlint-cli2` + `lychee` link check via `.github/workflows/lint.yml` | Same lint config + all links resolvable | Verified commit on `main` |
| 5. Promotion | Verified commit | None — promotion is the act of merging | None additional | Audited artifact: file in repo + commit in git history + (eventually) DAG node |

That's the entire current pipeline. Five stages, two of them gates,
producing one artifact type.

### Tomorrow (when the first non-markdown artifact type lands)

The next likely artifact types, in order of probable arrival:

1. **Executable spec / formal model** (Python or a formal-methods
   language). Written when the ISA design solidifies enough to want a
   reference semantics that can be exercised. Adds: type checker,
   property-based test runner, semantic equivalence gates.
2. **Simulator** (probably Python first, then a C/Rust port if perf
   matters). Adds: full Python toolchain (pylint / mypy --strict /
   pytest with branch coverage), per-instruction conformance tests
   against the spec.
3. **Compiler backend stub** (likely an LLVM or MLIR target, or a
   from-scratch lowering pass). Adds: lowering correctness tests,
   regression suite against a kernel zoo.
4. **ISA-targeted assembly** (the eventual product of the AI-compiler
   pipeline). Adds: ISA-validity check, functional equivalence against
   the spec, performance regression against a baseline (RV64GCV per
   task #16).

For each: per [D006](DECISIONS.md), **the gates land before the artifact.
No exceptions.** A simulator commit cannot land before its pylint /
mypy / pytest gates are operational and CI-integrated.

### The eventual full pipeline

Once all four future artifact types are integrated, the pipeline becomes:

```text
intent
  -> design markdown (gated)
  -> formal spec     (gated against design)
  -> simulator       (gated against spec)
  -> backend lowering (gated against spec via simulator)
  -> emitted asm     (gated against spec; perf-checked vs baseline)
```

Each arrow is a stage. Each stage has gates and produces a DAG node. The
audit trail for any emitted asm instruction is queryable backward through
every transformation to the design intent.

## The stage abstraction

A pipeline stage is a tuple `(name, inputs, transformation, gates,
outputs)`:

- **name** — unique identifier; used in the DAG as the edge label.
- **inputs** — typed references to artifacts (or, at stage 1, to intent
  statements). Types are project-defined: `intent`, `markdown`,
  `python_module`, `formal_spec`, `asm_block`, etc.
- **transformation** — the work that converts inputs into a candidate
  output. May be human, AI-assisted, or fully automated. Recorded in
  the DAG by author / agent / commit.
- **gates** — verifications that must all pass before promotion. Gates
  are append-only (you can add more, you don't remove them; their
  pass/fail history is part of the audit trail).
- **outputs** — typed artifacts produced. On gate failure, no output is
  promoted; the failure itself is recorded as a fact.

Stages are **first-class**: adding a new artifact type means adding new
stages, which means writing down the gate set and the DAG schema for the
new artifact type *before* writing the first artifact of that type. This
is the per-artifact CD-first rule from D006.

## The audit DAG

The DAG is the structural memory of the pipeline. Implementation details
are deliberately under-specified at this stage; the structural role is
fixed.

### Nodes

Every artifact in the project corresponds to one DAG node. Today:

- Each `.md` file in the repo.
- Each entry in `DECISIONS.md` (D001–D006 are six logical artifacts
  even though they share a file).
- Each task in the working task list.
- Each commit on `main` (commits are not artifacts in their own right
  but are *fact-bearing*: they record which artifact versions passed
  which gates at what time).

### Edges

Edges record derivation. An edge from artifact A to artifact B means
"B was produced using A as input." Edges are typed by the stage that
produced them: `synthesis`, `lint`, `link-check`, `decision-supersedes`,
`task-implements`, etc.

The decision-log supersession convention (D003 → D00N → D00M, with
bidirectional annotations) is already a hand-maintained DAG with this
shape. The audit DAG generalizes the same pattern across artifact types.

### Facts

Each node carries facts:

- **provenance** — which agent (human or AI session) produced it, against
  which intent, citing which prior artifacts.
- **gate history** — which gates ran, when, with what result, against
  which version.
- **status** — current (live), deprecated (annotated by a successor),
  withdrawn (deleted from the corpus, but the node persists).

### Where the DAG lives — resolved by D007

This was the largest open question when this document was first written;
it was resolved by [D007](DECISIONS.md) in favour of the
YAML/pydantic/audit-tool pattern proven in `~/iomoments/tooling/`.

The resolution in summary: a single hand-edited YAML file is the
authoring surface; pydantic validates the schema; a build tool produces
a content-hash-gated JSON snapshot that is the canonical artifact for
downstream tooling; a separate audit binary resolves every reference
against the actual repo and reports drift. Every entry carries a status
lifecycle (`spec | tested | implemented | deviation | n_a`) plus
implementation and verification refs. The audit tool flags
`status≠spec` with empty refs as a "provable lie" — the discipline
that lets the ontology lead the implementation honestly.

The three alternatives originally sketched here (git-history-as-DAG,
sidecar JSON / SQLite, frontmatter per file) are recorded in D007 as
the alternatives considered. The iomoments pattern is essentially a
refinement of "sidecar JSON" with the authoring surface lifted to YAML
for human editability and pydantic added for type safety; the status
lifecycle and the audit tool's drift detection are the inventions that
make this pattern qualitatively better than a passive sidecar.

This pattern requires Python as a new artifact type. Per [D006](DECISIONS.md)
the Python gates land before any pydantic; that installation plan is
[D008](DECISIONS.md).

## Adding a new artifact type — the protocol

When the project decides to support a new artifact type X (e.g., Python
modules for the simulator):

1. **Decision-log entry.** A new entry in `DECISIONS.md` records the
   choice to support X, the rationale, and the artifact's role in the
   pipeline.
2. **Gate definition.** Write down the gates for X *before* writing any
   X. For Python: pylint config, mypy strictness level, pytest coverage
   target, hook integration, CI workflow.
3. **DAG schema extension.** Define the DAG node shape and edge types
   for X. What does an X node carry as provenance? What earlier-stage
   artifacts are valid X inputs?
4. **Stage installation.** Add the stage to the pipeline:
   transformation conventions, gate runners, CI workflow. The stage
   must be operational on a deliberately-broken X before any real X is
   committed (CD-first verifies the gates fail when they should).
5. **First artifact lands.** Only now is the first X file allowed in.
   It travels through the new stage, with all gates active.

Skipping any of (1)–(4) violates D006 and creates the parallel-pipelines
drift the framing exists to prevent.

## What this pipeline gives the ISA design

The reason this matters for the ISA itself, not just for the project's
hygiene:

- **Auditable code generation.** When AI emits asm against the eventual
  ISA, every instruction has DAG provenance back to the design intent
  and to the spec it implements. The AI-code-gen failure mode that
  killed Itanium (compiler couldn't reliably extract what the ISA
  exposed) is invisible without an audit trail. The DAG makes that
  failure visible at the instruction level.
- **Equivalence verification.** Gates against the formal spec mean the
  AI compiler's output is checked, not trusted. This is the discipline
  that makes "AI writes the asm" credible per D002.
- **Iteration without regression.** Per-call-site optimizations
  (task #13: layout selection per call site), speculation budgets
  (task #15), and the other AI-distinguishing features depend on the
  pipeline being able to produce per-call-site code with full
  provenance. A flat compile-once compiler can't do this; a stage-aware
  pipeline with audit can.

## Open questions for the next iteration

These are deferred to subsequent decision-log entries and design
documents. Listed here so they don't get lost.

1. **DAG implementation choice.** ~~Frontmatter? Sidecar? Hybrid?~~
   **Resolved by D007** (adopt iomoments YAML + pydantic + audit
   pattern). Implementation gated on D008 (Python tooling installation).
2. **Intent representation.** Free-form prose in conversation has worked
   so far. Does it scale? Should there be a schema for intent statements
   (problem, constraints, success criteria)?
3. **Gate authorship.** When a new artifact type is added, who writes
   the gates — Ed by hand, AI-assisted, or extracted from a sibling
   project? Per "principles transfer; processes do not": probably
   re-derived per project, even when a sibling has a similar set.
4. **Equivalence checking for asm.** This is the hardest gate to
   build. Strategies range from differential testing (run asm + spec,
   compare outputs) to formal verification (prove asm implements spec).
   Out of scope for the pipeline framing; in scope for whichever future
   decision-log entry adopts an approach.
5. **Pipeline observability.** When something fails, what does the
   audit trail show, and how is it surfaced? Today: GitHub Actions
   logs. Tomorrow: probably needs more structured per-stage failure
   reporting, especially for gates that are expensive (full simulator
   runs, equivalence checks).
6. **Conversational intent capture and the DAG.** Most intent so far
   has been Ed-and-Claude conversation that lands as a decision-log
   entry. Should the conversation itself be part of the audit trail,
   or only the resolved artifact? The privacy posture (private memory
   in `~/.claude/` vs public `DECISIONS.md`) suggests the latter, but
   it loses some context.

## Summary

The pipeline is a small, recursive structure: stages with gates,
producing typed artifacts, recorded in an audit DAG. Today it lints
markdown. Tomorrow it emits asm. The shape is invariant; the gates and
artifact types evolve. The CD-first rule applies per artifact type, not
just project-wide. The DAG is the structural memory; its implementation
is an open design question to be resolved in its own decision-log entry
when the first non-markdown artifact type is approached.

This document is itself an artifact. It was produced by stage 2 (markdown
synthesis) from the intent statements in conversation, the prior-art
synthesis in [`prior_art.md`](prior_art.md), and the decisions D001–D006
in [`DECISIONS.md`](DECISIONS.md). It will be gated by stage 3 (the
pre-commit hook) and stage 4 (CI) before it is promoted to the audited
corpus.
