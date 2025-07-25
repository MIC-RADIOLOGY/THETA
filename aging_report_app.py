import streamlit as st
import pandas as pd

st.set_page_config(page_title="Theta Aging Report", layout="centered")

st.title("📊 Theta Aging Report Generator")
st.markdown("Upload your ZWG and USD CSV files to generate the combined aging report.")

# 🔧 Clean and prepare data
def clean_data(file):
    raw = pd.read_csv(file, skip_blank_lines=True)

    # Try to detect where actual data starts
    first_col = raw.columns[0]
    first_valid_row = raw[first_col].first_valid_index()

    if first_valid_row is None:
        raise ValueError("⚠️ No valid data found in uploaded file.")

    df = raw.iloc[first_valid_row:].copy()

    # Use the first row of that block as headers
    df.columns = df.iloc[0]
    df = df[1:]  # Remove header row now in use as columns

    # Drop empty rows
    if df.shape[1] < 2:
        raise ValueError("⚠️ Data format seems incorrect. Not enough columns.")

    df = df.dropna(subset=[df.columns[0]])  # Drop rows with empty first column
    df = df.fillna("0.00")

    # Convert all numeric fields
    for col in df.columns[1:]:
        df[col] = df[col].apply(lambda val: str(val).replace(",", "").replace("$", "").strip())
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.00)

    df.reset_index(drop=True, inplace=True)
    return df

# 📤 File uploads
uploaded_zwg = st.file_uploader("Upload ZWG CSV", type="csv")
uploaded_usd = st.file_uploader("Upload USD CSV", type="csv")

if uploaded_zwg and uploaded_usd:
    try:
        # Clean both files
        zwg_df = clean_data(uploaded_zwg)
        usd_df = clean_data(uploaded_usd)

        # Add currency column
        zwg_df.insert(0, "Currency", "ZWG")
        usd_df.insert(0, "Currency", "USD")

        # Combine reports
        combined_df = pd.concat([zwg_df, usd_df], ignore_index=True)

        st.success("✅ Aging report generated successfully!")
        st.dataframe(combined_df, use_container_width=True)

        # Downloadable CSV
        csv = combined_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Combined Aging Report",
            data=csv,
            file_name="Theta_Aging_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
else:
    st.info("👈 Please upload both ZWG and USD files to continue.")
