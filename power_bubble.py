"""Animated power-sector bubble chart.

Grid carbon intensity (x) vs. total power-sector emissions (y), with bubble size
= manufacturing value added (% of GDP), one bubble per country, animated over
years with a play button and slider.

Run from the project folder (venv active):

    python power_bubble.py

Needs data_prep.py and combined_tidy_panel_ICUE.csv in the same folder. This
script is self-contained (it does not import from the main plotting file), so it
carries its own copy of the shared styling and colors.
"""
import os
import webbrowser

import plotly.express as px
import plotly.io as pio

from data_prep import prepare

# --- Shared styling (same template as the rest of the project) ---
pio.templates.default = "plotly_white"
pio.templates["plotly_white"].layout.font.family = "Calibri, sans-serif"
pio.templates["plotly_white"].layout.font.weight = "bold"
pio.templates["plotly_white"].layout.xaxis.tickfont.weight = "normal"
pio.templates["plotly_white"].layout.yaxis.tickfont.weight = "normal"
pio.templates["plotly_white"].layout.legend.font.size = 16

COUNTRY_ORDER = ["China", "United States", "EU", "India"]
COUNTRY_COLORS = {
    "China": "#c0392b",
    "United States": "#2d3944",
    "EU": "#2980b9",
    "India": "#e67e22",
}
DATA = "combined_tidy_panel_ICUE.csv"


def save(fig, path):
    """Write a fully self-contained interactive HTML file."""
    fig.write_html(path, include_plotlyjs=True)


def power_intensity_bubble(df):
    """Animated bubble chart of grid carbon intensity vs. power-sector emissions,
    sized by manufacturing value added (% of constant GDP)."""
    x_ind = "Power sector emissions - CO2 intensity"
    y_ind = "Power sector emissions - Total emissions"
    size_ind = "Manufacturing, value added (% of GDP)"

    sub = df[df["indicator"].isin([x_ind, y_ind, size_ind])]
    wide = sub.pivot_table(index=["country", "year"], columns="indicator", values="value")
    wide = wide.rename(columns={x_ind: "intensity", y_ind: "emissions", size_ind: "mva"})
    wide = wide.dropna().reset_index()

    # Keep only years where all countries are present, so the animation doesn't
    # have bubbles popping in and out between frames.
    n_countries = wide["country"].nunique()
    full = wide.groupby("year")["country"].transform("nunique") == n_countries
    wide = wide[full].sort_values(["year", "country"])

    fig = px.scatter(
        wide, x="intensity", y="emissions", size="mva", color="country",
        text="country",                          # <-- add this line
        animation_frame="year", animation_group="country",
        color_discrete_map=COUNTRY_COLORS, category_orders={"country": COUNTRY_ORDER},
        size_max=40, opacity=0.8,
        range_x=[0, wide["intensity"].max() * 1.1],
        range_y=[0, wide["emissions"].max() * 1.1],
        labels={"intensity": "Grid carbon intensity (gCO₂/kWh)",
                "emissions": "Total power-sector emissions (MtCO₂)",
                "mva": "MVA (% of GDP)"},
    )
    fig.update_traces(
        marker=dict(line=dict(width=1, color="white")),
        textposition="top center",               # label sits above each bubble
        textfont=dict(size=13),
    )
    fig.update_layout(
        title=dict(text="Grid Carbon Intensity vs Total Power Sector Emissions",
                   x=0.5, xanchor="center", y=0.97, yanchor="top"),
        showlegend=False,                         # <-- turn the legend off
        margin=dict(t=120),
    )
    fig.add_annotation(
        text="Bubble size = Manufacturing Value Added (% of GDP)",
        x=0.5, y=1.06, xref="paper", yref="paper",
        xanchor="center", yanchor="bottom", showarrow=False,
        font=dict(size=15, color="#555555"),
    )
    return fig


if __name__ == "__main__":
    df = prepare(DATA)
    fig = power_intensity_bubble(df)

    out = os.path.abspath("power_intensity_bubble.html")
    save(fig, out)
    print(">>> Saved:", out)
    webbrowser.open("file://" + out)
