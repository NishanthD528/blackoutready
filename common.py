"""Shared settings, data loading, and helper functions used by every page."""
import numpy as np
import pandas as pd
import requests
import streamlit as st

# ---------------- Settings ----------------
BATTERY_EFFICIENCY = 0.85   # assumption: about 15% of battery energy is lost converting it to wall power
FRIDGE_SAFE_HOURS = 4       # USDA: a closed fridge keeps food safe for about 4 hours
NEARBY_MILES = 25           # how far around your zip the local map looks

# Blackout Risk Score: how much each part counts (adds up to 1)
# Disaster threat counts most because it's what actually causes big, long outages;
# grid weakness and device dependence decide how bad an outage gets for people.
WEIGHTS = {
    "hazard": 0.4,       # FEMA: how threatened your county is by outage-causing disasters
    "grid": 0.3,         # EIA: how long your utility's customers go without power each year
    "dependence": 0.3,   # HHS: share of local Medicare patients who rely on powered devices
}

HAZARDS = {
    "HWAV": "Heat wave",
    "WFIR": "Wildfire",
    "WNTW": "Winter weather",
    "ISTM": "Ice storm",
    "HRCN": "Hurricane",
    "SWND": "Strong wind",
    "TRND": "Tornado",
    "CWAV": "Cold wave",
}

# Level name, badge color, plain-language meaning
LEVELS = [
    (75, "High", "red", "A long outage here would put many people at serious risk. Have a backup plan ready now."),
    (50, "Elevated", "orange", "Outages here are a real threat for people on powered devices. Make a plan before the next storm."),
    (25, "Moderate", "yellow", "Some risk. A simple backup plan goes a long way."),
    (0, "Low", "green", "Lower risk than most of the U.S., but any outage can be dangerous for device users."),
]

SOURCES = ("Sources: HHS emPOWER Map (Oct 2026) · U.S. EIA Form 861 (2025) · "
           "FEMA National Risk Index (Dec 2025) · U.S. Census Gazetteer (2024) · NREL utility zip codes (2024)")


# ---------------- Data ----------------
@st.cache_data(show_spinner="Loading federal data...")
def load_counties():
    df = pd.read_csv("data/counties.csv", dtype={"FIPS_Code": str})
    hazard_cols = [f"{h}_RISKS" for h in HAZARDS]
    df["biggest_hazard_score"] = df[hazard_cols].max(axis=1)
    # A few counties have no FEMA data at all; only look for a biggest threat where data exists
    has_data = df[hazard_cols].notna().any(axis=1)
    df["biggest_hazard"] = None
    df.loc[has_data, "biggest_hazard"] = df.loc[has_data, hazard_cols].idxmax(axis=1).str[:4].map(HAZARDS)
    return df


def blackout_risk_score(row):
    """Weighted average of the three parts for one zip code.
    If a part has no data, it's skipped and the other parts share its weight."""
    parts = {
        "hazard": row["hazard_part"],
        "grid": row["grid_part"],
        "dependence": row["dependence_part"],
    }
    total = 0
    weight_used = 0
    for name, value in parts.items():
        if pd.notna(value):
            total += value * WEIGHTS[name]
            weight_used += WEIGHTS[name]
    if weight_used == 0:
        return np.nan          # no data at all
    return total / weight_used


@st.cache_data(show_spinner="Calculating risk scores...")
def load_zips():
    df = pd.read_csv("data/zips.csv", dtype={"zip": str, "FIPS_Code": str, "eiaid": str})
    counties = load_counties()[["FIPS_Code", "biggest_hazard_score", "biggest_hazard"]]
    df = df.merge(counties, on="FIPS_Code", how="left")

    # Step 1: turn each ingredient into a 0-100 national percentile (100 = most at risk).
    # A percentile of 64 means "riskier than 64% of U.S. zip codes".
    df["device_share"] = df["on_devices"] / df["medicare_patients"].replace(0, np.nan)
    df["hazard_part"] = df["biggest_hazard_score"]            # FEMA scores are already percentiles
    df["grid_part"] = df["outage_minutes"].rank(pct=True) * 100
    df["dependence_part"] = df["device_share"].rank(pct=True) * 100

    # Step 2: combine the three parts into one score for each zip code
    df["risk_score"] = df.apply(blackout_risk_score, axis=1)
    return df


@st.cache_data(show_spinner="Loading county map...")
def load_county_shapes():
    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    return requests.get(url, timeout=30).json()


# ---------------- Helpers ----------------
def format_time(seconds):
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def miles_between(lat1, lon1, lat2, lon2):
    """Haversine formula: distance in miles between points on Earth."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))


def risk_level(score):
    for cutoff, name, color, meaning in LEVELS:
        if score >= cutoff:
            return name, color, meaning
    return LEVELS[-1][1:]


def part_text(value):
    return "No data" if pd.isna(value) else f"{value:.0f} / 100"
