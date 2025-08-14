#!/usr/bin/env python3
"""
Google News Collector - Collects news articles related to a brand or topic.
"""

import os
import json
import logging
import requests
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleNewsCollector:
    """
    Collects news articles from Google News API.
    """
    
    def __init__(self, api_key=None, output_dir="google_news_data"):
        """Initialize the Google News collector."""
        self.api_key = api_key
        self.output_dir = output_dir
        self.base_url = "https://newsapi.org/v2/everything"
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("Google News collector initialized")
    
    def set_api_key(self, api_key):
        """Set the API key."""
        self.api_key = api_key
        logger.info("API key set")
    
    async def search_news(self, query, days=7, max_results=20, language="en", sort_by="publishedAt"):
        """
        Search for news articles.
        
        Args:
            query: Search query
            days: Number of days to look back
            max_results: Maximum number of results to return
            language: Language code (default: en)
            sort_by: Sort order (default: publishedAt)
            
        Returns:
            List of news articles
        """
        if not self.api_key:
            logger.error("API key not set")
            return []
        
        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        # Prepare request
        params = {
            "q": query,
            "from": from_date,
            "to": to_date,
            "language": language,
            "sortBy": sort_by,
            "apiKey": self.api_key,
            "pageSize": min(max_results, 100)  # API limit is 100
        }
        
        try:
            logger.info(f"Searching news for query: {query}")
            response = requests.get(self.base_url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Error searching news: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            articles = data.get("articles", [])
            
            # Format articles for brand tracker
            formatted_articles = []
            for article in articles:
                formatted_article = {
                    "article_id": article.get("url", "").split("/")[-1],
                    "title": article.get("title", ""),
                    "text_content": article.get("description", "") + "\n" + article.get("content", ""),
                    "timestamp": article.get("publishedAt", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "author": article.get("author", ""),
                    "platform": "news",
                    "engagement_metrics": {
                        "source": article.get("source", {}).get("name", ""),
                    },
                    "brand_tracker": {
                        "matched_term": query,
                        "term_type": "keyword",
                        "brands_mentioned": []
                    }
                }
                formatted_articles.append(formatted_article)
            
            logger.info(f"Found {len(formatted_articles)} news articles for query: {query}")
            
            # Save results
            self.save_articles(formatted_articles, query)
            
            return formatted_articles
            
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []
    
    def save_articles(self, articles, query):
        """Save articles to file."""
        if not articles:
            return None
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_articles_{query.replace(' ', '_').lower()}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(articles)} articles to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
            return None

async def main():
    """Main function for testing."""
    # Set your API key here
    api_key = "97beed4894894a2b8bfd54a1e9c27e4c"
    
    collector = GoogleNewsCollector(api_key=api_key)
    
    # Test search
    articles = await collector.search_news("Tesla", days=7, max_results=10)
    
    # Print results
    print(f"Found {len(articles)} articles")
    for article in articles[:3]:
        print(f"- {article['title']} ({article['source']})")

if __name__ == "__main__":
    asyncio.run(main())
