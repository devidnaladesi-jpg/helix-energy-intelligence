
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ============================================================
# HELIX | Energy Intelligence
# Excel-backed simulation dashboard
#
# Navigation:
#   Overview
#   Comparison & Drilldown
#   Meter Intelligence
#   Anomalies & Actions
#   Data Quality
#
# Main workflow:
#   Monitor -> Compare -> Identify -> Understand -> Act -> Verify
# ============================================================

st.set_page_config(
    page_title="HELIX | Energy Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .stApp { background: #f7f9fb; }
    [data-testid="stSidebar"] { background: #eef4f7; }
    .title { font-size: 29px; font-weight: 750; color: #17324d; margin-bottom: 0; }
    .subtitle { color: #65747d; font-size: 13px; margin-bottom: 15px; }
    .card { background: white; border: 1px solid #d9e3e8; border-radius: 12px; padding: 14px 16px; }
    .kpi-label { color: #687780; font-size: 12px; }
    .kpi-value { color: #17324d; font-size: 22px; font-weight: 750; margin-top: 2px; }
    .insight { background: #eef6fa; border-left: 4px solid #2a6f97; padding: 11px 13px; border-radius: 8px; margin: 6px 0; color: #24485d; }
    .warning { background: #fff6e9; border-left: 4px solid #c48517; padding: 11px 13px; border-radius: 8px; margin: 6px 0; color: #6f5317; }
    .small { color: #6c7a82; font-size: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Excel data loader
# -----------------------------
DATA_FILE = Path(__file__).with_name("Helix_Energy_Intelligence_Simulation_Data.xlsx")

@st.cache_data
def load_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Excel data file not found: {DATA_FILE.name}. "
            "Keep the workbook in the same folder as app.py."
        )

    master = pd.read_excel(DATA_FILE, sheet_name="Meter_Master")
    raw = pd.read_excel(DATA_FILE, sheet_name="Raw_Meter_Data")
    summary = pd.read_excel(DATA_FILE, sheet_name="Building_Summary")
    anomalies = pd.read_excel(DATA_FILE, sheet_name="Anomalies")
    rules = pd.read_excel(DATA_FILE, sheet_name="Anomaly_Rules")

    # Excel may load date fields as serial numbers; convert them safely.
    for col in ["Timestamp", "Date"]:
        if col in raw.columns and pd.api.types.is_numeric_dtype(raw[col]):
            raw[col] = pd.to_datetime(raw[col], unit="D", origin="1899-12-30")
        else:
            raw[col] = pd.to_datetime(raw[col], errors="coerce")

    for col in ["Date"]:
        if col in anomalies.columns and pd.api.types.is_numeric_dtype(anomalies[col]):
            anomalies[col] = pd.to_datetime(anomalies[col], unit="D", origin="1899-12-30")
        else:
            anomalies[col] = pd.to_datetime(anomalies[col], errors="coerce")

    return master, raw, summary, anomalies, rules

try:
    meter_master, raw, building_summary, anomalies, anomaly_rules = load_data()
except Exception as e:
    st.error(str(e))
    st.stop()

current_raw = raw[raw["Period"].astype(str).str.lower() == "current"].copy()
previous_raw = raw[raw["Period"].astype(str).str.lower() == "previous"].copy()

def fmt_kwh(x):
    return f"{x:,.0f} kWh"

def fmt_mwh(x):
    return f"{x/1000:,.1f} MWh"

def fmt_pct(x):
    return f"{x:+.1f}%"

def fmt_rupee(x):
    return f"₹{x:,.0f}"

def meter_comparison(building):
    c = (
        current_raw[current_raw["Building"] == building]
        .groupby("Meter_Name")["kWh"]
        .sum()
        .rename("Current")
        .reset_index()
    )
    p = (
        previous_raw[previous_raw["Building"] == building]
        .groupby("Meter_Name")["kWh"]
        .sum()
        .rename("Previous")
        .reset_index()
    )

    out = c.merge(p, on="Meter_Name", how="outer").fillna(0)
    out["Change %"] = np.where(
        out["Previous"] > 0,
        (out["Current"] / out["Previous"] - 1) * 100,
        np.nan,
    )
    return out.sort_values("Change %", ascending=False)

# -----------------------------
# Sidebar - exact requested structure
# -----------------------------
st.sidebar.markdown("## HELIX")
st.sidebar.caption("Energy Intelligence – Simulation")

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Comparison & Drilldown",
        "Meter Intelligence",
        "Anomalies & Actions",
        "Data Quality",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Simulation / Demo Data")

# -----------------------------
# Header
# -----------------------------
st.markdown(
    '<div class="title">HELIX | Energy Intelligence</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">From energy monitoring to meaningful comparison, insight and action.</div>',
    unsafe_allow_html=True,
)

# ============================================================
# OVERVIEW
# ============================================================
if page == "Overview":

    total_current = building_summary["Current kWh"].sum()
    total_previous = building_summary["Previous kWh"].sum()
    total_change = (
        (total_current / total_previous - 1) * 100
        if total_previous > 0 else 0
    )

    peak = building_summary["Peak Current kW"].max()
    avg_pf = building_summary["Avg PF"].mean()

    # Use workbook anomalies, so the page reflects the Excel data exactly.
    active_anomalies = int(len(anomalies[anomalies["Status"].astype(str).str.lower() == "open"]))

    # Use a transparent 3% scenario against current-period site energy.
    # This is a demo opportunity, not a guaranteed saving.
    tariff = 8.5
    savings_opportunity = total_current * 0.03 * tariff

    cols = st.columns(6)
    kpis = [
        ("Total Energy", fmt_mwh(total_current)),
        ("vs Previous Period", fmt_pct(total_change)),
        ("Peak Demand", f"{peak:,.0f} kW"),
        ("Average PF", f"{avg_pf:.2f}"),
        ("Active Anomalies", str(active_anomalies)),
        ("Savings Opportunity", fmt_rupee(savings_opportunity)),
    ]

    for col, (label, value) in zip(cols, kpis):
        col.markdown(
            f"""
            <div class="card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Energy Trend")

    trend = (
        current_raw.groupby("Date")["kWh"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        trend,
        x="Date",
        y="kWh",
        title="Current Period Daily Energy Consumption",
        labels={"kWh": "Energy (kWh)", "Date": ""},
    )
    fig.update_layout(height=310, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Building-wise Energy Comparison")

    # IMPORTANT: use Building_Summary sheet directly for the comparison.
    bs = building_summary.copy()

    fig2 = px.bar(
        bs.sort_values("Current kWh", ascending=False),
        x="Building",
        y=["Previous kWh", "Current kWh"],
        barmode="group",
        title="Current Period vs Previous Period",
        labels={"value": "Energy (kWh)", "variable": "Period"},
    )
    fig2.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    display = bs.copy()
    display["Previous Period"] = display["Previous kWh"].map(fmt_kwh)
    display["Current Period"] = display["Current kWh"].map(fmt_kwh)
    display["Change"] = display["Change %"].map(fmt_pct)

    st.dataframe(
        display[
            ["Building", "Previous Period", "Current Period", "Change", "Insight Status"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Excel-defined Anomalies")

    for _, row in anomalies.iterrows():
        st.markdown(
            f"""
            <div class="warning">
                <b>{row['Anomaly_ID']}</b> | {row['Building']} | {row['Meter_Name']}
                <br><b>Signal:</b> {row['Signal']} |
                <b>Severity:</b> {row['Severity']} |
                <b>Change:</b> {row['Change/Value']}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# COMPARISON & DRILLDOWN
# ============================================================
elif page == "Comparison & Drilldown":

    st.markdown("### Energy Comparison & Drilldown")
    st.caption("Simple drill-down: Building → Meter")

    # Building view comes straight from the summary sheet.
    bs = building_summary.copy()

    fig = px.bar(
        bs.sort_values("Change %"),
        x="Building",
        y="Change %",
        text_auto=".1f",
        title="Building-wise Change vs Previous Period",
        labels={"Change %": "Change (%)"},
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    display = bs.copy()
    display["Previous Period"] = display["Previous kWh"].map(fmt_kwh)
    display["Current Period"] = display["Current kWh"].map(fmt_kwh)
    display["Change"] = display["Change %"].map(fmt_pct)

    st.dataframe(
        display[
            ["Building", "Previous Period", "Current Period", "Change", "Insight Status"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Meter Drilldown")
    building = st.selectbox(
        "Select Building",
        sorted(building_summary["Building"].tolist()),
    )

    mc = meter_comparison(building)

    fig2 = px.bar(
        mc.sort_values("Change %"),
        x="Meter_Name",
        y="Change %",
        text_auto=".1f",
        title=f"{building} – Meter-wise Change",
        labels={"Change %": "Change (%)"},
    )
    fig2.update_layout(height=340)
    st.plotly_chart(fig2, use_container_width=True)

    meter_display = mc.copy()
    meter_display["Previous Period"] = meter_display["Previous"].map(fmt_kwh)
    meter_display["Current Period"] = meter_display["Current"].map(fmt_kwh)
    meter_display["Change"] = meter_display["Change %"].map(fmt_pct)

    st.dataframe(
        meter_display[
            ["Meter_Name", "Previous Period", "Current Period", "Change"]
        ],
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# METER INTELLIGENCE
# ============================================================
elif page == "Meter Intelligence":

    st.markdown("### Meter Intelligence")
    st.caption("Energy-meter parameters used to move from monitoring towards investigation.")

    building = st.selectbox(
        "Building",
        sorted(meter_master["Building"].unique()),
    )

    meters_for_building = sorted(
        meter_master[meter_master["Building"] == building]["Meter_Name"].unique()
    )

    meter = st.selectbox("Meter", meters_for_building)

    mc = current_raw[
        (current_raw["Building"] == building)
        & (current_raw["Meter_Name"] == meter)
    ]
    mp = previous_raw[
        (previous_raw["Building"] == building)
        & (previous_raw["Meter_Name"] == meter)
    ]

    current_kwh = mc["kWh"].sum()
    previous_kwh = mp["kWh"].sum()
    change = (
        (current_kwh / previous_kwh - 1) * 100
        if previous_kwh > 0 else 0
    )

    peak_kw = mc["kW"].max()
    avg_pf_meter = mc["Power_Factor"].mean()
    avg_voltage = mc["Voltage_V"].mean()
    avg_current = mc["Current_A"].mean()

    cols = st.columns(6)
    kpis = [
        ("Current Energy", fmt_kwh(current_kwh)),
        ("Previous Energy", fmt_kwh(previous_kwh)),
        ("Change", fmt_pct(change)),
        ("Peak Demand", f"{peak_kw:,.0f} kW"),
        ("Avg PF", f"{avg_pf_meter:.2f}"),
        ("Avg Voltage", f"{avg_voltage:,.1f} V"),
    ]

    for col, (label, value) in zip(cols, kpis):
        col.markdown(
            f"""
            <div class="card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    trend = (
        mc.groupby("Date")
        .agg(
            kWh=("kWh", "sum"),
            Peak_kW=("kW", "max"),
        )
        .reset_index()
    )

    fig = px.line(
        trend,
        x="Date",
        y=["kWh", "Peak_kW"],
        title=f"{building} – {meter} Daily Energy & Peak Demand",
    )
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Investigation Signals")

    signals = []

    if change > 10:
        signals.append(
            f"Energy increased by {change:+.1f}% versus the previous period."
        )

    if avg_pf_meter < 0.90:
        signals.append(
            f"Average power factor is {avg_pf_meter:.2f}; review electrical loading/reactive-power conditions."
        )

    if not signals:
        st.success("No major simulated exception detected for the selected meter.")
    else:
        for message in signals:
            st.markdown(
                f'<div class="warning"><b>{message}</b></div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div class="small">Average current for this meter: {avg_current:,.1f} A</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# ANOMALIES & ACTIONS
# ============================================================
elif page == "Anomalies & Actions":

    st.markdown("### Anomalies & Actions")
    st.caption(
        "The Excel anomaly sheet provides the simulated exception; "
        "the FM/electrical team validates and takes action."
    )

    if anomalies.empty:
        st.success("No anomalies are defined in the simulation workbook.")
    else:
        for _, row in anomalies.iterrows():

            status = str(row["Status"])

            with st.container(border=True):
                st.markdown(
                    f"**{row['Anomaly_ID']} | {row['Building']} | {row['Meter_Name']}**"
                )

                st.write(
                    f"**Signal:** {row['Signal']}  |  "
                    f"**Severity:** {row['Severity']}  |  "
                    f"**Value:** {row['Change/Value']}"
                )

                st.write(
                    f"**Possible Investigation:** {row['Possible Investigation']}"
                )

                st.write(
                    f"**Recommended Action:** {row['Recommended Action']}"
                )

                st.write(
                    f"**Verification KPI:** {row['Verification KPI']}"
                )

                st.write(f"**Status:** {status}")

    st.markdown("### Intelligence Workflow")

    st.markdown(
        """
        <div class="insight">
        <b>Meter Data</b> → <b>Comparison</b> → <b>Exception</b> →
        <b>Possible Investigation</b> → <b>FM Action</b> →
        <b>Verification</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Savings Opportunity")
    tariff = st.number_input(
        "Demo tariff (₹/kWh)",
        min_value=1.0,
        max_value=25.0,
        value=8.5,
        step=0.5,
    )

    # Estimate only the energy excess represented by the Excel anomaly values.
    # We use the anomaly percentages as a scenario, not as a claim of actual savings.
    opportunity_monthly = 0.0

    for _, row in anomalies.iterrows():
        raw_value = str(row["Change/Value"]).replace("%", "").strip()
        try:
            pct = float(raw_value) / 100
        except ValueError:
            continue

        subset = current_raw[
            (current_raw["Building"] == row["Building"])
            & (current_raw["Meter_Name"] == row["Meter_Name"])
        ]

        current_kwh = subset["kWh"].sum()

        # Back-calculate an illustrative excess relative to the stated increase.
        if pct > 0:
            excess = current_kwh - (current_kwh / (1 + pct))
            opportunity_monthly += excess * tariff

    annualized = opportunity_monthly * 12

    st.info(
        f"Illustrative annual savings opportunity from the defined anomaly scenarios: "
        f"**₹{annualized:,.0f}/year**. "
        "This is a simulation scenario and not a guaranteed saving."
    )

# ============================================================
# DATA QUALITY
# ============================================================
else:

    st.markdown("### Data Quality")
    st.caption(
        "Basic checks using the meter master and raw meter data."
    )

    quality = (
        raw.groupby(["Building", "Meter_ID", "Meter_Name"])
        .agg(
            Records=("Timestamp", "count"),
            First_Reading=("Timestamp", "min"),
            Last_Reading=("Timestamp", "max"),
            Avg_kWh=("kWh", "mean"),
            Avg_PF=("Power_Factor", "mean"),
            Status=("Status", "last"),
        )
        .reset_index()
    )

    expected_records = raw["Date"].nunique()

    quality["Data Check"] = np.where(
        quality["Records"] >= expected_records * 0.90,
        "OK",
        "Check Missing Data",
    )

    st.dataframe(
        quality,
        use_container_width=True,
        hide_index=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Meters", len(meter_master))
    c2.metric("Online in Master", int((meter_master["Status"].astype(str).str.lower() == "online").sum()))
    c3.metric("Records", len(raw))

    st.markdown(
        """
        <div class="insight">
        <b>Operational principle:</b> validate data quality before acting on an energy exception.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")
st.sidebar.caption("HELIX Energy Intelligence | Simulation data only")
