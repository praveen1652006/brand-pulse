#!/usr/bin/env python3
"""
Reddit Post Collector - Collects Reddit posts based on keywords, hashtags and mentions.
Stores collected posts in JSON format.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Set
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditCollector:
    """Collects Reddit posts based on keywords, hashtags and mentions."""
    
    def __init__(self, output_dir: str = "reddit_data", interval: int = 120):
        """
        Initialize the RedditCollector.
        
        Args:
            output_dir: Directory to store the collected posts.
            interval: Interval in seconds between collections.
        """
        self.output_dir = output_dir
        self.interval = interval
        self.collected_posts: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_hashtags_mentions(self, text: str) -> Dict[str, List[str]]:
        """
        Extract hashtags and mentions from text.
        
        Args:
            text: Text to extract hashtags and mentions from.
            
        Returns:
            Dict with hashtags and mentions.
        """
        hashtags = re.findall(r'#\w+', text.lower())
        mentions = re.findall(r'u/\w+|@\w+|r/\w+', text.lower())
        
        return {
            "hashtags": list(set(hashtags)),
            "mentions": list(set(mentions))
        }
    
    def search_reddit_json(self, query: str, subreddit: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search Reddit using JSON API endpoint.
        
        Args:
            query: Search query.
            subreddit: Optional subreddit to search in.
            limit: Maximum number of posts to retrieve.
            
        Returns:
            List of posts.
        """
        posts = []
        
        try:
            # Construct the search URL
            if subreddit:
                base_url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    'q': query,
                    'restrict_sr': 'true',
                    'sort': 'new',
                    'limit': min(limit, 100)  # Reddit limits to 100 per request
                }
            else:
                base_url = "https://www.reddit.com/search.json"
                params = {
                    'q': query,
                    'sort': 'new',
                    'limit': min(limit, 100)
                }
            
            logger.info(f"Searching Reddit: {base_url} with params: {params}")
            
            response = self.session.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and 'children' in data['data']:
                for post_data in data['data']['children']:
                    try:
                        post = post_data['data']
                        post_id = post.get('id', '')
                        
                        # Skip if already collected
                        if post_id in self.collected_posts:
                            continue
                            
                        self.collected_posts.add(post_id)
                        
                        # Extract content
                        content = post.get('selftext', '') or post.get('title', '')
                        
                        # Extract hashtags and mentions
                        extracted = self.extract_hashtags_mentions(content + ' ' + post.get('title', ''))
                        
                        # Format timestamp
                        timestamp = datetime.fromtimestamp(post['created_utc'], tz=timezone.utc).isoformat()
                        
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
                            "extracted_hashtags": extracted["hashtags"],
                            "extracted_mentions": extracted["mentions"],
                            "query": query
                        }
                        
                        posts.append(post_formatted)
                        
                    except Exception as e:
                        logger.warning(f"Error processing post: {e}")
                        continue
            
            logger.info(f"Successfully collected {len(posts)} posts for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            
        return posts
    
    def search_multiple_subreddits(self, query: str, subreddits: List[str], limit_per_subreddit: int = 25) -> List[Dict[str, Any]]:
        """
        Search multiple subreddits for posts.
        
        Args:
            query: Search query.
            subreddits: List of subreddits to search in.
            limit_per_subreddit: Maximum number of posts to retrieve per subreddit.
            
        Returns:
            List of posts.
        """
        all_posts = []
        
        for subreddit in subreddits:
            logger.info(f"Searching r/{subreddit}...")
            posts = self.search_reddit_json(query, subreddit, limit_per_subreddit)
            all_posts.extend(posts)
            time.sleep(1)  # Be nice to Reddit's servers
            
        return all_posts
    
    def search_posts(self, query: str, max_posts: int = 100) -> List[Dict[str, Any]]:
        """
        Search for Reddit posts using the given query.
        
        Args:
            query: Search query.
            max_posts: Maximum number of posts to retrieve.
            
        Returns:
            List of posts.
        """
        posts_data = []
        
        try:
            # First try general search
            general_posts = self.search_reddit_json(query, limit=max_posts)
            posts_data.extend(general_posts)
            
            # If we don't have enough posts, try some popular subreddits related to the query
            if len(posts_data) < max_posts:
                # Get popular related subreddits based on the query
                popular_subreddits = self.get_related_subreddits(query)
                remaining_posts = max_posts - len(posts_data)
                limit_per_subreddit = max(5, remaining_posts // max(1, len(popular_subreddits)))
                
                subreddit_posts = self.search_multiple_subreddits(
                    query, 
                    popular_subreddits, 
                    limit_per_subreddit
                )
                
                # Add unique posts
                for post in subreddit_posts:
                    if post['post_id'] not in {p['post_id'] for p in posts_data}:
                        posts_data.append(post)
                        if len(posts_data) >= max_posts:
                            break
            
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            
        logger.info(f"Total posts collected: {len(posts_data)}")
        return posts_data
    
    def get_related_subreddits(self, query: str) -> List[str]:
        """
        Get popular subreddits related to the query.
        
        Args:
            query: Search query.
            
        Returns:
            List of subreddit names.
        """
        # Static list of popular subreddits for common topics
        popular_subreddits = {
            "python": ["Python", "learnpython", "programming", "coding", "compsci"],
            "programming": ["programming", "learnprogramming", "coding", "webdev", "javascript"],
            "gaming": ["gaming", "pcgaming", "games", "GameDeals", "gamernews"],
            "news": ["news", "worldnews", "politics", "technology", "science"],
            "tech": ["technology", "gadgets", "futurology", "tech", "hardware"],
            "music": ["Music", "listentothis", "hiphopheads", "metal", "electronicmusic"],
            "sports": ["sports", "nba", "soccer", "nfl", "baseball"],
            "movies": ["movies", "television", "anime", "netflixbestof", "boxoffice"],
            "crypto": ["CryptoCurrency", "Bitcoin", "ethereum", "CryptoMarkets", "binance"],
            "science": ["science", "askscience", "Physics", "biology", "chemistry"],
            "ai": ["artificial", "MachineLearning", "deeplearning", "OpenAI", "chatgpt"],
            "default": ["all", "popular", "AskReddit", "pics", "videos"]
        }
        
        # Look for keywords in the query
        for keyword, subreddits in popular_subreddits.items():
            if keyword.lower() in query.lower():
                return subreddits
                
        return popular_subreddits["default"]
    
    def collect_posts(self, keywords: List[str], hashtags: List[str], mentions: List[str], min_posts: int = 100) -> List[Dict[str, Any]]:
        """
        Collect posts based on keywords, hashtags and mentions.
        
        Args:
            keywords: List of keywords to search for.
            hashtags: List of hashtags to search for.
            mentions: List of mentions to search for.
            min_posts: Minimum number of posts to collect.
            
        Returns:
            List of collected posts.
        """
        collected_posts = []
        
        # Calculate the number of posts to collect per term
        search_terms = keywords + hashtags + mentions
        if not search_terms:
            logger.warning("No search terms provided.")
            return collected_posts
            
        posts_per_term = max(min_posts // len(search_terms), 10)
        
        # Collect posts for each keyword
        for keyword in keywords:
            logger.info(f"Collecting posts for keyword: {keyword}")
            posts = self.search_posts(keyword, max_posts=posts_per_term)
            collected_posts.extend(posts)
        
        # Collect posts for each hashtag
        for hashtag in hashtags:
            # Add # if not present
            if not hashtag.startswith('#'):
                hashtag = f"#{hashtag}"
                
            logger.info(f"Collecting posts for hashtag: {hashtag}")
            posts = self.search_posts(hashtag, max_posts=posts_per_term)
            collected_posts.extend(posts)
        
        # Collect posts for each mention
        for mention in mentions:
            # Add u/ if not present (Reddit usernames use u/ prefix)
            if not mention.startswith('u/') and not mention.startswith('@'):
                mention = f"u/{mention}"
                
            logger.info(f"Collecting posts for mention: {mention}")
            posts = self.search_posts(mention, max_posts=posts_per_term)
            collected_posts.extend(posts)
        
        logger.info(f"Total unique posts collected: {len(collected_posts)}")
        return collected_posts
    
    def save_posts(self, posts: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save posts to a JSON file.
        
        Args:
            posts: List of posts to save.
            filename: Optional filename to save posts to.
            
        Returns:
            Path to the saved file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_posts_{timestamp}.json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(posts)} posts to {filepath}")
        return filepath
    
    def run_collection(self, keywords: List[str], hashtags: List[str], mentions: List[str], min_posts: int = 100, 
                       max_iterations: int = None, single_run: bool = False) -> None:
        """
        Run the collection process periodically.
        
        Args:
            keywords: List of keywords to search for.
            hashtags: List of hashtags to search for.
            mentions: List of mentions to search for.
            min_posts: Minimum number of posts to collect per iteration.
            max_iterations: Maximum number of iterations to run (None for unlimited).
            single_run: If True, run only once and exit.
        """
        iteration = 0
        
        try:
            while True:
                start_time = time.time()
                logger.info(f"Starting collection iteration {iteration + 1}")
                
                # Collect posts
                posts = self.collect_posts(keywords, hashtags, mentions, min_posts)
                
                # Save posts if any were collected
                if posts:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"reddit_posts_{timestamp}.json"
                    self.save_posts(posts, filename)
                else:
                    logger.warning("No posts collected in this iteration.")
                
                iteration += 1
                
                # Check if we should exit
                if single_run:
                    logger.info("Single run completed. Exiting.")
                    break
                    
                if max_iterations is not None and iteration >= max_iterations:
                    logger.info(f"Reached maximum iterations ({max_iterations}). Exiting.")
                    break
                
                # Calculate time to sleep
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed_time)
                
                if sleep_time > 0:
                    logger.info(f"Waiting {int(sleep_time)} seconds until next collection...")
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Collection stopped by user.")
        except Exception as e:
            logger.error(f"Error during collection: {e}")
            raise

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Collect Reddit posts based on keywords, hashtags and mentions.")
    
    parser.add_argument("--keywords", type=str, default="", help="Comma-separated list of keywords to search for.")
    parser.add_argument("--hashtags", type=str, default="", help="Comma-separated list of hashtags to search for.")
    parser.add_argument("--mentions", type=str, default="", help="Comma-separated list of mentions to search for.")
    parser.add_argument("--min_posts", type=int, default=100, help="Minimum number of posts to collect per iteration.")
    parser.add_argument("--interval", type=int, default=120, help="Interval in seconds between collections.")
    parser.add_argument("--output_dir", type=str, default="reddit_data", help="Directory to store the collected posts.")
    parser.add_argument("--max_iterations", type=int, help="Maximum number of iterations to run.")
    parser.add_argument("--single_run", action="store_true", help="Run only once and exit.")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Parse comma-separated lists
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    hashtags = [h.strip() for h in args.hashtags.split(",") if h.strip()]
    mentions = [m.strip() for m in args.mentions.split(",") if m.strip()]
    
    if not any([keywords, hashtags, mentions]):
        logger.error("No search terms provided. Please specify at least one keyword, hashtag, or mention.")
        sys.exit(1)
    
    # Initialize collector
    collector = RedditCollector(output_dir=args.output_dir, interval=args.interval)
    
    # Run collection
    if args.single_run:
        logger.info("Running single collection...")
    else:
        logger.info(f"Starting continuous collection with interval {args.interval} seconds...")
    
    collector.run_collection(
        keywords=keywords,
        hashtags=hashtags,
        mentions=mentions,
        min_posts=args.min_posts,
        max_iterations=args.max_iterations,
        single_run=args.single_run
    )

if __name__ == "__main__":
    main()
