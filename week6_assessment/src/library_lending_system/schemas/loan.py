from datetime import datetime
import uuid

from pydantic import BaseModel

class LoanCreate(BaseModel):
    member_id: uuid.UUID
    book_id: uuid.UUID


class LoanResponse(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    book_id : uuid.UUID
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None


    model_config = {"from_attributes": True}


class LoanPage(BaseModel):
    loans: list[LoanResponse]
    cursor: datetime | None
