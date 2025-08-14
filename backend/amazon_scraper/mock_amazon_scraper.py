#!/usr/bin/env python3
"""
Mock Amazon Scraper for testing integration with brand tracker - Using real datasets
"""

import asyncio
import logging
import json
import random
import os
import csv
import re
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockAmazonScraper:
    """
    A mock Amazon scraper that returns data from actual datasets for testing purposes
    """
    
    def __init__(self):
        """Initialize the mock scraper and load dataset"""
        self.base_url = "https://www.amazon.com"
        logger.info("Initialized Mock Amazon Scraper with real datasets")
        
        # Path to dataset files
        self.dataset_files = [
            os.path.join(os.path.dirname(__file__), "1429_1.csv"),
            os.path.join(os.path.dirname(__file__), "Datafiniti_Amazon_Consumer_Reviews_of_Amazon_Products.csv"),
            os.path.join(os.path.dirname(__file__), "Datafiniti_Amazon_Consumer_Reviews_of_Amazon_Products_May19.csv")
        ]
        
        # Load all datasets into memory
        self.reviews_data = self._load_datasets()
        
        # Group products by brand for faster lookup
        self.brand_products = self._group_by_brand()
        
        # Pre-compute product reviews by ASIN
        self.product_reviews = self._group_reviews_by_asin()
        
    def _load_datasets(self):
        """Load the Amazon reviews datasets from multiple CSV files"""
        reviews = []
        
        for dataset_file in self.dataset_files:
            try:
                # Check if file exists
                if not os.path.exists(dataset_file):
                    logger.warning(f"Dataset file does not exist: {dataset_file}")
                    continue
                    
                logger.info(f"Loading dataset: {os.path.basename(dataset_file)}")
                with open(dataset_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    for row in csv_reader:
                        reviews.append(row)
                        
            except Exception as e:
                logger.error(f"Error loading dataset {dataset_file}: {e}")
        
        logger.info(f"Loaded {len(reviews)} total reviews from {len(self.dataset_files)} datasets")
        return reviews
    
    def _group_by_brand(self):
        """Group products and reviews by brand for faster access"""
        brand_products = {}
        
        for review in self.reviews_data:
            # Handle different possible field names for brand across different datasets
            brand = self._get_field_value(review, ['brand', 'product.brand', 'manufacturer'])
            if not brand:
                continue
                
            brand = brand.lower()
            if brand not in brand_products:
                brand_products[brand] = []
            
            # Get product ASIN - handle different possible field names
            asin = self._get_field_value(review, ['asins', 'asin', 'product.asin', 'id'])
            if isinstance(asin, str) and ',' in asin:
                asin = asin.split(',')[0].strip()
                
            # Get product name - handle different possible field names
            name = self._get_field_value(review, ['name', 'product.name', 'product.title', 'title'])
            
            # Get categories - handle different possible field names
            categories_raw = self._get_field_value(review, ['categories', 'product.categories', 'category'])
            categories = []
            if categories_raw:
                if isinstance(categories_raw, str):
                    categories = categories_raw.split(',')
                elif isinstance(categories_raw, list):
                    categories = categories_raw
            
            # Check if this product is already in the list
            product = {
                'id': self._get_field_value(review, ['id', 'product.id']),
                'name': name,
                'asin': asin,
                'brand': brand,
                'categories': categories,
                'price': self._get_field_value(review, ['price', 'product.price', 'product.prices', 'prices'])
            }
            
            # Only add unique products
            product_exists = False
            for existing_product in brand_products[brand]:
                if existing_product.get('asin') == product.get('asin') or existing_product.get('id') == product.get('id'):
                    product_exists = True
                    break
            
            if not product_exists and product.get('asin'):
                brand_products[brand].append(product)
        
        logger.info(f"Grouped products by {len(brand_products)} brands")
        return brand_products
    
    def _group_reviews_by_asin(self):
        """Group reviews by ASIN for faster lookup"""
        product_reviews = {}
        
        for review in self.reviews_data:
            # Handle different possible field names for ASIN across different datasets
            asins = review.get('asins', review.get('asin', ''))
            if not asins:
                continue
                
            # Split ASINs (a product can have multiple ASINs)
            asin_list = asins.split(',') if isinstance(asins, str) else [asins]
            
            for asin in asin_list:
                asin = str(asin).strip()
                if not asin:
                    continue
                    
                if asin not in product_reviews:
                    product_reviews[asin] = []
                
                # Format the review, handling different possible field names
                formatted_review = {
                    'id': self._get_field_value(review, ['reviews.id', 'id', 'review.id']) 
                          or f"review_{asin}_{len(product_reviews[asin])}",
                    'asin': asin,
                    'title': self._get_field_value(review, ['reviews.title', 'title', 'review.title', 'reviews.summary']),
                    'rating': float(self._get_field_value(review, ['reviews.rating', 'rating', 'review.rating', 'reviews.stars', 'stars']) or 0),
                    'date': self._get_field_value(review, ['reviews.date', 'date', 'review.date', 'reviews.dateAdded', 'dateAdded']),
                    'username': self._get_field_value(review, ['reviews.username', 'username', 'reviews.name', 'name']) or 'Anonymous',
                    'text': self._get_field_value(review, ['reviews.text', 'text', 'review.text', 'reviews.content', 'content']),
                    'helpfulVotes': int(self._get_field_value(review, ['reviews.numHelpful', 'numHelpful', 'reviews.helpful', 'helpful']) or 0),
                    'verified': self._get_field_value(review, ['reviews.didPurchase', 'didPurchase', 'verified']),
                }
                
                # Try to parse the date
                try:
                    if formatted_review['date']:
                        # Try different date formats
                        date_formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%B %d, %Y']
                        date_str = formatted_review['date'].split('T')[0] if 'T' in formatted_review['date'] else formatted_review['date']
                        
                        for date_format in date_formats:
                            try:
                                review_date = datetime.strptime(date_str, date_format)
                                formatted_review['timestamp'] = review_date.isoformat()
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    # If date parsing fails, set a random recent date
                    random_days = random.randint(1, 7)
                    review_date = datetime.now() - timedelta(days=random_days)
                    formatted_review['timestamp'] = review_date.isoformat()
                    formatted_review['date'] = f"Reviewed on {review_date.strftime('%B %d, %Y')}"
                
                product_reviews[asin].append(formatted_review)
        
        logger.info(f"Grouped reviews for {len(product_reviews)} products")
        return product_reviews
    
    def _get_field_value(self, data_dict, possible_fields):
        """Helper method to get a value from a dictionary with multiple possible field names"""
        for field in possible_fields:
            if field in data_dict and data_dict[field]:
                return data_dict[field]
        return None
    
    async def search_products(self, query, max_products=5):
        """
        Search for products on Amazon using the dataset
        
        Args:
            query (str): Search query
            max_products (int): Maximum number of products to return
            
        Returns:
            list: List of product data
        """
        logger.info(f"Searching for: {query}")
        # Add a slight delay to simulate network request
        await asyncio.sleep(0.5)
        
        # Extract brand name from query
        query_terms = query.lower().split()
        products = []
        query_lower = query.lower()
        
        # First, check if any brand in our dataset matches the query
        for brand, brand_products in self.brand_products.items():
            # If brand name is in the query or query terms match product name
            if brand.lower() in query_lower or any(term in brand.lower() for term in query_terms):
                # Add products from this brand
                for product in brand_products:
                    # Check if product name contains any query terms
                    product_name = product.get('name', '').lower()
                    if any(term in product_name for term in query_terms) or True:  # Include all products for this brand
                        asin = product.get('asin', '')
                        if not asin:
                            continue
                        
                        # Get the number of reviews for this product
                        review_count = 0
                        if asin in self.product_reviews:
                            review_count = len(self.product_reviews[asin])
                        
                        # Get average rating if available, otherwise use random
                        avg_rating = 0
                        if review_count > 0:
                            total_rating = sum(float(review.get('rating', 0)) for review in self.product_reviews[asin])
                            avg_rating = round(total_rating / review_count, 1)
                        else:
                            avg_rating = round(random.uniform(3.0, 5.0), 1)
                            
                        products.append({
                            "asin": asin,
                            "title": product.get('name', ''),
                            "url": f"{self.base_url}/dp/{asin}",
                            "price": {"value": product.get('price', round(random.uniform(50, 500), 2)), "currency": "$"},
                            "rating": avg_rating,
                            "reviewsCount": review_count,
                            "image": product.get('imageURLs', f"https://example.com/image_{asin}.jpg")
                        })
                        
                        if len(products) >= max_products:
                            break
                
                if len(products) >= max_products:
                    break
        
        # If no products were found based on brand, look for products that have reviews mentioning the query
        if not products:
            logger.info(f"No products with brand {query} found. Looking for products with reviews mentioning {query}")
            
            # Find products with reviews mentioning the query
            products_with_relevant_reviews = {}
            
            # Go through all reviews and check if they mention the query
            for asin, reviews_list in self.product_reviews.items():
                relevant_reviews = []
                
                for review in reviews_list:
                    # Check if review text contains the query
                    review_text = review.get('text', '')
                    if review_text and query_lower in review_text.lower():
                        relevant_reviews.append(review)
                
                if relevant_reviews:
                    # We found reviews mentioning the query for this product
                    # Get product info
                    product_info = None
                    for brand, brand_products in self.brand_products.items():
                        for product in brand_products:
                            if product.get('asin') == asin:
                                product_info = product
                                break
                        if product_info:
                            break
                    
                    if not product_info:
                        continue
                    
                    # Calculate average rating for these reviews
                    total_rating = sum(float(review.get('rating', 0)) for review in relevant_reviews)
                    avg_rating = round(total_rating / len(relevant_reviews), 1) if relevant_reviews else 0
                    
                    products_with_relevant_reviews[asin] = {
                        "asin": asin,
                        "title": product_info.get('name', ''),
                        "url": f"{self.base_url}/dp/{asin}",
                        "price": {"value": product_info.get('price', round(random.uniform(50, 500), 2)), "currency": "$"},
                        "rating": avg_rating,
                        "reviewsCount": len(relevant_reviews),
                        "image": product_info.get('imageURLs', f"https://example.com/image_{asin}.jpg"),
                        "relevant_reviews": relevant_reviews
                    }
            
            # Sort products by number of relevant reviews (descending)
            sorted_products = sorted(
                products_with_relevant_reviews.values(), 
                key=lambda x: x["reviewsCount"], 
                reverse=True
            )
            
            # Take the top products, up to max_products
            products = sorted_products[:max_products]
            
            if products:
                logger.info(f"Found {len(sorted_products)} products with reviews mentioning '{query}', using top {len(products)}")
        
        # If still no products found, generate mock products
        if not products:
            # Generate sample products based on the query
            logger.info(f"No products found in dataset for brand: {query}, generating mock products (datasets only contain Amazon brand products)")
            brand = query.split()[0] if query else "Generic"
            for i in range(min(max_products, 5)):
                asin = f"B0{random.randint(10000000, 99999999)}"
                products.append({
                    "asin": asin,
                    "title": f"{brand} Product {i+1} - Sample Item",
                    "url": f"{self.base_url}/dp/{asin}",
                    "price": {"value": round(random.uniform(50, 500), 2), "currency": "$"},
                    "rating": round(random.uniform(3.0, 5.0), 1),
                    "reviewsCount": random.randint(10, 1000),
                    "image": f"https://example.com/image_{asin}.jpg"
                })
        
        logger.info(f"Found {len(products)} products")
        return products
    
    async def get_product_reviews(self, asin, max_reviews=10, days_ago=7, brand_query=None):
        """
        Get reviews for a specific product from the dataset
        
        Args:
            asin (str): Amazon Standard Identification Number
            max_reviews (int): Maximum number of reviews to collect
            days_ago (int): Only collect reviews from the last X days (used for filtering if dates available)
            brand_query (str): Optional brand query to filter reviews by
            
        Returns:
            list: List of reviews
        """
        logger.info(f"Getting reviews for ASIN: {asin}")
        # Add a slight delay to simulate network request
        await asyncio.sleep(0.5)
        
        reviews = []
        
        # Check if we have reviews for this ASIN
        if asin in self.product_reviews:
            all_reviews = self.product_reviews[asin]
            logger.info(f"Found {len(all_reviews)} reviews in dataset for ASIN: {asin}")
            
            # If brand_query is provided, first try to find reviews mentioning that brand
            filtered_reviews = all_reviews
            if brand_query and brand_query.lower() != "amazon":
                brand_query_lower = brand_query.lower()
                brand_related_reviews = []
                
                for review in all_reviews:
                    review_text = review.get('text', '')
                    if review_text and brand_query_lower in review_text.lower():
                        brand_related_reviews.append(review)
                
                if brand_related_reviews:
                    logger.info(f"Found {len(brand_related_reviews)} reviews mentioning '{brand_query}' for ASIN: {asin}")
                    filtered_reviews = brand_related_reviews
                else:
                    logger.info(f"No reviews mentioning '{brand_query}' found for ASIN: {asin}, using all reviews")
            
            # Filter by date if needed - DISABLED for this implementation
            # We want to use the CSV data regardless of date
            cutoff_date = None
            if days_ago > 0 and False:  # Disable date filtering by adding False
                cutoff_date = (datetime.now() - timedelta(days=days_ago)).date()
                logger.info(f"Using cutoff date: {cutoff_date} for filtering reviews")
            
            for review in filtered_reviews:
                # Include all reviews regardless of date
                reviews.append(review)
                
                if len(reviews) >= max_reviews:
                    break
        
        # If no reviews were found in our dataset, generate mock reviews
        if not reviews:
            logger.info(f"No reviews found in dataset for ASIN: {asin}, generating mock reviews (datasets only contain Amazon brand products)")
            sentiments = ["Excellent", "Great", "Good", "Average", "Poor"]
            
            for i in range(min(max_reviews, 5)):
                # Generate a random date within the last few days
                review_date = datetime.now() - timedelta(days=random.randint(1, days_ago))
                
                rating = random.randint(1, 5)
                sentiment_idx = min(5 - rating, 4)  # Map rating to sentiment index
                
                reviews.append({
                    "id": f"review_{asin}_{i}",
                    "asin": asin,
                    "title": f"{sentiments[sentiment_idx]} product, {'highly recommend' if rating >= 4 else 'needs improvement'}",
                    "rating": float(rating),
                    "date": f"Reviewed in the United States on {review_date.strftime('%B %d, %Y')}",
                    "timestamp": review_date.isoformat(),
                    "username": f"TestUser{random.randint(100, 999)}",
                    "verified": random.choice([True, False]),
                    "text": f"This is a sample review for testing purposes. The product is {sentiments[sentiment_idx].lower()}. {'I recommend it.' if rating >= 4 else 'I would not recommend it.'} {' '.join(['Sample text'] * 10)}",
                    "helpfulVotes": random.randint(0, 50)
                })
        
        logger.info(f"Found {len(reviews)} reviews for {asin}")
        return reviews
    
    async def collect_brand_reviews(self, brand_name, product_keywords=None, max_products=3, max_reviews_per_product=10, days_ago=7):
        """
        Collect reviews for products related to a specific brand
        
        Args:
            brand_name (str): The brand name to search for
            product_keywords (list): Additional keywords to combine with brand name
            max_products (int): Maximum number of products to get reviews for
            max_reviews_per_product (int): Maximum reviews per product
            days_ago (int): Only collect reviews from the last X days
            
        Returns:
            list: List of all collected reviews
        """
        logger.info(f"Collecting reviews for brand: {brand_name}")
        
        # If searching for a brand that's not in our dataset but might be mentioned in reviews
        # We'll search for products with reviews mentioning the brand directly
        if brand_name.lower() not in [b.lower() for b in self.brand_products.keys()]:
            logger.info(f"Brand {brand_name} not found in dataset. Looking for products with reviews mentioning {brand_name}")
            query_lower = brand_name.lower()
            products_with_relevant_reviews = {}
            
            # Go through all reviews and check if they mention the query
            for asin, reviews_list in self.product_reviews.items():
                relevant_reviews = []
                
                for review in reviews_list:
                    # Check if review text contains the query
                    review_text = review.get('text', '')
                    if review_text and query_lower in review_text.lower():
                        relevant_reviews.append(review)
                
                if relevant_reviews:
                    # We found reviews mentioning the query for this product
                    # Get product info
                    product_info = None
                    for b_name, brand_products in self.brand_products.items():
                        for product in brand_products:
                            if product.get('asin') == asin:
                                product_info = product
                                break
                        if product_info:
                            break
                    
                    if not product_info:
                        continue
                        
                    products_with_relevant_reviews[asin] = {
                        "asin": asin,
                        "title": product_info.get('name', ''),
                        "reviews": relevant_reviews
                    }
            
            # Sort products by number of relevant reviews (descending)
            sorted_products = sorted(
                products_with_relevant_reviews.items(), 
                key=lambda x: len(x[1]["reviews"]), 
                reverse=True
            )
            
            # Take the top products, up to max_products
            products_to_use = sorted_products[:max_products]
            
            if products_to_use:
                logger.info(f"Found {len(sorted_products)} products with reviews mentioning '{brand_name}', using top {len(products_to_use)}")
                
                # Collect all reviews
                all_reviews = []
                for asin, product_info in products_to_use:
                    product_reviews = product_info["reviews"][:max_reviews_per_product]
                    
                    # Add product info and brand tracker info to each review
                    for review in product_reviews:
                        review["product"] = {
                            "asin": asin,
                            "title": product_info.get("title", ""),
                            "url": f"{self.base_url}/dp/{asin}",
                            "image": f"https://example.com/image_{asin}.jpg",
                            "price": {"value": None, "currency": "$"},
                            "rating": 4.6
                        }
                        
                        # Add platform and brand tracker info
                        review["platform"] = "amazon"
                        review["brand_tracker"] = {
                            "matched_term": brand_name,
                            "term_type": "brand",
                            "brands_mentioned": [brand_name]
                        }
                    
                    all_reviews.extend(product_reviews)
                
                logger.info(f"Collected {len(all_reviews)} total reviews for brand: {brand_name}")
                return all_reviews
        
        # If we're here, we're using the regular brand search
        # Generate queries
        queries = [brand_name]
        if product_keywords:
            for keyword in product_keywords:
                queries.append(f"{brand_name} {keyword}")
        
        # Search for products
        all_products = []
        for query in queries[:2]:  # Limit to 2 queries for testing
            products = await self.search_products(query, max_products=2)
            all_products.extend(products)
            await asyncio.sleep(0.2)
        
        # Get unique products
        unique_products = {}
        for product in all_products:
            if product["asin"] not in unique_products:
                unique_products[product["asin"]] = product
        
        # Limit to max_products
        product_asins = list(unique_products.keys())[:max_products]
        
        # Collect reviews for each product
        all_reviews = []
        for asin in product_asins:
            product_info = unique_products[asin]
            
            # Check if the product already has relevant reviews from the search phase
            if "relevant_reviews" in product_info and product_info["relevant_reviews"]:
                reviews = product_info["relevant_reviews"][:max_reviews_per_product]
                logger.info(f"Using {len(reviews)} pre-filtered reviews mentioning '{brand_name}' for ASIN: {asin}")
            else:
                # Get reviews, passing the brand name to filter by
                reviews = await self.get_product_reviews(
                    asin, 
                    max_reviews=max_reviews_per_product,
                    days_ago=days_ago,
                    brand_query=brand_name
                )
            
            # Add product info and brand tracker info to each review
            for review in reviews:
                review["product"] = {
                    "asin": asin,
                    "title": product_info.get("title", ""),
                    "url": product_info.get("url", ""),
                    "image": product_info.get("image", ""),
                    "price": product_info.get("price", {}),
                    "rating": product_info.get("rating", "")
                }
                
                # Add platform and brand tracker info
                review["platform"] = "amazon"
                review["brand_tracker"] = {
                    "matched_term": brand_name,
                    "term_type": "brand",
                    "brands_mentioned": [brand_name]
                }
            
            all_reviews.extend(reviews)
            await asyncio.sleep(0.2)
        
        logger.info(f"Collected {len(all_reviews)} total reviews for brand: {brand_name}")
        return all_reviews
        
        # Generate queries
        queries = [brand_name]
        if product_keywords:
            for keyword in product_keywords:
                queries.append(f"{brand_name} {keyword}")
        
        # Mock search for products
        all_products = []
        for query in queries[:2]:  # Limit to 2 queries for testing
            products = await self.search_products(query, max_products=2)
            all_products.extend(products)
            await asyncio.sleep(0.2)
        
        # Get unique products
        unique_products = {}
        for product in all_products:
            if product["asin"] not in unique_products:
                unique_products[product["asin"]] = product
        
        # Limit to max_products
        product_asins = list(unique_products.keys())[:max_products]
        
        # Collect reviews for each product
        all_reviews = []
        for asin in product_asins:
            product_info = unique_products[asin]
            
            reviews = await self.get_product_reviews(
                asin, 
                max_reviews=max_reviews_per_product,
                days_ago=days_ago
            )
            
            # Add product info and brand tracker info to each review
            for review in reviews:
                review["product"] = {
                    "asin": asin,
                    "title": product_info.get("title", ""),
                    "url": product_info.get("url", ""),
                    "image": product_info.get("image", ""),
                    "price": product_info.get("price", {}),
                    "rating": product_info.get("rating", "")
                }
                
                # Add platform and brand tracker info
                review["platform"] = "amazon"
                review["brand_tracker"] = {
                    "matched_term": brand_name,
                    "term_type": "brand",
                    "brands_mentioned": [brand_name]
                }
            
            all_reviews.extend(reviews)
            await asyncio.sleep(0.2)
        
        logger.info(f"Mock collected {len(all_reviews)} total reviews for brand: {brand_name}")
        return all_reviews

    def format_reviews_for_brand_tracker(self, reviews):
        """
        Format Amazon reviews to match the brand tracker format
        
        Args:
            reviews (list): List of Amazon reviews
            
        Returns:
            list: Formatted reviews
        """
        formatted_reviews = []
        
        for review in reviews:
            # Extract key fields and format them
            review_id = review.get("id", "")
            if not review_id:
                review_id = str(hash(review.get("title", "") + review.get("text", "")))
            
            # Create a formatted review object
            formatted_review = {
                "review_id": review_id,
                "username": review.get("username", "Anonymous"),
                "timestamp": review.get("timestamp", ""),
                "text_content": review.get("text", ""),
                "title": review.get("title", ""),
                "rating": review.get("rating", 0),
                "verified_purchase": review.get("verified", False),
                "product": review.get("product", {}),
                "platform": "amazon",
                "engagement_metrics": {
                    "helpful_votes": review.get("helpfulVotes", 0)
                },
                "brand_tracker": review.get("brand_tracker", {})
            }
            
            # Add sentiment info if not already present
            if "sentiment" not in formatted_review["brand_tracker"]:
                # Simple sentiment based on rating
                rating = float(review.get("rating", 0))
                sentiment_score = (rating - 3) / 2  # Convert 1-5 rating to -1 to 1 scale
                
                # Categorize sentiment
                if sentiment_score > 0.2:
                    sentiment_category = "positive"
                elif sentiment_score < -0.2:
                    sentiment_category = "negative"
                else:
                    sentiment_category = "neutral"
                
                formatted_review["brand_tracker"]["sentiment"] = {
                    "score": sentiment_score,
                    "category": sentiment_category
                }
            
            formatted_reviews.append(formatted_review)
        
        return formatted_reviews

# Example usage
async def main():
    scraper = MockAmazonScraper()
    
    # Test product search
    products = await scraper.search_products("Apple iPhone")
    print(f"Found {len(products)} products")
    
    # Test review collection
    if products:
        asin = products[0]["asin"]
        reviews = await scraper.get_product_reviews(asin)
        print(f"Found {len(reviews)} reviews")
    
    # Test brand reviews
    brand_reviews = await scraper.collect_brand_reviews(
        "Apple", 
        product_keywords=["iPhone", "MacBook"],
        max_products=2,
        max_reviews_per_product=3
    )
    
    # Format for brand tracker
    formatted_reviews = scraper.format_reviews_for_brand_tracker(brand_reviews)
    
    # Save to file
    with open("mock_amazon_reviews.json", "w") as f:
        json.dump(formatted_reviews, f, indent=2)
    
    print(f"Saved {len(formatted_reviews)} formatted reviews to mock_amazon_reviews.json")

if __name__ == "__main__":
    asyncio.run(main())
