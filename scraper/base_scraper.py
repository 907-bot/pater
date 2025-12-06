# backend/scrapers/base_scraper.py - Abstract base scraper class

import logging
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup

from config import settings

logger = logging.getLogger(__name__)

# ============ Base Scraper ============

class BaseScraper(ABC):
    """Abstract base class for platform-specific scrapers"""
    
    def __init__(
        self,
        platform_name: str,
        timeout: int = 10,
        max_retries: int = 3
    ):
        """
        Initialize base scraper
        
        Args:
            platform_name: Name of platform (amazon, flipkart, myntra)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.platform_name = platform_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = self._get_default_headers()
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default request headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': f'https://{self.platform_name}.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL with retry logic
        
        Args:
            url: URL to fetch
        
        Returns:
            HTML content or None
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1}/{self.max_retries})")
                
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
                logger.warning(f"Timeout (attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"Fetch error (attempt {attempt + 1}): {e}")
            
            # Wait before retry with exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content
        
        Args:
            html: HTML content
        
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'html.parser')
    
    @abstractmethod
    async def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape product information from URL
        
        Args:
            url: Product URL
        
        Returns:
            Product data dictionary
        """
        pass
    
    @abstractmethod
    async def scrape_search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search for products
        
        Args:
            query: Search query
            page: Page number
        
        Returns:
            List of product results
        """
        pass
    
    @abstractmethod
    def extract_product_id(self, url: str) -> str:
        """
        Extract product ID from URL
        
        Args:
            url: Product URL
        
        Returns:
            Product ID
        """
        pass
    
    @abstractmethod
    def parse_product(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse product data from soup
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Product data
        """
        pass
    
    def _safe_extract(
        self,
        element: Optional[Any],
        attr: str = 'text',
        default: str = ''
    ) -> str:
        """
        Safely extract element value
        
        Args:
            element: BeautifulSoup element
            attr: Attribute to extract
            default: Default value if extraction fails
        
        Returns:
            Extracted value
        """
        try:
            if element is None:
                return default
            
            if attr == 'text':
                return element.get_text(strip=True)
            else:
                return element.get(attr, default) or default
        
        except Exception as e:
            logger.debug(f"Extraction error: {e}")
            return default
    
    def _extract_price(self, price_str: str) -> float:
        """
        Extract price from string
        
        Args:
            price_str: Price string
        
        Returns:
            Price as float
        """
        try:
            # Remove common currency symbols and separators
            price_str = re.sub(r'[^0-9.]', '', price_str)
            # Handle Indian numbers (commas)
            price_str = price_str.replace(',', '')
            return float(price_str) if price_str else 0.0
        except Exception as e:
            logger.debug(f"Price extraction error: {e}")
            return 0.0
    
    def _extract_rating(self, rating_str: str) -> float:
        """
        Extract rating from string
        
        Args:
            rating_str: Rating string
        
        Returns:
            Rating as float (0-5)
        """
        try:
            rating = re.search(r'(\d+\.?\d*)', rating_str)
            if rating:
                rating_val = float(rating.group(1))
                return min(rating_val, 5.0)  # Cap at 5
            return 0.0
        except Exception as e:
            logger.debug(f"Rating extraction error: {e}")
            return 0.0
    
    async def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple products concurrently
        
        Args:
            urls: List of product URLs
        
        Returns:
            List of product data
        """
        try:
            logger.info(f"Scraping {len(urls)} products from {self.platform_name}")
            
            tasks = [self.scrape_product(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None and exceptions
            products = [r for r in results if r is not None and not isinstance(r, Exception)]
            
            logger.info(f"Successfully scraped {len(products)}/{len(urls)} products")
            return products
        
        except Exception as e:
            logger.error(f"Multiple scrape error: {e}")
            return []
    
    def validate_product_data(self, product: Dict[str, Any]) -> bool:
        """
        Validate product data
        
        Args:
            product: Product dictionary
        
        Returns:
            True if valid
        """
        required_fields = ['product_name', 'current_price', 'platform']
        return all(field in product and product[field] for field in required_fields)
