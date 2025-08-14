from flask import Flask, jsonify
from flask_cors import CORS
import os
import time
import threading
from sentiment_analysis import SentimentAnalyzer
from async_data_handler import get_handler

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the sentiment analyzer
analyzer = SentimentAnalyzer()

# Get the async data handler and initialize it
async_data_handler = get_handler()
async_data_handler.start(sentiment_analyzer=analyzer)

# Background task to refresh analysis periodically
def background_analysis():
    """Background task to periodically refresh the sentiment analysis."""
    while True:
        try:
            print(f"Background task: Refreshing sentiment analysis at {time.strftime('%H:%M:%S')}")
            # We don't need to explicitly call analyze_sentiment anymore as the async handler will trigger it
            # Just make sure we get the latest data
            analyzer.get_brand_pulse_data()
            # Sleep for exactly 60 seconds to update every minute
            time.sleep(60)  # Update every minute
        except Exception as e:
            print(f"Error in background analysis: {e}")
            time.sleep(60)  # Wait before trying again

# Start the background task
analysis_thread = threading.Thread(target=background_analysis, daemon=True)
analysis_thread.start()

@app.route('/api/brand-sentiment')
def get_brand_sentiment():
    try:
        # Get real sentiment data from the analyzer
        data = analyzer.get_brand_pulse_data()
        
        # Convert the ISO date string to timestamp for JavaScript
        if isinstance(data.get('lastUpdated'), str):
            # Keep the ISO string format as Angular will parse it correctly
            pass
            
        return jsonify(data)
    except Exception as e:
        print(f"Error serving sentiment data: {e}")
        # Return a fallback response in case of error
        return jsonify({
            'sentiment': {
                'positive': 65,
                'negative': 20,
                'neutral': 15
            },
            'distribution': {
                'positive': 70,
                'negative': 90,
                'neutral': 60
            },
            'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        })

@app.route('/api/health')
def health_check():
    """API endpoint for health check."""
    return jsonify({'status': 'healthy'})

@app.route('/api/latest-mentions')
def get_latest_mentions():
    """API endpoint for getting the latest mentions."""
    try:
        # Get the latest mentions from the async data handler
        mentions = async_data_handler.get_latest_mentions(limit=10)
        
        # Format the mentions for the API
        formatted_mentions = []
        for mention in mentions:
            # Extract timestamp
            timestamp = mention.get('timestamp', '')
            
            # Extract sentiment
            brand_tracker = mention.get('brand_tracker', {})
            sentiment = brand_tracker.get('sentiment', {}).get('category', 'neutral').lower()
            
            formatted_mentions.append({
                'timestamp': timestamp,
                'platform': mention.get('platform', 'Unknown'),
                'brand': mention.get('brand', 'Unknown'),
                'content': mention.get('content', '')[:100] + '...' if len(mention.get('content', '')) > 100 else mention.get('content', ''),
                'sentiment': sentiment
            })
        
        return jsonify({
            'mentions': formatted_mentions,
            'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        })
    except Exception as e:
        print(f"Error serving latest mentions: {e}")
        return jsonify({
            'mentions': [],
            'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        })

if __name__ == '__main__':
    # Default to port 5000, but allow override from environment variable
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Brand Sentiment API on http://localhost:{port}")
    app.run(debug=True, port=port, host='0.0.0.0')
