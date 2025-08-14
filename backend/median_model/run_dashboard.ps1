# Run Brand Pulse Dashboard
Write-Host "Starting Brand Pulse Dashboard..." -ForegroundColor Green
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Install required packages
Write-Host "Checking required packages..." -ForegroundColor Cyan
pip install streamlit pandas matplotlib seaborn nltk

# Run the Streamlit dashboard
Write-Host "Starting Streamlit dashboard..." -ForegroundColor Cyan
streamlit run dashboard.py
