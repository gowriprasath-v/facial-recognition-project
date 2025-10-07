import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
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
        try:
            self._client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self._client.server_info()
            db_name = Config.MONGODB_URI.split('/')[-1] or 'facial_recognition'
            self._db = self._client[db_name]
            print(f"Connected to MongoDB: {db_name}")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db

db_manager = DatabaseManager()

def get_db():
    return db_manager.db
