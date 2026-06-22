"use client"

import { useCurrentUser } from "../../lib/auth/useCurrentUser"
import { useEffect, useState } from "react"
import { LabelText } from "../ui/typography"

const ANON_SESSION_TTL_HOURS = parseInt(process.env.NEXT_PUBLIC_ANON_SESSION_TTL_HOURS || "72", 10)

export function DemoIndicator() {
  const { user, isAnonymous, isLoading } = useCurrentUser()
  const [hoursRemaining, setHoursRemaining] = useState<number | null>(null)

  useEffect(() => {
    if (isAnonymous && user?.created_at) {
      const createdAt = new Date(user.created_at).getTime()
      const expiresAt = createdAt + ANON_SESSION_TTL_HOURS * 60 * 60 * 1000
      
      const updateRemaining = () => {
        const now = Date.now()
        const remainingMs = expiresAt - now
        if (remainingMs > 0) {
          setHoursRemaining(Math.ceil(remainingMs / (1000 * 60 * 60)))
        } else {
          setHoursRemaining(0)
        }
      }

      updateRemaining()
      const interval = setInterval(updateRemaining, 60000)
      return () => clearInterval(interval)
    }
  }, [isAnonymous, user?.created_at])

  if (isLoading || !isAnonymous || hoursRemaining === null) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 pointer-events-none" data-testid="demo-indicator">
      <div className="bg-surface border border-surface-border rounded-control px-3 py-1.5 shadow-float flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
        <LabelText className="text-muted-foreground m-0">
          Demo session — resets in {hoursRemaining} {hoursRemaining === 1 ? 'hour' : 'hours'}
        </LabelText>
      </div>
    </div>
  )
}
