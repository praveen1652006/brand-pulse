"""
Asynchronous data handler for brand tracker data updates.
This module provides functionality to asynchronously update the dashboard with brand tracker data.
"""
import json
import os
import time
import threading
import pandas as pd
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from queue import Queue

# Global event queue for brand tracker updates
event_queue = Queue()

class ResultsFileHandler(FileSystemEventHandler):
    """Watches for changes to the results.json file and triggers updates."""
    
    def __init__(self, results_file_path, callback):
        """Initialize the file handler with the file path and callback function."""
        self.results_file_path = results_file_path
        self.callback = callback
        self.last_modified_time = os.path.getmtime(results_file_path) if os.path.exists(results_file_path) else 0
    
    def on_modified(self, event):
        """Called when the results file is modified."""
        if not event.is_directory and event.src_path == self.results_file_path:
            current_time = os.path.getmtime(self.results_file_path)
            if current_time > self.last_modified_time:
                self.last_modified_time = current_time
                self.callback(self.results_file_path)

class AsyncDataHandler:
    """Handles asynchronous data updates from the brand tracker to the dashboard."""
    
    def __init__(self):
        """Initialize the async data handler."""
        self.observers = []
        self.sentiment_analyzer = None
        self.last_update_time = 0
        self.update_interval = 10  # seconds
        self.running = False
        self.thread = None
        
        # Initialize paths
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.potential_paths = [
            os.path.join(self.script_dir, '..', 'brand_tracker', 'results.json'),
            os.path.join(self.script_dir, '..', 'results', 'results.json'),
            os.path.join(self.script_dir, '..', '..', 'brand_tracker', 'results.json'),
            os.path.join(self.script_dir, '..', '..', 'results.json')
        ]
        self.data_lock = threading.Lock()
        
        # Latest data cache
        self.latest_data = {}
        self.latest_mentions = []
    
    def start(self, sentiment_analyzer=None):
        """Start the async data handler."""
        if self.running:
            return
        
        self.sentiment_analyzer = sentiment_analyzer
        self.running = True
        
        # Set up file observers for all potential paths
        for path in self.potential_paths:
            abs_path = os.path.abspath(path)
            directory = os.path.dirname(abs_path)
            
            if os.path.exists(directory):
                event_handler = ResultsFileHandler(abs_path, self.on_results_updated)
                observer = Observer()
                observer.schedule(event_handler, directory, recursive=False)
                observer.start()
                self.observers.append(observer)
                print(f"Watching for changes to {abs_path}")
        
        # Start background thread for processing events
        self.thread = threading.Thread(target=self._process_events, daemon=True)
        self.thread.start()
        
        # Initial data load
        self.load_initial_data()
        
        print("Async data handler started")
    
    def stop(self):
        """Stop the async data handler."""
        self.running = False
        
        # Stop all observers
        for observer in self.observers:
            observer.stop()
        
        # Wait for observers to finish
        for observer in self.observers:
            observer.join()
        
        print("Async data handler stopped")
    
    def on_results_updated(self, file_path):
        """Called when the results file is updated."""
        # Add to event queue to be processed in the background thread
        event_queue.put(("file_update", file_path))
    
    def _process_events(self):
        """Background thread to process events from the queue."""
        while self.running:
            try:
                # Get event from queue with a timeout to allow checking running flag
                try:
                    event_type, data = event_queue.get(timeout=1)
                except:
                    continue
                
                if event_type == "file_update":
                    self._process_file_update(data)
                
                # Mark the task as done
                event_queue.task_done()
            except Exception as e:
                print(f"Error processing event: {e}")
    
    def _process_file_update(self, file_path):
        """Process a file update event."""
        try:
            # Check if enough time has passed since the last update
            current_time = time.time()
            if current_time - self.last_update_time < self.update_interval:
                return
            
            self.last_update_time = current_time
            
            # Load the updated data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process the data
            with self.data_lock:
                # Extract relevant metrics from data
                mentions = data if isinstance(data, list) else data.get('posts', [])
                
                # Update latest mentions
                self.latest_mentions = mentions
                
                # If we have a sentiment analyzer, trigger an analysis
                if self.sentiment_analyzer:
                    # Trigger sentiment analysis in the background
                    threading.Thread(target=self.sentiment_analyzer.analyze_sentiment, daemon=True).start()
                
                # Extract summary metrics
                total_mentions = len(mentions)
                
                # Count by platform
                platform_counts = {}
                for mention in mentions:
                    platform = mention.get('platform', 'unknown')
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                # Count by sentiment
                sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
                for mention in mentions:
                    # Get sentiment from brand_tracker field
                    brand_tracker = mention.get('brand_tracker', {})
                    sentiment_data = brand_tracker.get('sentiment', {})
                    
                    # Handle different sentiment formats
                    if isinstance(sentiment_data, dict):
                        sentiment = sentiment_data.get('category', 'neutral').lower()
                    elif isinstance(sentiment_data, str):
                        sentiment = sentiment_data.lower()
                    else:
                        sentiment = 'neutral'
                    
                    if sentiment == 'positive':
                        sentiment_counts['positive'] += 1
                    elif sentiment == 'negative':
                        sentiment_counts['negative'] += 1
                    else:
                        sentiment_counts['neutral'] += 1
                
                # Count by brand
                brand_counts = {}
                for mention in mentions:
                    brand = mention.get('brand', 'unknown')
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1
                
                # Extract most recent mentions by platform
                recent_by_platform = {}
                for platform in platform_counts.keys():
                    platform_mentions = [m for m in mentions if m.get('platform') == platform]
                    sorted_mentions = sorted(
                        platform_mentions, 
                        key=lambda x: x.get('timestamp', ''), 
                        reverse=True
                    )
                    recent_by_platform[platform] = sorted_mentions[:5]  # Top 5 most recent
                
                # Update the latest data
                self.latest_data = {
                    'total_mentions': total_mentions,
                    'platform_counts': platform_counts,
                    'brand_counts': brand_counts,
                    'sentiment_counts': sentiment_counts,
                    'recent_by_platform': recent_by_platform,
                    'last_update': datetime.now().isoformat()
                }
                
                print(f"Processed {total_mentions} mentions from {file_path}")
        except Exception as e:
            print(f"Error processing file update: {e}")
    
    def load_initial_data(self):
        """Load initial data from all potential paths."""
        for path in self.potential_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                self.on_results_updated(abs_path)
                return
    
    def get_latest_data(self):
        """Get the latest data."""
        with self.data_lock:
            return self.latest_data.copy()
    
    def get_latest_mentions(self, limit=50):
        """Get the latest mentions."""
        with self.data_lock:
            # Sort by timestamp if available
            sorted_mentions = sorted(
                self.latest_mentions, 
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )
            return sorted_mentions[:limit]

# Singleton instance
async_data_handler = AsyncDataHandler()

def get_handler():
    """Get the singleton instance of the async data handler."""
    return async_data_handler
