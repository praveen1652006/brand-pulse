@echo off
echo Starting the Brand Tracker Application...

:: Start brand tracker in one terminal window
start cmd /k "cd /d %~dp0 && cd brand_tracker && python run_async_brand_tracker.py"

:: Wait a bit for the brand tracker to initialize
timeout /t 5 /nobreak > nul

:: Start dashboard in another terminal window
start cmd /k "cd /d %~dp0 && cd median_model && python dashboard.py"

echo Application started. Please check the terminal windows for details.
echo Press any key to close this window.
pause > nul
