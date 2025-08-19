from typing import List, Dict, Any, Optional
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from .models import ChatMessage, ConversationEntry
import os

class ChatbotMemory:
    """Handles conversation memory with Supabase persistence and LangChain memory management."""
    
    def __init__(self, supabase_client, session_id: str, user_id: str, max_token_limit: int = 2000):
        self.supabase = supabase_client
        self.session_id = session_id
        self.user_id = user_id
        self.max_token_limit = max_token_limit
        
        # Initialize LangChain memory
        llm = ChatOpenAI(
            model=os.getenv("DEFAULT_LLM", "gpt-3.5-turbo"),
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.memory = ConversationSummaryBufferMemory(
            llm=llm,
            max_token_limit=max_token_limit,
            return_messages=True
        )
        
        # Load existing conversation
        self._load_conversation_history()
    
    def _load_conversation_history(self):
        """Load conversation history from Supabase."""
        try:
            response = self.supabase.table("conversations").select("*").eq(
                "session_id", self.session_id
            ).eq("user_id", self.user_id).order("created_at", desc=False).execute()
            
            messages = []
            for entry in response.data:
                if entry["role"] == "user":
                    messages.append(HumanMessage(content=entry["content"]))
                elif entry["role"] == "assistant":
                    messages.append(AIMessage(content=entry["content"]))
            
            # Add messages to memory
            for message in messages:
                self.memory.chat_memory.add_message(message)
                
        except Exception as e:
            print(f"Error loading conversation history: {e}")
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add user message to memory and persist to Supabase."""
        # Add to LangChain memory
        self.memory.chat_memory.add_user_message(content)
        
        # Persist to Supabase
        return self._persist_message("user", content, metadata or {})
    
    def add_ai_message(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add AI message to memory and persist to Supabase."""
        # Add to LangChain memory
        self.memory.chat_memory.add_ai_message(content)
        
        # Persist to Supabase
        return self._persist_message("assistant", content, metadata or {})
    
    def _persist_message(self, role: str, content: str, metadata: Dict[str, Any]) -> str:
        """Persist message to Supabase."""
        try:
            response = self.supabase.table("conversations").insert({
                "user_id": self.user_id,
                "session_id": self.session_id,
                "role": role,
                "content": content,
                "metadata": metadata
            }).execute()
            
            return response.data[0]["id"]
        except Exception as e:
            print(f"Error persisting message: {e}")
            return ""
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """Get conversation history from memory."""
        return self.memory.chat_memory.messages
    
    def get_memory_variables(self) -> Dict[str, Any]:
        """Get memory variables for use in prompts."""
        return self.memory.load_memory_variables({})
    
    def clear_memory(self):
        """Clear conversation memory (but keep in database)."""
        self.memory.clear()
    
    def get_conversation_summary(self) -> str:
        """Get conversation summary if available."""
        if hasattr(self.memory, 'moving_summary_buffer') and self.memory.moving_summary_buffer:
            return self.memory.moving_summary_buffer
        return ""