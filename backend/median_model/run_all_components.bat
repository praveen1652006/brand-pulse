@echo off
echo Starting Brand Guardian System...
echo.

set SCRIPT_DIR=%~dp0
set BRAND_TRACKER_DIR=%SCRIPT_DIR%\..\brand_tracker
set MEDIAN_MODEL_DIR=%SCRIPT_DIR%

echo Brand Tracker Path: %BRAND_TRACKER_DIR%
echo Median Model Path: %MEDIAN_MODEL_DIR%
echo.

REM Start Brand Tracker
echo Starting Brand Tracker...
if exist "%BRAND_TRACKER_DIR%\run_brand_tracker.py" (
    start "Brand Tracker" cmd /k "cd /d %BRAND_TRACKER_DIR% && python run_brand_tracker.py"
) else if exist "%BRAND_TRACKER_DIR%\brand_tracker.py" (
    start "Brand Tracker" cmd /k "cd /d %BRAND_TRACKER_DIR% && python brand_tracker.py"
) else (
    echo Error: Could not find brand tracker script!
    echo Please ensure the brand tracker script exists at: %BRAND_TRACKER_DIR%
)

REM Wait for brand tracker to initialize
timeout /t 5 /nobreak > nul

REM Start Median Model
echo Starting Median Model API...
if exist "%MEDIAN_MODEL_DIR%\brand_sentiment_api.py" (
    start "Median Model API" cmd /k "cd /d %MEDIAN_MODEL_DIR% && python brand_sentiment_api.py"
) else (
    echo Error: Could not find brand_sentiment_api.py!
    echo Please ensure brand_sentiment_api.py exists at: %MEDIAN_MODEL_DIR%
)

echo.
echo Brand Guardian System started successfully!
echo - Brand Tracker: Updates results.json every minute
echo - Median Model API: Processes data and serves via http://localhost:5000/api/brand-sentiment
echo.

echo Press any key to close this window...
pause > nul
