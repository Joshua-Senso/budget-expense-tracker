import type { ReactNode } from "react"

function AppLayout({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-svh bg-background text-foreground">
      <div className="mx-auto flex min-h-svh w-full max-w-6xl flex-col px-6 py-8">
        {children}
      </div>
    </main>
  )
}

export default AppLayout
