"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

D_MIN, D_MAX, DEFAULT_D = 1, 8, 4               # Teilstrecken des Netzes
N_OPTIONS = (100, 200, 400, 1000, 2000, 4000, 8000)
DEFAULT_N = 2000
KN_MIN, KN_MAX, KN_STEP, DEFAULT_KN = 0.1, 1.0, 0.1, 0.3     # Knappheit: Kapazität je Strecke als Anteil der Nachfrage dieser Strecke
SEED_MAX, DEFAULT_SEED = 999999, 7

LO, HI = 1.0, 10.0                              # Wert je Einheit liegt gleichverteilt zwischen LO und HI (Verhältnis U/L = 10)
TWO_LEG_SHARE = 0.5                             # Anteil der Buchungen, die zwei Teilstrecken nutzen
LEARN_START = 1 / 20                            # Preislernen: Anteil der Anfragen, die erst beobachtet werden
GRADIENT_ETA = 1.0                              # Faktor auf HI / sqrt(n) für das Dual-Gradient-Verfahren

REGELN = ("FCFS", "Orakel-Preise", "Preislernen", "Dual-Gradient", "exponentiell")
DEFAULT_REGEL = "Preislernen"
REGEL_HILFE = {
    "FCFS": "Nimmt jede Buchung an, solange der Platz auf allen ihren Strecken reicht, ohne auf den Wert zu schauen.",
    "Orakel-Preise": "Nimmt an, wenn der Wert die Schattenpreise der ganzen Folge übersteigt. Braucht die ganze Folge und ist online nicht möglich: nur zum Vergleich.",
    "Preislernen": "Berechnet aus dem bisher Gesehenen die Schattenpreise einer LP und erneuert sie, wenn sich die Zahl der Beobachtungen verdoppelt (in der Art von Agrawal, Wang und Ye).",
    "Dual-Gradient": "Hält einen Preis je Strecke, der steigt, wenn mehr verbraucht wird als der Plan je Buchung, und sinkt sonst (in der Art von Balseiro, Lu und Mirrokni).",
    "exponentiell": "Der Preis je Strecke wächst exponentiell mit der Auslastung; nimmt an, wenn der Wert die Summe der Preise erreicht. Verteilungsfrei (in der Art von Zhou, Chakrabarty und Lukose).",
}
ORDNUNGEN = ("zufällig", "aufsteigend (niedrige zuerst)", "absteigend")
DEFAULT_ORDNUNG = "zufällig"
ORDNUNG_HILFE = {
    "zufällig": "Die Buchungen kommen in zufälliger Reihenfolge, der Anfang ist typisch für das Ganze.",
    "aufsteigend (niedrige zuerst)": "Die Buchungen mit dem niedrigsten Wert je Einheit kommen zuerst: für FCFS, Dual-Gradient und die exponentielle Preisfunktion die schlechteste der drei Reihenfolgen (für Preislernen ist es die absteigende).",
    "absteigend": "Die Buchungen mit dem höchsten Wert je Einheit kommen zuerst: der Anfang ist völlig untypisch für das Ganze.",
}
TRACE_LEN = 20
CURVE_POINTS = 300

# feste Experimente (nie ein einzelner Seed als Befund)
SWEEP_SEEDS = tuple(range(10, 15))
SWEEP_N = 1000
ORDER_KNS = (0.1, 0.3, 0.6)
GROWTH_NS = (100, 400, 1000, 4000)
RESSOURCEN_DS = (1, 2, 4, 8)
STEP_FACTORS = (0.1, 0.3, 1.0, 3.0, 10.0)
GUARANTEE_KNS = (0.1, 0.3, 0.6)

COLORS = {"FCFS": "#c0392b", "Orakel-Preise": "#4c78a8", "Preislernen": "#2F6B65", "Dual-Gradient": "#d97706", "exponentiell": "#7c3aed"}
COLOR_REF = "rgba(150,150,150,0.8)"

PRESETS = {
    "Netz mit vier Strecken": {"regel": "Preislernen", "d": DEFAULT_D, "n": DEFAULT_N, "kn": DEFAULT_KN, "ordnung": "zufällig", "seed": DEFAULT_SEED},
    "Gegner: niedrige Werte zuerst": {"regel": "exponentiell", "d": DEFAULT_D, "n": DEFAULT_N, "kn": 0.1, "ordnung": "aufsteigend (niedrige zuerst)", "seed": DEFAULT_SEED},
    "Sortiert absteigend: Lernen scheitert": {"regel": "Preislernen", "d": DEFAULT_D, "n": DEFAULT_N, "kn": DEFAULT_KN, "ordnung": "absteigend", "seed": DEFAULT_SEED},
    "Eine Strecke (Online-Rucksack)": {"regel": "exponentiell", "d": 1, "n": DEFAULT_N, "kn": 0.1, "ordnung": "aufsteigend (niedrige zuerst)", "seed": DEFAULT_SEED},
    "Viele Strecken": {"regel": "Dual-Gradient", "d": 8, "n": DEFAULT_N, "kn": DEFAULT_KN, "ordnung": "zufällig", "seed": DEFAULT_SEED},
    "Reichlich Platz": {"regel": "FCFS", "d": DEFAULT_D, "n": DEFAULT_N, "kn": 1.0, "ordnung": "zufällig", "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Netz mit vier Strecken": "Vier Teilstrecken, die Hälfte der Buchungen nutzt zwei davon, 30 % der Nachfrage als Platz, zufällige Reihenfolge: Preislernen liegt bei etwa neun Zehnteln des Optimums.",
    "Gegner: niedrige Werte zuerst": "Die schlechteste der drei getesteten Reihenfolgen bei sehr knappem Platz: die verteilungsfreie Preisfunktion bleibt bei etwa einem Drittel des Optimums (die Garantie für eine Strecke wäre 30 %), FCFS verliert fast alles.",
    "Sortiert absteigend: Lernen scheitert": "Die wertvollsten Buchungen kommen zuerst: Preislernen lernt zu hohe Preise und lehnt danach in diesem Netz mit vier Strecken alles ab.",
    "Eine Strecke (Online-Rucksack)": "Nur eine Strecke: der Online-Rucksack. Die verteilungsfreie Preisfunktion gegen ihre Garantie für eine Ressource.",
    "Viele Strecken": "Acht Teilstrecken: Dual-Gradient liegt im Mittel 12 Punkte tiefer als mit einer Strecke (Experiment 3).",
    "Reichlich Platz": "Der Platz reicht für die ganze Nachfrage: FCFS nimmt alles an und ist optimal; die Preisregeln lehnen ohne Not einzelne Buchungen ab.",
}
