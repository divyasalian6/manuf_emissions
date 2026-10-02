"""Driver script: build the full ICUE chart set (Plotly)."""

if __name__ == "__main__":
    import os
    import webbrowser
    from data_prep import prepare
    import chart_definitions as chdf
    from chart_definitions import COUNTRY_ORDER
    print(">>> Running GDP-Emis_Int-Plot.py — building the charts...")
    df = prepare("data/combined_tidy_panel_ICUE.xlsx")

    PLOTS_DIR = "plots"
    os.makedirs(PLOTS_DIR, exist_ok=True)

    charts = {
        "gdp_vs_intensity_grid.html": chdf.gdp_vs_intensity_grid(df,COUNTRY_ORDER),  # 2x2 shared scale
        "manufacturing_share_refined.html": chdf.manufacturing_share_refined(df,COUNTRY_ORDER),
        "mva_branch_bars.html": chdf.mva_branch_bars(
            countries=[c for c in COUNTRY_ORDER if c != "EU"]),
        "grid_composition_grid.html": chdf.grid_composition_grid(df,COUNTRY_ORDER),
        "mfg_decoupling_grid.html": chdf.mfg_decoupling_grid(df,COUNTRY_ORDER), # % of GDP, one line/country
    }
    for name, fig in charts.items():
        path = os.path.abspath(os.path.join(PLOTS_DIR, name))
        chdf.save(fig, path)
        print(">>> Saved:", path)

    for name in charts:
        webbrowser.open("file://" + os.path.abspath(os.path.join(PLOTS_DIR, name)))
