import streamlit as st
import pandas as pd
import openai
import os
import requests
from requests.auth import HTTPBasicAuth
import plotly.express as px
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="RoyFit AI Coach", layout="wide")
st.title("🏋️‍♂️ RoyFit AI Analytics & RPE Fatigue Tracker 🤴")
st.markdown("*Bringing **IT** back to fitness*")

# 1. Load Background Security Secrets from Streamlit
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ATHLETE_ID = os.environ.get("INTERVALS_ATHLETE_ID")
INTERVALS_KEY = os.environ.get("INTERVALS_API_KEY")
openai.api_key = OPENAI_API_KEY

# 2. Establish Automated Live Background Streamer
@st.cache_data(ttl=300) # Caches data for 5 minutes to optimize performance
def fetch_live_intervals_data():
    if not ATHLETE_ID or not INTERVALS_KEY:
        st.error("❌ Missing Intervals.icu credentials in Streamlit Advanced Settings.")
        return None
        
    old_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    now_date = datetime.now().strftime('%Y-%m-%d')
    
    # FIXED: Corrected path layout with API versioning routing
    url = f"https://intervals.icu{ATHLETE_ID}/activities"
    params = {"oldest": old_date, "newest": now_date}
    
    # Secure API Call using raw string token authentication
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
        
        load_col = 'icu_training_load' if 'icu_training_load' in df.columns else 'training_load'
        type_col = 'type' if 'type' in df.columns else 'name'
        desc_col = 'description' if 'description' in df.columns else 'description'

        # --- ADVANCED RPE EXTRACTION FILTER ENGINE ---
        rpe_records = []
        
        if desc_col in df.columns:
            for idx, row in df.iterrows():
                text_block = str(row[desc_col])
                workout_date = row['Clean_Date']
                workout_type = row[type_col] if type_col in df.columns else "Workout"
                
                # Scans text notes for formats like "RPE 8", "RPE:9", "@8.5", or "@8"
                rpe_matches = re.findall(r'(?:rpe[:\s]*|@\s*)(\d+\.?\d*)', text_block, re.IGNORECASE)
                
                if rpe_matches:
                    # Convert found RPE strings to numbers and calculate peak workout intensity
                    numeric_rpes = [float(val) for val in rpe_matches if float(val) <= 10]
                    if numeric_rpes:
                        peak_rpe = max(numeric_rpes)
                        avg_rpe = sum(numeric_rpes) / len(numeric_rpes)
                        rpe_records.append({
                            "Date": workout_date,
                            "Type": workout_type,
                            "Peak RPE": peak_rpe,
                            "Avg RPE": avg_rpe
                        })
        
        # 4. Draw Interactive Progress Dashboards
        st.subheader("📈 Live Physical Stress & Strain Progression")
        
        # Chart A: Training Stress Over Time (TRIMP)
        if load_col in df.columns:
            fig_load = px.bar(df, x='Clean_Date', y=load_col, color=type_col if type_col in df.columns else None,
                             title="Daily Workout Training Stress (TRIMP Metrics)",
                             labels={load_col: "Training Load Score (TRIMP)"})
            st.plotly_chart(fig_load, use_container_width=True)

        # Chart B: Muscular RPE Fatigue Timeline
        if rpe_records:
            rpe_df = pd.DataFrame(rpe_records)
            st.subheader("🔥 Muscular Fatigue & RPE Intensity Trends")
            
            fig_rpe = px.line(rpe_df, x='Date', y='Peak RPE', markers=True, color='Type',
                             title="Peak Workout Difficulty Profile (RPE 1-10 Scale)",
                             labels={"Peak RPE": "Workout Intensity (Peak RPE)"})
            # Locks chart vertical limits to standard lifting scales
            fig_rpe.update_yaxes(range=[5, 10.5]) 
            st.plotly_chart(fig_rpe, use_container_width=True)
            
            with st.expander("📋 View Extracted RPE Records Data Table"):
                st.dataframe(rpe_df, use_container_width=True)
        else:
            st.info("💡 Tip: To see the RPE chart, make sure to type `@8` or `RPE 9` into your Hevy set notes when logging your workouts!")

        # 5. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength & Endurance Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Analyzing live training load and RPE parameters..."):
                    
                    # Combine activity metrics and extracted subjective RPE data for the AI context
                    activity_summary = df[['Clean_Date', type_col, load_col]].dropna().to_string(index=False)
                    rpe_summary = pd.DataFrame(rpe_records).to_string(index=False) if rpe_records else "No explicit RPE notes tagged yet."
                    
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an elite sports scientist analyzing subjective muscular RPE fatigue and objective TRIMP metrics."},
                            {"role": "user", "content": f"Review these two training data blocks.\n\n1. OBJECTIVE LOAD:\n{activity_summary}\n\n2. SUBJECTIVE RPE EFFORT:\n{rpe_summary}\n\nEvaluate if their perceived exertion matches their heart rate data. Tell them if they are hitting true failure safely or over-fatiguing their central nervous system, and suggest volume targets for next week:"}
                        ]
                    )
                    st.write(response.choices[0].message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
                
    except Exception as e:
        st.error(f"Processing Error: {e}")
else:
    st.info("🔄 Syncing automated data stream... Check your app credentials if this takes too long.")
