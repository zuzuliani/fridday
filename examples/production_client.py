"""
Example client for using the BifrostAI Chatbot API in production (Railway deployment).
This shows how to interact with the deployed chatbot API.
"""

import httpx
import asyncio
import json

class ProductionChatbotClient:
    """Client for interacting with the deployed chatbot API."""
    
    def __init__(self, base_url: str, jwt_token: str):
        """
        Initialize the client.
        
        Args:
            base_url: The Railway deployment URL (e.g., https://your-app.railway.app)
            jwt_token: Your Supabase JWT token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.session_id = None
        
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    
    async def health_check(self):
        """Check if the API is healthy."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/health")
                if response.status_code == 200:
                    print("✅ API is healthy!")
                    return response.json()
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return None
            except Exception as e:
                print(f"❌ Failed to connect to API: {e}")
                return None
    
    async def create_session(self, title: str = None):
        """Create a new chat session."""
        async with httpx.AsyncClient() as client:
            payload = {"title": title} if title else {}
            
            response = await client.post(
                f"{self.base_url}/api/v1/sessions",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code == 200:
                session_data = response.json()
                self.session_id = session_data["id"]
                print(f"✅ Created session: {self.session_id}")
                return session_data
            else:
                print(f"❌ Failed to create session: {response.status_code} - {response.text}")
                return None
    
    async def send_message(self, message: str):
        """Send a message to the chatbot."""
        if not self.session_id:
            await self.create_session("API Chat Session")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "message": message,
                "session_id": self.session_id,
                "metadata": {"client": "production_client"}
            }
            
            response = await client.post(
                f"{self.base_url}/api/v1/chat",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return None
    
    async def get_sessions(self):
        """Get all sessions for the user."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/sessions",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get sessions: {response.status_code} - {response.text}")
                return []
    
    async def get_conversation_history(self, session_id: str = None):
        """Get conversation history for a session."""
        session_id = session_id or self.session_id
        if not session_id:
            print("❌ No session ID provided")
            return None
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/sessions/{session_id}/history",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get conversation history: {response.status_code} - {response.text}")
                return None

async def demo_production_api():
    """Demonstrate using the production API."""
    # Configuration - Replace with your actual values
    RAILWAY_URL = "https://your-app.railway.app"  # Replace with your Railway URL
    JWT_TOKEN = "your_jwt_token_here"  # Replace with your Supabase JWT token
    
    print("🚀 BifrostAI Production API Demo")
    print("=" * 50)
    print(f"API URL: {RAILWAY_URL}")
    print(f"Token: {JWT_TOKEN[:20]}..." if JWT_TOKEN != "your_jwt_token_here" else "⚠️  Please set your JWT token")
    print()
    
    if JWT_TOKEN == "your_jwt_token_here":
        print("❌ Please update the JWT_TOKEN variable with your actual Supabase JWT token")
        return
    
    # Initialize client
    client = ProductionChatbotClient(RAILWAY_URL, JWT_TOKEN)
    
    # Test health check
    health = await client.health_check()
    if not health:
        print("❌ API is not accessible. Please check your Railway deployment.")
        return
    
    # Create a session
    session = await client.create_session("Production Demo")
    if not session:
        return
    
    # Demo conversation
    messages = [
        "Hello! I'm testing the deployed chatbot API.",
        "What capabilities do you have?",
        "Can you remember our conversation?",
        "What's the weather like in your digital world?"
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
            print(f"{role}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
    
    # Show all sessions
    print(f"\n--- All Sessions ---")
    sessions = await client.get_sessions()
    for session in sessions:
        print(f"📁 {session['title']} (ID: {session['id'][:8]}...)")
    
    print("\n✅ Production API demo completed!")

# Example of how to get a JWT token from Supabase (for reference)
def get_jwt_token_example():
    """
    Example of how to get a JWT token from Supabase.
    You would typically do this in your frontend or authentication service.
    """
    example_code = '''
    // Frontend JavaScript example
    import { createClient } from '@supabase/supabase-js'
    
    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    // Sign in user
    const { data, error } = await supabase.auth.signInWithPassword({
      email: 'user@example.com',
      password: 'password'
    })
    
    if (data.session) {
      const jwt_token = data.session.access_token
      // Use this token to authenticate with your chatbot API
    }
    '''
    print("Example of getting JWT token:")
    print(example_code)

if __name__ == "__main__":
    print("🔑 How to get JWT Token:")
    get_jwt_token_example()
    print("\n" + "="*50 + "\n")
    
    asyncio.run(demo_production_api())