import streamlit as st
import pandas as pd
import json
import re
import datetime
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

st.title("Extract and Match plateText with Scan Time + XML Data")

uploaded_csv = st.file_uploader("Upload your CSV file", type=["csv"])
uploaded_xml = st.file_uploader("Upload your XML file (optional)", type=["xml"])

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
        cleaned_plate = re.sub(r'[\s-]', '', plate).upper()
        return cleaned_plate
    except Exception:
        return None

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    entries = []
    for elem in root.findall(".//G_C6"):
        c6 = elem.findtext("C6")
        c9_full = elem.findtext("C9")
        c12 = elem.findtext("C12")
        if c6 and c9_full and c12:
            cleaned_c12 = re.sub(r'[\s-]', '', c12).upper()
            c9_short = c9_full.split(',')[0].strip()  # Get only the part before the comma
            entries.append({
                "plateText": cleaned_c12,
                "C6": c6,
                "C9": c9_short
            })
    return pd.DataFrame(entries)

def find_close_matches(plate, xml_df, threshold=0.85):
    for _, row in xml_df.iterrows():
        score = SequenceMatcher(None, plate, row["plateText"]).ratio()
        if score >= threshold and plate != row["plateText"]:
            return row["plateText"], row["C6"], row["C9"], score
    return None, None, None, 0

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv, header=None, dtype=str)
        json_col = df.columns[-1]
        timestamp_col = df.columns[0]

        # Extract
        df['cleaned_plateText'] = df[json_col].apply(extract_and_clean_plate)
        df['scan_time'] = df[timestamp_col].apply(timestamp_to_datetime)
        df['scan_date'] = df['scan_time'].str.slice(0, 10)

        filtered_df = df.dropna(subset=['cleaned_plateText', 'scan_time'])
        filtered_df = filtered_df[filtered_df['cleaned_plateText'] != ""]

        # Optional XML parsing
        xml_df = pd.DataFrame()
        if uploaded_xml:
            xml_df = parse_xml(uploaded_xml)

        # Date filtering
        available_dates = sorted(filtered_df['scan_date'].unique(), reverse=True)
        selected_date = st.selectbox("Select a date to filter entries:", ["All Dates"] + available_dates)

        if selected_date != "All Dates":
            filtered_df = filtered_df[filtered_df['scan_date'] == selected_date]

        # Display
        if not filtered_df.empty:
            st.write(f"Showing entries for: {selected_date}")

            results = []

            for _, row in filtered_df.iterrows():
                plate = row['cleaned_plateText']
                match = xml_df[xml_df['plateText'] == plate] if not xml_df.empty else pd.DataFrame()

                if not match.empty:
                    matched_row = match.iloc[0]
                    results.append({
                        "scan_time": row['scan_time'],
                        "plateText": plate,
                        "C6": matched_row["C6"],
                        "C9": matched_row["C9"],
                        "note": "Exact Match"
                    })
                elif not xml_df.empty:
                    # Typo detection (1-character diff / 85% similarity)
                    close_plate, c6, c9, score = find_close_matches(plate, xml_df)
                    if close_plate:
                        results.append({
                            "scan_time": row['scan_time'],
                            "plateText": plate,
                            "C6": c6,
                            "C9": c9,
                            "note": f"⚠ Possible Typo (Close to: {close_plate})"
                        })
                    else:
                        results.append({
                            "scan_time": row['scan_time'],
                            "plateText": plate,
                            "C6": "",
                            "C9": "",
                            "note": "No Match"
                        })
                else:
                    results.append({
                        "scan_time": row['scan_time'],
                        "plateText": plate,
                        "C6": "",
                        "C9": "",
                        "note": "No XML Loaded"
                    })

                result_df = pd.DataFrame(results)
                # Reorder columns: keep scan_time and note where they are, rearrange the middle ones
                result_df = result_df[["scan_time", "C6", "C9", "plateText", "note"]]
                st.dataframe(result_df)


            csv_output = result_df.to_csv(index=False)
            st.download_button(
                label="Download Results CSV",
                data=csv_output,
                file_name='matched_plateText.csv',
                mime='text/csv'
            )
        else:
            st.warning("No entries found for the selected date.")

    except Exception as e:
        st.error(f"Error processing file: {e}")


