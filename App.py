import streamlit as st
import pandas as pd
import openai
import os
import requests
from requests.auth import HTTPBasicAuth
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="RoyFit AI Coach", layout="wide")
st.title("🏋️‍♂️ RoyFit AI Analytics & Hevy Lift Tracker")
st.markdown("*Bring **IT** back to fitness*")

# 1. Load Background Security Secrets from Streamlit
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ATHLETE_ID = os.environ.get("INTERVALS_ATHLETE_ID")
INTERVALS_KEY = os.environ.get("INTERVALS_API_KEY")
openai.api_key = OPENAI_API_KEY

# 2. Establish Automated Live Background Streamer
@st.cache_data(ttl=120) # Caches data for 2 minutes
def fetch_live_intervals_data():
    if not ATHLETE_ID or not INTERVALS_KEY:
        st.error("❌ Missing Intervals.icu credentials in Streamlit Advanced Settings.")
        return None
        
    old_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d') # Grabs past 5 weeks of history
    now_date = datetime.now().strftime('%Y-%m-%d')
    
    url = f"https://intervals.org{ATHLETE_ID}/activities"
    params = {"oldest": old_date, "newest": now_date}
    
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
        
        # --- NATIVE HEVY DATA EXTRACTION ---
        # Pulls clean weight metrics passed down from Hevy fields instead of text notes
        hevy_workouts = []
        for idx, row in df.iterrows():
            if 'WeightLifting' in str(row.get(type_col, '')) or 'Strength' in str(row.get(type_col, '')):
                # Intervals.icu extracts total mechanical work into 'total_elevation_gain' or 'moving_time' blocks for strength files
                duration_mins = row.get('moving_time', 0) / 60
                calories_burned = row.get('calories', 0)
                trimp_score = row.get(load_col, 0)
                
                hevy_workouts.append({
                    "Date": row['Clean_Date'],
                    "Workout Name": row.get('name', 'Hevy Strength Session'),
                    "Duration (Mins)": round(duration_mins, 1),
                    "Calories": calories_burned,
                    "Cardio TRIMP": trimp_score
                })

        # 4. Draw Interactive Progress Dashboards
        st.subheader("📈 Live Physical Stress & Strain Progression")
        
        # Chart A: Training Stress Over Time (TRIMP)
        if load_col in df.columns:
            fig_load = px.bar(df, x='Clean_Date', y=load_col, color=type_col if type_col in df.columns else None,
                             title="Daily Workout Cardiovascular Strain (TRIMP Metrics)",
                             labels={load_col: "Training Load Score (TRIMP)"})
            st.plotly_chart(fig_load, use_container_width=True)

        # Chart B: Hevy Strength Training Timeline
        if hevy_workouts:
            hevy_df = pd.DataFrame(hevy_workouts)
            st.subheader("💪 Hevy Strength Training Analytics (Over 1 Month)")
            
            fig_hevy = px.line(hevy_df, x='Date', y='Duration (Mins)', markers=True,
                             title="Logged Weightlifting Duration Progression (Mins)",
                             labels={"Duration (Mins)": "Time Lifted (Minutes)"})
            st.plotly_chart(fig_hevy, use_container_width=True)
            
            with st.expander("📋 View Clean Synchronized Hevy Records"):
                st.dataframe(hevy_df, use_container_width=True)
        else:
            st.info("💡 Tip: Today's metrics loaded! Your Hevy timeline will display as soon as your latest workout completes syncing through HealthFit.")

        # 5. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength & Endurance Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Analyzing historical logs..."):
                    
                    # Package clean database strings for OpenAI
                    raw_activity_summary = df[['Clean_Date', type_col, load_col]].dropna().to_string(index=False)
                    hevy_summary = pd.DataFrame(hevy_workouts).to_string(index=False) if hevy_workouts else "No strength metadata isolated."
                    
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an elite sports scientist analyzing athletic recovery metrics and training load stress."},
                            {"role": "user", "content": f"Review this 1-month fitness history log block containing clean synchronized workout logs.\n\n1. CARDIAC STRAIN (TRIMP):\n{raw_activity_summary}\n\n2. HEVY LOG WORKOUT TIMELINE:\n{hevy_summary}\n\nCompare the results across this month. Assess if their lifting volume and durations indicate stable progressive overload, cross-reference against their cardiovascular TRIMP load spikes to ensure safe fatigue management, and provide structured coaching feedback:"}
                        ]
                    )
                    st.write(response.choices[0].message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
                
    except Exception as e:
        st.error(f"Processing Error: {e}")
else:
    st.info("🔄 Syncing automated data stream... Check your app credentials if this takes too long.")

