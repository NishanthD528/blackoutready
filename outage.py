"""Power out page: live countdowns for the device battery and the fridge."""
import time

import streamlit as st

from common import FRIDGE_SAFE_HOURS, format_time

_, center, _ = st.columns([1, 3, 1])
with center:
    st.title(":material/power_off: Did the power just go out?")

    if st.session_state.outage_start is None:
        st.write("Tap the button. BlackoutReady starts a countdown for your battery and your fridge, "
                 "and tells you when to act.")
        if st.session_state.battery_hours == 0:
            st.page_link("views/backup.py", label="Tip: set up your battery first for a device countdown",
                         icon=":material/battery_charging_full:")
        if st.button("Power just went out", type="primary", icon=":material/power_off:", width="stretch"):
            st.session_state.outage_start = time.time()
            st.rerun()
    else:
        @st.fragment(run_every=1)
        def countdown():
            elapsed = time.time() - st.session_state.outage_start
            battery_left = st.session_state.battery_hours * 3600 - elapsed
            fridge_left = FRIDGE_SAFE_HOURS * 3600 - elapsed

            st.write(f"Power has been out for **{format_time(elapsed)}**")

            c1, c2 = st.columns(2)
            with c1.container(border=True):
                if st.session_state.battery_hours > 0:
                    st.metric("Device battery left", format_time(battery_left))
                    st.progress(max(0.0, battery_left / (st.session_state.battery_hours * 3600)))
                    st.caption("Estimate")
                else:
                    st.markdown("**Device battery**")
                    st.caption("Set up your battery on the My backup power page to see a countdown.")
            with c2.container(border=True):
                st.metric("Fridge food & medicine", format_time(fridge_left))
                st.progress(max(0.0, fridge_left / (FRIDGE_SAFE_HOURS * 3600)))
                st.caption("Keep the door closed (USDA: about 4 hours)")

            if st.session_state.battery_hours > 0 and battery_left <= 0:
                st.error("Your battery may be empty. Call 911 if you need help breathing or are in danger.",
                         icon=":material/emergency:")
            elif st.session_state.battery_hours > 0 and battery_left < 3600:
                st.error("Less than 1 hour of battery left. Go to a charging location now or call your equipment supplier.",
                         icon=":material/battery_alert:")
            else:
                st.info("Next step: before your battery gets below 1 hour, plan where you'll go to charge it.",
                        icon=":material/directions_walk:")

        countdown()

        if st.button("Power is back", icon=":material/power:"):
            st.session_state.outage_start = None
            st.rerun()
