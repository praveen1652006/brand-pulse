# Brand Tracker with Real-time Dashboard Integration

This application provides a complete brand monitoring solution with a real-time dashboard that updates automatically. The system consists of two main components:

1. **Brand Tracker**: Collects data from various sources (Twitter, Reddit, News, Amazon) about specified brands
2. **Dashboard**: Displays real-time analytics about the collected data

## Flow Architecture

The system operates with the following data flow:

1. The Brand Tracker asynchronously collects data from multiple sources
2. Every minute, the Brand Tracker updates the `results.json` file with new data
3. The Dashboard automatically checks for updates and refreshes when new data is available
4. This creates a seamless real-time monitoring system for brand mentions and sentiment

## Running the Application

### Quick Start

The easiest way to run the complete application is to use the provided scripts:

**For Windows (PowerShell):**
```
.\run_application.ps1
```

**For Windows (Command Prompt):**
```
run_application.bat
```

This will start both the Brand Tracker and Dashboard components in separate windows.

### Manual Start

If you prefer to start the components separately:

1. **Start the Brand Tracker:**
   ```
   cd brand_tracker
   python run_async_brand_tracker.py
   ```

2. **Start the Dashboard:**
   ```
   cd median_model
   python dashboard.py
   ```

## Configuration

### Brand Tracker Configuration

The Brand Tracker can be configured to track specific brands, keywords, and hashtags. When running interactively, you'll be prompted to select a configuration or create a custom one.

### Dashboard Settings

The dashboard has the following settings:

- **Auto-refresh**: Enable/disable automatic refreshing (enabled by default)
- **Refresh interval**: Set how frequently the dashboard checks for updates (default: 60 seconds)

## Requirements

Make sure you have installed all the requirements from the various requirements.txt files:

```
pip install -r brand_tracker/requirements.txt
pip install -r brand_tracker/async_requirements.txt
pip install -r median_model/requirements.txt
```

## Troubleshooting

If you encounter any issues:

1. Ensure all requirements are installed
2. Check that the `results` directory exists at the project root
3. Verify that the Brand Tracker has proper API credentials configured in the config.py file

# Brand Guardian Hackathon Project

## Overview
This project is a real-time brand sentiment analysis and monitoring dashboard. It collects brand mentions from multiple platforms (Twitter, Reddit, News, Amazon), analyzes sentiment, and displays interactive visualizations using Streamlit.

## Features
- **Real-Time Data Collection**: Simulated or real brand mentions are collected and updated live.
- **Sentiment Analysis**: Each mention is analyzed for positive, negative, or neutral sentiment.
- **Dashboard**: Interactive Streamlit dashboard with charts, metrics, and live feed.
- **Platform Breakdown**: See mentions by platform (Twitter, Reddit, News, Amazon).
- **Error Handling**: Robust handling for JSON/data issues and auto-recovery.

## Directory Structure
```
Hackathon_project/
├── backend/
│   ├── brand_tracker/
│   │   ├── run_real_time_simulation.py   # Simulates real-time brand mentions
│   │   ├── results.json                 # Main data file for mentions
│   │   └── ...
│   ├── median_model/
│   │   ├── dashboard.py                 # Streamlit dashboard
│   │   ├── async_data_handler.py        # Watches for data updates
│   │   ├── real_time_feed.py            # Live feed page
│   │   └── ...
│   └── ...
├── requirements.txt                    # Python dependencies
├── README.md                            # Project documentation
└── ...
```

## Quick Start
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the real-time simulation**
   ```bash
   cd backend/brand_tracker
   python run_real_time_simulation.py 5
   ```
   (This generates simulated brand mentions every 5 seconds.)
3. **Start the dashboard**
   ```bash
   cd ../../median_model
   streamlit run dashboard.py
   ```
4. **Open the dashboard**
   - Visit [http://localhost:8501](http://localhost:8501) in your browser.

## Main Components
- **run_real_time_simulation.py**: Generates and updates `results.json` with simulated brand mentions.
- **async_data_handler.py**: Monitors `results.json` for changes and updates dashboard data.
- **dashboard.py**: Main Streamlit dashboard with charts, metrics, and live feed.
- **real_time_feed.py**: Displays the latest brand mentions in real time.

## Troubleshooting
- If you see JSON errors, the system will auto-recover and continue updating.
- If the dashboard does not update, ensure the simulation is running and `results.json` is being updated.
- For missing dependencies, run `pip install -r requirements.txt`.

## Customization
- You can modify `run_real_time_simulation.py` to change brands, platforms, or update frequency.
- To use real data, replace the simulation with actual API collectors in `brand_tracker`.

## License
MIT

## Authors
- Hackathon Team
- GitHub Copilot (AI Assistant)
