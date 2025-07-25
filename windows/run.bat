@echo off
setlocal

set SCRIPT_DIR=%~dp0
cd /D "%SCRIPT_DIR%.."

set VENV_NAME=moitruongao
set PYTHON_EXE_IN_VENV=%VENV_NAME%\Scripts\python.exe
set PYTHONW_EXE_IN_VENV=%VENV_NAME%\Scripts\pythonw.exe
set MAIN_SCRIPT=run_app.py

echo ===========================================================
echo Text Tree Builder Setup & Run Script for Windows
echo ===========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not found in PATH.
    echo Please install Python and ensure it's added to your PATH.
    pause
    exit /b 1
)
echo Python installation found.
echo.

if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo Creating virtual environment: %VENV_NAME%...
    python -m venv %VENV_NAME%
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
    echo.
)

echo Activating virtual environment...
call "%VENV_NAME%\Scripts\activate.bat"

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo.

echo Running Text Tree Builder application...

if exist "%PYTHONW_EXE_IN_VENV%" (
    start "TextTreeBuilder" /B "%PYTHONW_EXE_IN_VENV%" "%MAIN_SCRIPT%"
) else (
    start "TextTreeBuilder" /B "%PYTHON_EXE_IN_VENV%" "%MAIN_SCRIPT%"
)

endlocal
exit /b 0