from pydantic import BaseModel


class ImportSummary(BaseModel):
    inserted: int
    updated: int
    deleted: int


class ImportRowError(BaseModel):
    row: int
    messages: list[str]
