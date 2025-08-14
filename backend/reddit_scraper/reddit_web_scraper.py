#!/usr/bin/env python3
"""
Alternative Reddit scraper using direct web scraping instead of Pushshift API
"""

import requests
import json
import time
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditWebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def extract_hashtags_mentions(self, text: str) -> Dict[str, List[str]]:
        """Extract hashtags and mentions from text."""
        hashtags = re.findall(r'#\w+', text.lower())
        mentions = re.findall(r'u/\w+|@\w+', text.lower())
        
        return {
            "hashtags": list(set(hashtags)),
            "mentions": list(set(mentions))
        }
    
    def search_reddit_json(self, query: str, subreddit: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Search Reddit using JSON API endpoint"""
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
                        
                        # Extract content
                        content = post.get('selftext', '') or post.get('title', '')
                        
                        # Extract hashtags and mentions
                        extracted = self.extract_hashtags_mentions(content + ' ' + post.get('title', ''))
                        
                        # Format timestamp
                        timestamp = datetime.fromtimestamp(post['created_utc'], tz=timezone.utc).isoformat()
                        
                        post_formatted = {
                            "post_id": post.get('id', ''),
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
                            "is_self": post.get('is_self', False),
                            "domain": post.get('domain', ''),
                            "post_hint": post.get('post_hint', '')
                        }
                        
                        posts.append(post_formatted)
                        
                    except Exception as e:
                        logger.warning(f"Error processing post: {e}")
                        continue
            
            logger.info(f"Successfully collected {len(posts)} posts")
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            
        return posts
    
    def search_multiple_subreddits(self, query: str, subreddits: List[str], limit_per_subreddit: int = 25) -> List[Dict[str, Any]]:
        """Search multiple subreddits for posts"""
        all_posts = []
        
        for subreddit in subreddits:
            logger.info(f"Searching r/{subreddit}...")
            posts = self.search_reddit_json(query, subreddit, limit_per_subreddit)
            all_posts.extend(posts)
            time.sleep(1)  # Be nice to Reddit's servers
            
        return all_posts

def test_reddit_web_scraper():
    """Test the Reddit web scraper"""
    scraper = RedditWebScraper()
    
    # Test general search
    print("Testing general search...")
    posts = scraper.search_reddit_json("python", limit=5)
    
    print(f"Found {len(posts)} posts")
    for i, post in enumerate(posts[:2]):
        print(f"\nPost {i+1}:")
        print(f"  ID: {post['post_id']}")
        print(f"  Author: {post['username']}")
        print(f"  Title: {post['title'][:100]}...")
        print(f"  Subreddit: {post['subreddit']}")
        print(f"  Upvotes: {post['engagement_metrics']['upvotes']}")
        print(f"  Comments: {post['engagement_metrics']['num_comments']}")
    
    return posts

if __name__ == "__main__":
    test_reddit_web_scraper()
