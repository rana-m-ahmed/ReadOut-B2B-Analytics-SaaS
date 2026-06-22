"use client"

import { useEffect, useState } from "react"
import { createClient } from "../supabase/client"
import { User } from "@supabase/supabase-js"
import { useRouter, usePathname } from "next/navigation"

export function useCurrentUser() {
  const [user, setUser] = useState<User | null>(null)
  const [isAnonymous, setIsAnonymous] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    const supabase = createClient()
    
    // Initial fetch
    supabase.auth.getSession().then(({ data: { session } }) => {
      const currentUser = session?.user ?? null
      setUser(currentUser)
      setIsAnonymous(currentUser?.is_anonymous ?? false)
      setIsLoading(false)
      
      // Redirect to login if unauthenticated on protected routes
      if (!currentUser && pathname !== "/login" && pathname !== "/") {
        router.push("/login")
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      const currentUser = session?.user ?? null
      setUser(currentUser)
      setIsAnonymous(currentUser?.is_anonymous ?? false)
      setIsLoading(false)
      
      if (!currentUser && pathname !== "/login" && pathname !== "/") {
        router.push("/login")
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [pathname, router])

  return { user, isAnonymous, isLoading }
}
