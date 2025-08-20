"""
Test script for the new optimized chat flow.

This demonstrates the WeWeb-style optimistic UI pattern:
1. Create user message immediately
2. Create empty assistant message with 'pending' status
3. Call update API to fill in the assistant response
"""

import asyncio
import httpx
import json
from datetime import datetime
from auth_utils.supAuth import SupAuth

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

async def test_optimized_chat_flow():
    """Test the optimized chat flow."""
    
    # Initialize auth (using local development mode)
    sup_auth = SupAuth()  # Automatically does local login
    
    # Get authenticated client for direct Supabase operations
    supabase = sup_auth.supabase
    user_id = sup_auth.session.user.id
    
    print(f"🔐 Authenticated as user: {user_id}")
    
    # Step 1: Create a session (using existing API)
    async with httpx.AsyncClient() as client:
        session_response = await client.post(
            f"{BASE_URL}/sessions",
            headers={"Authorization": f"Bearer {sup_auth.get_token()}"},
            json={"title": "Optimized Chat Test"}
        )
        
        if session_response.status_code != 200:
            print(f"❌ Session creation failed: {session_response.text}")
            return
        
        session = session_response.json()
        session_id = session["id"]
        print(f"✅ Created session: {session_id}")
    
    # Step 2: WeWeb-style flow - Create messages directly in Supabase
    user_message = "What's the weather like today?"
    
    print("\n🚀 Starting optimized flow...")
    
    # 2a. Create user message immediately (WeWeb would do this)
    user_msg_response = supabase.table("conversations").insert({
        "user_id": user_id,
        "session_id": session_id,
        "role": "user",
        "content": user_message,
        "status": "complete"
    }).execute()
    
    user_msg_id = user_msg_response.data[0]["id"]
    print(f"✅ Created user message: {user_msg_id}")
    
    # 2b. Create empty assistant message with 'pending' status (WeWeb would do this)
    assistant_msg_response = supabase.table("conversations").insert({
        "user_id": user_id,
        "session_id": session_id,
        "role": "assistant",
        "content": "",  # Empty initially
        "status": "pending"
    }).execute()
    
    assistant_msg_id = assistant_msg_response.data[0]["id"]
    print(f"✅ Created empty assistant message: {assistant_msg_id}")
    print(f"📱 WeWeb UI would show: User message + empty assistant bubble with loading...")
    
    # Step 3: Call the new optimized update API
    print("\n🤖 Calling optimized update API...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        update_response = await client.post(
            f"{BASE_URL}/chat/update",
            headers={"Authorization": f"Bearer {sup_auth.get_token()}"},
            json={
                "message_id": assistant_msg_id,
                "context_limit": 10
            }
        )
        
        if update_response.status_code != 200:
            print(f"❌ Update failed: {update_response.text}")
            return
        
        result = update_response.json()
        print(f"✅ Assistant message updated!")
        print(f"📝 Response: {result['content']}")
        print(f"🎯 Status: {result['status']}")
        print(f"⏱️ Updated at: {result['updated_at']}")
    
    # Step 4: Verify the final state
    print("\n🔍 Verifying final conversation state...")
    
    final_conversation = supabase.table("conversations").select("*").eq(
        "session_id", session_id
    ).order("created_at", desc=False).execute()
    
    print("📜 Final conversation:")
    for msg in final_conversation.data:
        role_emoji = "👤" if msg["role"] == "user" else "🤖"
        status_emoji = "✅" if msg["status"] == "complete" else "⏳"
        print(f"  {role_emoji} {status_emoji} {msg['role']}: {msg['content'][:50]}...")

if __name__ == "__main__":
    asyncio.run(test_optimized_chat_flow())