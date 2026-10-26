"""How it works page: data sources, the risk score method, and limits."""
import pandas as pd
import streamlit as st

from common import WEIGHTS

_, center, _ = st.columns([1, 4, 1])
with center:
    st.title(":material/info: How BlackoutReady works")

    st.subheader("Four federal datasets, joined together")
    sources = pd.DataFrame([
        ["HHS emPOWER Map", "U.S. Dept. of Health & Human Services", "October 2026",
         "Medicare patients who rely on electricity-powered medical devices, by zip code and county"],
        ["Form EIA-861 Reliability", "U.S. Energy Information Administration", "2025",
         "How many hours and times each utility's customers lost power"],
        ["National Risk Index", "FEMA", "December 2025",
         "Each county's risk from 18 natural hazards (8 that commonly cause outages are used here)"],
        ["Gazetteer Files", "U.S. Census Bureau", "2024", "The center point of every zip code area, for the map"],
        ["Utility rates by zip code", "NREL / U.S. Dept. of Energy", "2024", "Which power company serves each zip code"],
    ], columns=["Dataset", "Agency", "Data year", "What BlackoutReady uses it for"])
    st.dataframe(sources, hide_index=True, width="stretch")

    st.subheader("The Blackout Risk Score")
    st.write("Each zip code gets three scores, each a national percentile from 0 to 100 "
             "(for example, 64 means riskier than 64% of U.S. zip codes):")
    st.markdown(f"""
- **Disaster threat ({WEIGHTS['hazard']:.0%})**: the highest FEMA risk score among heat wave, wildfire, winter weather, ice storm, hurricane, strong wind, tornado, and cold wave.
- **Grid weakness ({WEIGHTS['grid']:.0%})**: how many minutes the local utility's customers went without power in 2025, ranked against all zip codes.
- **Device dependence ({WEIGHTS['dependence']:.0%})**: the share of local Medicare patients who rely on powered devices, ranked against all zip codes.
""")
    st.code("Blackout Risk Score = 0.4 × disaster threat + 0.3 × grid weakness + 0.3 × device dependence",
            language=None)
    st.write("Disaster threat counts most because disasters cause the big, long outages. Grid weakness "
             "and device dependence decide how bad an outage gets for people. If one part has no data, "
             "the other two share its weight.")

    st.subheader("Limits to keep in mind")
    st.markdown("""
- emPOWER counts **Medicare** patients only, so the real number of people on powered devices is higher.
- Reliability numbers are averages for the whole utility, not your street.
- If a zip code's utility didn't report reliability, BlackoutReady uses the state average and says so.
- Backup times are estimates. Always plan with a doctor or equipment supplier.
""")

    st.subheader("Privacy")
    st.write("BlackoutReady uses only public, anonymous government data. It doesn't collect or store "
             "anything you type.")
