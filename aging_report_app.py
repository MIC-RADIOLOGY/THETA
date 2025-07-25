import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Theta Aging Report", layout="centered")

st.title("📊 Theta Aging Report Generator")
st.markdown("Upload your ZWG and USD aging report CSV files below.")

def clean_and_prepare_data(uploaded_file, currency_label):
    try:
        # Read raw content
        content = uploaded_file.read()
        df_raw = pd.read_csv(io.BytesIO(content), header=None)

        # Find the row that has the most non-null values = likely the header
        header_row_index = df_raw.notna().sum(axis=1).idxmax()
        df = df_raw.iloc[header_row_index:].copy()
        df.columns = df.iloc[0]  # set headers
        df = df[1:]  # drop the header row now used

        df = df.dropna(how='all')  # remove fully empty rows
        df = df.fillna("0.00")  # fill blanks with 0.00

        # Only process numeric columns (skip name columns)
        for col in df.columns[1:]:
            try:
                df[col] = (
                    df[col].astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.strip()
                )
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.00)
            except Exception as err:
                st.warning(f"⚠️ Column '{col}' could not be cleaned: {err}")
                df[col] = 0.00  # fallback

        df.insert(0, "Currency", currency_label)
        df.reset_index(drop=True, inplace=True)
        return df

    except Exception as e:
        raise ValueError(f"File parsing failed: {e}")

# Uploads
uploaded_zwg = st.file_uploader("Upload ZWG CSV File", type=["csv"])
uploaded_usd = st.file_uploader("Upload USD CSV File", type=["csv"])

if uploaded_zwg and uploaded_usd:
    try:
        zwg_data = clean_and_prepare_data(uploaded_zwg, "ZWG")
        usd_data = clean_and_prepare_data(uploaded_usd, "USD")

        combined = pd.concat([zwg_data, usd_data], ignore_index=True)
        st.success("✅ Aging report created successfully!")

        st.dataframe(combined, use_container_width=True)

        # Download button
        csv = combined.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Combined Aging Report",
            data=csv,
            file_name="Theta_Aging_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
else:
    st.info("⬆️ Please upload both ZWG and USD files to proceed.")
