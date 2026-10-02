
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openpyxl.utils import column_index_from_string
 
# ---------------- settings ----------------
# Both series come from the "Unified" sheet of the same workbook
EXCEL_FILE = "data/Output_Emissions_data_unified.xlsx"
SHEET = "Unified"
 
# Excel column letters: (previous = EEA-based intensity, new = facility intensity)
COLUMNS = {"Iron & Steel": ("J", "K"),
           "Cement":       ("N", "O")}
# Production (bars, left axis)
PRODUCTION = {"Iron & Steel": "H",
              "Cement":       "L"}
 
OUTPUT_HTML = "plots/eu_intensity_old_vs_new.html"
OUTPUT_CSV = "eu_intensity_old_vs_new.csv"
 
OLD_LABEL, NEW_LABEL = "Previous (EEA)", "New (EU ETS facilities)"
# ------------------------------------------
 
PAPER, INK, INK_SOFT, MUTED, RULE = "#ffffff", "#1d1d1b", "#55524c", "#8d8a83", "#e4e0d6"
OLD_COLOUR, NEW_COLOUR = "#8d8a83", "#d4632d"   # grey = previous, EU orange = new
BODY_FONT = "Calibri, Candara, Segoe, 'Segoe UI', Optima, Arial, sans-serif"
 
 
# 1-2. Read both series (same rows as the chart script: 2005-2025)
raw = pd.read_excel(EXCEL_FILE, sheet_name=SHEET, header=None, skiprows=5, nrows=21)
raw.index = raw[0].astype(int)
col = lambda letter: pd.to_numeric(raw[column_index_from_string(letter) - 1], errors="coerce")
old = pd.DataFrame({s: col(o) for s, (o, n) in COLUMNS.items()})
new = pd.DataFrame({s: col(n) for s, (o, n) in COLUMNS.items()})
prod = pd.DataFrame({s: col(letter) for s, letter in PRODUCTION.items()})
 
# 3. Comparison table
years = list(raw.index)
table = pd.DataFrame(index=pd.Index(years, name="year"))
for s in COLUMNS:
    table[f"{s} | {OLD_LABEL}"] = old[s].reindex(years)
    table[f"{s} | {NEW_LABEL}"] = new[s].reindex(years)
    table[f"{s} | diff %"] = (table[f"{s} | {NEW_LABEL}"] / table[f"{s} | {OLD_LABEL}"] - 1) * 100
table.to_csv(OUTPUT_CSV)
print(table.round(3).to_string())
 
for s in COLUMNS:
    d = table[f"{s} | diff %"].dropna()
    if len(d):
        print(f"\n{s}: {len(d)} overlapping years, mean diff {d.mean():+.1f}%, "
              f"largest {d.abs().max():.1f}% in {int(d.abs().idxmax())}")
 
# 4. Figure: per sector, production bars (left axis) with both intensity lines
#    overlaid (right axis)
BAR = "#d9d4c7"
sectors = list(COLUMNS)
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.13,
                    specs=[[{"secondary_y": True}] * 2])
 
for c, s in enumerate(sectors, start=1):
    p = prod[s].dropna()
    fig.add_trace(go.Bar(
        x=p.index, y=p.values, name="Production", legendgroup="prod", showlegend=(c == 1),
        marker=dict(color=BAR, line_width=0),
        hovertemplate="Production  <b>%{y:,.0f} Mt</b><extra></extra>",
    ), row=1, col=c, secondary_y=False)
 
    for label, series, colour, dash in ((OLD_LABEL, old[s], OLD_COLOUR, "dash"),
                                        (NEW_LABEL, new[s], NEW_COLOUR, "solid")):
        v = series.dropna()
        fig.add_trace(go.Scatter(
            x=v.index, y=v.values, mode="lines+markers", name=label, legendgroup=label,
            showlegend=(c == 1),
            line=dict(color=colour, width=2.6 if label == NEW_LABEL else 2, dash=dash),
            marker=dict(size=5, color=colour),
            hovertemplate=f"{label}  <b>%{{y:.3f}}</b> t CO₂e/t<extra></extra>",
        ), row=1, col=c, secondary_y=True)
 
    # sector title above each panel
    xa = "x" if c == 1 else f"x{c}"
    ya = "y" if c == 1 else "y3"
    fig.add_annotation(xref=f"{xa} domain", yref=f"{ya} domain", x=0, y=1.1, xanchor="left",
                       showarrow=False, text=f"<b>{s}</b>", font=dict(size=16, color=INK))
 
    # scales: production from 0, intensity from 0 with headroom
    p_top = prod[s].max() * 1.1
    i_top = np.nanmax([old[s].max(), new[s].max()]) * 1.15
    fig.update_yaxes(row=1, col=c, secondary_y=False, range=[0, p_top], gridcolor=RULE, zeroline=False,
                     tickformat=",", tickfont=dict(color=MUTED),
                     title_text="Production (Mt)", title_font=dict(size=11, color=MUTED))
    fig.update_yaxes(row=1, col=c, secondary_y=True, range=[0, i_top], showgrid=False, zeroline=False,
                     tickfont=dict(color=NEW_COLOUR),
                     title_text="Emissions intensity (t CO₂e / t)", title_font=dict(size=11, color=NEW_COLOUR))
 
fig.update_layout(
    title=dict(text="European Union production and emissions intensity: facility data vs EEA",
               x=0.5, xanchor="center", font=dict(size=22, color=INK)),
    height=520, margin=dict(l=70, r=70, t=120, b=60),
    paper_bgcolor=PAPER, plot_bgcolor=PAPER, bargap=0.28,
    font=dict(family=BODY_FONT, size=12, color=INK_SOFT),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#ffffff", bordercolor=RULE, font=dict(family=BODY_FONT, size=12, color=INK)),
    legend=dict(orientation="h", x=1, xanchor="right", y=1.12),
)
fig.update_xaxes(range=[2004.3, 2025.7], tickvals=[2005, 2010, 2015, 2020, 2025], showgrid=False,
                 showline=True, linecolor=RULE, tickfont=dict(color=MUTED))
 
os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
fig.write_html(OUTPUT_HTML, include_plotlyjs=True, full_html=True,
               config={"displaylogo": False, "responsive": True})
print(f"\nsaved {OUTPUT_HTML} and {OUTPUT_CSV}")
