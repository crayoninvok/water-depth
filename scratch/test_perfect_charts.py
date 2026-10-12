import data_manager
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def build_fig(jetty_key):
    df_data = data_manager.fetch_gsheet_public(jetty_key)
    cfg = data_manager.JETTY_CONFIG[jetty_key]
    df_plot = df_data.copy()
    df_plot['DateTimeStr'] = df_plot['Tanggal'].astype(str) + ' ' + df_plot['Waktu'].astype(str)
    df_plot['DateTime'] = pd.to_datetime(df_plot['DateTimeStr'], errors='coerce')
    df_plot = df_plot.sort_values(by='DateTime')
    df_plot['Kedalaman Aktual (m)'] = df_plot['Kedalaman Aktual (m)'].apply(lambda x: data_manager.safe_float(x, default=0.0))
    df_plot['Label'] = df_plot['DateTime'].dt.strftime('%d %b %H:%M')
    
    x_numeric = np.arange(len(df_plot))
    poly_fit = np.polyfit(x_numeric, df_plot['Kedalaman Aktual (m)'], 1)
    df_plot['Trend_Linear'] = np.polyval(poly_fit, x_numeric)
    
    fig = go.Figure()
    
    # Safety zones
    fig.add_hrect(
        y0=0, y1=4.0, fillcolor="#fee2e2", opacity=0.25, layer="below", line_width=0,
        annotation_text="🔴 Zona Surut (< 4.0m) — Tugboat TIDAK BISA MASUK",
        annotation_position="bottom right", annotation_font_size=10, annotation_font_color="#991b1b"
    )
    fig.add_hrect(
        y0=4.0, y1=8.0, fillcolor="#dcfce7", opacity=0.20, layer="below", line_width=0,
        annotation_text="🟢 Zona Operasional (4.0m - 8.0m) — Tugboat AMAN",
        annotation_position="top right", annotation_font_size=10, annotation_font_color="#166534"
    )
    fig.add_hrect(
        y0=8.0, y1=14.0, fillcolor="#dbeafe", opacity=0.25, layer="below", line_width=0,
        annotation_text="🔵 Zona Siaga Banjir (> 8.0m)",
        annotation_position="top right", annotation_font_size=10, annotation_font_color="#1e40af"
    )

    fig.add_trace(go.Bar(
        x=df_plot['Label'],
        y=df_plot['Kedalaman Aktual (m)'],
        name=f"Kedalaman {cfg['name']} (m)",
        marker=dict(color='#ef4444', line=dict(color='#b91c1c', width=1.5), opacity=0.9),
        text=[f"{v:.2f} m" for v in df_plot['Kedalaman Aktual (m)']],
        textposition='outside',
        textfont=dict(size=11, color='#0f172a'),
        hovertemplate=(
            "<b>Tanggal & Jam:</b> %{x}<br>" +
            "<b>Kedalaman:</b> %{y:.2f} m<extra></extra>"
        )
    ))
    fig.add_trace(go.Scatter(
        x=df_plot['Label'],
        y=df_plot['Trend_Linear'],
        mode='lines+markers',
        name='Tren Regresi Linier',
        line=dict(color='#db2777', width=3, dash='dash'),
        marker=dict(size=6, color='#be185d', symbol='square'),
        hovertemplate="<b>Tren:</b> %{y:.2f} m<extra></extra>"
    ))
    fig.add_hline(
        y=4.0, line_dash='dash', line_color='#dc2626', line_width=2.5,
        annotation_text="⚓ TOLAK UKUR: Batas Minimum Tugboat Masuk (4.0 m)",
        annotation_position="top left", annotation_font_color="#dc2626", annotation_font_size=11
    )
    
    data_min = float(df_plot['Kedalaman Aktual (m)'].min())
    data_max = float(df_plot['Kedalaman Aktual (m)'].max())
    
    # Always ensure 4.0m tolak ukur benchmark is included in the visible range!
    y_min = max(0.0, min(3.50, np.floor((data_min - 0.40) * 5) / 5))
    y_max = max(4.30, np.ceil((data_max + 0.60) * 5) / 5)
    
    fig.update_layout(
        title=dict(text=f"<b>Grafik Kedalaman Air {cfg['river']} ({cfg['name']}) vs Tolak Ukur Tugboat (4.0 m)</b>", font=dict(size=16, color="#0f172a")),
        xaxis=dict(type='category', title='Tanggal & Waktu Pengukuran', showgrid=True, gridcolor='#f1f5f9', tickangle=-45),
        yaxis=dict(title='Kedalaman Air (meter)', range=[y_min, y_max], dtick=0.5 if y_max - y_min > 5 else 0.2, tickformat='.2f', showgrid=True, gridcolor='#e2e8f0'),
        bargap=0.3,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=540,
        margin=dict(l=40, r=40, t=60, b=60),
        template='plotly_white'
    )
    return fig

fig_m = build_fig('muara_pahu')
fig_m.write_html('scratch/muara_pahu_perfect.html')
fig_s = build_fig('senyiur')
fig_s.write_html('scratch/senyiur_perfect.html')
print("Successfully wrote both HTML charts!")
