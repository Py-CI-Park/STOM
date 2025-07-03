import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from web_app.core.config import get_settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()
settings = get_settings()


class AuthManager:
    """Handles authentication and authorization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.users_db: Dict[str, Dict[str, Any]] = {
            # Default admin user (should be configured properly in production)
            "admin": {
                "username": "admin",
                "hashed_password": self.get_password_hash("admin123"),
                "role": "admin",
                "permissions": ["all"],
                "created_at": datetime.now(),
                "is_active": True
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.secret_key, algorithm=self.settings.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.settings.secret_key, algorithms=[self.settings.algorithm])
            username: str = payload.get("sub")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        user = self.users_db.get(username)
        
        if not user:
            return None
        
        if not user["is_active"]:
            return None
        
        if not self.verify_password(password, user["hashed_password"]):
            return None
        
        return user
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return self.users_db.get(username)
    
    def create_user(self, username: str, password: str, role: str = "user", 
                   permissions: list = None) -> Dict[str, Any]:
        """Create new user"""
        if username in self.users_db:
            raise ValueError("User already exists")
        
        user_data = {
            "username": username,
            "hashed_password": self.get_password_hash(password),
            "role": role,
            "permissions": permissions or ["read"],
            "created_at": datetime.now(),
            "is_active": True
        }
        
        self.users_db[username] = user_data
        return {k: v for k, v in user_data.items() if k != "hashed_password"}
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """Update user information"""
        if username not in self.users_db:
            return False
        
        user = self.users_db[username]
        
        # Hash password if provided
        if "password" in updates:
            updates["hashed_password"] = self.get_password_hash(updates.pop("password"))
        
        user.update(updates)
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete user"""
        if username not in self.users_db:
            return False
        
        # Don't allow deleting admin user
        if username == "admin":
            return False
        
        del self.users_db[username]
        return True
    
    def has_permission(self, user: Dict[str, Any], permission: str) -> bool:
        """Check if user has specific permission"""
        user_permissions = user.get("permissions", [])
        
        # Admin has all permissions
        if "all" in user_permissions:
            return True
        
        return permission in user_permissions


# Global auth manager instance
auth_manager = AuthManager()


# Dependency functions for FastAPI

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    username = payload.get("sub")
    
    user = auth_manager.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    return current_user


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if not auth_manager.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    return permission_checker


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Optional dependency (doesn't raise exception if no token)
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise None"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# API Key authentication (for programmatic access)
class APIKeyAuth:
    """API Key authentication for CLI and programmatic access"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {
            # Default API key (should be configured properly in production)
            "stom_api_key_123": {
                "name": "default",
                "permissions": ["all"],
                "created_at": datetime.now(),
                "is_active": True
            }
        }
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key"""
        key_info = self.api_keys.get(api_key)
        
        if not key_info or not key_info["is_active"]:
            return None
        
        return key_info
    
    def create_api_key(self, name: str, permissions: list = None) -> str:
        """Create new API key"""
        import secrets
        api_key = f"stom_{secrets.token_urlsafe(32)}"
        
        self.api_keys[api_key] = {
            "name": name,
            "permissions": permissions or ["read"],
            "created_at": datetime.now(),
            "is_active": True
        }
        
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key"""
        if api_key not in self.api_keys:
            return False
        
        self.api_keys[api_key]["is_active"] = False
        return True


# Global API key manager
api_key_auth = APIKeyAuth()


async def verify_api_key(api_key: str) -> Dict[str, Any]:
    """Verify API key dependency"""
    key_info = api_key_auth.verify_api_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return key_info


# Session management
class SessionManager:
    """Manages user sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user: Dict[str, Any]) -> str:
        """Create new session"""
        import secrets
        session_id = secrets.token_urlsafe(32)
        
        self.sessions[session_id] = {
            "user": user,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "is_active": True
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        
        if not session or not session["is_active"]:
            return None
        
        # Check if session expired (24 hours)
        if datetime.now() - session["last_activity"] > timedelta(hours=24):
            self.invalidate_session(session_id)
            return None
        
        # Update last activity
        session["last_activity"] = datetime.now()
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate session"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["is_active"] = False
        return True
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session["last_activity"] > timedelta(hours=24):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]


# Global session manager
session_manager = SessionManager()