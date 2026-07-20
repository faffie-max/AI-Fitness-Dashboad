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
        # Load the CSV file cleanly
        df = pd.read_csv(hevy_file)
        
        # Display the column dropdown troubleshooting checklist
        with st.expander("🔍 Inspect Data Headers"):
            st.write("File Columns Detected:", list(df.columns))
            st.dataframe(df.head(5))

        # Dynamically map the columns by case-insensitive name matching
        date_col = next((c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'created' in c.lower()), None)
        weight_col = next((c for c in df.columns if 'weight' in c.lower()), None)
        reps_col = next((c for c in df.columns if 'reps' in c.lower()), None)
        exercise_col = next((c for c in df.columns if 'exercise' in c.lower() or 'title' in c.lower()), None)

        if date_col and weight_col and reps_col:
            # Clean formats
            df['clean_date'] = pd.to_datetime(df[date_col]).dt.date
            df['volume'] = pd.to_numeric(df[weight_col], errors='coerce').fillna(0) * pd.to_numeric(df[reps_col], errors='coerce').fillna(0)
            
            # Group rows cleanly by date column
            daily_summary = df.groupby('clean_date')['volume'].sum().reset_index()
            daily_summary.columns = ['Date', 'Total Volume Calculated']
            daily_summary = daily_summary.sort_values(by='Date')

            # Render the Line Chart
            st.subheader("📈 Mechanical Progressive Overload Trend")
            fig = px.line(daily_summary, x='Date', y='Total Volume Calculated', markers=True,
                         title="Workout Volume Timeline Progression")
            fig.update_layout(xaxis_type='category')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show Raw Summary
            st.dataframe(daily_summary, use_container_width=True)
        else:
            st.warning("⚠️ Data loaded but target columns weren't automatically matched.")

        # --- AI Engine ---
        st.subheader("🤖 AI Strength Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Analyzing volume progression parameters..."):
                    # Send up clean historical table layout string straight to GPT-4o
                    dataset_string = daily_summary.to_string(index=False)
                    
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an elite sports scientist and strength conditioning coach."},
                            {"role": "user", "content": f"Analyze this user 3-week gym workout history volume totals. Check if their progression indicates proper progressive overload, and provide clear coaching feedback:\n{dataset_string}"}
                        ]
                    )
                    st.write(response.choices[0].message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
                
    except Exception as e:
        st.error(f"Error reading layout: {e}")
else:
    st.info("👈 Use the sidebar to upload your Hevy CSV file.")
