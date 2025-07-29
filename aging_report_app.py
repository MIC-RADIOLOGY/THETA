import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

st.set_page_config(page_title="📊 Aging Report Merger", layout="wide")
st.title("📊 AI-Powered Aging Report Merger")

# --- ✅ Updated Function to Parse and Clean File Correctly ---
def parse_ageing_file(df):
    # Drop empty rows/columns
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")

    # Detect header row (contains "Provider")
    header_idx = df[df.apply(lambda row: row.astype(str).str.contains("Provider", case=False).any(), axis=1)].index[0]
    df.columns = df.iloc[header_idx]
    df = df[header_idx + 1:]

    # Clean headers
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.fillna(0)

    # Identify numeric columns (skip "Provider")
    numeric_cols = [col for col in df.columns if col.lower() != "provider"]

    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(r"[^\d.,-]", "", regex=True)
        df[col] = df[col].str.replace(",", "")
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df[col] = df[col].apply(lambda x: 0 if x < 0 else x)

    return df

# --- Create Excel Output File ---
def generate_excel_output(zwg_df, usd_df):
    wb = Workbook()
    ws = wb.active
    ws.title = "Consolidated Aging"

    # ZWL Section
    ws.append(["ZWL AGING"])
    for r in dataframe_to_rows(zwg_df, index=False, header=True):
        ws.append(r)

    ws.append([])  # empty line

    # USD Section
    ws.append(["USD AGING"])
    for r in dataframe_to_rows(usd_df, index=False, header=True):
        ws.append(r)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# --- File Upload UI ---
usd_file = st.file_uploader("📤 Upload PROJECT USD", type=["xlsx"])
zwg_file = st.file_uploader("📤 Upload PROJECT ZWG", type=["xlsx"])
sample_file = st.file_uploader("📤 Upload Sample Layout File", type=["xlsx"])

# --- Processing ---
if usd_file and zwg_file and sample_file:
    try:
        usd_df_raw = pd.read_excel(usd_file, header=None)
        zwg_df_raw = pd.read_excel(zwg_file, header=None)
        sample_df_raw = pd.read_excel(sample_file, header=None)

        usd_df = parse_ageing_file(usd_df_raw)
        zwg_df = parse_ageing_file(zwg_df_raw)

        # Get layout structure from sample file
        sample_df_raw = sample_df_raw.dropna(axis=0, how="all")
        layout_headers = sample_df_raw.iloc[1].dropna().tolist()

        # Filter and reorder columns
        usd_df = usd_df[[col for col in layout_headers if col in usd_df.columns]]
        zwg_df = zwg_df[[col for col in layout_headers if col in zwg_df.columns]]
        usd_df = usd_df.reindex(columns=layout_headers)
        zwg_df = zwg_df.reindex(columns=layout_headers)

        # Create downloadable file
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
