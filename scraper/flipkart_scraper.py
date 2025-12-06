# backend/scrapers/flipkart_scraper.py - Flipkart-specific scraper

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import re

from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# ============ Flipkart Scraper ============

class FlipkartScraper(BaseScraper):
    """Flipkart product scraper"""
    
    def __init__(self):
        """Initialize Flipkart scraper"""
        super().__init__(platform_name='flipkart')
        self.base_url = 'https://www.flipkart.com'
    
    async def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape Flipkart product
        
        Args:
            url: Product URL
        
        Returns:
            Product data or None
        """
        try:
            logger.info(f"Scraping Flipkart product: {url}")
            
            html = await self.fetch_html(url)
            if not html:
                return None
            
            soup = self.parse_html(html)
            product = self.parse_product(soup)
            
            if self.validate_product_data(product):
                product['platform'] = 'flipkart'
                product['scraped_at'] = datetime.utcnow().isoformat()
                logger.info(f"✅ Successfully scraped: {product['product_name']}")
                return product
            
            return None
        
        except Exception as e:
            logger.error(f"Flipkart scraping error: {e}")
            return None
    
    def parse_product(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse Flipkart product page
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Product data
        """
        try:
            # Product ID
            product_id = self._extract_product_id_from_soup(soup)
            
            # Product name
            title_elem = soup.select_one('h1._4LOVkT')
            product_name = self._safe_extract(title_elem, 'text')
            
            # Price
            price_elem = soup.select_one('._30jeq3._16Jk6d')
            current_price = self._extract_price(self._safe_extract(price_elem, 'text'))
            
            # Original price
            original_elem = soup.select_one('._3qQ9m1')
            original_price = self._extract_price(self._safe_extract(original_elem, 'text'))
            
            # Discount
            discount_elem = soup.select_one('._3Ay6Sb')
            discount_percent = self._extract_discount(self._safe_extract(discount_elem, 'text'))
            
            # Rating
            rating_elem = soup.select_one('._3LWZlK')
            rating = self._extract_rating(self._safe_extract(rating_elem, 'text'))
            
            # Review count
            review_elem = soup.select_one('._2_R_DZ')
            review_count = self._extract_count(self._safe_extract(review_elem, 'text'))
            
            # Availability
            availability_elem = soup.select_one('._1z4O39 ._3qQ9m1')
            availability = self._safe_extract(availability_elem, 'text', 'In Stock')
            
            # Image
            image_elem = soup.select_one('._396cs4')
            image_url = self._safe_extract(image_elem, 'src')
            
            # Description
            description_elem = soup.select_one('.xwzEKc')
            description = self._safe_extract(description_elem, 'text')
            
            return {
                'product_id': product_id,
                'product_name': product_name,
                'current_price': current_price,
                'original_price': original_price,
                'discount_percent': discount_percent,
                'rating': rating,
                'review_count': review_count,
                'availability': availability,
                'image_url': image_url,
                'description': description,
                'platform': 'flipkart'
            }
        
        except Exception as e:
            logger.error(f"Flipkart parsing error: {e}")
            return {}
    
    async def scrape_search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search for products on Flipkart
        
        Args:
            query: Search query
            page: Page number
        
        Returns:
            List of products
        """
        try:
            logger.info(f"Searching Flipkart for: {query} (page {page})")
            
            search_url = f"{self.base_url}/search?q={query}&page={page}"
            html = await self.fetch_html(search_url)
            
            if not html:
                return []
            
            soup = self.parse_html(html)
            products = []
            
            # Extract product listings
            items = soup.select('._1xHGtK._373qXS')
            
            for item in items:
                try:
                    product = self._parse_search_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Error parsing search item: {e}")
                    continue
            
            logger.info(f"Found {len(products)} products on page {page}")
            return products
        
        except Exception as e:
            logger.error(f"Flipkart search error: {e}")
            return []
    
    def _parse_search_item(self, item: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse search result item"""
        try:
            # Product name
            name_elem = item.select_one('._1G6VN2._3qQ9m1')
            product_name = self._safe_extract(name_elem, 'text')
            
            if not product_name:
                return None
            
            # Price
            price_elem = item.select_one('._30jeq3._16Jk6d')
            current_price = self._extract_price(self._safe_extract(price_elem, 'text'))
            
            # Rating
            rating_elem = item.select_one('._3LWZlK')
            rating = self._extract_rating(self._safe_extract(rating_elem, 'text'))
            
            # Link
            link_elem = item.select_one('a._1fGeY5')
            product_url = self._safe_extract(link_elem, 'href')
            
            # Extract product ID from URL
            product_id = re.search(r'/p/([A-Z0-9]+)', product_url)
            product_id = product_id.group(1) if product_id else 'unknown'
            
            return {
                'product_id': product_id,
                'product_name': product_name,
                'current_price': current_price,
                'rating': rating,
                'platform': 'flipkart',
                'product_url': product_url
            }
        
        except Exception as e:
            logger.debug(f"Error parsing search item: {e}")
            return None
    
    def extract_product_id(self, url: str) -> str:
        """
        Extract product ID from Flipkart URL
        
        Args:
            url: Product URL
        
        Returns:
            Product ID
        """
        match = re.search(r'/p/([A-Z0-9]+)', url)
        return match.group(1) if match else 'unknown'
    
    def _extract_product_id_from_soup(self, soup: BeautifulSoup) -> str:
        """Extract product ID from soup"""
        try:
            # Find product ID in URL
            link = soup.select_one('link[rel="canonical"]')
            if link:
                url = link.get('href', '')
                return self.extract_product_id(url)
        except:
            pass
        return 'unknown'
    
    def _extract_discount(self, discount_str: str) -> float:
        """Extract discount percentage"""
        try:
            match = re.search(r'(\d+)%', discount_str)
            return float(match.group(1)) if match else 0.0
        except:
            return 0.0
    
    def _extract_count(self, count_str: str) -> int:
        """Extract count from string"""
        try:
            count = re.search(r'(\d+)', count_str.replace(',', ''))
            return int(count.group(1)) if count else 0
        except:
            return 0

# ============ Global Flipkart Scraper Instance ============

flipkart_scraper = FlipkartScraper()
