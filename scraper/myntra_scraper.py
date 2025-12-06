# backend/scrapers/myntra_scraper.py - Myntra-specific scraper

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import re

from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# ============ Myntra Scraper ============

class MyntraScraper(BaseScraper):
    """Myntra product scraper"""
    
    def __init__(self):
        """Initialize Myntra scraper"""
        super().__init__(platform_name='myntra')
        self.base_url = 'https://www.myntra.com'
    
    async def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape Myntra product
        
        Args:
            url: Product URL
        
        Returns:
            Product data or None
        """
        try:
            logger.info(f"Scraping Myntra product: {url}")
            
            html = await self.fetch_html(url)
            if not html:
                return None
            
            soup = self.parse_html(html)
            product = self.parse_product(soup)
            
            if self.validate_product_data(product):
                product['platform'] = 'myntra'
                product['scraped_at'] = datetime.utcnow().isoformat()
                logger.info(f"✅ Successfully scraped: {product['product_name']}")
                return product
            
            return None
        
        except Exception as e:
            logger.error(f"Myntra scraping error: {e}")
            return None
    
    def parse_product(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse Myntra product page
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Product data
        """
        try:
            # Product ID
            product_id = self._extract_product_id_from_soup(soup)
            
            # Product name
            title_elem = soup.select_one('h1.productTitle')
            product_name = self._safe_extract(title_elem, 'text')
            
            # Price
            price_elem = soup.select_one('span.discountedPriceText')
            current_price = self._extract_price(self._safe_extract(price_elem, 'text'))
            
            # Original price
            original_elem = soup.select_one('span.originalPriceText')
            original_price = self._extract_price(self._safe_extract(original_elem, 'text'))
            
            # Discount
            discount_elem = soup.select_one('span.discountBadge')
            discount_percent = self._extract_discount(self._safe_extract(discount_elem, 'text'))
            
            # Rating
            rating_elem = soup.select_one('span.ratingCount')
            rating = self._extract_rating(self._safe_extract(rating_elem, 'text'))
            
            # Review count
            review_elem = soup.select_one('span.reviewCount')
            review_count = self._extract_count(self._safe_extract(review_elem, 'text'))
            
            # Availability
            availability = 'In Stock'
            availability_elem = soup.select_one('div.sizeSelectionWidget span')
            if availability_elem:
                availability_text = self._safe_extract(availability_elem, 'text')
                if 'out of stock' in availability_text.lower():
                    availability = 'Out of Stock'
            
            # Image
            image_elem = soup.select_one('img.productPageImg')
            image_url = self._safe_extract(image_elem, 'src')
            
            # Brand
            brand_elem = soup.select_one('h2.productBrand')
            brand = self._safe_extract(brand_elem, 'text')
            
            # Description
            description_elem = soup.select_one('.productDescription p')
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
                'brand': brand,
                'description': description,
                'platform': 'myntra'
            }
        
        except Exception as e:
            logger.error(f"Myntra parsing error: {e}")
            return {}
    
    async def scrape_search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search for products on Myntra
        
        Args:
            query: Search query
            page: Page number
        
        Returns:
            List of products
        """
        try:
            logger.info(f"Searching Myntra for: {query} (page {page})")
            
            # Myntra uses JavaScript for search, so mock implementation
            logger.warning("Myntra search requires JavaScript rendering - returning empty results")
            return []
        
        except Exception as e:
            logger.error(f"Myntra search error: {e}")
            return []
    
    def extract_product_id(self, url: str) -> str:
        """
        Extract product ID from Myntra URL
        
        Args:
            url: Product URL
        
        Returns:
            Product ID
        """
        # Myntra URLs: https://www.myntra.com/shirts/product-id
        match = re.search(r'/([0-9]+)(?:\?|$)', url)
        return match.group(1) if match else 'unknown'
    
    def _extract_product_id_from_soup(self, soup: BeautifulSoup) -> str:
        """Extract product ID from soup"""
        try:
            # Look for product ID in script tags
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if 'productId' in script.string:
                    match = re.search(r'"productId":\s*"?(\d+)"?', script.string)
                    if match:
                        return match.group(1)
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

# ============ Global Myntra Scraper Instance ============

myntra_scraper = MyntraScraper()
