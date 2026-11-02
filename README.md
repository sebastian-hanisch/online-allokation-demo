# Online-Allokation – Buchungen mit Preisen statt mit Glück annehmen – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-online-allokation-demo.streamlit.app/)**

Viertes Stück der Reihe **Online-Algorithmen** („Entscheiden ohne Kenntnis der Zukunft“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, unabhängiger Ast neben [paging-demo](https://github.com/sebastian-hanisch/paging-demo) und [online-packen-demo](https://github.com/sebastian-hanisch/online-packen-demo) unter der Wurzel [ski-rental-demo](https://github.com/sebastian-hanisch/ski-rental-demo).
Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Konzept, **Preise für knappen Platz**, an einem wachsenden Beispiel: von einer Strecke (dem Online-Rucksack) über ein Netz mit mehreren Teilstrecken bis zu der Frage, was die Reihenfolge der Buchungen kostet.
Kante zum Vorgänger: Ski-Rental entscheidet **eine** Anschaffung, hier konkurrieren **viele Buchungen** um den Platz **mehrerer Strecken**, und der Wert der Entscheidung hängt an Preisen, die man nicht kennt.

**Verwandte bestehende Demos:** `uld-buchungsannahme-demo` (Luftfracht: **eine** Ressource, bekannte stationäre Verteilung, exakte dynamische Programmierung; dort stehen „parallele Volumengrenze“ und „Prognoseunschärfe“ unter *Bewusst nicht umgesetzt*, hier sind sie das Thema), `revenue-management-demo` (Seefracht: zwei Klassen, Littlewood-Formel), `nahverkehr-demo` (Annahme gegen ein Rückblick-Orakel), `online-matching-demo` (Zuordnen ohne Kenntnis der Zukunft).

## Warum dieses Problem

Buchungsanfragen für Laderaum auf mehreren Teilstrecken eines Netzes kommen nacheinander, jede wird sofort angenommen oder abgelehnt, solange der Platz auf allen ihren Strecken reicht. Wer die **Preise** des knappen Platzes kennt (die Schattenpreise einer linearen Optimierung), entscheidet fast optimal: Er nimmt an, was mehr wert ist als der Platz kostet. Die Kernfrage: **Was kann man ohne diese Preise tun, und was kostet es, wenn die Reihenfolge ungünstig ist?**

## Modell

d Teilstrecken mit Kapazität b_i, n Buchungen. Jede Buchung nutzt eine oder (zu 50 %) zwei Teilstrecken, je eine Einheit, und hat einen **Wert je Einheit** gleichverteilt zwischen 1 und 10 (U/L = 10); ihr Wert ist der Wert je Einheit mal Zahl der Strecken. Die Kapazität je Strecke ist der Anteil „Knappheit“ der Nachfrage dieser Strecke (abgerundet, mindestens 1). **Referenz:** die LP-Relaxation der ganzen Folge (obere Schranke des Optimums) mit ihren **Schattenpreisen**; eine Buchung wird bei Preisen p angenommen, wenn ihr Wert die Summe der Preise ihrer Strecken übersteigt.
Fünf Regeln: **FCFS** (annehmen, solange es passt), **Orakel-Preise** (Schattenpreise der ganzen Folge: online unmöglich, nur zum Vergleich), **Preislernen** (LP auf dem bisher Gesehenen, Preise bei Verdopplung erneuert; die ersten 5 % lehnt es ab; in der Art von Agrawal/Wang/Ye), **Dual-Gradient** (Preis steigt bei Verbrauch über dem Plan; in der Art von Balseiro/Lu/Mirrokni), **exponentielle Preisfunktion** (Preis wächst exponentiell mit der Auslastung, verteilungsfrei; in der Art von Zhou/Chakrabarty/Lukose und Buchbinder/Naor). Alle fünf sind **vereinfachte eigene Fassungen** ohne die in den Arbeiten bewiesenen Konstanten. Formeln im 📐-Expander der App.

## Methodik

| Abschnitt der App | Was gerechnet wird |
|---|---|
| Ergebnis | alle Regeln auf der gewählten Instanz und Reihenfolge; Anteil des LP-Optimums, Kurve des Werts über die Zeit, Auslastung, Ablauf der ersten 20 Buchungen |
| Experiment 1 | Knappheit 0,1 / 0,3 / 0,6 × drei Reihenfolgen, 4 Teilstrecken, 1000 Buchungen, Mittel über fünf feste Seeds |
| Experiment 2 | n = 100 bis 4000 Buchungen (zufällig, Knappheit 0,3) |
| Experiment 3 | d = 1 bis 8 Teilstrecken (zufällig, Knappheit 0,3) |
| Experiment 4 | Schrittweite des Dual-Gradient-Verfahrens, Faktor 0,1 bis 10 |
| Experiment 5 | eine Strecke, schlechteste Reihenfolge: die exponentielle Preisfunktion gegen ihre Garantie |

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen in `tests/test_claims.py` nachgerechnet. „Anteil“ steht für Wert geteilt durch den LP-Wert; Tabellen sind Mittel über fünf feste Seeds, soweit nicht ein Preset genannt ist (Preset: ein Seed, 2000 Buchungen).

| Frage | Befund |
|---|---|
| Netz mit vier Strecken, zufällige Reihenfolge, Knappheit 0,3 (Preset)? | FCFS 0,624, Orakel-Preise 0,997, **Preislernen 0,926**, Dual-Gradient 0,939, exponentiell 0,743; Preislernen nimmt 562, FCFS 608 von 2000 Buchungen an. |
| Richtige Preise? | Mit den Orakel-Preisen erreicht dieselbe Annahmeregel **0,98 bis 1,00** des Optimums (Mittel über fünf Seeds, einzelne Läufe ab 0,97) in den drei Reihenfolgen und drei Knappheiten von Experiment 1. Was fehlt, ist das Wissen über die Preise; die Orakel-Preise nutzen die ganze Folge und sind online nicht verfügbar. |
| FCFS? | Zufällig 0,590 / 0,640 / 0,755 bei Knappheit 0,1 / 0,3 / 0,6; in der schlechtesten der drei Reihenfolgen (aufsteigend, niedrige Werte zuerst) **0,153** / 0,272 / 0,506; absteigend sortiert mindestens 0,999. |
| Preislernen in absteigender Reihenfolge? | **0,000** bei Knappheit 0,1 bis 0,6 (vier Strecken, n = 1000): Die ersten Buchungen sind die wertvollsten, die gelernten Preise liegen über allen späteren Werten, und nichts wird mehr angenommen. Bei Knappheit 1,0 (vier Strecken) liegt der Wert im Mittel bei 0,23, und auch bei vielen Strecken mit kleinem n ist er größer als 0. Zufällig 0,845 / 0,871 / 0,871. |
| Exponentielle Preisfunktion? | In **jeder** Reihenfolge ein Wert über 0,3: schlechteste der drei Reihenfolgen 0,313 / 0,381 / 0,547, zufällig 0,686 / 0,757 / 0,869 (bei Knappheit 0,1 und 0,3 deutlich unter Preislernen, bei 0,6 gleichauf), absteigend 0,992 / 0,942 / 0,879. |
| Dual-Gradient? | Dazwischen: zufällig 0,770 / 0,918 / 0,960, aufsteigend 0,313 / 0,500 / 0,670, absteigend 0,995 / 0,793 / 0,839. |
| Wächst n (zufällig, Knappheit 0,3)? | n = 100 / 400 / 1000 / 4000: Preislernen 0,746 / 0,862 / 0,871 / **0,921**, Dual-Gradient 0,788 / 0,858 / 0,918 / **0,955**, Orakel 0,949 / 0,986 / 0,994 / 0,999; exponentiell 0,746 / 0,735 / 0,757 / 0,756 und FCFS 0,659 / 0,615 / 0,640 / 0,636 **bleiben flach**. |
| Mehr Teilstrecken (n = 1000)? | d = 1 / 2 / 4 / 8: Preislernen 0,895 / 0,927 / 0,871 / 0,856, Dual-Gradient 0,967 / 0,947 / 0,918 / **0,847**, exponentiell 0,758 / 0,735 / 0,757 / 0,748, FCFS 0,640 / 0,619 / 0,640 / 0,639. |
| Schrittweite des Dual-Gradient (Faktor 0,1 / 0,3 / 1 / 3 / 10)? | zufällig 0,659 / 0,770 / 0,918 / **0,954** / 0,920; aufsteigend 0,272 / 0,341 / 0,500 / 0,583 / **0,627**: Große Schritte helfen in der schlechten Reihenfolge und schaden im Normalfall nach einem Optimum bei Faktor 3. |
| Eine Strecke, aufsteigende Reihenfolge (die schlechteste der drei getesteten; Knappheit 0,1 / 0,3 / 0,6)? | Die exponentielle Preisfunktion erreicht **0,320** / 0,385 / 0,553; die Garantie für eine Strecke ist 1/(ln 10 + 1) = **0,3028**. FCFS 0,153 / 0,277 / 0,513, Preislernen 0,201 / 0,330 / 0,575. |
| Reichlich Platz (Knappheit 1,0, Preset)? | FCFS 1,000 (nimmt alle 2000 an); die Preisregeln lehnen ohne Not Buchungen ab: Preislernen 0,940 (1823 angenommen), exponentiell 0,925. |

## Ehrliche Grenzen

- Die Demo ist **nur an erfundenen Buchungen** geprüft; die Werte je Einheit sind gleichverteilt, das Netz ist ein Zufallsmodell.
- **Referenz:** der LP-Wert ist eine obere Schranke des ganzzahligen Optimums (auf 20 kleinen Instanzen höchstens 5 % darüber, im Test gegen CP-SAT). Die Anteile sind deshalb untere Schranken der wahren Anteile.
- Die Regeln sind **vereinfachte Fassungen in der Art** der genannten Arbeiten, ohne deren bewiesene Konstanten und Schemata. Die Garantie 1/(ln(U/L) + 1) gilt in der Quelle für **eine** Ressource; für mehrere Strecken gibt es hier **keinen geprüften Wert**, und die App behauptet keinen.
- Die **Primärquellen wurden nicht eingesehen**; es liegen nur Auszüge der Websuche vor (**offen**). Deshalb gibt es keinen Literaturtest.
- Preislernen lehnt die ersten 5 % ab, solange es lernt; das Verhalten bei kleinem n (unter 100) ist entsprechend schwach.
- Die Schattenpreise der LP sind nicht immer eindeutig; die Orakel-Preise nehmen eine Lösung des Solvers.
- Nicht modelliert: mehrere Einheiten je Buchung, Stornos, Overbooking, echte Preissetzung mit Kundenverhalten.

## Verifikation

- **Umfang:** 78 Tests (siehe `pytest --collect-only -q tests`), rund zwei Minuten lokal.
- **Kern:** alle fünf Regeln auf der Mini-Instanz von Hand (eine Strecke, Kapazität 2, Werte 3, 1, 2: FCFS 4, Optimum 5, Orakel 5, exponentiell 5, Dual-Gradient 5, Preislernen 0) und auf einer Zwei-Strecken-Instanz von Hand; Preis-Endpunkte; Randfälle.
- **Orakel** (`tests/test_oracle_online_allokation.py`): LP gegen das **ganzzahlige Optimum (CP-SAT)** auf 20 kleinen Instanzen; das **duale LP** als zweites, getrennt formuliertes Programm (starke Dualität, schwache Dualität für beliebige Preise); FCFS und exponentielle Preisfunktion gegen zweite, schleifenweise Fassungen.
- **Eigenschaften** (`tests/test_eigenschaften_online_allokation.py`): nie mehr angenommen als der Platz erlaubt (unabhängiger Prüfer), nie mehr Wert als das LP; **Online-Eigenschaft** (andere spätere Buchungen ändern die früheren Entscheidungen nicht); das LP wächst mit Kapazität und Buchungen; Orakel-Preise 0,97 bis 1,0 in jeder Reihenfolge; FCFS absteigend ≥ 0,98; Preislernen absteigend 0; exponentielle Preisfunktion bei einer Strecke ≥ Garantie − 0,02.
- **Literatur:** kein Referenzwert-Test (siehe oben, **offen**).
- **Verdikte** (`tests/test_verdicts.py`): jede Zahl und jede Verzweigung der Texte. **Claims** (`tests/test_claims.py`): jede Zahl dieser README.
- **Presets, Layout, Oberfläche:** vollständig, Werte in den Reglergrenzen; Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben; AppTest-Rauchtest (jeder Button, jeder Regler an beiden Grenzen, jede Auswahl jedes Auswahlfelds); Footer; Laufzeit-Importe.
- **Browser:** im Desktop-Browser durchgeklickt (alle sechs Presets, Seitenleiste, Diagramme). Nicht mit echtem Touch-Gerät getestet.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Ergebnis, Kernfrage, fünf Experimente, Grenzen, Formeln |
| `requirements-dev.txt` | Laufzeit plus pytest und ortools (nur für das Orakel) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; `scipy` für das LP) |
| `ola_algorithm.py` | Kern: LP und Schattenpreise, die fünf Regeln, Prüfer, Garantie der Preisfunktion |
| `ola_constants.py` | Regler-Grenzen, feste Annahmen, Experimente, Farben, Presets |
| `ola_evaluation.py` | Kennzahlen, Ablauftabelle, Experimente, Verdikte |
| `ola_layout.py` | Fester Kopf (Stylesheet) |
| `ola_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `ola_scenario.py` | Netz und Buchungen, Reihenfolgen |
| `ola_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Kern, Randfälle, Orakel, Eigenschaften, Verdikte, Claims, Presets, Layout, Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Nachbau der Algorithmen** aus den Arbeiten (bewiesene Konstanten, Verdopplungsschemata mit Schranke, Dual Mirror Descent mit Regret-Garantie).
- **Bekannte Verteilung und exakte Rechnung** für eine Ressource: `uld-buchungsannahme-demo`.
- **Mehrere Einheiten je Buchung**, Stornos, Overbooking, echte Preissetzung, mehrere Kundenklassen mit Wahlverhalten.
- **Vorhersagen** der Nachfrage (Preise aus einer Vorhersage): ein eigenes Stück der Reihe.
- **Echte Buchungsdaten** und PDF-Export.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, SciPy und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Online-Algorithmen: Entscheiden ohne Zukunft](https://sebastianhanisch.net/konzepte-online-algorithmen.html).
