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

// Signed URLs expire after service.DOWNLOAD_URL_EXPIRES_IN (300s). staleTime
// alone only affects refetch-on-(re)mount -- a thumbnail left mounted past
// that window would otherwise keep serving the same, now-dead, URL. Combine
// it with refetchInterval so an open dialog also refreshes in the background,
// well before expiry.
const DOWNLOAD_URL_REFRESH_MS = 4 * 60 * 1000

function useAttachmentDownloadUrl(expenseId: string, attachmentId: string) {
  return useQuery({
    queryKey: queryKeys.attachmentDownloadUrl(expenseId, attachmentId),
    queryFn: () =>
      apiFetch<AttachmentDownloadUrl>(
        `/expenses/${expenseId}/attachments/${attachmentId}/download-url`,
      ),
    staleTime: DOWNLOAD_URL_REFRESH_MS,
    refetchInterval: DOWNLOAD_URL_REFRESH_MS,
  })
}

export { useAttachments, useAttachmentDownloadUrl }
