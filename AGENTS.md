# AGENTS.md — collaboration rules for coding agents in this repository

## Disclosure boundary (hard rule)

This is a **public** repository during the pre-submission phase:

- Never commit, force-add, or push `.paper-project/` state files,
  manuscript drafts, novelty/claims notes, review packets, or exported
  chat/research discussions. `scripts/repo-guard.sh` fails CI on any of
  these and on obvious token patterns.
- Commit messages, branch names, and issue titles are public too: keep
  them about engineering facts (build, test, refactor), not about the
  research contributions.
- If a task seems to require publishing sensitive material, stop and
  surface the decision to the user instead of working around the guard.

## Source-of-truth discipline

- The current project phase, checkpoint, admissible evidence, and next
  gate live in the local `.paper-project/` directory (managed by the
  `research-paper-pipeline` skill), **not** in this repository. Read
  the checkpoint before planning work; never let a chat message outrank
  it.
- CI success is engineering evidence only. It never substitutes for
  formal experimental evidence; formal runs must satisfy the frozen
  admission contract in the project state.

## Branch and commit discipline

- One task, one branch (`task/<short-name>`); keep unrelated edits off
  a branch while CI or a reviewer is witnessing its head commit.
- Never rewrite `main` history. Land changes via fast-forward merges or
  squash merges after CI passes on the exact merged commit.
- Tag frozen states (`freeze/<name>`) that results or reviews are bound
  to; do not move a tag once anything references it.

## Engineering expectations

- Match the existing code style; keep dependencies minimal and locked.
- Tests for scientific behavior and failure-closed boundaries are part
  of the feature, not an afterthought.
- Heavy compute does not belong on casual CI runs: keep public-runner
  jobs small (build + unit + small-scale protocol checks); large runs
  execute on the designated workstation and return artifacts with
  digests.
