import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows

st.set_page_config(page_title="Aging Report Merger", layout="wide")
st.title("📊 Aging Report Merger (ZWL & USD with Formulas)")

def clean_dataframe(df):
    df = df.applymap(lambda x: str(x).replace(',', '') if isinstance(x, str) else x)
    df = df.apply(pd.to_numeric, errors='ignore')
    df = df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x)
    return df

# --- Uploads ---
sample_file = st.file_uploader("📄 Upload Sample Layout File (with formulas)", type=["xlsx", "xls"], key="sample")
zwl_file = st.file_uploader("💱 Upload ZWL Aging Report", type=["xlsx", "xls"], key="zwl")
usd_file = st.file_uploader("💲 Upload USD Aging Report", type=["xlsx", "xls"], key="usd")

if sample_file and zwl_file and usd_file:
    try:
        # Load sample and extract structure
        sample_wb = load_workbook(sample_file, data_only=False)
        sample_ws = sample_wb.active
        sample_headers = [cell.value for cell in next(sample_ws.iter_rows(min_row=1, max_row=1))]
        formula_columns = {}
        for col_idx, cell in enumerate(sample_ws[2], start=1):
            if cell.data_type == 'f':
                formula_columns[col_idx - 1] = cell.value  # map index to formula

        # Load data
        zwl_df = pd.read_excel(zwl_file)
        usd_df = pd.read_excel(usd_file)

        # Clean
        zwl_df = clean_dataframe(zwl_df)
        usd_df = clean_dataframe(usd_df)

        # Remove "Balance" column
        if 'Balance' in zwl_df.columns:
            zwl_df.drop(columns=['Balance'], inplace=True)
        if 'Balance' in usd_df.columns:
            usd_df.drop(columns=['Balance'], inplace=True)

        # Label currencies
        zwl_df.insert(0, 'Currency', 'ZWL')
        usd_df.insert(0, 'Currency', 'USD')

        # Combine and reorder
        combined_df = pd.concat([zwl_df, usd_df], ignore_index=True)
        combined_df = combined_df.reindex(columns=sample_headers)

        # Display preview
        st.subheader("🔎 Consolidated Preview")
        st.dataframe(combined_df)

        # Export with formulas using openpyxl
        def to_excel_with_formulas(df, formula_cols):
            output = BytesIO()
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active

            # Write headers
            ws.append(df.columns.tolist())

            for row_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), start=2):
                ws.append(row)
                for col_idx, formula in formula_cols.items():
                    col_letter = ws.cell(row=row_idx, column=col_idx + 1).column_letter
                    formula_row = f"{formula}".replace("2", str(row_idx))  # adjust formula to current row
                    ws.cell(row=row_idx, column=col_idx + 1).value = f"={formula_row}"

            wb.save(output)
            output.seek(0)
            return output.getvalue()

        # Download
        st.download_button(
            label="📥 Download Final Report with Formulas",
            data=to_excel_with_formulas(combined_df, formula_columns),
            file_name="Consolidated_Aging_Report_with_Formulas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
