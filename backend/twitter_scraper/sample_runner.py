#!/usr/bin/env python3
"""
Sample Runner for Twitter Collector - Runs the Twitter collector with predefined configurations.
"""

import os
import sys
import time
from twitter_collector import TwitterCollector

# Try to import config
try:
    from config import (
        API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN,
        DEFAULT_KEYWORDS, DEFAULT_HASHTAGS, DEFAULT_MENTIONS, DEFAULT_USERS,
        MIN_TWEETS, INTERVAL
    )
except ImportError as e:
    print(f"Error importing config: {e}")
    print("Please make sure config.py exists with the required variables.")
    sys.exit(1)

# Predefined configurations
CONFIGURATIONS = {
    "programming": {
        "keywords": ["python", "javascript", "programming", "coding", "webdev"],
        "hashtags": ["python", "javascript", "webdev", "coding", "100daysofcode"],
        "mentions": ["github", "vscode", "stackoverflow"],
        "users": ["github", "vscode", "ThePSF"],
        "min_tweets": 100,
        "interval": 120
    },
    "tech": {
        "keywords": ["technology", "tech", "innovation", "gadget", "devices"],
        "hashtags": ["tech", "technology", "innovation", "ai", "machinelearning"],
        "mentions": ["WIRED", "TechCrunch", "verge"],
        "users": ["WIRED", "TechCrunch", "verge"],
        "min_tweets": 100,
        "interval": 120
    },
    "ai": {
        "keywords": ["ai", "artificialintelligence", "machinelearning", "deeplearning", "nlp"],
        "hashtags": ["ai", "artificialintelligence", "machinelearning", "deeplearning", "llm"],
        "mentions": ["OpenAI", "DeepMind", "huggingface"],
        "users": ["OpenAI", "DeepMind", "huggingface"],
        "min_tweets": 100,
        "interval": 120
    },
    "news": {
        "keywords": ["news", "breaking", "headlines", "world", "politics"],
        "hashtags": ["news", "breaking", "headlines", "politics", "worldnews"],
        "mentions": ["CNN", "BBCNews", "Reuters"],
        "users": ["CNN", "BBCNews", "Reuters"],
        "min_tweets": 100,
        "interval": 120
    }
}

def run_configuration(config_name, single_run=False, max_cycles=None):
    """Run the collector with a predefined configuration."""
    if config_name not in CONFIGURATIONS:
        print(f"Configuration '{config_name}' not found. Available configurations:")
        for name in CONFIGURATIONS:
            print(f"- {name}")
        return
    
    config = CONFIGURATIONS[config_name]
    
    print(f"Running {config_name} configuration...")
    print(f"Keywords: {', '.join(config['keywords'])}")
    print(f"Hashtags: {', '.join(config['hashtags'])}")
    print(f"Mentions: {', '.join(config['mentions'])}")
    print(f"Users: {', '.join(config['users'])}")
    print(f"Min tweets: {config['min_tweets']}")
    print(f"Interval: {config['interval']} seconds")
    print(f"Single run: {single_run}")
    if max_cycles:
        print(f"Max cycles: {max_cycles}")
    print("--------------------------------------------------")
    
    # Initialize collector
    collector = TwitterCollector(
        api_key=API_KEY,
        api_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
        bearer_token=BEARER_TOKEN,
        interval=config['interval']
    )
    
    # Run collection
    collector.run_collection(
        keywords=config['keywords'],
        hashtags=config['hashtags'],
        mentions=config['mentions'],
        users=config['users'],
        min_tweets=config['min_tweets'],
        max_cycles=max_cycles,
        single_run=single_run
    )

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Twitter collector with predefined configurations.")
    parser.add_argument("config", choices=list(CONFIGURATIONS.keys()) + ["list"], help="Configuration name or 'list' to see available configurations")
    parser.add_argument("--single-run", action="store_true", help="Run only once and exit")
    parser.add_argument("--max-cycles", type=int, help="Maximum number of cycles to run")
    
    args = parser.parse_args()
    
    if args.config == "list":
        print("Available configurations:")
        for name, config in CONFIGURATIONS.items():
            print(f"\n{name}:")
            print(f"  Keywords: {', '.join(config['keywords'])}")
            print(f"  Hashtags: {', '.join(config['hashtags'])}")
            print(f"  Mentions: {', '.join(config['mentions'])}")
            print(f"  Users: {', '.join(config['users'])}")
            print(f"  Min tweets: {config['min_tweets']}")
            print(f"  Interval: {config['interval']} seconds")
        return
    
    run_configuration(args.config, single_run=args.single_run, max_cycles=args.max_cycles)

if __name__ == "__main__":
    main()
