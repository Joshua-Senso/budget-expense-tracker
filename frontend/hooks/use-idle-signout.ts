"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

import { authClient } from "@/lib/auth-client"

const IDLE_MS = 30 * 60 * 1000
const THROTTLE_MS = 1_000
const CHECK_INTERVAL_MS = 60_000

const ACTIVITY_EVENTS = ["mousemove", "keydown", "click", "touchstart", "scroll"] as const

export function useIdleSignout({ enabled }: { enabled: boolean }) {
  const router = useRouter()

  useEffect(() => {
    if (!enabled) return

    let lastActivity = Date.now()
    let throttleTimer: ReturnType<typeof setTimeout> | null = null

    async function signOutNow() {
      try {
        await authClient.signOut()
      } finally {
        router.replace("/sign-in")
      }
    }

    async function checkIdle() {
      if (Date.now() - lastActivity >= IDLE_MS) {
        await signOutNow()
      }
    }

    // Throttled: record activity at most once per second to avoid churn
    // on high-frequency events like mousemove and scroll.
    function onActivity() {
      if (throttleTimer !== null) return
      throttleTimer = setTimeout(() => {
        lastActivity = Date.now()
        throttleTimer = null
      }, THROTTLE_MS)
    }

    // Periodic check catches idle-in-tab after 30 min without tab switching.
    const interval = setInterval(checkIdle, CHECK_INTERVAL_MS)

    // visibilitychange and focus catch backgrounded tabs and device sleep,
    // where setTimeout would have been throttled or suspended.
    document.addEventListener("visibilitychange", checkIdle)
    window.addEventListener("focus", checkIdle)
    ACTIVITY_EVENTS.forEach((e) => window.addEventListener(e, onActivity, { passive: true }))

    return () => {
      if (throttleTimer !== null) clearTimeout(throttleTimer)
      clearInterval(interval)
      document.removeEventListener("visibilitychange", checkIdle)
      window.removeEventListener("focus", checkIdle)
      ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, onActivity))
    }
  }, [enabled, router])
}
