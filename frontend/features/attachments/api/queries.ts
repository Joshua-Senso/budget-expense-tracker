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
// that window would otherwise keep serving the same, now-dead, URL, so this
// also needs an active refresh trigger. refetchInterval covers a dialog left
// open and foregrounded, but it (like all query activity) pauses while the
// tab is hidden. The query-client default also turns off refetchOnWindowFocus
// app-wide, so switching tabs away and back would otherwise skip a refetch
// entirely -- override it here so regaining focus/visibility always revalidates.
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
    refetchOnWindowFocus: true,
  })
}

export { useAttachments, useAttachmentDownloadUrl }
