import pytest

from baseline import CardinalityOracle, attack_binary_tree, attack_single_element, score


def _pool(secret, negatives):
    candidates = list(secret) + negatives
    return candidates


def test_single_element_is_exact():
    secret = frozenset({11, 22, 33})
    candidates = _pool(secret, [7, 8, 9, 10])
    oracle = CardinalityOracle(secret)
    verdict = attack_single_element(oracle, candidates)
    tp, fp, tn, fn = score(verdict, secret)
    assert (tp, fp, tn, fn) == (3, 0, 4, 0)
    assert oracle.queries == len(candidates)


def test_binary_tree_decides_pool_with_early_stop():
    secret = frozenset(range(0, 200, 2))  # 100 positives
    negatives = list(range(1000, 1400))   # 400 negatives, contiguous block
    candidates = _pool(secret, negatives)
    oracle = CardinalityOracle(secret)
    verdict = attack_binary_tree(oracle, candidates)
    tp, fp, tn, fn = score(verdict, secret)
    assert (tp, fp, tn, fn) == (100, 0, 400, 0)
    # Early termination on the pure negative block must keep queries below
    # the single-element budget for this pool shape.
    assert oracle.queries < len(candidates)


def test_oracle_counts_every_call():
    oracle = CardinalityOracle(frozenset({1, 2}))
    assert oracle.count({1, 2, 3}) == 2
    assert oracle.count(set()) == 0
    assert oracle.queries == 2
