# backend/models/schemas.py - Pydantic schemas and data models

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ============ Enums ============

class PlatformEnum(str, Enum):
    """E-commerce platform enum"""
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    MYNTRA = "myntra"

class RecommendationEnum(str, Enum):
    """Purchase recommendation enum"""
    BUY_NOW = "buy_now"
    WAIT = "wait"
    SKIP = "skip"

class UserRoleEnum(str, Enum):
    """User role enum"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"

# ============ Product Schemas ============

class ProductData(BaseModel):
    """Product data model"""
    product_name: str = Field(..., min_length=1, max_length=500)
    current_price: float = Field(..., gt=0)
    platform: PlatformEnum
    category: str = Field(..., min_length=1, max_length=100)
    product_url: Optional[str] = None
    product_id: Optional[str] = None
    
    class Config:
        use_enum_values = True

class ProductInDB(ProductData):
    """Product data in database"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime
    price_history: List[Dict[str, Any]] = []
    lowest_price: float
    highest_price: float
    average_discount: float = 0.0
    
    class Config:
        populate_by_name = True

# ============ Prediction Schemas ============

class PredictionResponse(BaseModel):
    """Prediction response model"""
    product_name: str
    current_price: float
    festival_probability: float = Field(..., ge=0, le=100)
    expected_discount: float = Field(..., ge=0, le=100)
    recommendation: RecommendationEnum
    confidence: float = Field(..., ge=0, le=1)
    predicted_price: Optional[float] = None
    optimal_buy_time: Optional[str] = None
    reason: Optional[str] = None

class PredictionRequest(BaseModel):
    """Prediction request model"""
    product_name: str
    current_price: float
    platform: PlatformEnum
    category: str
    historical_data: Optional[List[Dict[str, Any]]] = None

# ============ Watchlist Schemas ============

class WatchlistItem(BaseModel):
    """Watchlist item model"""
    product_id: str
    product_name: str
    current_price: float
    platform: PlatformEnum
    category: str
    added_at: datetime
    target_price: Optional[float] = None
    alert_threshold: Optional[float] = None  # percentage
    
    class Config:
        use_enum_values = True

class WatchlistItemInDB(WatchlistItem):
    """Watchlist item in database"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    last_price_check: Optional[datetime] = None
    price_drops: int = 0

class WatchlistSyncRequest(BaseModel):
    """Watchlist sync request from extension"""
    products: List[ProductData]
    timestamp: Optional[datetime] = None

class WatchlistSyncResponse(BaseModel):
    """Watchlist sync response"""
    success: bool
    synced_count: int
    message: str
    updated_at: datetime

# ============ Price Schemas ============

class PriceAlert(BaseModel):
    """Price alert model"""
    product_id: str
    threshold: float = Field(..., gt=0, le=100)  # percentage
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool = True

class PriceAlertInDB(PriceAlert):
    """Price alert in database"""
    id: Optional[str] = Field(None, alias="_id")
    triggered: bool = False
    triggered_at: Optional[datetime] = None
    current_price: Optional[float] = None
    alert_price: Optional[float] = None

class PriceHistory(BaseModel):
    """Price history entry"""
    product_id: str
    price: float
    platform: PlatformEnum
    timestamp: datetime
    discount_percent: Optional[float] = None
    
    class Config:
        use_enum_values = True

class PriceHistoryResponse(BaseModel):
    """Price history response"""
    product_id: str
    platform: PlatformEnum
    prices: List[PriceHistory]
    days: int
    average_price: float
    lowest_price: float
    highest_price: float
    price_trend: str  # up, down, stable
    
    class Config:
        use_enum_values = True

# ============ Festival Schemas ============

class Festival(BaseModel):
    """Festival event model"""
    name: str = Field(..., min_length=1, max_length=200)
    start_date: datetime
    end_date: datetime
    discount_range: tuple = Field(..., min_items=2, max_items=2)  # (min, max)
    platform: PlatformEnum
    description: Optional[str] = None
    category_specific_discounts: Optional[Dict[str, tuple]] = None
    
    class Config:
        use_enum_values = True

class FestivalInDB(Festival):
    """Festival in database"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    is_active: bool = True
    expected_products_count: int = 0

class FestivalResponse(BaseModel):
    """Festival response with analytics"""
    festival: Festival
    days_remaining: int
    estimated_savings: float
    product_count: int

# ============ User Schemas ============

class UserSchema(BaseModel):
    """User schema"""
    user_id: str
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRoleEnum = UserRoleEnum.FREE
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class UserInDB(UserSchema):
    """User in database"""
    id: Optional[str] = Field(None, alias="_id")
    password_hash: str
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = {}
    subscription_end: Optional[datetime] = None

class UserCreate(BaseModel):
    """User creation schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

class UserUpdate(BaseModel):
    """User update schema"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    """User response schema"""
    user_id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Token Schemas ============

class TokenSchema(BaseModel):
    """Token schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    """Token data payload"""
    user_id: str
    email: str
    role: str
    exp: datetime
    iat: datetime

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

# ============ Analytics Schemas ============

class SavingsAnalytics(BaseModel):
    """Savings analytics"""
    total_savings: float
    total_purchases: int
    average_discount: float
    best_deal: Optional[str] = None
    best_deal_savings: float
    period_days: int = 30

class DiscountAnalytics(BaseModel):
    """Discount analytics"""
    average_discount: float
    max_discount: float
    min_discount: float
    by_category: Dict[str, float]
    by_platform: Dict[str, float]

class TrendAnalytics(BaseModel):
    """Price trend analytics"""
    trending_up: List[str]
    trending_down: List[str]
    stable: List[str]
    best_time_to_buy: str
    forecast_accuracy: float

# ============ Notification Schemas ============

class Notification(BaseModel):
    """Notification model"""
    user_id: str
    title: str
    message: str
    type: str  # price_drop, festival, recommendation
    product_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime

class NotificationPreferences(BaseModel):
    """User notification preferences"""
    email_alerts: bool = True
    price_drop_alerts: bool = True
    festival_alerts: bool = True
    recommendation_alerts: bool = True
    alert_threshold: float = 10.0  # percentage

# ============ Error Schemas ============

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: bool = True
    message: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationError(BaseModel):
    """Validation error schema"""
    field: str
    message: str

# ============ Pagination Schemas ============

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = "asc"

class PaginatedResponse(BaseModel):
    """Paginated response"""
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool

# ============ Health Check Schemas ============

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    dependencies: Dict[str, str]
