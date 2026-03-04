import streamlit as st
import json
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide", page_title="CCaR Dashboard")

# 1. FILE LOADING (Robust Method)
filename = "Budget Execution Chart Data.json"

if not os.path.exists(filename):
    st.error(f"❌ File '{filename}' not found in your GitHub repository.")
else:
    with open(filename, 'r') as f:
        content = f.read()
        
        # Find the first '{' and the last '}' to extract only the JSON object
        start_index = content.find('{')
        end_index = content.rfind('}')
        
        if start_index == -1 or end_index == -1:
            st.error("❌ The file does not contain a valid JSON object (missing braces).")
        else:
            json_string = content[start_index:end_index + 1]
            try:
                raw_data = json.loads(json_string)
                
                # Navigate to the chart section
                data_json = raw_data["widgets"][0]
                chart_data = data_json["chart"]
                
                # 2. KPI METRICS
                kpis = chart_data["kpis"]
                cols = st.columns(len(kpis))
                for i, kpi in enumerate(kpis):
                    cols[i].metric(kpi["label"], f"${kpi['value']/1000000:,.1f}M")

                # 3. CHARTING
                fig = go.Figure()
                for series in chart_data["series"]:
                    fig.add_trace(go.Scatter(
                        x=chart_data["xcategories"], 
                        y=series["data"], 
                        name=series["label"],
                        mode='lines+markers'
                    ))

                fig.update_layout(
                    title=chart_data["meta"]["title"],
                    template="plotly_dark",
                    height=600,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig, use_container_width=True)

            except json.JSONDecodeError as e:
                st.error(f"❌ JSON Parsing Error: {e}")
                st.info("Ensure there are no trailing commas or comments inside your data file.")
