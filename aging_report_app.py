import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def clean_dataframe(df):
    # Remove commas and convert to numeric
    df = df.applymap(lambda x: str(x).replace(',', '') if isinstance(x, str) else x)

    # Convert to numeric where possible
    df = df.apply(pd.to_numeric, errors='ignore')

    # Replace negative numbers with zero
    df = df.applymap(lambda x: 0 if isinstance(x, (int, float)) and x < 0 else x)

    return df

def load_excel_file(title):
    file_path = filedialog.askopenfilename(title=title, filetypes=[("Excel files", "*.xlsx *.xls")])
    return file_path

def save_output_file(default_name="Consolidated_Aging_Report.xlsx"):
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default_name,
                                             filetypes=[("Excel files", "*.xlsx")])
    return file_path

def main():
    root = tk.Tk()
    root.withdraw()

    # Load Sample Layout File
    messagebox.showinfo("Sample Layout", "Select the SAMPLE layout file.")
    sample_file = load_excel_file("Select the Sample Layout File")
    if not sample_file:
        return

    sample_df = pd.read_excel(sample_file)

    # Load ZWL File
    messagebox.showinfo("ZWL File", "Select the ZWL aging report.")
    zwl_file = load_excel_file("Select ZWL File")
    if not zwl_file:
        return
    zwl_df = pd.read_excel(zwl_file)

    # Load USD File
    messagebox.showinfo("USD File", "Select the USD aging report.")
    usd_file = load_excel_file("Select USD File")
    if not usd_file:
        return
    usd_df = pd.read_excel(usd_file)

    # Clean Data
    zwl_df = clean_dataframe(zwl_df)
    usd_df = clean_dataframe(usd_df)

    # Remove "Balance" column if exists
    if 'Balance' in zwl_df.columns:
        zwl_df = zwl_df.drop(columns=['Balance'])
    if 'Balance' in usd_df.columns:
        usd_df = usd_df.drop(columns=['Balance'])

    # Add Currency Labels
    zwl_df.insert(0, 'Currency', 'ZWL')
    usd_df.insert(0, 'Currency', 'USD')

    # Combine both dataframes
    combined_df = pd.concat([zwl_df, usd_df], ignore_index=True)

    # Match Sample Layout Columns
    sample_columns = list(sample_df.columns)
    combined_df = combined_df.reindex(columns=sample_columns)

    # Save the result
    output_path = save_output_file()
    if output_path:
        try:
            combined_df.to_excel(output_path, index=False)
            messagebox.showinfo("Success", f"Consolidated report saved successfully:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

if __name__ == "__main__":
    main()

