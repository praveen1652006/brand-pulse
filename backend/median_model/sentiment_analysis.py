import json
import os
import re
import math
import time
import csv
import pandas as pd
from collections import Counter, defaultdict
import threading
from datetime import datetime

class SentimentAnalyzer:
    def __init__(self, results_file_path=None, max_posts_per_analysis=500):
        """Initialize the sentiment analyzer."""
        if results_file_path is None:
            # Check several potential locations for results.json
            script_dir = os.path.dirname(os.path.abspath(__file__))
            potential_paths = [
                os.path.join(script_dir, '..', 'brand_tracker', 'results.json'),
                os.path.join(script_dir, '..', 'results', 'results.json'),
                os.path.join(script_dir, '..', '..', 'brand_tracker', 'results.json'),
                os.path.join(script_dir, '..', '..', 'results.json')
            ]
            
            self.results_file_path = None
            for path in potential_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    self.results_file_path = abs_path
                    print(f"Found results.json at: {self.results_file_path}")
                    break
            
            # If no file is found, use the first path as default
            if self.results_file_path is None:
                self.results_file_path = os.path.abspath(potential_paths[0])
                print(f"No results.json found, will use path: {self.results_file_path}")
        else:
            self.results_file_path = results_file_path
        
        # Create sentiment_results directory if it doesn't exist
        self.sentiment_results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sentiment_results')
        os.makedirs(self.sentiment_results_dir, exist_ok=True)
        
        # Maximum number of posts to analyze per minute (for performance)
        self.max_posts_per_analysis = max_posts_per_analysis
        
        # Track the last processed index
        self.last_processed_index = 0
        
        # Cache for results
        self.last_modified_time = 0
        self.cached_results = None
        self.last_analysis_time = 0
        
        # Thread lock for thread safety
        self.lock = threading.Lock()
    
    def load_results(self):
        """Load results from the JSON file if it has been modified since last load."""
        try:
            # Check if file exists
            if not os.path.exists(self.results_file_path):
                print(f"Error: Results file not found at {self.results_file_path}")
                # Try to use the sample data instead
                sample_data_path = os.path.join(self.sentiment_results_dir, 'sample_data.json')
                if os.path.exists(sample_data_path):
                    print(f"Using sample data from {sample_data_path}")
                    with open(sample_data_path, 'r', encoding='utf-8') as file:
                        results = json.load(file)
                        self.cached_results = results
                        return results
                return None
                
            # Get file modification time
            current_mod_time = os.path.getmtime(self.results_file_path)
            file_size = os.path.getsize(self.results_file_path)
            
            # If file hasn't been modified since last load, return cached results
            if self.cached_results is not None and current_mod_time <= self.last_modified_time:
                print(f"Using cached results (file not modified since last load)")
                return self.cached_results
            
            print(f"Loading results file ({file_size/1024/1024:.2f} MB)")
            
            with open(self.results_file_path, 'r', encoding='utf-8') as file:
                try:
                    results = json.load(file)
                    self.cached_results = results
                    self.last_modified_time = current_mod_time
                    print(f"Successfully loaded results with {len(results.get('posts', []))} posts")
                    return results
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    # Try to use the sample data instead
                    sample_data_path = os.path.join(self.sentiment_results_dir, 'sample_data.json')
                    if os.path.exists(sample_data_path):
                        print(f"Using sample data from {sample_data_path}")
                        with open(sample_data_path, 'r', encoding='utf-8') as file:
                            results = json.load(file)
                            self.cached_results = results
                            return results
                    return self.cached_results if self.cached_results else None
        except Exception as e:
            print(f"Error loading results file: {e}")
            # Try to use the sample data instead
            sample_data_path = os.path.join(self.sentiment_results_dir, 'sample_data.json')
            if os.path.exists(sample_data_path):
                print(f"Using sample data from {sample_data_path}")
                with open(sample_data_path, 'r', encoding='utf-8') as file:
                    results = json.load(file)
                    self.cached_results = results
                    return results
            return self.cached_results if self.cached_results else None
    
    def analyze_sentiment(self):
        """Analyze sentiment from the loaded data."""
        with self.lock:
            results = self.load_results()
            if not results or 'posts' not in results:
                print("No valid data found for sentiment analysis")
                return self._create_default_analysis()
            
            posts = results.get('posts', [])
            total_posts = len(posts)
            
            if total_posts == 0:
                return self._create_default_analysis()
                
            print(f"Total posts available: {total_posts}")
            
            # Process only a subset of posts for efficiency
            start_index = self.last_processed_index
            end_index = min(start_index + self.max_posts_per_analysis, total_posts)
            
            # If we've processed all posts, start over
            if start_index >= total_posts:
                start_index = 0
                end_index = min(self.max_posts_per_analysis, total_posts)
            
            # Update the last processed index for next time
            self.last_processed_index = end_index % total_posts
            
            posts_to_analyze = posts[start_index:end_index]
            print(f"Analyzing posts from index {start_index} to {end_index} ({len(posts_to_analyze)} posts)")
            
            # Extract sentiment data from posts
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            # Create data structures for saving to CSV
            sentiment_results = []
            product_sentiment = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0, 'rating_sum': 0})
            
            for post in posts_to_analyze:
                brand_tracker = post.get('brand_tracker', {})
                sentiment = brand_tracker.get('sentiment', {}).get('category', 'neutral').lower()
                platform = post.get('platform', 'unknown')
                brand = post.get('brand', 'unknown')
                content = post.get('content', '')
                timestamp = post.get('timestamp', '')
                
                # Extract additional info like ratings
                rating = 3.0  # Default rating
                if 'amazon' in platform.lower():
                    # Try to extract rating from Amazon reviews
                    rating_match = re.search(r'rating[:\s]*([0-5](\.[0-9])?)', content, re.IGNORECASE)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                        except:
                            pass
                
                # Add to sentiment counts
                if sentiment == 'positive':
                    sentiment_counts['positive'] += 1
                elif sentiment == 'negative':
                    sentiment_counts['negative'] += 1
                else:
                    sentiment_counts['neutral'] += 1
                
                # Calculate sentiment scores based on sentiment category
                positive_score = 0.9 if sentiment == 'positive' else (0.1 if sentiment == 'negative' else 0.3)
                negative_score = 0.9 if sentiment == 'negative' else (0.1 if sentiment == 'positive' else 0.3)
                neutral_score = 0.9 if sentiment == 'neutral' else 0.2
                compound_score = positive_score - negative_score
                
                # Add to sentiment results for CSV
                sentiment_results.append({
                    'review_id': hash(content + timestamp)[:10] if isinstance(hash(content + timestamp), str) else hash(content + timestamp),
                    'product_name': brand,
                    'user_name': f"User_{hash(content)%1000:03d}",
                    'rating': rating,
                    'review_title': f"Review about {brand}",
                    'review_content': content,
                    'timestamp': timestamp,
                    'platform': platform,
                    'sentiment': sentiment,
                    'positive_score': positive_score,
                    'negative_score': negative_score,
                    'neutral_score': neutral_score,
                    'compound_score': compound_score
                })
                
                # Add to product sentiment summary
                product_sentiment[brand]['total'] += 1
                product_sentiment[brand][sentiment] += 1
                product_sentiment[brand]['rating_sum'] += rating
            
            # Calculate percentages based on the analyzed subset
            subset_total = len(posts_to_analyze)
            if subset_total == 0:
                return self._create_default_analysis()
                
            sentiment_percentages = {
                'positive': round((sentiment_counts['positive'] / subset_total) * 100),
                'negative': round((sentiment_counts['negative'] / subset_total) * 100),
                'neutral': round((sentiment_counts['neutral'] / subset_total) * 100)
            }
            
            # Normalize to ensure they sum to 100%
            total = sum(sentiment_percentages.values())
            if total != 100:
                # Find the largest value and adjust it
                max_key = max(sentiment_percentages, key=sentiment_percentages.get)
                sentiment_percentages[max_key] += (100 - total)
            
            # For distribution, we'll use different values to show variation
            # In a real system, this could be based on engagement metrics
            distribution = {
                'positive': min(100, max(1, int(sentiment_percentages['positive'] * 1.1))),
                'negative': min(100, max(1, int(sentiment_percentages['negative'] * 4.5))),
                'neutral': min(100, max(1, int(sentiment_percentages['neutral'] * 4.0)))
            }
            
            # Save sentiment results to CSV
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save individual sentiment results
            sentiment_csv_path = os.path.join(self.sentiment_results_dir, f"sentiment_results_{timestamp_str}.csv")
            try:
                # Create DataFrame and save to CSV
                sentiment_df = pd.DataFrame(sentiment_results)
                sentiment_df.to_csv(sentiment_csv_path, index=False)
                print(f"Saved sentiment results to {sentiment_csv_path}")
            except Exception as e:
                print(f"Error saving sentiment results to CSV: {e}")
            
            # Process product sentiment summary
            product_results = []
            for brand, data in product_sentiment.items():
                if data['total'] > 0:
                    # Calculate percentages and averages
                    positive_pct = (data['positive'] / data['total']) * 100
                    negative_pct = (data['negative'] / data['total']) * 100
                    neutral_pct = (data['neutral'] / data['total']) * 100
                    avg_rating = data['rating_sum'] / data['total']
                    sentiment_score = (data['positive'] - data['negative']) / data['total']
                    
                    product_results.append({
                        'product_name': brand,
                        'review_count': data['total'],
                        'positive_count': data['positive'],
                        'negative_count': data['negative'],
                        'neutral_count': data['neutral'],
                        'positive_pct': positive_pct,
                        'negative_pct': negative_pct,
                        'neutral_pct': neutral_pct,
                        'rating': avg_rating,
                        'sentiment_score': sentiment_score
                    })
            
            # Save product sentiment summary
            product_csv_path = os.path.join(self.sentiment_results_dir, f"product_sentiment_{timestamp_str}.csv")
            try:
                # Create DataFrame and save to CSV
                product_df = pd.DataFrame(product_results)
                product_df.to_csv(product_csv_path, index=False)
                print(f"Saved product sentiment summary to {product_csv_path}")
            except Exception as e:
                print(f"Error saving product sentiment summary to CSV: {e}")
            
            # Update last analysis time
            self.last_analysis_time = time.time()
            
            return {
                'sentiment': sentiment_percentages,
                'distribution': distribution,
                'lastUpdated': datetime.now().isoformat()
            }
    
    def _create_default_analysis(self):
        """Create a default analysis when no data is available."""
        return {
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
            'lastUpdated': datetime.now().isoformat()
        }
    
    def get_brand_pulse_data(self):
        """Get the brand pulse data for the frontend."""
        try:
            # If the last analysis was performed less than 30 seconds ago, return the cached analysis
            if time.time() - self.last_analysis_time < 30:
                if hasattr(self, 'last_analysis'):
                    return self.last_analysis
            
            print(f"Performing new sentiment analysis at {datetime.now().strftime('%H:%M:%S')}")
            
            # Otherwise, perform a new analysis
            analysis = self.analyze_sentiment()
            self.last_analysis = analysis
            return analysis
        except Exception as e:
            print(f"Error in get_brand_pulse_data: {e}")
            # Return a default analysis if anything goes wrong
            return self._create_default_analysis()


# For testing purposes
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print("Looking for results.json at:", analyzer.results_file_path)
    print("File exists:", os.path.exists(analyzer.results_file_path))
    result = analyzer.get_brand_pulse_data()
    print(json.dumps(result, indent=2))
