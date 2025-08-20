from typing import Optional, List
import uuid
from datetime import datetime
from .models import ChatSession

class SessionManager:
    """Manages chat sessions with Supabase persistence."""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def create_session(self, user_id: str, title: str = None) -> ChatSession:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        
        try:
            response = self.supabase.table("chat_sessions").insert({
                "id": session_id,
                "user_id": user_id,
                "title": title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "is_active": True
            }).execute()
            
            session_data = response.data[0]
            return ChatSession(
                id=session_data["id"],
                user_id=session_data["user_id"],
                title=session_data["title"],
                summary=session_data.get("summary"),
                created_at=datetime.fromisoformat(session_data["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(session_data["updated_at"].replace('Z', '+00:00')),
                is_active=session_data["is_active"]
            )
        except Exception as e:
            print(f"Error creating session: {e}")
            raise
    
    def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a specific session."""
        try:
            response = self.supabase.table("chat_sessions").select("*").eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                session_data = response.data[0]
                return ChatSession(
                    id=session_data["id"],
                    user_id=session_data["user_id"],
                    title=session_data["title"],
                    summary=session_data.get("summary"),
                    created_at=datetime.fromisoformat(session_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(session_data["updated_at"].replace('Z', '+00:00')),
                    is_active=session_data["is_active"]
                )
            return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[ChatSession]:
        """Get all sessions for a user."""
        try:
            query = self.supabase.table("chat_sessions").select("*").eq("user_id", user_id)
            
            if active_only:
                query = query.eq("is_active", True)
            
            response = query.order("updated_at", desc=True).execute()
            
            sessions = []
            for session_data in response.data:
                sessions.append(ChatSession(
                    id=session_data["id"],
                    user_id=session_data["user_id"],
                    title=session_data["title"],
                    summary=session_data.get("summary"),
                    created_at=datetime.fromisoformat(session_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(session_data["updated_at"].replace('Z', '+00:00')),
                    is_active=session_data["is_active"]
                ))
            
            return sessions
        except Exception as e:
            print(f"Error getting user sessions: {e}")
            return []
    
    def update_session(self, session_id: str, user_id: str, **updates) -> bool:
        """Update session data."""
        try:
            response = self.supabase.table("chat_sessions").update(updates).eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating session: {e}")
            return False
    
    def deactivate_session(self, session_id: str, user_id: str) -> bool:
        """Deactivate a session (soft delete)."""
        return self.update_session(session_id, user_id, is_active=False)
    
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Permanently delete a session and all its conversations."""
        try:
            # Delete conversations first
            self.supabase.table("conversations").delete().eq(
                "session_id", session_id
            ).eq("user_id", user_id).execute()
            
            # Delete session
            response = self.supabase.table("chat_sessions").delete().eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False