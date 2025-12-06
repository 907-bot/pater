# api/auth.py - Authentication and authorization

import logging
from datetime import datetime, timedelta
from typing import Optional
from functools import lru_cache

from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
import jwt
from config import settings

logger = logging.getLogger(__name__)

# ============ Security Schemes ============

security = HTTPBearer(auto_error=False)

# ============ Token Models ============

class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    email: str
    exp: datetime
    iat: datetime

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class User(BaseModel):
    """User model"""
    user_id: str
    email: str
    name: Optional[str] = None
    created_at: Optional[str] = None
    is_active: bool = True

# ============ JWT Helpers ============

def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> Token:
    """
    Create JWT access token
    
    Args:
        user_id: User ID
        email: User email
        expires_delta: Token expiration time
    
    Returns:
        Token object with access_token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default: 7 days
        expire = datetime.utcnow() + timedelta(days=7)
    
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    try:
        encoded_jwt = jwt.encode(
            payload,
            settings.secret_key,
            algorithm="HS256"
        )
        
        expires_in = int((expire - datetime.utcnow()).total_seconds())
        
        return Token(
            access_token=encoded_jwt,
            expires_in=expires_in
        )
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create token"
        )

def verify_token(token: str) -> TokenData:
    """
    Verify JWT token and extract data
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData with user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )
        
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        exp: int = payload.get("exp")
        iat: int = payload.get("iat")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )
        
        return TokenData(
            user_id=user_id,
            email=email,
            exp=datetime.fromtimestamp(exp),
            iat=datetime.fromtimestamp(iat)
        )
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token verification failed"
        )

# ============ Dependency Functions ============

async def get_current_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(security)
) -> TokenData:
    """
    Get current authenticated user
    
    Dependency for protected routes
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        TokenData of authenticated user
    
    Raises:
        HTTPException: If not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    return verify_token(credentials.credentials)

async def get_current_user_id(
    current_user: TokenData = Depends(get_current_user)
) -> str:
    """Get current user ID"""
    return current_user.user_id

async def get_current_user_email(
    current_user: TokenData = Depends(get_current_user)
) -> str:
    """Get current user email"""
    return current_user.email

# ============ Optional Authentication ============

async def get_optional_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(security)
) -> Optional[TokenData]:
    """
    Get current user (optional)
    
    Returns None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return None

# ============ API Key Authentication ============

async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> str:
    """
    Verify API key from header
    
    Args:
        x_api_key: API key from X-API-Key header
    
    Returns:
        API key if valid
    
    Raises:
        HTTPException: If API key is invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    
    # Mock verification (replace with database lookup)
    valid_keys = [
        "pater-key-12345",
        "pater-key-67890"
    ]
    
    if x_api_key not in valid_keys:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return x_api_key

# ============ Rate Limiting ============

class RateLimitData(BaseModel):
    """Rate limit information"""
    remaining: int
    reset_at: str
    limit: int

@lru_cache(maxsize=1000)
def check_rate_limit(user_id: str) -> RateLimitData:
    """
    Check rate limit for user
    
    Mock implementation - replace with Redis in production
    """
    return RateLimitData(
        remaining=100,
        reset_at=datetime.utcnow().isoformat(),
        limit=100
    )

async def rate_limit_check(
    current_user: TokenData = Depends(get_current_user)
) -> RateLimitData:
    """
    Check rate limit dependency
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    limit_data = check_rate_limit(current_user.user_id)
    
    if limit_data.remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    return limit_data

# ============ Permission Checks ============

async def require_admin(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Require admin user
    
    Raises:
        HTTPException: If user is not admin
    """
    # Mock check - replace with database lookup
    admin_users = ["admin@pater.ai"]
    
    if current_user.email not in admin_users:
        logger.warning(f"Admin access denied for: {current_user.email}")
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return current_user

async def require_premium(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Require premium user
    
    Raises:
        HTTPException: If user is not premium
    """
    # Mock check - replace with database lookup
    return current_user

# ============ Encryption Helpers ============

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Plain text password
        hashed: Hashed password from database
    
    Returns:
        True if password matches
    """
    import bcrypt
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ============ Session Management ============

class Session(BaseModel):
    """User session"""
    session_id: str
    user_id: str
    created_at: str
    expires_at: str
    device: Optional[str] = None
    ip_address: Optional[str] = None

def create_session(
    user_id: str,
    device: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Session:
    """Create new user session"""
    from uuid import uuid4
    
    session_id = str(uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(days=30)
    
    return Session(
        session_id=session_id,
        user_id=user_id,
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        device=device,
        ip_address=ip_address
    )

def invalidate_session(session_id: str) -> bool:
    """Invalidate a session"""
    # Mock implementation - replace with database
    logger.info(f"Session invalidated: {session_id}")
    return True
