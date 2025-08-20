#!/usr/bin/env python3
"""
Minimal startup test to identify the root cause of deployment failures
"""

import sys
import os
from dotenv import load_dotenv

print("=== MINIMAL STARTUP TEST ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Load environment variables
load_dotenv()
print("✅ Environment variables loaded")

# Test basic imports
try:
    from fastapi import FastAPI
    print("✅ FastAPI import successful")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    sys.exit(1)

try:
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ CORS middleware import successful")
except Exception as e:
    print(f"❌ CORS middleware import failed: {e}")
    sys.exit(1)

try:
    from supabase import create_client
    print("✅ Supabase import successful")
except Exception as e:
    print(f"❌ Supabase import failed: {e}")
    sys.exit(1)

# Test chatbot imports
try:
    from chatbot import Chatbot
    print("✅ Chatbot import successful")
except Exception as e:
    print(f"❌ Chatbot import failed: {e}")
    print("This is likely the root cause!")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from api.routes import router
    print("✅ API routes import successful")
except Exception as e:
    print(f"❌ API routes import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test creating minimal FastAPI app
try:
    app = FastAPI(title="Test App")
    print("✅ FastAPI app creation successful")
except Exception as e:
    print(f"❌ FastAPI app creation failed: {e}")
    sys.exit(1)

# Test adding health endpoint
try:
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    print("✅ Health endpoint added successfully")
except Exception as e:
    print(f"❌ Health endpoint failed: {e}")
    sys.exit(1)

print("=== ALL BASIC IMPORTS SUCCESSFUL ===")
print("The issue is likely in the complex initialization, not basic imports")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("APP_PORT", 8000)))
    
    print(f"🚀 Starting minimal test server on {host}:{port}")
    
    uvicorn.run(
        "test_minimal_startup:app",
        host=host,
        port=port,
        reload=False
    )
