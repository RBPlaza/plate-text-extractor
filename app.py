import streamlit as st
import pandas as pd
import json
import re

st.title("Extract and Clean plateText from CSV JSON Column")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    try:
        # Read CSV without header (since your data looks headerless)
        df = pd.read_csv(uploaded_file, header=None, dtype=str)  # read all as strings to avoid issues
        st.write("CSV preview:")
        st.write(df.head())

        # The last column contains the JSON string
        json_col = df.columns[-1]

        def extract_and_clean_plate(json_str):
            try:
                data = json.loads(json_str)
                plate = data.get("licensePlateResult", {}).get("plateText", "")
                # Remove spaces and dashes
                cleaned_plate = re.sub(r'[\s-]', '', plate)
                return cleaned_plate
            except Exception as e:
                return None

        df['cleaned_plateText'] = df[json_col].apply(extract_and_clean_plate)

        # Filter out empty or None values
        plates = df['cleaned_plateText'].dropna()
        plates = plates[plates != ""]

        if not plates.empty:
            st.write("Extracted and cleaned plateText values:")
            st.write(plates)

            csv_output = plates.to_csv(index=False, header=["plateText"])
            st.download_button(
                label="Download plateText CSV",
                data=csv_output,
                file_name='cleaned_plateText.csv',
                mime='text/csv'
            )
        else:
            st.error("No valid plateText values found.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
