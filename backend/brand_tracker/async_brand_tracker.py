#!/usr/bin/env python3
"""
Asynchronous Brand Tracker - Monitors social media platforms for brand mentions.
Collects at least 100 posts every minute from Twitter and Reddit using asynchronous requests.
"""

import os
import sys
import json
import time
import signal
import logging
import asyncio
import traceback
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsyncBrandTracker:
    """
    Tracks brand mentions, keywords, and sentiment across multiple social media platforms
    using asynchronous requests.
    """
    
    def __init__(self, output_dir="brand_data", interval=60):
        """Initialize the AsyncBrandTracker."""
        self.output_dir = output_dir
        self.interval = interval
        
        # Create main output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a single consolidated brand data directory
        self.brand_data_dir = os.path.join(output_dir, "brand_data")
        os.makedirs(self.brand_data_dir, exist_ok=True)
        
        # Results JSON file path for cumulative results - using central results.json
        self.results_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "results.json")
        self.last_results_update = 0  # Timestamp of last results.json update
        
        # Create other directories for organization
        self.raw_data_dir = os.path.join(output_dir, "raw_data")
        self.reports_dir = os.path.join(output_dir, "reports")
        self.metrics_dir = os.path.join(output_dir, "metrics")
        
        # Create platform-specific directories inside the brand_data directory
        self.twitter_dir = os.path.join(self.brand_data_dir, "twitter")
        self.reddit_dir = os.path.join(self.brand_data_dir, "reddit")
        self.news_dir = os.path.join(self.brand_data_dir, "news")
        self.amazon_dir = os.path.join(self.brand_data_dir, "amazon")
        
        # Create directories for combined data, metrics, and reports
        self.combined_data_dir = os.path.join(self.brand_data_dir, "combined_data")
        self.brand_metrics_dir = os.path.join(self.brand_data_dir, "metrics")
        self.brand_reports_dir = os.path.join(self.brand_data_dir, "reports")
        
        # Create all directories
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Platform-specific directories in old location (for backward compatibility)
        self.twitter_data_dir = os.path.join(self.raw_data_dir, "twitter")
        self.reddit_data_dir = os.path.join(self.raw_data_dir, "reddit")
        self.news_data_dir = os.path.join(self.raw_data_dir, "news")
        self.amazon_data_dir = os.path.join(self.raw_data_dir, "amazon")
        
        os.makedirs(self.twitter_data_dir, exist_ok=True)
        os.makedirs(self.reddit_data_dir, exist_ok=True)
        os.makedirs(self.news_data_dir, exist_ok=True)
        os.makedirs(self.amazon_data_dir, exist_ok=True)
        
        # Create new directory structure
        os.makedirs(self.twitter_dir, exist_ok=True)
        os.makedirs(self.reddit_dir, exist_ok=True)
        os.makedirs(self.news_dir, exist_ok=True)
        os.makedirs(self.amazon_dir, exist_ok=True)
        os.makedirs(self.combined_data_dir, exist_ok=True)
        os.makedirs(self.brand_metrics_dir, exist_ok=True)
        os.makedirs(self.brand_reports_dir, exist_ok=True)
        
        # API credentials (to be set later)
        self.twitter_api_credentials = None
        self.google_news_api_key = None
        self.apify_api_key = None
        
        # Collection statistics
        self.total_collected = 0
        self.cycles_run = 0
        self.platform_stats = defaultdict(int)
        self.brand_stats = defaultdict(int)
        
        # Control flag for the collection loop
        self.running = False
        
        # Log the 7-day data filter
        logger.info("Data collection configured to retrieve only posts from the past 7 days")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
        logger.info(f"Collection summary: {self.total_collected} posts in {self.cycles_run} cycles")
        for platform, count in self.platform_stats.items():
            logger.info(f"  - {platform}: {count} posts")
        for brand, count in self.brand_stats.items():
            logger.info(f"  - Brand '{brand}': {count} mentions")
    
    def set_twitter_credentials(self, api_key, api_secret, access_token, access_token_secret, bearer_token=None):
        """Set Twitter API credentials."""
        self.twitter_api_credentials = {
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "bearer_token": bearer_token
        }
        logger.info("Twitter API credentials set")
    
    def set_google_news_api_key(self, api_key):
        """Set Google News API key."""
        self.google_news_api_key = api_key
        logger.info("Google News API key set")
    
    def set_apify_api_key(self, api_key):
        """Set Apify API key for Amazon reviews collection."""
        self.apify_api_key = api_key
        logger.info("Apify API key set")
    
    async def collect_twitter_data(self, brand_identifiers, keywords, hashtags, min_posts=50):
        """Asynchronously collect Twitter data for brand monitoring."""
        if not self.twitter_api_credentials:
            logger.warning("Twitter API credentials not set")
            return []
        
        import tweepy
        
        twitter_posts = []
        tasks = []
        
        try:
            # Set up authentication
            auth = tweepy.OAuth1UserHandler(
                self.twitter_api_credentials["api_key"], 
                self.twitter_api_credentials["api_secret"],
                self.twitter_api_credentials["access_token"], 
                self.twitter_api_credentials["access_token_secret"]
            )
            api = tweepy.API(auth)
            
            # Calculate date 7 days ago
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            # Use asyncio.to_thread to run Twitter API calls in the thread pool
            async def search_twitter(query, max_tweets=20):
                try:
                    loop = asyncio.get_event_loop()
                    tweets = await loop.run_in_executor(
                        None, 
                        lambda: list(tweepy.Cursor(api.search_tweets, q=query, tweet_mode='extended').items(max_tweets))
                    )
                    
                    formatted_tweets = []
                    for tweet in tweets:
                        # Check if tweet is within the last 7 days
                        if hasattr(tweet, 'created_at') and tweet.created_at < seven_days_ago:
                            continue
                            
                        # Extract text
                        if hasattr(tweet, 'full_text'):
                            text = tweet.full_text
                        else:
                            text = tweet.text
                        
                        # Extract hashtags and mentions
                        hashtags = []
                        mentions = []
                        if hasattr(tweet, 'entities'):
                            if 'hashtags' in tweet.entities:
                                hashtags = [tag['text'] for tag in tweet.entities['hashtags']]
                            if 'user_mentions' in tweet.entities:
                                mentions = [mention['screen_name'] for mention in tweet.entities['user_mentions']]
                        
                        # Format tweet data
                        tweet_data = {
                            "tweet_id": str(tweet.id),
                            "username": tweet.user.screen_name,
                            "timestamp": tweet.created_at.isoformat(),
                            "text_content": text,
                            "engagement_metrics": {
                                "retweets": tweet.retweet_count,
                                "likes": tweet.favorite_count if hasattr(tweet, 'favorite_count') else 0,
                                "replies": tweet.reply_count if hasattr(tweet, 'reply_count') else 0
                            },
                            "extracted_hashtags": hashtags,
                            "extracted_mentions": mentions,
                            "query": query,
                            "platform": "twitter"
                        }
                        
                        formatted_tweets.append(tweet_data)
                    
                    return formatted_tweets
                except Exception as e:
                    logger.error(f"Error searching Twitter for query '{query}': {e}")
                    return []
            
            # Collect from brand identifiers - create tasks
            for brand in brand_identifiers:
                logger.info(f"Collecting Twitter data for brand: {brand}")
                tasks.append(search_twitter(brand, max_tweets=min_posts//len(brand_identifiers)))
            
            # Collect from keywords - create tasks
            for keyword in keywords:
                logger.info(f"Collecting Twitter data for keyword: {keyword}")
                tasks.append(search_twitter(keyword, max_tweets=min_posts//len(keywords) if keywords else min_posts))
            
            # Collect from hashtags - create tasks
            for hashtag in hashtags:
                query = f"#{hashtag}"
                logger.info(f"Collecting Twitter data for hashtag: {query}")
                tasks.append(search_twitter(query, max_tweets=min_posts//len(hashtags) if hashtags else min_posts))
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten the results
            for result in results:
                if isinstance(result, list):
                    twitter_posts.extend(result)
            
            # Remove duplicates
            unique_posts = []
            seen_ids = set()
            for post in twitter_posts:
                if post['tweet_id'] not in seen_ids:
                    seen_ids.add(post['tweet_id'])
                    # Add brand tracker info
                    post['brand_tracker'] = {
                        'matched_term': post.get('query', ''),
                        'term_type': 'hashtag' if post.get('query', '').startswith('#') else 'brand' if post.get('query', '') in brand_identifiers else 'keyword'
                    }
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
    
    async def collect_reddit_data(self, brand_identifiers, keywords, hashtags, min_posts=50):
        """Asynchronously collect Reddit data for brand monitoring."""
        import aiohttp
        import asyncio
        
        reddit_posts = []
        tasks = []
        
        # Calculate date 7 days ago in UTC timestamp
        seven_days_ago = (datetime.now() - timedelta(days=7)).timestamp()
        
        async def search_reddit(query, max_posts=20):
            posts = []
            headers = {
                'User-Agent': 'python:brand_tracker:v1.0 (by /u/your_username)'
            }
            
            try:
                # Search Reddit using the JSON API
                async with aiohttp.ClientSession() as session:
                    search_url = f"https://www.reddit.com/search.json"
                    params = {
                        'q': query,
                        'sort': 'new',
                        'limit': max_posts
                    }
                    
                    async with session.get(search_url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'data' in data and 'children' in data['data']:
                                for post_data in data['data']['children']:
                                    try:
                                        post = post_data['data']
                                        post_id = post.get('id', '')
                                        
                                        # Skip posts older than 7 days
                                        if post['created_utc'] < seven_days_ago:
                                            continue
                                        
                                        # Extract content
                                        content = post.get('selftext', '') or post.get('title', '')
                                        
                                        # Format timestamp
                                        timestamp = datetime.fromtimestamp(post['created_utc']).isoformat()
                                        
                                        post_formatted = {
                                            "post_id": post_id,
                                            "username": post.get('author', 'unknown'),
                                            "timestamp": timestamp,
                                            "text_content": content,
                                            "title": post.get('title', ''),
                                            "subreddit": post.get('subreddit', ''),
                                            "url": post.get('url', ''),
                                            "permalink": f"https://reddit.com{post.get('permalink', '')}",
                                            "engagement_metrics": {
                                                "upvotes": post.get('score', 0),
                                                "num_comments": post.get('num_comments', 0),
                                                "upvote_ratio": post.get('upvote_ratio', 0.0)
                                            },
                                            "query": query,
                                            "platform": "reddit"
                                        }
                                        
                                        posts.append(post_formatted)
                                        
                                    except Exception as e:
                                        logger.warning(f"Error processing Reddit post: {e}")
                                        continue
                        else:
                            logger.warning(f"Error searching Reddit for query '{query}': HTTP {response.status}")
                
                # If we need more posts, try some popular subreddits
                if len(posts) < max_posts:
                    popular_subreddits = ["all", "popular", "AskReddit", "pics", "videos"]
                    remaining = max_posts - len(posts)
                    per_subreddit = max(5, remaining // len(popular_subreddits))
                    
                    for subreddit in popular_subreddits:
                        if len(posts) >= max_posts:
                            break
                            
                        async with aiohttp.ClientSession() as session:
                            search_url = f"https://www.reddit.com/r/{subreddit}/search.json"
                            params = {
                                'q': query,
                                'restrict_sr': 'true',
                                'sort': 'new',
                                'limit': per_subreddit
                            }
                            
                            logger.info(f"Searching r/{subreddit}...")
                            
                            async with session.get(search_url, params=params, headers=headers) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    
                                    if 'data' in data and 'children' in data['data']:
                                        for post_data in data['data']['children']:
                                            try:
                                                post = post_data['data']
                                                post_id = post.get('id', '')
                                                
                                                # Skip posts older than 7 days
                                                if post['created_utc'] < seven_days_ago:
                                                    continue
                                                
                                                # Extract content
                                                content = post.get('selftext', '') or post.get('title', '')
                                                
                                                # Format timestamp
                                                timestamp = datetime.fromtimestamp(post['created_utc']).isoformat()
                                                
                                                post_formatted = {
                                                    "post_id": post_id,
                                                    "username": post.get('author', 'unknown'),
                                                    "timestamp": timestamp,
                                                    "text_content": content,
                                                    "title": post.get('title', ''),
                                                    "subreddit": post.get('subreddit', ''),
                                                    "url": post.get('url', ''),
                                                    "permalink": f"https://reddit.com{post.get('permalink', '')}",
                                                    "engagement_metrics": {
                                                        "upvotes": post.get('score', 0),
                                                        "num_comments": post.get('num_comments', 0),
                                                        "upvote_ratio": post.get('upvote_ratio', 0.0)
                                                    },
                                                    "query": query,
                                                    "platform": "reddit"
                                                }
                                                
                                                posts.append(post_formatted)
                                                
                                            except Exception as e:
                                                logger.warning(f"Error processing Reddit post: {e}")
                                                continue
                                else:
                                    logger.warning(f"Error searching Reddit for query '{query}' in r/{subreddit}: HTTP {response.status}")
                        
                        # Sleep a bit to avoid rate limiting
                        await asyncio.sleep(1)
                
                logger.info(f"Successfully collected {len(posts)} posts for query: {query}")
                
            except Exception as e:
                logger.error(f"Error searching Reddit for query '{query}': {e}")
            
            return posts
            
        try:
            # Create tasks for all search queries
            # Collect from brand identifiers
            for brand in brand_identifiers:
                logger.info(f"Collecting Reddit data for brand: {brand}")
                tasks.append(search_reddit(brand, max_posts=min_posts//len(brand_identifiers) if brand_identifiers else min_posts))
            
            # Collect from keywords
            for keyword in keywords:
                logger.info(f"Collecting Reddit data for keyword: {keyword}")
                tasks.append(search_reddit(keyword, max_posts=min_posts//len(keywords) if keywords else min_posts))
            
            # Collect from hashtags (as keywords on Reddit)
            for hashtag in hashtags:
                logger.info(f"Collecting Reddit data for hashtag: {hashtag}")
                tasks.append(search_reddit(hashtag, max_posts=min_posts//len(hashtags) if hashtags else min_posts))
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten the results
            for result in results:
                if isinstance(result, list):
                    reddit_posts.extend(result)
            
            # Remove duplicates
            unique_posts = []
            seen_ids = set()
            for post in reddit_posts:
                # Ensure post has a post_id and it's not already seen
                if 'post_id' in post and post['post_id'] not in seen_ids:
                    seen_ids.add(post['post_id'])
                    # Add brand tracker info
                    post['brand_tracker'] = {
                        'matched_term': post.get('query', ''),
                        'term_type': 'hashtag' if post.get('query', '').startswith('#') else 'brand' if post.get('query', '') in brand_identifiers else 'keyword'
                    }
                    unique_posts.append(post)
            
            logger.info(f"Collected {len(unique_posts)} unique Reddit posts")
            self.platform_stats['reddit'] += len(unique_posts)
            
            # Count brand mentions
            for brand in brand_identifiers:
                brand_mentions = sum(1 for post in unique_posts 
                                  if brand.lower() in post.get('title', '').lower() 
                                  or brand.lower() in post.get('text_content', '').lower())
                self.brand_stats[brand] += brand_mentions
                logger.info(f"Brand '{brand}' mentioned in {brand_mentions} Reddit posts")
            
            return unique_posts
        
        except Exception as e:
            logger.error(f"Error collecting Reddit data: {e}")
            return []
            
    async def collect_news_data(self, brand_identifiers, keywords, hashtags, min_articles=50):
        """Asynchronously collect news articles for brand monitoring."""
        import asyncio
        import aiohttp
        
        news_articles = []
        tasks = []
        
        # Calculate date 7 days ago
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        if not self.google_news_api_key:
            logger.warning("Google News API key not set")
            return []
        
        async def search_news(query, max_articles=20):
            try:
                # Use News API to get recent articles
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': query,
                    'from': seven_days_ago,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'apiKey': self.google_news_api_key,
                    'pageSize': max_articles
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('status') == 'ok':
                                articles = data.get('articles', [])
                                
                                formatted_articles = []
                                for article in articles:
                                    try:
                                        # Create a unique ID for the article
                                        article_id = str(hash(article.get('url', '')))
                                        
                                        # Get the publish date
                                        published_at = article.get('publishedAt', '')
                                        
                                        # Format the article data
                                        article_formatted = {
                                            "article_id": article_id,
                                            "source": article.get('source', {}).get('name', 'Unknown'),
                                            "author": article.get('author', 'Unknown'),
                                            "title": article.get('title', ''),
                                            "description": article.get('description', ''),
                                            "url": article.get('url', ''),
                                            "image_url": article.get('urlToImage', ''),
                                            "timestamp": published_at,
                                            "content": article.get('content', ''),
                                            "query": query,
                                            "platform": "news"
                                        }
                                        
                                        formatted_articles.append(article_formatted)
                                    except Exception as e:
                                        logger.warning(f"Error processing news article: {e}")
                                        continue
                                
                                logger.info(f"Successfully collected {len(formatted_articles)} news articles for query: {query}")
                                return formatted_articles
                            else:
                                logger.warning(f"Error searching news for query '{query}': {data.get('message', 'Unknown error')}")
                                return []
                        else:
                            logger.warning(f"Error searching news for query '{query}': HTTP {response.status}")
                            return []
            except Exception as e:
                logger.error(f"Error searching news for query '{query}': {e}")
                return []
        
        try:
            # Create tasks for all search queries
            # Collect from brand identifiers
            for brand in brand_identifiers:
                logger.info(f"Collecting news data for brand: {brand}")
                tasks.append(search_news(brand, max_articles=min_articles//len(brand_identifiers) if brand_identifiers else min_articles))
            
            # Collect from keywords
            for keyword in keywords:
                logger.info(f"Collecting news data for keyword: {keyword}")
                tasks.append(search_news(keyword, max_articles=min_articles//len(keywords) if keywords else min_articles))
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten the results
            for result in results:
                if isinstance(result, list):
                    news_articles.extend(result)
            
            # Remove duplicates
            unique_articles = []
            seen_urls = set()
            for article in news_articles:
                if article.get('url', '') not in seen_urls:
                    seen_urls.add(article.get('url', ''))
                    # Add brand tracker info
                    article['brand_tracker'] = {
                        'matched_term': article.get('query', ''),
                        'term_type': 'brand' if article.get('query', '') in brand_identifiers else 'keyword'
                    }
                    unique_articles.append(article)
            
            logger.info(f"Collected {len(unique_articles)} unique news articles")
            self.platform_stats['news'] += len(unique_articles)
            
            # Count brand mentions
            for brand in brand_identifiers:
                brand_mentions = sum(1 for article in unique_articles 
                                  if brand.lower() in article.get('title', '').lower() 
                                  or brand.lower() in article.get('description', '').lower() 
                                  or brand.lower() in article.get('content', '').lower())
                self.brand_stats[brand] += brand_mentions
                logger.info(f"Brand '{brand}' mentioned in {brand_mentions} news articles")
            
            return unique_articles
        
        except Exception as e:
            logger.info(f"Error collecting news data: {e}")
            return []
            
    async def collect_amazon_data(self, brand_identifiers, keywords, hashtags, min_reviews=50):
        """Asynchronously collect Amazon product reviews for brand monitoring."""
        try:
            # Import the Amazon scraper with better error handling
            try:
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                # First try to import the simple scraper
                try:
                    from amazon_scraper.simple_amazon_scraper import SimpleAmazonScraper
                    use_simple_scraper = True
                    logger.info("Successfully imported Simple Amazon scraper module")
                except ImportError:
                    # Fall back to the Apify-based scraper if simple scraper not available
                    from amazon_scraper.amazon_collector import AmazonScraper
                    use_simple_scraper = False
                    logger.info("Successfully imported Apify-based Amazon scraper module")
            except ImportError as e:
                logger.error(f"Failed to import Amazon scraper module: {e}")
                logger.error(f"Current Python path: {sys.path}")
                return []
            
            amazon_reviews = []
            
            # Create scraper instance with error handling
            try:
                if use_simple_scraper:
                    scraper = SimpleAmazonScraper()
                    logger.info("Created Simple Amazon scraper")
                else:
                    if not self.apify_api_key:
                        logger.warning("Apify API key not set for Amazon reviews collection")
                        return []
                    scraper = AmazonScraper(self.apify_api_key)
                    logger.info(f"Created Apify-based Amazon scraper with API key: {self.apify_api_key[:5]}...")
            except Exception as e:
                logger.error(f"Failed to create Amazon scraper: {e}")
                return []
            
            # Determine how many reviews to collect per brand
            reviews_per_brand = min_reviews // len(brand_identifiers) if brand_identifiers else min_reviews
            
            # For each brand, collect reviews
            for brand in brand_identifiers:
                logger.info(f"Collecting Amazon reviews for brand: {brand}")
                
                # Determine product keywords for this brand
                brand_keywords = keywords.copy() if keywords else []
                
                try:
                    # Collect reviews for this brand
                    brand_reviews = await scraper.collect_brand_reviews(
                        brand,
                        product_keywords=brand_keywords,
                        max_products=3,  # Limit to 3 products per brand to avoid long runs
                        max_reviews_per_product=reviews_per_brand // 3,  # Distribute reviews across products
                        days_ago=7  # Match the 7-day filter used for other platforms
                    )
                    
                    logger.info(f"Raw brand reviews count for {brand}: {len(brand_reviews)}")
                    
                    # Format reviews for brand tracker
                    formatted_reviews = scraper.format_reviews_for_brand_tracker(brand_reviews)
                    logger.info(f"Formatted brand reviews count for {brand}: {len(formatted_reviews)}")
                    
                    amazon_reviews.extend(formatted_reviews)
                    
                    # Count brand mentions
                    self.brand_stats[brand] += len(formatted_reviews)
                    logger.info(f"Brand '{brand}' found in {len(formatted_reviews)} Amazon reviews")
                except Exception as brand_error:
                    logger.error(f"Error collecting Amazon reviews for brand {brand}: {brand_error}")
            
            logger.info(f"Collected {len(amazon_reviews)} Amazon reviews")
            self.platform_stats['amazon'] += len(amazon_reviews)
            
            return amazon_reviews
            
        except Exception as e:
            import traceback
            logger.error(f"Error collecting Amazon reviews: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def analyze_sentiment(self, text):
        """
        Simple sentiment analysis based on keyword matching.
        Returns a sentiment score from -1.0 (negative) to 1.0 (positive).
        """
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
    
    def update_results_json(self, all_posts):
        """Update the results.json file with all collected data.
        
        This function updates the results.json file with all collected data
        from the brand tracker. It preserves all old data and adds new data
        without removing anything.
        """
        try:
            # Load existing data if available
            existing_data = []
            if os.path.exists(self.results_json_path):
                try:
                    with open(self.results_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if 'posts' in data:
                        existing_data = data['posts']
                except Exception as e:
                    logger.error(f"Error reading existing results.json: {e}")
            
            # Create a unique set of IDs to avoid duplicates
            existing_ids = set()
            for post in existing_data:
                post_id = None
                platform = post.get('platform', '')
                
                if platform == 'twitter':
                    post_id = post.get('tweet_id', '')
                elif platform == 'reddit':
                    post_id = post.get('post_id', '')
                elif platform == 'news':
                    post_id = post.get('url', '')
                elif platform == 'amazon':
                    post_id = post.get('review_id', '')
                
                if post_id:
                    existing_ids.add(post_id)
            
            # Add new posts
            new_posts_count = 0
            for post in all_posts:
                post_id = None
                platform = post.get('platform', '')
                
                if platform == 'twitter':
                    post_id = post.get('tweet_id', '')
                elif platform == 'reddit':
                    post_id = post.get('post_id', '')
                elif platform == 'news':
                    post_id = post.get('url', '')
                elif platform == 'amazon':
                    post_id = post.get('review_id', '')
                
                # Add a unique collection timestamp to each post to ensure it's always added
                # This is important because we want to see real-time updates
                current_time = datetime.now().isoformat()
                post['collection_timestamp'] = current_time
                
                # Always add the post with its new collection timestamp
                existing_data.append(post)
                new_posts_count += 1
            
            # Add timestamp for this update
            metadata = {
                "last_updated": datetime.now().isoformat(),
                "total_posts": len(existing_data),
                "dashboard_update": True,
                "last_dashboard_update": datetime.now().isoformat(),
                "platforms": {
                    "twitter": sum(1 for post in existing_data if post.get('platform') == 'twitter'),
                    "reddit": sum(1 for post in existing_data if post.get('platform') == 'reddit'),
                    "news": sum(1 for post in existing_data if post.get('platform') == 'news'),
                    "amazon": sum(1 for post in existing_data if post.get('platform') == 'amazon')
                }
            }
            
            # Create the final result with metadata
            result = {
                "metadata": metadata,
                "posts": existing_data
            }
            
            # Write to results.json
            with open(self.results_json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated results.json with {new_posts_count} new posts (total: {len(existing_data)})")
            
            # Update timestamp of last update
            self.last_results_update = time.time()
            
        except Exception as e:
            logger.error(f"Error updating results.json: {e}")
            traceback.print_exc()
    
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
            elif post.get('platform') == 'news':
                title = post.get('title', '')
                description = post.get('description', '')
                content = post.get('content', '')
                text = f"{title} {description} {content}"
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
    
    def save_platform_data(self, posts, platform, cycle_number):
        """Save platform-specific data to JSON file."""
        if not posts:
            logger.warning(f"No {platform} posts to save")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_data_cycle{cycle_number}_{timestamp}.json"
        
        # Use the new directory structure
        if platform == 'twitter':
            filepath = os.path.join(self.twitter_dir, filename)
        elif platform == 'reddit':
            filepath = os.path.join(self.reddit_dir, filename)
        elif platform == 'news':
            filepath = os.path.join(self.news_dir, filename)
        elif platform == 'amazon':
            filepath = os.path.join(self.amazon_dir, filename)
        else:
            filepath = os.path.join(self.brand_data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(posts)} {platform} posts to {filepath}")
        return filepath
    
    def update_combined_data_files(self, twitter_posts, reddit_posts, news_articles=None, amazon_reviews=None):
        """Update the combined data files for each platform."""
        # Calculate date 7 days ago in ISO format for filtering
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        # Combined Twitter data file
        twitter_combined_file = os.path.join(self.combined_data_dir, "twitter_combined.json")
        existing_twitter_data = []
        
        # Read existing Twitter data if file exists
        if os.path.exists(twitter_combined_file):
            try:
                with open(twitter_combined_file, 'r', encoding='utf-8') as f:
                    existing_twitter_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading combined Twitter data: {e}")
                existing_twitter_data = []
        
        # Filter out tweets older than 7 days
        existing_twitter_data = [
            post for post in existing_twitter_data 
            if post.get('timestamp', seven_days_ago) >= seven_days_ago
        ]
        
        # Add new Twitter data
        if twitter_posts:
            # Get existing tweet IDs to avoid duplicates
            existing_ids = set(post.get('tweet_id', '') for post in existing_twitter_data)
            
            # Add only new tweets
            for post in twitter_posts:
                if post.get('tweet_id', '') not in existing_ids:
                    existing_twitter_data.append(post)
            
            # Save updated Twitter data
            with open(twitter_combined_file, 'w', encoding='utf-8') as f:
                json.dump(existing_twitter_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated combined Twitter data file with {len(twitter_posts)} new tweets. Total: {len(existing_twitter_data)}")
        
        # Combined Reddit data file
        reddit_combined_file = os.path.join(self.combined_data_dir, "reddit_combined.json")
        existing_reddit_data = []
        
        # Read existing Reddit data if file exists
        if os.path.exists(reddit_combined_file):
            try:
                with open(reddit_combined_file, 'r', encoding='utf-8') as f:
                    existing_reddit_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading combined Reddit data: {e}")
                existing_reddit_data = []
        
        # Filter out posts older than 7 days
        existing_reddit_data = [
            post for post in existing_reddit_data 
            if post.get('timestamp', seven_days_ago) >= seven_days_ago
        ]
        
        # Add new Reddit data
        if reddit_posts:
            # Get existing post IDs to avoid duplicates
            existing_ids = set(post.get('post_id', '') for post in existing_reddit_data)
            
            # Add only new posts
            for post in reddit_posts:
                if post.get('post_id', '') not in existing_ids:
                    existing_reddit_data.append(post)
            
            # Save updated Reddit data
            with open(reddit_combined_file, 'w', encoding='utf-8') as f:
                json.dump(existing_reddit_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated combined Reddit data file with {len(reddit_posts)} new posts. Total: {len(existing_reddit_data)}")
        
        # Combined News data file
        if news_articles:
            news_combined_file = os.path.join(self.combined_data_dir, "news_combined.json")
            existing_news_data = []
            
            # Read existing News data if file exists
            if os.path.exists(news_combined_file):
                try:
                    with open(news_combined_file, 'r', encoding='utf-8') as f:
                        existing_news_data = json.load(f)
                except Exception as e:
                    logger.error(f"Error reading combined News data: {e}")
                    existing_news_data = []
            
            # Filter out articles older than 7 days
            existing_news_data = [
                article for article in existing_news_data 
                if article.get('timestamp', seven_days_ago) >= seven_days_ago
            ]
            
            # Get existing article IDs to avoid duplicates
            existing_ids = set(article.get('article_id', '') for article in existing_news_data)
            
            # Add only new articles
            for article in news_articles:
                if article.get('article_id', '') not in existing_ids:
                    existing_news_data.append(article)
            
            # Save updated News data
            with open(news_combined_file, 'w', encoding='utf-8') as f:
                json.dump(existing_news_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated combined News data file with {len(news_articles)} new articles. Total: {len(existing_news_data)}")
        
        # Combined Amazon reviews file
        if amazon_reviews:
            amazon_combined_file = os.path.join(self.combined_data_dir, "amazon_combined.json")
            existing_amazon_data = []
            
            # Read existing Amazon data if file exists
            if os.path.exists(amazon_combined_file):
                try:
                    with open(amazon_combined_file, 'r', encoding='utf-8') as f:
                        existing_amazon_data = json.load(f)
                except Exception as e:
                    logger.error(f"Error reading combined Amazon data: {e}")
                    existing_amazon_data = []
            
            # Filter out reviews older than 7 days
            existing_amazon_data = [
                review for review in existing_amazon_data 
                if review.get('timestamp', seven_days_ago) >= seven_days_ago
            ]
            
            # Get existing review IDs to avoid duplicates
            existing_ids = set(review.get('review_id', '') for review in existing_amazon_data)
            
            # Add only new reviews
            for review in amazon_reviews:
                if review.get('review_id', '') not in existing_ids:
                    existing_amazon_data.append(review)
            
            with open(amazon_combined_file, 'w', encoding='utf-8') as f:
                json.dump(existing_amazon_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated combined Amazon data file with {len(amazon_reviews)} new reviews. Total: {len(existing_amazon_data)}")
        
        # Also create a combined all-platforms file
        all_combined_file = os.path.join(self.combined_data_dir, "all_data_combined.json")
        try:
            if os.path.exists(all_combined_file):
                with open(all_combined_file, 'r', encoding='utf-8') as f:
                    existing_all_data = json.load(f)
            else:
                existing_all_data = []
            
            # Filter out data older than 7 days
            existing_all_data = [
                item for item in existing_all_data 
                if item.get('timestamp', seven_days_ago) >= seven_days_ago
            ]
            
            # Get existing IDs to avoid duplicates
            existing_tweet_ids = set(item.get('tweet_id', '') for item in existing_all_data if item.get('platform') == 'twitter')
            existing_post_ids = set(item.get('post_id', '') for item in existing_all_data if item.get('platform') == 'reddit')
            existing_article_urls = set(item.get('url', '') for item in existing_all_data if item.get('platform') == 'news')
            existing_review_ids = set(item.get('review_id', '') for item in existing_all_data if item.get('platform') == 'amazon')
            
            # Add new tweets
            for post in twitter_posts or []:
                if post.get('tweet_id', '') not in existing_tweet_ids:
                    existing_all_data.append(post)
            
            # Add new reddit posts
            for post in reddit_posts or []:
                if post.get('post_id', '') not in existing_post_ids:
                    existing_all_data.append(post)
            
            # Add new news articles
            for article in news_articles or []:
                if article.get('url', '') not in existing_article_urls:
                    existing_all_data.append(article)
                    
            # Add new amazon reviews
            for review in amazon_reviews or []:
                if review.get('review_id', '') not in existing_review_ids:
                    existing_all_data.append(review)
            
            with open(all_combined_file, 'w', encoding='utf-8') as f:
                json.dump(existing_all_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated combined all-platforms file with new data")
        except Exception as e:
            logger.error(f"Error updating combined all-platforms file: {e}")
    
    def save_brand_data(self, posts, cycle_number):
        """Save collected brand data to JSON file."""
        if not posts:
            logger.warning("No posts to save")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create the combined data file
        filename = f"brand_data_cycle{cycle_number}_{timestamp}.json"
        filepath = os.path.join(self.raw_data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(posts)} posts to {filepath}")
        
        # Separate posts by platform
        twitter_posts = [post for post in posts if post.get('platform') == 'twitter']
        reddit_posts = [post for post in posts if post.get('platform') == 'reddit']
        news_articles = [post for post in posts if post.get('platform') == 'news']
        
        # Save Twitter data separately
        if twitter_posts:
            twitter_filename = f"twitter_data_cycle{cycle_number}_{timestamp}.json"
            twitter_filepath = os.path.join(self.twitter_data_dir, twitter_filename)
            
            with open(twitter_filepath, 'w', encoding='utf-8') as f:
                json.dump(twitter_posts, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(twitter_posts)} Twitter posts to {twitter_filepath}")
        
        # Save Reddit data separately
        if reddit_posts:
            reddit_filename = f"reddit_data_cycle{cycle_number}_{timestamp}.json"
            reddit_filepath = os.path.join(self.reddit_data_dir, reddit_filename)
            
            with open(reddit_filepath, 'w', encoding='utf-8') as f:
                json.dump(reddit_posts, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(reddit_posts)} Reddit posts to {reddit_filepath}")
        
        # Save News data separately
        if news_articles:
            news_filename = f"news_data_cycle{cycle_number}_{timestamp}.json"
            news_filepath = os.path.join(self.news_data_dir, news_filename)
            
            with open(news_filepath, 'w', encoding='utf-8') as f:
                json.dump(news_articles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(news_articles)} News articles to {news_filepath}")
        
        # Update the combined data files for each platform
        self.update_combined_data_files(twitter_posts, reddit_posts, news_articles)
        
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
            'platform_distribution': dict(Counter(post.get('platform', 'unknown') for post in posts)),
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
                'news': {
                    'total_articles': 0,
                    'sources': {}
                }
            }
        }
        
        # Calculate metrics
        for post in posts:
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
            platform = post.get('platform')
            if platform == 'twitter':
                engagement = post.get('engagement_metrics', {})
                metrics['engagement']['twitter']['total_likes'] += engagement.get('likes', 0)
                metrics['engagement']['twitter']['total_retweets'] += engagement.get('retweets', 0)
                metrics['engagement']['twitter']['total_replies'] += engagement.get('replies', 0)
            elif platform == 'reddit':
                engagement = post.get('engagement_metrics', {})
                metrics['engagement']['reddit']['total_upvotes'] += engagement.get('upvotes', 0)
                metrics['engagement']['reddit']['total_comments'] += engagement.get('num_comments', 0)
            elif platform == 'news':
                metrics['engagement']['news']['total_articles'] += 1
                source = post.get('source', 'Unknown')
                if source not in metrics['engagement']['news']['sources']:
                    metrics['engagement']['news']['sources'][source] = 0
                metrics['engagement']['news']['sources'][source] += 1
        
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
        
        # Save metrics to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_cycle{cycle_number}_{timestamp}.json"
        
        # Save to both locations (new and old for backward compatibility)
        filepath = os.path.join(self.metrics_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        # Save to the new consolidated location
        new_filepath = os.path.join(self.brand_metrics_dir, filename)
        with open(new_filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved metrics to {new_filepath}")
        return metrics
    
    def generate_report(self, metrics, cycle_number):
        """Generate a human-readable report from metrics."""
        if not metrics:
            logger.warning("No metrics for report generation")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_cycle{cycle_number}_{timestamp}.md"
        
        # Save to both locations (new and old for backward compatibility)
        filepath = os.path.join(self.reports_dir, filename)
        new_filepath = os.path.join(self.brand_reports_dir, filename)
        
        # Generate report content
        report_content = self._generate_report_content(metrics, cycle_number)
        
        # Save to both locations
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Generated report: {new_filepath}")
        return new_filepath
    
    def _generate_report_content(self, metrics, cycle_number):
        """Generate the content for a report."""
        report = []
        report.append(f"# Brand Tracking Report - Cycle {cycle_number}\n\n")
        report.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        report.append("## Summary\n\n")
        report.append(f"- Total posts collected: **{metrics['total_posts']}**\n")
        report.append("- Platform distribution:\n")
        for platform, count in metrics['platform_distribution'].items():
            percentage = count/metrics['total_posts']*100 if metrics['total_posts'] > 0 else 0
            report.append(f"  - {platform.capitalize()}: {count} posts ({percentage:.1f}%)\n")
        
        report.append("\n## Brand Mentions\n\n")
        for brand, count in metrics['brand_mentions'].items():
            report.append(f"- **{brand}**: {count} mentions\n")
        
        report.append("\n## Sentiment Analysis\n\n")
        report.append("### Overall Sentiment\n\n")
        report.append("| Sentiment | Count | Percentage |\n")
        report.append("|-----------|-------|------------|\n")
        for sentiment, count in metrics['sentiment_distribution'].items():
            percentage = count/metrics['total_posts']*100 if metrics['total_posts'] > 0 else 0
            report.append(f"| {sentiment.capitalize()} | {count} | {percentage:.1f}% |\n")
        
        report.append("\n### Brand Sentiment\n\n")
        report.append("| Brand | Positive | Neutral | Negative | Average Score |\n")
        report.append("|-------|----------|---------|----------|---------------|\n")
        for brand, sentiment in metrics['brand_sentiment'].items():
            report.append(f"| {brand} | {sentiment['positive']} | {sentiment['neutral']} | {sentiment['negative']} | {sentiment['average_score']:.2f} |\n")
        
        report.append("\n## Engagement Metrics\n\n")
        report.append("### Twitter Engagement\n\n")
        twitter_engagement = metrics['engagement']['twitter']
        report.append(f"- Total likes: {twitter_engagement['total_likes']}\n")
        report.append(f"- Total retweets: {twitter_engagement['total_retweets']}\n")
        report.append(f"- Total replies: {twitter_engagement['total_replies']}\n")
        
        report.append("\n### Reddit Engagement\n\n")
        reddit_engagement = metrics['engagement']['reddit']
        report.append(f"- Total upvotes: {reddit_engagement['total_upvotes']}\n")
        report.append(f"- Total comments: {reddit_engagement['total_comments']}\n")
        
        # Add News Engagement Section
        if 'news' in metrics['engagement']:
            report.append("\n### News Articles\n\n")
            news_engagement = metrics['engagement']['news']
            report.append(f"- Total articles: {news_engagement.get('total_articles', 0)}\n")
            
            if news_engagement.get('sources', {}):
                report.append("\n#### News Sources\n\n")
                report.append("| Source | Article Count |\n")
                report.append("|--------|---------------|\n")
                # Sort sources by article count in descending order
                sorted_sources = sorted(news_engagement['sources'].items(), key=lambda x: x[1], reverse=True)
                for source, count in sorted_sources:
                    report.append(f"| {source} | {count} |\n")
            
            if news_engagement.get('source_distribution', {}):
                report.append("\n#### News Sources\n\n")
                report.append("| Source | Article Count |\n")
                report.append("|--------|---------------|\n")
                # Sort sources by article count in descending order
                sorted_sources = sorted(news_engagement['source_distribution'].items(), key=lambda x: x[1], reverse=True)
                for source, count in sorted_sources:
                    report.append(f"| {source} | {count} |\n")
        
        return "".join(report)
    
    async def collection_cycle(self, brand_identifiers, keywords, hashtags, min_posts=100):
        """Run one collection cycle asynchronously."""
        start_time = time.time()
        logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting collection cycle {self.cycles_run + 1}")
        
        all_posts = []
        
        # Check which platforms to collect from
        from config import PLATFORMS
        
        # Create collection tasks based on enabled platforms
        collection_tasks = []
        if "twitter" in PLATFORMS:
            collection_tasks.append(self.collect_twitter_data(brand_identifiers, keywords, hashtags, min_posts // len(PLATFORMS)))
        if "reddit" in PLATFORMS:
            collection_tasks.append(self.collect_reddit_data(brand_identifiers, keywords, hashtags, min_posts // len(PLATFORMS)))
        if "news" in PLATFORMS:
            collection_tasks.append(self.collect_news_data(brand_identifiers, keywords, hashtags, min_posts // len(PLATFORMS)))
        if "amazon" in PLATFORMS:
            collection_tasks.append(self.collect_amazon_data(brand_identifiers, keywords, hashtags, min_posts // len(PLATFORMS)))
        
        # Collect data from platforms concurrently
        results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # Process results
        twitter_posts, reddit_posts, news_articles, amazon_reviews = [], [], [], []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in collection task {i}: {result}")
                continue
                
            if i < len(collection_tasks):
                platform_name = PLATFORMS[i] if i < len(PLATFORMS) else f"platform_{i}"
                logger.info(f"Collected {len(result)} items from {platform_name}")
                
                if platform_name == "twitter":
                    twitter_posts = result
                elif platform_name == "reddit":
                    reddit_posts = result
                elif platform_name == "news":
                    news_articles = result
                elif platform_name == "amazon":
                    amazon_reviews = result
                    
                all_posts.extend(result)
        
        # Analyze posts
        analyzed_posts = self.analyze_posts(all_posts, brand_identifiers)
        
        # Save data
        if analyzed_posts:
            # Save to original location for backward compatibility
            self.save_brand_data(analyzed_posts, self.cycles_run + 1)
            
            # Save platform-specific data to new consolidated location
            if twitter_posts:
                self.save_platform_data(twitter_posts, 'twitter', self.cycles_run + 1)
            if reddit_posts:
                self.save_platform_data(reddit_posts, 'reddit', self.cycles_run + 1)
            if news_articles:
                self.save_platform_data(news_articles, 'news', self.cycles_run + 1)
            if amazon_reviews:
                self.save_platform_data(amazon_reviews, 'amazon', self.cycles_run + 1)
            
            # Update combined data files
            self.update_combined_data_files(twitter_posts, reddit_posts, news_articles, amazon_reviews)
            
            # Generate metrics and report
            metrics = self.generate_metrics(analyzed_posts, brand_identifiers, self.cycles_run + 1)
            if metrics:
                self.generate_report(metrics, self.cycles_run + 1)
            
            # Update the results.json file (every 2 minutes)
            self.update_results_json(analyzed_posts)
            
            self.total_collected += len(analyzed_posts)
        else:
            logger.warning("No posts collected in this cycle")
        
        # Update statistics
        self.cycles_run += 1
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        logger.info(f"Collection cycle took {elapsed:.2f} seconds")
        
        return analyzed_posts
    
    async def run_collection(self, brand_identifiers, keywords, hashtags, min_posts=100, max_cycles=None):
        """Run the collection process asynchronously."""
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
        self.running = True
        
        try:
            while self.running:
                cycle_start = time.time()
                
                # Run one collection cycle
                await self.collection_cycle(brand_identifiers, keywords, hashtags, min_posts)
                
                cycle_count += 1
                if max_cycles and cycle_count >= max_cycles:
                    logger.info(f"Reached maximum number of cycles ({max_cycles}), stopping")
                    break
                
                # Calculate time to wait until next cycle
                elapsed = time.time() - cycle_start
                wait_time = max(0, self.interval - elapsed)
                
                if wait_time > 0 and self.running:
                    logger.info(f"Waiting {wait_time:.2f} seconds until next collection cycle...")
                    await asyncio.sleep(wait_time)
                
        except Exception as e:
            logger.error(f"Error in collection process: {e}")
        finally:
            logger.info("Collection process finished")
    
    async def start(self, brand_identifiers, keywords=None, hashtags=None, min_posts=100, max_cycles=None):
        """Start the brand tracking process asynchronously."""
        # Ensure we have lists
        keywords = keywords or []
        hashtags = hashtags or []
        
        # Reset statistics
        self.total_collected = 0
        self.cycles_run = 0
        self.platform_stats = defaultdict(int)
        self.brand_stats = defaultdict(int)
        
        # Initialize empty results.json if it doesn't exist
        if not os.path.exists(self.results_json_path):
            initial_data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_posts": 0,
                    "platforms": {
                        "twitter": 0,
                        "reddit": 0,
                        "news": 0,
                        "amazon": 0
                    }
                },
                "posts": []
            }
            with open(self.results_json_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Initialized empty results.json file at {self.results_json_path}")
        
        # Run collection and periodic result updates in parallel
        await asyncio.gather(
            self.run_collection(brand_identifiers, keywords, hashtags, min_posts, max_cycles),
            self.periodic_result_update()
        )
        
        logger.info("Brand tracker stopped")
        logger.info(f"Collection summary: {self.total_collected} posts in {self.cycles_run} cycles")
        for platform, count in self.platform_stats.items():
            logger.info(f"  - {platform}: {count} posts")
        for brand, count in self.brand_stats.items():
            logger.info(f"  - Brand '{brand}': {count} mentions")
    
    async def periodic_result_update(self):
        """Periodically update the results.json file regardless of new data.
        
        This ensures the file is updated every minute even if no new data is collected.
        This allows the dashboard to get real-time updates.
        """
        try:
            # Store previous metadata to track changes
            previous_metadata = None
            
            while self.running:
                # Check if results.json exists
                if os.path.exists(self.results_json_path):
                    try:
                        with open(self.results_json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if 'metadata' in data:
                            # Store current metadata as previous before updating
                            if 'metadata' in data:
                                previous_metadata = data.get('metadata', {}).copy()
                            
                            # Update timestamp
                            current_time = datetime.now()
                            data['metadata']['last_updated'] = current_time.isoformat()
                            
                            # Add previous metadata for change tracking by the dashboard
                            if previous_metadata:
                                data['previous_metadata'] = previous_metadata
                            
                            # Flag for dashboard to indicate this is a real-time update
                            data['metadata']['dashboard_update'] = True
                            data['metadata']['last_dashboard_update'] = current_time.isoformat()
                            data['metadata']['is_live_update'] = True
                            
                            with open(self.results_json_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            
                            logger.info(f"Updated results.json for dashboard at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Create a signal file for the dashboard to detect updates
                            dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "median_model")
                            if not os.path.exists(dashboard_dir):
                                os.makedirs(dashboard_dir, exist_ok=True)
                            
                            update_signal_path = os.path.join(dashboard_dir, "data_updated.signal")
                            with open(update_signal_path, 'w') as f:
                                f.write(current_time.isoformat())
                            
                            logger.info(f"Created update signal for dashboard at {update_signal_path}")
                    except Exception as e:
                        logger.error(f"Error updating timestamp in results.json: {e}")
                        traceback.print_exc()
                
                # Wait for 60 seconds (1 minute) before checking again
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Periodic result update task cancelled")
        except Exception as e:
            logger.error(f"Error in periodic result update: {e}")
            traceback.print_exc()
