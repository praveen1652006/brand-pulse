#!/usr/bin/env python3
"""
Sample Reddit collection script with predefined configurations
"""

import subprocess
import sys
import os

def run_collection(config_name: str):
    """Run Reddit collection with predefined configurations."""
    
    configs = {
        "programming": {
            "keywords": "python,javascript,programming,coding,webdev",
            "hashtags": "python,javascript,webdev,coding,100daysofcode",
            "mentions": "u/python,u/javascript,u/webdev",
            "min_posts": 100,
            "interval": 120
        },
        "tech_news": {
            "keywords": "technology,AI,machine learning,artificial intelligence",
            "hashtags": "tech,AI,machinelearning,artificialintelligence",
            "mentions": "u/technology,u/MachineLearning",
            "min_posts": 80,
            "interval": 180
        },
        "cryptocurrency": {
            "keywords": "bitcoin,ethereum,cryptocurrency,crypto,blockchain",
            "hashtags": "crypto,bitcoin,ethereum,blockchain,btc",
            "mentions": "u/Bitcoin,u/ethereum,u/CryptoCurrency",
            "min_posts": 120,
            "interval": 120
        },
        "gaming": {
            "keywords": "gaming,games,videogames,esports",
            "hashtags": "gaming,videogames,esports,gamedev",
            "mentions": "u/gaming,u/Games,u/pcgaming",
            "min_posts": 100,
            "interval": 120
        },
        "science": {
            "keywords": "science,research,discovery,breakthrough",
            "hashtags": "science,research,scicomm",
            "mentions": "u/science,u/askscience",
            "min_posts": 60,
            "interval": 300
        }
    }
    
    if config_name not in configs:
        print(f"Available configurations: {', '.join(configs.keys())}")
        return
    
    config = configs[config_name]
    
    # Build command
    cmd = [
        sys.executable, "reddit_collector.py",
        "--keywords", config["keywords"],
        "--hashtags", config["hashtags"],
        "--mentions", config["mentions"],
        "--min_posts", str(config["min_posts"]),
        "--interval", str(config["interval"])
    ]
    
    print(f"Running {config_name} configuration...")
    print(f"Keywords: {config['keywords']}")
    print(f"Hashtags: {config['hashtags']}")
    print(f"Mentions: {config['mentions']}")
    print(f"Min posts: {config['min_posts']}")
    print(f"Interval: {config['interval']} seconds")
    print("-" * 50)
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nCollection stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running collection: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python sample_runner.py <config_name>")
        print("\nAvailable configurations:")
        print("- programming: Python, JavaScript, coding topics")
        print("- tech_news: Technology, AI, machine learning")
        print("- cryptocurrency: Bitcoin, crypto, blockchain")
        print("- gaming: Gaming, esports, video games")
        print("- science: Science, research, discoveries")
        print("\nExample: python sample_runner.py programming")
        return
    
    config_name = sys.argv[1]
    run_collection(config_name)

if __name__ == "__main__":
    main()
