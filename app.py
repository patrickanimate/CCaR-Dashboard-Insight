import streamlit as st
import pandas as pd
import plotly.express as px
import json
from openai import OpenAI

# 1. INITIALIZE AI CLIENT
# This pulls the key directly from your Streamlit Secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# Custom CSS for high-fidelity layout
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .kpi-card { background-color: #1e293b; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #334155; }
    .kpi-value { font-size: 2rem; font-weight: bold; color: #3b82f6; }
    .insight-card { background-color: #161b22; border-radius: 8px; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 12px; border: 1px solid #334155; }
    .chat-container { border: 1px solid #334155; border-radius: 8px; padding: 10px; background-color: #0d1117; height: 300px; overflow-y: auto; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# 2. DATA LOAD
# Using the data structure from your JSON file
data_raw = {
    "widgets": [{
        "chart": {
            "meta": {"title": "FY 2026 Budget Execution", "description": "Tracks budget authorization, forecasts, actuals, and OSD goals across FY 2026."},
            "series": [
                {"label": "Baseline Forecast", "data": [0.0, 5.8, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0]},
                {"label": "Current Forecast", "data": [0.0, 5.8, 5.8, 5.8, 5.8, 6.0, 11.0, 14.0, 18.0, 22.0, 22.0, 22.0, 25.0]},
                {"label": "CCaR Actuals", "data": [0.0, 5.8, 5.8, 5.8, 5.8, 5.8, None, None, None, None, None, None, None]},
                {"label": "DFAS Actuals", "data": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, None, None, None, None, None, None]},
                {"label": "OSD Goals", "data": [0.5, 0.9, 1.4, 1.8, 2.3, 2.7, 3.2, 3.6, 4.1, 4.5, 5.0, 5.4, None]},
                {"label": "Budget Authorized", "data": [5.0, 5.0, 15.0, 15.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0]}
            ],
            "kpis": [
                {"label": "CCaR Actuals Through Mar", "value": 5800000},
                {"label": "Total Budget Authorized", "value": 25000000},
                {"label": "Current Forecast to Completion", "value": 25000000}
            ],
            "xcategories": ["OCT", "NOV", "DEC", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "FY2027+"]
        }
    }]
}

chart_data = data_raw["widgets"][0]["chart"]

# 3. CHAT LOGIC
if 'messages' not in st.session_state:
    st.session_state.messages = []

def handle_chat():
    user_q = st.session_state.user_query
    if user_q:
        st.session_state.messages.append({"role": "user", "content": user_q})
        
        # SYSTEM PROMPT FOR DATA ANALYSIS
        sys_prompt = f"Analyze this CCaR budget data: {json.dumps(data_raw)}. Focus on the DFAS $0 vs CCaR $5.8M discrepancy and timeline risks."
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
        )
        st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
        st.session_state.user_query = ""

# 4. RENDER UI
st.title(f"📊 {chart_data['meta']['title']}")

# Top Metrics
cols = st.columns(3)
for i, kpi in enumerate(chart_data["kpis"]):
    cols[i].markdown(f'<div class="kpi-card"><div class="kpi-value">${kpi["value"]/1000000:,.1f}M</div><div>{kpi["label"]}</div></div>', unsafe_allow_html=True)

st.divider()

left, right = st.columns([2, 1])

with left:
    # Line Chart
    df = pd.DataFrame({"Month": chart_data["xcategories"]})
    for s in chart_data["series"]:
        df[s["label"]] = s["data"]
    fig = px.line(df, x="Month", y=[s["label"] for s in chart_data["series"]], markers=True, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary Section (Matches Screenshot)
    st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #334155;">', unsafe_allow_html=True)
    st.markdown("### 📋 Executive Summary")
    st.write(chart_data["meta"]["description"] + " Notable red flag: zero DFAS actuals despite $5.8M CCaR obligations.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown("### 🤖 AI Insights & Chat")
    st.markdown('<div class="insight-card"><strong>Divergence Detected</strong><br>CCaR at $5.8M vs DFAS at $0. Possible accounting lag.</div>', unsafe_allow_html=True)
    
    # Chat History
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for m in st.session_state.messages:
        role = "👤" if m["role"] == "user" else "✨"
        st.write(f"{role} {m['content']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.text_input("Ask about the data...", key="user_query", on_change=handle_chat)
