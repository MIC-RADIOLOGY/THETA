import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd

# --- Cleaning function ---
def clean_dataframe(df, currency):
    df = df.copy()
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces

    for col in df.select_dtypes(include='object').columns:
        if df[col].str.contains(r'\d', regex=True, na=False).any():
            df[col] = df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='ignore')

    df["Currency"] = currency
    return df

# --- Load CSV file ---
def load_file(currency):
    path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if not path:
        return
    try:
        df = pd.read_csv(path)
        if df.empty:
            raise ValueError("CSV is empty.")
        df_clean = clean_dataframe(df, currency)
        if currency == "ZWL":
            app_data["zwl"] = df_clean
            zwl_status.config(text="✅ ZWL File Loaded")
        else:
            app_data["usd"] = df_clean
            usd_status.config(text="✅ USD File Loaded")
    except Exception as e:
        messagebox.showerror("Load Error", str(e))

# --- Merge and show data ---
def merge_and_display():
    if app_data["zwl"] is None or app_data["usd"] is None:
        messagebox.showwarning("Missing Files", "Please load both ZWL and USD files.")
        return
    try:
        zwl_df = app_data["zwl"]
        usd_df = app_data["usd"]

        # Align columns if identical
        if set(zwl_df.columns) == set(usd_df.columns):
            usd_df = usd_df[zwl_df.columns]

        combined_df = pd.concat([zwl_df, usd_df], ignore_index=True)
        app_data["combined"] = combined_df

        # Display in table
        table.delete(*table.get_children())
        table["columns"] = list(combined_df.columns)
        table["show"] = "headings"
        for col in combined_df.columns:
            table.heading(col, text=col)
            table.column(col, width=100)

        for _, row in combined_df.iterrows():
            table.insert("", "end", values=list(row))

        messagebox.showinfo("Success", "Merged and displayed data.")
    except Exception as e:
        messagebox.showerror("Merge Error", str(e))

# --- Save merged file ---
def save_combined():
    df = app_data.get("combined")
    if df is None:
        messagebox.showwarning("No Data", "Merge the files first.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv",
                                        filetypes=[("CSV Files", "*.csv")])
    if path:
        try:
            df.to_csv(path, index=False)
            messagebox.showinfo("Saved", f"File saved: {path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

# --- GUI setup ---
app = tk.Tk()
app.title("Aging Report Merger")
app.geometry("900x600")

app_data = {"zwl": None, "usd": None, "combined": None}

# --- Top Controls ---
frame = tk.Frame(app)
frame.pack(pady=10)

tk.Button(frame, text="📂 Load ZWL CSV", command=lambda: load_file("ZWL")).grid(row=0, column=0, padx=10)
tk.Button(frame, text="📂 Load USD CSV", command=lambda: load_file("USD")).grid(row=0, column=1, padx=10)

zwl_status = tk.Label(frame, text="No ZWL file", fg="red")
usd_status = tk.Label(frame, text="No USD file", fg="red")
zwl_status.grid(row=1, column=0)
usd_status.grid(row=1, column=1)

tk.Button(app, text="🔁 Merge & Display", command=merge_and_display, width=30).pack(pady=10)
tk.Button(app, text="💾 Save Merged CSV", command=save_combined, width=30).pack()

# --- Table for displaying merged data ---
table = ttk.Treeview(app)
table.pack(expand=True, fill="both", padx=10, pady=10)

app.mainloop()
