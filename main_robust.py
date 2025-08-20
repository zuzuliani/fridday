#!/usr/bin/env python3
"""
Robust version of main.py with better error handling for Railway deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variables for optional components
chatbot_available = False
routes_available = False
supabase_available = False

# Try to import optional components
try:
    from supabase import create_client
    supabase_available = True
    print("✅ Supabase client available")
except ImportError as e:
    print(f"⚠️ Supabase not available: {e}")

try:
    from chatbot import Chatbot
    chatbot_available = True
    print("✅ Chatbot module available")
except ImportError as e:
    print(f"⚠️ Chatbot not available: {e}")
    traceback.print_exc()

try:
    from api.routes import router
    import api.routes as routes_module
    routes_available = True
    print("✅ API routes available")
except ImportError as e:
    print(f"⚠️ API routes not available: {e}")
    traceback.print_exc()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with graceful degradation."""
    print("🚀 Starting application lifespan...")
    
    # Only try to initialize if all components are available
    if chatbot_available and supabase_available and routes_available:
        try:
            # Check if required environment variables are available
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                # Initialize Supabase client
                supabase = create_client(supabase_url, supabase_key)
                
                if os.getenv("VERSION") == "development":
                    print("🔧 Using development mode - authentication per request")
                else:
                    print("🚀 Using production mode - JWT authentication")
                
                # Initialize chatbot
                chatbot = Chatbot(supabase)
                
                # Set global chatbot instance
                routes_module.chatbot_instance = chatbot
                
                print("🤖 Chatbot initialized successfully!")
            else:
                print("⚠️ Supabase credentials not available - running in degraded mode")
        except Exception as e:
            print(f"⚠️ Failed to initialize chatbot during startup: {e}")
            print("App will continue in degraded mode")
            traceback.print_exc()
    else:
        print("⚠️ Some components not available - running in degraded mode")
    
    yield
    
    # Cleanup if needed
    print("👋 Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title="BifrostAI Chatbot",
    description="AI Chatbot with LangChain, LangGraph, and Supabase",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes if available
if routes_available:
    app.include_router(router, prefix="/api/v1", tags=["chatbot"])
    print("✅ API routes included")
else:
    print("⚠️ API routes not included - limited functionality")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to BifrostAI Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": {
            "chatbot_available": chatbot_available,
            "routes_available": routes_available,
            "supabase_available": supabase_available
        }
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint for Railway."""
    return {
        "status": "healthy", 
        "service": "chatbot-api",
        "components": {
            "chatbot": chatbot_available,
            "routes": routes_available,
            "supabase": supabase_available
        }
    }

@app.get("/api/v1/health")
async def health_check_v1():
    """Health check endpoint with API prefix."""
    return {
        "status": "healthy", 
        "service": "chatbot-api",
        "components": {
            "chatbot": chatbot_available,
            "routes": routes_available,
            "supabase": supabase_available
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Check required environment variables but don't exit
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY", "DEFAULT_LLM"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("App will start in degraded mode")
        print("Please set them in your Railway dashboard environment variables")
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    # Railway sets PORT environment variable, fallback to APP_PORT, then 8000
    port = int(os.getenv("PORT", os.getenv("APP_PORT", 8000)))
    
    print(f"🚀 Starting BifrostAI Chatbot on {host}:{port}")
    print(f"📝 Environment: {os.getenv('VERSION', 'development')}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"❤️ Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "main_robust:app",
        host=host,
        port=port,
        reload=os.getenv("VERSION") == "development"
    )
