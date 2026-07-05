from datetime import datetime

from pydantic import BaseModel, Field


class AttachmentUploadRequest(BaseModel):
    content_type: str
    size_bytes: int = Field(gt=0)


class AttachmentUploadURLResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int


class AttachmentConfirm(BaseModel):
    object_key: str
    content_type: str
    size_bytes: int = Field(gt=0)


class AttachmentResponse(BaseModel):
    id: str
    expense_id: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class AttachmentDownloadURLResponse(BaseModel):
    download_url: str
    expires_in: int
