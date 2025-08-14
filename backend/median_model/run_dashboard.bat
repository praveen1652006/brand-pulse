@echo off
echo Brand Tracker Dashboard - Dynamic Analytics
echo ============================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.7 or higher.
    echo Visit https://www.python.org/downloads/ to download Python.
    pause
    exit /b
)

REM Check if virtual environment exists
if not exist .venv\ (
    echo Creating Python virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

echo.
echo Choose an option:
echo 1. Run sentiment analysis (processes amazon.csv)
echo 2. Launch interactive dashboard with real-time mentions feed
echo 3. Run analysis and then launch dashboard
echo 4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running sentiment analyzer...
    python sentiment_analyzer.py
    echo.
    pause
    %0
    exit /b
) else if "%choice%"=="2" (
    echo.
    echo Launching dashboard...
    streamlit run dashboard.py
    echo.
    pause
    %0
    exit /b
) else if "%choice%"=="3" (
    echo.
    echo Running sentiment analyzer and then launching dashboard...
    python sentiment_analyzer.py
    if %errorlevel% equ 0 (
        echo Analysis complete! Launching dashboard...
        streamlit run dashboard.py
    ) else (
        echo Sentiment analysis failed! Please check the error messages.
        pause
    )
    echo.
    pause
    %0
    exit /b
) else if "%choice%"=="4" (
    echo Exiting...
    exit /b
) else (
    echo Invalid choice, please try again.
    pause
    %0
    exit /b
)
