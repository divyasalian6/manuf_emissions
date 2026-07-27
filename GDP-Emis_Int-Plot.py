"""Interactive plotting helpers for the ICUE panel (Plotly)."""
import colorsys
import plotly.io as pio

# Shared theme + global font. Setting the font on the default template applies
# it to every figure (titles, axes, legend, hover) without repeating it per
# chart. The sans-serif fallback covers viewers without Calibri installed.
FONT_FAMILY = "Calibri, sans-serif"
pio.templates.default = "plotly_white"
pio.templates["plotly_white"].layout.font.family = FONT_FAMILY
pio.templates["plotly_white"].layout.font.weight = "bold"
# Keep the tick numbers/labels on the axes at normal weight (bold ticks read as
# clutter). Set on the template so it covers every axis in every subplot.
pio.templates["plotly_white"].layout.xaxis.tickfont.weight = "normal"
pio.templates["plotly_white"].layout.yaxis.tickfont.weight = "normal"
pio.templates["plotly_white"].layout.legend.font.size = 16
COUNTRY_ORDER = ["China", "United States", "EU", "India"]
COUNTRY_COLORS = {
    "China": "#c0392b",
    "United States": "#2c3e50",
    "EU": "#2980b9",
    "India": "#e67e22",
}

# Indicator names used by the chart functions below.
GDP_IND = "GDP (constant 2015 US$)"
INTENSITY_IND = "Carbon intensity of GDP (kg CO2e per constant 2015 US$ of GDP)"
MFG_SHARE_IND = "Manufacturing, value added (% of GDP)"

# Every chart uses one hue: translucent bars with a darker, more saturated line
# of the same hue on top. BAR_OPACITY sets the bar translucency; _darken()
# derives the line shade. GRID_COLOR is the single base hue for the grid.
BAR_OPACITY = 0.45
GRID_COLOR = "#4c78a8"

# --- Manufacturing branch composition from the WDI extract  ---
MVA_BRANCHES = {
    "Chemicals (% of value added in manufacturing)": "Chemicals",
    "Food, beverages and tobacco (% of value added in manufacturing)": "Food, bev. & tobacco",
    "Machinery and transport equipment (% of value added in manufacturing)": "Machinery & transport",
    "Textiles and clothing (% of value added in manufacturing)": "Textiles & clothing",
    "Other manufacturing (% of value added in manufacturing)": "Other manufacturing",
}
MVA_BRANCH_COLORS = {
    "Chemicals": "#4c78a8",
    "Food, bev. & tobacco": "#f58518",
    "Machinery & transport": "#54a24b",
    "Textiles & clothing": "#e45756",
    "Other manufacturing": "#b3aca6",
}
MVA_BRANCH_ORDER = list(MVA_BRANCH_COLORS)

def _darken(hex_color, sat=1.3, val=0.7):
    """Return a darker, more saturated variant of a hex color.

    Used for the line that overlays the translucent bars, so both share a hue
    but the line reads clearly on top. Boosts saturation and cuts brightness.
    """
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, s, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(hue, min(1.0, s * sat), v * val)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def series(df, indicator, countries=None, source=None):
    """Return a tidy slice of the panel for one indicator, ready to plot.

    Filters to the given `indicator` (and optionally a subset of `countries`
    and a single `source`), then sorts by country and year so lines draw
    cleanly. Does not aggregate — one row per country-year is assumed.
    """
    mask = df["indicator"] == indicator
    if countries is not None:
        mask &= df["country"].isin(countries)
    if source is not None:
        mask &= df["source"] == source
    out = df.loc[mask, ["country", "year", "value", "unit", "source"]]
    return out.sort_values(["country", "year"]).reset_index(drop=True)


def save(fig, path):
    """Write a fully self-contained interactive HTML file.

    include_plotlyjs=True embeds the Plotly library in the file (~3.5 MB), so it
    renders offline and on networks that block CDNs. Switch to 'cdn' for a much
    smaller file if you know the viewer always has internet.
    """
    fig.write_html(path, include_plotlyjs=True)


def _add_country_traces(fig, df, country, visible):
    """Add one country's GDP bar (left axis) + intensity line (right axis).

    Bars are the country's translucent hue; the line is a darker, more
    saturated version of the same hue, drawn on top.
    """
    gdp = series(df, GDP_IND, countries=[country])
    inten = series(df, INTENSITY_IND, countries=[country])
    base = COUNTRY_COLORS[country]
    line_color = _darken(base)
    fig.add_bar(
        x=gdp["year"], y=gdp["value"] / 1e12, name="GDP", visible=visible,
        marker_color=base, opacity=BAR_OPACITY,
        hovertemplate="%{x}: $%{y:.2f}T<extra></extra>", secondary_y=False,
    )
    fig.add_scatter(
        x=inten["year"], y=inten["value"], name="Emissions intensity",
        visible=visible, mode="lines+markers",
        line=dict(color=line_color, width=3), marker=dict(color=line_color),
        hovertemplate="%{x}: %{y:.3f} kg/$<extra></extra>", secondary_y=True,
    )


def gdp_vs_intensity(df, countries=None):
    """Interactive dual-axis combo with a country dropdown.

    GDP (constant 2015 US$) as bars on the left axis (scaled to trillions) and
    carbon intensity of GDP as a line on the right. A dropdown switches which
    country is shown; both axes rescale to fit. Returns a Plotly Figure.
    """
    from plotly.subplots import make_subplots
    countries = countries or COUNTRY_ORDER
    n = len(countries)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for i, c in enumerate(countries):
        _add_country_traces(fig, df, c, visible=(i == 0))

    # One dropdown entry per country: show only that country's two traces.
    buttons = []
    for i, c in enumerate(countries):
        vis = [False] * (2 * n)
        vis[2 * i] = vis[2 * i + 1] = True
        buttons.append(dict(
            label=c, method="update",
            args=[{"visible": vis}, {"title.text": f"{c}: GDP vs. emissions intensity"}],
        ))

    fig.update_layout(
        title=f"{countries[0]}: GDP vs. Emissions Intensity of GDP",
        updatemenus=[dict(buttons=buttons, direction="down", showactive=True,
                          x=1.0, xanchor="right", y=1.16, yanchor="top")],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        bargap=0.25,
    )
    fig.update_xaxes(dtick=10)
    fig.update_xaxes(title_text="Year", row=2)
    fig.update_yaxes(title_text="GDP (trillion constant 2015 US$)",
                     secondary_y=False, rangemode="tozero")
    fig.update_yaxes(title_text="kg CO₂e per constant 2015 US$",
                     secondary_y=True, rangemode="tozero")
    return fig


def gdp_vs_intensity_grid(df, countries=None, shared_scale=True):
    """2×2 small-multiples grid of the GDP-vs-intensity combo — one panel per
    country. GDP (bars, left axis, trillions) and carbon intensity (line, right
    axis) use one fixed color each across every panel; the country is named in
    the panel title.

    shared_scale=True (default) locks every panel to the same y-ranges for
    honest cross-country comparison, at the cost of flattening small countries'
    trends. shared_scale=False lets each panel autoscale to its own data, which
    reveals each country's year-to-year texture but loses comparability.
    Returns a Figure.
    """
    from plotly.subplots import make_subplots
    countries = countries or COUNTRY_ORDER
    cell = {"secondary_y": True}
    fig = make_subplots(
        rows=2, cols=2, specs=[[cell, cell], [cell, cell]],
        subplot_titles=countries, horizontal_spacing=0.10, vertical_spacing=0.13,
    )

    gdp_max = inten_max = 0
    line_color = _darken(GRID_COLOR)
    for i, c in enumerate(countries):
        r, col = i // 2 + 1, i % 2 + 1
        gdp = series(df, GDP_IND, countries=[c])
        inten = series(df, INTENSITY_IND, countries=[c])
        gdp_max = max(gdp_max, (gdp["value"] / 1e12).max())
        inten_max = max(inten_max, inten["value"].max())
        legend = i == 0  # show each series in the legend only once
        fig.add_bar(
            x=gdp["year"], y=gdp["value"] / 1e12, name="GDP",
            marker_color=GRID_COLOR, opacity=BAR_OPACITY, showlegend=legend,
            hovertemplate="%{x}: $%{y:.2f}T<extra>GDP</extra>",
            row=r, col=col, secondary_y=False,
        )
        fig.add_scatter(
            x=inten["year"], y=inten["value"], name="Emissions intensity",
            mode="lines", line=dict(color=line_color, width=2.5),
            showlegend=legend,
            hovertemplate="%{x}: %{y:.3f} kg/$<extra>Intensity</extra>",
            row=r, col=col, secondary_y=True,
        )

    for i in range(len(countries)):
        r, col = i // 2 + 1, i % 2 + 1
        if shared_scale:
            # Same range on every panel (with a little headroom).
            fig.update_yaxes(range=[0, gdp_max * 1.05], row=r, col=col, secondary_y=False)
            fig.update_yaxes(range=[0, inten_max * 1.05], row=r, col=col, secondary_y=True)
        else:
            # Each panel fits its own data, but both axes still start at zero.
            fig.update_yaxes(rangemode="tozero", row=r, col=col, secondary_y=False)
            fig.update_yaxes(rangemode="tozero", row=r, col=col, secondary_y=True)

    scale_note = "shared scale" if shared_scale else "independent scales"
    fig.update_layout(
        title=dict(text="GDP vs. Emissions Intensity of GDP",
        x=0.5, xanchor="center", y=0.97, yanchor="top"),
        legend=dict(orientation="h", yanchor="bottom", y=1.12, x=0.02),
        margin=dict(t=150),
        bargap=0.2,
    )
    fig.update_xaxes(dtick=10)
    fig.update_xaxes(title_text="Year", row=2)
    fig.update_yaxes(title_text="GDP (constant $ in Trillions)", col=1, secondary_y=False)
    fig.update_yaxes(title_text="Emissions Intensity (kg CO₂e/$)", col=2, secondary_y=True)
    return fig


def manufacturing_share_refined(df, countries=None):
    """Refined multi-line manufacturing-share chart: direct end-labels instead
    of a legend, zero baseline, ticks every 5%."""
    import plotly.graph_objects as go
    countries = countries or COUNTRY_ORDER

    fig = go.Figure()
    ends = []  # (end_value, end_year, country, color) for label placement
    ymin = ymax = None
    last_year = 0
    for c in countries:
        s = series(df, MFG_SHARE_IND, countries=[c], source="main_mfg_ems")
        fig.add_scatter(
            x=s["year"], y=s["value"], name=c, mode="lines",
            line=dict(color=COUNTRY_COLORS[c], width=3), showlegend=False,
            hovertemplate="%{y:.1f}%<extra>" + c + "</extra>",
        )
        ev, ey = s.iloc[-1]["value"], s.iloc[-1]["year"]
        ends.append([ev, ey, c, COUNTRY_COLORS[c]])
        last_year = max(last_year, ey)
        lo, hi = s["value"].min(), s["value"].max()
        ymin = lo if ymin is None else min(ymin, lo)
        ymax = hi if ymax is None else max(ymax, hi)

    # De-overlap the end labels: enforce a minimum vertical gap.
    span = ymax - ymin
    min_gap = span * 0.05
    ends.sort(key=lambda t: t[0])
    prev = float("-inf")
    for e in ends:
        e.append(max(e[0], prev + min_gap))  # label y (may nudge up from value)
        prev = e[-1]
    for value, year, c, color, label_y in ends:
        fig.add_annotation(
            x=year, y=label_y, text=f"<b>{c}</b>  {value:.1f}%",
            xanchor="left", xshift=10, showarrow=False,
            font=dict(color=color, size=14),
        )

    pad = span * 0.08
    fig.update_layout(
        title=dict(text="Manufacturing value added (% of GDP)",
                   x=0.5, xanchor="center", y=0.95, yanchor="top"),
        margin=dict(t=110, r=140),  # right room for the labels
        hovermode="x unified",
    )
    fig.update_xaxes(title_text="Year", dtick=5, range=[1990, last_year + 6])
    fig.update_yaxes(title_text="% of GDP", ticksuffix="%",
                     range=[0, ymax + pad], dtick=5, tick0=0)
    return fig

def mva_branch_bars(path, years=(1990, 2000, 2019),
                    countries=("China", "India", "United States")):
    """Stacked-bar manufacturing mix from the WDI extract, one panel per country.

    Reads the WDI Excel export, keeps the five branch categories (which sum to
    100% of MVA), and draws one 100% stacked bar per snapshot year. Only China,
    India and the US have branch data; China's series ends at 2019.
    """
    import pandas as pd
    import plotly.express as px

    raw = pd.read_excel(r"C:\Users\dsalian\OneDrive - rff\Desktop\mfg_ems_project\MVA_Cont.xlsx", sheet_name="Data")
    raw = raw[raw["Series Name"].isin(MVA_BRANCHES)
              & raw["Country Name"].isin(countries)].copy()
    ycols = [c for c in raw.columns if "YR" in str(c)]
    long = raw.melt(id_vars=["Series Name", "Country Name"], value_vars=ycols,
                    var_name="year", value_name="value")
    long["year"] = long["year"].str[:4].astype(int)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")  # '..' -> NaN
    long["component"] = long["Series Name"].map(MVA_BRANCHES)
    long = long[long["year"].isin(years) & long["value"].notna()].copy()
    long["year"] = long["year"].astype(str)  # categorical bars

    fig = px.bar(
        long, x="year", y="value", color="component",
        facet_col="Country Name", facet_col_spacing=0.06,
        category_orders={"component": MVA_BRANCH_ORDER,
                         "Country Name": list(countries)},
        color_discrete_map=MVA_BRANCH_COLORS,
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_layout(
        barmode="stack", bargap=0.3,
        title=dict(text="Manufacturing mix by branch (% of MVA)",
                   x=0.5, xanchor="center", y=0.97, yanchor="top"),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0.5,
                    xanchor="center", title_text=""),
        margin=dict(t=150),
    )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(range=[0, 100], ticksuffix="%", title_text="")
    fig.update_yaxes(title_text="% of MVA", col=1)
    return fig

if __name__ == "__main__":
    import os
    import webbrowser
    from data_prep import prepare

    print(">>> Running the current plots.py — building the charts...")
    df = prepare("combined_tidy_panel_ICUE.csv")

    charts = {
        "gdp_vs_intensity.html": gdp_vs_intensity(df),          # dropdown, per country
        "gdp_vs_intensity_grid.html": gdp_vs_intensity_grid(df),  # 2x2 shared scale
        "manufacturing_share_refined.html": manufacturing_share_refined(df), 
        "mva_branch_bars.html": mva_branch_bars(df),  # % of GDP, one line/country
    }
    for name, fig in charts.items():
        path = os.path.abspath(name)
        save(fig, path)
        print(">>> Saved:", path)

for name in charts:
    webbrowser.open("file://" + os.path.abspath(name))
