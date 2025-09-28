import streamlit as st
import pandas as pd
import json
import re
import datetime

st.title("Extract and Filter plateText with Scan Time")

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
        # Read CSV without header
        df = pd.read_csv(uploaded_file, header=None, dtype=str)
        st.write("CSV preview:")
        st.write(df.head())

        json_col = df.columns[-1]
        timestamp_col = df.columns[0]

        def extract_and_clean_plate(json_str):
            try:
                data = json.loads(json_str)
                plate = data.get("licensePlateResult", {}).get("plateText", "")
                cleaned_plate = re.sub(r'[\s-]', '', plate)
                return cleaned_plate
            except Exception:
                return None

        # Extract plateText and scan time
        df['cleaned_plateText'] = df[json_col].apply(extract_and_clean_plate)
        df['scan_time'] = df[timestamp_col].apply(timestamp_to_datetime)

        # Extract just the date (YYYY-MM-DD)
        df['scan_date'] = df['scan_time'].str.slice(0, 10)

        # Filter out invalid entries
        filtered_df = df.dropna(subset=['cleaned_plateText', 'scan_time'])
        filtered_df = filtered_df[filtered_df['cleaned_plateText'] != ""]

        # Display date filter dropdown
        available_dates = sorted(filtered_df['scan_date'].unique(), reverse=True)
        selected_date = st.selectbox("Select a date to filter entries:", ["All Dates"] + available_dates)

        if selected_date != "All Dates":
            filtered_df = filtered_df[filtered_df['scan_date'] == selected_date]

        if not filtered_df.empty:
            st.write(f"Showing entries for: {selected_date}")
# Let user click and highlight a plate
st.write("### Plate Entries")
selected_plate = st.session_state.get("selected_plate", None)

for idx, row in filtered_df.iterrows():
    plate = row['cleaned_plateText']
    time = row['scan_time']
    button_key = f"select_{idx}"

    if st.button(f"{plate} @ {time}", key=button_key):
        st.session_state.selected_plate = plate

    # Highlight selected
    if selected_plate == plate:
        st.markdown(f"✅ **Selected:** `{plate}` (scanned at {time})")

            csv_output = filtered_df[['scan_time', 'cleaned_plateText']].to_csv(index=False, header=["scan_time", "plateText"])
            st.download_button(
                label="Download filtered plateText CSV",
                data=csv_output,
                file_name='filtered_plateText.csv',
                mime='text/csv'
            )
        else:
            st.warning("No entries found for the selected date.")

    except Exception as e:
        st.error(f"Error processing file: {e}")

