from datetime import datetime

from pydantic import BaseModel, EmailStr
import uuid


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class BookMarkCreate(BaseModel):
    url : str
    title: str
    category : str
    notes: str | None

class BookMarkResponse(BaseModel):
    id: int
    url: str
    title: str
    category: str
    notes: str | None

    model_config = {
        "from_attributes": True
            }

class BookMarkUpdate(BaseModel):
    url: str
    title: str
    category: str
    notes: str | None

