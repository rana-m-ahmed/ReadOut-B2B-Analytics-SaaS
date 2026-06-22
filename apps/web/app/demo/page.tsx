"use client"
import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "../../lib/supabase/client"
import { apiClient } from "../../lib/api/client"
import { useAppStore } from "../../lib/store/useAppStore"

export default function DemoPage() {
  const router = useRouter()
  
  useEffect(() => {
    const initAnon = async () => {
      try {
        const supabase = createClient()
        await supabase.auth.signInAnonymously()
        
        // Fetch datasets to find the demo dataset ID
        const datasets = await apiClient.getDatasets()
        if (datasets.length > 0) {
          // Find demo dataset or just use the first one
          const demoDataset = datasets.find(d => d.name.toLowerCase().includes('demo')) || datasets[0]
          useAppStore.getState().setActiveDatasetId(demoDataset.id)
        }
        
        router.push("/overview")
      } catch (err) {
        console.error("Failed to init demo:", err)
        router.push("/connect-data")
      }
    }
    initAnon()
  }, [router])

  return <div className="p-4">Loading demo environment...</div>
}
