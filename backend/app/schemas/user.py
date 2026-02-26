from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_serializer

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: Optional[str] = "business_owner"

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    status: str
    created_at: Optional[datetime] = None
    
    @field_serializer('created_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.isoformat()

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None
