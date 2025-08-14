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
