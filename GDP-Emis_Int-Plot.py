"""Interactive plotting helpers for the ICUE panel (Plotly)."""
import plotly.io as pio
import manuf_emissions_code as mec

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

FUEL_ORDER = ["Coal", "Gas", "Nuclear", "Hydro",
              "Bioenergy", "Wind", "Solar"]
FUEL_COLORS = {
    "Coal": "#33322f", "Gas": "#d1603d",
    "Nuclear": "#a05eb5", "Hydro": "#2b7bba", "Bioenergy": "#5a8f3c",
    "Wind": "#4bb3c4", "Solar": "#f4c430",
}

MVA_LEVEL_IND = "Manufacturing, value added (constant 2015 US$)"
MFG_INTENSITY_IND = ("Carbon dioxide emissions from manufacturing industries per unit "
                     "of manufacturing value added (kilogrammes of CO2 per constant "
                     "2020 United States dollars)")



if __name__ == "__main__":
    import os
    import webbrowser
    from manuf_emissions_code.data_prep import prepare
    import manuf_emissions_code.chart_definitions as chdf
    print(">>> Running the current plots.py — building the charts...")
    df = prepare("combined_tidy_panel_ICUE.csv")

    charts = {
        "gdp_vs_intensity_grid.html": chdf.gdp_vs_intensity_grid(df,COUNTRY_ORDER),  # 2x2 shared scale
        "manufacturing_share_refined.html": chdf.manufacturing_share_refined(df,COUNTRY_ORDER), 
        "mva_branch_bars.html": chdf.mva_branch_bars(df,COUNTRY_ORDER),
        "grid_composition_grid.html": chdf.grid_composition_grid(df,COUNTRY_ORDER), 
        "mfg_decoupling_grid.html": chdf.mfg_decoupling_grid(df,COUNTRY_ORDER), # % of GDP, one line/country
    }
    for name, fig in charts.items():
        path = os.path.abspath(name)
        save(fig, path)
        print(">>> Saved:", path)

for name in charts:
    webbrowser.open("file://" + os.path.abspath(name))
