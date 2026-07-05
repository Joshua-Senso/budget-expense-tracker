"use client"

import { useState } from "react"
import { DownloadIcon, UploadIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useYearStore } from "@/stores/year-store"

import { useExportExpenses } from "../api/mutations"
import { ImportDialog } from "./import-dialog"

function getExportErrorMessage() {
  return "Could not export this year's expenses. Please try again."
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function ImportExportControls() {
  const year = useYearStore((state) => state.year)
  const exportExpenses = useExportExpenses()
  const [importOpen, setImportOpen] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  async function handleExport() {
    setExportError(null)
    try {
      const { blob, filename } = await exportExpenses.mutateAsync({ year })
      downloadBlob(blob, filename ?? `expenses-${year}.xlsx`)
    } catch {
      setExportError(getExportErrorMessage())
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={handleExport} disabled={exportExpenses.isPending}>
          <DownloadIcon />
          Export
        </Button>
        <Button variant="outline" size="sm" onClick={() => setImportOpen(true)}>
          <UploadIcon />
          Import
        </Button>
      </div>
      {exportError && (
        <p className="text-sm text-destructive" role="alert">
          {exportError}
        </p>
      )}
      <ImportDialog open={importOpen} onOpenChange={setImportOpen} year={year} />
    </div>
  )
}

export { ImportExportControls }
