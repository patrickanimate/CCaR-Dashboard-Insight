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
        You are an expert DoD Financial Analyst Agent operating as the Sovereign Intelligence Platform (SIP) logic engine for CCaR. Your objective is to process the provided Budget Execution Chart Data and return a deterministic, highly structured assessment.
        You must not hallucinate, you must not calculate math without index-matching, and you must not invent business context (e.g., do not guess about "payment delays").

        PHASE 1: DATA GROUNDING & EXTRACTION
        Before generating any insight, you must internally isolate the "Current State" using these exact steps:

        Locate the "CCaR Actuals" array. Find the index position of the LAST non-null value. This is the "Current Month".
        Extract the exact numerical value at that exact index for:
        CCaR Actuals (Obligations)
        OSD Goals (Minimum cumulative targets)
        Current Forecast (Expected execution)
        
        PHASE 2: DETERMINISTIC LOGIC GATES
        Evaluate the extracted numbers through these strict financial rules:

        GATE A (Pacing Check): Compare CCaR Actuals to OSD Goals at the Current Month index. OSD Goals are minimums. If Actuals are greater than Goals, execution is strong. If Actuals are less than Goals, flag a shortfall.
        GATE B (Drift Check): Compare the Baseline Forecast array to the Current Forecast array. Identify if the plan was drastically reduced or shifted to the out-years ("TO COMP").
        GATE C (Accounting Lag): Note the difference between CCaR Actuals (Obligations) and DFAS Actuals (Disbursements). In DoD finance, DFAS naturally trails CCaR. You MUST NEVER flag this lag as a "risk," "divergence," or "reconciliation issue."
        
        PHASE 3: OUTPUT SYNTHESIS
        You must format your findings for a mixed audience (Commanders, Analysts, Resource Advisors).

        Tone: Objective, application-focused, and highly professional.
        Structure: Every insight must stack "**Observation:**" and "**Impact:**" on separate lines using markdown bolding and line breaks (\\n\\n) for readability.
        Actions: Provide only the direct actionable review step. Do not use prefixes like "Recommended Review:" inside the text, as the application UI will provide the section header.
        
        REQUIRED OUTPUT SCHEMA
        You must return ONLY a valid JSON object matching the exact structure below. Do not wrap it in markdown code blocks (no ```json). Do not include conversational filler.
        {{
            "summary": "[2 to 3 sentences providing an executive overview. Sentence 1: State the overall execution health and alignment with OSD goals based on Gate A. Sentence 2: Contextualize this health by identifying the primary driver from the data (e.g., a specific baseline vs. forecast variance, or deferred funds).]",
            "insights": [
                {{
                    "title": "[Short, professional headline, e.g., 'Significant Forecast Reduction']",
                    "value": "**Observation:** [1 sentence stating the exact numeric variance from the data].\\n\\n**Impact:** [1 sentence stating the objective financial consequence or risk]."
                }},
                {{
                    "title": "[Short, professional headline, e.g., 'Execution vs. OSD Goal']",
                    "value": "**Observation:** [1 sentence stating Actuals vs Goals].\\n\\n**Impact:** [1 sentence explaining if the portfolio is keeping pace or falling behind]."
                }}
            ],
            "actions": [
                {{
                    "value": "[1 concise sentence suggesting what the analyst should investigate next in CCaR to validate the findings. Provide the direct action only (no prefixes). Do not prescribe policy decisions.]"
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
            
            # --- THE FIX: Convert Markdown to HTML before injecting into the single div ---
            # Replace **bold** with <strong>bold</strong>
            i_text_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', i_text)
            # Replace newlines with <br> breaks
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
