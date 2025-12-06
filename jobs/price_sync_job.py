# backend/jobs/price_sync_job.py - Scheduled price synchronization

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from db import get_mongo_db, get_redis_client
from scrapers import AmazonScraper, FlipkartScraper, MyntraScraper
from services import PriceService, CacheService

logger = logging.getLogger(__name__)

# ============ Price Sync Job ============

class PriceSyncJob:
    """Background job for synchronizing prices from e-commerce platforms"""
    
    def __init__(self):
        """Initialize price sync job"""
        self.scrapers = {
            'amazon': AmazonScraper(),
            'flipkart': FlipkartScraper(),
            'myntra': MyntraScraper()
        }
        self.price_service = PriceService()
        self.cache_service = CacheService()
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute price synchronization
        
        Returns:
            Job results summary
        """
        try:
            logger.info("🔄 Starting price sync job...")
            start_time = datetime.utcnow()
            
            # Get all products with watch status
            db = get_mongo_db()
            products = await db['products'].find({'is_tracked': True}).to_list(None)
            
            if not products:
                logger.warning("No products to sync")
                return {
                    'status': 'success',
                    'timestamp': start_time.isoformat(),
                    'products_synced': 0,
                    'duration_seconds': 0
                }
            
            logger.info(f"Syncing {len(products)} products...")
            
            # Sync prices by platform
            results = await self._sync_by_platform(products)
            
            # Update prices in database
            await self._update_prices(results)
            
            # Clear related caches
            await self._clear_caches(results)
            
            # Calculate job duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Price sync completed in {duration:.2f}s")
            
            return {
                'status': 'success',
                'timestamp': start_time.isoformat(),
                'products_synced': len(products),
                'duration_seconds': duration,
                'results': results
            }
        
        except Exception as e:
            logger.error(f"❌ Price sync job failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _sync_by_platform(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """Sync prices grouped by platform"""
        try:
            results = {
                'amazon': [],
                'flipkart': [],
                'myntra': []
            }
            
            # Group products by platform
            by_platform = {}
            for product in products:
                platform = product.get('platform', 'unknown')
                if platform not in by_platform:
                    by_platform[platform] = []
                by_platform[platform].append(product)
            
            # Sync each platform
            for platform, platform_products in by_platform.items():
                if platform in self.scrapers:
                    logger.info(f"Syncing {len(platform_products)} {platform} products...")
                    
                    scraped = await self._scrape_products(
                        platform,
                        platform_products
                    )
                    
                    results[platform] = scraped
                    logger.info(f"✅ Synced {len(scraped)} {platform} products")
            
            return results
        
        except Exception as e:
            logger.error(f"Platform sync error: {e}")
            return {'amazon': [], 'flipkart': [], 'myntra': []}
    
    async def _scrape_products(self, platform: str, products: List[Dict]) -> List[Dict]:
        """Scrape products from platform"""
        try:
            scraper = self.scrapers[platform]
            urls = [p.get('product_url') for p in products if p.get('product_url')]
            
            if not urls:
                return []
            
            # Scrape with concurrent requests
            scraped = await scraper.scrape_multiple(urls)
            return scraped
        
        except Exception as e:
            logger.error(f"Scraping error for {platform}: {e}")
            return []
    
    async def _update_prices(self, results: Dict[str, List[Dict]]) -> None:
        """Update prices in database"""
        try:
            db = get_mongo_db()
            
            for platform, products in results.items():
                for product in products:
                    if not product:
                        continue
                    
                    # Record price history
                    await db['price_history'].insert_one({
                        'product_id': product.get('product_id'),
                        'platform': platform,
                        'price': product.get('current_price'),
                        'discount_percent': product.get('discount_percent'),
                        'timestamp': datetime.utcnow()
                    })
                    
                    # Update product document
                    await db['products'].update_one(
                        {'product_id': product.get('product_id')},
                        {
                            '$set': {
                                'current_price': product.get('current_price'),
                                'discount_percent': product.get('discount_percent'),
                                'rating': product.get('rating'),
                                'review_count': product.get('review_count'),
                                'last_synced': datetime.utcnow()
                            }
                        }
                    )
            
            logger.info("✅ Prices updated in database")
        
        except Exception as e:
            logger.error(f"Price update error: {e}")
    
    async def _clear_caches(self, results: Dict[str, List[Dict]]) -> None:
        """Clear related caches"""
        try:
            redis = get_redis_client()
            
            for platform, products in results.items():
                for product in products:
                    if product:
                        product_id = product.get('product_id')
                        # Clear product cache
                        await redis.delete(f"product:{product_id}")
                        # Clear price cache
                        await redis.delete(f"price:{product_id}")
            
            logger.info("✅ Caches cleared")
        
        except Exception as e:
            logger.error(f"Cache clearing error: {e}")

# ============ Scheduler ============

async def schedule_price_sync(scheduler: AsyncIOScheduler) -> None:
    """
    Schedule price sync job
    
    Args:
        scheduler: APScheduler AsyncIOScheduler
    """
    try:
        job = PriceSyncJob()
        
        # Run every hour at minute 0
        scheduler.add_job(
            job.execute,
            CronTrigger(minute=0),
            id='price_sync_job',
            name='Price Synchronization Job',
            misfire_grace_time=300
        )
        
        logger.info("✅ Price sync job scheduled (hourly at :00)")
    
    except Exception as e:
        logger.error(f"Failed to schedule price sync: {e}")
