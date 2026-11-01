"""Buchungen für ein Netz mit d Teilstrecken. Jede Buchung nutzt eine oder zwei Strecken (je eine Einheit) und hat einen Wert je Einheit zwischen LO und HI."""

import numpy as np

import ola_constants as C


def make_instance(d: int, n: int, knappheit: float, seed: int):
    """A (d x n, Einträge 0/1), Werte r (Wert je Einheit mal Zahl der Strecken), Kapazitäten b (Anteil `knappheit` der Nachfrage je Strecke, mindestens 1),
    und der Wert je Einheit u."""
    rng = np.random.default_rng([seed, d, n])
    A = np.zeros((d, n))
    for j in range(n):
        first = int(rng.integers(d))
        A[first, j] = 1.0
        if d > 1 and rng.random() < C.TWO_LEG_SHARE:
            other = int(rng.integers(d))
            A[other, j] = 1.0                  # trifft der Zufall dieselbe Strecke, bleibt es bei einer
    u = rng.uniform(C.LO, C.HI, n)
    r = u * A.sum(axis=0)
    b = np.maximum(1.0, np.floor(knappheit * A.sum(axis=1)))
    return A, r, b, u


def make_order(u: np.ndarray, ordnung: str, seed: int) -> list[int]:
    """Reihenfolge, in der die Buchungen eintreffen (Indizes der Instanz)."""
    n = len(u)
    if ordnung == "zufällig":
        return [int(x) for x in np.random.default_rng([seed, n, 77]).permutation(n)]
    if ordnung == "aufsteigend (niedrige zuerst)":
        return [int(x) for x in np.argsort(u, kind="stable")]
    if ordnung == "absteigend":
        return [int(x) for x in np.argsort(-u, kind="stable")]
    raise ValueError(f"unbekannte Reihenfolge: {ordnung}")
