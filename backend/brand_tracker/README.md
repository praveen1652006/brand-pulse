# Brand Tracker

A SaaS solution that enables brands to monitor public perception, address concerns early, and optimize messaging in response to real-time sentiment trends.

## Overview

Brand Tracker is a comprehensive social media monitoring tool designed to help brands stay informed about how they are perceived across different platforms. It collects posts from Twitter and Reddit that mention specified brands, analyzes sentiment, and generates detailed reports and metrics.

## Features

- **Multi-platform Monitoring**: Collects data from Twitter and Reddit
- **Real-time Data Collection**: Collects at least 100 posts every 2 minutes
- **Sentiment Analysis**: Categorizes posts as positive, neutral, or negative
- **Engagement Metrics**: Tracks likes, retweets, comments, and other engagement metrics
- **Comprehensive Reporting**: Generates detailed reports and metrics in JSON and Markdown formats
- **Customizable Tracking**: Configure brand identifiers, keywords, and hashtags to monitor

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd Hackathon_project
   ```

2. Install dependencies:
   ```
   pip install -r brand_tracker/requirements.txt
   ```

3. Set up API credentials:
   - Twitter API credentials are already configured in `config.py`
   - To use your own credentials, edit the `config.py` file

## Usage

### Interactive Mode

Run the interactive script to configure and start brand tracking:

```
cd brand_tracker
python run_brand_tracker.py
```

Follow the prompts to:
1. Select a brand configuration (Apple, McDonald's, Nike, Starbucks, Tesla, or custom)
2. Choose which platforms to collect from (Twitter, Reddit)
3. Set the runtime (or run until manually stopped)

### Command Line Mode

You can also run the Brand Tracker directly with specific parameters:

```
python brand_tracker.py --brands "Brand1,Brand2" --keywords "keyword1,keyword2" --hashtags "hashtag1,hashtag2" --platforms "twitter,reddit" --min-posts 100 --interval 120 --output-dir "brand_data"
```

## Configurations

The `config.py` file includes pre-configured settings for several major brands:

- **Apple**: Tracks mentions of Apple products, services, and related topics
- **McDonald's**: Monitors fast food chain mentions and sentiment
- **Nike**: Follows sportswear brand perception and athlete partnerships
- **Starbucks**: Tracks coffee chain mentions and customer sentiment
- **Tesla**: Monitors electric vehicle manufacturer and related topics

You can also create custom configurations through the interactive runner.

## Output

Brand Tracker generates three types of output files:

1. **Raw Data** (`raw_data/`): JSON files containing all collected posts with metadata
2. **Metrics** (`metrics/`): JSON files with aggregated metrics like sentiment distribution and engagement statistics
3. **Reports** (`reports/`): Markdown files with human-readable summaries and visualizations

## Directory Structure

```
brand_tracker/
├── brand_tracker.py        # Main module
├── config.py               # Configuration and API credentials
├── run_brand_tracker.py    # Interactive runner
├── requirements.txt        # Dependencies
├── README.md               # Documentation
└── brand_data_[brand]/     # Generated when tracking a brand
    ├── raw_data/           # Raw JSON data files
    ├── metrics/            # Metrics JSON files
    └── reports/            # Markdown reports
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
