"use client"

import { useRef, useState } from "react"
import { ImageIcon, Loader2Icon, PaperclipIcon, Trash2Icon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { ApiError } from "@/lib/api-client"

import { useDeleteAttachment, useUploadAttachment } from "../api/mutations"
import { useAttachmentDownloadUrl, useAttachments } from "../api/queries"
import {
  PREVIEWABLE_RECEIPT_TYPES,
  RECEIPT_ACCEPT,
  isAllowedReceiptType,
  isReceiptSizeValid,
  type Attachment,
} from "../schemas"

const UPLOAD_ERROR_MESSAGE = "Unsupported file type or file is too large (max 10 MB)."

function getUploadErrorMessage(err: unknown) {
  if (err instanceof ApiError && err.status === 422) {
    return UPLOAD_ERROR_MESSAGE
  }

  return "Could not upload this receipt. Please try again."
}

interface ReceiptThumbnailProps {
  expenseId: string
  attachment: Attachment
}

function ReceiptThumbnail({ expenseId, attachment }: ReceiptThumbnailProps) {
  const [open, setOpen] = useState(false)
  const { data, isLoading, isError } = useAttachmentDownloadUrl(expenseId, attachment.id)
  const deleteAttachment = useDeleteAttachment(expenseId)
  const canPreview = PREVIEWABLE_RECEIPT_TYPES.has(attachment.content_type)
  const canOpen = !isLoading && !isError && !!data

  return (
    <>
      <div className="group relative size-20 shrink-0 overflow-hidden rounded-xl border bg-muted">
        <button
          type="button"
          className="flex size-full items-center justify-center disabled:cursor-default"
          onClick={() => setOpen(true)}
          disabled={!canOpen}
          aria-label="View receipt"
        >
          {isLoading && (
            <Loader2Icon className="size-4 animate-spin text-muted-foreground" />
          )}
          {!isLoading && (isError || !canPreview) && (
            <ImageIcon className="size-6 text-muted-foreground" />
          )}
          {canOpen && canPreview && (
            // eslint-disable-next-line @next/next/no-img-element -- signed URL, not a static asset
            <img
              src={data.download_url}
              alt="Receipt preview"
              className="size-full object-cover"
            />
          )}
        </button>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label="Delete receipt"
          onClick={() => deleteAttachment.mutate(attachment.id)}
          disabled={deleteAttachment.isPending}
          className="absolute top-1 right-1 size-6 bg-background/80 text-destructive opacity-0 group-hover:opacity-100 hover:bg-background hover:text-destructive"
        >
          <Trash2Icon className="size-3" />
        </Button>
      </div>

      {canOpen && (
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent className="sm:max-w-lg">
            <DialogTitle className="sr-only">Receipt</DialogTitle>
            {canPreview ? (
              // eslint-disable-next-line @next/next/no-img-element -- signed URL, not a static asset
              <img src={data.download_url} alt="Receipt" className="w-full rounded-2xl" />
            ) : (
              <a
                href={data.download_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm underline underline-offset-4"
              >
                Open receipt
              </a>
            )}
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}

interface ReceiptAttachmentsProps {
  expenseId: string
}

function ReceiptAttachments({ expenseId }: ReceiptAttachmentsProps) {
  const { data: attachments, isLoading, isError } = useAttachments(expenseId)
  const uploadAttachment = useUploadAttachment(expenseId)
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [pendingCount, setPendingCount] = useState(0)

  async function handleFilesSelected(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) {
      return
    }

    setUploadError(null)

    for (const file of Array.from(fileList)) {
      if (!isAllowedReceiptType(file) || !isReceiptSizeValid(file)) {
        setUploadError(UPLOAD_ERROR_MESSAGE)
        continue
      }

      setPendingCount((count) => count + 1)
      try {
        await uploadAttachment.mutateAsync(file)
      } catch (err) {
        setUploadError(getUploadErrorMessage(err))
      } finally {
        setPendingCount((count) => count - 1)
      }
    }

    if (inputRef.current) {
      inputRef.current.value = ""
    }
  }

  return (
    <div className="flex flex-col gap-2 sm:col-span-2">
      <span className="text-sm font-medium">Receipts</span>

      {isLoading && <p className="text-xs text-muted-foreground">Loading receipts…</p>}
      {isError && (
        <p className="text-xs text-destructive" role="alert">
          Failed to load receipts.
        </p>
      )}

      {!isLoading && !isError && (
        <div className="flex flex-wrap gap-2">
          {attachments?.map((attachment) => (
            <ReceiptThumbnail
              key={attachment.id}
              expenseId={expenseId}
              attachment={attachment}
            />
          ))}

          {Array.from({ length: pendingCount }).map((_, index) => (
            <div
              key={`pending-${index}`}
              className="flex size-20 shrink-0 items-center justify-center rounded-xl border border-dashed bg-muted"
            >
              <Loader2Icon className="size-4 animate-spin text-muted-foreground" />
            </div>
          ))}

          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="flex size-20 shrink-0 flex-col items-center justify-center gap-1 rounded-xl border border-dashed text-muted-foreground hover:border-foreground/40 hover:text-foreground"
          >
            <PaperclipIcon className="size-4" />
            <span className="text-xs">Add</span>
          </button>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={RECEIPT_ACCEPT}
        multiple
        className="hidden"
        onChange={(event) => handleFilesSelected(event.target.files)}
      />

      {uploadError && (
        <p className="text-xs text-destructive" role="alert">
          {uploadError}
        </p>
      )}
    </div>
  )
}

export { ReceiptAttachments }
