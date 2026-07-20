import streamlit as st
import pandas as pd
import openai
import os
import requests
from requests.auth import HTTPBasicAuth
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Automated AI Fitness Coach", layout="wide")
st.title("🏋️‍♂️ RoyFit AI Fitness Analytics")

# 1. Load Background Security Secrets
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ATHLETE_ID = os.environ.get("INTERVALS_ATHLETE_ID")
INTERVALS_KEY = os.environ.get("INTERVALS_API_KEY")
openai.api_key = OPENAI_API_KEY

# 2. Establish Automated Live Background Streamer
@st.cache_data(ttl=600) # Caches data for 10 minutes so it loads instantly without crashing APIs
def fetch_live_intervals_data():
    if not ATHLETE_ID or not INTERVALS_KEY:
        st.error("❌ Missing Intervals.icu credentials in Streamlit Advanced Settings.")
        return None
        
    # Calculate a rolling historical lookback window (Past 30 days)
    old_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    now_date = datetime.now().strftime('%Y-%m-%d')
    
    # Secure API Call directly into your Intervals account
    url = f"https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/activities"
    params = {"oldest": old_date, "newest": now_date}
    
    # Intervals.icu uses basic authentication (API_KEY as username)
    response = requests.get(url, params=params, auth=HTTPBasicAuth('API_KEY', INTERVALS_KEY))
    
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error(f"❌ Failed to stream live data. API Status Code: {response.status_code}")
        return None

# 3. Process the Streaming Pipeline
df = fetch_live_intervals_data()

if df is not None and not df.empty:
    st.success("⚡ Live background data stream synchronized successfully!")
    
    try:
        # Standardize live dates and core workout parameters
        df['Clean_Date'] = pd.to_datetime(df['start_date_local']).dt.date
        df = df.sort_values(by='Clean_Date')
        
        # Isolate Training Load (TRIMP) metrics and Workout Type
        load_col = 'icu_training_load' if 'icu_training_load' in df.columns else 'training_load'
        type_col = 'type' if 'type' in df.columns else 'name'
        
        # 4. Draw Interactive Progress Dashboards
        st.subheader("📈 Live Physical Stress & Strain Progression")
        
        if load_col in df.columns:
            fig = px.bar(df, x='Clean_Date', y=load_col, color=type_col if type_col in df.columns else None,
                         title="Daily Workout Training Stress (TRIMP Metrics)",
                         labels={load_col: "Training Load Score (TRIMP)"})
            st.plotly_chart(fig, use_container_width=True)
            
            # Show Clean Activity History List
            with st.expander("📋 View Synchronized Activity Feed"):
                display_cols = [c for c in ['Clean_Date', type_col, load_col, 'moving_time'] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True)
        
        # 5. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength & Endurance Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Analyzing live training load progression parameters..."):
                    # Compress data layout rows into plain text string for the AI coach
                    data_summary_string = df[['Clean_Date', type_col, load_col]].dropna().to_string(index=False)
                    
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an elite sports scientist analyzing real-time training loads (TRIMP metrics)."},
                            {"role": "user", "content": f"Review this automated 30-day training stress data. Assess if my workout progression is optimized for safe progression without risking injury or overtraining, and give clear, direct advice on volume adjustments:\n{data_summary_string}"}
                        ]
                    )
                    st.write(response.choices[0].message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
                
    except Exception as e:
        st.error(f"Processing Error: {e}")
else:
    st.info("🔄 Syncing data stream... Ensure your credentials are typed inside your app secrets panel.")
