import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
import threading
from async_data_handler import get_handler

# Initialize session state for real-time updates
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = time.time()

if 'update_interval' not in st.session_state:
    st.session_state.update_interval = 10  # seconds

def render_real_time_feed_page():
    """
    Renders the real-time feed page in the Streamlit dashboard.
    This function displays the most recent brand mentions collected by the Brand Tracker.
    Uses async data handler to automatically update when new data is available.
    """
    st.subheader("🔴 Live Brand Mentions Feed")
    
    st.markdown("""
    This feed shows the most recent brand mentions collected by the Brand Tracker.
    The data is automatically updated when new mentions are detected.
    """)
    
    # Get the async data handler
    data_handler = get_handler()
    
    # Add a refresh button
    if st.button("🔄 Refresh Feed"):
        st.rerun()
    
    # Get latest data summary
    latest_data = data_handler.get_latest_data()
    
    # Check if we have data
    if not latest_data or 'total_mentions' not in latest_data or latest_data['total_mentions'] == 0:
        # Try to load initial data if not already loaded
        if not data_handler.latest_mentions:
            # Path to the results JSON file (fallback)
            results_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     "brand_tracker", "results.json")
            
            if os.path.exists(results_path):
                data_handler.on_results_updated(results_path)
                latest_data = data_handler.get_latest_data()
            
        # If still no data, show warning
        if not latest_data or 'total_mentions' not in latest_data or latest_data['total_mentions'] == 0:
            st.warning("No brand mentions found. Please run the Brand Tracker first.")
            return
    
    try:
        # Display total mentions
        st.write(f"Total brand mentions: **{latest_data.get('total_mentions', 0)}**")
        
        # Display last update time
        last_update_time = latest_data.get('last_update', '')
        if last_update_time:
            try:
                date_obj = datetime.fromisoformat(last_update_time)
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                st.caption(f"Last updated: {formatted_date}")
            except:
                st.caption(f"Last updated: {last_update_time}")
        
        # Display platform breakdown
        platform_counts = latest_data.get('platform_counts', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            twitter_count = platform_counts.get('twitter', 0)
            st.metric("Twitter", twitter_count)
        
        with col2:
            reddit_count = platform_counts.get('reddit', 0)
            st.metric("Reddit", reddit_count)
        
        with col3:
            news_count = platform_counts.get('news', 0)
            st.metric("News", news_count)
        
        with col4:
            amazon_count = platform_counts.get('amazon', 0)
            st.metric("Amazon", amazon_count)
        
        # Display the mentions feed
        st.subheader("Latest Brand Mentions")
        
        # Get latest mentions
        latest_mentions = data_handler.get_latest_mentions(limit=50)
        
        if not latest_mentions:
            st.info("No brand mentions available yet. Waiting for data...")
            return
        
        # Process mentions
        for item in latest_mentions:
            # Extract timestamp
            timestamp = item.get('timestamp', '')
            
            # Format date if available
            try:
                date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_date = timestamp
            
            # Extract sentiment
            brand_tracker = item.get('brand_tracker', {})
            sentiment_data = brand_tracker.get('sentiment', {})
            
            # Handle different sentiment formats
            if isinstance(sentiment_data, dict):
                sentiment = sentiment_data.get('category', 'neutral').lower()
            elif isinstance(sentiment_data, str):
                sentiment = sentiment_data.lower()
            else:
                sentiment = 'neutral'
            
            # Extract content
            content = item.get('content', '')
            short_content = content[:200] + ('...' if len(content) > 200 else '')
            
            # Get platform-specific information
            platform = item.get('platform', 'Unknown')
            platform_info = ""
            
            if platform == 'twitter':
                user = item.get('user', '')
                platform_info = f"@{user}" if user else ""
            elif platform == 'reddit':
                subreddit = item.get('subreddit', '')
                platform_info = f"r/{subreddit}" if subreddit else ""
            elif platform == 'news':
                source = item.get('source', '')
                platform_info = f"Source: {source}" if source else ""
            elif platform == 'amazon':
                product = item.get('product', {})
                product_name = product.get('name', '')
                rating = product.get('rating', 0)
                platform_info = f"Product: {product_name} | Rating: {rating}/5" if product_name else ""
            
            with st.container():
                # Create a box with the mention
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    platform_display = platform.capitalize()
                    brand_display = item.get('brand', 'Unknown')
                    
                    st.markdown(f"**Platform:** {platform_display} | **Brand:** {brand_display} | **Time:** {formatted_date}")
                    if platform_info:
                        st.caption(platform_info)
                    st.markdown(short_content)
                
                with col2:
                    # Display sentiment emoji
                    if sentiment == 'positive':
                        st.markdown("### 😊")
                    elif sentiment == 'negative':
                        st.markdown("### ☹️")
                    elif sentiment == 'neutral':
                        st.markdown("### 😐")
                    else:
                        st.markdown("### ❓")
                
                # Add expand option for full content
                with st.expander("Show full content"):
                    st.write(content)
                    
                    # Show additional info based on platform
                    if platform == 'twitter':
                        engagement = item.get('engagement', {})
                        likes = engagement.get('likes', 0)
                        shares = engagement.get('shares', 0)
                        comments = engagement.get('comments', 0)
                        st.caption(f"Likes: {likes} | Retweets: {shares} | Replies: {comments}")
                    elif platform == 'reddit':
                        engagement = item.get('engagement', {})
                        likes = engagement.get('likes', 0)
                        comments = engagement.get('comments', 0)
                        st.caption(f"Upvotes: {likes} | Comments: {comments}")
                        if item.get('url'):
                            st.caption(f"Link: {item.get('url')}")
                    elif platform == 'news':
                        if item.get('url'):
                            st.caption(f"Article: {item.get('url')}")
                    elif platform == 'amazon':
                        engagement = item.get('engagement', {})
                        helpful_votes = engagement.get('helpful_votes', 0)
                        verified = item.get('product', {}).get('verified_purchase', False)
                        verified_text = "✓ Verified Purchase" if verified else "Not Verified"
                        st.caption(f"Helpful votes: {helpful_votes} | {verified_text}")
            
            # Add a divider
            st.markdown("---")
        
        # Create a placeholder for auto-refresh
        placeholder = st.empty()
        
        # Schedule next update using streamlit's auto-refresh
        current_time = time.time()
        time_since_last_update = current_time - st.session_state.last_update_time
        
        if time_since_last_update >= st.session_state.update_interval:
            st.session_state.last_update_time = current_time
            time.sleep(0.1)  # Small delay
            st.rerun()
            
    except Exception as e:
        st.error(f"Error displaying real-time feed: {e}")
        return
