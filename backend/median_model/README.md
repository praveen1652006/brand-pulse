# Brand Sentiment Analysis API

This module provides a sentiment analysis API that processes data from `results.json` and serves it to the Brand Guardian Dashboard.

## Features

- Real-time sentiment analysis of brand mentions
- Asynchronous data processing to avoid blocking the API
- Automatic periodic refresh of sentiment data
- API endpoint for sentiment data in the required format

## Setup and Installation

1. Ensure Python 3.8+ is installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the API

### Using Batch File (Windows)
Double-click the `run_sentiment_api.bat` file to start the API.

### Using PowerShell (Windows)
Right-click the `run_sentiment_api.ps1` file and select "Run with PowerShell".

### Manual Start
```
python brand_sentiment_api.py
```

## API Endpoints

- `/api/brand-sentiment`: Returns the sentiment analysis data in the following format:
  ```json
  {
    "sentiment": {
      "positive": 65,
      "negative": 20,
      "neutral": 15
    },
    "distribution": {
      "positive": 70,
      "negative": 90,
      "neutral": 60
    },
    "lastUpdated": "2023-10-15T14:30:45.123Z"
  }
  ```

- `/api/health`: Health check endpoint that returns `{"status": "healthy"}`

## Data Source

The API reads and processes data from `../results/results.json`. The file should contain social media posts with sentiment analysis data in the following format:

```json
{
  "posts": [
    {
      "brand_tracker": {
        "sentiment": {
          "category": "positive",
          "score": 0.85
        },
        ...
      },
      ...
    },
    ...
  ]
}
```

## Integration with Frontend

The Angular frontend should make requests to `http://localhost:5000/api/brand-sentiment` to receive the sentiment data. The data is automatically formatted to match the TypeScript interfaces defined in the frontend.
