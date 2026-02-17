import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# -----------------------
# Page Config
# -----------------------
st.set_page_config(page_title="Petroleum Supply vs WTI (EIA)", layout="wide")
st.title("Corelation between Weekly U.S. Petroleum Product Supplied (Total) and WTI Spot Price")
st.caption("Source: U.S. Energy Information Administration (EIA API v2). Two datasets pulled from EIA and aligned weekly.")

# -----------------------
# Sidebar Controls
# -----------------------
st.sidebar.header("Controls")

# Prefer Streamlit Secrets for deployment; fallback to sidebar input for local runs
DEFAULT_KEY = st.secrets.get("EIA_API_KEY", "")
EIA_API_KEY = st.sidebar.text_input("EIA API Key", value=DEFAULT_KEY, type="password")

rolling_weeks = st.sidebar.slider("Rolling Average (weeks)", 1, 12, 1)
show_scatter = st.sidebar.checkbox("Show scatter plot", value=True)

default_start = pd.Timestamp("2018-01-01")
default_end = pd.Timestamp.today().normalize()
start_date = st.sidebar.date_input("Start date", value=default_start)
end_date = st.sidebar.date_input("End date", value=default_end)

start_ts = pd.to_datetime(start_date)
end_ts = pd.to_datetime(end_date)

if start_ts >= end_ts:
    st.error("Start date must be before end date.")
    st.stop()

if not EIA_API_KEY:
    st.warning("Please provide an EIA API key (sidebar or Streamlit Secrets).")
    st.stop()

# -----------------------
# Helpers
# -----------------------
def eia_get(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# -----------------------
# Load Dataset 1: All Petroleum Product Supplied (weekly) -> aggregate to total by period
# -----------------------
@st.cache_data
def load_total_petroleum_supply(api_key: str) -> pd.DataFrame:
    """
    Pull ALL petroleum products supplied (weekly) from /petroleum/cons/wpsup/.
    Since multiple products are returned, aggregate (sum) by period to produce
    a single national total weekly series.
    """
    url = (
        "https://api.eia.gov/v2/petroleum/cons/wpsup/data/"
        f"?api_key={api_key}"
        "&frequency=weekly"
        "&data[0]=value"
        "&sort[0][column]=period"
        "&sort[0][direction]=asc"
        "&offset=0"
        "&length=5000"
    )

    js = eia_get(url)
    data = js.get("response", {}).get("data", [])
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["period", "value"])
    df["period"] = df["period"].dt.to_period("W").dt.to_timestamp()


    # Aggregate all products to total per week
    total = (
        df.groupby("period", as_index=False)["value"]
        .sum()
        .rename(columns={"value": "total_petroleum_supply_bpd"})
        .sort_values("period")
    )
    return total

# -----------------------
# Load Dataset 2: WTI Spot Price (RWTC) (weekly)
# -----------------------
@st.cache_data
def load_wti_price(api_key: str) -> pd.DataFrame:
    """
    Pull weekly WTI spot price from /petroleum/pri/spt/ with series RWTC.
    """
    url = (
        "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        f"?api_key={api_key}"
        "&frequency=weekly"
        "&data[0]=value"
        "&facets[series][]=RWTC"
        "&sort[0][column]=period"
        "&sort[0][direction]=asc"
        "&offset=0"
        "&length=5000"
    )

    js = eia_get(url)
    data = js.get("response", {}).get("data", [])
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["period", "value"])
    df["period"] = df["period"].dt.to_period("W").dt.to_timestamp()


    # Keep only essentials; series column may exist but we filtered it already
    out = df[["period", "value"]].rename(columns={"value": "wti_usd_per_bbl"}).sort_values("period")
    return out

# -----------------------
# Load and filter
# -----------------------
supply = load_total_petroleum_supply(EIA_API_KEY)
wti = load_wti_price(EIA_API_KEY)

if supply.empty:
    st.error("Supply dataset returned no rows. Check the API key or endpoint.")
    st.stop()

if wti.empty:
    st.error("WTI dataset returned no rows. Check the API key or endpoint.")
    st.stop()

# Filter date range
supply = supply[(supply["period"] >= start_ts) & (supply["period"] <= end_ts)].copy()
wti = wti[(wti["period"] >= start_ts) & (wti["period"] <= end_ts)].copy()

supply = supply.sort_values("period")
wti = wti.sort_values("period")

merged = pd.merge_asof(
    supply,
    wti,
    on="period",
    direction="nearest",
    tolerance=pd.Timedelta("7D")
)

# merge_asof 
merged = merged.dropna(subset=["wti_usd_per_bbl"]).sort_values("period")

if merged.empty:
    st.warning("No overlapping weeks after matching. Try expanding the date range.")
    st.stop()


# Rolling averages
if rolling_weeks > 1:
    merged["supply_ra"] = merged["total_petroleum_supply_bpd"].rolling(rolling_weeks).mean()
    merged["wti_ra"] = merged["wti_usd_per_bbl"].rolling(rolling_weeks).mean()
else:
    merged["supply_ra"] = merged["total_petroleum_supply_bpd"]
    merged["wti_ra"] = merged["wti_usd_per_bbl"]

# -----------------------
# Metrics
# -----------------------
c1, c2, c3 = st.columns(3)
c1.metric("Latest Total Product Supplied (bpd)", f"{merged['total_petroleum_supply_bpd'].iloc[-1]:,.0f}")
c2.metric("Latest WTI (USD/bbl)", f"{merged['wti_usd_per_bbl'].iloc[-1]:.2f}")
corr = merged[["total_petroleum_supply_bpd", "wti_usd_per_bbl"]].corr().iloc[0, 1]
c3.metric("Correlation (Supply vs WTI)", f"{corr:.2f}")

st.markdown("---")

# -----------------------
# Plot 1: Dual-axis weekly trends
# -----------------------
st.subheader("Weekly Trends (Dual Axis)")

fig, ax1 = plt.subplots()
ax1.plot(merged["period"], merged["supply_ra"], label="Total Product Supplied (bpd)")
ax1.set_xlabel("Week")
ax1.set_ylabel("Total Product Supplied (barrels/day)")

ax2 = ax1.twinx()
ax2.plot(merged["period"], merged["wti_ra"], label="WTI Spot Price (USD/bbl)")
ax2.set_ylabel("WTI (USD per barrel)")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

st.pyplot(fig)

# -----------------------
# Plot 2: Scatter
# -----------------------
if show_scatter:
    st.subheader("Supply vs WTI (Scatter)")
    fig2, ax = plt.subplots()
    ax.scatter(merged["wti_usd_per_bbl"], merged["total_petroleum_supply_bpd"])
    ax.set_xlabel("WTI (USD/bbl)")
    ax.set_ylabel("Total Product Supplied (barrels/day)")
    st.pyplot(fig2)

# -----------------------
# Data preview
# -----------------------
with st.expander("Show merged data"):
    st.dataframe(merged)

st.markdown("---")
st.caption("Note: 'Product supplied' is commonly used as a proxy for petroleum consumption. This app explores association, not causation.")
st.caption("Team Members: Add names here")
