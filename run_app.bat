@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=D:\software\anaconda3\envs\ENV_001\python.exe"
set "LOGFILE=%~dp0streamlit_log.txt"

if not exist "%PYTHON%" (
    echo [ERROR] Python ENV_001 tidak ditemukan di: %PYTHON%
    pause
    exit /b 1
)

echo ============================================================
echo  Menjalankan aplikasi Streamlit...
echo  Browser akan terbuka otomatis di http://localhost:8501
echo  Tekan Ctrl+C untuk menghentikan server.
echo  Log lengkap: streamlit_log.txt
echo ============================================================
echo.

"%PYTHON%" -m streamlit run app.py %* >> "%LOGFILE%" 2>&1

set "EXITCODE=%errorlevel%"
echo.
if not "%EXITCODE%"=="0" (
    echo [PERINGATAN] Streamlit berhenti dengan kode keluar %EXITCODE%.
    echo Periksa streamlit_log.txt untuk detail error.
) else (
    echo Server Streamlit telah berhenti.
)
echo.
pause
