"""Orakel-Test online-allokation-demo / online_allokation: unabhängige Rechenwege gegen den Kern.

Orakel 1: das ganzzahlige Optimum exakt (CP-SAT) gegen die LP-Relaxation des Kerns (LP ≥ Optimum; auf kleinen Instanzen oft gleich).
Orakel 2: das duale Programm als zweites, getrennt formuliertes LP (scipy.linprog): gleicher Wert wie das primale (starke Dualität); die Preise des Kerns sind dual zulässig.
Orakel 3: FCFS und die exponentielle Preisfunktion gegen zweite, schleifenweise Fassungen mit Python-Listen."""

import math

import numpy as np
import pytest
from scipy.optimize import linprog

import ola_algorithm as A
import ola_constants as C
from ola_scenario import make_instance, make_order

CP = pytest.importorskip("ortools.sat.python.cp_model")


def integer_opt(A_, r, b):
    d, n = A_.shape
    m = CP.CpModel()
    x = [m.NewBoolVar(f"x{j}") for j in range(n)]
    for i in range(d):
        m.Add(sum(int(A_[i, j]) * x[j] for j in range(n)) <= int(b[i]))
    m.Maximize(sum(int(round(r[j] * 1000)) * x[j] for j in range(n)))
    s = CP.CpSolver()
    s.parameters.num_workers = 1
    assert s.Solve(m) == CP.OPTIMAL
    return s.ObjectiveValue() / 1000


def test_lp_is_an_upper_bound_of_the_integer_optimum_on_small_instances():
    for seed in range(20):
        A_, r, b, _ = make_instance(3, 14, 0.5, seed)
        lp, _ = A.lp_opt(A_, r, b)
        opt = integer_opt(A_, r, b)
        assert lp >= opt - 0.01 and opt >= 0.95 * lp, seed          # opt ist auf Tausendstel gerundet (CP-SAT rechnet ganzzahlig)


def dual_lp_value(A_, r, b):
    """min b·p + Σ s  unter  Aᵀp + s ≥ r,  p, s ≥ 0, getrennt vom Primalen formuliert."""
    d, n = A_.shape
    cost = np.concatenate([b, np.ones(n)])
    a_ub = -np.hstack([A_.T, np.eye(n)])
    res = linprog(cost, A_ub=a_ub, b_ub=-r, bounds=[(0, None)] * (d + n), method="highs")
    assert res.status == 0
    return float(res.fun)


def test_strong_duality_and_dual_feasibility_of_the_kernel_prices():
    for seed in range(15):
        A_, r, b, _ = make_instance(4, 300, 0.3, seed)
        lp, duals = A.lp_opt(A_, r, b)
        assert dual_lp_value(A_, r, b) == pytest.approx(lp, rel=1e-6)
        assert duals.min() >= 0 and A.dual_value(A_, r, b, duals) == pytest.approx(lp, rel=1e-6)
        # schwache Dualität für beliebige Preise
        for p in (np.zeros(4), np.full(4, 2.0), duals * 1.2):
            assert A.dual_value(A_, r, b, p) >= lp - 1e-6


def fcfs_loop(A_, r, b, order):
    used = [0.0] * A_.shape[0]
    value = 0.0
    for j in order:
        legs = [i for i in range(A_.shape[0]) if A_[i, j] > 0]
        if all(used[i] + 1 <= b[i] for i in legs):
            for i in legs:
                used[i] += 1
            value += r[j]
    return value


def exp_loop(A_, r, b, order):
    used = [0.0] * A_.shape[0]
    value = 0.0
    for j in order:
        legs = [i for i in range(A_.shape[0]) if A_[i, j] > 0]
        price = sum((C.LO / math.e) * (C.HI * math.e / C.LO) ** (used[i] / b[i]) for i in legs)
        if all(used[i] + 1 <= b[i] for i in legs) and r[j] >= price:
            for i in legs:
                used[i] += 1
            value += r[j]
    return value


def test_fcfs_and_exponential_equal_their_second_versions():
    for seed in range(10):
        A_, r, b, u = make_instance(4, 500, 0.3, seed)
        for ordnung in C.ORDNUNGEN:
            order = make_order(u, ordnung, seed)
            assert A.simulate("FCFS", A_, r, b, order).value == pytest.approx(fcfs_loop(A_, r, b, order))
            assert A.simulate("exponentiell", A_, r, b, order).value == pytest.approx(exp_loop(A_, r, b, order))
