import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Petroleum Supply vs WTI (EIA)", layout="wide")
st.title("Correlation between Weekly U.S. Petroleum Product Supplied (Total) and WTI Spot Price")
st.caption("Source: U.S. Energy Information Administration (EIA API v2). Two datasets pulled from EIA and aligned weekly.")

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("Controls")

# Local: you can type your key in the sidebar
# Cloud deploy: you can store it in Streamlit Secrets (EIA_API_KEY)
default_key = ""
try:
    default_key = st.secrets.get("EIA_API_KEY", "")
except Exception:
    default_key = ""

EIA_API_KEY = st.sidebar.text_input("EIA API Key", value=default_key, type="password")

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
    st.warning("Please enter your EIA API key in the sidebar (local) or set it in Streamlit Secrets (deployment).")
    st.stop()

# -----------------------------
# Helper: simple GET with error handling
# -----------------------------
def eia_get_json(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# -----------------------------
# Dataset 1: wpsup (ALL products), weekly -> SUM across products by week
# -----------------------------
@st.cache_data
def load_total_petroleum_supply_weekly(api_key: str) -> pd.DataFrame:
    """
    Pull weekly petroleum product supplied for ALL products (wpsup).
    Because multiple products exist per week, we aggregate to a single total per week.
    We standardize week as W-FRI (week ending Friday) to align datasets.
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

    js = eia_get_json(url)
    data = js.get("response", {}).get("data", [])
    df = pd.DataFrame(data)

    if df.empty:
        return df

    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["period", "value"])

    # Standardize to a weekly key (week ending Friday)
    df["week"] = df["period"].dt.to_period("W-FRI").dt.end_time.dt.normalize()

    # Aggregate ALL products to a single total per week
    total = (
        df.groupby("week", as_index=False)["value"]
          .sum()
          .rename(columns={"value": "total_petroleum_supply"})
          .sort_values("week")
    )
    return total

# -----------------------------
# Dataset 2: WTI spot price (RWTC), weekly -> MEAN by week (just in case)
# -----------------------------
@st.cache_data
def load_wti_spot_price_weekly(api_key: str) -> pd.DataFrame:
    """
    Pull weekly WTI spot price series RWTC (Cushing, OK WTI Spot Price FOB).
    Standardize week as W-FRI to align datasets.
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

    js = eia_get_json(url)
    data = js.get("response", {}).get("data", [])
    df = pd.DataFrame(data)

    if df.empty:
        return df

    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["period", "value"])

    # Standardize to weekly key (week ending Friday)
    df["week"] = df["period"].dt.to_period("W-FRI").dt.end_time.dt.normalize()

    wti = (
        df.groupby("week", as_index=False)["value"]
          .mean()
          .rename(columns={"value": "wti_usd_per_bbl"})
          .sort_values("week")
    )
    return wti

# -----------------------------
# Load data
# -----------------------------
try:
    supply = load_total_petroleum_supply_weekly(EIA_API_KEY)
    wti = load_wti_spot_price_weekly(EIA_API_KEY)
except requests.HTTPError as e:
    st.error(f"API request failed: {e}")
    st.stop()
except Exception as e:
    st.error(f"Unexpected error while loading data: {e}")
    st.stop()

if supply.empty:
    st.error("Supply dataset returned no rows. Check your API key or the endpoint.")
    st.stop()

if wti.empty:
    st.error("WTI dataset returned no rows. Check your API key or the endpoint.")
    st.stop()

# Filter by selected dates (using week)
supply = supply[(supply["week"] >= start_ts) & (supply["week"] <= end_ts)].copy()
wti = wti[(wti["week"] >= start_ts) & (wti["week"] <= end_ts)].copy()

# Merge on standardized weekly key
merged = pd.merge(supply, wti, on="week", how="inner").sort_values("week")

if merged.empty:
    st.warning("No overlapping weeks after matching. Expand the date range or verify data availability.")
    st.stop()

# Rolling averages
if rolling_weeks > 1:
    merged["supply_ra"] = merged["total_petroleum_supply"].rolling(rolling_weeks).mean()
    merged["wti_ra"] = merged["wti_usd_per_bbl"].rolling(rolling_weeks).mean()
else:
    merged["supply_ra"] = merged["total_petroleum_supply"]
    merged["wti_ra"] = merged["wti_usd_per_bbl"]

# -----------------------------
# Metrics
# -----------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Latest Total Product Supplied", f"{merged['total_petroleum_supply'].iloc[-1]:,.0f}")
c2.metric("Latest WTI (USD/bbl)", f"{merged['wti_usd_per_bbl'].iloc[-1]:.2f}")
corr = merged[["total_petroleum_supply", "wti_usd_per_bbl"]].corr().iloc[0, 1]
c3.metric("Correlation", f"{corr:.2f}")

st.markdown("---")

# -----------------------------
# Plot: Dual axis time series
# -----------------------------
st.subheader("Weekly Trends (Aligned to Week Ending Friday)")

fig, ax1 = plt.subplots()
ax1.plot(merged["week"], merged["supply_ra"], label="Total Product Supplied")
ax1.set_xlabel("Week")
ax1.set_ylabel("Total Product Supplied (sum of values)")

ax2 = ax1.twinx()
ax2.plot(merged["week"], merged["wti_ra"], label="WTI Spot Price (USD/bbl)")
ax2.set_ylabel("WTI (USD per barrel)")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

st.pyplot(fig)


# -----------------------------
# Data preview / debugging
# -----------------------------
with st.expander("Show merged data"):
    st.dataframe(merged)

st.markdown("---")
st.caption("Note: 'Product supplied' is commonly used as a proxy for petroleum product demand. This app explores association, not causation.")
st.caption("Team Members: Add names here")
