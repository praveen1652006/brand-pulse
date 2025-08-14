#!/usr/bin/env python3
"""
Integrated runner for the Brand Tracker and Dashboard
This script starts both the async brand tracker and the Streamlit dashboard in parallel.
"""

import os
import sys
import subprocess
import time
import argparse
import signal
import threading
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("integrated_runner.log")
    ]
)
logger = logging.getLogger(__name__)

# Track child processes to terminate them properly
child_processes = []

def signal_handler(sig, frame):
    """Handle termination signals to gracefully shut down all processes."""
    logger.info("Shutting down all processes...")
    for process in child_processes:
        if process.poll() is None:  # if process is still running
            logger.info(f"Terminating process PID {process.pid}")
            try:
                process.terminate()
                process.wait(timeout=5)  # wait up to 5 seconds for normal termination
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.pid} did not terminate gracefully, killing it")
                process.kill()
    
    logger.info("All processes terminated. Exiting.")
    sys.exit(0)

def run_brand_tracker(brand_name="apple", non_interactive=True, runtime=None):
    """Start the brand tracker in a separate process."""
    logger.info("Starting the async brand tracker...")
    
    # Construct the command
    cmd = [sys.executable, os.path.join("brand_tracker", "run_async_brand_tracker.py"), "--non-interactive", "--brand", brand_name]
    
    if runtime:
        cmd.extend(["--runtime", str(runtime)])
    
    logger.info(f"Command: {' '.join(cmd)}")
    
    # Start the process
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        child_processes.append(process)
        
        # Start a thread to read and log output
        def log_output():
            for line in process.stdout:
                logger.info(f"[BRAND TRACKER] {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        logger.info(f"Brand tracker started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Error starting brand tracker: {e}")
        return None

def run_dashboard():
    """Start the Streamlit dashboard in a separate process."""
    logger.info("Starting the dashboard...")
    
    # Construct the command for Streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", os.path.join("median_model", "dashboard.py")]
    
    logger.info(f"Command: {' '.join(cmd)}")
    
    # Start the process
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        child_processes.append(process)
        
        # Start a thread to read and log output
        def log_output():
            for line in process.stdout:
                logger.info(f"[DASHBOARD] {line.strip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        logger.info(f"Dashboard started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        return None

def create_results_dir():
    """Ensure the results directory exists."""
    results_dir = os.path.join("results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)
        logger.info(f"Created results directory at {results_dir}")
    
    # Check if results.json exists, create empty template if not
    results_file = os.path.join(results_dir, "results.json")
    if not os.path.exists(results_file):
        import json
        
        template_data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_posts": 0,
                "platforms": {
                    "twitter": 0,
                    "reddit": 0,
                    "news": 0,
                    "amazon": 0
                }
            },
            "posts": []
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Created template results.json file at {results_file}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Integrated Brand Tracker and Dashboard")
    
    # Available brands from config.py
    available_brands = ["apple", "mcdonalds", "nike", "starbucks", "tesla", "custom"]
    
    parser.add_argument("--brand", choices=available_brands, default="apple",
                      help="Brand configuration to use (default: apple)")
    parser.add_argument("--runtime", type=int, default=None,
                      help="Runtime in minutes (default: run until stopped)")
    parser.add_argument("--dashboard-only", action="store_true",
                      help="Run only the dashboard without the brand tracker")
    parser.add_argument("--tracker-only", action="store_true",
                      help="Run only the brand tracker without the dashboard")
    
    return parser.parse_args()

def main():
    """Main function to run the integrated brand tracker and dashboard."""
    # Parse command line arguments
    args = parse_args()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create results directory
    create_results_dir()
    
    brand_tracker_process = None
    dashboard_process = None
    
    try:
        # Start brand tracker if not dashboard-only
        if not args.dashboard_only:
            brand_tracker_process = run_brand_tracker(
                brand_name=args.brand,
                non_interactive=True,
                runtime=args.runtime
            )
        
        # Start dashboard if not tracker-only
        if not args.tracker_only:
            dashboard_process = run_dashboard()
        
        # Print information about what's running
        if brand_tracker_process and dashboard_process:
            logger.info(f"Both brand tracker (PID: {brand_tracker_process.pid}) and dashboard (PID: {dashboard_process.pid}) are running")
            logger.info(f"Brand being tracked: {args.brand}")
            if args.runtime:
                logger.info(f"Brand tracker will run for {args.runtime} minutes")
            logger.info("Press Ctrl+C to stop both applications")
        elif brand_tracker_process:
            logger.info(f"Only brand tracker is running (PID: {brand_tracker_process.pid})")
            logger.info(f"Brand being tracked: {args.brand}")
            if args.runtime:
                logger.info(f"Brand tracker will run for {args.runtime} minutes")
            logger.info("Press Ctrl+C to stop")
        elif dashboard_process:
            logger.info(f"Only dashboard is running (PID: {dashboard_process.pid})")
            logger.info("Press Ctrl+C to stop")
        
        # Wait for processes to complete
        while True:
            if brand_tracker_process and brand_tracker_process.poll() is not None:
                logger.info(f"Brand tracker process exited with code {brand_tracker_process.returncode}")
                brand_tracker_process = None
            
            if dashboard_process and dashboard_process.poll() is not None:
                logger.info(f"Dashboard process exited with code {dashboard_process.returncode}")
                dashboard_process = None
            
            if not brand_tracker_process and not dashboard_process:
                logger.info("All processes have exited")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        signal_handler(signal.SIGTERM, None)

if __name__ == "__main__":
    main()
