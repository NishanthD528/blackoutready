"""Home page: what BlackoutReady is, the national picture, and where to go next."""
import streamlit as st

from common import SOURCES, load_counties, load_zips

counties = load_counties()
zips = load_zips()

_, center, _ = st.columns([1, 6, 1])
with center:
    st.title(":material/bolt: BlackoutReady")
    st.markdown("### When the power goes out, some people have hours, not days.")
    st.write("Oxygen machines, ventilators, home dialysis, and power wheelchairs all need electricity. "
             "BlackoutReady combines four federal datasets to show **who depends on power**, **how strong "
             "the local grid is**, **what disasters threaten it**, and **how much time** people have when it fails.")

    # Quick zip search that jumps straight to the My area page
    with st.form("home_search", border=True):
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        typed = c1.text_input("Check your area", st.session_state.zip_code, max_chars=5,
                              placeholder="Enter a zip code")
        go = c2.form_submit_button("Check risk", type="primary", icon=":material/search:", width="stretch")
    if go:
        st.session_state.zip_code = typed.strip()
        st.switch_page("views/my_area.py")

    # National numbers, calculated live from the data
    st.markdown("#### The national picture")
    total_devices = int(counties["on_devices"].sum())
    high_risk_zips = int((zips["risk_score"] >= 75).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Medicare patients on powered devices", f"{total_devices:,}", border=True)
    c2.metric("Zip codes analyzed", f"{len(zips):,}", border=True)
    c3.metric("Zip codes at High blackout risk", f"{high_risk_zips:,}", border=True)

    st.markdown("#### What you can do here")
    c1, c2 = st.columns(2)
    with c1.container(border=True):
        st.markdown("**:material/home_pin: See your area's risk**")
        st.caption("Your Blackout Risk Score, power company, grid reliability, biggest disaster threats, and a map of people nearby.")
        st.page_link("views/my_area.py", label="Open My area", icon=":material/arrow_forward:")
    with c2.container(border=True):
        st.markdown("**:material/map: Explore the national map**")
        st.caption("Compare every county in any state by people on devices or by disaster threat.")
        st.page_link("views/national_map.py", label="Open the map", icon=":material/arrow_forward:")
    with c1.container(border=True):
        st.markdown("**:material/battery_charging_full: Check your backup power**")
        st.caption("Find out how long your backup battery can run your medical device.")
        st.page_link("views/backup.py", label="Open calculator", icon=":material/arrow_forward:")
    with c2.container(border=True):
        st.markdown("**:material/power_off: Power just went out?**")
        st.caption("Start live countdowns for your battery and fridge, with clear next steps.")
        st.page_link("views/outage.py", label="Start countdown", icon=":material/arrow_forward:")

    st.caption(SOURCES)
