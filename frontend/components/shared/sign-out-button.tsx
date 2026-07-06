"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

import { authClient } from "@/lib/auth-client"
import { Button } from "@/components/ui/button"
import { useWorkspaceStore } from "@/stores/workspace-store"

function SignOutButton() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  async function handleSignOut() {
    setLoading(true)
    try {
      await authClient.signOut()
      useWorkspaceStore.getState().setActiveWorkspace({ id: null })
      router.replace("/sign-in")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      disabled={loading}
      onClick={handleSignOut}
    >
      {loading ? "Signing out…" : "Sign out"}
    </Button>
  )
}

export { SignOutButton }
