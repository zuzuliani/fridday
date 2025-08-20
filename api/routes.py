from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from chatbot import Chatbot, ChatRequest, ChatResponse, ChatSession, UpdateMessageRequest, UpdateMessageResponse, UserProfile
from .auth import get_current_user, get_authenticated_supabase

router = APIRouter()

# Global chatbot instance - will be initialized in main.py
chatbot_instance: Optional[Chatbot] = None

def get_chatbot():
    """Get the chatbot instance."""
    if chatbot_instance is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chatbot not initialized"
        )
    return chatbot_instance

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user = Depends(get_current_user),
    authenticated_supabase = Depends(get_authenticated_supabase)
):
    """
    Send a message to the chatbot.
    
    The request can include a user_profile field for personalized responses.
    If user_profile is not provided, you can optionally extract it from JWT data.
    
    Example request body:
    {
        "message": "Hello, can you help me with business strategy?",
        "session_id": "session-uuid",
        "user_profile": {
            "username": "João Silva",
            "companyName": "TechCorp", 
            "userRole": "Gerente de Projetos",
            "userFunction": "Diretor de TI",
            "communication_tone": " - mais executivo",
            "additional_guidelines": " - foque em ROI e métricas"
        }
    }
    """
    try:
        # Optional: If user_profile not provided, extract from JWT/user data
        # Uncomment and modify based on your JWT structure:
        # if not request.user_profile:
        #     request.user_profile = UserProfile(
        #         username=user.get("name") or user.get("username"),
        #         companyName=user.get("company"),
        #         userRole=user.get("role"),
        #         userFunction=user.get("function")
        #     )
        
        # Create chatbot with authenticated Supabase client
        from chatbot import Chatbot
        chatbot = Chatbot(authenticated_supabase)
        response = await chatbot.chat(request, user["id"])
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )

@router.post("/sessions", response_model=ChatSession)
async def create_session(
    title: Optional[str] = None,
    user = Depends(get_current_user),
    authenticated_supabase = Depends(get_authenticated_supabase)
):
    """Create a new chat session."""
    try:
        # Use authenticated Supabase client to create session manager
        from chatbot.session_manager import SessionManager
        session_manager = SessionManager(authenticated_supabase)
        session = session_manager.create_session(user["id"], title)
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session creation error: {str(e)}"
        )

@router.get("/sessions", response_model=List[ChatSession])
async def get_sessions(
    user = Depends(get_current_user),
    authenticated_supabase = Depends(get_authenticated_supabase)
):
    """Get all sessions for the current user."""
    try:
        from chatbot.session_manager import SessionManager
        session_manager = SessionManager(authenticated_supabase)
        sessions = session_manager.get_user_sessions(user["id"])
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    user = Depends(get_current_user),
    authenticated_supabase = Depends(get_authenticated_supabase)
):
    """Get conversation history for a session."""
    try:
        # Query conversations directly
        response = authenticated_supabase.table("conversations").select("*").eq(
            "session_id", session_id
        ).eq("user_id", user["id"]).order("created_at", desc=False).execute()
        
        return {"session_id": session_id, "messages": response.data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting conversation history: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user = Depends(get_current_user),
    authenticated_supabase = Depends(get_authenticated_supabase)
):
    """Delete a chat session."""
    try:
        from chatbot.session_manager import SessionManager
        session_manager = SessionManager(authenticated_supabase)
        success = session_manager.delete_session(session_id, user["id"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting session: {str(e)}"
        )

@router.post("/chat/update", response_model=UpdateMessageResponse)
async def update_message(
    request: UpdateMessageRequest,
    user = Depends(get_current_user),
    authenticated_supabase = Depends(get_authenticated_supabase)
):
    """Update an assistant message with LLM response - optimized for low latency."""
    try:
        # Create chatbot with authenticated Supabase client
        from chatbot import Chatbot
        chatbot = Chatbot(authenticated_supabase)
        response = await chatbot.update_message(request, user["id"])
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update message error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chatbot-api"}