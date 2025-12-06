# backend/services/cache_service.py - Redis caching service

import logging
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from models.database import get_redis_client, RedisKeys
from config import settings

logger = logging.getLogger(__name__)

# ============ Cache Service ============

class CacheService:
    """Redis caching service"""
    
    # Cache TTL defaults (in seconds)
    PRODUCT_CACHE_TTL = 3600  # 1 hour
    PREDICTION_CACHE_TTL = 1800  # 30 minutes
    FESTIVAL_CACHE_TTL = 86400  # 24 hours
    USER_CACHE_TTL = 1800  # 30 minutes
    
    @staticmethod
    async def set_product_cache(
        product_id: str,
        data: Dict[str, Any],
        ttl: int = PRODUCT_CACHE_TTL
    ) -> bool:
        """
        Cache product data
        
        Args:
            product_id: Product ID
            data: Product data
            ttl: Time to live in seconds
        
        Returns:
            Success status
        """
        try:
            redis = get_redis_client()
            key = RedisKeys.get_product_cache_key(product_id)
            
            await redis.setex(
                key,
                ttl,
                json.dumps(data, default=str)
            )
            
            logger.debug(f"Cached product {product_id}")
            return True
        
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @staticmethod
    async def get_product_cache(product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product from cache
        
        Args:
            product_id: Product ID
        
        Returns:
            Product data or None
        """
        try:
            redis = get_redis_client()
            key = RedisKeys.get_product_cache_key(product_id)
            
            data = await redis.get(key)
            
            if data:
                logger.debug(f"Product cache hit: {product_id}")
                return json.loads(data)
            
            logger.debug(f"Product cache miss: {product_id}")
            return None
        
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @staticmethod
    async def delete_product_cache(product_id: str) -> bool:
        """Delete product from cache"""
        try:
            redis = get_redis_client()
            key = RedisKeys.get_product_cache_key(product_id)
            
            await redis.delete(key)
            logger.debug(f"Cleared product cache: {product_id}")
            return True
        
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    @staticmethod
    async def cache_prediction(
        product_id: str,
        prediction_hash: str,
        data: Dict[str, Any],
        ttl: int = PREDICTION_CACHE_TTL
    ) -> bool:
        """Cache prediction result"""
        try:
            redis = get_redis_client()
            key = f"cache:predictions:{prediction_hash}"
            
            await redis.setex(
                key,
                ttl,
                json.dumps(data, default=str)
            )
            
            logger.debug(f"Cached prediction {prediction_hash}")
            return True
        
        except Exception as e:
            logger.error(f"Prediction cache error: {e}")
            return False
    
    @staticmethod
    async def get_cached_prediction(prediction_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction"""
        try:
            redis = get_redis_client()
            key = f"cache:predictions:{prediction_hash}"
            
            data = await redis.get(key)
            
            if data:
                logger.debug(f"Prediction cache hit: {prediction_hash}")
                return json.loads(data)
            
            return None
        
        except Exception as e:
            logger.error(f"Prediction get error: {e}")
            return None
    
    @staticmethod
    async def cache_festivals(
        festivals: list,
        ttl: int = FESTIVAL_CACHE_TTL
    ) -> bool:
        """Cache festival data"""
        try:
            redis = get_redis_client()
            key = "cache:festivals"
            
            await redis.setex(
                key,
                ttl,
                json.dumps(festivals, default=str)
            )
            
            logger.debug("Cached festivals list")
            return True
        
        except Exception as e:
            logger.error(f"Festival cache error: {e}")
            return False
    
    @staticmethod
    async def get_cached_festivals() -> Optional[list]:
        """Get cached festivals"""
        try:
            redis = get_redis_client()
            key = "cache:festivals"
            
            data = await redis.get(key)
            
            if data:
                logger.debug("Festival cache hit")
                return json.loads(data)
            
            return None
        
        except Exception as e:
            logger.error(f"Festival get error: {e}")
            return None
    
    @staticmethod
    async def set_user_session(
        user_id: str,
        session_data: Dict[str, Any],
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """
        Set user session data
        
        Args:
            user_id: User ID
            session_data: Session data
            ttl: Time to live
        
        Returns:
            Success status
        """
        try:
            redis = get_redis_client()
            key = RedisKeys.get_user_session_key(user_id)
            
            await redis.setex(
                key,
                ttl,
                json.dumps(session_data, default=str)
            )
            
            logger.debug(f"Session cached for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Session cache error: {e}")
            return False
    
    @staticmethod
    async def get_user_session(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        try:
            redis = get_redis_client()
            key = RedisKeys.get_user_session_key(user_id)
            
            data = await redis.get(key)
            
            if data:
                logger.debug(f"Session cache hit for user {user_id}")
                return json.loads(data)
            
            return None
        
        except Exception as e:
            logger.error(f"Session get error: {e}")
            return None
    
    @staticmethod
    async def invalidate_user_session(user_id: str) -> bool:
        """Invalidate user session"""
        try:
            redis = get_redis_client()
            key = RedisKeys.get_user_session_key(user_id)
            
            await redis.delete(key)
            logger.debug(f"Session invalidated for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Session invalidate error: {e}")
            return False
    
    @staticmethod
    async def get_rate_limit_count(
        user_id: str,
        window: int = 3600
    ) -> int:
        """
        Get rate limit count
        
        Args:
            user_id: User ID
            window: Time window in seconds
        
        Returns:
            Request count in current window
        """
        try:
            redis = get_redis_client()
            key = RedisKeys.get_rate_limit_key(user_id)
            
            count = await redis.get(key)
            return int(count) if count else 0
        
        except Exception as e:
            logger.error(f"Rate limit get error: {e}")
            return 0
    
    @staticmethod
    async def increment_rate_limit(
        user_id: str,
        window: int = 3600
    ) -> int:
        """Increment rate limit counter"""
        try:
            redis = get_redis_client()
            key = RedisKeys.get_rate_limit_key(user_id)
            
            count = await redis.incr(key)
            
            # Set expiration on first increment
            if count == 1:
                await redis.expire(key, window)
            
            return count
        
        except Exception as e:
            logger.error(f"Rate limit increment error: {e}")
            return 0
    
    @staticmethod
    async def clear_all_cache() -> bool:
        """Clear all application cache"""
        try:
            redis = get_redis_client()
            
            # Delete all cache: prefixed keys
            cursor = 0
            while True:
                cursor, keys = await redis.scan(
                    cursor,
                    match="cache:*",
                    count=100
                )
                
                if keys:
                    await redis.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info("Cache cleared")
            return True
        
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    @staticmethod
    async def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis = get_redis_client()
            
            info = await redis.info('memory')
            
            return {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'peak_memory': info.get('used_memory_peak_human', 'N/A'),
                'memory_fragmentation': info.get('mem_fragmentation_ratio', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}

# ============ Global Cache Service Instance ============

cache_service = CacheService()
