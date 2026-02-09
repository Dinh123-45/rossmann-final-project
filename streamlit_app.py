from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Rossmann Dashboard", layout="wide")
REPO_DIR = Path(__file__).resolve().parent  # streamlit_app.py nằm ở root

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

st.title("Rossmann Store Sales Dashboard (Sample)")

# ===== Sidebar filters =====
st.sidebar.header("Filters")

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input("Date range", (min_date, max_date))

# store type filter (optional)
store_types = ["All"] + sorted(df["StoreType"].dropna().unique().tolist())
store_type = st.sidebar.selectbox("StoreType", store_types)

start = pd.to_datetime(date_range[0])
end = pd.to_datetime(date_range[1])

f = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
if store_type != "All":
    f = f[f["StoreType"] == store_type]

# ===== KPIs =====
c1, c2, c3 = st.columns(3)
c1.metric("Total Sales", int(f["Sales"].sum()))
c2.metric("Avg Sales", round(f["Sales"].mean(), 2))
c3.metric("Total Customers", int(f["Customers"].sum()))

st.divider()

# Layout 2 columns
left, right = st.columns(2)

# ===== Q1 =====
with left:
    st.subheader("Q1. Total Sales Over Time")
    daily_sales = f.groupby("Date")["Sales"].sum()
    fig = plt.figure()
    daily_sales.plot()
    plt.ylabel("Sales")
    st.pyplot(fig)

# ===== Q2 =====
with right:
    st.subheader("Q2. Avg Sales by DayOfWeek")
    dow = f.groupby("DayOfWeek")["Sales"].mean().sort_index()
    fig = plt.figure()
    dow.plot(kind="bar")
    plt.xlabel("DayOfWeek (1=Mon ... 7=Sun)")
    plt.ylabel("Avg Sales")
    st.pyplot(fig)

st.divider()

left2, right2 = st.columns(2)

# ===== Q3 =====
st.subheader("Q3. Promo vs Sales (Boxplot)")

fig, ax = plt.subplots()
f.boxplot(column="Sales", by="Promo", ax=ax)
ax.set_yscale("log")
ax.set_title("Sales with/without Promo (log scale)")
ax.set_xlabel("Promo (0=No, 1=Yes)")
ax.set_ylabel("Sales (log)")
fig.suptitle("")
st.pyplot(fig)

# ===== Q6 =====
with right2:
    st.subheader("Q6. Avg Sales by StoreType")
    stype = f.groupby("StoreType")["Sales"].mean().sort_values(ascending=False)
    fig = plt.figure()
    stype.plot(kind="bar")
    plt.ylabel("Avg Sales")
    st.pyplot(fig)

st.divider()

left3, right3 = st.columns(2)

# ===== Q8 =====
with left3:
    st.subheader("Q8. Sales vs Customers (Scatter sample)")
    sample_scatter = f.sample(min(20000, len(f)), random_state=42)
    fig = plt.figure()
    plt.scatter(sample_scatter["Customers"], sample_scatter["Sales"], s=5)
    plt.xlabel("Customers")
    plt.ylabel("Sales")
    st.pyplot(fig)

# ===== Q10 =====
with right3:
    st.subheader("Q10. Top 10 Stores by Avg Sales")
    top10 = f.groupby("Store")["Sales"].mean().sort_values(ascending=False).head(10)
    fig = plt.figure()
    top10.sort_values().plot(kind="barh")
    plt.xlabel("Avg Sales")
    st.pyplot(fig)



st.divider()
st.subheader("Data preview")
st.dataframe(f.head(50))


