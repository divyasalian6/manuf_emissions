"""Data preparation for the ICUE combined tidy panel."""
import re
import pandas as pd

# Captures the contents of the LAST "(...)" group in a string.
# Anchoring to the end skips mid-name noise like "(CO2)" or "(Energy)".
_TRAILING_PAREN = re.compile(r"\(([^()]*)\)\s*$")

# Maps every observed country spelling to a canonical label. Edit the values
# here (e.g. move "Europe" off "EU") if you want different groupings.
COUNTRY_CANON = {
    "China": "China",
    "China, People's Republic of": "China",
    "EU": "EU",
    "Europe": "EU",                      # unep_mfg_co2's label for the EU slot
    "European Union": "EU",
    "Europeon Union": "EU",              # typo in imf_co2_embodied
    "India": "India",
    "United States": "United States",
    "United States of America": "United States",
}


def load_panel(path: str) -> pd.DataFrame:
    """Load the tidy panel CSV."""
    return pd.read_csv(path)


def backfill_units(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing `unit` values from the trailing parenthetical of `indicator`.

    Many indicators carry their unit in the name, e.g.
    'Total greenhouse gas emissions excluding LULUCF (Mt CO2e)', while the
    `unit` column is left blank. This extracts that trailing '(...)' group and
    uses it wherever `unit` is null; existing units are left untouched.

    Returns a new DataFrame; the input is not modified.
    """
    df = df.copy()
    extracted = df["indicator"].str.extract(_TRAILING_PAREN, expand=False)
    df["unit"] = df["unit"].fillna(extracted)
    return df


def normalize_countries(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse inconsistent country spellings to canonical labels.

    The same four entities appear under nine names across sources (e.g. China
    as "China, People's Republic of"; the EU as "EU", "Europe", "European
    Union", and the misspelled "Europeon Union"). Grouping by `country` as-is
    would split China into two series and the EU into four.

    Returns a new DataFrame; the input is not modified. Raises ValueError on any
    label missing from COUNTRY_CANON, so new spellings in future data fail
    loudly instead of silently fragmenting a chart.
    """
    df = df.copy()
    unknown = set(df["country"].unique()) - set(COUNTRY_CANON)
    if unknown:
        raise ValueError(f"Unmapped country labels: {sorted(unknown)}")
    df["country"] = df["country"].map(COUNTRY_CANON)
    return df


def prepare(path: str) -> pd.DataFrame:
    """Load the panel and run all cleaning steps in order."""
    return normalize_countries(backfill_units(load_panel(path)))


if __name__ == "__main__":
    raw = load_panel("combined_tidy_panel_ICUE.csv")
    clean = prepare("combined_tidy_panel_ICUE.csv")

    print(f"Missing units: {raw['unit'].isna().sum()} -> {clean['unit'].isna().sum()}")
    print(f"Country labels: {raw['country'].nunique()} -> {clean['country'].nunique()}")
    print()
    print("Rows per canonical country:")
    print(clean["country"].value_counts())
