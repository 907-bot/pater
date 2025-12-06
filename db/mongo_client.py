# backend/db/mongo_client.py - MongoDB connection manager

import logging
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextlib import asynccontextmanager

from config import settings

logger = logging.getLogger(__name__)

# ============ Global MongoDB Instance ============

_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None

# ============ MongoDB Client ============

class MongoClient:
    """MongoDB async client wrapper"""
    
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize MongoDB client
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.uri = uri or settings.mongodb_url
        self.db_name = db_name or settings.mongodb_db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> AsyncIOMotorDatabase:
        """
        Connect to MongoDB
        
        Returns:
            Database instance
        """
        try:
            logger.info(f"Connecting to MongoDB: {self.db_name}")
            
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
            
            # Test connection
            await self.client.admin.command('ismaster')
            
            logger.info("✅ Connected to MongoDB")
            return self.db
        
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        try:
            if self.client:
                logger.info("Closing MongoDB connection...")
                self.client.close()
                logger.info("✅ MongoDB disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MongoDB: {e}")
    
    async def create_indexes(self) -> None:
        """Create database indexes"""
        try:
            if not self.db:
                return
            
            logger.info("Creating MongoDB indexes...")
            
            # Users collection
            await self.db['users'].create_index('email', unique=True)
            await self.db['users'].create_index('user_id', unique=True)
            
            # Products collection
            await self.db['products'].create_index('product_id', unique=True)
            await self.db['products'].create_index([('platform', 1), ('category', 1)])
            
            # Watchlist
            await self.db['watchlist'].create_index([('user_id', 1), ('product_id', 1)], unique=True)
            
            # Price history
            await self.db['price_history'].create_index([('product_id', 1), ('timestamp', 1)])
            
            logger.info("✅ MongoDB indexes created")
        
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def health_check(self) -> bool:
        """Check MongoDB health"""
        try:
            if self.client:
                await self.client.admin.command('ismaster')
                return True
            return False
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    def get_collection(self, collection_name: str):
        """Get collection"""
        if not self.db:
            raise RuntimeError("MongoDB not connected")
        return self.db[collection_name]

# ============ Global Functions ============

async def init_mongo(uri: Optional[str] = None, db_name: Optional[str] = None) -> AsyncIOMotorDatabase:
    """Initialize MongoDB"""
    global _mongo_client, _mongo_db
    
    _mongo_client = MongoClient(uri, db_name)
    _mongo_db = await _mongo_client.connect()
    await _mongo_client.create_indexes()
    
    return _mongo_db

async def close_mongo() -> None:
    """Close MongoDB connection"""
    global _mongo_client
    if _mongo_client:
        await _mongo_client.disconnect()

def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    global _mongo_db
    if _mongo_db is None:
        raise RuntimeError("MongoDB not initialized - call init_mongo() first")
    return _mongo_db

@asynccontextmanager
async def mongo_session():
    """Context manager for MongoDB operations"""
    db = get_mongo_db()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error in MongoDB session: {e}")
        raise
