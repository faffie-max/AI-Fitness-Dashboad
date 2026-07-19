import streamlit as st
import pandas as pd
import openai
import os
import plotly.express as px

st.set_page_config(page_title="AI Strength Dashboard", layout="wide")
st.title("🏋️‍♂️ Personal AI Strength Analytics")

# Load Open AI Security Settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

st.sidebar.header("Data Import Pipeline")
hevy_file = st.sidebar.file_uploader("Upload your Hevy CSV", type="csv")

if hevy_file:
    st.success("🎯 File successfully uploaded to server memory. Beginning parsing...")
    
    # --- SMART DELIMITER LOOP FIX ---
    # Tests commas, semicolons, and tabs to prevent silent formatting crashes
    df = None
    for separator in [',', ';', '\t']:
        try:
            hevy_file.seek(0) # Reset file reading pointer
            test_df = pd.read_csv(hevy_file, sep=separator)
            if len(test_df.columns) > 1: # If it split nicely into multiple columns, it worked!
                df = test_df
                st.info(f"⚙️ Successfully read file structure using character separator: '{separator}'")
                break
        except Exception:
            continue

    # Final backup check if file formatting is completely warped
    if df is None:
        try:
            hevy_file.seek(0)
            df = pd.read_csv(hevy_file, sep=None, engine='python')
            st.info("⚙️ Used fallback engine to read formatting layout.")
        except Exception as csv_error:
            st.error(f"❌ Structural crash while opening spreadsheet: {csv_error}")

    # --- PROCESS UNIFIED DATA ---
    if df is not None:
        try:
            # Render a fallback data inspector tab so you can visually verify the content
            with st.expander("🔍 RAW DATAFRAME INSPECTOR (Troubleshooting)", expanded=True):
                st.write("Detected Columns:", list(df.columns))
                st.dataframe(df.head(10), use_container_width=True)

            # Auto-detect target data columns by looking for matching characters
            date_col = next((c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()), None)
            weight_col = next((c for c in df.columns if 'weight' in c.lower()), None)
            reps_col = next((c for c in df.columns if 'reps' in c.lower()), None)
            exercise_col = next((c for c in df.columns if 'exercise' in c.lower() or 'title' in c.lower()), None)

            if date_col and weight_col and reps_col:
                # Format cleaning parameters
                df['clean_date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
                df['clean_weight'] = pd.to_numeric(df[weight_col], errors='coerce').fillna(0)
                df['clean_reps'] = pd.to_numeric(df[reps_col], errors='coerce').fillna(0)
                
                # Math calculation for absolute mechanical load
                df['set_volume'] = df['clean_weight'] * df['clean_reps']
                daily_volume = df.groupby('clean_date')['set_volume'].sum().reset_index()
                daily_volume.columns = ['Date', 'Total Volume Calculated']
                
                # Render interactive progress dashboard chart
                st.subheader("📈 Mechanical Progressive Overload Trend")
                fig = px.line(daily_summary, x='Date', y='Total Volume Calculated', markers=True)
                st.plotly_chart(fig, use_container_width=True)
                
                # Render operational AI analysis text area blocks
                st.subheader("🤖 AI Strength Coach Insights")
                if OPENAI_API_KEY:
                    if st.button("Generate AI Training Load Report"):
                        with st.spinner("Analyzing parameters..."):
                            data_snippet = df[[date_col, exercise_col, weight_col, reps_col]].dropna().head(30).to_string(index=False)
                            response = openai.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "You are an elite strength conditioning coach."},
                                    {"role": "user", "content": f"Analyze this workout data snippet for progressive overload patterns:\n{data_snippet}"}
                                ]
                            )
                            st.write(response.choices.message.content)
                else:
                    st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
            else:
                st.warning("⚠️ Data structure loaded, but standard workout columns (date, weight, reps) are missing.")

        except Exception as pipeline_error:
            st.error(f"❌ Error during chart compilation logic: {pipeline_error}")
else:
    st.info("👈 Open the sidebar menu and upload your `workout_data_hevy.csv` file to begin.")

                
                
