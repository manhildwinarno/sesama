@echo off
setlocal
cd /d "%~dp0"

if not defined PYTHON set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%~dp0logs" mkdir "%~dp0logs"
set "LOGFILE=%~dp0logs\streamlit_log.txt"

if not exist "%PYTHON%" (
    echo [ERROR] Python proyek tidak ditemukan di: %PYTHON%
    echo Buat environment: py -3.11 -m venv .venv
    echo Instal dependensi: .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo ============================================================
echo  Menjalankan aplikasi Streamlit...
echo  Browser akan terbuka otomatis di http://localhost:8501
echo  Tekan Ctrl+C untuk menghentikan server.
echo  Log lengkap: logs\streamlit_log.txt
echo ============================================================
echo.

"%PYTHON%" -m streamlit run app.py %* >> "%LOGFILE%" 2>&1

set "EXITCODE=%errorlevel%"
echo.
if not "%EXITCODE%"=="0" (
    echo [PERINGATAN] Streamlit berhenti dengan kode keluar %EXITCODE%.
    echo Periksa logs\streamlit_log.txt untuk detail error.
) else (
    echo Server Streamlit telah berhenti.
)
echo.
pause
