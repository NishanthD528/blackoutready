"""National map page: compare counties in any state."""
import plotly.express as px
import streamlit as st

from common import SOURCES, load_counties, load_county_shapes

counties = load_counties()
shapes = load_county_shapes()

st.title(":material/map: Where are people most at risk?")
states = sorted(counties["State"].dropna().unique())
c1, c2 = st.columns([1, 3])
state = c1.selectbox("State", states, index=states.index("CA"))
color_by = c2.radio("Color counties by", ["People on powered devices", "Biggest disaster threat"], horizontal=True)
in_state = counties[counties["State"] == state]

map_col, side_col = st.columns([2, 1], gap="large")

with map_col:
    color_col = "on_devices" if color_by == "People on powered devices" else "biggest_hazard_score"
    fig = px.choropleth(
        in_state, geojson=shapes, locations="FIPS_Code", color=color_col,
        hover_name="County",
        hover_data={"FIPS_Code": False, "on_devices": ":,", "medicare_patients": ":,",
                    "biggest_hazard": True, "biggest_hazard_score": ":.0f"},
        labels={"on_devices": "On powered devices", "medicare_patients": "Medicare patients",
                "biggest_hazard": "Biggest threat", "biggest_hazard_score": "Threat score"},
        color_continuous_scale="Oranges",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=520)
    st.plotly_chart(fig)
    st.caption("Hover over a county to see its numbers.")

with side_col:
    total = int(in_state["on_devices"].sum())
    st.metric(f"People on powered devices in {state}", f"{total:,}", border=True)
    top_threat = in_state["biggest_hazard"].value_counts()
    if not top_threat.empty:
        st.metric(f"Most common top threat in {state}", top_threat.index[0], border=True)
    top = in_state.sort_values("on_devices", ascending=False).head(8)
    st.markdown(f"**Counties with the most people on devices**")
    st.dataframe(
        top[["County", "on_devices", "biggest_hazard"]].rename(columns={
            "on_devices": "On devices", "biggest_hazard": "Biggest threat"}),
        hide_index=True, width="stretch",
        column_config={"On devices": st.column_config.NumberColumn(format="localized")},
    )

st.caption(SOURCES)
