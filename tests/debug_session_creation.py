"""
Debug session creation to understand the RLS issue
"""
import os
os.environ["VERSION"] = "production"

from api.auth import get_current_user, get_authenticated_supabase
from chatbot.session_manager import SessionManager
from fastapi import Depends
from auth_utils.supAuth import SupAuth

# JWT token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik53U0pFYmNvQkVHUFNQUUQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2NyemhnZHRudWt1ZW1wdHNkZnBxLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYTI3NTFkMC02OGIxLTQ2NTYtODk2NS0wZWU1NGFlNmYzOWQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU0NDI5NjA3LCJpYXQiOjE3NTQ0MjYwMDcsImVtYWlsIjoibWF0ZXVzQGRnYmNvbnN1bHRvcmVzLmNvbS5iciIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzU0NDI2MDA3fV0sInNlc3Npb25faWQiOiI1NDY1YTlmNi1lZGM1LTRiZjgtYmQ3NC1mODQ1OTJiZWQyYzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.fLclMi_J9NTQhxpOI1MzToarDfuleaNZebDAN-0gmjg"

def test_session_creation():
    """Test session creation step by step."""
    
    print("🔍 Debug Session Creation")
    print("=" * 40)
    
    # Step 1: Test authentication
    print("Step 1: Test Authentication")
    try:
        from fastapi.security import HTTPAuthorizationCredentials
        from api.auth import get_current_user, get_supabase_client
        
        # Mock credentials
        credentials = type('Creds', (), {'credentials': JWT_TOKEN})()
        supabase = get_supabase_client()
        
        user = get_current_user(credentials, supabase)
        print(f"✅ User authenticated: {user['id']} ({user['email']})")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Step 2: Test get_authenticated_supabase
    print(f"\nStep 2: Test get_authenticated_supabase")
    try:
        auth_supabase = get_authenticated_supabase(user)
        print(f"✅ Got authenticated Supabase client")
        
        # Test if we can query something simple
        result = auth_supabase.table("chat_sessions").select("count", count="exact").execute()
        print(f"✅ Can query chat_sessions table, count: {result.count}")
        
    except Exception as e:
        print(f"❌ get_authenticated_supabase failed: {e}")
        return
    
    # Step 3: Test SessionManager directly
    print(f"\nStep 3: Test SessionManager")
    try:
        session_manager = SessionManager(auth_supabase)
        session = session_manager.create_session(user['id'], "Debug Test Session")
        print(f"✅ SessionManager works: {session.id}")
        
        # Clean up
        session_manager.delete_session(session.id, user['id'])
        
    except Exception as e:
        print(f"❌ SessionManager failed: {e}")
        print(f"   Error details: {str(e)}")
        return
    
    # Step 4: Compare with working SupAuth
    print(f"\nStep 4: Compare with Direct SupAuth")
    try:
        sup_auth = SupAuth(token=JWT_TOKEN)
        result = sup_auth.add("chat_sessions", {
            "id": "debug-test-direct",
            "user_id": user['id'],
            "title": "Direct SupAuth Test",
            "is_active": True
        })
        print(f"✅ Direct SupAuth works: {result.data[0]['id']}")
        
        # Clean up
        sup_auth.supabase.table("chat_sessions").delete().eq("id", "debug-test-direct").execute()
        
    except Exception as e:
        print(f"❌ Direct SupAuth failed: {e}")

if __name__ == "__main__":
    test_session_creation()