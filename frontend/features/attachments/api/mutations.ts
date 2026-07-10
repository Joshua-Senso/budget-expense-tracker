"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import { resolveReceiptContentType, type Attachment, type AttachmentUploadUrl } from "../schemas"

async function putFileToStorage(uploadUrl: string, file: File, contentType: string) {
  // Direct PUT to object storage -- receipt bytes never pass through our API
  // (PRD §9.6), and this isn't a call to api. so it bypasses apiFetch/auth.
  // contentType must match what upload-url was requested with -- the presigned
  // URL signs it, so a mismatched header fails the S3 signature check.
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": contentType },
    body: file,
  })

  if (!response.ok) {
    throw new Error(`Upload to object storage failed: ${response.status}`)
  }
}

function useUploadAttachment(expenseId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (file: File) => {
      const contentType = resolveReceiptContentType(file)
      if (!contentType) {
        throw new Error("Unsupported receipt content type.")
      }

      const { upload_url, object_key } = await apiFetch<AttachmentUploadUrl>(
        `/expenses/${expenseId}/attachments/upload-url`,
        {
          method: "POST",
          body: { content_type: contentType, size_bytes: file.size },
        },
      )

      await putFileToStorage(upload_url, file, contentType)

      return apiFetch<Attachment>(`/expenses/${expenseId}/attachments`, {
        method: "POST",
        body: { object_key },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.attachments(expenseId) })
    },
  })
}

function useDeleteAttachment(expenseId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (attachmentId: string) =>
      apiFetch<null>(`/expenses/${expenseId}/attachments/${attachmentId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.attachments(expenseId) })
    },
  })
}

export { useUploadAttachment, useDeleteAttachment }
