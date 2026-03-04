import streamlit as st
import json
import plotly.graph_objects as go
import os
import re

# PAGE CONFIG - Set to wide to match screenshot
st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# Custom CSS to mimic the screenshot's dark theme and card styling
st.markdown("""
    <style>
    .metric-container { background-color: #0f172a; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #1e293b; }
    .insight-card { background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #3b82f6; margin-bottom: 15px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1e293b; border-radius: 4px 4px 0px 0px; gap: 1px; }
    </style>
    """, unsafe_allow_html=True)

# 1. ROBUST JSON CLEANER
def clean_and_load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract only the content between the first { and last }
    start = content.find('{')
    end = content.rfind('}')
    json_str = content[start:end+1]
    
    # Fix "Smart Quotes" if they were copy-pasted from a doc
    json_str = json_str.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
    
    return json.loads(json_str)

# 2. LOAD DATA
filename = "Budget Execution Chart Data.json"
try:
    raw_data = clean_and_load_json(filename)
    data = raw_data["widgets"][0]["chart"]
    
    # --- HEADER & KPIs ---
    st.subheader("✨ CCaR Insights: " + data["meta"]["title"])
    kpi_cols = st.columns(len(data["kpis"]))
    for i, kpi in enumerate(data["kpis"]):
        with kpi_cols[i]:
            st.markdown(f"""<div class="metric-container">
                <div style="color: #94a3b8; font-size: 0.8rem;">{kpi['label']}</div>
                <div style="color: #3b82f6; font-size: 1.8rem; font-weight: bold;">${kpi['value']/1000000:,.1f}M</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # --- MAIN CONTENT LAYOUT (2 Columns) ---
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.write(f"**{data['meta']['title'].upper()}**")
        # Line Chart
        fig = go.Figure()
        for s in data["series"]:
            fig.add_trace(go.Scatter(x=data["xcategories"], y=s["data"], name=s["label"], mode='lines+markers'))
        
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
        st.plotly_chart(fig, use_container_width=True)

        # Summary/Description Tabs
        tab1, tab2 = st.tabs(["📝 Summary", "ℹ️ Description"])
        with tab1:
            st.info(data["meta"]["description"])
        with tab2:
            st.write("Detailed metadata and assumptions would go here.")

    with right_col:
        st.markdown("### 🤖 AI-Powered Insights")
        # Placeholder insights to match your screenshot
        insights = [
            {"t": "Significant Forecast Revision", "b": "Current Forecast dropped from $25M baseline to $22M by August."},
            {"t": "Execution Tracking Below Goals", "b": "CCaR Actuals ($5.8M) are below OSD Goals ($2.7M target)."}
        ]
        for ins in insights:
            st.markdown(f'<div class="insight-card"><strong>{ins["t"]}</strong><br><small>{ins["b"]}</small></div>', unsafe_allow_html=True)
        
        st.markdown("### ✅ Recommended Actions")
        st.success("Investigate DFAS-CCaR divergence ($5.8M).")
        
        # Bottom Search Box
        st.text_input("🔍 Ask a question about this chart", placeholder="e.g., Why is DFAS at zero?")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
