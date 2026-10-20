import uuid

from pydantic import BaseModel, Field, model_validator


class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    isbn: str = Field(min_length=1)
    total_copies: int = Field(gt=0)


class BookResponse(BookCreate):
    id: uuid.UUID
    available_copies: int
    model_config = {"from_attributes": True}


class BookUpdate(BaseModel):
    copies: int = Field(gt=0)


class BookMetadataUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    author: str | None = Field(default=None, min_length=1)
    isbn: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def reject_nulls(self):
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Metadata fields cannot be null")
        return self
