"""
prepare_data.py — BlackoutReady data pipeline

Joins four federal datasets into two small, fast files the app reads:
  data/zips.csv      one row per zip code
  data/counties.csv  one row per county

Run it once (or whenever you download newer data):
  python3.12 prepare_data.py
"""
import os

import pandas as pd

EMPOWER_FILE = "2026_HHSemPOWERMapHistoricalDataset.xlsx"   # HHS emPOWER, Oct 2026
ZIP_LOCATIONS_FILE = "2024_Gaz_zcta_national.txt"           # U.S. Census Gazetteer
UTILITY_FILES = ["iou_zipcodes_2024.csv", "non_iou_zipcodes_2024.csv"]  # NREL/OpenEI
RELIABILITY_FILE = "Reliability_2025.xlsx"                  # U.S. EIA Form 861
HAZARD_FILE = "NRI_Table_Counties.csv"                       # FEMA National Risk Index

MONTH = "Oct_2026"

# Hazards that commonly knock out power, and their names for the app
OUTAGE_HAZARDS = {
    "HWAV": "Heat wave",
    "WFIR": "Wildfire",
    "WNTW": "Winter weather",
    "ISTM": "Ice storm",
    "HRCN": "Hurricane",
    "SWND": "Strong wind",
    "TRND": "Tornado",
    "CWAV": "Cold wave",
}


def load_empower(sheet, id_column):
    """People on electricity-dependent medical devices, by zip or county."""
    columns = ["FIPS_Code", "County", "State",
               f"{MONTH}_Medicare_Benes", f"{MONTH}_Power_Dependent_Devices_DME"]
    if id_column not in columns:
        columns = [id_column] + columns
    df = pd.read_excel(EMPOWER_FILE, sheet_name=sheet, usecols=columns)
    df = df.rename(columns={
        f"{MONTH}_Medicare_Benes": "medicare_patients",
        f"{MONTH}_Power_Dependent_Devices_DME": "on_devices",
    })
    df["FIPS_Code"] = df["FIPS_Code"].astype(str).str.zfill(5)
    df["County"] = df["County"].str.strip()
    df["State"] = df["State"].str.strip()
    return df


def load_zip_locations():
    """Latitude/longitude of the center of every zip code area."""
    df = pd.read_csv(ZIP_LOCATIONS_FILE, sep="\t", dtype={"GEOID": str})
    df.columns = [c.strip() for c in df.columns]   # the last header has hidden spaces
    return df.rename(columns={"GEOID": "zip", "INTPTLAT": "lat", "INTPTLONG": "lon"})[["zip", "lat", "lon"]]


def load_reliability():
    """How often each utility's customers lose power (EIA 2025)."""
    df = pd.read_excel(RELIABILITY_FILE, sheet_name="Reliability_States", header=None, skiprows=3)
    # Columns by position: 1 utility id, 2 name, 5/6 IEEE SAIDI/SAIFI, 17/18 other-standard SAIDI/SAIFI
    df = df.iloc[:, [1, 2, 5, 6, 17, 18]]
    df.columns = ["eiaid", "utility_name", "saidi_ieee", "saifi_ieee", "saidi_other", "saifi_other"]
    df = df.dropna(subset=["eiaid"])
    df["eiaid"] = df["eiaid"].astype(int).astype(str)
    for col in ["saidi_ieee", "saifi_ieee", "saidi_other", "saifi_other"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")   # "." means no data
    # Utilities report with one of two standards; use whichever they reported
    df["outage_minutes"] = df["saidi_ieee"].fillna(df["saidi_other"])
    df["outages_per_year"] = df["saifi_ieee"].fillna(df["saifi_other"])
    df = df.dropna(subset=["outage_minutes"])
    # A utility that serves several states appears more than once: average its rows
    return df.groupby("eiaid", as_index=False)[["outage_minutes", "outages_per_year"]].mean()


def load_state_reliability():
    """Statewide average reliability, used when a zip's utility has no data."""
    df = pd.read_excel(RELIABILITY_FILE, sheet_name="State Totals", header=None, skiprows=3)
    # Columns by position: 1 state, 13/14 SAIDI/SAIFI for all utilities (any standard)
    df = df.iloc[:, [1, 13, 14]]
    df.columns = ["State", "state_outage_minutes", "state_outages_per_year"]
    df = df.dropna(subset=["State"])
    df["State"] = df["State"].astype(str).str.strip()
    for col in ["state_outage_minutes", "state_outages_per_year"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_utilities():
    """Which power company serves each zip code, plus its reliability."""
    zips = pd.concat([pd.read_csv(f, dtype={"zip": str, "eiaid": str}) for f in UTILITY_FILES])
    zips["zip"] = zips["zip"].str.zfill(5)
    zips = zips.drop_duplicates(["zip", "eiaid"])[["zip", "eiaid", "utility_name"]]
    zips = zips.merge(load_reliability(), on="eiaid", how="left")
    # If several utilities serve a zip, keep the one with reliability data first
    zips = zips.sort_values("outage_minutes", na_position="last")
    first = zips.drop_duplicates("zip").copy()
    first["other_utilities"] = first["zip"].map(zips.groupby("zip").size() - 1)
    return first


def load_hazards():
    """FEMA risk scores (0-100, national percentile) for outage-causing hazards."""
    cols = ["STCOFIPS"] + [f"{h}_RISKS" for h in OUTAGE_HAZARDS] + [f"{h}_RISKR" for h in OUTAGE_HAZARDS]
    df = pd.read_csv(HAZARD_FILE, usecols=cols, dtype={"STCOFIPS": str})
    df = df.rename(columns={"STCOFIPS": "FIPS_Code"})
    for h in OUTAGE_HAZARDS:
        df[f"{h}_RISKS"] = df[f"{h}_RISKS"].fillna(0)   # blank = hazard doesn't apply there
    return df


def main():
    os.makedirs("data", exist_ok=True)

    print("Loading emPOWER zip and county data (takes ~20 seconds)...")
    zips = load_empower("Zip Code", "Zip_Code").rename(columns={"Zip_Code": "zip"})
    zips["zip"] = zips["zip"].astype(str).str.zfill(5)
    counties = load_empower("County", "FIPS_Code")

    print("Adding zip locations, power companies, and reliability...")
    zips = zips.merge(load_zip_locations(), on="zip", how="left")
    # A few zips (like PO boxes) have no Census location: use their county's average
    for col in ["lat", "lon"]:
        zips[col] = zips[col].fillna(zips.groupby("FIPS_Code")[col].transform("mean"))
    zips = zips.merge(load_utilities(), on="zip", how="left")

    # No utility reliability for this zip? Fall back to the state average
    zips = zips.merge(load_state_reliability(), on="State", how="left")
    zips["reliability_source"] = "utility"
    missing = zips["outage_minutes"].isna()
    zips.loc[missing, "reliability_source"] = "state average"
    zips.loc[missing, "outage_minutes"] = zips.loc[missing, "state_outage_minutes"]
    zips.loc[missing, "outages_per_year"] = zips.loc[missing, "state_outages_per_year"]
    zips = zips.drop(columns=["state_outage_minutes", "state_outages_per_year"])

    print("Adding FEMA hazard risk...")
    counties = counties.merge(load_hazards(), on="FIPS_Code", how="left")

    zips.to_csv("data/zips.csv", index=False)
    counties.to_csv("data/counties.csv", index=False)
    print(f"Done: {len(zips):,} zip codes and {len(counties):,} counties saved in the data folder.")


if __name__ == "__main__":
    main()
