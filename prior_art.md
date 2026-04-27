# Prior Art — ISA Experiments That Bet on the Code Generator

A reading and synthesis pass on architectures that exposed more parallelism,
more memory-hierarchy control, or more declarative information than
contemporary compilers could reliably exploit. Each section asks the same
three questions:

1. **What did it try?**
2. **Why did it lose (technically and/or commercially)?**
3. **What does the AI-code-gen lens (D002) change about that verdict?**

Notes on stance: This is a synthesis of well-known architectural lore, not
fresh archival research. Where I'm uncertain about a date, an attribution,
or whether a specific feature was "the reason" something failed, I say so.
The post-mortems below are simplifications — real commercial failures
involve organizations and timing as much as architecture.

Order is roughly chronological so dependencies between ideas read forward.

---

## 1. Tera MTA / Cray MTA-2 / XMT (early 1990s onward)

**What.** Burton Smith's multithreaded architecture: instead of caching to
hide memory latency, the processor maintained ~128 hardware thread contexts
and switched on every cycle. Each thread saw uniform (long) memory latency,
but aggregate throughput stayed high because some thread always had work.
No data caches. Full/empty bits on every memory word for fine-grained
synchronization.

**Refs.** Smith, *Architecture and Applications of the HEP Multiprocessor
Computer System* (1981) → the lineage. Tera MTA papers from the mid-1990s.
Cray XMT (the commercial descendant) shipped to a small number of customers
into the 2000s.

**Why it lost.** Programs needed *enormous* exposed thread parallelism to
saturate the machine — typically far more than scientific codes naturally
expressed. Single-thread performance was poor. Compilers couldn't manufacture
the thread count. Cost-per-FLOP couldn't compete with cache-based
microprocessors riding Moore's Law on commodity volumes. The market for
"irregular graph workloads" (its strength) was smaller than the market for
"dense numerical kernels" (where caches win).

**AI-lens delta.** Modest. The constraint that bit Tera was *available
parallelism in the workload*, not *compiler ability to extract it*. AI
doesn't change the underlying parallelism a problem actually has. But:
Tera's "memory latency is uniform and long, hide it by switching" stance is
a useful counter-example to "memory latency is variable and short, hide it
by guessing." The architectural thesis (latency is a thread-scheduling
problem, not a cache problem) is worth carrying as a design alternative when
we get to the memory hierarchy.

---

## 2. Intel/HP Itanium / IA-64 / EPIC (1994 announced, shipped 2001)

**What.** *Explicitly Parallel Instruction Computing.* 128-bit instruction
bundles (three 41-bit slots + a template), with the compiler scheduling
which slots can issue in parallel. Rich predication: most instructions can
be guarded by a 1-bit predicate register, removing branches from inner
loops. Speculative loads (advance loads, check loads) for moving loads
above ambiguous stores. Software-managed register stack.

**Refs.** Sharangpani & Arora, *Itanium Processor Microarchitecture* (IEEE
Micro, 2000). Intel's IA-64 architecture manuals. Schlansker & Rau, *EPIC:
Explicitly Parallel Instruction Computing* (IEEE Computer, 2000). For the
post-mortem viewpoint, Hennessy & Patterson's appendix in later editions
treats it as a cautionary tale.

**Why it lost.** Compilers couldn't reliably fill the bundles or use
predication and speculation aggressively enough to hit the performance
targets the architecture's transistor budget assumed. x86 ate Itanium's
lunch on integer code by spending the same transistors on dynamic OoO
execution that didn't depend on the compiler being heroic. AMD64 then
removed the "you have to switch ISA to get 64-bit" forcing function. By
the time HP and Intel admitted defeat, a generation of compiler PhDs had
been spent and the niche had collapsed.

**AI-lens delta.** Large. Itanium's death was overwhelmingly a
*compiler-can't* story — the ISA assumed a code generator that could
schedule bundles, manage predicates, and place advance loads with
profile-grade global awareness. AI code generators that reason at
whole-program scope and can iterate against measured cost are exactly the
generator Itanium needed and didn't have. Worth a careful re-read in that
light. The specific mechanisms (predication, advance loads with check
points, software register stack, explicit bundle templates) are each
candidate building blocks for an AI-targeted ISA.

Caveat: even with a perfect compiler, EPIC made some bets that aged poorly
independent of code generation — large register file with rotating windows,
fixed bundle width, in-order issue. Don't conflate "predication is good
again" with "EPIC was right." Pull the parts; leave the whole.

---

## 3. Sony/Toshiba/IBM Cell Broadband Engine (announced 2005, PS3 2006)

**What.** Heterogeneous: one PowerPC PPE plus eight Synergistic Processing
Elements (SPEs). Each SPE had a 256 KB *local store* — directly addressed,
not a cache — and a DMA engine. Loads and stores from the SPE addressed
only its own local store; main memory came in via explicit DMA. Cache
coherence was a non-problem because there was no cache.

**Refs.** Pham et al., *The design and implementation of a first-generation
CELL processor* (ISSCC 2005). Kahle et al., *Introduction to the Cell
multiprocessor* (IBM J. R&D, 2005). Postmortem: Williams et al., *The
Potential of the Cell Processor for Scientific Computing* (CF 2006) — and
the long tail of "we got 80% of peak but it took six months" papers.

**Why it lost.** Programmability. The PS3 sold tens of millions of units,
so the hardware was not an economic failure, but the *programming model*
asked developers to manually orchestrate DMA, double-buffer working sets,
and pipeline computation against transfers — for every kernel. Compilers
never automated it well. Game engines and HPC codes that did the manual
work hit impressive numbers; everyone else got a fraction of peak. Cell
disappeared after PS3; the descendants (PowerXCell 8i in Roadrunner, the
first petaflop machine) were niche.

**AI-lens delta.** Very large. Cell's failure was almost purely "compilers
and average programmers can't manage explicit local stores + DMA at scale."
GPU shared-memory programming proves the model is viable when the code
generator (or human) can think about it; AI code generators arguably can do
this *generally*, not just for embarrassingly parallel kernels. The
software-managed scratchpad tier in our task list (#10) is essentially "what
if Cell, but the AI handles the bookkeeping." Worth treating Cell's
post-mortems as the most important reading in this whole pull.

---

## 4. TRIPS / EDGE (UT Austin, mid-2000s)

**What.** *Explicit Data Graph Execution.* Programs are compiled into
fixed-size *blocks* of up to 128 instructions. Within a block, instructions
name their *consumer* instructions directly (dataflow edges in the encoding)
rather than reading and writing a shared register file. Hardware fetches a
whole block, fires instructions as their inputs arrive, and commits the
block atomically. Across blocks, register and memory state is live; within
a block, it's pure dataflow.

The TRIPS chip (2007) was a 16-tile prototype that demonstrated the model
on real silicon at UT Austin under Doug Burger and Steve Keckler.

**Refs.** Burger et al., *Scaling to the End of Silicon with EDGE
Architectures* (IEEE Computer, 2004). Sankaralingam et al., *Exploiting ILP,
TLP, and DLP with the Polymorphous TRIPS Architecture* (ISCA 2003). Smith
et al., *Compiling for EDGE Architectures* (CGO 2006). The TRIPS chip paper
in IEEE Micro, 2007.

**Why it lost.** Two compounding issues. First, compiler-side: forming
maximal valid blocks under dataflow encoding constraints (limited consumer
fan-out, limited block size, no cycles within a block) was a hard scheduling
problem that the TRIPS compiler attacked but did not fully solve.
Second, market-side: the project was academic; it never had a path to
volume that would pressure the compiler problem to be solved. By the time
the chip ran, OoO execution on commodity cores had eaten most of the
"hardware complexity" critique that motivated EDGE in the first place.

**AI-lens delta.** Large, and the lens is unusually clean here because
EDGE's compiler problem is almost purely a *block-formation and scheduling*
problem. AI code generators that reason globally and can iterate against
profiles are well-matched to it. The architectural payoff (kill the rename
+ reorder logic that dominates modern OoO area) remains real. Of all the
buried ISAs, TRIPS may be the one whose "if only the compiler had been
better" critique most cleanly inverts under the AI lens.

Caveat: I should re-read the TRIPS papers before being confident the
block-formation constraints are AI-tractable. They may be intrinsically
hard in ways that AI doesn't help with (e.g., NP-hard scheduling under
encoding bounds) — in which case the question is whether AI can find
"good enough" solutions consistently, not optimal ones.

---

## 5. Mill Computing (Ivan Godard, design ongoing since ~2003, no shipping silicon)

**What.** A statically scheduled wide-issue architecture with several
unusual primitives:

- **The belt** instead of a register file: instruction results are pushed
  onto a fixed-length conveyor belt; older results fall off. Operands name
  belt positions, not registers. Eliminates register renaming entirely.
- **Exposed pipeline:** producer instructions name how many cycles their
  results take to land on the belt. Consumers schedule against that latency
  in the bundle.
- **Phasing:** within a single wide instruction, sub-operations issue in a
  defined order (reader, op, writer phases) so a wide instruction can
  encode loop-body-and-branch atomically.
- **Specification by family:** Mill is parameterized — different "family
  members" trade slot count, belt length, etc.

**Refs.** Mill Computing's lecture series on YouTube (Godard, multiple
talks 2013 onward) is the primary public material. Limited peer-reviewed
publications. Patents in the 2010s. No silicon has shipped as of my
training cutoff (early 2026). Treat all claims with appropriate skepticism
given the lack of independent measurement.

**Why it has not shipped.** Funding and time. Designing a from-scratch
ISA family with a from-scratch compiler is a decade-plus effort even
without commercial pressure. There is no evidence the technical ideas are
wrong; there is also no independent measurement that they're right.

**AI-lens delta.** Mixed. The belt and exposed pipeline assume a code
generator with cycle-accurate awareness of operation latencies — very
much a "compiler must be heroic" architecture, of the kind AI generators
should be good at. But the static scheduling assumes the underlying
microarchitecture is also static (no cache misses, no variable-latency
operations, or graceful handling thereof). That assumption is hard to
hold in any general-purpose CPU that touches DRAM.

Worth pulling: the *idea* that operands name producers (belt position) is
TRIPS-adjacent and cleaner than register renaming. Probably not worth
pulling: the family-of-implementations approach, until we have one
implementation working.

---

## 6. CHERI (Cambridge / SRI, 2010 onward, ongoing)

**What.** Capability hardware extension to existing ISAs (originally MIPS,
now ARM Morello, RISC-V CHERI-RISC-V). A *capability* is a hardware
pointer that carries bounds, permissions, and a validity bit, enforced by
the CPU on every dereference. Capabilities are unforgeable (you can only
narrow, not widen) and tagged in memory by extra metadata bits the CPU
maintains. Pointer arithmetic that exceeds bounds traps; type-confusion
attacks that forge pointers fail at hardware boundaries.

**Refs.** Watson et al., *CHERI: A Hybrid Capability-System Architecture for
Scalable Software Compartmentalization* (S&P 2015). The Morello program
(ARM + UK government, 2019 onward) shipped a real ARMv8.2 + CHERI prototype
SoC. CheriBSD is a working OS port.

**Why its commercial uptake has been slow.** Pointer-format change
(64-bit → 128-bit pointers) is a binary-ABI break across the entire
software stack. Memory bandwidth and cache cost rise. Commercial ARM has
not adopted CHERI in mainline. There is real momentum (Morello, recent
Microsoft "Azure CHERIoT" work targeting embedded) but no flagship CPU
has CHERI on by default.

**AI-lens delta.** Independent of code-generator capability — CHERI's
costs (pointer width, memory tag bits) are hardware costs, not compiler
costs. But: CHERI's *value* compounds when code generation is faster
than human review can keep up with. Hardware-enforced memory safety
becomes the audit substrate that lets generated code be trusted at
volume. Strong fit for an AI-targeted ISA on those grounds, even though
the AI doesn't change the cost ledger.

---

## 7. RISC-V Vector Extension (V) and Cache-Management Extensions
(Zicbom / Zicboz / Zicbop) — ratified 2021–2024

**What.**
- **V extension:** vector-length-agnostic SIMD, much in the spirit of ARM
  SVE. Software calls `vsetvl` to request a logical length; hardware tells
  it the actual number of elements per iteration. Same binary runs on
  implementations with different physical vector widths.
- **Zicbom / Zicboz / Zicbop:** standard cache-block management
  instructions — invalidate, clean, zero, and prefetch (read/write/instruction)
  by virtual address. Things that have been ad-hoc in other ISAs for
  decades, finally standardized.

**Refs.** RISC-V V Specification (v1.0 ratified 2021). RISC-V Zicbom/Zicboz/Zicbop
specifications (ratified 2021–2022). SiFive, Andes, and T-Head have shipping
implementations of V.

**Why these are interesting (rather than failed).** They aren't failures;
they're recent successes that show the industry inching toward
software-managed memory and vector-length agnosticism. Worth studying as
*bounds on what current commercial ISAs are willing to expose*.

**AI-lens delta.** RVV is roughly the right shape for the SIMD slot in
our design (#7). Zicbom/Zicboz/Zicbop are baseline cache-management
primitives that an AI-targeted memory hierarchy probably wants to
*exceed*, not match — they're prefetch-with-no-deadline, invalidate without
residency control, etc. Useful as a floor.

---

## 8. Apple AMX and ARM SME (2019 onward)

**What.**
- **Apple AMX** (undocumented, reverse-engineered ~2020): Apple Silicon
  matrix coprocessor with explicit tile registers (X, Y, Z) and
  load/store/multiply/accumulate instructions that operate on those tiles.
  Data movement between memory and tiles is explicit and high-bandwidth.
- **ARM SME** (Scalable Matrix Extension, announced 2021, shipping in
  2024+ silicon): the standardized version of the same idea, now part of
  ARMv9. SVE2 + matrix tiles + a "streaming SVE" mode for matrix-friendly
  data flow.

**Refs.** Reverse-engineering work on AMX by Dougall Johnson and others.
ARM SME architecture reference manual (2021 onward). The connection
between SME and AMX is widely assumed; I'm not certain how much shared
design lineage exists vs. parallel evolution.

**Why these are interesting.** Both make data movement between memory
and large register files (tiles) a first-class explicit operation, not a
side effect of cache behavior. Both were driven by ML inference workloads
where the cost of moving data dominates the cost of the math.

**AI-lens delta.** Confirmation rather than redirection — these are
modern commercial ISAs adopting "explicit data movement is a primitive"
exactly because the cost of *not* exposing it became unbearable for the
workloads that mattered. Generalize the lesson beyond matrix tiles to
arbitrary working-set movement.

---

## Cross-cutting Synthesis

Reading the eight together, several patterns emerge that should drive the
ISA design tasks (#3–#15):

**1. The same failure mode keeps repeating.** Itanium, Cell, TRIPS, Mill
all bet that a future code generator could exploit information the ISA
exposed. None of them got that generator in time. The failure is
*always* on the software side, not in the hardware physics. This is the
empirical case for D002 — if the AI-as-code-generator assumption holds,
the buried ideas become viable in a way they weren't before.

**2. Explicit data movement is winning at the margins.** AMX, SME, RVV
unit-stride loads, Cell's DMA, GPU shared memory — wherever workloads
actually demand bandwidth, the answer is to expose data movement as a
first-class operation, not to lean on caches and prefetchers. The trend
predates AI-code-gen and continues independent of it. AI accelerates the
trajectory; it didn't start it.

**3. CHERI is orthogonal but compounding.** Memory-safety capabilities
don't depend on the code-gen story, but their value rises sharply when
code is generated faster than humans can audit. They belong in the design
on safety grounds independent of the compiler-capability lens.

**4. Block-atomic dataflow (TRIPS) is the highest-leverage / highest-risk
idea.** It would, if it works, eliminate the largest single area cost in
modern OoO cores (rename + reorder). It is also the idea most dependent
on the code generator being capable. TRIPS' compiler partially solved
block formation; AI generators that reason globally and can iterate
against profiles plausibly do better. This is where to push hardest if
we want a result that's qualitatively different from "RISC-V plus some
extensions."

**5. Don't conflate "the architecture lost" with "the ideas were wrong."**
Itanium failed for many reasons; predication wasn't the cause. Cell
failed for one big reason; DMA + local store wasn't wrong, the
programming model was unsupported. Pull the *mechanisms*, leave the
*configurations*. The "principles transfer; processes do not" discipline
applies — extract the principle, re-derive the implementation in this
project's context.

**6. Tera MTA stands apart.** It's the one architecture in the set
where AI doesn't materially change the verdict. Latency-hiding by
massive multithreading needs *workload* parallelism, which the code
generator cannot manufacture. Worth holding as the counter-example: not
every "compilers couldn't" failure inverts under AI.

---

## Reading Priorities

If we don't read everything, read in this order:

1. **TRIPS papers** — the architecture whose failure most cleanly inverts
   under the AI-code-gen lens.
2. **Cell BE post-mortems** — the architecture whose failure mode (manual
   DMA at scale) is most relevant to the memory-hierarchy half of our
   design.
3. **EPIC retrospectives** — the canonical "compiler couldn't" case, well
   studied, with multiple post-mortems available.
4. **CHERI / Morello** — for the safety substrate, treat as a baseline to
   adopt rather than a research question to reopen.
5. **RVV + Zicbom/Zicboz/Zicbop** — the modern floor; know what's already
   standardized so we don't re-invent.

Mill, AMX/SME, and Tera are useful background but lower priority for the
next design pass.
