import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Aging Report Merger", layout="wide")
st.title("📊 Aging Report Merger (ZWL & USD)")

def clean_dataframe(df):
    # Remove commas and convert to numeric
    df = df.applymap(lambda x: str(x).replace(',', '') if isinstance(x, str) else x)
    df = df.apply(pd.to_numeric, errors='ignore')

    # Replace negative numbers with zero
    df = df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x)
    
    return df

# Upload sample layout file
sample_file = st.file_uploader("Upload Sample Layout File (Excel)", type=["xlsx", "xls"], key="sample")
if sample_file:
    sample_df = pd.read_excel(sample_file)
    st.success("✅ Sample layout uploaded.")

# Upload ZWL file
zwl_file = st.file_uploader("Upload ZWL Aging Report", type=["xlsx", "xls"], key="zwl")
if zwl_file:
    zwl_df = pd.read_excel(zwl_file)
    st.success("✅ ZWL file uploaded.")

# Upload USD file
usd_file = st.file_uploader("Upload USD Aging Report", type=["xlsx", "xls"], key="usd")
if usd_file:
    usd_df = pd.read_excel(usd_file)
    st.success("✅ USD file uploaded.")

# Process files
if sample_file and zwl_file and usd_file:
    try:
        # Clean both files
        zwl_df = clean_dataframe(zwl_df)
        usd_df = clean_dataframe(usd_df)

        # Drop Balance column if exists
        if 'Balance' in zwl_df.columns:
            zwl_df = zwl_df.drop(columns=['Balance'])
        if 'Balance' in usd_df.columns:
            usd_df = usd_df.drop(columns=['Balance'])

        # Add Currency column
        zwl_df.insert(0, 'Currency', 'ZWL')
        usd_df.insert(0, 'Currency', 'USD')

        # Combine
        combined_df = pd.concat([zwl_df, usd_df], ignore_index=True)

        # Reorder columns to match sample
        sample_columns = list(sample_df.columns)
        combined_df = combined_df.reindex(columns=sample_columns)

        # Display result
        st.subheader("✅ Consolidated Preview")
        st.dataframe(combined_df)

        # Create download link
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()

        st.download_button(
            label="📥 Download Consolidated Report",
            data=to_excel(combined_df),
            file_name="Consolidated_Aging_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
   
