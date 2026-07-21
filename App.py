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
@st.cache_data(ttl=60) # Fast 1-minute caching
def fetch_live_intervals_data():
    if not ATHLETE_ID or not INTERVALS_KEY:
        st.error("❌ Missing Intervals.icu credentials in Streamlit Advanced Settings.")
        return None
        
    old_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d') # Rolling 5-week history
    now_date = datetime.now().strftime('%Y-%m-%d')
    
    url = f"https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/activities"
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
        
        # --- NATIVE HEVY TEXT LOGGER MATRIX ---
        hevy_workouts = []
        for idx, row in df.iterrows():
            activity_type = str(row.get(type_col, '')).lower()
            activity_name = str(row.get('name', '')).lower()
            
            # Identify any fitness activity that matches your weightlifting profiles
            if any(w in activity_type or w in activity_name for w in ['lift', 'weight', 'strength', 'gym', 'hevy', 'workout']):
                duration_mins = row.get('moving_time', 0) / 60
                calories_burned = row.get('calories', 0)
                trimp_score = row.get(load_col, 0)
                
                # Dynamic fallback strategy to scan every possible notes folder for your raw texts
                raw_exercises = row.get('notes', row.get('comment', row.get('description', 'No details available.')))
                
                hevy_workouts.append({
                    "Date": str(row['Clean_Date']),
                    "Workout": row.get('name', 'Strength Session'),
                    "Duration": f"{round(duration_mins, 1)}m",
                    "TRIMP": trimp_score,
                    "Exercises": str(raw_exercises).strip()
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
            st.dataframe(hevy_df, use_container_width=True)
        else:
            st.info("💡 Tip: Today's metrics loaded! Your Hevy timeline will display as soon as your latest workout completes syncing through HealthFit.")

        # 5. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength & Endurance Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Analyzing historical lifting data text files..."):
                    
                    # Convert your workout data block directly into a massive plain text layout
                    if hevy_workouts:
                        formatted_hevy_data = ""
                        for hw in hevy_workouts:
                            formatted_hevy_data += f"Date: {hw['Date']} | Name: {hw['Workout']} | TRIMP: {hw['TRIMP']}\n Lifts logged:\n{hw['Exercises']}\n-------------------\n"
                    else:
                        formatted_hevy_data = "No explicit workout metadata logs isolated."
                    
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are RoyFit, an elite strength conditioning scientist. You read gym tracking descriptions (like 3x10 Box Squats @ 80kg) to critique muscular progressive overload limits across a month."},
                            {"role": "user", "content": f"Review this exercise training log payload containing my literal weightlifting logs from the past month:\n\n{formatted_hevy_data}\n\nTask: Explicitly look at the text listed under 'Lifts logged:'. Identify specific exercise names (like Box Squats, Lat Pull Downs, etc.), check their historical weight progression over the 4-week window, and provide a clear, actionable analysis of my progressive overload trend."}
                        ]
                    )
                    st.write(response.choices[0].message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
                
    except Exception as e:
        st.error(f"Processing Error: {e}")
else:
    st.info("🔄 Syncing automated data stream... Check your app credentials if this takes too long.")
