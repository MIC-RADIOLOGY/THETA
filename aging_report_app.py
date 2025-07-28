import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook, load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows

st.set_page_config(page_title="Aging Report Merger", layout="wide")
st.title("📊 Aging Report Merger (ZWL & USD with Formulas)")

def clean_dataframe(df):
    df = df.applymap(lambda x: str(x).replace(',', '') if isinstance(x, str) else x)
    df = df.apply(pd.to_numeric, errors='ignore')
    df = df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x)
    return df

def read_excel_with_valid_header(file, preview_rows=10):
    # Try different skiprows to find the first row with actual headers
    for skip in range(preview_rows):
        df = pd.read_excel(file, skiprows=skip)
        if df.columns.str.contains("Customer", case=False).any() or df.columns.str.contains("Account", case=False).any():
            return df
    # Fallback: read normally
    return pd.read_excel(file)

def to_excel_with_formulas(df, sample_file):
    # Load sample workbook to detect formulas
    sample_wb = load_workbook(sample_file, data_only=False)
    sample_ws = sample_wb.active
    sample_headers = [cell.value for cell in next(sample_ws.iter_rows(min_row=1, max_row=1))]

    formula_columns = {}
    for col_idx, cell in enumerate(sample_ws[2], start=1):
        if cell.data_type == 'f':
            formula_columns[col_idx - 1] = cell.value  # zero-indexed

    # Write final Excel with formulas
    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.append(df.columns.tolist())

    for row_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), start=2):
        ws.append(row)
        for col_idx, formula in formula_columns.items():
            formula_for_row = formula.replace("2", str(row_idx))  # adjust row reference
            ws.cell(row=row_idx, column=col_idx + 1).value = f"={formula_for_row}"

    wb.save(output)
    output.seek(0)
    return output

# === File Uploads ===
sample_file = st.file_uploader("📄 Upload Sample Layout File (with Formulas)", type=["xlsx"])
zwl_file = st.file_uploader("💱 Upload ZWL Aging Report", type=["xlsx"])
usd_file = st.file_uploader("💲 Upload USD Aging Report", type=["xlsx"])

# === Process Logic ===
if sample_file and zwl_file and usd_file:
    try:
        # Load sample file for layout reference
        sample_wb = load_workbook(sample_file, data_only=False)
        sample_ws = sample_wb.active
        sample_headers = [cell.value for cell in sample_ws[1]]

        # Read and clean ZWL data
        zwl_df = read_excel_with_valid_header(zwl_file)
        zwl_df = clean_dataframe(zwl_df)
        zwl_df.insert(0, "Currency", "ZWL")
        if 'Balance' in zwl_df.columns:
            zwl_df = zwl_df.drop(columns=['Balance'])

        # Read and clean USD data
        usd_df = read_excel_with_valid_header(usd_file)
        usd_df = clean_dataframe(usd_df)
        usd_df.insert(0, "Currency", "USD")
        if 'Balance' in usd_df.columns:
            usd_df = usd_df.drop(columns=['Balance'])

        # Merge and match sample layout
        merged_df = pd.concat([zwl_df, usd_df], ignore_index=True)
        merged_df = merged_df.reindex(columns=sample_headers)

        # Display preview
        st.subheader("🔍 Consolidated Preview")
        st.dataframe(merged_df)

        # Prepare downloadable file with formulas
        excel_bytes = to_excel_with_formulas(merged_df, sample_file)
        st.download_button(
            label="📥 Download Final Report with Formulas",
            data=excel_bytes,
            file_name="Consolidated_Aging_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
