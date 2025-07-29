import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

st.set_page_config(page_title="📊 Aging Report Merger", layout="wide")
st.title("📊 AI-Powered Aging Report Merger")

# --- Smart Cleaning ---
def parse_ageing_file(df):
    # Drop empty columns
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    # Find header row: the one containing "Provider"
    header_row_idx = df[df.apply(lambda row: row.astype(str).str.contains("Provider", case=False).any(), axis=1)].index[0]

    # Set headers
    df.columns = df.iloc[header_row_idx]
    df = df[header_row_idx + 1:]

    # Strip column names and drop empty ones
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    # Replace negative and non-numeric with 0
    df = df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x)
    
    # Convert everything that looks like a string number to float
    for col in df.columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace("[^0-9.-]", "", regex=True), errors='ignore')
    
    return df.fillna(0)

# --- Create Excel Output ---
def generate_excel_output(zwg_df, usd_df):
    wb = Workbook()
    ws = wb.active
    ws.title = "Consolidated Aging"

    # Write ZWL
    ws.append(["ZWL AGING"])
    for r in dataframe_to_rows(zwg_df, index=False, header=True):
        ws.append(r)

    ws.append([])
    ws.append(["USD AGING"])
    for r in dataframe_to_rows(usd_df, index=False, header=True):
        ws.append(r)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# --- Upload UI ---
usd_file = st.file_uploader("📤 Upload PROJECT USD", type=["xlsx"])
zwg_file = st.file_uploader("📤 Upload PROJECT ZWG", type=["xlsx"])
sample_file = st.file_uploader("📤 Upload Sample Layout File", type=["xlsx"])

if usd_file and zwg_file and sample_file:
    try:
        # Load Excel
        usd_df_raw = pd.read_excel(usd_file, header=None)
        zwg_df_raw = pd.read_excel(zwg_file, header=None)

        # Smart parse
        usd_df = parse_ageing_file(usd_df_raw)
        zwg_df = parse_ageing_file(zwg_df_raw)

        # Reorder columns to match sample layout
        sample_df_raw = pd.read_excel(sample_file, header=None)
        sample_df_raw = sample_df_raw.dropna(axis=0, how="all")
        layout_headers = sample_df_raw.iloc[1].dropna().tolist()

        # Keep only relevant columns
        usd_df = usd_df[[col for col in layout_headers if col in usd_df.columns]]
        zwg_df = zwg_df[[col for col in layout_headers if col in zwg_df.columns]]

        # Reorder
        usd_df = usd_df.reindex(columns=layout_headers)
        zwg_df = zwg_df.reindex(columns=layout_headers)

        # Replace negative and nulls with 0
        usd_df = usd_df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x).fillna(0)
        zwg_df = zwg_df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x).fillna(0)

        # Output file
        output_excel = generate_excel_output(zwg_df, usd_df)

        st.success("✅ Merged and formatted successfully!")
        st.download_button(
            label="📥 Download Consolidated Aging Report",
            data=output_excel,
            file_name="Consolidated_Aging_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("⬆️ Upload all 3 files (ZWG, USD, and Sample) to begin.")
