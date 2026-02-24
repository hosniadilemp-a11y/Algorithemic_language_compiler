@echo off
REM =============================================================================
REM AlgoCompiler - Setup Script for Windows
REM Run this script ONCE to install all required dependencies.
REM Simply double-click this file to run it.
REM =============================================================================

title AlgoCompiler Setup

echo.
echo  +==============================================+
echo  ^|    AlgoCompiler -- Windows Setup Script     ^|
echo  +==============================================+
echo.

REM --- Step 1: Check for Python ---
echo [1/4] Checking Python installation...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Python is not installed or not in your PATH!
    echo.
    echo  Please follow these steps:
    echo    1. Go to: https://www.python.org/downloads/
    echo    2. Download Python 3 (e.g. Python 3.12.x)
    echo    3. Run the installer.
    echo    4. IMPORTANT: Check the box "Add Python to PATH" during installation!
    echo    5. Restart your computer, then run this script again.
    echo.
    pause
    exit /b 1
)

python --version
echo  [OK] Python found.
echo.

REM --- Step 2: Check Python version is 3.x ---
echo [2/4] Verifying Python version...
python -c "import sys; exit(0 if sys.version_info.major >= 3 else 1)"
IF ERRORLEVEL 1 (
    echo  ERROR: Python 3 is required. You appear to have Python 2.
    echo  Please install Python 3 from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo  [OK] Python 3 confirmed.
echo.

REM --- Step 3: Create a virtual environment ---
echo [3/4] Creating Python virtual environment in .\venv ...
cd /d "%~dp0\.."

IF NOT EXIST "venv\" (
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
) ELSE (
    echo  [SKIP] Virtual environment already exists.
)
echo.

REM --- Step 4: Install dependencies ---
echo [4/4] Installing dependencies from requirements.txt...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Something went wrong during installation.
    echo  Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo  +===============================================+
echo  ^|  Setup complete! You are ready to go.  :)   ^|
echo  +===============================================+
echo.
echo  To launch AlgoCompiler:
echo    1. Double-click  run_app.bat
echo    2. Open your browser at:  http://localhost:5000
echo.
pause
