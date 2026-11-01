"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Eine Strecke mit Kapazität 2, drei Buchungen mit Werten 3, 1, 2 (in dieser Reihenfolge), je eine Einheit: (A, r, b, order).

    Handrechnung: FCFS nimmt 3 und 1 (Wert 4), das Optimum 3 und 2 (Wert 5). Orakel-Preis 1,5: nimmt 3 und 2 (5). Exponentielle Preisfunktion: Preis bei Auslastung 0
    ist 1/e = 0,37 (3 wird angenommen), bei Auslastung 1/2 ist er (1/e)(10e)^(1/2) = 1,92 (die 1 wird abgelehnt), die 2 ≥ 1,92 wird angenommen: Wert 5.
    Dual-Gradient: Schritt η = 10/√3, Plan ρ = 2/3: nach der 3 steigt der Preis auf 1,92, die 1 wird abgelehnt und der Preis fällt auf 0, die 2 wird angenommen: Wert 5.
    Preislernen: bei n = 3 ist die Lernphase (mindestens 5 Buchungen) länger als die Folge, es nimmt nichts an: Wert 0."""
    A = np.array([[1.0, 1.0, 1.0]])
    r = np.array([3.0, 1.0, 2.0])
    b = np.array([2.0])
    return A, r, b, [0, 1, 2]
