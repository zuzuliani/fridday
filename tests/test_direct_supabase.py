"""
Direct test of Supabase authentication and RLS policies
"""
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik53U0pFYmNvQkVHUFNQUUQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2NyemhnZHRudWt1ZW1wdHNkZnBxLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYTI3NTFkMC02OGIxLTQ2NTYtODk2NS0wZWU1NGFlNmYzOWQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU0NDI5NjA3LCJpYXQiOjE3NTQ0MjYwMDcsImVtYWlsIjoibWF0ZXVzQGRnYmNvbnN1bHRvcmVzLmNvbS5iciIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzU0NDI2MDA3fV0sInNlc3Npb25faWQiOiI1NDY1YTlmNi1lZGM1LTRiZjgtYmQ3NC1mODQ1OTJiZWQyYzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.fLclMi_J9NTQhxpOI1MzToarDfuleaNZebDAN-0gmjg"

def test_supabase_auth():
    """Test different methods of Supabase authentication."""
    
    print("🧪 Testing Direct Supabase Authentication")
    print("=" * 50)
    
    # Method 1: Using local auth (known to work)
    print("📝 Test 1: Local Auth (SupAuth)")
    try:
        from supabase_auth.supAuth import SupAuth
        sup_auth = SupAuth()
        
        # Try to create a session
        result = sup_auth.add("chat_sessions", {
            "id": "test-session-local",
            "user_id": sup_auth.session.user.id,
            "title": "Local Auth Test",
            "is_active": True
        })
        print(f"✅ Local auth works: {result.data[0]['id']}")
        
        # Clean up
        sup_auth.supabase.table("chat_sessions").delete().eq("id", "test-session-local").execute()
        
    except Exception as e:
        print(f"❌ Local auth failed: {e}")
    
    # Method 2: Using JWT token directly
    print(f"\n📝 Test 2: Direct JWT Token")
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # Set JWT token
        supabase.postgrest.auth(JWT_TOKEN)
        
        # Try to create a session
        result = supabase.table("chat_sessions").insert({
            "id": "test-session-jwt",
            "user_id": "aa2751d0-68b1-4656-8965-0ee54ae6f39d",  # User ID from JWT
            "title": "JWT Auth Test",
            "is_active": True
        }).execute()
        
        print(f"✅ JWT auth works: {result.data[0]['id']}")
        
        # Clean up
        supabase.table("chat_sessions").delete().eq("id", "test-session-jwt").execute()
        
    except Exception as e:
        print(f"❌ JWT auth failed: {e}")
    
    # Method 3: Check if user exists
    print(f"\n📝 Test 3: User Verification")
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # Check user with JWT
        user_response = supabase.auth.get_user(JWT_TOKEN)
        if user_response.user:
            print(f"✅ User exists: {user_response.user.id} ({user_response.user.email})")
        else:
            print(f"❌ User not found with JWT token")
            
    except Exception as e:
        print(f"❌ User verification failed: {e}")
    
    # Method 4: Try using the same method as SupAuth but with JWT
    print(f"\n📝 Test 4: SupAuth Method with JWT")
    try:
        from supabase_auth.supAuth import SupAuth
        sup_auth_jwt = SupAuth(token=JWT_TOKEN)
        
        # Try to create a session
        result = sup_auth_jwt.add("chat_sessions", {
            "id": "test-session-supauth-jwt",
            "user_id": "aa2751d0-68b1-4656-8965-0ee54ae6f39d",
            "title": "SupAuth JWT Test",
            "is_active": True
        })
        print(f"✅ SupAuth with JWT works: {result.data[0]['id']}")
        
        # Clean up
        sup_auth_jwt.supabase.table("chat_sessions").delete().eq("id", "test-session-supauth-jwt").execute()
        
    except Exception as e:
        print(f"❌ SupAuth with JWT failed: {e}")

if __name__ == "__main__":
    test_supabase_auth()