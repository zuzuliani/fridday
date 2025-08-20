"""
Example script showing how to use the Fridday Chatbot API with user profiles.
This demonstrates how to send personalized chat requests to the API.
"""

import asyncio
import json
import requests
from typing import Optional

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

class FriddayAPIClient:
    """Simple client for testing the Fridday Chatbot API with user profiles."""
    
    def __init__(self, base_url: str = API_BASE_URL, jwt_token: Optional[str] = None):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}" if jwt_token else None
        }
    
    def create_session(self, title: str = None) -> dict:
        """Create a new chat session."""
        response = requests.post(
            f"{self.base_url}/sessions",
            headers=self.headers,
            json={"title": title} if title else {}
        )
        response.raise_for_status()
        return response.json()
    
    def send_message(self, message: str, session_id: str, user_profile: dict = None) -> dict:
        """Send a message to the chatbot with optional user profile."""
        payload = {
            "message": message,
            "session_id": session_id,
            "metadata": {"test": True}
        }
        
        if user_profile:
            payload["user_profile"] = user_profile
        
        response = requests.post(
            f"{self.base_url}/chat",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_conversation_history(self, session_id: str) -> dict:
        """Get conversation history for a session."""
        response = requests.get(
            f"{self.base_url}/sessions/{session_id}/history",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def test_api_with_profiles():
    """Test the API with different user profiles."""
    
    # Note: In development mode, you don't need a real JWT token
    # The API will use local authentication
    client = FriddayAPIClient()
    
    print("🚀 Testing Fridday Chatbot API with User Profiles")
    print("=" * 60)
    
    try:
        # Test 1: Create session
        print("\n📋 Creating new session...")
        session = client.create_session("API Test with Profiles")
        session_id = session["id"]
        print(f"✅ Session created: {session_id[:8]}...")
        
        # Test 2: Chat without user profile (default behavior)
        print("\n💬 Testing without user profile...")
        response1 = client.send_message(
            "Olá! Você pode se apresentar?",
            session_id
        )
        print(f"🤖 Response: {response1['message'][:100]}...")
        
        # Test 3: Chat with executive profile
        print("\n👔 Testing with executive profile...")
        executive_profile = {
            "username": "Carlos Silva",
            "companyName": "TechCorp Brasil",
            "userRole": "CEO",
            "userFunction": "Chief Executive Officer",
            "communication_tone": " - mais executivo",
            "additional_guidelines": " - sempre inclua impacto no negócio e ROI"
        }
        
        response2 = client.send_message(
            "Preciso de uma estratégia de transformação digital para nossa empresa. Como devemos começar?",
            session_id,
            executive_profile
        )
        print(f"🤖 Executive Response: {response2['message'][:150]}...")
        
        # Test 4: Chat with technical profile
        print("\n💻 Testing with technical profile...")
        tech_profile = {
            "username": "Ana Costa",
            "companyName": "DevStudio",
            "userRole": "CTO",
            "userFunction": "Chief Technology Officer", 
            "communication_tone": " - mais técnico",
            "additional_guidelines": " - foque em arquitetura e implementação prática"
        }
        
        response3 = client.send_message(
            "Quais métricas técnicas devo acompanhar para nossa migração para cloud?",
            session_id,
            tech_profile
        )
        print(f"🤖 Technical Response: {response3['message'][:150]}...")
        
        # Test 5: Get conversation history
        print("\n📚 Getting conversation history...")
        history = client.get_conversation_history(session_id)
        print(f"✅ Retrieved {len(history['messages'])} messages from conversation")
        
        print("\n✅ API testing completed successfully!")
        print(f"Session ID: {session_id}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        print("Make sure the API server is running at http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def show_api_examples():
    """Show example API requests."""
    
    print("\n📖 API Request Examples:")
    print("=" * 40)
    
    print("\n1️⃣ Basic chat request (no profile):")
    basic_request = {
        "message": "Hello, can you help me with business strategy?",
        "session_id": "session-uuid-here"
    }
    print(json.dumps(basic_request, indent=2))
    
    print("\n2️⃣ Personalized chat request (with profile):")
    personalized_request = {
        "message": "Preciso de ajuda com análise de processos",
        "session_id": "session-uuid-here",
        "user_profile": {
            "username": "Maria Santos",
            "companyName": "InnovaCorp",
            "userRole": "Gerente de Processos",
            "userFunction": "Process Manager",
            "communication_tone": " - profissional e direto",
            "additional_guidelines": " - sempre sugira automações"
        }
    }
    print(json.dumps(personalized_request, indent=2))
    
    print("\n3️⃣ cURL example:")
    curl_example = '''curl -X POST "http://localhost:8000/api/v1/chat" \\
     -H "Content-Type: application/json" \\
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
     -d '{
       "message": "Como implementar IA na minha empresa?",
       "session_id": "your-session-id",
       "user_profile": {
         "username": "João Silva",
         "companyName": "TechStart",
         "userRole": "Fundador",
         "userFunction": "CEO"
       }
     }' '''
    print(curl_example)


if __name__ == "__main__":
    # Show examples first
    show_api_examples()
    
    # Ask if user wants to run live test
    print("\n" + "="*60)
    choice = input("Run live API test? (y/n): ").lower().strip()
    
    if choice == 'y':
        test_api_with_profiles()
    else:
        print("👋 Examples shown. Run with 'y' to test live API.")
