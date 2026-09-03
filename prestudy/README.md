# prestudy

Small, self-contained engineering studies. Nothing here is a formal
experiment result; outputs are run records only.

- `baseline/` — cardinality-oracle membership inference baselines
  (reproduction of the attack family of Guo et al., USENIX Security
  2022) used as the regression floor for later comparisons.
  CI runs its unit tests on every push.
- `psi-backend/` — two-party PSI-cardinality smoke benchmark using
  OpenMined PSI (`openmined-psi`, exact `RAW` container,
  `reveal_intersection=False`). Not exercised in CI; requires
  `pip install openmined-psi` under Python 3.12.
