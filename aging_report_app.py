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
        if df.columns.notna().sum() > 1:  # more than one non-None column name
            return skip
    return 0  # fallback

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
    outpu
