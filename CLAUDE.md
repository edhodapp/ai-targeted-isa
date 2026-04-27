# CLAUDE.md — ai-targeted-isa

Conventions for AI assistants (Claude, Gemini, others) working in this
repository. This file is read at session start. It captures the project's
load-bearing axioms and process discipline in a form AI tooling can act on.

Human collaborators may also find it useful as a single-page orientation.

---

## Project axiom (load-bearing)

This project explores what an instruction set architecture looks like when
the code generator is AI rather than a human or a classical optimizing
compiler. This is **D002** in `DECISIONS.md`. Treat it as the load-bearing
assumption: most other design choices follow from it.

If you find yourself recommending a design that assumes a *human* asm
writer or a *classical* compiler as the target, stop and ask whether the
recommendation still makes sense with AI as the code generator. Often the
answer changes — that's the point of the project.

## Decision log is the source of truth

`DECISIONS.md` records every load-bearing design choice. Read it before
making recommendations.

**Conventions (do not violate):**
- Sequential numbering, never renumbered.
- **Entry content is immutable.** Never edit or delete an existing entry.
- **Supersession is bidirectional.** A new entry that supersedes an old
  one opens with `**Supersedes:** D00N (deprecated YYYY-MM-DD HH:MM UTC).
  [reason]`. The superseded entry gets an append-only annotation
  *prepended* — `**DEPRECATED YYYY-MM-DD HH:MM UTC — superseded by D00M.**
  [reason]` — with the original body intact below.
- Annotations are the **one permitted addition** to old entries.
- Same-day timestamps include UTC time.

If you make a load-bearing design recommendation, propose it as a new
decision-log entry (next sequential number) with rationale. Do not silently
update old entries.

## Prior-art discipline

`prior_art.md` is the synthesis of architectures whose lessons inform the
design. Before recommending a new ISA feature or memory-hierarchy mechanism:

1. Check whether the same idea has been tried (it often has).
2. Read why it lost or stalled commercially.
3. Ask what the AI-code-gen lens changes about the verdict.

If your recommendation duplicates a buried architecture's idea without
addressing why that architecture failed, that's a gap. State it.

When you cite a paper, architecture, or commercial product, get the names
and dates right. Mathematical and historical claims survive review by
readers who know the domain. Honest "I'm not sure about this date" is
better than confident wrong.

## State observations as observations

Project documents (markdown design notes, prior-art entries, decision
rationale) are written like a lab notebook, not a pitch deck. State what
was observed under what conditions. Hedge empirical claims; state design
rules as design rules.

The test: would an experienced computer architect reading this sentence
push back with "well, actually..."? If yes, qualify it.

This applies to all prose in the repo. It does **not** apply to commit
messages (factual records of what changed) or to entries already in
`DECISIONS.md` (immutable once written).

## Don't conflate "the architecture lost" with "the ideas were wrong"

Itanium failed for many reasons; predication wasn't the cause. Cell failed
because the programming model was unsupported, not because DMA + local
store was wrong. Pull *mechanisms* into the design, leave *configurations*
behind. Re-derive in this project's context — don't copy-paste from
sibling architectures.

## Code generator as a co-equal design artifact

The ISA spec and the AI code-generation pipeline that targets it are
designed together (D003). When you propose an ISA feature, also state how
the code generator emits it correctly and how the audit substrate verifies
the result. Features that pass the ISA-design test but flunk the
code-generator test do not belong.

## Process at this stage

- **Design-only.** No running code yet. Markdown is the artifact.
- **Light CD posture.** Markdown lint and link checking only. When code
  lands, the toolchain (Python with pylint/mypy/pytest, or whatever
  language fits the simulator/backend) gets retrofitted properly — not
  copy-pasted from sibling projects.
- **No mandatory clean-Claude review on docs**, but spot-check substantial
  design changes against the prior-art doc and the existing decision log
  to avoid going in circles. The decision log itself is the primary
  anti-circular tool — write entries when reasoning resolves.

## Contribution shape

Outside contributions go through GitHub PRs with **Developer Certificate
of Origin** sign-off (`git commit -s`). See `CONTRIBUTING.md` for review
process. Substantive design changes require a decision-log entry as part
of the PR.

Ed Hodapp is BDFL on design calls; collaborators are welcome to argue,
propose, and prototype, but the decision log is where the project's
position is durably recorded.
