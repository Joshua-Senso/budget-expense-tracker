import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class CategoryCreate(BaseModel):
    name: str
    color: str
    expense_group: Literal["card", "other"]

    @field_validator("name")
    @classmethod
    def name_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v

    @field_validator("color")
    @classmethod
    def color_hex(cls, v: str) -> str:
        if not _HEX_COLOR_RE.match(v):
            raise ValueError("color must be a 6-digit hex string, e.g. #FF0000")
        return v


class CategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    expense_group: Literal["card", "other"] | None = None

    @field_validator("name")
    @classmethod
    def name_nonempty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name must not be blank")
        return v

    @field_validator("color")
    @classmethod
    def color_hex(cls, v: str | None) -> str | None:
        if v is not None and not _HEX_COLOR_RE.match(v):
            raise ValueError("color must be a 6-digit hex string, e.g. #FF0000")
        return v


class CategoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    color: str
    expense_group: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
