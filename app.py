"""Online-Allokation – Buchungen mit Preisen statt mit Glück annehmen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der Reihe „Online-Algorithmen“: Buchungen für Laderaum auf mehreren Teilstrecken werden sofort angenommen oder abgelehnt, ohne die späteren zu kennen.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import ola_algorithm as A
import ola_constants as C
from ola_evaluation import (
    Settings,
    analyse,
    delta_text,
    growth_rows,
    guarantee_rows,
    order_rows,
    resource_rows,
    step_rows,
    verdict_garantie,
    verdict_kern,
    verdict_ordnung,
    verdict_ressourcen,
    verdict_schritt,
    verdict_wachstum,
)
from ola_layout import dunkles_design, kopf_css
from ola_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from ola_visualization import build_curves, build_fractions, build_growth, build_guarantee, build_heat, build_resources, build_steps, build_utilization

st.set_page_config(page_title="Online-Allokation – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne die Preise …")
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner="Rechne Knappheit und Reihenfolge über fünf Seeds …")
def _order():
    return order_rows()


@st.cache_data(show_spinner=False)
def _growth():
    return growth_rows()


@st.cache_data(show_spinner=False)
def _resources():
    return resource_rows()


@st.cache_data(show_spinner=False)
def _steps():
    return step_rows()


@st.cache_data(show_spinner=False)
def _guarantee():
    return guarantee_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in ola_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧮 Online-Allokation – Buchungen mit Preisen statt mit Glück annehmen")
st.markdown(
    """
**Viertes Stück der Reihe „Online-Algorithmen“** (Entscheiden ohne Kenntnis der Zukunft). Buchungen für Laderaum auf den **Teilstrecken eines Netzes** kommen nacheinander; jede wird **sofort angenommen oder abgelehnt**, solange der Platz auf allen ihren Strecken reicht.
Wer **Preise** für den knappen Platz kennt, entscheidet fast optimal: Er nimmt an, was mehr wert ist als der Platz kostet. Hier kennt man die Preise nicht.
Gemessen wird am **LP-Optimum der ganzen Folge** (obere Schranke des Optimums); was die Regeln erreichen, ist ein Anteil davon.

Weiter unten: die **Kernfrage**, fünf Experimente (**Knappheit und Reihenfolge**, **wachsende Buchungszahl**, **mehr Teilstrecken**, **Schrittweite**, **eine Strecke gegen die Garantie**), **🚧 Wo die Annahmen enden**, **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Online-Allokation", expanded=True):
    st.markdown(
        """
1. **Jede Buchung** nutzt eine oder zwei Teilstrecken (je eine Einheit) und hat einen **Wert je Einheit** zwischen 1 und 10. Jede Strecke hat nur so viel Platz, wie die **Knappheit** vorgibt (ein Anteil der Nachfrage dieser Strecke).
2. **Die Referenz** kennt alle Buchungen vorher: eine lineare Optimierung (LP) wählt aus, was den Gesamtwert maximiert. Ihre **Schattenpreise** sagen, was ein Platz auf jeder Strecke wert ist.
3. **Mit diesen Preisen wird die Entscheidung einfach:** Eine Buchung wird angenommen, wenn ihr Wert die Summe der Preise ihrer Strecken übersteigt. Die **Orakel-Preise** zeigen das (sie brauchen die ganze Folge und sind online unmöglich).
4. **Online muss man die Preise schätzen:** **Preislernen** löst die LP auf dem bisher Gesehenen und erneuert die Preise bei jeder Verdopplung; das **Dual-Gradient-Verfahren** erhöht den Preis einer Strecke, wenn mehr verbraucht wird als geplant; die **exponentielle Preisfunktion** setzt den Preis nach der Auslastung, ganz ohne Verteilung. **FCFS** nimmt an, was passt.
5. **Garantie, Lernen und Reihenfolge:** wer lernt, braucht einen typischen Anfang; wer keine Verteilung annimmt, zahlt im Normalfall. Die Experimente messen beides.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Regel**")
    regel = st.selectbox("Regel (hervorgehoben)", C.REGELN, key="regel_select", help="Alle Regeln laufen mit; die gewählte steht im Ergebnis und im Verdikt.")
    st.caption(C.REGEL_HILFE[regel])
    st.markdown("**Netz und Nachfrage**")
    d = st.slider("Teilstrecken d", *bounds("d_slider"), key="d_slider", help="Wie viele Strecken (Ressourcen) das Netz hat. Eine Strecke ist der Online-Rucksack.")
    n = st.select_slider("Buchungen n", options=C.N_OPTIONS, key="n_select")
    kn = st.slider("Knappheit", *bounds("kn_slider"), step=C.KN_STEP, key="kn_slider", help="Platz je Strecke als Anteil der Nachfrage dieser Strecke: 0,1 heißt, nur jede zehnte Anfrage passt.")
    ordnung = st.selectbox("Reihenfolge", C.ORDNUNGEN, key="ordnung_select", help="In welcher Reihenfolge die Buchungen eintreffen.")
    st.caption(C.ORDNUNG_HILFE[ordnung])
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Buchungen ziehen", width="stretch", on_click=randomize_seed)

sync_query_params({"regel_select": regel, "d_slider": int(d), "n_select": int(n), "kn_slider": float(kn), "ordnung_select": ordnung, "seed_input": int(seed)})

settings = Settings(regel, int(d), int(n), float(kn), ordnung, int(seed))
a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"{n} Buchungen auf {d} Teilstrecken · Knappheit {kn:g} · Reihenfolge „{ordnung}“ · hervorgehoben: {regel}")
f = a.fractions[regel]
m1, m2, m3, m4 = st.columns(4)
d1, c1 = delta_text(f, a.fractions["FCFS"], "FCFS")
m1.metric("Anteil des Optimums", f"{f * 100:.1f} %", delta=d1, delta_color=c1, help="Erreichter Wert geteilt durch das LP-Optimum der ganzen Folge.")
m2.metric("LP-Optimum", f"{a.lp_value:.0f}", delta="Referenz", delta_color="off", help="Obere Schranke des Optimums; kennt alle Buchungen.")
m3.metric("Angenommen", f"{a.accepted[regel]}", delta=f"von {n}", delta_color="off", help="Zahl der angenommenen Buchungen der hervorgehobenen Regel.")
m4.metric("Größte Auslastung", f"{max(a.utilization) * 100:.0f} %", delta=f"kleinste {min(a.utilization) * 100:.0f} %", delta_color="off", help="Auslastung der vollsten Strecke (hervorgehobene Regel).")
st.plotly_chart(build_fractions(a.fractions, regel), width="stretch", key="fractions_chart")
st.caption("Anteil des LP-Optimums je Regel (hervorgehoben: die gewählte). Die Orakel-Preise kennen die ganze Folge und zeigen, was mit richtigen Preisen möglich wäre.")
st.plotly_chart(build_curves(a.curves, regel), width="stretch", key="curves_chart")
st.caption("Wie der Wert über die Zeit entsteht. Bei Preislernen bleibt die Kurve zu Beginn flach (es lehnt ab, solange es lernt); bei FCFS wächst sie früh und flacht ab, sobald der Platz weg ist.")
st.plotly_chart(build_utilization(a.utilization), width="stretch", key="utilization_chart")
st.caption(f"Auslastung der Strecken am Ende ({regel}). Platz, der leer bleibt, ist entgangener Wert; Platz, der mit billigen Buchungen voll ist, auch.")
with st.expander(f"Ablauf der ersten {C.TRACE_LEN} Buchungen der hervorgehobenen Regel"):
    st.caption("Preis = Summe der Preise der Strecken der Buchung zum Zeitpunkt der Entscheidung; – bei FCFS (kein Preis), ∞ solange Preislernen noch lernt.")
    st.dataframe(pd.DataFrame(a.trace), hide_index=True, width="stretch")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel vom Optimum erreicht die Regel?")
kind, text = verdict_kern(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Knappheit und Reihenfolge")
rows_or = _order()
st.caption(f"{len(C.SWEEP_SEEDS)} feste Seeds, {C.SWEEP_N} Buchungen, 4 Teilstrecken; Zahl = Wert geteilt durch LP-Optimum. Aufsteigend: die niedrigen Werte kommen zuerst; absteigend: die hohen.")
st.plotly_chart(build_heat(rows_or), width="stretch", key="heat_chart")
kind, text = verdict_ordnung(rows_or)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment 2: Wächst die Zahl der Buchungen?")
rows_gr = _growth()
st.caption("Zufällige Reihenfolge, Knappheit 0,3, 4 Teilstrecken, feste Seeds.")
st.plotly_chart(build_growth(rows_gr), width="stretch", key="growth_chart")
kind, text = verdict_wachstum(rows_gr)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment 3: Mehr Teilstrecken")
rows_rs = _resources()
st.caption(f"Zufällige Reihenfolge, Knappheit 0,3, {C.SWEEP_N} Buchungen, feste Seeds.")
st.plotly_chart(build_resources(rows_rs), width="stretch", key="resources_chart")
kind, text = verdict_ressourcen(rows_rs)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment 4: Wie schnell sollen die Preise steigen?")
rows_st = _steps()
st.caption("Das Dual-Gradient-Verfahren mit verschiedenen Schrittweiten (Faktor auf HI/√n), Knappheit 0,3, 4 Teilstrecken. Zufällige gegen aufsteigende Reihenfolge.")
st.plotly_chart(build_steps(rows_st), width="stretch", key="steps_chart")
kind, text = verdict_schritt(rows_st)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment 5: Eine Strecke gegen die Garantie")
rows_ga = _guarantee()
st.caption(f"Eine Teilstrecke (der Online-Rucksack), aufsteigende Reihenfolge (niedrige Werte zuerst, die schlechteste der drei getesteten). Garantie der verteilungsfreien Preisfunktion für eine Strecke: 1/(ln(U/L) + 1) mit U/L = {C.HI / C.LO:g}.")
st.plotly_chart(build_guarantee(rows_ga), width="stretch", key="guarantee_chart")
kind, text = verdict_garantie(rows_ga)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Anfang der Folge ist typisch** (Preislernen) | Ist er es nicht, lernt das Verfahren falsche Preise; Experiment 1 zeigt den Extremfall mit 0,000. | – |
| **Eine Einheit je Strecke, höchstens zwei Strecken je Buchung** | Größere Mengen und längere Reisewege machen das Problem schwerer; nicht modelliert. | – |
| **Die Preise sind interne Schwellen** | Echte Preissetzung mit Kundenverhalten, Stornos und Overbooking fehlt. | – |
| **Eine bekannte Verteilung der Nachfrage** | Bei bekannter Verteilung und einer Ressource rechnet die dynamische Programmierung exakt (`uld-buchungsannahme-demo`). | – |
| **Keine Vorhersage der Nachfrage** | Eine Vorhersage lässt sich in die Preise stecken, darf aber nicht blind gelten. | Vorhersagen |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(
        f"""
**Annahmen.** Der Wert je Einheit ist gleichverteilt zwischen {C.LO:g} und {C.HI:g} (U/L = {C.HI / C.LO:g}), {C.TWO_LEG_SHARE * 100:.0f} % der Buchungen nutzen zwei Strecken; der Wert einer Buchung ist der Wert je Einheit mal Zahl der Strecken. Die Kapazität je Strecke ist der Anteil „Knappheit“ der Nachfrage dieser Strecke (abgerundet, mindestens 1). Das **LP-Optimum** ist eine obere Schranke des ganzzahligen Optimums; auf kleinen Instanzen fiel beides zusammen oder lag weniger als 0,002 % auseinander, im Allgemeinen ist ein Abstand möglich. Die Anteile sind deshalb **untere Schranken** der wahren Anteile.

**Grenzen.** Die Demo ist nur an erfundenen Buchungen geprüft. Die Regeln sind **vereinfachte Fassungen in der Art** der genannten Arbeiten, ohne deren bewiesene Konstanten. Die Garantie 1/(ln(U/L) + 1) gilt in der Quelle für **eine** Ressource; für mehrere Strecken ist kein geprüfter Wert bekannt, und die App behauptet keinen. Preislernen lehnt die ersten {C.LEARN_START * 100:.0f} % der Buchungen ab, solange es lernt. Die Experimente laufen über {len(C.SWEEP_SEEDS)} feste Seeds und sind Mittelwerte.

**Bekannte Probleme und Unsicherheiten.** Bei reichlich Platz (Knappheit 1) lehnen die Preisregeln einzelne Buchungen ohne Not ab, FCFS ist dort optimal. Die Schattenpreise der LP sind nicht immer eindeutig; die Orakel-Preise nehmen eine Lösung des Solvers.
        """
    )

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        rf"""
**Lesehilfe.** Gegeben sind $d$ Strecken mit Kapazitäten $b_i$ und $n$ Buchungen $j$ mit Wert $r_j$ und Verbrauch $a_{{ij}} \in \{{0, 1\}}$, die nacheinander eintreffen und sofort angenommen oder abgelehnt werden. Gesucht ist ein möglichst großer Gesamtwert.

| Symbol | Bedeutung |
|---|---|
| $d$, $n$ | Zahl der Strecken und der Buchungen |
| $b_i$ | Kapazität der Strecke $i$ |
| $r_j$, $a_{{ij}}$ | Wert und Verbrauch der Buchung $j$ |
| $x_j$ | Annahme der Buchung $j$ (0 oder 1) |
| $p_i$ | Preis (Schattenpreis) der Strecke $i$ |

**Referenz (LP).** $\max \sum_j r_j x_j$ unter $\sum_j a_{{ij}} x_j \le b_i$ und $0 \le x_j \le 1$. Das duale Programm: $\min \sum_i b_i p_i + \sum_j s_j$ unter $s_j \ge r_j - \sum_i a_{{ij}} p_i$, $s_j, p_i \ge 0$. Bei den optimalen Preisen $p$ gilt: Buchung $j$ wird gewählt, wenn $r_j > \sum_i a_{{ij}} p_i$.

**Preislernen.** Nach $k$ Buchungen löst die Regel die LP auf diesen $k$ Buchungen mit den Kapazitäten $b_i \tfrac{{k}}{{n}} (1 - \varepsilon_k)$, $\varepsilon_k = \sqrt{{\ln d / k}}$, nimmt die Schattenpreise und erneuert sie bei $2k$.

**Dual-Gradient.** $p \leftarrow \max(0,\; p - \eta(\rho - a_j x_j))$ mit $\rho_i = b_i / n$ und $\eta = f \cdot U/\sqrt{{n}}$ ($U = {C.HI:g}$, $f$ der Faktor aus Experiment 4); $x_j = 1$, wenn $r_j > a_j \cdot p$.

**Exponentielle Preisfunktion.** Preis je Einheit bei Auslastung $z \in [0, 1]$: $\psi(z) = \tfrac{{L}}{{e}} \left(\tfrac{{U e}}{{L}}\right)^z$, mit $L = {C.LO:g}$, $U = {C.HI:g}$; $j$ wird angenommen, wenn $r_j \ge \sum_i a_{{ij}}\, \psi(z_i)$. Für **eine** Ressource erreicht sie im schlechtesten Fall mindestens den Anteil $1/(\ln(U/L) + 1)$ des Optimums ({A.exp_guarantee():.3f} bei $U/L = {C.HI / C.LO:g}$).

**Literatur (nicht nachgebaut; Auszüge per Websuche gesehen, Volltexte nicht eingesehen).** S. Agrawal, Z. Wang, Y. Ye: *A Dynamic Near-Optimal Algorithm for Online Linear Programming* (arXiv 0911.2974). S. Balseiro, H. Lu, V. Mirrokni: *The Best of Many Worlds: Dual Mirror Descent for Online Allocation Problems* (arXiv 2011.10124). N. Buchbinder, J. Naor: *The Design of Competitive Online Algorithms via a Primal-Dual Approach* (2009). Y. Zhou, D. Chakrabarty, R. Lukose: *Budget Constrained Bidding in Keyword Auctions and Online Knapsack Problems* (WWW 2008). Die Regeln hier sind vereinfachte Fassungen in der Art dieser Arbeiten; belegt sind die Zahlen durch vollständiges Durchrechnen der Folgen.
        """
    )

st.markdown("---")
st.caption(
    "Verwandte Demos: [Ski-Rental](https://github.com/sebastian-hanisch/ski-rental-demo), [Paging](https://github.com/sebastian-hanisch/paging-demo) und [Online-Packen](https://github.com/sebastian-hanisch/online-packen-demo) (Stücke 1 bis 3 der Reihe), "
    "Buchungsannahme mit Gewichtslimit (`uld-buchungsannahme-demo`, eine Ressource und bekannte Verteilung), Slot-Vergabe mit Littlewood (`revenue-management-demo`), "
    "[Online-Matching](https://sebastianhanisch-online-matching-demo.streamlit.app/) (Zuordnen ohne Kenntnis der Zukunft)."
)
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Online-Algorithmen: Entscheiden ohne Zukunft](https://sebastianhanisch.net/konzepte-online-algorithmen.html)."
)
