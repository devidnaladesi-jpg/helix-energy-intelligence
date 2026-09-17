
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ============================================================
# HELIX | Energy Intelligence - Simple Client / CEO Demo
# Simulation only
#
# Workflow:
#   Monitor -> Compare -> Identify -> Understand -> Act
#
# Main drill-down:
#   Total Energy -> Building/Tower -> Meter
#
# No tenant-level or multi-step drill-down is used on purpose.
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

        .title {
            font-size: 29px;
            font-weight: 750;
            color: #17324d;
            margin-bottom: 0;
        }

        .subtitle {
            color: #65747d;
            font-size: 13px;
            margin-bottom: 16px;
        }

        .card {
            background: white;
            border: 1px solid #d9e3e8;
            border-radius: 12px;
            padding: 14px 16px;
            min-height: 88px;
        }

        .kpi-label {
            color: #687780;
            font-size: 12px;
        }

        .kpi-value {
            color: #17324d;
            font-size: 22px;
            font-weight: 750;
            margin-top: 3px;
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

        .muted {
            color: #6c7a82;
            font-size: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Simulation data
# -----------------------------
@st.cache_data
def build_simulation():
    rng = np.random.default_rng(7)

    towers = [
        ("Tower 1", 1.06),
        ("Tower 2", 0.93),
        ("Tower 3", 1.18),
        ("Tower 4", 0.86),
        ("Tower 5", 1.01),
        ("Tower 6", 0.80),
        ("Tower 7", 0.95),
        ("Tower 8", 0.73),
        ("Tower 9", 1.12),
    ]

    meter_templates = [
        ("Main Energy Meter", 1.00),
        ("HVAC Meter", 0.47),
        ("Lighting Meter", 0.20),
        ("Other Loads Meter", 0.23),
    ]

    dates = pd.date_range(
        pd.Timestamp(datetime.now().date()) - pd.Timedelta(days=89),
        periods=90,
        freq="D",
    )

    rows = []

    # Last 30 days are the current period; preceding 30 days are previous period.
    current_start = dates.max() - pd.Timedelta(days=29)
    previous_start = current_start - pd.Timedelta(days=30)

    for tower, tower_factor in towers:
        for date in dates:
            weekday_factor = 1.00 if date.dayofweek < 5 else 0.73
            seasonal_factor = 1 + 0.045 * np.sin((date.dayofyear / 365) * 2 * np.pi)
            base = 18000 * tower_factor * weekday_factor * seasonal_factor

            # Simulated tower-level change in current period
            tower_multiplier = 1.0
            if date >= current_start and tower == "Tower 3":
                tower_multiplier *= 1.22
            if date >= current_start and tower == "Tower 9":
                tower_multiplier *= 1.12

            tower_energy = max(1500, base * tower_multiplier * (1 + rng.normal(0, 0.035)))

            for meter_name, share in meter_templates:
                value = tower_energy * share * (1 + rng.normal(0, 0.03))

                # Stronger meter-level signal in Tower 3
                if (
                    date >= current_start
                    and tower == "Tower 3"
                    and meter_name == "HVAC Meter"
                ):
                    value *= 1.18

                # Moderate lighting increase in Tower 6
                if (
                    date >= current_start
                    and tower == "Tower 6"
                    and meter_name == "Lighting Meter"
                ):
                    value *= 1.10

                rows.append(
                    [
                        date,
                        tower,
                        meter_name,
                        max(50, value),
                    ]
                )

    df = pd.DataFrame(
        rows,
        columns=["Date", "Building", "Meter", "kWh"],
    )

    df["Period"] = np.where(df["Date"] >= current_start, "Current", "Previous")
    return df, current_start, previous_start


df, current_start, previous_start = build_simulation()

current = df[df["Period"] == "Current"].copy()
previous = df[df["Period"] == "Previous"].copy()

# -----------------------------
# Helpers
# -----------------------------
def comparison_table(current_df, previous_df, group_col):
    c = current_df.groupby(group_col)["kWh"].sum().rename("Current").reset_index()
    p = previous_df.groupby(group_col)["kWh"].sum().rename("Previous").reset_index()

    out = c.merge(p, on=group_col, how="outer").fillna(0)
    out["Change %"] = np.where(
        out["Previous"] > 0,
        (out["Current"] / out["Previous"] - 1) * 100,
        np.nan,
    )
    return out.sort_values("Change %", ascending=False)


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## HELIX")
st.sidebar.caption("Energy Intelligence")
page = st.sidebar.radio(
    "Navigate",
    [
        "Energy Overview",
        "Energy Comparison",
        "Energy Intelligence",
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
    '<div class="subtitle">From energy monitoring to comparison, meaningful insight and operational action.</div>',
    unsafe_allow_html=True,
)

# ============================================================
# PAGE 1: Energy Overview
# ============================================================
if page == "Energy Overview":

    total_current = current["kWh"].sum()
    total_previous = previous["kWh"].sum()
    change_pct = (total_current / total_previous - 1) * 100

    peak_daily = (
        current.groupby("Date")["kWh"]
        .sum()
        .max()
    )

    avg_daily = (
        current.groupby("Date")["kWh"]
        .sum()
        .mean()
    )

    tariff = 8.50
    estimated_monthly_cost = avg_daily * 30 * tariff

    tower_comp = comparison_table(
        current,
        previous,
        "Building",
    )

    active_exceptions = int((tower_comp["Change %"] > 10).sum())

    # KPI row
    cols = st.columns(6)
    kpis = [
        ("Total Energy", f"{total_current / 1000:,.1f} MWh"),
        ("Previous Period", f"{total_previous / 1000:,.1f} MWh"),
        ("Change", f"{change_pct:+.1f}%"),
        ("Peak Daily Energy", f"{peak_daily / 1000:,.1f} MWh"),
        ("Active Exceptions", str(active_exceptions)),
        ("Est. Monthly Cost", f"₹{estimated_monthly_cost:,.0f}"),
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
    daily = (
        current.groupby("Date")["kWh"]
        .sum()
        .reset_index()
    )

    fig_trend = px.line(
        daily,
        x="Date",
        y="kWh",
        title="Current Period Daily Energy Consumption",
        labels={"kWh": "Energy (kWh)"},
    )
    fig_trend.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("### Building-wise Energy Consumption")
    fig_build = px.bar(
        tower_comp.sort_values("Current", ascending=False),
        x="Building",
        y=["Previous", "Current"],
        barmode="group",
        title="Current Period vs Previous Period",
        labels={"value": "Energy (kWh)", "variable": "Period"},
    )
    fig_build.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_build, use_container_width=True)

    display = tower_comp.copy()
    display["Previous Month"] = display["Previous"].map(lambda x: f"{x:,.0f} kWh")
    display["Current Month"] = display["Current"].map(lambda x: f"{x:,.0f} kWh")
    display["Change"] = display["Change %"].map(lambda x: f"{x:+.1f}%")

    st.dataframe(
        display[["Building", "Previous Month", "Current Month", "Change"]],
        use_container_width=True,
        hide_index=True,
    )

    top = tower_comp.iloc[0]
    if top["Change %"] > 8:
        st.markdown(
            f"""
            <div class="insight">
                <b>Insight:</b> {top["Building"]} shows the highest increase
                at <b>{top["Change %"]:+.1f}%</b>.
                The next step is to identify which meter is driving the change.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# PAGE 2: Energy Comparison
# ============================================================
elif page == "Energy Comparison":

    st.markdown("### Energy Comparison")
    st.caption("Simple drill-down: Total Energy → Building → Meter")

    level = st.radio(
        "Comparison level",
        ["Building", "Meter"],
        horizontal=True,
    )

    if level == "Building":
        comp = comparison_table(current, previous, "Building")

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

        st.markdown(
            '<div class="muted">Use the Meter level to continue one step deeper into the selected building.</div>',
            unsafe_allow_html=True,
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
# PAGE 3: Energy Intelligence
# ============================================================
elif page == "Energy Intelligence":

    st.markdown("### Energy Intelligence")
    st.caption("Identify where the change is happening, then guide the FM team toward the next investigation.")

    comp = comparison_table(current, previous, "Building")

    alert_buildings = comp[comp["Change %"] > 10].sort_values(
        "Change %",
        ascending=False,
    )

    if alert_buildings.empty:
        st.success("No major simulated energy exceptions detected.")
    else:
        for _, row in alert_buildings.iterrows():

            building = row["Building"]

            meter_comp = comparison_table(
                current[current["Building"] == building],
                previous[previous["Building"] == building],
                "Meter",
            )

            driver = meter_comp.iloc[0]

            st.markdown(
                f"""
                <div class="warning">
                    <b>{building}</b> increased by <b>{row["Change %"]:+.1f}%</b>.
                    Highest meter contribution: <b>{driver["Meter"]}</b>
                    at <b>{driver["Change %"]:+.1f}%</b>.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="insight">
                    <b>Possible investigation:</b>
                    Validate meter data and communication first, then check
                    operating schedule, occupancy/load conditions and the major
                    connected loads contributing to the increase.
                    <br><br>
                    <b>Recommended action:</b>
                    FM/electrical team to investigate the identified meter/load
                    and record the action taken.
                    <br><br>
                    <b>Verification:</b>
                    Compare the next period's energy against the baseline after action.
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Example Operating Workflow")
    flow = pd.DataFrame(
        {
            "Step": [
                "Monitor",
                "Compare",
                "Identify",
                "Understand",
                "Act",
                "Verify",
            ],
            "Purpose": [
                "Collect meter data",
                "Current vs previous",
                "Find high-change building/meter",
                "Validate data + investigate conditions",
                "FM team takes action",
                "Measure next-period result",
            ],
        }
    )

    st.dataframe(flow, use_container_width=True, hide_index=True)

# ============================================================
# PAGE 4: Data Quality
# ============================================================
else:

    st.markdown("### Data Quality")
    st.caption("Basic checks that help ensure energy insights are based on usable meter data.")

    quality = (
        df.groupby(["Building", "Meter"])
        .agg(
            Records=("Date", "count"),
            First_Reading=("Date", "min"),
            Last_Reading=("Date", "max"),
            Avg_kWh=("kWh", "mean"),
        )
        .reset_index()
    )

    quality["Status"] = np.where(
        quality["Records"] >= 80,
        "OK",
        "Check Data",
    )

    st.dataframe(
        quality,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <div class="insight">
            <b>Why this matters:</b> before acting on an energy exception,
            the FM team should confirm that the meter is online, readings are
            complete and the comparison is meaningful.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")
st.sidebar.caption("HELIX Energy Intelligence | Simulation data only")
