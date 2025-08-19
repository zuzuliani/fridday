"""
Debug script to analyze the JWT token and understand the authentication issue.
"""

import jwt
import json
from datetime import datetime

# Your JWT token from WeWeb/local
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik53U0pFYmNvQkVHUFNQUUQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2NyemhnZHRudWt1ZW1wdHNkZnBxLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhYTI3NTFkMC02OGIxLTQ2NTYtODk2NS0wZWU1NGFlNmYzOWQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU0NDI5NjA3LCJpYXQiOjE3NTQ0MjYwMDcsImVtYWlsIjoibWF0ZXVzQGRnYmNvbnN1bHRvcmVzLmNvbS5iciIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzU0NDI2MDA3fV0sInNlc3Npb25faWQiOiI1NDY1YTlmNi1lZGM1LTRiZjgtYmQ3NC1mODQ1OTJiZWQyYzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.fLclMi_J9NTQhxpOI1MzToarDfuleaNZebDAN-0gmjg"

def decode_jwt_token(token):
    """Decode JWT token without verification to see its contents."""
    try:
        # Decode without verification to see the payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        print("🔍 JWT Token Analysis")
        print("=" * 50)
        
        print(f"📧 Email: {decoded.get('email')}")
        print(f"👤 User ID: {decoded.get('sub')}")
        print(f"🏢 Issuer: {decoded.get('iss')}")
        print(f"👥 Audience: {decoded.get('aud')}")
        print(f"🔑 Role: {decoded.get('role')}")
        
        # Check expiration
        exp = decoded.get('exp')
        if exp:
            exp_date = datetime.fromtimestamp(exp)
            now = datetime.now()
            print(f"⏰ Expires: {exp_date}")
            print(f"⏱️  Current: {now}")
            if exp_date > now:
                print("✅ Token is still valid (not expired)")
            else:
                print("❌ Token has expired!")
        
        # Check issuer URL - this is key!
        issuer = decoded.get('iss')
        if 'crzhgdtnukuemptsdfpq.supabase.co' in issuer:
            print("✅ Token is from your Supabase instance")
        else:
            print(f"❌ Token is from different instance: {issuer}")
        
        print(f"\n📋 Full payload:")
        print(json.dumps(decoded, indent=2))
        
        return decoded
        
    except Exception as e:
        print(f"❌ Error decoding token: {e}")
        return None

def main():
    """Main function."""
    decoded = decode_jwt_token(JWT_TOKEN)
    
    if decoded:
        print(f"\n💡 Analysis:")
        print(f"- This token is from your local/production Supabase instance")
        print(f"- User ID: {decoded.get('sub')}")
        print(f"- This user needs to exist in your Supabase database")
        print(f"- The RLS policies are working, but authentication might not be setting the user context properly")
        
        print(f"\n🔧 Next steps:")
        print(f"1. Verify this user exists in your Supabase auth.users table")
        print(f"2. Make sure the JWT is being properly set in the Supabase client")
        print(f"3. Check that the RLS policies are correctly configured")

if __name__ == "__main__":
    main()