# HELIX Energy Intelligence – Excel-backed Simulation

This is the Excel-backed version of the HELIX Energy Intelligence dashboard.

## Exact navigation

- Overview
- Comparison & Drilldown
- Meter Intelligence
- Anomalies & Actions
- Data Quality

## Data source

The dashboard reads `Helix_Energy_Intelligence_Simulation_Data.xlsx` at runtime.

The workbook contains:
- README
- Meter_Master
- Raw_Meter_Data
- Building_Summary
- Anomalies
- Anomaly_Rules

## Workflow

**Monitor → Compare → Identify → Understand → Act → Verify**

## Local run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open:

`http://localhost:8501`

> All values are simulated for demonstration only.
