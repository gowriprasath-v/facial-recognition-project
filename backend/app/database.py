import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Singleton database manager"""
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            from app.config import Config
            self._client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            self._client.server_info()
            # Get database from URI or use default
            db_name = Config.MONGODB_URI.split('/')[-1] or 'facial_recognition'
            self._db = self._client[db_name]
            logger.info(f"Connected to MongoDB: {db_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
    
    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db
    
    def health_check(self):
        """Check database health"""
        try:
            self._client.server_info()
            return True
        except Exception:
            return False

# Global instance
db_manager = DatabaseManager()

def get_db():
    """Get database instance"""
    return db_manager.db
