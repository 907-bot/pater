# backend/db/__init__.py - Database utilities module initialization

"""
Database utilities module for Pater FastAPI backend

This module contains database connection managers and utilities.
"""

from .mongo_client import MongoClient, get_mongo_db
from .neo4j_client import Neo4jClient, get_neo4j_driver
from .redis_client import RedisClient, get_redis_client
from .schemas import (
    MongoCollections,
    Neo4jLabels,
    RedisKeys,
    DatabaseConfig
)

__all__ = [
    "MongoClient",
    "get_mongo_db",
    "Neo4jClient",
    "get_neo4j_driver",
    "RedisClient",
    "get_redis_client",
    "MongoCollections",
    "Neo4jLabels",
    "RedisKeys",
    "DatabaseConfig"
]
