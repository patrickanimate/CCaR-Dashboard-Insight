import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide")

# Use the exact filename from your GitHub
filename = "Budget Execution Chart Data.json"

if not os.path.exists(filename):
    st.error(f"File '{filename}' not found. Check your GitHub file name!")
else:
    with open(filename, 'r') as f:
        content = f.read()
        # This removes "BudgetExecutionChart =" and the ending ";" 
        # so Python can read it as JSON
        json_string = content.split('=', 1)[-1].strip().rstrip(';')
        raw_data = json.loads(json_string)

    # Navigating your specific JSON structure
    data_json = raw_data["widgets"][0]
    chart_data = data_json["chart"]
    
    # 1. Metrics / KPIs
    kpi_list = chart_data["kpis"]
    cols = st.columns(len(kpi_list))
    for i, kpi in enumerate(kpi_list):
        cols[i].metric(kpi["label"], f"${kpi['value']/1000000:,.1f}M")

    # 2. The Chart
    fig = go.Figure()
    for s in chart_data["series"]:
        fig.add_trace(go.Scatter(
            x=chart_data["xcategories"], 
            y=s["data"], 
            name=s["label"],
            mode='lines+markers'
        ))

    fig.update_layout(
        title=chart_data["meta"]["title"],
        template="plotly_dark",
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)
