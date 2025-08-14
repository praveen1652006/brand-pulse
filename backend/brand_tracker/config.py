"""
Configuration file for the Brand Tracker.
"""

# Twitter API credentials
TWITTER_API_KEY = "8UKr0E75FysHz9a9R4n5dm6sZ"
TWITTER_API_SECRET = "z8jdiE5PrEUuWQapqONaixjlM6MZ8ZETGWs31sKxMO3tgvaoev"
TWITTER_ACCESS_TOKEN = "1955269594773659648-DMHQfAv3Tb4jUIkTSTqwhpaLGYDd4i"
TWITTER_ACCESS_TOKEN_SECRET = "FSCud4D428Ps88NuZ5j9GHRdeEPyS1drg8cq4Ud6yi9i3"
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAACko3gEAAAAAIXTrdSkn%2B4GafjtZhMGTZjw3sTs%3DHWakOyZm7bLXriyduxabbCAH3v3FqGabTEx34uLbawZ61EfTOt"

# Google News API credentials
GOOGLE_NEWS_API_KEY = "97beed4894894a2b8bfd54a1e9c27e4c"

# Apify API credentials (for Amazon reviews)
APIFY_API_KEY = "apify_api_rnZx39I9aIdOw10fbzFXD0nmxoUp0M4w9ymi"

# Brand tracking configurations
BRAND_CONFIGS = {
    # Technology company tracking
    "apple": {
        "brand_identifiers": ["Apple", "iPhone", "iPad", "MacBook", "iOS", "Tim Cook"],
        "keywords": ["Apple products", "Apple store", "Genius Bar", "Apple support", "Apple event"],
        "hashtags": ["apple", "iphone", "ipad", "macbook", "ios", "wwdc"],
        "min_posts": 100,
        "interval": 60,  # 1 minute
    },
    
    # Fast food chain tracking
    "mcdonalds": {
        "brand_identifiers": ["McDonald's", "McD", "Big Mac", "Happy Meal", "Golden Arches"],
        "keywords": ["fast food", "McDonalds menu", "McDonalds restaurant", "drive thru"],
        "hashtags": ["mcdonalds", "imlovinit", "bigmac", "happymeal"],
        "min_posts": 100,
        "interval": 60,  # 1 minute
    },
    
    # Sportswear brand tracking
    "nike": {
        "brand_identifiers": ["Nike", "Just Do It", "Air Jordan", "Nike Air", "Swoosh"],
        "keywords": ["Nike shoes", "Nike store", "sportswear", "athletic wear", "running shoes"],
        "hashtags": ["nike", "justdoit", "nikeair", "nikeshoes", "sportswear"],
        "min_posts": 100,
        "interval": 60,  # 1 minute
    },
    
    # Coffee chain tracking
    "starbucks": {
        "brand_identifiers": ["Starbucks", "Frappuccino", "Pumpkin Spice Latte", "PSL", "Coffee"],
        "keywords": ["Starbucks coffee", "coffee shop", "cafe", "barista", "coffee chain"],
        "hashtags": ["starbucks", "frappuccino", "psl", "coffee", "coffeelover"],
        "min_posts": 100,
        "interval": 60,  # 1 minute
    },
    
    # Automotive brand tracking
    "tesla": {
        "brand_identifiers": ["Tesla", "Elon Musk", "Model S", "Model 3", "Model X", "Model Y", "Cybertruck"],
        "keywords": ["electric cars", "Tesla stock", "supercharger", "autopilot", "EV"],
        "hashtags": ["tesla", "elonmusk", "electriccars", "ev", "cybertruck"],
        "min_posts": 100,
        "interval": 60,  # 1 minute
    },
    
    # Custom configuration (fill in your own)
    "custom": {
        "brand_identifiers": ["Amazon"],
        "keywords": ["e-commerce", "online shopping", "Amazon Prime", "AWS"],
        "hashtags": ["amazon", "prime", "aws", "onlineshopping"],
        "min_posts": 100,
        "interval": 60,  # 1 minute
    }
}

# Platforms to collect from
PLATFORMS = ["twitter", "reddit", "news", "amazon"]
