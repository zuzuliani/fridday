"""
Example client for testing the BifrostAI Chatbot API.
This demonstrates how to interact with the chatbot via HTTP requests.
"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ChatbotClient:
    """Simple client for interacting with the chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url
        self.token = token
        self.session_id = None
        
        # For development mode, get token from local auth
        if not token and os.getenv("VERSION") == "development":
            try:
                from auth_utils.supAuth import SupAuth
                sup_auth = SupAuth()
                self.token = sup_auth.get_token()
                print(f"✅ Using development token: {self.token[:20]}...")
            except Exception as e:
                print(f"❌ Failed to get development token: {e}")
    
    async def create_session(self, title: str = None):
        """Create a new chat session."""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            
            response = await client.post(
                f"{self.base_url}/api/v1/sessions",
                json={"title": title} if title else {},
                headers=headers
            )
            
            if response.status_code == 200:
                session_data = response.json()
                self.session_id = session_data["id"]
                print(f"✅ Created session: {self.session_id}")
                return session_data
            else:
                print(f"❌ Failed to create session: {response.text}")
                return None
    
    async def send_message(self, message: str):
        """Send a message to the chatbot."""
        if not self.session_id:
            await self.create_session()
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            
            response = await client.post(
                f"{self.base_url}/api/v1/chat",
                json={
                    "message": message,
                    "session_id": self.session_id,
                    "metadata": {"example_client": True}
                },
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to send message: {response.text}")
                return None
    
    async def get_sessions(self):
        """Get all sessions for the user."""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            
            response = await client.get(
                f"{self.base_url}/api/v1/sessions",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get sessions: {response.text}")
                return []
    
    async def get_conversation_history(self, session_id: str = None):
        """Get conversation history for a session."""
        session_id = session_id or self.session_id
        if not session_id:
            print("❌ No session ID provided")
            return None
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            
            response = await client.get(
                f"{self.base_url}/api/v1/sessions/{session_id}/history",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get conversation history: {response.text}")
                return None

async def demo_conversation():
    """Demonstrate a conversation with the chatbot."""
    print("🤖 BifrostAI Chatbot Client Demo")
    print("=" * 40)
    
    # Initialize client
    client = ChatbotClient()
    
    if not client.token:
        print("❌ No authentication token available. Make sure the server is running in development mode.")
        return
    
    # Create a session
    session = await client.create_session("Demo Conversation")
    if not session:
        return
    
    # Demo conversation
    messages = [
        "Hello! Can you introduce yourself?",
        "What are your main capabilities?",
        "Can you help me with Python programming?",
        "What did we just discuss in this conversation?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"👤 User: {message}")
        
        response = await client.send_message(message)
        if response:
            print(f"🤖 Bot: {response['message']}")
        else:
            break
    
    # Show conversation history
    print(f"\n--- Conversation History ---")
    history = await client.get_conversation_history()
    if history:
        for msg in history["messages"]:
            role = "👤 User" if msg["role"] == "user" else "🤖 Bot"
            print(f"{role}: {msg['content']}")
    
    # Show all sessions
    print(f"\n--- All Sessions ---")
    sessions = await client.get_sessions()
    for session in sessions:
        print(f"📁 {session['title']} (ID: {session['id']})")
    
    print("\n✅ Demo completed!")

async def interactive_chat():
    """Interactive chat mode."""
    print("🤖 BifrostAI Interactive Chat")
    print("Type 'quit' to exit, 'history' to see conversation history")
    print("=" * 50)
    
    client = ChatbotClient()
    
    if not client.token:
        print("❌ No authentication token available.")
        return
    
    # Create a session
    await client.create_session("Interactive Chat")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'history':
                history = await client.get_conversation_history()
                if history:
                    print("\n--- Conversation History ---")
                    for msg in history["messages"]:
                        role = "👤 You" if msg["role"] == "user" else "🤖 Bot"
                        print(f"{role}: {msg['content']}")
                continue
            elif not user_input:
                continue
            
            response = await client.send_message(user_input)
            if response:
                print(f"🤖 Bot: {response['message']}")
            else:
                print("❌ Failed to get response")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_chat())
    else:
        asyncio.run(demo_conversation())