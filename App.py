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

if hevy_file:
    try:
        # Load the CSV
        df = pd.read_csv(hevy_file)
        
        # 1. Clean the Dates (Hevy uses 'created_at')
        if 'created_at' in df.columns:
            df['Date'] = pd.to_datetime(df['created_at']).dt.date
        elif 'start_time' in df.columns:
            df['Date'] = pd.to_datetime(df['start_time']).dt.date
        else:
            # Fallback if column names vary
            date_col = next((c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()), df.columns[0])
            df['Date'] = pd.to_datetime(df[date_col]).dt.date

        # 2. Find Weight and Reps Columns
        weight_col = next((c for c in df.columns if 'weight' in c.lower()), None)
        reps_col = next((c for c in df.columns if 'reps' in c.lower()), None)
        exercise_col = next((c for c in df.columns if 'exercise' in c.lower() or 'title' in c.lower()), None)

        if weight_col and reps_col:
            # Calculate total volume per set
            df['set_volume'] = pd.to_numeric(df[weight_col], errors='coerce').fillna(0) * pd.to_numeric(df[reps_col], errors='coerce').fillna(0)
            
            # Group by clean Date column
            daily_volume = df.groupby('Date')['set_volume'].sum().reset_index()
            daily_volume.columns = ['Date', 'Total Volume']
            daily_volume = daily_volume.sort_values(by='Date')
            
            # 3. Render the Line Chart
            st.subheader("📈 Mechanical Progressive Overload Trend")
            fig = px.line(daily_volume, x='Date', y='Total Volume', markers=True,
                         title="Workout Volume Timeline Progression")
            fig.update_layout(xaxis_type='category') # Forces clear calendar dates on the bottom axis
            st.plotly_chart(fig, use_container_width=True)
            
            # Show Raw Data Summary Table
            with st.expander("📊 View Cleaned Data Summary"):
                st.dataframe(daily_volume, use_container_width=True)
        else:
            st.warning("⚠️ Could not calculate volume. Ensure columns for weight and reps exist.")

        # 4. Generative AI Coaching Engine
        st.subheader("🤖 AI Strength Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Analyzing your volume progression and training layout..."):
                    # Pass a clean structured summary to the AI to prevent layout token crashes
                    dataset_string = df[['created_at', exercise_col, weight_col, reps_col]].dropna().head(40).to_string(index=False)
                    
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an elite sports scientist and strength conditioning coach."},
                            {"role": "user", "content": f"Analyze this user gym workout history spanning June 29 to July 17. Evaluate their exercise selection, check if their weight volume shows proper progressive overload, and provide actionable coaching advice:\n{dataset_string}"}
                        ]
                    )
                    st.write(response.choices[0].message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
                
    except Exception as e:
        st.error(f"Error parsing spreadsheet layout: {e}")
else:
    st.info("👈 Use the sidebar to upload your Hevy CSV file.")

                
