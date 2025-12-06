# backend/models/__init__.py - Models module initialization

"""
Models module for Pater FastAPI backend

This module contains database models, schemas, and data structures.
"""

from .schemas import (
    ProductData,
    PredictionResponse,
    WatchlistItem,
    PriceAlert,
    Festival,
    UserSchema,
    TokenSchema
)

from .database import (
    get_mongodb_client,
    get_mongodb_db,
    get_redis_client,
    close_mongodb,
    close_redis
)

__all__ = [
    # Schemas
    "ProductData",
    "PredictionResponse",
    "WatchlistItem",
    "PriceAlert",
    "Festival",
    "UserSchema",
    "TokenSchema",
    # Database
    "get_mongodb_client",
    "get_mongodb_db",
    "get_redis_client",
    "close_mongodb",
    "close_redis"
]
