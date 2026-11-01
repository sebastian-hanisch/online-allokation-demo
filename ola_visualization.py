"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import ola_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.3), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_fractions(fractions: dict, selected: str):
    names = list(C.REGELN)
    colors = [C.COLORS[n] if n == selected else "rgba(150,150,150,0.55)" for n in names]
    fig = go.Figure(go.Bar(x=names, y=[fractions[n] for n in names], marker_color=colors, text=[f"{fractions[n] * 100:.1f} %" for n in names], textposition="outside",
                           hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    fig.update_yaxes(title_text="Wert geteilt durch LP-Optimum", range=[0, 1.12])
    return _base(fig, height=320)


def build_curves(curves: dict, selected: str):
    """Kumulierter Wert geteilt durch das LP-Optimum über den Anteil der eingetroffenen Buchungen."""
    fig = go.Figure()
    for rule, (xs, ys) in curves.items():
        sel = rule == selected
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=rule, line=dict(color=C.COLORS[rule], width=4 if sel else 1.8, dash="solid" if sel else "dot"),
                                 hovertemplate="%{x:.0%} der Buchungen: %{y:.3f}<extra>" + rule + "</extra>"))
    fig.update_xaxes(title_text="Anteil der eingetroffenen Buchungen", tickformat=".0%")
    fig.update_yaxes(title_text="Wert bisher / LP-Optimum", range=[0, 1.05])
    return _base(fig)


def build_utilization(util: list[float]):
    xs = [f"Strecke {i + 1}" for i in range(len(util))]
    colors = [C.COLORS["Preislernen"] if u >= 0.9 else "#d97706" if u >= 0.5 else "#c0392b" for u in util]
    fig = go.Figure(go.Bar(x=xs, y=[u * 100 for u in util], marker_color=colors, hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    fig.update_yaxes(title_text="Auslastung (%)", range=[0, 105])
    return _base(fig, height=260)


def build_heat(rows: list[dict]):
    """Zeilen: Knappheit und Reihenfolge; Spalten: Regel; Zahl: Wert / LP-Optimum."""
    labels = [f"Knappheit {r['Knappheit']:g}, {r['Reihenfolge']}" for r in rows]
    z = [[r[x] for x in C.REGELN] for r in rows]
    fig = go.Figure(go.Heatmap(z=z, x=list(C.REGELN), y=labels, text=[[f"{v:.3f}" for v in row] for row in z], texttemplate="%{text}", colorscale="RdYlGn", zmin=0.0, zmax=1.0,
                               showscale=False, hovertemplate="%{y}, %{x}: %{z:.3f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=420)


def _lines(rows, key, names, xtitle, height=340):
    fig = go.Figure()
    xs = [str(r[key]) for r in rows]
    for rule in names:
        fig.add_trace(go.Scatter(x=xs, y=[r[rule] for r in rows], mode="lines+markers", name=rule, line=dict(color=C.COLORS[rule], width=3),
                                 hovertemplate=f"{key} = " + "%{x}: %{y:.3f}<extra>" + rule + "</extra>"))
    fig.update_xaxes(title_text=xtitle, type="category")
    fig.update_yaxes(title_text="Wert geteilt durch LP-Optimum", range=[0, 1.05])
    return _base(fig, height=height)


def build_growth(rows):
    return _lines(rows, "n", C.REGELN, "Zahl der Buchungen n")


def build_resources(rows):
    return _lines(rows, "d", C.REGELN, "Teilstrecken d")


def build_steps(rows):
    fig = go.Figure()
    xs = [f"{r['Faktor']:g}" for r in rows]
    fig.add_trace(go.Scatter(x=xs, y=[r["zufällig"] for r in rows], mode="lines+markers", name="zufällige Reihenfolge", line=dict(color=C.COLORS["Dual-Gradient"], width=3),
                             hovertemplate="Faktor %{x}: %{y:.3f}<extra>zufällig</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["aufsteigend"] for r in rows], mode="lines+markers", name="aufsteigende Reihenfolge", line=dict(color=C.COLORS["exponentiell"], width=3),
                             hovertemplate="Faktor %{x}: %{y:.3f}<extra>aufsteigend</extra>"))
    fig.update_xaxes(title_text="Schrittweite (Faktor auf HI/√n)", type="category")
    fig.update_yaxes(title_text="Wert geteilt durch LP-Optimum", range=[0, 1.05])
    return _base(fig)


def build_guarantee(rows):
    xs = [f"Knappheit {r['Knappheit']:g}" for r in rows]
    fig = go.Figure()
    for rule in ("FCFS", "Preislernen", "exponentiell"):
        fig.add_trace(go.Bar(x=xs, y=[r[rule] for r in rows], name=rule, marker_color=C.COLORS[rule], hovertemplate="%{x}: %{y:.3f}<extra>" + rule + "</extra>"))
    fig.add_hline(y=rows[0]["Garantie"], line=dict(color=C.COLOR_REF, dash="dash"), annotation_text=f"Garantie für eine Strecke: {rows[0]['Garantie']:.3f}", annotation_position="top left")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Wert geteilt durch LP-Optimum", range=[0, 0.8])
    return _base(fig)
