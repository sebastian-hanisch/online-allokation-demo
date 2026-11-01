"""Kennzahlen, Verdikt-Logik und Experimente. Verdikte sind reine Funktionen (Art, Text); tests/test_verdicts.py prüft jede Zahl darin."""

from dataclasses import dataclass

import numpy as np

import ola_algorithm as A
import ola_constants as C
from ola_scenario import make_instance, make_order

OK_FRACTION, WARN_FRACTION = 0.9, 0.6            # Verdikt: grün ab 90 % des LP-Werts, gelb ab 60 %, sonst Warnung


@dataclass(frozen=True)
class Settings:
    regel: str = C.DEFAULT_REGEL
    d: int = C.DEFAULT_D
    n: int = C.DEFAULT_N
    kn: float = C.DEFAULT_KN
    ordnung: str = C.DEFAULT_ORDNUNG
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    lp_value: float
    fractions: dict               # Regel -> Wert / LP-Wert
    values: dict                  # Regel -> Wert
    accepted: dict                # Regel -> Zahl der angenommenen Buchungen
    utilization: list             # Auslastung je Strecke (0 bis 1) der hervorgehobenen Regel
    trace: list                   # Zeilen der Ablauftabelle der hervorgehobenen Regel
    curves: dict                  # Regel -> (Anteil der Buchungen, kumulierter Wert / LP-Wert), auf CURVE_POINTS Punkte verkleinert


def fraction(value: float, lp_value: float) -> float:
    """Wert geteilt durch den LP-Wert; ohne Wert der LP (nichts zu verteilen) ist 1 der neutrale Wert."""
    return 1.0 if lp_value <= 0 else float(value) / float(lp_value)


def run_all(A_, r, b, order, eta_factor: float = 1.0):
    """Alle fünf Regeln auf derselben Instanz und Reihenfolge; Rückgabe (LP-Wert, {Regel: Result})."""
    lp_value, duals = A.lp_opt(A_, r, b)
    results = {rule: A.simulate(rule, A_, r, b, order, oracle_duals=duals, eta_factor=eta_factor) for rule in C.REGELN}
    return lp_value, results


def analyse(s: Settings) -> Analysis:
    A_, r, b, u = make_instance(s.d, s.n, s.kn, s.seed)
    order = make_order(u, s.ordnung, s.seed)
    lp_value, results = run_all(A_, r, b, order)
    fr = {k: fraction(v.value, lp_value) for k, v in results.items()}
    return Analysis(
        s, lp_value, fr, {k: v.value for k, v in results.items()}, {k: int(v.accepted.sum()) for k, v in results.items()},
        [float(x) for x in results[s.regel].used / b], trace_rows(A_, r, u, order, results[s.regel]), curves(A_, r, order, results, lp_value),
    )


def trace_rows(A_, r, u, order, res: A.Result, limit: int = C.TRACE_LEN) -> list[dict]:
    """Die ersten Buchungen der hervorgehobenen Regel: Strecken, Wert, Preis und Entscheidung."""
    rows = []
    for t, j in enumerate(order[:limit]):
        price = res.prices[t]
        rows.append({
            "Nr": t + 1, "Strecken": "+".join(str(i + 1) for i in np.flatnonzero(A_[:, j])), "Wert": round(float(r[j]), 2),
            "Preis": "–" if price != price else ("∞" if price == float("inf") else round(price, 2)),
            "Entscheidung": "angenommen" if res.accepted[j] else "abgelehnt",
        })
    return rows


def curves(A_, r, order, results, lp_value) -> dict:
    n = len(order)
    idx = np.unique(np.linspace(0, n - 1, min(n, C.CURVE_POINTS)).astype(int))
    out = {}
    for rule, res in results.items():
        gained = np.cumsum([r[j] if res.accepted[j] else 0.0 for j in order])
        out[rule] = ([float((i + 1) / n) for i in idx], [float(gained[i] / lp_value) if lp_value > 0 else 1.0 for i in idx])
    return out


# ---------------------------------------------------------------------------------------------------------------------------------
# Experimente mit festen Instanzen und Seeds


def _mean_fractions(d, n, kn, ordnung, seeds=C.SWEEP_SEEDS, eta_factor=1.0, rules=C.REGELN) -> dict:
    acc = {k: [] for k in rules}
    for sd in seeds:
        A_, r, b, u = make_instance(d, n, kn, sd)
        order = make_order(u, ordnung, sd)
        lp_value, duals = A.lp_opt(A_, r, b)
        for rule in rules:
            res = A.simulate(rule, A_, r, b, order, oracle_duals=duals, eta_factor=eta_factor)
            acc[rule].append(fraction(res.value, lp_value))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def order_rows(d: int = C.DEFAULT_D, n: int = C.SWEEP_N) -> list[dict]:
    """Knappheit × Reihenfolge: Wert / LP-Wert je Regel, Mittel über feste Seeds."""
    return [{"Knappheit": kn, "Reihenfolge": o, **_mean_fractions(d, n, kn, o)} for kn in C.ORDER_KNS for o in C.ORDNUNGEN]


def growth_rows(d: int = C.DEFAULT_D) -> list[dict]:
    """Wächst die Zahl der Buchungen (zufällige Reihenfolge, Knappheit 0,3)?"""
    return [{"n": n, **_mean_fractions(d, n, C.DEFAULT_KN, "zufällig")} for n in C.GROWTH_NS]


def resource_rows(n: int = C.SWEEP_N) -> list[dict]:
    """Mehr Teilstrecken (zufällige Reihenfolge, Knappheit 0,3)."""
    return [{"d": d, **_mean_fractions(d, n, C.DEFAULT_KN, "zufällig")} for d in C.RESSOURCEN_DS]


def step_rows(d: int = C.DEFAULT_D, n: int = C.SWEEP_N) -> list[dict]:
    """Schrittweite des Dual-Gradient-Verfahrens (Faktor auf HI/√n): zufällige und aufsteigende Reihenfolge."""
    rows = []
    for f in C.STEP_FACTORS:
        rnd = _mean_fractions(d, n, C.DEFAULT_KN, "zufällig", eta_factor=f, rules=("Dual-Gradient",))["Dual-Gradient"]
        asc = _mean_fractions(d, n, C.DEFAULT_KN, "aufsteigend (niedrige zuerst)", eta_factor=f, rules=("Dual-Gradient",))["Dual-Gradient"]
        rows.append({"Faktor": f, "zufällig": rnd, "aufsteigend": asc})
    return rows


def guarantee_rows(n: int = C.SWEEP_N) -> list[dict]:
    """Eine Strecke (Online-Rucksack), schlechteste Reihenfolge: die verteilungsfreie Preisfunktion gegen ihre Garantie 1/(ln(U/L) + 1)."""
    g = A.exp_guarantee()
    rows = []
    for kn in C.GUARANTEE_KNS:
        fr = _mean_fractions(1, n, kn, "aufsteigend (niedrige zuerst)")
        rows.append({"Knappheit": kn, "Garantie": g, **fr})
    return rows


# ---------------------------------------------------------------------------------------------------------------------------------
# Verdikte (rein: Art, Text)


def delta_text(value: float, reference: float, label: str) -> tuple[str, str]:
    """Text und Farbregel des Deltas: „mein Wert minus Referenz“, in Prozentpunkten. Ein auf zwei Stellen gleicher Wert bekommt keinen Pfeil und keine Farbe."""
    d = 100.0 * (value - reference)
    if abs(d) < 0.05:
        return f"gleich wie {label}", "off"
    return f"{d:+.1f} Punkte gegen {label}", "normal"


def verdict_kern(a: Analysis) -> tuple[str, str]:
    """Kernfrage: Wie viel vom Optimum erreicht die Regel auf dieser Folge?"""
    s = a.settings
    f = a.fractions[s.regel]
    text = (f"**{s.regel}** nimmt {a.accepted[s.regel]} von {s.n} Buchungen an und erreicht **{f * 100:.1f} %** des LP-Optimums ({a.values[s.regel]:.0f} von {a.lp_value:.0f}). "
            f"FCFS erreicht {a.fractions['FCFS'] * 100:.1f} %, die Orakel-Preise (nur mit der ganzen Folge möglich) {a.fractions['Orakel-Preise'] * 100:.1f} %.")
    if s.regel == "exponentiell" and s.d == 1:
        text += f" Die Garantie dieser Regel für eine Strecke ist {A.exp_guarantee() * 100:.1f} %."
    kind = "success" if f >= OK_FRACTION else "info" if f >= WARN_FRACTION else "warning"
    return kind, text


def verdict_ordnung(rows: list[dict]) -> tuple[str, str]:
    """Experiment 1: Knappheit und Reihenfolge."""
    z = next(r for r in rows if r["Knappheit"] == min(x["Knappheit"] for x in rows) and r["Reihenfolge"] == "zufällig")
    asc = next(r for r in rows if r["Knappheit"] == z["Knappheit"] and r["Reihenfolge"].startswith("aufsteigend"))
    desc = next(r for r in rows if r["Knappheit"] == z["Knappheit"] and r["Reihenfolge"] == "absteigend")
    orakel_min = min(r["Orakel-Preise"] for r in rows)
    return "info", (f"Bei Knappheit {z['Knappheit']:g}: Preislernen erreicht {z['Preislernen']:.3f} des Optimums bei zufälliger Reihenfolge und **{desc['Preislernen']:.3f}** bei absteigender; "
                    f"die exponentielle Preisfunktion in der schlechtesten Reihenfolge {asc['exponentiell']:.3f}, FCFS {asc['FCFS']:.3f}. Die Orakel-Preise erreichen in jeder Reihenfolge mindestens {orakel_min:.3f}.")


def verdict_wachstum(rows: list[dict]) -> tuple[str, str]:
    """Experiment 2: wachsendes n."""
    a, b = rows[0], rows[-1]
    return "info", (f"Von n = {a['n']} auf n = {b['n']} Buchungen steigt Preislernen von {a['Preislernen']:.3f} auf {b['Preislernen']:.3f}, Dual-Gradient von {a['Dual-Gradient']:.3f} auf {b['Dual-Gradient']:.3f}; "
                    f"die exponentielle Preisfunktion bleibt bei {a['exponentiell']:.3f} und {b['exponentiell']:.3f}, FCFS bei {a['FCFS']:.3f} und {b['FCFS']:.3f}.")


def verdict_ressourcen(rows: list[dict]) -> tuple[str, str]:
    """Experiment 3: mehr Teilstrecken."""
    a, b = rows[0], rows[-1]
    return "info", (f"Von {a['d']} auf {b['d']} Strecken sinkt Preislernen von {a['Preislernen']:.3f} auf {b['Preislernen']:.3f} und Dual-Gradient von {a['Dual-Gradient']:.3f} auf {b['Dual-Gradient']:.3f}; "
                    f"die exponentielle Preisfunktion liegt bei {a['exponentiell']:.3f} und {b['exponentiell']:.3f}.")


def verdict_schritt(rows: list[dict]) -> tuple[str, str]:
    """Experiment 4: Schrittweite des Dual-Gradient-Verfahrens."""
    best_rnd = max(rows, key=lambda r: r["zufällig"])
    best_asc = max(rows, key=lambda r: r["aufsteigend"])
    return "info", (f"Bei zufälliger Reihenfolge ist der Faktor {best_rnd['Faktor']:g} am besten ({best_rnd['zufällig']:.3f}), bei aufsteigender der Faktor {best_asc['Faktor']:g} ({best_asc['aufsteigend']:.3f}); "
                    f"der kleinste Faktor {rows[0]['Faktor']:g} erreicht {rows[0]['zufällig']:.3f} und {rows[0]['aufsteigend']:.3f}.")


def verdict_garantie(rows: list[dict]) -> tuple[str, str]:
    """Experiment 5: eine Strecke, schlechteste Reihenfolge, Garantie."""
    first = rows[0]
    return "info", (f"Bei Knappheit {first['Knappheit']:g} erreicht die exponentielle Preisfunktion in der schlechtesten Reihenfolge **{first['exponentiell']:.3f}** des Optimums; "
                    f"die Garantie für eine Strecke ist {first['Garantie']:.3f}. FCFS erreicht dort {first['FCFS']:.3f}, Preislernen {first['Preislernen']:.3f}.")
