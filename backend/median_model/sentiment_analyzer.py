import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import string
from datetime import datetime
import os

# Ensure necessary NLTK packages are downloaded
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    print("Downloading NLTK Vader lexicon...")
    nltk.download('vader_lexicon')
    
# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

def load_csv(file_path):
    """
    Load the CSV file containing brand mentions
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None

def filter_records(df):
    """
    Filter records based on various criteria
    - Remove duplicates
    - Remove records with empty content
    - Remove spam/bot entries (if identifiable)
    """
    original_len = len(df)
    
    # In the Amazon dataset, the review_content column contains the text to analyze
    if 'review_content' in df.columns:
        # Remove duplicates based on review content
        df = df.drop_duplicates(subset=['review_content'])
        
        # Remove records with empty review content
        df = df[df['review_content'].notna() & (df['review_content'] != "")]
        
        # Filter out very short reviews (likely not useful for analysis)
        df['text_length'] = df['review_content'].astype(str).apply(len)
        df = df[df['text_length'] > 5]  # Filter out very short content
        df = df.drop(columns=['text_length'])
    else:
        # Fallback to generic content columns
        # Remove duplicates based on content
        for content_col in ['content', 'text', 'review', 'comment']:
            if content_col in df.columns:
                df = df.drop_duplicates(subset=[content_col])
                break
        
        # Remove records with empty content
        for col in ['content', 'text', 'review', 'comment']:
            if col in df.columns:
                df = df[df[col].notna() & (df[col] != "")]
        
        # Filter out very short content (likely not useful for analysis)
        text_columns = [col for col in ['content', 'text', 'review', 'comment'] if col in df.columns]
        if text_columns:
            df['text_length'] = df[text_columns[0]].astype(str).apply(len)
            df = df[df['text_length'] > 5]  # Filter out very short content
            df = df.drop(columns=['text_length'])
    
    print(f"Filtered out {original_len - len(df)} records, {len(df)} remaining")
    return df

def clean_text(text):
    """
    Clean text for better sentiment analysis
    - Remove URLs
    - Remove special characters
    - Remove extra spaces
    """
    if not isinstance(text, str):
        return ""
        
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Remove special characters but keep punctuation for sentiment analysis
    text = re.sub(r'[^\w\s\.\,\!\?\-\:]', '', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def analyze_sentiment(df):
    """
    Analyze sentiment for each record and add sentiment score columns
    """
    # For Amazon dataset, prioritize 'review_content' column
    if 'review_content' in df.columns:
        text_column = 'review_content'
        print(f"Analyzing sentiment from Amazon review column: '{text_column}'")
    else:
        # Fallback to other potential text columns
        text_columns = [col for col in ['content', 'text', 'review', 'comment'] if col in df.columns]
        
        if not text_columns:
            print("Error: Could not find text column to analyze")
            return df
            
        text_column = text_columns[0]
        print(f"Analyzing sentiment from column: '{text_column}'")
    
    # Clean the text
    df['clean_text'] = df[text_column].apply(clean_text)
    
    # Calculate sentiment scores
    sentiment_scores = df['clean_text'].apply(lambda x: sia.polarity_scores(x))
    
    # Extract individual scores
    df['compound_score'] = sentiment_scores.apply(lambda x: x['compound'])
    df['positive_score'] = sentiment_scores.apply(lambda x: x['pos'])
    df['negative_score'] = sentiment_scores.apply(lambda x: x['neg'])
    df['neutral_score'] = sentiment_scores.apply(lambda x: x['neu'])
    
    # Categorize sentiment based on compound score
    df['sentiment'] = df['compound_score'].apply(
        lambda score: 'positive' if score >= 0.05 else ('negative' if score <= -0.05 else 'neutral')
    )
    
    # For Amazon dataset, compare sentiment with the actual rating
    if 'rating' in df.columns and df['rating'].dtype != object:
        # Convert ratings to numeric if they aren't already
        if not pd.api.types.is_numeric_dtype(df['rating']):
            df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce')
        else:
            df['rating_numeric'] = df['rating']
            
        # Compare predicted sentiment with actual rating
        df['rating_sentiment'] = df['rating_numeric'].apply(
            lambda score: 'positive' if score >= 4 else ('negative' if score <= 2 else 'neutral')
        )
        
        # Calculate agreement between NLTK sentiment and rating-based sentiment
        agreement = (df['sentiment'] == df['rating_sentiment']).mean() * 100
        print(f"Sentiment-Rating Agreement: {agreement:.2f}%")
    
    return df

def generate_summary(df):
    """
    Generate summary statistics and visualizations
    """
    # Overall sentiment counts
    sentiment_counts = df['sentiment'].value_counts()
    total_records = len(df)
    
    # Calculate percentages
    sentiment_percentages = (sentiment_counts / total_records * 100).round(2)
    
    print("\n=== SENTIMENT ANALYSIS SUMMARY ===")
    print(f"Total records analyzed: {total_records}")
    print("\nSentiment Distribution:")
    for sentiment, percentage in sentiment_percentages.items():
        print(f"- {sentiment.capitalize()}: {percentage}% ({sentiment_counts[sentiment]} records)")
        
    # Create a results directory if it doesn't exist
    results_dir = "sentiment_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    # Save results to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"sentiment_results_{timestamp}.csv")
    df.to_csv(results_file, index=False)
    print(f"\nDetailed results saved to: {results_file}")
    
    # Create visualizations
    create_visualizations(df, sentiment_counts, sentiment_percentages, results_dir, timestamp)
    
    return sentiment_counts, sentiment_percentages

def product_sentiment_analysis(df):
    """
    Analyze sentiment by product to identify best and worst rated products
    """
    # Check if product_name column exists
    if 'product_name' not in df.columns:
        print("Product name column not found, skipping product-specific analysis")
        return
        
    # Group by product and calculate average sentiment
    df['sentiment_score'] = df['sentiment'].map({'positive': 1, 'neutral': 0, 'negative': -1})
    
    # Convert rating to numeric to avoid errors
    if 'rating' in df.columns:
        try:
            df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce')
        except:
            df['rating_numeric'] = None
    else:
        df['rating_numeric'] = None
    
    product_sentiment = df.groupby('product_name').agg({
        'sentiment_score': 'mean',
        'compound_score': 'mean',
        'sentiment': lambda x: x.value_counts().to_dict(),
        'product_id': 'first',  # Keep product_id for reference
        'rating_numeric': 'mean'  # Average product rating
    }).reset_index()
    
    # Rename back to rating for consistency
    product_sentiment = product_sentiment.rename(columns={'rating_numeric': 'rating'})
    
    # Calculate percentage of positive, negative, neutral reviews for each product
    for product_idx, row in product_sentiment.iterrows():
        sentiment_dict = row['sentiment']
        total = sum(sentiment_dict.values())
        
        # Initialize values to 0 if not present
        positive_pct = sentiment_dict.get('positive', 0) / total * 100 if total > 0 else 0
        negative_pct = sentiment_dict.get('negative', 0) / total * 100 if total > 0 else 0
        neutral_pct = sentiment_dict.get('neutral', 0) / total * 100 if total > 0 else 0
        
        product_sentiment.at[product_idx, 'positive_pct'] = round(positive_pct, 2)
        product_sentiment.at[product_idx, 'negative_pct'] = round(negative_pct, 2)
        product_sentiment.at[product_idx, 'neutral_pct'] = round(neutral_pct, 2)
        product_sentiment.at[product_idx, 'review_count'] = total
    
    # Sort by sentiment score
    product_sentiment_sorted = product_sentiment.sort_values('sentiment_score', ascending=False)
    
    # Save product sentiment results
    results_dir = "sentiment_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    product_results_file = os.path.join(results_dir, f"product_sentiment_{timestamp}.csv")
    
    # Select columns to save
    cols_to_save = ['product_id', 'product_name', 'sentiment_score', 'compound_score', 
                    'positive_pct', 'negative_pct', 'neutral_pct', 'review_count', 'rating']
    product_sentiment_sorted[cols_to_save].to_csv(product_results_file, index=False)
    
    # Print summary of all products instead of just top 5
    print(f"\n=== PRODUCT SENTIMENT SUMMARY (ALL {len(product_sentiment_sorted)} PRODUCTS) ===")
    print(f"Total products analyzed: {len(product_sentiment_sorted)}")
    
    # Get counts by sentiment majority
    positive_majority = sum(1 for _, row in product_sentiment_sorted.iterrows() if row['positive_pct'] > max(row['negative_pct'], row['neutral_pct']))
    negative_majority = sum(1 for _, row in product_sentiment_sorted.iterrows() if row['negative_pct'] > max(row['positive_pct'], row['neutral_pct']))
    neutral_majority = sum(1 for _, row in product_sentiment_sorted.iterrows() if row['neutral_pct'] > max(row['positive_pct'], row['negative_pct']))
    
    print(f"\nProducts with majority positive sentiment: {positive_majority} ({positive_majority/len(product_sentiment_sorted)*100:.1f}%)")
    print(f"Products with majority negative sentiment: {negative_majority} ({negative_majority/len(product_sentiment_sorted)*100:.1f}%)")
    print(f"Products with majority neutral sentiment: {neutral_majority} ({neutral_majority/len(product_sentiment_sorted)*100:.1f}%)")
    
    # Print products by review count
    products_by_reviews = product_sentiment_sorted.sort_values('review_count', ascending=False)
    print(f"\nTop 10 most reviewed products:")
    for i, (_, row) in enumerate(products_by_reviews.head(10).iterrows()):
        print(f"{i+1}. {row['product_name'][:50]}... ({row['review_count']} reviews)")
    
    # Print distribution of review counts
    review_counts = product_sentiment_sorted['review_count'].value_counts().sort_index()
    print(f"\nDistribution of review counts:")
    print(f"- Products with 1 review: {review_counts.get(1, 0)}")
    print(f"- Products with 2-5 reviews: {sum(review_counts.get(i, 0) for i in range(2, 6))}")
    print(f"- Products with 6+ reviews: {sum(review_counts.get(i, 0) for i in range(6, 100))}")
        
    # Create visualizations for product sentiment
    create_product_visualizations(product_sentiment_sorted, results_dir, timestamp)
    
    print(f"\nProduct sentiment analysis saved to: {product_results_file}")
    
    return product_sentiment_sorted

def create_visualizations(df, sentiment_counts, sentiment_percentages, results_dir, timestamp):
    """
    Create visualizations for sentiment analysis results
    """
    # Set up the style
    sns.set(style="whitegrid")
    
    # Create figure for pie chart
    plt.figure(figsize=(10, 6))
    colors = ['#5cb85c', '#d9534f', '#5bc0de']  # green, red, blue
    
    # Create pie chart
    plt.pie(
        sentiment_percentages, 
        labels=[f"{s.capitalize()} ({p}%)" for s, p in sentiment_percentages.items()],
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        shadow=True,
        explode=(0.05, 0.05, 0.05)
    )
    plt.axis('equal')
    plt.title('Overall Sentiment Distribution', fontsize=16)
    
    # Save pie chart
    pie_chart_file = os.path.join(results_dir, f"sentiment_pie_{timestamp}.png")
    plt.savefig(pie_chart_file)
    plt.close()
    
    # Create bar chart for sentiment counts
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x=sentiment_counts.index, y=sentiment_counts.values, palette=colors)
    
    # Add count labels on top of bars
    for i, count in enumerate(sentiment_counts.values):
        ax.text(i, count + 5, str(count), ha='center')
    
    plt.title('Sentiment Counts', fontsize=16)
    plt.xlabel('Sentiment', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    
    # Save bar chart
    bar_chart_file = os.path.join(results_dir, f"sentiment_bars_{timestamp}.png")
    plt.savefig(bar_chart_file)
    plt.close()
    
    print(f"Visualizations saved to {results_dir} directory")
    
def create_product_visualizations(product_df, results_dir, timestamp):
    """
    Create visualizations for product sentiment analysis
    """
    # Set up the style
    sns.set(style="whitegrid")
    
    # Filter to products with at least 2 reviews for better visualization
    products_with_reviews = product_df[product_df['review_count'] >= 2].copy()
    
    if len(products_with_reviews) == 0:
        print("Not enough products with multiple reviews for visualization")
        return
    
    # 1. Create horizontal bar chart comparing positive percentages for top 10 products
    plt.figure(figsize=(12, 8))
    
    # Sort by positive percentage and select top 10
    top_positive = products_with_reviews.sort_values('positive_pct', ascending=False).head(10).copy()
    
    # Create shortened product names for better display
    top_positive['short_name'] = top_positive['product_name'].apply(lambda x: x[:40] + '...' if len(x) > 40 else x)
    
    # Create horizontal bar chart
    ax = sns.barplot(x='positive_pct', y='short_name', data=top_positive, color='#5cb85c')
    
    # Add percentage labels
    for i, v in enumerate(top_positive['positive_pct']):
        ax.text(v + 1, i, f"{v}%", va='center')
    
    plt.title('Top 10 Products by Positive Sentiment', fontsize=16)
    plt.xlabel('Positive Reviews (%)', fontsize=12)
    plt.ylabel('Product', fontsize=12)
    plt.tight_layout()
    
    # Save chart
    positive_chart_file = os.path.join(results_dir, f"top_positive_products_{timestamp}.png")
    plt.savefig(positive_chart_file)
    plt.close()
    
    # 2. Create scatter plot comparing sentiment score vs product rating
    plt.figure(figsize=(12, 8))
    
    # Add number of reviews to size of points
    sizes = products_with_reviews['review_count'] * 20
    
    # Create scatter plot
    plt.scatter(
        products_with_reviews['rating'], 
        products_with_reviews['sentiment_score'],
        s=sizes,
        alpha=0.6,
        c=products_with_reviews['sentiment_score'],
        cmap='RdYlGn'
    )
    
    # Add trend line
    x = products_with_reviews['rating']
    y = products_with_reviews['sentiment_score']
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x, p(x), "r--", alpha=0.8)
    
    # Add labels and title
    plt.title('Product Rating vs. Sentiment Score', fontsize=16)
    plt.xlabel('Average Product Rating', fontsize=12)
    plt.ylabel('Sentiment Score (-1 to 1)', fontsize=12)
    
    # Add colorbar legend
    cbar = plt.colorbar()
    cbar.set_label('Sentiment Score')
    
    # Add grid lines
    plt.grid(True, alpha=0.3)
    
    # Save chart
    scatter_file = os.path.join(results_dir, f"rating_vs_sentiment_{timestamp}.png")
    plt.savefig(scatter_file)
    plt.close()
    
    # 3. Create stacked bar chart showing sentiment distribution for top products
    plt.figure(figsize=(12, 10))
    
    # Select top 10 products by review count
    top_reviewed = products_with_reviews.sort_values('review_count', ascending=False).head(10).copy()
    
    # Create shortened product names
    top_reviewed['short_name'] = top_reviewed['product_name'].apply(lambda x: x[:30] + '...' if len(x) > 30 else x)
    
    # Create data for stacked bar
    positive_data = top_reviewed['positive_pct']
    neutral_data = top_reviewed['neutral_pct']
    negative_data = top_reviewed['negative_pct']
    
    # Create stacked bar chart
    bar_width = 0.8
    bars = range(len(top_reviewed))
    
    plt.barh(bars, positive_data, bar_width, color='#5cb85c', label='Positive')
    plt.barh(bars, neutral_data, bar_width, left=positive_data, color='#5bc0de', label='Neutral')
    plt.barh(bars, negative_data, bar_width, left=positive_data+neutral_data, color='#d9534f', label='Negative')
    
    # Set labels and title
    plt.yticks(bars, top_reviewed['short_name'])
    plt.xlabel('Percentage (%)', fontsize=12)
    plt.title('Sentiment Distribution for Most Reviewed Products', fontsize=16)
    plt.legend(loc='upper right')
    
    # Add review count to y-axis labels
    for i, product in enumerate(top_reviewed['short_name']):
        plt.text(
            101, 
            i, 
            f"({top_reviewed['review_count'].iloc[i]} reviews)", 
            va='center'
        )
    
    plt.tight_layout()
    plt.xlim(0, 110)  # Make space for review count text
    
    # Save chart
    stacked_file = os.path.join(results_dir, f"product_sentiment_distribution_{timestamp}.png")
    plt.savefig(stacked_file)
    plt.close()
    
    print(f"Product visualizations saved to {results_dir} directory")

def main():
    """
    Main function to run the sentiment analysis pipeline
    """
    print("=== Brand Sentiment Analysis Tool ===\n")
    
    # Use amazon.csv file directly
    input_file = "amazon.csv"
    
    # Load data
    df = load_csv(input_file)
    if df is None:
        return
        
    # Display column names to help understand the data
    print("\nCSV columns found:", df.columns.tolist())
    
    # Filter records
    filtered_df = filter_records(df)
    
    # Analyze sentiment
    analyzed_df = analyze_sentiment(filtered_df)
    
    # Generate summary
    generate_summary(analyzed_df)
    
    # Additional product-specific analysis
    print("\nPerforming product-specific sentiment analysis...")
    product_sentiment_analysis(analyzed_df)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
