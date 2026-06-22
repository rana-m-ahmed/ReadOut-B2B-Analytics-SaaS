"use client"
import * as React from "react"
import { AnimatePresence, motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { SPRING_DEFAULT } from "@/lib/motion"

export interface ModalWrapperProps {
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
  type?: "modal" | "drawer"
  className?: string
}

export function ModalWrapper({ isOpen, onClose, children, type = "modal", className }: ModalWrapperProps) {
  React.useEffect(() => {
    // Implementing MODAL_OPEN scale-back
    if (isOpen) {
      document.body.style.transform = "scale(0.98)"
      document.body.style.transition = "transform 0.4s cubic-bezier(0.32, 0.72, 0, 1)"
      document.body.style.transformOrigin = "top center"
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.transform = ""
      document.body.style.overflow = ""
    }
    return () => {
      document.body.style.transform = ""
      document.body.style.overflow = ""
    }
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={SPRING_DEFAULT}
            className="fixed inset-0 z-50 bg-black/10 backdrop-blur-[8px]"
            onClick={onClose}
            data-testid="modal-backdrop"
          />
          <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center">
            <motion.div
              initial={type === "modal" ? { scale: 0.95, opacity: 0 } : { y: "100%" }}
              animate={type === "modal" ? { scale: 1, opacity: 1 } : { y: 0 }}
              exit={type === "modal" ? { scale: 0.95, opacity: 0 } : { y: "100%" }}
              transition={SPRING_DEFAULT}
              className={cn(
                "pointer-events-auto bg-[var(--surface)] shadow-[var(--shadow-lift)]",
                type === "modal" 
                  ? "w-full max-w-lg rounded-[var(--radius-modal)] p-6"
                  : "absolute bottom-0 w-full rounded-t-[var(--radius-modal)] p-6",
                className
              )}
              data-testid="modal-content"
            >
              {children}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
