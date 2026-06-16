# FastAPI main application entry point

import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routes and models
from api.routes import router as api_router

# Initialize FastAPI app
app = FastAPI(
    title="Pater API",
    description="AI-powered price prediction and product aggregation API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.amazon.in",
        "https://www.flipkart.com",
        "https://www.myntra.com",
        "chrome-extension://*",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run and monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Pater API",
        "description": "AI-powered shopping assistant for price predictions",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include API routes
app.include_router(api_router, prefix="/api")

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Pater API starting up...")
    # Initialize databases, cache, ML models here
    try:
        logger.info("✅ All services initialized")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Pater API shutting down...")
    # Cleanup resources here

# Metrics endpoint
@app.get("/metrics")
async def metrics(x_api_key: str = Header(None)):
    """Prometheus metrics endpoint (requires API key)"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    return {
        "uptime": datetime.utcnow().isoformat(),
        "requests_total": 0,
        "predictions_total": 0,
        "api_errors": 0
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "False") == "True",
        log_level="info"
    )
