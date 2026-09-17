
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="HELIX | Energy Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
    .stApp { background: #f7f9fb; }
    [data-testid="stSidebar"] { background: #eef4f7; }

    .title {
        font-size: 29px;
        font-weight: 750;
        color: #17324d;
        margin-bottom: 0;
    }

    .subtitle {
        color: #65747d;
        font-size: 13px;
        margin-bottom: 15px;
    }

    .card {
        background: white;
        border: 1px solid #d9e3e8;
        border-radius: 12px;
        padding: 14px 16px;
    }

    .kpi-label {
        color: #687780;
        font-size: 12px;
    }

    .kpi-value {
        color: #17324d;
        font-size: 22px;
        font-weight: 750;
        margin-top: 2px;
    }

    .insight {
        background: #eef6fa;
        border-left: 4px solid #2a6f97;
        padding: 11px 13px;
        border-radius: 8px;
        margin: 6px 0;
        color: #24485d;
    }

    .warning {
        background: #fff6e9;
        border-left: 4px solid #c48517;
        padding: 11px 13px;
        border-radius: 8px;
        margin: 6px 0;
        color: #6f5317;
    }

    .small {
        color: #6c7a82;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Simulation data
# -----------------------------
@st.cache_data
def build_data():
    rng = np.random.default_rng(11)

    buildings = [
        ("Building A", 1.06),
        ("Building B", 0.93),
        ("Building C", 1.18),
        ("Building D", 0.86),
        ("Building E", 1.01),
        ("Building F", 0.80),
        ("Building G", 0.95),
        ("Building H", 0.73),
        ("Building I", 1.12),
    ]

    meters = [
        ("Main Meter", 1.00),
        ("HVAC Meter", 0.48),
        ("Lighting Meter", 0.19),
        ("Plug Load Meter", 0.24),
    ]

    dates = pd.date_range(
        pd.Timestamp(datetime.now().date()) - pd.Timedelta(days=89),
        periods=90,
        freq="D",
    )

    current_start = dates.max() - pd.Timedelta(days=29)

    rows = []

    for building, building_factor in buildings:
        for date in dates:
            weekday = date.dayofweek < 5
            occupancy = 1.00 if weekday else 0.70
            seasonal = 1 + 0.04 * np.sin((date.dayofyear / 365) * 2 * np.pi)

            base_energy = (
                18000
                * building_factor
                * occupancy
                * seasonal
                * (1 + rng.normal(0, 0.035))
            )

            base_energy = max(2000, base_energy)

            # Simulated high-consumption situations
            multiplier = 1.0

            if date >= current_start and building == "Building C":
                multiplier *= 1.22

            if date >= current_start and building == "Building I":
                multiplier *= 1.12

            total_energy = max(2000, base_energy * multiplier)

            for meter_name, share in meters:
                value = total_energy * share * (1 + rng.normal(0, 0.03))

                if (
                    date >= current_start
                    and building == "Building C"
                    and meter_name == "HVAC Meter"
                ):
                    value *= 1.18

                if (
                    date >= current_start
                    and building == "Building F"
                    and meter_name == "Lighting Meter"
                ):
                    value *= 1.10

                rows.append([
                    date,
                    building,
                    meter_name,
                    max(50, value),
                ])

    df = pd.DataFrame(
        rows,
        columns=["Date", "Building", "Meter", "kWh"],
    )

    df["Period"] = np.where(
        df["Date"] >= current_start,
        "Current",
        "Previous",
    )

    # Supporting meter parameters
    df["kW"] = df["kWh"] / 24 * (1 + rng.normal(0, 0.03, len(df)))
    df["kW"] = df["kW"].clip(lower=1)

    df["Voltage_V"] = rng.normal(415, 2.5, len(df))
    df["PF"] = np.clip(rng.normal(0.93, 0.02, len(df)), 0.76, 0.99)
    df["Current_A"] = (
        df["kW"] * 1000
        / (np.sqrt(3) * df["Voltage_V"] * df["PF"])
    ).clip(lower=0.1)

    return df


df = build_data()
current = df[df["Period"] == "Current"].copy()
previous = df[df["Period"] == "Previous"].copy()


def comparison_table(current_df, previous_df, group_col):
    c = (
        current_df.groupby(group_col)["kWh"]
        .sum()
        .rename("Current")
        .reset_index()
    )

    p = (
        previous_df.groupby(group_col)["kWh"]
        .sum()
        .rename("Previous")
        .reset_index()
    )

    out = c.merge(p, on=group_col, how="outer").fillna(0)

    out["Change %"] = np.where(
        out["Previous"] > 0,
        (out["Current"] / out["Previous"] - 1) * 100,
        np.nan,
    )

    return out.sort_values("Change %", ascending=False)


# -----------------------------
# Sidebar — matches requested design
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
# Overview
# ============================================================
if page == "Overview":

    total_current = current["kWh"].sum()
    total_previous = previous["kWh"].sum()
    change_pct = (total_current / total_previous - 1) * 100

    peak_demand = current["kW"].max()
    avg_pf = current["PF"].mean()

    building_comp = comparison_table(
        current,
        previous,
        "Building",
    )

    exceptions = int((building_comp["Change %"] > 10).sum())

    tariff = 8.5
    avg_daily = current.groupby("Date")["kWh"].sum().mean()
    est_monthly_cost = avg_daily * 30 * tariff

    cols = st.columns(6)

    kpis = [
        ("Total Energy", f"{total_current / 1000:,.1f} MWh"),
        ("vs Previous Period", f"{change_pct:+.1f}%"),
        ("Peak Demand", f"{peak_demand:,.0f} kW"),
        ("Average PF", f"{avg_pf:.2f}"),
        ("Active Exceptions", str(exceptions)),
        ("Est. Monthly Cost", f"₹{est_monthly_cost:,.0f}"),
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
        current.groupby("Date")["kWh"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        trend,
        x="Date",
        y="kWh",
        title="Current Period Daily Energy Consumption",
        labels={"kWh": "Energy (kWh)"},
    )

    fig.update_layout(height=330, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Building-wise Energy Comparison")

    fig2 = px.bar(
        building_comp.sort_values("Current", ascending=False),
        x="Building",
        y=["Previous", "Current"],
        barmode="group",
        title="Current Period vs Previous Period",
        labels={"value": "Energy (kWh)", "variable": "Period"},
    )

    fig2.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    table = building_comp.copy()
    table["Previous Month"] = table["Previous"].map(lambda x: f"{x:,.0f} kWh")
    table["Current Month"] = table["Current"].map(lambda x: f"{x:,.0f} kWh")
    table["Change"] = table["Change %"].map(lambda x: f"{x:+.1f}%")

    st.dataframe(
        table[["Building", "Previous Month", "Current Month", "Change"]],
        use_container_width=True,
        hide_index=True,
    )

    top = building_comp.iloc[0]

    if top["Change %"] > 8:
        st.markdown(
            f"""
            <div class="insight">
                <b>Insight:</b> {top["Building"]} shows the highest
                increase at <b>{top["Change %"]:+.1f}%</b>.
                Use <b>Comparison & Drilldown</b> to identify the
                meter contributing to the change.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# Comparison & Drilldown
# ============================================================
elif page == "Comparison & Drilldown":

    st.markdown("### Energy Comparison & Drilldown")
    st.caption(
        "Simple drill-down: Site / Building → Meter. "
        "The comparison uses the same energy-meter data at each level."
    )

    level = st.radio(
        "Select level",
        ["Building", "Meter"],
        horizontal=True,
    )

    if level == "Building":

        comp = comparison_table(
            current,
            previous,
            "Building",
        )

        fig = px.bar(
            comp.sort_values("Change %"),
            x="Building",
            y="Change %",
            text_auto=".1f",
            title="Building-wise Change vs Previous Period",
            labels={"Change %": "Change (%)"},
        )

        fig.update_layout(height=370)
        st.plotly_chart(fig, use_container_width=True)

        table = comp.copy()
        table["Previous"] = table["Previous"].map(lambda x: f"{x:,.0f} kWh")
        table["Current"] = table["Current"].map(lambda x: f"{x:,.0f} kWh")
        table["Change"] = table["Change %"].map(lambda x: f"{x:+.1f}%")

        st.dataframe(
            table[["Building", "Previous", "Current", "Change"]],
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "Next step: select Meter and choose a building to see "
            "which meter is contributing to the change."
        )

    else:

        building = st.selectbox(
            "Select Building",
            sorted(df["Building"].unique()),
        )

        comp = comparison_table(
            current[current["Building"] == building],
            previous[previous["Building"] == building],
            "Meter",
        )

        fig = px.bar(
            comp.sort_values("Change %"),
            x="Meter",
            y="Change %",
            text_auto=".1f",
            title=f"{building} – Meter-wise Change vs Previous Period",
            labels={"Change %": "Change (%)"},
        )

        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

        table = comp.copy()
        table["Previous"] = table["Previous"].map(lambda x: f"{x:,.0f} kWh")
        table["Current"] = table["Current"].map(lambda x: f"{x:,.0f} kWh")
        table["Change"] = table["Change %"].map(lambda x: f"{x:+.1f}%")

        st.dataframe(
            table[["Meter", "Previous", "Current", "Change"]],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Meter Intelligence
# ============================================================
elif page == "Meter Intelligence":

    st.markdown("### Meter Intelligence")
    st.caption(
        "Use available meter parameters to move from monitoring "
        "towards investigation."
    )

    building = st.selectbox(
        "Building",
        sorted(df["Building"].unique()),
    )

    meter = st.selectbox(
        "Meter",
        sorted(df[df["Building"] == building]["Meter"].unique()),
    )

    m_current = current[
        (current["Building"] == building)
        & (current["Meter"] == meter)
    ]

    m_previous = previous[
        (previous["Building"] == building)
        & (previous["Meter"] == meter)
    ]

    current_kwh = m_current["kWh"].sum()
    previous_kwh = m_previous["kWh"].sum()

    change = (
        (current_kwh / previous_kwh - 1) * 100
        if previous_kwh > 0
        else 0
    )

    peak = m_current["kW"].max()
    pf = m_current["PF"].mean()

    cols = st.columns(4)

    for col, (label, value) in zip(
        cols,
        [
            ("Current Energy", f"{current_kwh:,.0f} kWh"),
            ("Change vs Previous", f"{change:+.1f}%"),
            ("Peak Demand", f"{peak:,.0f} kW"),
            ("Average PF", f"{pf:.2f}"),
        ],
    ):
        col.markdown(
            f"""
            <div class="card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    daily = (
        m_current.groupby("Date")
        .agg(
            kWh=("kWh", "sum"),
            Peak_kW=("kW", "max"),
            PF=("PF", "mean"),
        )
        .reset_index()
    )

    fig = px.line(
        daily,
        x="Date",
        y=["kWh", "Peak_kW"],
        title=f"{building} – {meter} Daily Energy & Peak",
    )

    fig.update_layout(height=330)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Investigation Signals")

    if change > 10:
        st.markdown(
            f"""
            <div class="warning">
                <b>Energy increase:</b> {change:+.1f}% versus the previous period.
                Validate the meter data and investigate changes in operating pattern
                or connected load.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if pf < 0.90:
        st.markdown(
            f"""
            <div class="warning">
                <b>Power factor:</b> average PF is {pf:.2f}.
                Review the electrical loading and reactive-power condition.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if change <= 10 and pf >= 0.90:
        st.success(
            "No major simulated exception detected from the selected meter."
        )


# ============================================================
# Anomalies & Actions
# ============================================================
elif page == "Anomalies & Actions":

    st.markdown("### Anomalies & Actions")
    st.caption(
        "Helix identifies the exception; the FM/electrical team validates "
        "the condition and takes the action."
    )

    comp = comparison_table(
        current,
        previous,
        "Building",
    )

    alerts = comp[
        comp["Change %"] > 10
    ].sort_values("Change %", ascending=False)

    if alerts.empty:
        st.success("No simulated anomalies detected.")
    else:
        for _, row in alerts.iterrows():

            building = row["Building"]

            meter_comp = comparison_table(
                current[current["Building"] == building],
                previous[previous["Building"] == building],
                "Meter",
            )

            driver = meter_comp.iloc[0]

            with st.container(border=True):
                st.markdown(
                    f"**{building} — Energy increased {row['Change %']:+.1f}%**"
                )

                st.write(
                    f"**Highest meter change:** "
                    f"{driver['Meter']} ({driver['Change %']:+.1f}%)"
                )

                st.write(
                    "**Possible investigation:** Validate meter data, "
                    "communication and operating/load conditions."
                )

                st.write(
                    "**Recommended action:** FM/electrical team to "
                    "investigate the identified meter/load and record "
                    "the action taken."
                )

                st.write(
                    "**Verification KPI:** Compare the next period "
                    "against the baseline after action."
                )

                st.write("**Status:** Open")

    st.markdown("### Savings Opportunity")

    tariff = st.number_input(
        "Demo tariff (₹/kWh)",
        min_value=1.0,
        max_value=25.0,
        value=8.5,
        step=0.5,
    )

    excess = (
        current["kWh"]
        .sum()
        * (
            current.groupby(["Building", "Meter"])["kWh"]
            .transform("mean")
            / current.groupby(["Building", "Meter"])["kWh"].transform("mean")
        )
    )

    # Transparent illustrative opportunity:
    opportunity = 0.03 * current["kWh"].sum() * tariff
    annualized = opportunity * 12

    st.info(
        f"Illustrative annual savings opportunity: "
        f"**₹{annualized:,.0f}/year** assuming a 3% avoidable-energy "
        f"opportunity. This is a simulation scenario, not a guaranteed saving."
    )


# ============================================================
# Data Quality
# ============================================================
else:

    st.markdown("### Data Quality")
    st.caption(
        "Basic meter checks to ensure the dashboard is working with "
        "usable data before operational action."
    )

    quality = (
        df.groupby(["Building", "Meter"])
        .agg(
            Records=("Date", "count"),
            First_Reading=("Date", "min"),
            Last_Reading=("Date", "max"),
            Avg_kWh=("kWh", "mean"),
            Avg_PF=("PF", "mean"),
        )
        .reset_index()
    )

    quality["Status"] = np.where(
        (quality["Records"] >= 80)
        & (quality["Avg_PF"] >= 0.85),
        "OK",
        "Check",
    )

    st.dataframe(
        quality,
        use_container_width=True,
        hide_index=True,
    )

    checks = quality["Status"].value_counts()

    c1, c2 = st.columns(2)
    c1.metric("Meters Checked", len(quality))
    c2.metric("Meters Requiring Check", int((quality["Status"] == "Check").sum()))

    st.markdown(
        """
        <div class="insight">
            <b>Operational principle:</b> validate data quality first,
            then use the comparison and intelligence views for investigation
            and action.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")
st.sidebar.caption("HELIX Energy Intelligence | Simulation data only")
