# PowerShell script to run the Brand Tracker application

Write-Host "Starting the Brand Tracker Application..." -ForegroundColor Green

# Start brand tracker in one PowerShell window
$brandTrackerWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\brand_tracker'; python run_async_brand_tracker.py" -PassThru

# Wait a bit for the brand tracker to initialize
Write-Host "Waiting for brand tracker to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start dashboard in another PowerShell window
$dashboardWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\median_model'; python dashboard.py" -PassThru

Write-Host "Application started successfully!" -ForegroundColor Green
Write-Host "- Brand Tracker process ID: $($brandTrackerWindow.Id)" -ForegroundColor Cyan
Write-Host "- Dashboard process ID: $($dashboardWindow.Id)" -ForegroundColor Cyan
Write-Host "Press any key to close this window (the application windows will remain open)..."

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
