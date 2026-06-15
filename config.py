import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # News API Configuration (using NewsAPI.org - get free key from https://newsapi.org)
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'b2d690b31bba4e0d833738cec0ddaded')
    NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
    
    # Gemini API Configuration - USING FREE VERSION
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDGCWzvSHwiKTqKWEK7E4CugR294vpgn4U')
    GEMINI_MODEL = "gemini-1.5-flash"  # Updated to free model
    
    # Application Configuration
    CHECK_INTERVAL_MINUTES = 30
    MAX_POSTS_PER_BATCH = 5
    COUNTRY = "us"  # Change as needed
    CATEGORY = "technology"  # business, entertainment, general, health, science, sports, technology
    
    # Instagram Post Dimensions
    POST_WIDTH = 1080
    POST_HEIGHT = 1920  # Instagram Stories 9:16 ratio (matching template)
    
    # Storage
    PROCESSED_NEWS_FILE = "processed_news.json"
    POSTS_DIRECTORY = "posts"