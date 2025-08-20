"""
Test script for the chatbot functionality.
Run this to test the chatbot locally.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to Python path to import chatbot module
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
from supabase import create_client
from chatbot import Chatbot, ChatRequest

# Load environment variables
load_dotenv()

async def test_chatbot():
    """Test the chatbot functionality."""
    
    # For testing, use local auth
    from auth_utils.supAuth import SupAuth
    sup_auth = SupAuth()
    user_id = sup_auth.session.user.id
    
    # Use the authenticated Supabase client from SupAuth
    chatbot = Chatbot(sup_auth.supabase)
    
    print(f"Testing chatbot for user: {user_id}")
    print("-" * 50)
    
    # Create a new session
    session = chatbot.create_new_session(user_id, "Test Session")
    print(f"Created session: {session.id}")
    
    # Test conversations
    test_messages = [
        "Hello! How are you today?",
        "What can you help me with?",
        "Tell me a joke about programming",
        "What did we just talk about?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")
        
        request = ChatRequest(
            message=message,
            session_id=session.id,
            metadata={"test": True}
        )
        
        try:
            response = await chatbot.chat(request, user_id)
            print(f"Bot: {response.message}")
            print(f"Conversation ID: {response.conversation_id}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test getting conversation history
    print(f"\n--- Conversation History ---")
    history = chatbot.get_conversation_history(session.id, user_id)
    for entry in history:
        role = "User" if entry["role"] == "user" else "Bot"
        print(f"{role}: {entry['content']}")
    
    # Test getting user sessions
    print(f"\n--- User Sessions ---")
    sessions = chatbot.get_user_sessions(user_id)
    for session in sessions:
        print(f"Session: {session.id} - {session.title} (Active: {session.is_active})")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_chatbot())