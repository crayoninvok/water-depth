# 🌊 Aplikasi Monitoring Kedalaman Air Sungai Senyiur

Aplikasi berbasis **Python** dan **Streamlit** dengan **Database Tunggal Google Spreadsheet (Cloud)** untuk mencatat, menganalisis, dan memvisualisasikan kedalaman air sungai di **Senyiur**, Kutai Kartanegara, Kalimantan Timur.

---

## 🌟 Arsitektur Database Tunggal (Pure Cloud)

- **100% Google Spreadsheet Online**: Tidak ada data yang disimpan di drive lokal komputer (`@data`). Seluruh data tersimpan secara eksklusif di Google Spreadsheet.
- **Dual-Input Sinkron**:
  1. **Input via Web Streamlit**: Form input langsung mengirim data ke Google Spreadsheet melalui Google Apps Script Webhook.
  2. **Input via Google Sheet**: Pengguna dapat langsung mengetik atau mengedit data di spreadsheet melalui web browser atau aplikasi Google Sheets ponsel.
- **Tolak Ukur Tetap Operasional: 4,0 Meter**:
  - Kedalaman **< 4,0 m**: **Surut** (Tugboat **TIDAK BISA** masuk ke sungai).
  - Kedalaman **≥ 4,0 m**: **Aman** (Tugboat bisa masuk dan beroperasi lancar).
  - Kedalaman **> 8,0 m**: **Siaga Banjir / Arus Deras**.

---

## 🔗 Informasi Database Spreadsheet

- **Nama Spreadsheet**: Water Depth
- **Spreadsheet ID**: `1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4`
- **Tautan Google Spreadsheet**: [Buka Google Spreadsheet](https://docs.google.com/spreadsheets/d/1QfY81fyk-hLYEQNGyn1B__jngaeTkKblIO1YWnrwlW4/edit?usp=sharing)
- **Webhook Apps Script**: `https://script.google.com/macros/s/AKfycbwwFYKKp8q-6BFgJldMO1GCX1GeHviWa3dVbigrCoq22aebjVM7w6OyOE_yY6trRQE/exec`

---

## 📊 Fitur Analisis & Visualisasi

1. **Grafik Time-Series Interaktif (Plotly)**: Visualisasi kedalaman air aktual dari waktu ke waktu.
2. **Garis Tolak Ukur 4,0 m**: Garis batas referensi keselamatan tugboat dengan visualisasi zona aman dan surut.
3. **Analisis Tren (Trendline)**: Moving Average dan Linear Regression untuk memprediksi arah pasang-surut.
4. **Deviasi Tolak Ukur**: Indikator surplus/defisit kedalaman terhadap batas minimal 4.0 m.
5. **Ringkasan KPI Realtime**: Kedalaman terkini, perubahan dari pengukuran sebelumnya, rata-rata, nilai min/max, dan status navigasi tugboat.

---

## 🚀 Cara Menjalankan Aplikasi

### Opsi 1: Klik Ganda (Paling Mudah di Windows)
Klik ganda file:
👉 **`run_app.bat`**

### Opsi 2: Lewat Terminal / Command Prompt
```bash
# Masuk ke direktori
cd "d:\Data\06_Development App Batara\water-depth"

# Jalankan Streamlit dengan virtual environment
.\.venv\Scripts\streamlit run app.py
```
Aplikasi akan terbuka otomatis di browser pada: **`http://localhost:8501`** (atau port aktif lainnya).

---

## 📁 Struktur Berkas Proyek

```text
water-depth/
├── app.py                      # Antarmuka web Streamlit, visualisasi & form input
├── data_manager.py             # Modul integrasi langsung ke Google Spreadsheet & Webhook
├── requirements.txt            # Dependensi Python
├── run_app.bat                 # Launcher 1-klik untuk Windows
└── README.md                   # Dokumentasi sistem
```
*(Tidak ada folder penyimpanan lokal data)*
