import streamlit as st
import pandas as pd
import plotly.express as px
import json

# --- 1. PAGE SETUP & CSS VISUAL POLISH ---
# Match the screenshot's wide aspect ratio and title.
st.set_page_config(layout="wide", page_title="CCaR Insights Prototype")

# Define CSS to perfectly mimic the target UI cards, colors, and spacing.
# This makes your prompt comparison tests look realistic.
st.markdown("""
<style>
    /* Main Dark Theme Background */
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }

    /* Top KPI Row Cards */
    .kpi-card { background-color: #1e293b; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #334155; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .kpi-value { font-size: 2.2rem; font-weight: bold; color: #3b82f6; }
    .kpi-label { font-size: 0.9rem; color: #94a3b8; }

    /* AI-Powered Insights Cards with left colored borders */
    .insight-card { background-color: #161b22; border-radius: 8px; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 12px; border-top: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155; }
    .insight-title { color: #f1f5f9; font-weight: bold; font-size: 1.1rem; }
    .insight-text { color: #cbd5e1; font-size: 0.95rem; line-height: 1.5; }

    /* Recommended Actions Section and Items */
    .action-header { color: #3b82f6; font-size: 1.3rem; margin-top: 25px; margin-bottom: 15px; font-weight: bold; }
    .action-item { background-color: #161b22; border-radius: 8px; padding: 12px; margin-bottom: 10px; color: #cbd5e1; font-size: 0.95rem; border: 1px solid #334155; display: flex; align-items: start; }
    .action-icon { color: #3b82f6; font-weight: bold; margin-right: 10px; font-size: 1.2rem; }

    /* Interactive Chat Components at the bottom right */
    .chat-container { border: 1px solid #334155; border-radius: 8px; padding: 15px; background-color: #161b22; height: 350px; overflow-y: scroll; margin-top: 10px; margin-bottom: 15px; }
    .chat-row { display: flex; align-items: center; margin-bottom: 10px; padding: 8px; border-radius: 8px; }
    .chat-row.user { background-color: #1e293b; color: #f1f5f9; justify-content: flex-end; }
    .chat-row.bot { background-color: #0d1117; color: #cbd5e1; }
    .chat-avatar { color: #3b82f6; font-size: 1.2rem; margin-right: 10px; }
    .sparkle-icon { color: #3b82f6; font-weight: bold; margin-right: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA PROCESSING (TIDYING THE JSON) ---
# Paste your original JSON data below to initialize the dashboard.
data_raw = {
    "version": "1.0",
    "widgets": [{
        "widgetId": 99999,
        "widgetTypeKey": "BUDGET_EXECUTION_SNAKE",
        "status": "ok",
        "message": None,
        "errorId": None,
        "chart": {
            "meta": {
                "title": "FY 2026 Budget Execution",
                "subtitle": "Months of FY 2026",
                "description": "Tracks budget authorization, forecasts, actuals, and OSD goals across FY 2026.",
                "xlabel": "Month",
                "ylabel": "USD (Millions)"
            },
            "series": [
                {"label": "Baseline Forecast ($M)", "data": [0.0, 5.8, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0]},
                {"label": "Current Forecast ($M)", "data": [0.0, 5.8, 5.8, 5.8, 5.8, 6.0, 11.0, 14.0, 18.0, 22.0, 22.0, 22.0, 25.0]},
                {"label": "CCaR Actuals ($M)", "data": [0.0, 5.8, 5.8, 5.8, 5.8, 5.8, None, None, None, None, None, None, None]},
                {"label": "DFAS Actuals ($M)", "data": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, None, None, None, None, None, None]},
                {"label": "OSD Goals ($M)", "data": [0.5, 0.9, 1.4, 1.8, 2.3, 2.7, 3.2, 3.6, 4.1, 4.5, 5.0, 5.4, None]},
                {"label": "Budget Authorized ($M)", "data": [5.0, 5.0, 15.0, 15.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0]}
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
kpis = chart_data["kpis"]
xcats = chart_data["xcategories"]

# Transform tidy data structure for Plotly. Handle None values as line breaks for actuals.
tidy_df = pd.DataFrame({'Month': xcats})
for ser in chart_data["series"]:
    tidy_df[ser["label"]] = ser["data"]

# Melt for long format Plotly uses for coloring and legend.
long_df = tidy_df.melt(id_vars=['Month'], var_name='Metric', value_name='Millions')

# Define custom colors to match the screenshot lines.
color_palette = {
    "Baseline Forecast ($M)": "#5ac8fa",
    "Current Forecast ($M)": "#ffcc00",
    "CCaR Actuals ($M)": "#4cd964",
    "DFAS Actuals ($M)": "#ff3b30",
    "OSD Goals ($M)": "#ff9500",
    "Budget Authorized ($M)": "#c7c7cc"
}

# --- 3. STATEFUL INTERACTIVE CHAT INTIALIZATION ---
# Session state is how Streamlit stores memory.
if 'chat_messages' not in st.session_state:
    # Initialize with default placeholders or clear state.
    st.session_state.chat_messages = [
        {"role": "bot", "content": "How can I help you analyze the FY 2026 Budget Execution data today?"}
    ]

# Callback to process input and generate mock responses. This is where your prompt tests will plug in.
def submit_chat():
    user_input = st.session_state.chat_input
    if user_input:
        # Append User Message.
        st.session_state.chat_messages.append({"role": "user", "content": user_input})

        # --- THIS AREA WILL USE YOUR TEST PROMPTS AGAINST THE DATA ---
        if "risk" in user_input.lower():
            response = "**AI INSIGHT (Testing Prompt):** Based on the chart, the risk is 'Significant Forecast Revision Downward' deferring $25M spending to FY2027+. This creates a compressed timeline risk."
        elif "dfas" in user_input.lower():
            response = "**AI INSIGHT (Testing Prompt):** Current analysis confirms DFAS actuals remain at $0M through March despite CCaR Obligations of $5.8M. This is a major red flag for disbursement bottlenecks."
        else:
            response = "I see your question about '{}'. I can analyze the $5.8M CCaR actuals or the $25M forecast based on our model's logic. Try asking about specific metrics or risks."

        # Append Bot Message.
        st.session_state.chat_messages.append({"role": "bot", "content": response})

        # Clear input box after submission.
        st.session_state.chat_input = ""

# --- 4. RENDER LAYOUT: TOP KPIs ---
st.title(f"📊 {chart_data['meta']['title']} Dashboard")

kpi_cols = st.columns(len(kpis))
for i, kpi in enumerate(kpis):
    with kpi_cols[i]:
        # Using custom CSS for metric boxes matching the target visual.
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">${kpi['value']/1000000:,.1f}M</div>
            <div class="kpi-label">{kpi['label']}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# --- 5. RENDER LAYOUT: MAIN DASHBOARD (Chart + Tabs vs Insights + Chat) ---
main_left, main_right = st.columns([2.2, 1])  # 2.2/3 Left, 1/3 Right ratio.

# --- LEFT: CHART & SUMMARY TABS ---
with main_left:
    st.markdown(f"### {chart_data['meta']['title'].upper()} CHART ANALYSIS")

    # Create Plotly Chart with wide aesthetic, dark theme, custom colors, and legend at bottom.
    fig = px.line(long_df, x='Month', y='Millions', color='Metric',
                  color_discrete_map=color_palette, markers=True, template="plotly_dark")
    fig.update_layout(xaxis_title='Month of FY 2026', yaxis_title='USD (Millions)', height=500,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig, use_container_width=True)

    # Tabs component for Summary/Description below chart.
    tab1, tab2 = st.tabs(["📝 SUMMARY", "ℹ️ DESCRIPTION"])
    with tab1:
        st.info("**SUMMARY (Testing Prompt Response):** " + chart_data["meta"]["description"] + " Program reveals significant revision downward from aggressive baseline plan. Program is *exceeding* OSD goals signal, but dramatic first-half slow execution creates potential risks of unexecuted funds later. Investigation into the zero DFAS actuals signal against $5.8M in CCaR obligations is needed.")
    with tab2:
        st.write("Detailed metadata, assumptions, and JSON structure details would be documented here for prompt context refinement.")

# --- RIGHT: AI INSIGHTS, ACTIONS, CHAT ---
with main_right:
    st.markdown("### ✨ AI-POWERED INSIGHTS")

    # Create cards matching the insights in the screenshot visually.
    st.markdown("""
        <div class="insight-card">
            <div class="insight-title">Significant Forecast Revision Downward</div>
            <div class="insight-text">The Current Forecast dropped from $25M baseline to a much slower ramp, reaching only $22M by August. Defers substantial spending into future fiscal years.</div>
        </div>
        <div class="insight-card">
            <div class="insight-title">Execution Tracking Below OSD Goals</div>
            <div class="insight-text">Through March, CCaR Actuals ($5.8M cumulative) track *below* March OSD goals ($2.7M target). Current forecast projects continued underperformance vs revised goals through September.</div>
        </div>
        <div class="insight-card">
            <div class="insight-title">DFAS-CCaR Divergence Signal</div>
            <div class="insight-text">DFAS actual disbursements remain at ZERO through March, contrasting sharply with $5.8M executed obligations on the CCaR track. Suggests timing lag in payment processing or significant accounting issues.</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="action-header">✅ RECOMMENDED ACTIONS</div>', unsafe_allow_html=True)
    # Using flexbox action items with blue arrow icons.
    st.markdown("""
        <div class="action-item"><span class="action-icon">→</span>Investigate root cause of the DFAS-CCaR $5.8M divergence to confirm proper conversion to disbursements and identify bottlenecks.</div>
        <div class="action-item"><span class="action-icon">→</span>Validate current forecast timing given slow start execution pace to assess risk of compressed timeline later.</div>
    """, unsafe_allow_html=True)

    # --- THE INTERACTIVE CHAT TESTING GROUND ---
    # Container for rendering the scrollable chat history visually.
    chat_box = st.container()
    with chat_box:
        st.markdown('<div class="chat-container" id="chat_messages_div">', unsafe_allow_html=True)
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-row user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-row bot"><span class="sparkle-icon">✨</span>{msg["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input text box at the very bottom right.
    # Using 'key' connects it to session state, 'on_change' triggers callback function submit_chat.
    st.text_input("Ask a question about this chart...", key="chat_input", on_change=submit_chat, placeholder="e.g., Explain the DFAS risk")
