@echo off
REM Quick run script for Job Application Tracker (Windows)

echo ================================
echo Job Application Tracker
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if database exists
if not exist "job_applications.db" (
    echo Database not found!
    echo Initializing database...
    python -m app.db.init_db
    echo Database initialized
    echo.
)

REM Check if credentials exist
if not exist "credentials.json" (
    echo WARNING: credentials.json not found!
    echo Please:
    echo   1. Go to https://console.cloud.google.com/
    echo   2. Enable Gmail API
    echo   3. Create OAuth credentials
    echo   4. Download as credentials.json
    echo.
    pause
    exit /b 1
)

REM Menu
echo Select an option:
echo   1) Run poller once (process new emails)
echo   2) Start dashboard
echo   3) Start continuous poller
echo   4) Run tests
echo   5) Reset database (WARNING: deletes all data)
echo.
set /p choice="Enter choice [1-5]: "

if "%choice%"=="1" (
    echo Running poller once...
    python -m app.poller --once
) else if "%choice%"=="2" (
    echo Starting dashboard...
    streamlit run app/dashboard.py
) else if "%choice%"=="3" (
    echo Starting continuous poller...
    python -m app.poller
) else if "%choice%"=="4" (
    echo Running tests...
    python -m app.tests
) else if "%choice%"=="5" (
    set /p confirm="WARNING: This will DELETE ALL DATA. Are you sure? (yes/no): "
    if "%confirm%"=="yes" (
        python -m app.db.init_db --reset
        echo Database reset
    ) else (
        echo Cancelled
    )
) else (
    echo Invalid choice
    exit /b 1
)

pause
