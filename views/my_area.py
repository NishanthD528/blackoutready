"""My area page: risk score, grid, hazards, and a local map for one zip code."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from common import (HAZARDS, NEARBY_MILES, SOURCES, WEIGHTS, load_counties, load_zips,
                    miles_between, part_text, risk_level)

zips = load_zips()
counties = load_counties()

# A link like .../my-area?zip=10001 opens straight to that zip (shareable)
if "zip" in st.query_params and "zip_from_link" not in st.session_state:
    st.session_state.zip_code = st.query_params["zip"]
    st.session_state.zip_from_link = True

st.title(":material/home_pin: My area")
# The search box has its own memory ("zip_input"); start it with the last zip the user checked
if "zip_input" not in st.session_state:
    st.session_state.zip_input = st.session_state.zip_code
st.text_input("Enter your zip code", key="zip_input", max_chars=5,
              placeholder="e.g. 94538", help="Any 5-digit U.S. zip code")
zip_code = st.session_state.zip_input.strip()
st.session_state.zip_code = zip_code
match = zips[zips["zip"] == zip_code]

if not (zip_code.isdigit() and len(zip_code) == 5):
    st.info("Type a 5-digit zip code to see your area.")
    st.stop()
if match.empty:
    st.warning("We couldn't find that zip code in the federal data. Try a nearby zip code.")
    st.stop()

st.query_params["zip"] = zip_code       # keeps the page address shareable
z = match.iloc[0]
county = counties[counties["FIPS_Code"] == z["FIPS_Code"]]
st.header(f"{z['County']} County, {z['State']} · {zip_code}")

left, right = st.columns([1, 1], gap="large")

# ================= LEFT COLUMN =================
with left:
    # ---- Blackout Risk Score card ----
    with st.container(border=True):
        if pd.notna(z["risk_score"]):
            score = z["risk_score"]
            level, color, meaning = risk_level(score)
            a, b = st.columns([1, 2], vertical_alignment="center")
            a.metric("Blackout Risk Score", f"{score:.0f} / 100")
            with b:
                st.badge(f"{level} risk", color=color, icon=":material/warning:")
                st.write(meaning)
            st.progress(score / 100)
            c1, c2, c3 = st.columns(3)
            c1.metric("Disaster threat", part_text(z["hazard_part"]), border=True,
                      help="FEMA: how threatened this county is by outage-causing disasters, compared with the rest of the U.S.")
            c2.metric("Grid weakness", part_text(z["grid_part"]), border=True,
                      help="EIA: how long this utility's customers went without power in 2025, compared with the rest of the U.S.")
            c3.metric("Device dependence", part_text(z["dependence_part"]), border=True,
                      help="HHS: share of local Medicare patients on powered medical devices, compared with the rest of the U.S.")
            st.caption(f"Score = {WEIGHTS['hazard']:.0%} disaster threat + {WEIGHTS['grid']:.0%} grid weakness "
                       f"+ {WEIGHTS['dependence']:.0%} device dependence. See *How it works* for details.")
        else:
            st.write("There isn't enough federal data to score this zip code.")

    # ---- Plain-language summary ----
    summary = []
    if pd.notna(z.get("biggest_hazard")):
        summary.append(f"**{z['biggest_hazard']}** is the biggest threat to power in {z['County']} County.")
    if pd.notna(z["outage_minutes"]):
        if pd.notna(z.get("utility_name")) and z["reliability_source"] == "utility":
            who = f"{z['utility_name']} customers"
        else:
            who = f"customers in {z['State']}"
        summary.append(f"In 2025, {who} lost power about **{z['outages_per_year']:.1f} times**, "
                       f"for **{z['outage_minutes'] / 60:.1f} hours** in total on average.")
    summary.append(f"**{z['on_devices']:,} people** in this zip code rely on powered medical devices.")
    st.info(" ".join(summary), icon=":material/lightbulb:")

    # ---- People + grid ----
    c1, c2 = st.columns(2)
    with c1.container(border=True, height="stretch"):
        st.markdown("**:material/groups: People who depend on power**")
        st.metric("On powered medical devices", f"{z['on_devices']:,}")
        share = "No data" if pd.isna(z["device_share"]) else f"{z['device_share']:.1%}"
        st.metric("Share of Medicare patients", share)
    with c2.container(border=True, height="stretch"):
        st.markdown("**:material/electric_bolt: Your power grid**")
        st.write(z["utility_name"] if pd.notna(z.get("utility_name")) else "Power company not listed for this zip.")
        if pd.notna(z["outage_minutes"]):
            st.metric("Hours without power (2025)", f"{z['outage_minutes'] / 60:.1f}")
            st.metric("Outages per customer (2025)", f"{z['outages_per_year']:.1f}")
            if z["reliability_source"] == "state average":
                st.caption(f"{z['State']} statewide average (utility data not available).")

    # ---- Get ready checklist ----
    with st.expander(":material/checklist: Get ready before the next outage", expanded=True):
        st.checkbox("Ask your power company about medical priority or alert programs for people on powered devices")
        st.checkbox("Write down how many watts each device uses (it's on the label)")
        st.checkbox("Get a backup battery and check how long it lasts on the My backup power page")
        st.checkbox("Find a place you can go to charge devices, like a friend's home or a community center")
        st.checkbox("Keep your doctor's and equipment supplier's phone numbers somewhere you can find in the dark")
    st.page_link("views/backup.py", label="Check how long your backup battery lasts",
                 icon=":material/battery_charging_full:")

# ================= RIGHT COLUMN =================
with right:
    # ---- Local map ----
    with st.container(border=True):
        st.markdown(f"**:material/location_on: People on powered devices within {NEARBY_MILES} miles**")
        distance = miles_between(z["lat"], z["lon"], zips["lat"], zips["lon"])
        nearby = zips[distance <= NEARBY_MILES].copy()
        nearby["Where"] = np.where(nearby["zip"] == zip_code, "Your zip", "Nearby zip")
        fig = px.scatter_map(
            nearby, lat="lat", lon="lon", size="on_devices", color="Where",
            color_discrete_map={"Your zip": "#13315C", "Nearby zip": "#E8590C"},
            hover_name="zip",
            hover_data={"on_devices": ":,", "County": True, "lat": False, "lon": False, "Where": False},
            labels={"on_devices": "On powered devices"},
            center={"lat": z["lat"], "lon": z["lon"]}, zoom=9, size_max=30,
            map_style="carto-positron",
        )
        fig.update_layout(height=430, margin=dict(l=0, r=0, t=0, b=0), legend_title_text="")
        st.plotly_chart(fig)
        st.caption(f"{nearby['on_devices'].sum():,} people on powered medical devices live within "
                   f"{NEARBY_MILES} miles, across {len(nearby)} zip codes. Bigger circle = more people.")

    # ---- What threatens the grid ----
    if not county.empty and pd.notna(county.iloc[0]["biggest_hazard_score"]):
        with st.container(border=True):
            st.markdown("**:material/thunderstorm: What could knock out power here**")
            row = county.iloc[0]
            threats = pd.DataFrame({
                "Hazard": list(HAZARDS.values()),
                "Risk score": [row[f"{h}_RISKS"] for h in HAZARDS],
                "FEMA rating": [row[f"{h}_RISKR"] for h in HAZARDS],
            }).sort_values("Risk score")
            fig = px.bar(threats, x="Risk score", y="Hazard", orientation="h",
                         hover_data={"FEMA rating": True}, range_x=[0, 100],
                         color="Risk score", color_continuous_scale="Oranges")
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                              coloraxis_showscale=False, yaxis_title=None)
            st.plotly_chart(fig)
            st.caption(f"FEMA National Risk Index for {row['County']} County. 0 = lowest in the U.S., 100 = highest.")

st.caption(SOURCES)
