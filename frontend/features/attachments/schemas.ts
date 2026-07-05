// Mirrors services/api/app/features/attachments/service.py ALLOWED_CONTENT_TYPES /
// MAX_SIZE_BYTES so bad files are rejected client-side before hitting the API.
const ALLOWED_RECEIPT_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/heic",
  "image/heif",
]

const MAX_RECEIPT_SIZE_BYTES = 10 * 1024 * 1024

const RECEIPT_ACCEPT = ALLOWED_RECEIPT_TYPES.join(",")

// HEIC/HEIF can't be rendered by <img> in most browsers; those attachments
// fall back to a generic icon with a link to open the signed URL directly.
const PREVIEWABLE_RECEIPT_TYPES = new Set(["image/jpeg", "image/png", "image/webp"])

type Attachment = {
  id: string
  expense_id: string
  content_type: string
  size_bytes: number
  uploaded_at: string
}

type AttachmentUploadUrl = {
  upload_url: string
  object_key: string
  expires_in: number
}

type AttachmentDownloadUrl = {
  download_url: string
  expires_in: number
}

function isAllowedReceiptType(file: File) {
  return ALLOWED_RECEIPT_TYPES.includes(file.type)
}

function isReceiptSizeValid(file: File) {
  return file.size > 0 && file.size <= MAX_RECEIPT_SIZE_BYTES
}

export {
  ALLOWED_RECEIPT_TYPES,
  MAX_RECEIPT_SIZE_BYTES,
  RECEIPT_ACCEPT,
  PREVIEWABLE_RECEIPT_TYPES,
  isAllowedReceiptType,
  isReceiptSizeValid,
}
export type { Attachment, AttachmentUploadUrl, AttachmentDownloadUrl }
