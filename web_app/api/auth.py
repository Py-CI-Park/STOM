from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import timedelta

from web_app.core.security import auth_manager, session_manager, get_current_user, require_admin
from web_app.core.config import get_settings

router = APIRouter()
settings = get_settings()


# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    role: str
    permissions: list
    is_active: bool
    created_at: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"
    permissions: list = ["read"]


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[list] = None
    is_active: Optional[bool] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class APIKeyCreate(BaseModel):
    name: str
    permissions: list = ["read"]


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with username and password"""
    user = auth_manager.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/login-json", response_model=Token)
async def login_json(login_data: LoginRequest):
    """Login with JSON payload"""
    user = auth_manager.authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.get("/me", response_model=User)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return User(
        username=current_user["username"],
        role=current_user["role"],
        permissions=current_user["permissions"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"].isoformat()
    )


@router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": current_user["username"], "role": current_user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    # In a real implementation, you might want to blacklist the token
    return {"message": "Successfully logged out"}


# User management (admin only)

@router.get("/users")
async def list_users(current_user: Dict[str, Any] = Depends(require_admin)):
    """List all users (admin only)"""
    users = []
    for username, user_data in auth_manager.users_db.items():
        users.append(User(
            username=user_data["username"],
            role=user_data["role"],
            permissions=user_data["permissions"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"].isoformat()
        ))
    return users


@router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, current_user: Dict[str, Any] = Depends(require_admin)):
    """Create new user (admin only)"""
    try:
        created_user = auth_manager.create_user(
            user_data.username,
            user_data.password,
            user_data.role,
            user_data.permissions
        )
        
        return User(
            username=created_user["username"],
            role=created_user["role"],
            permissions=created_user["permissions"],
            is_active=created_user["is_active"],
            created_at=created_user["created_at"].isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{username}", response_model=User)
async def get_user(username: str, current_user: Dict[str, Any] = Depends(require_admin)):
    """Get user by username (admin only)"""
    user = auth_manager.get_user(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        username=user["username"],
        role=user["role"],
        permissions=user["permissions"],
        is_active=user["is_active"],
        created_at=user["created_at"].isoformat()
    )


@router.put("/users/{username}", response_model=User)
async def update_user(username: str, updates: UserUpdate, 
                     current_user: Dict[str, Any] = Depends(require_admin)):
    """Update user (admin only)"""
    user = auth_manager.get_user(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build updates dict
    update_data = {}
    if updates.password is not None:
        update_data["password"] = updates.password
    if updates.role is not None:
        update_data["role"] = updates.role
    if updates.permissions is not None:
        update_data["permissions"] = updates.permissions
    if updates.is_active is not None:
        update_data["is_active"] = updates.is_active
    
    success = auth_manager.update_user(username, update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )
    
    updated_user = auth_manager.get_user(username)
    return User(
        username=updated_user["username"],
        role=updated_user["role"],
        permissions=updated_user["permissions"],
        is_active=updated_user["is_active"],
        created_at=updated_user["created_at"].isoformat()
    )


@router.delete("/users/{username}")
async def delete_user(username: str, current_user: Dict[str, Any] = Depends(require_admin)):
    """Delete user (admin only)"""
    success = auth_manager.delete_user(username)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or cannot be deleted"
        )
    
    return {"message": f"User {username} deleted successfully"}


# API Key management

@router.get("/api-keys")
async def list_api_keys(current_user: Dict[str, Any] = Depends(require_admin)):
    """List all API keys (admin only)"""
    from web_app.core.security import api_key_auth
    
    keys = []
    for api_key, key_info in api_key_auth.api_keys.items():
        keys.append({
            "key": api_key[:8] + "..." + api_key[-4:],  # Mask key
            "name": key_info["name"],
            "permissions": key_info["permissions"],
            "is_active": key_info["is_active"],
            "created_at": key_info["created_at"].isoformat()
        })
    
    return keys


@router.post("/api-keys")
async def create_api_key(key_data: APIKeyCreate, current_user: Dict[str, Any] = Depends(require_admin)):
    """Create new API key (admin only)"""
    from web_app.core.security import api_key_auth
    
    api_key = api_key_auth.create_api_key(key_data.name, key_data.permissions)
    
    return {
        "api_key": api_key,
        "name": key_data.name,
        "permissions": key_data.permissions,
        "message": "API key created successfully. Store it securely as it won't be shown again."
    }


@router.delete("/api-keys/{api_key}")
async def revoke_api_key(api_key: str, current_user: Dict[str, Any] = Depends(require_admin)):
    """Revoke API key (admin only)"""
    from web_app.core.security import api_key_auth
    
    success = api_key_auth.revoke_api_key(api_key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key revoked successfully"}


# Permission checking

@router.get("/check-permission/{permission}")
async def check_permission(permission: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Check if current user has specific permission"""
    has_permission = auth_manager.has_permission(current_user, permission)
    
    return {
        "username": current_user["username"],
        "permission": permission,
        "has_permission": has_permission
    }