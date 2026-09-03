"""Cardinality-oracle membership inference baselines.

Engineering reproduction of the attack family introduced by
Guo et al., "Leakage Abuse Attacks on Multi-Party PSI-CA" style
strategic querying (USENIX Security 2022): an oracle reveals only the
intersection *cardinality* |S & B| for an attacker-chosen query set S,
and the attacker infers set membership of a candidate pool.

Baseline attacks implemented here (prior-art reproduction):

- single_element: query each candidate alone; count 0/1 decides it.
- binary_tree   : recursively split the pool; skip pure subtrees
                  (count==0 or count==size), recurse into mixed ones.

This file is deliberately mechanism-free: exact-count oracle only, no
output filtering. It exists to (a) validate the oracle harness and
(b) provide the regression baseline that later studies compare
against.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import dataclass, field


class CardinalityOracle:
    """Answers |S & B| for attacker-chosen S. Counts every call."""

    def __init__(self, secret: frozenset[int]):
        self.secret = secret
        self.queries = 0

    def count(self, query: set[int]) -> int:
        self.queries += 1
        return len(query & self.secret)


@dataclass
class AttackReport:
    attack: str
    queries: int
    tp: int
    fp: int
    tn: int
    fn: int
    seconds: float
    extra: dict = field(default_factory=dict)


def metrics(rep: AttackReport, pool_positives: int, pool_size: int) -> dict:
    recall_pos = rep.tp / pool_positives if pool_positives else float("nan")
    precision = rep.tp / (rep.tp + rep.fp) if (rep.tp + rep.fp) else float("nan")
    resolved = (rep.tp + rep.tn) / pool_size if pool_size else float("nan")
    yield_per_query = rep.tp / rep.queries if rep.queries else float("nan")
    return {
        "attack": rep.attack,
        "queries": rep.queries,
        "tp": rep.tp,
        "fp": rep.fp,
        "tn": rep.tn,
        "fn": rep.fn,
        "recall_pos": recall_pos,
        "precision": precision,
        "resolved_coverage": resolved,
        "positive_yield_per_query": yield_per_query,
        "seconds": rep.seconds,
        "extra": rep.extra,
    }


def attack_single_element(oracle: CardinalityOracle, candidates: list[int]) -> dict[int, bool]:
    """Query each candidate alone. Exact: decided membership for every queried element."""
    verdict: dict[int, bool] = {}
    for c in candidates:
        verdict[c] = oracle.count({c}) == 1
    return verdict


def attack_binary_tree(oracle: CardinalityOracle, candidates: list[int]) -> dict[int, bool]:
    """Split the pool; stop early on pure nodes (count 0 or count == node size)."""
    verdict: dict[int, bool] = {}
    stack: list[list[int]] = [candidates]
    while stack:
        node = stack.pop()
        cnt = oracle.count(set(node))
        if cnt == 0:
            for c in node:
                verdict[c] = False
        elif cnt == len(node):
            for c in node:
                verdict[c] = True
        elif len(node) == 1:
            # cnt must be 0 or 1 here; 1 == len(node) handled above.
            verdict[node[0]] = cnt == 1
        else:
            mid = len(node) // 2
            stack.append(node[:mid])
            stack.append(node[mid:])
    return verdict


def score(verdict: dict[int, bool], secret: frozenset[int]) -> tuple[int, int, int, int]:
    tp = fp = tn = fn = 0
    for c, guess in verdict.items():
        actual = c in secret
        if guess and actual:
            tp += 1
        elif guess and not actual:
            fp += 1
        elif not guess and actual:
            fn += 1
        else:
            tn += 1
    return tp, fp, tn, fn


def run_pool(pool_size: int, pool_positives: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    positives = rng.sample(range(pool_size * 10), pool_positives)
    secret = frozenset(positives)
    negatives = rng.sample([x for x in range(pool_size * 100) if x not in secret], pool_size - pool_positives)
    candidates = positives + negatives
    rng.shuffle(candidates)

    out = []
    for name, attack in (("single_element", attack_single_element), ("binary_tree", attack_binary_tree)):
        oracle = CardinalityOracle(secret)
        t0 = time.perf_counter()
        verdict = attack(oracle, candidates)
        elapsed = time.perf_counter() - t0
        tp, fp, tn, fn = score(verdict, secret)
        rep = AttackReport(
            attack=name,
            queries=oracle.queries,
            tp=tp,
            fp=fp,
            tn=tn,
            fn=fn,
            seconds=elapsed,
            extra={"pool_size": pool_size, "pool_positives": pool_positives, "seed": seed},
        )
        out.append(metrics(rep, pool_positives, pool_size))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool-size", type=int, default=10_000)
    ap.add_argument("--pool-positives", type=int, default=1_000)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--out", type=str, default="")
    args = ap.parse_args()

    rows: list[dict] = []
    for seed in range(args.seeds):
        rows.extend(run_pool(args.pool_size, args.pool_positives, seed))

    # Regression assertions (engineering gate, not a scientific result).
    failures = []
    for r in rows:
        if r["precision"] != 1.0:
            failures.append(f"{r['attack']} seed={r['extra']['seed']}: precision {r['precision']} != 1.0")
        if r["recall_pos"] != 1.0:
            failures.append(f"{r['attack']} seed={r['extra']['seed']}: recall {r['recall_pos']} != 1.0")
        if r["queries"] > args.pool_size + 1:
            failures.append(
                f"{r['attack']} seed={r['extra']['seed']}: {r['queries']} queries > pool+1"
            )
    print(json.dumps(rows, indent=2))
    if failures:
        raise SystemExit("REGRESSION FAILED:\n" + "\n".join(failures))
    print(f"REGRESSION OK: {len(rows)} runs, all exact, queries <= pool+1")


if __name__ == "__main__":
    main()
