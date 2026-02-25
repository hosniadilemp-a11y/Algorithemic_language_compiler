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

REM --- Step 1: Find Python ---
echo [1/4] Searching for Python installation...

SET PYTHON_EXE=

REM Try python in PATH first
python --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYTHON_EXE=python
    GOTO :python_found
)

REM Try py launcher (standard Python installs)
py --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYTHON_EXE=py
    GOTO :python_found
)

REM Search common Anaconda / Miniconda locations
FOR %%P IN (
    "%USERPROFILE%\anaconda3\python.exe"
    "%USERPROFILE%\miniconda3\python.exe"
    "%LOCALAPPDATA%\anaconda3\python.exe"
    "%LOCALAPPDATA%\miniconda3\python.exe"
    "C:\ProgramData\Anaconda3\python.exe"
    "C:\ProgramData\Miniconda3\python.exe"
    "C:\Anaconda3\python.exe"
    "C:\Miniconda3\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe"
) DO (
    IF EXIST %%P (
        SET PYTHON_EXE=%%P
        GOTO :python_found
    )
)

REM Python not found anywhere
echo.
echo  ERROR: Python could not be found on this system!
echo.
echo  Please install Python 3 from https://www.python.org/downloads/
echo  or install Anaconda from https://www.anaconda.com/
echo  Then re-run this script.
echo.
pause
exit /b 1

:python_found
echo  [OK] Python found: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

REM --- Step 2: Check Python version is 3.x ---
echo [2/4] Verifying Python version...
%PYTHON_EXE% -c "import sys; exit(0 if sys.version_info.major >= 3 else 1)"
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
    %PYTHON_EXE% -m venv venv
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
