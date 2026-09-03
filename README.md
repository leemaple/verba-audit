# verba-audit

Research prototype and experiment infrastructure for a two-party
privacy-preserving auditing study. Work in progress; the paper is in
preparation and code will arrive in later milestones.

## Repository layout

- `scripts/` — repository maintenance and verification scripts
- `.github/workflows/` — CI: hygiene and disclosure guard on every push/PR

## Repository policy

This repository is the engineering and reproducibility surface only:

- Project state, claims, manuscripts, and research notes are managed
  outside this repository and must not be committed. CI enforces this
  via `scripts/repo-guard.sh`.
- Experiment code will land on isolated feature branches once the
  study design is frozen; CI must pass on the exact commit that a
  result is claimed against.
