import streamlit as st
import pandas as pd
import openai
import os
import re

st.set_page_config(page_title="AI Strength Dashboard", layout="wide")
st.title("🏋️‍♂️ Personal AI Strength Analytics")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

st.sidebar.header("Data Import Pipeline")
hevy_file = st.sidebar.file_uploader("Upload your Hevy CSV", type="csv")

if hevy_file:
    try:
        # Read the file as raw lines to completely bypass data row layout errors
        bytes_data = hevy_file.getvalue()
        raw_text = bytes_data.decode("utf-8", errors="ignore")
        lines = raw_text.splitlines()
        
        # Display troubleshooting log onto screen
        with st.expander("🔍 Cleaned Text Rows Preview"):
            st.text("\n".join(lines[:6]))

        # --- TEXT CLEANING ENGINE ---
        parsed_data = []
        # Matches any format like "17 Jul 2026" or "29 Jun 2026"
        date_pattern = r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})"
        
        for line in lines:
            if "workout" not in line.lower() and "squat" not in line.lower() and "press" not in line.lower():
                continue
            
            # 1. Extract the text date cleanly
            date_match = re.search(date_pattern, line)
            workout_date = date_match.group(1) if date_match else None
            
            if not workout_date:
                continue
                
            # 2. Extract numbers using text splitting to isolate final weights and reps
            # Breaks up commas and quotation blocks cleanly
            row_items = re.findall(r"[-+]?\d*\.\d+|\d+", line)
            
            # Strip out calendar years and stray single digits to isolate lifting volume
            clean_metrics = [float(item) for item in row_items if item not in ["2026", "2025", "2024", "14", "15"]]
            
            if len(clean_metrics) >= 2:
                # In standard formats, the final two isolated numbers are Weight and Reps
                weight = clean_metrics[-2]
                reps = clean_metrics[-1]
                set_volume = weight * reps
                parsed_data.append({"Date": workout_date, "Volume": set_volume})

        # --- BUILD DATAFRAME TABLES ---
        if parsed_data:
            summary_df = pd.DataFrame(parsed_data)
            
            # Collapse total metrics by date strings cleanly
            daily_totals = summary_df.groupby("Date")["Volume"].sum().reset_index()
            daily_totals.columns = ['Workout Date', 'Calculated Total Volume']
            
            # Display a clean data layout table summary card directly onto your screen
            st.subheader("📋 Parsed Mechanical Training Volume Summary")
            st.dataframe(daily_totals, use_container_width=True)
        else:
            st.warning("⚠️ Processing completed, but weight or rep columns are incorrectly scaled.")

        # --- GENERATIVE AI COACHING ENGINE ---
        st.subheader("🤖 AI Strength Coach Insights")
        if st.button("Generate AI Training Load Report"):
            if OPENAI_API_KEY:
                with st.spinner("Decoding your workout volume metrics..."):
                    # Send up the top text logs directly to OpenAI - AI reads unformatted strings perfectly!
                    text_data_snippet = "\n".join(lines[:40])
                    
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an elite sports scientist and strength conditioning coach."},
                            {"role": "user", "content": f"Analyze this user gym workout text dataset block from June 29 to July 17. Extract the exercises, evaluate if their progression shows proper progressive overload across these 9 sessions, and provide actionable coaching advice:\n{text_data_snippet}"}
                        ]
                    )
                    st.write(response.choices.message.content)
            else:
                st.error("❌ OpenAI Developer Key is missing from Advanced settings.")
                
    except Exception as e:
        st.error(f"Processing Error: {e}")
else:
    st.info("👈 Open the sidebar menu and upload your `workout_data_hevy.csv` file to begin.")



                
