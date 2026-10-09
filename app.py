from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from pathlib import Path

# Load custom CSS
css_path = Path(__file__).parent / "streamlit" / "style.css"

if css_path.exists():
    with open(css_path, encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True
        )
else:
    st.warning(f"CSS file not found: {css_path}")

st.set_page_config(
    page_title="Clinical Trial Feasibility",
    page_icon="",
    layout="wide"
)

st.title("Clinical Trial Feasibility & Site Intelligence")
st.caption("Exploratory site assessment using synthetic data")


DATA_PATH = Path(__file__).parent / "data" / "sites_data.csv"
@st.cache_data
def load_data(path):
    return pd.read_csv(path)

try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error("Dataset not found. Generate data/sites_data.csv first.")
    st.stop()

#sidebar filters
st.sidebar.header("Filters")

selected_countries = st.sidebar.multiselect(
    "Country",
    options=sorted(df["country"].unique()),
    default=sorted(df["country"].unique())
)

selected_indications = st.sidebar.multiselect(
"Therapeutic Area",
    options=sorted(df["indication"].unique()),
    default=sorted(df["indication"].unique())
)

filtered_df = df[
    df["country"].isin(selected_countries)
    & df["indication"].isin(selected_indications)
]

#Key performance indicators
total_sites = filtered_df["site_id"].nunique()
median_recruitment = filtered_df["adjusted_recruitment"].median()
median_activation = filtered_df.drop_duplicates("site_id")["activation_days"].median()
low_risk_sites = (
    filtered_df.loc[filtered_df["risk_level"] == "Low", "site_id"].nunique()
)
medium_risk_sites = (
    filtered_df.loc[filtered_df["risk_level"] == "Medium", "site_id"].nunique()
)
high_risk_sites = (
    filtered_df.loc[filtered_df["risk_level"] == "High", "site_id"].nunique()

)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Sites", total_sites)
col2.metric(
"Median estimated recruitment",
f"{median_recruitment:.2f}" if pd.notna(median_recruitment) else "N/A"
)
col3.metric(
"Median activation time",
f"{median_activation:.0f} days" if pd.notna(median_activation) else "N/A"
)
col4.metric("Low-risk sites", low_risk_sites)
col5.metric("Medium-risk sites", medium_risk_sites)
col6.metric("High-risk sites", high_risk_sites)

st.divider()

#recruitment by site and indication
st.subheader("Site-TA Ranking by Recruitment Potential")

site_summary = (
    filtered_df[
        [
            "site_id",
            "country",
            "indication",
            "adjusted_recruitment",
            "risk_level"
        ]
    ]
    .loc[lambda x: x["risk_level"] != "High"]
    .sort_values(
        by="adjusted_recruitment",
        ascending=False
    )
)

fig = px.bar(
    site_summary.head(15),
    x="site_id",
    y="adjusted_recruitment",
    color="risk_level",
    hover_data=["country", "indication"],
    labels={
        "site_id": "Site",
        "adjusted_recruitment": "Estimated Recruitment (patients/month)",
        "risk_level": "Operational Risk"
    },
    #title="Site-TA Ranking by Recruitment Potential"
)
st.plotly_chart(fig, use_container_width=True)

#site-level table
st.subheader("Site Comparison")

site_table = (
    filtered_df.sort_values(
        "adjusted_recruitment", ascending=False
    )
    [[
        "site_id",
        "country",
        "indication",
        "eligible_patients_monthly",
        "screen_failure_rate",
        "competing_studies",
        "activation_days",
        "staff_capacity",
        "data_quality_score",
        "adjusted_recruitment",
        "risk_level"
    ]]
)

with st.expander("How is operational risk classified?"):
    st.markdown("""
    Operational risk is assigned using a rule-based classification
    based on four synthetic site-level indicators: activation time,
    data quality score, staff capacity, and competing studies.

    - **High:** activation > 120 days, data quality < 65,
      staff capacity ≤ 3, or competing studies ≥ 3.
    - **Medium:** no high-risk condition applies, but activation
      > 90 days, data quality < 80, staff capacity ≤ 5,
      or competing studies ≥ 2.
    - **Low:** none of these conditions apply.

    When multiple conditions apply, the highest applicable risk category takes precedence.These thresholds are illustrative assumptions, not validated
    industry standards. Risk levels indicate potential operational
    risks and are not validated predictions of site performance
    or recruitment outcomes.
    """)

st.dataframe(site_table, use_container_width=True, hide_index=True)
st.caption("Note: Data is synthetic and for demonstration purposes only. Recruitment estimates are illustrative and not based on real-world data.")