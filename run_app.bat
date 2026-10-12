@echo off
title Monitoring Kedalaman Air Sungai Senyiur
echo ===================================================
echo   MEMBUKA APLIKASI MONITORING KEDALAMAN AIR SENYIUR
echo ===================================================
echo Memulai server Streamlit...
echo Buka browser di http://localhost:8501 jika tidak terbuka otomatis.
echo Tekan CTRL + C di jendela ini untuk mematikan aplikasi.
echo.

.\.venv\Scripts\streamlit.exe run app.py --server.port 8501
pause
