@echo off
echo Starting Integrated Brand Tracker and Dashboard...
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python.
    goto :end
)

REM Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing required packages...
    pip install -r brand_tracker\async_requirements.txt
    pip install -r median_model\requirements.txt
) else (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo.
echo ================================================================
echo BRAND TRACKER AND DASHBOARD INTEGRATED APPLICATION
echo ================================================================
echo.
echo Available brands:
echo 1. Apple
echo 2. McDonald's
echo 3. Nike
echo 4. Starbucks
echo 5. Tesla
echo 6. Custom
echo.

set /p brand_choice=Select a brand (1-6, default is 1): 

if "%brand_choice%"=="" set brand_choice=1

if "%brand_choice%"=="1" (
    set brand=apple
) else if "%brand_choice%"=="2" (
    set brand=mcdonalds
) else if "%brand_choice%"=="3" (
    set brand=nike
) else if "%brand_choice%"=="4" (
    set brand=starbucks
) else if "%brand_choice%"=="5" (
    set brand=tesla
) else if "%brand_choice%"=="6" (
    set brand=custom
) else (
    echo Invalid choice. Using default (Apple).
    set brand=apple
)

echo.
echo Selected brand: %brand%
echo.
echo Starting integrated application...
echo.
echo The dashboard will open in your default web browser.
echo Press Ctrl+C to stop the application.
echo.

python run_integrated.py --brand %brand%

:end
echo.
pause
