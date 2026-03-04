import streamlit as st
import pandas as pd
import plotly.express as px
import json
import re
from openai import OpenAI

# 1. INITIALIZE AI CLIENT
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# 2. CUSTOM CSS
st.markdown("""
<style>
    .kpi-card { border-radius: 10px; padding: 20px; text-align: center; border: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 20px; }
    .insight-card { border-radius: 8px; padding: 15px; margin-bottom: 12px; border-top: 1px solid rgba(128, 128, 128, 0.2); border-right: 1px solid rgba(128, 128, 128, 0.2); border-bottom: 1px solid rgba(128, 128, 128, 0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.05); background-color: transparent; }
    .insight-title { font-weight: bold; font-size: 1.05rem; margin-bottom: 6px; }
    .insight-text { font-size: 0.9rem; line-height: 1.4; opacity: 0.75; }
    
    /* Sparkle Button */
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
    
    /* Chat bubbles styling */
    .chat-user { background-color: rgba(59, 130, 246, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #3b82f6; }
    .chat-ai { background-color: rgba(128, 128, 128, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #94a3b8; }
</style>
""", unsafe_allow_html=True)

# 3. SMART SESSION STATE
if 'show_insights' not in st.session_state:
    st.session_state.show_insights = False
if 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = False
if 'ai_content' not in st.session_state:
    st.session_state.ai_content = {}
# Chat states
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you analyze this execution data?"}]
if 'user_query' not in st.session_state:
    st.session_state.user_query = ""

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

# 5. FUNCTIONS
def toggle_intelligence():
    st.session_state.show_insights = not st.session_state.show_insights
    
    if st.session_state.show_insights and not st.session_state.data_fetched:
        prompt = f"""
        You are a senior DoD Financial Analyst Agent operating as the Sovereign Intelligence Platform (SIP) logic engine for CCaR. Your objective is to process the provided Budget Execution Chart Data and return a deterministic, highly structured assessment.
        You must not hallucinate, you must not calculate math without index-matching, and you must not invent business context (e.g., do not guess about "payment delays").

        PHASE 1: DATA GROUNDING & EXTRACTION
        Before generating any insight, you must internally isolate the "Current State" and "End of Year (EOY) State" using these exact steps:
        1. Find the "Current Month": Locate the index position of the LAST non-null value in the "CCaR Actuals" array.
        2. Extract Current Month Values: Extract the exact numerical value at that index for "CCaR Actuals" and "OSD Goals".
        3. Extract EOY Values: Locate the "SEP" (September) index or the final numerical month index. Extract the exact numerical values for "Baseline Forecast", "Current Forecast", and "Budget Authorized".

        PHASE 2: DETERMINISTIC LOGIC GATES
        Evaluate the extracted numbers through these strict financial rules. You MUST base your insights on these three gates:
        - GATE A (Pacing Check): Compare [Current Month CCaR Actuals] to [Current Month OSD Goals]. If Actuals > Goals, execution is strong. If Actuals < Goals, flag a shortfall.
        - GATE B (Drift Check): Compare [EOY Baseline Forecast] to [EOY Current Forecast]. If the Current Forecast is lower, the plan has been reduced or deferred. State the exact numeric difference.
        - GATE C (Authorization Gap): Compare [EOY Budget Authorized] to [EOY Current Forecast]. If Forecast < Authorized, there are unforecasted/unused funds remaining in the fiscal year.
        - RULE: In DoD finance, DFAS (Disbursements) naturally trails CCaR (Obligations). NEVER flag a CCaR vs. DFAS lag as a risk or divergence.

        PHASE 3: OUTPUT SYNTHESIS
        You must format your findings for a mixed audience (Commanders, Analysts, Resource Advisors).
        Tone: Objective, application-focused, and highly professional.
        Structure: Every insight must stack "**Observation:**" and "**Impact:**" using markdown line breaks (\\n\\n).
        
        REQUIRED OUTPUT SCHEMA
        Return ONLY a valid JSON object matching the exact structure below. Output exactly 3 insights (one for each Gate) and 2 to 3 specific actions.
        {{
            "summary": "[2 to 3 sentences. Sentence 1: State overall execution pacing based on Gate A. Sentence 2: Contextualize the EOY trajectory based on Gates B and C (e.g., noting if funds are deferred or forecasts are reduced).]",
            "insights": [
                {{
                    "title": "Execution vs. OSD Goal",
                    "value": "**Observation:** [1 sentence stating Current Month Actuals vs Goals].\\n\\n**Impact:** [1 sentence explaining if the portfolio is keeping pace or falling behind]."
                }},
                {{
                    "title": "Forecast Drift & Trajectory",
                    "value": "**Observation:** [1 sentence stating EOY Baseline vs EOY Current Forecast].\\n\\n**Impact:** [1 sentence stating the objective financial consequence of this shift]."
                }},
                {{
                    "title": "Authorization Utilization",
                    "value": "**Observation:** [1 sentence stating EOY Budget Authorized vs EOY Current Forecast].\\n\\n**Impact:** [1 sentence stating the risk of unexecuted funds or carryover]."
                }}
            ],
            "actions": [
                {{
                    "value": "[1 concise sentence suggesting a specific CCaR review step based on Gate B (e.g., 'Validate the cause of the forecast reduction...'). No prefixes.]"
                }},
                {{
                    "value": "[1 concise sentence suggesting a specific CCaR review step based on Gate C (e.g., 'Review unforecasted authorized funds to prevent expiration...'). No prefixes.]"
                }}
            ]
        }}
        
        DATA TO ANALYZE:
        {json.dumps(data_raw)}
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
            st.session_state.ai_content = json.loads(response.choices[0].message.content)
            st.session_state.data_fetched = True
        except Exception as e:
            st.error(f"AI Analysis Failed: {e}")
            st.session_state.show_insights = False

def handle_chat():
    user_q = st.session_state.user_query
    if user_q:
        st.session_state.messages.append({"role": "user", "content": user_q})
        
        sys_prompt = f"You are a budget analyst. Answer questions based ONLY on this data: {json.dumps(data_raw)}. Keep answers concise."
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
            )
            st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
        
        st.session_state.user_query = ""

# 6. RENDER UI - KPI HEADER
kpis = chart_data["kpis"]
kpi_cols = st.columns(len(kpis))
for i, kpi in enumerate(kpis):
    with kpi_cols[i]:
        st.markdown(f'<div class="kpi-card"><div style="font-size: 2.2rem; font-weight: bold; color: #3b82f6;">${kpi["value"]/1000000:,.1f}M</div><div style="opacity: 0.7;">{kpi["label"]}</div></div>', unsafe_allow_html=True)

st.divider()

# 7. MAIN LAYOUT
left, right = st.columns([2.2, 1])

with left:
    col_chart, col_sparkle = st.columns([0.95, 0.05])
    with col_sparkle:
        st.button("✨", help="Toggle AI Insights", on_click=toggle_intelligence)

    df_plot = pd.DataFrame({"Month": chart_data["xcategories"]})
    for s in chart_data["series"]:
        df_plot[s["label"]] = s["data"]
    
    fig = px.line(df_plot, x="Month", y=[s["label"] for s in chart_data["series"]], markers=True)
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
            summary_text = st.session_state.ai_content.get("summary", "")
            st.markdown(f'<div style="font-size: 1rem; line-height: 1.5; opacity: 0.85;">{summary_text}</div>', unsafe_allow_html=True)
        else:
            st.info("Click the blue sparkle ✨ icon to generate intelligence.")
    with tab_desc:
        st.write(chart_data["meta"]["description"])

# RIGHT COLUMN - TOGGLEABLE AI PANEL + CHAT
with right:
    if st.session_state.show_insights and st.session_state.data_fetched:
        st.markdown("### 🤖 AI-Powered Insights")
        
        border_colors = ["#8db6d9", "#f5b066", "#9bd3a1", "#94a3b8"]
        
        for i, insight in enumerate(st.session_state.ai_content.get("insights", [])):
            b_color = border_colors[i % len(border_colors)]
            
            i_title = insight.get("title", "") if isinstance(insight, dict) else "Insight"
            i_text = insight.get("value", insight.get("description", "")) if isinstance(insight, dict) else str(insight)
            
            # --- Convert Markdown to HTML before injecting into the single div ---
            i_text_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', i_text)
            i_text_html = i_text_html.replace('\n', '<br>')
            
            st.markdown(f'''
                <div class="insight-card" style="border-left: 5px solid {b_color};">
                    <div class="insight-title">{i_title}</div>
                    <div class="insight-text">{i_text_html}</div>
                </div>
            ''', unsafe_allow_html=True)
        
        st.markdown("### ✅ Recommended Actions")
        for action in st.session_state.ai_content.get("actions", []):
            a_text = action.get("value", "") if isinstance(action, dict) else str(action)
            st.success(a_text)
            
        st.divider()
        
        # --- INTERACTIVE CHAT SECTION ---
        st.markdown("### 💬 Ask about this data")
        chat_container = st.container(height=300)
        with chat_container:
            for m in st.session_state.messages:
                if m["role"] == "user":
                    st.markdown(f'<div class="chat-user"><b>You:</b> {m["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-ai"><b>✨ AI:</b> {m["content"]}</div>', unsafe_allow_html=True)
        
        st.text_input("Type your question here...", key="user_query", on_change=handle_chat)
