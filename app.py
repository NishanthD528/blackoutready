"""BlackoutReady — main file. Sets up the pages and the top navigation bar.

Run with:  python3.12 -m streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="BlackoutReady", page_icon=":material/bolt:", layout="wide")

# Memory shared by all pages (survives switching pages)
if "battery_hours" not in st.session_state:
    st.session_state.battery_hours = 0.0
if "outage_start" not in st.session_state:
    st.session_state.outage_start = None
if "zip_code" not in st.session_state:
    st.session_state.zip_code = "94538"

home = st.Page("views/home.py", title="Home", icon=":material/bolt:", default=True)
my_area = st.Page("views/my_area.py", title="My area", icon=":material/home_pin:", url_path="my-area")
national = st.Page("views/national_map.py", title="National map", icon=":material/map:", url_path="national-map")
backup = st.Page("views/backup.py", title="My backup power", icon=":material/battery_charging_full:", url_path="backup")
outage = st.Page("views/outage.py", title="Power out!", icon=":material/power_off:", url_path="power-out")
about = st.Page("views/about.py", title="How it works", icon=":material/info:", url_path="how-it-works")

nav = st.navigation([home, my_area, national, backup, outage, about], position="top")
nav.run()
