"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { Attachment, AttachmentUploadUrl } from "../schemas"

async function putFileToStorage(uploadUrl: string, file: File) {
  // Direct PUT to object storage -- receipt bytes never pass through our API
  // (PRD §9.6), and this isn't a call to api. so it bypasses apiFetch/auth.
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type },
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
      const { upload_url, object_key } = await apiFetch<AttachmentUploadUrl>(
        `/expenses/${expenseId}/attachments/upload-url`,
        {
          method: "POST",
          body: { content_type: file.type, size_bytes: file.size },
        },
      )

      await putFileToStorage(upload_url, file)

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
