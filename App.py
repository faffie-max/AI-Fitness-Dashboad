import streamlit as st
import pandas as pd
import openai
import os
import plotly.express as px

st.set_page_config(page_title="AI Strength Dashboard", layout="wide")
st.title("🏋️‍♂️ Personal AI Strength Analytics")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

st.sidebar.header("Data Import Pipeline")
hevy_file = st.sidebar.file_uploader("Upload your Hevy CSV", type="csv")

if hevy_file and OPENAI_API_KEY:
    try:
        # Load the CSV
        df = pd.read_csv(hevy_file)
        
        # 1. Debugging View: Let's see what columns actually exist in your file
        with st.expander("🔍 Inspect File Columns (Troubleshooting)"):
            st.write("Your file columns are:", list(df.columns))
            st.dataframe(df.head(5))

        # 2. Automatically find and standardize the Date Column
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        if date_col:
            df['clean_date'] = pd.to_datetime(df[date_col]).dt.date
        else:
            df['clean_date'] = pd.Timestamp.now().date()

        # 3. Handle the Weight and Reps volume calculation dynamically
        # This checks for casing variations like 'Weight', 'weight', 'Reps', 'reps'
        weight_col = next((c for c in df.columns if 'weight' in c.lower()), None)
        reps_col = next((c for c in df.columns if 'reps' in c.lower()), None)
        exercise_col = next((c for c in df.columns if 'exercise' in c.lower() or 'title' in c.lower()), None)

        if weight_col and reps_col:
            df['calculated_volume'] = pd.to_numeric(df[weight_col], errors='coerce') * pd.to_numeric(df[reps_col], errors='coerce')
            daily_summary = df.groupby('clean_date')['calculated_volume'].sum().reset_index()
            daily_summary.columns = ['Date', 'Total Volume Calculated']
            
            # Display interactive timeline graph
            st.subheader("📈 Mechanical Progressive Overload Trend")
            fig = px.line(daily_summary, x='Date', y='Total Volume Calculated', markers=True,
                         title="Workout Volume Timeline Progression")
            st.plotly_chart(fig, use_container_width=True)
            
            # List logged workouts for user confirmation
            if exercise_col:
                st.subheader("📋 Logged Workout Sessions")
                unique_exercises = df[exercise_col].dropna().unique()
                st.write(f"Detected **{len(unique_exercises)}** distinct movements over your 3-week block.")
        else:
            st.warning("⚠️ Could not locate weight or rep columns. Check the troubleshooting dropdown above.")
            daily_summary = df.head(20) # Fallback to pass raw text to AI if columns don't match

        # 4. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength Coach Insights")
        if st.button("Generate AI Training Load Report"):
            with st.spinner("Analyzing your volume progression and training layout..."):
                # Pass a compressed text snippet to avoid token errors
                dataset_string = df[[date_col, exercise_col, weight_col, reps_col]].dropna().head(40).to_string(index=False)
                
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an elite sports scientist and strength conditioning coach."},
                        {"role": "user", "content": f"Analyze this user gym workout history spanning June 29 to July 17. Evaluate their exercise selection, check if their weight jumps indicate proper progressive overload, and provide actionable coaching advice:\n{dataset_string}"}
                    ]
                )
                st.write(response.choices.message.content)
                
    except Exception as e:
        st.error(f"Error parsing spreadsheet setup: {e}")
else:
    st.info("👈 Use the sidebar to upload your Hevy CSV file.")

                
                
