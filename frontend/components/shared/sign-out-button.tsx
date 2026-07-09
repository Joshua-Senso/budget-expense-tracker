"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"

import { authClient, clearBearerToken } from "@/lib/auth-client"
import { Button } from "@/components/ui/button"
import { useWorkspaceStore } from "@/stores/workspace-store"

function SignOutButton() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [loading, setLoading] = useState(false)

  async function handleSignOut() {
    setLoading(true)
    try {
      await authClient.signOut()
    } catch (error) {
      console.error("auth: sign out request failed", error)
    } finally {
      // Clear local auth/query state even if the sign-out request itself
      // failed, so a rejected request can't leave sensitive cached data
      // reachable.
      clearBearerToken()
      queryClient.clear()
      useWorkspaceStore.getState().setActiveWorkspace({ id: null })
      router.replace("/sign-in")
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
