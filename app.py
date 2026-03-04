import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go

# Load the cleaned JSON file
with open('budget_data.json', 'r') as f:
    raw_data = json.load(f)

# Navigate to the chart section within your specific JSON structure
data_json = raw_data["widgets"][0] # This enters the 'widgets' list to the first item
chart_meta = data_json["chart"]["meta"] # Accesses title, subtitle, etc.
