#!/usr/bin/env python3
"""
Brand Tracker - Monitors social media platforms for brand mentions, keywords, and sentiment.
Collects at least 100 posts every 2 minutes from Twitter and Reddit.
"""

import os
import sys
import json
import time
import signal
import logging
import threading
import argparse
from datetime import datetime
import re
from collections import defaultdict, Counter

# Add parent directory to path to import from sibling directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import collectors from sibling directories
try:
    from twitter_scraper.twitter_collector import TwitterCollector
except ImportError:
    try:
        # Try alternative import with full path
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        from twitter_scraper.twitter_collector import TwitterCollector
    except ImportError:
        print("Twitter collector not found. Make sure it's in the twitter_scraper directory.")
        TwitterCollector = None

try:
    from reddit_scraper.reddit_collector import RedditCollector
except ImportError:
    try:
        # Try alternative import with full path
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        from reddit_scraper.reddit_collector import RedditCollector
    except ImportError:
        print("Reddit collector not found. Make sure it's in the reddit_scraper directory.")
        RedditCollector = None

try:
    from amazon_scraper.amazon_collector import AmazonCollector
except ImportError:
    try:
        # Try alternative import with full path
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        from amazon_scraper.amazon_collector import AmazonCollector
    except ImportError:
        print("Amazon collector not found. Make sure it's in the amazon_scraper directory.")
        AmazonCollector = None

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrandTracker:
    """
    Tracks brand mentions, keywords, and sentiment across multiple social media platforms.
    """
    
    def __init__(self, output_dir="brand_data", interval=120):
        """Initialize the BrandTracker."""
        self.output_dir = output_dir
        self.interval = interval
        
        # Create output directory structure
        os.makedirs(output_dir, exist_ok=True)
        self.raw_data_dir = os.path.join(output_dir, "raw_data")
        self.reports_dir = os.path.join(output_dir, "reports")
        self.metrics_dir = os.path.join(output_dir, "metrics")
        
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Initialize collectors
        self.twitter_collector = None
        self.reddit_collector = None
        self.amazon_collector = None
        
        # Collection statistics
        self.total_collected = 0
        self.cycles_run = 0
        self.platform_stats = defaultdict(int)
        self.brand_stats = defaultdict(int)
        
        # Thread control
        self.running = False
        self.collection_thread = None
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
        logger.info(f"Collection summary: {self.total_collected} posts in {self.cycles_run} cycles")
        for platform, count in self.platform_stats.items():
            logger.info(f"  - {platform}: {count} posts")
        for brand, count in self.brand_stats.items():
            logger.info(f"  - Brand '{brand}': {count} mentions")
        sys.exit(0)
    
    def setup_twitter_collector(self, api_key, api_secret, access_token, access_token_secret, bearer_token=None):
        """Set up the Twitter collector."""
        if TwitterCollector is None:
            logger.warning("Twitter collector module not available")
            return False
        
        try:
            self.twitter_collector = TwitterCollector(
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                bearer_token=bearer_token,
                output_dir=os.path.join(self.raw_data_dir, "twitter")
            )
            logger.info("Twitter collector initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Twitter collector: {e}")
            return False
    
    def setup_reddit_collector(self):
        """Set up the Reddit collector."""
        if RedditCollector is None:
            logger.warning("Reddit collector module not available")
            return False
        
        try:
            self.reddit_collector = RedditCollector(
                output_dir=os.path.join(self.raw_data_dir, "reddit")
            )
            logger.info("Reddit collector initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Reddit collector: {e}")
            return False
    
    def setup_amazon_collector(self, use_mock=True):
        """Set up the Amazon collector."""
        if AmazonCollector is None:
            logger.warning("Amazon collector module not available")
            return False
        
        try:
            self.amazon_collector = AmazonCollector(
                output_dir=os.path.join(self.raw_data_dir, "amazon"),
                use_mock=use_mock
            )
            logger.info("Amazon collector initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Amazon collector: {e}")
            return False
    
    def collect_twitter_data(self, brand_identifiers, keywords, hashtags, min_posts=50):
        """Collect Twitter data for brand monitoring."""
        if self.twitter_collector is None:
            logger.warning("Twitter collector not initialized")
            return []
        
        twitter_posts = []
        
        try:
            # Adjust min_posts to ensure we get enough posts
            posts_per_term = max(min_posts // len(brand_identifiers) if brand_identifiers else min_posts, 20)
            
            # Collect from brand identifiers
            for brand in brand_identifiers:
                logger.info(f"Collecting Twitter data for brand: {brand}")
                posts = self.twitter_collector.search_tweets(brand, max_tweets=posts_per_term)
                for post in posts:
                    post['platform'] = 'twitter'
                    post['brand_tracker'] = {
                        'matched_term': brand,
                        'term_type': 'brand'
                    }
                twitter_posts.extend(posts)
                logger.info(f"Collected {len(posts)} tweets for brand: {brand}")
            
            # Collect from keywords
            for keyword in keywords:
                logger.info(f"Collecting Twitter data for keyword: {keyword}")
                posts = self.twitter_collector.search_tweets(keyword, max_tweets=posts_per_term)
                for post in posts:
                    post['platform'] = 'twitter'
                    post['brand_tracker'] = {
                        'matched_term': keyword,
                        'term_type': 'keyword'
                    }
                twitter_posts.extend(posts)
                logger.info(f"Collected {len(posts)} tweets for keyword: {keyword}")
            
            # Collect from hashtags
            for hashtag in hashtags:
                query = f"#{hashtag}"
                logger.info(f"Collecting Twitter data for hashtag: {query}")
                posts = self.twitter_collector.search_tweets(query, max_tweets=posts_per_term)
                for post in posts:
                    post['platform'] = 'twitter'
                    post['brand_tracker'] = {
                        'matched_term': hashtag,
                        'term_type': 'hashtag'
                    }
                twitter_posts.extend(posts)
                logger.info(f"Collected {len(posts)} tweets for hashtag: {query}")
            
            # Remove duplicates
            unique_posts = []
            seen_ids = set()
            for post in twitter_posts:
                if post['tweet_id'] not in seen_ids:
                    seen_ids.add(post['tweet_id'])
                    unique_posts.append(post)
            
            logger.info(f"Collected {len(unique_posts)} unique tweets")
            self.platform_stats['twitter'] += len(unique_posts)
            
            # Count brand mentions
            for brand in brand_identifiers:
                brand_mentions = sum(1 for post in unique_posts if brand.lower() in post['text_content'].lower())
                self.brand_stats[brand] += brand_mentions
                logger.info(f"Brand '{brand}' mentioned in {brand_mentions} tweets")
            
            return unique_posts
        
        except Exception as e:
            logger.error(f"Error collecting Twitter data: {e}")
            return []
    
    def collect_reddit_data(self, brand_identifiers, keywords, hashtags, min_posts=50):
        """Collect Reddit data for brand monitoring."""
        if self.reddit_collector is None:
            logger.warning("Reddit collector not initialized")
            return []
        
        reddit_posts = []
        
        try:
            # Adjust min_posts to ensure we get enough posts
            posts_per_term = max(min_posts // len(brand_identifiers) if brand_identifiers else min_posts, 20)
            
            # Collect from brand identifiers
            for brand in brand_identifiers:
                logger.info(f"Collecting Reddit data for brand: {brand}")
                posts = self.reddit_collector.search_posts(brand, max_posts=posts_per_term)
                for post in posts:
                    post['platform'] = 'reddit'
                    post['brand_tracker'] = {
                        'matched_term': brand,
                        'term_type': 'brand'
                    }
                reddit_posts.extend(posts)
                logger.info(f"Collected {len(posts)} Reddit posts for brand: {brand}")
            
            # Collect from keywords
            for keyword in keywords:
                logger.info(f"Collecting Reddit data for keyword: {keyword}")
                posts = self.reddit_collector.search_posts(keyword, max_posts=posts_per_term)
                for post in posts:
                    post['platform'] = 'reddit'
                    post['brand_tracker'] = {
                        'matched_term': keyword,
                        'term_type': 'keyword'
                    }
                reddit_posts.extend(posts)
                logger.info(f"Collected {len(posts)} Reddit posts for keyword: {keyword}")
            
            # Collect from hashtags (as keywords on Reddit)
            for hashtag in hashtags:
                logger.info(f"Collecting Reddit data for hashtag: {hashtag}")
                posts = self.reddit_collector.search_posts(hashtag, max_posts=posts_per_term)
                for post in posts:
                    post['platform'] = 'reddit'
                    post['brand_tracker'] = {
                        'matched_term': hashtag,
                        'term_type': 'hashtag'
                    }
                reddit_posts.extend(posts)
                logger.info(f"Collected {len(posts)} Reddit posts for hashtag: {hashtag}")
            
            # Remove duplicates
            unique_posts = []
            seen_ids = set()
            for post in reddit_posts:
                if post['post_id'] not in seen_ids:
                    seen_ids.add(post['post_id'])
                    unique_posts.append(post)
            
            logger.info(f"Collected {len(unique_posts)} unique Reddit posts")
            self.platform_stats['reddit'] += len(unique_posts)
            
            # Count brand mentions
            for brand in brand_identifiers:
                # Check both title and content
                brand_mentions = sum(1 for post in unique_posts if 
                                  brand.lower() in post.get('title', '').lower() or 
                                  brand.lower() in post.get('text_content', '').lower())
                self.brand_stats[brand] += brand_mentions
                logger.info(f"Brand '{brand}' mentioned in {brand_mentions} Reddit posts")
            
            return unique_posts
        
        except Exception as e:
            logger.error(f"Error collecting Reddit data: {e}")
            return []
    
    async def collect_amazon_data(self, brand_identifiers, keywords, hashtags, min_posts=50):
        """Collect Amazon data for brand monitoring."""
        if self.amazon_collector is None:
            logger.warning("Amazon collector not initialized")
            return []
        
        amazon_posts = []
        
        try:
            # Adjust min_posts to ensure we get enough posts
            posts_per_brand = max(min_posts // len(brand_identifiers) if brand_identifiers else min_posts, 10)
            max_products = 3  # Number of products to fetch per brand
            max_reviews_per_product = max(posts_per_brand // max_products, 5)  # Reviews per product
            
            # Collect from brand identifiers
            for brand in brand_identifiers:
                logger.info(f"Collecting Amazon data for brand: {brand}")
                # Use keywords as product keywords for this brand if available
                brand_keywords = keywords if keywords else None
                
                reviews = await self.amazon_collector.collect_brand_reviews(
                    brand,
                    product_keywords=brand_keywords,
                    max_products=max_products,
                    max_reviews_per_product=max_reviews_per_product,
                    days_ago=30  # Get reviews from the last 30 days
                )
                
                # Format reviews for brand tracker format
                formatted_reviews = self.amazon_collector.format_reviews_for_brand_tracker(reviews)
                amazon_posts.extend(formatted_reviews)
                
                logger.info(f"Collected {len(formatted_reviews)} Amazon reviews for brand: {brand}")
            
            # Remove duplicates
            unique_posts = []
            seen_ids = set()
            for post in amazon_posts:
                if post['review_id'] not in seen_ids:
                    seen_ids.add(post['review_id'])
                    unique_posts.append(post)
            
            logger.info(f"Collected {len(unique_posts)} unique Amazon reviews")
            self.platform_stats['amazon'] += len(unique_posts)
            
            # Count brand mentions
            for brand in brand_identifiers:
                # Check title and text content
                brand_mentions = sum(1 for post in unique_posts if 
                                  brand.lower() in post.get('title', '').lower() or 
                                  brand.lower() in post.get('text_content', '').lower())
                self.brand_stats[brand] += brand_mentions
                logger.info(f"Brand '{brand}' mentioned in {brand_mentions} Amazon reviews")
            
            return unique_posts
            
        except Exception as e:
            logger.error(f"Error collecting Amazon data: {e}")
            return []
    
    def analyze_sentiment(self, text):
        """
        Simple sentiment analysis based on keyword matching.
        Returns a sentiment score from -1.0 (negative) to 1.0 (positive).
        """
        # This is a placeholder for a more sophisticated sentiment analysis solution
        # In a real-world scenario, you would use a proper NLP library or API
        
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 
            'wonderful', 'love', 'best', 'happy', 'positive', 'recommend'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'hate',
            'disappointing', 'disappointed', 'negative', 'problem', 'issue', 'fail'
        ]
        
        if not text:
            return 0.0
        
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calculate sentiment score
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_count
    
    def categorize_sentiment(self, score):
        """Categorize sentiment score into positive, neutral, or negative."""
        if score > 0.2:
            return "positive"
        elif score < -0.2:
            return "negative"
        else:
            return "neutral"
    
    def analyze_posts(self, posts, brand_identifiers):
        """Analyze posts for sentiment and categorize them."""
        for post in posts:
            # Get the text content to analyze
            if post.get('platform') == 'twitter':
                text = post.get('text_content', '')
            elif post.get('platform') == 'reddit':
                title = post.get('title', '')
                content = post.get('text_content', '')
                text = f"{title} {content}"
            else:
                text = post.get('text_content', '')
            
            # Analyze sentiment
            sentiment_score = self.analyze_sentiment(text)
            sentiment_category = self.categorize_sentiment(sentiment_score)
            
            # Add sentiment data to post
            post['brand_tracker']['sentiment'] = {
                'score': sentiment_score,
                'category': sentiment_category
            }
            
            # Check which brands are mentioned
            post['brand_tracker']['brands_mentioned'] = [
                brand for brand in brand_identifiers 
                if brand.lower() in text.lower()
            ]
        
        return posts
    
    def save_brand_data(self, posts, cycle_number):
        """Save collected brand data to JSON file."""
        if not posts:
            logger.warning("No posts to save")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"brand_data_cycle{cycle_number}_{timestamp}.json"
        filepath = os.path.join(self.raw_data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(posts)} posts to {filepath}")
        return filepath
    
    def generate_metrics(self, posts, brand_identifiers, cycle_number):
        """Generate metrics from collected brand data."""
        if not posts:
            logger.warning("No posts for metrics generation")
            return None
        
        # Initialize metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cycle_number': cycle_number,
            'total_posts': len(posts),
            'platform_distribution': Counter(),
            'brand_mentions': {brand: 0 for brand in brand_identifiers},
            'sentiment_distribution': {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            },
            'brand_sentiment': {
                brand: {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0,
                    'average_score': 0.0
                } for brand in brand_identifiers
            },
            'engagement': {
                'twitter': {
                    'total_likes': 0,
                    'total_retweets': 0,
                    'total_replies': 0
                },
                'reddit': {
                    'total_upvotes': 0,
                    'total_comments': 0
                },
                'amazon': {
                    'total_helpful_votes': 0,
                    'total_ratings': 0,
                    'sum_ratings': 0,
                    'average_rating': 0.0,
                    'verified_purchases': 0,
                    'verified_percentage': 0.0
                }
            }
        }
        
        
        # Calculate metrics
        for post in posts:
            # Platform distribution
            platform = post.get('platform', 'unknown')
            metrics['platform_distribution'][platform] += 1
            
            # Brand mentions
            brands_mentioned = post.get('brand_tracker', {}).get('brands_mentioned', [])
            for brand in brands_mentioned:
                metrics['brand_mentions'][brand] += 1
            
            # Sentiment distribution
            sentiment = post.get('brand_tracker', {}).get('sentiment', {}).get('category', 'neutral')
            metrics['sentiment_distribution'][sentiment] += 1
            
            # Brand sentiment
            for brand in brands_mentioned:
                metrics['brand_sentiment'][brand][sentiment] += 1
            
            # Engagement metrics
            if platform == 'twitter':
                engagement = post.get('engagement_metrics', {})
                metrics['engagement']['twitter']['total_likes'] += engagement.get('likes', 0)
                metrics['engagement']['twitter']['total_retweets'] += engagement.get('retweets', 0)
                metrics['engagement']['twitter']['total_replies'] += engagement.get('replies', 0)
            elif platform == 'reddit':
                engagement = post.get('engagement_metrics', {})
                metrics['engagement']['reddit']['total_upvotes'] += engagement.get('upvotes', 0)
                metrics['engagement']['reddit']['total_comments'] += engagement.get('num_comments', 0)
            elif platform == 'amazon':
                engagement = post.get('engagement_metrics', {})
                metrics['engagement']['amazon']['total_helpful_votes'] += engagement.get('helpful_votes', 0)
                
                # Track ratings
                rating = post.get('rating', 0)
                if rating > 0:
                    metrics['engagement']['amazon']['total_ratings'] += 1
                    metrics['engagement']['amazon']['sum_ratings'] += rating
                
                # Track verified purchases
                if post.get('verified_purchase', False):
                    metrics['engagement']['amazon']['verified_purchases'] += 1
        
        # Calculate average sentiment score for each brand
        for brand in brand_identifiers:
            brand_posts = [
                post for post in posts 
                if brand in post.get('brand_tracker', {}).get('brands_mentioned', [])
            ]
            
            if brand_posts:
                total_score = sum(
                    post.get('brand_tracker', {}).get('sentiment', {}).get('score', 0.0) 
                    for post in brand_posts
                )
                metrics['brand_sentiment'][brand]['average_score'] = total_score / len(brand_posts)
        
        # Calculate Amazon statistics
        amazon_posts = [post for post in posts if post.get('platform') == 'amazon']
        if amazon_posts:
            # Calculate average rating
            if metrics['engagement']['amazon']['total_ratings'] > 0:
                metrics['engagement']['amazon']['average_rating'] = (
                    metrics['engagement']['amazon']['sum_ratings'] / 
                    metrics['engagement']['amazon']['total_ratings']
                )
            
            # Calculate verified purchase percentage
            amazon_post_count = len(amazon_posts)
            if amazon_post_count > 0:
                metrics['engagement']['amazon']['verified_percentage'] = (
                    metrics['engagement']['amazon']['verified_purchases'] / amazon_post_count * 100
                )
        
        # Save metrics to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_cycle{cycle_number}_{timestamp}.json"
        filepath = os.path.join(self.metrics_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved metrics to {filepath}")
        return metrics
    
    def generate_report(self, metrics, cycle_number):
        """Generate a human-readable report from metrics."""
        if not metrics:
            logger.warning("No metrics for report generation")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_cycle{cycle_number}_{timestamp}.md"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Brand Tracking Report - Cycle {cycle_number}\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- Total posts collected: **{metrics['total_posts']}**\n")
            f.write("- Platform distribution:\n")
            for platform, count in metrics['platform_distribution'].items():
                f.write(f"  - {platform.capitalize()}: {count} posts ({count/metrics['total_posts']*100:.1f}%)\n")
            
            f.write("\n## Brand Mentions\n\n")
            for brand, count in metrics['brand_mentions'].items():
                f.write(f"- **{brand}**: {count} mentions\n")
            
            f.write("\n## Sentiment Analysis\n\n")
            f.write("### Overall Sentiment\n\n")
            f.write("| Sentiment | Count | Percentage |\n")
            f.write("|-----------|-------|------------|\n")
            for sentiment, count in metrics['sentiment_distribution'].items():
                percentage = count/metrics['total_posts']*100 if metrics['total_posts'] > 0 else 0
                f.write(f"| {sentiment.capitalize()} | {count} | {percentage:.1f}% |\n")
            
            f.write("\n### Brand Sentiment\n\n")
            f.write("| Brand | Positive | Neutral | Negative | Average Score |\n")
            f.write("|-------|----------|---------|----------|---------------|\n")
            for brand, sentiment in metrics['brand_sentiment'].items():
                f.write(f"| {brand} | {sentiment['positive']} | {sentiment['neutral']} | {sentiment['negative']} | {sentiment['average_score']:.2f} |\n")
            
            f.write("\n## Engagement Metrics\n\n")
            f.write("### Twitter Engagement\n\n")
            twitter_engagement = metrics['engagement']['twitter']
            f.write(f"- Total likes: {twitter_engagement['total_likes']}\n")
            f.write(f"- Total retweets: {twitter_engagement['total_retweets']}\n")
            f.write(f"- Total replies: {twitter_engagement['total_replies']}\n")
            
            f.write("\n### Reddit Engagement\n\n")
            reddit_engagement = metrics['engagement']['reddit']
            f.write(f"- Total upvotes: {reddit_engagement['total_upvotes']}\n")
            f.write(f"- Total comments: {reddit_engagement['total_comments']}\n")
            
            # Add Amazon engagement metrics if available
            if 'amazon' in metrics['engagement']:
                f.write("\n### Amazon Engagement\n\n")
                amazon_engagement = metrics['engagement']['amazon']
                f.write(f"- Total helpful votes: {amazon_engagement['total_helpful_votes']}\n")
                f.write(f"- Average rating: {amazon_engagement['average_rating']:.1f}/5.0\n")
                f.write(f"- Verified purchases: {amazon_engagement['verified_purchases']} ({amazon_engagement['verified_percentage']:.1f}%)\n")
        
        logger.info(f"Generated report: {filepath}")
        return filepath
    
    def collection_cycle(self, brand_identifiers, keywords, hashtags, min_posts=100):
        """Run one collection cycle."""
        start_time = time.time()
        logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting collection cycle {self.cycles_run + 1}")
        
        all_posts = []
        platforms_to_collect = []
        
        # Check which platforms are available
        if self.twitter_collector:
            platforms_to_collect.append('twitter')
        if self.reddit_collector:
            platforms_to_collect.append('reddit')
        if self.amazon_collector:
            platforms_to_collect.append('amazon')
            
        if not platforms_to_collect:
            logger.error("No collector platforms available. Please set up at least one platform.")
            return []
            
        # Calculate posts per platform
        posts_per_platform = min_posts // len(platforms_to_collect)
        
        # Collect Twitter data
        if 'twitter' in platforms_to_collect:
            twitter_posts = self.collect_twitter_data(brand_identifiers, keywords, hashtags, posts_per_platform)
            all_posts.extend(twitter_posts)
        
        # Collect Reddit data
        if 'reddit' in platforms_to_collect:
            reddit_posts = self.collect_reddit_data(brand_identifiers, keywords, hashtags, posts_per_platform)
            all_posts.extend(reddit_posts)
        
        # Collect Amazon data
        if 'amazon' in platforms_to_collect:
            # Since amazon_collector uses async methods, we need to handle this differently
            import asyncio
            try:
                # Get event loop or create one if it doesn't exist
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run the async collection method
                amazon_posts = loop.run_until_complete(
                    self.collect_amazon_data(brand_identifiers, keywords, hashtags, posts_per_platform)
                )
                all_posts.extend(amazon_posts)
            except Exception as e:
                logger.error(f"Error collecting Amazon data: {e}")
        
        # Analyze posts
        analyzed_posts = self.analyze_posts(all_posts, brand_identifiers)
        
        # Save data
        if analyzed_posts:
            self.save_brand_data(analyzed_posts, self.cycles_run + 1)
            
            # Generate metrics and report
            metrics = self.generate_metrics(analyzed_posts, brand_identifiers, self.cycles_run + 1)
            if metrics:
                self.generate_report(metrics, self.cycles_run + 1)
            
            self.total_collected += len(analyzed_posts)
        else:
            logger.warning("No posts collected in this cycle")
        
        # Update statistics
        self.cycles_run += 1
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        logger.info(f"Collection cycle took {elapsed:.2f} seconds")
        
        return analyzed_posts
    
    def run_collection(self, brand_identifiers, keywords, hashtags, min_posts=100, max_cycles=None):
        """Run the collection process."""
        if not brand_identifiers:
            logger.error("No brand identifiers provided")
            return
        
        logger.info(f"Starting brand tracker with:")
        logger.info(f"- Brand identifiers: {brand_identifiers}")
        logger.info(f"- Keywords: {keywords}")
        logger.info(f"- Hashtags: {hashtags}")
        logger.info(f"- Minimum posts per cycle: {min_posts}")
        logger.info(f"- Collection interval: {self.interval} seconds")
        if max_cycles:
            logger.info(f"- Maximum cycles: {max_cycles}")
        
        cycle_count = 0
        
        try:
            while self.running:
                cycle_start = time.time()
                
                # Run one collection cycle
                self.collection_cycle(brand_identifiers, keywords, hashtags, min_posts)
                
                cycle_count += 1
                if max_cycles and cycle_count >= max_cycles:
                    logger.info(f"Reached maximum number of cycles ({max_cycles}), stopping")
                    break
                
                # Calculate time to wait until next cycle
                elapsed = time.time() - cycle_start
                wait_time = max(0, self.interval - elapsed)
                
                if wait_time > 0 and self.running:
                    logger.info(f"Waiting {wait_time:.2f} seconds until next collection cycle...")
                    time.sleep(wait_time)
                
        except Exception as e:
            logger.error(f"Error in collection process: {e}")
        finally:
            logger.info("Collection process finished")
    
    def start(self, brand_identifiers, keywords=None, hashtags=None, min_posts=100, max_cycles=None):
        """Start the brand tracking process."""
        if self.running:
            logger.warning("Brand tracker is already running")
            return
        
        self.running = True
        
        # Ensure we have lists
        keywords = keywords or []
        hashtags = hashtags or []
        
        # Reset statistics
        self.total_collected = 0
        self.cycles_run = 0
        self.platform_stats = defaultdict(int)
        self.brand_stats = defaultdict(int)
        
        # Run collection directly
        self.run_collection(brand_identifiers, keywords, hashtags, min_posts, max_cycles)
        
        logger.info("Brand tracker started. Press Ctrl+C to stop.")
    
    def stop(self):
        """Stop the brand tracking process."""
        if not self.running:
            logger.warning("Brand tracker is not running")
            return
        
        logger.info("Stopping brand tracker...")
        self.running = False
        
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=10)
        
        logger.info("Brand tracker stopped")
        logger.info(f"Collection summary: {self.total_collected} posts in {self.cycles_run} cycles")
        for platform, count in self.platform_stats.items():
            logger.info(f"  - {platform}: {count} posts")
        for brand, count in self.brand_stats.items():
            logger.info(f"  - Brand '{brand}': {count} mentions")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Track brand mentions across social media platforms.")
    
    # Twitter API credentials
    parser.add_argument("--api-key", help="Twitter API key")
    parser.add_argument("--api-secret", help="Twitter API secret")
    parser.add_argument("--access-token", help="Twitter access token")
    parser.add_argument("--access-token-secret", help="Twitter access token secret")
    parser.add_argument("--bearer-token", help="Twitter bearer token (for v2 API)")
    
    # Brand tracking parameters
    parser.add_argument("--brands", required=True, help="Comma-separated list of brand identifiers to track")
    parser.add_argument("--keywords", help="Comma-separated list of keywords to track")
    parser.add_argument("--hashtags", help="Comma-separated list of hashtags to track")
    parser.add_argument("--min-posts", type=int, default=100, help="Minimum number of posts to collect per cycle")
    parser.add_argument("--interval", type=int, default=120, help="Collection interval in seconds")
    parser.add_argument("--max-cycles", type=int, help="Maximum number of collection cycles to run")
    parser.add_argument("--output-dir", default="brand_data", help="Output directory for collected data")
    
    # Platforms to use
    parser.add_argument("--platforms", default="twitter,reddit", help="Comma-separated list of platforms to collect from")
    
    return parser.parse_args()


def main():
    """Main function to run the brand tracker from command line."""
    args = parse_args()
    
    # Parse brand identifiers and keywords
    brand_identifiers = [b.strip() for b in args.brands.split(",") if b.strip()]
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
    hashtags = [h.strip() for h in args.hashtags.split(",")] if args.hashtags else []
    platforms = [p.strip().lower() for p in args.platforms.split(",")] if args.platforms else ["twitter", "reddit"]
    
    if not brand_identifiers:
        logger.error("No brand identifiers provided")
        return
    
    # Initialize brand tracker
    tracker = BrandTracker(output_dir=args.output_dir, interval=args.interval)
    
    # Set up collectors based on selected platforms
    if "twitter" in platforms and all([args.api_key, args.api_secret, args.access_token, args.access_token_secret]):
        tracker.setup_twitter_collector(
            api_key=args.api_key,
            api_secret=args.api_secret,
            access_token=args.access_token,
            access_token_secret=args.access_token_secret,
            bearer_token=args.bearer_token
        )
    elif "twitter" in platforms:
        logger.warning("Twitter API credentials not provided, Twitter collection disabled")
    
    if "reddit" in platforms:
        tracker.setup_reddit_collector()
    
    # Start brand tracking
    try:
        tracker.start(
            brand_identifiers=brand_identifiers,
            keywords=keywords,
            hashtags=hashtags,
            min_posts=args.min_posts,
            max_cycles=args.max_cycles
        )
        
        # Keep the main thread alive
        while tracker.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        tracker.stop()


if __name__ == "__main__":
    main()
