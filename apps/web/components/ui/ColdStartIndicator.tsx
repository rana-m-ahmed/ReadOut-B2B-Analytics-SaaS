"use client"

import { useIsFetching } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'

export function ColdStartIndicator() {
  const isFetching = useIsFetching()
  const [showIndicator, setShowIndicator] = useState(false)

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>

    if (isFetching > 0) {
      // If fetching continues for more than 2.5s, show the indicator
      timeoutId = setTimeout(() => {
        setShowIndicator(true)
      }, 2500)
    } else {
      // Hide immediately when fetching finishes
      setShowIndicator(false)
    }

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
  }, [isFetching])

  return (
    <AnimatePresence>
      {showIndicator && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50 pointer-events-none"
          data-testid="cold-start-indicator"
        >
          <div className="bg-surface border border-surface-border shadow-float rounded-control px-4 py-2 flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin text-accent" />
            <p className="text-sm text-muted-foreground m-0">
              Waking up the backend — this can take up to a minute on first load
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
