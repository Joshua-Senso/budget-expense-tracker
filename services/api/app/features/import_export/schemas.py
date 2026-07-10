from datetime import date

from pydantic import BaseModel


class ImportSummary(BaseModel):
    inserted: int
    updated: int
    deleted: int


class ImportRowError(BaseModel):
    row: int
    messages: list[str]


class PendingDeletion(BaseModel):
    row_id: str
    description: str
    spent_on: date
