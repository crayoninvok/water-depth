import os
import io
import base64
import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

import data_manager

# Helper Base64 Logo Loader
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_PATH = "assets/logo.png"
LOGO_B64 = get_base64_image(LOGO_PATH)

# ==========================================================
# KONFIGURASI HALAMAN STREAMLIT
# ==========================================================
st.set_page_config(
    page_title="Monitoring Kedalaman Air Senyiur — PT Batara Dharma Persada",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0d3b66 0%, #001e3d 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(13, 59, 102, 0.2);
    }
    
    .main-header h1 {
        color: #ffffff;
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: #b0c4de;
        margin: 6px 0 0 0;
        font-size: 0.95rem;
    }
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }
    
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 6px;
    }
    
    .metric-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    
    .metric-sub {
        font-size: 0.82rem;
        font-weight: 500;
        margin-top: 6px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        text-align: center;
    }
    
    .badge-normal {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }
    
    .badge-warning {
        background-color: #fef9c3;
        color: #854d0e;
        border: 1px solid #fde047;
    }
    
    .badge-danger {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    
    .badge-flood {
        background-color: #dbeafe;
        color: #1e40af;
        border: 1px solid #93c5fd;
    }
    
    .gsheet-box {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================================
# INISIALISASI & LOAD DATA (DATABASE TUNGGAL CLOUD)
# ==========================================================
df_raw, source_info = data_manager.load_data()

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width="stretch")
    else:
        st.markdown("### 🏢 **PT Batara Dharma Persada**")
        
    st.markdown("### 🌊 **Sungai Senyiur Monitoring**")
    st.caption("PT Batara Dharma Persada — Pemantauan Kedalaman Air & Tugboat")
    
    st.markdown("---")
    
    # Status Database Tunggal
    st.markdown("#### ☁️ **Database Tunggal (Cloud)**")
    st.success(f"🟢 **Sumber Data:**\n\n{source_info}")
    
    # Tombol Akses Langsung Google Sheet
    st.link_button("🌐 Buka Google Spreadsheet", data_manager.GSHEET_URL, width="stretch", type="primary")
    
    st.markdown(f"**Total Baris Data:** `{len(df_raw):,}` catatan")
    
    if st.button("🔄 Sync / Reload dari Google Sheet", width="stretch"):
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🔍 **Filter Tampilan Data**")

    st.markdown("📍 **Titik Pantau:** `KM 0 Jetty Senyiur`")
    
    df_raw["Tanggal_dt"] = pd.to_datetime(df_raw["Tanggal"], errors="coerce")
    valid_dates = df_raw["Tanggal_dt"].dropna()
    
    today = datetime.date.today()
    if not valid_dates.empty:
        try:
            raw_min = valid_dates.min()
            raw_max = valid_dates.max()
            min_date = raw_min.date() if pd.notna(raw_min) else (today - datetime.timedelta(days=30))
            max_date = raw_max.date() if pd.notna(raw_max) else today
        except Exception:
            min_date = today - datetime.timedelta(days=30)
            max_date = today
    else:
        min_date = today - datetime.timedelta(days=30)
        max_date = today
        
    if min_date > max_date:
        min_date = max_date
        
    date_range = st.date_input(
        "Rentang Tanggal:",
        value=(min_date, max_date),
        min_value=min_date - datetime.timedelta(days=365),
        max_value=max_date + datetime.timedelta(days=30)
    )
    
    status_options = ["Semua Status"] + sorted(list(df_raw["Status"].dropna().unique()))
    selected_status = st.selectbox("Status Kondisi:", status_options)

# ==========================================================
# FILTERING DATA
# ==========================================================
df_filtered = df_raw.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    if start_d and end_d:
        start_str = start_d.strftime("%Y-%m-%d")
        end_str = end_d.strftime("%Y-%m-%d")
        df_filtered = df_filtered[
            (df_filtered["Tanggal"].astype(str) >= start_str) & 
            (df_filtered["Tanggal"].astype(str) <= end_str)
        ]
elif isinstance(date_range, (datetime.date, tuple)):
    if isinstance(date_range, tuple) and len(date_range) == 1 and date_range[0]:
        start_str = date_range[0].strftime("%Y-%m-%d")
        df_filtered = df_filtered[df_filtered["Tanggal"].astype(str) >= start_str]
    elif isinstance(date_range, datetime.date):
        start_str = date_range.strftime("%Y-%m-%d")
        df_filtered = df_filtered[df_filtered["Tanggal"].astype(str) >= start_str]



if selected_status != "Semua Status":
    df_filtered = df_filtered[df_filtered["Status"] == selected_status]

analytics = data_manager.calculate_analytics(df_filtered if not df_filtered.empty else df_raw)

# ==========================================================
# MAIN HEADER
# ==========================================================
header_logo_tag = ""
if LOGO_B64:
    header_logo_tag = (
        f'<div style="background:#ffffff;padding:6px 14px;border-radius:12px;'
        f'box-shadow:0 4px 14px rgba(0,0,0,0.18);display:inline-flex;align-items:center;">'
        f'<img src="data:image/png;base64,{LOGO_B64}" style="height:44px;object-fit:contain;" alt="PT Batara Dharma Persada" />'
        f'</div>'
    )

header_html = (
    f'<div class="main-header">'
    f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">'
    f'<div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;">'
    f'{header_logo_tag}'
    f'<div>'
    f'<h1 style="color:#ffffff;margin:0;font-size:1.85rem;font-weight:800;letter-spacing:-0.5px;">🌊 Pemantauan Kedalaman Air Sungai Senyiur</h1>'
    f'<p style="color:#b0c4de;margin:4px 0 0 0;font-size:0.95rem;"><b>PT Batara Dharma Persada</b> — Tolak Ukur Tetap Operasional: <b>4,0 Meter</b> (Batas Minimum Tugboat Masuk)</p>'
    f'</div>'
    f'</div>'
    f'<div>'
    f'<span style="background:rgba(255,255,255,0.18);padding:8px 16px;border-radius:20px;font-size:0.88rem;font-weight:700;color:#ffffff;">'
    f'📍 KM 0 Jetty Senyiur'
    f'</span>'
    f'</div>'
    f'</div>'
    f'</div>'
)

st.markdown(header_html, unsafe_allow_html=True)

# ==========================================================
# KPI METRICS CARDS
# ==========================================================
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

latest_status = analytics["status_latest"]
badge_class = "badge-normal"
if "Kritis" in latest_status or "Surut" in latest_status or "Tidak Bisa" in latest_status:
    badge_class = "badge-danger"
elif "Waspada" in latest_status:
    badge_class = "badge-warning"
elif "Banjir" in latest_status:
    badge_class = "badge-flood"

with kpi1:
    delta_color = "#16a34a" if analytics["delta_depth"] >= 0 else "#dc2626"
    delta_symbol = "▲" if analytics["delta_depth"] >= 0 else "▼"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">📏 Kedalaman Terkini</div>
        <div class="metric-val">{analytics['current_depth']:.2f} <span style="font-size: 1rem; color:#64748b;">m</span></div>
        <div class="metric-sub" style="color: {delta_color};">
            {delta_symbol} {abs(analytics['delta_depth']):.2f} m vs pengukuran lalu
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    dev = analytics["plan_deviation"]
    dev_color = "#16a34a" if dev >= 0 else "#dc2626"
    dev_sign = "+" if dev >= 0 else ""
    sub_text = "Tugboat Aman Masuk" if dev >= 0 else "Tugboat Tidak Bisa Masuk"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">⚓ Tolak Ukur Tugboat</div>
        <div class="metric-val">4.00 <span style="font-size: 1rem; color:#64748b;">m</span></div>
        <div class="metric-sub" style="color: {dev_color}; font-weight: 700;">
            {dev_sign}{dev:.2f} m ({sub_text})
        </div>
    </div>
    """, unsafe_allow_html=True)


with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🚦 Status Operasional</div>
        <div style="margin-top: 4px; margin-bottom: 6px;">
            <span class="status-badge {badge_class}">{latest_status}</span>
        </div>
        <div class="metric-sub" style="color: #64748b;">
            {analytics.get('latest_date', '')} ({analytics.get('latest_time', '')})
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    tren_icon = "📈" if "Menaik" in analytics["trend_direction"] else ("📉" if "Menurun" in analytics["trend_direction"] else "➡️")
    tren_color = "#0284c7" if "Menaik" in analytics["trend_direction"] else ("#ea580c" if "Menurun" in analytics["trend_direction"] else "#475569")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">📊 Tren Kedalaman</div>
        <div class="metric-val" style="font-size: 1.35rem; color: {tren_color};">{tren_icon} {analytics['trend_direction'].split(' ')[0]}</div>
        <div class="metric-sub" style="color: #64748b;">
            Slope: {analytics['trend_slope']:+.2f} m/interval
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">📐 Rata-rata & Rentang</div>
        <div class="metric-val">{analytics['avg_7d']:.2f} <span style="font-size: 1rem; color:#64748b;">m</span></div>
        <div class="metric-sub" style="color: #64748b;">
            Min: <b>{analytics['min_depth']:.2f}m</b> | Max: <b>{analytics['max_depth']:.2f}m</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ==========================================================
# MAIN TABS NAVIGATION
# ==========================================================
tab_viz, tab_input, tab_table, tab_settings = st.tabs([
    "📈 Visualisasi, Tren & Plan Air",
    "📝 Input Data Kedalaman Baru",
    "📋 Tabel & Riwayat Spreadsheet",
    "⚙️ Database & Koneksi Google Sheet"
])

# ==========================================================
# TAB 1: VISUALISASI, TREN & PLAN AIR
# ==========================================================
with tab_viz:
    st.markdown("### 📊 Analisis Grafik Kedalaman Sungai Senyiur")
    
    with st.expander("🛠️ Opsi Tampilan Grafik (Model Grafik, Tolak Ukur & Garis Tren)", expanded=False):
        c_opt0, c_opt1, c_opt2, c_opt3, c_opt4 = st.columns([1.5, 1.2, 1, 1, 1.3])
        with c_opt0:
            chart_type = st.radio("Model Visualisasi:", ["📊 Bar Chart (Diagram Batang)", "📈 Line Chart (Garis)"], index=0, horizontal=True)
        with c_opt1:
            show_benchmark = st.checkbox("Tolak Ukur 4.0m (Tugboat)", value=True)
        with c_opt2:
            show_trend = st.checkbox("Tampilkan Garis Tren", value=True)
        with c_opt3:
            show_zones = st.checkbox("Zona Keselamatan", value=True)
        with c_opt4:
            trend_type = st.radio("Tipe Tren:", ["Moving Average (7 Hari)", "Regresi Linier"], horizontal=True)

    if df_filtered.empty:
        st.warning("⚠️ Tidak ada data untuk kriteria filter yang dipilih. Silakan reset filter di sidebar.")
    else:
        df_plot = df_filtered.copy()
        df_plot["DateTimeStr"] = df_plot["Tanggal"].astype(str) + " " + df_plot["Waktu"].astype(str)
        df_plot["DateTime"] = pd.to_datetime(df_plot["DateTimeStr"], errors="coerce")
        df_plot = df_plot.sort_values(by="DateTime")
        
        df_plot["Kedalaman Aktual (m)"] = df_plot["Kedalaman Aktual (m)"].apply(lambda x: data_manager.safe_float(x, default=0.0))
        if "Plan Kedalaman (m)" in df_plot.columns:
            df_plot["Plan Kedalaman (m)"] = df_plot["Plan Kedalaman (m)"].apply(lambda x: data_manager.safe_float(x, default=data_manager.PLAN_BENCHMARK))
        else:
            df_plot["Plan Kedalaman (m)"] = data_manager.PLAN_BENCHMARK
            
        df_plot["MA_7d"] = df_plot["Kedalaman Aktual (m)"].rolling(window=7, min_periods=1).mean()

        
        x_numeric = np.arange(len(df_plot))
        if len(df_plot) > 1:
            poly_fit = np.polyfit(x_numeric, df_plot["Kedalaman Aktual (m)"], 1)
            df_plot["Trend_Linear"] = np.polyval(poly_fit, x_numeric)
        else:
            df_plot["Trend_Linear"] = df_plot["Kedalaman Aktual (m)"]
            
        fig = go.Figure()
        
        # 1. Zona Keselamatan (Background Thresholds)
        if show_zones:
            # Zona Surut: < 4.0m (Tugboat Tidak Bisa Masuk)
            fig.add_hrect(
                y0=0, y1=4.0,
                fillcolor="#fee2e2", opacity=0.45,
                layer="below", line_width=0,
                annotation_text="🔴 Zona Surut (< 4.0m) — Tugboat TIDAK BISA MASUK",
                annotation_position="bottom right",
                annotation_font_size=11,
                annotation_font_color="#991b1b"
            )
            # Zona Aman / Operasional: 4.0m - 8.0m (Tugboat Bisa Masuk)
            fig.add_hrect(
                y0=4.0, y1=8.0,
                fillcolor="#dcfce7", opacity=0.35,
                layer="below", line_width=0,
                annotation_text="🟢 Zona Operasional (4.0m - 8.0m) — Tugboat AMAN MASUK & BEROPERASI",
                annotation_position="top right",
                annotation_font_size=11,
                annotation_font_color="#166534"
            )
            # Zona Siaga Banjir: > 8.0m
            fig.add_hrect(
                y0=8.0, y1=14.0,
                fillcolor="#dbeafe", opacity=0.45,
                layer="below", line_width=0,
                annotation_text="🔵 Zona Siaga Banjir (> 8.0m) — Debit & Arus Kuat",
                annotation_position="top right",
                annotation_font_size=11,
                annotation_font_color="#1e40af"
            )
        
        # Penentuan Warna Batang Berdasarkan Ambang Batas 4.0m
        bar_colors = []
        bar_borders = []
        for val in df_plot["Kedalaman Aktual (m)"]:
            if val < 4.0:
                bar_colors.append("#ef4444")    # Merah: Surut (< 4.0m)
                bar_borders.append("#b91c1c")
            elif val <= 8.0:
                bar_colors.append("#10b981")   # Hijau: Aman (4.0 - 8.0m)
                bar_borders.append("#047857")
            else:
                bar_colors.append("#3b82f6")   # Biru: Siaga Banjir (> 8.0m)
                bar_borders.append("#1d4ed8")

        # 2. Trace Kedalaman Aktual (Bar Chart atau Line Chart)
        if "Bar Chart" in chart_type:
            bar_kwargs = {}
            if len(df_plot) == 1:
                bar_kwargs["width"] = [86400000 * 0.4]
                
            fig.add_trace(go.Bar(
                x=df_plot["DateTime"],
                y=df_plot["Kedalaman Aktual (m)"],
                name="Kedalaman Aktual (m)",
                marker=dict(
                    color=bar_colors,
                    line=dict(color=bar_borders, width=1.5),
                    opacity=0.9
                ),
                text=[f"{v:.2f} m" for v in df_plot["Kedalaman Aktual (m)"]],
                textposition="outside",
                textfont=dict(size=12, color="#0f172a"),
                hovertemplate=(
                    "<b>Tanggal & Jam:</b> %{x|%Y-%m-%d %H:%M}<br>" +
                    "<b>Kedalaman Aktual:</b> %{y:.2f} m<br>" +
                    "<b>Status:</b> %{customdata[0]}<br>" +
                    "<b>Titik:</b> %{customdata[1]}<br>" +
                    "<b>Karyawan Input:</b> %{customdata[2]}<br>" +
                    "<b>Keterangan:</b> %{customdata[3]}<extra></extra>"
                ),
                customdata=df_plot[["Status", "Titik Pantau", "Petugas", "Keterangan"]].values,
                **bar_kwargs
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df_plot["DateTime"],
                y=df_plot["Kedalaman Aktual (m)"],
                mode="lines+markers",
                name="Kedalaman Aktual (m)",
                line=dict(color="#0284c7", width=3),
                marker=dict(size=8, color="#0369a1", symbol="circle"),
                hovertemplate=(
                    "<b>Tanggal & Jam:</b> %{x|%Y-%m-%d %H:%M}<br>" +
                    "<b>Kedalaman Aktual:</b> %{y:.2f} m<br>" +
                    "<b>Status:</b> %{customdata[0]}<br>" +
                    "<b>Titik:</b> %{customdata[1]}<br>" +
                    "<b>Karyawan Input:</b> %{customdata[2]}<br>" +
                    "<b>Keterangan:</b> %{customdata[3]}<extra></extra>"
                ),
                customdata=df_plot[["Status", "Titik Pantau", "Petugas", "Keterangan"]].values
            ))
        
        # 3. Garis Tolak Ukur 4.0m
        if show_benchmark:
            fig.add_hline(
                y=4.0,
                line_dash="dash",
                line_color="#dc2626",
                line_width=2.5,
                annotation_text="⚓ TOLAK UKUR: Batas Minimum Tugboat Masuk (4.0 m)",
                annotation_position="top left",
                annotation_font_color="#dc2626",
                annotation_font_size=11
            )
            
        # 4. Garis Tren (Superimposed Line Trace)
        if show_trend:
            if "Moving Average" in trend_type:
                fig.add_trace(go.Scatter(
                    x=df_plot["DateTime"],
                    y=df_plot["MA_7d"],
                    mode="lines+markers",
                    name="Tren Moving Average (7 Hari)",
                    line=dict(color="#f59e0b", width=3.5, dash="dash"),
                    marker=dict(size=7, color="#d97706", symbol="diamond"),
                    hovertemplate="<b>Tren MA:</b> %{y:.2f} m<extra></extra>"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=df_plot["DateTime"],
                    y=df_plot["Trend_Linear"],
                    mode="lines+markers",
                    name="Tren Regresi Linier",
                    line=dict(color="#db2777", width=3.5, dash="dash"),
                    marker=dict(size=7, color="#be185d", symbol="square"),
                    hovertemplate="<b>Garis Regresi:</b> %{y:.2f} m<extra></extra>"
                ))
                
        y_max = max(10.0, df_plot["Kedalaman Aktual (m)"].max() + 1.8)
        
        xaxis_config = dict(
            title="Tanggal & Waktu Pengukuran",
            showgrid=True,
            gridcolor="#f1f5f9",
            tickformat="%d %b\n%H:%M"
        )
        if len(df_plot) == 1 and "Bar Chart" in chart_type:
            dt0 = df_plot["DateTime"].iloc[0]
            if pd.notna(dt0):
                xaxis_config["range"] = [dt0 - pd.Timedelta(days=1), dt0 + pd.Timedelta(days=1)]
                
        fig.update_layout(
            title=dict(
                text="<b>Grafik Kedalaman Air Sungai Senyiur (Bar Chart & Tren) vs Tolak Ukur Tugboat (4.0 m)</b>",
                font=dict(size=17, color="#0f172a")
            ),
            xaxis=xaxis_config,
            yaxis=dict(
                title="Kedalaman Air (meter)",
                showgrid=True,
                gridcolor="#f1f5f9",
                range=[0, y_max],
                dtick=1.0
            ),
            bargap=0.3,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#e2e8f0",
                borderwidth=1
            ),
            margin=dict(l=40, r=40, t=60, b=40),
            height=520,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, width="stretch")
        
        # Deviasi terhadap Tolak Ukur 4.0m & Distribusi Status
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.markdown("#### ⚖️ Deviasi Kedalaman terhadap Batas 4.0m")
            st.caption("Selisih kedalaman air terhadap batas tolak ukur masuk tugboat (4,0 meter). Negatif = Air Surut (Tugboat Tidak Bisa Masuk).")
            
            df_plot["Deviasi"] = df_plot["Kedalaman Aktual (m)"] - 4.0
            df_plot["Color_Dev"] = np.where(df_plot["Deviasi"] >= 0, "#10b981", "#ef4444")
            
            fig_dev = go.Figure()
            fig_dev.add_trace(go.Bar(
                x=df_plot["DateTime"],
                y=df_plot["Deviasi"],
                marker_color=df_plot["Color_Dev"],
                name="Deviasi vs 4.0m",
                hovertemplate="Tanggal: %{x|%Y-%m-%d %H:%M}<br>Deviasi: %{y:+.2f} m<extra></extra>"
            ))
            fig_dev.add_hline(y=0, line_dash="solid", line_color="#334155", line_width=1)
            fig_dev.update_layout(
                yaxis_title="Deviasi vs 4.0m (meter)",
                xaxis_title="Tanggal",
                margin=dict(l=30, r=30, t=30, b=30),
                height=320,
                template="plotly_white"
            )
            st.plotly_chart(fig_dev, width="stretch")
            
        with col_c2:
            st.markdown("#### 📊 Distribusi Status Operasional Tugboat")
            st.caption("Proporsi kondisi izin masuk dan operasi tugboat di alur Senyiur.")
            
            status_counts = df_plot["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Jumlah"]
            
            color_map = {
                "Aman (Tugboat Bisa Beroperasi)": "#22c55e",
                "Aman / Normal": "#22c55e",
                "Surut (Tugboat Tidak Bisa Masuk)": "#ef4444",
                "Kritis / Surut": "#ef4444",
                "Siaga Banjir / Arus Deras": "#3b82f6",
                "Siaga Banjir": "#3b82f6"
            }
            colors = [color_map.get(s, "#94a3b8") for s in status_counts["Status"]]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=status_counts["Status"],
                values=status_counts["Jumlah"],
                hole=0.45,
                marker=dict(colors=colors),
                textinfo="label+percent",
                insidetextorientation="radial"
            )])
            fig_pie.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=320,
                showlegend=False,
                template="plotly_white"
            )
            st.plotly_chart(fig_pie, width="stretch")

        # Status Operasional & Rekomendasi Navigasi Tugboat
        curr_d = analytics['current_depth']
        st.markdown("### 💡 Status Operasional & Rekomendasi Tugboat")
        if curr_d < 4.0:
            st.error(f"""
            **🚨 PERINGATAN SURUT — TUGBOAT TIDAK BISA MASUK KE SUNGAI ({curr_d:.2f} m < 4,0 m):**
            - Kedalaman air sungai saat ini **{curr_d:.2f} meter**, berada di bawah tolak ukur minimum operasional **4,0 Meter** (Deviasi: **{curr_d - 4.0:+.2f} m**).
            - **Status Armada:** Tugboat **TIDAK BISA MASUK** ke alur sungai Senyiur karena kondisi surut dan berisiko tinggi kandas.
            - **Instruksi:** Hentikan rencana pelayaran masuk alur, tunggu elevasi pasang air sungai naik mencapai minimal **4,0 Meter**.
            """)
        elif curr_d <= 8.0:
            st.success(f"""
            **✅ KONDISI AMAN — TUGBOAT BISA MASUK & BEROPERASI ({curr_d:.2f} m >= 4,0 m):**
            - Kedalaman air sungai saat ini **{curr_d:.2f} meter** (memenuhi tolak ukur ≥ 4,0 meter).
            - **Status Armada:** Tugboat dan tongkang **BISA MASUK** dan berlayar secara aman di alur sungai Senyiur.
            """)
        else:
            st.info(f"""
            **🌊 SIAGA BANJIR / ARUS DERAS ({curr_d:.2f} m > 8,0 m):**
            - Debit air sungai Senyiur tinggi. Tugboat dapat melintas tetapi wajib mewaspadai kecepatan arus deras dan kayu hanyut dari hulu.
            """)



# ==========================================================
# TAB 2: INPUT DATA BARU VIA WEB FORM
# ==========================================================
with tab_input:
    st.markdown("### 📝 Form Pencatatan Kedalaman Air Sungai")
    st.markdown("""
    Input data melalui form ini akan **langsung tersimpan ke database Spreadsheet** 
    dan otomatis memperbarui tabel serta grafik visualisasi.
    """)
    
    with st.container():
        with st.form("form_input_kedalaman", clear_on_submit=True):
            st.markdown("##### 📌 Informasi Waktu & Lokasi")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                input_tgl = st.date_input("📅 Tanggal Pengukuran", value=datetime.date.today())
            with col_f2:
                jam_default = datetime.datetime.now().strftime("%H:%M")
                input_waktu = st.text_input("⏰ Jam / Waktu (HH:MM)", value=jam_default)
            with col_f3:
                input_titik = st.text_input(
                    "📍 Titik Pantau",
                    value="KM 0 Jetty Senyiur",
                    disabled=True,
                    help="Titik pantau tunggal operasional sungai Senyiur."
                )
                
            st.markdown("##### 📐 Parameter Kedalaman Air")
            st.info("⚓ **Tolak Ukur Tetap Operasional:** **4,0 Meter**. Di bawah 4,0 meter tugboat tidak bisa masuk ke sungai karena surut. Anda tidak perlu menginput plan, tolak ukur sudah otomatis 4,0 m.")
            
            col_f4, col_f5 = st.columns(2)
            with col_f4:
                input_aktual = st.number_input(
                    "📏 Kedalaman Aktual Hasil Pengukuran (meter) *",
                    min_value=0.2, max_value=25.0, value=1.20, step=0.05, format="%.2f",
                    help="Tinggi muka air sungai hasil pengukuran langsung di tiang ukur (peilskal)"
                )
            with col_f5:
                auto_status = data_manager.determine_status(input_aktual)
                status_choices = [
                    "Surut (Tugboat Tidak Bisa Masuk)",
                    "Aman (Tugboat Bisa Beroperasi)",
                    "Siaga Banjir / Arus Deras"
                ]
                input_status = st.selectbox(
                    "🚦 Status Operasional Tugboat (Otomatis)",
                    status_choices,
                    index=status_choices.index(auto_status) if auto_status in status_choices else 0
                )
                
            st.markdown("##### 👤 Karyawan Input & Catatan Lapangan")
            col_f7, col_f8 = st.columns([1, 2])
            with col_f7:
                input_petugas = st.text_input("👤 Nama Karyawan Input *", value="Dzaky")
            with col_f8:
                input_ket = st.text_input("📝 Catatan Lapangan / Keterangan", value="Kondisi air sungai masih surut, tugboat belum bisa masuk ke sungai.", placeholder="Contoh: Arus stabil, aman untuk navigasi.")

                
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button("💾 Simpan Data ke Spreadsheet", width="stretch", type="primary")
            
            if submit_btn:
                if not input_petugas.strip():
                    st.error("Nama karyawan input wajib diisi!")
                else:
                    new_entry = {
                        "Tanggal": input_tgl.strftime("%Y-%m-%d"),
                        "Waktu": input_waktu.strip(),
                        "Titik Pantau": input_titik,
                        "Kedalaman Aktual (m)": float(input_aktual),
                        "Plan Kedalaman (m)": 4.00,
                        "Status": input_status,
                        "Petugas": input_petugas.strip(),
                        "Keterangan": input_ket.strip() if input_ket.strip() else "Tidak ada catatan khusus."
                    }
                    
                    success, msg = data_manager.add_new_entry(new_entry)
                    if success:
                        st.success(f"🎉 **{msg}**")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")



# ==========================================================
# TAB 3: TABEL DATA & RIWAYAT SPREADSHEET
# ==========================================================
with tab_table:
    st.markdown("### 📋 Tabel Riwayat Data Kedalaman Air")
    st.markdown("Seluruh data yang tersimpan di database Spreadsheet.")
    
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        search_query = st.text_input("🔍 Cari berdasarkan Nama Karyawan, Titik, atau Keterangan:", placeholder="Ketik kata kunci...")
    with col_t2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.caption(f"Menampilkan **{len(df_filtered)}** dari **{len(df_raw)}** data")
        
    df_display = df_filtered.copy()
    if search_query:
        mask = (
            df_display["Petugas"].astype(str).str.contains(search_query, case=False, na=False) |
            df_display["Titik Pantau"].astype(str).str.contains(search_query, case=False, na=False) |
            df_display["Keterangan"].astype(str).str.contains(search_query, case=False, na=False) |
            df_display["Status"].astype(str).str.contains(search_query, case=False, na=False)
        )
        df_display = df_display[mask]
        
    if not df_display.empty and "Tanggal" in df_display.columns:
        df_display = df_display.sort_values(by=["Tanggal", "Waktu"], ascending=[False, False])
        
    if not df_display.empty and "ID" in df_display.columns:
        df_display["ID"] = pd.to_numeric(df_display["ID"], errors="coerce").fillna(1).astype(int)
        
    st.dataframe(
        df_display[[col for col in data_manager.COLUMNS if col in df_display.columns]],
        width="stretch",
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", format="%d", width="small"),
            "Tanggal": st.column_config.TextColumn("Tanggal", width="medium"),
            "Waktu": st.column_config.TextColumn("Waktu", width="small"),
            "Titik Pantau": st.column_config.TextColumn("Titik Pantau", width="medium"),
            "Kedalaman Aktual (m)": st.column_config.NumberColumn("Aktual (m)", format="%.2f m", width="small"),
            "Plan Kedalaman (m)": st.column_config.NumberColumn("Plan (m)", format="%.2f m", width="small"),
            "Status": st.column_config.TextColumn("Status Kondisi", width="medium"),
            "Petugas": st.column_config.TextColumn("Nama Karyawan Input", width="medium"),
            "Keterangan": st.column_config.TextColumn("Keterangan", width="large")
        }
    )
    with st.expander("ℹ️ Kelola / Edit / Hapus Baris di Google Spreadsheet"):
        st.info(
            f"Karena seluruh data tersimpan pada **Database Tunggal Google Spreadsheet Online**, "
            f"Anda dapat mengedit, menambah, atau menghapus baris data secara langsung di "
            f"[**Google Spreadsheet Anda**]({data_manager.GSHEET_URL}). "
            f"Setelah mengedit, klik tombol **'🔄 Sync / Reload dari Google Sheet'** di sidebar untuk memperbarui tampilan web."
        )
        st.link_button("🌐 Buka Spreadsheet untuk Edit / Hapus Baris", data_manager.GSHEET_URL, width="stretch", type="primary")


# ==========================================================
# TAB 4: DATABASE TUNGGAL GOOGLE SPREADSHEET
# ==========================================================
with tab_settings:
    st.markdown("### ☁️ Database Tunggal: Google Spreadsheet")
    st.markdown("""
    Aplikasi ini beroperasi dengan **arsitektur database tunggal berbasis cloud**:
    - **Tidak ada file data yang disimpan di komputer lokal**.
    - Seluruh pencatatan dan riwayat tersimpan langsung di **Google Spreadsheet Online**.
    - Sinkronisasi berjalan secara realtime 2-arah.
    """)
    
    st.markdown(f"""
    <div class="gsheet-box">
        <h4 style="margin: 0 0 8px 0; color: #166534;">🟢 Google Spreadsheet Aktif (Database Utama)</h4>
        <p style="margin: 0; color: #334155; font-size: 0.95rem;">
            Nama Spreadsheet: <b>Water Depth</b><br>
            Sheet ID: <code>{data_manager.GSHEET_ID}</code><br>
            Link Langsung: <b><a href="{data_manager.GSHEET_URL}" target="_blank">{data_manager.GSHEET_URL}</a></b>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### 🔗 1. Akses Langsung Spreadsheet")
        st.markdown("Buka dan edit data langsung melalui browser Google Sheets:")
        st.link_button("🌐 Buka Google Spreadsheet di Tab Baru", data_manager.GSHEET_URL, width="stretch", type="primary")
        
        st.markdown("##### 📌 Struktur Kolom Resmi:")
        for idx, col in enumerate(data_manager.COLUMNS, 1):
            st.markdown(f"{idx}. `{col}`")
            
    with col_g2:
        st.markdown("#### ⚡ 2. Status Webhook Sinkronisasi Realtime")
        st.success("🟢 **Google Apps Script Webhook: AKTIF**\n\nInput dari form web otomatis masuk ke baris baru Google Sheet tanpa perantara lokal.")
        st.code(data_manager.WEBHOOK_URL, language="text")
        
        st.markdown("##### 🔄 Cara Kerja Alur Data:")
        st.markdown("""
        1. **Input via Web:** Petugas mengisi data di web ➡️ otomatis di-POST ke Google Apps Script ➡️ masuk ke Google Sheet.
        2. **Input via Sheet:** Petugas mengetik di Google Sheet ➡️ aplikasi web membaca langsung dari Google Sheet via live API.
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 10px 0;">
    🌊 <b>Sistem Pemantauan Kedalaman Air Sungai Senyiur</b> — <b>PT Batara Dharma Persada</b> | Database Tunggal Google Spreadsheet
</div>
""", unsafe_allow_html=True)

