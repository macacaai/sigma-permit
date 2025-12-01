from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
import hashlib
import json
from app.database import get_db
from app import models, schemas, crud
from app.auth import get_current_user
import secrets

router = APIRouter()

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return secrets.token_urlsafe(32)

def extract_device_info(request: Request) -> Dict[str, Any]:
    """Extract device information from request"""
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else "unknown"

    # Simple device detection (in production, use a proper library)
    device_info = {
        "user_agent": user_agent,
        "ip_address": ip_address,
        "device_type": "desktop",  # Default
        "os": "unknown",
        "browser": "unknown"
    }

    # Basic device type detection
    if "mobile" in user_agent.lower() or "android" in user_agent.lower() or "iphone" in user_agent.lower():
        device_info["device_type"] = "mobile"
    elif "tablet" in user_agent.lower() or "ipad" in user_agent.lower():
        device_info["device_type"] = "tablet"

    # Basic OS detection
    if "windows" in user_agent.lower():
        device_info["os"] = "windows"
    elif "macintosh" in user_agent.lower() or "mac os" in user_agent.lower():
        device_info["os"] = "macos"
    elif "linux" in user_agent.lower():
        device_info["os"] = "linux"
    elif "android" in user_agent.lower():
        device_info["os"] = "android"
    elif "ios" in user_agent.lower() or "iphone" in user_agent.lower():
        device_info["os"] = "ios"

    # Basic browser detection
    if "chrome" in user_agent.lower():
        device_info["browser"] = "chrome"
    elif "firefox" in user_agent.lower():
        device_info["browser"] = "firefox"
    elif "safari" in user_agent.lower():
        device_info["browser"] = "safari"
    elif "edge" in user_agent.lower():
        device_info["browser"] = "edge"

    return device_info

def create_session_fingerprint(device_info: Dict[str, Any]) -> str:
    """Create a fingerprint for device recognition"""
    fingerprint_data = {
        "user_agent": device_info.get("user_agent", ""),
        "ip_address": device_info.get("ip_address", ""),
        "device_type": device_info.get("device_type", ""),
        "os": device_info.get("os", ""),
        "browser": device_info.get("browser", "")
    }

    # Create a hash of the device info for fingerprinting
    fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def check_concurrent_session_limit(user_id: str, db: Session, max_sessions: int = 5) -> bool:
    """Check if user has exceeded concurrent session limit"""
    active_sessions = db.query(models.UserSession).filter(
        models.UserSession.user_id == user_id,
        models.UserSession.is_active == True,
        models.UserSession.expires_at > datetime.utcnow()
    ).count()

    return active_sessions < max_sessions

@router.post("/", response_model=schemas.Session)
async def create_session(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new user session"""
    # Check concurrent session limit
    if not check_concurrent_session_limit(str(current_user.id), db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum concurrent sessions exceeded"
        )

    # Extract device information
    device_info = extract_device_info(request)
    fingerprint = create_session_fingerprint(device_info)

    # Create session
    session_id = generate_session_id()
    expires_at = datetime.utcnow() + timedelta(hours=8)  # 8 hours default

    session = models.UserSession(
        user_id=str(current_user.id),
        session_id=session_id,
        device_info=device_info,
        ip_address=device_info.get("ip_address"),
        user_agent=device_info.get("user_agent"),
        is_active=True,
        expires_at=expires_at
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return schemas.Session.from_orm(session)

@router.get("/", response_model=List[schemas.Session])
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List user sessions"""
    query = db.query(models.UserSession).filter(
        models.UserSession.user_id == str(current_user.id)
    )

    if active_only:
        query = query.filter(
            models.UserSession.is_active == True,
            models.UserSession.expires_at > datetime.utcnow()
        )

    sessions = query.offset(skip).limit(limit).all()
    return [schemas.Session.from_orm(session) for session in sessions]

@router.get("/{session_id}", response_model=schemas.Session)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get session details"""
    session = db.query(models.UserSession).filter(
        models.UserSession.session_id == session_id,
        models.UserSession.user_id == str(current_user.id)
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return schemas.Session.from_orm(session)

@router.put("/{session_id}", response_model=schemas.Session)
async def update_session(
    session_id: str,
    session_update: schemas.SessionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update session (extend, activate/deactivate)"""
    session = db.query(models.UserSession).filter(
        models.UserSession.session_id == session_id,
        models.UserSession.user_id == str(current_user.id)
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Update fields
    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    # If activating, extend expiration
    if session_update.is_active and session_update.is_active == True:
        session.expires_at = datetime.utcnow() + timedelta(hours=8)

    db.commit()
    db.refresh(session)

    return schemas.Session.from_orm(session)

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Terminate a specific session"""
    session = db.query(models.UserSession).filter(
        models.UserSession.session_id == session_id,
        models.UserSession.user_id == str(current_user.id)
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Mark as inactive instead of deleting (for audit purposes)
    session.is_active = False
    db.commit()

    return

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Terminate all user sessions"""
    # Update all active sessions for this user
    db.query(models.UserSession).filter(
        models.UserSession.user_id == str(current_user.id),
        models.UserSession.is_active == True
    ).update({"is_active": False})

    db.commit()

    return

@router.post("/{session_id}/extend", response_model=schemas.Session)
async def extend_session(
    session_id: str,
    extension_minutes: int = Query(480, ge=1, le=43200),  # 1 min to 30 days
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Extend session expiration"""
    session = db.query(models.UserSession).filter(
        models.UserSession.session_id == session_id,
        models.UserSession.user_id == str(current_user.id)
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot extend inactive session"
        )

    # Extend expiration
    session.expires_at = datetime.utcnow() + timedelta(minutes=extension_minutes)
    session.last_activity = datetime.utcnow()

    db.commit()
    db.refresh(session)

    return schemas.Session.from_orm(session)

@router.get("/devices/", response_model=List[schemas.DeviceInfo])
async def list_devices(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List unique devices for the user"""
    # Get distinct device fingerprints and their latest session info
    sessions = db.query(models.UserSession).filter(
        models.UserSession.user_id == str(current_user.id)
    ).order_by(models.UserSession.last_activity.desc()).all()

    devices = {}
    for session in sessions:
        if session.device_info:
            fingerprint = create_session_fingerprint(session.device_info)
            if fingerprint not in devices:
                devices[fingerprint] = {
                    "device_id": fingerprint,
                    "device_name": f"{session.device_info.get('device_type', 'Unknown')} - {session.device_info.get('browser', 'Unknown')}",
                    "device_type": session.device_info.get('device_type'),
                    "os": session.device_info.get('os'),
                    "browser": session.device_info.get('browser'),
                    "is_trusted": False  # In production, this would be stored separately
                }

    return list(devices.values())

@router.post("/devices/{device_id}/trust", response_model=schemas.DeviceInfo)
async def trust_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a device as trusted"""
    # In a real implementation, this would update a device trust table
    # For now, just return success
    device_info = schemas.DeviceInfo(
        device_id=device_id,
        is_trusted=True
    )

    return device_info

@router.delete("/devices/{device_id}/trust", response_model=schemas.DeviceInfo)
async def untrust_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Remove device trust"""
    # In a real implementation, this would update a device trust table
    device_info = schemas.DeviceInfo(
        device_id=device_id,
        is_trusted=False
    )

    return device_info

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_expired_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Clean up expired sessions (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform session cleanup"
        )

    # Mark expired sessions as inactive
    expired_count = db.query(models.UserSession).filter(
        models.UserSession.expires_at < datetime.utcnow(),
        models.UserSession.is_active == True
    ).update({"is_active": False})

    db.commit()

    return {"message": f"Cleaned up {expired_count} expired sessions"}

@router.get("/stats/", response_model=Dict[str, Any])
async def get_session_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get session statistics for the user"""
    if not current_user.is_superuser:
        # Regular users only see their own stats
        total_sessions = db.query(models.UserSession).filter(
            models.UserSession.user_id == str(current_user.id)
        ).count()

        active_sessions = db.query(models.UserSession).filter(
            models.UserSession.user_id == str(current_user.id),
            models.UserSession.is_active == True,
            models.UserSession.expires_at > datetime.utcnow()
        ).count()

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": total_sessions - active_sessions
        }
    else:
        # Admins see global stats
        total_sessions = db.query(models.UserSession).count()
        active_sessions = db.query(models.UserSession).filter(
            models.UserSession.is_active == True,
            models.UserSession.expires_at > datetime.utcnow()
        ).count()

        expired_sessions = db.query(models.UserSession).filter(
            models.UserSession.expires_at < datetime.utcnow()
        ).count()

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "inactive_sessions": total_sessions - active_sessions - expired_sessions
        }