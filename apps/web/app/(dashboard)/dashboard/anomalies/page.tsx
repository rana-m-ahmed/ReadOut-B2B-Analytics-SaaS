import { PageHeader } from "@/components/dashboard/page-header";
import { AnomaliesWorkspace } from "@/components/anomalies/anomalies-workspace";
export default function Anomalies(){return <div className="mx-auto max-w-[1400px]"><PageHeader eyebrow="Variance monitor" title="Changes outside the baseline." description="Calm, prioritized context for deviations that deserve attention."/><AnomaliesWorkspace/></div>}
