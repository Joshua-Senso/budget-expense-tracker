import type { ReactNode } from "react"

import { SignOutButton } from "./sign-out-button"

function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b bg-card">
        <nav className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-6">
          <span className="text-sm font-semibold tracking-tight">
            Expense Tracker
          </span>
          <SignOutButton />
        </nav>
      </header>
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-8">
        {children}
      </div>
    </div>
  )
}

export { AppShell }
