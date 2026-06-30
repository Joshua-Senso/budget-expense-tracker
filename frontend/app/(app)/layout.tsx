import type { ReactNode } from "react"

import { AppShell } from "@/components/shared/app-shell"

import { AuthGuard } from "./auth-guard"

function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  )
}

export default AppLayout
