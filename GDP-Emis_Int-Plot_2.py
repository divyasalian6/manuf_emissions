"""Interactive plotting helpers for the ICUE panel (Plotly)."""
import plotly.io as pio

# Shared theme. A fixed color per country means the same entity is the same
# color in every chart you make.
pio.templates.default = "plotly_white"
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
    """Add one country's GDP bar (left axis) + intensity line (right axis)."""
    gdp = series(df, GDP_IND, countries=[country])
    inten = series(df, INTENSITY_IND, countries=[country])
    color = COUNTRY_COLORS[country]
    fig.add_bar(
        x=gdp["year"], y=gdp["value"] / 1e12, name="GDP", visible=visible,
        marker_color=color, opacity=0.45,
        hovertemplate="%{x}: $%{y:.2f}T<extra></extra>", secondary_y=False,
    )
    fig.add_scatter(
        x=inten["year"], y=inten["value"], name="Emissions intensity",
        visible=visible, mode="lines+markers", line=dict(color=color, width=3),
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
    fig.update_xaxes(title_text="Year", dtick=5)
    fig.update_yaxes(title_text="GDP (trillion constant 2015 US$)",
                     secondary_y=False, rangemode="tozero")
    fig.update_yaxes(title_text="kg CO₂e per constant 2015 US$",
                     secondary_y=True, rangemode="tozero")
    return fig


if __name__ == "__main__":
    import os
    import webbrowser
    from data_prep import prepare

    print(">>> Running the current plots.py — building the chart...")
    df = prepare("combined_tidy_panel_ICUE.csv")
    fig = gdp_vs_intensity(df)

    out = os.path.abspath("gdp_vs_intensity.html")
    save(fig, out)
    print(">>> Saved:", out)
    webbrowser.open("file://" + out)  # open it in your browser
