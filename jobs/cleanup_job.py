# backend/jobs/cleanup_job.py - Data cleanup and maintenance

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from db import get_mongo_db, get_redis_client, get_neo4j_driver

logger = logging.getLogger(__name__)

# ============ Cleanup Job ============

class CleanupJob:
    """Background job for data cleanup and maintenance"""
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute cleanup operations
        
        Returns:
            Job results summary
        """
        try:
            logger.info("🧹 Starting cleanup job...")
            start_time = datetime.utcnow()
            
            results = {}
            
            # Cleanup MongoDB
            logger.info("🧹 Cleaning up MongoDB...")
            results['mongodb'] = await self._cleanup_mongodb()
            
            # Cleanup Redis
            logger.info("🧹 Cleaning up Redis...")
            results['redis'] = await self._cleanup_redis()
            
            # Cleanup Neo4j
            logger.info("🧹 Cleaning up Neo4j...")
            results['neo4j'] = await self._cleanup_neo4j()
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Cleanup job completed in {duration:.2f}s")
            
            return {
                'status': 'success',
                'timestamp': start_time.isoformat(),
                'duration_seconds': duration,
                'results': results
            }
        
        except Exception as e:
            logger.error(f"❌ Cleanup job failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _cleanup_mongodb(self) -> Dict[str, Any]:
        """Cleanup MongoDB - remove old records"""
        try:
            db = get_mongo_db()
            
            # Delete price history older than 1 year
            cutoff_date = datetime.utcnow() - timedelta(days=365)
            result = await db['price_history'].delete_many(
                {'timestamp': {'$lt': cutoff_date}}
            )
            deleted_history = result.deleted_count
            
            # Delete inactive sessions older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            result = await db['sessions'].delete_many(
                {'last_activity': {'$lt': cutoff_date}}
            )
            deleted_sessions = result.deleted_count
            
            # Remove duplicate price records (keep latest)
            logger.info("Deduplicating price records...")
            duplicates = await self._remove_duplicate_prices(db)
            
            logger.info(f"✅ MongoDB cleanup complete")
            
            return {
                'status': 'success',
                'deleted_price_history': deleted_history,
                'deleted_sessions': deleted_sessions,
                'deduplicated_prices': duplicates
            }
        
        except Exception as e:
            logger.error(f"MongoDB cleanup error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _remove_duplicate_prices(self, db) -> int:
        """Remove duplicate price records"""
        try:
            count = 0
            
            # Get all products with prices
            products = await db['products'].find({}).to_list(None)
            
            for product in products:
                product_id = product.get('product_id')
                
                # Find duplicate prices for this product
                pipeline = [
                    {'$match': {'product_id': product_id}},
                    {'$sort': {'timestamp': -1}},
                    {
                        '$group': {
                            '_id': {'product_id': '$product_id', 'price': '$price'},
                            'ids': {'$push': '$_id'},
                            'count': {'$sum': 1}
                        }
                    },
                    {'$match': {'count': {'$gt': 1}}}
                ]
                
                duplicates = await db['price_history'].aggregate(pipeline).to_list(None)
                
                for dup in duplicates:
                    ids_to_delete = dup['ids'][1:]  # Keep first, delete rest
                    if ids_to_delete:
                        result = await db['price_history'].delete_many(
                            {'_id': {'$in': ids_to_delete}}
                        )
                        count += result.deleted_count
            
            return count
        
        except Exception as e:
            logger.error(f"Deduplication error: {e}")
            return 0
    
    async def _cleanup_redis(self) -> Dict[str, Any]:
        """Cleanup Redis - remove expired keys"""
        try:
            redis = get_redis_client()
            
            # Get memory stats before cleanup
            stats_before = await redis.get_stats()
            
            # Check and remove expired keys (Redis does this automatically)
            # But we can log memory usage
            
            # Optional: Clear old cache patterns
            # Get all keys matching pattern
            cursor = 0
            deleted = 0
            
            # You might want to manually clear specific patterns
            patterns = [
                'search:*',           # Old search results
                'cache:*',            # Old cached data
            ]
            
            for pattern in patterns:
                try:
                    # This is a simplified version - in production use SCAN
                    cursor = '0'
                    while True:
                        cursor, keys = await redis.client.scan(cursor, match=pattern, count=100)
                        if keys:
                            # Check each key's TTL
                            for key in keys:
                                ttl = await redis.ttl(key)
                                if ttl == -1:  # No expiration set
                                    await redis.delete(key)
                                    deleted += 1
                        
                        if cursor == '0':
                            break
                except Exception as e:
                    logger.debug(f"Pattern cleanup error for {pattern}: {e}")
            
            logger.info(f"✅ Redis cleanup complete")
            
            return {
                'status': 'success',
                'keys_deleted': deleted
            }
        
        except Exception as e:
            logger.error(f"Redis cleanup error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _cleanup_neo4j(self) -> Dict[str, Any]:
        """Cleanup Neo4j - remove orphaned nodes"""
        try:
            driver = get_neo4j_driver()
            
            async with driver.session() as session:
                # Remove orphaned products (no relationships)
                result = await session.run("""
                    MATCH (p:Product)
                    WHERE NOT (p)-[]-()
                    DELETE p
                    RETURN COUNT(p) as deleted
                """)
                
                orphaned = await result.single()
                deleted_orphans = orphaned['deleted'] if orphaned else 0
                
                # Remove orphaned users (no relationships)
                result = await session.run("""
                    MATCH (u:User)
                    WHERE NOT (u)-[]-()
                    DELETE u
                    RETURN COUNT(u) as deleted
                """)
                
                deleted_users = await result.single()
                deleted_users = deleted_users['deleted'] if deleted_users else 0
                
                logger.info(f"✅ Neo4j cleanup complete")
                
                return {
                    'status': 'success',
                    'orphaned_products_deleted': deleted_orphans,
                    'orphaned_users_deleted': deleted_users
                }
        
        except Exception as e:
            logger.error(f"Neo4j cleanup error: {e}")
            return {'status': 'error', 'error': str(e)}

# ============ Scheduler ============

async def schedule_cleanup(scheduler: AsyncIOScheduler) -> None:
    """
    Schedule cleanup job
    
    Args:
        scheduler: APScheduler AsyncIOScheduler
    """
    try:
        job = CleanupJob()
        
        # Run every day at 3 AM
        scheduler.add_job(
            job.execute,
            CronTrigger(hour=3, minute=0),
            id='cleanup_job',
            name='Data Cleanup Job',
            misfire_grace_time=300
        )
        
        logger.info("✅ Cleanup job scheduled (daily at 3:00 AM)")
    
    except Exception as e:
        logger.error(f"Failed to schedule cleanup job: {e}")
