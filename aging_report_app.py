import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

st.set_page_config(page_title="📊 Aging Report Merger", layout="wide")
st.title("📊 Aging Report Merger (ZWL & USD Matching Sample Layout)")

# Upload files
usd_file = st.file_uploader("Upload USD Aging Report", type=["xlsx"])
zwg_file = st.file_uploader("Upload ZWG Aging Report", type=["xlsx"])
sample_file = st.file_uploader("Upload Sample Layout File", type=["xlsx"])

def clean_and_prepare(df):
    df = df.dropna(how="all")  # Remove fully empty rows
    df.columns = df.iloc[0]    # First row as header
    df = df[1:]
    df = df.fillna(0)
    df = df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x)  # Replace negatives
    return df

def create_output_file(zwg_df, usd_df):
    wb = Workbook()
    ws = wb.active
    ws.title = "Consolidated Aging"

    # Title
    ws.append(["ZWL AGING"])
    for r in dataframe_to_rows(zwg_df, index=False, header=True):
        ws.append(r)

    ws.append([])  # Empty row
    ws.append(["USD AGING"])
    for r in dataframe_to_rows(usd_df, index=False, header=True):
        ws.append(r)

    # Save to buffer
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

if usd_file and zwg_file and sample_file:
    # Read and clean data
    try:
        zwg_raw = pd.read_excel(zwg_file, header=None)
        usd_raw = pd.read_excel(usd_file, header=None)

        zwg_df = clean_and_prepare(zwg_raw)
        usd_df = clean_and_prepare(usd_raw)

        # Match column names from sample (assume first non-empty row is the structure)
        sample_raw = pd.read_excel(sample_file, header=None)
        sample_raw = sample_raw.dropna(how="all")
        sample_columns = sample_raw.iloc[0].dropna().tolist()

        zwg_df = zwg_df[[col for col in zwg_df.columns if col in sample_columns]]
        usd_df = usd_df[[col for col in usd_df.columns if col in sample_columns]]

        # Reorder columns to match sample
        zwg_df = zwg_df.reindex(columns=sample_columns)
        usd_df = usd_df.reindex(columns=sample_columns)

        output = create_output_file(zwg_df, usd_df)

        st.success("✅ Files successfully merged and cleaned!")
        st.download_button(
            label="📥 Download Consolidated Aging Report",
            data=output,
            file_name="Consolidated_Aging_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
else:
    st.info("⬆️ Please upload all three files to begin processing.")
