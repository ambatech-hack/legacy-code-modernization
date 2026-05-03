@echo off
REM IBM Bob Legacy Code Modernization Platform - Quick Start Script (Windows)
REM This script automates the setup and launch process

setlocal enabledelayedexpansion

REM Colors (limited in Windows CMD)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

echo.
echo ========================================
echo IBM Bob Quick Start (Windows)
echo ========================================
echo.

REM Step 1: Check prerequisites
echo ========================================
echo Step 1: Checking Prerequisites
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%X Python is not installed%NC%
    echo.
    echo Please install Python 3.11 or higher from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%√ Python is installed: !PYTHON_VERSION!%NC%
)

REM Check pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%X pip is not installed%NC%
    pause
    exit /b 1
) else (
    echo %GREEN%√ pip is installed%NC%
)

echo.

REM Step 2: Setup virtual environment
echo ========================================
echo Step 2: Setting Up Virtual Environment
echo ========================================
echo.

cd /d "%PROJECT_DIR%"

if exist "venv" (
    echo %YELLOW%! Virtual environment already exists%NC%
    set /p "RECREATE=Remove and recreate? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q venv
        echo %GREEN%√ Removed existing virtual environment%NC%
    )
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo %RED%X Failed to create virtual environment%NC%
        pause
        exit /b 1
    )
    echo %GREEN%√ Virtual environment created%NC%
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo %GREEN%√ Virtual environment activated%NC%

echo.

REM Step 3: Install dependencies
echo ========================================
echo Step 3: Installing Dependencies
echo ========================================
echo.

echo Upgrading pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo %YELLOW%! Warning: Failed to upgrade pip%NC%
)

echo Installing requirements...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo %RED%X Failed to install dependencies%NC%
    pause
    exit /b 1
)
echo %GREEN%√ Dependencies installed%NC%

echo.

REM Step 4: Configure environment
echo ========================================
echo Step 4: Configuring Environment
echo ========================================
echo.

if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo %GREEN%√ .env file created%NC%
    echo.
    echo %YELLOW%! Please configure your IBM watsonx.ai credentials in .env%NC%
    echo Required variables:
    echo   - WATSONX_API_KEY
    echo   - WATSONX_PROJECT_ID
    echo.
    
    set /p "CONFIGURE=Do you want to configure now? (y/N): "
    if /i "!CONFIGURE!"=="y" (
        set /p "API_KEY=Enter your watsonx.ai API key: "
        set /p "PROJECT_ID=Enter your watsonx.ai Project ID: "
        
        REM Update .env file (basic replacement)
        powershell -Command "(gc .env) -replace 'your_api_key_here', '!API_KEY!' | Out-File -encoding ASCII .env"
        powershell -Command "(gc .env) -replace 'your_project_id_here', '!PROJECT_ID!' | Out-File -encoding ASCII .env"
        
        echo %GREEN%√ Credentials configured%NC%
    ) else (
        echo %YELLOW%! Remember to configure .env before running the application%NC%
    )
) else (
    echo %GREEN%√ .env file already exists%NC%
)

echo.

REM Step 5: Create output directories
echo ========================================
echo Step 5: Creating Output Directories
echo ========================================
echo.

if not exist "output" mkdir output
if not exist "logs" mkdir logs
echo %GREEN%√ Output directories created%NC%

echo.

REM Step 6: Run tests (optional)
echo ========================================
echo Step 6: Running Tests (Optional)
echo ========================================
echo.

set /p "RUN_TESTS=Run tests to verify installation? (Y/n): "
if /i not "!RUN_TESTS!"=="n" (
    echo Running tests...
    python -m pytest tests\ -v --tb=short 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%√ All tests passed%NC%
    ) else (
        echo %YELLOW%! Some tests failed (this may be expected if watsonx.ai is not configured)%NC%
    )
)

echo.

REM Step 7: Launch application
echo ========================================
echo Step 7: Launch Application
echo ========================================
echo.

echo Choose how to start IBM Bob:
echo   1) Streamlit Web UI (recommended for beginners)
echo   2) REST API Server (for programmatic access)
echo   3) Both UI and API
echo   4) Run demo
echo   5) Exit (manual start)
echo.

set /p "CHOICE=Enter choice (1-5): "

echo.

if "!CHOICE!"=="1" (
    echo Starting Streamlit UI...
    echo %GREEN%√ UI will be available at: http://localhost:8501%NC%
    echo.
    streamlit run ui\app.py
) else if "!CHOICE!"=="2" (
    echo Starting REST API...
    echo %GREEN%√ API will be available at: http://localhost:8000%NC%
    echo %GREEN%√ API docs at: http://localhost:8000/docs%NC%
    echo.
    python scripts\run_api_server.py
) else if "!CHOICE!"=="3" (
    echo Starting both UI and API...
    echo %GREEN%√ UI: http://localhost:8501%NC%
    echo %GREEN%√ API: http://localhost:8000%NC%
    echo.
    start /b python scripts\run_api_server.py
    streamlit run ui\app.py
) else if "!CHOICE!"=="4" (
    echo Running demo...
    python scripts\demo.py
) else if "!CHOICE!"=="5" (
    echo Setup complete!
    echo.
    echo To start manually:
    echo   1. Activate virtual environment: venv\Scripts\activate.bat
    echo   2. Start UI: streamlit run ui\app.py
    echo   3. Or start API: python scripts\run_api_server.py
    echo   4. Or run demo: python scripts\demo.py
) else (
    echo %RED%X Invalid choice%NC%
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo %GREEN%√ IBM Bob is ready to use%NC%
echo.
echo Documentation:
echo   - User Guide: USER_GUIDE.md
echo   - API Docs: API_DOCUMENTATION.md
echo   - Demo Guide: DEMO.md
echo.

pause

