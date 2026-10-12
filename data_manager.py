import os
import io
import urllib.request
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ==========================================================
# KONFIGURASI DATABASE TUNGGAL (GOOGLE SPREADSHEET)
# ==========================================================
GSHEET_ID = "1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{GSHEET_ID}/edit"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwwFYKKp8q-6BFgJldMO1GCX1GeHviWa3dVbigrCoq22aebjVM7w6OyOE_yY6trRQE/exec"

PLAN_BENCHMARK = 4.0  # Tolak ukur tetap operasional: < 4.0m tugboat tidak bisa masuk

COLUMNS = [
    "ID",
    "Tanggal",
    "Waktu",
    "Titik Pantau",
    "Kedalaman Aktual (m)",
    "Plan Kedalaman (m)",
    "Status",
    "Petugas",
    "Keterangan"
]

def safe_float(val, default=0.0):
    """Konversi aman ke float untuk mencegah error pada string kosong ('') atau format koma"""
    if val is None or pd.isna(val):
        return default
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip().replace(",", ".")
    if not val_str:
        return default
    try:
        return float(val_str)
    except (ValueError, TypeError):
        return default

def determine_status(depth):
    """
    Tolak Ukur Operasional Sungai Senyiur:
    - Kedalaman < 4.0 meter: Surut (Tugboat TIDAK BISA masuk ke sungai).
    - Kedalaman >= 4.0 meter: Aman (Tugboat bisa masuk dan beroperasi lancar).
    - Kedalaman > 8.0 meter: Siaga Banjir / Debit dan arus kuat.
    """
    depth_val = safe_float(depth, default=PLAN_BENCHMARK)
    if depth_val < PLAN_BENCHMARK:
        return "Surut (Tugboat Tidak Bisa Masuk)"
    elif depth_val <= 8.0:
        return "Aman (Tugboat Bisa Beroperasi)"
    else:
        return "Siaga Banjir / Arus Deras"

def create_empty_template() -> pd.DataFrame:
    """Menghasilkan DataFrame kosong dengan struktur kolom standar"""
    return pd.DataFrame(columns=COLUMNS)

def fetch_gsheet_public() -> pd.DataFrame | None:
    """Mengambil data murni langsung dari Google Spreadsheet Online secara realtime"""
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{GSHEET_ID}/export?format=csv"
        req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            if len(content) > 5:
                df_raw = pd.read_csv(io.BytesIO(content), header=None)
                if not df_raw.empty and df_raw.shape[1] >= 8:
                    first_cell = str(df_raw.iloc[0, 0]).strip().lower()
                    second_cell = str(df_raw.iloc[0, 1]).strip().lower()
                    
                    # Cek apakah baris 0 adalah Header
                    if first_cell == "id" or "tanggal" in second_cell:
                        df = pd.read_csv(io.BytesIO(content))
                    else:
                        # Baris 0 adalah data langsung
                        df = df_raw.copy()
                        df.columns = COLUMNS[:df.shape[1]]
                    
                    # Normalisasi nilai desimal
                    if "Kedalaman Aktual (m)" in df.columns:
                        df["Kedalaman Aktual (m)"] = df["Kedalaman Aktual (m)"].apply(safe_float)
                    if "Plan Kedalaman (m)" in df.columns:
                        df["Plan Kedalaman (m)"] = df["Plan Kedalaman (m)"].apply(lambda x: safe_float(x, default=PLAN_BENCHMARK))
                    else:
                        df["Plan Kedalaman (m)"] = PLAN_BENCHMARK
                        
                    if "Tanggal" in df.columns:
                        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce").dt.strftime("%Y-%m-%d").fillna(df["Tanggal"].astype(str))
                        
                    return df
    except Exception as e:
        print(f"Error fetching Google Sheet: {e}")
        
    return None

def load_data() -> tuple[pd.DataFrame, str]:
    """
    Memuat data HANYA dari Google Spreadsheet Online (Database Tunggal).
    Tidak menyimpan atau membaca dari disk lokal.
    """
    gsheet_df = fetch_gsheet_public()
    if gsheet_df is not None and not gsheet_df.empty:
        return gsheet_df, "Google Spreadsheet Online (Database Tunggal)"
        
    return create_empty_template(), "Google Spreadsheet Online (Menunggu Data)"

def add_new_entry(entry_dict: dict) -> tuple[bool, str]:
    """
    Menambahkan baris data baru LANGSUNG ke Google Spreadsheet Online via Webhook Apps Script.
    Tidak ada penyimpanan lokal.
    """
    try:
        df, _ = load_data()
        
        # Tentukan ID urut berikutnya
        if not df.empty and "ID" in df.columns and pd.to_numeric(df["ID"], errors="coerce").notnull().any():
            max_id = int(pd.to_numeric(df["ID"], errors="coerce").dropna().max())
            new_id = max_id + 1
        else:
            new_id = 1
            
        entry_dict["ID"] = new_id
        entry_dict["Plan Kedalaman (m)"] = PLAN_BENCHMARK
        entry_dict["Status"] = determine_status(entry_dict.get("Kedalaman Aktual (m)", PLAN_BENCHMARK))
        
        # POST LANGSUNG ke Google Sheet via Webhook
        resp = requests.post(WEBHOOK_URL, json=entry_dict, timeout=12)
        if resp.status_code == 200:
            return True, f"Data berhasil disimpan langsung ke Google Spreadsheet online dengan ID #{new_id}!"
        else:
            return False, f"Gagal mengirim data ke Google Spreadsheet (Status Webhook: {resp.status_code})"
    except Exception as e:
        return False, f"Terjadi kesalahan saat menyimpan ke Google Spreadsheet: {str(e)}"

def calculate_analytics(df: pd.DataFrame) -> dict:
    """Menghitung metrik analisis, tren, dan deviasi tolak ukur 4.0m dengan aman"""
    if df.empty:
        return {
            "current_depth": 0.0,
            "prev_depth": 0.0,
            "delta_depth": 0.0,
            "current_plan": PLAN_BENCHMARK,
            "plan_deviation": 0.0,
            "avg_7d": 0.0,
            "min_depth": 0.0,
            "max_depth": 0.0,
            "trend_direction": "Stabil",
            "trend_slope": 0.0,
            "status_latest": "Surut (Tugboat Tidak Bisa Masuk)",
            "latest_date": str(datetime.now().date()),
            "latest_time": "00:00",
            "latest_location": "KM 0 Jetty Senyiur"
        }
    
    df_sorted = df.copy()
    
    # Sanitasi angka
    df_sorted["Kedalaman Aktual (m)"] = df_sorted["Kedalaman Aktual (m)"].apply(safe_float)
    if "Plan Kedalaman (m)" in df_sorted.columns:
        df_sorted["Plan Kedalaman (m)"] = df_sorted["Plan Kedalaman (m)"].apply(lambda x: safe_float(x, default=PLAN_BENCHMARK))
    else:
        df_sorted["Plan Kedalaman (m)"] = PLAN_BENCHMARK
        
    df_sorted["DateTimeStr"] = df_sorted["Tanggal"].astype(str) + " " + df_sorted["Waktu"].astype(str)
    df_sorted["DateTime"] = pd.to_datetime(df_sorted["DateTimeStr"], errors="coerce")
    df_sorted = df_sorted.sort_values(by="DateTime")
    
    latest = df_sorted.iloc[-1]
    current_depth = safe_float(latest.get("Kedalaman Aktual (m)"), default=0.0)
    current_plan = PLAN_BENCHMARK
    
    prev_depth = current_depth
    if len(df_sorted) > 1:
        prev_depth = safe_float(df_sorted.iloc[-2].get("Kedalaman Aktual (m)"), default=current_depth)
        
    delta_depth = round(current_depth - prev_depth, 2)
    plan_deviation = round(current_depth - PLAN_BENCHMARK, 2)
    
    tail_n = min(len(df_sorted), 21)
    tail_vals = df_sorted.tail(tail_n)["Kedalaman Aktual (m)"]
    avg_7d = round(float(tail_vals.mean()), 2) if not tail_vals.empty else current_depth
    min_depth = round(float(df_sorted["Kedalaman Aktual (m)"].min()), 2) if not df_sorted.empty else current_depth
    max_depth = round(float(df_sorted["Kedalaman Aktual (m)"].max()), 2) if not df_sorted.empty else current_depth
    
    trend_samples = df_sorted.tail(15)["Kedalaman Aktual (m)"].values
    if len(trend_samples) > 2:
        x = np.arange(len(trend_samples))
        slope, _ = np.polyfit(x, trend_samples, 1)
    else:
        slope = 0.0
        
    if slope > 0.05:
        trend_direction = "Menaik (Pasang / Debit Naik)"
    elif slope < -0.05:
        trend_direction = "Menurun (Surut)"
    else:
        trend_direction = "Stabil"
        
    return {
        "current_depth": current_depth,
        "prev_depth": prev_depth,
        "delta_depth": delta_depth,
        "current_plan": current_plan,
        "plan_deviation": plan_deviation,
        "avg_7d": avg_7d,
        "min_depth": min_depth,
        "max_depth": max_depth,
        "trend_direction": trend_direction,
        "trend_slope": round(float(slope), 3),
        "status_latest": latest.get("Status", determine_status(current_depth)),
        "latest_date": str(latest.get("Tanggal", datetime.now().date())),
        "latest_time": str(latest.get("Waktu", "00:00")),
        "latest_location": str(latest.get("Titik Pantau", "KM 0 Jetty Senyiur"))
    }
