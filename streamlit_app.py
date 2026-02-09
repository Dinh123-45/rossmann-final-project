from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Rossmann Dashboard", layout="wide")

REPO_DIR = Path(__file__).resolve().parent  # vì streamlit_app.py nằm ở root repo

@st.cache_data
def load_data():
    train = pd.read_csv(REPO_DIR / "train_sample.csv", low_memory=False)
    store = pd.read_csv(REPO_DIR / "store.csv", low_memory=False)

    df = train.merge(store, on="Store", how="left")

    df["Date"] = pd.to_datetime(df["Date"])
    df["StateHoliday"] = df["StateHoliday"].astype(str).replace({"0": "None"})
    df["CompetitionDistance"] = df["CompetitionDistance"].fillna(df["CompetitionDistance"].median())

    df_open = df[df["Open"] == 1].copy()
    return df_open

df = load_data()

st.title("Rossmann Store Sales Dashboard (Sample Data)")

# KPI
c1, c2, c3 = st.columns(3)
c1.metric("Total Sales", int(df["Sales"].sum()))
c2.metric("Avg Sales", round(df["Sales"].mean(), 2))
c3.metric("Total Customers", int(df["Customers"].sum()))

st.divider()

# Q1: Total Sales Over Time
st.subheader("Q1. Total Sales Over Time")
daily_sales = df.groupby("Date")["Sales"].sum()

fig = plt.figure()
daily_sales.plot()
plt.ylabel("Sales")
st.pyplot(fig)

st.divider()
st.subheader("Preview")
st.dataframe(df.head(30))

