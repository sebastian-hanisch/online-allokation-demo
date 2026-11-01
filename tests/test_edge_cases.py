"""Randfälle: Gestalt der Instanzen, Reihenfolgen, Extremwerte der Regler."""

import numpy as np
import pytest

import ola_algorithm as A
import ola_constants as C
import ola_evaluation as ev
from ola_scenario import make_instance, make_order


@pytest.mark.parametrize("d", [1, 2, 8])
@pytest.mark.parametrize("n", [100, 1000])
def test_instances_have_the_expected_shape_and_are_reproducible(d, n):
    A_, r, b, u = make_instance(d, n, 0.3, 5)
    A2, r2, b2, u2 = make_instance(d, n, 0.3, 5)
    assert A_.shape == (d, n) and r.shape == u.shape == (n,) and b.shape == (d,)
    assert np.array_equal(A_, A2) and np.array_equal(r, r2) and np.array_equal(b, b2)
    legs = A_.sum(axis=0)
    assert legs.min() >= 1 and legs.max() <= 2 and (d > 1 or legs.max() == 1)
    assert u.min() >= C.LO and u.max() <= C.HI and np.allclose(r, u * legs)
    assert b.min() >= 1 and np.all(b == np.floor(b))


def test_capacity_is_the_share_of_the_demand_and_at_least_one():
    A_, _, b, _ = make_instance(4, 1000, 0.3, 1)
    assert np.all(b == np.maximum(1.0, np.floor(0.3 * A_.sum(axis=1))))
    A_, _, b, _ = make_instance(8, 100, 0.1, 1)
    assert b.min() >= 1


def test_orders_are_permutations_and_sorted_by_value_per_unit():
    _, _, _, u = make_instance(4, 500, 0.3, 2)
    for ordnung in C.ORDNUNGEN:
        order = make_order(u, ordnung, 2)
        assert sorted(order) == list(range(500))
    asc = make_order(u, "aufsteigend (niedrige zuerst)", 2)
    desc = make_order(u, "absteigend", 2)
    assert all(u[a] <= u[b] for a, b in zip(asc, asc[1:])) and all(u[a] >= u[b] for a, b in zip(desc, desc[1:]))
    assert make_order(u, "zufällig", 2) == make_order(u, "zufällig", 2) and make_order(u, "zufällig", 2) != make_order(u, "zufällig", 3)


def test_when_everything_fits_fcfs_takes_everything_and_equals_the_lp():
    a = ev.analyse(ev.Settings("FCFS", 4, 400, 1.0, "zufällig", 3))
    assert a.accepted["FCFS"] == 400 and a.fractions["FCFS"] == pytest.approx(1.0) and a.fractions["Orakel-Preise"] == pytest.approx(1.0)


def test_extreme_settings_run_and_stay_feasible():
    for s in (ev.Settings("Preislernen", 8, 8000, 0.1, "absteigend", C.SEED_MAX), ev.Settings("Dual-Gradient", 1, 100, 1.0, "aufsteigend (niedrige zuerst)", 0),
              ev.Settings("exponentiell", 2, 100, 0.1, "zufällig", 1)):
        a = ev.analyse(s)
        assert all(0.0 <= f <= 1.0 + 1e-9 for f in a.fractions.values()), s
        assert len(a.trace) == C.TRACE_LEN and all(0.0 <= u <= 1.0 + 1e-9 for u in a.utilization)


def test_fraction_guard_and_curves():
    assert ev.fraction(5, 0) == 1.0 and ev.fraction(3, 4) == 0.75
    a = ev.analyse(ev.Settings("FCFS", 4, 400, 0.3, "zufällig", 1))
    for rule, (xs, ys) in a.curves.items():
        assert xs[-1] == pytest.approx(1.0) and ys[-1] == pytest.approx(a.fractions[rule]) and all(q >= p - 1e-12 for p, q in zip(ys, ys[1:]))
        assert len(xs) <= C.CURVE_POINTS


def test_trace_rows_show_prices_and_decisions():
    a = ev.analyse(ev.Settings("exponentiell", 1, 100, 0.3, "zufällig", 1))
    assert [r["Nr"] for r in a.trace] == list(range(1, C.TRACE_LEN + 1))
    assert all(r["Entscheidung"] in ("angenommen", "abgelehnt") and r["Strecken"] == "1" for r in a.trace)
    fcfs = ev.analyse(ev.Settings("FCFS", 1, 100, 0.3, "zufällig", 1)).trace
    assert all(r["Preis"] == "–" for r in fcfs)
    learn = ev.analyse(ev.Settings("Preislernen", 4, 400, 0.3, "zufällig", 1)).trace
    assert all(r["Preis"] == "∞" and r["Entscheidung"] == "abgelehnt" for r in learn)          # die Lernphase umfasst bei n = 400 die ersten 20 Buchungen


def test_lp_of_a_single_request():
    A_ = np.array([[1.0]])
    assert A.lp_opt(A_, np.array([4.0]), np.array([1.0]))[0] == pytest.approx(4.0)
