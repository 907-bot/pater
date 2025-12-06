# api/__init__.py - API module initialization

"""
API module for Pater FastAPI backend

This module contains all API routes and middleware for the Pater application.
"""

from .routes import router as api_router

__all__ = ["api_router"]
