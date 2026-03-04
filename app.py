import streamlit as st
import json
import plotly.graph_objects as go

# Match the dashboard theme from your screenshot
st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# Custom styles for metrics and cards
st.markdown("""
    <style>
    .kpi-box { background-color: #0f172a; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #1e293b; }
    .insight-card { background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #3b82f6; margin-bottom: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 1. LOAD CLEAN JSON
with open('budget_data.json', 'r') as f:
    data = json.load(f)["widgets"][0]["chart"]

# 2. HEADER KPIs (Top Row)
st.title(f"✨ {data['meta']['title']}")
kpi_cols = st.columns(3)
for i, kpi in enumerate(data["kpis"]):
    with kpi_cols[i]:
        st.markdown(f"""<div class="kpi-box">
            <div style="color: #94a3b8; font-size: 0.9rem;">{kpi['label']}</div>
            <div style="color: #3b82f6; font-size: 2rem; font-weight: bold;">${kpi['value']/1000000:,.1f}M</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# 3. MAIN DASHBOARD (2 Columns)
left, right = st.columns([2.5, 1])

with left:
    st.subheader(data["meta"]["title"])
    # Plotly Line Chart
    fig = go.Figure()
    for s in data["series"]:
        fig.add_trace(go.Scatter(x=data["xcategories"], y=s["data"], name=s["label"], mode='lines+markers'))
    
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=20, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary Tab
    with st.expander("📝 Summary", expanded=True):
        st.write(data["meta"]["description"])

with right:
    st.subheader("🤖 AI-Powered Insights")
    st.markdown("""
        <div class="insight-card">
            <strong>Significant Forecast Revision Downward</strong><br>
            <small>Current Forecast has been revised from $25M to $22M.</small>
        </div>
        <div class="insight-card">
            <strong>Execution Tracking Below Goals</strong><br>
            <small>CCaR Actuals ($5.8M) are below March OSD targets.</small>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("✅ Recommended Actions")
    st.success("Investigate DFAS-CCaR $5.8M divergence.")
    
    st.text_input("🔍 Ask a question about this chart")
