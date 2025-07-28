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

def detect_valid_header(file, max_check=10):
    for skip in range(max_check):
        df = pd.read_excel(file, skiprows=skip, nrows=1)
        if df.columns.notna().sum() > 1:
            return skip
    return 0

def read_excel_clean(file):
    skiprows = detect_valid_header(file)
    df = pd.read_excel(file, skiprows=skip)
    df.columns = df.columns.astype(str)
    return df

def to_excel_with_formulas(df, sample_file):
    sample_wb = load_workbook(sample_file, data_only=False)
    sample_ws = sample_wb.active
    sample_headers = [cell.value for cell in sample_ws[1]]

    formula_columns = {}
    for col_idx, cell in enumerate(sample_ws[2], start=1):
        if cell.data_type == 'f':
            formula_columns[col_idx - 1] = cell.value

    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.append(df.columns.tolist())

    for row_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), start=2):
        ws.append(row)
        for col_idx, formula in formula_columns.items():
            adjusted_formula = formula.replace("2", str(row_idx))
            ws.cell(row=row_idx, column=col_idx + 1).value = f"={adjusted_formula}"

    wb.save(output)
    output.seek(0)
    return output

# --- File Uploads ---
st.header("📂 Step 1: Upload Files")

sample_file = st.file_uploader("📄 Upload Sample Layout File (with Formulas)", type=["xlsx"])
zwl_file = st.file_uploader("💱 Upload ZWL Aging Report", type=["xlsx"])
usd_file = st.file_uploader("💲 Upload USD Aging Report", type=["xlsx"])

# Show status
if not sample_file:
    st.warning("Please upload the sample layout file.")
elif not zwl_file:
    st.warning("Please upload the ZWL report.")
elif not usd_file:
    st.warning("Please upload the USD report.")
else:
    try:
        # Load sample layout
        sample_wb = load_workbook(sample_file, data_only=False)
        sample_ws = sample_wb.active
        sample_headers = [cell.value for cell in sample_ws[1]]

        # Load and clean ZWL
        zwl_df = read_excel_clean(zwl_file)
        zwl_df = clean_dataframe(zwl_df)
        zwl_df.insert(0, "Currency", "ZWL")
        if 'Balance' in zwl_df.columns:
            zwl_df.drop(columns=['Balance'], inplace=True)

        # Load and clean USD
        usd_df = read_excel_clean(usd_file)
        usd_df = clean_dataframe(usd_df)
        usd_df.insert(0, "Currency", "USD")
        if 'Balance' in usd_df.columns:
            usd_df.drop(columns=['Balance'], inplace=True)

        # Merge and match layout
        merged_df = pd.concat([zwl_df, usd_df], ignore_index=True)
        merged_df = merged_df.reindex(columns=sample_headers)

        st.subheader("✅ Step 2: Consolidated Preview")
        st.dataframe(merged_df)

        final_excel = to_excel_with_formulas(merged_df, sample_file)
        st.subheader("📥 Step 3: Download Final Report")
        st.download_button(
            label="Download Consolidated Aging Report",
            data=final_excel,
            file_name="Consolidated_Aging_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")

    
