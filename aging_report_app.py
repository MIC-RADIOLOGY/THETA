import streamlit as st
import pandas as pd

st.set_page_config(page_title="Theta Aging Report", layout="centered")

st.title("📊 Theta Aging Report Generator")
st.markdown("Upload your ZWG and USD CSV files to generate the combined aging report.")

def clean_data(file):
    raw = pd.read_csv(file, skip_blank_lines=True)
    # Auto-detect data starting point
    data_start = raw[raw.columns[0]].first_valid_index()
    df = raw.iloc[data_start:].copy()
    df.columns = df.iloc[0]
    df = df[1:]  # Drop duplicated header row
    df = df.dropna(subset=[df.columns[0]])  # Drop empty rows
    df = df.fillna("0.00")

    # Clean numeric columns
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace(",", "").str.replace("$", "").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.00)

    df.reset_index(drop=True, inplace=True)
    return df

uploaded_zwg = st.file_uploader("Upload ZWG CSV", type="csv")
uploaded_usd = st.file_uploader("Upload USD CSV", type="csv")

if uploaded_zwg and uploaded_usd:
    zwg_df = clean_data(uploaded_zwg)
    usd_df = clean_data(uploaded_usd)

    zwg_df.insert(0, "Currency", "ZWG")
    usd_df.insert(0, "Currency", "USD")

    combined_df = pd.concat([zwg_df, usd_df], ignore_index=True)

    st.success("✅ Report generated!")
    st.dataframe(combined_df, use_container_width=True)

    csv = combined_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Combined Report", data=csv, file_name="Theta_Aging_Report.csv", mime="text/csv")

