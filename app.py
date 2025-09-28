import streamlit as st
import pandas as pd

st.title("CSV PlateText Extractor")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if 'plateText' in df.columns:
        st.write("Extracted plateText values:")
        st.write(df['plateText'])
        
        # Prepare CSV for download
        csv = df['plateText'].to_csv(index=False)
        st.download_button(
            label="Download plateText CSV",
            data=csv,
            file_name='plateText.csv',
            mime='text/csv'
        )
    else:
        st.error("The CSV does not contain a 'plateText' column.")
