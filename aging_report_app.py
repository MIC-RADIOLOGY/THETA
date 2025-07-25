import streamlit as st
import pandas as pd
import io
import datetime
import re # Import the re module for regular expressions

st.set_page_config(page_title="Aging Report Merger", layout="wide")

st.title("📊 Aging Report Merger (ZWL & USD)")
st.markdown("Upload your ZWL and USD aging CSV files to generate a combined, formatted report.")

# --- File Upload ---
zwl_file = st.file_uploader("Upload ZWL Aging CSV (e.g., PROJECT ZWG.csv)", type=["csv"], key="zwl")
usd_file = st.file_uploader("Upload USD Aging CSV (e.g., PROJECT USD.csv)", type=["csv"], key="usd")

# --- Helper to clean and process dataframe ---
def clean_and_process_df(file_buffer, currency_type):
    """
    Reads the raw CSV content from a file buffer, cleans it by selecting relevant columns,
    removing non-numeric characters from numeric fields, converting them to float,
    adding an 'Unallocated' column, and adding a currency column.
    It is designed to be robust against slight variations in column presence and data formatting.
    """
    try:
        # Read CSV, skipping the initial header rows (header=5 means row 6 is header)
        df_raw = pd.read_csv(file_buffer, header=5, skipinitialspace=True)
    except Exception as e:
        raise ValueError(f"Error reading CSV file. Please ensure it's a valid CSV and the header is at row 6. Details: {e}")

    # Define the target column names for the final DataFrame
    target_numeric_cols = [
        '180 Days Plus', '150 Days', '120 Days', '90 Days',
        '60 Days', '30 Days', 'Current', 'Balance'
    ]
    
    # Initialize an empty DataFrame with the expected final columns to ensure consistent structure
    cleaned_df = pd.DataFrame()

    # Process 'Provider' column - it's crucial and should ideally be the first column
    if 'Provider' in df_raw.columns:
        cleaned_df['Provider'] = df_raw['Provider']
    elif len(df_raw.columns) > 0:
        # Fallback: assume the first column is 'Provider' if not explicitly named
        cleaned_df['Provider'] = df_raw.iloc[:, 0]
        # Rename the original column in df_raw for consistency if it was unnamed
        if df_raw.columns[0] != 'Provider':
            df_raw.rename(columns={df_raw.columns[0]: 'Provider'}, inplace=True)
    else:
        raise ValueError("Could not find 'Provider' column in the CSV or the file is empty. Please check your file format.")

    # Process numeric columns with more robust cleaning
    for col_idx, col_name in enumerate(target_numeric_cols):
        # Determine the actual column name in df_raw based on its position in the header
        # This assumes the relative positions (e.g., 7th, 9th, etc.) are consistent
        # in the raw CSVs, as identified in previous turns.
        # We need to map the target_numeric_cols to their actual index in the raw header (header=5)
        # Based on the snippet:
        # Provider (0), 180 Days Plus (7), 150 Days (9), 120 Days (12), 90 Days (15), 60 Days (17), 30 Days (19), Current (21), Balance (23)
        raw_col_index_map = {
            '180 Days Plus': 7, '150 Days': 9, '120 Days': 12, '90 Days': 15,
            '60 Days': 17, '30 Days': 19, 'Current': 21, 'Balance': 23
        }
        
        raw_col_actual_name = None
        if raw_col_index_map[col_name] < len(df_raw.columns):
            raw_col_actual_name = df_raw.columns[raw_col_index_map[col_name]]

        if raw_col_actual_name and raw_col_actual_name in df_raw.columns:
            # Convert to string and strip whitespace
            temp_series = df_raw[raw_col_actual_name].astype(str).str.strip()
            
            # Remove parentheses (for negative numbers like "(123.45)")
            temp_series = temp_series.str.replace(r'[\(\)]', '', regex=True)
            
            # Remove commas and dollar signs
            temp_series = temp_series.str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            
            # Convert to numeric, coercing errors to NaN, then fill NaN with 0.0
            cleaned_df[col_name] = pd.to_numeric(temp_series, errors='coerce').fillna(0.0)
        else:
            # If a numeric column is missing or not found at its expected index, add it with 0.0 values
            cleaned_df[col_name] = 0.0

    # Add 'Unallocated' column initialized to 0.0, as per the desired AGING.xlsx format
    cleaned_df['Unallocated'] = 0.0

    # Add currency column
    cleaned_df['Currency'] = currency_type

    # Ensure all target columns are present and in the correct order for the final DataFrame
    final_cols_order = [
        'Provider', '180 Days Plus', '150 Days', '120 Days', '90 Days',
        '60 Days', '30 Days', 'Current', 'Unallocated', 'Balance', 'Currency'
    ]
    
    # Reindex the DataFrame to ensure all columns are present and in the correct order.
    cleaned_df = cleaned_df.reindex(columns=final_cols_order, fill_value=0.0)

    return cleaned_df

if zwl_file and usd_file:
    try:
        # Process and clean both ZWL and USD dataframes
        df_zwl_clean = clean_and_process_df(zwl_file, "ZWL")
        df_usd_clean = clean_and_process_df(usd_file, "USD")

        # Concatenate for display in Streamlit tabs
        final_df_display = pd.concat([df_zwl_clean, df_usd_clean], ignore_index=True)

        st.success("✅ Files merged and processed successfully!")

        # --- Display DataFrames in Tabs ---
        tab1, tab2, tab3 = st.tabs(["💵 USD Only", "🪙 ZWL Only", "📋 Combined Data"])

        with tab1:
            st.header("USD Aging Data")
            # Display without the 'Currency' column for a cleaner data view
            st.dataframe(df_usd_clean.drop(columns=['Currency']), use_container_width=True)

        with tab2:
            st.header("ZWL Aging Data")
            # Display without the 'Currency' column for a cleaner data view
            st.dataframe(df_zwl_clean.drop(columns=['Currency']), use_container_width=True)

        with tab3:
            st.header("Combined Aging Data")
            # Display with the 'Currency' column for the combined view
            st.dataframe(final_df_display, use_container_width=True)

        # --- Generate Formatted CSV for Download ---
        csv_buffer = io.StringIO()
        current_date = datetime.datetime.now().strftime('%d.%m.%Y')

        # Write top header rows as per AGING.xlsx example
        csv_buffer.write(f',,AGING@{current_date},,,,,,,,,\n')
        csv_buffer.write(',,Provider,180 Days Plus,150 Days,120 Days,90 Days,60 Days,30 Days,Current,Unallocated,Balance\n')

        # Write ZWL data section
        csv_buffer.write(',,Currency: ZWL,,,,,,,,,\n')
        # Select only the columns that match the AGING format, excluding 'Currency' for the CSV output
        zwl_data_for_csv = df_zwl_clean[['Provider', '180 Days Plus', '150 Days', '120 Days', '90 Days', '60 Days', '30 Days', 'Current', 'Unallocated', 'Balance']]
        for index, row in zwl_data_for_csv.iterrows():
            # Prepend two empty columns (,,)
            formatted_row_parts = [row['Provider']]
            for col in ['180 Days Plus', '150 Days', '120 Days', '90 Days', '60 Days', '30 Days', 'Current']:
                formatted_row_parts.append(f"{row[col]:.2f}")
            
            # Special handling for 'Unallocated': blank if 0.0, else format to 2 decimal places
            formatted_row_parts.append("" if row['Unallocated'] == 0.0 else f"{row['Unallocated']:.2f}")
            
            formatted_row_parts.append(f"{row['Balance']:.2f}")
            
            csv_buffer.write(f',,{",".join(map(str, formatted_row_parts))}\n')

        csv_buffer.write('\n') # Add a blank line for visual separation between currency sections

        # Write USD data section
        csv_buffer.write(',,Currency: USD,,,,,,,,,\n')
        usd_data_for_csv = df_usd_clean[['Provider', '180 Days Plus', '150 Days', '120 Days', '90 Days', '60 Days', '30 Days', 'Current', 'Unallocated', 'Balance']]
        for index, row in usd_data_for_csv.iterrows():
            # Prepend two empty columns (,,)
            formatted_row_parts = [row['Provider']]
            for col in ['180 Days Plus', '150 Days', '120 Days', '90 Days', '60 Days', '30 Days', 'Current']:
                formatted_row_parts.append(f"{row[col]:.2f}")
            
            # Special handling for 'Unallocated': blank if 0.0, else format to 2 decimal places
            formatted_row_parts.append("" if row['Unallocated'] == 0.0 else f"{row['Unallocated']:.2f}")
            
            formatted_row_parts.append(f"{row['Balance']:.2f}")
            
            csv_buffer.write(f',,{",".join(map(str, formatted_row_parts))}\n')

        # Get the final CSV string and encode it for download
        csv_data_for_download = csv_buffer.getvalue().encode("utf-8")

        st.download_button(
            "⬇️ Download Combined Aging Report (Formatted)",
            csv_data_for_download,
            f"combined_aging_report_formatted_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}. Please ensure your CSV files have the expected format.")
        st.exception(e) # Display the full exception for debugging
else:
    st.info("Please upload both ZWL and USD CSV files to proceed.")

 
