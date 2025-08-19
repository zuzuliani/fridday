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
    # Initialize Supabase client
    # In production, we use a basic client and authenticate per request
    # In development, we use a pre-authenticated client
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    if os.getenv("VERSION") == "development":
        print("🔧 Using development mode - authentication per request")
    else:
        print("🚀 Using production mode - JWT authentication")
    
    # Initialize chatbot
    chatbot = Chatbot(supabase)
    
    # Set global chatbot instance
    routes_module.chatbot_instance = chatbot
    
    print("🤖 Chatbot initialized successfully!")
    
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

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    # Railway sets PORT environment variable, fallback to APP_PORT, then 8000
    port = int(os.getenv("PORT", os.getenv("APP_PORT", 8000)))
    
    print(f"🚀 Starting BifrostAI Chatbot on {host}:{port}")
    print(f"📝 Environment: {os.getenv('VERSION', 'development')}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("VERSION") == "development"
    )