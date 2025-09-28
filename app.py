import streamlit as st
import pandas as pd
import json
import re
import datetime

st.title("Extract and Clean plateText from CSV JSON Column with Scan Time")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

def timestamp_to_datetime(ms_timestamp):
    try:
        ts_seconds = int(ms_timestamp) / 1000
        dt = datetime.datetime.utcfromtimestamp(ts_seconds)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return None

if uploaded_file:
    try:
        # Read CSV without header (your data looks headerless)
        df = pd.read_csv(uploaded_file, header=None, dtype=str)
        st.write("CSV preview:")
        st.write(df.head())

        json_col = df.columns[-1]  # JSON data is last column
        timestamp_col = df.columns[0]  # Timestamp is first column

        def extract_and_clean_plate(json_str):
            try:
                data = json.loads(json_str)
                plate = data.get("licensePlateResult", {}).get("plateText", "")
                cleaned_plate = re.sub(r'[\s-]', '', plate)
                return cleaned_plate
            except Exception:
                return None

        # Extract plateText
        df['cleaned_plateText'] = df[json_col].apply(extract_and_clean_plate)

        # Convert timestamp to readable date/time
        df['scan_time'] = df[timestamp_col].apply(timestamp_to_datetime)

        # Filter rows with valid plateText
        filtered_df = df.dropna(subset=['cleaned_plateText'])
        filtered_df = filtered_df[filtered_df['cleaned_plateText'] != ""]

        if not filtered_df.empty:
            st.write("Extracted scan times and cleaned plateText values:")
            st.write(filtered_df[['scan_time', 'cleaned_plateText']])

            csv_output = filtered_df[['scan_time', 'cleaned_plateText']].to_csv(index=False, header=["scan_time", "plateText"])
            st.download_button(
                label="Download scan time + plateText CSV",
                data=csv_output,
                file_name='scanTime_plateText.csv',
                mime='text/csv'
            )
        else:
            st.error("No valid plateText values found.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
