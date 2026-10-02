import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


EXCEL_FILE = "data/Output_Emissions_data_unified.xlsx"
SHEET = "Unified"
SHARED_SCALES = True
OUTPUT_FILES = {
    "Iron & Steel": "plots/production_intensity_iron_steel.html",
    "Cement": "plots/production_intensity_cement.html",
}

COUNTRIES = {
    "United States":  (1,  "#2f6db3"),
    "European Union": (7,  "#d4632d"),
    "China":          (19, "#23a079"),
    "India":          (13, "#b3478a"),
}

SECTORS = {"Iron & Steel": (0, 2), "Cement": (3, 5)}
HEADLINES = {
    "Iron & Steel": "Emissions Intensity and Production Levels of Iron & Steel",
    "Cement": "Emissions Intensity and Production Levels of Cement",
}

PAPER, INK, INK_SOFT, MUTED, RULE = "#ffffff", "#1d1d1b", "#55524c", "#8d8a83", "#e4e0d6"
BAR = "#d9d4c7"
BODY_FONT = "Calibri, Candara, Segoe, 'Segoe UI', Optima, Arial, sans-serif"
HEAD_FONT = BODY_FONT

# ----------------------------------------------------------------- data
raw = pd.read_excel(EXCEL_FILE, sheet_name=SHEET, header=None, skiprows=5, nrows=21)
raw.index = raw[0].astype(int)


def series(col, off):
    return pd.to_numeric(raw[col + off], errors="coerce")


# ----------------------------------------------------------------- figure
names = list(COUNTRIES)
cell = {n: (i // 2 + 1, i % 2 + 1) for i, n in enumerate(names)}


def nice_step(top, ticks=4):
    """A round tick step (1, 2, 2.5 or 5 x 10^n) giving roughly `ticks` gridlines up to `top`."""
    raw_step = top / ticks
    mag = 10 ** np.floor(np.log10(raw_step))
    return next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw_step)


def axis_ids(i):
    """Plotly axis names for panel i: (x, y-left, y-right)."""
    x = "x" if i == 0 else f"x{i + 1}"
    return x, f"y{2 * i + 1}".replace("y1", "y") if i == 0 else f"y{2 * i + 1}", f"y{2 * i + 2}"


def header(sector):
    return [
        dict(xref="paper", yref="paper", x=0, y=1.19, xanchor="left", showarrow=False,
             text=HEADLINES[sector], font=dict(family=HEAD_FONT, size=22, color=INK)),
        dict(xref="paper", yref="paper", x=0, y=-0.1, xanchor="left", showarrow=False,
             text="Sources: USGS, EPA, EEA, Eurofer, CEADS, CEEW, NITI Aayog.",
             font=dict(size=10.5, color=MUTED)),
    ]


def build_figure(sector, p_off, i_off):
    fig = make_subplots(
        rows=2, cols=2, specs=[[{"secondary_y": True}] * 2] * 2,
        horizontal_spacing=0.11, vertical_spacing=0.16,
    )
    prod_max = np.ceil(np.nanmax([series(c, p_off).max() for c, _ in COUNTRIES.values()]) * 1.08 / 500) * 500
    int_max = np.ceil(np.nanmax([series(c, i_off).max() for c, _ in COUNTRIES.values()]) * 1.1)
    annotations, shapes = [], []

    for i, (name, (col, colour)) in enumerate(COUNTRIES.items()):
        r, c = cell[name]
        xref, yref_left, yref_right = axis_ids(i)
        india_cement = name == "India" and sector == "Cement"

        # production bars
        prod = series(col, p_off).dropna()
        fig.add_trace(go.Bar(
            x=prod.index, y=prod.values, name="Production",
            marker=dict(color=BAR, line_width=0),
            hovertemplate="Production  <b>%{y:,.0f} Mt</b><extra></extra>",
            showlegend=False,
        ), row=r, col=c, secondary_y=False)

        # intensity line (main)
        inten = series(col, i_off)
        main = inten.loc[:2018] if india_cement else inten
        main = main.dropna()
        fig.add_trace(go.Scatter(
            x=main.index, y=main.values, mode="lines", name="Intensity",
            line=dict(color=colour, width=2.6, shape="linear"),
            hovertemplate="Intensity  <b>%{y:.2f}</b> t CO₂e/t<extra></extra>",
            showlegend=False,
        ), row=r, col=c, secondary_y=True)

        # caveated points: India cement process-only years
        if india_cement:
            extra = inten.loc[2019:2020]
            fig.add_trace(go.Scatter(
                x=extra.index, y=extra.values,
                mode="markers",
                line=dict(color=colour, width=1.6, dash="dot"),
                marker=dict(size=7, color=PAPER, line=dict(color=colour, width=1.6)),
                hovertemplate="Intensity  <b>%{y:.2f}</b> (process emissions only)<extra></extra>",
                showlegend=False,
            ), row=r, col=c, secondary_y=True)
            annotations.append(dict(xref=xref, yref=yref_right, x=2020.6, y=extra.max(), text="process only",
                                    showarrow=False, xanchor="left", font=dict(size=10, color=MUTED)))

        
        fig.add_trace(go.Scatter(
            x=[main.index[0], main.index[-1]], y=[main.iloc[0], main.iloc[-1]], mode="markers",
            marker=dict(size=8, color=colour, line=dict(color=PAPER, width=2)),
            hoverinfo="skip", showlegend=False,
        ), row=r, col=c, secondary_y=True)
        for yr, strong in ((main.index[0], False), (main.index[-1], True)):
            annotations.append(dict(
                xref=xref, yref=yref_right, x=yr, y=main[yr], yshift=13, showarrow=False,
                text=f"<b>{main[yr]:.2f}</b>" if strong else f"{main[yr]:.2f}",
                font=dict(size=11, color=INK if strong else INK_SOFT)))

        # country name (panel title)
        annotations.append(dict(xref=f"{xref} domain", yref=f"{yref_left} domain", x=0, y=1.13, xanchor="left",
                                text=f"<b>{name}</b>", showarrow=False,
                                font=dict(family=HEAD_FONT, size=16, color=INK)))

    ranges = {}
    for i, (col, _) in enumerate(COUNTRIES.values()):
        _, yl, yr_ = axis_ids(i)
        left, right = f"yaxis{'' if yl == 'y' else yl[1:]}", f"yaxis{yr_[1:]}"
        if SHARED_SCALES:
            p_top, p_step, i_top, i_step = prod_max, 500, int_max, 1
        else:
            p_step = nice_step(series(col, p_off).max())
            p_top = np.ceil(series(col, p_off).max() * 1.08 / p_step) * p_step
            i_step = nice_step(series(col, i_off).max())
            i_top = np.ceil(series(col, i_off).max() * 1.1 / i_step) * i_step
        ranges[f"{left}.range"], ranges[f"{left}.dtick"] = [0, p_top], p_step
        ranges[f"{right}.range"], ranges[f"{right}.dtick"] = [0, i_top], i_step

    fig.update_layout(annotations=annotations + header(sector), shapes=shapes)
    fig.update_layout(ranges)

    # ------------------------------------------------------------- styling
    fig.update_layout(
        height=820, margin=dict(l=70, r=70, t=150, b=90),
        paper_bgcolor=PAPER, plot_bgcolor=PAPER, bargap=0.28,
        font=dict(family=BODY_FONT, size=12, color=INK_SOFT),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=RULE, font=dict(family=BODY_FONT, size=12, color=INK)),
    )
    fig.update_xaxes(range=[2004.3, 2025.7], tickvals=[2005, 2010, 2015, 2020, 2025], showgrid=False,
                     showline=True, linecolor=RULE, ticks="", tickfont=dict(color=MUTED),
                     showspikes=True, spikemode="across", spikethickness=1, spikecolor=MUTED, spikedash="solid")
    fig.update_yaxes(secondary_y=False, gridcolor=RULE, zeroline=False, tickformat=",", tickfont=dict(color=MUTED),
                     title_text="Production (Mt)", title_font=dict(size=11, color=MUTED))
    for i, (name, (_, colour)) in enumerate(COUNTRIES.items()):
        r, c = cell[name]
        fig.update_yaxes(secondary_y=True, row=r, col=c, showgrid=False, zeroline=False,
                         tickfont=dict(color=colour), title_text="Emissions Intensity (t CO₂e/t)",
                         title_font=dict(size=11, color=colour))
    return fig


os.makedirs("plots", exist_ok=True)
for sector, (p_off, i_off) in SECTORS.items():
    fig = build_figure(sector, p_off, i_off)
    out = OUTPUT_FILES[sector]
    fig.write_html(out, include_plotlyjs=True, full_html=True,
                   config={"displaylogo": False, "responsive": True,
                           "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]})
    print("saved", out)
