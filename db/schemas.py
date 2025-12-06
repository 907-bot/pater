# backend/db/schemas.py - Database schemas and constants

from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass

# ============ Enums ============

class MongoCollections(str, Enum):
    """MongoDB collection names"""
    USERS = "users"
    PRODUCTS = "products"
    WATCHLIST = "watchlist"
    PRICE_HISTORY = "price_history"
    ALERTS = "alerts"
    REVIEWS = "reviews"
    ORDERS = "orders"
    SESSIONS = "sessions"

class Neo4jLabels(str, Enum):
    """Neo4j node labels"""
    USER = "User"
    PRODUCT = "Product"
    CATEGORY = "Category"
    BRAND = "Brand"
    PLATFORM = "Platform"
    REVIEW = "Review"
    ALERT = "Alert"

class Neo4jRelationships(str, Enum):
    """Neo4j relationship types"""
    WATCHES = "WATCHES"
    REVIEWED = "REVIEWED"
    BELONGS_TO = "BELONGS_TO"
    HAS_DISCOUNT = "HAS_DISCOUNT"
    SIMILAR_TO = "SIMILAR_TO"
    RECOMMENDED_BY = "RECOMMENDED_BY"
    PRICE_DROPPED = "PRICE_DROPPED"

class RedisKeys(str, Enum):
    """Redis key patterns"""
    USER_CACHE = "user:{user_id}"
    PRODUCT_CACHE = "product:{product_id}"
    SEARCH_CACHE = "search:{query}:{page}"
    PRICE_CACHE = "price:{product_id}"
    PREDICTION_CACHE = "pred:{product_id}"
    SESSION = "session:{session_id}"
    RATE_LIMIT = "rate:{user_id}:{endpoint}"
    WATCHLIST = "watchlist:{user_id}"

# ============ Data Classes ============

@dataclass
class DatabaseConfig:
    """Database configuration"""
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "pater_db"
    
    # Neo4j
    neo4j_url: str = "neo4j://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Settings
    mongo_pool_size: int = 10
    neo4j_pool_size: int = 50
    redis_pool_size: int = 10

# ============ MongoDB Schemas ============

MONGO_USER_SCHEMA = {
    "bsonType": "object",
    "required": ["user_id", "email", "created_at"],
    "properties": {
        "user_id": {"bsonType": "string"},
        "email": {"bsonType": "string"},
        "name": {"bsonType": "string"},
        "avatar_url": {"bsonType": "string"},
        "bio": {"bsonType": "string"},
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": "date"},
        "is_active": {"bsonType": "bool"}
    }
}

MONGO_PRODUCT_SCHEMA = {
    "bsonType": "object",
    "required": ["product_id", "product_name", "platform"],
    "properties": {
        "product_id": {"bsonType": "string"},
        "product_name": {"bsonType": "string"},
        "platform": {"bsonType": "string"},
        "category": {"bsonType": "string"},
        "brand": {"bsonType": "string"},
        "current_price": {"bsonType": "double"},
        "original_price": {"bsonType": "double"},
        "discount_percent": {"bsonType": "double"},
        "rating": {"bsonType": "double"},
        "review_count": {"bsonType": "int"},
        "availability": {"bsonType": "string"},
        "image_url": {"bsonType": "string"},
        "description": {"bsonType": "string"},
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": "date"}
    }
}

MONGO_WATCHLIST_SCHEMA = {
    "bsonType": "object",
    "required": ["user_id", "product_id"],
    "properties": {
        "user_id": {"bsonType": "string"},
        "product_id": {"bsonType": "string"},
        "added_at": {"bsonType": "date"},
        "last_price": {"bsonType": "double"},
        "notes": {"bsonType": "string"}
    }
}

MONGO_PRICE_HISTORY_SCHEMA = {
    "bsonType": "object",
    "required": ["product_id", "price", "timestamp"],
    "properties": {
        "product_id": {"bsonType": "string"},
        "platform": {"bsonType": "string"},
        "price": {"bsonType": "double"},
        "discount_percent": {"bsonType": "double"},
        "timestamp": {"bsonType": "date"}
    }
}

MONGO_ALERT_SCHEMA = {
    "bsonType": "object",
    "required": ["user_id", "product_id", "target_price"],
    "properties": {
        "user_id": {"bsonType": "string"},
        "product_id": {"bsonType": "string"},
        "target_price": {"bsonType": "double"},
        "alert_type": {"bsonType": "string"},
        "is_active": {"bsonType": "bool"},
        "created_at": {"bsonType": "date"},
        "triggered_at": {"bsonType": "date"}
    }
}

# ============ Neo4j Query Templates ============

NEO4J_QUERIES = {
    "create_user": """
        CREATE (u:User {
            user_id: $user_id,
            email: $email,
            name: $name,
            created_at: datetime()
        })
        RETURN u
    """,
    
    "create_product": """
        CREATE (p:Product {
            product_id: $product_id,
            name: $name,
            platform: $platform,
            category: $category,
            price: $price,
            rating: $rating
        })
        RETURN p
    """,
    
    "create_watches_relationship": """
        MATCH (u:User {user_id: $user_id})
        MATCH (p:Product {product_id: $product_id})
        CREATE (u)-[r:WATCHES {
            added_at: datetime(),
            notes: $notes
        }]->(p)
        RETURN r
    """,
    
    "find_similar_products": """
        MATCH (p:Product {product_id: $product_id})
        MATCH (p)-[r:SIMILAR_TO]-(similar:Product)
        RETURN similar, r
        LIMIT $limit
    """,
    
    "find_user_recommendations": """
        MATCH (u:User {user_id: $user_id})
        MATCH (u)-[w:WATCHES]->(watched:Product)
        MATCH (watched)-[r:SIMILAR_TO]-(recommended:Product)
        WHERE NOT (u)-[:WATCHES]->(recommended)
        RETURN recommended, COUNT(r) as score
        ORDER BY score DESC
        LIMIT $limit
    """
}

# ============ Redis Key Patterns ============

REDIS_PATTERNS = {
    "user_prefix": "user:",
    "product_prefix": "product:",
    "cache_prefix": "cache:",
    "session_prefix": "session:",
    "rate_limit_prefix": "rate:",
    "watchlist_prefix": "watchlist:"
}

# ============ TTL Constants (in seconds) ============

CACHE_TTL = {
    "product": 3600,           # 1 hour
    "user": 1800,              # 30 minutes
    "search": 1800,            # 30 minutes
    "prediction": 1800,        # 30 minutes
    "session": 86400,          # 24 hours
    "rate_limit": 3600,        # 1 hour
    "watchlist": 86400         # 24 hours
}

# ============ Index Definitions ============

MONGO_INDEXES = {
    "users": [
        {"keys": [("email", 1)], "unique": True},
        {"keys": [("user_id", 1)], "unique": True},
        {"keys": [("created_at", 1)]},
    ],
    "products": [
        {"keys": [("product_id", 1)], "unique": True},
        {"keys": [("platform", 1), ("category", 1)]},
        {"keys": [("rating", -1)]},
        {"keys": [("created_at", -1)]},
    ],
    "watchlist": [
        {"keys": [("user_id", 1), ("product_id", 1)], "unique": True},
        {"keys": [("added_at", -1)]},
    ],
    "price_history": [
        {"keys": [("product_id", 1), ("timestamp", -1)]},
        {"keys": [("platform", 1), ("timestamp", -1)]},
    ],
    "alerts": [
        {"keys": [("user_id", 1), ("is_active", 1)]},
        {"keys": [("product_id", 1)]},
    ]
}

NEO4J_INDEXES = {
    "product_id": "CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.product_id)",
    "user_id": "CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.user_id)",
    "product_platform": "CREATE INDEX product_platform IF NOT EXISTS FOR (p:Product) ON (p.platform)",
    "user_email": "CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email)"
}

# ============ Health Check Queries ============

DB_HEALTH_CHECKS = {
    "mongodb": "db.admin.command('ismaster')",
    "neo4j": "RETURN 1",
    "redis": "PING"
}
