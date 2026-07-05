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

// Many browsers (esp. on platforms without native HEIC/HEIF decoding) report
// file.type as "" for these -- fall back to the extension so a receipt type
// the feature advertises isn't rejected before it ever reaches the API.
const EXTENSION_CONTENT_TYPES: Record<string, string> = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  webp: "image/webp",
  heic: "image/heic",
  heif: "image/heif",
}

function extensionOf(filename: string) {
  return filename.slice(filename.lastIndexOf(".") + 1).toLowerCase()
}

// The content type the upload-url request and the PUT's Content-Type header
// must both use -- resolved once so they can never disagree.
function resolveReceiptContentType(file: File): string | null {
  if (ALLOWED_RECEIPT_TYPES.includes(file.type)) {
    return file.type
  }

  if (file.type) {
    return null
  }

  return EXTENSION_CONTENT_TYPES[extensionOf(file.name)] ?? null
}

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
  return resolveReceiptContentType(file) !== null
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
  resolveReceiptContentType,
}
export type { Attachment, AttachmentUploadUrl, AttachmentDownloadUrl }
