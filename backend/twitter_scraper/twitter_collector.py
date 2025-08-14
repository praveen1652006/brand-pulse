#!/usr/bin/env python3
"""
Twitter Collector - Collects at least 100 tweets every 2 minutes based on
keywords, hashtags, mentions, and user timelines.
"""

import tweepy
import json
import os
import time
from datetime import datetime
import re
import logging
import threading
import sys
import argparse
import signal

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitterCollector:
    """Collects Twitter posts based on keywords, hashtags, mentions, and user timelines."""
    
    def __init__(self, api_key, api_secret, access_token, access_token_secret, bearer_token=None,
                 output_dir="twitter_data", interval=120):
        """Initialize the TwitterCollector."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.bearer_token = bearer_token
        self.output_dir = output_dir
        self.interval = interval
        
        # Set up authentication
        auth = tweepy.OAuth1UserHandler(
            self.api_key, self.api_secret,
            self.access_token, self.access_token_secret
        )
        self.api = tweepy.API(auth)
        
        # Initialize v2 client if bearer token is provided
        if bearer_token:
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
        else:
            self.client = None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Collection statistics
        self.collected_tweets = set()
        self.total_collected = 0
        self.cycles_run = 0
        
        # Thread control
        self.running = False
        self.collection_thread = None
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def extract_hashtags_mentions(self, text):
        """Extract hashtags and mentions from text."""
        hashtags = re.findall(r'#(\w+)', text.lower())
        mentions = re.findall(r'@(\w+)', text.lower())
        
        return {
            "hashtags": list(set(hashtags)),
            "mentions": list(set(mentions))
        }
    
    def search_tweets(self, query, max_tweets=100):
        """Search for tweets matching a query."""
        tweets = []
        
        try:
            logger.info(f"Searching for tweets with query: {query}")
            
            if self.client:  # Use v2 API if available
                response = self.client.search_recent_tweets(
                    query=query, 
                    max_results=min(100, max_tweets),
                    tweet_fields=['created_at', 'public_metrics', 'entities', 'author_id'],
                    user_fields=['username', 'name'],
                    expansions=['author_id']
                )
                
                if response.data:
                    users = {user.id: user for user in response.includes['users']} if 'users' in response.includes else {}
                    for tweet in response.data:
                        if str(tweet.id) in self.collected_tweets:
                            continue
                            
                        self.collected_tweets.add(str(tweet.id))
                        
                        # Extract hashtags and mentions
                        hashtags = []
                        mentions = []
                        
                        if hasattr(tweet, 'entities'):
                            if 'hashtags' in tweet.entities:
                                hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
                            if 'mentions' in tweet.entities:
                                mentions = [mention['username'] for mention in tweet.entities['mentions']]
                        
                        # Extract from text as fallback
                        if not hashtags or not mentions:
                            extracted = self.extract_hashtags_mentions(tweet.text)
                            if not hashtags:
                                hashtags = extracted["hashtags"]
                            if not mentions:
                                mentions = extracted["mentions"]
                        
                        tweet_data = {
                            'tweet_id': str(tweet.id),
                            'username': users[tweet.author_id].username if tweet.author_id in users else None,
                            'timestamp': tweet.created_at.isoformat(),
                            'text_content': tweet.text,
                            'engagement_metrics': {
                                'retweets': tweet.public_metrics.get('retweet_count', 0),
                                'likes': tweet.public_metrics.get('like_count', 0),
                                'replies': tweet.public_metrics.get('reply_count', 0)
                            },
                            'extracted_hashtags': hashtags,
                            'extracted_mentions': mentions,
                            'query': query
                        }
                        
                        tweets.append(tweet_data)
            else:  # Fall back to v1.1 API
                for tweet in tweepy.Cursor(self.api.search_tweets, 
                                          q=query, 
                                          count=max_tweets, 
                                          tweet_mode='extended').items(max_tweets):
                    if str(tweet.id) in self.collected_tweets:
                        continue
                        
                    self.collected_tweets.add(str(tweet.id))
                    
                    # Get the text content
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
                    
                    # Extract from text as fallback
                    if not hashtags or not mentions:
                        extracted = self.extract_hashtags_mentions(text)
                        if not hashtags:
                            hashtags = extracted["hashtags"]
                        if not mentions:
                            mentions = extracted["mentions"]
                    
                    tweet_data = {
                        'tweet_id': str(tweet.id),
                        'username': tweet.user.screen_name,
                        'timestamp': tweet.created_at.isoformat(),
                        'text_content': text,
                        'engagement_metrics': {
                            'retweets': tweet.retweet_count,
                            'likes': tweet.favorite_count if hasattr(tweet, 'favorite_count') else 0,
                            'replies': tweet.reply_count if hasattr(tweet, 'reply_count') else 0
                        },
                        'extracted_hashtags': hashtags,
                        'extracted_mentions': mentions,
                        'query': query
                    }
                    
                    tweets.append(tweet_data)
            
            logger.info(f"Found {len(tweets)} tweets for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching tweets for query '{query}': {e}")
            
        return tweets
    
    def get_user_tweets(self, username, max_tweets=50):
        """Get tweets from a user's timeline."""
        tweets = []
        
        try:
            logger.info(f"Getting tweets from user: {username}")
            
            if self.client:  # Use v2 API if available
                # First get user ID from username
                user = self.client.get_user(username=username)
                if not user.data:
                    logger.warning(f"User not found: {username}")
                    return tweets
                    
                user_id = user.data.id
                
                response = self.client.get_users_tweets(
                    id=user_id,
                    max_results=min(100, max_tweets),
                    tweet_fields=['created_at', 'public_metrics', 'entities']
                )
                
                if response.data:
                    for tweet in response.data:
                        if str(tweet.id) in self.collected_tweets:
                            continue
                            
                        self.collected_tweets.add(str(tweet.id))
                        
                        # Extract hashtags and mentions
                        hashtags = []
                        mentions = []
                        
                        if hasattr(tweet, 'entities'):
                            if 'hashtags' in tweet.entities:
                                hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
                            if 'mentions' in tweet.entities:
                                mentions = [mention['username'] for mention in tweet.entities['mentions']]
                        
                        # Extract from text as fallback
                        if not hashtags or not mentions:
                            extracted = self.extract_hashtags_mentions(tweet.text)
                            if not hashtags:
                                hashtags = extracted["hashtags"]
                            if not mentions:
                                mentions = extracted["mentions"]
                        
                        tweet_data = {
                            'tweet_id': str(tweet.id),
                            'username': username,
                            'timestamp': tweet.created_at.isoformat(),
                            'text_content': tweet.text,
                            'engagement_metrics': {
                                'retweets': tweet.public_metrics.get('retweet_count', 0),
                                'likes': tweet.public_metrics.get('like_count', 0),
                                'replies': tweet.public_metrics.get('reply_count', 0)
                            },
                            'extracted_hashtags': hashtags,
                            'extracted_mentions': mentions,
                            'source': f"user:{username}"
                        }
                        
                        tweets.append(tweet_data)
            else:  # Fall back to v1.1 API
                for tweet in tweepy.Cursor(self.api.user_timeline, 
                                          screen_name=username, 
                                          count=max_tweets,
                                          tweet_mode='extended').items(max_tweets):
                    if str(tweet.id) in self.collected_tweets:
                        continue
                        
                    self.collected_tweets.add(str(tweet.id))
                    
                    # Get the text content
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
                    
                    # Extract from text as fallback
                    if not hashtags or not mentions:
                        extracted = self.extract_hashtags_mentions(text)
                        if not hashtags:
                            hashtags = extracted["hashtags"]
                        if not mentions:
                            mentions = extracted["mentions"]
                    
                    tweet_data = {
                        'tweet_id': str(tweet.id),
                        'username': tweet.user.screen_name,
                        'timestamp': tweet.created_at.isoformat(),
                        'text_content': text,
                        'engagement_metrics': {
                            'retweets': tweet.retweet_count,
                            'likes': tweet.favorite_count if hasattr(tweet, 'favorite_count') else 0,
                            'replies': tweet.reply_count if hasattr(tweet, 'reply_count') else 0
                        },
                        'extracted_hashtags': hashtags,
                        'extracted_mentions': mentions,
                        'source': f"user:{username}"
                    }
                    
                    tweets.append(tweet_data)
            
            logger.info(f"Found {len(tweets)} tweets from user: {username}")
            
        except Exception as e:
            logger.error(f"Error getting tweets for user '{username}': {e}")
            
        return tweets
    
    def collect_tweets(self, keywords=None, hashtags=None, mentions=None, users=None, min_tweets=100):
        """
        Collect tweets based on keywords, hashtags, mentions, and user timelines.
        
        Args:
            keywords: List of keywords to search for.
            hashtags: List of hashtags to search for.
            mentions: List of mentions to search for.
            users: List of users to get tweets from.
            min_tweets: Minimum number of tweets to collect.
            
        Returns:
            List of collected tweets.
        """
        keywords = keywords or []
        hashtags = hashtags or []
        mentions = mentions or []
        users = users or []
        
        collected_tweets = []
        
        # Calculate the number of tweets to collect per term
        search_terms = keywords + hashtags + mentions + users
        if not search_terms:
            logger.warning("No search terms provided. Collecting from home timeline.")
            # TODO: Add home timeline collection
            return collected_tweets
            
        posts_per_term = max(min_tweets // len(search_terms) if search_terms else min_tweets, 10)
        
        # Collect tweets for each keyword
        for keyword in keywords:
            logger.info(f"Collecting tweets for keyword: {keyword}")
            tweets = self.search_tweets(keyword, max_tweets=posts_per_term)
            collected_tweets.extend(tweets)
        
        # Collect tweets for each hashtag
        for hashtag in hashtags:
            # Add # if not present
            if not hashtag.startswith('#'):
                hashtag = f"#{hashtag}"
                
            logger.info(f"Collecting tweets for hashtag: {hashtag}")
            tweets = self.search_tweets(hashtag, max_tweets=posts_per_term)
            collected_tweets.extend(tweets)
        
        # Collect tweets for each mention
        for mention in mentions:
            # Add @ if not present
            if not mention.startswith('@'):
                mention = f"@{mention}"
                
            logger.info(f"Collecting tweets for mention: {mention}")
            tweets = self.search_tweets(mention, max_tweets=posts_per_term)
            collected_tweets.extend(tweets)
        
        # Collect tweets from user timelines
        for user in users:
            # Remove @ if present
            if user.startswith('@'):
                user = user[1:]
                
            logger.info(f"Collecting tweets from user: {user}")
            tweets = self.get_user_tweets(user, max_tweets=posts_per_term)
            collected_tweets.extend(tweets)
        
        # Check if we have enough tweets
        if len(collected_tweets) < min_tweets:
            logger.warning(f"Only collected {len(collected_tweets)} tweets, which is less than the minimum {min_tweets}")
            
            # Try to get more from popular searches if we don't have enough
            additional_searches = ["news", "trending", "viral", "popular"]
            
            for search in additional_searches:
                if len(collected_tweets) >= min_tweets:
                    break
                    
                logger.info(f"Collecting additional tweets with search: {search}")
                additional_tweets = self.search_tweets(search, max_tweets=min_tweets - len(collected_tweets))
                collected_tweets.extend(additional_tweets)
        
        logger.info(f"Total tweets collected: {len(collected_tweets)}")
        return collected_tweets
    
    def save_tweets(self, tweets, filename=None):
        """
        Save tweets to a JSON file.
        
        Args:
            tweets: List of tweets to save.
            filename: Optional filename to save tweets to.
            
        Returns:
            Path to the saved file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tweets_{timestamp}.json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tweets, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(tweets)} tweets to {filepath}")
        return filepath
    
    def collection_cycle(self, keywords=None, hashtags=None, mentions=None, users=None, min_tweets=100):
        """Run one collection cycle."""
        start_time = time.time()
        logger.info(f"Starting collection cycle {self.cycles_run + 1}")
        
        # Collect tweets
        tweets = self.collect_tweets(keywords, hashtags, mentions, users, min_tweets)
        
        # Save tweets
        if tweets:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tweets_{timestamp}.json"
            self.save_tweets(tweets, filename)
            self.total_collected += len(tweets)
        else:
            logger.warning("No tweets collected in this cycle.")
        
        # Update statistics
        self.cycles_run += 1
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        logger.info(f"Collection cycle took {elapsed:.2f} seconds")
        
        return tweets
    
    def run_collection(self, keywords=None, hashtags=None, mentions=None, users=None, min_tweets=100, 
                       max_cycles=None, single_run=False):
        """
        Run the collection process periodically.
        
        Args:
            keywords: List of keywords to search for.
            hashtags: List of hashtags to search for.
            mentions: List of mentions to search for.
            users: List of users to get tweets from.
            min_tweets: Minimum number of tweets to collect per cycle.
            max_cycles: Maximum number of cycles to run (None for unlimited).
            single_run: If True, run only once and exit.
        """
        cycle = 0
        
        self.running = True
        
        try:
            while self.running:
                cycle_start = time.time()
                
                # Run one collection cycle
                self.collection_cycle(keywords, hashtags, mentions, users, min_tweets)
                
                cycle += 1
                
                # Check if we should exit
                if single_run:
                    logger.info("Single run completed. Exiting.")
                    break
                    
                if max_cycles is not None and cycle >= max_cycles:
                    logger.info(f"Reached maximum cycles ({max_cycles}). Exiting.")
                    break
                
                # Calculate time to wait
                elapsed_time = time.time() - cycle_start
                sleep_time = max(0, self.interval - elapsed_time)
                
                if sleep_time > 0 and self.running:
                    logger.info(f"Waiting {int(sleep_time)} seconds until next collection...")
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Collection stopped by user.")
        except Exception as e:
            logger.error(f"Error during collection: {e}")
            raise
        finally:
            self.running = False
    
    def start(self, keywords=None, hashtags=None, mentions=None, users=None, min_tweets=100, 
             max_cycles=None, single_run=False):
        """Start the collection process in a separate thread."""
        if self.running:
            logger.info("Collection is already running")
            return
        
        # Reset statistics
        self.total_collected = 0
        self.cycles_run = 0
        
        # Start collection in a separate thread
        self.collection_thread = threading.Thread(
            target=self.run_collection,
            args=(keywords, hashtags, mentions, users, min_tweets, max_cycles, single_run),
            daemon=True
        )
        self.collection_thread.start()
        
        logger.info("Collection started in background thread.")
        return self.collection_thread
    
    def stop(self):
        """Stop the collection process."""
        if not self.running:
            logger.info("Collection is not running")
            return
        
        logger.info("Stopping collection...")
        self.running = False
        
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=10)
        
        logger.info("Collection stopped")
        logger.info(f"Collection summary: {self.total_collected} tweets in {self.cycles_run} cycles")
        if self.cycles_run > 0:
            logger.info(f"Average: {self.total_collected / self.cycles_run:.2f} tweets per cycle")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Collect Twitter posts based on keywords, hashtags, mentions, and users.")
    
    parser.add_argument("--keywords", type=str, default="", help="Comma-separated list of keywords to search for.")
    parser.add_argument("--hashtags", type=str, default="", help="Comma-separated list of hashtags to search for.")
    parser.add_argument("--mentions", type=str, default="", help="Comma-separated list of mentions to search for.")
    parser.add_argument("--users", type=str, default="", help="Comma-separated list of users to get tweets from.")
    parser.add_argument("--min_tweets", type=int, default=100, help="Minimum number of tweets to collect per cycle.")
    parser.add_argument("--interval", type=int, default=120, help="Interval in seconds between collections.")
    parser.add_argument("--output_dir", type=str, default="twitter_data", help="Directory to store the collected tweets.")
    parser.add_argument("--max_cycles", type=int, help="Maximum number of cycles to run.")
    parser.add_argument("--single_run", action="store_true", help="Run only once and exit.")
    
    # API credentials arguments
    parser.add_argument("--api_key", type=str, help="Twitter API key")
    parser.add_argument("--api_secret", type=str, help="Twitter API secret")
    parser.add_argument("--access_token", type=str, help="Twitter access token")
    parser.add_argument("--access_token_secret", type=str, help="Twitter access token secret")
    parser.add_argument("--bearer_token", type=str, help="Twitter bearer token")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Try to import API credentials from config.py if not provided via command line
    api_key = args.api_key
    api_secret = args.api_secret
    access_token = args.access_token
    access_token_secret = args.access_token_secret
    bearer_token = args.bearer_token
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        try:
            from config import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN
            api_key = api_key or API_KEY
            api_secret = api_secret or API_SECRET
            access_token = access_token or ACCESS_TOKEN
            access_token_secret = access_token_secret or ACCESS_TOKEN_SECRET
            bearer_token = bearer_token or BEARER_TOKEN
        except ImportError:
            logger.error("API credentials not provided and config.py not found.")
            sys.exit(1)
    
    if not all([api_key, api_secret, access_token, access_token_secret]):
        logger.error("API credentials not complete. Please provide all required credentials.")
        sys.exit(1)
    
    # Parse comma-separated lists
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    hashtags = [h.strip() for h in args.hashtags.split(",") if h.strip()]
    mentions = [m.strip() for m in args.mentions.split(",") if m.strip()]
    users = [u.strip() for u in args.users.split(",") if u.strip()]
    
    if not any([keywords, hashtags, mentions, users]):
        logger.warning("No search terms provided. Using default search terms.")
        try:
            from config import DEFAULT_KEYWORDS, DEFAULT_HASHTAGS, DEFAULT_MENTIONS, DEFAULT_USERS
            keywords = DEFAULT_KEYWORDS
            hashtags = DEFAULT_HASHTAGS
            mentions = DEFAULT_MENTIONS
            users = DEFAULT_USERS
        except ImportError:
            keywords = ["python", "javascript", "programming", "coding", "webdev"]
            hashtags = ["python", "javascript", "webdev", "coding", "100daysofcode"]
            mentions = ["twitter", "github", "vscode"]
            users = ["elonmusk", "twitter", "github"]
    
    # Initialize collector
    collector = TwitterCollector(
        api_key=api_key,
        api_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        bearer_token=bearer_token,
        output_dir=args.output_dir,
        interval=args.interval
    )
    
    # Run collection
    if args.single_run:
        logger.info("Running single collection...")
    else:
        logger.info(f"Starting continuous collection with interval {args.interval} seconds...")
    
    collector.run_collection(
        keywords=keywords,
        hashtags=hashtags,
        mentions=mentions,
        users=users,
        min_tweets=args.min_tweets,
        max_cycles=args.max_cycles,
        single_run=args.single_run
    )

if __name__ == "__main__":
    main()
