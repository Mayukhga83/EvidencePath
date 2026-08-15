@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
call .venv\Scripts\activate.bat
python -c "import streamlit, sklearn, pandas, openai, pypdf, pydantic" >nul 2>&1
if errorlevel 1 (
  echo Installing Python dependencies (first launch only)...
  python -m pip install -r requirements.txt
  if errorlevel 1 goto :error
)
python -m streamlit run app.py
exit /b 0
:error
echo.
echo Unable to start. Ensure Python 3.10-3.12 and internet access for first-time package installation.
pause
exit /b 1
