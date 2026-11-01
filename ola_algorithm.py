"""Kern: Online-Allokation. Buchungen kommen nacheinander, jede wird sofort angenommen oder abgelehnt, solange die Restkapazität reicht.

Referenz ist die LP-Relaxation der ganzen Folge (obere Schranke des Optimums) mit ihren Schattenpreisen. Die fünf Regeln unterscheiden sich nur darin,
welchen Preis sie einer Buchung zuweisen: angenommen wird, wenn der Wert den Preis übersteigt (FCFS: immer)."""

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

import ola_constants as C


@dataclass(frozen=True)
class Result:
    value: float
    accepted: np.ndarray        # bool je Buchung (Index der Instanz)
    prices: list                # Preis der Buchung zum Zeitpunkt der Entscheidung (nan, wenn die Regel keinen hat), in Eintreffreihenfolge
    used: np.ndarray            # Verbrauch je Strecke am Ende


def lp_opt(A: np.ndarray, r: np.ndarray, b: np.ndarray):
    """LP-Relaxation: größter Wert bei Kapazitäten b und 0 <= x <= 1; Rückgabe (Wert, Schattenpreise je Strecke)."""
    res = linprog(-r, A_ub=A, b_ub=b, bounds=[(0, 1)] * A.shape[1], method="highs")
    if res.status != 0:
        raise RuntimeError(f"LP nicht lösbar: {res.message}")
    return float(-res.fun), np.maximum(0.0, -res.ineqlin.marginals)


def dual_value(A: np.ndarray, r: np.ndarray, b: np.ndarray, p: np.ndarray) -> float:
    """Zielwert des dualen Programms bei Preisen p: b·p + Σ_j max(0, r_j − a_j·p). Schwache Dualität: nie kleiner als der LP-Wert."""
    return float(b @ p + np.sum(np.maximum(0.0, r - A.T @ p)))


def is_feasible(A: np.ndarray, accepted: np.ndarray, b: np.ndarray) -> bool:
    """Unabhängiger Prüfer: der Verbrauch der angenommenen Buchungen übersteigt keine Kapazität."""
    return bool(np.all(A[:, accepted].sum(axis=1) <= b + 1e-9))


def exp_price(z: float) -> float:
    """Preis je Einheit bei Auslastung z in [0, 1]: LO/e · (HI·e/LO)^z; bei z = 0 LO/e (gut ein Drittel des niedrigsten Werts), bei z = 1 genau HI."""
    return (C.LO / math.e) * (C.HI * math.e / C.LO) ** z


def exp_guarantee(lo: float = C.LO, hi: float = C.HI) -> float:
    """Garantie der verteilungsfreien Preisfunktion für EINE Ressource: Anteil des Optimums 1/(ln(U/L) + 1) (Zhou/Chakrabarty/Lukose, Auszug)."""
    return 1.0 / (math.log(hi / lo) + 1.0)


def simulate(rule: str, A: np.ndarray, r: np.ndarray, b: np.ndarray, order, oracle_duals=None, eta_factor: float = 1.0) -> Result:
    d, n = A.shape
    used = np.zeros(d)
    accepted = np.zeros(n, dtype=bool)
    prices: list = []
    value = 0.0
    learned = None
    next_epoch = max(5, int(n * C.LEARN_START))
    p_grad = np.zeros(d)
    rho = b / n
    eta = C.GRADIENT_ETA * eta_factor * C.HI / math.sqrt(n)
    for t, j in enumerate(order):
        a = A[:, j]
        rj = r[j]
        if rule == "FCFS":
            price = float("nan")
        elif rule == "Orakel-Preise":
            price = float(a @ oracle_duals)
        elif rule == "Preislernen":
            if t == next_epoch:
                idx = list(order[:t])
                eps = math.sqrt(math.log(max(d, 2)) / t)
                bb = b * (t / n) * (1 - eps)
                if bb.min() <= 0:
                    bb = b * (t / n)
                learned = lp_opt(A[:, idx], r[idx], np.maximum(bb, 1e-6))[1]
                next_epoch = 2 * t
            price = float("inf") if learned is None else float(a @ learned)
        elif rule == "Dual-Gradient":
            price = float(a @ p_grad)
        elif rule == "exponentiell":
            price = float(sum(exp_price(used[i] / b[i]) for i in np.flatnonzero(a)))
        else:
            raise ValueError(f"unbekannte Regel: {rule}")
        fits = bool(np.all(used + a <= b + 1e-9))
        if rule == "FCFS":
            take = fits
        elif rule == "exponentiell":
            take = fits and rj >= price
        else:
            take = fits and rj > price
        if rule == "Dual-Gradient":
            x = 1.0 if (rj > price) else 0.0                        # der Preis lernt aus dem Wunsch, nicht aus dem Platz
            p_grad = np.maximum(0.0, p_grad - eta * (rho - a * x))
        prices.append(price)
        if take:
            used = used + a
            accepted[j] = True
            value += rj
    return Result(value, accepted, prices, used)
