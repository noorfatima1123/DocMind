# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import uuid

from db.postgres import get_db
from models.user import User
from services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------- Request Models ----------
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ---------- REGISTER ----------
@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        name=request.name,
        email=request.email,
        hashed_password=hash_password(request.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    token = create_access_token(str(new_user.id))
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": str(new_user.id),
            "name": new_user.name,
            "email": new_user.email
        },
        "access_token": token,
        "token_type": "bearer"
    }


# ---------- LOGIN ----------
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate token
    token = create_access_token(str(user.id))
    
    return {
        "message": "Login successful",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email
        },
        "access_token": token,
        "token_type": "bearer"
    }