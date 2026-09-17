# HELIX Energy Intelligence – Simple Simulation Dashboard

A clean, client/CEO-friendly Streamlit simulation focused on:

**Monitor → Compare → Identify → Understand → Act → Verify**

Main flow:

**Total Energy → Building/Tower → Meter**

## Features

- Total energy and previous-period comparison
- Energy trend
- Building-wise current vs previous comparison
- One-step meter drill-down
- Energy exceptions
- Possible investigation / recommended action
- Verification workflow
- Basic data-quality checks

## Local run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open:
`http://localhost:8501`

## Deployment

Use `app.py` as the Streamlit entry point.

> All values are simulated and are for demonstration only.
