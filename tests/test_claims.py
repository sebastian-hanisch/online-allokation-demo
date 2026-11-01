"""Jede Zahl aus der README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über dieselben Auswertungsfunktionen wie die App.

Feste Seeds und Längen wie in den Presets und Experimenten der App; Rundung wie in der README (drei Nachkommastellen)."""

import math

import pytest

import ola_algorithm as A
import ola_constants as C
import ola_evaluation as ev

TOL = 1.5e-3


def _preset(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def _fractions(a):
    return [a.fractions[r] for r in C.REGELN]


# --- Presets -----------------------------------------------------------------------------------------------------------------------------


def test_network_preset():
    a = _preset("Netz mit vier Strecken")
    assert a.lp_value == pytest.approx(7156, abs=1) and a.accepted["Preislernen"] == 562 and a.accepted["FCFS"] == 608
    assert _fractions(a) == pytest.approx([0.624, 0.997, 0.926, 0.939, 0.743], abs=TOL)
    assert a.utilization == pytest.approx([0.87, 1.0, 0.87, 1.0], abs=0.01)


def test_adversary_preset_lowest_values_first():
    a = _preset("Gegner: niedrige Werte zuerst")
    assert _fractions(a) == pytest.approx([0.152, 0.979, 0.202, 0.362, 0.316], abs=TOL)


def test_descending_preset_learning_fails_completely():
    a = _preset("Sortiert absteigend: Lernen scheitert")
    assert a.fractions["Preislernen"] == 0.0 and a.accepted["Preislernen"] == 0 and max(a.utilization) == 0.0
    assert _fractions(a) == pytest.approx([1.0, 0.997, 0.0, 0.749, 0.929], abs=TOL)


def test_one_leg_preset():
    a = _preset("Eine Strecke (Online-Rucksack)")
    assert _fractions(a) == pytest.approx([0.148, 1.0, 0.193, 0.475, 0.322], abs=TOL) and a.lp_value == pytest.approx(1902, abs=1)


def test_many_legs_and_plenty_of_room_presets():
    a = _preset("Viele Strecken")
    assert _fractions(a) == pytest.approx([0.646, 0.997, 0.859, 0.888, 0.755], abs=TOL)
    a = _preset("Reichlich Platz")
    assert _fractions(a) == pytest.approx([1.0, 1.0, 0.94, 0.991, 0.925], abs=TOL) and a.accepted["FCFS"] == 2000 and a.accepted["Preislernen"] == 1823


# --- Experiment 1 -------------------------------------------------------------------------------------------------------------------------


ORDER = {
    (0.1, "zufällig"): [0.590, 0.981, 0.845, 0.770, 0.686],
    (0.1, "aufsteigend (niedrige zuerst)"): [0.153, 0.980, 0.199, 0.313, 0.313],
    (0.1, "absteigend"): [1.000, 0.982, 0.000, 0.995, 0.992],
    (0.3, "zufällig"): [0.640, 0.994, 0.871, 0.918, 0.757],
    (0.3, "aufsteigend (niedrige zuerst)"): [0.272, 0.994, 0.324, 0.500, 0.381],
    (0.3, "absteigend"): [1.000, 0.994, 0.000, 0.793, 0.942],
    (0.6, "zufällig"): [0.755, 0.999, 0.871, 0.960, 0.869],
    (0.6, "aufsteigend (niedrige zuerst)"): [0.506, 0.999, 0.567, 0.670, 0.547],
    (0.6, "absteigend"): [1.000, 0.999, 0.000, 0.839, 0.879],
}


def test_order_table():
    rows = {(r["Knappheit"], r["Reihenfolge"]): r for r in ev.order_rows()}
    assert set(rows) == set(ORDER)
    for key, expected in ORDER.items():
        assert [rows[key][r] for r in C.REGELN] == pytest.approx(expected, abs=TOL), key


def test_order_findings():
    rows = ev.order_rows()
    assert min(r["Orakel-Preise"] for r in rows) >= 0.979 and max(r["Orakel-Preise"] for r in rows) <= 1.0     # richtige Preise: in jeder Reihenfolge 0,979 bis 0,999
    assert all(r["Preislernen"] == 0.0 for r in rows if r["Reihenfolge"] == "absteigend")
    assert all(0.999 <= r["FCFS"] <= 1.0 for r in rows if r["Reihenfolge"] == "absteigend")      # FCFS in absteigender Reihenfolge: 0,9995 bis 0,9998 des Optimums
    asc01 = next(r for r in rows if r["Knappheit"] == 0.1 and r["Reihenfolge"].startswith("aufsteigend"))
    assert asc01["exponentiell"] == max(asc01[r] for r in ("FCFS", "Preislernen", "exponentiell")) and asc01["FCFS"] < 0.16
    rnd = [r for r in rows if r["Reihenfolge"] == "zufällig"]
    assert all(r["Preislernen"] > r["exponentiell"] and r["Preislernen"] > r["FCFS"] for r in rnd)


# --- Experimente 2 bis 5 -----------------------------------------------------------------------------------------------------------------


def test_growth_table():
    rows = ev.growth_rows()
    expected = {100: [0.659, 0.949, 0.746, 0.788, 0.746], 400: [0.615, 0.986, 0.862, 0.858, 0.735], 1000: [0.640, 0.994, 0.871, 0.918, 0.757], 4000: [0.636, 0.999, 0.921, 0.955, 0.756]}
    for r in rows:
        assert [r[x] for x in C.REGELN] == pytest.approx(expected[r["n"]], abs=TOL), r["n"]
    assert rows[-1]["Preislernen"] > rows[0]["Preislernen"] + 0.15 and abs(rows[-1]["exponentiell"] - rows[0]["exponentiell"]) < 0.02


def test_resources_table():
    rows = ev.resource_rows()
    expected = {1: [0.640, 1.000, 0.895, 0.967, 0.758], 2: [0.619, 0.997, 0.927, 0.947, 0.735], 4: [0.640, 0.994, 0.871, 0.918, 0.757], 8: [0.639, 0.991, 0.856, 0.847, 0.748]}
    for r in rows:
        assert [r[x] for x in C.REGELN] == pytest.approx(expected[r["d"]], abs=TOL), r["d"]
    assert rows[-1]["Dual-Gradient"] < rows[0]["Dual-Gradient"] - 0.1


def test_step_table():
    rows = ev.step_rows()
    assert [r["Faktor"] for r in rows] == [0.1, 0.3, 1.0, 3.0, 10.0]
    assert [r["zufällig"] for r in rows] == pytest.approx([0.659, 0.770, 0.918, 0.954, 0.920], abs=TOL)
    assert [r["aufsteigend"] for r in rows] == pytest.approx([0.272, 0.341, 0.500, 0.583, 0.627], abs=TOL)
    assert max(rows, key=lambda r: r["zufällig"])["Faktor"] == 3.0 and max(rows, key=lambda r: r["aufsteigend"])["Faktor"] == 10.0


def test_guarantee_table_for_one_resource():
    rows = ev.guarantee_rows()
    assert A.exp_guarantee() == pytest.approx(1 / (math.log(10) + 1)) and A.exp_guarantee() == pytest.approx(0.3028, abs=5e-5)
    expected = {0.1: [0.153, 1.0, 0.201, 0.449, 0.320], 0.3: [0.277, 1.0, 0.330, 0.584, 0.385], 0.6: [0.513, 1.0, 0.575, 0.722, 0.553]}
    for r in rows:
        assert [r[x] for x in C.REGELN] == pytest.approx(expected[r["Knappheit"]], abs=TOL), r["Knappheit"]
    assert all(r["exponentiell"] >= r["Garantie"] for r in rows) and rows[0]["exponentiell"] < rows[0]["Garantie"] + 0.02     # bei Knappheit 0,1 nur 0,017 darüber
