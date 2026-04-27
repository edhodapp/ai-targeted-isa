# Decision Log — hwdesign/cpu

ADR-style log for the AI-targeted CPU architecture exploration. Conventions
(per `~/.claude/CLAUDE.md`):

- **Sequential numbering, never renumbered.** Entries appear in creation order.
- **Entry content is immutable.** Once written, decision text and rationale
  are never edited or deleted.
- **Supersession is bidirectional.** A new entry that supersedes an older one
  opens with a `**Supersedes:** D00N (deprecated YYYY-MM-DD HH:MM UTC). [reason]`
  back-pointer. The superseded entry gets an append-only annotation
  *prepended* — `**DEPRECATED YYYY-MM-DD HH:MM UTC — superseded by D00M.**
  [reason]` — with the original body left intact below it.
- **The annotation is the one permitted addition** to an old entry. It records
  a later event (supersession), not a revision; content immutability holds.
- **Timestamps include UTC time** when same-day ordering matters.

This log is expected to grow with frequent supersession as the design iterates;
that's by design, not a sign of churn. Reading the log top-to-bottom should
reconstruct how thinking evolved; landing on any entry should let a reader
follow forward (annotation) or backward (Supersedes) to find the live decision
in one step.

---

## D001 — Treat `~/hwdesign/cpu` as exploratory blue-sky, not a deliverable

**Date:** 2026-04-27 18:50 UTC

The directory sits in `~/hwdesign/`, sibling-shaped to `~/math/` subdirs.
It is for prototype/ideation work on CPU architecture, not for shipping an
artifact. Per the global "CD-first for deliverables; review-discipline-first
for experiments" rule, this means: no CD pipeline, no Makefile-level build
loop, no deploy target, no directory skeleton predicted in advance. Structure
emerges per experiment. Review discipline still applies on any functional
commits.

If a concrete prototype matures into something downstream consumers depend on,
spawn a new repo CD-first per the "principles transfer; processes do not"
rule — re-derive its pipeline rather than copy-pasting from this exploratory
work.

## D002 — Design lens: the ideal ISA assumes AI writes the assembly

**Date:** 2026-04-27 18:55 UTC

The exploration is framed by the question: *what does an ISA look like when
the code generator is AI rather than a human or a classical compiler?* This
is the load-bearing assumption that distinguishes this work from
contemporary ISA design.

**Rationale.** The historical ISA arc (CISC → RISC → modern OoO) has been
constrained by what compilers can extract. ISA experiments that exposed more
parallelism than compilers could manage — Itanium/EPIC's predicated bundles,
Cell BE's SPE local stores + DMA, EDGE/TRIPS's block-atomic dataflow, Mill's
exposed pipeline — failed commercially despite sound hardware ideas. AI code
generators reasoning at whole-program scope, not trapped in C's aliasing
pessimism, relax that constraint. The "ideal AI ISA" question is concretely:
*which buried hardware ideas become viable when the code generator can do
what compilers couldn't?*

This lens cascades into specific ISA features (explicit-over-implicit
semantics, first-class predication, block-atomic dataflow, per-instruction
effect annotations, etc.) and into the memory hierarchy's treatment as
software-managed rather than hardware-guessed.

## D003 — AI-as-compiler pipeline is a co-equal design artifact to the ISA

**Date:** 2026-04-27 19:00 UTC

The ISA spec and the AI code-generation pipeline that targets it are designed
together, not sequentially. The pipeline is multi-layered (intent →
intermediate representations → ISA-targeted asm) with stages chosen for what
AI does well (whole-program reasoning, intent capture, prior-art pattern
matching, proof-obligation tracking) rather than what classical compiler
passes do well.

**Audit substrate.** The pipeline's stage-to-stage transitions are tracked
via the ontology DAG conventions established in Ed's sibling projects.
Provenance for the final asm output is therefore inspectable: any instruction
in the generated code traces back through the DAG to the design intent it
implements. This is the discipline that makes AI-generated low-level code
trustworthy at scale.

**Why co-equal.** If the ISA is designed in isolation and the pipeline is
treated as an afterthought, the design risks repeating the EPIC/Cell/TRIPS
failure mode at the AI layer instead of the compiler layer — exposing
parallelism the generator cannot reliably extract. Designing both together
keeps the ISA's exposed complexity matched to what the pipeline can audit
and emit correctly.

## D004 — Publish as a public GitHub repository for outside collaboration

**Date:** 2026-04-27 20:16 UTC

Repository will be published publicly as **`ai-targeted-isa`** to invite
outside collaboration. The project remains design-only at this stage, with
markdown as the artifact (decision log, prior-art synthesis, design notes,
task list). Outside contributions are most useful as prior-art corrections,
buried-architecture pointers, and design critique on the open questions in
the task list.

**Governance.** Ed Hodapp is BDFL on design decisions. Collaborators argue,
propose, and prototype via issues and PRs; the decision log is where the
project's position is durably recorded. This is *not* the
single-author / no-contributions posture used in some sibling projects —
the explicit aim here is to surface ideas for critique by people with
real Itanium / Cell / TRIPS / Mill / CHERI background.

**Why now.** The prior-art synthesis (D002 → `prior_art.md`) and the
load-bearing axiom (AI writes the assembly) already have outside-critique
value before any further design work. Surfacing them publicly now exposes
the framing to challenge before more design choices stack on top.

**IP hygiene.** Contributions require Developer Certificate of Origin
(DCO) sign-off — every commit carries a `Signed-off-by:` line. No CLA at
this stage. License terms governed by D005.

**What this changes about process.** This crosses the experimental →
deliverable transition (per the global "CD-first for deliverables" rule).
The deliverable here is markdown, so the CI shape is markdown linting and
link checking, not a full Python toolchain. When code lands (simulator,
backend), the toolchain gets retrofitted properly — re-derived in this
project's context, not copy-pasted from sibling projects.

## D005 — License under Apache 2.0 (not MIT)

**Date:** 2026-04-27 20:17 UTC

License: **Apache License 2.0**, with a split LICENSE + COPYRIGHT file
layout. LICENSE holds the verbatim Apache 2.0 text; COPYRIGHT holds the
project notice (project name + copyright holder + SPDX tag + Apache
boilerplate + contribution policy pointing to CONTRIBUTING.md and DCO).

**Why Apache 2.0 over MIT.** The shortlist was MIT, Apache 2.0, and BSD-3.
All three are permissive enough for the "ideas should flow widely" intent
of the project. Apache 2.0 was chosen for two reasons:

1. **Explicit patent grant between contributors.** CPU architecture is
   patent-heavy territory — TRIPS, Mill, CHERI, and most commercial ISA
   features have associated patents. Apache 2.0 grants an irrevocable
   patent license from each contributor for any patents they hold that
   would otherwise read on their contribution. MIT and BSD-3 are silent
   on patents, which leaves a contributor free to assert later. For a
   project where multiple people may co-design a feature, Apache 2.0's
   explicit grant is the more defensive choice without sacrificing
   permissiveness.
2. **Standard in adjacent ecosystems.** RISC-V specifications, LLVM,
   MLIR, TVM, and most modern compiler-infrastructure projects are
   Apache 2.0. Choosing the same license reduces friction for
   contributors who already operate under it.

**License layout adapted from Ed's standard convention.** The standard
split is LICENSE (verbatim license text, never modified) + COPYRIGHT
(short notice, four sections). Apache 2.0 is in LICENSE; COPYRIGHT
adapts to the new posture: the "no external contributions accepted"
section that appears in Ed's AGPL-licensed projects is replaced with a
"contributions welcome via DCO sign-off" section pointing to
CONTRIBUTING.md.

**Why not AGPL.** AGPL is Ed's default for his single-author proprietary
projects with OEM-licensing flexibility (e.g. fireasmserver). It is
wrong here for two reasons: (a) the project's product is *ideas* meant
to flow into commercial silicon implementations, not network-served
software; AGPL §13 has no purchase. (b) Outside collaboration is the
explicit goal — an AGPL repo with a "no contributions" stance and
commercial-license-required path is incompatible with that.

## D006 — The AI-compiler pipeline IS the project's CD pipeline

**Date:** 2026-04-27 21:25 UTC

The multi-stage AI code-generation pipeline (D003) and the project's CD
pipeline are not two different systems. They are **the same system** viewed
at different scales.

**The isomorphism.** A CD pipeline is `source → build → gate → deploy`,
producing artifacts (binaries, packages, deployments) with provenance
tying each artifact back to a source commit. The AI-compiler pipeline is
`intent → transformation → gate → emit`, producing code artifacts
(eventually ISA-targeted asm) with provenance — the audit DAG (D003) —
tying each instruction back to design intent. The shapes match. The DAG
is the structural memory of the pipeline; gate-passes are facts recorded
against artifact nodes.

**Consequences.**

1. **The current CI is the embryonic pipeline.** Markdownlint + lychee
   today are not "infrastructure that surrounds the design work." They
   *are* the pipeline at its current scope, where the only artifact type
   is markdown. Adding new artifact types means adding new pipeline
   stages.

2. **CD-first applies per artifact type, not just project-wide.** When
   the project starts emitting Python (e.g. for a simulator), the Python
   gates — pylint, mypy, pytest, branch coverage, hooks, CI integration —
   land *before* any Python file. When the project starts emitting
   ISA-targeted asm, the asm gates (ISA validity, functional equivalence
   to intent) land before any asm. **No exceptions.** The "CD-first for
   deliverables" rule from Ed's other projects applies here at higher
   resolution: each artifact type within the pipeline is independently
   CD-first.

3. **The audit DAG is not a sidecar.** It is the project's memory of
   what artifacts exist, how they derived from each other, and which
   gates each one passed. Implementation details (where the DAG lives,
   how it's queried, what intermediate forms it captures) are open
   questions in the pipeline design, but the structural role is fixed.

**Why this framing now.** Without it, future contributors (and future
sessions) might treat "CD/CI" and "AI compiler pipeline" as separate
concerns and end up with two parallel provenance systems, two parallel
gate sets, and ambiguity about which one is authoritative. Naming them
as one thing forecloses that drift.

**How this shapes task #1 (pipeline framing).** The pipeline design must
specify (a) the stage abstraction, (b) the audit DAG schema, (c) the
artifact-type plug-in protocol, and (d) the CD-first sequencing rule
for adding new artifact types. The current markdown-only state and the
eventual asm-emission state are both points on the same trajectory.

## D007 — Adopt the iomoments YAML + pydantic + audit ontology pattern

**Date:** 2026-04-27 22:08 UTC

The audit DAG implementation choice from `pipeline_design.md`'s open
questions is resolved: ai-targeted-isa adopts the pattern proven in Ed's
sibling project `~/iomoments/tooling/`, re-derived for this project's
domain.

**The pattern adopted (in detail).**

1. **Single authoring surface = one YAML file.** Hand-edited at a stable
   path (proposed: `ontology/ai-targeted-isa.yaml`). Sections defined by
   the schema; entries are typed records, not free-form prose.
2. **Validation via pydantic.** Constrained-string types (`SafeId`,
   `ShortName`, `Description`), `Literal` enums for status / cardinality
   / artifact-type / etc. Schema rejects malformed input at parse time.
3. **Build = content-hash-gated JSON snapshot.** A `build` tool reads the
   YAML, validates it, and appends a snapshot to a versioned JSON file
   when the content hash changes. The JSON is the canonical artifact for
   downstream tooling and the historical record.
4. **Status lifecycle on every entry.** `spec | tested | implemented |
   deviation | n_a`, plus `implementation_refs` and `verification_refs`
   lists pointing at concrete locations in the repo.
5. **Separate `audit` tool.** Resolves every ref against the actual repo
   (file exists? anchor / symbol exists?), runs consistency rules
   (notably: empty refs + `status≠spec` = provable lie, flagged), emits
   a flat report consumable by humans and by CI gates.
6. **Draft-first is endorsed.** The YAML may project the future via
   `status: spec` with empty refs. The audit tool detects when reality
   diverges from any non-`spec` claim. This is the discipline that lets
   the ontology lead the implementation honestly.

**What ai-targeted-isa re-derives.** Schema entities (ISA features,
memory tiers, pipeline stages, design constraints — not iomoments'
workloads / moments / probes / verdicts). Ref grammar (markdown sections
by anchor today; later formal-spec entries, simulator code, kernel test
files, asm samples — not iomoments' C / eBPF symbols). All Python code
in `tooling/`. Per Ed's "principles transfer; processes do not" rule,
the iomoments tooling is reference, not source for copy-paste.

**What stays compatible at the interface level.** Type primitives
(`SafeId` regex, length caps). Status lifecycle values. Ref grammar
conventions where applicable (`path:symbol` shape; for markdown,
`path.md#anchor`). Audit report structure (flat list of
ConstraintReport-shaped records plus a Summary). The point of the
shared interface is to leave the door open for a unified
cross-project audit tool later (iomoments, fireasmserver, and
ai-targeted-isa would all conform).

**Why this pattern over alternatives.** The three alternatives sketched
in `pipeline_design.md` were git-history-as-DAG, sidecar
JSON / SQLite, and frontmatter in each artifact. The iomoments pattern
is effectively a refinement of "sidecar JSON" with the authoring
surface lifted to YAML for human editability and pydantic added for
type safety. The status lifecycle and the audit tool's
"provable lie" detection are the inventions that make this pattern
qualitatively better than a passive sidecar. They are exactly what
D006's audit DAG requires.

**Dependency: D008 must land first.** Adopting this pattern means
adopting Python as a new artifact type. Per D006 (CD-first per artifact
type), the Python gates land before any pydantic file. D008 specifies
the gate set and installation plan.

## D008 — CD-first plan for the Python tooling artifact type

**Date:** 2026-04-27 22:08 UTC

D007 introduces Python as the second artifact type in this project (the
first being markdown). Per D006, the gates for the Python type land
*before* the first `.py` file is committed. This decision specifies the
gate set, the installation order, and the verification that the gates
actually fail when they should.

**Gate set for Python in this project.** Mirrors the global Python
quality bar from `~/.claude/CLAUDE.md`:

- **Lint:** flake8 with `--max-complexity=5`.
- **Style + correctness:** pylint using the Google Python Style Guide
  config at `~/.claude/pylintrc`. (The config is project-external and
  shared across Ed's projects; this project pins the version it
  validates against in its own pyproject.toml.)
- **Type checking:** mypy `--strict`.
- **Tests:** pytest with `--cov --cov-branch`, branch coverage target
  100% for new code (negotiable for unreachable failure paths,
  documented per Ed's "track every requirements deviation" rule).
- **Python floor:** >= 3.11.
- **Data structures:** pydantic `BaseModel` for typed records (matches
  iomoments).

**Project layout for the Python tooling.** Subdirectory at the repo root,
named to match the iomoments shape so cross-project tooling extraction
stays viable later:

```text
tooling/
  pyproject.toml          # project metadata, deps, tool configs
  src/
    <package_name>/       # source modules
  tests/                  # pytest suite
```

`tooling/.venv/` is gitignored (already covered by the existing
`.gitignore`). The repo root keeps its existing markdown-only shape;
Python lives in `tooling/`.

**Installation order (must be performed in this order).**

1. Create `tooling/pyproject.toml` with deps (`pydantic`, `pyyaml`),
   dev-deps (`pytest`, `pytest-cov`, `flake8`, `pylint`, `mypy`), and
   per-tool configuration (mypy strict, pytest coverage settings, etc.).
2. Create `tooling/.venv/` and install dependencies.
3. Extend `scripts/pre-commit-hook.sh` to run flake8, pylint, mypy, and
   pytest on staged `.py` files (with the same "no tools = error"
   discipline as the existing markdown gate).
4. Extend `.github/workflows/lint.yml` (or add a sibling workflow) with
   a Python job that mirrors the local hook: same gates, same configs,
   same expected outcome.
5. **Verify the gates fail when they should.** Commit a deliberately-
   broken `.py` file (lint violation, type error, failing test) on a
   throwaway branch or in a single test commit, observe each gate fire,
   then revert. This is the per-artifact equivalent of the negative test
   we ran on the markdown pre-commit hook.
6. Only after step 5 passes: write the first real Python file
   (most likely the pydantic schema for the ontology).

**Why steps 5 and 6 are not collapsible.** Skipping the deliberate-break
verification leaves the project in a state where the gates *might* be
operational but no one has *proven* they catch real failures. That's
the same trust gap the iomoments audit tool's "provable lie" detection
is designed to close, applied at the gate-installation level. The cost
of step 5 is one commit + one revert; the cost of skipping it is a
silently-broken gate discovered only when a real failure slips through.

**Out of scope for this decision.** The pydantic schema content (which
entities, which constraints, which verdict shape) is D009's problem.
This decision installs the *gates*, not the *artifacts*. Drafting
schema content before the gates exist would violate D006.

**Effort estimate.** Steps 1–4 are mostly transcription from Ed's
sibling Python projects (re-derived per "principles transfer; processes
do not", but the targets are clear). Step 5 is one cycle of
deliberate-break commit + observation + revert. Total: hours, not days.
