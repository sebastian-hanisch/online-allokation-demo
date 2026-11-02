"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Verzweigung steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text). Die Tests geben ihr Analyse-Objekte oder Zeilen mit gesetzten Werten und prüfen die Art und jede genannte Zahl."""

import ola_algorithm as A
import ola_evaluation as ev


def _analysis(regel="Preislernen", d=4, f=0.926, lp=7000.0):
    s = ev.Settings(regel=regel, d=d, n=2000)
    fr = {"FCFS": 0.624, "Orakel-Preise": 0.997, "Preislernen": f, "Dual-Gradient": f, "exponentiell": f}
    vals = {k: v * lp for k, v in fr.items()}
    acc = {k: 562 for k in fr}
    return ev.Analysis(s, lp, fr, vals, acc, [1.0, 0.8], [], {})


def test_kern_names_accepted_fraction_values_and_comparisons():
    kind, text = ev.verdict_kern(_analysis())
    assert kind == "success"
    assert "**Preislernen** nimmt 562 von 2000 Buchungen an und erreicht **92.6 %** des LP-Optimums (6482 von 7000)." in text
    assert "FCFS erreicht 62.4 %, die Orakel-Preise (nur mit der ganzen Folge möglich) 99.7 %." in text and "Garantie" not in text


def test_kern_thresholds_are_ninety_and_sixty_percent():
    assert ev.verdict_kern(_analysis(f=0.9))[0] == "success"
    assert ev.verdict_kern(_analysis(f=0.8999))[0] == "info"
    assert ev.verdict_kern(_analysis(f=0.6))[0] == "info"
    assert ev.verdict_kern(_analysis(f=0.5999))[0] == "warning"


def test_kern_mentions_the_guarantee_only_for_the_exponential_rule_on_one_leg():
    _, text = ev.verdict_kern(_analysis(regel="exponentiell", d=1, f=0.32))
    assert f"Die Garantie dieser Regel für eine Strecke ist {A.exp_guarantee() * 100:.1f} %." in text and "30.3 %" in text
    assert "Garantie" not in ev.verdict_kern(_analysis(regel="exponentiell", d=4, f=0.32))[1]
    assert "Garantie" not in ev.verdict_kern(_analysis(regel="Preislernen", d=1))[1]


def _order_rows():
    def row(kn, o, **v):
        base = {"FCFS": 0, "Orakel-Preise": 0.98, "Preislernen": 0, "Dual-Gradient": 0, "exponentiell": 0}
        base.update(v)
        return {"Knappheit": kn, "Reihenfolge": o, **base}
    return [row(0.1, "zufällig", Preislernen=0.845), row(0.1, "aufsteigend (niedrige zuerst)", FCFS=0.153, exponentiell=0.313), row(0.1, "absteigend", Preislernen=0.0, **{"Orakel-Preise": 0.982}),
            row(0.3, "zufällig", Preislernen=0.9), row(0.3, "aufsteigend (niedrige zuerst)", FCFS=0.3), row(0.3, "absteigend", Preislernen=0.1, **{"Orakel-Preise": 0.994})]


def test_ordnung_uses_the_smallest_knappheit_and_names_the_extreme_cells():
    kind, text = ev.verdict_ordnung(_order_rows())
    assert kind == "info"
    assert "Bei Knappheit 0.1: Preislernen erreicht 0.845 des Optimums bei zufälliger Reihenfolge und **0.000** bei absteigender" in text
    assert "die exponentielle Preisfunktion in der aufsteigenden Reihenfolge (der schlechtesten der drei getesteten) 0.313, FCFS 0.153." in text and "in jeder Reihenfolge mindestens 0.980." in text


def test_wachstum_ressourcen_schritt_and_garantie_name_first_and_last_row():
    rows = [{"n": 100, "FCFS": 0.659, "Preislernen": 0.746, "Dual-Gradient": 0.788, "exponentiell": 0.746}, {"n": 4000, "FCFS": 0.636, "Preislernen": 0.921, "Dual-Gradient": 0.955, "exponentiell": 0.756}]
    kind, text = ev.verdict_wachstum(rows)
    assert kind == "info" and "Von n = 100 auf n = 4000 Buchungen steigt Preislernen von 0.746 auf 0.921, Dual-Gradient von 0.788 auf 0.955" in text
    assert "die exponentielle Preisfunktion bleibt bei 0.746 und 0.756, FCFS bei 0.659 und 0.636." in text
    rows = [{"d": 1, "Preislernen": 0.895, "Dual-Gradient": 0.967, "exponentiell": 0.758}, {"d": 8, "Preislernen": 0.856, "Dual-Gradient": 0.847, "exponentiell": 0.748}]
    _, text = ev.verdict_ressourcen(rows)
    assert "Von 1 auf 8 Strecken sinkt Preislernen von 0.895 auf 0.856 und Dual-Gradient von 0.967 auf 0.847" in text and "bei 0.758 und 0.748." in text
    rows = [{"Faktor": 0.1, "zufällig": 0.659, "aufsteigend": 0.272}, {"Faktor": 3.0, "zufällig": 0.954, "aufsteigend": 0.583}, {"Faktor": 10.0, "zufällig": 0.92, "aufsteigend": 0.627}]
    _, text = ev.verdict_schritt(rows)
    assert "Bei zufälliger Reihenfolge ist der Faktor 3 am besten (0.954), bei aufsteigender der Faktor 10 (0.627)" in text and "der kleinste Faktor 0.1 erreicht 0.659 und 0.272." in text
    rows = [{"Knappheit": 0.1, "Garantie": 0.303, "exponentiell": 0.32, "FCFS": 0.153, "Preislernen": 0.201}]
    _, text = ev.verdict_garantie(rows)
    assert "Bei Knappheit 0.1 erreicht die exponentielle Preisfunktion in der aufsteigenden Reihenfolge (der schlechtesten der drei getesteten) **0.320**" in text
    assert "die Garantie für eine Strecke ist 0.303. FCFS erreicht dort 0.153, Preislernen 0.201." in text


def test_delta_text_is_in_percentage_points():
    assert ev.delta_text(0.926, 0.624, "FCFS") == ("+30.2 Punkte gegen FCFS", "normal")
    assert ev.delta_text(0.5, 0.6, "FCFS") == ("-10.0 Punkte gegen FCFS", "normal")
    assert ev.delta_text(0.9, 0.90004, "FCFS") == ("gleich wie FCFS", "off")
