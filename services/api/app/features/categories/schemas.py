import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_name(v: str) -> str:
    stripped = v.strip()
    if not stripped:
        raise ValueError("name must not be blank")
    return stripped


def _validate_color(v: str) -> str:
    if not _HEX_COLOR_RE.match(v):
        raise ValueError("color must be a 6-digit hex string, e.g. #FF0000")
    return v


class CategoryCreate(BaseModel):
    name: str
    color: str
    expense_group: Literal["card", "other"]
    household_id: str | None = None

    @field_validator("name")
    @classmethod
    def name_nonempty(cls, v: str) -> str:
        return _validate_name(v)

    @field_validator("color")
    @classmethod
    def color_hex(cls, v: str) -> str:
        return _validate_color(v)


class CategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    expense_group: Literal["card", "other"] | None = None

    @field_validator("name")
    @classmethod
    def name_nonempty(cls, v: str | None) -> str | None:
        return _validate_name(v) if v is not None else None

    @field_validator("color")
    @classmethod
    def color_hex(cls, v: str | None) -> str | None:
        return _validate_color(v) if v is not None else None


class CategoryResponse(BaseModel):
    id: str
    user_id: str
    household_id: str | None
    name: str
    color: str
    expense_group: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
