"""
LangGraph UI Adapter for Fridday Chatbot
Adapts the existing chatbot to work with LangGraph testing interfaces

NOTE: This adapter is for advanced use cases where you want to integrate
with LangGraph's Agent Chat UI or other LangGraph-based tools.
For normal chatbot usage, use the main Chatbot class directly.
"""

from typing import Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
import uuid
from .chatbot import Chatbot
from .models import ChatRequest
from .prompt_loader import get_chatbot_system_prompt


class ChatbotUIState(TypedDict):
    """State for LangGraph UI compatibility - uses standard message format"""
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_id: str


class LangGraphUIAdapter:
    """Adapter to make Fridday chatbot compatible with LangGraph UI testing tools"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.chatbot = Chatbot(supabase_client)
        
        # Create the UI-compatible workflow
        self.workflow = self._create_ui_workflow()
    
    def _create_ui_workflow(self) -> StateGraph:
        """Create a LangGraph workflow compatible with UI testing tools"""
        
        async def process_chat_ui(state: ChatbotUIState) -> ChatbotUIState:
            """Process chat messages in UI-compatible format"""
            messages = state["messages"]
            # Generate proper UUIDs for database compatibility
            user_id = state.get("user_id", str(uuid.uuid4()))
            session_id = state.get("session_id", str(uuid.uuid4()))
            
            # Get the last human message
            last_message = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_message = msg
                    break
            
            if not last_message:
                # Return with system message if no human message found
                system_prompt = get_chatbot_system_prompt()
                return {
                    **state,
                    "messages": state["messages"] + [SystemMessage(content=system_prompt)]
                }
            
            # Create chat request from the UI message
            chat_request = ChatRequest(
                message=last_message.content,
                session_id=session_id,
                metadata={"ui_test": True}
            )
            
            # Process through our existing chatbot
            try:
                response = await self.chatbot.chat(chat_request, user_id)
                
                # Add AI response to messages
                ai_message = AIMessage(content=response.message)
                
                return {
                    **state,
                    "messages": state["messages"] + [ai_message]
                }
                
            except Exception as e:
                # Return error message
                error_message = AIMessage(content=f"Error: {str(e)}")
                return {
                    **state,
                    "messages": state["messages"] + [error_message]
                }
        
        # Create the workflow
        workflow = StateGraph(ChatbotUIState)
        
        # Add the processing node
        workflow.add_node("process_chat", process_chat_ui)
        
        # Set entry point and end
        workflow.set_entry_point("process_chat")
        workflow.add_edge("process_chat", END)
        
        return workflow.compile()
    
    def get_compiled_workflow(self):
        """Get the compiled workflow for use with LangGraph UI tools"""
        return self.workflow


# Standalone function to create the workflow (for LangGraph server usage)
def create_chatbot_workflow(supabase_client=None):
    """Create a chatbot workflow for LangGraph server deployment"""
    if not supabase_client:
        # For testing, we might need to create a mock or use environment setup
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        # Try both possible environment variable names for Supabase key
        supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            supabase_client = create_client(supabase_url, supabase_key)
        else:
            raise ValueError("Supabase credentials not found in environment")
    
    adapter = LangGraphUIAdapter(supabase_client)
    return adapter.get_compiled_workflow()


# For direct testing with simple interface
async def test_chat_workflow():
    """Simple test function for the UI adapter"""
    from supabase import create_client
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    # Try both possible environment variable names for Supabase key
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials in environment")
        return
    
    supabase_client = create_client(supabase_url, supabase_key)
    adapter = LangGraphUIAdapter(supabase_client)
    
    # Test with a simple message
    initial_state = {
        "messages": [HumanMessage(content="Hello, can you help me with business strategy?")],
        "user_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4())
    }
    
    result = await adapter.workflow.ainvoke(initial_state)
    
    print("Test conversation:")
    for msg in result["messages"]:
        print(f"{msg.__class__.__name__}: {msg.content}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chat_workflow())
