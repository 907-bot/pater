# backend/models/database.py - Database connections and utilities

import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from contextlib import asynccontextmanager

from config import settings

logger = logging.getLogger(__name__)

# ============ Global Database Instances ============

mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_db: Optional[AsyncIOMotorDatabase] = None
redis_client: Optional[AsyncRedis] = None

# ============ MongoDB Functions ============

async def connect_to_mongodb():
    """Connect to MongoDB"""
    global mongodb_client, mongodb_db
    
    try:
        logger.info("Connecting to MongoDB...")
        
        mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        mongodb_db = mongodb_client[settings.mongodb_db_name]
        
        # Test connection
        await mongodb_client.admin.command('ismaster')
        
        logger.info("✅ Connected to MongoDB")
        return mongodb_db
    
    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {e}")
        raise

async def close_mongodb():
    """Close MongoDB connection"""
    global mongodb_client
    
    try:
        if mongodb_client:
            logger.info("Closing MongoDB connection...")
            mongodb_client.close()
            mongodb_client = None
            logger.info("✅ MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB: {e}")

def get_mongodb_client() -> AsyncIOMotorClient:
    """Get MongoDB client instance"""
    if mongodb_client is None:
        raise RuntimeError("MongoDB not connected")
    return mongodb_client

def get_mongodb_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    if mongodb_db is None:
        raise RuntimeError("MongoDB database not initialized")
    return mongodb_db

# ============ Redis Functions ============

async def connect_to_redis():
    """Connect to Redis"""
    global redis_client
    
    try:
        logger.info("Connecting to Redis...")
        
        redis_client = await AsyncRedis.from_url(
            settings.redis_url,
            encoding="utf8",
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        
        logger.info("✅ Connected to Redis")
        return redis_client
    
    except Exception as e:
        logger.error(f"❌ Redis connection error: {e}")
        raise

async def close_redis():
    """Close Redis connection"""
    global redis_client
    
    try:
        if redis_client:
            logger.info("Closing Redis connection...")
            await redis_client.close()
            redis_client = None
            logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

def get_redis_client() -> AsyncRedis:
    """Get Redis client instance"""
    if redis_client is None:
        raise RuntimeError("Redis not connected")
    return redis_client

# ============ MongoDB Collections ============

class MongoDBCollections:
    """MongoDB collection accessors"""
    
    @staticmethod
    def get_users_collection():
        """Get users collection"""
        return get_mongodb_db()['users']
    
    @staticmethod
    def get_products_collection():
        """Get products collection"""
        return get_mongodb_db()['products']
    
    @staticmethod
    def get_watchlist_collection():
        """Get watchlist collection"""
        return get_mongodb_db()['watchlist']
    
    @staticmethod
    def get_price_alerts_collection():
        """Get price alerts collection"""
        return get_mongodb_db()['price_alerts']
    
    @staticmethod
    def get_price_history_collection():
        """Get price history collection"""
        return get_mongodb_db()['price_history']
    
    @staticmethod
    def get_predictions_collection():
        """Get predictions collection"""
        return get_mongodb_db()['predictions']
    
    @staticmethod
    def get_festivals_collection():
        """Get festivals collection"""
        return get_mongodb_db()['festivals']
    
    @staticmethod
    def get_notifications_collection():
        """Get notifications collection"""
        return get_mongodb_db()['notifications']
    
    @staticmethod
    def get_sessions_collection():
        """Get sessions collection"""
        return get_mongodb_db()['sessions']
    
    @staticmethod
    def get_analytics_collection():
        """Get analytics collection"""
        return get_mongodb_db()['analytics']

# ============ Redis Key Patterns ============

class RedisKeys:
    """Redis key pattern definitions"""
    
    # User keys
    USER_PREFIX = "user:"
    USER_SESSION = f"{USER_PREFIX}session:{{user_id}}"
    USER_WATCHLIST = f"{USER_PREFIX}watchlist:{{user_id}}"
    USER_PREFERENCES = f"{USER_PREFIX}preferences:{{user_id}}"
    
    # Product keys
    PRODUCT_PREFIX = "product:"
    PRODUCT_CACHE = f"{PRODUCT_PREFIX}{{product_id}}"
    PRODUCT_PRICES = f"{PRODUCT_PREFIX}prices:{{product_id}}"
    
    # Cache keys
    CACHE_PREFIX = "cache:"
    CACHE_PREDICTIONS = f"{CACHE_PREFIX}predictions:{{hash}}"
    CACHE_FESTIVALS = f"{CACHE_PREFIX}festivals"
    
    # Rate limiting keys
    RATE_LIMIT_PREFIX = "rate:"
    RATE_LIMIT_USER = f"{RATE_LIMIT_PREFIX}user:{{user_id}}"
    RATE_LIMIT_IP = f"{RATE_LIMIT_PREFIX}ip:{{ip_address}}"
    
    # Session keys
    SESSION_PREFIX = "session:"
    SESSION_DATA = f"{SESSION_PREFIX}{{session_id}}"
    
    @staticmethod
    def get_user_session_key(user_id: str) -> str:
        """Get user session key"""
        return f"user:session:{user_id}"
    
    @staticmethod
    def get_user_watchlist_key(user_id: str) -> str:
        """Get user watchlist key"""
        return f"user:watchlist:{user_id}"
    
    @staticmethod
    def get_product_cache_key(product_id: str) -> str:
        """Get product cache key"""
        return f"product:{product_id}"
    
    @staticmethod
    def get_rate_limit_key(user_id: str) -> str:
        """Get rate limit key for user"""
        return f"rate:user:{user_id}"

# ============ Lifespan Context Manager ============

@asynccontextmanager
async def lifespan():
    """FastAPI lifespan context manager"""
    # Startup
    try:
        await connect_to_mongodb()
        await connect_to_redis()
        logger.info("✅ All databases connected")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await close_mongodb()
        await close_redis()
        logger.info("✅ All databases closed")
    except Exception as e:
        logger.error(f"❌ Database cleanup error: {e}")

# ============ Database Utilities ============

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        db = get_mongodb_db()
        
        # Users collection indexes
        await db['users'].create_index('email', unique=True)
        await db['users'].create_index('user_id', unique=True)
        await db['users'].create_index('created_at')
        
        # Products collection indexes
        await db['products'].create_index('product_id', unique=True)
        await db['products'].create_index([('platform', 1), ('category', 1)])
        await db['products'].create_index('created_at')
        
        # Watchlist indexes
        await db['watchlist'].create_index([('user_id', 1), ('product_id', 1)], unique=True)
        await db['watchlist'].create_index('user_id')
        await db['watchlist'].create_index('added_at')
        
        # Price history indexes
        await db['price_history'].create_index([('product_id', 1), ('timestamp', 1)])
        await db['price_history'].create_index('platform')
        
        # Price alerts indexes
        await db['price_alerts'].create_index([('user_id', 1), ('product_id', 1)])
        await db['price_alerts'].create_index('is_active')
        
        # Predictions indexes
        await db['predictions'].create_index([('user_id', 1), ('created_at', 1)])
        await db['predictions'].create_index('product_id')
        
        # Sessions indexes
        await db['sessions'].create_index('user_id')
        await db['sessions'].create_index('expires_at', expireAfterSeconds=0)
        
        # Notifications indexes
        await db['notifications'].create_index([('user_id', 1), ('created_at', -1)])
        await db['notifications'].create_index('is_read')
        
        logger.info("✅ Database indexes created")
    
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

async def check_database_health() -> Dict[str, str]:
    """Check health of all databases"""
    health = {}
    
    # Check MongoDB
    try:
        client = get_mongodb_client()
        await client.admin.command('ismaster')
        health['mongodb'] = 'healthy'
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        health['mongodb'] = 'unhealthy'
    
    # Check Redis
    try:
        redis = get_redis_client()
        await redis.ping()
        health['redis'] = 'healthy'
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health['redis'] = 'unhealthy'
    
    return health

# ============ Query Helpers ============

async def insert_one(collection_name: str, document: Dict[str, Any]) -> str:
    """Insert a single document"""
    try:
        db = get_mongodb_db()
        result = await db[collection_name].insert_one(document)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Insert error in {collection_name}: {e}")
        raise

async def find_one(collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find a single document"""
    try:
        db = get_mongodb_db()
        return await db[collection_name].find_one(query)
    except Exception as e:
        logger.error(f"Find error in {collection_name}: {e}")
        raise

async def find_many(
    collection_name: str,
    query: Dict[str, Any],
    limit: int = 100,
    skip: int = 0,
    sort: Optional[list] = None
) -> list:
    """Find multiple documents"""
    try:
        db = get_mongodb_db()
        cursor = db[collection_name].find(query).skip(skip).limit(limit)
        
        if sort:
            cursor = cursor.sort(sort)
        
        return await cursor.to_list(length=limit)
    except Exception as e:
        logger.error(f"Find many error in {collection_name}: {e}")
        raise

async def update_one(
    collection_name: str,
    query: Dict[str, Any],
    update: Dict[str, Any]
) -> int:
    """Update a single document"""
    try:
        db = get_mongodb_db()
        result = await db[collection_name].update_one(query, {'$set': update})
        return result.modified_count
    except Exception as e:
        logger.error(f"Update error in {collection_name}: {e}")
        raise

async def delete_one(collection_name: str, query: Dict[str, Any]) -> int:
    """Delete a single document"""
    try:
        db = get_mongodb_db()
        result = await db[collection_name].delete_one(query)
        return result.deleted_count
    except Exception as e:
        logger.error(f"Delete error in {collection_name}: {e}")
        raise

async def count_documents(collection_name: str, query: Dict[str, Any]) -> int:
    """Count documents matching query"""
    try:
        db = get_mongodb_db()
        return await db[collection_name].count_documents(query)
    except Exception as e:
        logger.error(f"Count error in {collection_name}: {e}")
        raise
