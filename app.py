import streamlit as st
import pandas as pd
import plotly.express as px
import json
from openai import OpenAI

# 1. INITIALIZE AI CLIENT
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# Custom CSS - Sanitized and Fixed
st.markdown("""
<style>
    .kpi-card { border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #334155; margin-bottom: 20px; }
    .insight-card { border-radius: 8px; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 12px; border: 1px solid #334155; }
    
    /* Target the Streamlit button specifically for the Blue Sparkle */
    div.stButton > button {
        color: #3b82f6 !important;
        background-color: transparent !important;
        border: none !important;
        font-size: 30px !important;
        padding: 0px !important;
        line-height: 1 !important;
    }
    div.stButton > button:hover {
        color: #60a5fa !important;
        transform: scale(1.2);
    }
</style>
""", unsafe_allow_html=True)

# 2. SESSION STATE
if 'ai_generated' not in st.session_state:
    st.session_state.ai_generated = False
if 'ai_content' not in st.session_state:
    st.session_state.ai_content = {"summary": "", "insights": [], "actions": []}

# 3. DATA LOAD
# Note: Ensure the filename matches exactly what is in your GitHub
try:
    with open('Budget Execution Chart Data.json', 'r') as f:
        content = f.read()
        json_string = content.split('=', 1)[-1].strip().rstrip(';')
        data_raw = json.loads(json_string)
    chart_data = data_raw["widgets"][0]["chart"]
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 4. PROMPT TRIGGER FUNCTION
def trigger_intelligence():
    st.session_state.ai_generated = True
    # This is where your prompt will eventually live
    st.session_state.ai_content = {
        "summary": "This execution chart reveals a program experiencing significant execution delays relative to original plans.",
        "insights": [
            "Significant Forecast Revision Indicates Execution Delay",
            "Execution Tracking Below OSD Goals Creates Risk",
            "DFAS-CCaR Divergence Signals Accounting Lag",
            "Back-Loaded Execution Pattern Concentrates Risk"
        ],
        "actions": [
            "Investigate root cause of the DFAS-CCaR $5.8M divergence.",
            "Validate feasibility of the Current Forecast's aggressive ramp."
        ]
    }

# 5. RENDER UI - KPI HEADER
kpis = chart_data["kpis"]
kpi_cols = st.columns(len(kpis))
for i, kpi in enumerate(kpis):
    with kpi_cols[i]:
        st.markdown(f'<div class="kpi-card"><div style="font-size: 2.2rem; font-weight: bold; color: #3b82f6;">${kpi["value"]/1000000:,.1f}M</div><div style="color: #94a3b8;">{kpi["label"]}</div></div>', unsafe_allow_html=True)

st.divider()

# 6. MAIN LAYOUT
left, right = st.columns([2.2, 1])

with left:
    col_chart, col_sparkle = st.columns([0.92, 0.08])
    with col_sparkle:
        if st.button("✨", help="Generate AI Insights"):
            trigger_intelligence()

    # LINE CHART SETUP
    df_plot = pd.DataFrame({"Month": chart_data["xcategories"]})
    for s in chart_data["series"]:
        df_plot[s["label"]] = s["data"]
    
    fig = px.line(df_plot, x="Month", y=[s["label"] for s in chart_data["series"]], markers=True, template="plotly_dark")
    fig.update_traces(hovertemplate='<b>$ %{y}M</b><br>%{x}') 
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=20, b=80)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    tab_summary, tab_desc = st.tabs(["📝 Summary", "ℹ️ Description"])
    with tab_summary:
        if st.session_state.ai_generated:
            st.info(st.session_state.ai_content["summary"])
        else:
            st.info("Click the sparkle icon above to generate the AI summary.")

with right:
    st.markdown("### 🤖 AI-Powered Insights")
    if st.session_state.ai_generated:
        # COLLAPSIBLE EXPANDER
        with st.expander("View Generated Intelligence", expanded=True):
            for insight in st.session_state.ai_content["insights"]:
                st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)
            
            st.markdown("### ✅ Recommended Actions")
            for action in st.session_state.ai_content["actions"]:
                st.success(action)
    else:
        st.write("Click the blue sparkle ✨ to begin analysis.")
