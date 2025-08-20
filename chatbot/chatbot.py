from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from .memory import ChatbotMemory
from .session_manager import SessionManager
from .models import ChatRequest, ChatResponse
from .prompt_loader import get_chatbot_system_prompt

class ChatbotState:
    """State for the chatbot graph."""
    def __init__(self):
        self.user_input: str = ""
        self.ai_response: str = ""
        self.session_id: str = ""
        self.user_id: str = ""
        self.metadata: Dict[str, Any] = {}
        self.memory: Optional[ChatbotMemory] = None

class Chatbot:
    """Main chatbot class using LangGraph for conversation flow."""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.session_manager = SessionManager(supabase_client)
        
        # Initialize OpenAI
        self.llm = ChatOpenAI(
            model=os.getenv("DEFAULT_LLM", "gpt-3.5-turbo"),
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create conversation prompt
        system_prompt_content = get_chatbot_system_prompt()
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt_content),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(content="{input}")
        ])
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for processing conversations."""
        
        def process_input(state: Dict[str, Any]) -> Dict[str, Any]:
            """Process user input and prepare for AI response."""
            memory = state["memory"]
            user_input = state["user_input"]
            
            # Add user message to memory
            conversation_id = memory.add_user_message(user_input, state.get("metadata", {}))
            state["conversation_id"] = conversation_id
            
            return state
        
        def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate AI response using LangChain."""
            memory = state["memory"]
            user_input = state["user_input"]
            
            # Get memory variables
            memory_vars = memory.get_memory_variables()
            
            # Format prompt with history
            formatted_prompt = self.prompt.format_messages(
                history=memory_vars.get("history", []),
                input=user_input
            )
            
            # Generate response
            response = self.llm.invoke(formatted_prompt)
            ai_response = response.content
            
            # Add AI response to memory
            memory.add_ai_message(ai_response, state.get("metadata", {}))
            
            state["ai_response"] = ai_response
            return state
        
        # Create workflow graph
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("process_input", process_input)
        workflow.add_node("generate_response", generate_response)
        
        # Add edges
        workflow.add_edge("process_input", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Set entry point
        workflow.set_entry_point("process_input")
        
        return workflow.compile()
    
    async def chat(self, request: ChatRequest, user_id: str) -> ChatResponse:
        """Process a chat request and return response."""
        try:
            # Get or create session
            session = self.session_manager.get_session(request.session_id, user_id)
            if not session:
                session = self.session_manager.create_session(user_id)
            
            # Initialize memory for this session
            memory = ChatbotMemory(
                supabase_client=self.supabase,
                session_id=session.id,
                user_id=user_id
            )
            
            # Prepare state
            state = {
                "user_input": request.message,
                "session_id": session.id,
                "user_id": user_id,
                "metadata": request.metadata or {},
                "memory": memory,
                "conversation_id": ""
            }
            
            # Run workflow
            result = await self.workflow.ainvoke(state)
            
            # Update session timestamp
            self.session_manager.update_session(session.id, user_id)
            
            return ChatResponse(
                message=result["ai_response"],
                session_id=session.id,
                conversation_id=result["conversation_id"],
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            print(f"Error in chat: {e}")
            raise
    
    def get_conversation_history(self, session_id: str, user_id: str) -> list:
        """Get conversation history for a session."""
        try:
            response = self.supabase.table("conversations").select("*").eq(
                "session_id", session_id
            ).eq("user_id", user_id).order("created_at", desc=False).execute()
            
            return response.data
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def create_new_session(self, user_id: str, title: str = None):
        """Create a new chat session."""
        return self.session_manager.create_session(user_id, title)
    
    def get_user_sessions(self, user_id: str):
        """Get all sessions for a user."""
        return self.session_manager.get_user_sessions(user_id)
    
    async def update_message(self, request, user_id: str):
        """Update an assistant message with LLM response - optimized version."""
        from .models import UpdateMessageResponse
        from datetime import datetime
        
        try:
            # 1. Get the message to update and verify ownership
            message_response = self.supabase.table("conversations").select("*").eq(
                "id", request.message_id
            ).eq("user_id", user_id).single().execute()
            
            if not message_response.data:
                raise Exception("Message not found or access denied")
            
            message = message_response.data
            session_id = message["session_id"]
            
            # 2. Update status to 'processing'
            self.supabase.table("conversations").update({
                "status": "processing"
            }).eq("id", request.message_id).execute()
            
            # 3. Get recent conversation context
            context_response = self.supabase.table("conversations").select("*").eq(
                "session_id", session_id
            ).eq("user_id", user_id).order("created_at", desc=False).limit(
                request.context_limit
            ).execute()
            
            context_messages = []
            for msg in context_response.data:
                if msg["id"] != request.message_id:  # Don't include the empty assistant message
                    context_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # 4. Get LLM response
            try:
                # Convert to LangChain format
                from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
                
                lc_messages = []
                for msg in context_messages:
                    if msg["role"] == "user":
                        lc_messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        lc_messages.append(AIMessage(content=msg["content"]))
                    elif msg["role"] == "system":
                        lc_messages.append(SystemMessage(content=msg["content"]))
                
                # Get response from LLM
                response = await self.llm.ainvoke(lc_messages)
                assistant_content = response.content
                
            except Exception as llm_error:
                # Mark as failed and re-raise
                self.supabase.table("conversations").update({
                    "status": "failed",
                    "content": f"Error: {str(llm_error)}"
                }).eq("id", request.message_id).execute()
                raise llm_error
            
            # 5. Update the assistant message with LLM response
            update_response = self.supabase.table("conversations").update({
                "content": assistant_content,
                "status": "complete"
            }).eq("id", request.message_id).execute()
            
            updated_message = update_response.data[0]
            
            return UpdateMessageResponse(
                message_id=updated_message["id"],
                content=updated_message["content"],
                status=updated_message["status"],
                session_id=updated_message["session_id"],
                updated_at=datetime.fromisoformat(updated_message["updated_at"].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            # Try to mark as failed if we have the message_id
            try:
                self.supabase.table("conversations").update({
                    "status": "failed"
                }).eq("id", request.message_id).execute()
            except:
                pass  # Ignore errors when trying to update status
            
            print(f"Error in update_message: {e}")
            raise