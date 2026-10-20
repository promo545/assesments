from datetime import datetime
import uuid

from pydantic import BaseModel, EmailStr


class MemberCreate(BaseModel):
    name: str
    email: EmailStr

class MemberResponse(BaseModel):
    id: uuid.UUID
    name : str
    email : EmailStr
    joined_at: datetime

    model_config = {
        "from_attributes" : True
            }


