#!/usr/bin/env python3
"""
Interactive runner for the Brand Tracker.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try direct import first
    from brand_tracker import BrandTracker
    from config import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN, BRAND_CONFIGS, PLATFORMS
except ImportError:
    try:
        # Try with full package name
        from brand_tracker.brand_tracker import BrandTracker
        from brand_tracker.config import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN, BRAND_CONFIGS, PLATFORMS
    except ImportError:
        print("Could not import BrandTracker module. Make sure you're running this script from the correct directory.")
        sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_banner():
    """Print a banner for the Brand Tracker."""
    banner = """
================================================================================
                BRAND TRACKER - Social Media Monitoring Solution                
================================================================================

A SaaS solution that enables brands to monitor public perception,
address concerns early, and optimize messaging in response to real-time
sentiment trends.
"""
    print(banner)

def get_brand_config():
    """Get brand configuration from user."""
    print("\nAvailable brand configurations:")
    for i, brand in enumerate(BRAND_CONFIGS.keys(), 1):
        print(f"{i}. {brand}")
    
    while True:
        try:
            choice = input("\nSelect a configuration (number) or type 'custom' for custom setup: ")
            if choice.lower() == 'custom':
                return setup_custom_config()
            
            choice = int(choice)
            if 1 <= choice <= len(BRAND_CONFIGS):
                brand_name = list(BRAND_CONFIGS.keys())[choice - 1]
                print(f"\nSelected configuration: {brand_name}")
                return brand_name, BRAND_CONFIGS[brand_name]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number or 'custom'.")

def setup_custom_config():
    """Set up a custom brand configuration."""
    print("\nCustom Brand Configuration Setup:")
    
    brand_name = input("Enter a name for your brand configuration: ")
    
    brand_identifiers = input("Enter brand identifiers (comma-separated): ").strip()
    brand_identifiers = [b.strip() for b in brand_identifiers.split(",") if b.strip()]
    
    keywords = input("Enter keywords (comma-separated): ").strip()
    keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    
    hashtags = input("Enter hashtags (without #, comma-separated): ").strip()
    hashtags = [h.strip() for h in hashtags.split(",") if h.strip()]
    
    try:
        min_posts = int(input("Enter minimum posts per collection cycle [100]: ") or "100")
    except ValueError:
        min_posts = 100
        print("Invalid value, using default: 100")
    
    try:
        interval = int(input("Enter collection interval in seconds [120]: ") or "120")
    except ValueError:
        interval = 120
        print("Invalid value, using default: 120")
    
    config = {
        "brand_identifiers": brand_identifiers,
        "keywords": keywords,
        "hashtags": hashtags,
        "min_posts": min_posts,
        "interval": interval
    }
    
    return brand_name, config

def select_platforms():
    """Select platforms to collect from."""
    print("\nUsing all available platforms: " + ", ".join(PLATFORMS))
    return PLATFORMS  # Always return all platforms

def get_runtime():
    """Get runtime from user."""
    while True:
        try:
            runtime_input = input("\nEnter runtime in minutes (leave empty to run until stopped): ").strip()
            if not runtime_input:
                return None
            
            runtime = int(runtime_input)
            if runtime > 0:
                print(f"\nRuntime: {runtime} minutes")
                return runtime
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

def main():
    """Main function."""
    print_banner()
    
    # Get brand configuration
    brand_name, config = get_brand_config()
    
    # Select platforms
    platforms = select_platforms()
    
    # Get runtime
    runtime = get_runtime()
    max_cycles = None
    if runtime:
        # Calculate max cycles based on runtime and interval
        interval_minutes = config["interval"] / 60
        max_cycles = int(runtime / interval_minutes)
    
    # Output directory based on brand name
    output_dir = f"brand_data_{brand_name}"
    
    # Print configuration
    print("\nBrand tracking configuration:")
    print(f"- Brand identifiers: {config['brand_identifiers']}")
    print(f"- Keywords: {config['keywords']}")
    print(f"- Hashtags: {config['hashtags']}")
    print(f"- Minimum posts per cycle: {config['min_posts']}")
    print(f"- Collection interval: {config['interval']} seconds")
    
    # Confirm with user
    confirm = input("\nStart brand tracking with this configuration? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborting.")
        return
    
    # Initialize brand tracker
    tracker = BrandTracker(output_dir=output_dir, interval=config["interval"])
    
    # Set up collectors based on selected platforms
    if "twitter" in platforms:
        tracker.setup_twitter_collector(
            api_key=TWITTER_API_KEY,
            api_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            bearer_token=TWITTER_BEARER_TOKEN
        )
    
    if "reddit" in platforms:
        tracker.setup_reddit_collector()
    
    if "amazon" in platforms:
        # Use mock=True by default to use the CSV datasets
        tracker.setup_amazon_collector(use_mock=True)
    
    # Start brand tracking
    try:
        print("\nStarting brand tracking. Press Ctrl+C to stop.")
        tracker.start(
            brand_identifiers=config["brand_identifiers"],
            keywords=config["keywords"],
            hashtags=config["hashtags"],
            min_posts=config["min_posts"],
            max_cycles=max_cycles
        )
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        tracker.stop()
    
    print("\nBrand tracking completed.")
    print(f"Results saved to {output_dir} directory.")


if __name__ == "__main__":
    main()
