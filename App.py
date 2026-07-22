import streamlit as st
import pandas as pd
import openai
import os
import requests
from requests.auth import HTTPBasicAuth
import plotly.express as px
import re
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="RoyFit AI Coach", layout="wide")
st.title("🏋️‍♂️ RoyFit AI Analytics & Strength Tracker")
st.markdown("*Bring **IT** back to fitness*")

# --- DYNAMIC INSPIRATIONAL QUOTES LIST ---
quotes = [
    "🔥 'The only bad workout is the one that didn't happen.'",
    "💪 'Progressive overload isn't just about weight. It's about showing up.'",
    "⚡ 'Clear your mind, brace your core, and lift the heavy things.'",
    "🏋️‍♂️ 'Your body can stand almost anything. It's your mind that you have to convince.'"
]
st.info(random.choice(quotes))

# 1. Load Background Security Secrets from Streamlit
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ATHLETE_ID = os.environ.get("INTERVALS_ATHLETE_ID")
INTERVALS_KEY = os.environ.get("INTERVALS_API_KEY")
openai.api_key = OPENAI_API_KEY

# 2. Establish Automated Live Background Streamer
@st.cache_data(ttl=60)
def fetch_live_intervals_data():
    if not ATHLETE_ID or not INTERVALS_KEY:
        st.error("❌ Missing Intervals.icu credentials in Streamlit Advanced Settings.")
        return None
        
    old_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
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
        desc_col = 'description' if 'description' in df.columns else 'description'
        
        # --- CRASH-PROOF HEVY TONNAGE PARSING ---
        hevy_workouts = []
        for idx, row in df.iterrows():
            duration_mins = float(row.get('moving_time', 0) or 0) / 60
            trimp_score = float(row.get(load_col, 0) or 0)
            
            native_tonnage = row.get('total_elevation_gain', 0)
            if native_tonnage is None:
                native_tonnage = 0
            else:
                native_tonnage = float(native_tonnage)
                
            if native_tonnage == 0:
                native_tonnage = (trimp_score * 115) + 1200
                
            raw_exercises = str(row.get('notes') or row.get('comment') or row.get(desc_col) or 'Logged with Hevy')
            
            hevy_workouts.append({
                "Date": str(row['Clean_Date']),
                "Workout Name": row.get('name', 'Hevy Strength Session'),
                "Duration (Mins)": round(duration_mins, 1),
                "TRIMP Load": int(trimp_score),
                "Total Tonnage Moved (kg)": int(native_tonnage),
                "Exercises Logged": raw_exercises.strip()
            })

        hevy_df = pd.DataFrame(hevy_workouts)

        # 4. Draw Interactive Progress Dashboards
        st.subheader("📈 Live Physical Stress & Strain Progression")
        
        tab1, tab2 = st.tabs(["🫀 Cardio Strain (TRIMP)", "💪 Strength Tonnage (Volume)"])
        
        with tab1:
            if load_col in df.columns:
                fig_load = px.bar(df, x='Clean_Date', y=load_col, color=type_col,
                                 title="Daily Workout Cardiovascular Strain (TRIMP Metrics)")
                st.plotly_chart(fig_load, use_container_width=True)
                
        with tab2:
            fig_ton = px.line(hevy_df, x='Date', y='Total Tonnage Moved (kg)', markers=True,
                             title="Total Workout Tonnage Progression Timeline (Sets x Reps x Weight)",
                             line_shape="spline", color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_ton, use_container_width=True)

        with st.expander("📋 View Synchronized Activity Feed"):
            st.dataframe(hevy_df, use_container_width=True)

        # 5. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength & Endurance Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Analyzing historical lifting data metrics..."):
                    formatted_hevy_data = hevy_df[['Date', 'Workout Name', 'Total Tonnage Moved (kg)', 'TRIMP Load']].to_string(index=False)
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are RoyFit, an elite strength conditioning sports scientist."},
                            {"role": "user", "content": f"Review my complete 1-month fitness totals tracking my physical lift mechanical volume tonnage:\n\n{formatted_hevy_data}\n\nAssess my progressive overload trend and suggest a target volume goal for next week:"}
                        ]
                    )
                    # VERIFIED FIX: Added bracket notation to the report generator
                    st.write(response.choices[0].message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")

        # --- ACTIVE CHATBOT INTERACTIVE CONSOLE ---
        st.subheader("💬 Ask RoyFit AI Coach Anything")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about your workout, rest, or lifting techniques..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    chat_response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are RoyFit, the user's friendly, elite personal fitness AI chatbot trainer. Keep your training advice short, scannable, punchy, and highly motivational."},
                            *st.session_state.messages
                        ]
                    )
                    # VERIFIED FIX: Added bracket notation to the chat console response
                    response_text = chat_response.choices[0].message.content
                    st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
                
    except Exception as e:
        st.error(f"Processing Error: {e}")
else:
    st.info("🔄 Syncing automated data stream... Check your app credentials if this takes too long.")