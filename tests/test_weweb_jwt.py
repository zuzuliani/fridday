"""
Test script for JWT token from WeWeb
Paste your JWT token from WeWeb below and run this script.
"""

import asyncio
import httpx

# 🔑 PASTE YOUR JWT TOKEN FROM WEWEB HERE:
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik53U0pFYmNvQkVHUFNQUUQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2NyemhnZHRudWt1ZW1wdHNkZnBxLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYTI3NTFkMC02OGIxLTQ2NTYtODk2NS0wZWU1NGFlNmYzOWQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU0NDI5NjA3LCJpYXQiOjE3NTQ0MjYwMDcsImVtYWlsIjoibWF0ZXVzQGRnYmNvbnN1bHRvcmVzLmNvbS5iciIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzU0NDI2MDA3fV0sInNlc3Npb25faWQiOiI1NDY1YTlmNi1lZGM1LTRiZjgtYmQ3NC1mODQ1OTJiZWQyYzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.fLclMi_J9NTQhxpOI1MzToarDfuleaNZebDAN-0gmjg"

# 🌐 CHANGE THIS TO YOUR RAILWAY URL WHEN TESTING PRODUCTION:
# BASE_URL = "http://localhost:8000"  # For local testing
BASE_URL = "https://web-production-95dfd.up.railway.app"  # For Railway testing

async def test_weweb_jwt():
    """Test the JWT token from WeWeb."""
    
    if JWT_TOKEN == "PASTE_YOUR_JWT_TOKEN_HERE":
        print("❌ Please paste your JWT token from WeWeb in the JWT_TOKEN variable")
        return
    
    print("🧪 Testing JWT Token from WeWeb")
    print("=" * 50)
    print(f"Token: {JWT_TOKEN[:50]}...")
    print(f"Base URL: {BASE_URL}")
    print()
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health Check (no auth needed)
        print("🏥 Testing Health Check...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/health")
            if response.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print("🔧 Make sure your server is running")
                return
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("🔧 Make sure your server is running at {BASE_URL}")
            return
        
        # Test 2: Create Session (auth required)
        print("\n📝 Testing Create Session...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/sessions",
                json={"title": "WeWeb JWT Test Session"},
                headers=headers
            )
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data["id"]
                print(f"✅ Session created successfully!")
                print(f"   Session ID: {session_id}")
            else:
                print(f"❌ Create session failed:")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Create session error: {e}")
            return
        
        # Test 3: Send Chat Message (auth required)
        print("\n💬 Testing Chat Message...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "message": "Hello! This is a test message from WeWeb JWT authentication.",
                    "session_id": session_id,
                    "metadata": {"source": "weweb_test"}
                },
                headers=headers
            )
            
            if response.status_code == 200:
                chat_data = response.json()
                print(f"✅ Chat message sent successfully!")
                print(f"   Bot response: {chat_data['message']}")
                print(f"   Conversation ID: {chat_data['conversation_id']}")
            else:
                print(f"❌ Chat message failed:")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Chat message error: {e}")
            return
        
        # Test 4: Get Sessions (auth required)
        print("\n📋 Testing Get Sessions...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/sessions",
                headers=headers
            )
            
            if response.status_code == 200:
                sessions = response.json()
                print(f"✅ Retrieved {len(sessions)} sessions")
                for session in sessions[-3:]:  # Show last 3 sessions
                    print(f"   - {session['title']} ({session['id'][:8]}...)")
            else:
                print(f"❌ Get sessions failed:")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Get sessions error: {e}")
    
    print("\n🎉 All tests completed!")
    print("\n💡 If all tests passed, your JWT authentication is working correctly!")
    print("   You can now use this same token in WeWeb to call your chatbot API.")

if __name__ == "__main__":
    asyncio.run(test_weweb_jwt())