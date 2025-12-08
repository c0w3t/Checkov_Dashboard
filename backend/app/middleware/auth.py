"""
Authentication Middleware for API Tokens
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.api_token import ApiToken
from datetime import datetime


async def verify_api_token(
    x_api_token: str = Header(..., alias="X-API-Token"),
    db: Session = Depends(get_db)
) -> ApiToken:
    """
    Verify API token from request header
    """
    token = db.query(ApiToken).filter(
        ApiToken.token == x_api_token,
        ApiToken.is_active == True
    ).first()
    
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or inactive API token")
    
    # Check expiration
    if token.expires_at and token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API token has expired")
    
    # Update last used timestamp
    token.last_used_at = datetime.utcnow()
    db.commit()
    
    return token
