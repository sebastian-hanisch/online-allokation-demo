"""Kern gegen Handrechnung auf der Mini-Instanz und auf kleinen Instanzen von Hand."""

import math

import numpy as np
import pytest

import ola_algorithm as A
import ola_constants as C


def test_mini_instance_by_hand(mini):
    A_, r, b, order = mini
    lp, duals = A.lp_opt(A_, r, b)
    assert lp == pytest.approx(5.0)
    fcfs = A.simulate("FCFS", A_, r, b, order)
    assert fcfs.value == 4 and fcfs.accepted.tolist() == [True, True, False]
    orakel = A.simulate("Orakel-Preise", A_, r, b, order, oracle_duals=np.array([1.5]))
    assert orakel.value == 5 and orakel.accepted.tolist() == [True, False, True]
    exp = A.simulate("exponentiell", A_, r, b, order)
    assert exp.value == 5 and exp.accepted.tolist() == [True, False, True]
    assert exp.prices[0] == pytest.approx(1 / math.e) and exp.prices[1] == pytest.approx((1 / math.e) * (10 * math.e) ** 0.5)
    grad = A.simulate("Dual-Gradient", A_, r, b, order)
    assert grad.value == 5 and grad.accepted.tolist() == [True, False, True] and grad.prices[1] == pytest.approx(10 / math.sqrt(3) * (1 - 2 / 3))
    learn = A.simulate("Preislernen", A_, r, b, order)
    assert learn.value == 0 and not learn.accepted.any() and all(p == float("inf") for p in learn.prices)


def test_dual_value_is_never_below_the_lp_value_and_equals_it_at_the_optimum(mini):
    A_, r, b, _ = mini
    lp, duals = A.lp_opt(A_, r, b)
    assert A.dual_value(A_, r, b, duals) == pytest.approx(lp)
    assert A.dual_value(A_, r, b, np.array([1.5])) == pytest.approx(5.0)          # 2 · 1,5 + 1,5 + 0,5 = 5
    for p in (0.0, 0.5, 1.0, 2.0, 3.0, 10.0):
        assert A.dual_value(A_, r, b, np.array([p])) >= lp - 1e-9


def test_two_leg_instance_by_hand():
    # zwei Strecken mit je einer Einheit; Buchung 0 nutzt beide (Wert 5), Buchungen 1 und 2 je eine (Werte 2 und 4): das Optimum nimmt 1 und 2 (Wert 6)
    A_ = np.array([[1.0, 1.0, 0.0], [1.0, 0.0, 1.0]])
    r = np.array([5.0, 2.0, 4.0])
    b = np.array([1.0, 1.0])
    lp, duals = A.lp_opt(A_, r, b)
    assert lp == pytest.approx(6.0)
    assert A.dual_value(A_, r, b, np.array([2.0, 4.0])) == pytest.approx(6.0)        # Preise (2, 4) sind optimal; (1, 4) auch: die Duale ist nicht eindeutig
    assert A.dual_value(A_, r, b, duals) == pytest.approx(6.0)
    assert A.simulate("FCFS", A_, r, b, [0, 1, 2]).value == 5.0                      # FCFS nimmt die Doppelbuchung und blockiert beide Strecken
    assert A.simulate("FCFS", A_, r, b, [1, 2, 0]).value == 6.0                      # in anderer Reihenfolge füllen die zwei einzelnen beide Strecken


def test_exponential_price_endpoints_and_guarantee():
    assert A.exp_price(0.0) == pytest.approx(C.LO / math.e) and A.exp_price(1.0) == pytest.approx(C.HI)
    assert all(A.exp_price(z) < A.exp_price(z + 0.1) for z in (0.0, 0.3, 0.8))
    assert A.exp_guarantee() == pytest.approx(1 / (math.log(10) + 1)) and A.exp_guarantee(1.0, 1.0) == 1.0


def test_infeasible_requests_are_never_accepted():
    A_ = np.array([[1.0, 1.0, 1.0, 1.0]])
    r = np.array([9.0, 9.0, 9.0, 9.0])
    b = np.array([2.0])
    for rule in C.REGELN:
        res = A.simulate(rule, A_, r, b, [0, 1, 2, 3], oracle_duals=np.array([0.0]))
        assert res.accepted.sum() <= 2 and A.is_feasible(A_, res.accepted, b)


def test_is_feasible_by_hand(mini):
    A_, r, b, _ = mini
    assert A.is_feasible(A_, np.array([True, True, False]), b) and not A.is_feasible(A_, np.array([True, True, True]), b)
    assert A.is_feasible(A_, np.array([False, False, False]), b)


def test_gradient_price_never_negative_and_learning_starts_after_the_observation_phase():
    rng = np.random.default_rng(1)
    d, n = 3, 400
    A_ = (rng.random((d, n)) < 0.4).astype(float)
    r = rng.uniform(1, 10, n) * np.maximum(A_.sum(axis=0), 1)
    b = np.maximum(1.0, np.floor(0.3 * A_.sum(axis=1)))
    order = list(rng.permutation(n))
    grad = A.simulate("Dual-Gradient", A_, r, b, order)
    assert min(grad.prices) >= 0.0
    learn = A.simulate("Preislernen", A_, r, b, order)
    k0 = max(5, int(n * C.LEARN_START))
    assert all(p == float("inf") for p in learn.prices[:k0]) and all(p < float("inf") for p in learn.prices[k0:])
    assert not learn.accepted[order[:k0]].any()                                      # solange es lernt, nimmt es nichts an
