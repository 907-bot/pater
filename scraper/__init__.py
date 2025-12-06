# backend/scrapers/__init__.py - Platform-specific scrapers module

"""
Scrapers module for Pater FastAPI backend

This module contains platform-specific web scrapers for e-commerce sites.
"""

from .base_scraper import BaseScraper
from .amazon_scraper import AmazonScraper
from .flipkart_scraper import FlipkartScraper
from .myntra_scraper import MyntraScraper

__all__ = [
    "BaseScraper",
    "AmazonScraper",
    "FlipkartScraper",
    "MyntraScraper"
]
