import streamlit as st
import pandas as pd
import plotly.express as px
import json
from openai import OpenAI

# 1. INITIALIZE AI CLIENT
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# 2. CUSTOM CSS - Restored High-Fidelity Visuals
st.markdown("""
<style>
    .kpi-card { border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #334155; margin-bottom: 20px; }
    
    /* Perfecting the Insight Cards to match the screenshot */
    .insight-card { background-color: #161b22; border-radius: 8px; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 12px; border-top: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155; }
    .insight-title { color: #f1f5f9; font-weight: bold; font-size: 1.05rem; margin-bottom: 6px; }
    .insight-text { color: #cbd5e1; font-size: 0.9rem; line-height: 1.4; }
    
    /* Forcing the Sparkle Button to be Blue and act like an icon */
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
        transform: scale(1.1);
    }
</style>
""", unsafe_allow_html=True)

# 3. SMART SESSION STATE
# 'show_insights' controls visibility (the toggle)
if 'show_insights' not in st.session_state:
    st.session_state.show_insights = False
# 'data_fetched' ensures we only call OpenAI once per session
if 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = False
if 'ai_content' not in st.session_state:
    st.session_state.ai_content = {}

# 4. DATA LOAD
try:
    with open('Budget Execution Chart Data.json', 'r') as f:
        content = f.read()
        json_string = content.split('=', 1)[-1].strip().rstrip(';')
        data_raw = json.loads(json_string)
    chart_data = data_raw["widgets"][0]["chart"]
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 5. SMART TOGGLE & FETCH FUNCTION
def toggle_intelligence():
    # Flip the visibility state
    st.session_state.show_insights = not st.session_state.show_insights
    
    # Only run the AI if we are showing the panel AND haven't fetched data yet
    if st.session_state.show_insights and not st.session_state.data_fetched:
        
        prompt = f"""
        Analyze the following CCaR budget data and provide strategic insights.
        Data: {json.dumps(data_raw)}
        
        Return your response EXACTLY as a JSON object with this exact structure:
        {{
            "summary": "A 3-sentence executive summary of the execution risks.",
            "insights": [
                {{"title": "Insight Title 1", "description": "Detailed explanation 1"}},
                {{"title": "Insight Title 2", "description": "Detailed explanation 2"}},
                {{"title": "Insight Title 3", "description": "Detailed explanation 3"}}
            ],
            "actions": ["Recommended Action 1", "Recommended Action 2"]
        }}
        Focus heavily on the $5.8M CCaR actuals vs $0 DFAS actuals, and the timeline compression risk created by deferring the $25M baseline to a $22M current forecast.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior DoD budget analyst specializing in CCaR data."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            # Save the data and mark as fetched
            st.session_state.ai_content = json.loads(response.choices[0].message.content)
            st.session_state.data_fetched = True
            
        except Exception as e:
            st.error(f"AI Analysis Failed: {e}")
            # Fallback so your demo doesn't break if API fails
            st.session_state.show_insights = False

# 6. RENDER UI - KPI HEADER
kpis = chart_data["kpis"]
kpi_cols = st.columns(len(kpis))
for i, kpi in enumerate(kpis):
    with kpi_cols[i]:
        st.markdown(f'<div class="kpi-card"><div style="font-size: 2.2rem; font-weight: bold; color: #3b82f6;">${kpi["value"]/1000000:,.1f}M</div><div style="color: #94a3b8;">{kpi["label"]}</div></div>', unsafe_allow_html=True)

st.divider()

# 7. MAIN LAYOUT
left, right = st.columns([2.2, 1])

with left:
    # SPARKLE ICON TRIGGER (Now uses on_click callback)
    col_chart, col_sparkle = st.columns([0.95, 0.05])
    with col_sparkle:
        st.button("✨", help="Toggle AI Insights", on_click=toggle_intelligence)

    # LINE CHART SETUP
    df_plot = pd.DataFrame({"Month": chart_data["xcategories"]})
    for s in chart_data["series"]:
        df_plot[s["label"]] = s["data"]
    
    fig = px.line(df_plot, x="Month", y=[s["label"] for s in chart_data["series"]], markers=True, template="plotly_dark")
    fig.update_traces(hovertemplate='<b>$ %{y}M</b><br>%{x}') 
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=10, b=80)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # TABBED SUMMARY
    tab_summary, tab_desc = st.tabs(["📝 Summary", "ℹ️ Description"])
    with tab_summary:
        if st.session_state.show_insights and st.session_state.data_fetched:
            st.info(st.session_state.ai_content.get("summary", ""))
        else:
            st.info("Click the blue sparkle ✨ icon to generate intelligence.")
    with tab_desc:
        st.write(chart_data["meta"]["description"])

# RIGHT COLUMN - TOGGLEABLE AI PANEL
with right:
    # Only render this entire section if the toggle is ON
    if st.session_state.show_insights and st.session_state.data_fetched:
        st.markdown("### 🤖 AI-Powered Insights")
        
        # Loop through the structured JSON objects to recreate the screenshot layout
        for insight in st.session_state.ai_content.get("insights", []):
            st.markdown(f'''
                <div class="insight-card">
                    <div class="insight-title">{insight["title"]}</div>
                    <div class="insight-text">{insight["description"]}</div>
                </div>
            ''', unsafe_allow_html=True)
        
        st.markdown("### ✅ Recommended Actions")
        for action in st.session_state.ai_content.get("actions", []):
            st.success(action)
