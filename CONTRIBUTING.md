# Contributing

Outside contributions are welcome. This file describes how to participate
productively at the current stage of the project (design-only, no running
code), what kinds of contributions are most useful right now, and the IP
and review hygiene we ask for.

## What's most useful at this stage

The project is in design exploration. The artifacts are markdown documents
(prior-art synthesis, decision log, design notes for ISA features and
memory hierarchy). Useful contributions:

- **Prior-art corrections.** If [`prior_art.md`](prior_art.md) mischaracterizes an
  architecture you know, file an issue with the citation. We'd rather
  correct than entrench errors.
- **Buried-architecture pointers.** Architectures we should read and
  haven't (Lisp Machines, Transputer, iWarp, REX/STAR-100, GE-645, others).
  Open an issue stating what makes the architecture relevant under the
  AI-code-gen lens (D002).
- **Design critique.** Open tasks include ISA-feature design (predication,
  block-atomic dataflow, capabilities, per-instruction effects) and
  memory-hierarchy design (scratchpad tiers, streaming bypass, residency
  control, topology-visible placement). PRs that add markdown design
  notes or counter-proposals are welcome.
- **Code-generator critique.** D003 holds that the AI compiler pipeline is
  a co-equal design artifact to the ISA. Contributions that flesh out
  pipeline stages, intermediate representations, or audit-substrate
  mechanics are welcome.

Implementation contributions (simulator, HDL, compiler backend) are
welcome in spirit but premature in practice — the design isn't settled
enough for code to be load-bearing. Watch the decision log; when a
prototype becomes the right next move, it'll be entered there.

## Local development setup

The project uses [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)
to enforce markdown style. The same check runs in CI on every push and PR.
For fast feedback locally, install the linter and the project's pre-commit
hook:

```sh
# 1. Install markdownlint-cli2 (one-time, system-wide)
sudo npm install -g markdownlint-cli2

# 2. Install the pre-commit hook (one-time, per clone)
ln -sf ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit
```

The hook lints staged `.md` files on every `git commit` and blocks the
commit if any error is reported. Configuration lives in `.markdownlint.json`
at the repo root; rules and rationale follow the
[markdownlint rule reference](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md).

To run the lint manually against the whole tree:

```sh
markdownlint-cli2 "**/*.md"
```

When code lands later (simulator, compiler backend), the local toolchain
will grow language-specific gates retrofitted at that point — not
copy-pasted from sibling projects. The current shape (one tool, one hook)
matches the current artifact (markdown only).

## Developer Certificate of Origin (DCO) sign-off

Every commit (including merge commits introducing outside work) must carry
a sign-off line:

```text
Signed-off-by: Your Name <your@email>
```

Use `git commit -s` to add it automatically. The DCO is a lightweight
attestation — the same one used by the Linux kernel and many other open
projects — that you have the right to submit the contribution under the
project's license. Full text: <https://developercertificate.org/>

By submitting a PR you license your contribution under the project's
Apache License 2.0.

We do not require a Contributor License Agreement (CLA) at this time.

## Decision-log discipline

[`DECISIONS.md`](DECISIONS.md) is the project's source of truth on design choices. The
conventions are documented in [`CLAUDE.md`](CLAUDE.md) and at the top of the decision
log itself, but the headlines are:

- **Sequential numbering, never renumbered** (D001, D002, ...).
- **Entry content is immutable** once written.
- **Supersession is bidirectional** — new entry back-points to the
  superseded one; superseded entry gets a prepended annotation noting
  the supersession.

If your PR makes a substantive design change — new ISA feature, change to
a load-bearing assumption, revised pipeline stage — propose a new
decision-log entry as part of the PR. The reviewer (currently Ed) merges
the design and the log entry together. Small editorial fixes (typos,
clarifications, prior-art corrections that don't change conclusions) do
not need a log entry.

## Review process

- File an issue first for substantive proposals; PRs that arrive without
  prior discussion may be asked to pause for a design conversation.
- Small fixes (typos, link rot, prior-art citation corrections) can go
  straight to PR.
- Ed Hodapp is the design BDFL: collaborators are welcome to argue,
  propose, and prototype, but the merge decision rests with him and the
  decision log is where the project's position is durably recorded.
- PR review is asynchronous; no SLA at this stage.

## Honest-claim hygiene

[`CLAUDE.md`](CLAUDE.md) describes the "lab notebook, not pitch deck" stance for
project documents. The same applies to PR text and issue descriptions:

- State observations as observations.
- Hedge empirical claims; state design rules as design rules.
- Cite papers and architectures with names and dates correct. "I'm not
  sure about this date" is better than confident wrong.

Mathematical and historical claims will be reviewed by people who know
the domain. Make their job easy.

## Code of conduct

Be civil. Critique ideas, not people. Disagreement on design is the
point of the project; rudeness is not. There is no formal code of conduct
document yet; if the project grows enough to need one, we'll adopt the
Contributor Covenant.
