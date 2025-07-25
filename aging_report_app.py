import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Aging Report Merger", layout="wide")

st.title("📊 Aging Report Merger (ZWL & USD)")

# --- File Upload ---
zwl_file = st.file_uploader("Upload ZWL Aging CSV", type=["csv"], key="zwl")
usd_file = st.file_uploader("Upload USD Aging CSV", type=["csv"], key="usd")

# --- Helper to clean currency columns ---
def clean_dataframe(df, currency):
    df = df.copy()

    # Automatically detect amount-like columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace('[\$,]', '', regex=True)
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except Exception:
                pass

    df["Currency"] = currency
    return df

if zwl_file and usd_file:
    try:
        df_zwl = pd.read_csv(zwl_file)
        df_usd = pd.read_csv(usd_file)

        df_zwl_clean = clean_dataframe(df_zwl, "ZWL")
        df_usd_clean = clean_dataframe(df_usd, "USD")

        # Combine both
        final_df = pd.concat([df_zwl_clean, df_usd_clean], ignore_index=True)

        st.success("✅ Files merged successfully!")

        # --- Show separated dataframes ---
        tab1, tab2, tab3 = st.tabs(["💵 USD Only", "🪙 ZWL Only", "📋 Combined"])

        with tab1:
            st.dataframe(df_usd_clean, use_container_width=True)

        with tab2:
            st.dataframe(df_zwl_clean, use_container_width=True)

        with tab3:
            st.dataframe(final_df, use_container_width=True)

        # --- Download button ---
        csv_data = final_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Combined Aging Report", csv_data, "combined_aging_report.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
else:
    st.info("Please upload both ZWL and USD CSV files to proceed.")
