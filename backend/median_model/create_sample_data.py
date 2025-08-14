import pandas as pd
import os
from datetime import datetime

def create_sample_data():
    """
    Creates a sample CSV file with mock brand mentions to test the sentiment analyzer
    """
    # Sample data with various sentiments
    data = {
        'source': ['Twitter', 'Reddit', 'Amazon', 'Twitter', 'Reddit', 'Google News', 'Amazon', 'Twitter', 'Reddit', 'Twitter'],
        'date': ['2025-08-10', '2025-08-11', '2025-08-09', '2025-08-12', '2025-08-10', '2025-08-08', '2025-08-11', '2025-08-12', '2025-08-10', '2025-08-11'],
        'content': [
            "I absolutely love this product! Best purchase ever.",
            "The quality of this brand has really gone downhill. Very disappointed.",
            "Average product, does what it claims but nothing special.",
            "This is a fantastic brand, customer service was excellent too!",
            "Terrible experience with this product. Broke after two uses.",
            "Company announces exciting new features for their flagship product.",
            "This product works well enough but is overpriced for what you get.",
            "I can't believe how amazing this product is! Exceeded all expectations.",
            "Not worth the money. Save your cash and buy something else.",
            "Just received my order and already loving it. Great job!"
        ],
        'user_id': ['user123', 'user456', 'user789', 'user234', 'user567', 'news1', 'user890', 'user345', 'user678', 'user901'],
        'likes': [45, 23, 5, 67, 89, 12, 3, 56, 34, 78],
        'location': ['New York', 'California', '', 'Texas', 'Florida', '', 'Washington', 'Oregon', 'Illinois', 'Arizona']
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create sample data directory if it doesn't exist
    if not os.path.exists('sample_data'):
        os.makedirs('sample_data')
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save to CSV
    file_path = os.path.join('sample_data', f'brand_mentions_{timestamp}.csv')
    df.to_csv(file_path, index=False)
    
    print(f"Sample data created at: {file_path}")
    return file_path

if __name__ == "__main__":
    # Create sample data
    sample_file = create_sample_data()
    
    print("\nNow you can run the sentiment analyzer with this sample data:")
    print(f"python sentiment_analyzer.py")
    print(f"Then enter the path: {sample_file}")
