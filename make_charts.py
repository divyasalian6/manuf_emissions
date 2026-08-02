"""Driver script: build and save every figure for the ICUE project.

Run this from the project folder (with the venv active):

    python make_charts.py

It cleans the data once, then writes one self-contained HTML file per chart.
Add a new chart by importing its function and adding one save(...) line below.
"""
import os
import webbrowser

from data_prep import prepare
from plots import (
    gdp_vs_intensity,
    gdp_vs_intensity_grid,
    manufacturing_share,
    save,
)

DATA = "combined_tidy_panel_ICUE.csv"


def main():
    df = prepare(DATA)

    charts = {
        "gdp_vs_intensity.html": gdp_vs_intensity(df),
        "gdp_vs_intensity_grid.html": gdp_vs_intensity_grid(df),
        "gdp_vs_intensity_grid_independent.html": gdp_vs_intensity_grid(df, shared_scale=False),
        "manufacturing_share.html": manufacturing_share(df),
    }

    for name, fig in charts.items():
        path = os.path.abspath(name)
        save(fig, path)
        print(">>> Saved:", path)

    # Open the last one in the browser so you get a quick visual check.
    webbrowser.open("file://" + os.path.abspath(list(charts)[-1]))


if __name__ == "__main__":
    main()
