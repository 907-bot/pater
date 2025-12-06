# backend/db/neo4j_client.py - Neo4j connection manager

import logging
from typing import Optional, List, Dict, Any
from neo4j import AsyncDriver, asyncio as neo4j_asyncio

from config import settings

logger = logging.getLogger(__name__)

# ============ Global Neo4j Instance ============

_neo4j_driver: Optional[AsyncDriver] = None

# ============ Neo4j Client ============

class Neo4jClient:
    """Neo4j async client wrapper for relationship graphs"""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Neo4j client
        
        Args:
            uri: Neo4j connection URI
            username: Username
            password: Password
        """
        self.uri = uri or settings.neo4j_url
        self.username = username or settings.neo4j_username
        self.password = password or settings.neo4j_password
        self.driver: Optional[AsyncDriver] = None
    
    async def connect(self) -> AsyncDriver:
        """
        Connect to Neo4j
        
        Returns:
            Driver instance
        """
        try:
            logger.info(f"Connecting to Neo4j: {self.uri}")
            
            self.driver = neo4j_asyncio.AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            
            # Test connection
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            
            logger.info("✅ Connected to Neo4j")
            return self.driver
        
        except Exception as e:
            logger.error(f"❌ Neo4j connection error: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Neo4j"""
        try:
            if self.driver:
                logger.info("Closing Neo4j connection...")
                await self.driver.close()
                logger.info("✅ Neo4j disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Neo4j: {e}")
    
    async def create_constraints(self) -> None:
        """Create graph constraints and indexes"""
        try:
            if not self.driver:
                return
            
            logger.info("Creating Neo4j constraints...")
            
            async with self.driver.session() as session:
                # Product constraints
                await session.run(
                    "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE"
                )
                
                # User constraints
                await session.run(
                    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE"
                )
                
                # Indexes
                await session.run(
                    "CREATE INDEX product_platform IF NOT EXISTS FOR (p:Product) ON (p.platform)"
                )
                
                await session.run(
                    "CREATE INDEX product_category IF NOT EXISTS FOR (p:Product) ON (p.category)"
                )
            
            logger.info("✅ Neo4j constraints created")
        
        except Exception as e:
            logger.error(f"Error creating constraints: {e}")
    
    async def health_check(self) -> bool:
        """Check Neo4j health"""
        try:
            if self.driver:
                async with self.driver.session() as session:
                    await session.run("RETURN 1")
                return True
            return False
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False

# ============ Global Functions ============

async def init_neo4j(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> AsyncDriver:
    """Initialize Neo4j"""
    global _neo4j_driver
    
    client = Neo4jClient(uri, username, password)
    _neo4j_driver = await client.connect()
    await client.create_constraints()
    
    return _neo4j_driver

async def close_neo4j() -> None:
    """Close Neo4j connection"""
    global _neo4j_driver
    if _neo4j_driver:
        await _neo4j_driver.close()

def get_neo4j_driver() -> AsyncDriver:
    """Get Neo4j driver instance"""
    global _neo4j_driver
    if _neo4j_driver is None:
        raise RuntimeError("Neo4j not initialized - call init_neo4j() first")
    return _neo4j_driver
