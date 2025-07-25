import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Theta Aging Report", layout="centered")
st.title("📊 Aging Report Generator – Theta")
st.write("Upload ZWG and USD CSV files to generate the combined aging report.")

zwg_file = st.file_uploader("Upload ZWG CSV", type="csv")
usd_file = st.file_uploader("Upload USD CSV", type="csv")

expected_columns = [
    "Provider", "180 Days Plus", "150 Days", "120 Days", "90 Days",
    "60 Days", "30 Days", "Current", "Unallocated", "Balance"
]

def clean_amount(val):
    if pd.isna(val):
        return 0.0
    val = str(val).replace(",", "").replace("$", "").strip()
    try:
        return float(val)
    except:
        return 0.0

def prepare_aging_data(uploaded_file):
    raw = pd.read_csv(uploaded_file)
    clean = raw.iloc[5:].copy()
    clean.columns = raw.iloc[4]
    clean = clean.loc[:, clean.columns.notna()]
    clean = clean.dropna(subset=[clean.columns[0]])
    clean.reset_index(drop=True, inplace=True)

    for col in expected_columns:
        if col not in clean.columns:
            clean[col] = None

    df = clean[expected_columns].copy()
    for col in expected_columns[1:-1]:
        df[col] = df[col].apply(clean_amount)
    df["Balance"] = df[expected_columns[1:-1]].sum(axis=1)
    return df

if zwg_file and usd_file:
    with st.spinner("Processing files..."):
        zwg_df = prepare_aging_data(zwg_file)
        usd_df = prepare_aging_data(usd_file)

        blank = pd.DataFrame([[""] * len(expected_columns)], columns=expected_columns)
        zwg_label = pd.DataFrame([["ZWG"] + [""] * (len(expected_columns) - 1)], columns=expected_columns)
        usd_label = pd.DataFrame([["USD"] + [""] * (len(expected_columns) - 1)], columns=expected_columns)

        final_df = pd.concat([
            zwg_label,
            zwg_df,
            blank,
            usd_label,
            usd_df
        ], ignore_index=True)

        st.success("✅ Report generated successfully!")
        st.dataframe(final_df)

        csv_buffer = io.StringIO()
        final_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Combined Aging Report (CSV)",
            data=csv_buffer.getvalue(),
            file_name="Combined_Aging_Report_Theta.csv",
            mime="text/csv"
        )
