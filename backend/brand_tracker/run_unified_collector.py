"""
Run the unified brand data collector with real data from Twitter, Reddit, Google News, and Amazon.
"""
import os
import sys
import time
import logging
import argparse
from unified_collector import UnifiedBrandDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RunUnifiedCollector")

def parse_args():
    parser = argparse.ArgumentParser(description="Run the unified brand data collector")
    
    # Available brand configurations
    brands = ["apple", "mcdonalds", "nike", "starbucks", "tesla", "custom"]
    
    parser.add_argument(
        "--brand", 
        choices=brands,
        default="apple",
        help="Brand configuration to use"
    )
    
    parser.add_argument(
        "--interval", 
        type=int, 
        default=60,
        help="Collection interval in seconds"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="results",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--max-cycles", 
        type=int, 
        default=None,
        help="Maximum number of collection cycles to run"
    )
    
    parser.add_argument(
        "--platforms", 
        type=str, 
        default="twitter,reddit,news,amazon",
        help="Comma-separated list of platforms to collect from"
    )
    
    return parser.parse_args()

def print_banner():
    """Print a banner for the Brand Tracker."""
    banner = """
================================================================================
                UNIFIED BRAND TRACKER - Real-time Data Collection                
================================================================================

Collecting real-time brand data from multiple platforms:
- Twitter
- Reddit
- Google News
- Amazon

Data will be fed directly to the Brand Pulse Dashboard for real-time visualization.
"""
    print(banner)

def main():
    """Main function."""
    args = parse_args()
    print_banner()
    
    # Print selected configuration
    logger.info(f"Selected brand: {args.brand}")
    logger.info(f"Collection interval: {args.interval} seconds")
    logger.info(f"Output directory: {args.output_dir}")
    if args.max_cycles:
        logger.info(f"Maximum cycles: {args.max_cycles}")
    logger.info(f"Platforms: {args.platforms}")
    
    # Confirm with user
    confirm = input("\nStart brand data collection with this configuration? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Aborting.")
        return
    
    # Create the output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize the collector
    collector = UnifiedBrandDataCollector(
        brand_name=args.brand,
        output_dir=args.output_dir,
        interval=args.interval
    )
    
    # Start collection
    try:
        logger.info("Starting brand data collection...")
        collector.start(max_cycles=args.max_cycles)
        
        # Display progress information
        while collector.running:
            # Print collection stats every 10 seconds
            time.sleep(10)
            if collector.cycles_run > 0:
                logger.info(f"Collection status: {collector.total_collected} posts in {collector.cycles_run} cycles")
                for platform, count in collector.platform_stats.items():
                    if count > 0:
                        logger.info(f"  - {platform}: {count} posts")
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user. Stopping collection...")
        collector.stop()
    
    logger.info("Brand data collection completed.")
    logger.info(f"Results saved to {os.path.abspath(args.output_dir)}")

if __name__ == "__main__":
    main()
