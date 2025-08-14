#!/usr/bin/env python3
"""
Test script to debug Reddit scraping with snscrape
"""

import snscrape.modules.reddit as snreddit

def test_reddit_scraper():
    print("Testing Reddit scraper...")
    
    try:
        # Test with a simple query
        query = "python"
        print(f"Searching for: {query}")
        
        scraper = snreddit.RedditSearchScraper(query)
        print(f"Scraper created: {scraper}")
        
        # Get a few items to test
        count = 0
        for post in scraper.get_items():
            count += 1
            print(f"\nPost {count}:")
            print(f"  ID: {getattr(post, 'id', 'N/A')}")
            print(f"  Author: {getattr(post, 'author', 'N/A')}")
            print(f"  Title: {getattr(post, 'title', 'N/A')}")
            print(f"  Content: {getattr(post, 'content', 'N/A')}")
            print(f"  Subreddit: {getattr(post, 'subreddit', 'N/A')}")
            print(f"  Score: {getattr(post, 'score', 'N/A')}")
            print(f"  URL: {getattr(post, 'url', 'N/A')}")
            print(f"  Date: {getattr(post, 'date', 'N/A')}")
            
            # Print all available attributes
            print(f"  Available attributes: {dir(post)}")
            
            if count >= 2:  # Just get 2 posts for testing
                break
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reddit_scraper()
