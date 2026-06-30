import type { ReactNode } from "react"

import { AppShell } from "@/components/shared/app-shell"

import { AuthGuard } from "./auth-guard"

function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col">
      <AuthGuard>
        <AppShell>{children}</AppShell>
      </AuthGuard>
    </div>
  )
}

export default AppLayout
