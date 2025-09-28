import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime

st.title("Extract and Clean plateText from CSV JSON Column")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    try:
        # Read CSV without header (since your data looks headerless)
        df = pd.read_csv(uploaded_file, header=None, dtype=str)
        st.write("CSV preview:")
        st.write(df.head())

        json_col = df.columns[-1]

        def extract_and_clean_plate(json_str):
            try:
                data = json.loads(json_str)
                plate = data.get("licensePlateResult", {}).get("plateText", "")
                cleaned_plate = re.sub(r'[\s-]', '', plate)
                return cleaned_plate
            except Exception:
                return None

        def extract_timestamp(ts):
            try:
                # Assume timestamp is in milliseconds since epoch
                return datetime.fromtimestamp(int(ts) / 1000)
            except Exception:
                return None

        # Extract scan time and cleaned plate text
        df['scan_time'] = df[0].apply(extract_timestamp)
        df['cleaned_plateText'] = df[json_col].apply(extract_and_clean_plate)

        # Drop rows with missing scan time or plate
        df = df.dropna(subset=['scan_time', 'cleaned_plateText'])

        # Extract date options
        df['scan_date'] = df['scan_time'].dt.date
        available_dates = sorted(df['scan_date'].unique())

        selected_date = st.selectbox("Select a date to filter by", options=available_dates)

        # Filter data by selected date
        filtered_df = df[df['scan_date'] == selected_date]

        # Button to reset and view all
        if st.button("Show all dates"):
            filtered_df = df

        # Track selected plate across interactions
        if "selected_plate" not in st.session_state:
            st.session_state.selected_plate = None

        st.write("### Plate Entries")
        for idx, row in filtered_df.iterrows():
            plate = row['cleaned_plateText']
            time = row['scan_time']
            button_key = f"select_{idx}"

            if st.button(f"{plate} @ {time}", key=button_key):
                st.session_state.selected_plate = plate

            # Highlight selected
            if st.session_state.selected_plate == plate:
                st.markdown(f"✅ **Selected:** `{plate}` (scanned at {time})")

        # Export filtered data
        if not filtered_df.empty:
            export = filtered_df[['cleaned_plateText']]
            export_csv = export.to_csv(index=False, header=["plateText"])
            st.download_button(
                label="Download plateText CSV",
                data=export_csv,
                file_name='filtered_plateText.csv',
                mime='text/csv'
            )
        else:
            st.warning("No data available for the selected date.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
