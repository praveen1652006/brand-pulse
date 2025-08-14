#!/usr/bin/env python3
"""
Interactive runner for the Asynchronous Brand Tracker.
"""

import os
import sys
import asyncio
import logging
import argparse
import traceback
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import (
        TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, 
        TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN,
        GOOGLE_NEWS_API_KEY, APIFY_API_KEY, BRAND_CONFIGS, PLATFORMS
    )
    from async_brand_tracker import AsyncBrandTracker
except ImportError:
    print("Could not import necessary modules. Make sure you're running this script from the correct directory.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_banner():
    """Print a welcome banner."""
    print("\n" + "=" * 80)
    print("=" * 80)
    print("ENHANCED BRAND TRACKER - Asynchronous Data Collection".center(80))
    print("=" * 80)
    print("=" * 80)
    print("\nA SaaS solution that enables brands to monitor public perception,")
    print("address concerns early, and optimize messaging in response to real-time")
    print("sentiment trends.\n")

def get_brand_config():
    """Get brand configuration from user input."""
    print("\nAvailable brand configurations:")
    for i, brand in enumerate(BRAND_CONFIGS.keys(), 1):
        print(f"{i}. {brand}")
    
    while True:
        try:
            choice = input("\nSelect a configuration (number) or type 'custom' for custom setup: ")
            if choice.lower() == 'custom':
                return create_custom_config()
            
            choice = int(choice)
            if 1 <= choice <= len(BRAND_CONFIGS):
                brand_name = list(BRAND_CONFIGS.keys())[choice - 1]
                return brand_name, BRAND_CONFIGS[brand_name]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number or 'custom'.")

def get_platforms():
    """Get platforms to collect data from."""
    print("\nAvailable data sources:")
    for i, platform in enumerate(PLATFORMS, 1):
        print(f"{i}. {platform}")
    
    while True:
        try:
            choice = input("\nSelect platforms (comma-separated numbers, or 'all' for all): ").strip()
            if choice.lower() == 'all':
                return PLATFORMS
            
            selected_indices = [int(x.strip()) for x in choice.split(',') if x.strip()]
            selected_platforms = []
            
            for idx in selected_indices:
                if 1 <= idx <= len(PLATFORMS):
                    selected_platforms.append(PLATFORMS[idx-1])
                else:
                    print(f"Invalid choice: {idx}. Please try again.")
                    break
            else:
                if selected_platforms:
                    return selected_platforms
                else:
                    print("No valid platforms selected. Please try again.")
        except ValueError:
            print("Please enter numbers separated by commas, or 'all'.")

def create_custom_config():
    """Create a custom brand tracking configuration."""
    print("\n--- Custom Brand Configuration ---")
    
    # Get brand identifiers
    brand_name = input("Enter a name for this configuration: ").strip()
    brand_identifiers_input = input("Enter brand identifiers (comma-separated): ").strip()
    brand_identifiers = [b.strip() for b in brand_identifiers_input.split(",") if b.strip()]
    
    # Get keywords
    keywords_input = input("Enter keywords to track (comma-separated): ").strip()
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    
    # Get hashtags
    hashtags_input = input("Enter hashtags to track (without #, comma-separated): ").strip()
    hashtags = [h.strip() for h in hashtags_input.split(",") if h.strip()]
    
    # Get min_posts
    min_posts_input = input("Enter minimum posts per cycle [100]: ").strip()
    min_posts = int(min_posts_input) if min_posts_input else 100
    
    # Get interval
    interval_input = input("Enter collection interval in seconds [60]: ").strip()
    interval = int(interval_input) if interval_input else 60
    
    config = {
        "brand_identifiers": brand_identifiers,
        "keywords": keywords,
        "hashtags": hashtags,
        "min_posts": min_posts,
        "interval": interval
    }
    
    return brand_name, config

def get_runtime():
    """Get runtime configuration."""
    while True:
        runtime_input = input("\nEnter runtime in minutes (leave empty to run until stopped): ").strip()
        if not runtime_input:
            return None
        
        try:
            runtime = int(runtime_input)
            if runtime > 0:
                return runtime
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

async def parse_command_line():
    """Parse command line arguments for non-interactive mode."""
    parser = argparse.ArgumentParser(description="Run the Asynchronous Brand Tracker")
    
    parser.add_argument("--brand", choices=list(BRAND_CONFIGS.keys()), 
                      help="Brand configuration to use")
    parser.add_argument("--runtime", type=int, 
                      help="Runtime in minutes (defaults to running until stopped)")
    parser.add_argument("--platforms", nargs="+", choices=PLATFORMS,
                      help="Platforms to collect data from (defaults to all)")
    parser.add_argument("--non-interactive", action="store_true", 
                      help="Run in non-interactive mode")
    
    args = parser.parse_args()
    return args

async def main():
    """Main function to run the brand tracker interactively or via command line."""
    # Parse command line arguments
    args = await parse_command_line()
    
    # Check if running in non-interactive mode
    if args.non_interactive and args.brand:
        # Non-interactive mode with command line arguments
        brand_name = args.brand
        config = BRAND_CONFIGS[brand_name]
        runtime = args.runtime
        platforms = args.platforms or PLATFORMS
        
        logger.info(f"Running in non-interactive mode for brand: {brand_name}")
        logger.info(f"Using platforms: {', '.join(platforms)}")
        if runtime:
            logger.info(f"Runtime: {runtime} minutes")
        else:
            logger.info("Runtime: Until manually stopped")
    else:
        # Interactive mode with user input
        print_banner()
        
        # Get brand configuration
        brand_name, config = get_brand_config()
        print(f"\nSelected configuration: {brand_name}")
        
        # Get platforms
        platforms = get_platforms()
        print(f"\nUsing {len(platforms) == len(PLATFORMS) and 'all available' or 'selected'} platforms: {', '.join(platforms)}")
        
        # Get runtime
        runtime = get_runtime()
        if runtime:
            print(f"\nRuntime: {runtime} minutes")
        else:
            print("\nRuntime: Until manually stopped")
        
        # Confirm start
        print("\nBrand tracking configuration:")
        print(f"- Brand identifiers: {config['brand_identifiers']}")
        print(f"- Keywords: {config['keywords']}")
        print(f"- Hashtags: {config['hashtags']}")
        print(f"- Minimum posts per cycle: {config['min_posts']}")
        print(f"- Collection interval: {config['interval']} seconds")
        
        confirm = input("\nStart brand tracking with this configuration? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Brand tracking cancelled.")
            return
    
    # Initialize brand tracker
    tracker = AsyncBrandTracker(output_dir=f"brand_data_{brand_name}", interval=config['interval'])
    
    # Create directories for the brand
    os.makedirs(tracker.output_dir, exist_ok=True)
    logger.info("Created directories for brand data")
    
    # Set Twitter API credentials
    tracker.set_twitter_credentials(
        api_key=TWITTER_API_KEY,
        api_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        bearer_token=TWITTER_BEARER_TOKEN
    )
    logger.info("Twitter API key set")
    
    # Set Google News API key
    tracker.set_google_news_api_key(GOOGLE_NEWS_API_KEY)
    logger.info("Google News API key set")
    
    # Initialize Amazon collector (if method exists)
    if hasattr(tracker, 'setup_amazon_collector'):
        tracker.setup_amazon_collector(use_mock=True)
        logger.info("Amazon collector initialized")
    
    # Start brand tracking
    try:
        if not args.non_interactive:
            print("\nStarting enhanced brand tracker. Press Ctrl+C to stop.")
        
        max_cycles = runtime * 60 // config['interval'] if runtime else None
        
        await tracker.start(
            brand_identifiers=config['brand_identifiers'],
            keywords=config['keywords'],
            hashtags=config['hashtags'],
            min_posts=config['min_posts'],
            max_cycles=max_cycles
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error during brand tracking: {e}")
        traceback.print_exc()
    
    print("\nBrand tracking complete!")
    print(f"Results saved to: {os.path.abspath(tracker.output_dir)}")

if __name__ == "__main__":
    asyncio.run(main())
