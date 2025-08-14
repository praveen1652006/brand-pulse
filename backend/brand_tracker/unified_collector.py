"""
Unified Brand Data Collector

This module collects and combines brand tracker data from multiple sources:
- Twitter
- Reddit
- Google News
- Amazon

It provides a consistent interface for passing real data to the dashboard.
"""
import os
import sys
import json
import time
import logging
import threading
import asyncio
from datetime import datetime
import uuid
import traceback

# Add parent directory to path to import from sibling directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import collectors from sibling directories
try:
    from twitter_scraper.twitter_collector import TwitterCollector
except ImportError:
    print("Twitter collector not found or not available.")
    TwitterCollector = None

try:
    from reddit_scraper.reddit_collector import RedditCollector
except ImportError:
    print("Reddit collector not found or not available.")
    RedditCollector = None

try:
    from amazon_scraper.amazon_collector import AmazonCollector
except ImportError:
    print("Amazon collector not found or not available.")
    AmazonCollector = None

try:
    from google_news.news_collector import NewsCollector
except ImportError:
    print("News collector not found or not available.")
    NewsCollector = None

# Import configuration
try:
    from config import (
        TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, 
        TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN, 
        GOOGLE_NEWS_API_KEY, BRAND_CONFIGS, PLATFORMS
    )
except ImportError:
    print("Configuration not found, using default values.")
    # Default configuration values
    TWITTER_API_KEY = "your_twitter_api_key"
    TWITTER_API_SECRET = "your_twitter_api_secret"
    TWITTER_ACCESS_TOKEN = "your_twitter_access_token"
    TWITTER_ACCESS_TOKEN_SECRET = "your_twitter_access_token_secret"
    TWITTER_BEARER_TOKEN = "your_twitter_bearer_token"
    GOOGLE_NEWS_API_KEY = "your_google_news_api_key"
    PLATFORMS = ["twitter", "reddit", "news", "amazon"]
    BRAND_CONFIGS = {
        "apple": {
            "brand_identifiers": ["Apple", "iPhone", "iPad", "MacBook"],
            "keywords": ["Apple products", "Apple store"],
            "hashtags": ["apple", "iphone", "ipad"],
            "min_posts": 100,
            "interval": 60,
        }
    }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "unified_collector.log"))
    ]
)
logger = logging.getLogger("UnifiedCollector")

class UnifiedBrandDataCollector:
    """
    Collects and combines brand data from multiple sources.
    """
    
    def __init__(self, brand_name=None, output_dir="results", interval=60):
        """Initialize the collector."""
        self.brand_name = brand_name
        self.output_dir = output_dir
        self.interval = interval
        self.results_file = os.path.join(output_dir, "results.json")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize collectors
        self.twitter_collector = None
        self.reddit_collector = None
        self.amazon_collector = None
        self.news_collector = None
        
        # Collection statistics
        self.total_collected = 0
        self.cycles_run = 0
        self.platform_stats = {platform: 0 for platform in PLATFORMS}
        
        # Thread control
        self.running = False
        self.collection_thread = None
        
        # Get brand configuration
        if brand_name and brand_name in BRAND_CONFIGS:
            self.config = BRAND_CONFIGS[brand_name]
        else:
            # Default to first configuration
            self.brand_name = next(iter(BRAND_CONFIGS))
            self.config = BRAND_CONFIGS[self.brand_name]
        
        logger.info(f"Initialized unified collector for brand: {self.brand_name}")
    
    def setup_twitter_collector(self):
        """Set up the Twitter collector."""
        if TwitterCollector is None:
            logger.warning("Twitter collector module not available")
            return False
        
        try:
            self.twitter_collector = TwitterCollector(
                api_key=TWITTER_API_KEY,
                api_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
                bearer_token=TWITTER_BEARER_TOKEN,
                output_dir=os.path.join(self.output_dir, "twitter")
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
                output_dir=os.path.join(self.output_dir, "reddit")
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
                output_dir=os.path.join(self.output_dir, "amazon"),
                use_mock=use_mock
            )
            logger.info("Amazon collector initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Amazon collector: {e}")
            return False
    
    def setup_news_collector(self):
        """Set up the News collector."""
        if NewsCollector is None:
            logger.warning("News collector module not available")
            return False
        
        try:
            self.news_collector = NewsCollector(
                api_key=GOOGLE_NEWS_API_KEY,
                output_dir=os.path.join(self.output_dir, "news")
            )
            logger.info("News collector initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize News collector: {e}")
            return False
    
    def collect_twitter_data(self, brand_identifiers, keywords, hashtags, min_posts=50):
        """Collect Twitter data for brand monitoring."""
        if self.twitter_collector is None:
            logger.warning("Twitter collector not initialized")
            return []
        
        posts = []
        try:
            # Process keywords, hashtags, and brand identifiers
            search_terms = []
            search_terms.extend(brand_identifiers)
            search_terms.extend(keywords)
            
            # Append hashtags with #
            search_terms.extend([f"#{h}" if not h.startswith('#') else h for h in hashtags])
            
            # Calculate posts per term to meet minimum
            posts_per_term = max(min_posts // len(search_terms) if search_terms else min_posts, 10)
            
            # Collect from all search terms
            for term in search_terms:
                logger.info(f"Collecting Twitter data for: {term}")
                term_posts = self.twitter_collector.search_tweets(term, max_tweets=posts_per_term)
                
                # Format posts for unified structure
                for post in term_posts:
                    formatted_post = {
                        'id': post.get('tweet_id', str(uuid.uuid4())),
                        'platform': 'twitter',
                        'brand': self.brand_name,
                        'content': post.get('text_content', ''),
                        'timestamp': post.get('timestamp', datetime.now().isoformat()),
                        'user': post.get('username', 'unknown'),
                        'engagement': {
                            'likes': post.get('engagement_metrics', {}).get('likes', 0),
                            'shares': post.get('engagement_metrics', {}).get('retweets', 0),
                            'comments': post.get('engagement_metrics', {}).get('replies', 0)
                        },
                        'hashtags': post.get('extracted_hashtags', []),
                        'mentions': post.get('extracted_mentions', []),
                        'brand_tracker': {
                            'matched_term': term,
                            'term_type': 'hashtag' if term.startswith('#') else 'brand' if term in brand_identifiers else 'keyword',
                            'sentiment': self._analyze_sentiment(post.get('text_content', ''))
                        }
                    }
                    posts.append(formatted_post)
            
            logger.info(f"Collected {len(posts)} Twitter posts")
            self.platform_stats['twitter'] += len(posts)
            return posts
        
        except Exception as e:
            logger.error(f"Error collecting Twitter data: {e}")
            return []
    
    def collect_reddit_data(self, brand_identifiers, keywords, hashtags, min_posts=50):
        """Collect Reddit data for brand monitoring."""
        if self.reddit_collector is None:
            logger.warning("Reddit collector not initialized")
            return []
        
        posts = []
        try:
            # Process keywords, hashtags, and brand identifiers
            search_terms = []
            search_terms.extend(brand_identifiers)
            search_terms.extend(keywords)
            search_terms.extend(hashtags)  # Reddit doesn't use hashtags, so just use as keywords
            
            # Calculate posts per term to meet minimum
            posts_per_term = max(min_posts // len(search_terms) if search_terms else min_posts, 10)
            
            # Collect from all search terms
            for term in search_terms:
                logger.info(f"Collecting Reddit data for: {term}")
                term_posts = self.reddit_collector.search_posts(term, max_posts=posts_per_term)
                
                # Format posts for unified structure
                for post in term_posts:
                    # Combine title and content for sentiment analysis
                    full_content = f"{post.get('title', '')} {post.get('text_content', '')}"
                    
                    formatted_post = {
                        'id': post.get('post_id', str(uuid.uuid4())),
                        'platform': 'reddit',
                        'brand': self.brand_name,
                        'content': full_content,
                        'timestamp': post.get('timestamp', datetime.now().isoformat()),
                        'user': post.get('author', 'unknown'),
                        'engagement': {
                            'likes': post.get('engagement_metrics', {}).get('upvotes', 0),
                            'shares': 0,  # Reddit doesn't have shares
                            'comments': post.get('engagement_metrics', {}).get('num_comments', 0)
                        },
                        'url': post.get('url', ''),
                        'subreddit': post.get('subreddit', ''),
                        'title': post.get('title', ''),
                        'brand_tracker': {
                            'matched_term': term,
                            'term_type': 'brand' if term in brand_identifiers else 'keyword',
                            'sentiment': self._analyze_sentiment(full_content)
                        }
                    }
                    posts.append(formatted_post)
            
            logger.info(f"Collected {len(posts)} Reddit posts")
            self.platform_stats['reddit'] += len(posts)
            return posts
        
        except Exception as e:
            logger.error(f"Error collecting Reddit data: {e}")
            return []
    
    def collect_news_data(self, brand_identifiers, keywords, min_posts=20):
        """Collect news data for brand monitoring."""
        if self.news_collector is None:
            logger.warning("News collector not initialized")
            return []
        
        posts = []
        try:
            # Process search terms (combine brand identifiers and keywords)
            search_terms = []
            search_terms.extend(brand_identifiers)
            search_terms.extend(keywords)
            
            # Calculate articles per term to meet minimum
            articles_per_term = max(min_posts // len(search_terms) if search_terms else min_posts, 5)
            
            # Collect from all search terms
            for term in search_terms:
                logger.info(f"Collecting news data for: {term}")
                term_articles = self.news_collector.search_news(term, max_results=articles_per_term)
                
                # Format articles for unified structure
                for article in term_articles:
                    # Combine title and description for sentiment analysis
                    full_content = f"{article.get('title', '')} {article.get('description', '')}"
                    
                    formatted_post = {
                        'id': article.get('article_id', str(uuid.uuid4())),
                        'platform': 'news',
                        'brand': self.brand_name,
                        'content': full_content,
                        'timestamp': article.get('published_at', datetime.now().isoformat()),
                        'source': article.get('source', {}).get('name', 'unknown'),
                        'url': article.get('url', ''),
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'brand_tracker': {
                            'matched_term': term,
                            'term_type': 'brand' if term in brand_identifiers else 'keyword',
                            'sentiment': self._analyze_sentiment(full_content)
                        }
                    }
                    posts.append(formatted_post)
            
            logger.info(f"Collected {len(posts)} news articles")
            self.platform_stats['news'] += len(posts)
            return posts
        
        except Exception as e:
            logger.error(f"Error collecting news data: {e}")
            return []
    
    async def collect_amazon_data(self, brand_identifiers, keywords, min_posts=30):
        """Collect Amazon data for brand monitoring."""
        if self.amazon_collector is None:
            logger.warning("Amazon collector not initialized")
            return []
        
        posts = []
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
                
                # Format reviews for unified structure
                for product_reviews in reviews.values():
                    for review in product_reviews:
                        # Extract product information
                        product_name = review.get('product_name', 'Unknown Product')
                        rating = review.get('rating', 0)
                        review_text = review.get('review_text', '')
                        
                        formatted_post = {
                            'id': review.get('review_id', str(uuid.uuid4())),
                            'platform': 'amazon',
                            'brand': brand,
                            'content': review_text,
                            'timestamp': review.get('date', datetime.now().isoformat()),
                            'user': review.get('reviewer_name', 'unknown'),
                            'engagement': {
                                'helpful_votes': review.get('helpful_votes', 0),
                            },
                            'product': {
                                'name': product_name,
                                'rating': rating,
                                'verified_purchase': review.get('verified_purchase', False)
                            },
                            'brand_tracker': {
                                'matched_term': brand,
                                'term_type': 'brand',
                                'sentiment': self._analyze_sentiment_from_rating(rating, review_text)
                            }
                        }
                        posts.append(formatted_post)
            
            logger.info(f"Collected {len(posts)} Amazon reviews")
            self.platform_stats['amazon'] += len(posts)
            return posts
            
        except Exception as e:
            logger.error(f"Error collecting Amazon data: {e}")
            traceback.print_exc()
            return []
    
    def _analyze_sentiment(self, text):
        """
        Simple sentiment analysis based on keyword matching.
        Returns a sentiment object with category and score.
        """
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 
            'wonderful', 'love', 'best', 'happy', 'positive', 'recommend'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'hate',
            'disappointing', 'disappointed', 'negative', 'problem', 'issue', 'fail'
        ]
        
        if not text or not isinstance(text, str):
            return {'category': 'neutral', 'score': 0.0}
        
        # Convert to lowercase and split into words
        words = text.lower().split()
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calculate sentiment score
        total_count = positive_count + negative_count
        if total_count == 0:
            return {'category': 'neutral', 'score': 0.0}
        
        score = (positive_count - negative_count) / total_count
        
        # Categorize sentiment
        if score > 0.2:
            category = 'positive'
        elif score < -0.2:
            category = 'negative'
        else:
            category = 'neutral'
        
        return {'category': category, 'score': score}
    
    def _analyze_sentiment_from_rating(self, rating, text=None):
        """
        Analyze sentiment based on rating and optional text.
        Returns a sentiment object with category and score.
        """
        # Convert rating to a sentiment score in range -1 to 1
        if rating is None or rating == 0:
            score = 0.0
        else:
            # Convert 5-star rating to -1 to 1 range
            score = (rating - 3) / 2
        
        # If text is provided, combine with rating-based score
        if text:
            text_sentiment = self._analyze_sentiment(text)
            text_score = text_sentiment.get('score', 0.0)
            # Weight: 70% rating, 30% text
            score = 0.7 * score + 0.3 * text_score
        
        # Categorize sentiment
        if score > 0.2:
            category = 'positive'
        elif score < -0.2:
            category = 'negative'
        else:
            category = 'neutral'
        
        return {'category': category, 'score': score}
    
    def save_results(self, posts):
        """Save collected posts to the results file."""
        if not posts:
            logger.warning("No posts to save")
            return
        
        # Load existing results if file exists
        existing_posts = []
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_posts = existing_data
                    elif isinstance(existing_data, dict) and 'posts' in existing_data:
                        existing_posts = existing_data['posts']
            except Exception as e:
                logger.error(f"Error loading existing results: {e}")
        
        # Combine with new posts
        all_posts = existing_posts + posts
        
        # Remove duplicates based on id
        unique_posts = []
        seen_ids = set()
        for post in all_posts:
            post_id = post.get('id', '')
            if post_id and post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_posts.append(post)
        
        # Sort by timestamp (newest first)
        sorted_posts = sorted(
            unique_posts, 
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Keep only the latest 1000 posts to avoid file getting too large
        if len(sorted_posts) > 1000:
            sorted_posts = sorted_posts[:1000]
        
        # Save to file
        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_posts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(sorted_posts)} posts to {self.results_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def collection_cycle(self):
        """Run one collection cycle to collect data from all platforms."""
        start_time = time.time()
        logger.info(f"Starting collection cycle {self.cycles_run + 1} for brand: {self.brand_name}")
        
        # Get configuration
        brand_identifiers = self.config.get('brand_identifiers', [])
        keywords = self.config.get('keywords', [])
        hashtags = self.config.get('hashtags', [])
        min_posts = self.config.get('min_posts', 100)
        
        # Calculate min_posts per platform
        platforms_to_collect = []
        if self.twitter_collector:
            platforms_to_collect.append('twitter')
        if self.reddit_collector:
            platforms_to_collect.append('reddit')
        if self.amazon_collector:
            platforms_to_collect.append('amazon')
        if self.news_collector:
            platforms_to_collect.append('news')
        
        if not platforms_to_collect:
            logger.error("No platforms available for collection")
            return []
        
        min_posts_per_platform = max(min_posts // len(platforms_to_collect), 10)
        
        # Collect from all platforms
        all_posts = []
        
        # Twitter
        if 'twitter' in platforms_to_collect:
            twitter_posts = self.collect_twitter_data(
                brand_identifiers, keywords, hashtags, min_posts_per_platform
            )
            all_posts.extend(twitter_posts)
        
        # Reddit
        if 'reddit' in platforms_to_collect:
            reddit_posts = self.collect_reddit_data(
                brand_identifiers, keywords, hashtags, min_posts_per_platform
            )
            all_posts.extend(reddit_posts)
        
        # News
        if 'news' in platforms_to_collect:
            news_posts = self.collect_news_data(
                brand_identifiers, keywords, min_posts_per_platform
            )
            all_posts.extend(news_posts)
        
        # Amazon (async)
        if 'amazon' in platforms_to_collect:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                amazon_posts = loop.run_until_complete(
                    self.collect_amazon_data(brand_identifiers, keywords, min_posts_per_platform)
                )
                loop.close()
                all_posts.extend(amazon_posts)
            except Exception as e:
                logger.error(f"Error collecting Amazon data: {e}")
        
        # Save results
        if all_posts:
            self.save_results(all_posts)
            self.total_collected += len(all_posts)
        
        # Update statistics
        self.cycles_run += 1
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        logger.info(f"Collection cycle took {elapsed:.2f} seconds")
        logger.info(f"Collected {len(all_posts)} posts")
        
        return all_posts
    
    def run_collection(self, max_cycles=None):
        """Run the collection process."""
        logger.info(f"Starting collection for brand: {self.brand_name}")
        logger.info(f"Collection interval: {self.interval} seconds")
        if max_cycles:
            logger.info(f"Maximum cycles: {max_cycles}")
        
        cycle_count = 0
        
        try:
            while self.running:
                cycle_start = time.time()
                
                # Run one collection cycle
                self.collection_cycle()
                
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
    
    def start(self, max_cycles=None):
        """Start the brand data collection process."""
        if self.running:
            logger.warning("Collection is already running")
            return
        
        self.running = True
        
        # Initialize collectors
        self.setup_twitter_collector()
        self.setup_reddit_collector()
        self.setup_amazon_collector()
        self.setup_news_collector()
        
        # Reset statistics
        self.total_collected = 0
        self.cycles_run = 0
        self.platform_stats = {platform: 0 for platform in PLATFORMS}
        
        # Start collection in a separate thread
        self.collection_thread = threading.Thread(
            target=self.run_collection,
            args=(max_cycles,),
            daemon=True
        )
        self.collection_thread.start()
        
        logger.info("Collection started in background thread")
    
    def stop(self):
        """Stop the brand data collection process."""
        if not self.running:
            logger.warning("Collection is not running")
            return
        
        logger.info("Stopping collection...")
        self.running = False
        
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=10)
        
        logger.info("Collection stopped")
        logger.info(f"Collection summary: {self.total_collected} posts in {self.cycles_run} cycles")
        for platform, count in self.platform_stats.items():
            logger.info(f"  - {platform}: {count} posts")


def main():
    """Run the unified brand data collector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect brand data from multiple platforms")
    parser.add_argument("--brand", type=str, help="Brand name from configuration")
    parser.add_argument("--interval", type=int, default=60, help="Collection interval in seconds")
    parser.add_argument("--output-dir", type=str, default="results", help="Output directory")
    parser.add_argument("--max-cycles", type=int, help="Maximum number of cycles to run")
    
    args = parser.parse_args()
    
    # Print available brands
    logger.info("Available brands:")
    for brand in BRAND_CONFIGS.keys():
        logger.info(f"  - {brand}")
    
    # Initialize collector
    collector = UnifiedBrandDataCollector(
        brand_name=args.brand,
        output_dir=args.output_dir,
        interval=args.interval
    )
    
    # Start collection
    try:
        collector.start(max_cycles=args.max_cycles)
        
        # Keep main thread alive
        while collector.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        collector.stop()


if __name__ == "__main__":
    main()
