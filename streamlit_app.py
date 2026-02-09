from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(page_title="Rossmann Dashboard", layout="wide")

# ------------------ Find data ------------------
BASE_DIR = Path(__file__).resolve().parent
CANDIDATE_DATA_DIRS = [BASE_DIR / "data", BASE_DIR.parent / "data", Path.cwd() / "data"]

def find_data_dir():
    for d in CANDIDATE_DATA_DIRS:
        if (d / "train.csv").exists() and (d / "store.csv").exists():
            return d
    return None

DATA_DIR = find_data_dir()
if DATA_DIR is None:
    st.error(
        "Không tìm thấy train.csv / store.csv.\n"
        "Hãy đảm bảo có thư mục data/ nằm cạnh file streamlit_app.py và chứa train.csv + store.csv.\n\n"
        "Đã thử:\n" + "\n".join([str(x) for x in CANDIDATE_DATA_DIRS])
    )
    st.stop()

@st.cache_data
def load_df():
    train = pd.read_csv(DATA_DIR / "train.csv", low_memory=False)
    store = pd.read_csv(DATA_DIR / "store.csv", low_memory=False)
    df = train.merge(store, on="Store", how="left")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    if "Open" in df.columns:
        df = df[df["Open"] == 1].copy()
    return df

df = load_df()

st.title("📊 Rossmann Sales Dashboard")

# ------------------ Sidebar filters ------------------
st.sidebar.header("Filters")

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
else:
    start_date = pd.to_datetime(min_date)
    end_date = pd.to_datetime(max_date)

df_f = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

def multiselect_if_exists(col, label):
    if col in df_f.columns:
        opts = sorted([x for x in df_f[col].dropna().unique()])
        sel = st.sidebar.multiselect(label, opts, default=opts)
        if sel:
            return df_f[df_f[col].isin(sel)].copy()
    return df_f

df_f = multiselect_if_exists("StoreType", "StoreType")
df_f = multiselect_if_exists("Assortment", "Assortment")

if "Promo" in df_f.columns:
    promo_sel = st.sidebar.multiselect("Promo", options=[0, 1], default=[0, 1])
    df_f = df_f[df_f["Promo"].isin(promo_sel)].copy()

# optional: chọn vài store
if "Store" in df_f.columns:
    store_count = df_f["Store"].nunique()
    st.sidebar.caption(f"Stores in data: {store_count}")
    if store_count <= 200:
        store_opts = sorted(df_f["Store"].dropna().unique().astype(int).tolist())
        chosen = st.sidebar.multiselect("Stores (optional)", store_opts, default=store_opts)
        if chosen:
            df_f = df_f[df_f["Store"].isin(chosen)].copy()

# ------------------ KPI ------------------
c1, c2, c3, c4 = st.columns(4)
total_sales = float(df_f["Sales"].sum()) if "Sales" in df_f.columns else 0.0
avg_sales = float(df_f["Sales"].mean()) if "Sales" in df_f.columns and len(df_f) else 0.0
n_stores = int(df_f["Store"].nunique()) if "Store" in df_f.columns else 0
n_days = int(df_f["Date"].nunique()) if "Date" in df_f.columns else 0

c1.metric("Total Sales", f"{total_sales:,.0f}")
c2.metric("Avg Sales / day-row", f"{avg_sales:,.0f}")
c3.metric("Stores", f"{n_stores:,}")
c4.metric("Days", f"{n_days:,}")

st.divider()

# ------------------ Q1: Total sales over time ------------------
st.subheader("Q1 — Total Sales Over Time")
daily = df_f.groupby("Date", as_index=False)["Sales"].sum().sort_values("Date")
line = (
    alt.Chart(daily)
    .mark_line()
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Sales:Q", title="Total Sales"),
        tooltip=[alt.Tooltip("Date:T"), alt.Tooltip("Sales:Q", format=",.0f")],
    )
    .properties(height=320)
)
st.altair_chart(line, use_container_width=True)

# ------------------ Q2: Sales by day of week ------------------
st.subheader("Q2 — Sales by Day of Week")
if "DayOfWeek" in df_f.columns:
    dow = df_f.groupby("DayOfWeek", as_index=False)["Sales"].sum()
    dow["DayOfWeek"] = pd.to_numeric(dow["DayOfWeek"], errors="coerce").astype("Int64")
    dow = dow.dropna(subset=["DayOfWeek"]).sort_values("DayOfWeek")
    bar = (
        alt.Chart(dow)
        .mark_bar()
        .encode(
            x=alt.X("DayOfWeek:O", title="DayOfWeek (1=Mon … 7=Sun)"),
            y=alt.Y("Sales:Q", title="Total Sales"),
            tooltip=[alt.Tooltip("DayOfWeek:O"), alt.Tooltip("Sales:Q", format=",.0f")],
        )
        .properties(height=280)
    )
    st.altair_chart(bar, use_container_width=True)
else:
    st.info("Không có cột DayOfWeek trong data.")

# ------------------ Q3: Promo vs no promo (boxplot) ------------------
st.subheader("Q3 — Promo vs No Promo (Sales Distribution)")
if "Promo" in df_f.columns:
    df_box = df_f[["Promo", "Sales"]].dropna().copy()
    df_box["Promo"] = df_box["Promo"].astype(int).astype(str).replace({"0": "No Promo", "1": "Promo"})
    box = (
        alt.Chart(df_box)
        .mark_boxplot()
        .encode(
            x=alt.X("Promo:N", title="Promo"),
            y=alt.Y("Sales:Q", title="Sales"),
        )
        .properties(height=280)
    )
    st.altair_chart(box, use_container_width=True)
else:
    st.info("Không có cột Promo trong data.")

# ------------------ Q6: StoreType performance ------------------
st.subheader("Q6 — StoreType Performance")
if "StoreType" in df_f.columns:
    stype = df_f.groupby("StoreType", as_index=False)["Sales"].mean().sort_values("Sales", ascending=False)
    bar2 = (
        alt.Chart(stype)
        .mark_bar()
        .encode(
            x=alt.X("StoreType:N", title="StoreType"),
            y=alt.Y("Sales:Q", title="Avg Sales"),
            tooltip=[alt.Tooltip("StoreType:N"), alt.Tooltip("Sales:Q", format=",.0f")],
        )
        .properties(height=280)
    )
    st.altair_chart(bar2, use_container_width=True)
else:
    st.info("Không có cột StoreType trong data.")

# ------------------ Q10: Top 10 stores ------------------
st.subheader("Q10 — Top 10 Stores (by Total Sales)")
if "Store" in df_f.columns:
    top10 = (
        df_f.groupby("Store", as_index=False)["Sales"].sum()
        .sort_values("Sales", ascending=False)
        .head(10)
    )
    top10["Store"] = top10["Store"].astype(int).astype(str)
    bar3 = (
        alt.Chart(top10)
        .mark_bar()
        .encode(
            y=alt.Y("Store:N", sort="-x", title="Store"),
            x=alt.X("Sales:Q", title="Total Sales"),
            tooltip=[alt.Tooltip("Store:N"), alt.Tooltip("Sales:Q", format=",.0f")],
        )
        .properties(height=320)
    )
    st.altair_chart(bar3, use_container_width=True)
else:
    st.info("Không có cột Store trong data.")
