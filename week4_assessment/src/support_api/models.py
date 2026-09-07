from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    subject: str
    description: str | None = None
    severity: int = Field(default=1, ge=1, le=5)


class TicketResponse(BaseModel):
    id: int
    subject: str
    description: str | None
    severity: int = Field(ge=1, le=5)
    resolved: bool


class TicketUpdate(BaseModel):
    subject: str
    description: str | None = None
    severity: int = Field(ge=1, le=5)
    resolved: bool


class TicketPatch(BaseModel):
    subject: str | None = None
    description: str | None = None
    severity: int | None = Field(default=None, ge=1, le=5)
    resolved: bool | None = None

