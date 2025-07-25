import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Theta Aging Report", layout="centered")

st.title("📊 Theta Aging Report Generator")
st.markdown("Upload your ZWG and USD aging report CSV files below.")

def clean_and_prepare_data(uploaded_file, currency_label):
    # Read the CSV
    try:
        content = uploaded_file.read()
        df_raw = pd.read_csv(io.BytesIO(content))
    except Exception:
        raise ValueError("Unable to read the uploaded file. Please ensure it's a valid CSV.")

    # Try to locate the first row with actual column names
    for i in range(len(df_raw)):
        if df_raw.iloc[i].notna().sum() > 2:
            df = df_raw.iloc[i:].copy()
            df.columns = df.iloc[0]
            df = df[1:]
            break
    else:
        raise ValueError("Could not detect valid header row.")

    df = df.dropna(how='all')  # drop empty rows
    df = df.fillna("0.00")  # fill empty cells with zero as string

    # Clean numeric columns
    for col in df.columns[1:]:
        df[col] = (
            df[col].astype(str)
            .str.replace(",", "")
            .str.replace("$", "")
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.00)

    df.insert(0, "Currency", currency_label)
    df.reset_index(drop=True, inplace=True)
    return df

# Upload section
uploaded_zwg = st.file_uploader("Upload ZWG CSV File", type=["csv"])
uploaded_usd = st.file_uploader("Upload USD CSV File", type=["csv"])

# Process button
if uploaded_zwg and uploaded_usd:
    try:
        zwg_data = clean_and_prepare_data(uploaded_zwg, "ZWG")
        usd_data = clean_and_prepare_data(uploaded_usd, "USD")

        combined = pd.concat([zwg_data, usd_data], ignore_index=True)
        st.success("✅ Aging report created successfully!")

        st.dataframe(combined, use_container_width=True)

        # Downloadable CSV
        csv = combined.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Combined Report",
            data=csv,
            file_name="Theta_Aging_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("⬆️ Please upload both ZWG and USD files to proceed.")
