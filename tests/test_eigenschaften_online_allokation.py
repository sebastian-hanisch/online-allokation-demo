"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für Online-Allokation gelten müssen, ohne das richtige Ergebnis zu kennen.

Jede Eigenschaft folgt aus der Definition: nie mehr angenommen als der Platz erlaubt, nie mehr Wert als das LP, Online-Verfahren sehen die Zukunft nicht
(die ersten j Entscheidungen hängen nicht von späteren Buchungen ab), das LP wächst mit der Kapazität und mit weiteren Buchungen."""

import numpy as np
import pytest

import ola_algorithm as A
import ola_constants as C
from ola_scenario import make_instance, make_order

ONLINE = ("FCFS", "Preislernen", "Dual-Gradient", "exponentiell")


def _cases():
    for seed in range(6):
        for d, kn in ((1, 0.2), (3, 0.4), (6, 0.1)):
            A_, r, b, u = make_instance(d, 300, kn, seed)
            for ordnung in C.ORDNUNGEN:
                yield A_, r, b, make_order(u, ordnung, seed)


def test_every_rule_stays_feasible_and_never_beats_the_lp():
    for A_, r, b, order in _cases():
        lp, duals = A.lp_opt(A_, r, b)
        for rule in C.REGELN:
            res = A.simulate(rule, A_, r, b, order, oracle_duals=duals)
            assert A.is_feasible(A_, res.accepted, b), rule
            assert res.value <= lp + 1e-6 and res.value == pytest.approx(float(r[res.accepted].sum()))
            assert np.allclose(res.used, A_[:, res.accepted].sum(axis=1))


def test_online_rules_do_not_see_the_future():
    # zwei Instanzen mit denselben ersten m Buchungen und gleichem n (dem Planungshorizont) und verschiedenen späteren: dieselben ersten m Entscheidungen
    m = 120
    for seed in range(4):
        A_, r, b, u = make_instance(4, 400, 0.3, seed)
        order = make_order(u, "zufällig", seed)
        late = order[m:]
        r2 = r.copy()
        r2[late] = np.random.default_rng(seed).uniform(1, 10, len(late))
        for rule in ONLINE:
            first = A.simulate(rule, A_, r, b, order)
            second = A.simulate(rule, A_, r2, b, order)
            assert np.array_equal(first.accepted[order[:m]], second.accepted[order[:m]]), rule


def test_lp_grows_with_capacity_and_with_more_requests():
    A_, r, b, _ = make_instance(4, 300, 0.3, 1)
    base = A.lp_opt(A_, r, b)[0]
    assert A.lp_opt(A_, r, b * 1.5)[0] >= base - 1e-9 and A.lp_opt(A_, r, b * 0.5)[0] <= base + 1e-9
    assert A.lp_opt(A_[:, :200], r[:200], b)[0] <= base + 1e-9


def test_order_does_not_change_the_lp_or_the_oracle_value_much():
    # die Orakel-Preise machen die Entscheidung (fast) unabhängig von der Reihenfolge
    for seed in range(4):
        A_, r, b, u = make_instance(4, 1000, 0.3, seed)
        lp, duals = A.lp_opt(A_, r, b)
        vals = [A.simulate("Orakel-Preise", A_, r, b, make_order(u, o, seed), oracle_duals=duals).value / lp for o in C.ORDNUNGEN]
        assert min(vals) >= 0.97 and max(vals) <= 1.0 + 1e-9


def test_fcfs_in_descending_value_order_is_nearly_optimal_and_in_ascending_order_poor():
    for seed in range(4):
        A_, r, b, u = make_instance(4, 1000, 0.1, seed)
        lp = A.lp_opt(A_, r, b)[0]
        assert A.simulate("FCFS", A_, r, b, make_order(u, "absteigend", seed)).value / lp >= 0.98
        assert A.simulate("FCFS", A_, r, b, make_order(u, "aufsteigend (niedrige zuerst)", seed)).value / lp <= 0.3


def test_learning_fails_when_the_beginning_is_untypical():
    for seed in range(4):
        A_, r, b, u = make_instance(4, 1000, 0.3, seed)
        res = A.simulate("Preislernen", A_, r, b, make_order(u, "absteigend", seed))
        assert res.value == 0.0


def test_exponential_rule_is_never_worse_than_a_third_of_the_lp_on_one_resource_in_the_worst_order():
    # Garantie 1/(ln(U/L) + 1) = 0,303 für eine Ressource (Auszug einer Quelle); die Messung liegt nur wenig darüber
    for seed in range(6):
        for kn in (0.1, 0.3, 0.6):
            A_, r, b, u = make_instance(1, 1000, kn, seed)
            lp = A.lp_opt(A_, r, b)[0]
            f = A.simulate("exponentiell", A_, r, b, make_order(u, "aufsteigend (niedrige zuerst)", seed)).value / lp
            assert f >= A.exp_guarantee() - 0.02, (seed, kn, f)
