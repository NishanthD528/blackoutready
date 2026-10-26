"""Backup power page: how long a battery can run a medical device."""
import streamlit as st

from common import BATTERY_EFFICIENCY, format_time

_, center, _ = st.columns([1, 3, 1])
with center:
    st.title(":material/battery_charging_full: How long will my backup last?")
    st.write("Find two numbers on your labels, and BlackoutReady estimates how long your backup battery "
             "can run your device.")

    with st.container(border=True):
        device = st.selectbox("Device", ["Oxygen concentrator", "CPAP or BiPAP", "Home ventilator", "Other"])
        c1, c2 = st.columns(2)
        watts = c1.number_input("Device power (watts)", min_value=1, value=300, step=10,
                                help="Look for a number followed by W on the device's label or manual.")
        battery_wh = c2.number_input("Battery size (watt-hours)", min_value=0, value=1000, step=100,
                                     help="Look for a number followed by Wh on the battery's label.")
        if st.button("Calculate", type="primary", icon=":material/calculate:", width="stretch"):
            st.session_state.battery_hours = battery_wh * BATTERY_EFFICIENCY / watts

    if st.session_state.battery_hours > 0:
        with st.container(border=True):
            st.metric(f"Estimated backup time for your {device.lower()}",
                      format_time(st.session_state.battery_hours * 3600))
            st.caption(f"{battery_wh:,} Wh × {BATTERY_EFFICIENCY:.0%} usable ÷ {watts} W")
            st.page_link("views/outage.py", label="Power out? Start a live countdown",
                         icon=":material/power_off:")

    st.warning("This is an estimate. Make a backup plan with your doctor or equipment supplier. "
               "In an emergency, call 911.", icon=":material/medical_services:")
