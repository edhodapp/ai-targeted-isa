# ai-targeted-isa

A research and design exploration: **what does an instruction set
architecture look like when the code generator is AI rather than a human
or a classical optimizing compiler?**

This is an early-stage, design-only project. There is no simulator, no
HDL, no shipping artifact — yet. The current output is markdown: prior-art
review, decision log, and a task list of open design questions. If the
direction proves out, prototypes (a simulator, a small LLVM/MLIR backend,
maybe an FPGA toy) will follow.

## The load-bearing assumption

The historical ISA arc (CISC → RISC → modern OoO) has been constrained by
what compilers can extract. ISA experiments that exposed more parallelism
than compilers could manage — Itanium/EPIC, Cell BE's SPE local store +
DMA, EDGE/TRIPS block-atomic dataflow, Mill's exposed pipeline — failed
commercially despite sound hardware ideas. The recurring failure mode is
the same: *the code generator could not keep up with what the ISA exposed*.

If the code generator is now AI reasoning at whole-program scope, not
trapped in C's aliasing pessimism and able to iterate against measured
cost, that constraint relaxes. The project's central question: which
buried hardware ideas become viable under that lens, and what does an
ISA designed *for* an AI code generator actually look like?

This is recorded as decision **D002** in `DECISIONS.md` and is treated as
a load-bearing project axiom — change it and most of the rest unwinds.

## Where to start reading

1. **`DECISIONS.md`** — ADR-style log of every load-bearing design choice.
   Numbering is sequential and never renumbered; entries are immutable
   once written; supersession is annotated bidirectionally. This is the
   source of truth on what the project has decided and why.

2. **`prior_art.md`** — synthesis pass on eight architectures whose
   compiler-can't failure modes inform the design (Tera MTA, Itanium EPIC,
   Cell BE, TRIPS/EDGE, Mill, CHERI, RISC-V V + cache management, Apple
   AMX / ARM SME). Each is read through the AI-code-gen lens.

3. **`CLAUDE.md`** — conventions for AI assistants working in this repo
   (yours and ours). Captures the project axioms in a form that AI tooling
   can read at session start.

4. **`CONTRIBUTING.md`** — how to contribute, including DCO sign-off and
   decision-log discipline.

## Project status

- **Stage:** design exploration. No running code.
- **Maintainer:** Ed Hodapp (BDFL on design decisions; collaborators
  welcome on issues, PRs, and design critique).
- **License:** Apache License 2.0 (see `LICENSE` and `COPYRIGHT`).
  Apache 2.0 was chosen over MIT specifically for the explicit patent
  grant it carries between contributors — important in CPU-architecture
  territory where ideas can be patented and where multiple contributors
  may co-design a feature.

## How to contribute

Outside contribution is welcome. Most useful at this stage:

- **Prior-art corrections.** If we mischaracterized Itanium, Cell, TRIPS,
  Mill, or any of the others, file an issue with the citation. Honest
  history is the foundation; we'd rather correct than entrench errors.
- **Buried-architecture pointers.** Architectures we should read but
  haven't (e.g., the Lisp Machines, the Transputer, REX/STAR-100, GE-645,
  iWarp) — open an issue with what makes the architecture relevant under
  the AI-code-gen lens.
- **Design critique on the open tasks.** The task list in our working
  notes covers ISA-feature design questions and memory-hierarchy questions.
  PRs that add markdown design notes or counter-proposals are welcome;
  see `CONTRIBUTING.md` for the decision-log discipline.

Implementation contributions (simulator, HDL, compiler backend) are
welcome but premature — the design isn't settled enough for code to be
load-bearing yet. Watch the decision log for when that changes.

## Honest disclaimers

- This is a research direction, not a product roadmap.
- Some of the cross-cutting claims in `prior_art.md` are simplifications
  of multi-causal commercial outcomes. The doc flags its own uncertainty
  where it can; corrections are welcome.
- "AI writes the assembly" is an *assumption* the project tests, not an
  established result. If the assumption fails — if AI code generators
  turn out to have the same blind spots as classical compilers in this
  regime — much of the design unwinds. We treat that as a result worth
  reaching, not a failure to fear.
