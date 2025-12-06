# backend/db/redis_client.py - Redis connection manager

import logging
from typing import Optional, Any
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio import from_url

from config import settings

logger = logging.getLogger(__name__)

# ============ Global Redis Instance ============

_redis_client: Optional[AsyncRedis] = None

# ============ Redis Client ============

class RedisClient:
    """Redis async client wrapper for caching"""
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize Redis client
        
        Args:
            url: Redis connection URL
        """
        self.url = url or settings.redis_url
        self.client: Optional[AsyncRedis] = None
    
    async def connect(self) -> AsyncRedis:
        """
        Connect to Redis
        
        Returns:
            Redis client instance
        """
        try:
            logger.info(f"Connecting to Redis: {self.url}")
            
            self.client = await from_url(
                self.url,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Test connection
            await self.client.ping()
            
            logger.info("✅ Connected to Redis")
            return self.client
        
        except Exception as e:
            logger.error(f"❌ Redis connection error: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        try:
            if self.client:
                logger.info("Closing Redis connection...")
                await self.client.close()
                logger.info("✅ Redis disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Redis: {e}")
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in Redis
        
        Args:
            key: Redis key
            value: Value to set
            ttl: Time to live in seconds
        
        Returns:
            Success status
        """
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis
        
        Args:
            key: Redis key
        
        Returns:
            Value or None
        """
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis incr error: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            await self.client.expire(key, seconds)
            return True
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get key TTL in seconds"""
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl error: {e}")
            return -1
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if self.client:
                await self.client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def flush_all(self) -> bool:
        """Flush all Redis data (use carefully!)"""
        try:
            await self.client.flushall()
            logger.warning("⚠️  Redis flushed")
            return True
        except Exception as e:
            logger.error(f"Redis flush error: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """Get Redis statistics"""
        try:
            info = await self.client.info('stats')
            return info
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {}

# ============ Global Functions ============

async def init_redis(url: Optional[str] = None) -> AsyncRedis:
    """Initialize Redis"""
    global _redis_client
    
    client = RedisClient(url)
    _redis_client = await client.connect()
    
    return _redis_client

async def close_redis() -> None:
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()

def get_redis_client() -> AsyncRedis:
    """Get Redis client instance"""
    global _redis_client
    if _redis_client is None:
        raise RuntimeError("Redis not initialized - call init_redis() first")
    return _redis_client
