import requests
from config import NEWS_API_KEY, NEWS_URL

def fetch_news():
    params = {
        "apikey": NEWS_API_KEY,
        "language": "en",
        "category": "technology"
    }
    res = requests.get(NEWS_URL, params=params)
    return res.json().get("results", [])
