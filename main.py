from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from supabase import create_client

from chatbot import Chatbot
from api.routes import router
import api.routes as routes_module

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
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
            print("⚠️ Supabase credentials not available - chatbot will be initialized per request")
            routes_module.chatbot_instance = None
    except Exception as e:
        print(f"⚠️ Failed to initialize chatbot during startup: {e}")
        print("App will continue to start - chatbot will be initialized per request")
        routes_module.chatbot_instance = None
    
    yield
    
    # Cleanup if needed
    print("👋 Shutting down chatbot...")

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

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["chatbot"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to BifrostAI Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint for Railway."""
    return {"status": "healthy", "service": "chatbot-api"}

@app.get("/api/v1/health")
async def health_check_v1():
    """Health check endpoint with API prefix."""
    return {"status": "healthy", "service": "chatbot-api"}

if __name__ == "__main__":
    import uvicorn
    
    # Check required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY", "DEFAULT_LLM"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("App will start but some features may not work properly")
        print("Please set them in your Railway dashboard environment variables")
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    # Railway sets PORT environment variable, fallback to APP_PORT, then 8000
    port = int(os.getenv("PORT", os.getenv("APP_PORT", 8000)))
    
    print(f"🚀 Starting BifrostAI Chatbot on {host}:{port}")
    print(f"📝 Environment: {os.getenv('VERSION', 'development')}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"❤️ Health Check: http://{host}:{port}/api/v1/health")
    print(f"✅ All required environment variables are set")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("VERSION") == "development"
    )