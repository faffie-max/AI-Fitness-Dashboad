import streamlit as st
import pandas as pd
import openai
import os
import plotly.express as px

# 1. Page Configuration for Mobile Layout
st.set_page_config(page_title="AI Strength Dashboard", layout="wide")
st.title("🏋️‍♂️ Personal AI Strength Analytics")

# 2. Secure API Credentials (Loaded from hosting platform variables)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 3. Sidebar File Uploader
st.sidebar.header("Data Import Pipeline")
hevy_file = st.sidebar.file_uploader("Upload workout_data_hevy.csv", type="csv")

if hevy_file and OPENAI_API_KEY:
    try:
        # Load and parse Hevy CSV
        df = pd.read_csv(hevy_file)
        
        # Standardize dates
        df['date'] = pd.to_datetime(df['start_time']).dt.date
        
        # Calculate mechanical volume: Sets x Reps x Weight
        # Adjust column names if your Hevy export uses slightly different casing
        df['set_volume'] = df['reps'] * df['weight']
        daily_volume = df.groupby('date')['set_volume'].sum().reset_index()
        daily_volume.columns = ['Date', 'Total Volume (lbs/kg)']
        
        # 4. Display Progression Chart
        st.subheader("📈 Mechanical Progressive Overload Trend")
        fig = px.line(daily_volume, x='Date', y='Total Volume (lbs/kg)', markers=True,
                     title="Total Volume Progression (June 29 - July 17)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Display raw structured data frame
        with st.expander("View Cleaned Data Table"):
            st.dataframe(daily_volume, use_container_width=True)
            
        # 5. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength Coach Insights")
        if st.button("Generate AI Training Load Report"):
            with st.spinner("Analyzing volume progression and fatigue markers..."):
                # Convert the data frame into a clean string layout for the AI
                dataset_string = daily_volume.to_string(index=False)
                
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an elite sports scientist and strength conditioning coach."},
                        {"role": "user", "content": f"Analyze this 3-week block of weightlifting volume data. Assess if progressive overload is occurring effectively across these 9 sessions, and provide structured training feedback:\n{dataset_string}"}
                    ]
                )
                st.write(response.choices.message.content)
                
    except Exception as e:
        st.error(f"Error parsing spreadsheet layout: {e}. Check your CSV column headers.")
else:
    st.info("👈 Please use the sidebar to upload your Hevy CSV file.")
