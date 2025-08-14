import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from datetime import datetime
import numpy as np
# Import real-time feed module
from real_time_feed import render_real_time_feed_page
# Import async data handler
from async_data_handler import get_handler
# Import sentiment analyzer for async updates
from sentiment_analysis import SentimentAnalyzer

# Set page configuration
st.set_page_config(
    page_title="Brand Pulse - Sentiment Analysis",
    page_icon="📊",
    layout="wide"
)

# Initialize the async data handler
# Only initialize once to avoid multiple watchers
if 'async_handler_initialized' not in st.session_state:
    st.session_state.async_handler_initialized = True
    # Initialize the sentiment analyzer
    sentiment_analyzer = SentimentAnalyzer()
    # Get the async data handler and start it
    async_data_handler = get_handler()
    async_data_handler.start(sentiment_analyzer=sentiment_analyzer)
    st.info("Asynchronous data updates enabled. Dashboard will refresh automatically when new data is available.")

# Title and description
st.title("📊 Brand Pulse - Sentiment Analysis Dashboard")
st.markdown("""
This dashboard provides insights into brand sentiment analysis across social media platforms and reviews.
""")

# Find the most recent sentiment analysis results
results_dir = "sentiment_results"
if not os.path.exists(results_dir):
    st.error("No sentiment analysis results found. Please run the sentiment analyzer first.")
    st.stop()

# Find the latest sentiment and product sentiment files
sentiment_files = glob.glob(os.path.join(results_dir, "sentiment_results_*.csv"))
product_files = glob.glob(os.path.join(results_dir, "product_sentiment_*.csv"))

if not sentiment_files or not product_files:
    st.error("Sentiment analysis result files not found. Please run the sentiment analyzer first.")
    st.stop()

# Sort by date and get the latest
latest_sentiment_file = sorted(sentiment_files)[-1]
latest_product_file = sorted(product_files)[-1]

# Load data
try:
    df_sentiment = pd.read_csv(latest_sentiment_file)
    df_products = pd.read_csv(latest_product_file)
    
    # Get the timestamp from the filename
    timestamp = os.path.basename(latest_sentiment_file).replace("sentiment_results_", "").replace(".csv", "")
    date_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
    formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
    
    st.info(f"Showing analysis from: {formatted_date}")
except Exception as e:
    st.error(f"Error loading sentiment analysis results: {e}")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Brand Analysis", "Mention Explorer", "Live Feed", "Raw Data"])

# Tab 1: Overview
with tab1:
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Overall sentiment counts
        sentiment_counts = df_sentiment['sentiment'].value_counts()
        total_reviews = len(df_sentiment)
        
        st.subheader("Overall Brand Sentiment Distribution")
        st.write(f"Total Mentions Analyzed: **{total_reviews}**")
        
        # Calculate percentages
        sentiment_pct = (sentiment_counts / total_reviews * 100).round(1)
        
        # Show percentages in a nice format
        col_a, col_b, col_c = st.columns(3)
        
        positive_pct = sentiment_pct.get('positive', 0)
        negative_pct = sentiment_pct.get('negative', 0)
        neutral_pct = sentiment_pct.get('neutral', 0)
        
        col_a.metric(
            "Positive", 
            f"{positive_pct}%", 
            f"{sentiment_counts.get('positive', 0)} reviews"
        )
        
        col_b.metric(
            "Negative", 
            f"{negative_pct}%", 
            f"{sentiment_counts.get('negative', 0)} reviews"
        )
        
        col_c.metric(
            "Neutral", 
            f"{neutral_pct}%", 
            f"{sentiment_counts.get('neutral', 0)} reviews"
        )

    with col2:
        # Pie chart visualization
        st.subheader("Sentiment Visualization")
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['#5cb85c', '#d9534f', '#5bc0de']  # green, red, blue
        
        # Get sentiment counts
        positive_count = sentiment_counts.get('positive', 0)
        negative_count = sentiment_counts.get('negative', 0)
        neutral_count = sentiment_counts.get('neutral', 0)
        
        # Labels with percentages
        labels = [
            f'Positive ({positive_pct:.1f}%)',
            f'Negative ({negative_pct:.1f}%)',
            f'Neutral ({neutral_pct:.1f}%)'
        ]
        
        # Values
        values = [positive_count, negative_count, neutral_count]
        
        # Create pie chart
        plt.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
            explode=(0.05, 0.05, 0.05)
        )
        plt.axis('equal')
        st.pyplot(fig)
    
    # Word frequency analysis
    st.subheader("Most Common Words in Brand Mentions")
    
    # Simple word frequency analysis
    import re
    from collections import Counter
    import nltk
    from nltk.corpus import stopwords
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    
    stop_words = set(stopwords.words('english'))
    
    def extract_words(text):
        if not isinstance(text, str):
            return []
        words = re.findall(r'\b[a-zA-Z]{3,15}\b', text.lower())
        return [w for w in words if w not in stop_words]
    
    # Add tabs for positive and negative word clouds
    word_tab1, word_tab2 = st.tabs(["Positive Words", "Negative Words"])
    
    with word_tab1:
        # Get text from positive reviews
        positive_reviews = df_sentiment[df_sentiment['sentiment'] == 'positive']['review_content'].fillna('')
        positive_words = []
        for review in positive_reviews:
            positive_words.extend(extract_words(review))
        
        positive_word_counts = Counter(positive_words).most_common(20)
        pos_words, pos_counts = zip(*positive_word_counts) if positive_word_counts else ([], [])
        
        # Create bar chart for positive words
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=list(pos_counts), y=list(pos_words), palette='Greens_d')
        plt.title("Top 20 Words in Positive Reviews")
        plt.xlabel("Count")
        plt.tight_layout()
        st.pyplot(fig)
    
    with word_tab2:
        # Get text from negative reviews
        negative_reviews = df_sentiment[df_sentiment['sentiment'] == 'negative']['review_content'].fillna('')
        negative_words = []
        for review in negative_reviews:
            negative_words.extend(extract_words(review))
        
        negative_word_counts = Counter(negative_words).most_common(20)
        neg_words, neg_counts = zip(*negative_word_counts) if negative_word_counts else ([], [])
        
        # Create bar chart for negative words
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=list(neg_counts), y=list(neg_words), palette='Reds_d')
        plt.title("Top 20 Words in Negative Reviews")
        plt.xlabel("Count")
        plt.tight_layout()
        st.pyplot(fig)

# Tab 2: Product Analysis
with tab2:
    st.subheader("Brand Sentiment Analysis")
    
    # Filter products with at least 2 reviews
    df_products_filtered = df_products[df_products['review_count'] >= 2].copy()
    
    # Sort options
    sort_options = {
        "Most Positive": "sentiment_score",
        "Most Negative": "sentiment_score (asc)",
        "Most Mentions": "review_count",
        "Highest Rating": "rating"
    }
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Sorting options
        sort_by = st.selectbox(
            "Sort products by:",
            options=list(sort_options.keys())
        )
        
        # Category filter - if category info is available
        if 'category' in df_sentiment.columns:
            categories = ['All'] + sorted(df_sentiment['category'].dropna().unique().tolist())
            selected_category = st.selectbox("Filter by category:", categories)
        
        # Min reviews filter
        max_review_value = int(max(df_products['review_count'])) if not df_products.empty else 10
        min_reviews = st.slider("Minimum number of reviews:", 1, max_review_value, 2)
        
        # Apply filters
        df_filtered = df_products[df_products['review_count'] >= min_reviews].copy()
        
        # Sort the products
        if sort_by == "Most Positive":
            df_filtered = df_filtered.sort_values('sentiment_score', ascending=False)
        elif sort_by == "Most Negative":
            df_filtered = df_filtered.sort_values('sentiment_score', ascending=True)
        elif sort_by == "Most Reviews":
            df_filtered = df_filtered.sort_values('review_count', ascending=False)
        elif sort_by == "Highest Rating":
            df_filtered = df_filtered.sort_values('rating', ascending=False)
    
    with col2:
        # Show filtered products in a table
        if not df_filtered.empty:
            # Create a formatted table
            table_data = []
            
            for idx, row in df_filtered.iterrows():
                product_name = row['product_name']
                if len(product_name) > 50:
                    product_name = product_name[:50] + "..."
                
                # Format percentages
                pos_pct = row.get('positive_pct', 0)
                neg_pct = row.get('negative_pct', 0)
                neu_pct = row.get('neutral_pct', 0)
                
                table_data.append({
                    "Product": product_name,
                    "Sentiment": f"😊 {pos_pct:.1f}% | 😐 {neu_pct:.1f}% | ☹️ {neg_pct:.1f}%",
                    "Rating": f"{row['rating']:.1f}/5",
                    "Reviews": int(row['review_count'])
                })
            
            # Display as DataFrame
            st.dataframe(pd.DataFrame(table_data), height=400)
        else:
            st.info("No products match the selected filters.")
    
    # Visualizations
    st.subheader("Product Sentiment Visualizations")
    
    # Only proceed if we have enough data
    if len(df_filtered) > 0:
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Product Sentiment", "Rating vs. Sentiment", "All Products"])
        
        with viz_tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Set number of products to display
                num_products = len(df_filtered)
                if num_products <= 1:
                    st.info("Not enough products to display. Need at least 2 products.")
                    st.stop()
                    
                # Make sure min_value is less than max_value
                min_slider_val = min(5, max(1, num_products-1))
                max_slider_val = max(min_slider_val+1, min(50, num_products))
                default_val = min(20, max(min_slider_val, num_products))
                
                num_products_slider = st.slider("Number of products to display:", 
                                              min_value=min_slider_val, 
                                              max_value=max_slider_val, 
                                              value=default_val)
                
                # Positive products visualization
                top_n = min(num_products_slider, len(df_filtered))
                top_positive = df_filtered.sort_values('positive_pct', ascending=False).head(top_n)
                
                if not top_positive.empty:
                    fig, ax = plt.subplots(figsize=(10, 8))
                    
                    # Create shortened product names
                    top_positive['short_name'] = top_positive['product_name'].apply(
                        lambda x: x[:30] + '...' if len(x) > 30 else x
                    )
                    
                    # Create horizontal bar chart
                    sns.barplot(
                        y='short_name',
                        x='positive_pct',
                        data=top_positive.iloc[::-1],  # Reverse for better viewing
                        color='#5cb85c'
                    )
                    
                    plt.title(f'Top {top_n} Products by Positive Sentiment')
                    plt.xlabel('Positive Reviews (%)')
                    plt.ylabel('Product')
                    plt.tight_layout()
                    st.pyplot(fig)
            
            with col2:
                st.write(" ")  # Space to align with slider
                st.write(" ")  # Space to align with slider
                
                # Negative products visualization
                top_negative = df_filtered.sort_values('negative_pct', ascending=False).head(top_n)
                
                if not top_negative.empty:
                    fig, ax = plt.subplots(figsize=(10, 8))
                    
                    # Create shortened product names
                    top_negative['short_name'] = top_negative['product_name'].apply(
                        lambda x: x[:30] + '...' if len(x) > 30 else x
                    )
                    
                    # Create horizontal bar chart
                    sns.barplot(
                        y='short_name',
                        x='negative_pct',
                        data=top_negative.iloc[::-1],  # Reverse for better viewing
                        color='#d9534f'
                    )
                    
                    plt.title(f'Top {top_n} Products by Negative Sentiment')
                    plt.xlabel('Negative Reviews (%)')
                    plt.ylabel('Product')
                    plt.tight_layout()
                    st.pyplot(fig)
        
        with viz_tab2:
            # Scatter plot of rating vs sentiment
            if len(df_filtered) >= 5:  # Only show if we have enough data
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Add number of reviews to size of points
                sizes = df_filtered['review_count'] * 20
                
                # Create scatter plot
                scatter = plt.scatter(
                    df_filtered['rating'], 
                    df_filtered['sentiment_score'],
                    s=sizes,
                    alpha=0.6,
                    c=df_filtered['sentiment_score'],
                    cmap='RdYlGn'
                )
                
                # Add trend line if we have enough data
                if len(df_filtered) >= 5:
                    x = df_filtered['rating'].values
                    y = df_filtered['sentiment_score'].values
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    plt.plot(x, p(x), "r--", alpha=0.8)
                
                # Add labels and title
                plt.title('Product Rating vs. Sentiment Score')
                plt.xlabel('Average Product Rating')
                plt.ylabel('Sentiment Score (-1 to 1)')
                
                # Add colorbar legend
                cbar = plt.colorbar(scatter)
                cbar.set_label('Sentiment Score')
                
                # Add grid lines
                plt.grid(True, alpha=0.3)
                
                st.pyplot(fig)
            else:
                st.info("Not enough data for meaningful visualization. Need at least 5 products.")
                
        with viz_tab3:
            # Show all products in a comprehensive view
            st.subheader("All Products Overview")
            
            # Get summary statistics
            total_products = len(df_filtered)
            pos_majority = sum(1 for _, row in df_filtered.iterrows() if row['positive_pct'] > max(row['negative_pct'], row['neutral_pct']))
            neg_majority = sum(1 for _, row in df_filtered.iterrows() if row['negative_pct'] > max(row['positive_pct'], row['neutral_pct']))
            neu_majority = sum(1 for _, row in df_filtered.iterrows() if row['neutral_pct'] > max(row['positive_pct'], row['negative_pct']))
            
            # Display summary stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Products with Positive Sentiment", 
                      f"{pos_majority} ({pos_majority/total_products*100:.1f}%)")
            col2.metric("Products with Negative Sentiment", 
                      f"{neg_majority} ({neg_majority/total_products*100:.1f}%)")
            col3.metric("Products with Neutral Sentiment", 
                      f"{neu_majority} ({neu_majority/total_products*100:.1f}%)")
            
            # Display review count distribution
            st.subheader("Review Count Distribution")
            review_counts = df_filtered['review_count'].value_counts().sort_index()
            single_review = review_counts.get(1, 0)
            few_reviews = sum(review_counts.get(i, 0) for i in range(2, 6))
            many_reviews = sum(review_counts.get(i, 0) for i in range(6, 100))
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Products with 1 Review", f"{single_review} ({single_review/total_products*100:.1f}%)")
            col2.metric("Products with 2-5 Reviews", f"{few_reviews} ({few_reviews/total_products*100:.1f}%)")
            col3.metric("Products with 6+ Reviews", f"{many_reviews} ({many_reviews/total_products*100:.1f}%)")
            
            # Create a heatmap of all products sorted by sentiment score
            if len(df_filtered) > 0:
                st.subheader("All Products Sentiment Heatmap")
                
                # Allow user to choose how many products to display
                max_display = min(100, len(df_filtered))
                if max_display < 10:
                    st.info("Not enough products to display in heatmap. Need at least 10 products.")
                    st.stop()
                
                # Make sure min_value is less than max_value
                min_slider_val = min(10, max(2, max_display-1))
                max_slider_val = max(min_slider_val+1, max_display)
                default_val = min(50, max(min_slider_val, max_display))
                
                display_count = st.slider("Number of products to display in heatmap:", 
                                        min_value=min_slider_val, 
                                        max_value=max_slider_val, 
                                        value=default_val)
                
                # Sort option for heatmap
                sort_options = ["By Positive %", "By Negative %", "By Review Count", "By Rating"]
                selected_sort = st.radio("Sort products by:", sort_options, horizontal=True)
                
                if selected_sort == "By Positive %":
                    sorted_df = df_filtered.sort_values('positive_pct', ascending=False).head(display_count)
                elif selected_sort == "By Negative %":
                    sorted_df = df_filtered.sort_values('negative_pct', ascending=False).head(display_count)
                elif selected_sort == "By Review Count":
                    sorted_df = df_filtered.sort_values('review_count', ascending=False).head(display_count)
                else:  # By Rating
                    sorted_df = df_filtered.sort_values('rating', ascending=False).head(display_count)
                
                # Create heatmap data
                heatmap_data = sorted_df[['positive_pct', 'neutral_pct', 'negative_pct']].copy()
                
                # Create short product names for y-axis
                sorted_df['short_name'] = sorted_df['product_name'].apply(
                    lambda x: x[:40] + '...' if len(x) > 40 else x
                )
                
                # Create heatmap
                fig, ax = plt.subplots(figsize=(10, max(10, display_count * 0.3)))
                
                # Add review count to product names
                y_labels = [f"{name} ({sorted_df['review_count'].iloc[i]:.0f})" 
                           for i, name in enumerate(sorted_df['short_name'])]
                
                # Create the heatmap
                sns.heatmap(
                    heatmap_data,
                    annot=True,
                    fmt='.1f',
                    cmap='RdYlGn',
                    linewidths=0.5,
                    yticklabels=y_labels,
                    xticklabels=['Positive %', 'Neutral %', 'Negative %'],
                    ax=ax
                )
                
                plt.title(f"Sentiment Distribution for {display_count} Products")
                plt.tight_layout()
                st.pyplot(fig)

# Tab 3: Review Explorer
with tab3:
    st.subheader("Explore Individual Brand Mentions")
    
    # Product selection
    products = ["All Brands"] + sorted(df_sentiment['product_name'].unique().tolist())
    selected_product = st.selectbox("Select a brand:", products)
    
    # Filter reviews
    if selected_product == "All Brands":
        filtered_reviews = df_sentiment
    else:
        filtered_reviews = df_sentiment[df_sentiment['product_name'] == selected_product]
    
    # Sentiment filter
    sentiment_filter = st.multiselect(
        "Filter by sentiment:",
        options=['positive', 'negative', 'neutral'],
        default=['positive', 'negative', 'neutral']
    )
    
    filtered_reviews = filtered_reviews[filtered_reviews['sentiment'].isin(sentiment_filter)]
    
    # Sort options
    sort_options = ["Most Positive", "Most Negative", "Highest Rating", "Lowest Rating"]
    sort_selection = st.selectbox("Sort reviews by:", sort_options)
    
    if sort_selection == "Most Positive":
        filtered_reviews = filtered_reviews.sort_values('compound_score', ascending=False)
    elif sort_selection == "Most Negative":
        filtered_reviews = filtered_reviews.sort_values('compound_score', ascending=True)
    elif sort_selection == "Highest Rating":
        filtered_reviews = filtered_reviews.sort_values('rating', ascending=False)
    elif sort_selection == "Lowest Rating":
        filtered_reviews = filtered_reviews.sort_values('rating', ascending=True)
    
    # Display reviews
    if not filtered_reviews.empty:
        st.write(f"Showing {len(filtered_reviews)} reviews")
        
        for i, (idx, review) in enumerate(filtered_reviews.iterrows()):
            # Create a card-like container for each review
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Show the product name if we're looking at all products
                    if selected_product == "All Products":
                        product_name = review['product_name']
                        st.markdown(f"**Product:** {product_name}")
                    
                    # Review title if available
                    if 'review_title' in review and not pd.isna(review['review_title']):
                        st.markdown(f"**Title:** {review['review_title']}")
                    
                    # Review text
                    review_text = review['review_content']
                    st.markdown(f"{review_text}")
                    
                    # User name if available
                    if 'user_name' in review and not pd.isna(review['user_name']):
                        st.caption(f"By: {review['user_name']}")
                
                with col2:
                    # Sentiment emoji
                    sentiment = review['sentiment']
                    if sentiment == 'positive':
                        st.markdown("### 😊")
                    elif sentiment == 'negative':
                        st.markdown("### ☹️")
                    else:
                        st.markdown("### 😐")
                    
                    # Rating if available
                    if 'rating' in review and not pd.isna(review['rating']):
                        st.markdown(f"**Rating:** {review['rating']}/5")
                    
                    # Sentiment scores
                    pos = review['positive_score']
                    neg = review['negative_score']
                    neu = review['neutral_score']
                    
                    st.caption(f"Pos: {pos:.2f}, Neg: {neg:.2f}, Neu: {neu:.2f}")
            
            # Add a divider between reviews
            st.markdown("---")
            
            # Limit the number of reviews shown to prevent overwhelming the UI
            if i >= 19:  # Show max 20 reviews
                st.info(f"Showing 20 of {len(filtered_reviews)} reviews. Please apply filters to see more specific reviews.")
                break

# Tab 4: Raw Data
with tab4:
    st.subheader("Raw Data")
    
    # Create tabs for different data views
    data_tab1, data_tab2 = st.tabs(["Review Data", "Product Summary Data"])
    
    with data_tab1:
        st.write("Complete sentiment analysis results for all reviews:")
        st.dataframe(df_sentiment)
        
        # Download button
        csv = df_sentiment.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Complete Results CSV",
            csv,
            "amazon_reviews_sentiment.csv",
            "text/csv",
            key='download-csv'
        )
    
    with data_tab2:
        st.write("Product summary data:")
        st.dataframe(df_products)
        
        # Download button
        product_csv = df_products.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Product Summary CSV",
            product_csv,
            "amazon_products_sentiment.csv",
            "text/csv",
            key='download-products-csv'
        )

# Tab 4: Live Feed
with tab4:
    # Render real-time feed
    render_real_time_feed_page()

# Footer
st.markdown("---")
st.caption("Brand Pulse Sentiment Analysis Dashboard | Created for Brand Guardian")
