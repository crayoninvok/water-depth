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
    page_title="Monitoring Kedalaman Air Sungai — PT Batara Dharma Persada",
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
# INISIALISASI & LOAD DATA KEDUA JETTY (SENYIUR & MUARA PAHU)
# ==========================================================
df_senyiur_raw, info_senyiur = data_manager.load_data("senyiur")
df_muara_raw, info_muara = data_manager.load_data("muara_pahu")

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width="stretch")
    else:
        st.markdown("### 🏢 **PT Batara Dharma Persada**")
        
    st.markdown("---")
    st.markdown("### 📍 **Tampilan Lokasi Monitoring:**")
    view_mode = st.radio(
        "Pilih Mode Tampilan Grafik:",
        [
            "🌊 Tampilkan Kedua Jetty (Senyiur & Muara Pahu)",
            "🌊 Hanya Jetty Senyiur",
            "🌊 Hanya Jetty Muara Pahu"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("#### ☁️ **Database Spreadsheet**")
    st.caption("Penyimpanan Tunggal Cloud Google Sheets:")
    st.markdown(f"• **Tab Senyiur:** `{len(df_senyiur_raw):,}` baris data")
    st.markdown(f"• **Tab Muara Pahu:** `{len(df_muara_raw):,}` baris data")
    
    c_sb1, c_sb2 = st.columns(2)
    with c_sb1:
        st.link_button("🌐 Tab Senyiur", f"{data_manager.GSHEET_URL}#gid={data_manager.JETTY_CONFIG['senyiur']['sheet_gid']}", width="stretch")
    with c_sb2:
        st.link_button("🌐 Tab Muara Pahu", f"{data_manager.GSHEET_URL}#gid={data_manager.JETTY_CONFIG['muara_pahu']['sheet_gid']}", width="stretch")
        
    if st.button("🔄 Sync / Reload dari Google Sheet", width="stretch"):
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🔍 **Filter Tampilan Data**")

    # Ambil rentang tanggal gabungan
    all_dates = []
    for d in [df_senyiur_raw, df_muara_raw]:
        if not d.empty and "Tanggal" in d.columns:
            d_dt = pd.to_datetime(d["Tanggal"], errors="coerce").dropna()
            all_dates.extend(d_dt.tolist())
            
    today = datetime.date.today()
    if all_dates:
        min_date = min(all_dates).date()
        max_date = max(all_dates).date()
    else:
        min_date = today - datetime.timedelta(days=30)
        max_date = today

    if min_date > max_date:
        min_date = max_date

    date_range = st.date_input(
        "Rentang Tanggal Pengukuran:",
        value=(min_date, max_date),
        min_value=min_date - datetime.timedelta(days=365),
        max_value=max_date + datetime.timedelta(days=30)
    )
    
    all_statuses = set()
    for d in [df_senyiur_raw, df_muara_raw]:
        if not d.empty and "Status" in d.columns:
            all_statuses.update(d["Status"].dropna().unique())
            
    status_options = ["Semua Status"] + sorted(list(all_statuses))
    selected_status = st.selectbox("Status Kondisi:", status_options)

# ==========================================================
# FILTERING DATA
# ==========================================================
def apply_filters(df, d_range, s_status):
    if df.empty or "Tanggal" not in df.columns:
        return df.copy()
    dff = df.copy()
    if isinstance(d_range, tuple) and len(d_range) == 2:
        start_d, end_d = d_range
        if start_d and end_d:
            start_str = start_d.strftime("%Y-%m-%d")
            end_str = end_d.strftime("%Y-%m-%d")
            dff = dff[(dff["Tanggal"].astype(str) >= start_str) & (dff["Tanggal"].astype(str) <= end_str)]
    elif isinstance(d_range, (datetime.date, tuple)):
        if isinstance(d_range, tuple) and len(d_range) == 1 and d_range[0]:
            start_str = d_range[0].strftime("%Y-%m-%d")
            dff = dff[dff["Tanggal"].astype(str) >= start_str]
        elif isinstance(d_range, datetime.date):
            start_str = d_range.strftime("%Y-%m-%d")
            dff = dff[dff["Tanggal"].astype(str) >= start_str]
            
    if s_status != "Semua Status" and "Status" in dff.columns:
        dff = dff[dff["Status"] == s_status]
    return dff

df_senyiur = apply_filters(df_senyiur_raw, date_range, selected_status)
df_muara = apply_filters(df_muara_raw, date_range, selected_status)

an_senyiur = data_manager.calculate_analytics(df_senyiur if not df_senyiur.empty else df_senyiur_raw, jetty_key="senyiur")
an_muara = data_manager.calculate_analytics(df_muara if not df_muara.empty else df_muara_raw, jetty_key="muara_pahu")

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
    f'<h1 style="color:#ffffff;margin:0;font-size:1.85rem;font-weight:800;letter-spacing:-0.5px;">🌊 Pemantauan Kedalaman Air Sungai Batara</h1>'
    f'<p style="color:#b0c4de;margin:4px 0 0 0;font-size:0.95rem;"><b>PT Batara Dharma Persada</b> — Monitoring Terpadu <b>Jetty Senyiur</b> & <b>Jetty Muara Pahu</b> | Tolak Ukur Tetap Operasional: <b>4.0 Meter</b> (Batas Tugboat Masuk)</p>'
    f'</div>'
    f'</div>'
    f'<div style="display:flex;gap:10px;flex-wrap:wrap;">'
    f'<span style="background:rgba(255,255,255,0.18);padding:6px 14px;border-radius:20px;font-size:0.85rem;font-weight:700;color:#ffffff;">📍 KM 0 Jetty Senyiur</span>'
    f'<span style="background:rgba(255,255,255,0.18);padding:6px 14px;border-radius:20px;font-size:0.85rem;font-weight:700;color:#ffffff;">📍 Jetty Muara Pahu</span>'
    f'</div>'
    f'</div>'
    f'</div>'
)
st.markdown(header_html, unsafe_allow_html=True)

# RINGKASAN STATUS KEDUA JETTY
col_ex1, col_ex2 = st.columns(2)
with col_ex1:
    c_s_color = "#16a34a" if an_senyiur["current_depth"] >= 4.0 else "#dc2626"
    st.markdown(f"""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-left:5px solid #0284c7;padding:12px 16px;border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,0.04);margin-bottom:18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="font-weight:800;color:#0f172a;font-size:1.05rem;">🌊 Jetty Senyiur (Sungai Senyiur)</span>
                <div style="color:#64748b;font-size:0.85rem;">KM 0 Jetty Senyiur | Tab: <b>Senyiur</b> ({len(df_senyiur_raw)} baris data)</div>
            </div>
            <span style="font-size:1.45rem;font-weight:800;color:{c_s_color};">
                {an_senyiur['current_depth']:.2f} m
            </span>
        </div>
        <div style="margin-top:6px;font-size:0.85rem;color:#334155;display:flex;justify-content:space-between;border-top:1px dashed #f1f5f9;padding-top:6px;">
            <span>Tolak Ukur Tugboat: <b>4,00 m</b> (Deviasi: <b>{an_senyiur['plan_deviation']:+.2f} m</b>)</span>
            <span style="font-weight:700;color:{'#16a34a' if 'Aman' in an_senyiur['status_latest'] else '#dc2626'};">{an_senyiur['status_latest']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_ex2:
    if df_muara_raw.empty:
        c_m_color = "#94a3b8"
        val_str = "- m"
        stat_str = "Menunggu Data Input"
    else:
        c_m_color = "#16a34a" if an_muara["current_depth"] >= 4.0 else "#dc2626"
        val_str = f"{an_muara['current_depth']:.2f} m"
        stat_str = an_muara["status_latest"]
        
    st.markdown(f"""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-left:5px solid #0284c7;padding:12px 16px;border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,0.04);margin-bottom:18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="font-weight:800;color:#0f172a;font-size:1.05rem;">🌊 Jetty Muara Pahu (Sungai Muara Pahu)</span>
                <div style="color:#64748b;font-size:0.85rem;">Jetty Muara Pahu | Tab: <b>Muara Pahu</b> ({len(df_muara_raw)} baris data)</div>
            </div>
            <span style="font-size:1.45rem;font-weight:800;color:{c_m_color};">
                {val_str}
            </span>
        </div>
        <div style="margin-top:6px;font-size:0.85rem;color:#334155;display:flex;justify-content:space-between;border-top:1px dashed #f1f5f9;padding-top:6px;">
            <span>Tolak Ukur Tugboat: <b>4,00 m</b> (Deviasi: <b>{an_muara['plan_deviation']:+.2f} m</b>)</span>
            <span style="font-weight:700;color:{'#16a34a' if 'Aman' in stat_str else ('#64748b' if df_muara_raw.empty else '#dc2626')};">{stat_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================================
# MAIN TABS NAVIGATION
# ==========================================================
tab_viz, tab_input, tab_table, tab_settings = st.tabs([
    "📈 Visualisasi & Tren Grafik Air",
    "📝 Input Data Kedalaman Baru",
    "📋 Tabel & Riwayat Spreadsheet",
    "⚙️ Database & Koneksi Google Sheet"
])

# ==========================================================
# FUNGSI RENDER DASHBOARD LOKASI JETTY (GRAFIK, KPI & ANALISIS)
# ==========================================================
def render_jetty_dashboard_section(
    jetty_key: str,
    df_data: pd.DataFrame,
    df_full: pd.DataFrame,
    chart_type: str,
    show_benchmark: bool,
    show_trend: bool,
    show_zones: bool,
    trend_type: str,
    scale_mode: str,
    color_mode: str = "🔴 Seragam Merah Batara (Persis Senyiur)"
):
    cfg = data_manager.JETTY_CONFIG[jetty_key]
    analytics = data_manager.calculate_analytics(df_data if not df_data.empty else df_full, jetty_key=jetty_key)
    
    badge_bg = "#e0f2fe"
    badge_col = "#0369a1"
    accent_bar = "#0284c7"
    
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;background:#ffffff;padding:12px 18px;border-radius:12px;border:1px solid #e2e8f0;border-left:5px solid {accent_bar};margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,0.03);">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.6rem;">{cfg['icon']}</span>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:1.2rem;font-weight:700;">{cfg['name']} — Pemantauan Kedalaman {cfg['river']}</h3>
                <span style="color:#64748b;font-size:0.85rem;">Tab Database: <b>{cfg['sheet_name']}</b> | Tolak Ukur Tetap Operasional Tugboat: <b>{cfg['plan_benchmark']:.1f} m</b></span>
            </div>
        </div>
        <div>
            <span style="background:{badge_bg};color:{badge_col};padding:6px 14px;border-radius:20px;font-size:0.85rem;font-weight:700;">
                📍 {cfg['titik_pantau']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI 5 Cards
    k1, k2, k3, k4, k5 = st.columns(5)
    latest_status = analytics["status_latest"]
    badge_class = "badge-normal"
    if "Kritis" in latest_status or "Surut" in latest_status or "Tidak Bisa" in latest_status:
        badge_class = "badge-danger"
    elif "Waspada" in latest_status:
        badge_class = "badge-warning"
    elif "Banjir" in latest_status:
        badge_class = "badge-flood"

    with k1:
        if df_data.empty:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-title">📏 Kedalaman Terkini</div>
                <div class="metric-val" style="font-size: 1.25rem; color:#94a3b8;">- m</div>
                <div class="metric-sub" style="color: #94a3b8;">Menunggu data input</div>
            </div>
            """, unsafe_allow_html=True)
        else:
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

    with k2:
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

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🚦 Status Operasional</div>
            <div style="margin-top: 4px; margin-bottom: 6px;">
                <span class="status-badge {badge_class}">{latest_status if not df_data.empty else "Menunggu Data"}</span>
            </div>
            <div class="metric-sub" style="color: #64748b;">
                {analytics.get('latest_date', '')} ({analytics.get('latest_time', '')})
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
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

    with k5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📐 Rata-rata & Rentang</div>
            <div class="metric-val">{analytics['avg_7d']:.2f} <span style="font-size: 1rem; color:#64748b;">m</span></div>
            <div class="metric-sub" style="color: #64748b;">
                Min: <b>{analytics['min_depth']:.2f}m</b> | Max: <b>{analytics['max_depth']:.2f}m</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # Main Chart
    if df_data.empty:
        fig_empty = go.Figure()
        if show_zones:
            fig_empty.add_hrect(
                y0=0, y1=4.0, fillcolor="#fee2e2", opacity=0.45, layer="below", line_width=0,
                annotation_text="🔴 Zona Surut (< 4.0m) — Tugboat TIDAK BISA MASUK",
                annotation_position="bottom right", annotation_font_size=11, annotation_font_color="#991b1b"
            )
            fig_empty.add_hrect(
                y0=4.0, y1=8.0, fillcolor="#dcfce7", opacity=0.35, layer="below", line_width=0,
                annotation_text="🟢 Zona Operasional (4.0m - 8.0m) — Tugboat AMAN MASUK",
                annotation_position="top right", annotation_font_size=11, annotation_font_color="#166534"
            )
            fig_empty.add_hrect(
                y0=8.0, y1=12.0, fillcolor="#dbeafe", opacity=0.45, layer="below", line_width=0,
                annotation_text="🔵 Zona Siaga Banjir (> 8.0m)",
                annotation_position="top right", annotation_font_size=11, annotation_font_color="#1e40af"
            )
        if show_benchmark:
            fig_empty.add_hline(
                y=4.0, line_dash="dash", line_color="#dc2626", line_width=2.5,
                annotation_text="⚓ TOLAK UKUR: Batas Minimum Tugboat Masuk (4.0 m)",
                annotation_position="top left", annotation_font_color="#dc2626", annotation_font_size=11
            )
        
        now_ts = pd.Timestamp.now()
        fig_empty.update_layout(
            title=dict(
                text=f"<b>Grafik Kedalaman Air {cfg['river']} ({cfg['name']}) vs Tolak Ukur Tugboat (4.0 m)</b>",
                font=dict(size=16, color="#0f172a")
            ),
            xaxis=dict(
                title="Tanggal & Waktu Pengukuran",
                range=[now_ts - pd.Timedelta(days=2), now_ts + pd.Timedelta(days=2)],
                showgrid=True, gridcolor="#f1f5f9"
            ),
            yaxis=dict(
                title="Kedalaman Air (meter)",
                range=[0.0, 6.0], dtick=0.50, tickformat=".2f",
                showgrid=True, gridcolor="#e2e8f0"
            ),
            annotations=[
                dict(
                    x=now_ts, y=2.0,
                    text=f"⚓ <b>Grafik {cfg['name']} Aktif</b><br>Belum ada data pengukuran di tab Google Sheet '{cfg['sheet_name']}'.<br>Silakan input data perdana melalui tab '📝 Input Data Kedalaman Baru' di atas.",
                    showarrow=False,
                    font=dict(size=13, color="#475569"),
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#cbd5e1",
                    borderwidth=1,
                    borderpad=12
                )
            ],
            margin=dict(l=40, r=40, t=60, b=40),
            height=420,
            template="plotly_white"
        )
        st.plotly_chart(fig_empty, width="stretch", config={"displayModeBar": True, "displaylogo": False})
        st.info(f"💡 **Jetty {cfg['name']} Siap Menerima Data:** Tab Spreadsheet: **`{cfg['sheet_name']}`**. Begitu Anda menginput data pengukuran pertama pada tab **'📝 Input Data Kedalaman Baru'**, grafik batang dan analisis tren otomatis tampil.")
    else:
        df_plot = df_data.copy()
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
        
        # 1. Zona Keselamatan
        if show_zones:
            fig.add_hrect(
                y0=0, y1=4.0, fillcolor="#fee2e2", opacity=0.45, layer="below", line_width=0,
                annotation_text="🔴 Zona Surut (< 4.0m) — Tugboat TIDAK BISA MASUK",
                annotation_position="bottom right", annotation_font_size=11, annotation_font_color="#991b1b"
            )
            fig.add_hrect(
                y0=4.0, y1=8.0, fillcolor="#dcfce7", opacity=0.35, layer="below", line_width=0,
                annotation_text="🟢 Zona Operasional (4.0m - 8.0m) — Tugboat AMAN MASUK & BEROPERASI",
                annotation_position="top right", annotation_font_size=11, annotation_font_color="#166534"
            )
            fig.add_hrect(
                y0=8.0, y1=14.0, fillcolor="#dbeafe", opacity=0.45, layer="below", line_width=0,
                annotation_text="🔵 Zona Siaga Banjir (> 8.0m) — Debit & Arus Kuat",
                annotation_position="top right", annotation_font_size=11, annotation_font_color="#1e40af"
            )
        
        # 2. Trace Kedalaman Aktual & Penentuan Skema Warna
        # Default: Seragam Merah Batara (#ef4444 Coral Red dengan outline #b91c1c), persis sama antara Senyiur dan Muara Pahu
        if "Dinamis" in color_mode:
            bar_colors = []
            bar_borders = []
            for val in df_plot["Kedalaman Aktual (m)"]:
                if val < 4.0:
                    bar_colors.append("#ef4444")
                    bar_borders.append("#b91c1c")
                elif val <= 8.0:
                    bar_colors.append("#10b981")
                    bar_borders.append("#047857")
                else:
                    bar_colors.append("#3b82f6")
                    bar_borders.append("#1d4ed8")
            bar_marker_dict = dict(color=bar_colors, line=dict(color=bar_borders, width=1.5), opacity=0.9)
            line_trace_color = "#ef4444"
            line_marker_color = "#b91c1c"
        else:
            # Seragam persis dengan Senyiur (#ef4444)
            bar_marker_dict = dict(color="#ef4444", line=dict(color="#b91c1c", width=1.5), opacity=0.9)
            line_trace_color = "#ef4444"
            line_marker_color = "#b91c1c"

        if "Bar Chart" in chart_type:
            bar_kwargs = {}
            if len(df_plot) == 1:
                bar_kwargs["width"] = [86400000 * 0.4]
                
            fig.add_trace(go.Bar(
                x=df_plot["DateTime"],
                y=df_plot["Kedalaman Aktual (m)"],
                name=f"Kedalaman {cfg['name']} (m)",
                marker=bar_marker_dict,
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
                name=f"Kedalaman {cfg['name']} (m)",
                line=dict(color=line_trace_color, width=3),
                marker=dict(size=8, color=line_marker_color, symbol="circle"),
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
            
        # 4. Garis Tren
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
                
        data_min = float(df_plot["Kedalaman Aktual (m)"].min()) if not df_plot.empty else 0.0
        data_max = float(df_plot["Kedalaman Aktual (m)"].max()) if not df_plot.empty else 4.0

        if "Super Zoom" in scale_mode:
            y_min = max(0.0, np.floor((data_min - 0.25) * 10) / 10)
            y_max = np.ceil((data_max + 0.35) * 10) / 10
            dtick_val = 0.10
        elif "Detail Fokus" in scale_mode:
            y_min = max(0.0, np.floor((data_min - 0.40) * 5) / 5)
            y_max = max(4.30, np.ceil((data_max + 0.60) * 5) / 5)
            dtick_val = 0.20
        else:
            y_min = 0.0
            y_max = max(10.0, data_max + 1.8)
            dtick_val = 1.00
        
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
                text=f"<b>Grafik Kedalaman Air {cfg['river']} ({cfg['name']}) vs Tolak Ukur Tugboat (4.0 m)</b>",
                font=dict(size=17, color="#0f172a")
            ),
            xaxis=xaxis_config,
            yaxis=dict(
                title="Kedalaman Air (meter)",
                showgrid=True,
                gridcolor="#e2e8f0",
                gridwidth=1,
                range=[y_min, y_max],
                dtick=dtick_val,
                tickformat=".2f"
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
            height=560,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, width="stretch", config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False})
        
        # Deviasi & Distribusi
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.markdown(f"#### ⚖️ Deviasi Kedalaman vs Tolak Ukur 4.0m ({cfg['name']})")
            st.caption(f"Selisih kedalaman air terhadap batas tolak ukur masuk tugboat (4,0 meter) di alur {cfg['river']}.")
            
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
                height=300,
                template="plotly_white"
            )
            st.plotly_chart(fig_dev, width="stretch")
            
        with col_c2:
            st.markdown(f"#### 📊 Distribusi Status Operasional Tugboat ({cfg['name']})")
            st.caption(f"Proporsi kondisi izin masuk dan operasi tugboat di alur {cfg['river']}.")
            
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
                height=300,
                showlegend=False,
                template="plotly_white"
            )
            st.plotly_chart(fig_pie, width="stretch")

# ==========================================================
# TAB 1: VISUALISASI, TREN & PLAN AIR
# ==========================================================
with tab_viz:
    st.markdown("### 📊 Analisis & Visualisasi Kedalaman Air Sungai Batara")
    
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

        st.markdown("---")
        c_sc1, c_sc2 = st.columns([2.5, 2.5])
        with c_sc1:
            scale_mode = st.radio(
                "🔍 Skala Vertikal Kedalaman (Zoom Rentang):",
                [
                    "🔍 Detail Fokus (Kenaikan 0 koma terlihat jelas)",
                    "🔬 Super Zoom (Fokus rentang data aktual)",
                    "🌐 Skala Penuh (0 s/d 10 Meter)"
                ],
                index=0
            )
        with c_sc2:
            color_mode = st.radio(
                "🎨 Skema Warna Batang Grafik:",
                [
                    "🔴 Seragam Merah Batara (Persis Senyiur)",
                    "🚥 Dinamis Berdasarkan Status (Merah/Hijau/Biru)"
                ],
                index=0
            )
            st.info("💡 **Mode Detail Fokus** memperbesar rentang sumbu kedalaman secara otomatis dan menampilkan garis kisi (*grid*) setiap **0,20 meter**, sehingga fluktuasi sekecil 0,05 m – 0,10 m langsung terlihat jelas dan bergelombang.")

    # Render Grafik Senyiur
    if "Kedua Jetty" in view_mode or "Senyiur" in view_mode:
        render_jetty_dashboard_section("senyiur", df_senyiur, df_senyiur_raw, chart_type, show_benchmark, show_trend, show_zones, trend_type, scale_mode, color_mode)
        
    # Pemisah visual jika kedua jetty ditampilkan
    if "Kedua Jetty" in view_mode:
        st.markdown("""
        <div style='margin: 35px 0 25px 0; border-top: 3px dashed #cbd5e1; text-align: center;'>
            <span style='position: relative; top: -14px; background: #e0f2fe; color: #0369a1; padding: 4px 18px; border-radius: 20px; border: 1px solid #bae6fd; font-weight: 700; font-size: 0.88rem;'>
                🌊 GRAFIK JETTY MUARA PAHU (DI BAWAH)
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Render Grafik Muara Pahu (Tepat di bawah Senyiur)
    if "Kedua Jetty" in view_mode or "Muara Pahu" in view_mode:
        render_jetty_dashboard_section("muara_pahu", df_muara, df_muara_raw, chart_type, show_benchmark, show_trend, show_zones, trend_type, scale_mode, color_mode)


# ==========================================================
# TAB 2: INPUT DATA BARU VIA WEB FORM
# ==========================================================
with tab_input:
    st.markdown("### 📝 Form Pencatatan Kedalaman Air Sungai")
    st.markdown("Input data melalui form ini akan **langsung tersimpan ke database Google Spreadsheet** pada tab sheet yang sesuai.")
    
    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        input_target_jetty = st.radio(
            "📍 Pilih Jetty Tujuan Input:",
            ["🌊 Jetty Senyiur (Tab: Senyiur)", "🌊 Jetty Muara Pahu (Tab: Muara Pahu)"],
            index=0 if "Senyiur" in view_mode else (1 if "Muara Pahu" in view_mode else 0)
        )
    target_key = "senyiur" if "Senyiur" in input_target_jetty else "muara_pahu"
    target_cfg = data_manager.JETTY_CONFIG[target_key]
    
    with col_sel2:
        st.info(
            f"🎯 **Target Penyimpanan:** Data akan dikirim langsung ke Google Sheet **Tab: `{target_cfg['sheet_name']}`**.<br>"
            f"Titik Pantau: <b>{target_cfg['titik_pantau']}</b> | Tolak Ukur: <b>{target_cfg['plan_benchmark']:.1f} Meter</b>.",
            icon="ℹ️"
        )
    
    with st.container():
        with st.form("form_input_kedalaman", clear_on_submit=True):
            st.markdown(f"##### 📌 Informasi Waktu & Lokasi ({target_cfg['name']})")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                input_tgl = st.date_input("📅 Tanggal Pengukuran", value=datetime.date.today())
            with col_f2:
                jam_default = datetime.datetime.now().strftime("%H:%M")
                input_waktu = st.text_input("⏰ Jam / Waktu (HH:MM)", value=jam_default)
            with col_f3:
                input_titik = st.text_input(
                    "📍 Titik Pantau",
                    value=target_cfg["titik_pantau"],
                    disabled=True,
                    help=f"Titik pantau operasional {target_cfg['river']} ({target_cfg['name']})."
                )
                
            st.markdown("##### 📐 Parameter Kedalaman Air")
            st.info(f"⚓ **Tolak Ukur Tetap Operasional ({target_cfg['name']}):** **4,0 Meter**. Di bawah 4,0 meter tugboat tidak bisa masuk ke sungai karena surut. Anda tidak perlu menginput plan, tolak ukur sudah otomatis 4,0 m.")
            
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
                default_note = f"Kondisi air {target_cfg['river']} masih surut, tugboat belum bisa masuk ke sungai."
                input_ket = st.text_input("📝 Catatan Lapangan / Keterangan", value=default_note, placeholder="Contoh: Arus stabil, aman untuk navigasi.")

            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button(f"💾 Simpan Data ke Sheet: {target_cfg['sheet_name']}", width="stretch", type="primary")
            
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
                    
                    success, msg = data_manager.add_new_entry(new_entry, jetty_key=target_key)
                    if success:
                        st.success(f"🎉 **{msg}**")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


# ==========================================================
# TAB 3: TABEL DATA & RIWAYAT SPREADSHEET
# ==========================================================
def render_table_view(jetty_key: str, df_raw_jetty: pd.DataFrame, df_filtered_jetty: pd.DataFrame):
    cfg = data_manager.JETTY_CONFIG[jetty_key]
    sheet_url = f"{data_manager.GSHEET_URL}#gid={cfg['sheet_gid']}"
    
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        search_query = st.text_input(
            f"🔍 Cari di {cfg['name']} (Nama Karyawan, Titik, atau Keterangan):",
            placeholder="Ketik kata kunci...",
            key=f"search_{jetty_key}"
        )
    with col_t2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.caption(f"Menampilkan **{len(df_filtered_jetty)}** dari **{len(df_raw_jetty)}** data")
        
    df_disp = df_filtered_jetty.copy()
    if search_query:
        mask = (
            df_disp["Petugas"].astype(str).str.contains(search_query, case=False, na=False) |
            df_disp["Titik Pantau"].astype(str).str.contains(search_query, case=False, na=False) |
            df_disp["Keterangan"].astype(str).str.contains(search_query, case=False, na=False) |
            df_disp["Status"].astype(str).str.contains(search_query, case=False, na=False)
        )
        df_disp = df_disp[mask]
        
    if not df_disp.empty and "Tanggal" in df_disp.columns:
        df_disp = df_disp.sort_values(by=["Tanggal", "Waktu"], ascending=[False, False])
        
    if not df_disp.empty and "ID" in df_disp.columns:
        df_disp["ID"] = pd.to_numeric(df_disp["ID"], errors="coerce").fillna(1).astype(int)
        
    if df_disp.empty:
        st.info(f"Belum ada catatan data pada {cfg['name']} (Tab Google Sheet: **{cfg['sheet_name']}**).")
    else:
        st.dataframe(
            df_disp[[col for col in data_manager.COLUMNS if col in df_disp.columns]],
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
        
    with st.expander(f"ℹ️ Kelola / Edit / Hapus Baris di Google Spreadsheet (Tab: {cfg['sheet_name']})"):
        st.info(
            f"Karena seluruh data tersimpan pada **Database Tunggal Google Spreadsheet Online**, "
            f"Anda dapat mengedit atau menghapus baris data langsung di "
            f"[**Google Spreadsheet (Tab: {cfg['sheet_name']})**]({sheet_url}). "
            f"Setelah mengedit, klik tombol **'🔄 Sync / Reload dari Google Sheet'** di sidebar."
        )
        st.link_button(f"🌐 Buka Spreadsheet Tab: {cfg['sheet_name']}", sheet_url, width="stretch", type="primary")

with tab_table:
    st.markdown("### 📋 Tabel Riwayat Data Kedalaman Air Google Spreadsheet")
    st.markdown("Pilih tab di bawah untuk melihat dan mencari data per Jetty:")
    
    t_tab1, t_tab2 = st.tabs([
        f"🌊 Jetty Senyiur ({len(df_senyiur_raw)} baris)",
        f"🌊 Jetty Muara Pahu ({len(df_muara_raw)} baris)"
    ])
    
    with t_tab1:
        render_table_view("senyiur", df_senyiur_raw, df_senyiur)
    with t_tab2:
        render_table_view("muara_pahu", df_muara_raw, df_muara)


# ==========================================================
# TAB 4: DATABASE TUNGGAL GOOGLE SPREADSHEET
# ==========================================================
with tab_settings:
    st.markdown("### ☁️ Database Tunggal: Google Spreadsheet Multi-Tab")
    st.markdown("""
    Aplikasi ini beroperasi dengan **arsitektur database tunggal berbasis cloud multi-lokasi**:
    - **Tidak ada file data yang disimpan di komputer lokal**.
    - Memantau 2 Jetty dalam satu file Spreadsheet yang sama menggunakan sheet tab terpisah:
      1. **Tab `Senyiur`** (gid=0) untuk Jetty Senyiur.
      2. **Tab `Muara Pahu`** (gid=222827428) untuk Jetty Muara Pahu.
    - Sinkronisasi berjalan realtime 2-arah secara otomatis.
    """)
    
    st.markdown(f"""
    <div class="gsheet-box">
        <h4 style="margin: 0 0 8px 0; color: #166534;">🟢 Google Spreadsheet Aktif (Database Utama Multi-Tab)</h4>
        <p style="margin: 0; color: #334155; font-size: 0.95rem;">
            Nama File Spreadsheet: <b>Water Depth</b><br>
            Spreadsheet ID: <code>{data_manager.GSHEET_ID}</code><br>
            Link Dokumen: <b><a href="{data_manager.GSHEET_URL}" target="_blank">{data_manager.GSHEET_URL}</a></b>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### 🔗 1. Akses Langsung ke Tab Spreadsheet")
        st.markdown("Pilih tab sheet yang ingin dibuka dan diedit secara langsung di browser:")
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            st.link_button(
                "🌊 Buka Tab Senyiur",
                f"{data_manager.GSHEET_URL}#gid={data_manager.JETTY_CONFIG['senyiur']['sheet_gid']}",
                width="stretch",
                type="primary"
            )
        with c_btn2:
            st.link_button(
                "🌊 Buka Tab Muara Pahu",
                f"{data_manager.GSHEET_URL}#gid={data_manager.JETTY_CONFIG['muara_pahu']['sheet_gid']}",
                width="stretch",
                type="primary"
            )
            
        st.markdown("##### 📌 Struktur Kolom Standar (Kedua Sheet):")
        for idx, col in enumerate(data_manager.COLUMNS, 1):
            st.markdown(f"{idx}. `{col}`")
            
    with col_g2:
        st.markdown("#### ⚡ 2. Google Apps Script Webhook (Multi-Sheet)")
        st.success("🟢 **Webhook URL Aktif:** Menerima input dari web dan otomatis memisahkan data ke tab sheet yang sesuai.")
        st.code(data_manager.WEBHOOK_URL, language="text")
        
        with st.expander("💻 Script Google Apps Script untuk Routing Sheet Otomatis (Klik untuk lihat)"):
            st.markdown("""
            Pastikan script Google Apps Script di Spreadsheet Anda dapat membedakan sheet tujuan dengan kode berikut:
            """)
            st.code('''function doPost(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var data = JSON.parse(e.postData.contents);
    
    // Tentukan sheet tujuan berdasarkan parameter yang dikirim aplikasi
    var sheetName = data.sheet || data.sheetName || "Senyiur";
    var sheet = ss.getSheetByName(sheetName);
    
    // Fallback pencarian fleksibel
    if (!sheet) {
      if (sheetName.toLowerCase().indexOf("senyiur") !== -1) {
        sheet = ss.getSheetByName("Senyiur") || ss.getSheetByName("Sheet1") || ss.getSheets()[0];
      } else if (sheetName.toLowerCase().indexOf("muara") !== -1) {
        sheet = ss.getSheetByName("Muara Pahu") || ss.getSheetByName("Sheet2");
      }
    }
    
    if (!sheet) {
      sheet = ss.getSheets()[0];
    }
    
    // Append baris baru ke sheet yang dituju
    sheet.appendRow([
      data["ID"],
      data["Tanggal"],
      data["Waktu"],
      data["Titik Pantau"],
      data["Kedalaman Aktual (m)"],
      data["Plan Kedalaman (m)"],
      data["Status"],
      data["Petugas"],
      data["Keterangan"]
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success", 
      message: "Data berhasil disimpan ke sheet " + sheet.getName(),
      row: sheet.getLastRow()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch(err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error", 
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}''', language="javascript")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 10px 0;">
    🌊 <b>Sistem Pemantauan Kedalaman Air Sungai (Jetty Senyiur & Jetty Muara Pahu)</b> — <b>PT Batara Dharma Persada</b> | Database Tunggal Google Spreadsheet
</div>
""", unsafe_allow_html=True)

