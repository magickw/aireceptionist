"""
Firebase Authentication Utilities
Handles Firebase token validation and user management
"""
import os
import json
import firebase_admin
from firebase_admin import auth, credentials
from typing import Dict, Optional, Any
from fastapi import HTTPException, status

# Initialize Firebase Admin (lazy initialization)
_firebase_app = None

def get_firebase_app():
    """Get or initialize Firebase Admin app"""
    global _firebase_app
    if _firebase_app is None:
        # Check for Firebase credentials
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
        if firebase_creds:
            # Try to parse as JSON string (for environment variable)
            try:
                creds_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(creds_dict)
            except json.JSONDecodeError:
                # If it's a file path
                cred = credentials.Certificate(firebase_creds)
        else:
            # Try to find service account file
            cred_path = os.path.join(os.path.dirname(__file__), "firebase-service-account.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Firebase credentials not configured"
                )
        
        _firebase_app = firebase_admin.initialize_app(cred, name="aireceptionist-backend")
    
    return _firebase_app

async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return decoded claims
    
    Args:
        token: Firebase ID token
        
    Returns:
        Decoded token claims
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        app = get_firebase_app()
        decoded = auth.verify_id_token(token, app=app)
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

async def get_firebase_user(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get Firebase user by UID
    
    Args:
        uid: Firebase user ID
        
    Returns:
        User record or None
    """
    try:
        app = get_firebase_app()
        user = auth.get_user(uid, app=app)
        return {
            "uid": user.uid,
            "email": user.email,
            "email_verified": user.email_verified,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "provider": user.provider_data[0].provider_id if user.provider_data else None
        }
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Firebase user: {str(e)}"
        )

async def create_firebase_user(email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new Firebase user
    
    Args:
        email: User email
        password: User password
        display_name: Optional display name
        
    Returns:
        Created user record
    """
    try:
        app = get_firebase_app()
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            app=app
        )
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name
        }
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Firebase user: {str(e)}"
        )