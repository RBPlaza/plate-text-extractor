import streamlit as st
import pandas as pd
import json
import re
import datetime
import xml.etree.ElementTree as ET

st.title("Extract and Filter plateText with Scan Time + Optional XML Info")

uploaded_csv = st.file_uploader("Upload your CSV file", type=["csv"])
uploaded_xml = st.file_uploader("Upload optional XML file (Oracle format)", type=["xml"])

def timestamp_to_datetime(ms_timestamp):
    try:
        ts_seconds = int(ms_timestamp) / 1000
        dt = datetime.datetime.utcfromtimestamp(ts_seconds)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return None

def extract_and_clean_plate(json_str):
    try:
        data = json.loads(json_str)
        plate = data.get("licensePlateResult", {}).get("plateText", "")
        cleaned_plate = re.sub(r'[\s-]', '', plate)
        return cleaned_plate
    except Exception:
        return None

# Parse the XML file and extract plate-related data
def parse_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        plate_map = {}

        for g_c6 in root.findall(".//G_C6"):
            plate = g_c6.findtext("C12", default="").strip().upper().replace(" ", "").replace("-", "")
            id_val = g_c6.findtext("C6", default="")
            name_val = g_c6.findtext("C9", default="")
            if plate:
                plate_map[plate] = {"ID": id_val, "Name": name_val}

        return plate_map
    except Exception as e:
        st.error(f"Error parsing XML: {e}")
        return {}

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv, header=None, dtype=str)
        st.write("CSV preview:")
        st.write(df.head())

        json_col = df.columns[-1]
        timestamp_col = df.columns[0]

        df['cleaned_plateText'] = df[json_col].apply(extract_and_clean_plate)
        df['scan_time'] = df[timestamp_col].apply(timestamp_to_datetime)
        df['scan_date'] = df['scan_time'].str.slice(0, 10)

        filtered_df = df.dropna(subset=['cleaned_plateText', 'scan_time'])
        filtered_df = filtered_df[filtered_df['cleaned_plateText'] != ""]

        # If XML is uploaded, enrich the data
        xml_data = {}
        if uploaded_xml:
            xml_data = parse_xml(uploaded_xml)
            filtered_df['XML_ID'] = filtered_df['cleaned_plateText'].map(lambda p: xml_data.get(p, {}).get("ID", ""))
            filtered_df['XML_Name'] = filtered_df['cleaned_plateText'].map(lambda p: xml_data.get(p, {}).get("Name", ""))

        available_dates = sorted(filtered_df['scan_date'].unique(), reverse=True)
        selected_date = st.selectbox("Select a date to filter entries:", ["All Dates"] + available_dates)

        if selected_date != "All Dates":
            filtered_df = filtered_df[filtered_df['scan_date'] == selected_date]

        if not filtered_df.empty:
            st.write(f"Showing entries for: {selected_date}")
            display_cols = ['scan_time', 'cleaned_plateText']
            if uploaded_xml:
                display_cols += ['XML_ID', 'XML_Name']
            st.write(filtered_df[display_cols])

            # Prepare CSV export
            export_cols = display_cols
            csv_output = filtered_df[export_cols].to_csv(index=False)
            st.download_button(
                label="Download filtered plateText CSV",
                data=csv_output,
                file_name='filtered_plateText_with_xml.csv',
                mime='text/csv'
            )
        else:
            st.warning("No entries found for the selected date.")
    except Exception as e:
        st.error(f"Error processing file: {e}")
