import streamlit as st
import json
import plotly.graph_objects as go
import os

# Set page to wide mode to match your original screenshot
st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# 1. ROBUST FILE LOADING
# This looks for your specific file name from GitHub
filename = "Budget Execution Chart Data.json"

if not os.path.exists(filename):
    st.error(f"❌ File '{filename}' not found! Please ensure it is in your GitHub root folder.")
else:
    with open(filename, 'r') as f:
        content = f.read()
        
        # This part handles the "BudgetExecutionChart =" prefix in your file
        try:
            start_index = content.find('{')
            end_index = content.rfind('}')
            json_string = content[start_index:end_index + 1]
            raw_data = json.loads(json_string)
            
            # Navigating your specific JSON structure
            chart_data = raw_data["widgets"][0]["chart"]
            
            # --- HEADER & KPI SECTION ---
            st.title(f"📊 {chart_data['meta']['title']}")
            kpi_cols = st.columns(len(chart_data["kpis"]))
            for i, kpi in enumerate(chart_data["kpis"]):
                with kpi_cols[i]:
                    st.metric(kpi["label"], f"${kpi['value']/1000000:,.1f}M")

            st.divider()

            # --- MAIN CONTENT (2 Columns) ---
            left, right = st.columns([2, 1])

            with left:
                st.subheader("Budget Execution Chart")
                fig = go.Figure()
                for s in chart_data["series"]:
                    fig.add_trace(go.Scatter(
                        x=chart_data["xcategories"], 
                        y=s["data"], 
                        name=s["label"], 
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    template="plotly_dark", 
                    height=500,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig, use_container_width=True)

            with right:
                st.subheader("🤖 AI-Powered Insights")
                # Creating cards to match your screenshot
                st.info("**Significant Forecast Revision Downward**\n\nThe Current Forecast has been revised dramatically from the Baseline.")
                st.warning("**Execution Tracking Below Goals**\n\nActuals are tracking below OSD Goals ($2.7M target).")
                
                st.subheader("✅ Recommended Actions")
                st.success("Investigate the root cause of the DFAS-CCaR $5.8M divergence.")

        except Exception as e:
            st.error(f"❌ Error reading the file: {e}")
