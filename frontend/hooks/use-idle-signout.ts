"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

import { authClient } from "@/lib/auth-client"

const IDLE_MS = 30 * 60 * 1000

const ACTIVITY_EVENTS = ["mousemove", "keydown", "click", "touchstart", "scroll"] as const

export function useIdleSignout({ enabled }: { enabled: boolean }) {
  const router = useRouter()

  useEffect(() => {
    if (!enabled) return

    let timer: ReturnType<typeof setTimeout>

    async function onIdle() {
      await authClient.signOut()
      router.replace("/sign-in")
    }

    function resetTimer() {
      clearTimeout(timer)
      timer = setTimeout(onIdle, IDLE_MS)
    }

    ACTIVITY_EVENTS.forEach((e) => window.addEventListener(e, resetTimer, { passive: true }))
    resetTimer()

    return () => {
      clearTimeout(timer)
      ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, resetTimer))
    }
  }, [enabled, router])
}
