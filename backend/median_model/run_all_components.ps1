# Run Brand Tracker and Median Model Asynchronously
Write-Host "Starting Brand Guardian System..." -ForegroundColor Green
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Ensure paths are correct
$brandTrackerPath = Join-Path (Split-Path -Parent $scriptPath) "brand_tracker"
$medianModelPath = $scriptPath

Write-Host "Brand Tracker Path: $brandTrackerPath" -ForegroundColor Cyan
Write-Host "Median Model Path: $medianModelPath" -ForegroundColor Cyan

# Function to start the brand tracker in a new window
function Start-BrandTracker {
    Write-Host "Starting Brand Tracker..." -ForegroundColor Yellow
    
    # Check if run_brand_tracker.py exists
    $brandTrackerScript = Join-Path $brandTrackerPath "run_brand_tracker.py"
    if (Test-Path $brandTrackerScript) {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$brandTrackerPath'; python run_brand_tracker.py"
    } else {
        # Check if brand_tracker.py exists
        $brandTrackerScript = Join-Path $brandTrackerPath "brand_tracker.py"
        if (Test-Path $brandTrackerScript) {
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$brandTrackerPath'; python brand_tracker.py"
        } else {
            Write-Host "Error: Could not find brand tracker script!" -ForegroundColor Red
            Write-Host "Please ensure the brand tracker script exists at: $brandTrackerPath" -ForegroundColor Red
        }
    }
}

# Function to start the median model API in a new window
function Start-MedianModel {
    Write-Host "Starting Median Model API..." -ForegroundColor Yellow
    
    # Check if brand_sentiment_api.py exists
    $apiScript = Join-Path $medianModelPath "brand_sentiment_api.py"
    if (Test-Path $apiScript) {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$medianModelPath'; python brand_sentiment_api.py"
    } else {
        Write-Host "Error: Could not find brand_sentiment_api.py!" -ForegroundColor Red
        Write-Host "Please ensure brand_sentiment_api.py exists at: $medianModelPath" -ForegroundColor Red
    }
}

# Run both components asynchronously
Start-BrandTracker
Start-Sleep -Seconds 5  # Wait for brand tracker to initialize
Start-MedianModel

Write-Host "Brand Guardian System started successfully!" -ForegroundColor Green
Write-Host "- Brand Tracker: Updates results.json every minute" -ForegroundColor White
Write-Host "- Median Model API: Processes data and serves via http://localhost:5000/api/brand-sentiment" -ForegroundColor White
