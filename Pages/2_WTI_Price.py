from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="WTI Price", layout="wide")

st.title("WTI Crude Oil Price")
st.caption("Source: U.S. Energy Information Administration")

# Get API key
try:
    API_KEY = st.secrets["EIA_API_KEY"]
except:
    st.error("Missing EIA API key. Set it in Streamlit Secrets as EIA_API_KEY.")
    st.stop()

# EIA WTI API
URL = (
    "https://api.eia.gov/v2/petroleum/pri/spt/data/"
    f"?api_key={API_KEY}"
    "&frequency=weekly"
    "&data[0]=value"
    "&facets[series][]=RWTC"
    "&sort[0][column]=period"
    "&sort[0][direction]=desc"
    "&offset=0&length=5000"
)

response = requests.get(URL)
data_json = response.json()

if "response" not in data_json:
    st.error("Error fetching data from EIA.")
    st.stop()

data = data_json["response"]["data"]

df = pd.DataFrame(data)

if df.empty:
    st.error("No data returned.")
    st.stop()

# Convert date
df["week"] = pd.to_datetime(df["period"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = df.dropna()

# Filter 2012-present
df = df[df["week"] >= pd.to_datetime("2012-01-01")]

if df.empty:
    st.error("No data after filtering.")
    st.stop()

st.metric("Latest WTI Price ($/barrel)", f"{df['value'].iloc[-1]:,.2f}")

# Plot
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df["week"], df["value"])
ax.set_title("WTI Crude Oil Spot Price (Weekly)")
ax.set_xlabel("Year")
ax.set_ylabel("Price ($/barrel)")
ax.grid(True)

st.pyplot(fig)
