from pymongo import MongoClient
from datetime import datetime
from config import Config

class NewsDatabase:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.posted_news = self.db.posted_news
        self.pending_news = self.db.pending_news
    
    def is_news_posted(self, news_id):
        """Check if news has been posted"""
        return self.posted_news.find_one({'news_id': news_id}) is not None
    
    def mark_as_posted(self, news_id, instagram_post_id, news_data):
        """Mark news as posted"""
        self.posted_news.insert_one({
            'news_id': news_id,
            'instagram_post_id': instagram_post_id,
            'title': news_data.get('title'),
            'summary': news_data.get('summary'),
            'posted_at': datetime.now(),
            'source': news_data.get('source')
        })
    
    def add_pending_news(self, news_items):
        """Add news to pending queue"""
        for news in news_items:
            if not self.is_news_posted(news['id']) and not self.pending_news.find_one({'news_id': news['id']}):
                self.pending_news.insert_one({
                    'news_id': news['id'],
                    'data': news,
                    'added_at': datetime.now()
                })
    
    def get_pending_news(self, limit=5):
        """Get pending news for posting"""
        pending = list(self.pending_news.find().sort('added_at', 1).limit(limit))
        news_items = [item['data'] for item in pending]
        # Remove from pending after retrieval
        ids_to_remove = [item['_id'] for item in pending]
        self.pending_news.delete_many({'_id': {'$in': ids_to_remove}})
        return news_items
    
    def get_posted_count(self):
        """Get count of posted news"""
        return self.posted_news.count_documents({})