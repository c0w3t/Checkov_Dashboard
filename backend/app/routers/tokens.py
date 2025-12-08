"""
API Token Management Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets
from app.database import get_db
from app.models.api_token import ApiToken
from app.schemas.api_token import ApiTokenCreate, ApiTokenResponse

router = APIRouter(prefix="/api/tokens", tags=["API Tokens"])


def generate_token() -> str:
    """Generate a secure random API token"""
    return secrets.token_urlsafe(48)


@router.get("/", response_model=List[ApiTokenResponse])
def get_all_tokens(db: Session = Depends(get_db)):
    """Get all API tokens"""
    return db.query(ApiToken).all()


@router.post("/", response_model=ApiTokenResponse)
def create_token(token_data: ApiTokenCreate, db: Session = Depends(get_db)):
    """Create a new API token"""
    new_token = ApiToken(
        name=token_data.name,
        token=generate_token(),
        permissions=token_data.permissions,
        expires_at=token_data.expires_at,
        is_active=True
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token


@router.delete("/{token_id}")
def delete_token(token_id: int, db: Session = Depends(get_db)):
    """Delete an API token"""
    token = db.query(ApiToken).filter(ApiToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    db.delete(token)
    db.commit()
    return {"message": "Token deleted successfully"}


@router.patch("/{token_id}/toggle")
def toggle_token(token_id: int, db: Session = Depends(get_db)):
    """Enable or disable a token"""
    token = db.query(ApiToken).filter(ApiToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token.is_active = not token.is_active
    db.commit()
    db.refresh(token)
    return token
