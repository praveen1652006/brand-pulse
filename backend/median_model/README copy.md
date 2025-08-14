# Brand Sentiment Analysis & Dashboard

This tool analyzes sentiment from brand mentions collected across social media platforms and generates an interactive dashboard with comprehensive insights.

## Features

- Filters out duplicate and irrelevant content
- Analyzes sentiment (positive, negative, neutral) for each mention
- Generates overall sentiment distribution statistics
- Creates interactive visualizations
- Product-specific sentiment analysis
- Interactive dashboard to explore reviews and insights
- Real-time mentions feed with live sentiment tagging
- Saves detailed results to CSV for further analysis

## Requirements

- Python 3.7+
- Required packages listed in `requirements.txt`

## Quick Start

The easiest way to get started is to use the included batch files:

1. Double-click `run_dashboard.bat`
2. Choose option 1 to run the sentiment analysis
3. Then choose option 2 to launch the interactive dashboard

## Manual Installation

1. Create a virtual environment (optional but recommended):
```
python -m venv .venv
.venv\Scripts\activate
```

2. Install required packages:
```
pip install -r requirements.txt
```

## Usage

### Running the Sentiment Analyzer

```
python sentiment_analyzer.py
```

The tool will:
- Load the Amazon product review data
- Filter out irrelevant records
- Analyze sentiment
- Print a summary
- Save detailed results and visualizations to the `sentiment_results` folder

### Launching the Dashboard

```
streamlit run dashboard.py
```

This will start a local web server and open the dashboard in your browser. The dashboard allows you to:
- View overall sentiment distribution
- Explore product-specific sentiment analysis
- Read and filter individual reviews
- Monitor real-time brand mentions with sentiment tags
- Generate visualizations
- Download the raw data

## Input CSV Format

The tool is configured to work with Amazon product reviews in the following format:
- `product_id`: Unique identifier for the product
- `product_name`: Name of the product
- `review_content`: The text of the review to analyze
- `rating`: Numeric rating (typically 1-5 stars)

For other data sources, the script will automatically detect text columns such as:
- `content`
- `text`
- `review`
- `comment`

## Output

- Interactive Streamlit dashboard
- Console summary showing sentiment distribution percentages
- CSV files with detailed results including sentiment scores
- Visualizations (pie charts, bar charts, scatter plots)

All output files are saved with timestamps in the `sentiment_results` directory.
