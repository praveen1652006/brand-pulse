@echo off
echo Brand Sentiment Analysis Tool
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

REM Install required packages if not already installed
echo Installing required packages...
pip install -r requirements.txt

echo.
echo Choose an option:
echo 1. Create sample data
echo 2. Run sentiment analyzer
echo 3. Exit
echo.

set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Creating sample data...
    python create_sample_data.py
    echo.
    pause
    %0
    exit /b
) else if "%choice%"=="2" (
    echo.
    echo Running sentiment analyzer...
    python sentiment_analyzer.py
    echo.
    pause
    %0
    exit /b
) else if "%choice%"=="3" (
    echo Exiting...
    exit /b
) else (
    echo Invalid choice, please try again.
    pause
    %0
    exit /b
)
