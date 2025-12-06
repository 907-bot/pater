# backend/scrapers/amazon_scraper.py - Amazon-specific scraper

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import re

from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# ============ Amazon Scraper ============

class AmazonScraper(BaseScraper):
    """Amazon product scraper"""
    
    def __init__(self):
        """Initialize Amazon scraper"""
        super().__init__(platform_name='amazon')
        self.base_url = 'https://www.amazon.in'
    
    async def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape Amazon product
        
        Args:
            url: Product URL
        
        Returns:
            Product data or None
        """
        try:
            logger.info(f"Scraping Amazon product: {url}")
            
            html = await self.fetch_html(url)
            if not html:
                return None
            
            soup = self.parse_html(html)
            product = self.parse_product(soup)
            
            if self.validate_product_data(product):
                product['platform'] = 'amazon'
                product['scraped_at'] = datetime.utcnow().isoformat()
                logger.info(f"✅ Successfully scraped: {product['product_name']}")
                return product
            
            return None
        
        except Exception as e:
            logger.error(f"Amazon scraping error: {e}")
            return None
    
    def parse_product(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse Amazon product page
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Product data
        """
        try:
            # Extract product ID (ASIN)
            asin = self._extract_asin_from_soup(soup)
            
            # Product name
            title_elem = soup.select_one('h1 span')
            product_name = self._safe_extract(title_elem, 'text')
            
            # Price
            price_elem = soup.select_one('.a-price-whole')
            current_price = self._extract_price(self._safe_extract(price_elem, 'text'))
            
            # Rating
            rating_elem = soup.select_one('[data-a-icon-star] span')
            rating = self._extract_rating(self._safe_extract(rating_elem, 'text'))
            
            # Review count
            review_elem = soup.select_one('[data-hook="total-review-count"]')
            review_count = self._extract_count(self._safe_extract(review_elem, 'text'))
            
            # Availability
            availability_elem = soup.select_one('.availability span')
            availability = self._safe_extract(availability_elem, 'text', 'Unknown')
            
            # Images
            image_elem = soup.select_one('img.a-dynamic-image')
            image_url = self._safe_extract(image_elem, 'src')
            
            # Discount (if available)
            discount_elem = soup.select_one('.a-price-fraction')
            discount_percent = 0.0
            
            # Product description
            description_elem = soup.select_one('div[data-feature-name="title"]')
            description = self._safe_extract(description_elem, 'text')
            
            return {
                'product_id': asin,
                'product_name': product_name,
                'current_price': current_price,
                'rating': rating,
                'review_count': review_count,
                'availability': availability,
                'image_url': image_url,
                'discount_percent': discount_percent,
                'description': description,
                'product_url': '',  # Would be extracted from context
                'platform': 'amazon'
            }
        
        except Exception as e:
            logger.error(f"Amazon parsing error: {e}")
            return {}
    
    async def scrape_search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon
        
        Args:
            query: Search query
            page: Page number
        
        Returns:
            List of products
        """
        try:
            logger.info(f"Searching Amazon for: {query} (page {page})")
            
            search_url = f"{self.base_url}/s?k={query}&page={page}"
            html = await self.fetch_html(search_url)
            
            if not html:
                return []
            
            soup = self.parse_html(html)
            products = []
            
            # Extract product listings
            items = soup.select('[data-component-type="s-search-result"]')
            
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
            logger.error(f"Amazon search error: {e}")
            return []
    
    def _parse_search_item(self, item: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse search result item"""
        try:
            # Product name
            name_elem = item.select_one('h2 a span')
            product_name = self._safe_extract(name_elem, 'text')
            
            if not product_name:
                return None
            
            # Price
            price_elem = item.select_one('.a-price-whole')
            current_price = self._extract_price(self._safe_extract(price_elem, 'text'))
            
            # Rating
            rating_elem = item.select_one('[data-a-icon-star] span')
            rating = self._extract_rating(self._safe_extract(rating_elem, 'text'))
            
            # Link
            link_elem = item.select_one('h2 a')
            product_url = self._safe_extract(link_elem, 'href')
            
            # Extract ASIN from URL
            product_id = re.search(r'/dp/([A-Z0-9]{10})', product_url)
            product_id = product_id.group(1) if product_id else 'unknown'
            
            return {
                'product_id': product_id,
                'product_name': product_name,
                'current_price': current_price,
                'rating': rating,
                'platform': 'amazon',
                'product_url': product_url
            }
        
        except Exception as e:
            logger.debug(f"Error parsing search item: {e}")
            return None
    
    def extract_product_id(self, url: str) -> str:
        """
        Extract ASIN from Amazon URL
        
        Args:
            url: Product URL
        
        Returns:
            ASIN or 'unknown'
        """
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return match.group(1) if match else 'unknown'
    
    def _extract_asin_from_soup(self, soup: BeautifulSoup) -> str:
        """Extract ASIN from soup"""
        # Try to find ASIN in various ways
        asin_elem = soup.select_one('[data-asin]')
        if asin_elem:
            return asin_elem.get('data-asin', 'unknown')
        return 'unknown'
    
    def _extract_count(self, count_str: str) -> int:
        """Extract count from string"""
        try:
            count = re.search(r'(\d+)', count_str.replace(',', ''))
            return int(count.group(1)) if count else 0
        except:
            return 0

# ============ Global Amazon Scraper Instance ============

amazon_scraper = AmazonScraper()
