import streamlit as st
import pandas as pd
import plotly.express as px
import json
from openai import OpenAI

# 1. INITIALIZE AI CLIENT
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# Custom CSS - FIXED: Corrected color codes and syntax
st.markdown("""
<style>
    /* Card borders and padding */
    .kpi-card { border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #334155; margin-bottom: 20px; }
    .insight-card { border-radius: 8px; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 12px; border: 1px solid #334155; }
    
    /* Sparkle Button styling - FIXED blue color */
    .stButton>button {
        color: #3b82f6 !important; /* Forces the sparkle icon to be blue */
        border: none !important;
        background: transparent !important;
        font-size: 24px !important;
    }
    .stButton>button:hover {
        transform: scale(1.2);
        color: #60a5fa !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. SESSION STATE FOR "SPARKLE" TRIGGER
if 'ai_generated' not in st.session_state:
    st.session_state.ai_generated = False
if 'ai_content' not in st.session_state:
    st.session_state.ai_content = {"summary": "", "insights": [], "actions": []}

# 3. DATA LOAD
with open('Budget Execution Chart Data.json', 'r') as f:
    content = f.read()
    # Handle the JS variable assignment if present
    json_string = content.split('=', 1)[-1].strip().rstrip(';')
    data_raw = json.loads(json_string)

chart_data = data_raw["widgets"][0]["chart"]

# 4. PROMPT TRIGGER FUNCTION
def trigger_intelligence():
    st.session_state.ai_generated = True
    # System Prompt for dynamic generation
    sys_prompt = f"Analyze this CCaR data: {json.dumps(data_raw)}. Generate a summary, 4 insights, and 2 actions."
    
    # Placeholder for OpenAI call - Logic would go here
    st.session_state.ai_content = {
        "summary": "AI Generated Summary would appear here based on your prompt...",
        "insights": ["Insight 1", "Insight 2", "Insight 3", "Insight 4"],
        "actions": ["Action 1", "Action 2"]
    }

# 5. RENDER UI - KPI HEADER
kpi_cols = st.columns(3)
for i, kpi in enumerate(chart_data["kpis"]):
    with kpi_cols[i]:
        st.markdown(f'<div class="kpi-card"><div style="font-size: 2rem; font-weight: bold; color: #3b82f6;">${kpi["value"]/1000000:,.1f}M</div><div>{kpi["label"]}</div></div>', unsafe_allow_html=True)

st.divider()

# 6. MAIN LAYOUT
left, right = st.columns([2.2, 1])

with left:
    col_chart, col_sparkle = st.columns([0.95, 0.05])
    with col_sparkle:
        # Use button with blue CSS applied
        if st.button("✨", help="Generate AI Insights"):
            trigger_intelligence()

    # LINE CHART SETUP
    df = pd.DataFrame({"Month": chart_data["xcategories"]})
    for s in chart_data["series"]:
        df[s["label"]] = s["data"]
    
    fig = px.line(df, x="Month", y=[s["label"] for s in chart_data["series"]], 
                  markers=True, template="plotly_dark")
    
    # Hover Priority: Dollar Amount
    fig.update_traces(hovertemplate='<b>%{y}M</b><br>%{x}') 
    
    # Legend at Bottom
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
    )

    st.plotly_chart(fig, use_container_width=True)
    
    tab_summary, tab_desc = st.tabs(["📝 Summary", "ℹ️ Description"])
    with tab_summary:
        if st.session_state.ai_generated:
            st.write(st.session_state.ai_content["summary"])
        else:
            st.info("Click the sparkle icon above to generate the AI summary.")

with right:
    st.markdown("### 🤖 AI-Powered Insights")
    
    if st.session_state.ai_generated:
        # Collapsible drawer for AI content
        with st.expander("View Generated Intelligence", expanded=True):
            for insight in st.session_state.ai_content["insights"]:
                st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)
            
            st.markdown("### ✅ Recommended Actions")
            for action in st.session_state.ai_content["actions"]:
                st.success(action)
    else:
        st.markdown("*Awaiting intelligence generation...*")
