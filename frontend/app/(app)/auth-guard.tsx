"use client"

import * as React from "react"
import { useRouter } from "next/navigation"

import { authClient } from "@/lib/auth-client"
import { useIdleSignout } from "@/hooks/use-idle-signout"

function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { data: session, isPending } = authClient.useSession()

  useIdleSignout({ enabled: !!session })

  React.useEffect(() => {
    if (!isPending && !session) {
      router.replace("/sign-in")
    }
  }, [isPending, router, session])

  if (isPending) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        Loading your workspace...
      </div>
    )
  }

  if (!session) {
    return null
  }

  return children
}

export { AuthGuard }
