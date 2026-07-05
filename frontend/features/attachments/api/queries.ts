"use client"

import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

import type { Attachment, AttachmentDownloadUrl } from "../schemas"

function useAttachments(expenseId: string) {
  return useQuery({
    queryKey: queryKeys.attachments(expenseId),
    queryFn: () => apiFetch<Attachment[]>(`/expenses/${expenseId}/attachments`),
  })
}

function useAttachmentDownloadUrl(expenseId: string, attachmentId: string) {
  return useQuery({
    queryKey: queryKeys.attachmentDownloadUrl(expenseId, attachmentId),
    queryFn: () =>
      apiFetch<AttachmentDownloadUrl>(
        `/expenses/${expenseId}/attachments/${attachmentId}/download-url`,
      ),
    // Signed URLs expire after service.DOWNLOAD_URL_EXPIRES_IN (300s) -- refetch
    // well before that so a still-open dialog doesn't end up with a dead <img src>.
    staleTime: 4 * 60 * 1000,
  })
}

export { useAttachments, useAttachmentDownloadUrl }
