@echo off
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
    py -m pip install -r requirements.txt
    py -m streamlit run app.py --server.address 127.0.0.1
) else (
    python -m pip install -r requirements.txt
    python -m streamlit run app.py --server.address 127.0.0.1
)
pause
