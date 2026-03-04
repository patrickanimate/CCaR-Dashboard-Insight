import streamlit as st
import pandas as pd
import plotly.express as px
import json
from openai import OpenAI

# 1. INITIALIZE AI CLIENT
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# Custom CSS for high-fidelity cards and sparkle button
st.markdown("""
<style>
    /* Card borders and padding */
    .kpi-card { border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #334155; margin-bottom: 20px; }
    .insight-card { border-radius: 8px; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 12px; border: 1px solid #334155; }
    
    /* Sparkle Button styling */
    .sparkle-btn { cursor: pointer; font-size: 24px; transition: 0.3s; }
    .sparkle-btn:hover { transform: scale(1.2); color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# 2. SESSION STATE FOR "SPARKLE" TRIGGER
if 'ai_generated' not in st.session_state:
    st.session_state.ai_generated = False
if 'ai_content' not in st.session_state:
    st.session_state.ai_content = {"summary": "", "insights": [], "actions": []}

# 3. DATA LOAD (From your JSON)
# (For the prototype, we keep the JSON reference, but the prompt will extract the text)
with open('Budget Execution Chart Data.json', 'r') as f:
    content = f.read()
    json_string = content.split('=', 1)[-1].strip().rstrip(';')
    data_raw = json.loads(json_string)

chart_data = data_raw["widgets"][0]["chart"]

# 4. PROMPT TRIGGER FUNCTION
def trigger_intelligence():
    st.session_state.ai_generated = True
    # Your System Prompt goes here to generate the insights dynamically
    sys_prompt = f"Analyze this CCaR data and generate: 1. A summary, 2. Four key insights, 3. Two actions. Data: {json.dumps(data_raw)}"
    
    # Placeholder for OpenAI call to populate st.session_state.ai_content
    # response = client.chat.completions.create(...)
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
    # SPARKLE ICON TRIGGER
    col_chart, col_sparkle = st.columns([0.95, 0.05])
    with col_sparkle:
        if st.button("✨", help="Generate AI Insights"):
            trigger_intelligence()

    # LINE CHART WITH DOLLAR-FIRST TOOLTIPS
    df = pd.DataFrame({"Month": chart_data["xcategories"]})
    for s in chart_data["series"]:
        df[s["label"]] = s["data"]
    
    fig = px.line(df, x="Month", y=[s["label"] for s in chart_data["series"]], 
                  markers=True, template="plotly_dark")
    
    # Force tooltip to show Dollar Amount prominently
    fig.update_traces(hovertemplate='<b>%{y}M</b><br>%{x}') 
    st.plotly_chart(fig, use_container_width=True)
    # --- ADD THESE LINES HERE ---
    fig.update_layout(
        legend=dict(
            orientation="h",   # horizontal legend
            yanchor="bottom",
            y=-0.5,            # pushes it below the chart
            xanchor="center",
            x=0.5              # centers it
        )
    )
    # ----------------------------

    st.plotly_chart(fig, use_container_width=True)
    
    # TABBED SUMMARY SECTION
    tab_summary, tab_desc = st.tabs(["📝 Summary", "ℹ️ Description"])
    with tab_summary:
        if st.session_state.ai_generated:
            st.write(st.session_state.ai_content["summary"])
        else:
            st.info("Click the sparkle icon above to generate the AI summary.")

with right:
    st.markdown("### 🤖 AI-Powered Insights")
    if st.session_state.ai_generated:
        for insight in st.session_state.ai_content["insights"]:
            st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)
        
        st.markdown("### ✅ Recommended Actions")
        for action in st.session_state.ai_content["actions"]:
            st.success(action)
    else:
        st.markdown("*Awaiting intelligence generation...*")
