# api/middleware.py - Custom middleware for request/response handling

import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ============ Request ID Middleware ============

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to all requests
    
    Useful for request tracing and logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request and response"""
        request_id = str(uuid4())
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

# ============ Logging Middleware ============

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details"""
        
        # Request info
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        query_params = request.url.query
        client_ip = request.client.host if request.client else "unknown"
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"[{request_id}] → {method} {path} | "
            f"IP: {client_ip} | Query: {query_params}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] ← {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] ✗ ERROR | {method} {path} | "
                f"Time: {process_time:.3f}s | Error: {str(e)}"
            )
            
            raise

# ============ Rate Limiting Middleware ============

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    
    Production: Use Redis for distributed rate limiting
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {ip: [(timestamp, count)]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit"""
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Initialize or get request history
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove old requests (older than 1 minute)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "message": "Rate limit exceeded",
                    "retry_after": 60
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        return response

# ============ CORS Middleware (Alternative) ============

class CORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware for fine-grained control
    """
    
    def __init__(
        self,
        app,
        allowed_origins: list = None,
        allowed_methods: list = None,
        allowed_headers: list = None
    ):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["*"]
        self.allowed_headers = allowed_headers or ["*"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS"""
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": self._get_origin(request),
                    "Access-Control-Allow-Methods": ", ".join(self.allowed_methods),
                    "Access-Control-Allow-Headers": ", ".join(self.allowed_headers),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = self._get_origin(request)
        
        return response
    
    def _get_origin(self, request: Request) -> str:
        """Get allowed origin"""
        if "*" in self.allowed_origins:
            return "*"
        
        origin = request.headers.get("origin")
        return origin if origin in self.allowed_origins else ""

# ============ Error Handling Middleware ============

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors gracefully"""
        
        try:
            response = await call_next(request)
            return response
        
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": "Invalid request",
                    "detail": str(e)
                }
            )
        
        except PermissionError as e:
            logger.error(f"Permission error: {e}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "message": "Access denied",
                    "detail": str(e)
                }
            )
        
        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error",
                    "detail": str(e) if logger.isEnabledFor(logging.DEBUG) else "Unknown error"
                }
            )

# ============ Compression Middleware ============

class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Compress responses larger than threshold
    """
    
    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Compress response"""
        
        response = await call_next(request)
        
        # Check if client accepts gzip
        if "gzip" not in request.headers.get("accept-encoding", ""):
            return response
        
        # Check response size
        if response.status_code != 200:
            return response
        
        # Would implement gzip compression here
        # For now, just return response as-is
        
        return response

# ============ Security Headers Middleware ============

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers"""
        
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

# ============ Metrics Middleware ============

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Collect metrics about requests and responses
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track metrics"""
        
        self.metrics["total_requests"] += 1
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Track timing
            response_time = time.time() - start_time
            self.metrics["total_response_time"] += response_time
            
            # Track success/failure
            if 200 <= response.status_code < 300:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1
            
            return response
        
        except Exception as e:
            self.metrics["failed_requests"] += 1
            raise
    
    def get_metrics(self) -> dict:
        """Get collected metrics"""
        total = self.metrics["total_requests"]
        
        return {
            **self.metrics,
            "average_response_time": (
                self.metrics["total_response_time"] / total
                if total > 0 else 0
            ),
            "success_rate": (
                (self.metrics["successful_requests"] / total * 100)
                if total > 0 else 0
            )
        }
