"""
Aggregate EU ETS installation-level emissions to EU ETS totals by year (2005-2025),
for the iron & steel and cement industries only.

Input : installation-year panel (.xlsx, .csv or tab-separated .tsv/.txt)
Output: eu_emissions_by_year.csv  (one row per year)

Emissions are in million tonnes CO2 (Mt).
"""

from pathlib import Path
import pandas as pd

# ---------------- settings ----------------
INPUT_FILE = "data\\1b_eutl_installation_year_panel_filled.xlsx"   # <- your file
OUTPUT_FILE = "eu_emissions_by_year.csv"

YEAR_START, YEAR_END = 2005, 2025

# "verified_t_filled" = reported emissions, with gaps filled by estimates (recommended:
#                       dozens of large plants are blank in 2025, which otherwise
#                       shows up as a fake ~18 Mt drop)
# "verified_t"        = reported emissions only
EMISSIONS_COL = "verified_t_filled"

# EU ETS countries: EU27 + Norway, Iceland, Liechtenstein, the UK (until 2020)
# and Northern Ireland (XI, from 2021).
EU27_ONLY = False
EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
}


EXCLUDE_UK_ALL_YEARS = False


SECTOR_METHOD = "nace"

SECTORS = {
    "iron_steel": {
        "nace4": [2410],        # 24.10 Manufacture of basic iron and steel and ferro-alloys
        "activity_id": [24, 5], # 24 = pig iron/steel (2013+ numbering)
                                #  5 = same activity, old 2005-2012 numbering
    },
    "cement": {
        "nace4": [2351],        # 23.51 Manufacture of cement
        "activity_id": [29, 6], # 29 = cement clinker (2013+ numbering)
                                #  6 = cement clinker OR lime, old numbering
    },
}

# 1. Load
path = Path(INPUT_FILE)
if path.suffix.lower() in (".xlsx", ".xls"):
    print("Reading Excel file (this can take a minute for a large file)...")
    df = pd.read_excel(path)
else:
    sep = "," if path.suffix.lower() == ".csv" else "\t"
    try:
        df = pd.read_csv(path, sep=sep, encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep=sep, encoding="latin-1", low_memory=False)

print(f"Loaded {len(df):,} rows, {df['id'].nunique():,} installations")

# 2. Make sure numbers are numbers (blank cells become NaN)
for col in ["year", EMISSIONS_COL, "nace4", "activity_id", "first_emit_year"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df["verified_imputed"] = pd.to_numeric(df.get("verified_imputed", 0), errors="coerce").fillna(0)

# 3. Years and countries
df = df[df["year"].between(YEAR_START, YEAR_END)]
if EU27_ONLY:
    df = df[df["country_id"].replace({"EL": "GR"}).isin(EU27)]
if EXCLUDE_UK_ALL_YEARS:
    df = df[df["country_id"] != "GB"]

# 4. Label each row with its sector, and keep only iron & steel and cement
code_col = "nace4" if SECTOR_METHOD == "nace" else "activity_id"
df["sector"] = None
for sector, codes in SECTORS.items():
    df.loc[df[code_col].isin(codes[code_col]), "sector"] = sector
df = df[df["sector"].notna()]
print(f"Kept {df['id'].nunique():,} installations (sector assigned by {code_col})")

# 5. Guard against double counting: one row per installation per year
dupes = df.duplicated(subset=["id", "year"]).sum()
if dupes:
    print(f"Warning: dropping {dupes:,} duplicate installation-year rows")
    df = df.drop_duplicates(subset=["id", "year"])

# 6. Flags used in the output
df["emitting"] = df[EMISSIONS_COL] > 0                      # zeros aren't active plants
df["imputed"] = (df["verified_imputed"] == 1) & df[EMISSIONS_COL].notna()
# Installations that only entered the ETS in 2013 (Phase 3 scope expansion).
# Their emissions weren't covered before 2013, so they create a step up that year.
df["phase3_entrant"] = df["first_emit_year"] >= 2013

# 7. Aggregate by year and sector
g = df.groupby(["year", "sector"])
by_sector = pd.DataFrame({
    "emissions_mt": g[EMISSIONS_COL].sum() / 1e6,
    "n_installations": g["emitting"].sum(),
    "n_imputed": g["imputed"].sum(),
    "phase3_entrants_mt": df[df["phase3_entrant"]].groupby(["year", "sector"])[EMISSIONS_COL].sum() / 1e6,
})

wide = by_sector.unstack("sector")
wide.columns = [f"{sector}_{measure}" for measure, sector in wide.columns]
wide = wide.reindex(range(YEAR_START, YEAR_END + 1))
wide.index.name = "year"

out = pd.DataFrame(index=wide.index)
for sector in SECTORS:
    out[f"{sector}_emissions_mt"] = wide.get(f"{sector}_emissions_mt")
    out[f"{sector}_n_installations"] = wide.get(f"{sector}_n_installations").fillna(0).astype(int)
    out[f"{sector}_n_imputed"] = wide.get(f"{sector}_n_imputed").fillna(0).astype(int)
    out[f"{sector}_of_which_phase3_entrants_mt"] = wide.get(f"{sector}_phase3_entrants_mt").fillna(0)
out["total_emissions_mt"] = out[[f"{s}_emissions_mt" for s in SECTORS]].sum(axis=1, min_count=1)
out = out.reset_index()

# 8. Warn about plants that report one year and are blank the next, but come back
#    or were active right up to the gap (likely missing data rather than closures)
last_year = df.loc[df[EMISSIONS_COL].notna(), "year"].max()
prev = set(df.loc[(df["year"] == last_year - 1) & df["emitting"], "id"])
curr = set(df.loc[(df["year"] == last_year) & df[EMISSIONS_COL].notna(), "id"])
missing = prev - curr
if missing:
    lost = df[(df["year"] == last_year - 1) & df["id"].isin(missing)][EMISSIONS_COL].sum() / 1e6
    print(f"Note: {len(missing)} installations emitted in {last_year - 1} but have no value "
          f"in {last_year} ({lost:.1f} Mt in {last_year - 1}). {last_year} may be incomplete.")

# 9. Save and show
out.to_csv(OUTPUT_FILE, index=False)
show = ["year"] + [c for c in out.columns if c.endswith("emissions_mt")]
print(out[show].to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
print(f"\nSaved to {OUTPUT_FILE} (emissions in million tonnes CO2)")
