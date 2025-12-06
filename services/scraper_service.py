# backend/services/scraper_service.py - Web scraping service

import logging
import asyncio
import aiohttp
from typing import Optional, Dict, List, Any
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

from models.database import MongoDBCollections
from config import settings

logger = logging.getLogger(__name__)

# ============ Scraper Service ============

class ScraperService:
    """Web scraping service for e-commerce platforms"""
    
    def __init__(self):
        """Initialize scraper"""
        self.timeout = settings.scraper_timeout
        self.retry_count = settings.scraper_retry_count
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scrape_product(
        self,
        product_url: str,
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape product information from URL
        
        Args:
            product_url: Product page URL
            platform: Platform name (amazon, flipkart, myntra)
        
        Returns:
            Product data dictionary
        """
        try:
            logger.info(f"Scraping {platform} product: {product_url}")
            
            # Determine scraper based on platform
            if platform.lower() == "amazon":
                return await self._scrape_amazon(product_url)
            elif platform.lower() == "flipkart":
                return await self._scrape_flipkart(product_url)
            elif platform.lower() == "myntra":
                return await self._scrape_myntra(product_url)
            else:
                logger.warning(f"Unknown platform: {platform}")
                return None
        
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return None
    
    async def _scrape_amazon(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape Amazon product"""
        try:
            html = await self._fetch_html(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract product information
            title = soup.select_one('h1 span')
            price = soup.select_one('.a-price-whole')
            rating = soup.select_one('.a-icon-star span')
            availability = soup.select_one('.availability span')
            image = soup.select_one('img.a-dynamic-image')
            
            product_id = self._extract_asin_from_url(url)
            
            return {
                'product_id': product_id,
                'product_name': title.text.strip() if title else None,
                'current_price': float(price.text.replace('₹', '').replace(',', '')) if price else 0,
                'platform': 'amazon',
                'rating': float(rating.text.split()[0]) if rating else None,
                'availability': availability.text.strip() if availability else 'Unknown',
                'image_url': image.get('src') if image else None,
                'product_url': url,
                'scraped_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Amazon scraping error: {e}")
            return None
    
    async def _scrape_flipkart(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape Flipkart product"""
        try:
            html = await self._fetch_html(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract product information
            title = soup.select_one('h1._4LOVkT')
            price = soup.select_one('._30jeq3._16Jk6d')
            rating = soup.select_one('._3LWZlK')
            reviews = soup.select_one('._2_R_DZ')
            
            product_id = self._extract_product_id_from_url(url)
            
            return {
                'product_id': product_id,
                'product_name': title.text.strip() if title else None,
                'current_price': float(price.text.replace('₹', '').replace(',', '')) if price else 0,
                'platform': 'flipkart',
                'rating': float(rating.text) if rating else None,
                'reviews_count': int(reviews.text.split()[0]) if reviews else 0,
                'product_url': url,
                'scraped_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Flipkart scraping error: {e}")
            return None
    
    async def _scrape_myntra(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape Myntra product"""
        try:
            html = await self._fetch_html(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract product information
            title = soup.select_one('h1.productTitle')
            price = soup.select_one('span.discountedPriceText')
            original_price = soup.select_one('span.originalPriceText')
            discount = soup.select_one('span.discountBadge')
            rating = soup.select_one('span.ratingCount')
            
            product_id = self._extract_product_id_from_url(url)
            
            return {
                'product_id': product_id,
                'product_name': title.text.strip() if title else None,
                'current_price': float(price.text.replace('₹', '').replace(',', '')) if price else 0,
                'original_price': float(original_price.text.replace('₹', '').replace(',', '')) if original_price else 0,
                'discount_percent': int(discount.text.replace('% OFF', '')) if discount else 0,
                'platform': 'myntra',
                'rating': float(rating.text.split()[0]) if rating else None,
                'product_url': url,
                'scraped_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Myntra scraping error: {e}")
            return None
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content with retry logic"""
        for attempt in range(self.retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.warning(f"HTTP {response.status}: {url}")
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout attempt {attempt + 1}/{self.retry_count}: {url}")
            except Exception as e:
                logger.error(f"Fetch error attempt {attempt + 1}/{self.retry_count}: {e}")
            
            # Wait before retry
            if attempt < self.retry_count - 1:
                await asyncio.sleep(2 ** attempt)
        
        return None
    
    @staticmethod
    def _extract_asin_from_url(url: str) -> str:
        """Extract ASIN from Amazon URL"""
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return match.group(1) if match else 'unknown'
    
    @staticmethod
    def _extract_product_id_from_url(url: str) -> str:
        """Extract product ID from URL"""
        parts = url.split('/')
        return parts[-1].split('?')[0] if parts else 'unknown'
    
    async def scrape_festival_deals(
        self,
        platform: str,
        festival_name: str
    ) -> List[Dict[str, Any]]:
        """
        Scrape festival deals for a platform
        
        Args:
            platform: Platform name
            festival_name: Festival name
        
        Returns:
            List of products with special pricing
        """
        try:
            logger.info(f"Scraping {festival_name} deals on {platform}")
            
            # Mock implementation - replace with actual scraping
            deals = [
                {
                    'product_id': f'deal_{i}',
                    'product_name': f'Product {i}',
                    'current_price': 5000 + (i * 1000),
                    'original_price': 10000 + (i * 1000),
                    'discount_percent': 50 - (i * 5),
                    'platform': platform,
                    'festival': festival_name,
                    'scraped_at': datetime.utcnow().isoformat()
                }
                for i in range(10)
            ]
            
            return deals
        
        except Exception as e:
            logger.error(f"Festival scraping error: {e}")
            return []

# ============ Global Scraper Instance ============

scraper_service = ScraperService()
