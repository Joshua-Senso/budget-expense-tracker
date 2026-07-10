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
    # content_type/size_bytes are deliberately not accepted here -- they are
    # re-derived from the uploaded object's actual S3 metadata (head_object)
    # so a client can't misreport them to bypass the size/type checks.
    object_key: str


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
