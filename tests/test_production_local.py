"""
Test production authentication locally by setting VERSION=production
"""
import os
import asyncio
import httpx

# Force production mode for this test
os.environ["VERSION"] = "production"

# JWT token from your analysis
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik53U0pFYmNvQkVHUFNQUUQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2NyemhnZHRudWt1ZW1wdHNkZnBxLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYTI3NTFkMC02OGIxLTQ2NTYtODk2NS0wZWU1NGFlNmYzOWQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU0NDI5NjA3LCJpYXQiOjE3NTQ0MjYwMDcsImVtYWlsIjoibWF0ZXVzQGRnYmNvbnN1bHRvcmVzLmNvbS5iciIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzU0NDI2MDA3fV0sInNlc3Npb25faWQiOiI1NDY1YTlmNi1lZGM1LTRiZjgtYmQ3NC1mODQ1OTJiZWQyYzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.fLclMi_J9NTQhxpOI1MzToarDfuleaNZebDAN-0gmjg"

async def test_production_auth():
    """Test production authentication with JWT token."""
    
    print("🧪 Testing Production Authentication Locally")
    print("=" * 50)
    print(f"VERSION = {os.getenv('VERSION')}")
    print(f"Token: {JWT_TOKEN[:50]}...")
    print()
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        
        # Test health check
        print("🏥 Testing Health Check...")
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            if response.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("🔧 Make sure your server is running with: python main.py")
            return
        
        # Test create session
        print("\n📝 Testing Create Session with Production Auth...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/sessions",
                json={"title": "Production Auth Test"},
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data["id"]
                print(f"✅ Session created successfully!")
                print(f"   Session ID: {session_id}")
                
                # Test chat message
                print(f"\n💬 Testing Chat Message...")
                chat_response = await client.post(
                    f"{base_url}/api/v1/chat",
                    json={
                        "message": "Hello! Testing production authentication.",
                        "session_id": session_id
                    },
                    headers=headers
                )
                
                print(f"Chat Status: {chat_response.status_code}")
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print(f"✅ Chat successful!")
                    print(f"   Bot: {chat_data['message']}")
                else:
                    print(f"❌ Chat failed: {chat_response.text}")
                
            else:
                print(f"❌ Create session failed:")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_production_auth())