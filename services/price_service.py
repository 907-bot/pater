# backend/services/price_service.py - Price tracking service

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import statistics

from models.database import (
    MongoDBCollections,
    insert_one,
    find_one,
    find_many,
    update_one
)

logger = logging.getLogger(__name__)

# ============ Price Service ============

class PriceService:
    """Price tracking and analysis service"""
    
    @staticmethod
    async def add_price_history(
        product_id: str,
        price: float,
        platform: str,
        discount_percent: float = 0
    ) -> bool:
        """
        Add price history entry
        
        Args:
            product_id: Product ID
            price: Current price
            platform: Platform name
            discount_percent: Discount percentage
        
        Returns:
            Success status
        """
        try:
            logger.info(f"Adding price history for {product_id}: {price}")
            
            history_doc = {
                'product_id': product_id,
                'price': price,
                'platform': platform,
                'timestamp': datetime.utcnow(),
                'discount_percent': discount_percent
            }
            
            await insert_one('price_history', history_doc)
            return True
        
        except Exception as e:
            logger.error(f"Error adding price history: {e}")
            return False
    
    @staticmethod
    async def get_price_history(
        product_id: str,
        days: int = 30,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get price history for product
        
        Args:
            product_id: Product ID
            days: Number of days to retrieve
            platform: Filter by platform
        
        Returns:
            List of price history entries
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            query = {
                'product_id': product_id,
                'timestamp': {'$gte': since_date}
            }
            
            if platform:
                query['platform'] = platform
            
            history = await find_many(
                'price_history',
                query,
                limit=1000,
                sort=[('timestamp', 1)]
            )
            
            return history or []
        
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []
    
    @staticmethod
    async def get_price_statistics(
        product_id: str,
        days: int = 30
    ) -> Dict[str, float]:
        """
        Get price statistics for product
        
        Args:
            product_id: Product ID
            days: Number of days
        
        Returns:
            Statistics dictionary
        """
        try:
            history = await PriceService.get_price_history(product_id, days)
            
            if not history:
                return {
                    'average_price': 0,
                    'lowest_price': 0,
                    'highest_price': 0,
                    'median_price': 0,
                    'std_dev': 0,
                    'price_trend': 'stable'
                }
            
            prices = [h['price'] for h in history]
            
            avg_price = statistics.mean(prices)
            lowest_price = min(prices)
            highest_price = max(prices)
            median_price = statistics.median(prices)
            std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
            
            # Determine trend
            if len(prices) >= 2:
                recent = statistics.mean(prices[-5:]) if len(prices) >= 5 else prices[-1]
                old = statistics.mean(prices[:5]) if len(prices) >= 5 else prices[0]
                
                if recent < old * 0.95:
                    price_trend = 'down'
                elif recent > old * 1.05:
                    price_trend = 'up'
                else:
                    price_trend = 'stable'
            else:
                price_trend = 'stable'
            
            return {
                'average_price': round(avg_price, 2),
                'lowest_price': round(lowest_price, 2),
                'highest_price': round(highest_price, 2),
                'median_price': round(median_price, 2),
                'std_dev': round(std_dev, 2),
                'price_trend': price_trend,
                'data_points': len(prices)
            }
        
        except Exception as e:
            logger.error(f"Error calculating price statistics: {e}")
            return {}
    
    @staticmethod
    async def create_price_alert(
        user_id: str,
        product_id: str,
        threshold: float,
        current_price: float
    ) -> Optional[str]:
        """
        Create price alert
        
        Args:
            user_id: User ID
            product_id: Product ID
            threshold: Price drop threshold (percentage)
            current_price: Current product price
        
        Returns:
            Alert ID or None
        """
        try:
            logger.info(f"Creating alert for {product_id}: {threshold}% threshold")
            
            alert_doc = {
                'user_id': user_id,
                'product_id': product_id,
                'threshold': threshold,
                'current_price': current_price,
                'alert_price': current_price * (1 - threshold / 100),
                'is_active': True,
                'triggered': False,
                'created_at': datetime.utcnow(),
                'triggered_at': None
            }
            
            alert_id = await insert_one('price_alerts', alert_doc)
            return alert_id
        
        except Exception as e:
            logger.error(f"Error creating price alert: {e}")
            return None
    
    @staticmethod
    async def check_price_alerts(product_id: str, new_price: float) -> List[str]:
        """
        Check and trigger price alerts
        
        Args:
            product_id: Product ID
            new_price: New product price
        
        Returns:
            List of triggered user IDs
        """
        try:
            # Find active alerts for product
            alerts = await find_many(
                'price_alerts',
                {
                    'product_id': product_id,
                    'is_active': True,
                    'triggered': False
                }
            )
            
            triggered_users = []
            
            for alert in alerts:
                # Check if price drops below alert price
                if new_price <= alert['alert_price']:
                    # Trigger alert
                    await update_one(
                        'price_alerts',
                        {'_id': alert['_id']},
                        {
                            'triggered': True,
                            'triggered_at': datetime.utcnow(),
                            'triggered_price': new_price
                        }
                    )
                    
                    triggered_users.append(alert['user_id'])
                    logger.info(f"Alert triggered for user {alert['user_id']}")
            
            return triggered_users
        
        except Exception as e:
            logger.error(f"Error checking price alerts: {e}")
            return []
    
    @staticmethod
    async def compare_prices(product_name: str) -> Dict[str, Any]:
        """
        Compare prices across platforms
        
        Args:
            product_name: Product name
        
        Returns:
            Comparison data
        """
        try:
            logger.info(f"Comparing prices for {product_name}")
            
            # Find products with same name on different platforms
            products = await find_many(
                'products',
                {'product_name': {'$regex': product_name, '$options': 'i'}},
                limit=100
            )
            
            # Group by platform
            by_platform = {}
            for product in products:
                platform = product.get('platform', 'unknown')
                if platform not in by_platform:
                    by_platform[platform] = []
                by_platform[platform].append(product)
            
            # Find best deal
            all_prices = [(p.get('current_price', 0), p.get('platform', '')) for p in products]
            best_price, best_platform = min(all_prices, key=lambda x: x[0]) if all_prices else (0, '')
            
            return {
                'product_name': product_name,
                'by_platform': by_platform,
                'best_price': best_price,
                'best_platform': best_platform,
                'price_difference': max([p[0] for p in all_prices]) - min([p[0] for p in all_prices]) if all_prices else 0
            }
        
        except Exception as e:
            logger.error(f"Error comparing prices: {e}")
            return {}
    
    @staticmethod
    async def get_best_time_to_buy(product_id: str) -> Dict[str, Any]:
        """
        Analyze and recommend best time to buy
        
        Args:
            product_id: Product ID
        
        Returns:
            Recommendation data
        """
        try:
            stats = await PriceService.get_price_statistics(product_id, days=90)
            
            if not stats:
                return {'recommendation': 'insufficient_data'}
            
            avg_price = stats.get('average_price', 0)
            current_price = stats.get('lowest_price', 0)  # Assuming latest is lowest
            
            # Calculate discount percentage
            if avg_price > 0:
                discount_pct = ((avg_price - current_price) / avg_price) * 100
            else:
                discount_pct = 0
            
            # Recommendation logic
            if discount_pct > 20:
                recommendation = 'buy_now'
                reason = f'Price is {discount_pct:.1f}% below average'
            elif stats['price_trend'] == 'down':
                recommendation = 'wait'
                reason = 'Price trend is downward'
            elif discount_pct > 10:
                recommendation = 'buy_now'
                reason = 'Good discount available'
            else:
                recommendation = 'wait'
                reason = 'Price near average, wait for festival'
            
            return {
                'recommendation': recommendation,
                'reason': reason,
                'current_price': current_price,
                'average_price': avg_price,
                'discount_percent': round(discount_pct, 1),
                'trend': stats['price_trend']
            }
        
        except Exception as e:
            logger.error(f"Error analyzing best time: {e}")
            return {'recommendation': 'error'}

# ============ Global Price Service Instance ============

price_service = PriceService()
