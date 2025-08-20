from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class UserProfile(BaseModel):
    """User profile information for prompt personalization"""
    username: Optional[str] = None
    companyName: Optional[str] = None
    userRole: Optional[str] = None
    userFunction: Optional[str] = None
    communication_tone: Optional[str] = ""
    additional_guidelines: Optional[str] = ""

class ChatRequest(BaseModel):
    message: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = {}
    user_profile: Optional[UserProfile] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = {}

class ChatSession(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class ConversationEntry(BaseModel):
    id: str
    user_id: str
    session_id: str
    role: str
    content: str
    status: Optional[str] = "complete"  # 'pending', 'processing', 'complete', 'failed'
    metadata: Optional[Dict[str, Any]] = {}
    reflection_steps: Optional[List[Dict[str, Any]]] = None  # Array of JSONB for reflection data
    created_at: datetime
    updated_at: datetime

class UpdateMessageRequest(BaseModel):
    message_id: str
    context_limit: Optional[int] = 10  # How many previous messages to include as context

class UpdateMessageResponse(BaseModel):
    message_id: str
    content: str
    status: str
    session_id: str
    updated_at: datetime