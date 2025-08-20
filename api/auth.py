from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
import os
from typing import Optional

security = HTTPBearer()

def get_supabase_client():
    """Get Supabase client."""
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase = Depends(get_supabase_client)
):
    """
    Get current user from JWT token.
    In development mode, uses local authentication.
    In production, validates the JWT token from the request.
    """
    try:
        if os.getenv("VERSION") == "development":
            # For development, use local auth
            from auth_utils.supAuth import SupAuth
            sup_auth = SupAuth()
            return {
                "id": sup_auth.session.user.id,
                "email": sup_auth.session.user.email,
                "token": sup_auth.token
            }
        else:
            # For production, validate the JWT token directly
            token = credentials.credentials
            
            try:
                # Use SupAuth to validate the JWT token (proven method)
                from auth_utils.supAuth import SupAuth
                sup_auth = SupAuth(token=token)
                
                # Verify the token by getting user info
                user_response = sup_auth.supabase.auth.get_user(token)
                
                if not user_response.user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token"
                    )
                
                # Store the authenticated supabase client for reuse
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "token": token,
                    "_supabase_client": sup_auth.supabase  # Pass the authenticated client
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token validation failed: {str(e)}"
                )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

def get_authenticated_supabase(
    user = Depends(get_current_user)
):
    """Get Supabase client with user authentication."""
    if os.getenv("VERSION") == "development":
        # In development, return the already authenticated client
        from supabase_auth.supAuth import SupAuth
        sup_auth = SupAuth()
        return sup_auth.supabase
    else:
        # In production, reuse the authenticated client if available
        if "_supabase_client" in user:
            return user["_supabase_client"]
        else:
            # Fallback: create new SupAuth instance
            from auth_utils.supAuth import SupAuth
            sup_auth = SupAuth(token=user["token"])
            return sup_auth.supabase